# streamlit_app.py  –  Developer / Admin Testing Console
# ============================================================
# RULE: Only this file is modified.  All backend endpoints are
# consumed AS-IS (no new endpoints, no endpoint modifications).
# ============================================================

import streamlit as st
import requests
import os
import time
import json
from typing import Optional, Dict, Any, List

# ─────────────────────────────────────────────
#  PAGE CONFIG  (must be first Streamlit call)
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="AI Avatar · Dev Console",
    page_icon="🛸",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS  – dark professional theme
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Font ──────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ── Root palette ─────────────────────────── */
:root {
    --bg-base:      #0d1117;
    --bg-card:      #161b22;
    --bg-card2:     #1c2128;
    --border:       #30363d;
    --accent:       #58a6ff;
    --accent2:      #3fb950;
    --accent3:      #f78166;
    --accent4:      #d2a8ff;
    --accent5:      #ffa657;
    --text-primary: #e6edf3;
    --text-muted:   #8b949e;
    --danger:       #f85149;
    --warning:      #d29922;
    --success:      #3fb950;
}

/* ── Global reset ─────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
    background-color: var(--bg-base) !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar ──────────────────────────────── */
[data-testid="stSidebar"] {
    background: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] * {
    color: var(--text-primary) !important;
}

/* ── Main area ────────────────────────────── */
.main .block-container {
    background: var(--bg-base) !important;
    padding-top: 1.5rem !important;
    max-width: 100% !important;
}

/* ── Metric cards ─────────────────────────── */
[data-testid="stMetric"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.05em; }
[data-testid="stMetricValue"] { color: var(--accent) !important; font-size: 2rem !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { color: var(--accent2) !important; }

/* ── Buttons ──────────────────────────────── */
.stButton > button {
    background: linear-gradient(135deg, #1f6feb 0%, #388bfd 100%) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.45rem 1.1rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(56,139,253,0.35) !important;
}

/* Danger button variant */
.danger-btn > button {
    background: linear-gradient(135deg, #b91c1c 0%, #ef4444 100%) !important;
    box-shadow: 0 2px 8px rgba(239,68,68,0.2) !important;
}
.danger-btn > button:hover {
    box-shadow: 0 4px 14px rgba(239,68,68,0.4) !important;
}

/* ── Text inputs ──────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background: var(--bg-card2) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* ── Expanders ────────────────────────────── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
}

/* ── Divider ──────────────────────────────── */
hr { border-color: var(--border) !important; }

/* ── Badges / pills ───────────────────────── */
.badge {
    display: inline-block;
    padding: 0.2em 0.65em;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-green  { background: rgba(63,185,80,0.15);  color: #3fb950; border: 1px solid rgba(63,185,80,0.3); }
.badge-red    { background: rgba(248,81,73,0.15);  color: #f85149; border: 1px solid rgba(248,81,73,0.3); }
.badge-blue   { background: rgba(88,166,255,0.15); color: #58a6ff; border: 1px solid rgba(88,166,255,0.3); }
.badge-orange { background: rgba(255,166,87,0.15); color: #ffa657; border: 1px solid rgba(255,166,87,0.3); }
.badge-purple { background: rgba(210,168,255,0.15);color: #d2a8ff; border: 1px solid rgba(210,168,255,0.3); }

/* ── Section header cards ─────────────────── */
.section-header {
    background: linear-gradient(135deg, var(--bg-card) 0%, var(--bg-card2) 100%);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.25rem;
}
.section-header h2 { margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--accent); }
.section-header p  { margin: 0.25rem 0 0; font-size: 0.82rem; color: var(--text-muted); }

/* ── Status dot ───────────────────────────── */
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; }
.dot-green  { background: #3fb950; box-shadow: 0 0 6px #3fb950; }
.dot-red    { background: #f85149; box-shadow: 0 0 6px #f85149; }
.dot-yellow { background: #d29922; box-shadow: 0 0 6px #d29922; }

/* ── Debug panels (monospace) ─────────────── */
.debug-panel {
    background: #010409;
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: #79c0ff;
    overflow-x: auto;
    white-space: pre-wrap;
}

/* ── Chat bubbles ─────────────────────────── */
[data-testid="stChatMessage"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem !important;
}

/* ── File uploader ────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    background: var(--bg-card2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 10px !important;
}

/* ── Workspace badge ──────────────────────── */
.workspace-pill {
    background: linear-gradient(135deg, rgba(88,166,255,0.12) 0%, rgba(210,168,255,0.12) 100%);
    border: 1px solid rgba(88,166,255,0.3);
    border-radius: 20px;
    padding: 0.4rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: var(--accent);
    font-weight: 600;
    display: inline-block;
    margin-top: 0.25rem;
}

/* ── Dataframe ────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    overflow: hidden !important;
}

/* ── Tabs ─────────────────────────────────── */
[data-testid="stTabs"] [role="tab"] {
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    color: var(--text-muted) !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom-color: var(--accent) !important;
}

/* ── Checkbox ─────────────────────────────── */
[data-testid="stCheckbox"] label { color: var(--text-primary) !important; }

/* ── Spinner ──────────────────────────────── */
[data-testid="stSpinner"] { color: var(--accent) !important; }

/* ── Tooltips / captions ──────────────────── */
.stCaption { color: var(--text-muted) !important; font-size: 0.76rem !important; }

/* ── Table rows ───────────────────────────── */
.stTable tbody tr:hover { background: rgba(88,166,255,0.06) !important; }

/* ── Sidebar nav items ────────────────────── */
.nav-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.55rem 0.85rem;
    border-radius: 8px;
    cursor: pointer;
    font-size: 0.88rem;
    font-weight: 500;
    color: var(--text-muted);
    margin-bottom: 0.15rem;
    border: none;
    background: transparent;
    width: 100%;
    text-align: left;
    transition: all 0.18s ease;
}
.nav-item:hover, .nav-item.active {
    background: rgba(88,166,255,0.12);
    color: var(--accent);
}

/* ── Success/error overrides ──────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  CONSTANTS & SESSION STATE
# ─────────────────────────────────────────────
BASE_URL = os.environ.get("BASE_FASTAPI_URL", "http://127.0.0.1:8000")

PAGES = [
    ("💬", "Chat"),
    ("📤", "Uploads"),
    ("🧠", "Knowledge Base"),
    ("🌐", "Resources"),
    ("📊", "Database Stats"),
    ("🔧", "Workspace Tools"),
    ("❤️", "System Health"),
]

# Initialise session state keys
_defaults: Dict[str, Any] = {
    "page": "Chat",
    "workspace_id": "default",
    "chat_history": [],
    "api_key": "",
    "last_request": None,
    "last_response": None,
    "last_status": None,
    "last_latency": None,
    "file_to_delete": None,
    "kb_to_delete": None,
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────
#  CORE API HELPER
# ─────────────────────────────────────────────
def api(
    endpoint: str,
    method: str = "GET",
    data: Optional[Dict] = None,
    params: Optional[Dict] = None,
    files=None,
    stream: bool = False,
    timeout: int = 120,
    bearer: Optional[str] = None,
) -> Optional[requests.Response]:
    """
    Central HTTP helper.  Records last request/response into session state
    for the Developer Debug Panel.
    """
    url = f"{BASE_URL}/{endpoint}"
    headers: Dict[str, str] = {}
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"

    # Build debug snapshot (before sending)
    debug_req = {
        "method": method,
        "url": url,
        "params": params,
        "body": data if data else ("<multipart>" if files else None),
        "headers": headers,
    }
    st.session_state.last_request = debug_req

    t0 = time.time()
    try:
        if method == "GET":
            resp = requests.get(url, params=params, headers=headers, timeout=timeout, stream=stream)
        elif method == "POST":
            if files:
                resp = requests.post(url, files=files, params=params, headers=headers, timeout=timeout)
            else:
                headers["Content-Type"] = "application/json"
                resp = requests.post(url, json=data, params=params, headers=headers, timeout=timeout, stream=stream)
        elif method == "DELETE":
            resp = requests.delete(url, params=params, headers=headers, timeout=timeout)
        else:
            return None

        latency = round(time.time() - t0, 3)
        st.session_state.last_status = resp.status_code
        st.session_state.last_latency = latency
        try:
            st.session_state.last_response = resp.json()
        except Exception:
            st.session_state.last_response = resp.text[:2000]
        return resp

    except requests.exceptions.ConnectionError:
        st.session_state.last_status = "CONNECTION_ERROR"
        st.session_state.last_response = "Could not reach the backend. Is uvicorn running?"
        st.session_state.last_latency = None
        return None
    except requests.exceptions.Timeout:
        st.session_state.last_status = "TIMEOUT"
        st.session_state.last_response = f"Request timed out after {timeout}s"
        st.session_state.last_latency = None
        return None
    except Exception as exc:
        st.session_state.last_status = "EXCEPTION"
        st.session_state.last_response = str(exc)
        st.session_state.last_latency = None
        return None


# ─────────────────────────────────────────────
#  SMALL UI UTILITIES
# ─────────────────────────────────────────────
def badge(label: str, color: str = "blue") -> str:
    return f'<span class="badge badge-{color}">{label}</span>'


def status_dot(ok: bool) -> str:
    cls = "dot-green" if ok else "dot-red"
    return f'<span class="dot {cls}"></span>'


def section_header(icon: str, title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""<div class="section-header">
              <h2>{icon} {title}</h2>
              {'<p>' + subtitle + '</p>' if subtitle else ''}
            </div>""",
        unsafe_allow_html=True,
    )


def debug_panel() -> None:
    """Collapsible developer debug panel shown at bottom of every page."""
    with st.expander("🔬 Developer Debug Panel", expanded=False):
        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("**Last Request**")
            if st.session_state.last_request:
                st.markdown(
                    f'<div class="debug-panel">{json.dumps(st.session_state.last_request, indent=2, default=str)}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("No request recorded yet.")

        with col_b:
            st.markdown("**Last Response**")
            status_val = st.session_state.last_status
            latency_val = st.session_state.last_latency

            meta_parts = []
            if status_val is not None:
                color = "green" if str(status_val) == "200" else "red"
                meta_parts.append(
                    f'<span class="badge badge-{color}">HTTP {status_val}</span>'
                )
            if latency_val is not None:
                meta_parts.append(
                    f'<span class="badge badge-blue">⏱ {latency_val}s</span>'
                )
            if meta_parts:
                st.markdown(" ".join(meta_parts), unsafe_allow_html=True)

            if st.session_state.last_response is not None:
                payload = st.session_state.last_response
                if isinstance(payload, (dict, list)):
                    display = json.dumps(payload, indent=2, default=str)
                else:
                    display = str(payload)
                st.markdown(
                    f'<div class="debug-panel">{display}</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.caption("No response recorded yet.")


# ─────────────────────────────────────────────
#  SIDEBAR NAVIGATION
# ─────────────────────────────────────────────
with st.sidebar:
    # Logo / title
    st.markdown(
        """<div style="padding: 0.5rem 0 1rem; text-align: center;">
            <div style="font-size: 2.2rem;">🛸</div>
            <div style="font-size: 1rem; font-weight: 700; color: #58a6ff; letter-spacing: 0.06em;">DEV CONSOLE</div>
            <div style="font-size: 0.7rem; color: #8b949e; margin-top: 0.1rem;">AI Avatar · Backend Testing</div>
           </div>""",
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Workspace selector ───────────────────
    st.markdown("**🗂 Workspace**")
    ws_input = st.text_input(
        "workspace_id",
        value=st.session_state.workspace_id,
        placeholder="e.g. teacher_abc123",
        label_visibility="collapsed",
        key="ws_input_sidebar",
    )
    if ws_input.strip():
        st.session_state.workspace_id = ws_input.strip()

    st.markdown(
        f'<div class="workspace-pill">📌 {st.session_state.workspace_id}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── API Key (for protected endpoints) ────
    st.markdown("**🔑 API Key** *(for protected ops)*")
    api_key_input = st.text_input(
        "api_key",
        value=st.session_state.api_key,
        type="password",
        placeholder="FASTAPI_API_KEY",
        label_visibility="collapsed",
        key="api_key_sidebar",
    )
    st.session_state.api_key = api_key_input

    st.divider()

    # ── Navigation ───────────────────────────
    st.markdown("**Navigation**", unsafe_allow_html=True)
    for icon, name in PAGES:
        is_active = st.session_state.page == name
        btn_label = f"{icon}  {name}"
        style = (
            "background:rgba(88,166,255,0.15);color:#58a6ff;border-radius:8px;"
            if is_active
            else ""
        )
        if st.button(btn_label, key=f"nav_{name}", use_container_width=True):
            st.session_state.page = name
            st.rerun()

    st.divider()

    # ── Quick health indicator ───────────────
    st.markdown("**Backend Status**")
    try:
        ping = requests.get(f"{BASE_URL}/", timeout=3)
        online = ping.status_code == 200
    except Exception:
        online = False

    dot = status_dot(online)
    label = "Online" if online else "Offline"
    color = "green" if online else "red"
    st.markdown(
        f'{dot} <span class="badge badge-{color}">{label}</span> '
        f'<span style="font-size:0.72rem;color:#8b949e;">{BASE_URL}</span>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="margin-top:2rem;font-size:0.68rem;color:#30363d;text-align:center;">'
        "AI Avatar Dev Console · v2.0</div>",
        unsafe_allow_html=True,
    )

# ─────────────────────────────────────────────
#  PAGE ROUTER
# ─────────────────────────────────────────────
page = st.session_state.page
workspace = st.session_state.workspace_id


# ══════════════════════════════════════════════
#  PAGE 1: CHAT
# ══════════════════════════════════════════════
if page == "Chat":
    section_header("💬", "Chat Testing Panel",
                   "Stream a query through the full RAG pipeline and inspect retrieved context.")

    # ── Render history ───────────────────────
    for msg in st.session_state.chat_history:
        role = msg.get("role", "user")
        avatar = "🧑‍💻" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg.get("text", ""))
            if role == "assistant":
                meta_col1, meta_col2, meta_col3 = st.columns(3)
                with meta_col1:
                    src = msg.get("source", "unknown")
                    clr = "green" if src == "knowledge_base" else ("blue" if src == "rag" else "purple")
                    st.markdown(badge(f"source: {src}", clr), unsafe_allow_html=True)
                with meta_col2:
                    elapsed = msg.get("time", 0)
                    st.markdown(badge(f"⏱ {elapsed:.2f}s", "orange"), unsafe_allow_html=True)
                if msg.get("context"):
                    with st.expander("📎 Retrieved Context", expanded=False):
                        st.markdown(
                            f'<div class="debug-panel">{msg["context"]}</div>',
                            unsafe_allow_html=True,
                        )

    # ── Input ────────────────────────────────
    prompt = st.chat_input("Type your query…", key="chat_input_main")
    if prompt:
        st.session_state.chat_history.append({"role": "user", "text": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        payload = {"question": prompt, "workspace_id": workspace}
        # Record request manually (stream=True bypasses our helper's response capture)
        st.session_state.last_request = {
            "method": "POST",
            "url": f"{BASE_URL}/query",
            "body": payload,
        }

        t0 = time.time()
        try:
            resp = requests.post(
                f"{BASE_URL}/query",
                json=payload,
                headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
                stream=True,
                timeout=120,
            )
            source = resp.headers.get("X-Response-Source", "rag")
            st.session_state.last_status = resp.status_code

            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                raw_buffer: List[str] = []
                final_text = ""
                event_type = ""

                for line in resp.iter_lines(decode_unicode=True):
                    if line.startswith("event:"):
                        event_type = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        try:
                            data_json = json.loads(line[len("data:"):].strip())
                            chunk = data_json.get("text", "")
                            if event_type == "token":
                                raw_buffer.append(chunk)
                                placeholder.markdown("".join(raw_buffer) + "▌")
                            elif event_type == "final_response":
                                final_text = chunk
                                placeholder.markdown(final_text)
                        except json.JSONDecodeError:
                            continue

                if not final_text:
                    final_text = "".join(raw_buffer)
                    placeholder.markdown(final_text)

            elapsed = round(time.time() - t0, 2)
            st.session_state.last_latency = elapsed
            st.session_state.last_response = {"text": final_text[:500], "source": source}
            token_count = len(final_text.split())

            # ── Diagnostics row ──────────────
            diag_col1, diag_col2, diag_col3 = st.columns(3)
            with diag_col1:
                st.metric("Latency", f"{elapsed}s")
            with diag_col2:
                st.metric("Approx Tokens", token_count)
            with diag_col3:
                st.metric("HTTP Status", resp.status_code)

            st.session_state.chat_history.append({
                "role": "assistant",
                "text": final_text,
                "source": source,
                "time": elapsed,
            })
            st.rerun()

        except requests.exceptions.ConnectionError:
            st.error("❌ Backend unreachable. Make sure uvicorn is running.")
            st.session_state.last_status = "CONNECTION_ERROR"
        except Exception as exc:
            st.error(f"❌ Error: {exc}")
            st.session_state.last_status = "EXCEPTION"

    # ── Actions ──────────────────────────────
    if st.session_state.chat_history:
        if st.button("🗑 Clear Chat History", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    debug_panel()


# ══════════════════════════════════════════════
#  PAGE 2: UPLOADS
# ══════════════════════════════════════════════
elif page == "Uploads":
    section_header("📤", "Upload Management",
                   "Upload PDF / TXT / DOCX files and manage indexed documents.")

    tab_up, tab_list = st.tabs(["⬆️ Upload Files", "📋 Document List"])

    # ── Upload tab ───────────────────────────
    with tab_up:
        st.markdown("#### Select Documents")
        uploaded_files = st.file_uploader(
            "Drag & drop or click to browse",
            type=["pdf", "txt", "docx"],
            accept_multiple_files=True,
            key="upload_files_input",
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} file(s) selected:**")
            for uf in uploaded_files:
                size_kb = round(len(uf.getvalue()) / 1024, 1)
                ext = uf.name.rsplit(".", 1)[-1].upper()
                clr = "blue" if ext == "PDF" else ("green" if ext == "TXT" else "purple")
                st.markdown(
                    f"- {uf.name} &nbsp; {badge(ext, clr)} &nbsp; "
                    f'<span style="color:#8b949e;font-size:0.8rem;">{size_kb} KB</span>',
                    unsafe_allow_html=True,
                )

        if st.button("🚀 Process & Index Documents", key="process_docs_btn"):
            if not uploaded_files:
                st.warning("Please select at least one file.")
            else:
                files_payload = [
                    ("files", (f.name, f.getvalue(), f.type or "application/octet-stream"))
                    for f in uploaded_files
                ]
                # workspace_id must be sent as Form field
                data_payload = [("workspace_id", workspace)]

                with st.spinner("Uploading and indexing… this may take a minute."):
                    t0 = time.time()
                    try:
                        resp = requests.post(
                            f"{BASE_URL}/upload",
                            files=files_payload,
                            data=data_payload,
                            timeout=180,
                        )
                        elapsed = round(time.time() - t0, 2)
                        st.session_state.last_status = resp.status_code
                        st.session_state.last_latency = elapsed
                        st.session_state.last_request = {
                            "method": "POST", "url": f"{BASE_URL}/upload",
                            "body": f"<multipart> workspace_id={workspace}, {len(uploaded_files)} file(s)",
                        }
                        try:
                            body = resp.json()
                            st.session_state.last_response = body
                        except Exception:
                            body = {}
                            st.session_state.last_response = resp.text

                        if resp.status_code == 200:
                            msg_txt = body.get("message", "Upload successful!")
                            qa_idx = body.get("qa_indexed", 0)
                            st.success(f"✅ {msg_txt}")
                            m1, m2, m3 = st.columns(3)
                            m1.metric("HTTP Status", resp.status_code)
                            m2.metric("QA Pairs Indexed", qa_idx)
                            m3.metric("Upload Time", f"{elapsed}s")
                        else:
                            st.error(f"❌ Upload failed (HTTP {resp.status_code}): {resp.text[:300]}")

                    except requests.exceptions.ConnectionError:
                        st.error("❌ Backend unreachable.")
                    except Exception as exc:
                        st.error(f"❌ Exception: {exc}")

    # ── Document list tab ────────────────────
    with tab_list:
        st.markdown("#### Indexed Documents")
        if st.button("🔄 Refresh List", key="refresh_docs_btn"):
            st.rerun()

        stats_resp = api("db_stats", params={"workspace_id": workspace})
        if stats_resp and stats_resp.status_code == 200:
            info = stats_resp.json()
            raw_files: List[str] = info.get("raw_files", [])

            if not raw_files:
                st.info("No documents uploaded yet for this workspace.")
            else:
                st.markdown(f"**{len(raw_files)} document(s)** in workspace `{workspace}`")
                for filename in raw_files:
                    col_name, col_del = st.columns([5, 1])
                    ext = filename.rsplit(".", 1)[-1].upper() if "." in filename else "FILE"
                    clr = "blue" if ext == "PDF" else ("green" if ext == "TXT" else "purple")
                    with col_name:
                        st.markdown(
                            f"📄 {filename} &nbsp; {badge(ext, clr)}",
                            unsafe_allow_html=True,
                        )
                    with col_del:
                        if st.session_state.file_to_delete == filename:
                            pass  # handled below
                        else:
                            if st.button("Delete", key=f"del_doc_{filename}"):
                                st.session_state.file_to_delete = filename
                                st.rerun()

                    if st.session_state.file_to_delete == filename:
                        st.warning(
                            f"⚠️ Delete **{filename}** and all its indexed embeddings? This cannot be undone."
                        )
                        c1, c2 = st.columns(2)
                        if c1.button("✅ Yes, Delete", key=f"confirm_del_{filename}", type="primary"):
                            del_resp = api(
                                "raw_docs",
                                method="DELETE",
                                params={"filename": filename, "workspace_id": workspace},
                            )
                            if del_resp and del_resp.status_code == 200:
                                st.success(f"Deleted {filename}")
                            else:
                                st.error("Deletion failed.")
                            st.session_state.file_to_delete = None
                            st.rerun()
                        if c2.button("❌ Cancel", key=f"cancel_del_{filename}"):
                            st.session_state.file_to_delete = None
                            st.rerun()
        else:
            st.error("❌ Could not fetch document list from backend.")

    debug_panel()


# ══════════════════════════════════════════════
#  PAGE 3: KNOWLEDGE BASE
# ══════════════════════════════════════════════
elif page == "Knowledge Base":
    section_header("🧠", "Knowledge Base Manager",
                   "Add, view and delete Q&A pairs stored in the knowledge base.")

    # ── Add new entry ─────────────────────────
    with st.expander("➕ Add New Q&A Entry", expanded=True):
        kb_q = st.text_area("Question", placeholder="e.g. What is the admission process?", key="kb_q_input")
        kb_a = st.text_area("Answer", placeholder="The admission process involves…", key="kb_a_input")
        kb_tags = st.text_input("Tags (comma separated, optional)", placeholder="admissions, fees", key="kb_tags_input")

        if st.button("💾 Add to Knowledge Base", key="add_kb_btn"):
            if not kb_q.strip() or not kb_a.strip():
                st.warning("Both Question and Answer are required.")
            else:
                add_resp = api(
                    "add_knowledge",
                    method="POST",
                    data={
                        "workspace_id": workspace,
                        "question": kb_q.strip(),
                        "answer": kb_a.strip(),
                        "tags": kb_tags.strip(),
                    },
                )
                if add_resp and add_resp.status_code == 200:
                    st.success("✅ Knowledge entry added successfully!")
                    st.rerun()
                else:
                    err = add_resp.text if add_resp else "No response"
                    st.error(f"❌ Failed to add entry: {err}")

    st.divider()

    # ── List entries ──────────────────────────
    col_hdr, col_refresh = st.columns([4, 1])
    with col_hdr:
        st.markdown("#### Existing Q&A Entries")
    with col_refresh:
        if st.button("🔄 Refresh", key="refresh_kb_btn"):
            st.rerun()

    kb_resp = api("knowledge", params={"workspace_id": workspace})
    if kb_resp and kb_resp.status_code == 200:
        items: List[Dict] = kb_resp.json()

        if not items:
            st.info("No knowledge base entries found for this workspace.")
        else:
            # Summary metrics
            m1, m2 = st.columns(2)
            m1.metric("Total Entries", len(items))
            all_tags = [t for item in items for t in (item.get("tags") or "").split(",") if t.strip()]
            m2.metric("Unique Tags", len(set(all_tags)))

            st.markdown("")
            for item in items:
                qa_id = item.get("id", "?")
                question_text = item.get("question", "No Question")
                answer_text = item.get("answer", "No Answer")
                tags_text = item.get("tags", "")
                created_at = item.get("created_at", "")

                with st.expander(f"#{qa_id} · {question_text[:80]}", expanded=False):
                    st.markdown(f"**Answer:** {answer_text}")
                    meta_row = []
                    if tags_text:
                        for t in tags_text.split(","):
                            if t.strip():
                                meta_row.append(badge(t.strip(), "purple"))
                    if created_at:
                        meta_row.append(f'<span style="color:#8b949e;font-size:0.75rem;">🕐 {created_at}</span>')
                    if meta_row:
                        st.markdown("&nbsp;".join(meta_row), unsafe_allow_html=True)

                    # Delete with confirmation
                    if st.session_state.kb_to_delete == qa_id:
                        st.warning("⚠️ Delete this entry permanently?")
                        dc1, dc2 = st.columns(2)
                        if dc1.button("✅ Confirm Delete", key=f"confirm_kb_{qa_id}", type="primary"):
                            del_resp = api(
                                f"delete_knowledge/{qa_id}",
                                method="DELETE",
                                params={"workspace_id": workspace},
                                bearer=st.session_state.api_key or None,
                            )
                            if del_resp and del_resp.status_code == 200:
                                st.success("Deleted.")
                            elif del_resp and del_resp.status_code == 401:
                                st.error("❌ Unauthorized. Provide your FASTAPI_API_KEY in the sidebar.")
                            else:
                                st.error(f"❌ Delete failed: {del_resp.text if del_resp else 'No response'}")
                            st.session_state.kb_to_delete = None
                            st.rerun()
                        if dc2.button("❌ Cancel", key=f"cancel_kb_{qa_id}"):
                            st.session_state.kb_to_delete = None
                            st.rerun()
                    else:
                        if st.button("🗑 Delete Entry", key=f"del_kb_{qa_id}"):
                            st.session_state.kb_to_delete = qa_id
                            st.rerun()
    else:
        st.error("❌ Could not fetch knowledge base.")

    debug_panel()


# ══════════════════════════════════════════════
#  PAGE 4: RESOURCES / WEBSITE INGESTION
# ══════════════════════════════════════════════
elif page == "Resources":
    section_header("🌐", "Website / Resource Ingestion",
                   "Scrape and index external URLs into the vector store.")

    with st.container():
        st.markdown("#### Ingest a Website")
        web_url = st.text_input(
            "URL",
            placeholder="https://example.com/documentation",
            key="web_url_input",
        )
        st.caption("Supported: plain HTML pages, Wikipedia articles, documentation sites.")

        if st.button("🕸 Scrape & Index Website", key="ingest_website_btn"):
            if not web_url.strip():
                st.warning("Please enter a valid URL.")
            else:
                with st.spinner("Scraping and embedding… this may take 30–90 seconds."):
                    ingest_resp = api(
                        "ingest/website",
                        method="POST",
                        data={"url": web_url.strip(), "workspace_id": workspace},
                    )

                if ingest_resp and ingest_resp.status_code == 200:
                    result = ingest_resp.json()
                    status = result.get("status", "unknown")
                    if status == "success":
                        st.success("✅ Website ingested successfully!")
                        chunks_indexed = result.get("chunks_indexed", result.get("indexed", "N/A"))
                        pages_crawled = result.get("pages_crawled", result.get("pages", "N/A"))
                        m1, m2 = st.columns(2)
                        m1.metric("Chunks Indexed", chunks_indexed)
                        m2.metric("Pages Crawled", pages_crawled)
                        with st.expander("📋 Full Ingestion Result"):
                            st.json(result)
                    else:
                        st.error(f"❌ Ingestion failed: {result.get('message', result.get('error', 'Unknown error'))}")
                        st.json(result)
                elif ingest_resp:
                    st.error(f"❌ HTTP {ingest_resp.status_code}: {ingest_resp.text[:400]}")
                else:
                    st.error("❌ Backend unreachable.")

    debug_panel()


# ══════════════════════════════════════════════
#  PAGE 5: DATABASE STATS
# ══════════════════════════════════════════════
elif page == "Database Stats":
    section_header("📊", "Database Stats Dashboard",
                   f"Live statistics for workspace: {workspace}")

    col_refresh, _ = st.columns([1, 5])
    with col_refresh:
        if st.button("🔄 Refresh Stats", key="refresh_stats_btn"):
            st.rerun()

    stats_resp = api("db_stats", params={"workspace_id": workspace})
    if stats_resp and stats_resp.status_code == 200:
        info = stats_resp.json()
        vdb: Dict = info.get("vector_db", {})
        qa_count: int = info.get("qa_pairs", 0)
        raw_count: int = info.get("raw_count", 0)
        raw_files: List[str] = info.get("raw_files", [])

        # ── Top-level metrics ─────────────────
        st.markdown("### 📈 Key Metrics")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📄 Unique Documents", vdb.get("total_documents", 0))
        c2.metric("🧩 Indexed Chunks", vdb.get("indexed_chunks", 0))
        c3.metric("🧠 KB Q&A Pairs", qa_count)
        c4.metric("📁 Raw Files", raw_count)

        st.markdown("### 🗄 Vector DB Details")
        vdb_col1, vdb_col2 = st.columns(2)
        with vdb_col1:
            st.markdown(
                f"""<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1.2rem;">
                    <div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;">Collections</div>
                    <div style="font-size:2rem;font-weight:700;color:#58a6ff;">{vdb.get('collections', 'N/A')}</div>
                    </div>""",
                unsafe_allow_html=True,
            )
        with vdb_col2:
            model_name = vdb.get("model", "N/A")
            st.markdown(
                f"""<div style="background:var(--bg-card);border:1px solid var(--border);border-radius:12px;padding:1.2rem;">
                    <div style="color:#8b949e;font-size:0.75rem;text-transform:uppercase;letter-spacing:.05em;">Embedding Model</div>
                    <div style="font-size:1rem;font-weight:600;color:#d2a8ff;margin-top:.4rem;font-family:'JetBrains Mono',monospace;">{model_name}</div>
                    </div>""",
                unsafe_allow_html=True,
            )

        # ── Raw files table ───────────────────
        if raw_files:
            st.markdown("### 📁 Raw File Inventory")
            table_data = []
            for fn in raw_files:
                ext = fn.rsplit(".", 1)[-1].upper() if "." in fn else "UNKNOWN"
                table_data.append({"Filename": fn, "Type": ext})
            import pandas as pd
            st.dataframe(pd.DataFrame(table_data), use_container_width=True, hide_index=True)
        else:
            st.info("No raw files found for this workspace.")

        # ── Raw JSON ─────────────────────────
        with st.expander("📋 Raw API Response"):
            st.json(info)

    else:
        st.error("❌ Could not retrieve database stats. Ensure the backend is running and workspace_id is correct.")

    debug_panel()


# ══════════════════════════════════════════════
#  PAGE 6: WORKSPACE TOOLS (reset + eval)
# ══════════════════════════════════════════════
elif page == "Workspace Tools":
    section_header("🔧", "Workspace Tools",
                   "Advanced management operations and RAG evaluation for the selected workspace.")

    # ── Evaluation ────────────────────────────
    st.markdown("### 🧪 RAG vs Baseline Evaluation")

    eval_tab, reset_tab = st.tabs(["📊 Run Evaluation", "⚠️ Danger Zone"])

    with eval_tab:
        DATASET_PATH = "evaluation/dataset.json"
        st.caption(f"Dataset path: `{DATASET_PATH}`")

        eval_question = st.text_input(
            "Quick Eval – Single Question",
            placeholder="Type a question to test both RAG and baseline…",
            key="eval_q_input",
        )

        col_rag, col_base = st.columns(2)
        with col_rag:
            if st.button("▶ Test RAG (non-stream)", key="test_rag_btn"):
                if eval_question.strip():
                    with st.spinner("Querying RAG pipeline…"):
                        r = api(
                            "query_eval",
                            method="POST",
                            data={"question": eval_question.strip(), "workspace_id": workspace},
                        )
                    if r and r.status_code == 200:
                        body = r.json()
                        st.success("**RAG Answer:**")
                        st.markdown(body.get("answer", "No answer"))
                        m1, m2 = st.columns(2)
                        m1.metric("Source", body.get("source", "N/A"))
                        m2.metric("Context Used", body.get("context_used", "N/A"))
                    else:
                        st.error(f"❌ HTTP {r.status_code if r else 'N/A'}: {r.text[:300] if r else 'No response'}")
                else:
                    st.warning("Enter a question first.")

        with col_base:
            if st.button("▶ Test Baseline (Qwen only)", key="test_qwen_btn"):
                if eval_question.strip():
                    with st.spinner("Querying baseline Qwen…"):
                        r = api(
                            "qwen",
                            method="POST",
                            data={"question": eval_question.strip()},
                        )
                    if r and r.status_code == 200:
                        body = r.json()
                        st.success("**Baseline Answer:**")
                        st.markdown(body.get("answer", "No answer"))
                    else:
                        st.error(f"❌ HTTP {r.status_code if r else 'N/A'}")
                else:
                    st.warning("Enter a question first.")

        st.divider()
        st.markdown("#### 🚀 Full Dataset Evaluation")

        if st.button("▶ Run Full Evaluation Suite", key="run_full_eval_btn"):
            if not os.path.exists(DATASET_PATH):
                st.error(f"Dataset not found at `{DATASET_PATH}`. Create it first.")
            else:
                import pandas as pd
                with open(DATASET_PATH, "r") as f:
                    dataset = json.load(f)

                results = []
                rag_score = 0
                qwen_score = 0

                progress_bar = st.progress(0, text="Running evaluation…")

                for i, item in enumerate(dataset):
                    q = item["question"]
                    gt = item["ground_truth"]

                    rag_r = api("query_eval", method="POST", data={"question": q, "workspace_id": workspace})
                    rag_ans = rag_r.json().get("answer", "ERROR") if rag_r and rag_r.status_code == 200 else "ERROR"

                    qwen_r = api("qwen", method="POST", data={"question": q})
                    qwen_ans = qwen_r.json().get("answer", "ERROR") if qwen_r and qwen_r.status_code == 200 else "ERROR"

                    rag_ok = gt.lower() in rag_ans.lower()
                    qwen_ok = gt.lower() in qwen_ans.lower()
                    rag_score += rag_ok
                    qwen_score += qwen_ok

                    results.append({
                        "Question": q,
                        "Ground Truth": gt,
                        "RAG Answer": rag_ans[:120],
                        "Qwen Answer": qwen_ans[:120],
                        "RAG ✔": "✅" if rag_ok else "❌",
                        "Qwen ✔": "✅" if qwen_ok else "❌",
                    })
                    progress_bar.progress((i + 1) / len(dataset), text=f"Evaluated {i+1}/{len(dataset)}")

                total = len(dataset)
                progress_bar.empty()
                st.success("✅ Evaluation complete!")

                em1, em2, em3 = st.columns(3)
                em1.metric("RAG Score", f"{rag_score}/{total}", delta=f"{round(rag_score/total*100,1)}%")
                em2.metric("Qwen Score", f"{qwen_score}/{total}", delta=f"{round(qwen_score/total*100,1)}%")
                em3.metric("Total Questions", total)

                st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)

    # ── Danger Zone ───────────────────────────
    with reset_tab:
        st.markdown(
            """<div style="background:rgba(248,81,73,0.08);border:1px solid rgba(248,81,73,0.3);
                          border-radius:12px;padding:1.25rem;margin-bottom:1rem;">
                <h3 style="color:#f85149;margin:0 0 .5rem;">⚠️ Danger Zone</h3>
                <p style="color:#8b949e;margin:0;font-size:.85rem;">
                  The actions below are <strong style="color:#f85149;">irreversible</strong>.
                  All vector embeddings, raw files and Q&amp;A pairs for the workspace will be permanently deleted.
                </p>
               </div>""",
            unsafe_allow_html=True,
        )

        st.markdown(f"**Target workspace:** `{workspace}`")

        confirm_check = st.checkbox(
            "I understand this action is irreversible and I want to reset this workspace.",
            key="reset_confirm_check",
        )

        if st.button("💣 Reset Workspace Database", key="reset_db_btn", type="primary",
                     disabled=not confirm_check):
            with st.spinner("Resetting workspace…"):
                reset_resp = api(
                    "reset_db",
                    method="POST",
                    params={"workspace_id": workspace},
                )
            if reset_resp and reset_resp.status_code == 200:
                body = reset_resp.json()
                st.success(f"✅ {body.get('message', 'Workspace reset successfully.')}")
                deleted = body.get("deleted_files", [])
                if deleted:
                    st.info(f"Deleted files: {', '.join(deleted)}")
            else:
                msg = reset_resp.text if reset_resp else "No response"
                st.error(f"❌ Reset failed: {msg}")

    debug_panel()


# ══════════════════════════════════════════════
#  PAGE 7: SYSTEM HEALTH
# ══════════════════════════════════════════════
elif page == "System Health":
    section_header("❤️", "System Health Panel",
                   "Live endpoint status checks and environment diagnostics.")

    # ── Refresh ───────────────────────────────
    col_r, _ = st.columns([1, 5])
    with col_r:
        if st.button("🔄 Re-run Checks", key="health_refresh_btn"):
            st.rerun()

    st.markdown("### 🔌 Endpoint Status Checks")

    CHECKS = [
        ("Root / Ping",      "GET",  "/",                       None,                              None),
        ("DB Stats",         "GET",  "/db_stats",               {"workspace_id": workspace},        None),
        ("Knowledge List",   "GET",  "/knowledge",              {"workspace_id": workspace},        None),
        ("Raw Docs List",    "GET",  "/raw_docs",               {"workspace_id": workspace},        None),
    ]

    results_table = []
    for name, method, path, params, body in CHECKS:
        t0 = time.time()
        try:
            if method == "GET":
                r = requests.get(f"{BASE_URL}{path}", params=params, timeout=5)
            else:
                r = requests.post(f"{BASE_URL}{path}", json=body, params=params, timeout=5)
            lat = round(time.time() - t0, 3)
            ok = r.status_code == 200
            results_table.append({
                "Endpoint": name,
                "Path": path,
                "Status": r.status_code,
                "OK": "✅" if ok else "❌",
                "Latency (s)": lat,
            })
        except Exception as exc:
            lat = round(time.time() - t0, 3)
            results_table.append({
                "Endpoint": name,
                "Path": path,
                "Status": "ERR",
                "OK": "❌",
                "Latency (s)": lat,
            })

    # Display as styled cards
    for row in results_table:
        ok = row["OK"] == "✅"
        dot = status_dot(ok)
        status_badge = badge(str(row["Status"]), "green" if ok else "red")
        lat_badge = badge(f"{row['Latency (s)']}s", "blue")
        st.markdown(
            f"""<div style="display:flex;align-items:center;gap:1rem;
                           background:var(--bg-card);border:1px solid var(--border);
                           border-radius:10px;padding:.75rem 1.25rem;margin-bottom:.5rem;">
                  {dot}
                  <span style="font-weight:600;flex:1;">{row['Endpoint']}</span>
                  <code style="color:#8b949e;font-size:.78rem;flex:1;">{row['Path']}</code>
                  {status_badge} &nbsp; {lat_badge}
                </div>""",
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Environment diagnostics ───────────────
    st.markdown("### 🌍 Environment Diagnostics")
    env_col1, env_col2 = st.columns(2)

    with env_col1:
        api_key_set = bool(st.session_state.api_key)
        hf_key_env = bool(os.environ.get("HF_API_KEY"))

        def env_row(label, ok, hint=""):
            d = status_dot(ok)
            b = badge("SET" if ok else "MISSING", "green" if ok else "red")
            hint_html = (
                '<span style="color:#8b949e;font-size:.72rem;">' + hint + "</span>"
                if hint else ""
            )
            return (
                f'<div style="display:flex;align-items:center;gap:.6rem;margin-bottom:.4rem;">'
                f'{d}<span style="flex:1;">{label}</span>{b}{hint_html}'
                f'</div>'
            )

        st.markdown("**Key Configuration**", unsafe_allow_html=True)
        st.markdown(env_row("FASTAPI_API_KEY (sidebar)", api_key_set, "for DELETE /delete_knowledge"), unsafe_allow_html=True)
        st.markdown(env_row("HF_API_KEY (env)", hf_key_env, "for LLM inference"), unsafe_allow_html=True)

    with env_col2:
        st.markdown("**Backend Connection**")
        backend_ok = any(r["OK"] == "✅" for r in results_table)
        st.markdown(
            f'<div style="background:var(--bg-card);border:1px solid var(--border);'
            f'border-radius:10px;padding:1rem;">'
            f'{status_dot(backend_ok)}'
            f'<span style="font-weight:600;">{BASE_URL}</span><br/>'
            f'<span style="color:#8b949e;font-size:.78rem;margin-top:.3rem;display:block;">'
            f'{"All checks passing" if backend_ok else "Backend appears unreachable"}'
            f'</span></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    # ── Full response dump ────────────────────
    with st.expander("📋 Endpoint Results (raw table)"):
        import pandas as pd
        st.dataframe(pd.DataFrame(results_table), use_container_width=True, hide_index=True)

    debug_panel()
