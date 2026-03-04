"""Helper functions for common operations.

This module contains lightweight, dependency-free helpers used across the
application: request parsing, URL validation, ID generation, time helpers,
user-agent parsing, and safe conversions.
"""
from flask import request
from datetime import datetime, timezone
import uuid
import re
from typing import Optional


def get_client_ip(req: Optional[object] = None) -> Optional[str]:
    """Return the client's IP address.

    Accepts an optional `req` (Flask request) for easier unit testing. If not
    provided uses the global `request`.
    """
    r = req or request
    xff = r.headers.get('X-Forwarded-For')
    if xff:
        # X-Forwarded-For may contain a list
        return xff.split(',')[0].strip()
    return getattr(r, 'remote_addr', None)


def get_user_agent(req: Optional[object] = None) -> str:
    r = req or request
    return r.headers.get('User-Agent', '')


def validate_url(url: str) -> bool:
    """Basic URL validation to prevent open redirect to unsafe schemes.

    This allows only http or https schemes and performs a simple regex check.
    For more strict validation, integrate ``validators`` or ``urllib.parse``
    checks.
    """
    if not isinstance(url, str) or not url:
        return False
    # Accept only http(s)
    return bool(re.match(r'^https?://', url.strip().lower()))


def generate_click_id() -> str:
    """Return a stable UUID4-based click id as string."""
    return str(uuid.uuid4())


def now_utc() -> datetime:
    """Return timezone-aware current UTC time."""
    return datetime.now(timezone.utc)


def safe_int(value, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def parse_accept_language(req: Optional[object] = None) -> str:
    """Return the primary Accept-Language token (e.g., 'en-US')."""
    r = req or request
    val = r.headers.get('Accept-Language', '')
    if not val:
        return ''
    # take the first token before comma
    return val.split(',')[0].strip()


def detect_device_type(user_agent: str) -> str:
    """Detect device type from user agent.

    Returns one of: 'mobile', 'tablet', 'desktop', 'bot', 'unknown'
    """
    if not user_agent:
        return 'unknown'
    ua_lower = user_agent.lower()

    # Bot detection first (includes tools/scripts)
    bot_keywords = ['bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python', 'java', 'node', 'requests']
    if any(kw in ua_lower for kw in bot_keywords):
        return 'bot'

    # Mobile detection
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
    if any(kw in ua_lower for kw in mobile_keywords):
        return 'mobile'

    # Tablet detection
    tablet_keywords = ['tablet', 'ipad', 'kindle']
    if any(kw in ua_lower for kw in tablet_keywords):
        return 'tablet'

    # Desktop detection (has common desktop patterns)
    if 'windows' in ua_lower or 'macintosh' in ua_lower or 'linux' in ua_lower:
        if 'mobile' not in ua_lower:
            return 'desktop'

    return 'unknown'


def extract_browser_name(user_agent: str) -> str:
    """Extract browser name from user agent.

    Returns browser name or 'unknown'
    """
    if not user_agent:
        return 'unknown'
    ua_lower = user_agent.lower()

    # iOS Safari (on iPhone/iPad) usually doesn't have explicit Safari, but mobile+webkit indicates Safari
    if ('iphone' in ua_lower or 'ipad' in ua_lower or 'ipod' in ua_lower) and 'webkit' in ua_lower:
        if 'chrome' not in ua_lower and 'firefox' not in ua_lower:
            return 'safari'

    if 'edg' in ua_lower:
        return 'edge'
    elif 'chrome' in ua_lower and 'edg' not in ua_lower:
        return 'chrome'
    elif 'firefox' in ua_lower:
        return 'firefox'
    elif 'safari' in ua_lower and 'chrome' not in ua_lower:
        return 'safari'
    elif 'opera' in ua_lower or 'opr' in ua_lower:
        return 'opera'
    elif 'trident' in ua_lower or 'msie' in ua_lower:
        return 'ie'

    return 'unknown'


def get_referrer(req: Optional[object] = None) -> str:
    r = req or request
    return r.headers.get('Referer', '')


def get_visitor_data(req: Optional[object] = None) -> dict:
    """Extract comprehensive visitor data from request.

    Returns dict with visitor profile including IP, device, browser, referrer, etc.
    """
    r = req or request
    ua = get_user_agent(r)
    return {
        'ip_address': get_client_ip(r),
        'user_agent': ua,
        'accept_language': parse_accept_language(r),
        'device_type': detect_device_type(ua),
        'browser': extract_browser_name(ua),
        'referrer': get_referrer(r),
        'timestamp': now_utc().isoformat(),
    }
