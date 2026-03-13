import json
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

from src import config
from src import qbittorrent
from src.state import state

logger = logging.getLogger(__name__)

INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>qBittorrent Automation</title>
<style>
  *, *::before, *::after { box-sizing: border-box; }
  body { font-family: -apple-system, system-ui, sans-serif; margin: 0; padding: 20px; background: #1a1a2e; color: #e0e0e0; }
  h1 { color: #00d4ff; margin-bottom: 24px; font-size: 1.4em; }
  .card { background: #16213e; border-radius: 8px; padding: 16px; margin-bottom: 16px; }
  .card h2 { margin: 0 0 12px; font-size: 1.1em; color: #8899aa; }
  .status { display: flex; gap: 12px; flex-wrap: wrap; }
  .badge { padding: 6px 14px; border-radius: 16px; font-size: 0.9em; font-weight: 600; }
  .ok { background: #0a3d2a; color: #4caf50; }
  .warn { background: #3d2a0a; color: #ff9800; }
  .err { background: #3d0a0a; color: #f44336; }
  .neutral { background: #2a2a3e; color: #8899aa; }
  .info-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #1a1a2e; }
  .info-row:last-child { border-bottom: none; }
  .label { color: #8899aa; }
  .value { font-weight: 600; }
  .controls { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; }
  button { padding: 8px 18px; border: none; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.95em; }
  .btn-primary { background: #00d4ff; color: #1a1a2e; }
  .btn-danger { background: #f44336; color: white; }
  .btn-success { background: #4caf50; color: white; }
  .btn-secondary { background: #334; color: #e0e0e0; }
  .override-active { border: 2px solid #ff9800; }
</style>
</head>
<body>
<h1>qBittorrent Automation</h1>

<div class="card" id="ip-card">
  <h2>IP Check</h2>
  <div class="status" id="ip-status"></div>
</div>

<div class="card" id="ping-card">
  <h2>Ping</h2>
  <div class="status" id="ping-status"></div>
</div>

<div class="card" id="speed-card">
  <h2>Alternative Speed Limits</h2>
  <div id="speed-info"></div>
  <div class="controls">
    <button class="btn-success" onclick="setOverride(true)">Force ON</button>
    <button class="btn-danger" onclick="setOverride(false)">Force OFF</button>
    <button class="btn-secondary" onclick="clearOverride()">Auto</button>
  </div>
</div>

<script>
async function load() {
  try {
    const r = await fetch('/api/status');
    const d = await r.json();

    // IP
    const ips = document.getElementById('ip-status');
    if (d.ip === null) {
      ips.innerHTML = '<span class="badge neutral">waiting...</span>';
    } else if (d.ip === '') {
      ips.innerHTML = '<span class="badge err">unreachable</span>';
    } else {
      const cls = d.ip_ok ? 'ok' : 'err';
      ips.innerHTML = '<span class="badge ' + cls + '">' + d.ip + '</span>';
    }

    // Ping
    const ps = document.getElementById('ping-status');
    if (d.host_online === null) {
      ps.innerHTML = '<span class="badge neutral">waiting...</span>';
    } else {
      const cls = d.host_online ? 'ok' : 'neutral';
      const txt = d.host_online ? d.ping_host + ' online' : d.ping_host + ' offline';
      ps.innerHTML = '<span class="badge ' + cls + '">' + txt + '</span>';
    }

    // Speed
    const si = document.getElementById('speed-info');
    const sc = document.getElementById('speed-card');
    const ov = d.override;
    const isOverride = ov !== null;
    sc.className = isOverride ? 'card override-active' : 'card';

    const mode = isOverride ? 'MANUAL' : 'AUTO';
    const altOn = d.alt_speed_enabled;
    const altLabel = altOn === null ? 'unknown' : (altOn ? 'ON' : 'OFF');
    const altCls = altOn ? 'ok' : 'neutral';

    si.innerHTML =
      '<div class="info-row"><span class="label">Mode</span><span class="value">' + mode + '</span></div>' +
      '<div class="info-row"><span class="label">Alt speed limits</span><span class="badge ' + altCls + '">' + altLabel + '</span></div>';
  } catch(e) {
    console.error(e);
  }
}

async function setOverride(on) {
  await fetch('/api/override?alt_speed=' + (on ? '1' : '0'), {method:'POST'});
  load();
}

async function clearOverride() {
  await fetch('/api/override', {method:'DELETE'});
  load();
}

load();
setInterval(load, 5000);
</script>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.debug(format, *args)

    def _json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def _html(self, html, status=200):
        body = html.encode()
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html(INDEX_HTML)
        elif parsed.path == "/api/status":
            self._json({
                "ip": state.current_ip,
                "ip_ok": state.ip_ok,
                "host_online": state.host_online,
                "ping_host": config.PING_HOST,
                "override": state.override,
                "alt_speed_enabled": state.alt_speed_enabled,
            })
        else:
            self.send_error(404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/override":
            qs = parse_qs(parsed.query)
            alt_on = qs.get("alt_speed", ["1"])[0] == "1"
            state.set_override(alt_on)
            qbittorrent.set_alt_speed(alt_on)
            state.alt_speed_enabled = alt_on
            logger.info("Manual override: alt speed %s", "on" if alt_on else "off")
            self._json({"status": "ok", "override": state.override})
        else:
            self.send_error(404)

    def do_DELETE(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/override":
            state.clear_override()
            logger.info("Manual override cleared, returning to automatic mode")
            self._json({"status": "ok", "override": None})
        else:
            self.send_error(404)


def start():
    server = HTTPServer(("0.0.0.0", config.HTTP_PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Web server started on port %d", config.HTTP_PORT)
