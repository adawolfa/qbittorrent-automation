import threading


class State:
    def __init__(self):
        self._lock = threading.Lock()
        # IP check
        self.current_ip: str | None = None
        self.ip_ok: bool | None = None
        # Ping
        self.host_online: bool | None = None
        # Alt speed override: None = automatic, True = force on, False = force off
        self._override: bool | None = None
        # Current alt speed state
        self.alt_speed_enabled: bool | None = None
        # qBittorrent reachable
        self.qbt_ok: bool | None = None

    @property
    def override(self) -> bool | None:
        with self._lock:
            return self._override

    def set_override(self, alt_speed_on: bool) -> None:
        with self._lock:
            self._override = alt_speed_on

    def clear_override(self) -> None:
        with self._lock:
            self._override = None


state = State()
