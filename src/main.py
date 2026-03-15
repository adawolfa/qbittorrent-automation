import ipaddress
import logging
import time

from src import config
from src import docker_exec
from src import ntfy
from src import ping_check
from src import qbittorrent
from src import server
from src.state import state

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def _parse_networks(value: str) -> list[ipaddress.IPv4Network | ipaddress.IPv6Network]:
    """Parse comma-separated IPs/networks into a list of network objects."""
    if not value.strip():
        return []
    networks = []
    for entry in value.split(","):
        entry = entry.strip()
        if entry:
            networks.append(ipaddress.ip_network(entry, strict=False))
    return networks


def _is_ip_ok(ip_str: str) -> bool:
    """Check IP against allowed/denied lists. Returns True if IP is acceptable."""
    addr = ipaddress.ip_address(ip_str)

    allowed = _parse_networks(config.IP_ALLOWED)
    if allowed and not any(addr in net for net in allowed):
        logger.warning("IP %s is not in allowed list", ip_str)
        return False

    denied = _parse_networks(config.IP_DENIED)
    if denied and any(addr in net for net in denied):
        logger.warning("IP %s is in denied list", ip_str)
        return False

    return True


def check_ip():
    """Check the public IP of the target container."""
    if not config.IP_CHECK_CONTAINER:
        logger.debug("IP_CHECK_CONTAINER not set, skipping IP check")
        return

    prev_ip = state.current_ip
    prev_ok = state.ip_ok

    try:
        ip = docker_exec.exec_in_container(
            config.IP_CHECK_CONTAINER, "curl -s --max-time 10 ifconfig.me"
        )
    except Exception:
        ip = ""
        logger.exception("Failed to reach container %s", config.IP_CHECK_CONTAINER)

    if not ip:
        state.current_ip = ""
        state.ip_ok = False
        try:
            _qbt_call(qbittorrent.pause_all)
        except Exception:
            pass
        if prev_ok is not False:
            msg = f"Container {config.IP_CHECK_CONTAINER}: network unreachable (ifconfig.me failed), torrents paused"
            logger.warning(msg)
            ntfy.send(msg, priority="high")
        return

    ok = _is_ip_ok(ip)
    state.current_ip = ip
    state.ip_ok = ok

    if ok:
        logger.info("Container %s public IP: %s (OK)", config.IP_CHECK_CONTAINER, ip)
        if not prev_ok:
            msg = f"Container {config.IP_CHECK_CONTAINER}: IP is OK again ({ip}), resuming torrents"
            logger.info(msg)
            try:
                _qbt_call(qbittorrent.resume_all)
            except Exception:
                pass
            ntfy.send(msg, priority="default")
    else:
        logger.warning("Container %s public IP: %s (NOT acceptable)", config.IP_CHECK_CONTAINER, ip)
        try:
            _qbt_call(qbittorrent.pause_all)
        except Exception:
            pass
        if prev_ok is not False or ip != prev_ip:
            msg = f"Container {config.IP_CHECK_CONTAINER}: IP {ip} is not acceptable! Torrents paused."
            ntfy.send(msg, priority="high")


def _qbt_call(func, *args):
    """Call a qBittorrent function with state tracking and notifications."""
    prev_ok = state.qbt_ok
    try:
        result = func(*args)
        state.qbt_ok = True
        if prev_ok is False:
            msg = "qBittorrent is reachable again"
            logger.info(msg)
            ntfy.send(msg, priority="default")
        return result
    except Exception:
        state.qbt_ok = False
        logger.exception("Failed to communicate with qBittorrent")
        if prev_ok is not False:
            msg = f"qBittorrent unreachable at {config.QBITTORRENT_URL}"
            ntfy.send(msg, priority="high")
        raise


def adjust_speed():
    """Toggle qBittorrent alternative speed limits based on ping or override."""
    override = state.override
    if override is not None:
        logger.debug("Manual override active: alt speed %s", "on" if override else "off")
        try:
            _qbt_call(qbittorrent.set_alt_speed, override)
            state.alt_speed_enabled = override
        except Exception:
            pass
        return

    if not config.PING_HOST:
        logger.debug("PING_HOST not set, skipping ping check")
        return

    try:
        online = ping_check.is_host_online(config.PING_HOST)
    except Exception:
        logger.exception("Ping check failed")
        return

    state.host_online = online

    try:
        alt_on = online
        _qbt_call(qbittorrent.set_alt_speed, alt_on)
        state.alt_speed_enabled = alt_on
        if online:
            logger.info("Host %s is online, alt speed enabled", config.PING_HOST)
        else:
            logger.info("Host %s is offline, alt speed disabled", config.PING_HOST)
    except Exception:
        pass


def run_cycle():
    logger.info("--- Running check cycle ---")
    check_ip()
    adjust_speed()


def main():
    logger.info("Starting qBittorrent automation (interval: %ds)", config.CHECK_INTERVAL)
    server.start()
    while True:
        run_cycle()
        time.sleep(config.CHECK_INTERVAL)


if __name__ == "__main__":
    main()
