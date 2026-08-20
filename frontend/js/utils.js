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

    function renderMarkdown(text) {
        if (typeof marked === 'undefined') return escapeHtml(text);

        marked.setOptions({
            breaks: true,
            gfm: true,
        });

        const raw = marked.parse(text);
        if (typeof DOMPurify !== 'undefined') {
            return DOMPurify.sanitize(raw, { ADD_TAGS: ['button'] });
        }
        return escapeHtml(text);
    }

    function addCopyButtons(container) {
        container.querySelectorAll('pre').forEach(pre => {
            const btn = document.createElement('button');
            btn.className = 'copy-btn';
            btn.textContent = 'Copy';
            btn.addEventListener('click', () => {
                const code = pre.querySelector('code');
                navigator.clipboard.writeText(code?.textContent || pre.textContent).then(() => {
                    btn.textContent = 'Copied!';
                    setTimeout(() => btn.textContent = 'Copy', 2000);
                });
            });
            pre.style.position = 'relative';
            pre.appendChild(btn);
        });
    }

    return { escapeHtml, formatTime, formatDate, renderMarkdown, addCopyButtons };
})();
