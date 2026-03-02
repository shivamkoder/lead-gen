"""
Fraud Detection Service
Detect and prevent fraudulent leads and clicks
"""

import hashlib
import re
from datetime import datetime, timedelta


class FraudDetector:
    """Fraud detection for leads and clicks"""
    
    def __init__(self):
        self.rules = [
            self._check_email_quality,
            self._check_ip_quality,
            self._check_user_agent,
            self._check_fingerprint,
            self._check_velocity
        ]
    
    def calculate_score(self, ip_address=None, user_agent=None, email=None, fingerprint=None):
        """
        Calculate fraud score (0-1, higher is more suspicious)
        """
        score = 0.0
        factors = []
        
        # Check email quality
        if email:
            email_score, email_factors = self._check_email_quality(email)
            score += email_score * 0.3
            factors.extend(email_factors)
        
        # Check IP quality
        if ip_address:
            ip_score, ip_factors = self._check_ip_quality(ip_address)
            score += ip_score * 0.3
            factors.extend(ip_factors)
        
        # Check user agent
        if user_agent:
            ua_score, ua_factors = self._check_user_agent(user_agent)
            score += ua_score * 0.2
            factors.extend(ua_factors)
        
        # Check fingerprint
        if fingerprint:
            fp_score, fp_factors = self._check_fingerprint(fingerprint)
            score += fp_score * 0.2
            factors.extend(fp_factors)
        
        return min(score, 1.0), factors
    
    def _check_email_quality(self, email):
        """Check email for fraud indicators"""
        score = 0.0
        factors = []
        
        # Check for disposable email domains
        disposable_domains = [
            'tempmail.com', '10minutemail.com', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'getnada.com'
        ]
        
        if '@' in email:
            domain = email.split('@')[1].lower()
            if domain in disposable_domains:
                score += 0.8
                factors.append('disposable_email_domain')
        
        # Check for suspicious patterns
        if re.match(r'^[a-z0-9]{1,3}@[a-z0-9]', email.lower()):
            score += 0.3
            factors.append('short_local_part')
        
        # Check for numbers in local part
        local_part = email.split('@')[0] if '@' in email else ''
        if any(c.isdigit() for c in local_part) and len(local_part) < 5:
            score += 0.2
            factors.append('numbers_in_short_local_part')
        
        return score, factors
    
    def _check_ip_quality(self, ip_address):
        """Check IP for fraud indicators"""
        score = 0.0
        factors = []
        
        # Check for private IP ranges
        if ip_address.startswith(('10.', '172.16.', '192.168.', '127.')):
            score += 0.5
            factors.append('private_ip')
        
        # Check for known VPN/proxy indicators (simplified)
        # In production, use a VPN detection service
        
        return score, factors
    
    def _check_user_agent(self, user_agent):
        """Check user agent for fraud indicators"""
        score = 0.0
        factors = []
        
        if not user_agent:
            score += 0.3
            factors.append('missing_user_agent')
            return score, factors
        
        # Check for empty or minimal user agent
        if len(user_agent) < 20:
            score += 0.4
            factors.append('suspiciously_short_user_agent')
        
        # Check for known bot user agents
        bot_patterns = ['bot', 'crawler', 'spider', 'scraper']
        user_agent_lower = user_agent.lower()
        if any(pattern in user_agent_lower for pattern in bot_patterns):
            score += 0.7
            factors.append('bot_user_agent')
        
        return score, factors
    
    def _check_fingerprint(self, fingerprint):
        """Check fingerprint for fraud indicators"""
        score = 0.0
        factors = []
        
        if not fingerprint:
            score += 0.2
            factors.append('missing_fingerprint')
            return score, factors
        
        # Check fingerprint length (should be reasonable)
        if len(fingerprint) < 10:
            score += 0.5
            factors.append('short_fingerprint')
        
        return score, factors
    
    def _check_velocity(self, email=None, ip_address=None):
        """Check for velocity/frequency issues"""
        score = 0.0
        factors = []
        
        # In production, query database for recent submissions
        # from same email/IP within time window
        # This is a simplified placeholder
        
        return score, factors
    
    def is_fraudulent(self, score, threshold=0.7):
        """Determine if lead is fraudulent based on score"""
        return score >= threshold

    def is_bot_click(self, user_agent):
        """True if user agent looks like a bot/crawler (do not count as valid click)."""
        if not user_agent or len(user_agent) < 15:
            return True
        ua_lower = user_agent.lower()
        bot_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget', 'python-requests',
            'headless', 'phantom', 'selenium', 'googlebot', 'bingbot', 'yandexbot'
        ]
        return any(p in ua_lower for p in bot_patterns)

    def generate_click_fingerprint(self, ip_address, user_agent, campaign_id, affiliate_id=None):
        """Fingerprint for duplicate click detection (same visitor, same campaign, short window)."""
        raw = f"{ip_address}|{user_agent or ''}|{campaign_id}|{affiliate_id or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def is_duplicate_click(self, fingerprint_hash, existing_hashes_in_window):
        """True if this fingerprint was already seen for a valid click in the window."""
        return fingerprint_hash in existing_hashes_in_window

    def generate_fingerprint(self, user_agent, accept_language, screen_resolution=None):
        """
        Generate browser fingerprint
        In production, use a proper fingerprinting library
        """
        data = f"{user_agent}|{accept_language}"
        if screen_resolution:
            data += f"|{screen_resolution}"
        
        return hashlib.sha256(data.encode()).hexdigest()[:32]
