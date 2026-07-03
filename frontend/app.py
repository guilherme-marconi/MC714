import html

import requests
import streamlit as st

NODES = {"n1": "http://localhost:8001","n2": "http://localhost:8002","n3": "http://localhost:8003"}

GREEN = "#1DB954"
GREEN_LIGHT = "#1ED760"
BACKGROUND = "#121212"
CARD = "#181818"
LINE = "#282828"
TEXT = "#FFFFFF"
TEXT_MUTED = "#B3B3B3"
RED = "#E22134"

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

    border = GREEN if is_leader else LINE
    if is_leader:
        badge = (f'<span style="background:{GREEN};color:#000;padding:2px 10px;'
                 f'border-radius:12px;font-size:12px;font-weight:700;">★ LEADER</span>')
    else:
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
        st.success(f"Play sent to {target}.") if ok else st.error(f"Failed: {result}")
    if col_pause.button("Pause", use_container_width=True):
        ok, result = post_action(target_url, "/actions/pause")
        st.success(f"Pause sent to {target}.") if ok else st.error(f"Failed: {result}")

    st.divider()
    if st.button("🔄 Refresh now", use_container_width=True):
        st.rerun()


st.markdown(
    f'<h1 style="color:{GREEN};margin-bottom:0;">🎵 Distributed Playlist</h1>'
    f'<div style="color:#777;margin-bottom:14px;">Each column is a node. The queue converges '
    f'across all nodes via replication · the leader is elected by Bully · ordering follows the Lamport clock.</div>',
    unsafe_allow_html=True,
)


@st.fragment(run_every=2)
def state_panel():
    columns = st.columns(len(NODES))
    for column, (node_id, url) in zip(columns, NODES.items()):
        with column:
            st.markdown(render_node_card(node_id, fetch_state(url)), unsafe_allow_html=True)


state_panel()