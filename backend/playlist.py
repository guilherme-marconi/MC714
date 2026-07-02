import threading
from dataclasses import dataclass
from typing import Optional

@dataclass
class Song:
    id: str
    title: str
    artist: str

def _mock_songs() -> list[Song]:
    return [
        Song(id="s1", title="Me Desculpa Jay-Z", artist="Baco Exu do Blues"),
        Song(id="s2", title="Miçanga", artist="BaianaSystem"),
        Song(id="s3", title="Flor de Plástico", artist="Russo Passapusso"),
        Song(id="s4", title="Leal", artist="Djonga"),
        Song(id="s5", title="Aquela fé", artist="Don L"),
        Song(id="s6", title="Ela é do Tipo", artist="MC Kevin o Chris"),
    ]

class Playlist:
    """
    Estado da fila.
    Cada nó tem um.
    Consistência entre nós é responsabilidade dos algoritmos distribuídos.
    """
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.songs: list[Song] = _mock_songs()
        self.is_playing: bool = False
        self.current_song_id: Optional[str] = None

    def add_song(self, song: Song, position: Optional[int] = None) -> None:
        """Insere uma música na fila (ao final ou numa posição específica)."""
        with self._lock:
            if position is None:
                self.songs.append(song)
            else:
                self.songs.insert(position, song)

    def remove_song(self, song_id: str) -> bool:
        """Remove uma música pelo id. Retorna True se removeu."""
        with self._lock:
            before = len(self.songs)
            self.songs = [s for s in self.songs if s.id != song_id]
            return len(self.songs) < before

    def set_playing(self, playing: bool, song_id: Optional[str] = None) -> None:
        """Atualiza o estado de reprodução."""
        with self._lock:
            self.is_playing = playing
            if song_id is not None:
                self.current_song_id = song_id