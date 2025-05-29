from flask import Flask, render_template, jsonify
import os
import re
import time
import math
from datetime import datetime
import json
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

LOG_DIR = os.getenv("LOG_DIR", "./logs")
INTERACTION_LOG = os.path.join(LOG_DIR, "llm_interactions.log")
SYSTEM_LOG = os.path.join(LOG_DIR, "skynet.log")
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
    """Parse logs for the six most recent activities with proper JSON parsing and clickable entries"""
    activities = []
    
    # Parse llm_interactions.log for interaction entries first
    if os.path.exists(INTERACTION_LOG):
        try:
            with open(INTERACTION_LOG, 'r') as f:
                lines = f.readlines()[-50:]  # Check last 50 lines for interaction data
                
                for line in lines:
                    try:
                        # Try to parse JSON log entry
                        if '{' in line and '}' in line:
                            json_part = line[line.find('{'):line.rfind('}')+1]
                            log_data = json.loads(json_part)
                            
                            if 'timestamp' in log_data:
                                timestamp_str = log_data['timestamp']
                                
                                # Parse ISO timestamp
                                try:
                                    if 'T' in timestamp_str:
                                        dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                                    else:
                                        dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    
                                    time_str = dt.strftime('%H:%M')
                                    
                                    # Create log ID for clickable entry
                                    log_id = f"{dt.strftime('%Y%m%d_%H%M%S')}_{dt.microsecond//1000:03d}"
                                    
                                    # Extract query/prompt for summary
                                    summary = ""
                                    if 'query' in log_data:
                                        query = log_data['query']
                                        if len(query) > 60:
                                            summary = f"Query: {query[:57]}..."
                                        else:
                                            summary = f"Query: {query}"
                                    elif 'prompt' in log_data:
                                        prompt = log_data['prompt']
                                        if len(prompt) > 60:
                                            summary = f"Prompt: {prompt[:57]}..."
                                        else:
                                            summary = f"Prompt: {prompt}"
                                    else:
                                        summary = "LLM Interaction"
                                    
                                    # Determine log level
                                    level = log_data.get('level', 'INFO')
                                    
                                    activities.append({
                                        "id": log_id,  # This makes it clickable
                                        "timestamp": timestamp_str,
                                        "time_display": time_str,
                                        "summary": summary,
                                        "activity": summary,  # For backward compatibility
                                        "level": level,
                                        "type": "interaction",
                                        "sort_time": dt
                                    })
                                    
                                except Exception as e:
                                    print(f"Error parsing JSON timestamp {timestamp_str}: {e}")
                                    continue
                    except json.JSONDecodeError:
                        # Try regex parsing for non-JSON log entries
                        match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+.*?(?:INFO|ERROR|WARNING|DEBUG)\s+-\s+(.*)', line)
                        if match:
                            timestamp_str = match.group(1)
                            message = match.group(2).strip()
                            
                            try:
                                if ',' in timestamp_str:
                                    dt = datetime.strptime(timestamp_str.split(',')[0], '%Y-%m-%d %H:%M:%S')
                                    milliseconds = timestamp_str.split(',')[1][:3]
                                else:
                                    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    milliseconds = "000"
                                
                                time_str = dt.strftime('%H:%M')
                                log_id = f"{dt.strftime('%Y%m%d_%H%M%S')}_{milliseconds}"
                                
                                # Extract level from message if possible
                                level_match = re.search(r'(INFO|ERROR|WARNING|DEBUG)', line)
                                level = level_match.group(1) if level_match else 'INFO'
                                
                                display_message = message
                                if len(display_message) > 60:
                                    display_message = display_message[:57] + '...'
                                
                                activities.append({
                                    "id": log_id,  # This makes it clickable
                                    "timestamp": timestamp_str,
                                    "time_display": time_str,
                                    "summary": display_message,
                                    "activity": display_message,
                                    "level": level,
                                    "type": "interaction",
                                    "sort_time": dt
                                })
                            except Exception as e:
                                print(f"Error parsing regex timestamp {timestamp_str}: {e}")
                                continue
                        continue
                                
        except Exception as e:
            print(f"Error parsing interaction log for activities: {e}")
    
    # Parse skynet.log for system activities (non-clickable)
    if os.path.exists(SYSTEM_LOG):
        try:
            with open(SYSTEM_LOG, 'r') as f:
                lines = f.readlines()[-50:]  # Check last 50 lines for system data
                
                for line in lines:
                    # Extract timestamp and message - support multiple log formats
                    match = re.search(r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:,\d+)?)\s+.*?(?:INFO|ERROR|WARNING|DEBUG)\s+-\s+(.*)', line)
                    if not match:
                        match = re.search(r'\[(.*?)\].*?(?:INFO|ERROR|WARNING|DEBUG)\s+-\s+(.*)', line)
                    
                    if match:
                        timestamp_str = match.group(1)
                        message = match.group(2).strip()
                        
                        # Skip empty messages
                        if not message:
                            continue
                        
                        try:
                            # Parse timestamp
                            if ',' in timestamp_str:
                                dt = datetime.strptime(timestamp_str.split(',')[0], '%Y-%m-%d %H:%M:%S')
                            else:
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            
                            time_str = dt.strftime('%H:%M')
                            
                            # Extract level from line
                            level_match = re.search(r'(INFO|ERROR|WARNING|DEBUG)', line)
                            level = level_match.group(1) if level_match else 'INFO'
                            
                            # Determine activity type based on message content
                            activity_type = "system"
                            if any(keyword in message.lower() for keyword in ["query", "user", "telegram", "signal"]):
                                activity_type = "interaction"
                            elif any(keyword in message.lower() for keyword in ["error", "exception", "failed"]):
                                activity_type = "error"
                            elif any(keyword in message.lower() for keyword in ["warning", "warn"]):
                                activity_type = "warning"
                            
                            # Shorten long messages for display
                            display_message = message
                            if len(display_message) > 60:
                                display_message = display_message[:57] + '...'
                            
                            # No ID for system log entries (non-clickable)
                            activities.append({
                                "timestamp": timestamp_str,
                                "time_display": time_str,
                                "summary": display_message,
                                "activity": display_message,
                                "level": level,
                                "type": activity_type,
                                "sort_time": dt
                            })
                            
                        except Exception as e:
                            print(f"Error parsing timestamp {timestamp_str}: {e}")
                            continue
                                
        except Exception as e:
            print(f"Error parsing system log for activities: {e}")
    
    # Sort by timestamp and return last 6
    try:
        activities.sort(key=lambda x: x.get('sort_time', datetime.min), reverse=True)
    except Exception as e:
        print(f"Error sorting activities: {e}")
    
    # Remove sort_time before returning
    for activity in activities:
        activity.pop('sort_time', None)
    
    return activities[:6]

def parse_log_entry(log_line):
    """Parse a single log entry and extract structured information"""
    # Parse log line format: TIMESTAMP - LEVEL - MESSAGE
    match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}),(\d+) - ([^-]+) - (.+)', log_line.strip())
    if not match:
        return None
        
    timestamp_str, milliseconds, level, message = match.groups()
    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    
    # Create a unique ID for this log entry
    log_id = f"{timestamp.strftime('%Y%m%d_%H%M%S')}_{milliseconds}"
    
    # Extract summary from message (first 80 characters or until first newline)
    summary = message.split('\n')[0]
    if len(summary) > 80:
        summary = summary[:77] + '...'
    
    return {
        'id': log_id,
        'timestamp': timestamp,
        'time_str': timestamp.strftime('%H:%M:%S'),
        'level': level.strip(),
        'summary': summary,
        'full_message': message
    }

def get_recent_interactions():
    """Get recent LLM interactions from logs"""
    interactions = []
    
    if not os.path.exists(INTERACTION_LOG):
        return interactions
    
    try:
        with open(INTERACTION_LOG, 'r') as f:
            lines = f.readlines()[-20:]  # Get last 20 interactions
            
        for line in lines:
            parsed = parse_log_entry(line)
            if parsed:
                interactions.append({
                    'id': parsed['id'],
                    'time': parsed['time_str'],
                    'summary': parsed['summary'],
                    'level': parsed['level']
                })
    except Exception as e:
        print(f"Error reading interaction log: {e}")
    
    return list(reversed(interactions))

def get_log_entry_by_id(log_id):
    """Get detailed log entry by ID - supports both JSON and regular log entries"""
    if not os.path.exists(INTERACTION_LOG):
        return None
        
    try:
        with open(INTERACTION_LOG, 'r') as f:
            lines = f.readlines()
            
        for line in lines:
            try:
                # First try JSON parsing
                if '{' in line and '}' in line:
                    json_part = line[line.find('{'):line.rfind('}')+1]
                    log_data = json.loads(json_part)
                    
                    if 'timestamp' in log_data:
                        timestamp_str = log_data['timestamp']
                        
                        # Parse ISO timestamp
                        try:
                            if 'T' in timestamp_str:
                                dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            else:
                                dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                            
                            # Create log ID
                            entry_log_id = f"{dt.strftime('%Y%m%d_%H%M%S')}_{dt.microsecond//1000:03d}"
                            
                            if entry_log_id == log_id:
                                # Format full message from JSON data
                                full_message = json.dumps(log_data, indent=2, ensure_ascii=False)
                                
                                return {
                                    'id': entry_log_id,
                                    'timestamp': dt,
                                    'time_str': dt.strftime('%H:%M:%S'),
                                    'level': log_data.get('level', 'INFO'),
                                    'summary': f"LLM Interaction: {log_data.get('query', log_data.get('prompt', 'N/A'))[:60]}...",
                                    'full_message': full_message
                                }
                        except Exception as e:
                            print(f"Error parsing JSON timestamp for ID matching: {e}")
                            continue
            except json.JSONDecodeError:
                # Fallback to regex parsing for regular log entries
                parsed = parse_log_entry(line)
                if parsed and parsed['id'] == log_id:
                    return parsed
                continue
                    
    except Exception as e:
        print(f"Error reading log entry: {e}")
    
    return None

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

def get_current_task():
    """Read current task from current_task.tmp file"""
    current_task_file = os.path.join(LOG_DIR, "current_task.tmp")
    try:
        if os.path.exists(current_task_file):
            with open(current_task_file, 'r', encoding='utf-8') as f:
                task = f.read().strip()
                if task:
                    return task
    except Exception as e:
        print(f"Error reading current task file: {e}")
    return None

def get_system_state():
    """Parse logs to determine current system state"""
    try:
        loop_iterations = 0
        last_action_time = None
        
        # First try to get current task from file
        current_task = get_current_task()
        if current_task:
            current_activity = current_task
        else:
            # Fallback to log parsing
            with open(SYSTEM_LOG, 'r') as f:
                lines = f.readlines()[-20:]  # Check last 20 lines
                
            current_activity = "Idle"
            
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

def get_recent_tasks():
    """Get recent completed tasks from tasks.log file - only showing completed tasks with time only"""
    tasks = []
    tasks_file = os.path.join(LOG_DIR, "tasks.log")
    
    try:
        if os.path.exists(tasks_file):
            with open(tasks_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-50:]  # Check more lines to find completed tasks
                
            completed_tasks = []
            
            for line in lines:
                line = line.strip()
                if line:
                    # Parse task line format - handle both old and new formats
                    # Old format: TIMESTAMP - STATUS - TASK_DESCRIPTION
                    # New format: ISO_TIMESTAMP - STATUS: TASK_DESCRIPTION
                    
                    # Try new ISO format first
                    iso_match = re.match(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+) - ([^:]+): (.+)', line)
                    if iso_match:
                        timestamp_str, status, description = iso_match.groups()
                        
                        # Only include completed tasks
                        if status.strip().lower() in ["completed", "done", "finished"]:
                            try:
                                # Parse ISO timestamp
                                timestamp = datetime.fromisoformat(timestamp_str.replace('T', ' ').split('.')[0])
                                
                                completed_tasks.append({
                                    "status": status.strip(),
                                    "description": description.strip(),
                                    "timestamp": timestamp.strftime('%H:%M'),  # Only show time, not seconds
                                    "type": "completed",
                                    "full_timestamp": timestamp_str,
                                    "sort_time": timestamp  # For sorting
                                })
                            except Exception as e:
                                print(f"Error parsing ISO task timestamp {timestamp_str}: {e}")
                                continue
                    else:
                        # Try old format
                        old_match = re.match(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([^-]+) - (.+)', line)
                        if old_match:
                            timestamp_str, status, description = old_match.groups()
                            
                            # Only include completed tasks
                            if status.strip().lower() in ["completed", "done", "finished"]:
                                try:
                                    timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                                    
                                    completed_tasks.append({
                                        "status": status.strip(),
                                        "description": description.strip(),
                                        "timestamp": timestamp.strftime('%H:%M'),  # Only show time, not seconds
                                        "type": "completed",
                                        "full_timestamp": timestamp_str,
                                        "sort_time": timestamp  # For sorting
                                    })
                                except Exception as e:
                                    print(f"Error parsing old task timestamp {timestamp_str}: {e}")
                                    continue
            
            # Sort by timestamp and take the most recent 6 completed tasks
            completed_tasks.sort(key=lambda x: x.get('sort_time', datetime.min), reverse=True)
            tasks = completed_tasks[:6]
            
            # Remove sort_time before returning
            for task in tasks:
                task.pop('sort_time', None)
                
    except Exception as e:
        print(f"Error reading tasks file: {e}")
        # Don't add error tasks to the list - just return empty if there's an issue
        
    return tasks

@app.route('/api/dashboard')
def get_dashboard_data():
    """API endpoint for real-time dashboard data"""
    persona_state = get_persona_state()
    system_state = get_system_state()
    tasks = get_recent_tasks()
    
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
        "tasks": tasks,
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

@app.route('/log/<log_id>')
def show_log_entry(log_id):
    """Show detailed view of a specific log entry"""
    log_entry = get_log_entry_by_id(log_id)
    if not log_entry:
        return "Log entry not found", 404
        
    return render_template('log_detail.html', 
                         log_entry=log_entry,
                         ai_name=AI_NAME)

@app.route('/api/log/<log_id>')
def get_log_entry_api(log_id):
    """Get detailed log entry as JSON"""
    log_entry = get_log_entry_by_id(log_id)
    if not log_entry:
        return jsonify({"error": "Log entry not found"}), 404
        
    return jsonify(log_entry)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs(os.path.join(os.path.dirname(__file__), 'templates'), exist_ok=True)
    
    # Import config here to avoid circular imports
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from config import config
    
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