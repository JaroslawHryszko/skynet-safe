document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const statusText = document.getElementById('status-text');
    const currentActivityContent = document.getElementById('current-activity-content');
    const recentActivitiesList = document.getElementById('recent-activities-list');
    const interactionDetails = document.getElementById('interaction-details');
    const promptContent = document.getElementById('prompt-content');
    const responseContent = document.getElementById('response-content');
    const closeDetailsBtn = document.getElementById('close-details');
    
    // Close interaction details
    closeDetailsBtn.addEventListener('click', function() {
        interactionDetails.classList.add('hidden');
    });
    
    // Initial load
    refreshData();
    
    // Refresh data every 10 seconds
    setInterval(refreshData, 10000);
    
    function refreshData() {
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                updateStatus(data);
                updateCurrentActivity(data);
                return fetch('/api/activities');
            })
            .then(response => response.json())
            .then(activities => {
                updateRecentActivities(activities);
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                statusText.textContent = 'Error connecting to server';
                statusText.style.color = 'var(--danger-color)';
            });
    }
    
    function updateStatus(data) {
        if (data.last_activity || data.last_interaction) {
            statusText.textContent = 'Active';
            statusText.style.color = 'var(--success-color)';
        } else {
            statusText.textContent = 'Idle';
            statusText.style.color = 'var(--accent-color)';
        }
    }
    
    function updateCurrentActivity(data) {
        if (data.recent_events && data.recent_events.length > 0) {
            const latestEvent = data.recent_events[0];
            
            let activityHTML = `
                <div class="activity-item ${latestEvent.type}">
                    <span class="timestamp">${latestEvent.timestamp}</span>
                    <p>${latestEvent.type === 'interaction' ? 'Interaction' : latestEvent.activity}</p>
                </div>
            `;
            
            currentActivityContent.innerHTML = activityHTML;
            
            // Add click handler for interaction details
            if (latestEvent.type === 'interaction') {
                const activityItem = currentActivityContent.querySelector('.activity-item');
                activityItem.addEventListener('click', function() {
                    showInteractionDetails(latestEvent);
                });
            }
        } else {
            currentActivityContent.innerHTML = '<p class="loading">No recent activity</p>';
        }
    }
    
    function updateRecentActivities(activities) {
        if (activities.length > 0) {
            let activitiesHTML = '';
            
            activities.forEach(activity => {
                activitiesHTML += `
                    <div class="activity-item ${activity.type}">
                        <span class="timestamp">${activity.timestamp}</span>
                        <p>${activity.activity}</p>
                    </div>
                `;
            });
            
            recentActivitiesList.innerHTML = activitiesHTML;
        } else {
            recentActivitiesList.innerHTML = '<p class="loading">No activities to display</p>';
        }
        
        // Also fetch and handle interactions
        fetch('/api/interactions')
            .then(response => response.json())
            .then(interactions => {
                updateInteractions(interactions);
            });
    }
    
    function updateInteractions(interactions) {
        // Get AI name from status first
        let aiName = "AI";
        fetch('/api/status')
            .then(response => response.json())
            .then(data => {
                aiName = data.ai_name || "AI";
                displayInteractions(interactions, aiName);
            })
            .catch(error => {
                console.error('Error fetching AI name:', error);
                displayInteractions(interactions, aiName);
            });
            
        function displayInteractions(interactions, aiName) {
            if (interactions.length > 0) {
                const activityItems = document.querySelectorAll('.activity-item.interaction');
                
                // Remove existing interaction items first
                activityItems.forEach(item => {
                    if (item.parentNode === recentActivitiesList) {
                        recentActivitiesList.removeChild(item);
                    }
                });
                
                // Add new interaction items
                interactions.forEach(interaction => {
                    const interactionEl = document.createElement('div');
                    interactionEl.className = 'activity-item interaction';
                    interactionEl.innerHTML = `
                        <span class="timestamp">${interaction.timestamp}</span>
                        <p>${aiName} Interaction</p>
                    `;
                    
                    // Add click handler
                    interactionEl.addEventListener('click', function() {
                        showInteractionDetails(interaction);
                    });
                    
                    recentActivitiesList.appendChild(interactionEl);
                });
            }
        }
    }
    
    function showInteractionDetails(interaction) {
        promptContent.textContent = interaction.prompt || 'No prompt available';
        responseContent.textContent = interaction.response || 'No response available';
        interactionDetails.classList.remove('hidden');
    }
});