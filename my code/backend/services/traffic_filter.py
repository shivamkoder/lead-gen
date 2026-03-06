"""Traffic filtering logic.

Checks (in order, cheapest first):
  1. Bot user-agent detection
  2. IP blacklist (BLACKLISTED_IPS env var)
  3. Per-IP rate limiting  — Redis-backed in production, in-memory fallback for dev
  4. VPN / proxy heuristics (header-based, no paid API required)
  5. Advanced fraud score from fingerprint.py

Redis rate limiting works correctly across all Gunicorn workers.
Set REDIS_URL env var to enable it; falls back to in-memory if not set.
"""

import os
import time
from collections import deque

from backend.middleware.bot_detection import detect_bot
from backend.services.fingerprint import (
    get_click_risk_score,
    generate_click_fingerprint,
    _is_likely_vpn_proxy,   # already implemented in fingerprint.py
)

# ── Configuration ─────────────────────────────────────────────────────────────
_BLACKLIST: set = set()
if os.getenv('BLACKLISTED_IPS'):
    _BLACKLIST = {ip.strip() for ip in os.getenv('BLACKLISTED_IPS', '').split(',') if ip.strip()}

_RATE_LIMIT = int(os.getenv('RATE_LIMIT_PER_MIN', '60'))   # clicks per IP per minute
_REDIS_URL   = os.getenv('REDIS_URL')

# ── Rate limit backend ────────────────────────────────────────────────────────

def _make_redis_client():
    """Return a Redis client or None if Redis is unavailable."""
    if not _REDIS_URL:
        return None
    try:
        import redis
        client = redis.from_url(_REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
        client.ping()          # fail fast if Redis is down
        return client
    except Exception:
        return None


_redis = _make_redis_client()

# In-memory fallback (single-process only)
_history: dict[str, deque] = {}


def _check_rate_redis(ip: str) -> bool:
    """Rate check using Redis sorted sets — works across all workers."""
    key   = f'rl:{ip}'
    now   = time.time()
    window = 60.0

    pipe = _redis.pipeline()
    pipe.zremrangebyscore(key, 0, now - window)   # drop stale entries
    pipe.zadd(key, {str(now): now})               # record this hit
    pipe.zcard(key)                               # count hits in window
    pipe.expire(key, 120)                         # auto-cleanup
    results = pipe.execute()

    count = results[2]
    return count <= _RATE_LIMIT


def _check_rate_memory(ip: str) -> bool:
    """Rate check using in-memory deque — single-process only."""
    if not ip:
        return True
    now = time.time()
    dq  = _history.setdefault(ip, deque())
    while dq and dq[0] < now - 60:
        dq.popleft()
    if len(dq) >= _RATE_LIMIT:
        return False
    dq.append(now)
    return True


def _check_rate(ip: str) -> bool:
    if _redis:
        try:
            return _check_rate_redis(ip)
        except Exception:
            pass   # Redis error — fall through to memory
    return _check_rate_memory(ip)


# ── VPN / proxy detection ─────────────────────────────────────────────────────

def _is_vpn_or_proxy(request) -> bool:
    """
    Heuristic VPN/proxy detection — no paid API required.
    Uses header signals already implemented in fingerprint.py.

    For stronger detection in production, integrate a service like
    IPHub (free tier), ip-api.com, or ipqualityscore.com and set
    VPN_CHECK_API_KEY + VPN_CHECK_URL env vars.
    """
    # Header-based heuristics (free, built-in)
    if _is_likely_vpn_proxy(request):
        return True

    # Optional: external IP reputation API
    api_url = os.getenv('VPN_CHECK_URL')      # e.g. https://v2.api.iphub.info/ip/{ip}
    api_key = os.getenv('VPN_CHECK_API_KEY')
    if api_url and api_key:
        ip = getattr(request, 'remote_addr', '') or ''
        if ip:
            try:
                import httpx
                url  = api_url.replace('{ip}', ip)
                resp = httpx.get(url, headers={'X-Key': api_key}, timeout=1.5)
                if resp.status_code == 200:
                    data  = resp.json()
                    # IPHub: block=1 means hosting/VPN, block=2 means residential proxy
                    block = data.get('block', 0)
                    if block in (1, 2):
                        return True
            except Exception:
                pass   # Never let a VPN check crash a click

    return False


# ── Email verification helper ─────────────────────────────────────────────────

def _check_email_domain(email: str) -> bool:
    """
    Basic email domain MX-record check (no external API).
    Returns True if the domain appears to have valid MX records.
    Only used for lead submission, not for click tracking.
    """
    if not email or '@' not in email:
        return False
    domain = email.split('@')[1].lower()
    # Known disposable email domains blocklist (extend as needed)
    disposable = {
        'mailinator.com', 'guerrillamail.com', 'tempmail.com', 'throwaway.email',
        'yopmail.com', 'sharklasers.com', 'trashmail.com', 'maildrop.cc',
        '10minutemail.com', 'dispostable.com', 'fakeinbox.com',
    }
    if domain in disposable:
        return False
    try:
        import socket
        socket.getaddrinfo(domain, None)   # basic DNS check
        return True
    except socket.gaierror:
        return False


# ── Public API ────────────────────────────────────────────────────────────────

def is_valid_traffic(request) -> bool:
    """
    Return True when the request should be counted as a valid click.
    Checks are ordered cheapest → most expensive.
    """
    ua = request.headers.get('User-Agent', '')
    if not ua or detect_bot(ua):
        return False

    ip = getattr(request, 'remote_addr', '') or ''
    if ip in _BLACKLIST:
        return False

    if not _check_rate(ip):
        return False

    if _is_vpn_or_proxy(request):
        return False

    # Advanced fraud score (fingerprint.py)
    risk = get_click_risk_score(request)
    if risk.get('recommendation') == 'block':
        return False

    return True


def get_traffic_risk(request) -> dict:
    """Return detailed risk assessment dict for logging/analytics."""
    return get_click_risk_score(request)


def get_click_fingerprint(request) -> str:
    """Return the unique fingerprint for this click."""
    return generate_click_fingerprint(request)


def is_valid_email_domain(email: str) -> bool:
    """Check if an email domain is real and not disposable."""
    return _check_email_domain(email)
