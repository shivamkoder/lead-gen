"""
Client (Advertiser) Routes
Campaign creation, listing, and PPC dashboard (clicks, spend).
"""

import time
from flask import Blueprint, request, jsonify
from flask_login import current_user
from backend.app.extensions import db
from backend.app.models import Client, Campaign, Click
from backend.app.utils.decorators import login_required

client_bp = Blueprint('client', __name__)


def _ensure_client():
    """Ensure current user has a Client record; create if role is client and missing."""
    if not current_user.is_authenticated:
        return None
    if current_user.client:
        return current_user.client
    if current_user.role == 'client':
        client = Client(
            user_id=current_user.id,
            company_name=current_user.username or 'My Company',
            website=request.host_url.rstrip('/'),
        )
        db.session.add(client)
        db.session.commit()
        return client
    return None


@client_bp.route('/register', methods=['POST'])
@login_required
def register_client():
    """Register as a client (advertiser). Creates Client record."""
    if current_user.client:
        return jsonify({'error': 'Already registered as client'}), 400
    data = request.get_json() or {}
    client = Client(
        user_id=current_user.id,
        company_name=data.get('company_name', current_user.username or 'My Company'),
        website=data.get('website', ''),
        industry=data.get('industry', ''),
    )
    db.session.add(client)
    current_user.role = 'client'
    db.session.commit()
    return jsonify({
        'message': 'Client registered successfully',
        'client': {
            'id': client.id,
            'company_name': client.company_name,
            'website': client.website,
        },
    }), 201


@client_bp.route('/campaigns', methods=['GET'])
@login_required
def list_campaigns():
    """List campaigns for the current client (PPC: clicks, spend, status)."""
    client = _ensure_client()
    if not client:
        return jsonify({'error': 'Not registered as client'}), 404
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    q = Campaign.query.filter_by(client_id=client.id)
    if status:
        q = q.filter_by(status=status)
    campaigns = q.order_by(Campaign.updated_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    base_url = request.host_url.rstrip('/')
    return jsonify({
        'campaigns': [
            {
                'id': c.id,
                'name': c.name,
                'description': c.description,
                'offer_url': c.offer_url,
                'status': c.status,
                'budget': float(c.budget or 0),
                'cost_per_click': float(c.cost_per_click or 0),
                'affiliate_cpc': float(c.affiliate_cpc or 0),
                'total_clicks': c.total_clicks or 0,
                'total_spend': float(c.total_spend or 0),
                'tracking_link_example': f"{base_url}/t/{c.id}?aff=AFFILIATE_ID",
                'created_at': c.created_at.isoformat() if c.created_at else None,
            }
            for c in campaigns.items
        ],
        'total': campaigns.total,
        'page': campaigns.page,
        'pages': campaigns.pages,
    }), 200


@client_bp.route('/campaigns', methods=['POST'])
@login_required
def create_campaign():
    """Create a PPC campaign (target URL, budget, client CPC, optional affiliate CPC)."""
    client = _ensure_client()
    if not client:
        return jsonify({'error': 'Not registered as client'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'JSON body required'}), 400
    name = data.get('name')
    offer_url = data.get('offer_url') or data.get('target_url')
    if not name or not offer_url:
        return jsonify({'error': 'name and offer_url (or target_url) are required'}), 400
    budget = float(data.get('budget', 0))
    cost_per_click = float(data.get('cost_per_click', 0))
    affiliate_cpc = float(data.get('affiliate_cpc', 0))
    if cost_per_click <= 0:
        return jsonify({'error': 'cost_per_click must be positive'}), 400
    campaign = Campaign(
        client_id=client.id,
        name=name,
        description=data.get('description'),
        offer_url=offer_url,
        budget=budget,
        cost_per_click=cost_per_click,
        affiliate_cpc=affiliate_cpc if affiliate_cpc > 0 else (cost_per_click * 0.6),
        status='active',
    )
    db.session.add(campaign)
    db.session.commit()
    base_url = request.host_url.rstrip('/')
    # notify client room of updated dashboard
    try:
        from backend.app.extensions import socketio
        campaigns = Campaign.query.filter_by(client_id=client.id).all()
        total_clicks = sum(c.total_clicks or 0 for c in campaigns)
        total_spend = sum(float(c.total_spend or 0) for c in campaigns)
        active_count = sum(1 for c in campaigns if c.status == 'active')
        socketio.emit('dashboard_update', {
            'ts': time.time(),
            'summary': {
                'total_campaigns': len(campaigns),
                'active_campaigns': active_count,
                'total_clicks': total_clicks,
                'total_spend': round(total_spend, 2),
            },
            'campaigns': [
                {
                    'id': c.id,
                    'name': c.name,
                    'status': c.status,
                    'total_clicks': c.total_clicks or 0,
                    'total_spend': float(c.total_spend or 0),
                }
                for c in campaigns[:50]
            ],
        }, room=f'client_{client.id}')
    except Exception:
        pass
    
    return jsonify({
        'message': 'Campaign created',
        'campaign': {
            'id': campaign.id,
            'name': campaign.name,
            'offer_url': campaign.offer_url,
            'cost_per_click': campaign.cost_per_click,
            'affiliate_cpc': campaign.affiliate_cpc,
            'budget': campaign.budget,
            'status': campaign.status,
            'tracking_link_example': f"{base_url}/t/{campaign.id}?aff=AFFILIATE_ID",
        },
    }), 201


@client_bp.route('/campaigns/<int:campaign_id>', methods=['GET'])
@login_required
def get_campaign(campaign_id):
    """Get one campaign with PPC stats (clicks, spend) for client dashboard."""
    client = _ensure_client()
    if not client:
        return jsonify({'error': 'Not registered as client'}), 404
    campaign = Campaign.query.filter_by(id=campaign_id, client_id=client.id).first()
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    base_url = request.host_url.rstrip('/')
    return jsonify({
        'campaign': {
            'id': campaign.id,
            'name': campaign.name,
            'description': campaign.description,
            'offer_url': campaign.offer_url,
            'status': campaign.status,
            'budget': float(campaign.budget or 0),
            'cost_per_click': float(campaign.cost_per_click or 0),
            'affiliate_cpc': float(campaign.affiliate_cpc or 0),
            'total_clicks': campaign.total_clicks or 0,
            'total_spend': float(campaign.total_spend or 0),
            'tracking_link_example': f"{base_url}/t/{campaign.id}?aff=AFFILIATE_ID",
            'created_at': campaign.created_at.isoformat() if campaign.created_at else None,
        },
    }), 200


@client_bp.route('/campaigns/<int:campaign_id>', methods=['PUT'])
@login_required
def update_campaign(campaign_id):
    """Update campaign (status, budget, CPC)."""
    client = _ensure_client()
    if not client:
        return jsonify({'error': 'Not registered as client'}), 404
    campaign = Campaign.query.filter_by(id=campaign_id, client_id=client.id).first()
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    data = request.get_json() or {}
    if 'status' in data and data['status'] in ('draft', 'active', 'paused', 'completed'):
        campaign.status = data['status']
    if 'budget' in data:
        campaign.budget = float(data['budget'])
    if 'cost_per_click' in data:
        campaign.cost_per_click = float(data['cost_per_click'])
    if 'affiliate_cpc' in data:
        campaign.affiliate_cpc = float(data['affiliate_cpc'])
    if 'name' in data:
        campaign.name = data['name']
    if 'offer_url' in data:
        campaign.offer_url = data['offer_url']
    db.session.commit()
    return jsonify({
        'message': 'Campaign updated',
        'campaign': {
            'id': campaign.id,
            'name': campaign.name,
            'status': campaign.status,
            'total_clicks': campaign.total_clicks,
            'total_spend': float(campaign.total_spend or 0),
        },
    }), 200


@client_bp.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    """Client dashboard: summary of campaigns, total clicks, total spend."""
    client = _ensure_client()
    if not client:
        return jsonify({'error': 'Not registered as client'}), 404
    campaigns = Campaign.query.filter_by(client_id=client.id).all()
    total_clicks = sum(c.total_clicks or 0 for c in campaigns)
    total_spend = sum(float(c.total_spend or 0) for c in campaigns)
    active = [c for c in campaigns if c.status == 'active']
    return jsonify({
        'client': {
            'id': client.id,
            'company_name': client.company_name,
        },
        'summary': {
            'total_campaigns': len(campaigns),
            'active_campaigns': len(active),
            'total_clicks': total_clicks,
            'total_spend': round(total_spend, 2),
        },
        'campaigns': [
            {
                'id': c.id,
                'name': c.name,
                'status': c.status,
                'total_clicks': c.total_clicks or 0,
                'total_spend': float(c.total_spend or 0),
            }
            for c in campaigns[:20]
        ],
    }), 200


@client_bp.route('/dashboard/poll', methods=['GET'])
@login_required
def dashboard_poll():
    """Lightweight endpoint for realtime polling: summary + per-campaign stats only."""
    client = _ensure_client()
    if not client:
        return jsonify({'error': 'Not registered as client'}), 404
    campaigns = Campaign.query.filter_by(client_id=client.id).all()
    total_clicks = sum(c.total_clicks or 0 for c in campaigns)
    total_spend = sum(float(c.total_spend or 0) for c in campaigns)
    active_count = sum(1 for c in campaigns if c.status == 'active')
    return jsonify({
        'ts': time.time(),
        'summary': {
            'total_campaigns': len(campaigns),
            'active_campaigns': active_count,
            'total_clicks': total_clicks,
            'total_spend': round(total_spend, 2),
        },
        'campaigns': [
            {
                'id': c.id,
                'name': c.name,
                'status': c.status,
                'total_clicks': c.total_clicks or 0,
                'total_spend': float(c.total_spend or 0),
            }
            for c in campaigns[:50]
        ],
    }), 200


