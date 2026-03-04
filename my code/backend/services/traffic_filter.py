"""Traffic filtering logic.

This service inspects incoming requests and decides whether a click
should be considered legitimate before it is processed by ``tracker``.
It currently implements:

* bot user agent detection
* configurable IP blacklist (via environment variable)
* simple per-IP rate limiting (requests per minute)

The implementation is kept intentionally small; a production deployment
would likely use Redis or another shared cache for rate‑limits and
blacklist storage.
"""

import os
import time
from collections import deque

from backend.middleware.bot_detection import detect_bot
from backend.services.fingerprint import get_click_risk_score, generate_click_fingerprint

# ---------- configuration ----------
_BLACKLIST = set()
if os.getenv('BLACKLISTED_IPS'):
    _BLACKLIST = {ip.strip() for ip in os.getenv('BLACKLISTED_IPS').split(',') if ip.strip()}

_RATE_LIMIT = int(os.getenv('RATE_LIMIT_PER_MIN', '60'))  # clicks per IP per minute

# in‑memory history mapping ip -> deque of timestamp floats
_history = {}


# ---------- helpers ----------

def _check_rate(ip_address: str) -> bool:
    """Return False if *ip_address* has exceeded the rate limit."""
    if not ip_address:
        return True
    now = time.time()
    dq = _history.setdefault(ip_address, deque())
    # purge entries older than 60 seconds
    while dq and dq[0] < now - 60:
        dq.popleft()
    if len(dq) >= _RATE_LIMIT:
        return False
    dq.append(now)
    return True


# ---------- public API ----------

def is_valid_traffic(request) -> bool:
    """Return ``True`` when the request should be counted as a click.

    The checks are intentionally ordered so that cheap tests run first.
    Includes both basic filtering and advanced fraud detection.
    """
    ua = request.headers.get('User-Agent', '')
    if not ua or detect_bot(ua):
        return False

    # ``request`` may be a simplified object in tests, so use getattr
    # to avoid AttributeError when ``remote_addr`` is missing.
    ip = getattr(request, 'remote_addr', '') or ''
    if ip in _BLACKLIST:
        return False

    if not _check_rate(ip):
        return False

    # Advanced fraud detection: check risk score
    risk_data = get_click_risk_score(request)
    if risk_data['recommendation'] == 'block':
        return False
    # 'flag' and 'allow' both pass traffic, but flag is logged for analysis

    return True


def get_traffic_risk(request) -> dict:
    """Return detailed risk assessment for a click.
    
    Useful for logging, analytics, and fraud analysis.
    """
    return get_click_risk_score(request)


def get_click_fingerprint(request) -> str:
    """Return the unique fingerprint for this click."""
    return generate_click_fingerprint(request)
