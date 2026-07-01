import threading


class LamportClock:
    """Relógio de Lamport

    Importa threading para fazer uso do Lock.
    """
    def __init__(self) -> None:
        self._time = 0
        self._lock = threading.Lock()

    def tick(self) -> int:
        """Aumenta em 1 o time do relógio. Usado para registrar atividades locais do processo.
        
        Retorna o timestamp atualizado.
        """
        with self._lock:
            self._time += 1
            return self._time

    def update(self, received_time: int) -> int:
        """Atualiza o relógio ao receber uma mensagem de outro processo.

        Retorna o novo timestamp local
        """
        with self._lock:
            self._time = max(self._time, received_time) + 1
            return self._time

    def now(self) -> int:
        """Retorna o timestamp atual do processo.
        """
        with self._lock:
            return self._time