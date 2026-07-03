import threading
import requests
from backend.lamport import LamportClock

RELEASED = "RELEASED"
WANTED = "WANTED"
HELD = "HELD"

class ExclusaoMutua:
    def __init__(self, node_id: str, peers: dict[str, str], clock: LamportClock) -> None:
        self.node_id = node_id
        self.peers = peers
        self.clock = clock
        self._lock = threading.Lock()
        self._state = RELEASED
        self._request_timestamp = 0
        self._ok_received = set()
        self._deferred = []
        self._event = threading.Event()


    @staticmethod
    def has_priority(timestamp_A: int, id_A: str, timestamp_B: int, id_B: str) -> bool:
        if timestamp_A < timestamp_B:
            return True
        elif timestamp_A == timestamp_B and id_A < id_B:
            return True
        else:
            return False


    def request_access(self) -> None:
        with self._lock:
            self._state = WANTED
            self._request_timestamp = self.clock.tick()
            self._ok_received = set()
            self._event.clear()

        for peer_id, base_url in self.peers.items():
            self._send_request(base_url, self._request_timestamp, self.node_id)

        self._event.wait()

        with self._lock:
            self._state = HELD


    def release_access(self) -> None:
        with self._lock:
            self._state = RELEASED
            deferred_copy = list(self._deferred)
            self._deferred.clear()

        for peer_id in deferred_copy:
            base_url = self.peers.get(peer_id)
            if base_url:
                self._send_ok(base_url, self.node_id)


    def on_request(self, sender_id: str, timestamp: int) -> None:
        self.clock.update(timestamp)

        with self._lock:
            if self._state == HELD:
                self._deferred.append(sender_id)
                grant = False
            elif self._state == WANTED and self.has_priority(
                    self._request_timestamp, self.node_id, timestamp, sender_id):
                self._deferred.append(sender_id)
                grant = False
            else:
                grant = True

        if grant:
            base_url = self.peers.get(sender_id)
            if base_url:
                self._send_ok(base_url, self.node_id)


    def on_ok(self, sender_id: str) -> None:
        with self._lock:
            self._ok_received.add(sender_id)
            if self._state == WANTED and len(self._ok_received) >= len(self.peers):
                self._event.set()


    def _send_request(self, base_url: str, timestamp: int, sender_id: str) -> None:
        try:
            requests.post(
                f"{base_url}/mutex/request",
                json={"timestamp": timestamp, "sender_id": sender_id},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            pass


    def _send_ok(self, base_url: str, sender_id: str) -> None:
        try:
            requests.post(
                f"{base_url}/mutex/ok",
                json={"sender_id": sender_id},
                timeout=5,
            )
        except requests.exceptions.RequestException:
            pass