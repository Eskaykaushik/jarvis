const App = (() => {
    const form = document.getElementById('input-form');
    const field = document.getElementById('input-field');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');

    async function checkHealth() {
        try {
            await API.health();
            statusEl.textContent = 'online';
            statusEl.className = 'header__status header__status--online';
        } catch {
            statusEl.textContent = 'offline';
            statusEl.className = 'header__status header__status--offline';
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
            Chat.addMessage(data.response, 'assistant');

            if (data.conversation_id) {
                Chat.setConversationId(data.conversation_id);
            }
        } catch (err) {
            Chat.hideTyping();
            Chat.showError(`Failed to get response: ${err.message}`);
        } finally {
            sendBtn.disabled = false;
            field.focus();
        }
    }

    function init() {
        form.addEventListener('submit', (e) => {
            e.preventDefault();
            const text = field.value.trim();
            if (text) sendMessage(text);
        });

        checkHealth();
        setInterval(checkHealth, 60000);
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', App.init);
