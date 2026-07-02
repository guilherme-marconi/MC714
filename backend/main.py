from fastapi import FastAPI
from pydantic import BaseModel

from backend.playlist import Playlist

playlist = Playlist()

app = FastAPI(title="Playlist P2P")

class AddSongRequest(BaseModel):
    title: str
    artist: str
    position: int | None = None

class RemoveSongRequest(BaseModel):
    song_id: str

@app.post("/actions/add")
async def action_add(req: AddSongRequest) -> dict:
    """"
    Adiciona uma música na fila.

    1. Pede acesso acesso via exclusão mútua
    2. Registra o evento no relogio
    3. Aplica a mudança na fila e replica no peers
    4. Libera a exclusão 
    """

    # TODO: orquestrar 
    raise NotImplementedError

@app.post("/actions/remove")
async def action_remove(req: RemoveSongRequest) -> dict:
    """"
    Remove uma música da fila.

    1. Pede acesso acesso via exclusão mútua
    2. Registra o evento no relogio
    3. Aplica a mudança na fila e replica no peers
    4. Libera a exclusão 
    """

    # TODO: orquestrar 
    raise NotImplementedError

@app.post("/actions/play")
async def action_play() -> dict:
    """
    Requisita tocar o player

    1. So o lider confirma o comando.
    2. Nós não lideres levam pedido para o lider eleito.
    """
    raise NotImplementedError

@app.post("/actions/pause")
async def action_pause() -> dict:
    """
    Requisita pausar o player

    1. So o lider confirma o comando.
    2. Nós não lideres levam pedido para o lider eleito.
    """
    raise NotImplementedError