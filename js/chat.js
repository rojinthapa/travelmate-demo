document.addEventListener('DOMContentLoaded', function() {
    // DOM elements
    const chatMessages = document.querySelector('.chat-messages');
    const messageInput = document.getElementById('message-input');
    const sendButton = document.getElementById('send-button');
    const micButton = document.getElementById('mic-button');
    const actionButtons = document.querySelectorAll('.action-button');
    
    // Get API URL dynamically (works on both localhost and Render)
    const API_URL = window.location.origin + '/api/chat';
    
    // Clear any existing messages
    chatMessages.innerHTML = '';
    
    // Display welcome message
    displayMessage("Hello! I'm TravelMate, your AI travel companion. How can I help you today?", 'bot');
    
    // Event listeners
    sendButton.addEventListener('click', sendMessage);
    
    messageInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            sendMessage();
        }
    });

    // Voice message event listener
    document.addEventListener('voiceMessageReady', function(e) {
        if (e.detail && e.detail.message) {
            messageInput.value = e.detail.message;
            sendMessage();
        }
    });
    
    // Quick action button listeners
    actionButtons.forEach(button => {
        button.addEventListener('click', function() {
            const action = this.textContent.trim();
            let message = '';
            
            switch(action) {
                case 'Restaurants':
                    message = "Find me restaurants";
                    break;
                case 'Hotels':
                    message = "Find me hotels";
                    break;
                case 'Attractions':
                    message = "Find me attractions";
                    break;
            }
            
            if (message) {
                messageInput.value = message;
                sendMessage();
            }
        });
    });

    // Store user location
    let userCity = "your current location";
    
    // Try to get user location on page load
    getUserLocation();

    function getUserLocation() {
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                function(position) {
                    console.log("Location obtained:", position.coords.latitude, position.coords.longitude);
                    
                    fetch('https://ipapi.co/json/')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error('IP API error');
                            }
                            return response.json();
                        })
                        .then(data => {
                            userCity = data.city || "your current location";
                            console.log("City detected:", userCity);
                        })
                        .catch(error => {
                            console.warn("Error getting city from IP:", error);
                        });
                },
                function(error) {
                    console.warn("Geolocation error:", error.message);
                },
                { timeout: 10000, maximumAge: 600000 }
            );
        } else {
            console.warn("Geolocation is not supported by this browser");
        }
    }

    async function sendMessage() {
        let message = messageInput.value.trim();
        if (message) {
            displayMessage(message, 'user');
            
            // Handle "near me" queries
            if (/\b(nearby|near me)\b/gi.test(message)) {
                message = message.replace(/\b(nearby|near me)\b/gi, `in ${userCity}`);
                console.log("Message with location replaced:", message);
            }
            
            await handleResponse(message);
            messageInput.value = '';
        }
    }

    async function handleResponse(message) {
        try {
            // Show typing indicator
            const typingIndicator = document.createElement('div');
            typingIndicator.className = 'message bot-message typing';
            typingIndicator.innerHTML = '<div class="typing-indicator"><span></span><span></span><span></span></div>';
            chatMessages.appendChild(typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;

            // Make API call to backend
            const response = await fetch(API_URL, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    timestamp: new Date().toISOString()
                })
            });

            // Remove typing indicator
            typingIndicator.remove();

            if (!response.ok) {
                throw new Error('Network response was not ok');
            }

            const data = await response.json();
            displayMessage(data.response, 'bot');

        } catch (error) {
            console.error('Error:', error);
            const typingIndicator = document.querySelector('.typing');
            if (typingIndicator) {
                typingIndicator.remove();
            }
            displayMessage("I apologize, but I'm having trouble connecting to the server. Please try again in a moment.", 'bot');
        }
    }

    function displayMessage(message, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;

        const avatar = document.createElement('div');
        avatar.className = 'avatar';
        avatar.innerHTML = type === 'bot' ? '🤖' : '👤';

        const messageWrapper = document.createElement('div');
        messageWrapper.className = 'message-wrapper';

        const content = document.createElement('div');
        content.className = 'content';
        content.textContent = message;

        const timestamp = document.createElement('div');
        timestamp.className = 'timestamp';
        timestamp.textContent = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        messageWrapper.appendChild(content);
        messageWrapper.appendChild(timestamp);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageWrapper);

        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        // If it's a bot message and voice is enabled, speak it
        if (type === 'bot' && window.voiceHandler && window.voiceHandler.voiceEnabled) {
            window.voiceHandler.speak(message);
        }
    }
});
