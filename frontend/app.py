import html
import json
import os
import threading

import requests
import streamlit as st

# No Docker o docker-compose injeta NODES_JSON com os nomes de serviço (node1:8000 etc.).
# Sem essa env (rodando local), cai no padrão localhost:8001/8002/8003.
DEFAULT_NODES = {
    "n1": "http://localhost:8001",
    "n2": "http://localhost:8002",
    "n3": "http://localhost:8003",
}
NODES = json.loads(os.environ.get("NODES_JSON", json.dumps(DEFAULT_NODES)))

GREEN = "#1DB954"
GREEN_LIGHT = "#1ED760"
BACKGROUND = "#121212"
CARD = "#181818"
LINE = "#282828"
TEXT = "#FFFFFF"
TEXT_MUTED = "#B3B3B3"
RED = "#E22134"
YELLOW = "#E2B21A"

REQ_TIMEOUT = 2    
ACT_TIMEOUT = 5     


def fetch_state(node_url: str) -> dict | None:
    """Lê GET /state de um nó. Retorna o dict, ou None se o nó estiver fora."""
    try:
        resp = requests.get(f"{node_url}/state", timeout=REQ_TIMEOUT)
        resp.raise_for_status()
        return resp.json()
    except requests.exceptions.RequestException:
        return None


def post_action(node_url: str, path: str, payload: dict | None = None):
    """Envia uma ação. Retorna (ok, resultado_ou_erro)."""
    try:
        resp = requests.post(f"{node_url}{path}", json=payload or {}, timeout=ACT_TIMEOUT)
        resp.raise_for_status()
        try:
            return True, resp.json()
        except ValueError:
            return True, {}
    except requests.exceptions.RequestException as exc:
        return False, str(exc)


KIND_COLORS = {
    "lamport": "#4FADEA",
    "mutex": "#E29A2E",
    "election": "#B980F0",
    "playlist": GREEN,
    "admin": "#9AA0A6",
}


def fetch_events(node_url: str) -> list:
    """Lê GET /events de um nó. Retorna a lista (vazia se o nó não responder)."""
    try:
        resp = requests.get(f"{node_url}/events", timeout=REQ_TIMEOUT)
        resp.raise_for_status()
        return resp.json().get("events", [])
    except requests.exceptions.RequestException:
        return []


def disparar_em_paralelo(reqs: list) -> None:
    """Dispara vários POST /actions/* no MESMO instante, direto da UI.

    Uma Barrier faz os threads saírem juntos; não esperamos a resposta (as
    ações seguram a seção crítica pela câmera-lenta). A timeline mostra o
    resultado do conflito (REQUEST/DEFER/ENTER/RELEASE).
    """
    barreira = threading.Barrier(len(reqs))

    def _um(url: str, path: str, payload: dict) -> None:
        try:
            barreira.wait(timeout=5)
            requests.post(f"{url}{path}", json=payload, timeout=30)
        except Exception:
            pass

    for url, path, payload in reqs:
        threading.Thread(target=_um, args=(url, path, payload), daemon=True).start()


def _song_title(songs: list, song_id) -> str:
    for s in songs:
        if s.get("id") == song_id:
            return str(s.get("title", ""))
    return str(song_id)


def render_node_card(node_id: str, state: dict | None) -> str:
    if state is None:
        return f"""
        <div style="background:{CARD};border:2px solid {RED};border-radius:12px;
                    padding:16px;min-height:260px;">
            <div style="font-size:22px;font-weight:700;color:{RED};">{html.escape(node_id)}</div>
            <div style="color:{RED};margin-top:8px;font-weight:600;">● OFFLINE</div>
            <div style="color:#777;margin-top:6px;font-size:13px;">No response from /state.
            Killing a node here is expected in the election demo.</div>
        </div>
        """

    reported_id = state.get("node_id", node_id)
    leader = state.get("leader")
    is_leader = leader is not None and leader == reported_id
    clock = state.get("clock", "—")
    is_playing = bool(state.get("is_playing", False))
    current_id = state.get("current_song_id")
    songs = state.get("songs", []) or []

    alive = bool(state.get("alive", True))
    if not alive:
        border = YELLOW
        badge = ('<span style="background:#E2B21A;color:#000;padding:2px 10px;'
                 'border-radius:12px;font-size:12px;font-weight:700;">💀 KILLED</span>')
    elif is_leader:
        border = GREEN
        badge = (f'<span style="background:{GREEN};color:#000;padding:2px 10px;'
                 f'border-radius:12px;font-size:12px;font-weight:700;">★ LEADER</span>')
    else:
        border = LINE
        leader_label = html.escape(str(leader)) if leader else "—"
        badge = f'<span style="color:{TEXT_MUTED};font-size:12px;">leader: {leader_label}</span>'

    if is_playing and current_id:
        now_playing = f'▶ {html.escape(_song_title(songs, current_id))}'
    else:
        now_playing = "⏸ paused"

    rows = []
    for index, s in enumerate(songs, start=1):
        song_id = s.get("id")
        title = html.escape(str(s.get("title", "")))
        artist = html.escape(str(s.get("artist", "")))
        playing = (song_id == current_id and is_playing)
        row_bg = "rgba(29,185,84,0.15)" if playing else "transparent"
        color = GREEN if playing else TEXT
        rows.append(
            f'<div style="background:{row_bg};padding:6px 8px;border-radius:6px;margin-bottom:4px;">'
            f'<span style="color:{color};font-weight:600;font-size:14px;">{index}. {title}</span>'
            f'<br><span style="color:{TEXT_MUTED};font-size:12px;">{artist}</span></div>'
        )
    list_html = "".join(rows) if rows else f'<div style="color:#777;">(empty queue)</div>'

    return f"""
    <div style="background:{CARD};border:2px solid {border};border-radius:12px;
                padding:16px;min-height:260px;">
        <div style="display:flex;justify-content:space-between;align-items:center;">
            <span style="font-size:22px;font-weight:700;color:{TEXT};">{html.escape(node_id)}</span>
            {badge}
        </div>
        <div style="margin-top:8px;">
            <span style="background:{LINE};color:{TEXT_MUTED};padding:2px 8px;border-radius:10px;
                         font-size:12px;">🕐 clock: {html.escape(str(clock))}</span>
            <span style="color:{GREEN};font-size:13px;margin-left:8px;">{now_playing}</span>
        </div>
        <hr style="border:none;border-top:1px solid {LINE};margin:10px 0;">
        {list_html}
    </div>
    """


st.set_page_config(page_title="Distributed Playlist", page_icon="🎵", layout="wide")

st.markdown(f"""
<style>
.stApp {{ background-color: {BACKGROUND}; }}
[data-testid="stSidebar"] {{ background-color: #000000; }}
h1, h2, h3, h4 {{ color: {TEXT}; }}
.stButton > button {{
    background-color: {GREEN}; color: #000000; border: none;
    border-radius: 20px; font-weight: 700;
}}
.stButton > button:hover {{ background-color: {GREEN_LIGHT}; color: #000000; }}
</style>
""", unsafe_allow_html=True)


# ---------------- Barra lateral: controles (fora do fragmento, não piscam) --------
with st.sidebar:
    st.markdown("### 🎛 Controls")
    target = st.selectbox("Target node for actions", list(NODES.keys()))
    target_url = NODES[target]

    st.markdown("#### Add song")
    title = st.text_input("Title", key="add_title")
    artist = st.text_input("Artist", key="add_artist")
    at_end = st.checkbox("Add to end of queue", value=True)
    position = None
    if not at_end:
        position = int(st.number_input("Position", min_value=0, step=1, value=0))
    if st.button("Add", use_container_width=True):
        if title.strip() and artist.strip():
            ok, result = post_action(
                target_url, "/actions/add",
                {"title": title, "artist": artist, "position": position},
            )
            if ok:
                st.success(f"Add sent to {target}.")
            else:
                st.error(f"Failed: {result}")
        else:
            st.warning("Fill in title and artist.")

    st.markdown("#### Remove song")
    target_state = fetch_state(target_url)
    target_songs = (target_state.get("songs", []) if target_state else []) or []
    if target_songs:
        options = {f'{s.get("title")} — {s.get("artist")}': s.get("id") for s in target_songs}
        choice = st.selectbox("Song", list(options.keys()))
        if st.button("Remove", use_container_width=True):
            ok, result = post_action(target_url, "/actions/remove", {"song_id": options[choice]})
            if ok:
                st.success(f"Remove sent to {target}.")
            else:
                st.error(f"Failed: {result}")
    else:
        st.caption("Node offline or empty queue.")

    st.markdown("#### Player (confirmed by leader)")
    col_play, col_pause = st.columns(2)
    if col_play.button("Play", use_container_width=True):
        ok, result = post_action(target_url, "/actions/play")
        if ok:
            st.success(f"Play sent to {target}.")
        else:
            st.error(f"Failed: {result}")
    if col_pause.button("Pause", use_container_width=True):
        ok, result = post_action(target_url, "/actions/pause")
        if ok:
            st.success(f"Pause sent to {target}.")
        else:
            st.error(f"Failed: {result}")

    st.markdown("#### 💀 Falha & eleição")
    col_kill, col_revive = st.columns(2)
    if col_kill.button("Kill", use_container_width=True):
        post_action(target_url, "/admin/kill")
        st.warning(f"{target} morto (simulado). Os outros vão reeleger.")
    if col_revive.button("Revive", use_container_width=True):
        post_action(target_url, "/admin/revive")
        st.success(f"{target} revivido — vai reentrar na eleição.")

    st.markdown("#### 🐢 Câmera-lenta")
    delay = st.slider("Delay por operação (s)", 0.0, 3.0, 0.0, 0.5)
    if st.button("Aplicar em todos os nós", use_container_width=True):
        for url in NODES.values():
            post_action(url, "/admin/config", {"step_delay": delay})
        st.info(f"Delay = {delay:.1f}s em todos os nós.")

    st.divider()
    if st.button("🔄 Refresh now", use_container_width=True):
        st.rerun()


st.markdown(
    f'<h1 style="color:{GREEN};margin-bottom:0;">🎵 Distributed Playlist</h1>'
    f'<div style="color:#777;margin-bottom:14px;">Each column is a node. The queue converges '
    f'across all nodes via replication · the leader is elected by Bully · ordering follows the Lamport clock.</div>',
    unsafe_allow_html=True,
)


with st.expander("⚔️ Teste de conflito (forçar exclusão mútua)", expanded=False):
    st.caption("A própria UI dispara dois requests /actions/* no mesmo instante (um por nó). "
               "O Ricart-Agrawala arbitra quem entra primeiro na seção crítica.")
    _node_ids = list(NODES.keys())
    _c1, _c2 = st.columns(2)
    conf_a = _c1.selectbox("Nó A", _node_ids, index=0, key="conf_a")
    conf_b = _c2.selectbox("Nó B", _node_ids, index=min(1, len(_node_ids) - 1), key="conf_b")

    conf_modo = st.radio("Ação", ["Remover a mesma música", "Ambos adicionam"],
                         horizontal=True, key="conf_modo")
    conf_song_id = None
    conf_title_a = conf_title_b = None
    if conf_modo == "Remover a mesma música":
        _estado_a = fetch_state(NODES[conf_a]) or {}
        _songs = _estado_a.get("songs", []) or []
        if _songs:
            _opcoes = {f'{s.get("title")} — {s.get("artist")}': s.get("id") for s in _songs}
            _escolha = st.selectbox("Música que os dois vão remover", list(_opcoes.keys()), key="conf_song")
            conf_song_id = _opcoes[_escolha]
        else:
            st.info("Nó A sem músicas na fila (ou offline).")
    else:
        conf_title_a = st.text_input("Música do Nó A", "Faixa A", key="conf_ta")
        conf_title_b = st.text_input("Música do Nó B", "Faixa B", key="conf_tb")

    conf_hold = st.number_input("Câmera-lenta durante (s)", min_value=0.0, max_value=4.0,
                                value=2.0, step=0.5, key="conf_hold",
                                help="Segura a seção crítica pra dar tempo de ver o DEFER do outro nó.")

    if st.button("⚔️ Disparar conflito", use_container_width=True, key="conf_go"):
        if conf_a == conf_b:
            st.error("Escolha dois nós diferentes.")
        elif conf_modo == "Remover a mesma música" and not conf_song_id:
            st.error("Selecione uma música (Nó A precisa ter fila).")
        else:
            for _url in NODES.values():
                post_action(_url, "/admin/config", {"step_delay": conf_hold})
            if conf_modo == "Remover a mesma música":
                _reqs = [
                    (NODES[conf_a], "/actions/remove", {"song_id": conf_song_id}),
                    (NODES[conf_b], "/actions/remove", {"song_id": conf_song_id}),
                ]
            else:
                _reqs = [
                    (NODES[conf_a], "/actions/add", {"title": conf_title_a, "artist": conf_a}),
                    (NODES[conf_b], "/actions/add", {"title": conf_title_b, "artist": conf_b}),
                ]
            disparar_em_paralelo(_reqs)
            st.success(f"Disparado! {conf_a} e {conf_b} foram no mesmo instante. Veja DEFER/ENTER na timeline.")


@st.fragment(run_every=1)
def live_panel():
    columns = st.columns(len(NODES))
    for column, (node_id, url) in zip(columns, NODES.items()):
        with column:
            st.markdown(render_node_card(node_id, fetch_state(url)), unsafe_allow_html=True)

    st.markdown("### 📜 Timeline de eventos")
    st.caption("Ordem de chegada · L = relógio de Lamport · mais recentes no topo")

    todos = []
    for node_id, url in NODES.items():
        todos.extend(fetch_events(url))
    todos.sort(key=lambda e: e.get("ts", 0))

    linhas = []
    for e in reversed(todos[-40:]):
        cor = KIND_COLORS.get(e.get("kind"), TEXT)
        lam = e.get("lamport")
        lam_txt = f"L{lam}" if lam is not None else "L—"
        node = html.escape(str(e.get("node_id", "")))
        kind = html.escape(str(e.get("kind", "")))
        detail = html.escape(str(e.get("detail", "")))
        linhas.append(
            f'<div style="padding:3px 8px;border-left:3px solid {cor};margin-bottom:3px;'
            f'font-family:monospace;font-size:13px;background:{CARD};">'
            f'<span style="color:{TEXT_MUTED};">[{lam_txt}]</span> '
            f'<b style="color:{cor};">{node}</b> '
            f'<span style="color:{cor};">{kind}</span>'
            f'<span style="color:{TEXT};"> — {detail}</span></div>'
        )
    st.markdown(
        "".join(linhas) or '<div style="color:#777;">(sem eventos ainda)</div>',
        unsafe_allow_html=True,
    )


live_panel()