const Cache = (() => {
    const LS_KEY = 'jarvis_recent';
    const LS_MAX = 10;
    const DB_NAME = 'jarvis_cache';
    const DB_VERSION = 1;
    const STORE = 'conversations';

    let db = null;

    function getLocal() {
        try {
            return JSON.parse(localStorage.getItem(LS_KEY)) || [];
        } catch {
            return [];
        }
    }

    function setLocal(messages) {
        localStorage.setItem(LS_KEY, JSON.stringify(messages.slice(-LS_MAX)));
    }

    function addMessageLocal(msg) {
        const msgs = getLocal();
        msgs.push(msg);
        setLocal(msgs);
    }

    function getRecentLocal() {
        return getLocal();
    }

    async function openDB() {
        if (db) return db;
        return new Promise((resolve, reject) => {
            const req = indexedDB.open(DB_NAME, DB_VERSION);
            req.onupgradeneeded = (e) => {
                const database = e.target.result;
                if (!database.objectStoreNames.contains(STORE)) {
                    const store = database.createObjectStore(STORE, { keyPath: 'id' });
                    store.createIndex('updated_at', 'updated_at', { unique: false });
                }
            };
            req.onsuccess = (e) => {
                db = e.target.result;
                resolve(db);
            };
            req.onerror = () => reject(req.error);
        });
    }

    async function saveConversation(id, messages) {
        const database = await openDB();
        const tx = database.transaction(STORE, 'readwrite');
        const store = tx.objectStore(STORE);
        store.put({
            id,
            messages,
            updated_at: Date.now(),
        });
        return new Promise((resolve, reject) => {
            tx.oncomplete = resolve;
            tx.onerror = () => reject(tx.error);
        });
    }

    async function getConversation(id) {
        const database = await openDB();
        const tx = database.transaction(STORE, 'readonly');
        const store = tx.objectStore(STORE);
        return new Promise((resolve, reject) => {
            const req = store.get(id);
            req.onsuccess = () => resolve(req.result || null);
            req.onerror = () => reject(req.error);
        });
    }

    async function getAllConversations() {
        const database = await openDB();
        const tx = database.transaction(STORE, 'readonly');
        const store = tx.objectStore(STORE);
        return new Promise((resolve, reject) => {
            const req = store.index('updated_at').getAll();
            req.onsuccess = () => resolve(req.result.reverse());
            req.onerror = () => reject(req.error);
        });
    }

    async function deleteConversation(id) {
        const database = await openDB();
        const tx = database.transaction(STORE, 'readwrite');
        const store = tx.objectStore(STORE);
        store.delete(id);
        return new Promise((resolve, reject) => {
            tx.oncomplete = resolve;
            tx.onerror = () => reject(tx.error);
        });
    }

    return {
        addMessageLocal,
        getRecentLocal,
        saveConversation,
        getConversation,
        getAllConversations,
        deleteConversation,
    };
})();
