"""
Demo Routes
Fake dashboard data for sales demos (no auth required).
Includes poll endpoints for realtime-style demo updates.
"""

import time
from flask import Blueprint, jsonify

demo_bp = Blueprint('demo', __name__)


def _fake_campaigns():
    return [
        {'id': 1, 'name': 'Summer Sale 2025', 'status': 'active', 'total_clicks': 1247, 'total_spend': 6235.0},
        {'id': 2, 'name': 'Product Launch', 'status': 'active', 'total_clicks': 892, 'total_spend': 4460.0},
        {'id': 3, 'name': 'Brand Awareness', 'status': 'paused', 'total_clicks': 2103, 'total_spend': 10515.0},
    ]


@demo_bp.route('/dashboard/client', methods=['GET'])
def demo_client_dashboard():
    """Fake client dashboard for demo mode (no login)."""
    campaigns = _fake_campaigns()
    total_clicks = sum(c['total_clicks'] for c in campaigns)
    total_spend = sum(c['total_spend'] for c in campaigns)
    return jsonify({
        'demo': True,
        'client': {'id': 1, 'company_name': 'Demo Advertiser'},
        'summary': {
            'total_campaigns': len(campaigns),
            'active_campaigns': 2,
            'total_clicks': total_clicks,
            'total_spend': round(total_spend, 2),
        },
        'campaigns': campaigns,
    }), 200


@demo_bp.route('/dashboard/affiliate', methods=['GET'])
def demo_affiliate_dashboard():
    """Fake affiliate dashboard for demo mode (no login)."""
    return jsonify({
        'demo': True,
        'earnings': {
            'total_earnings': 3840.0,
            'pending_payout': 720.0,
            'valid_clicks': 1280,
            'commission_rate': 0.6,
        },
        'campaigns': [
            {'id': 1, 'name': 'Summer Sale 2025', 'clicks': 640, 'earnings': 1920.0},
            {'id': 2, 'name': 'Product Launch', 'clicks': 640, 'earnings': 1920.0},
        ],
    }), 200


@demo_bp.route('/stats', methods=['GET'])
def demo_stats():
    """Fake platform stats for landing page."""
    return jsonify({
        'demo': True,
        'total_clicks': 12450,
        'total_payouts': 28400.0,
        'active_affiliates': 156,
        'active_campaigns': 42,
    }), 200


# ---------- Poll endpoints (same shape as real dashboards for demo UI) ----------

@demo_bp.route('/dashboard/client/poll', methods=['GET'])
def demo_client_poll():
    """Fake client dashboard poll for realtime demo (no auth)."""
    campaigns = _fake_campaigns()
    total_clicks = sum(c['total_clicks'] for c in campaigns)
    total_spend = sum(c['total_spend'] for c in campaigns)
    return jsonify({
        'demo': True,
        'ts': time.time(),
        'summary': {
            'total_campaigns': len(campaigns),
            'active_campaigns': 2,
            'total_clicks': total_clicks,
            'total_spend': round(total_spend, 2),
        },
        'campaigns': campaigns,
    }), 200


@demo_bp.route('/dashboard/affiliate/poll', methods=['GET'])
def demo_affiliate_poll():
    """Fake affiliate dashboard poll for realtime demo (no auth)."""
    return jsonify({
        'demo': True,
        'ts': time.time(),
        'valid_clicks': 1280,
        'total_earnings': 3840.0,
        'pending_payout': 720.0,
        'commission_rate': 0.6,
    }), 200
