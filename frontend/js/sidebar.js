const Sidebar = (() => {
    let activeId = null;
    let conversations = [];
    let searchQuery = '';

    const listEl = document.getElementById('conversation-list');
    const sidebarEl = document.getElementById('sidebar');
    const toggleBtn = document.getElementById('sidebar-toggle');
    const closeBtn = document.getElementById('sidebar-close');
    const newChatBtn = document.getElementById('new-chat-btn');
    const searchEl = document.getElementById('conversation-search');

    function debounce(fn, ms) {
        let timer;
        return (...args) => {
            clearTimeout(timer);
            timer = setTimeout(() => fn(...args), ms);
        };
    }

    function formatTime(ts) {
        const d = new Date(ts * 1000);
        const now = new Date();
        const diffMs = now - d;
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffDays === 0) {
            return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        } else if (diffDays === 1) {
            return 'Yesterday';
        } else if (diffDays < 7) {
            return d.toLocaleDateString([], { weekday: 'short' });
        }
        return d.toLocaleDateString([], { month: 'short', day: 'numeric' });
    }

    function getFiltered() {
        if (!searchQuery) return conversations;
        const q = searchQuery.toLowerCase();
        return conversations.filter(c => c.title.toLowerCase().includes(q));
    }

    function render() {
        const filtered = getFiltered();

        if (conversations.length === 0 && !searchQuery) {
            listEl.innerHTML = '<div class="sidebar__empty">No conversations yet</div>';
            return;
        }

        if (filtered.length === 0) {
            listEl.innerHTML = `<div class="sidebar__empty">${searchQuery ? 'No matches' : 'No conversations yet'}</div>`;
            return;
        }

        listEl.innerHTML = filtered.map(c => `
            <div class="sidebar__item ${c.id === activeId ? 'sidebar__item--active' : ''}" data-id="${c.id}">
                <div class="sidebar__item-text">
                    <span class="sidebar__item-title">${escapeHtml(c.title)}</span>
                    <span class="sidebar__item-time">${formatTime(c.updated_at)}</span>
                </div>
                <button class="sidebar__item-delete" data-delete="${c.id}" title="Delete">&times;</button>
            </div>
        `).join('');
    }

    function escapeHtml(str) {
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    async function load() {
        try {
            conversations = await API.listConversations();
            render();
        } catch (e) {
            console.error('Failed to load conversations:', e);
        }
    }

    function select(id) {
        activeId = id;
        render();
    }

    function setActive(id) {
        activeId = id;
        render();
    }

    function clearActive() {
        activeId = null;
        render();
    }

    function clearSearch() {
        searchQuery = '';
        searchEl.value = '';
        render();
    }

    function refresh() {
        load();
    }

    function addConversation(id, title) {
        const exists = conversations.find(c => c.id === id);
        if (!exists) {
            conversations.unshift({
                id,
                title: title || 'New conversation',
                updated_at: Date.now() / 1000,
            });
        } else {
            exists.updated_at = Date.now() / 1000;
            if (title && title !== 'New conversation') {
                exists.title = title;
            }
            conversations.sort((a, b) => b.updated_at - a.updated_at);
        }
        activeId = id;
        clearSearch();
    }

    function removeConversation(id) {
        conversations = conversations.filter(c => c.id !== id);
        if (activeId === id) {
            activeId = null;
        }
        render();
    }

    function toggle() {
        sidebarEl.classList.toggle('open');
    }

    function close() {
        sidebarEl.classList.remove('open');
    }

    function init(onSelect, onDelete, onNew) {
        listEl.addEventListener('click', (e) => {
            const deleteBtn = e.target.closest('[data-delete]');
            if (deleteBtn) {
                e.stopPropagation();
                const id = deleteBtn.dataset.delete;
                if (confirm('Delete this conversation?')) {
                    onDelete(id);
                }
                return;
            }

            const item = e.target.closest('.sidebar__item');
            if (item) {
                onSelect(item.dataset.id);
                close();
            }
        });

        toggleBtn.addEventListener('click', toggle);
        closeBtn.addEventListener('click', close);
        newChatBtn.addEventListener('click', () => {
            onNew();
            close();
        });

        searchEl.addEventListener('input', debounce((e) => {
            searchQuery = e.target.value.trim();
            render();
        }, 150));

        load();
    }

    return {
        init,
        load,
        select,
        setActive,
        clearActive,
        clearSearch,
        refresh,
        addConversation,
        removeConversation,
        toggle,
        close,
    };
})();
