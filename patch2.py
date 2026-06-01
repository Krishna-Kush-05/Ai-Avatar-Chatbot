frontend_file = r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\app.py'
with open(frontend_file, 'r', encoding='utf-8') as f:
    content = f.read()

# Fix 798 (stream=True)
content = content.replace(
    '''            with requests.post(
                BASE_FASTAPI_URL + "/query",
                json={"question": question, "workspace_id": workspace_id},
                stream=True,
                timeout=120''',
    '''            with requests.post(
                BASE_FASTAPI_URL + "/query",
                json={"question": question, "workspace_id": workspace_id},
                stream=True,
                headers=FASTAPI_HEADERS, timeout=120'''
)

# Fix 885 (f-string)
content = content.replace(
    '''        resp = requests.delete(
            f"{BASE_FASTAPI_URL}/delete_knowledge/{kid}",
            timeout=30''',
    '''        resp = requests.delete(
            f"{BASE_FASTAPI_URL}/delete_knowledge/{kid}",
            headers=FASTAPI_HEADERS, timeout=30'''
)

with open(frontend_file, 'w', encoding='utf-8') as f:
    f.write(content)
