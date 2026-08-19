const App = (() => {
    const form = document.getElementById('input-form');
    const field = document.getElementById('input-field');
    const sendBtn = document.getElementById('send-btn');
    const statusEl = document.getElementById('status');
    const signoutBtn = document.getElementById('signout-btn');
    const appEl = document.getElementById('app');
    const authScreen = document.getElementById('auth-screen');

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

    function showApp() {
        appEl.style.display = 'flex';
        authScreen.style.display = 'none';
        signoutBtn.style.display = 'inline-block';
    }

    function showAuth() {
        appEl.style.display = 'none';
        authScreen.style.display = 'flex';
        signoutBtn.style.display = 'none';
    }

    async function handleAuthSubmit(e) {
        e.preventDefault();
        const email = document.getElementById('auth-email').value.trim();
        const password = document.getElementById('auth-password').value;
        const errorEl = document.getElementById('auth-error');
        const submitBtn = document.getElementById('auth-submit');
        const isSignup = submitBtn.textContent.toLowerCase().includes('sign up') || submitBtn.textContent.toLowerCase().includes('create');

        errorEl.textContent = '';
        submitBtn.disabled = true;
        submitBtn.textContent = isSignup ? 'Creating...' : 'Signing in...';

        try {
            if (isSignup) {
                await Auth.signUp(email, password);
            } else {
                await Auth.signIn(email, password);
            }
            showApp();
            loadRecentMessages();
            checkHealth();
            setInterval(checkHealth, 60000);
        } catch (err) {
            errorEl.textContent = err.message || 'Authentication failed';
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = isSignup ? 'Create account' : 'Sign in';
        }
    }

    function initAuthToggle() {
        const switchBtn = document.getElementById('auth-switch');
        const submitBtn = document.getElementById('auth-submit');

        switchBtn.addEventListener('click', () => {
            const isSignup = submitBtn.textContent.toLowerCase().includes('sign up') || submitBtn.textContent.toLowerCase().includes('create');
            if (isSignup) {
                switchBtn.textContent = 'Already have an account? Sign In';
                submitBtn.textContent = 'Sign in';
            } else {
                switchBtn.textContent = 'Need an account? Sign Up';
                submitBtn.textContent = 'Create account';
            }
        });
    }

    function initOAuth() {
        document.getElementById('auth-google').addEventListener('click', () => Auth.signInWithGoogle());
        document.getElementById('auth-github').addEventListener('click', () => Auth.signInWithGitHub());
    }

    async function init() {
        Auth.onAuthStateChanged((user) => {
            if (user) {
                showApp();
                checkHealth();
            } else {
                showAuth();
            }
        });

        signoutBtn.addEventListener('click', () => {
            Auth.signOut();
            showAuth();
        });

        const result = await Auth.init();

        document.getElementById('auth-form').addEventListener('submit', handleAuthSubmit);
        initAuthToggle();
        initOAuth();

        if (result.authenticated) {
            showApp();
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                const text = field.value.trim();
                if (text) sendMessage(text);
            });
            loadRecentMessages();
            checkHealth();
            setInterval(checkHealth, 60000);
        } else {
            showAuth();
        }

        Offline.init((status, detail) => {
            updateStatus(status, detail);
        });
    }

    return { init };
})();

document.addEventListener('DOMContentLoaded', App.init);
