// ChatGPT-Style Interface JavaScript

// Auto-resize textarea
function autoResize(textarea) {
    textarea.style.height = 'auto';
    textarea.style.height = (textarea.scrollHeight) + 'px';
}

// Send message function
async function sendMessage(event) {
    event.preventDefault();
    const input = document.getElementById('userInput');
    const message = input.value.trim();
    
    if (message) {
        // Add user message to chat
        addMessageToChat(message, 'user');
        
        // Clear input
        input.value = '';
        autoResize(input);
        
        // Show typing indicator
        showTypingIndicator();
        
        try {
            // Get API key from localStorage or use default
            const apiKey = localStorage.getItem('openrouterApiKey') || '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';
            
            // Send request to backend to generate Manim code
            const response = await fetch('/api/openrouter/generate-code', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    input: message,
                    api_key: apiKey
                })
            });
            
            const data = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator();
            
            if (response.ok && data.manimCode) {
                // Add AI response with generated code
                addMessageToChat("I've generated an educational visualization for you. Here's what I'm creating...", 'assistant');
                
                // Show loading indicator while generating video
                showVideoLoading();
                
                // Execute the generated Manim code
                const executeResponse = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        script: data.manimCode
                    })
                });
                
                const executeData = await executeResponse.json();
                
                if (executeResponse.ok && executeData.video_url) {
                    // Update the last assistant message with the video
                    updateLastAssistantMessageWithVideo(executeData.video_url);
                } else {
                    // Show error message
                    updateLastAssistantMessageWithError(executeData.error || 'Failed to generate visualization');
                }
            } else {
                // Remove typing indicator
                removeTypingIndicator();
                
                // Show error message
                addMessageToChat(`Error: ${data.error || 'Failed to generate response'}`, 'assistant');
            }
        } catch (error) {
            // Remove typing indicator
            removeTypingIndicator();
            
            // Show error message
            addMessageToChat(`Error: ${error.message}`, 'assistant');
        }
    }
}

// Add message to chat
function addMessageToChat(content, sender) {
    const chatMessages = document.querySelector('.chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}-message`;
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    avatarDiv.innerHTML = `<i class="fas fa-${sender === 'user' ? 'user' : 'robot'}"></i>`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = content;
    
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    return messageDiv;
}

// Show typing indicator
function showTypingIndicator() {
    const chatMessages = document.querySelector('.chat-messages');
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant-message';
    messageDiv.id = 'typing-indicator';
    
    const avatarDiv = document.createElement('div');
    avatarDiv.className = 'avatar';
    avatarDiv.innerHTML = `<i class="fas fa-robot"></i>`;
    
    const contentDiv = document.createElement('div');
    contentDiv.className = 'message-content';
    
    const textDiv = document.createElement('div');
    textDiv.className = 'message-text';
    textDiv.textContent = 'EduVis Pro is thinking...';
    
    contentDiv.appendChild(textDiv);
    messageDiv.appendChild(avatarDiv);
    messageDiv.appendChild(contentDiv);
    
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Remove typing indicator
function removeTypingIndicator() {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
}

// Show video loading indicator
function showVideoLoading() {
    const chatMessages = document.querySelector('.chat-messages');
    const messages = chatMessages.querySelectorAll('.message');
    const lastMessage = messages[messages.length - 1];
    
    if (lastMessage && lastMessage.classList.contains('assistant-message')) {
        const contentDiv = lastMessage.querySelector('.message-content');
        if (contentDiv) {
            const videoContainer = document.createElement('div');
            videoContainer.className = 'video-container';
            videoContainer.id = 'video-loading';
            videoContainer.innerHTML = `
                <div class="video-placeholder">
                    <i class="fas fa-cog fa-spin"></i>
                    <p>Generating visualization...</p>
                </div>
            `;
            contentDiv.appendChild(videoContainer);
        }
    }
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update last assistant message with video
function updateLastAssistantMessageWithVideo(videoUrl) {
    const chatMessages = document.querySelector('.chat-messages');
    const messages = chatMessages.querySelectorAll('.message');
    const lastMessage = messages[messages.length - 1];
    
    if (lastMessage && lastMessage.classList.contains('assistant-message')) {
        const contentDiv = lastMessage.querySelector('.message-content');
        if (contentDiv) {
            // Remove loading indicator
            const loadingIndicator = contentDiv.querySelector('#video-loading');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
            
            // Add video container
            const videoContainer = document.createElement('div');
            videoContainer.className = 'video-container';
            videoContainer.innerHTML = `
                <video id="generator-output-video" controls>
                    <source src="${videoUrl}" type="video/mp4">
                    Your browser does not support the video tag.
                </video>
            `;
            contentDiv.appendChild(videoContainer);
        }
    }
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// Update last assistant message with error
function updateLastAssistantMessageWithError(error) {
    const chatMessages = document.querySelector('.chat-messages');
    const messages = chatMessages.querySelectorAll('.message');
    const lastMessage = messages[messages.length - 1];
    
    if (lastMessage && lastMessage.classList.contains('assistant-message')) {
        const contentDiv = lastMessage.querySelector('.message-content');
        if (contentDiv) {
            // Remove loading indicator
            const loadingIndicator = contentDiv.querySelector('#video-loading');
            if (loadingIndicator) {
                loadingIndicator.remove();
            }
            
            // Add error message
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error-message';
            errorDiv.innerHTML = `
                <div class="error-container">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Error generating visualization: ${error}</p>
                </div>
            `;
            contentDiv.appendChild(errorDiv);
        }
    }
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// New chat function
function newChat() {
    // Clear chat messages except the first welcome message
    const chatMessages = document.querySelector('.chat-messages');
    const messages = chatMessages.querySelectorAll('.message');
    
    // Keep the first message (welcome message)
    for (let i = 1; i < messages.length; i++) {
        messages[i].remove();
    }
    
    // Reset input
    const input = document.getElementById('userInput');
    input.value = '';
    autoResize(input);
}

// Show settings panel
function showSettings() {
    const rightPanel = document.getElementById('rightPanel');
    rightPanel.classList.add('open');
}

// Close settings panel
function closeRightPanel() {
    const rightPanel = document.getElementById('rightPanel');
    rightPanel.classList.remove('open');
}

// Show code editor
function showCodeEditor() {
    alert("Code Editor functionality would open here in a modal or separate view.");
}

// Show voiceover
function showVoiceover() {
    alert("Voiceover functionality would open here in a modal or separate view.");
}

// Initialize webhook URL from localStorage if available
function initWebhookUrl() {
    const savedWebhookUrl = localStorage.getItem('n8nWebhookUrl');
    if (savedWebhookUrl) {
        document.getElementById('n8n-webhook').value = savedWebhookUrl;
    }
}

// Initialize OpenRouter API Key from localStorage if available
function initOpenRouterApiKey() {
    const savedOpenRouterApiKey = localStorage.getItem('openrouterApiKey');
    if (savedOpenRouterApiKey) {
        document.getElementById('openrouter-api-key').value = savedOpenRouterApiKey;
    }
}

// Save webhook URL
function saveWebhookUrl() {
    const webhookUrl = document.getElementById('n8n-webhook').value;
    localStorage.setItem('n8nWebhookUrl', webhookUrl);
    alert('Webhook URL saved successfully!');
}

// Save OpenRouter API Key
function saveOpenRouterApiKey() {
    const apiKey = document.getElementById('openrouter-api-key').value;
    localStorage.setItem('openrouterApiKey', apiKey);
    alert('API Key saved successfully!');
}

// Test server connection on page load
async function testServerConnection() {
    try {
        const response = await fetch('/healthz');
        const serverStatus = document.getElementById('server-status');
        const statusIndicator = document.getElementById('server-status-indicator');
        
        if (response.ok) {
            serverStatus.textContent = "Online";
            serverStatus.style.color = "#10a37f";
            statusIndicator.style.backgroundColor = "#10a37f";
        } else {
            serverStatus.textContent = "Offline";
            serverStatus.style.color = "#ef4444";
            statusIndicator.style.backgroundColor = "#ef4444";
        }
    } catch (error) {
        console.error('Server connection error:', error);
        const serverStatus = document.getElementById('server-status');
        const statusIndicator = document.getElementById('server-status-indicator');
        serverStatus.textContent = "Connection Error";
        serverStatus.style.color = "#ef4444";
        statusIndicator.style.backgroundColor = "#ef4444";
    }
}

// Initialize theme selector
function initThemeSelector() {
    const themeSelector = document.getElementById('theme-selector');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    themeSelector.value = savedTheme;
    
    themeSelector.addEventListener('change', function() {
        localStorage.setItem('theme', this.value);
        // In a real implementation, you would apply the theme here
    });
}

// DOMContentLoaded event
document.addEventListener('DOMContentLoaded', function() {
    // Initialize components
    initWebhookUrl();
    initOpenRouterApiKey();
    initThemeSelector();
    testServerConnection();
    
    // Set initial textarea height
    const textarea = document.getElementById('userInput');
    if (textarea) {
        autoResize(textarea);
    }
    
    // Add event listeners for conversation items
    const conversations = document.querySelectorAll('.conversation');
    conversations.forEach(conv => {
        conv.addEventListener('click', function() {
            // Remove active class from all conversations
            conversations.forEach(c => c.classList.remove('active'));
            // Add active class to clicked conversation
            this.classList.add('active');
            // Update chat title
            const title = this.querySelector('span').textContent;
            document.querySelector('.chat-title').textContent = title;
        });
    });
});

// Utility function to clean invalid Unicode characters that can cause syntax errors
function cleanInvalidUnicode(text) {
    if (typeof text !== 'string') return text;
    
    return text.replace(/\u2013|\u2014|\u2018|\u2019|\u201c|\u201d|\u2026/g, function(match) {
        switch(match) {
            case '\u2013': // en dash
            case '\u2014': // em dash
                return '-';
            case '\u2018': // left single quotation mark
            case '\u2019': // right single quotation mark
                return "'";
            case '\u201c': // left double quotation mark
            case '\u201d': // right double quotation mark
                return '"';
            case '\u2026': // horizontal ellipsis
                return '...';
            default:
                return match;
        }
    });
}