self.addEventListener('push', function(event) {
    let data = {};
    if (event.data) {
        try { data = event.data.json(); } catch (e) { data = {}; }
    }
    const title = data.title || 'MINEXX';
    const body = data.body || '';
    const url = data.url || '/';
    const urgent = !!(data.urgent || data.type === 'course_new' || data.type === 'course_assigned' || data.type === 'order_assigned');
    const options = {
        body: body,
        icon: data.icon || '/static/images/logo_minexx.png',
        badge: data.badge || '/static/images/logo_minexx.png',
        data: url,
        silent: false,
        requireInteraction: urgent,
        vibrate: urgent
            ? [300, 120, 300, 120, 300, 120, 300]
            : [120, 60, 120, 60, 120],
    };
    event.waitUntil(
        Promise.all([
            self.registration.showNotification(title, options),
            self.clients.matchAll({ type: 'window', includeUncontrolled: true }).then(function(clientList) {
                clientList.forEach(function(client) {
                    client.postMessage({
                        type: 'minexx_ring',
                        urgent: urgent,
                        title: title,
                        body: body,
                        url: url
                    });
                });
            })
        ])
    );
});

self.addEventListener('notificationclick', function(event) {
    event.notification.close();
    const url = event.notification.data || '/';
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(function(clientList) {
            for (var i = 0; i < clientList.length; i++) {
                var client = clientList[i];
                if (client.url === url && 'focus' in client)
                    return client.focus();
            }
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});
