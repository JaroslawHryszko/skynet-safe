document.addEventListener('DOMContentLoaded', function() {
    // DOM element references
    const statusDot = document.getElementById('status-dot');
    const systemStatus = document.getElementById('system-status');
    const lastUpdate = document.getElementById('last-update');
    const footerTimestamp = document.getElementById('footer-timestamp');
    
    // Current Activity elements
    const activityIcon = document.getElementById('activity-icon');
    const currentActivityText = document.getElementById('current-activity-text');
    const activityDescription = document.getElementById('activity-description');
    
    // Persona elements
    const personaName = document.getElementById('persona-name');
    const selfAwarenessBar = document.getElementById('self-awareness-bar');
    const selfAwarenessText = document.getElementById('self-awareness-text');
    const identityStrengthBar = document.getElementById('identity-strength-bar');
    const identityStrengthText = document.getElementById('identity-strength-text');
    const metacognitionBar = document.getElementById('metacognition-bar');
    const metacognitionText = document.getElementById('metacognition-text');
    const interestsCount = document.getElementById('interests-count');
    const interactionsCount = document.getElementById('interactions-count');
    
    // Other elements
    const issuesList = document.getElementById('issues-list');
    const activitiesTimeline = document.getElementById('activities-timeline');
    const aiName = document.getElementById('ai-name');
    const uptime = document.getElementById('uptime');
    const completedTasks = document.getElementById('completed-tasks');
    
    // Activity icons mapping
    const activityIcons = {
        'Idle': '😴',
        'Periodic Tasks': '⚡',
        'Internet Exploration': '🌐',
        'Initiating Conversation': '💬',
        'Persona Update': '🧠',
        'Self-Reflection': '🤔',
        'External Evaluation': '📊',
        'Processing Messages': '📨',
        'Unknown': '❓'
    };
    
    // Activity descriptions
    const activityDescriptions = {
        'Idle': 'System is waiting for input or tasks',
        'Periodic Tasks': 'Running scheduled system maintenance',
        'Internet Exploration': 'Searching for new information online',
        'Initiating Conversation': 'Starting conversation with users',
        'Persona Update': 'Updating personality and traits',
        'Self-Reflection': 'Analyzing recent interactions',
        'External Evaluation': 'Running external quality assessment',
        'Processing Messages': 'Handling incoming user messages',
        'Unknown': 'Activity status unclear'
    };

    // Initialize dashboard
    refreshDashboard();
    
    // Auto-refresh every 5 seconds
    setInterval(refreshDashboard, 5000);
    
    function refreshDashboard() {
        fetch('/api/dashboard')
            .then(response => response.json())
            .then(data => {
                updateSystemStatus(data.system);
                updatePersonaState(data.persona);
                updateLatestPrompt(data.latest_prompt);
                updateRecentTasks(data.tasks);
                updateRecentActivities(data.recent_activities);
                updateTimestamp();
            })
            .catch(error => {
                console.error('Error fetching dashboard data:', error);
                showConnectionError();
            });
    }
    
    function updateSystemStatus(systemData) {
        // Update status indicator
        if (systemData.status === 'active') {
            statusDot.className = 'status-dot active';
            systemStatus.textContent = 'Active';
        } else {
            statusDot.className = 'status-dot idle';
            systemStatus.textContent = 'Idle';
        }
        
        // Update current activity
        const activity = systemData.current_activity;
        activityIcon.textContent = activityIcons[activity] || activityIcons['Unknown'];
        currentActivityText.textContent = activity;
        activityDescription.textContent = activityDescriptions[activity] || activityDescriptions['Unknown'];
        
        // Update AI name, uptime, and completed tasks
        aiName.textContent = systemData.ai_name;
        if (uptime && systemData.uptime) {
            uptime.textContent = systemData.uptime;
        }
        if (completedTasks && systemData.completed_tasks !== undefined) {
            completedTasks.textContent = systemData.completed_tasks;
        }
    }
    
    function updatePersonaState(personaData) {
        personaName.textContent = personaData.name;
        
        // Update progress bars - show absolute values for model metrics
        if (personaData.show_absolute_values) {
            updateAbsoluteValueBar(selfAwarenessBar, selfAwarenessText, personaData.self_awareness);
            updateAbsoluteValueBar(identityStrengthBar, identityStrengthText, personaData.identity_strength);
            updateAbsoluteValueBar(metacognitionBar, metacognitionText, personaData.metacognition);
        } else {
            updateProgressBar(selfAwarenessBar, selfAwarenessText, personaData.self_awareness);
            updateProgressBar(identityStrengthBar, identityStrengthText, personaData.identity_strength);
            updateProgressBar(metacognitionBar, metacognitionText, personaData.metacognition);
        }
        
        // Update stats
        interestsCount.textContent = personaData.interests_count;
        interactionsCount.textContent = personaData.interactions_count;
    }
    
    function updateProgressBar(barElement, textElement, value, rawValue = null) {
        const percentage = Math.round(value * 100);
        barElement.style.width = percentage + '%';
        
        // Show both percentage and raw value if available
        if (rawValue !== null && rawValue !== value) {
            textElement.textContent = `${percentage}% (${rawValue.toFixed(2)})`;
        } else {
            textElement.textContent = percentage + '%';
        }
        
        // Color coding based on value
        if (percentage >= 80) {
            barElement.className = 'progress-fill high';
        } else if (percentage >= 50) {
            barElement.className = 'progress-fill medium';
        } else {
            barElement.className = 'progress-fill low';
        }
    }
    
    function updateAbsoluteValueBar(barElement, textElement, value) {
        // For absolute values, show the raw number without percentage conversion
        const displayValue = typeof value === 'number' ? value.toFixed(2) : value;
        textElement.textContent = displayValue;
        
        // For visual bar, normalize to a reasonable scale (0-10 range)
        const normalizedPercentage = Math.min(Math.max((value / 10) * 100, 0), 100);
        barElement.style.width = normalizedPercentage + '%';
        
        // Color coding based on absolute value ranges
        if (value >= 7) {
            barElement.className = 'progress-fill high';
        } else if (value >= 4) {
            barElement.className = 'progress-fill medium';
        } else {
            barElement.className = 'progress-fill low';
        }
    }
    
    function updateLatestPrompt(prompt) {
        const promptContent = document.getElementById('prompt-content');
        if (!promptContent) return;

        if (!prompt) {
            promptContent.innerHTML = '<div class="no-data">📝 No recent prompt available</div>';
            return;
        }

        // Display the prompt content with proper formatting
        promptContent.textContent = prompt;
    }
    
    function updateRecentTasks(tasks) {
        if (!tasks || tasks.length === 0) {
            issuesList.innerHTML = '<div class="no-tasks">📝 No recent tasks</div>';
            return;
        }
        
        let tasksHTML = '';
        tasks.forEach(task => {
            const iconMap = {
                'completed': '✅',
                'running': '🔄',
                'pending': '⏳',
                'error': '❌'
            };
            
            tasksHTML += `
                <div class="task-item ${task.type}">
                    <span class="task-icon">${iconMap[task.type] || '📝'}</span>
                    <div class="task-content">
                        <div class="task-description">${task.description}</div>
                        <div class="task-meta">
                            <span class="task-status">${task.status}</span>
                            <span class="task-time">${task.timestamp}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        
        issuesList.innerHTML = tasksHTML;
    }
    
    function updateRecentActivities(activities) {
        if (!activities || activities.length === 0) {
            activitiesTimeline.innerHTML = '<div class="loading">No recent activities</div>';
            return;
        }
        
        let activitiesHTML = '';
        activities.forEach(activity => {
            // Use time_display if available, otherwise format timestamp
            const timeDisplay = activity.time_display || formatTime(activity.timestamp) || 'Unknown';
            const activityText = activity.summary || activity.activity || 'Unknown activity';
            
            // Check if this is a log entry with ID (clickable)
            if (activity.id) {
                activitiesHTML += `
                    <div class="timeline-item clickable-log" onclick="openLogDetail('${activity.id}')" title="Click to view full log details">
                        <div class="timeline-time">${timeDisplay}</div>
                        <div class="timeline-content">
                            <span class="log-summary">${activityText}</span>
                            <span class="log-level level-${(activity.level || 'info').toLowerCase()}">${activity.level || 'INFO'}</span>
                        </div>
                    </div>
                `;
            } else {
                // Regular activity (non-clickable)
                activitiesHTML += `
                    <div class="timeline-item">
                        <div class="timeline-time">${timeDisplay}</div>
                        <div class="timeline-content">${activityText}</div>
                    </div>
                `;
            }
        });
        
        activitiesTimeline.innerHTML = activitiesHTML;
    }
    
    function updateTimestamp() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        lastUpdate.textContent = timeString;
        footerTimestamp.textContent = timeString;
    }
    
    function formatTime(timestamp) {
        if (!timestamp) {
            return 'Unknown';
        }
        try {
            const date = new Date(timestamp);
            if (isNaN(date.getTime())) {
                return 'Invalid Date';
            }
            return date.toLocaleTimeString();
        } catch (e) {
            return 'Invalid Date';
        }
    }
    
    function showConnectionError() {
        statusDot.className = 'status-dot error';
        systemStatus.textContent = 'Connection Error';
        currentActivityText.textContent = 'Cannot connect to system';
        activityDescription.textContent = 'Please check if SKYNET-SAFE is running';
        activityIcon.textContent = '⚠️';
    }
    
    // Global function for opening log details
    window.openLogDetail = function(logId) {
        // Open log detail page in the same window
        window.location.href = `/log/${logId}`;
    };
});