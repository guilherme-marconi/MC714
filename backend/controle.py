import threading
import time

from backend import eventos

_lock = threading.Lock()
_estado = {"alive": True, "step_delay": 0.0}


def esta_vivo() -> bool:
    with _lock:
        return _estado["alive"]


def matar() -> None:
    with _lock:
        _estado["alive"] = False
    eventos.log_admin("KILLED (nó simulado como morto)")


def reviver() -> None:
    with _lock:
        _estado["alive"] = True
    eventos.log_admin("REVIVED (nó de volta)")


def get_delay() -> float:
    with _lock:
        return _estado["step_delay"]


def set_delay(segundos: float) -> None:
    segundos = max(0.0, float(segundos))
    with _lock:
        _estado["step_delay"] = segundos
    eventos.log_admin(f"DELAY = {segundos:.1f}s")


def esperar() -> None:
    """Dorme o tempo de câmera-lenta configurado (0 = sem atraso)."""
    delay = get_delay()
    if delay > 0:
        time.sleep(delay)
