import os


CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", "60"))

QBITTORRENT_URL = os.environ.get("QBITTORRENT_URL", "http://qbittorrent:8080")

PING_HOST = os.environ.get("PING_HOST", "")

IP_CHECK_CONTAINER = os.environ.get("IP_CHECK_CONTAINER", "")

# Comma-separated IPs/networks (e.g. "1.2.3.4,10.0.0.0/8")
IP_ALLOWED = os.environ.get("IP_ALLOWED", "")
IP_DENIED = os.environ.get("IP_DENIED", "")

NTFY_URL = os.environ.get("NTFY_URL", "")

HTTP_PORT = int(os.environ.get("HTTP_PORT", "8090"))

LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
