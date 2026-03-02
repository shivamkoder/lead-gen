"""
Helper Functions
Utility functions used throughout the application
"""

import re
import secrets
import string
from datetime import datetime
from flask import request


def generate_referral_code(length=12):
    """Generate unique referral code for affiliates"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_token(length=32):
    """Generate random token"""
    return secrets.token_urlsafe(length)


def validate_email(email):
    """Validate email format"""
    if not email:
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Validate password strength
    Returns: (is_valid, error_message)
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"
    
    return True, None


def format_currency(amount, currency='USD'):
    """Format amount as currency"""
    symbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'JPY': '¥'
    }
    
    symbol = symbols.get(currency, currency + ' ')
    
    if currency == 'JPY':
        return f"{symbol}{int(amount)}"
    
    return f"{symbol}{amount:,.2f}"


def paginate_query(query, page=None, per_page=None):
    """
    Paginate a SQLAlchemy query
    Returns: pagination object
    """
    if page is None:
        page = request.args.get('page', 1, type=int)
    
    if per_page is None:
        per_page = request.args.get('per_page', 20, type=int)
    
    # Limit max per page
    per_page = min(per_page, 100)
    
    return query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=False
    )


def get_client_ip():
    """Get client IP address from request"""
    # Check for forwarded header (if behind proxy)
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    
    return request.remote_addr


def parse_user_agent():
    """Parse user agent string"""
    user_agent = request.headers.get('User-Agent', '')
    
    # Simple parsing (in production, use ua-parser library)
    browser = 'Unknown'
    os = 'Unknown'
    
    if 'Chrome' in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent:
        browser = 'Safari'
    elif 'Edge' in user_agent:
        browser = 'Edge'
    
    if 'Windows' in user_agent:
        os = 'Windows'
    elif 'Mac' in user_agent:
        os = 'macOS'
    elif 'Linux' in user_agent:
        os = 'Linux'
    elif 'Android' in user_agent:
        os = 'Android'
    elif 'iOS' in user_agent:
        os = 'iOS'
    
    return {
        'browser': browser,
        'os': os,
        'raw': user_agent
    }


def sanitize_input(text, max_length=None):
    """Sanitize user input"""
    if not text:
        return text
    
    # Remove null bytes
    text = text.replace('\x00', '')
    
    # Trim whitespace
    text = text.strip()
    
    # Limit length
    if max_length:
        text = text[:max_length]
    
    return text


def calculate_percentage(value, total):
    """Calculate percentage safely"""
    if not total or total == 0:
        return 0
    
    return round((value / total) * 100, 2)


def format_date(date, format='%Y-%m-%d'):
    """Format datetime object"""
    if not date:
        return None
    
    if isinstance(date, str):
        return date
    
    return date.strftime(format)


def format_datetime(dt, format='%Y-%m-%d %H:%M:%S'):
    """Format datetime object"""
    if not dt:
        return None
    
    if isinstance(dt, str):
        return dt
    
    return dt.strftime(format)


def get_time_ago(dt):
    """Get human-readable time ago string"""
    if not dt:
        return 'Unknown'
    
    now = datetime.utcnow()
    diff = now - dt
    
    seconds = diff.total_seconds()
    
    if seconds < 60:
        return 'just now'
    elif seconds < 3600:
        minutes = int(seconds / 60)
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif seconds < 86400:
        hours = int(seconds / 3600)
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif seconds < 2592000:
        days = int(seconds / 86400)
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif seconds < 31536000:
        months = int(seconds / 2592000)
        return f'{months} month{"s" if months != 1 else ""} ago'
    else:
        years = int(seconds / 31536000)
        return f'{years} year{"s" if years != 1 else ""} ago'
