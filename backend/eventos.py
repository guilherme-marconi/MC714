import os
import threading
import time

NODE_ID = os.environ.get("NODE_ID", "node")

MAX_EVENTS = 500


class EventLog:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._events: list[dict] = []
        self._seq = 0

    def add(self, kind: str, detail: str, lamport=None) -> None:
        with self._lock:
            self._seq += 1
            self._events.append({
                "seq": self._seq,
                "ts": time.time(),
                "lamport": lamport,
                "node_id": NODE_ID,
                "kind": kind,
                "detail": detail,
            })
            if len(self._events) > MAX_EVENTS:
                self._events = self._events[-MAX_EVENTS:]

    def list(self, since: int = 0) -> list[dict]:
        with self._lock:
            return [e for e in self._events if e["seq"] > since]


log = EventLog()


def log_lamport(valor: int, motivo: str) -> None:
    log.add("lamport", f"{motivo} -> L{valor}", lamport=valor)


def log_mutex(fase: str, detail: str = "", lamport=None) -> None:
    log.add("mutex", fase if not detail else f"{fase}: {detail}", lamport=lamport)


def log_eleicao(fase: str, detail: str = "") -> None:
    log.add("election", fase if not detail else f"{fase}: {detail}")


def log_playlist(acao: str, detail: str = "", lamport=None) -> None:
    log.add("playlist", acao if not detail else f"{acao}: {detail}", lamport=lamport)


def log_admin(msg: str) -> None:
    log.add("admin", msg)


def listar(since: int = 0) -> list[dict]:
    return log.list(since)
