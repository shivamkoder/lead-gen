"""Bot detection middleware."""


def detect_bot(user_agent):
    """Simple bot detection based on user agent string."""
    bot_keywords = ['bot', 'crawler', 'spider', 'scraper']
    user_agent_lower = user_agent.lower()
    return any(keyword in user_agent_lower for keyword in bot_keywords)
