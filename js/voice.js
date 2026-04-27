class VoiceHandler {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.voiceEnabled = false;
        
        // DOM elements
        this.micButton = document.getElementById('mic-button');
        this.voiceFeedback = document.getElementById('voice-feedback');
        this.voiceToggle = document.getElementById('voice-toggle-checkbox');
        
        console.log('VoiceHandler initialized');
        this.initSpeechRecognition();
        this.setupEventListeners();
        
        // Display voice input availability message
        this.displayVoiceInputMessage();
    }
    
    displayVoiceInputMessage() {
        const chatMessages = document.getElementById('chat-messages');
        if (chatMessages) {
            const messageElement = document.createElement('div');
            messageElement.className = 'message bot-message';
            messageElement.innerHTML = `
                <div class="message-content">
                    <p>Voice input is now available! Click the microphone button to start speaking.</p>
                    <span class="message-time">${this.getCurrentTime()}</span>
                </div>
            `;
            chatMessages.appendChild(messageElement);
        }
    }
    
    getCurrentTime() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }
    
    initSpeechRecognition() {
        // Check for browser support
        if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
            console.error('Speech recognition not supported in this browser');
            this.micButton.style.display = 'none';
            return;
        }
        
        try {
            // Initialize speech recognition
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            this.recognition = new SpeechRecognition();
            this.recognition.continuous = false;
            this.recognition.interimResults = false;
            this.recognition.lang = 'en-US'; // Set language
            
            console.log('Speech recognition initialized');
            
            // Setup recognition events
            this.recognition.onstart = () => {
                console.log('Speech recognition started');
                this.isListening = true;
                this.showListeningFeedback();
            };
            
            this.recognition.onend = () => {
                console.log('Speech recognition ended');
                this.isListening = false;
                this.hideListeningFeedback();
            };
            
            this.recognition.onresult = (event) => {
                console.log('Speech recognition result:', event);
                if (event.results && event.results[0] && event.results[0][0]) {
                    const transcript = event.results[0][0].transcript;
                    console.log('Transcribed text:', transcript);
                    
                    const messageInput = document.getElementById('message-input');
                    if (messageInput) {
                        messageInput.value = transcript;
                        this.hideListeningFeedback();
                        
                        // Small delay before sending to allow user to see what was transcribed
                        setTimeout(() => {
                            document.dispatchEvent(new CustomEvent('voiceMessageReady', {
                                detail: { message: transcript }
                            }));
                        }, 500);
                    } else {
                        console.error('Message input element not found');
                    }
                } else {
                    console.error('No speech results found');
                }
            };
            
            this.recognition.onerror = (event) => {
                console.error('Speech recognition error:', event.error);
                this.isListening = false;
                this.hideListeningFeedback();
                
                // Show error message to user
                let errorMessage = 'An error occurred with speech recognition. ';
                switch(event.error) {
                    case 'no-speech':
                        errorMessage = 'No speech was detected. Try again.';
                        break;
                    case 'audio-capture':
                        errorMessage = 'No microphone was found. Ensure that a microphone is installed.';
                        break;
                    case 'not-allowed':
                        errorMessage = 'Permission to use microphone was denied. Please allow microphone access.';
                        break;
                    case 'aborted':
                        errorMessage = 'Speech recognition was aborted.';
                        break;
                    case 'network':
                        errorMessage = 'Network error occurred during speech recognition.';
                        break;
                    default:
                        errorMessage += `Error: ${event.error}`;
                }
                
                alert(errorMessage);
            };
            
        } catch (error) {
            console.error('Error initializing speech recognition:', error);
            this.micButton.style.display = 'none';
            alert('Failed to initialize speech recognition. Please try a different browser.');
        }
    }
    
    setupEventListeners() {
        // Mic button click
        if (this.micButton) {
            this.micButton.addEventListener('click', () => {
                console.log('Mic button clicked, isListening:', this.isListening);
                if (this.isListening) {
                    this.stopListening();
                } else {
                    this.startListening();
                }
            });
        } else {
            console.error('Mic button element not found');
        }
        
        // Voice toggle
        if (this.voiceToggle) {
            this.voiceToggle.addEventListener('change', (e) => {
                this.voiceEnabled = e.target.checked;
                console.log('Voice responses enabled:', this.voiceEnabled);
                
                // Save preference
                localStorage.setItem('voiceEnabled', this.voiceEnabled);
                
                // If turned on, do a test speak
                if (this.voiceEnabled) {
                    this.speak('Voice responses enabled.');
                }
            });
            
            // Load saved preference
            const savedVoicePreference = localStorage.getItem('voiceEnabled');
            if (savedVoicePreference !== null) {
                this.voiceEnabled = savedVoicePreference === 'true';
                this.voiceToggle.checked = this.voiceEnabled;
            }
        } else {
            console.error('Voice toggle element not found');
        }
    }
    
    startListening() {
        if (this.recognition) {
            try {
                console.log('Starting speech recognition');
                this.recognition.start();
            } catch (error) {
                console.error('Error starting speech recognition:', error);
                alert('Error starting speech recognition. Please try again.');
            }
        } else {
            console.error('Speech recognition not initialized');
            alert('Speech recognition not initialized. Please refresh the page.');
        }
    }
    
    stopListening() {
        if (this.recognition) {
            console.log('Stopping speech recognition');
            this.recognition.stop();
        }
    }
    
    showListeningFeedback() {
        if (this.voiceFeedback) {
            this.voiceFeedback.classList.remove('hidden');
            this.micButton.classList.add('active');
            console.log('Showing listening feedback');
        } else {
            console.error('Voice feedback element not found');
        }
    }
    
    hideListeningFeedback() {
        if (this.voiceFeedback) {
            this.voiceFeedback.classList.add('hidden');
            this.micButton.classList.remove('active');
            console.log('Hiding listening feedback');
        }
    }
    
    speak(text) {
        if (this.voiceEnabled && this.synthesis) {
            try {
                // Cancel any ongoing speech
                this.synthesis.cancel();
                
                // Create new utterance
                const utterance = new SpeechSynthesisUtterance(text);
                
                // Set voice properties
                utterance.rate = 1.0;  // Normal speed
                utterance.pitch = 1.0; // Normal pitch
                utterance.volume = 1.0; // Full volume
                
                // Get available voices and select a female voice if available
                const voices = this.synthesis.getVoices();
                const femaleVoice = voices.find(voice => 
                    voice.name.includes('Female') || 
                    voice.name.includes('female') ||
                    voice.name.includes('Samantha')
                );
                
                if (femaleVoice) {
                    utterance.voice = femaleVoice;
                }
                
                // Speak
                this.synthesis.speak(utterance);
                console.log('Speaking:', text);
            } catch (error) {
                console.error('Error in text-to-speech:', error);
            }
        }
    }
}

// Initialize voice handler when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing VoiceHandler');
    window.voiceHandler = new VoiceHandler();
}); 
