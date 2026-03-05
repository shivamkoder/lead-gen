"""Tracking service for processing and recording click events.

This module encapsulates all rules governing what constitutes a valid
click, the payout calculation, and budget enforcement.  It is used by
`routes/redirect.py` so that the route remains thin.
"""

from datetime import datetime, timedelta

from backend.database.db import db
from backend.database.models import Click, Campaign


def track_click(
    campaign_id,
    affiliate_id=None,
    ip_address=None,
    user_agent=None,
    device_type=None,
    browser=None,
    referrer=None,
    fingerprint=None,
    risk_score=None,
    duplicate_window=30,
):
    """Process a click and store it if allowed.

    Returns a dict with keys ``allowed`` (bool), ``reason`` (str) and
    ``click`` (Click instance) when appropriate.

    The logic is deliberately simple for the demo; a real platform would
    have far more checks (geo, rate limiting, bot scores, etc.).
    """

    campaign = Campaign.query.get(campaign_id)
    if campaign is None or campaign.status != 'active':
        return {'allowed': False, 'reason': 'campaign_inactive'}

    # duplicate click detection:
    # 1. prefer fingerprint-based if available (more reliable)
    # 2. fallback to IP-based if fingerprint not available
    cutoff = datetime.utcnow() - timedelta(seconds=duplicate_window)
    
    dup = None
    if fingerprint:
        dup = (
            Click.query
            .filter_by(campaign_id=campaign_id, fingerprint=fingerprint)
            .filter(Click.timestamp >= cutoff)
            .first()
        )
    elif ip_address:
        # fallback to IP-based detection
        dup = (
            Click.query
            .filter_by(campaign_id=campaign_id, ip_address=ip_address)
            .filter(Click.timestamp >= cutoff)
            .first()
        )
    
    if dup:
        # record the click anyway with status duplicate for auditing
        click = Click(
            campaign_id=campaign_id,
            affiliate_id=affiliate_id,
            ip_address=ip_address,
            user_agent=user_agent,
            device_type=device_type,
            browser=browser,
            referrer=referrer,
            fingerprint=fingerprint,
            risk_score=risk_score or 0.0,
            payout=0.0,
            status='duplicate',
        )
        db.session.add(click)
        db.session.commit()
        return {'allowed': False, 'reason': 'duplicate', 'click': click}

    # compute payout and update campaign spend/budget
    payout = campaign.cpc
    campaign.spend = (campaign.spend or 0.0) + payout
    if campaign.budget and campaign.spend >= campaign.budget:
        campaign.status = 'paused'
    db.session.add(campaign)

    click = Click(
        campaign_id=campaign_id,
        affiliate_id=affiliate_id,
        ip_address=ip_address,
        user_agent=user_agent,
        device_type=device_type,
        browser=browser,
        referrer=referrer,
        fingerprint=fingerprint,
        risk_score=risk_score or 0.0,
        payout=payout,
        status='ok',
    )
    db.session.add(click)
    db.session.commit()

    return {'allowed': True, 'click': click}
