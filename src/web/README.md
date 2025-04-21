# SKYNET-SAFE Activity Monitor

A simple web interface for monitoring SKYNET-SAFE activities. This interface provides minimal, useful information about the AI's current activities without overwhelming the user with too much detail.

## Features

- View current AI activity at a glance
- See recent system activities and AI interactions
- Click on interactions to view detailed prompt-response pairs
- Minimal interface that focuses on useful information
- Updates automatically every 10 seconds

## Setup

1. Make sure you have installed all the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Ensure your `.env` file includes:
   ```
   LOG_DIR="/path/to/logs"
   AI_NAME="YourAIName"
   WEB_PORT=5000
   ```

## Usage

Run the monitor:

```
python src/web/run_monitor.py
```

Then open your browser to `http://localhost:5000`

## Customization

You can customize the look and feel by modifying:
- CSS: `static/css/style.css`
- HTML: `templates/index.html`
- JavaScript: `static/js/monitor.js`

## Implementation Details

The monitor works by:
1. Reading system and interaction logs from the configured LOG_DIR
2. Parsing these logs to extract useful information
3. Exposing this information via a simple API
4. Displaying the information in a clean, minimal web interface

The interface is designed to be non-intrusive and only reads information from logs without affecting the core functionality of SKYNET-SAFE.