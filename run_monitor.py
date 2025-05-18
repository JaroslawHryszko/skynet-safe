#!/usr/bin/env python3
"""
SKYNET-SAFE Activity Monitor Launcher
A simple web interface for monitoring SKYNET-SAFE activities.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Load environment variables
load_dotenv()

if __name__ == '__main__':
    # Import here to ensure environment is properly set up
    from src.web.skynet_activity_monitor import app
    from src.config import config
    
    # Get host and port from config
    host = config.WEB_INTERFACE.get("host", "0.0.0.0")
    port = config.WEB_INTERFACE.get("port", 7860)
    debug = config.WEB_INTERFACE.get("debug", False)
    
    # Allow override via environment variables
    host = os.getenv("WEB_HOST", host)
    port = int(os.getenv("WEB_PORT", port))
    debug = os.getenv("WEB_DEBUG", str(debug)).lower() in ('true', '1', 't')
    
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
    
    print(f"Starting SKYNET-SAFE Activity Monitor on port {port}")
    print(f"Access locally at: http://localhost:{port}")
    print(f"Access from network at: http://{ip_address}:{port}")
    print("Press Ctrl+C to stop")
    
    # Explicitly set host to '0.0.0.0' to listen on all interfaces
    app.run(debug=debug, host='0.0.0.0', port=port)