from flask import Blueprint, redirect as flask_redirect, request, abort
from backend.database.db import db
from backend.database.models import Campaign
from backend.services.traffic_filter import is_valid_traffic, get_click_fingerprint, get_traffic_risk
from backend.services.tracker import track_click
from backend.services.redirect_engine import choose_target
from backend.utils.helpers import (
    get_client_ip,
    get_user_agent,
    detect_device_type,
    extract_browser_name,
    get_referrer,
)

redirect_bp = Blueprint('redirect', __name__)


@redirect_bp.route('/r/<string:slug>')
def handle_redirect(slug):
    """Entry point for click‑through links.

    The URL contains the ``slug`` identifying a campaign.  We perform a
    series of steps:

      * resolve the slug to an active campaign
      * collect metadata (IP, UA)
      * validate the traffic (bot filtering, rate limits, etc.)
      * persist a ``Click`` record via ``tracker``
      * determine the final destination via ``redirect_engine``
      * issue an HTTP redirect

    If anything goes wrong we fall back to the campaign's configured
    ``target_url`` or a generic home page.
    """

    campaign = Campaign.query.filter_by(slug=slug, status='active').first()
    if campaign is None:
        # campaign doesn't exist or is paused
        abort(404)

    client_ip = get_client_ip()
    user_agent = get_user_agent()
    device_type = detect_device_type(user_agent)
    browser = extract_browser_name(user_agent)
    referrer = get_referrer()

    if not is_valid_traffic(request):
        # non‑human traffic, simply send to the target URL without
        # recording a click (alternatively could record a 'bot click').
        return flask_redirect(campaign.target_url)

    # generate fingerprint and assess fraud risk
    fingerprint = get_click_fingerprint(request)
    risk_data = get_traffic_risk(request)

    # record the click and capture result
    try:
        result = track_click(
            campaign.id,
            ip_address=client_ip,
            user_agent=user_agent,
            device_type=device_type,
            browser=browser,
            referrer=referrer,
            fingerprint=fingerprint,
            risk_score=risk_data['risk_score'],
            affiliate_id=request.args.get('aid')
        )
    except Exception:
        result = {'allowed': False, 'reason': 'error'}

    destination = choose_target(campaign.id, {'ip': client_ip, 'ua': user_agent})
    if not destination:
        destination = campaign.target_url

    # if tracking returned a reason, surface it as a header for debugging/logging
    status_header = result.get('reason') if isinstance(result, dict) else None

    resp = flask_redirect(destination)
    if status_header:
        resp.headers['X-Click-Status'] = status_header
    return resp
