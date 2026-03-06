"""
Admin Routes
Administrative endpoints for managing users, campaigns, and system
"""

from flask import Blueprint, request, jsonify
from flask_login import current_user
from backend.app.extensions import db
from backend.app.models import User, Affiliate, Campaign, Lead, Payout, Analytics
from backend.app.utils.decorators import login_required, roles_required

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/dashboard', methods=['GET'])
@login_required
@roles_required('admin')
def get_dashboard():
    """Get admin dashboard statistics"""
    total_users = User.query.count()
    total_affiliates = Affiliate.query.count()
    total_campaigns = Campaign.query.count()
    total_leads = Lead.query.count()
    
    total_earnings = db.session.query(db.func.sum(Affiliate.total_earnings)).scalar() or 0
    pending_payouts = db.session.query(db.func.sum(Affiliate.pending_payout)).scalar() or 0
    
    # Get recent activity
    recent_leads = Lead.query.order_by(Lead.created_at.desc()).limit(10).all()
    recent_registrations = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    return jsonify({
        'stats': {
            'total_users': total_users,
            'total_affiliates': total_affiliates,
            'total_campaigns': total_campaigns,
            'total_leads': total_leads,
            'total_earnings': float(total_earnings),
            'pending_payouts': float(pending_payouts)
        },
        'recent_leads': [{
            'id': l.id,
            'email': l.email,
            'status': l.status,
            'created_at': l.created_at.isoformat()
        } for l in recent_leads],
        'recent_registrations': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'created_at': u.created_at.isoformat()
        } for u in recent_registrations]
    }), 200


@admin_bp.route('/users', methods=['GET'])
@login_required
@roles_required('admin')
def get_users():
    """Get all users with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role')
    
    query = User.query
    if role:
        query = query.filter_by(role=role)
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'users': [{
            'id': u.id,
            'username': u.username,
            'email': u.email,
            'role': u.role,
            'is_active': u.is_active,
            'created_at': u.created_at.isoformat()
        } for u in users.items],
        'total': users.total,
        'page': users.page,
        'pages': users.pages
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
@roles_required('admin')
def get_user(user_id):
    """Get user details"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.role,
            'is_active': user.is_active,
            'created_at': user.created_at.isoformat()
        }
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
@roles_required('admin')
def update_user(user_id):
    """Update user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    data = request.get_json()
    
    if 'role' in data:
        user.role = data['role']
    if 'is_active' in data:
        user.is_active = data['is_active']
    if 'first_name' in data:
        user.first_name = data['first_name']
    if 'last_name' in data:
        user.last_name = data['last_name']
    
    db.session.commit()
    
    return jsonify({
        'message': 'User updated successfully',
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.role,
            'is_active': user.is_active
        }
    }), 200


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@login_required
@roles_required('admin')
def delete_user(user_id):
    """Delete user"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    db.session.delete(user)
    db.session.commit()
    
    return jsonify({'message': 'User deleted successfully'}), 200


@admin_bp.route('/campaigns', methods=['GET'])
@login_required
@roles_required('admin')
def get_all_campaigns():
    """Get all campaigns"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Campaign.query
    if status:
        query = query.filter_by(status=status)
    
    campaigns = query.order_by(Campaign.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'campaigns': [{
            'id': c.id,
            'name': c.name,
            'status': c.status,
            'budget': c.budget,
            'client_id': c.client_id,
            'affiliate_id': c.affiliate_id,
            'created_at': c.created_at.isoformat()
        } for c in campaigns.items],
        'total': campaigns.total,
        'page': campaigns.page,
        'pages': campaigns.pages
    }), 200


@admin_bp.route('/campaigns/<int:campaign_id>', methods=['PUT'])
@login_required
@roles_required('admin')
def update_campaign(campaign_id):
    """Update campaign"""
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return jsonify({'error': 'Campaign not found'}), 404
    
    data = request.get_json()
    
    if 'status' in data:
        campaign.status = data['status']
    if 'budget' in data:
        campaign.budget = data['budget']
    if 'cost_per_click' in data:
        campaign.cost_per_click = data['cost_per_click']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Campaign updated successfully',
        'campaign': {
            'id': campaign.id,
            'name': campaign.name,
            'status': campaign.status
        }
    }), 200


@admin_bp.route('/leads', methods=['GET'])
@login_required
@roles_required('admin')
def get_all_leads():
    """Get all leads"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    campaign_id = request.args.get('campaign_id', type=int)
    
    query = Lead.query
    if status:
        query = query.filter_by(status=status)
    if campaign_id:
        query = query.filter_by(campaign_id=campaign_id)
    
    leads = query.order_by(Lead.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'leads': [{
            'id': l.id,
            'email': l.email,
            'name': l.name,
            'status': l.status,
            'campaign_id': l.campaign_id,
            'affiliate_id': l.affiliate_id,
            'payout_amount': l.payout_amount,
            'created_at': l.created_at.isoformat()
        } for l in leads.items],
        'total': leads.total,
        'page': leads.page,
        'pages': leads.pages
    }), 200


@admin_bp.route('/leads/<int:lead_id>', methods=['PUT'])
@login_required
@roles_required('admin')
def update_lead(lead_id):
    """Update lead status"""
    lead = Lead.query.get(lead_id)
    if not lead:
        return jsonify({'error': 'Lead not found'}), 404
    
    data = request.get_json()
    
    if 'status' in data:
        lead.status = data['status']
    
    db.session.commit()
    
    return jsonify({
        'message': 'Lead updated successfully',
        'lead': {
            'id': lead.id,
            'status': lead.status
        }
    }), 200


@admin_bp.route('/payouts', methods=['GET'])
@login_required
@roles_required('admin')
def get_all_payouts():
    """Get all payouts"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    
    query = Payout.query
    if status:
        query = query.filter_by(status=status)
    
    payouts = query.order_by(Payout.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'payouts': [{
            'id': p.id,
            'affiliate_id': p.affiliate_id,
            'amount': p.amount,
            'status': p.status,
            'payment_method': p.payment_method,
            'created_at': p.created_at.isoformat()
        } for p in payouts.items],
        'total': payouts.total,
        'page': payouts.page,
        'pages': payouts.pages
    }), 200


@admin_bp.route('/payouts/<int:payout_id>/process', methods=['POST'])
@login_required
@roles_required('admin')
def process_payout(payout_id):
    """Process a payout"""
    payout = Payout.query.get(payout_id)
    if not payout:
        return jsonify({'error': 'Payout not found'}), 404
    
    if payout.status != 'pending':
        return jsonify({'error': 'Payout is not pending'}), 400
    
    data = request.get_json()
    
    payout.status = 'processing'
    payout.payment_reference = data.get('payment_reference', '')
    payout.processed_at = db.func.now()
    
    db.session.commit()
    
    return jsonify({
        'message': 'Payout processing started',
        'payout': {
            'id': payout.id,
            'status': payout.status
        }
    }), 200


@admin_bp.route('/analytics', methods=['GET'])
@login_required
@roles_required('admin')
def get_analytics():
    """Get analytics data"""
    # Get date range from query params
    days = request.args.get('days', 30, type=int)
    
    # Get clicks and leads by day
    from datetime import datetime, timedelta
    start_date = datetime.utcnow() - timedelta(days=days)
    
    clicks = Analytics.query.filter(
        Analytics.event_type == 'click',
        Analytics.created_at >= start_date
    ).count()
    
    leads = Analytics.query.filter(
        Analytics.event_type == 'lead',
        Analytics.created_at >= start_date
    ).count()
    
    conversions = Lead.query.filter(
        Lead.status == 'converted',
        Lead.created_at >= start_date
    ).count()
    
    return jsonify({
        'period_days': days,
        'clicks': clicks,
        'leads': leads,
        'conversions': conversions,
        'conversion_rate': (conversions / clicks * 100) if clicks > 0 else 0
    }), 200

