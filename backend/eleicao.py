import threading
import time
import requests

from backend import eventos


class Election:
    def __init__(self, node_id: str, peers: dict[str, str]) -> None:
        self.node_id = node_id
        self.peers = peers
        self._lock = threading.Lock()
        self.leader = None
        self._in_election = False


    def start_election(self) -> None:
        with self._lock:
            if self._in_election:
                return
            self._in_election = True

        eventos.log_eleicao("START", "procurando nós de id maior")

        higher_responded = False
        for peer_id, base_url in self.peers.items():
            if peer_id > self.node_id:
                if self._send_election(base_url):
                    higher_responded = True

        if not higher_responded:
            self.become_leader()

        with self._lock:
            self._in_election = False


    def become_leader(self) -> None:
        with self._lock:
            self.leader = self.node_id

        eventos.log_eleicao("LEADER", f"{self.node_id} virou lider")

        for peer_id, base_url in self.peers.items():
            if peer_id < self.node_id:
                self._send_coordinator(base_url, self.node_id)


    def receive_election(self, sender_id: str) -> None:
        threading.Thread(target=self.start_election, daemon=True).start()


    def receive_coordinator(self, leader_id: str) -> None:
        with self._lock:
            self.leader = leader_id
            self._in_election = False
        eventos.log_eleicao("COORDINATOR", f"lider = {leader_id}")


    def monitor_leader(self) -> None:
        while True:
            time.sleep(3)
            with self._lock:
                current_leader = self.leader
            if current_leader == self.node_id:
                continue
            if current_leader is None or not self._ping(current_leader):
                eventos.log_eleicao("DETECT", f"lider {current_leader} inacessivel")
                self.start_election()


    def start(self) -> None:
        threading.Thread(target=self.monitor_leader, daemon=True).start()
        threading.Thread(target=self.start_election, daemon=True).start()


    def _send_election(self, base_url: str) -> bool:
        try:
            response = requests.post(
                f"{base_url}/election",
                json={"sender_id": self.node_id},
                timeout=2,
            )
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False


    def _send_coordinator(self, base_url: str, leader_id: str) -> None:
        try:
            requests.post(
                f"{base_url}/coordinator",
                json={"leader_id": leader_id},
                timeout=2,
            )
        except requests.exceptions.RequestException:
            pass


    def _ping(self, leader_id: str) -> bool:
        base_url = self.peers.get(leader_id)
        if not base_url:
            return False
        try:
            response = requests.get(f"{base_url}/health", timeout=2)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False