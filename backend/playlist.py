from dataclasses import dataclass

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