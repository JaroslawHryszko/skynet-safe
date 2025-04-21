from flask import Flask, render_template, jsonify
import os
import re
from datetime import datetime
import json
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

LOG_DIR = os.getenv("LOG_DIR", "/opt/skynet-safe/logs")
INTERACTION_LOG = os.path.join(LOG_DIR, "llm_interactions.log")
SYSTEM_LOG = os.path.join(LOG_DIR, "system.log")
AI_NAME = os.getenv("AI_NAME", "AI")

def parse_system_log():
    """Parse the system log to extract current activities"""
    activities = []
    
    if not os.path.exists(SYSTEM_LOG):
        return activities
    
    with open(SYSTEM_LOG, 'r') as f:
        for line in f.readlines()[-100:]:  # Only check last 100 lines for recent activity
            # Extract timestamp and message
            match = re.search(r'\[(.*?)\].*?INFO\s+-\s+(.*)', line)
            if match:
                timestamp = match.group(1)
                message = match.group(2)
                
                # Filter only for activity messages
                if "started" in message.lower() or "processing" in message.lower() or "analyzing" in message.lower():
                    activities.append({
                        "timestamp": timestamp,
                        "activity": message,
                        "type": "system"
                    })
    
    return activities[-5:]  # Return only the 5 most recent activities

def parse_interaction_log():
    """Parse the interaction log to get latest model interactions"""
    interactions = []
    
    if not os.path.exists(INTERACTION_LOG):
        return interactions
    
    current_interaction = None
    
    with open(INTERACTION_LOG, 'r') as f:
        for line in f.readlines()[-200:]:  # Check last 200 lines
            prompt_match = re.search(r'\[(.*?)\].*?PROMPT:\s+(.*)', line)
            response_match = re.search(r'\[(.*?)\].*?RESPONSE:\s+(.*)', line)
            
            if prompt_match:
                # Start a new interaction
                if current_interaction:
                    interactions.append(current_interaction)
                timestamp = prompt_match.group(1)
                prompt = prompt_match.group(2)
                current_interaction = {
                    "timestamp": timestamp,
                    "prompt": prompt,
                    "response": "",
                    "type": "interaction"
                }
            elif response_match and current_interaction:
                # Add response to current interaction
                response = response_match.group(2)
                current_interaction["response"] = response
    
    # Add the last interaction if there is one
    if current_interaction:
        interactions.append(current_interaction)
    
    return interactions[-5:]  # Return only the 5 most recent interactions

@app.route('/')
def index():
    """Render the main dashboard page"""
    return render_template('index.html')

@app.route('/api/activities')
def get_activities():
    """API endpoint to get current activities"""
    activities = parse_system_log()
    return jsonify(activities)

@app.route('/api/interactions')
def get_interactions():
    """API endpoint to get recent interactions"""
    interactions = parse_interaction_log()
    return jsonify(interactions)

@app.route('/api/status')
def get_status():
    """API endpoint to get system status"""
    activities = parse_system_log()
    interactions = parse_interaction_log()
    
    # Combine and sort by timestamp
    all_events = activities + interactions
    all_events.sort(key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S,%f"), reverse=True)
    
    return jsonify({
        "last_activity": activities[0] if activities else None,
        "last_interaction": interactions[0] if interactions else None,
        "recent_events": all_events[:5],  # 5 most recent events of any type
        "ai_name": AI_NAME
    })

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    
    # Import config here to avoid circular imports
    from src.config import config
    
    # Get host and port from config
    host = config.WEB_INTERFACE.get("host", "0.0.0.0")
    port = config.WEB_INTERFACE.get("port", 7860)
    debug = config.WEB_INTERFACE.get("debug", False)
    
    # Allow override via environment variables
    host = os.getenv("WEB_HOST", host)
    port = int(os.getenv("WEB_PORT", port))
    debug = os.getenv("WEB_DEBUG", str(debug)).lower() in ('true', '1', 't')
    
    # Explicitly set host to '0.0.0.0' to listen on all interfaces
    app.run(debug=debug, host='0.0.0.0', port=port)