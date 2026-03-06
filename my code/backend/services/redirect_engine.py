"""Engine that decides where to redirect users.

For now it simply looks up the campaign's configured target URL, but
this is the place to add rotation, weight‑based offers, geo‑targeting,
etc.
"""

from backend.database.models import Campaign


def choose_target(campaign_id, user_info):
    """Return a URL to which the visitor should be sent.

    Args:
        campaign_id (int): the primary campaign identifier
        user_info (dict): information about the requester (ip, ua, etc.)

    Returns:
        str|None: destination URL or ``None`` if not found
    """
    campaign = Campaign.query.get(campaign_id)
    if not campaign:
        return None
    return campaign.target_url
