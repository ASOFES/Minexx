window.MinexxGPSLive = (function () {
  let map, markers = {}, polylines = {}, cfg = {};

  function statusClass(s) {
    return 'gps-status-' + (s || 'aucune');
  }

  function statusLabel(s) {
    if (s === 'connecte') return 'Connecté';
    if (s === 'derniere_recue') return 'Dernière position reçue';
    return 'Aucune position';
  }

  function ensureMap() {
    if (map) return;
    // Carto (pas tile.openstreetmap.org — bloqué 403 hors usage conforme)
    map = L.map('gps-live-map').setView([-11.66, 27.48], 12);
    L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
      maxZoom: 20,
      subdomains: 'abcd',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; <a href="https://carto.com/attributions">CARTO</a>'
    }).addTo(map);
  }

  function renderList(missions) {
    const el = document.getElementById('gps-mission-list');
    if (!el) return;
    if (!missions.length) {
      el.innerHTML = '<div class="alert alert-secondary mb-0">Aucune mission en cours.</div>';
      return;
    }
    el.innerHTML = missions.map(function (m) {
      const detail = cfg.detailUrlTemplate.replace('{id}', m.id);
      return (
        '<div class="card gps-mission-card">' +
          '<div class="card-body py-2">' +
            '<div class="d-flex justify-content-between">' +
              '<strong>🟢 ' + m.reference + '</strong>' +
              '<span class="' + statusClass(m.gps_status) + ' small">' + statusLabel(m.gps_status) + '</span>' +
            '</div>' +
            '<div class="small text-muted mt-1">' +
              (m.chauffeur || '—') + ' · ' + (m.vehicule || '—') + '<br>' +
              '→ ' + (m.destination || '') + '<br>' +
              'Départ: ' + (m.date_depart ? new Date(m.date_depart).toLocaleString() : '—') + '<br>' +
              'Vitesse: ' + (m.vitesse != null ? Math.round(m.vitesse) + ' km/h' : '—') +
              ' · GPS: ' + (m.distance_gps_km || 0) + ' km' +
            '</div>' +
            '<a class="btn btn-sm btn-outline-primary mt-2" href="' + detail + '">Détail / Replay</a>' +
          '</div>' +
        '</div>'
      );
    }).join('');
  }

  function updateMap(missions) {
    ensureMap();
    const bounds = [];
    const seen = {};
    missions.forEach(function (m) {
      seen[m.id] = true;
      if (m.track && m.track.length > 1) {
        const latlngs = m.track.map(function (p) { return [p.latitude, p.longitude]; });
        if (polylines[m.id]) {
          polylines[m.id].setLatLngs(latlngs);
        } else {
          polylines[m.id] = L.polyline(latlngs, { color: '#2563eb', weight: 4, opacity: 0.7 }).addTo(map);
        }
        latlngs.forEach(function (ll) { bounds.push(ll); });
      }
      if (m.last_position) {
        const ll = [m.last_position.latitude, m.last_position.longitude];
        bounds.push(ll);
        const html =
          '<b>' + m.reference + '</b><br>' +
          (m.chauffeur || '') + '<br>' +
          (m.vehicule || '') + '<br>' +
          '→ ' + (m.destination || '') + '<br>' +
          (m.vitesse != null ? Math.round(m.vitesse) + ' km/h' : '');
        if (markers[m.id]) {
          markers[m.id].setLatLng(ll).setPopupContent(html);
        } else {
          markers[m.id] = L.marker(ll).addTo(map).bindPopup(html);
        }
      }
    });
    Object.keys(markers).forEach(function (id) {
      if (!seen[id]) {
        map.removeLayer(markers[id]);
        delete markers[id];
      }
    });
    Object.keys(polylines).forEach(function (id) {
      if (!seen[id]) {
        map.removeLayer(polylines[id]);
        delete polylines[id];
      }
    });
    if (bounds.length) {
      map.fitBounds(bounds, { padding: [30, 30], maxZoom: 15 });
    }
  }

  function refresh() {
    fetch(cfg.apiUrl, { credentials: 'same-origin' })
      .then(function (r) { return r.json(); })
      .then(function (data) {
        if (!data.success) return;
        renderList(data.missions || []);
        updateMap(data.missions || []);
      })
      .catch(function () {});
  }

  function init(options) {
    cfg = options || {};
    ensureMap();
    refresh();
    const btn = document.getElementById('gps-refresh');
    if (btn) btn.addEventListener('click', refresh);
    setInterval(refresh, cfg.pollMs || 10000);
  }

  return { init: init, refresh: refresh };
})();
