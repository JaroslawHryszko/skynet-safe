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
    
    # Get port from environment variable or use default
    port = int(os.getenv('WEB_PORT', 5000))
    
    print(f"Starting SKYNET-SAFE Activity Monitor on port {port}")
    print(f"Access the monitor at http://localhost:{port}")
    print("Press Ctrl+C to stop")
    
    app.run(debug=False, host='0.0.0.0', port=port)