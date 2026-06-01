import requests
import json
import base64
import os
import sys
from dotenv import load_dotenv

env_path = os.path.join("Backend", ".env")
load_dotenv(env_path)

API_KEY = os.getenv("FASTAPI_API_KEY", "super-secret-dev-key")
BASE_URL = "http://127.0.0.1:8000"
WORKSPACE = "test_ws_unique"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def run_tests():
    print("=== RAG INTEGRATION VERIFICATION ===")
    
    # 1. Add Knowledge Base Entry
    print("\n[Setup] Adding KB entry...")
    requests.post(f"{BASE_URL}/add_knowledge", headers=HEADERS, json={
        "workspace_id": WORKSPACE,
        "question": "What is the capital of Mars?",
        "answer": "New Mars City."
    })
    
    # 2. Add ChromaDB Entry
    print("[Setup] Uploading ChromaDB document...")
    with open("mars_lore.txt", "w", encoding="utf-8") as f:
        f.write("According to the official sci-fi universe, the capital of Mars is actually called Mars Prime.")
    
    with open("mars_lore.txt", "rb") as f:
        requests.post(f"{BASE_URL}/upload", headers=HEADERS, data={"workspace_id": WORKSPACE}, files={"files": ("mars_lore.txt", f, "text/plain")})
    
    # Run tests using /query_eval
    
    # Test 1: Exact Match
    print("\n--- TEST 1: Exact-match KB query ---")
    q1 = "what is the capital of mars?"
    print(f"Question: {q1}")
    r1 = requests.post(f"{BASE_URL}/query_eval", headers=HEADERS, json={"workspace_id": WORKSPACE, "question": q1}).json()
    print(f"Source: {r1.get('source')}")
    print(f"Expected: knowledge_base -> {'PASS' if r1.get('source') == 'knowledge_base' else 'FAIL'}")

    # Test 2: Similar KB query
    print("\n--- TEST 2: Similar KB query ---")
    q2 = "what is the capital of the red planet?"
    print(f"Question: {q2}")
    r2 = requests.post(f"{BASE_URL}/query_eval", headers=HEADERS, json={"workspace_id": WORKSPACE, "question": q2}).json()
    context2 = r2.get('contexts', [""])[0] if r2.get('contexts') else ""
    print(f"Source: {r2.get('source')}")
    has_kb = "New Mars City." in context2
    print(f"KB context included? {'YES' if has_kb else 'NO'} -> {'PASS' if has_kb else 'FAIL'}")

    # Test 3: Chroma-only query
    print("\n--- TEST 3: Chroma-only query ---")
    q3 = "what is the name of the capital in the sci-fi universe?"
    print(f"Question: {q3}")
    r3 = requests.post(f"{BASE_URL}/query_eval", headers=HEADERS, json={"workspace_id": WORKSPACE, "question": q3}).json()
    context3 = r3.get('contexts', [""])[0] if r3.get('contexts') else ""
    print(f"Source: {r3.get('source')}")
    has_chroma = "Mars Prime" in context3
    print(f"Chroma document included? {'YES' if has_chroma else 'NO'} -> {'PASS' if has_chroma else 'FAIL'}")

    # Test 4: Mixed query
    print("\n--- TEST 4: Mixed query ---")
    q4 = "what are the various names for the capital of the red planet?"
    print(f"Question: {q4}")
    r4 = requests.post(f"{BASE_URL}/query_eval", headers=HEADERS, json={"workspace_id": WORKSPACE, "question": q4}).json()
    context4 = r4.get('contexts', [""])[0] if r4.get('contexts') else ""
    print(f"Source: {r4.get('source')}")
    has_kb_mixed = "New Mars City." in context4
    has_chroma_mixed = "Mars Prime" in context4
    print(f"KB included? {'YES' if has_kb_mixed else 'NO'}")
    print(f"Chroma included? {'YES' if has_chroma_mixed else 'NO'}")
    print(f"Mixed Context successfully generated? {'YES' if (has_kb_mixed and has_chroma_mixed) else 'NO'} -> {'PASS' if (has_kb_mixed and has_chroma_mixed) else 'FAIL'}")
    
    print("\n--- FINAL CONTEXT ASSEMBLY PREVIEW (Query 4) ---")
    print(context4[:400] + ("..." if len(context4) > 400 else ""))
    print(f"Final Context Length: {len(context4)} characters")

    # Cleanup
    print("\n[Teardown] Cleaning up...")
    kb_list = requests.get(f"{BASE_URL}/knowledge", headers=HEADERS, params={"workspace_id": WORKSPACE}).json()
    for kb in kb_list:
        if kb.get('answer') == "New Mars City.":
            requests.delete(f"{BASE_URL}/delete_knowledge/{kb['id']}", headers=HEADERS, params={"workspace_id": WORKSPACE})
            
    requests.delete(f"{BASE_URL}/raw_docs", headers=HEADERS, params={"workspace_id": WORKSPACE, "filename": "mars_lore.txt"})
    if os.path.exists("mars_lore.txt"): os.remove("mars_lore.txt")
    print("Done.")

if __name__ == "__main__":
    run_tests()
