import logging
from urllib.parse import urlparse

import requests

from src import config

logger = logging.getLogger(__name__)


def _parse_url() -> tuple[str, str | None, str | None]:
    """Parse NTFY_URL into (url, user, password). Supports https?://[user:password@]host/topic."""
    raw = config.NTFY_URL
    if not raw:
        return "", None, None

    parsed = urlparse(raw)
    user = parsed.username
    password = parsed.password

    # Rebuild URL without credentials
    if user:
        netloc = parsed.hostname
        if parsed.port:
            netloc += f":{parsed.port}"
        url = parsed._replace(netloc=netloc).geturl()
    else:
        url = raw

    return url, user, password


def send(message: str, title: str = "qBittorrent Automation", priority: str = "default") -> None:
    """Send a notification via ntfy."""
    url, user, password = _parse_url()
    if not url:
        return

    auth = None
    if user and password:
        auth = (user, password)

    try:
        resp = requests.post(
            url,
            data=message.encode("utf-8"),
            headers={
                "Title": title,
                "Priority": priority,
            },
            auth=auth,
            timeout=10,
        )
        resp.raise_for_status()
        logger.info("Notification sent: %s", message)
    except Exception:
        logger.exception("Failed to send ntfy notification")
