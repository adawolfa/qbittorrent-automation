import logging
import requests
from src import config

logger = logging.getLogger(__name__)

_TIMEOUT = 10


def set_alt_speed(enabled: bool) -> None:
    """Enable or disable alternative speed limits."""
    url = f"{config.QBITTORRENT_URL}/api/v2/transfer/toggleSpeedLimitsMode"
    current = get_alt_speed()
    if current == enabled:
        logger.debug("Alt speed already %s", "enabled" if enabled else "disabled")
        return
    requests.post(url, timeout=_TIMEOUT)
    logger.info("Alt speed limits %s", "enabled" if enabled else "disabled")


def get_alt_speed() -> bool:
    """Check if alternative speed limits are currently enabled."""
    url = f"{config.QBITTORRENT_URL}/api/v2/transfer/speedLimitsMode"
    resp = requests.get(url, timeout=_TIMEOUT)
    return resp.text.strip() == "1"
