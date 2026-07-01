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
        self.songs: list[Song] = _mock_songs()
        self.is_playing: bool = False
        self.current_song_id: Optional[str] = None

    def add_song(self, song: Song, position: Optional[int] = None) -> None:
        #todo: implementar a inserção de música na fila
        pass

    def remove_song(self, song_id: str) -> bool:
        #todo: implementar a remoção de música da fila
        pass

    def set_playing(self, is_playing: bool) -> None:
        #todo: implementar a atualização do estado de reprodução
        pass