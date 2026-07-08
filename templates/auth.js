// Shared auth & nav helper — included in every protected page.
// Checks /api/me, redirects to /login.html if not authenticated.
// Sets window.__user and window.__config for the page to use.
// Call eBoatReady() with a callback that receives (user, config) when both are loaded.

window.__user   = null;
window.__config = null;
let __readyCallbacks = [];

async function eBoatInit() {
    try {
        const [userRes, configRes] = await Promise.all([
            fetch('/api/me',        {credentials:'include'}),
            fetch('/api/me/config', {credentials:'include'})
        ]);
        if (!userRes.ok) {
            window.location.href = '/login.html';
            return;
        }
        window.__user   = await userRes.json();
        window.__config = await configRes.json();

        // Populate nav
        const uEl = document.getElementById('nav-username');
        if(uEl) uEl.textContent = window.__user.username;
        const aEl = document.getElementById('nav-admin-link');
        if(aEl) aEl.style.display = window.__user.role === 'admin' ? '' : 'none';

        // Fire ready callbacks
        __readyCallbacks.forEach(cb => cb(window.__user, window.__config));
        __readyCallbacks = [];
    } catch(e) {
        window.location.href = '/login.html';
    }
}

function eBoatReady(cb) {
    if(window.__user && window.__config) {
        cb(window.__user, window.__config);
    } else {
        __readyCallbacks.push(cb);
    }
}

async function logout() {
    await fetch('/api/auth/logout', {method:'POST', credentials:'include'});
    window.location.href = '/login.html';
}

// Run immediately
eBoatInit();
