/**
 * PaaMoja Initiative — Service Worker
 * Provides offline support for core pages and assets.
 *
 * Place this file at: static/js/sw.js
 * It is registered from base.html (see registration snippet below).
 *
 * Strategy:
 *   - Core pages:   Cache-first with network fallback
 *   - Static assets: Cache-first (CSS, fonts, images)
 *   - API/Forms:    Network-first (M-Pesa, contact, newsletter)
 *   - Offline page: Shown when network is unavailable
 */

const CACHE_NAME    = 'paamoja-v1';
const OFFLINE_PAGE  = '/offline/';

// Pages and assets to pre-cache on install
const PRECACHE_URLS = [
    '/',
    '/about/',
    '/programs/',
    '/contact/',
    '/volunteer/',
    '/impact-reports/',
    OFFLINE_PAGE,
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600;700&family=Playfair+Display:wght@700;800&display=swap',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.0/css/all.min.css',
];

// ── Install: pre-cache core assets ───────────────────────────────────────────
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(PRECACHE_URLS))
            .then(() => self.skipWaiting())
            .catch(err => console.warn('[SW] Pre-cache failed:', err))
    );
});

// ── Activate: clean old caches ────────────────────────────────────────────────
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(keys =>
            Promise.all(
                keys
                    .filter(key => key !== CACHE_NAME)
                    .map(key => caches.delete(key))
            )
        ).then(() => self.clients.claim())
    );
});

// ── Fetch: routing strategy ───────────────────────────────────────────────────
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip non-GET and browser-extension requests
    if (request.method !== 'GET') return;
    if (!url.protocol.startsWith('http')) return;

    // Network-only for M-Pesa, contact form, newsletter (must be real-time)
    const networkOnlyPaths = ['/mpesa/', '/newsletter/', '/admin/'];
    if (networkOnlyPaths.some(path => url.pathname.startsWith(path))) {
        return; // fall through to browser
    }

    // For HTML pages: network-first, cache fallback, offline page last resort
    if (request.headers.get('accept')?.includes('text/html')) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    if (response.ok) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
                    }
                    return response;
                })
                .catch(() =>
                    caches.match(request)
                        .then(cached => cached || caches.match(OFFLINE_PAGE))
                )
        );
        return;
    }

    // For static assets: cache-first
    event.respondWith(
        caches.match(request).then(cached => {
            if (cached) return cached;
            return fetch(request).then(response => {
                if (response.ok && response.type !== 'opaque') {
                    const clone = response.clone();
                    caches.open(CACHE_NAME).then(cache => cache.put(request, clone));
                }
                return response;
            }).catch(() => {
                // Silent failure for non-essential assets
            });
        })
    );
});

// ── Push notifications (future use) ──────────────────────────────────────────
self.addEventListener('push', event => {
    const data = event.data?.json() || {};
    const title = data.title || 'PaaMoja Initiative';
    const options = {
        body:    data.body    || 'New update from PaaMoja.',
        icon:    data.icon    || '/static/img/icons/icon-192x192.png',
        badge:   data.badge   || '/static/img/icons/icon-72x72.png',
        data:    { url: data.url || '/' },
    };
    event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener('notificationclick', event => {
    event.notification.close();
    event.waitUntil(
        clients.openWindow(event.notification.data?.url || '/')
    );
});