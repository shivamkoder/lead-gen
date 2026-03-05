"""Hashing utilities for secure data handling.

This module provides:
- Secure token generation for tracking IDs, affiliate links, campaign slugs
- Deterministic hashing for data integrity verification
- Hash validation and verification utilities
- Anti-tampering for tracking URLs

Architecture:
    Internal DB ID (15) → hash.py → Public Tracking Hash (a9f3x7c21d)
    
This separation prevents URL manipulation and click fraud.
"""
import hashlib
import secrets
import hmac
import json
from typing import Optional


# ============================================================================
# PASSWORD & AUTH HASHING (for completeness, though auth.py handles most)
# ============================================================================

def hash_string(text: str, algorithm: str = 'sha256') -> str:
    """Hash a string with the specified algorithm.
    
    Args:
        text: String to hash
        algorithm: 'sha256' (default), 'sha512', or 'md5'
    
    Returns:
        Hex-encoded hash string
    """
    h = hashlib.new(algorithm)
    h.update(text.encode())
    return h.hexdigest()


def verify_hash(text: str, expected_hash: str, algorithm: str = 'sha256') -> bool:
    """Verify that text matches the given hash.
    
    Args:
        text: Original text to verify
        expected_hash: Hash to compare against
        algorithm: Algorithm used for hashing
    
    Returns:
        True if text matches hash, False otherwise
    """
    computed_hash = hash_string(text, algorithm)
    return hmac.compare_digest(computed_hash, expected_hash)


# ============================================================================
# SECURE TOKEN GENERATION
# ============================================================================

def generate_token(length: int = 32) -> str:
    """Generate a cryptographically secure random token.
    
    Used for:
    - Session tokens
    - API keys
    - CSRF tokens
    
    Args:
        length: Length parameter for token generation (results in ~1.33x longer base64 output)
    
    Returns:
        URL-safe random token
    """
    return secrets.token_urlsafe(length)


def generate_tracking_id(prefix: str = '') -> str:
    """Generate a unique tracking ID for campaigns, affiliates, or clicks.
    
    This is the **public-facing identifier** used in tracking URLs.
    Example: campaign ID 15 → tracking ID "a9f3_x7c2_1d9k"
    
    Args:
        prefix: Optional prefix (e.g., 'aff_', 'cmp_', 'clk_')
    
    Returns:
        Unique alphanumeric tracking ID
    """
    token = secrets.token_hex(8)  # 16 hex chars = 64 bits entropy
    if prefix:
        return f"{prefix}{token}"
    return token


def generate_affiliate_token() -> str:
    """Generate a unique token for affiliate accounts.
    
    Used to:
    - Track affiliate performance
    - Generate affiliate dashboard URLs
    - Authenticate affiliate API requests
    
    Returns:
        Unique affiliate tracking token
    """
    return generate_tracking_id(prefix='aff_')


def generate_campaign_slug(campaign_name: str, campaign_id: Optional[int] = None) -> str:
    """Generate a URL-friendly slug for a campaign.
    
    This slug is used in tracking links: /r/<slug>
    
    Example:
        campaign_name="Q1 Facebook Ads"
        campaign_id=42
        → slug="q1_facebook_ads_42_xyz789"
    
    Args:
        campaign_name: Campaign name from user
        campaign_id: Optional database ID (mixed to create uniqueness)
    
    Returns:
        URL-safe slug (lowercase, alphanumeric + underscore/dash)
    """
    # Sanitize name: lowercase, replace spaces/special chars with underscore
    slug_base = campaign_name.lower().strip()
    slug_base = ''.join(c if c.isalnum() else '_' for c in slug_base)
    slug_base = '_'.join(slug_base.split('_'))  # Remove multiple underscores
    slug_base = slug_base[:30]  # Limit length
    
    # Add campaign ID if provided (makes it unique)
    if campaign_id:
        slug = f"{slug_base}_{campaign_id}"
    else:
        slug = slug_base
    
    # Add random suffix to guarantee uniqueness even if names collide
    random_suffix = secrets.token_hex(3)  # 6 hex chars
    slug = f"{slug}_{random_suffix}"
    
    return slug


# ============================================================================
# DATA INTEGRITY HASHING (HMAC-based)
# ============================================================================

def generate_data_hash(data: dict, secret_key: str) -> str:
    """Generate an HMAC-SHA256 hash of data for integrity verification.
    
    Used to prevent tampering with click data, redirect parameters, etc.
    
    Example:
        data = {'campaign_id': 15, 'affiliate_id': 7}
        hash = generate_data_hash(data, SECRET_KEY)
        # Later, verify that data + hash haven't changed
    
    Args:
        data: Dictionary to hash (will be JSON-serialized)
        secret_key: Secret key for HMAC (application SECRET_KEY)
    
    Returns:
        HMAC-SHA256 hex digest
    """
    # Serialize data consistently for reproducible hashes
    json_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
    return hmac.new(
        secret_key.encode(),
        json_data.encode(),
        hashlib.sha256
    ).hexdigest()


def verify_data_hash(data: dict, provided_hash: str, secret_key: str) -> bool:
    """Verify that data hasn't been tampered with.
    
    Args:
        data: Original data (as dict)
        provided_hash: Hash to verify against
        secret_key: Secret key for HMAC
    
    Returns:
        True if data is authentic, False if tampered
    """
    computed_hash = generate_data_hash(data, secret_key)
    return hmac.compare_digest(computed_hash, provided_hash)


# ============================================================================
# CLICK TRACKING SECURITY
# ============================================================================

def generate_click_token() -> str:
    """Generate a unique token for a tracked click.
    
    Used to:
    - Create immutable click records
    - Prevent duplicate click processing
    - Track click uniqueness
    
    Returns:
        Unique click token
    """
    return generate_tracking_id(prefix='clk_')


def hash_click_parameters(campaign_slug: str, affiliate_id: Optional[str], 
                         user_agent: str, ip_address: str, secret_key: str) -> str:
    """Generate a hash of click parameters for deduplication & validation.
    
    This creates a fingerprint of the click to prevent duplicate processing.
    
    Args:
        campaign_slug: Campaign tracking slug
        affiliate_id: Affiliate identifier (may be None)
        user_agent: User-Agent header
        ip_address: Client IP address
        secret_key: Application SECRET_KEY
    
    Returns:
        HMAC-SHA256 hash of click parameters
    """
    params = {
        'slug': campaign_slug,
        'aff': affiliate_id or '',
        'ua': user_agent,
        'ip': ip_address,
    }
    return generate_data_hash(params, secret_key)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def is_valid_token_format(token: str, prefix: Optional[str] = None) -> bool:
    """Validate that a token matches expected format.
    
    Args:
        token: Token to validate
        prefix: Expected prefix (e.g., 'aff_', 'clk_'). If None, any format OK.
    
    Returns:
        True if token format is valid
    """
    if not token or not isinstance(token, str):
        return False
    
    if prefix:
        return token.startswith(prefix) and len(token) > len(prefix)
    
    return len(token) >= 16  # Minimum reasonable length


def shorten_hash(hash_value: str, length: int = 10) -> str:
    """Shorten a hash for URL usage.
    
    Example:
        full_hash = "a9f3x7c21d8b4f6e2a9c7d1e3b5f8a2c"
        short = shorten_hash(full_hash, 10)
        → "a9f3x7c21d"
    
    Args:
        hash_value: Full hash or token
        length: Desired output length
    
    Returns:
        First N characters of hash
    """
    return hash_value[:length]
