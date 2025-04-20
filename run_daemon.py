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
from datetime import datetime
import argparse

from src.main import SkynetSystem
from src.config import config


# Setup logging
def setup_logging(log_file):
    """Configure logging for daemon mode."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("SKYNET-DAEMON")


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
        # os.chdir("/") - nie zmieniaj katalogu, aby zachować względne ścieżki
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
        # Wyłączenie daemonizacji i uruchomienie w trybie foreground dla celów debugowania
        # self.daemonize()
        # Zapisz PID do pliku
        with open(self.pidfile,'w+') as f:
            f.write("%s\n" % os.getpid())
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
        super().__init__(pidfile)
        self.config = config
        self.logfile = logfile if logfile else "/var/log/skynet-safe/skynet.log"
        if self.logfile.startswith("/"):
            os.makedirs(os.path.dirname(self.logfile), exist_ok=True)
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
    parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'],
                      help='Action to perform with the daemon')
    parser.add_argument('--pidfile', default='/tmp/skynet-safe/skynet.pid',
                      help='Path to the PID file')
    parser.add_argument('--logfile', default='/var/log/skynet-safe/skynet.log',
                      help='Path to the log file')
    parser.add_argument('--platform', default='console',
                      help='Communication platform (console, signal, telegram)')
    
    args = parser.parse_args()
    
    # Create pidfile directory if it doesn't exist
    os.makedirs(os.path.dirname(args.pidfile), exist_ok=True)
    
    # Setup configuration
    system_config = {
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
    
    # Perform requested action
    if args.action == 'start':
        print(f"Starting SKYNET-SAFE daemon with {args.platform} platform...")
        daemon.start()
    elif args.action == 'stop':
        print("Stopping SKYNET-SAFE daemon...")
        daemon.stop()
    elif args.action == 'restart':
        print("Restarting SKYNET-SAFE daemon...")
        daemon.restart()
    elif args.action == 'status':
        daemon.status()


if __name__ == "__main__":
    main()