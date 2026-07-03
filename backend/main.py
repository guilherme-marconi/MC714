import json
import os

import requests
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from backend.eleicao import Election
from backend.exclusao_mutua import ExclusaoMutua
from backend.lamport import LamportClock
from backend.playlist import Playlist, Song

NODE_ID = os.environ["NODE_ID"]
PEERS = json.loads(os.environ["PEERS"])
ACT_TIMEOUT = 5

clock = LamportClock()
playlist = Playlist()
mutex = ExclusaoMutua(NODE_ID, PEERS, clock)
election = Election(NODE_ID, PEERS)

app = FastAPI(title="Playlist P2P")


class AddSongRequest(BaseModel):
    title: str
    artist: str
    position: int | None = None


class RemoveSongRequest(BaseModel):
    song_id: str


class ReplicateRequest(BaseModel):
    op: str
    timestamp: int
    song: dict | None = None
    position: int | None = None
    song_id: str | None = None
    current_song_id: str | None = None


class MutexRequest(BaseModel):
    timestamp: int
    sender_id: str


class MutexOk(BaseModel):
    sender_id: str


class ElectionMsg(BaseModel):
    sender_id: str


class CoordinatorMsg(BaseModel):
    leader_id: str


def replicate_to_peers(payload: dict) -> None:
    for peer_id, base_url in PEERS.items():
        try:
            requests.post(f"{base_url}/replicate", json=payload, timeout=ACT_TIMEOUT)
        except requests.exceptions.RequestException:
            pass


def _player_command(playing: bool) -> dict:
    op = "play" if playing else "pause"

    if election.leader == NODE_ID:
        timestamp = clock.tick()
        current = playlist.current_song_id
        if playing and current is None and playlist.songs:
            current = playlist.songs[0].id
        playlist.set_playing(playing, current)
        replicate_to_peers({"op": op, "timestamp": timestamp, "current_song_id": current})
        return {"ok": True, "confirmed_by": NODE_ID}

    leader_url = PEERS.get(election.leader)
    if leader_url is None:
        raise HTTPException(status_code=503, detail="Sem líder eleito no momento.")
    try:
        requests.post(f"{leader_url}/actions/{op}", timeout=ACT_TIMEOUT)
    except requests.exceptions.RequestException as exc:
        raise HTTPException(status_code=503, detail=f"Falha ao encaminhar ao líder: {exc}")
    return {"ok": True, "forwarded_to": election.leader}


@app.post("/actions/add")
def action_add(req: AddSongRequest) -> dict:
    mutex.request_access()
    try:
        timestamp = clock.tick()
        song_id = f"s{timestamp}-{NODE_ID}"
        playlist.add_song(Song(id=song_id, title=req.title, artist=req.artist), req.position)
        replicate_to_peers({
            "op": "add",
            "timestamp": timestamp,
            "song": {"id": song_id, "title": req.title, "artist": req.artist},
            "position": req.position,
        })
    finally:
        mutex.release_access()
    return {"ok": True, "song_id": song_id, "timestamp": timestamp}


@app.post("/actions/remove")
def action_remove(req: RemoveSongRequest) -> dict:
    mutex.request_access()
    try:
        timestamp = clock.tick()
        removed = playlist.remove_song(req.song_id)
        replicate_to_peers({
            "op": "remove",
            "timestamp": timestamp,
            "song_id": req.song_id,
        })
    finally:
        mutex.release_access()
    return {"ok": True, "removed": removed, "timestamp": timestamp}


@app.post("/actions/play")
def action_play() -> dict:
    return _player_command(playing=True)


@app.post("/actions/pause")
def action_pause() -> dict:
    return _player_command(playing=False)


@app.post("/replicate")
def replicate(req: ReplicateRequest) -> dict:
    clock.update(req.timestamp)
    if req.op == "add" and req.song is not None:
        playlist.add_song(
            Song(id=req.song["id"], title=req.song["title"], artist=req.song["artist"]),
            req.position,
        )
    elif req.op == "remove" and req.song_id is not None:
        playlist.remove_song(req.song_id)
    elif req.op == "play":
        playlist.set_playing(True, req.current_song_id)
    elif req.op == "pause":
        playlist.set_playing(False)
    return {"ok": True}


@app.get("/state")
def get_state() -> dict:
    songs = [{"id": s.id, "title": s.title, "artist": s.artist} for s in list(playlist.songs)]
    return {
        "node_id": NODE_ID,
        "leader": election.leader,
        "clock": clock.now(),
        "is_playing": playlist.is_playing,
        "current_song_id": playlist.current_song_id,
        "songs": songs,
    }


@app.post("/mutex/request")
def mutex_request(req: MutexRequest) -> dict:
    mutex.on_request(req.sender_id, req.timestamp)
    return {"status": "received"}


@app.post("/mutex/ok")
def mutex_ok(req: MutexOk) -> dict:
    mutex.on_ok(req.sender_id)
    return {"status": "received"}


@app.post("/election")
def election_message(req: ElectionMsg) -> dict:
    election.receive_election(req.sender_id)
    return {"status": "alive"}


@app.post("/coordinator")
def coordinator_message(req: CoordinatorMsg) -> dict:
    election.receive_coordinator(req.leader_id)
    return {"status": "received"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


election.start()