import requests
import json
import base64
import os
import sys
from dotenv import load_dotenv

# Use os.path.join or raw strings carefully
env_path = os.path.join("backend", ".env")
load_dotenv(env_path)

API_KEY = os.getenv("FASTAPI_API_KEY", "super-secret-dev-key")
BASE_URL = "http://127.0.0.1:8000"
WORKSPACE = "test_ws"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# A valid minimal PDF (1 page, text)
MINIMAL_PDF_B64 = b'JVBERi0xLjQKJcOkw7zDtsOfCjIgMCBvYmoKPDwvTGVuZ3RoIDMgMCBSPj4Kc3RyZWFtCkJUCjEvRm50MSAtdGhpcyBpcyBhIHRlc3QKRVQKZW5kc3RyZWFtCmVuZG9iagozIDAgb2JqCjMzCmVuZG9iago0IDAgb2JqCjw8L1R5cGUgL1BhZ2UKL01lZGlhQm94IFswIDAgNjEyIDc5Ml0KL1Jlc291cmNlcyA8PC9Gb250IDw8L0ZudDEgMSAwIFI+Pj4+Ci9Db250ZW50cyAyIDAgUgovUGFyZW50IDUgMCBSCj4+CmVuZG9iago1IDAgb2JqCjw8L1R5cGUgL1BhZ2VzCi9LaWRzIFs0IDAgUl0KL0NvdW50IDEKPj4KZW5kb2JqCjEgMCBvYmoKPDwvVHlwZSAvRm9udAovU3VidHlwZSAvVHlwZTEKL0Jhc2VGb250IC9IZWx2ZXRpY2EKPj4KZW5kb2JqCjYgMCBvYmoKPDwvVHlwZSAvQ2F0YWxvZwovUGFnZXMgNSAwIFIKPj4KZW5kb2JqCjcgMCBvYmoKPDwvUHJvZHVjZXIgKE1pbmltYWwgUERGKQovQ3JlYXRvciAoTWluaW1hbCBQREYpCj4+CmVuZG9iagp4cmVmCjAgOAowMDAwMDAwMDAwIDY1NTM1IGYgCjAwMDAwMDAyOTUgMDAwMDAgbiAKMDAwMDAwMDAxNSAwMDAwMCBuIAowMDAwMDAwMTAxIDAwMDAwIG4gCjAwMDAwMDAxMjIgMDAwMDAgbiAKMDAwMDAwMDIzNyAwMDAwMCBuIAowMDAwMDAwMzg3IDAwMDAwIG4gCjAwMDAwMDA0NDAgMDAwMDAgbiAKdHJhaWxlcgo8PC9TaXplIDgKL1Jvb3QgNiAwIFIKL0luZm8gNyAwIFIKPj4Kc3RhcnR4cmVmCjUxMQolJUVPRgo='

def test_endpoint(name, func):
    print(f"Testing {name} ... ", end="")
    try:
        success = func()
        if success:
            print("[PASS]")
            return True
        else:
            print("[FAIL]")
            return False
    except Exception as e:
        print(f"[FAIL] - Uncaught Exception: {e}")
        return False

def run_tests():
    all_passed = True
    
    # Generate test files
    with open("test.txt", "w", encoding="utf-8") as f:
        f.write("This is a valid text file for regression testing.")
        
    with open("test.pdf", "wb") as f:
        f.write(base64.b64decode(MINIMAL_PDF_B64))

    # 1. /upload (txt & pdf)
    def test_upload():
        with open("test.txt", "rb") as f:
            resp = requests.post(f"{BASE_URL}/upload", headers=HEADERS, data={"workspace_id": WORKSPACE}, files={"files": ("test.txt", f, "text/plain")})
            if resp.status_code >= 400:
                print(f"TXT upload failed ({resp.status_code}): {resp.text} ", end="")
                return False
        
        with open("test.pdf", "rb") as f:
            resp = requests.post(f"{BASE_URL}/upload", headers=HEADERS, data={"workspace_id": WORKSPACE}, files={"files": ("test.pdf", f, "application/pdf")})
            if resp.status_code >= 400:
                print(f"PDF upload failed ({resp.status_code}): {resp.text} ", end="")
                return False
        return True
    
    all_passed &= test_endpoint("/upload", test_upload)

    # 2. /query
    def test_query():
        resp = requests.post(f"{BASE_URL}/query", headers=HEADERS, json={"question": "Hello", "workspace_id": WORKSPACE}, stream=True)
        if resp.status_code >= 400:
            return False
        return True
    
    all_passed &= test_endpoint("/query", test_query)

    # 3. /add_knowledge
    def test_add_knowledge():
        resp = requests.post(f"{BASE_URL}/add_knowledge", headers=HEADERS, json={"workspace_id": WORKSPACE, "question": "What is AI?", "answer": "Artificial Intelligence."})
        if resp.status_code >= 400:
            return False
        return True

    all_passed &= test_endpoint("/add_knowledge", test_add_knowledge)

    # 4. /knowledge (list)
    def test_list_knowledge():
        resp = requests.get(f"{BASE_URL}/knowledge", headers=HEADERS, params={"workspace_id": WORKSPACE})
        if resp.status_code >= 400:
            return False
        if not isinstance(resp.json(), list):
            return False
        return True

    all_passed &= test_endpoint("/knowledge (list)", test_list_knowledge)

    # 5. /db_stats
    def test_db_stats():
        resp = requests.get(f"{BASE_URL}/db_stats", headers=HEADERS, params={"workspace_id": WORKSPACE})
        if resp.status_code >= 400:
            return False
        return True

    all_passed &= test_endpoint("/db_stats", test_db_stats)

    # 6. /knowledge (delete)
    def test_delete_knowledge():
        list_resp = requests.get(f"{BASE_URL}/knowledge", headers=HEADERS, params={"workspace_id": WORKSPACE})
        data = list_resp.json()
        if not data:
            print("Skipped (no ID) ", end="")
            return False
        q_id = data[0].get('id')
        resp = requests.delete(f"{BASE_URL}/knowledge/{q_id}", headers=HEADERS, params={"workspace_id": WORKSPACE})
        if resp.status_code >= 400:
            return False
        return True

    all_passed &= test_endpoint("/knowledge (delete)", test_delete_knowledge)

    # 7. /raw_docs (delete txt & pdf)
    def test_raw_docs_delete():
        resp1 = requests.delete(f"{BASE_URL}/raw_docs", headers=HEADERS, params={"filename": "test.txt", "workspace_id": WORKSPACE})
        if resp1.status_code >= 400:
            return False
        resp2 = requests.delete(f"{BASE_URL}/raw_docs", headers=HEADERS, params={"filename": "test.pdf", "workspace_id": WORKSPACE})
        if resp2.status_code >= 400:
            return False
        return True

    all_passed &= test_endpoint("/raw_docs delete", test_raw_docs_delete)

    # Cleanup
    if os.path.exists("test.txt"): os.remove("test.txt")
    if os.path.exists("test.pdf"): os.remove("test.pdf")

    print("\nOVERALL STATUS:", "PASS" if all_passed else "FAIL")
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    run_tests()
