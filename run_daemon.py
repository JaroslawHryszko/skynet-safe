#!/usr/bin/env python3
"""
Daemon mode for SKYNET-SAFE.
Allows running the system as a background process.
"""

import os
import sys
import logging
import time
import signal
import atexit
import json
import subprocess
from datetime import datetime
import argparse
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

from src.main import SkynetSystem
from src.config import config


# Setup logging
def setup_logging(log_file):
    """Configure logging for daemon mode."""
    # Create directory for log file if it doesn't exist
    log_dir = os.path.dirname(log_file)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    logger = logging.getLogger("SKYNET-DAEMON")
    logger.setLevel(logging.INFO)
    
    # File handler - always log to file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)
    
    # Only add console logging if not in daemon mode
    if sys.stdout.isatty():
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger


# Daemon class
class Daemon:
    """
    A generic daemon class.
    
    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        
        # Ensure pidfile directory exists
        os.makedirs(os.path.dirname(self.pidfile), exist_ok=True)
        
    def daemonize(self):
        """
        do the UNIX double-fork magic, see Stevens' "Advanced 
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit first parent
                sys.exit(0) 
        except OSError as e: 
            sys.stderr.write("fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)
    
        # decouple from parent environment
        # Stay in the current directory to preserve relative paths
        os.setsid() 
        os.umask(0)
    
        # do second fork
        try: 
            pid = os.fork() 
            if pid > 0:
                # exit from second parent
                sys.exit(0) 
        except OSError as e: 
            sys.stderr.write("fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1) 
    
        # redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        si = open(self.stdin, 'r')
        so = open(self.stdout, 'a+')
        se = open(self.stderr, 'a+')
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
    
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile,'w+') as f:
            f.write("%s\n" % pid)
    
    def delpid(self):
        os.remove(self.pidfile)

    def start(self):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
    
        if pid:
            message = "pidfile %s already exists. Daemon already running?\n"
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)
        
        # Start the daemon
        self.daemonize()
        self.run()

    def stop(self):
        """
        Stop the daemon
        """
        # Get the pid from the pidfile
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
    
        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)
            return # not an error in a restart

        # Try killing the daemon process    
        try:
            while True:
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
        except OSError as err:
            err = str(err)
            if err.find("No such process") > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)
            else:
                print(str(err))
                sys.exit(1)

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def status(self):
        """
        Get the daemon status
        """
        try:
            with open(self.pidfile,'r') as pf:
                pid = int(pf.read().strip())
        except IOError:
            pid = None
        
        if not pid:
            print("SKYNET-SAFE daemon is not running")
            return False
        
        try:
            os.kill(pid, 0)  # Check if process exists
            print(f"SKYNET-SAFE daemon is running with PID {pid}")
            return True
        except OSError:
            print("SKYNET-SAFE daemon is not running (stale PID file)")
            return False

    def run(self):
        """
        You should override this method when you subclass Daemon. 
        It will be called after the process has been daemonized.
        """
        pass


class SkynetDaemon(Daemon):
    """SKYNET-SAFE running as a daemon process."""
    
    def __init__(self, pidfile, config, logfile=None):
        # Get log directory from environment if available
        log_dir = os.getenv("LOG_DIR", "/var/log/skynet-safe")
        
        # Set default logfile if not provided
        self.logfile = logfile if logfile else os.path.join(log_dir, "skynet.log")
        
        # Initialize daemon
        if sys.stdout.isatty() and os.isatty(sys.stdout.fileno()):
            # If running in a terminal, use standard output for logs
            super().__init__(pidfile, stdin='/dev/null', stdout=sys.stdout.name, stderr=sys.stderr.name)
        else:
            # Otherwise use default redirections
            super().__init__(pidfile)
            
        self.config = config
        self.logger = setup_logging(self.logfile)
    
    def run(self):
        """Run SKYNET-SAFE as a daemon."""
        self.logger.info("Starting SKYNET-SAFE in daemon mode...")
        
        try:
            # Setup communication platform based on config
            # Default to console mode for testing, but this can be any supported platform
            if "platform" not in self.config["COMMUNICATION"]:
                self.config["COMMUNICATION"]["platform"] = "console"
            
            # Initialize the SKYNET system
            system = SkynetSystem(self.config)
            
            # Write status file
            status_file = os.path.join(os.path.dirname(self.pidfile), "skynet_status.json")
            with open(status_file, "w") as f:
                json.dump({
                    "status": "running",
                    "start_time": datetime.now().isoformat(),
                    "pid": os.getpid(),
                    "platform": self.config["COMMUNICATION"]["platform"]
                }, f, indent=2)
            
            # Register signal handlers
            def handle_signal(sig, frame):
                self.logger.info(f"Received signal {sig}, shutting down...")
                system._cleanup()
                with open(status_file, "w") as f:
                    json.dump({
                        "status": "stopped",
                        "stop_time": datetime.now().isoformat(),
                        "pid": os.getpid()
                    }, f, indent=2)
                sys.exit(0)
            
            signal.signal(signal.SIGTERM, handle_signal)
            signal.signal(signal.SIGINT, handle_signal)
            
            # Run the system
            system.run()
            
        except Exception as e:
            self.logger.error(f"Error in daemon mode: {e}")
            # Write error to status file
            status_file = os.path.join(os.path.dirname(self.pidfile), "skynet_status.json")
            with open(status_file, "w") as f:
                json.dump({
                    "status": "error",
                    "error_time": datetime.now().isoformat(),
                    "error": str(e),
                    "pid": os.getpid()
                }, f, indent=2)
            raise


def main():
    """Main function to handle daemon operations."""
    parser = argparse.ArgumentParser(description='SKYNET-SAFE Daemon')
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status', 'foreground'],
                      help='Action to perform with the daemon. Use "foreground" to run without daemonizing (for debugging)')
    
    # Get the default log directory from environment variable or use default
    log_dir = os.getenv("LOG_DIR", "/var/log/skynet-safe")
    default_pid_dir = os.path.join(log_dir, "run")
    
    parser.add_argument('--pidfile', default=os.path.join(default_pid_dir, 'skynet.pid'),
                      help='Path to the PID file')
    parser.add_argument('--logfile', default=os.path.join(log_dir, 'skynet.log'),
                      help='Path to the log file')
    parser.add_argument('--platform', default='console',
                      help='Communication platform (console, signal, telegram)')
    parser.add_argument('--web', action='store_true',
                      help='Start the web interface alongside the daemon')
    # Load default port from config
    from src.config import config
    default_web_port = config.WEB_INTERFACE.get("port", 7860)
    
    parser.add_argument('--web-port', type=int, default=default_web_port,
                      help=f'Port for the web interface (default: {default_web_port})')
    
    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(args.pidfile), exist_ok=True)
    os.makedirs(os.path.dirname(args.logfile), exist_ok=True)
    
    # Setup configuration
    system_config = {
        "SYSTEM_SETTINGS": config.SYSTEM_SETTINGS,
        "MODEL": config.MODEL,
        "MEMORY": config.MEMORY,
        "COMMUNICATION": {
            "platform": args.platform,
            "check_interval": 10,
            "response_delay": 1.5,
        },
        "INTERNET": config.INTERNET,
        "LEARNING": config.LEARNING,
        "CONVERSATION_INITIATOR": config.CONVERSATION_INITIATOR,
        "PERSONA": config.PERSONA,
        "METAWARENESS": config.METAWARENESS,
        "SELF_IMPROVEMENT": config.SELF_IMPROVEMENT,
        "EXTERNAL_EVALUATION": config.EXTERNAL_EVALUATION,
        "SECURITY_SYSTEM": config.SECURITY_SYSTEM,
        "DEVELOPMENT_MONITOR": config.DEVELOPMENT_MONITOR,
        "CORRECTION_MECHANISM": config.CORRECTION_MECHANISM,
        "ETHICAL_FRAMEWORK": config.ETHICAL_FRAMEWORK,
        "EXTERNAL_VALIDATION": config.EXTERNAL_VALIDATION
    }
    
    # Copy platform specific configs
    if args.platform == "signal":
        if "signal_phone_number" in config.COMMUNICATION:
            system_config["COMMUNICATION"]["signal_phone_number"] = config.COMMUNICATION["signal_phone_number"]
        if "signal_config_path" in config.COMMUNICATION:
            system_config["COMMUNICATION"]["signal_config_path"] = config.COMMUNICATION["signal_config_path"]
    elif args.platform == "telegram":
        if "telegram_bot_token" in config.COMMUNICATION:
            system_config["COMMUNICATION"]["telegram_bot_token"] = config.COMMUNICATION["telegram_bot_token"]
        if "telegram_allowed_users" in config.COMMUNICATION:
            system_config["COMMUNICATION"]["telegram_allowed_users"] = config.COMMUNICATION["telegram_allowed_users"]
        if "telegram_polling_timeout" in config.COMMUNICATION:
            system_config["COMMUNICATION"]["telegram_polling_timeout"] = config.COMMUNICATION["telegram_polling_timeout"]
        if "telegram_chat_state_file" in config.COMMUNICATION:
            system_config["COMMUNICATION"]["telegram_chat_state_file"] = config.COMMUNICATION["telegram_chat_state_file"]
        if "telegram_test_chat_id" in config.COMMUNICATION:
            system_config["COMMUNICATION"]["telegram_test_chat_id"] = config.COMMUNICATION["telegram_test_chat_id"]
    
    # Create daemon instance
    daemon = SkynetDaemon(args.pidfile, system_config, args.logfile)
    
    # Define function to start web interface
    def start_web_interface(port=5000):
        """Start the web interface in a separate process."""
        web_pidfile = os.path.join(os.path.dirname(args.pidfile), 'skynet-web.pid')
        
        # Check if web interface is already running
        if os.path.exists(web_pidfile):
            try:
                with open(web_pidfile, 'r') as f:
                    web_pid = int(f.read().strip())
                try:
                    os.kill(web_pid, 0)  # Check if process exists
                    print(f"Web interface already running on port {port} with PID {web_pid}")
                    return web_pid
                except OSError:
                    # Process not running, remove stale PID file
                    os.remove(web_pidfile)
            except (IOError, ValueError):
                # Invalid PID file, remove it
                if os.path.exists(web_pidfile):
                    os.remove(web_pidfile)
        
        # Use the run_monitor.py script to start the web interface
        monitor_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'run_monitor.py')
        
        # Set environment variable for web port
        env = os.environ.copy()
        env['WEB_PORT'] = str(port)
        
        # Get host from config
        host = config.WEB_INTERFACE.get("host", "0.0.0.0")
        host = os.getenv("WEB_HOST", host)
        
        # Start web interface in a new process
        print(f"Starting web interface on {host}:{port}...")
        
        # Set environment variables for web interface
        env['WEB_PORT'] = str(port)
        env['WEB_HOST'] = host
        
        if args.action == 'foreground':
            # For foreground mode, use a separate process group
            web_process = subprocess.Popen([sys.executable, monitor_script],
                                          env=env,
                                          stdout=subprocess.PIPE,
                                          stderr=subprocess.PIPE,
                                          preexec_fn=os.setsid)
        else:
            # For daemon mode, detach completely
            web_process = subprocess.Popen([sys.executable, monitor_script],
                                         env=env,
                                         stdout=subprocess.DEVNULL,
                                         stderr=subprocess.DEVNULL,
                                         preexec_fn=os.setsid)
        
        # Write PID to file
        with open(web_pidfile, 'w') as f:
            f.write(f"{web_process.pid}\n")
        
        print(f"Web interface started with PID {web_process.pid}")
        
        # Get machine's IP address
        import socket
        def get_ip_address():
            try:
                # Create a socket connection to an external server
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                # Doesn't need to be reachable
                s.connect(('10.255.255.255', 1))
                ip = s.getsockname()[0]
                s.close()
                return ip
            except Exception:
                return '127.0.0.1'
        
        ip_address = get_ip_address()
        
        print(f"Access locally at: http://localhost:{port}")
        print(f"Access from network at: http://{ip_address}:{port}")
        return web_process.pid

    # Perform requested action
    if args.action == 'start':
        print(f"Starting SKYNET-SAFE daemon with {args.platform} platform...")
        
        # Start web interface if requested
        if args.web:
            start_web_interface(args.web_port)
            
        daemon.start()
        
    elif args.action == 'stop':
        print("Stopping SKYNET-SAFE daemon...")
        
        # Also stop web interface if it's running
        web_pidfile = os.path.join(os.path.dirname(args.pidfile), 'skynet-web.pid')
        if os.path.exists(web_pidfile):
            try:
                with open(web_pidfile, 'r') as f:
                    web_pid = int(f.read().strip())
                try:
                    print(f"Stopping web interface (PID {web_pid})...")
                    os.killpg(os.getpgid(web_pid), signal.SIGTERM)
                    os.remove(web_pidfile)
                except OSError as e:
                    print(f"Error stopping web interface: {e}")
            except (IOError, ValueError):
                print("Could not read web interface PID file")
                
        daemon.stop()
        
    elif args.action == 'restart':
        print("Restarting SKYNET-SAFE daemon...")
        
        # Stop web interface if it's running
        web_pidfile = os.path.join(os.path.dirname(args.pidfile), 'skynet-web.pid')
        if os.path.exists(web_pidfile):
            try:
                with open(web_pidfile, 'r') as f:
                    web_pid = int(f.read().strip())
                try:
                    print(f"Stopping web interface (PID {web_pid})...")
                    os.killpg(os.getpgid(web_pid), signal.SIGTERM)
                    os.remove(web_pidfile)
                except OSError as e:
                    print(f"Error stopping web interface: {e}")
            except (IOError, ValueError):
                print("Could not read web interface PID file")
        
        daemon.restart()
        
        # Start web interface if requested
        if args.web:
            start_web_interface(args.web_port)
            
    elif args.action == 'status':
        daemon_running = daemon.status()
        
        # Check web interface status
        web_pidfile = os.path.join(os.path.dirname(args.pidfile), 'skynet-web.pid')
        if os.path.exists(web_pidfile):
            try:
                with open(web_pidfile, 'r') as f:
                    web_pid = int(f.read().strip())
                try:
                    os.kill(web_pid, 0)  # Check if process exists
                    print(f"Web interface is running with PID {web_pid}")
                except OSError:
                    print("Web interface is not running (stale PID file)")
            except (IOError, ValueError):
                print("Could not read web interface PID file")
        else:
            print("Web interface is not running")
            
    elif args.action == 'foreground':
        print(f"Starting SKYNET-SAFE in foreground mode with {args.platform} platform...")
        
        # Start web interface if requested
        web_pid = None
        if args.web:
            web_pid = start_web_interface(args.web_port)
            
        # Write PID file without daemonizing
        with open(daemon.pidfile, 'w+') as f:
            f.write("%s\n" % os.getpid())
        try:
            daemon.run()
        except KeyboardInterrupt:
            print("\nShutting down SKYNET-SAFE...")
            
            # Also stop web interface if it was started
            if args.web and web_pid:
                try:
                    print(f"Stopping web interface (PID {web_pid})...")
                    os.killpg(os.getpgid(web_pid), signal.SIGTERM)
                    web_pidfile = os.path.join(os.path.dirname(args.pidfile), 'skynet-web.pid')
                    if os.path.exists(web_pidfile):
                        os.remove(web_pidfile)
                except OSError as e:
                    print(f"Error stopping web interface: {e}")
                    
            if os.path.exists(daemon.pidfile):
                os.remove(daemon.pidfile)


if __name__ == "__main__":
    main()