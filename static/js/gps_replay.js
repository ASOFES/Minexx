window.MinexxGPSReplay = (function () {
  let map, polyline, marker, positions = [], idx = 0, timer = null;

  function setLabel() {
    const el = document.getElementById('gps-replay-label');
    const scrub = document.getElementById('gps-scrubber');
    if (!positions.length) {
      if (el) el.textContent = 'Aucun point GPS';
      return;
    }
    const p = positions[idx];
    if (scrub) scrub.value = String(idx);
    if (el) {
      el.textContent =
        (idx + 1) + '/' + positions.length +
        ' — ' + new Date(p.timestamp).toLocaleString() +
        (p.vitesse != null ? ' — ' + Math.round(p.vitesse) + ' km/h' : '');
    }
  }

  function showIndex(i) {
    if (!positions.length) return;
    idx = Math.max(0, Math.min(positions.length - 1, i));
    const p = positions[idx];
    const ll = [p.latitude, p.longitude];
    if (marker) marker.setLatLng(ll);
    setLabel();
  }

  function play() {
    if (timer || !positions.length) return;
    timer = setInterval(function () {
      if (idx >= positions.length - 1) {
        pause();
        return;
      }
      showIndex(idx + 1);
    }, 400);
  }

  function pause() {
    if (timer) {
      clearInterval(timer);
      timer = null;
    }
  }

  function reset() {
    pause();
    showIndex(0);
    if (positions.length && map) {
      map.fitBounds(polyline.getBounds(), { padding: [24, 24] });
    }
  }

  function init(options) {
    positions = options.positions || [];
    if (typeof positions === 'string') {
      try { positions = JSON.parse(positions); } catch (e) { positions = []; }
    }
    map = L.map(options.mapId || 'gps-replay-map').setView([-11.66, 27.48], 12);
    L.tileLayer('https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}', {
      maxZoom: 19,
      attribution: 'Tiles &copy; Esri &mdash; Source: Esri, OpenStreetMap'
    }).addTo(map);

    const scrub = document.getElementById('gps-scrubber');
    if (scrub) {
      scrub.max = String(Math.max(0, positions.length - 1));
      scrub.addEventListener('input', function () {
        pause();
        showIndex(parseInt(scrub.value, 10) || 0);
      });
    }

    document.getElementById('gps-play')?.addEventListener('click', play);
    document.getElementById('gps-pause')?.addEventListener('click', pause);
    document.getElementById('gps-reset')?.addEventListener('click', reset);

    if (!positions.length) {
      setLabel();
      return;
    }
    const latlngs = positions.map(function (p) { return [p.latitude, p.longitude]; });
    polyline = L.polyline(latlngs, { color: '#0ea5e9', weight: 4 }).addTo(map);
    marker = L.circleMarker(latlngs[0], {
      radius: 8,
      color: '#16a34a',
      fillColor: '#22c55e',
      fillOpacity: 1
    }).addTo(map);
    map.fitBounds(polyline.getBounds(), { padding: [24, 24] });
    showIndex(0);
  }

  return { init: init };
})();
