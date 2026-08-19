const Utils = (() => {
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    function formatTime(date) {
        return new Date(date).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function formatDate(date) {
        return new Date(date).toLocaleDateString([], { year: 'numeric', month: 'short', day: 'numeric' });
    }

    return { escapeHtml, formatTime, formatDate };
})();
