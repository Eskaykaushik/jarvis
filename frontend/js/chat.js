const Chat = (() => {
    const messagesEl = document.getElementById('messages');
    let conversationId = null;

    function scrollToBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function addMessage(text, role, cached = false) {
        const div = document.createElement('div');
        div.className = `message message--${role}`;

        const p = document.createElement('p');
        p.textContent = text;
        div.appendChild(p);

        const time = document.createElement('span');
        time.className = 'message__time';
        const now = new Date();
        time.textContent = (cached ? '(cached) ' : '') + now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        div.appendChild(time);

        messagesEl.appendChild(div);
        scrollToBottom();
        return div;
    }

    function showTyping() {
        const div = document.createElement('div');
        div.className = 'typing';
        div.id = 'typing-indicator';
        div.innerHTML = '<span class="typing__dot"></span><span class="typing__dot"></span><span class="typing__dot"></span>';
        messagesEl.appendChild(div);
        scrollToBottom();
    }

    function hideTyping() {
        const el = document.getElementById('typing-indicator');
        if (el) el.remove();
    }

    function showError(text) {
        const div = document.createElement('div');
        div.className = 'message message--error';
        div.textContent = text;
        messagesEl.appendChild(div);
        scrollToBottom();
    }

    function setConversationId(id) {
        conversationId = id;
    }

    function getConversationId() {
        return conversationId;
    }

    return { addMessage, showTyping, hideTyping, showError, setConversationId, getConversationId };
})();
