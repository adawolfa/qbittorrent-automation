# qBittorrent Automation

I may or may not have a qBittorrent client hosted in a self-hosted Coolify behind a VPN.

This tool:

1. Automatically toggles qBittorrent's alternative speed limits based on whether my PC is online (ping check).
2. Monitors the public IP address of my VPN container and sends notifications if it becomes unreachable or its IP
   changes to something I don't expect.
3. Provides a simple web UI to see the current status and manually override the automatic speed control.
4. Reports status and errors via ntfy notifications.
5. Runs as Docker container in Coolify itself.

### Quick Start

```bash
docker compose up -d
```

### Configuration

| Variable             | Default                   | Description                                                       |
|----------------------|---------------------------|-------------------------------------------------------------------|
| `CHECK_INTERVAL`     | `60`                      | Check interval in seconds                                         |
| `QBITTORRENT_URL`    | `http://qbittorrent:8080` | qBittorrent WebUI URL                                             |
| `PING_HOST`          | *(empty)*                 | Host to ping for speed control (disabled if empty)                |
| `IP_CHECK_CONTAINER` | *(empty)*                 | Docker container name for IP check                                |
| `IP_ALLOWED`         | *(empty)*                 | Allowed IPs/networks, comma-separated (e.g. `1.2.3.4,10.0.0.0/8`) |
| `IP_DENIED`          | *(empty)*                 | Denied IPs/networks, comma-separated                              |
| `NTFY_URL`           | *(empty)*                 | ntfy URL (e.g. `https://user:pass@ntfy.example.com/topic`)        |
| `HTTP_PORT`          | `8090`                    | Web UI port                                                       |
| `LOG_LEVEL`          | `INFO`                    | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`)                   |

### docker-compose.yml

```yaml
services:
  qbittorrent-automation:
    build: .
    restart: unless-stopped
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    network_mode: host
    environment:
      - CHECK_INTERVAL=60
      - QBITTORRENT_URL=http://localhost:8080
      - PING_HOST=
      - IP_CHECK_CONTAINER=my-vpn-container
      - IP_ALLOWED=
      - IP_DENIED=203.0.113.0/24
      - NTFY_URL=https://ntfy.example.com/alerts
      - HTTP_PORT=8090
      - LOG_LEVEL=INFO
```