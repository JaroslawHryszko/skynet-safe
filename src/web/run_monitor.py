#!/usr/bin/env python3
"""
SKYNET-SAFE Activity Monitor Launcher
A simple web interface for monitoring SKYNET-SAFE activities.
"""

import os
import sys
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Load environment variables
load_dotenv()

# Import the web app
from web.skynet_activity_monitor import app

if __name__ == '__main__':
    # Get port from environment variable or use default
    port = int(os.getenv('WEB_PORT', 5000))
    
    print(f"Starting SKYNET-SAFE Activity Monitor on port {port}")
    print("Access the monitor at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    app.run(debug=False, host='0.0.0.0', port=port)