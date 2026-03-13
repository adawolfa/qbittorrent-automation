import logging
import subprocess

logger = logging.getLogger(__name__)


def is_host_online(host: str, timeout: int = 2) -> bool:
    """Check if a host is reachable via ICMP ping."""
    try:
        result = subprocess.run(
            ["ping", "-c", "1", "-W", str(timeout), host],
            capture_output=True,
            timeout=timeout + 2,
        )
        online = result.returncode == 0
        logger.info("Ping %s: %s", host, "online" if online else "offline")
        return online
    except subprocess.TimeoutExpired:
        logger.info("Ping %s: timeout", host)
        return False
