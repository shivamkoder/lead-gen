"""
Database Models
All SQLAlchemy models for the application
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from backend.app.extensions import db


class User(UserMixin, db.Model):
    """User model for authentication and authorization"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.String(20), default='user')  # user, admin, affiliate, client
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    affiliate = db.relationship('Affiliate', backref='user', uselist=False)
    client = db.relationship('Client', backref='user', uselist=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Affiliate(db.Model):
    """Affiliate model for tracking partners"""
    __tablename__ = 'affiliates'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    referral_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    commission_rate = db.Column(db.Float, default=0.20)  # 20% default
    payment_email = db.Column(db.String(120))
    total_earnings = db.Column(db.Float, default=0.0)
    pending_payout = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='active')  # active, paused, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    leads = db.relationship('Lead', backref='affiliate')
    campaigns = db.relationship('Campaign', backref='affiliate')
    
    def __repr__(self):
        return f'<Affiliate {self.referral_code}>'


class Client(db.Model):
    """Client model for businesses running campaigns"""
    __tablename__ = 'clients'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    website = db.Column(db.String(200))
    industry = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')  # active, paused
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaigns = db.relationship('Campaign', backref='client')
    
    def __repr__(self):
        return f'<Client {self.company_name}>'


class Campaign(db.Model):
    """Campaign model for advertising campaigns (PPC: client pays per click)"""
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliates.id'))  # legacy; PPC uses aff in URL
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    offer_url = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='draft')  # draft, active, paused, completed
    budget = db.Column(db.Float, default=0.0)
    cost_per_click = db.Column(db.Float, default=0.0)   # client CPC (what advertiser pays)
    affiliate_cpc = db.Column(db.Float, default=0.0)     # affiliate CPC (what we pay per valid click)
    total_clicks = db.Column(db.Integer, default=0)     # valid clicks (for quick dashboard)
    total_spend = db.Column(db.Float, default=0.0)      # client spend = total_clicks * cost_per_click
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    leads = db.relationship('Lead', backref='campaign')
    clicks = db.relationship('Click', backref='campaign', lazy='dynamic')
    
    def __repr__(self):
        return f'<Campaign {self.name}>'


class Click(db.Model):
    """PPC click: one row per tracked click; valid clicks drive affiliate payout and client spend."""
    __tablename__ = 'clicks'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False, index=True)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliates.id'), index=True)
    ip_address = db.Column(db.String(45), nullable=False, index=True)
    user_agent = db.Column(db.String(500))
    fingerprint_hash = db.Column(db.String(64), index=True)  # for duplicate detection
    is_valid = db.Column(db.Boolean, default=True)  # False if duplicate/bot/fraud
    payout_amount = db.Column(db.Float, default=0.0)  # affiliate_cpc at time of click
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships (Campaign.clicks set above)
    affiliate = db.relationship('Affiliate', backref='clicks')
    
    def __repr__(self):
        return f'<Click {self.id} campaign={self.campaign_id} valid={self.is_valid}>'


class Lead(db.Model):
    """Lead model for tracking conversions"""
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliates.id'))
    email = db.Column(db.String(120), nullable=False, index=True)
    name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    meta_data = db.Column('metadata', db.JSON)  # Store additional lead data
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    fingerprint = db.Column(db.String(100), index=True)  # For fraud detection
    status = db.Column(db.String(20), default='pending')  # pending, verified, rejected, converted
    payout_amount = db.Column(db.Float, default=0.0)
    conversion_id = db.Column(db.String(100), unique=True, index=True)  # External conversion ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    conversions = db.relationship('Conversion', backref='lead')
    
    def __repr__(self):
        return f'<Lead {self.id} - {self.email}>'


class Conversion(db.Model):
    """Conversion model for tracking lead conversions"""
    __tablename__ = 'conversions'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='pending')  # pending, paid, failed
    external_id = db.Column(db.String(100), unique=True)
    paid_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Conversion {self.id} - ${self.amount}>'


class Payout(db.Model):
    """Payout model for affiliate payments"""
    __tablename__ = 'payouts'
    
    id = db.Column(db.Integer, primary_key=True)
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliates.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='USD')
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    payment_method = db.Column(db.String(50))  # paypal, bank_transfer, crypto
    payment_reference = db.Column(db.String(100))  # Transaction ID
    processed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    affiliate = db.relationship('Affiliate', backref='payouts')
    
    def __repr__(self):
        return f'<Payout ${self.amount} to Affiliate {self.affiliate_id}>'


class Analytics(db.Model):
    """Analytics model for tracking events"""
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String(50), nullable=False, index=True)  # click, lead, conversion
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    affiliate_id = db.Column(db.Integer, db.ForeignKey('affiliates.id'))
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'))
    meta_data = db.Column('metadata', db.JSON)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    campaign = db.relationship('Campaign', backref='analytics')
    affiliate = db.relationship('Affiliate', backref='analytics')
    
    def __repr__(self):
        return f'<Analytics {self.event_type}>'

