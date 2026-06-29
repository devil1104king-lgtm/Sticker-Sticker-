import re
from datetime import datetime

def format_user_info(user_id: int, username: str = None, first_name: str = None) -> str:
    """Format user info for logging."""
    name = first_name or "Unknown"
    username_str = f" (@{username})" if username else ""
    return f"{name}{username_str} [ID: {user_id}]"

def parse_channel_link(link: str) -> str:
    """Extract channel username or ID from input."""
    # If it's a username (starts with @) or a number (ID), return as is.
    if link.startswith("@"):
        return link
    if link.isdigit() or (link.startswith("-") and link[1:].isdigit()):
        return link
    # Assume it's a full link like https://t.me/username
    match = re.search(r"t\.me/([a-zA-Z0-9_]+)", link)
    if match:
        return "@" + match.group(1)
    return link  # fallback

def format_datetime(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else "N/A"
