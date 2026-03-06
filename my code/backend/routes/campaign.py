from flask import Blueprint, request, jsonify, abort
from backend.database.db import db
from backend.database.models import Campaign, Click, campaign_to_dict
from backend.utils.auth import login_required
from backend.utils.hash import generate_campaign_slug, generate_tracking_id

campaign_bp = Blueprint('campaign', __name__)


@campaign_bp.route('/campaigns', methods=['GET'])
def list_campaigns():
    """Return all campaigns (would normally scope to current user)."""
    camps = Campaign.query.all()
    return jsonify([campaign_to_dict(c) for c in camps])


@campaign_bp.route('/campaigns', methods=['POST'])
@login_required
def create_campaign():
    """Create a new campaign based on JSON payload.
    
    Auto-generates slug and tracking_id for security.
    User provides: name, target_url, optional (description, cpc, budget)
    """
    data = request.json or {}
    required = ['name', 'target_url']
    for f in required:
        if f not in data:
            abort(400, f"missing field {f}")

    # User can provide slug, but it will be sanitized/regenerated for uniqueness
    provided_slug = data.get('slug', data['name'])
    
    # Auto-generate secure slug (adds randomness for uniqueness)
    slug = generate_campaign_slug(provided_slug)
    
    # Generate tracking ID (additional public identifier)
    tracking_id = generate_tracking_id(prefix='cmp_')
    
    camp = Campaign(
        name=data['name'],
        slug=slug,
        tracking_id=tracking_id,
        target_url=data['target_url'],
        description=data.get('description'),
        cpc=float(data.get('cpc', 0.0)),
        budget=float(data.get('budget', 0.0)),
    )
    db.session.add(camp)
    db.session.commit()
    return jsonify(campaign_to_dict(camp)), 201


@campaign_bp.route('/campaigns/<int:cid>', methods=['GET'])
def get_campaign(cid):
    camp = Campaign.query.get_or_404(cid)
    return jsonify(campaign_to_dict(camp))


@campaign_bp.route('/campaigns/<int:cid>', methods=['PUT'])
@login_required
def update_campaign(cid):
    camp = Campaign.query.get_or_404(cid)
    data = request.json or {}
    for key in ['name', 'target_url', 'description', 'cpc', 'budget']:
        if key in data:
            setattr(camp, key, data[key])
    # status update handled separately
    db.session.commit()
    return jsonify(campaign_to_dict(camp))


@campaign_bp.route('/campaigns/<int:cid>/pause', methods=['POST'])
@login_required
def pause_campaign(cid):
    camp = Campaign.query.get_or_404(cid)
    camp.status = 'paused' if camp.status == 'active' else 'active'
    db.session.commit()
    return jsonify({'status': camp.status})


@campaign_bp.route('/campaigns/<int:cid>/stats', methods=['GET'])
def campaign_stats(cid):
    camp = Campaign.query.get_or_404(cid)
    clicks = Click.query.filter_by(campaign_id=cid).count()
    spend = camp.spend
    return jsonify({'clicks': clicks, 'spend': spend, 'budget': camp.budget})
