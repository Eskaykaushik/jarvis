const API = (() => {
    const BASE_URL = localStorage.getItem('jarvis_api_url') || 'https://jarvis-xtqt.onrender.com';

    async function request(endpoint, options = {}) {
        const url = `${BASE_URL}${endpoint}`;
        const config = {
            headers: { 'Content-Type': 'application/json' },
            ...options,
        };

        if (!navigator.onLine) {
            Offline.enqueue({ url, options: config });
            throw new Error('You are offline. Request queued.');
        }

        const response = await fetch(url, config);

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        return response.json();
    }

    async function chat(message, conversationId = null) {
        const body = JSON.stringify({ message, conversation_id: conversationId });

        const cached = await Cache.getConversation(conversationId || 'current');
        if (cached && cached.messages) {
            const last = cached.messages[cached.messages.length - 1];
            if (last && last.role === 'user' && last.content === message) {
                const assistantMsg = cached.messages.find(
                    (m, i) => m.role === 'assistant' && i > cached.messages.lastIndexOf(last)
                );
                if (assistantMsg) {
                    return {
                        response: assistantMsg.content,
                        conversation_id: conversationId,
                        cached: true,
                    };
                }
            }
        }

        const data = await request('/chat', { method: 'POST', body });

        Cache.addMessageLocal({ role: 'user', content: message });
        Cache.addMessageLocal({ role: 'assistant', content: data.response });

        if (data.conversation_id) {
            const msgs = Cache.getRecentLocal();
            await Cache.saveConversation(data.conversation_id, msgs);
        }

        return data;
    }

    async function getConversation(id) {
        const cached = await Cache.getConversation(id);
        if (cached) return cached;
        return request(`/conversation/${id}`);
    }

    async function health() {
        return request('/health');
    }

    return { chat, getConversation, health, BASE_URL };
})();
