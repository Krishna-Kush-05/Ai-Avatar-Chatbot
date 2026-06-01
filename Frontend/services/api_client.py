import os
import requests

BASE_FASTAPI_URL = os.environ.get("BASE_FASTAPI_URL", "http://127.0.0.1:8000")
FASTAPI_API_KEY = os.environ.get("FASTAPI_API_KEY")

if not FASTAPI_API_KEY:
    raise RuntimeError("FASTAPI_API_KEY environment variable is missing and is strictly required.")

def _get_headers():
    return {
        "Authorization": f"Bearer {FASTAPI_API_KEY}"
    }

def upload_files(files, workspace_id: str):
    return requests.post(
        f"{BASE_FASTAPI_URL}/upload",
        files=files,
        data={"workspace_id": workspace_id},
        headers=_get_headers(),
        timeout=120
    )

def delete_raw_doc(filename: str, workspace_id: str):
    return requests.delete(
        f"{BASE_FASTAPI_URL}/raw_docs",
        params={"filename": filename, "workspace_id": workspace_id},
        headers=_get_headers(),
        timeout=30
    )

def reset_db(workspace_id: str):
    return requests.post(
        f"{BASE_FASTAPI_URL}/reset_db",
        params={"workspace_id": workspace_id},
        headers=_get_headers(),
        timeout=30
    )

def ingest_website(url: str, workspace_id: str):
    return requests.post(
        f"{BASE_FASTAPI_URL}/ingest/website",
        json={"url": url, "workspace_id": workspace_id},
        headers=_get_headers(),
        timeout=30
    )

def get_db_stats(workspace_id: str):
    return requests.get(
        f"{BASE_FASTAPI_URL}/db_stats",
        params={"workspace_id": workspace_id},
        headers=_get_headers(),
        timeout=30
    )

def send_query(payload: dict):
    return requests.post(
        f"{BASE_FASTAPI_URL}/query",
        json=payload,
        stream=True,
        headers=_get_headers(),
        timeout=120
    )

def get_knowledge(workspace_id: str):
    return requests.get(
        f"{BASE_FASTAPI_URL}/knowledge",
        params={"workspace_id": workspace_id},
        headers=_get_headers(),
        timeout=30
    )

def add_knowledge(data: dict):
    return requests.post(
        f"{BASE_FASTAPI_URL}/add_knowledge",
        json=data,
        headers=_get_headers(),
        timeout=30
    )

def delete_knowledge(kid: str, workspace_id: str):
    return requests.delete(
        f"{BASE_FASTAPI_URL}/delete_knowledge/{kid}",
        params={"workspace_id": workspace_id},
        headers=_get_headers(),
        timeout=30
    )
