"""
Affiliate Routes
Affiliate management, earnings, and marketplace endpoints
"""

import time
from flask import Blueprint, request, jsonify
from flask_login import current_user
from app.extensions import db
from app.models import Affiliate, Campaign, Lead, Payout, Click
from app.utils.decorators import login_required, roles_required
import secrets
import string

affiliate_bp = Blueprint('affiliate', __name__)


def generate_referral_code(length=12):
    """Generate unique referral code"""
    chars = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(chars) for _ in range(length))


@affiliate_bp.route('/register', methods=['POST'])
@login_required
def register_affiliate():
    """Register as an affiliate"""
    if current_user.affiliate:
        return jsonify({'error': 'Already registered as affiliate'}), 400
    
    data = request.get_json()
    
    affiliate = Affiliate(
        user_id=current_user.id,
        referral_code=generate_referral_code(),
        commission_rate=data.get('commission_rate', 0.20),
        payment_email=data.get('payment_email', current_user.email)
    )
    
    db.session.add(affiliate)
    db.session.commit()
    
    return jsonify({
        'message': 'Affiliate registered successfully',
        'affiliate': {
            'id': affiliate.id,
            'referral_code': affiliate.referral_code,
            'commission_rate': affiliate.commission_rate,
            'status': affiliate.status
        }
    }), 201


@affiliate_bp.route('/profile', methods=['GET'])
@login_required
def get_affiliate_profile():
    """Get affiliate profile"""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    affiliate = current_user.affiliate
    
    return jsonify({
        'affiliate': {
            'id': affiliate.id,
            'referral_code': affiliate.referral_code,
            'commission_rate': affiliate.commission_rate,
            'total_earnings': affiliate.total_earnings,
            'pending_payout': affiliate.pending_payout,
            'status': affiliate.status,
            'payment_email': affiliate.payment_email
        }
    }), 200


@affiliate_bp.route('/profile', methods=['PUT'])
@login_required
def update_affiliate_profile():
    """Update affiliate profile"""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    data = request.get_json()
    affiliate = current_user.affiliate
    
    if 'commission_rate' in data:
        affiliate.commission_rate = data['commission_rate']
    if 'payment_email' in data:
        affiliate.payment_email = data['payment_email']
    if 'status' in data:
        if data['status'] in ['active', 'paused']:
            affiliate.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Profile updated successfully',
        'affiliate': {
            'id': affiliate.id,
            'referral_code': affiliate.referral_code,
            'commission_rate': affiliate.commission_rate,
            'status': affiliate.status
        }
    }), 200


@affiliate_bp.route('/campaigns', methods=['GET'])
@login_required
def get_available_campaigns():
    """Get available campaigns for affiliate"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    campaigns = Campaign.query.filter_by(status='active').paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'campaigns': [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'offer_url': c.offer_url,
            'cost_per_click': c.cost_per_click,
            'budget': c.budget,
            'client': c.client.company_name if c.client else None
        } for c in campaigns.items],
        'total': campaigns.total,
        'page': campaigns.page,
        'pages': campaigns.pages
    }), 200


@affiliate_bp.route('/campaigns/<int:campaign_id>/join', methods=['POST'])
@login_required
def join_campaign(campaign_id):
    """Register interest in a campaign (PPC: any affiliate can promote; link has aff= in URL)."""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    if campaign.status != 'active':
        return jsonify({'error': 'Campaign is not active'}), 400
    
    base_url = request.host_url.rstrip('/')
    tracking_url = f"{base_url}/t/{campaign.id}?aff={current_user.affiliate.id}"
    
    return jsonify({
        'message': 'You can promote this campaign with your tracking link',
        'campaign_id': campaign_id,
        'tracking_url': tracking_url,
    }), 200


@affiliate_bp.route('/earnings', methods=['GET'])
@login_required
def get_earnings():
    """Get affiliate earnings (PPC: from valid clicks + legacy leads)."""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    affiliate = current_user.affiliate
    valid_clicks = Click.query.filter_by(affiliate_id=affiliate.id, is_valid=True).count()
    leads = Lead.query.filter_by(affiliate_id=affiliate.id).all()
    total_leads = len(leads)
    converted_leads = len([l for l in leads if l.status == 'converted'])
    pending_leads = len([l for l in leads if l.status == 'pending'])
    
    return jsonify({
        'earnings': {
            'total_earnings': affiliate.total_earnings,
            'pending_payout': affiliate.pending_payout,
            'valid_clicks': valid_clicks,
            'total_leads': total_leads,
            'converted_leads': converted_leads,
            'pending_leads': pending_leads,
            'commission_rate': affiliate.commission_rate,
        },
    }), 200


@affiliate_bp.route('/dashboard/poll', methods=['GET'])
@login_required
def dashboard_poll():
    """Lightweight endpoint for realtime polling: earnings and click stats only."""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    affiliate = current_user.affiliate
    valid_clicks = Click.query.filter_by(affiliate_id=affiliate.id, is_valid=True).count()
    return jsonify({
        'ts': time.time(),
        'valid_clicks': valid_clicks,
        'total_earnings': float(affiliate.total_earnings or 0),
        'pending_payout': float(affiliate.pending_payout or 0),
        'commission_rate': float(affiliate.commission_rate or 0),
    }), 200


@affiliate_bp.route('/leads', methods=['GET'])
@login_required
def get_affiliate_leads():
    """Get leads for affiliate"""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Lead.query.filter_by(affiliate_id=current_user.affiliate.id)
    
    if status:
        query = query.filter_by(status=status)
    
    leads = query.order_by(Lead.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'leads': [{
            'id': l.id,
            'email': l.email,
            'name': l.name,
            'status': l.status,
            'payout_amount': l.payout_amount,
            'campaign_id': l.campaign_id,
            'created_at': l.created_at.isoformat()
        } for l in leads.items],
        'total': leads.total,
        'page': leads.page,
        'pages': leads.pages
    }), 200


@affiliate_bp.route('/payouts', methods=['GET'])
@login_required
def get_payouts():
    """Get payout history"""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    payouts = Payout.query.filter_by(
        affiliate_id=current_user.affiliate.id
    ).order_by(Payout.created_at.desc()).all()
    
    return jsonify({
        'payouts': [{
            'id': p.id,
            'amount': p.amount,
            'currency': p.currency,
            'status': p.status,
            'payment_method': p.payment_method,
            'processed_at': p.processed_at.isoformat() if p.processed_at else None,
            'created_at': p.created_at.isoformat()
        } for p in payouts]
    }), 200


@affiliate_bp.route('/payouts/request', methods=['POST'])
@login_required
def request_payout():
    """Request payout"""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    affiliate = current_user.affiliate
    
    if affiliate.pending_payout <= 0:
        return jsonify({'error': 'No pending earnings to payout'}), 400
    
    data = request.get_json()
    
    payout = Payout(
        affiliate_id=affiliate.id,
        amount=affiliate.pending_payout,
        payment_method=data.get('payment_method', 'paypal')
    )
    
    affiliate.pending_payout = 0
    
    db.session.add(payout)
    db.session.commit()
    
    return jsonify({
        'message': 'Payout requested successfully',
        'payout': {
            'id': payout.id,
            'amount': payout.amount,
            'status': payout.status
        }
    }), 201


@affiliate_bp.route('/links/<int:campaign_id>', methods=['GET'])
@login_required
def get_tracking_link(campaign_id):
    """Get PPC tracking link for campaign. Format: /t/<campaign_id>?aff=<affiliate_id>"""
    if not current_user.affiliate:
        return jsonify({'error': 'Not registered as affiliate'}), 404
    
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    base_url = request.host_url.rstrip('/')
    tracking_url = f"{base_url}/t/{campaign.id}?aff={current_user.affiliate.id}"
    
    return jsonify({
        'campaign_id': campaign.id,
        'tracking_url': tracking_url,
        'referral_code': current_user.affiliate.referral_code,
        'affiliate_cpc': campaign.affiliate_cpc,
    }), 200
