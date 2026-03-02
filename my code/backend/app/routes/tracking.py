"""
Tracking Routes
Click tracking, lead capture, and attribution endpoints.
PPC: public /t/<campaign_id>?aff=affiliateID for pay-per-click redirect + validation.
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, redirect
from app.extensions import db
from app.models import Campaign, Lead, Affiliate, Analytics, Click
from app.services.fraud import FraudDetector
import uuid

# Duplicate click window: same visitor (fingerprint) within this time = 1 click only
CLICK_DEDUP_WINDOW_MINUTES = 60

tracking_bp = Blueprint('tracking', __name__)

# Public PPC redirect: yourdomain.com/t/<campaign_id>?aff=affiliateID
ppc_bp = Blueprint('ppc', __name__)


@ppc_bp.route('/t/<int:campaign_id>', methods=['GET'])
def ppc_redirect(campaign_id):
    """
    PPC tracking endpoint. Validates click, records it, updates earnings/spend, redirects to offer.
    Link format: /t/<campaign_id>?aff=<affiliate_id>
    """
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    if campaign.status != 'active':
        return jsonify({'error': 'Campaign is not active'}), 404

    affiliate_id = request.args.get('aff', type=int)
    affiliate = None
    if affiliate_id:
        affiliate = Affiliate.query.get(affiliate_id)
        if not affiliate or affiliate.status != 'active':
            affiliate = None
            affiliate_id = None

    ip = request.remote_addr or '0.0.0.0'
    user_agent = request.headers.get('User-Agent') or ''

    fraud = FraudDetector()
    if fraud.is_bot_click(user_agent):
        # Record click but invalid; redirect anyway
        click = Click(
            campaign_id=campaign_id,
            affiliate_id=affiliate_id,
            ip_address=ip,
            user_agent=user_agent,
            is_valid=False,
        )
        db.session.add(click)
        db.session.commit()
        return redirect(campaign.offer_url, code=302)

    fingerprint = fraud.generate_click_fingerprint(ip, user_agent, campaign_id, affiliate_id)
    window_start = datetime.utcnow() - timedelta(minutes=CLICK_DEDUP_WINDOW_MINUTES)
    existing = (
        db.session.query(Click.fingerprint_hash)
        .filter(
            Click.campaign_id == campaign_id,
            Click.fingerprint_hash == fingerprint,
            Click.created_at >= window_start,
            Click.is_valid == True,
        )
        .first()
    )
    if existing:
        # Duplicate: record invalid click, redirect
        click = Click(
            campaign_id=campaign_id,
            affiliate_id=affiliate_id,
            ip_address=ip,
            user_agent=user_agent,
            fingerprint_hash=fingerprint,
            is_valid=False,
        )
        db.session.add(click)
        db.session.commit()
        return redirect(campaign.offer_url, code=302)

    # Valid click: record, update campaign spend and affiliate earnings
    affiliate_cpc = float(campaign.affiliate_cpc or 0)
    client_cpc = float(campaign.cost_per_click or 0)

    click = Click(
        campaign_id=campaign_id,
        affiliate_id=affiliate_id,
        ip_address=ip,
        user_agent=user_agent,
        fingerprint_hash=fingerprint,
        is_valid=True,
        payout_amount=affiliate_cpc,
    )
    db.session.add(click)

    campaign.total_clicks = (campaign.total_clicks or 0) + 1
    campaign.total_spend = (campaign.total_spend or 0) + client_cpc
    if campaign.budget and campaign.total_spend >= campaign.budget:
        campaign.status = 'paused'

    if affiliate and affiliate_cpc > 0:
        affiliate.total_earnings = (affiliate.total_earnings or 0) + affiliate_cpc
        affiliate.pending_payout = (affiliate.pending_payout or 0) + affiliate_cpc

    db.session.commit()
    return redirect(campaign.offer_url, code=302)


@tracking_bp.route('/click/<int:campaign_id>', methods=['GET'])
def track_click(campaign_id):
    """Track click and redirect to offer URL"""
    affiliate_id = request.args.get('affiliate_id')
    sub_id = request.args.get('sub_id')
    
    campaign = Campaign.query.get(campaign_id)
    if not campaign or campaign.status != 'active':
        return jsonify({'error': 'Campaign not found or inactive'}), 404
    
    analytics = Analytics(
        event_type='click',
        campaign_id=campaign_id,
        affiliate_id=affiliate_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        meta_data={
            'sub_id': sub_id,
            'referrer': request.referrer,
            'utm_source': request.args.get('utm_source'),
            'utm_medium': request.args.get('utm_medium'),
            'utm_campaign': request.args.get('utm_campaign')
        }
    )
    db.session.add(analytics)
    db.session.commit()
    
    click_id = analytics.id
    redirect_url = f"{campaign.offer_url}?click_id={click_id}"
    
    if affiliate_id:
        redirect_url += f"&affiliate_id={affiliate_id}"
    
    return redirect(redirect_url, code=302)


@tracking_bp.route('/lead', methods=['POST'])
def track_lead():
    """Track new lead/conversion"""
    data = request.get_json()
    
    if not data.get('campaign_id'):
        return jsonify({'error': 'campaign_id is required'}), 400
    
    if not data.get('email'):
        return jsonify({'error': 'email is required'}), 400
    
    campaign = Campaign.query.get(data['campaign_id'])
    if not campaign or campaign.status != 'active':
        return jsonify({'error': 'Campaign not found or inactive'}), 404
    
    affiliate = None
    if data.get('affiliate_id'):
        affiliate = Affiliate.query.get(data['affiliate_id'])
    
    fraud_detector = FraudDetector()
    fraud_score = fraud_detector.calculate_score(
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        email=data.get('email'),
        fingerprint=data.get('fingerprint')
    )
    
    status = 'verified' if fraud_score < 0.5 else 'pending'
    
    existing_lead = Lead.query.filter_by(
        campaign_id=data['campaign_id'],
        email=data['email']
    ).first()
    
    if existing_lead:
        return jsonify({
            'error': 'Lead already exists',
            'lead_id': existing_lead.id,
            'status': existing_lead.status
        }), 409
    
    lead = Lead(
        campaign_id=data['campaign_id'],
        affiliate_id=affiliate.id if affiliate else None,
        email=data['email'],
        name=data.get('name'),
        phone=data.get('phone'),
        meta_data=data.get('metadata'),
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        fingerprint=data.get('fingerprint'),
        status=status,
        payout_amount=campaign.cost_per_click or 0
    )
    
    lead.conversion_id = str(uuid.uuid4())
    
    db.session.add(lead)
    
    analytics = Analytics(
        event_type='lead',
        campaign_id=data['campaign_id'],
        affiliate_id=affiliate.id if affiliate else None,
        lead_id=lead.id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        meta_data={'fraud_score': fraud_score}
    )
    db.session.add(analytics)
    db.session.commit()
    
    return jsonify({
        'message': 'Lead tracked successfully',
        'lead_id': lead.id,
        'conversion_id': lead.conversion_id,
        'status': status
    }), 201


@tracking_bp.route('/conversion', methods=['POST'])
def track_conversion():
    """Track conversion/affiliate payout"""
    data = request.get_json()
    
    if not data.get('conversion_id'):
        return jsonify({'error': 'conversion_id is required'}), 400
    
    if not data.get('amount'):
        return jsonify({'error': 'amount is required'}), 400
    
    lead = Lead.query.filter_by(conversion_id=data['conversion_id']).first()
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    
    lead.status = 'converted'
    
    payout_amount = data['amount']
    if lead.affiliate:
        payout_amount = data['amount'] * lead.affiliate.commission_rate
        lead.affiliate.total_earnings += payout_amount
        lead.affiliate.pending_payout += payout_amount
    
    lead.payout_amount = payout_amount
    
    analytics = Analytics(
        event_type='conversion',
        campaign_id=lead.campaign_id,
        affiliate_id=lead.affiliate_id,
        lead_id=lead.id,
        meta_data={
            'amount': data['amount'],
            'payout_amount': payout_amount
        }
    )
    db.session.add(analytics)
    db.session.commit()
    
    return jsonify({
        'message': 'Conversion tracked successfully',
        'lead_id': lead.id,
        'payout_amount': payout_amount
    }), 200


@tracking_bp.route('/pixel/<int:campaign_id>', methods=['GET'])
def tracking_pixel(campaign_id):
    """Return 1x1 tracking pixel"""
    affiliate_id = request.args.get('affiliate_id')
    
    analytics = Analytics(
        event_type='pixel',
        campaign_id=campaign_id,
        affiliate_id=affiliate_id,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(analytics)
    db.session.commit()
    
    return '', 204, {'Content-Type': 'image/gif'}


@tracking_bp.route('/stats/<int:campaign_id>', methods=['GET'])
def get_campaign_stats(campaign_id):
    """Get campaign statistics"""
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    clicks = Analytics.query.filter_by(
        event_type='click',
        campaign_id=campaign_id
    ).count()
    
    leads = Lead.query.filter_by(campaign_id=campaign_id).count()
    
    conversions = Lead.query.filter_by(
        campaign_id=campaign_id,
        status='converted'
    ).count()
    
    total_payout = db.session.query(db.func.sum(Lead.payout_amount)).filter(
        Lead.campaign_id == campaign_id,
        Lead.status == 'converted'
    ).scalar() or 0
    
    return jsonify({
        'campaign_id': campaign_id,
        'clicks': clicks,
        'leads': leads,
        'conversions': conversions,
        'total_payout': float(total_payout),
        'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0
    }), 200
