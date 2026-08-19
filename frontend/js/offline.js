const Offline = (() => {
    const QUEUE_KEY = 'jarvis_offline_queue';
    let isOnline = navigator.onLine;

    function getQueue() {
        try {
            return JSON.parse(localStorage.getItem(QUEUE_KEY)) || [];
        } catch {
            return [];
        }
    }

    function setQueue(queue) {
        localStorage.setItem(QUEUE_KEY, JSON.stringify(queue));
    }

    function enqueue(request) {
        const queue = getQueue();
        queue.push({
            ...request,
            timestamp: Date.now(),
        });
        setQueue(queue);
    }

    async function processQueue() {
        const queue = getQueue();
        if (queue.length === 0) return;

        const remaining = [];
        for (const req of queue) {
            try {
                await fetch(req.url, req.options);
            } catch {
                remaining.push(req);
            }
        }
        setQueue(remaining);
        return queue.length - remaining.length;
    }

    function getStatus() {
        if (!isOnline) return 'offline';
        const queue = getQueue();
        if (queue.length > 0) return 'syncing';
        return 'online';
    }

    function init(onStatusChange) {
        window.addEventListener('online', async () => {
            isOnline = true;
            onStatusChange('syncing');
            const synced = await processQueue();
            onStatusChange('online', synced);
        });

        window.addEventListener('offline', () => {
            isOnline = false;
            onStatusChange('offline');
        });

        isOnline = navigator.onLine;
    }

    return { init, enqueue, processQueue, getStatus, getQueue };
})();
