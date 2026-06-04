# streamlit_app.py  –  Developer Operations Console & Architecture Explorer
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
#  CUSTOM CSS  – Professional dual-mode theme
#  Light mode is first-class; dark mode auto-
#  detected via prefers-color-scheme.
# ─────────────────────────────────────────────
st.markdown("""
<style>
/* ── Google Fonts ─────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

/* ══════════════════════════════════════════════
   BASE VARIABLES (Fallbacks to Streamlit theme)
   ══════════════════════════════════════════════ */
:root {
    --bg-base:      var(--background-color, #F8FAFC);
    --bg-card:      var(--secondary-background-color, #FFFFFF);
    --bg-card2:     var(--secondary-background-color, #F1F5F9);
    --border:       var(--secondary-background-color, #E2E8F0);
    --border-hover: rgba(128, 128, 128, 0.3);
    --accent:       var(--primary-color, #2563EB);
    --accent-soft:  rgba(128, 128, 128, 0.1);
    --accent2:      #16A34A;
    --accent3:      #D97706;
    --accent4:      #7C3AED;
    --accent5:      #EA580C;
    --text-primary: var(--text-color, #0F172A);
    --text-secondary:var(--text-color, #334155);
    --text-muted:   rgba(128, 128, 128, 0.8);
    --danger:       #DC2626;
    --danger-soft:  rgba(220,38,38,0.06);
    --warning:      #D97706;
    --success:      #16A34A;
    --success-soft: rgba(22,163,74,0.06);
    --code-bg:      var(--secondary-background-color, #F1F5F9);
    --code-text:    var(--primary-color, #1E40AF);
    --shadow-sm:    0 1px 2px rgba(0,0,0,0.05);
    --shadow-md:    0 2px 8px rgba(0,0,0,0.1);
    --shadow-lg:    0 4px 16px rgba(0,0,0,0.15);
    --gradient-primary: linear-gradient(135deg, var(--primary-color, #2563EB) 0%, var(--primary-color, #3B82F6) 100%);
    --gradient-card: linear-gradient(135deg, var(--secondary-background-color, #FFFFFF) 0%, var(--background-color, #F8FAFC) 100%);
}

/* ══════════════════════════════════════════════
   LIGHT MODE
   ══════════════════════════════════════════════ */
@media (prefers-color-scheme: light) {
    :root {
        --bg-base:      #F8FAFC;
        --bg-card:      #FFFFFF;
        --bg-card2:     #F1F5F9;
        --border:       #E2E8F0;
        --border-hover: #CBD5E1;
        --accent:       #2563EB;
        --accent-soft:  rgba(37,99,235,0.08);
        --accent2:      #16A34A;
        --accent3:      #D97706;
        --accent4:      #7C3AED;
        --accent5:      #EA580C;
        --text-primary: #0F172A;
        --text-secondary:#334155;
        --text-muted:   #64748B;
        --danger:       #DC2626;
        --danger-soft:  rgba(220,38,38,0.06);
        --warning:      #D97706;
        --success:      #16A34A;
        --success-soft: rgba(22,163,74,0.06);
        --code-bg:      #F1F5F9;
        --code-text:    #1E40AF;
        --shadow-sm:    0 1px 2px rgba(0,0,0,0.04);
        --shadow-md:    0 2px 8px rgba(0,0,0,0.06);
        --shadow-lg:    0 4px 16px rgba(0,0,0,0.08);
        --gradient-primary: linear-gradient(135deg, #2563EB 0%, #3B82F6 100%);
        --gradient-card: linear-gradient(135deg, #FFFFFF 0%, #F8FAFC 100%);
    }
}

/* ══════════════════════════════════════════════
   DARK MODE
   ══════════════════════════════════════════════ */
@media (prefers-color-scheme: dark) {
    :root {
        --bg-base:      #0F172A;
        --bg-card:      #1E293B;
        --bg-card2:     #273548;
        --border:       #334155;
        --border-hover: #475569;
        --accent:       #3B82F6;
        --accent-soft:  rgba(59,130,246,0.12);
        --accent2:      #22C55E;
        --accent3:      #F59E0B;
        --accent4:      #A78BFA;
        --accent5:      #FB923C;
        --text-primary: #F1F5F9;
        --text-secondary:#CBD5E1;
        --text-muted:   #94A3B8;
        --danger:       #EF4444;
        --danger-soft:  rgba(239,68,68,0.10);
        --warning:      #F59E0B;
        --success:      #22C55E;
        --success-soft: rgba(34,197,94,0.10);
        --code-bg:      #0F172A;
        --code-text:    #7DD3FC;
        --shadow-sm:    0 1px 2px rgba(0,0,0,0.20);
        --shadow-md:    0 2px 8px rgba(0,0,0,0.30);
        --shadow-lg:    0 4px 16px rgba(0,0,0,0.40);
        --gradient-primary: linear-gradient(135deg, #1D4ED8 0%, #3B82F6 100%);
        --gradient-card: linear-gradient(135deg, #1E293B 0%, #273548 100%);
    }
}

/* ══════════════════════════════════════════════
   STREAMLIT THEME OVERRIDES (when user forces Light or Dark via Streamlit settings)
   ══════════════════════════════════════════════ */
[data-testid="stAppViewContainer"][data-theme="light"],
.stApp[data-theme="light"] {
    --bg-base:      #F8FAFC;
    --bg-card:      #FFFFFF;
    --bg-card2:     #F1F5F9;
    --border:       #E2E8F0;
    --border-hover: #CBD5E1;
    --accent:       var(--primary-color, #2563EB);
    --accent-soft:  rgba(37,99,235,0.08);
    --accent2:      #16A34A;
    --accent3:      #D97706;
    --accent4:      #7C3AED;
    --accent5:      #EA580C;
    --text-primary: var(--text-color, #0F172A);
    --text-secondary:var(--text-color, #334155);
    --text-muted:   #64748B;
    --danger:       #DC2626;
    --danger-soft:  rgba(220,38,38,0.06);
    --warning:      #D97706;
    --success:      #16A34A;
    --success-soft: rgba(22,163,74,0.06);
    --code-bg:      var(--secondary-background-color, #F1F5F9);
    --code-text:    var(--primary-color, #1E40AF);
    --shadow-sm:    0 1px 2px rgba(0,0,0,0.04);
    --shadow-md:    0 2px 8px rgba(0,0,0,0.06);
    --shadow-lg:    0 4px 16px rgba(0,0,0,0.08);
    --gradient-primary: linear-gradient(135deg, var(--primary-color, #2563EB) 0%, var(--primary-color, #3B82F6) 100%);
    --gradient-card: linear-gradient(135deg, var(--secondary-background-color, #FFFFFF) 0%, var(--background-color, #F8FAFC) 100%);
}

[data-testid="stAppViewContainer"][data-theme="dark"],
.stApp[data-theme="dark"] {
    --bg-base:      #0F172A;
    --bg-card:      #1E293B;
    --bg-card2:     #273548;
    --border:       #334155;
    --border-hover: #475569;
    --accent:       var(--primary-color, #3B82F6);
    --accent-soft:  rgba(59,130,246,0.12);
    --accent2:      #22C55E;
    --accent3:      #F59E0B;
    --accent4:      #A78BFA;
    --accent5:      #FB923C;
    --text-primary: var(--text-color, #F1F5F9);
    --text-secondary:var(--text-color, #CBD5E1);
    --text-muted:   #94A3B8;
    --danger:       #EF4444;
    --danger-soft:  rgba(239,68,68,0.10);
    --warning:      #F59E0B;
    --success:      #22C55E;
    --success-soft: rgba(34,197,94,0.10);
    --code-bg:      var(--secondary-background-color, #0F172A);
    --code-text:    var(--primary-color, #7DD3FC);
    --shadow-sm:    0 1px 2px rgba(0,0,0,0.20);
    --shadow-md:    0 2px 8px rgba(0,0,0,0.30);
    --shadow-lg:    0 4px 16px rgba(0,0,0,0.40);
    --gradient-primary: linear-gradient(135deg, var(--primary-color, #1D4ED8) 0%, var(--primary-color, #3B82F6) 100%);
    --gradient-card: linear-gradient(135deg, var(--secondary-background-color, #1E293B) 0%, var(--background-color, #273548) 100%);
}

/* ── Global reset ─────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
    color: var(--text-primary) !important;
}

/* ── Sidebar ──────────────────────────────── */
[data-testid="stSidebar"] {
    background-color: var(--bg-card) !important;
    border-right: 1px solid var(--border) !important;
}

/* ── Main area ────────────────────────────── */
.main .block-container {
    padding-top: 1.5rem !important;
    max-width: 100% !important;
}

/* ── Metric cards ─────────────────────────── */
[data-testid="stMetric"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 1rem 1.25rem !important;
    box-shadow: var(--shadow-sm) !important;
}
[data-testid="stMetricLabel"] { color: var(--text-muted) !important; font-size: 0.78rem !important; text-transform: uppercase; letter-spacing: 0.05em; }
[data-testid="stMetricValue"] { color: var(--accent) !important; font-size: 1.8rem !important; font-weight: 700 !important; }
[data-testid="stMetricDelta"] { color: var(--accent2) !important; }

/* ── Buttons ──────────────────────────────── */
.stButton > button {
    background: var(--gradient-primary) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.85rem !important;
    padding: 0.5rem 1.15rem !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.01em !important;
    box-shadow: var(--shadow-sm) !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 14px rgba(37,99,235,0.3) !important;
}

/* ── Text inputs ──────────────────────────── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div > div {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* ── Expanders ────────────────────────────── */
[data-testid="stExpander"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    margin-bottom: 0.5rem !important;
    box-shadow: var(--shadow-sm) !important;
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
.badge-green  { background-color: var(--success-soft);  color: var(--success); border: 1px solid rgba(22,163,74,0.2); }
.badge-red    { background-color: var(--danger-soft);   color: var(--danger);  border: 1px solid rgba(220,38,38,0.2); }
.badge-blue   { background-color: var(--accent-soft);   color: var(--accent);  border: 1px solid rgba(37,99,235,0.2); }
.badge-orange { background-color: rgba(217,119,6,0.08); color: var(--warning); border: 1px solid rgba(217,119,6,0.2); }
.badge-purple { background-color: rgba(124,58,237,0.08);color: var(--accent4); border: 1px solid rgba(124,58,237,0.2); }

/* ── Section header cards ─────────────────── */
.section-header {
    background: var(--gradient-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.25rem;
    box-shadow: var(--shadow-sm);
}
.section-header h2 { margin: 0; font-size: 1.25rem; font-weight: 700; color: var(--accent); }
.section-header p  { margin: 0.25rem 0 0; font-size: 0.82rem; color: var(--text-muted); }

/* ── Status dot ───────────────────────────── */
.dot { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
.dot-green  { background-color: var(--success); box-shadow: 0 0 6px var(--success); }
.dot-red    { background-color: var(--danger);  box-shadow: 0 0 6px var(--danger); }
.dot-yellow { background-color: var(--warning); box-shadow: 0 0 6px var(--warning); }

/* ── Debug / code panels ──────────────────── */
.debug-panel {
    background-color: var(--code-bg);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.78rem;
    color: var(--code-text);
    overflow-x: auto;
    white-space: pre-wrap;
}

/* ── Info cards (architecture, docs) ──────── */
.info-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.2s ease, border-color 0.2s ease;
}
.info-card:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--border-hover);
}
.info-card h4 { margin: 0 0 0.5rem; font-weight: 700; color: var(--text-primary); font-size: 0.95rem; }
.info-card p  { margin: 0; font-size: 0.84rem; color: var(--text-secondary); line-height: 1.55; }
.info-card code {
    background-color: var(--accent-soft);
    color: var(--accent);
    padding: 0.15em 0.45em;
    border-radius: 4px;
    font-size: 0.8em;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Flow / pipeline diagram ──────────────── */
.flow-step {
    display: flex;
    align-items: flex-start;
    gap: 1rem;
    padding: 1rem 1.25rem;
    margin-bottom: 2px;
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 10px;
    box-shadow: var(--shadow-sm);
    transition: all 0.2s ease;
}
.flow-step:hover { border-color: var(--accent); box-shadow: var(--shadow-md); }
.flow-step-num {
    min-width: 32px; min-height: 32px;
    display: flex; align-items: center; justify-content: center;
    border-radius: 50%;
    background-color: var(--accent);
    color: #fff;
    font-weight: 700;
    font-size: 0.82rem;
    flex-shrink: 0;
}
.flow-step-content { flex: 1; }
.flow-step-content h4 { margin: 0 0 0.25rem; font-size: 0.92rem; font-weight: 600; color: var(--text-primary); }
.flow-step-content p  { margin: 0; font-size: 0.82rem; color: var(--text-muted); line-height: 1.5; }
.flow-arrow {
    text-align: center;
    color: var(--text-muted);
    font-size: 1.1rem;
    padding: 0.15rem 0;
}

/* ── Endpoint table cards ─────────────────── */
.ep-card {
    background-color: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem;
    margin-bottom: 0.75rem;
    box-shadow: var(--shadow-sm);
}
.ep-method {
    display: inline-block;
    padding: 0.2em 0.6em;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 0.04em;
}
.ep-get    { background-color: rgba(22,163,74,0.1);  color: var(--success); }
.ep-post   { background-color: rgba(37,99,235,0.1);  color: var(--accent); }
.ep-delete { background-color: rgba(220,38,38,0.1);  color: var(--danger); }
.ep-route  { font-family: 'JetBrains Mono', monospace; font-weight: 600; font-size: 0.92rem; color: var(--text-primary); }

/* ── Workspace pill ───────────────────────── */
.workspace-pill {
    background-color: var(--accent-soft);
    border: 1px solid rgba(37,99,235,0.2);
    border-radius: 20px;
    padding: 0.4rem 1rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem;
    color: var(--accent);
    font-weight: 600;
    display: inline-block;
    margin-top: 0.25rem;
}

/* ── Page docs footer ─────────────────────── */
.page-docs {
    background-color: var(--bg-card2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1.25rem 1.5rem;
    margin-top: 2rem;
}
.page-docs h4 { margin: 0 0 .6rem; color: var(--accent); font-size: 0.95rem; }
.page-docs p, .page-docs li { font-size: 0.84rem; color: var(--text-secondary); line-height: 1.6; }
.page-docs code {
    background-color: var(--accent-soft); color: var(--accent);
    padding: 0.12em 0.4em; border-radius: 4px; font-size: 0.82em;
    font-family: 'JetBrains Mono', monospace;
}

/* ── Chat bubbles ─────────────────────────── */
[data-testid="stChatMessage"] {
    background-color: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 12px !important;
    margin-bottom: 0.5rem !important;
}

/* ── File uploader ────────────────────────── */
[data-testid="stFileUploaderDropzone"] {
    background-color: var(--bg-card2) !important;
    border: 2px dashed var(--border) !important;
    border-radius: 10px !important;
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

/* ── Alerts ───────────────────────────────── */
[data-testid="stAlert"] {
    border-radius: 10px !important;
    font-size: 0.85rem !important;
}

/* ── Internal explainer ───────────────────── */
.how-it-works {
    background-color: var(--accent-soft);
    border-left: 3px solid var(--accent);
    border-radius: 0 8px 8px 0;
    padding: 1rem 1.25rem;
    margin-top: 0.75rem;
}
.how-it-works h5 { margin: 0 0 .4rem; color: var(--accent); font-size: 0.85rem; }
.how-it-works p, .how-it-works li { font-size: 0.8rem; color: var(--text-secondary); line-height: 1.55; margin: 0; }
.how-it-works ol, .how-it-works ul { padding-left: 1.2rem; margin: .25rem 0 0; }

/* ── Warning callout ──────────────────────── */
.callout-warn {
    background-color: rgba(217,119,6,0.06);
    border: 1px solid rgba(217,119,6,0.2);
    border-left: 3px solid var(--warning);
    border-radius: 0 8px 8px 0;
    padding: 0.85rem 1.15rem;
    margin: 0.75rem 0;
}
.callout-warn p { margin: 0; font-size: 0.84rem; color: var(--text-secondary); }
.callout-warn strong { color: var(--warning); }
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
    ("🏗", "Architecture"),
    ("🔌", "Endpoint Explorer"),
    ("🔬", "RAG Pipeline"),
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
    sub_html = "<p>" + subtitle + "</p>" if subtitle else ""
    st.markdown(
        f'<div class="section-header"><h2>{icon} {title}</h2>{sub_html}</div>',
        unsafe_allow_html=True,
    )


def how_it_works(title: str, steps: List[str]) -> None:
    """Render a 'How this works internally' explainer block."""
    items = "".join(f"<li>{s}</li>" for s in steps)
    st.markdown(
        f'<div class="how-it-works">'
        f'<h5>⚙️ {title}</h5>'
        f'<ol>{items}</ol>'
        f'</div>',
        unsafe_allow_html=True,
    )


def page_docs(purpose: str, used_by: List[str], endpoints: List[str]) -> None:
    """Render 'What does this page do?' footer on every page."""
    used_items = "".join(f"<li>{u}</li>" for u in used_by)
    ep_items = "".join(f"<li><code>{e}</code></li>" for e in endpoints)
    st.markdown(
        f'<div class="page-docs">'
        f'<h4>📖 What does this page do?</h4>'
        f'<p><strong>Purpose:</strong> {purpose}</p>'
        f'<p style="margin-top:.6rem;"><strong>Used by:</strong></p><ol>{used_items}</ol>'
        f'<p style="margin-top:.6rem;"><strong>Related endpoints:</strong></p><ul>{ep_items}</ul>'
        f'</div>',
        unsafe_allow_html=True,
    )


def flow_step(num: int, title: str, desc: str, show_arrow: bool = True) -> None:
    """Render a numbered step in a pipeline visualization."""
    st.markdown(
        f'<div class="flow-step">'
        f'<div class="flow-step-num">{num}</div>'
        f'<div class="flow-step-content"><h4>{title}</h4><p>{desc}</p></div>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if show_arrow:
        st.markdown('<div class="flow-arrow">↓</div>', unsafe_allow_html=True)


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
                    f'<span class="badge badge-blue">{latency_val}s</span>'
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
    st.markdown(
        '<div style="padding: 0.5rem 0 1rem; text-align: center;">'
        '<div style="font-size: 2.2rem;">🛸</div>'
        '<div style="font-size: 1rem; font-weight: 700; color: var(--accent); letter-spacing: 0.06em;">DEV CONSOLE</div>'
        '<div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 0.1rem;">AI Avatar &middot; DevOps &amp; Architecture</div>'
        '</div>',
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

    # ── Navigation: Operations ───────────────
    st.markdown("**Operations**")
    for icon, name in PAGES[:7]:
        btn_label = f"{icon}  {name}"
        if st.button(btn_label, key=f"nav_{name}", use_container_width=True):
            st.session_state.page = name
            st.rerun()

    st.divider()

    # ── Navigation: Documentation ────────────
    st.markdown("**Documentation**")
    for icon, name in PAGES[7:]:
        btn_label = f"{icon}  {name}"
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
        f'<span style="font-size:0.72rem;color:var(--text-muted);">{BASE_URL}</span>',
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div style="margin-top:2rem;font-size:0.68rem;color:var(--text-muted);text-align:center;">'
        "AI Avatar Dev Console &middot; v3.0</div>",
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

    if st.session_state.chat_history:
        if st.button("🗑 Clear Chat History", key="clear_chat"):
            st.session_state.chat_history = []
            st.rerun()

    # ── How it works ─────────────────────────
    how_it_works("How Chat Query Works Internally", [
        "Your question and <code>workspace_id</code> are sent to <code>POST /query</code>.",
        "Backend checks the TTL cache for an identical recent question.",
        "Knowledge Base is searched for a high-confidence match (score &ge; 0.75).",
        "If no KB match, ChromaDB similarity search retrieves top-4 document chunks.",
        "KB context and Chroma context are merged into a single prompt.",
        "Prompt is sent to Qwen/HF API with a strict system message.",
        "Response is streamed back as SSE events (<code>token</code> and <code>final_response</code>).",
    ])

    debug_panel()

    page_docs(
        "Send a natural-language question through the full RAG pipeline and observe the streamed response, "
        "response source, latency, and approximate token count.",
        ["Developers testing RAG answer quality.", "Debugging slow or incorrect responses.", "Comparing KB vs document-based answers."],
        ["POST /query"],
    )


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
                    f'<span style="color:var(--text-muted);font-size:0.8rem;">{size_kb} KB</span>',
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

        how_it_works("How Upload Works Internally", [
            "Files are sent as multipart form data with <code>workspace_id</code>.",
            "Backend validates file extensions (.pdf, .txt, .docx) and size (&le; 100 MB).",
            "Each file is saved to <code>./data/raw_docs/{workspace_id}/</code>.",
            "Markdown (.md) files are parsed for Q&A pairs and added to the Knowledge Base.",
            "All files are split into text chunks using <code>load_and_split()</code>.",
            "Chunks are embedded and stored in ChromaDB under the workspace collection.",
        ])

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
                            pass
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

    page_docs(
        "Upload documents into the vector store for RAG retrieval. Manage and delete indexed files.",
        ["Adding course material, PDFs, or reference docs.", "Removing outdated documents.", "Checking ingestion results (chunk counts, QA pairs)."],
        ["POST /upload", "GET /db_stats", "DELETE /raw_docs"],
    )


# ══════════════════════════════════════════════
#  PAGE 3: KNOWLEDGE BASE
# ══════════════════════════════════════════════
elif page == "Knowledge Base":
    section_header("🧠", "Knowledge Base Manager",
                   "Add, view and delete Q&A pairs stored in the knowledge base.")

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

        how_it_works("How Adding Knowledge Works Internally", [
            "Question, answer, and tags are sent to <code>POST /add_knowledge</code> with <code>workspace_id</code>.",
            "Backend stores the Q&A pair in SQLite (<code>knowledge_base.db</code>).",
            "An embedding is generated for the question for similarity matching.",
            "During queries, KB entries are matched first (score &ge; 0.75 = instant answer).",
            "Lower-scoring KB entries (0.4&ndash;0.75) are mixed into RAG context.",
        ])

    st.divider()

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
                        meta_row.append(f'<span style="color:var(--text-muted);font-size:0.75rem;">🕐 {created_at}</span>')
                    if meta_row:
                        st.markdown("&nbsp;".join(meta_row), unsafe_allow_html=True)

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

    page_docs(
        "Store manual Q&A definitions that override or enrich RAG-generated answers.",
        [
            "Exact answer matching — if a question scores ≥ 0.75 against a KB entry, the KB answer is returned instantly.",
            "RAG context enrichment — lower-scoring KB entries are merged into the context sent to the LLM.",
            "Curating authoritative answers for frequently asked questions.",
        ],
        ["GET /knowledge", "POST /add_knowledge", "DELETE /delete_knowledge/{id}"],
    )


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

        how_it_works("How Website Ingestion Works Internally", [
            "URL and <code>workspace_id</code> are sent to <code>POST /ingest/website</code>.",
            "Backend uses <code>web_ingest.ingest_website()</code> to scrape page content.",
            "HTML is converted to clean text and split into chunks.",
            "Chunks are embedded and stored in ChromaDB under the workspace.",
        ])

    debug_panel()

    page_docs(
        "Ingest content from external websites into the vector store for RAG retrieval.",
        ["Adding online documentation as context.", "Indexing Wikipedia or blog articles.", "Expanding the knowledge available for a workspace."],
        ["POST /ingest/website"],
    )


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
                f'<div class="info-card">'
                f'<h4>Collections</h4>'
                f'<p style="font-size:2rem;font-weight:700;color:var(--accent);">{vdb.get("collections", "N/A")}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with vdb_col2:
            model_name = vdb.get("model", "N/A")
            st.markdown(
                f'<div class="info-card">'
                f'<h4>Embedding Model</h4>'
                f'<p style="font-family:JetBrains Mono,monospace;color:var(--accent4);font-weight:600;margin-top:.4rem;">{model_name}</p>'
                f'</div>',
                unsafe_allow_html=True,
            )

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

        with st.expander("📋 Raw API Response"):
            st.json(info)

    else:
        st.error("❌ Could not retrieve database stats. Ensure the backend is running and workspace_id is correct.")

    debug_panel()

    page_docs(
        "View live statistics about the current workspace: document counts, chunk counts, KB entries, and raw files.",
        ["Monitoring data ingestion progress.", "Verifying workspace state before/after operations.", "Debugging missing or duplicate data."],
        ["GET /db_stats"],
    )


# ══════════════════════════════════════════════
#  PAGE 6: WORKSPACE TOOLS (reset + eval)
# ══════════════════════════════════════════════
elif page == "Workspace Tools":
    section_header("🔧", "Workspace Tools",
                   "Advanced management operations and RAG evaluation for the selected workspace.")

    eval_tab, ws_guide_tab, reset_tab = st.tabs(["📊 Evaluation", "🧩 Workspace Isolation", "⚠️ Danger Zone"])

    with eval_tab:
        st.markdown("### 🧪 RAG vs Baseline Evaluation")
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
                        "RAG OK": "✅" if rag_ok else "❌",
                        "Qwen OK": "✅" if qwen_ok else "❌",
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

    # ── Workspace Isolation Guide ─────────────
    with ws_guide_tab:
        st.markdown("### 🧩 Workspace Isolation Guide")
        st.markdown(
            '<div class="info-card">'
            '<h4>What is <code>workspace_id</code>?</h4>'
            '<p>Every API call in this system is scoped to a <strong>workspace</strong>. '
            'A workspace_id is a unique string (typically a user email or tenant ID) that '
            'isolates all data: uploads, knowledge base entries, vector embeddings, and statistics.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("#### Example: Two Isolated Workspaces")
        ws_col1, ws_col2 = st.columns(2)
        with ws_col1:
            st.markdown(
                '<div class="info-card" style="border-left: 3px solid var(--accent);">'
                '<h4>📁 Workspace A</h4>'
                '<p><code>student1@gmail.com</code></p>'
                '<p style="margin-top:.5rem;">Separate:</p>'
                '<ul style="font-size:.84rem;color:var(--text-secondary);">'
                '<li>Uploads &rarr; <code>./data/raw_docs/student1@gmail.com/</code></li>'
                '<li>Knowledge Base &rarr; filtered by workspace_id</li>'
                '<li>Vector Embeddings &rarr; ChromaDB collection filter</li>'
                '<li>Statistics &rarr; scoped counts only</li>'
                '</ul>'
                '</div>',
                unsafe_allow_html=True,
            )
        with ws_col2:
            st.markdown(
                '<div class="info-card" style="border-left: 3px solid var(--accent4);">'
                '<h4>📁 Workspace B</h4>'
                '<p><code>student2@gmail.com</code></p>'
                '<p style="margin-top:.5rem;">Separate:</p>'
                '<ul style="font-size:.84rem;color:var(--text-secondary);">'
                '<li>Uploads &rarr; <code>./data/raw_docs/student2@gmail.com/</code></li>'
                '<li>Knowledge Base &rarr; filtered by workspace_id</li>'
                '<li>Vector Embeddings &rarr; ChromaDB collection filter</li>'
                '<li>Statistics &rarr; scoped counts only</li>'
                '</ul>'
                '</div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="callout-warn">'
            '<p>⚠️ <strong>Warning:</strong> Changing the <code>workspace_id</code> in the sidebar '
            'changes the entire data scope. All operations (chat, upload, knowledge, stats, reset) '
            'will target the new workspace. Data from one workspace is never visible to another.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

        st.markdown("#### How Workspace Isolation Works in Code")
        how_it_works("Workspace Scoping Internals", [
            "Every endpoint receives <code>workspace_id</code> as a body field, form field, or query parameter.",
            "ChromaDB stores all embeddings in a shared collection but filters by a <code>workspace_id</code> metadata field.",
            "SQLite Knowledge Base uses <code>WHERE workspace_id = ?</code> in every query.",
            "Raw files are stored under <code>./data/raw_docs/{workspace_id}/</code> (filesystem isolation).",
            "Cache keys are prefixed with <code>{workspace_id}::</code> to avoid cross-workspace cache hits.",
        ])

    # ── Danger Zone ───────────────────────────
    with reset_tab:
        st.markdown(
            '<div style="background:var(--danger-soft);border:1px solid rgba(220,38,38,0.2);'
            'border-radius:12px;padding:1.25rem;margin-bottom:1rem;">'
            '<h3 style="color:var(--danger);margin:0 0 .5rem;">⚠️ Danger Zone</h3>'
            '<p style="color:var(--text-secondary);margin:0;font-size:.85rem;">'
            'The actions below are <strong style="color:var(--danger);">irreversible</strong>. '
            'All vector embeddings, raw files and Q&amp;A pairs for the workspace will be permanently deleted.'
            '</p></div>',
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

        how_it_works("How Reset Works Internally", [
            "<code>POST /reset_db?workspace_id=...</code> is called.",
            "All vector embeddings for the workspace are deleted from ChromaDB.",
            "All raw files under <code>./data/raw_docs/{workspace_id}/</code> are deleted.",
            "All Q&A pairs for the workspace are removed from SQLite.",
            "The cache is cleared for that workspace.",
        ])

    debug_panel()

    page_docs(
        "Advanced workspace management: run evaluations, understand workspace isolation, and reset workspace data.",
        ["Comparing RAG vs baseline answer quality.", "Understanding how workspace_id scoping works.", "Resetting a workspace to start fresh."],
        ["POST /query_eval", "POST /qwen", "POST /reset_db"],
    )


# ══════════════════════════════════════════════
#  PAGE 7: SYSTEM HEALTH
# ══════════════════════════════════════════════
elif page == "System Health":
    section_header("❤️", "System Health Panel",
                   "Live endpoint status checks and environment diagnostics.")

    col_r, _ = st.columns([1, 5])
    with col_r:
        if st.button("🔄 Re-run Checks", key="health_refresh_btn"):
            st.rerun()

    st.markdown("### 🔌 Endpoint Status Checks")

    CHECKS = [
        ("Root / Ping",      "GET",  "/",          None,                           None),
        ("DB Stats",         "GET",  "/db_stats",  {"workspace_id": workspace},    None),
        ("Knowledge List",   "GET",  "/knowledge", {"workspace_id": workspace},    None),
        ("Raw Docs List",    "GET",  "/raw_docs",  {"workspace_id": workspace},    None),
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
                "Endpoint": name, "Path": path, "Status": r.status_code,
                "OK": "✅" if ok else "❌", "Latency (s)": lat,
            })
        except Exception:
            lat = round(time.time() - t0, 3)
            results_table.append({
                "Endpoint": name, "Path": path, "Status": "ERR",
                "OK": "❌", "Latency (s)": lat,
            })

    for row in results_table:
        ok = row["OK"] == "✅"
        dot = status_dot(ok)
        status_badge = badge(str(row["Status"]), "green" if ok else "red")
        lat_badge = badge(f"{row['Latency (s)']}s", "blue")
        st.markdown(
            f'<div class="info-card" style="display:flex;align-items:center;gap:1rem;padding:.75rem 1.25rem;">'
            f'{dot}'
            f'<span style="font-weight:600;flex:1;">{row["Endpoint"]}</span>'
            f'<code style="color:var(--text-muted);font-size:.78rem;flex:1;">{row["Path"]}</code>'
            f'{status_badge} &nbsp; {lat_badge}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### 🌍 Environment Diagnostics")
    env_col1, env_col2 = st.columns(2)

    with env_col1:
        api_key_set = bool(st.session_state.api_key)
        hf_key_env = bool(os.environ.get("HF_API_KEY"))

        def env_row(label, ok, hint=""):
            d = status_dot(ok)
            b = badge("SET" if ok else "MISSING", "green" if ok else "red")
            hint_html = (
                '<span style="color:var(--text-muted);font-size:.72rem;">' + hint + "</span>"
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
        status_text = "All checks passing" if backend_ok else "Backend appears unreachable"
        st.markdown(
            f'<div class="info-card">'
            f'{status_dot(backend_ok)}'
            f'<span style="font-weight:600;">{BASE_URL}</span><br/>'
            f'<span style="color:var(--text-muted);font-size:.78rem;margin-top:.3rem;display:block;">'
            f'{status_text}</span></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    with st.expander("📋 Endpoint Results (raw table)"):
        import pandas as pd
        st.dataframe(pd.DataFrame(results_table), use_container_width=True, hide_index=True)

    debug_panel()

    page_docs(
        "Monitor backend health by pinging key endpoints and checking environment variables.",
        ["Quick verification that all services are running.", "Diagnosing connection or configuration issues.", "Checking API key status before protected operations."],
        ["GET /", "GET /db_stats", "GET /knowledge", "GET /raw_docs"],
    )


# ══════════════════════════════════════════════
#  PAGE 8: ARCHITECTURE EXPLORER
# ══════════════════════════════════════════════
elif page == "Architecture":
    section_header("🏗", "Architecture Explorer",
                   "Visual overview of the system architecture, components, and data flow.")

    st.markdown("### 🔄 System Data Flow")
    st.markdown("The following shows how a user query flows through the system end-to-end:")

    flow_step(1, "👤 User (Student / Teacher)",
              "Enters a question through the Flask web UI or this Streamlit Dev Console.")
    flow_step(2, "🖥 Frontend (Flask Web App)",
              "The production user interface. Renders the chatbot UI, handles sessions, and forwards queries to the FastAPI backend. "
              "Runs on port 5000 by default.")
    flow_step(3, "🛸 Streamlit Dev Console (This App)",
              "Developer/admin testing interface. Provides direct access to all backend endpoints with debug tooling. "
              "Runs on port 8501. This is a testing tool, not the production UI.")
    flow_step(4, "⚡ FastAPI Backend",
              "The core API server. Handles routing, authentication, rate limiting, file processing, and LLM orchestration. "
              "Runs on port 8000 via uvicorn. All business logic lives here.")
    flow_step(5, "🧠 Knowledge Base (SQLite)",
              "Stores manually curated Q&A pairs in <code>knowledge_base.db</code>. "
              "Provides high-confidence instant answers (score &ge; 0.75) and context enrichment (0.4&ndash;0.75).")
    flow_step(6, "📚 ChromaDB (Vector Store)",
              "Stores document embeddings in <code>./data/chroma_db/</code>. "
              "Performs similarity search to retrieve the top-4 most relevant document chunks for context.")
    flow_step(7, "🤖 Qwen / HuggingFace API",
              "The LLM inference endpoint. Receives the assembled prompt (system message + context + question) "
              "and generates a response. Model: <code>Qwen/Qwen2.5-7B-Instruct</code>.", show_arrow=False)

    st.divider()

    st.markdown("### 🧱 Component Details")
    comp_data = [
        ("⚡ FastAPI Backend", "app/main.py",
         "Central API server. Handles all HTTP endpoints, request validation, rate limiting (slowapi), "
         "CORS, file upload processing, LLM calls, and SSE streaming.",
         ["Route requests to appropriate handlers",
          "Validate workspace_id on every call",
          "Manage TTL cache for repeated queries",
          "Orchestrate KB + ChromaDB + LLM pipeline",
          "Stream responses via Server-Sent Events"]),

        ("🧠 Knowledge Base Manager", "app/utils/kb_manager.py",
         "SQLite-backed storage for curated Q&A pairs. Each entry is scoped to a workspace_id.",
         ["Store and retrieve Q&A pairs per workspace",
          "Compute similarity scores for question matching",
          "Provide high-confidence instant answers",
          "Supply context entries for RAG enrichment"]),

        ("📚 ChromaDB Manager", "app/utils/db_manager.py",
         "Vector database manager using ChromaDB for document embeddings and similarity search.",
         ["Embed and store document chunks",
          "Perform similarity search filtered by workspace",
          "Track unique document sources",
          "Clear workspace data on reset"]),

        ("📄 Document Loader", "app/utils/loader.py",
         "File parsing and text splitting utility. Supports PDF, TXT, and DOCX formats.",
         ["Parse document files into raw text",
          "Split text into manageable chunks for embedding",
          "Handle encoding and format differences"]),

        ("🌐 Web Ingestion", "app/utils/web_ingest.py",
         "Website scraping and indexing utility. Converts web pages into vector-searchable chunks.",
         ["Scrape HTML content from URLs",
          "Clean and extract meaningful text",
          "Split into chunks and index into ChromaDB"]),

        ("🖥 Flask Frontend", "Frontend/app.py",
         "Production user-facing web application. Provides the chatbot UI that students and teachers interact with.",
         ["Render chat interface with avatar",
          "Stream responses from FastAPI backend",
          "Handle user sessions and workspace routing",
          "Serve static assets"]),
    ]

    for comp_name, file_path, description, responsibilities in comp_data:
        resp_items = "".join(f"<li>{r}</li>" for r in responsibilities)
        st.markdown(
            f'<div class="info-card">'
            f'<h4>{comp_name}</h4>'
            f'<p style="font-size:.78rem;color:var(--text-muted);margin-bottom:.5rem;"><code>{file_path}</code></p>'
            f'<p>{description}</p>'
            f'<p style="margin-top:.6rem;font-weight:600;font-size:.84rem;color:var(--text-primary);">Responsibilities:</p>'
            f'<ul style="font-size:.84rem;color:var(--text-secondary);line-height:1.6;">{resp_items}</ul>'
            f'</div>',
            unsafe_allow_html=True,
        )

    debug_panel()

    page_docs(
        "Understand the full system architecture: components, data flow, and responsibilities.",
        ["Onboarding new developers to the project.", "Understanding where to make changes.", "Visualizing how data flows from user to LLM and back."],
        ["N/A — This is a documentation page, no endpoints are called."],
    )


# ══════════════════════════════════════════════
#  PAGE 9: ENDPOINT EXPLORER
# ══════════════════════════════════════════════
elif page == "Endpoint Explorer":
    section_header("🔌", "Endpoint Explorer",
                   "Complete reference for every backend API endpoint, including request/response formats.")

    # Endpoint data: (method, route, purpose, payload, response_type, workspace_aware, auth_required, flow, importance)
    ENDPOINTS = [
        {
            "method": "GET", "route": "/",
            "purpose": "Health check / ping.",
            "payload": "None",
            "response": '{"status": "API is running"}',
            "workspace": False, "auth": False,
            "flow": "Returns static JSON.",
            "importance": "Used by health checks and monitoring.",
        },
        {
            "method": "POST", "route": "/query",
            "purpose": "Main RAG pipeline. Streaming chat endpoint.",
            "payload": '{"question": "...", "workspace_id": "..."}',
            "response": "SSE stream: event:token + event:final_response",
            "workspace": True, "auth": False,
            "flow": "Question → Cache check → KB lookup (≥0.75 = instant) → KB context (0.4–0.75) → ChromaDB retrieval (top 4) → Context merge → Prompt assembly → Qwen/HF API → SSE response",
            "importance": "Primary chatbot endpoint. Powers both Flask frontend and Streamlit chat.",
        },
        {
            "method": "POST", "route": "/query_eval",
            "purpose": "Non-streaming RAG endpoint for evaluation.",
            "payload": '{"question": "...", "workspace_id": "..."}',
            "response": '{"answer": "...", "contexts": [...], "source": "rag", "context_used": N}',
            "workspace": True, "auth": False,
            "flow": "Same RAG pipeline as /query but returns JSON instead of SSE.",
            "importance": "Used for automated evaluation and RAGAS scoring.",
        },
        {
            "method": "POST", "route": "/qwen",
            "purpose": "Baseline Qwen-only endpoint (no RAG context).",
            "payload": '{"question": "..."}',
            "response": '{"answer": "..."}',
            "workspace": False, "auth": False,
            "flow": "Question → Qwen/HF API directly (no context, no KB).",
            "importance": "Comparison baseline for evaluation. Shows what Qwen answers without RAG.",
        },
        {
            "method": "POST", "route": "/upload",
            "purpose": "Upload and index documents.",
            "payload": "multipart/form-data: files[] + workspace_id",
            "response": '{"message": "Uploaded N file(s), indexed M chunks", "qa_indexed": K}',
            "workspace": True, "auth": False,
            "flow": "Files → Validation → Save to disk → Parse & split → Embed → Store in ChromaDB",
            "importance": "Core data ingestion. Accepts PDF, TXT, DOCX (max 100 MB each).",
        },
        {
            "method": "GET", "route": "/db_stats",
            "purpose": "Get database statistics for a workspace.",
            "payload": "Query param: workspace_id",
            "response": '{"vector_db": {...}, "qa_pairs": N, "raw_count": N, "raw_files": [...]}',
            "workspace": True, "auth": False,
            "flow": "Queries ChromaDB stats + SQLite KB count + filesystem listing.",
            "importance": "Dashboard metrics. Used by Database Stats page.",
        },
        {
            "method": "GET", "route": "/knowledge",
            "purpose": "List all KB Q&A pairs for a workspace.",
            "payload": "Query param: workspace_id",
            "response": '[{"id": N, "question": "...", "answer": "...", "tags": "..."}]',
            "workspace": True, "auth": False,
            "flow": "Queries SQLite for all Q&A rows matching workspace_id.",
            "importance": "Knowledge Base viewer. Read-only listing.",
        },
        {
            "method": "POST", "route": "/add_knowledge",
            "purpose": "Add a Q&A pair to the Knowledge Base.",
            "payload": '{"workspace_id": "...", "question": "...", "answer": "...", "tags": "..."}',
            "response": '{"message": "Knowledge added"}',
            "workspace": True, "auth": False,
            "flow": "Validates input → Inserts into SQLite → Generates embedding.",
            "importance": "Allows manual curation of authoritative answers.",
        },
        {
            "method": "DELETE", "route": "/delete_knowledge/{qa_id}",
            "purpose": "Delete a specific KB entry.",
            "payload": "Path param: qa_id, Query param: workspace_id",
            "response": '{"message": "Deleted"}',
            "workspace": True, "auth": True,
            "flow": "Validates API key → Deletes from SQLite by ID + workspace.",
            "importance": "Protected endpoint. Requires Bearer token (FASTAPI_API_KEY).",
        },
        {
            "method": "POST", "route": "/reset_db",
            "purpose": "Reset entire workspace: vectors, files, and KB.",
            "payload": "Query param: workspace_id",
            "response": '{"message": "Deleted N file(s)...", "deleted_files": [...]}',
            "workspace": True, "auth": False,
            "flow": "Clear ChromaDB workspace → Delete raw files → Reset KB → Clear cache.",
            "importance": "Destructive. Irreversible. Used for workspace cleanup.",
        },
        {
            "method": "GET", "route": "/raw_docs",
            "purpose": "List raw uploaded files for a workspace.",
            "payload": "Query param: workspace_id",
            "response": '[{"filename": "..."}]',
            "workspace": True, "auth": False,
            "flow": "Lists files in ./data/raw_docs/{workspace_id}/.",
            "importance": "File inventory for the document list view.",
        },
        {
            "method": "DELETE", "route": "/raw_docs",
            "purpose": "Delete a specific raw file and its embeddings.",
            "payload": "Query params: filename, workspace_id",
            "response": '{"message": "Deleted filename"}',
            "workspace": True, "auth": False,
            "flow": "Delete embeddings by source path → Remove file from disk.",
            "importance": "Selective document removal without full workspace reset.",
        },
        {
            "method": "POST", "route": "/ingest/website",
            "purpose": "Scrape and index a website URL.",
            "payload": '{"url": "...", "workspace_id": "..."}',
            "response": '{"status": "success", "chunks_indexed": N, ...}',
            "workspace": True, "auth": False,
            "flow": "Scrape URL → Extract text → Split chunks → Embed → Store in ChromaDB.",
            "importance": "Extends knowledge base with web content.",
        },
    ]

    # Summary metrics
    total = len(ENDPOINTS)
    ws_aware = sum(1 for e in ENDPOINTS if e["workspace"])
    auth_required = sum(1 for e in ENDPOINTS if e["auth"])
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric("Total Endpoints", total)
    mc2.metric("Workspace-Aware", ws_aware)
    mc3.metric("Auth Required", auth_required)
    mc4.metric("Public (No Auth)", total - auth_required)

    st.divider()

    # Filter
    method_filter = st.multiselect(
        "Filter by method:", ["GET", "POST", "DELETE"],
        default=["GET", "POST", "DELETE"],
        key="ep_method_filter",
    )

    for ep in ENDPOINTS:
        if ep["method"] not in method_filter:
            continue

        method_lower = ep["method"].lower()
        method_class = f"ep-{method_lower}"
        ws_badge = badge("WORKSPACE", "blue") if ep["workspace"] else badge("GLOBAL", "orange")
        auth_badge = badge("AUTH REQUIRED", "red") if ep["auth"] else badge("PUBLIC", "green")

        st.markdown(
            f'<div class="ep-card">'
            f'<div style="display:flex;align-items:center;gap:.75rem;margin-bottom:.75rem;">'
            f'<span class="ep-method {method_class}">{ep["method"]}</span>'
            f'<span class="ep-route">{ep["route"]}</span>'
            f'<span style="margin-left:auto;">{ws_badge} &nbsp; {auth_badge}</span>'
            f'</div>'
            f'<p style="font-size:.88rem;color:var(--text-primary);font-weight:500;margin:0 0 .5rem;">{ep["purpose"]}</p>'
            f'<p style="font-size:.82rem;color:var(--text-muted);margin:0;">'
            f'<strong>Flow:</strong> {ep["flow"]}</p>'
            f'</div>',
            unsafe_allow_html=True,
        )

        with st.expander(f"Details: {ep['method']} {ep['route']}", expanded=False):
            det_c1, det_c2 = st.columns(2)
            with det_c1:
                st.markdown("**Request Payload:**")
                st.markdown(f'<div class="debug-panel">{ep["payload"]}</div>', unsafe_allow_html=True)
            with det_c2:
                st.markdown("**Response Format:**")
                st.markdown(f'<div class="debug-panel">{ep["response"]}</div>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size:.82rem;color:var(--text-muted);margin-top:.5rem;">'
                        f'<strong>Importance:</strong> {ep["importance"]}</p>', unsafe_allow_html=True)

    debug_panel()

    page_docs(
        "Complete API reference for every backend endpoint: methods, payloads, responses, and auth requirements.",
        ["Understanding which endpoints to call for each feature.", "Checking request/response formats before integration.", "Identifying which endpoints require authentication."],
        ["N/A — This is a documentation page referencing all endpoints."],
    )


# ══════════════════════════════════════════════
#  PAGE 10: RAG PIPELINE VISUALIZER
# ══════════════════════════════════════════════
elif page == "RAG Pipeline":
    section_header("🔬", "RAG Pipeline Visualizer",
                   "Step-by-step visualization of how questions are processed through the Retrieval-Augmented Generation pipeline.")

    st.markdown("### 📋 Full Pipeline Flow")

    flow_step(1, "📝 Question Input",
              "User submits a natural-language question. The question is lowercased and trimmed. "
              "A <code>workspace_id</code> must be provided to scope the search.")
    flow_step(2, "💾 Cache Check",
              "The backend checks a TTL cache (max 100 entries, 1-hour TTL) using the key "
              "<code>{workspace_id}::{question}</code>. If a cached answer exists, it is returned immediately as SSE.")
    flow_step(3, "🧠 Knowledge Base Search (High Confidence)",
              "The question is compared against all KB entries for the workspace using semantic similarity. "
              "If score &ge; <strong>0.75</strong>, the KB answer is returned directly (no LLM call). "
              "This is the fastest path — instant, curated answers.")
    flow_step(4, "🧠 Knowledge Base Context (Low Confidence)",
              "KB entries scoring between <strong>0.4</strong> and <strong>0.75</strong> are collected (top 3). "
              "These are not used as direct answers but are added to the context for the LLM.")
    flow_step(5, "📚 ChromaDB Similarity Search",
              "The question is embedded and compared against document chunks in ChromaDB, "
              "filtered by <code>workspace_id</code>. The <strong>top 4</strong> most similar chunks are retrieved.")
    flow_step(6, "🔗 Context Merge",
              "KB context entries and ChromaDB document chunks are merged into a single context string. "
              "KB entries appear first under 'Knowledge Base Entries:', followed by 'Document Excerpts:'.")
    flow_step(7, "📋 Prompt Assembly",
              "A strict system prompt is prepended. The user message wraps context in <code>&lt;context&gt;</code> tags "
              "and the question in <code>&lt;question&gt;</code> tags. The system prompt enforces context-only answering.")
    flow_step(8, "🤖 LLM Inference (Qwen)",
              "The assembled prompt is sent to <code>Qwen/Qwen2.5-7B-Instruct</code> via HuggingFace Router API. "
              "Settings: temperature=0.5, max_tokens=250, stream=False (response is chunked by backend for SSE).")
    flow_step(9, "🧹 Response Cleaning",
              "The raw LLM output is cleaned: extra whitespace collapsed, punctuation spacing fixed. "
              "The cleaned answer is cached for future identical questions.")
    flow_step(10, "📡 SSE Streaming",
              "The answer is streamed character-by-character as <code>event: token</code> SSE events (2ms delay). "
              "Finally, the complete answer is sent as <code>event: final_response</code>.", show_arrow=False)

    st.divider()

    st.markdown("### 🔍 Key Decision Points")

    dec_col1, dec_col2 = st.columns(2)
    with dec_col1:
        st.markdown(
            '<div class="info-card" style="border-left:3px solid var(--success);">'
            '<h4>🟢 Cache Hit</h4>'
            '<p>If the exact <code>{workspace_id}::{question}</code> was asked in the last hour, '
            'the cached answer is returned immediately. No KB search, no ChromaDB, no LLM call.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="info-card" style="border-left:3px solid var(--accent);">'
            '<h4>🔵 KB Direct Answer (score ≥ 0.75)</h4>'
            '<p>If a Knowledge Base entry matches the question with high confidence, '
            'the curated answer is returned immediately. The LLM is never called.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
    with dec_col2:
        st.markdown(
            '<div class="info-card" style="border-left:3px solid var(--accent4);">'
            '<h4>🟣 Full RAG Pipeline</h4>'
            '<p>If no cache hit and no high-confidence KB match, the full pipeline runs: '
            'KB context + ChromaDB chunks are merged and sent to the LLM with the question.</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="info-card" style="border-left:3px solid var(--warning);">'
            '<h4>🟡 No Context Available</h4>'
            '<p>In <code>/query_eval</code>, if neither KB nor ChromaDB return any relevant context, '
            'the system returns a safe fallback message instead of hallucinating.</p>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.divider()

    st.markdown("### 📊 Response Source Header")
    st.markdown(
        '<div class="info-card">'
        '<h4>X-Response-Source</h4>'
        '<p>The <code>/query</code> endpoint returns an <code>X-Response-Source</code> HTTP header '
        'indicating where the answer came from. Possible values:</p>'
        '<ul style="font-size:.84rem;color:var(--text-secondary);line-height:1.6;">'
        '<li><code>cache</code> — Answer was served from TTL cache</li>'
        '<li><code>knowledge_base</code> — Direct KB match (score &ge; 0.75)</li>'
        '<li><code>llm</code> / <code>rag</code> — Full RAG pipeline was used</li>'
        '</ul>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    # ── Live test: single query through query_eval ──
    st.markdown("### 🧪 Live Pipeline Test")
    st.caption("Send a question through `/query_eval` to see the full response breakdown.")

    test_q = st.text_input("Question", placeholder="Enter a test question…", key="rag_test_q")
    if st.button("▶ Run Through Pipeline", key="rag_test_btn"):
        if test_q.strip():
            with st.spinner("Running through RAG pipeline…"):
                t0 = time.time()
                r = api("query_eval", method="POST",
                        data={"question": test_q.strip(), "workspace_id": workspace})
                elapsed = round(time.time() - t0, 2)

            if r and r.status_code == 200:
                body = r.json()
                m1, m2, m3 = st.columns(3)
                m1.metric("Source", body.get("source", "N/A"))
                m2.metric("Context Pieces", body.get("context_used", "N/A"))
                m3.metric("Latency", f"{elapsed}s")

                st.success("**Answer:**")
                st.markdown(body.get("answer", "No answer"))

                contexts = body.get("contexts", [])
                if contexts:
                    with st.expander("📎 Retrieved Context", expanded=False):
                        for i, ctx in enumerate(contexts):
                            st.markdown(f"**Context {i+1}:**")
                            st.markdown(f'<div class="debug-panel">{ctx[:500]}</div>', unsafe_allow_html=True)
            else:
                st.error(f"❌ HTTP {r.status_code if r else 'N/A'}")
        else:
            st.warning("Enter a question first.")

    debug_panel()

    page_docs(
        "Visualize and understand the complete RAG pipeline: from question input through caching, "
        "knowledge base search, vector retrieval, context assembly, LLM inference, to streamed response.",
        ["Understanding the query processing flow.", "Debugging why certain answers are returned.", "Learning the decision tree (cache → KB → RAG → no context)."],
        ["POST /query (streaming)", "POST /query_eval (non-streaming, with context breakdown)"],
    )
