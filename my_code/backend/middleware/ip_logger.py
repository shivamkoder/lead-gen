"""IP logging middleware for capturing visitor metadata.

On each request, extracts and stores comprehensive visitor information:
- IP address and proxy chain
- User agent and device/browser detection
- Referrer and traffic source
- Request timestamp

This data is used for analytics, fraud detection, and traffic analysis.
"""
from flask import request, g
from backend.utils.helpers import (
    get_client_ip,
    get_user_agent,
    detect_device_type,
    extract_browser_name,
    get_referrer,
)
from datetime import datetime


def log_visitor_data():
    """Capture and store visitor profile on each request.
    
    Stores in Flask's g object for request-level access.
    """
    ua = get_user_agent()
    
    g.client_ip = get_client_ip()
    g.user_agent = ua
    g.device_type = detect_device_type(ua)
    g.browser = extract_browser_name(ua)
    g.referrer = get_referrer()
    g.request_timestamp = datetime.utcnow()
    
    # Also store as dict for convenience
    g.visitor_data = {
        'ip_address': g.client_ip,
        'user_agent': g.user_agent,
        'device_type': g.device_type,
        'browser': g.browser,
        'referrer': g.referrer,
        'timestamp': g.request_timestamp.isoformat(),
    }


# Kept for backward compatibility
def log_client_ip():
    """Deprecated: use log_visitor_data() instead."""
    log_visitor_data()
