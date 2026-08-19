const API = (() => {
    const BASE_URL = localStorage.getItem('jarvis_api_url') || 'http://localhost:8000';

    async function request(endpoint, options = {}) {
        const url = `${BASE_URL}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        };

        const response = await fetch(url, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    async function chat(message, conversationId = null) {
        return request('/chat', {
            method: 'POST',
            body: JSON.stringify({ message, conversation_id: conversationId }),
        });
    }

    async function getConversation(id) {
        return request(`/conversation/${id}`);
    }

    async function health() {
        return request('/health');
    }

    return { chat, getConversation, health, BASE_URL };
})();
