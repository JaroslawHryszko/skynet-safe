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
SYSTEM_LOG = os.path.join(LOG_DIR, "skynet.log")
AI_NAME = os.getenv("AI_NAME", "AI")

def parse_system_log():
    """Parse the system log to extract current activities"""
    activities = []
    
    if not os.path.exists(SYSTEM_LOG):
        return activities
    
    try:
        with open(SYSTEM_LOG, 'r') as f:
            lines = f.readlines()[-100:]  # Only check last 100 lines for recent activity
            
            for line in lines:
                # Extract timestamp and message
                # Try multiple patterns to catch different log formats
                match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+.*?INFO\s+-\s+(.*)', line)
                if not match:
                    match = re.search(r'\[(.*?)\].*?INFO\s+-\s+(.*)', line)
                
                if match:
                    timestamp = match.group(1)
                    message = match.group(2)
                    
                    # Broader filter for activity messages
                    activity_keywords = ["started", "processing", "analyzing", "received", 
                                        "sending", "initializing", "loaded", "performing", 
                                        "running", "executed", "fetched", "completed"]
                    
                    if any(keyword in message.lower() for keyword in activity_keywords):
                        activities.append({
                            "timestamp": timestamp,
                            "activity": message,
                            "type": "system"
                        })
                    
    except Exception as e:
        print(f"Error parsing system log: {e}")
        return []
    
    return activities[-5:]  # Return only the 5 most recent activities

def parse_interaction_log():
    """Parse the interaction log to get latest model interactions"""
    interactions = []
    
    if not os.path.exists(INTERACTION_LOG):
        return interactions
    
    try:
        with open(INTERACTION_LOG, 'r') as f:
            lines = f.readlines()[-200:]  # Check last 200 lines
            
            # Look for JSON formatted entries
            for line in lines:
                try:
                    # Try to parse as JSON
                    if '{' in line and '}' in line:
                        json_part = line[line.find('{'):line.rfind('}')+1]
                        interaction_data = json.loads(json_part)
                        
                        # Extract relevant fields
                        if 'timestamp' in interaction_data and 'query' in interaction_data and 'response' in interaction_data:
                            interactions.append({
                                "timestamp": interaction_data.get('timestamp', '').split('T')[0],
                                "prompt": interaction_data.get('query', 'No query available'),
                                "response": interaction_data.get('response', 'No response available'),
                                "type": "interaction"
                            })
                except json.JSONDecodeError:
                    # If JSON parsing fails, try regex based approach
                    continue
            
            # If no interactions found with JSON parsing, fall back to regex
            if not interactions:
                current_interaction = None
                
                for line in lines:
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
    except Exception as e:
        print(f"Error parsing interaction log: {e}")
        return []
    
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
    
    # Combine all events
    all_events = activities + interactions
    
    # Sort by timestamp with a more flexible approach
    def safe_timestamp_sort(x):
        try:
            ts = x.get("timestamp", "")
            # Try different timestamp formats
            formats = [
                "%Y-%m-%d %H:%M:%S,%f",  # Standard format with microseconds
                "%Y-%m-%d %H:%M:%S",     # Without microseconds
                "%Y-%m-%d"               # Just date
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(ts, fmt)
                except ValueError:
                    continue
            
            # If all parsing fails, return a default old date
            return datetime(2000, 1, 1)
        except Exception:
            # Last resort fallback
            return datetime(2000, 1, 1)
    
    # Sort the events
    try:
        all_events.sort(key=safe_timestamp_sort, reverse=True)
    except Exception as e:
        print(f"Error sorting events: {e}")
    
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