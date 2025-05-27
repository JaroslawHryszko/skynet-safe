from flask import Flask, render_template, jsonify
import os
import re
import time
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
STDERR_LOG = os.path.join(LOG_DIR, "stderr.log")
STDOUT_LOG = os.path.join(LOG_DIR, "stdout.log")
AI_NAME = os.getenv("AI_NAME", "AI")

# Track start time for uptime calculation
start_time = time.time()

def get_uptime():
    """Calculate system uptime in human readable format"""
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    
    if hours > 0:
        return f"{hours}h {minutes}m"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def get_completed_tasks_count():
    """Count completed tasks from system logs"""
    completed_count = 0
    
    if not os.path.exists(SYSTEM_LOG):
        return completed_count
    
    try:
        with open(SYSTEM_LOG, 'r') as f:
            lines = f.readlines()
            
        # Keywords that indicate task completion
        completion_keywords = [
            "completed", "finished", "done", "success", 
            "Generated initiation message", "Persona updated",
            "External evaluation completed", "Reflection completed",
            "Discovery saved", "Learning cycle completed"
        ]
        
        for line in lines:
            if "INFO" in line:
                for keyword in completion_keywords:
                    if keyword.lower() in line.lower():
                        completed_count += 1
                        break  # Don't count the same line multiple times
                        
    except Exception as e:
        print(f"Error counting completed tasks: {e}")
        return 0
    
    return completed_count

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

def parse_recent_activities():
    """Parse interaction, system, stdout and stderr logs for recent activities with clean formatting"""
    activities = []
    
    # Parse interaction log for user queries
    if os.path.exists(INTERACTION_LOG):
        try:
            with open(INTERACTION_LOG, 'r') as f:
                lines = f.readlines()[-50:]  # Check last 50 lines
                
                for line in lines:
                    try:
                        # Try to parse as JSON
                        if '{' in line and '}' in line:
                            json_part = line[line.find('{'):line.rfind('}')+1]
                            interaction_data = json.loads(json_part)
                            
                            # Extract relevant fields
                            if 'timestamp' in interaction_data and 'query' in interaction_data:
                                timestamp_str = interaction_data.get('timestamp', '')
                                query = interaction_data.get('query', '').strip()
                                
                                if query and timestamp_str:
                                    # Format timestamp to HH:MM
                                    try:
                                        if 'T' in timestamp_str:
                                            # ISO format
                                            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                        else:
                                            # Try parsing as standard datetime
                                            dt = datetime.strptime(timestamp_str.split('.')[0], '%Y-%m-%d %H:%M:%S')
                                        
                                        time_str = dt.strftime('%H:%M')
                                        
                                        # Anonymize user queries for privacy
                                        activities.append({
                                            "timestamp": timestamp_str,
                                            "time_display": time_str,
                                            "activity": "Query",
                                            "type": "interaction",
                                            "sort_time": dt
                                        })
                                        
                                    except Exception as e:
                                        print(f"Error parsing timestamp {timestamp_str}: {e}")
                                        continue
                                        
                    except json.JSONDecodeError:
                        continue
                        
        except Exception as e:
            print(f"Error parsing interaction log for activities: {e}")
    
    # Parse system log for system activities
    if os.path.exists(SYSTEM_LOG):
        try:
            with open(SYSTEM_LOG, 'r') as f:
                lines = f.readlines()[-50:]  # Check last 50 lines
                
                for line in lines:
                    # Extract timestamp and message
                    match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+.*?INFO\s+-\s+(.*)', line)
                    if not match:
                        match = re.search(r'\[(.*?)\].*?INFO\s+-\s+(.*)', line)
                    
                    if match:
                        timestamp_str = match.group(1)
                        message = match.group(2)
                        
                        # Filter for important system activities
                        important_keywords = ["Performing periodic", "Generating initiation", "New discovery", 
                                            "Persona updated", "Performing reflection", "External evaluation",
                                            "started", "completed"]
                        
                        if any(keyword in message for keyword in important_keywords):
                            try:
                                # Parse timestamp
                                if ',' in timestamp_str:
                                    dt = datetime.strptime(timestamp_str.split(',')[0], '%Y-%m-%d %H:%M:%S')
                                else:
                                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                
                                time_str = dt.strftime('%H:%M')
                                
                                # Shorten long system messages
                                if len(message) > 40:
                                    message = message[:40] + '...'
                                
                                activities.append({
                                    "timestamp": timestamp_str,
                                    "time_display": time_str,
                                    "activity": message,
                                    "type": "system",
                                    "sort_time": dt
                                })
                                
                            except Exception as e:
                                print(f"Error parsing system timestamp {timestamp_str}: {e}")
                                continue
                                
        except Exception as e:
            print(f"Error parsing system log for activities: {e}")
    
    # Parse stdout log for output activities
    if os.path.exists(STDOUT_LOG):
        try:
            with open(STDOUT_LOG, 'r') as f:
                lines = f.readlines()[-20:]  # Check last 20 lines
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        # Extract timestamp if present
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                        
                        if timestamp_match:
                            timestamp_str = timestamp_match.group(1)
                            try:
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                time_str = dt.strftime('%H:%M')
                                
                                # Look for relevant stdout activities
                                if any(keyword in line.lower() for keyword in ['started', 'loaded', 'initialized', 'ready']):
                                    activities.append({
                                        "timestamp": timestamp_str,
                                        "time_display": time_str,
                                        "activity": "System Output",
                                        "type": "stdout",
                                        "sort_time": dt
                                    })
                                    
                            except Exception as e:
                                print(f"Error parsing stdout timestamp {timestamp_str}: {e}")
                                continue
                                
        except Exception as e:
            print(f"Error parsing stdout log for activities: {e}")
    
    # Parse stderr log for error activities
    if os.path.exists(STDERR_LOG):
        try:
            with open(STDERR_LOG, 'r') as f:
                lines = f.readlines()[-20:]  # Check last 20 lines
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('#'):  # Skip empty lines and comments
                        # Extract timestamp if present
                        timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                        
                        if timestamp_match:
                            timestamp_str = timestamp_match.group(1)
                            try:
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                time_str = dt.strftime('%H:%M')
                                
                                # Look for relevant stderr activities
                                if any(keyword in line.lower() for keyword in ['error', 'warning', 'exception']):
                                    activities.append({
                                        "timestamp": timestamp_str,
                                        "time_display": time_str,
                                        "activity": "System Error",
                                        "type": "stderr",
                                        "sort_time": dt
                                    })
                                    
                            except Exception as e:
                                print(f"Error parsing stderr timestamp {timestamp_str}: {e}")
                                continue
                                
        except Exception as e:
            print(f"Error parsing stderr log for activities: {e}")
    
    # Sort by timestamp and return last 6
    try:
        activities.sort(key=lambda x: x.get('sort_time', datetime.min), reverse=True)
    except Exception as e:
        print(f"Error sorting activities: {e}")
    
    # Remove sort_time before returning
    for activity in activities:
        activity.pop('sort_time', None)
    
    return activities[:6]

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

def normalize_unbounded_metric(value, baseline=1.0, scale_factor=0.1):
    """Normalize potentially unbounded metrics to 0-1 range using tanh scaling"""
    if value is None or not isinstance(value, (int, float)):
        return 0.0
    
    # Use tanh to map to 0-1 range, with baseline as midpoint
    normalized = (math.tanh((value - baseline) * scale_factor) + 1) / 2
    return min(max(normalized, 0.0), 1.0)

def get_persona_state():
    """Read current persona state from file"""
    persona_file = "./data/persona/persona_state.json"
    try:
        if os.path.exists(persona_file):
            with open(persona_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"Error reading persona state: {e}")
    return {}

def get_system_state():
    """Parse logs to determine current system state"""
    try:
        with open(SYSTEM_LOG, 'r') as f:
            lines = f.readlines()[-20:]  # Check last 20 lines
            
        current_activity = "Idle"
        loop_iterations = 0
        last_action_time = None
        
        for line in reversed(lines):
            if "Performing periodic system tasks" in line:
                current_activity = "Periodic Tasks"
                break
            elif "Generating initiation message" in line:
                current_activity = "Initiating Conversation"
                break
            elif "New discovery:" in line:
                current_activity = "Internet Exploration"
                break
            elif "Persona updated" in line:
                current_activity = "Persona Update"
                break
            elif "Performing reflection" in line:
                current_activity = "Self-Reflection"
                break
            elif "External evaluation" in line:
                current_activity = "External Evaluation"
                break
            elif "processing" in line.lower() or "received" in line.lower():
                current_activity = "Processing Messages"
                break
                
        return {
            "current_activity": current_activity,
            "loop_iterations": loop_iterations,
            "last_action_time": last_action_time
        }
    except Exception as e:
        print(f"Error getting system state: {e}")
        return {"current_activity": "Unknown", "loop_iterations": 0}

def get_system_issues():
    """Check for system issues from logs"""
    issues = []
    
    # Check main system log
    try:
        if os.path.exists(SYSTEM_LOG):
            with open(SYSTEM_LOG, 'r') as f:
                lines = f.readlines()[-50:]
                
            for line in lines:
                if "ERROR" in line:
                    # Extract error message
                    error_match = re.search(r'ERROR\s+-\s+(.*)', line)
                    if error_match:
                        issues.append({
                            "type": "error",
                            "message": error_match.group(1),
                            "timestamp": datetime.now().isoformat(),
                            "source": "system"
                        })
                elif "WARNING" in line:
                    warning_match = re.search(r'WARNING\s+-\s+(.*)', line)
                    if warning_match:
                        issues.append({
                            "type": "warning", 
                            "message": warning_match.group(1),
                            "timestamp": datetime.now().isoformat(),
                            "source": "system"
                        })
    except Exception as e:
        issues.append({
            "type": "error",
            "message": f"Could not read system logs: {e}",
            "timestamp": datetime.now().isoformat(),
            "source": "system"
        })
    
    # Check stderr log for errors
    try:
        if os.path.exists(STDERR_LOG):
            with open(STDERR_LOG, 'r') as f:
                lines = f.readlines()[-30:]
                
            for line in lines:
                line = line.strip()
                if line and not line.startswith('#'):  # Skip empty lines and comments
                    # Extract timestamp if present
                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})', line)
                    timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().isoformat()
                    
                    # Common error patterns in stderr
                    if any(keyword in line.lower() for keyword in ['error', 'exception', 'traceback', 'failed', 'critical']):
                        issues.append({
                            "type": "error",
                            "message": line[:100] + "..." if len(line) > 100 else line,
                            "timestamp": timestamp,
                            "source": "stderr"
                        })
                    elif any(keyword in line.lower() for keyword in ['warning', 'warn', 'deprecated']):
                        issues.append({
                            "type": "warning",
                            "message": line[:100] + "..." if len(line) > 100 else line,
                            "timestamp": timestamp,
                            "source": "stderr"
                        })
    except Exception as e:
        issues.append({
            "type": "error",
            "message": f"Could not read stderr logs: {e}",
            "timestamp": datetime.now().isoformat(),
            "source": "stderr"
        })
        
    return issues[-10:]  # Return last 10 issues

@app.route('/api/dashboard')
def get_dashboard_data():
    """API endpoint for real-time dashboard data"""
    persona_state = get_persona_state()
    system_state = get_system_state()
    issues = get_system_issues()
    
    # Get AI name from persona state, fallback to environment variable
    ai_display_name = persona_state.get("name", AI_NAME)
    
    return jsonify({
        "system": {
            "status": "active" if system_state["current_activity"] != "Idle" else "idle",
            "current_activity": system_state["current_activity"],
            "ai_name": ai_display_name,
            "uptime": get_uptime(),
            "completed_tasks": get_completed_tasks_count(),
            "timestamp": datetime.now().isoformat()
        },
        "persona": {
            "name": persona_state.get("name", "Unknown"),
            "traits": persona_state.get("traits", {}),  # Absolute values (0-10 scale)
            "interests_count": len(persona_state.get("interests", [])),  # Absolute count
            "interactions_count": len(persona_state.get("persona_history", [])),  # Absolute count
            "self_awareness": persona_state.get("self_perception", {}).get("self_awareness_level", 0),  # Absolute value
            "identity_strength": persona_state.get("self_perception", {}).get("identity_strength", 0),  # Absolute value
            "metacognition": persona_state.get("self_perception", {}).get("metacognition_depth", 0),  # Absolute value
            "show_absolute_values": True  # Flag to show absolute values instead of percentages for model metrics
        },
        "issues": issues,
        "recent_activities": parse_recent_activities()
    })

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