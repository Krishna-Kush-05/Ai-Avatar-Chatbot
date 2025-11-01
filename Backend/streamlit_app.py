# streamlit_app.py
import streamlit as st
import requests
import os
import time
import re
import json
from typing import List, Dict, Any, Optional

# --- Configuration ---
API_URL = "http://localhost:8000"
TABS = ["💬 Chat", "📚 Resources", "🧠 Knowledge", "⚙️ Admin"]

st.set_page_config(page_title="MITAOE AI Assistant", layout="wide", page_icon="🤖")
st.title("MITAOE AI Assistant")

# --- Session State Initialization ---
if "history" not in st.session_state:
    st.session_state.history = []
if "file_to_delete" not in st.session_state:
    st.session_state.file_to_delete = None
if "kb_to_delete" not in st.session_state:
    st.session_state.kb_to_delete = None

# --- API Request Helper ---
def api_request(endpoint: str, method: str = "GET", data: Optional[Dict] = None,
                params: Optional[Dict] = None, files: Optional[List] = None, stream: bool = False):
    """A centralized function to handle all API requests."""
    url = f"{API_URL}/{endpoint}"
    try:
        if method == "GET":
            return requests.get(url, params=params, stream=stream, timeout=30)
        elif method == "POST":
            return requests.post(url, json=data, files=files, params=params, stream=stream, timeout=60)
        elif method == "DELETE":
            return requests.delete(url, params=params, stream=stream, timeout=30)
    except requests.exceptions.RequestException as e:
        st.error(f"API connection error: {e}")
        return None

# --- UI Tabs ---
tab1, tab2, tab3, tab4 = st.tabs(TABS)

## -----------------------------
## Tab 1: Chat 💬
## -----------------------------
with tab1:
    st.header("🗣️ Chat with MITAOE's AI")

    # Display chat history
    for msg in st.session_state.history:
        role = msg.get("role", "user")
        avatar = "🧑‍💻" if role == "user" else "🤖"
        with st.chat_message(role, avatar=avatar):
            st.markdown(msg.get("text", ""))
            if role == "assistant":
                st.caption(f"Source: {msg.get('source', 'unknown')} | Time: {msg.get('time', 0):.2f}s")
    
    # Handle user input
    prompt = st.chat_input("Ask anything about MITAOE…", key="main_chat_input")
    if prompt:
        st.session_state.history.append({"role": "user", "text": prompt})
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

        # Stream response from API
        resp = api_request("query", method="POST", data={"question": prompt}, stream=True)
        if not resp:
            st.error("Failed to get response from API.")
        else:
            source = resp.headers.get("X-Response-Source", "llm")
            start_time = time.time()
            
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                raw_buffer = []
                final_text = ""
                event_type = ""
                
                for line in resp.iter_lines(decode_unicode=True):
                    if line.startswith("event:"):
                        event_type = line[len("event:"):].strip()
                    elif line.startswith("data:"):
                        try:
                            data_json = json.loads(line[len("data:"):].strip())
                            text_chunk = data_json.get("text", "")
                            
                            if event_type == "token":
                                raw_buffer.append(text_chunk)
                                placeholder.markdown("".join(raw_buffer) + "▌")
                            
                            elif event_type == "final_response":
                                final_text = text_chunk
                                placeholder.markdown(final_text) # Replace stream with final version

                        except json.JSONDecodeError:
                            continue # Ignore empty or malformed data lines
                
                # Fallback if stream ends without a 'final_response' event
                if not final_text:
                    final_text = "".join(raw_buffer)
                    placeholder.markdown(final_text)

            elapsed_time = time.time() - start_time
            st.session_state.history.append({
                "role": "assistant", "text": final_text, "source": source, "time": elapsed_time
            })
            st.rerun() # Rerun to properly display the final caption

## -----------------------------
## Tab 2: Documents 📚
## -----------------------------
with tab2:
    st.header("Document Management")
    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader("Upload Documents")
        uploaded_files = st.file_uploader("Select files (PDF, TXT, DOCX, MD)", accept_multiple_files=True, type=["pdf", "txt", "docx", "md"])
        if st.button("Process Documents"):
            if uploaded_files:
                files_payload = [("files", (f.name, f.getvalue(), f.type)) for f in uploaded_files]
                resp = api_request("upload", method="POST", files=files_payload)
                if resp and resp.status_code == 200:
                    st.success(resp.json().get("message", "Upload successful!"))
                else:
                    st.error(f"Upload failed: {resp.text if resp else 'No response'}")
            else:
                st.warning("Please select files to upload.")
    with col2:
        st.subheader("Database Status & Raw Files")
        stats_resp = api_request("db_stats", method="GET")
        if stats_resp and stats_resp.status_code == 200:
            info = stats_resp.json()
            st.json(info.get("vector_db", {}))
            raw_files = info.get("raw_files", [])
            
            for filename in raw_files:
                if st.session_state.get("file_to_delete") == filename:
                    st.warning(f"Delete `{filename}` and all its indexed data?")
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, Delete It", key=f"confirm_del_{filename}", type="primary"):
                        del_resp = api_request("raw_docs", method="DELETE", params={"filename": filename})
                        if del_resp and del_resp.status_code == 200:
                            st.success(f"Deleted {filename}")
                        else:
                            st.error(f"Failed to delete {filename}: {del_resp.text if del_resp else 'No response'}")
                        st.session_state.file_to_delete = None
                        st.rerun()
                    if c2.button("Cancel", key=f"cancel_del_{filename}"):
                        st.session_state.file_to_delete = None
                        st.rerun()
                else:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"- `{filename}`")
                    if c2.button("Delete", key=f"del_{filename}"):
                        st.session_state.file_to_delete = filename
                        st.rerun()
        else:
            st.error("Failed to get document stats.")

## -----------------------------
## Tab 3: Knowledge Base 🧠
## -----------------------------
with tab3:
    st.header("Knowledge Base Management")
    with st.expander("➕ Add New Q&A Pair", expanded=True):
        question = st.text_area("Question", key="kb_q")
        answer = st.text_area("Answer", key="kb_a")
        tags = st.text_input("Tags (comma separated)", key="kb_t")
        if st.button("Add to Knowledge Base"):
            if question and answer:
                add_resp = api_request("add_knowledge", method="POST", data={"question": question, "answer": answer, "tags": tags})
                if add_resp and add_resp.status_code == 200:
                    st.success("Knowledge added!")
                else:
                    st.error("Failed to add knowledge.")
            else:
                st.warning("Question and Answer fields are required.")
    
    st.divider()
    st.subheader("Existing Q&A Pairs")
    kb_resp = api_request("knowledge", method="GET")
    if kb_resp and kb_resp.status_code == 200:
        items = kb_resp.json()
        for item in items:
            with st.expander(item.get("question", "No Question")):
                st.write(item.get("answer", "No Answer"))
                st.caption(f"Tags: {item.get('tags', 'None')}")
                item_id = item.get('id')
                if st.session_state.get("kb_to_delete") == item_id:
                    st.warning("Are you sure you want to delete this Q&A pair?")
                    c1, c2 = st.columns(2)
                    if c1.button("Yes, Delete", key=f"confirm_del_kb_{item_id}", type="primary"):
                        del_resp = api_request(f"knowledge/{item_id}", method="DELETE")
                        if del_resp and del_resp.status_code == 200:
                            st.success("Deleted successfully!")
                        else:
                            st.error("Failed to delete knowledge.")
                        st.session_state.kb_to_delete = None
                        st.rerun()
                    if c2.button("Cancel", key=f"cancel_del_kb_{item_id}"):
                        st.session_state.kb_to_delete = None
                        st.rerun()
                else:
                    if st.button("Delete Entry", key=f"del_kb_{item_id}"):
                        st.session_state.kb_to_delete = item_id
                        st.rerun()
    else:
        st.warning("Could not fetch knowledge base.")

## -----------------------------
## Tab 4: Admin ⚙️
## -----------------------------
with tab4:
    st.header("Admin Tools")
    st.subheader("Danger Zone")
    st.warning("These actions are irreversible and will delete data from the vector database.")
    if st.button("Reset Document Database", type="primary"):
        reset_resp = api_request("reset_db", method="POST")
        if reset_resp and reset_resp.status_code == 200:
            st.success("Database reset successfully! All document vectors have been cleared and re-indexed.")
        else:
            st.error(f"Failed to reset database: {reset_resp.text if reset_resp else 'No response'}")

st.markdown("---")
st.caption("© 2025 MITAOE AI Assistant")