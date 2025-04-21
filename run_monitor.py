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
    
    print(f"Starting SKYNET-SAFE Activity Monitor on {host}:{port}")
    if host == "0.0.0.0":
        print(f"Access the monitor at http://localhost:{port}")
    else:
        print(f"Access the monitor at http://{host}:{port}")
    print("Press Ctrl+C to stop")
    
    app.run(debug=debug, host=host, port=port)