"""Database models for the lead gen platform."""
from backend.database.db import db
from werkzeug.security import generate_password_hash, check_password_hash


class User(db.Model):
    """Simple user model for authentication and roles."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='user')
    created_at = db.Column(db.DateTime, default=db.func.now())

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class Campaign(db.Model):
    """Campaign model for tracking lead generation campaigns."""
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)  # Public tracking URL slug
    tracking_id = db.Column(db.String(64), unique=True, nullable=False)  # Additional public identifier (hash.py generated)
    target_url = db.Column(db.String(2048), nullable=False)
    description = db.Column(db.Text)
    cpc = db.Column(db.Float, default=0.0)
    budget = db.Column(db.Float, default=0.0)
    spend = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(50), default='active')
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, default=db.func.now(), onupdate=db.func.now())


class Click(db.Model):
    """Click event model."""
    __tablename__ = 'clicks'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    affiliate_id = db.Column(db.Integer, nullable=True)  # optional affiliate who drove click
    timestamp = db.Column(db.DateTime, default=db.func.now(), index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    device_type = db.Column(db.String(20))  # mobile, tablet, desktop, bot, unknown
    browser = db.Column(db.String(50))  # chrome, firefox, safari, edge, etc.
    referrer = db.Column(db.Text)  # traffic source URL
    fingerprint = db.Column(db.String(64), index=True)  # SHA256 hex of click identity
    risk_score = db.Column(db.Float, default=0.0)  # 0.0-1.0 fraud likelihood
    payout = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='ok')  # ok, duplicate, invalid, vpn, etc.

    def __repr__(self):
        return f"<Click {self.id} camp={self.campaign_id} ip={self.ip_address}>"

def campaign_to_dict(campaign):
    """Utility converting a Campaign instance to JSON-serializable dict."""
    return {
        'id': campaign.id,
        'name': campaign.name,
        'slug': campaign.slug,
        'tracking_id': campaign.tracking_id,
        'target_url': campaign.target_url,
        'description': campaign.description,
        'cpc': campaign.cpc,
        'budget': campaign.budget,
        'spend': campaign.spend,
        'status': campaign.status,
        'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
        'updated_at': campaign.updated_at.isoformat() if campaign.updated_at else None,
    }


class Lead(db.Model):
    """Lead model for tracking lead conversions."""
    __tablename__ = 'leads'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'))
    email = db.Column(db.String(255))
    status = db.Column(db.String(50), default='pending')
    created_at = db.Column(db.DateTime, default=db.func.now())
