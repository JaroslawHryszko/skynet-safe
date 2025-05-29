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
from contextlib import contextmanager

# Load environment variables first
load_dotenv()


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
        Daemonization using fork() when available, subprocess fallback.
        """
        # Force fork-based daemonization regardless of TTY status when called from start()

        try:
            # Try fork-based daemonization first
            pid = os.fork()
            if pid > 0:
                # Parent process - wait briefly and exit
                time.sleep(0.1)
                print(f"Daemon started successfully with PID {pid}")
                sys.exit(0)
        except OSError as e:
            # Fork not available, use subprocess fallback
            import subprocess
            
            # Get current script arguments but change action to 'foreground'
            args = sys.argv[:]
            if len(args) > 1:
                args[1] = 'foreground'
            else:
                args.append('foreground')
            
            # Start the daemon in a completely separate process
            process = subprocess.Popen(args, 
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, 
                stdin=subprocess.DEVNULL, preexec_fn=os.setsid)
            
            # Wait a moment to ensure process starts
            time.sleep(0.5)
            
            # Check if process is still running
            if process.poll() is None:
                print(f"Daemon started successfully with PID {process.pid}")
                # Write PID file manually
                with open(self.pidfile, 'w') as f:
                    f.write(f"{process.pid}\n")
                sys.exit(0)
            else:
                print("Failed to start daemon process")
                sys.exit(1)
        
        # Child process continues here (fork was successful)
        self._setup_daemon_environment()
    
    
    def _setup_daemon_environment(self):
        """Setup daemon environment (session, umask, file descriptors)."""
        # Create new session
        try:
            os.setsid()
        except OSError:
            # Already session leader or not supported
            pass
            
        # Set umask
        os.umask(0)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        # Only redirect if we have valid file paths
        if hasattr(self, 'stdin') and self.stdin:
            try:
                si = open(self.stdin, 'r')
                os.dup2(si.fileno(), sys.stdin.fileno())
            except (OSError, IOError):
                pass
                
        if hasattr(self, 'stdout') and self.stdout:
            try:
                so = open(self.stdout, 'a+')
                os.dup2(so.fileno(), sys.stdout.fileno())
            except (OSError, IOError):
                pass
                
        if hasattr(self, 'stderr') and self.stderr:
            try:
                se = open(self.stderr, 'a+')
                os.dup2(se.fileno(), sys.stderr.fileno())
            except (OSError, IOError):
                pass
    
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
            try:
                # Check if process is actually running
                os.kill(pid, 0)
                message = "pidfile %s already exists. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                sys.exit(1)
            except OSError:
                # Process not running, remove stale pidfile
                os.remove(self.pidfile)
        
        # Start the daemon
        self.daemonize()
        
        # If we reach here, we're in the child process
        # write pidfile
        atexit.register(self.delpid)
        pid = str(os.getpid())
        with open(self.pidfile,'w+') as f:
            f.write("%s\n" % pid)
            
        # Run the daemon
        self.run()

    def stop(self):
        """
        Stop the daemon with enhanced safety checks
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

        # Enhanced stopping procedure with multiple attempts and verification
        print(f"Stopping daemon process {pid}...")
        
        # Try to send shutdown notification if daemon is running
        try:
            # Check if process is still running before trying to notify
            os.kill(pid, 0)
            # Process exists, try to read its communication config for notification
            # Note: This is a best-effort attempt - may not always work
            print("Attempting to send shutdown notification...")
        except OSError:
            # Process not running
            pass
        
        # First attempt: SIGTERM (graceful shutdown)
        try:
            os.kill(pid, signal.SIGTERM)
            print("Sent SIGTERM, waiting for graceful shutdown...")
            
            # Wait up to 10 seconds for graceful shutdown
            for i in range(50):  # 50 * 0.2 = 10 seconds
                try:
                    os.kill(pid, 0)  # Check if process still exists
                    time.sleep(0.2)
                except OSError:
                    # Process has terminated
                    print("Process terminated gracefully")
                    break
            else:
                # Process still running after 10 seconds
                print("Graceful shutdown timeout, forcing termination...")
                try:
                    os.kill(pid, signal.SIGKILL)
                    print("Sent SIGKILL")
                    
                    # Wait up to 5 seconds for force kill
                    for i in range(25):  # 25 * 0.2 = 5 seconds
                        try:
                            os.kill(pid, 0)
                            time.sleep(0.2)
                        except OSError:
                            print("Process force-terminated")
                            break
                    else:
                        print("WARNING: Process may still be running after force kill")
                        
                except OSError as e:
                    if "No such process" not in str(e):
                        print(f"Error during force kill: {e}")
                        
        except OSError as err:
            err_str = str(err)
            if "No such process" in err_str:
                print("Process was already terminated")
            else:
                print(f"Error stopping process: {err_str}")
                sys.exit(1)
        
        # Additional cleanup: check for child processes
        self._cleanup_child_processes(pid)
        
        # Clean up PID file
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)
            print("Removed PID file")
        
        # Verify complete shutdown
        self._verify_shutdown(pid)
        print("Daemon stopped successfully")

    def _cleanup_child_processes(self, parent_pid):
        """Clean up any child processes that might still be running"""
        try:
            # Use ps to find child processes
            result = subprocess.run(['ps', '--ppid', str(parent_pid), '-o', 'pid', '--no-headers'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0 and result.stdout.strip():
                child_pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
                
                if child_pids:
                    print(f"Found {len(child_pids)} child processes, terminating...")
                    for child_pid in child_pids:
                        try:
                            os.kill(child_pid, signal.SIGTERM)
                            time.sleep(0.5)
                            # Check if still running, then force kill
                            try:
                                os.kill(child_pid, 0)
                                os.kill(child_pid, signal.SIGKILL)
                                print(f"Force-killed child process {child_pid}")
                            except OSError:
                                print(f"Child process {child_pid} terminated")
                        except OSError:
                            pass  # Process already terminated
                            
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            # ps command failed or timed out, try alternative method
            try:
                # Use pgrep to find processes with skynet in name
                result = subprocess.run(['pgrep', '-f', 'skynet'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and result.stdout.strip():
                    pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
                    for pid in pids:
                        if pid != parent_pid and pid != os.getpid():
                            try:
                                print(f"Terminating related process {pid}")
                                os.kill(pid, signal.SIGTERM)
                                time.sleep(0.5)
                                try:
                                    os.kill(pid, 0)
                                    os.kill(pid, signal.SIGKILL)
                                except OSError:
                                    pass
                            except OSError:
                                pass
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                print("Could not check for child processes")

    def _verify_shutdown(self, pid):
        """Verify that the daemon and related processes are completely stopped"""
        # Check main process
        try:
            os.kill(pid, 0)
            print(f"WARNING: Main process {pid} is still running!")
            return False
        except OSError:
            pass  # Process is stopped, which is expected
        
        # Check for any remaining skynet processes
        try:
            result = subprocess.run(['pgrep', '-f', 'skynet'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                remaining_pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') 
                                if pid.strip() and int(pid.strip()) != os.getpid()]
                if remaining_pids:
                    print(f"WARNING: Found {len(remaining_pids)} remaining skynet processes: {remaining_pids}")
                    return False
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass  # pgrep not available or failed
        
        return True

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
        log_dir = os.getenv("LOG_DIR", "./logs")
        
        # Set default logfile if not provided
        self.logfile = logfile if logfile else os.path.join(log_dir, "skynet.log")
        
        # Initialize daemon
        if sys.stdout.isatty() and os.isatty(sys.stdout.fileno()):
            # If running in a terminal, use log file for output
            log_dir = os.path.dirname(self.logfile)
            if not log_dir:
                # Fallback to skynet-safe/logs/ directory
                script_dir = os.path.dirname(os.path.abspath(__file__))
                log_dir = os.path.join(script_dir, 'logs')
                os.makedirs(log_dir, exist_ok=True)
            super().__init__(pidfile, stdin='/dev/null', 
                           stdout=self.logfile, 
                           stderr=self.logfile)
        else:
            # Otherwise use default redirections
            super().__init__(pidfile)
            
        self.config = config
        self.logger = setup_logging(self.logfile)
    
    def run(self):
        """Run SKYNET-SAFE as a daemon."""
        self.logger.info("Starting SKYNET-SAFE in daemon mode...")
        
        try:
            # Import here to avoid issues during daemonization
            from src.main import SkynetSystem
            
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
                # Send shutdown notification via communication platform
                try:
                    system.communication.send_system_message("🔴 System shutting down...", "info")
                except Exception as e:
                    self.logger.error(f"Failed to send shutdown notification: {e}")
                
                system.shutdown()  # Use proper shutdown method
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
    log_dir = os.getenv("LOG_DIR", "./logs")
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
    try:
        from src.config import config
        default_web_port = config.WEB_INTERFACE.get("port", 7860)
    except ImportError:
        default_web_port = 7860
    
    parser.add_argument('--web-port', type=int, default=default_web_port,
                      help=f'Port for the web interface (default: {default_web_port})')
    
    args = parser.parse_args()
    
    # Create directories if they don't exist
    os.makedirs(os.path.dirname(args.pidfile), exist_ok=True)
    os.makedirs(os.path.dirname(args.logfile), exist_ok=True)
    
    # Setup configuration
    # Import config here to avoid import issues during daemonization
    from src.config import config
    
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
        
        # Enhanced web interface stopping
        web_pidfile = os.path.join(os.path.dirname(args.pidfile), 'skynet-web.pid')
        if os.path.exists(web_pidfile):
            try:
                with open(web_pidfile, 'r') as f:
                    web_pid = int(f.read().strip())
                try:
                    print(f"Stopping web interface (PID {web_pid})...")
                    # Try graceful shutdown first
                    os.killpg(os.getpgid(web_pid), signal.SIGTERM)
                    
                    # Wait for graceful shutdown
                    for i in range(30):  # 30 * 0.2 = 6 seconds
                        try:
                            os.kill(web_pid, 0)
                            time.sleep(0.2)
                        except OSError:
                            print("Web interface terminated gracefully")
                            break
                    else:
                        # Force kill if still running
                        try:
                            print("Force-killing web interface...")
                            os.killpg(os.getpgid(web_pid), signal.SIGKILL)
                        except OSError:
                            pass
                    
                    # Clean up PID file
                    if os.path.exists(web_pidfile):
                        os.remove(web_pidfile)
                        
                except OSError as e:
                    print(f"Error stopping web interface: {e}")
                    # Try to remove PID file anyway
                    if os.path.exists(web_pidfile):
                        os.remove(web_pidfile)
            except (IOError, ValueError):
                print("Could not read web interface PID file")
                # Try to remove invalid PID file
                if os.path.exists(web_pidfile):
                    os.remove(web_pidfile)
                
        daemon.stop()
        
        # Final verification that all processes are stopped
        print("Verifying complete shutdown...")
        try:
            result = subprocess.run(['pgrep', '-f', 'skynet'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and result.stdout.strip():
                remaining_pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') 
                                if pid.strip() and int(pid.strip()) != os.getpid()]
                if remaining_pids:
                    print(f"WARNING: Found {len(remaining_pids)} remaining processes: {remaining_pids}")
                    print("You may need to manually kill these processes")
                else:
                    print("All processes stopped successfully")
            else:
                print("All processes stopped successfully")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            print("Could not verify process shutdown (pgrep not available)")
        
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
        
        def cleanup_foreground():
            """Clean up resources when exiting foreground mode."""
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
        
        try:
            daemon.run()
        except KeyboardInterrupt:
            cleanup_foreground()
        except Exception as e:
            print(f"Error in foreground mode: {e}")
            cleanup_foreground()
            sys.exit(1)
        finally:
            cleanup_foreground()


if __name__ == "__main__":
    main()