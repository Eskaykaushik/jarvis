const Auth = (() => {
    const SUPABASE_URL = 'https://uvznfwrfhpfsefsdecei.supabase.co';
    const SUPABASE_ANON_KEY = 'sb_publishable_XMhbY4Nplgc_hwNGJuq8Fg_9SNoUzH_';

    let client = null;
    let token = localStorage.getItem('jarvis_token') || null;
    let user = null;
    const listeners = [];

    function getClient() {
        if (client) return client;
        if (typeof supabase === 'undefined') {
            throw new Error('Supabase client not loaded');
        }
        client = supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY, {
            auth: {
                storage: window.localStorage,
                storageKey: 'jarvis_auth',
                autoRefreshToken: true,
                persistSession: true,
                detectSessionInUrl: true,
            },
        });
        return client;
    }

    async function init() {
        try {
            const c = getClient();
            const { data: { session } } = await c.auth.getSession();
            if (session) {
                token = session.access_token;
                user = session.user;
                _notify(user, token);
                return { authenticated: true, user, token };
            }
        } catch (e) {
            console.error('Auth init failed:', e);
        }
        _notify(null, null);
        return { authenticated: false, user: null, token: null };
    }

    async function signUp(email, password) {
        const c = getClient();
        const { data, error } = await c.auth.signUp({ email, password });
        if (error) throw error;
        if (data.session) {
            token = data.session.access_token;
            user = data.session.user;
            localStorage.setItem('jarvis_token', token);
            _notify(user, token);
        }
        return data;
    }

    async function signIn(email, password) {
        const c = getClient();
        const { data, error } = await c.auth.signInWithPassword({ email, password });
        if (error) throw error;
        if (data.session) {
            token = data.session.access_token;
            user = data.session.user;
            localStorage.setItem('jarvis_token', token);
            _notify(user, token);
        }
        return data;
    }

    async function signInWithGoogle() {
        const c = getClient();
        const { data, error } = await c.auth.signInWithOAuth({
            provider: 'google',
            options: {
                redirectTo: window.location.origin,
            },
        });
        if (error) throw error;
        return data;
    }

    async function signInWithGitHub() {
        const c = getClient();
        const { data, error } = await c.auth.signInWithOAuth({
            provider: 'github',
            options: {
                redirectTo: window.location.origin,
            },
        });
        if (error) throw error;
        return data;
    }

    async function signOut() {
        const c = getClient();
        await c.auth.signOut();
        token = null;
        user = null;
        localStorage.removeItem('jarvis_token');
        _notify(null, null);
    }

    function getToken() {
        return token;
    }

    function getUser() {
        return user;
    }

    function isAuthenticated() {
        return !!token;
    }

    function onAuthStateChanged(callback) {
        listeners.push(callback);
    }

    function _notify(u, t) {
        listeners.forEach(cb => cb(u, t));
    }

    function updateToken(newToken) {
        token = newToken;
        if (token) {
            localStorage.setItem('jarvis_token', token);
        } else {
            localStorage.removeItem('jarvis_token');
        }
        _notify(user, token);
    }

    return {
        init,
        signUp,
        signIn,
        signInWithGoogle,
        signInWithGitHub,
        signOut,
        getToken,
        getUser,
        isAuthenticated,
        onAuthStateChanged,
        updateToken,
    };
})();
