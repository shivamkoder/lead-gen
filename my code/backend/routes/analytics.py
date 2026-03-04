from datetime import datetime, timedelta

from flask import Blueprint, jsonify, request
from backend.database.db import db
from backend.database.models import Campaign, Click, campaign_to_dict

analytics_bp = Blueprint('analytics', __name__)


def _date_series(start, end):
    """Generate list of dates between start and end (inclusive)."""
    series = []
    cur = start
    while cur <= end:
        series.append(cur)
        cur += timedelta(days=1)
    return series


def _clicks_by_date(query):
    """Return dict mapping date->count for given base query."""
    results = (
        query.with_entities(
            db.func.date(Click.timestamp).label('day'),
            db.func.count(Click.id)
        )
        .group_by('day')
        .all()
    )
    # SQLite returns string; other dbs may return date object
    out = {}
    for r in results:
        day = r[0]
        if hasattr(day, 'isoformat'):
            day = day.isoformat()
        out[day] = r[1]
    return out


@analytics_bp.route('/analytics/campaign/<int:cid>')
def analytics_campaign(cid):
    camp = Campaign.query.get_or_404(cid)
    base = Click.query.filter_by(campaign_id=cid)

    total = base.count()
    today = base.filter(db.func.date(Click.timestamp) == datetime.utcnow().date()).count()

    # last 7 days
    end = datetime.utcnow().date()
    start = end - timedelta(days=6)
    series = _clicks_by_date(base.filter(Click.timestamp >= start))
    last7 = []
    for d in _date_series(start, end):
        last7.append({'date': d.isoformat(), 'clicks': series.get(d.isoformat(), 0)})

    # hourly last 24h
    last24 = []
    now = datetime.utcnow()
    for h in range(24):
        period = now - timedelta(hours=h)
        count = base.filter(
            db.func.strftime('%Y-%m-%d %H', Click.timestamp) == period.strftime('%Y-%m-%d %H')
        ).count()
        last24.append({'hour': period.strftime('%Y-%m-%d %H:00'), 'clicks': count})
    last24.reverse()

    return jsonify({
        'campaign': campaign_to_dict(camp),
        'total_clicks': total,
        'today_clicks': today,
        'last_7_days': last7,
        'last_24_hours': last24,
    })


@analytics_bp.route('/analytics/client')
def analytics_client():
    # aggregate across all campaigns
    base = Click.query
    total = base.count()
    campaigns = Campaign.query.all()

    # calculate spend based on actual stored payouts (supports duplicates with zero payout)
    spend = base.with_entities(db.func.sum(Click.payout)).scalar() or 0.0

    return jsonify({'total_clicks': total, 'spend': float(spend)})


@analytics_bp.route('/analytics/affiliate')
def analytics_affiliate():
    # group by affiliate_id
    results = (
        db.session.query(Click.affiliate_id, db.func.count(Click.id))
        .group_by(Click.affiliate_id)
        .all()
    )
    data = [{'affiliate_id': r[0], 'clicks': r[1]} for r in results]
    return jsonify(data)


@analytics_bp.route('/analytics/live')
def analytics_live():
    # return clicks in last minute
    since = datetime.utcnow() - timedelta(minutes=1)
    count = Click.query.filter(Click.timestamp >= since).count()
    return jsonify({'last_minute': count})
