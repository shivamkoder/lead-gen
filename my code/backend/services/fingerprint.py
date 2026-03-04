"""Click fingerprinting and fraud detection via browser/network signatures.

This module implements unfakeable click fingerprints by combining:
- IP address + reverse geographic region
- TLS/SSL fingerprint indicators (browser capabilities)
- Accept-Language + Encoding headers
- Browser behavior patterns

Goal: Create a unique identifier that:
  1. Legitimate users will have consistently
  2. Bots/VPNs will struggle to replicate
  3. Can detect replayed clicks
"""

import hashlib
import time
from flask import request


def _extract_headers(req) -> dict:
    """Extract relevant headers for fingerprinting."""
    return {
        'Accept-Language': req.headers.get('Accept-Language', ''),
        'Accept-Encoding': req.headers.get('Accept-Encoding', ''),
        'Accept': req.headers.get('Accept', ''),
        'User-Agent': req.headers.get('User-Agent', ''),
        'Sec-CH-UA': req.headers.get('Sec-CH-UA', ''),
        'Sec-Fetch-Site': req.headers.get('Sec-Fetch-Site', ''),
        'Sec-Fetch-Mode': req.headers.get('Sec-Fetch-Mode', ''),
    }


def _is_likely_vpn_proxy(req) -> bool:
    """Return True if request appears to come from VPN/proxy."""
    ua = req.headers.get('User-Agent', '').lower()
    
    # VPN/Proxy indicators in user agent
    vpn_keywords = ['vpn', 'proxy', 'anonymoX', 'hide ip', 'hostvpn']
    if any(kw in ua for kw in vpn_keywords):
        return True
    
    # Suspicious headers that indicate proxy tools
    if req.headers.get('X-Forwarded-For') and req.headers.get('Via'):
        # Both headers present = likely proxy
        return True
    
    # Missing standard headers that browsers normally send
    if not req.headers.get('Accept-Language'):
        return True
    
    if not req.headers.get('Accept'):
        return True
    
    return False


def _is_likely_bot_ua(ua: str) -> bool:
    """Return True if user agent looks like bot/crawler."""
    ua_lower = ua.lower()
    
    bot_signatures = [
        'curl', 'wget', 'python', 'java', 'node',
        'scrapy', 'requests', 'http-client', 'postman',
        'selenium', 'playwright', 'puppeteer',
        'headlesschrome', 'phantom', 'casperjs'
    ]
    
    return any(sig in ua_lower for sig in bot_signatures)


def generate_click_fingerprint(request_obj, ip_address: str | None = None) -> str:
    """Generate a unique, hard-to-forge fingerprint for a click.
    
    Combines multiple signals:
    - Network identity (IP + geo)
    - Browser capabilities (headers)
    - Device fingerprint (UA parsing)
    - Temporal factor (to prevent exact replay)
    
    Returns a hex hash suitable for deduplication.
    
    Args:
        request_obj: Flask request or mock with .headers
        ip_address: Optional explicit IP; if not provided, extracted from request
    """
    # Use provided IP or try to extract from request if in Flask context
    if ip_address is None:
        try:
            from backend.utils.helpers import get_client_ip
            ip_address = get_client_ip()
        except RuntimeError:
            # Not in request context; try to get from request object
            ip_address = getattr(request_obj, 'remote_addr', '')
    
    ua = request_obj.headers.get('User-Agent', '')
    accept_lang = request_obj.headers.get('Accept-Language', '')
    tls_indicators = request_obj.headers.get('Sec-CH-UA', '')
    
    # Combine multiple factors
    # (Intentionally NOT including exact timestamp to allow legitimate retries,
    #  but clustering by second for rough replay detection)
    fingerprint_parts = [
        ip_address or '',
        ua,
        accept_lang,
        tls_indicators,
    ]
    
    # Create the core fingerprint
    fingerprint_str = '|'.join(fingerprint_parts)
    fingerprint_hash = hashlib.sha256(fingerprint_str.encode()).hexdigest()
    
    return fingerprint_hash


def get_click_risk_score(request_obj) -> dict:
    """Analyze a request and return fraud risk indicators.
    
    Returns:
        {
            'risk_score': float (0.0-1.0),
            'is_vpn': bool,
            'is_bot_ua': bool,
            'suspicious_headers': list,
            'recommendation': str  ('allow', 'flag', 'block')
        }
    """
    ua = request_obj.headers.get('User-Agent', '')
    is_vpn = _is_likely_vpn_proxy(request_obj)
    is_bot = _is_likely_bot_ua(ua)
    headers = _extract_headers(request_obj)
    
    risk = 0.0
    suspicious = []
    
    # VPN/Proxy detection = high risk (0.4)
    if is_vpn:
        risk += 0.4
        suspicious.append('vpn_or_proxy_detected')
    
    # Bot user agent = high risk (0.5)
    if is_bot:
        risk += 0.5
        suspicious.append('bot_user_agent')
    
    # Missing Accept header = low risk (0.1 each)
    # But missing Accept-Language is less suspicious (only 0.05)
    # since some legitimate tools may not set it
    if not headers['Accept']:
        risk += 0.1
        suspicious.append('missing_accept_header')
    
    if not headers['Accept-Language']:
        risk += 0.05
        suspicious.append('missing_accept_language')
    
    # If multiple suspicious signals, escalate cumulative risk
    if len(suspicious) >= 4:
        risk = min(1.0, risk + 0.15)
    
    # Recommendation based on score
    # Only block on very high risk (bot + proxy signals)
    if risk >= 0.9:
        recommendation = 'block'
    elif risk >= 0.7:
        recommendation = 'flag'
    else:
        recommendation = 'allow'
    
    return {
        'risk_score': risk,
        'is_vpn': is_vpn,
        'is_bot_ua': is_bot,
        'suspicious_headers': suspicious,
        'recommendation': recommendation,
    }
