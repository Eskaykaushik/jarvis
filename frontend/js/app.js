const App = (() => {
    const form = document.getElementById('input-form');
    const field = document.getElementById('input-field');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');

    function updateStatus(status, detail) {
        const labels = {
            online: 'online',
            offline: 'offline',
            syncing: 'syncing...',
            degraded: 'degraded',
        };
        statusEl.textContent = labels[status] || status;
        statusEl.className = `header__status header__status--${status === 'online' ? 'online' : 'offline'}`;

        if (detail && status === 'online') {
            statusEl.textContent = `online (+${detail} synced)`;
        }
    }

    async function checkHealth() {
        if (!navigator.onLine) {
            updateStatus('offline');
            return;
        }
        try {
            await API.health();
            updateStatus(Offline.getStatus());
        } catch {
            updateStatus('degraded');
        }
    }

    async function sendMessage(text) {
        sendBtn.disabled = true;
        field.value = '';

        Chat.addMessage(text, 'user');
        Chat.showTyping();

        try {
            const data = await API.chat(text, Chat.getConversationId());
            Chat.hideTyping();
            Chat.addMessage(data.response, 'assistant', data.cached);

            if (data.conversation_id) {
                Chat.setConversationId(data.conversation_id);
            }
        } catch (err) {
            Chat.hideTyping();
            if (err.message.includes('offline')) {
                Chat.addMessage(text, 'user');
                Chat.showError('You are offline. Your message has been queued and will send when you reconnect.');
            } else {
                Chat.showError(`Failed to get response: ${err.message}`);
            }
        } finally {
            sendBtn.disabled = false;
            field.focus();
        }
    }

    function loadRecentMessages() {
        const recent = Cache.getRecentLocal();
        recent.forEach(msg => Chat.addMessage(msg.content, msg.role, true));
    }

    function init() {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = field.value.trim();
            if (text) sendMessage(text);
        });

        Offline.init((status, detail) => {
            updateStatus(status, detail);
        });

        loadRecentMessages();
        checkHealth();
        setInterval(checkHealth, 60000);
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', App.init);
