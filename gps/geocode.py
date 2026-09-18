"""Géocodage Nominatim (OpenStreetMap) — usage raisonnable, User-Agent obligatoire."""
from __future__ import annotations

import json
import urllib.parse
import urllib.request


NOMINATIM_URL = 'https://nominatim.openstreetmap.org/search'
USER_AGENT = 'MinexxFleetGPS/1.0 (contact: totoasofes22@gmail.com)'


def geocode_address(query: str, country_codes: str = 'cd', limit: int = 5):
    """
    Retourne une liste de résultats {display_name, latitude, longitude}.
    """
    q = (query or '').strip()
    if not q:
        return []

    params = {
        'q': q,
        'format': 'json',
        'limit': str(limit),
        'addressdetails': '0',
    }
    if country_codes:
        params['countrycodes'] = country_codes

    url = NOMINATIM_URL + '?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
    except Exception:
        return []

    results = []
    for item in data:
        try:
            results.append({
                'display_name': item.get('display_name') or q,
                'latitude': float(item['lat']),
                'longitude': float(item['lon']),
            })
        except (KeyError, TypeError, ValueError):
            continue
    return results


def geocode_first(query: str, country_codes: str = 'cd'):
    results = geocode_address(query, country_codes=country_codes, limit=1)
    return results[0] if results else None
