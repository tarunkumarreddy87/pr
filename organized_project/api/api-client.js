// API Client for connecting to backend services

class ApiClient {
    constructor() {
        // Default backend URL - can be overridden
        // Use relative URLs so requests go through the proxy
        this.backendUrl = '';
        this.componentUrl = '';
    }
    
    // Set backend URL
    setBackendUrl(url) {
        this.backendUrl = url;
        localStorage.setItem('backendUrl', url);
    }
    
    // Set component URL
    setComponentUrl(url) {
        this.componentUrl = url;
        localStorage.setItem('componentUrl', url);
    }
    
    // Generic fetch method with error handling
    async fetchFromApi(endpoint, options = {}) {
        // Use relative URLs so requests go through the proxy
        const url = `${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
        
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });
            
            // Check if response is OK
            if (!response.ok) {
                const errorText = await response.text();
                let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
                
                try {
                    const errorData = JSON.parse(errorText);
                    errorMessage = errorData.error || errorMessage;
                } catch (e) {
                    if (errorText) {
                        errorMessage = errorText;
                    }
                }
                
                throw new Error(errorMessage);
            }
            
            // Try to parse JSON response
            const contentType = response.headers.get('content-type');
            if (contentType && contentType.includes('application/json')) {
                return await response.json();
            } else {
                return await response.text();
            }
        } catch (error) {
            console.error(`API Error for ${url}:`, error);
            throw error;
        }
    }

    // Process n8n webhook
    async processN8nWebhook(data) {
        return await this.fetchFromApi('/api/n8n/webhook', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    }

    // Generate visualization
    async generateVisualization(script) {
        return await this.fetchFromApi('/api/generate', {
            method: 'POST',
            body: JSON.stringify({ script })
        });
    }
    
    // Get latest video
    async getLatestVideo() {
        return await this.fetchFromApi('/video/latest');
    }
    
    // Get user profile
    async getUserProfile() {
        return await this.fetchFromApi('/api/profile');
    }
    
    // Update user profile
    async updateUserProfile(profileData) {
        return await this.fetchFromApi('/api/profile', {
            method: 'PUT',
            body: JSON.stringify(profileData)
        });
    }
    
    // Get chat messages
    async getChatMessages() {
        return await this.fetchFromApi('/api/chat/messages');
    }
    
    // Send chat message
    async sendChatMessage(content) {
        return await this.fetchFromApi('/api/chat/messages', {
            method: 'POST',
            body: JSON.stringify({ content })
        });
    }
    
    // Get navigation items
    async getNavigationItems() {
        return await this.fetchFromApi('/api/navigation/items');
    }
    
    // Select navigation item
    async selectNavigationItem(itemId) {
        return await this.fetchFromApi('/api/navigation/select', {
            method: 'POST',
            body: JSON.stringify({ item_id: itemId })
        });
    }
    
    // Toggle sidebar
    async toggleSidebar(collapsed) {
        return await this.fetchFromApi('/api/sidebar/toggle', {
            method: 'POST',
            body: JSON.stringify({ collapsed })
        });
    }
    
    // Get learning paths
    async getLearningPaths() {
        return await this.fetchFromApi('/api/learning_paths');
    }
    
    // Get educational content
    async getEducationalContent(topicId) {
        return await this.fetchFromApi(`/api/content/${topicId}`);
    }
    
    // Generate voiceover
    async generateVoiceover(text, service = 'gtts') {
        return await this.fetchFromApi('/api/voiceover', {
            method: 'POST',
            body: JSON.stringify({ text, service })
        });
    }
    
    // Get settings
    async getSettings() {
        return await this.fetchFromApi('/api/settings');
    }
    
    // Update settings
    async updateSettings(settings) {
        return await this.fetchFromApi('/api/settings', {
            method: 'POST',
            body: JSON.stringify(settings)
        });
    }
    
    // Cleanup old animations
    async cleanup() {
        return await this.fetchFromApi('/api/cleanup', {
            method: 'POST'
        });
    }
    
    // Cleanup audio files
    async cleanupAudio() {
        return await this.fetchFromApi('/api/cleanup_audio', {
            method: 'POST'
        });
    }
    
    // Health check
    async healthCheck() {
        return await this.fetchFromApi('/healthz');
    }
}

// Create a global instance
const apiClient = new ApiClient();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { ApiClient, apiClient };
}