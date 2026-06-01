import re

file_path = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Payload
payload_pattern = r'(workspace_id = payload\.get\("workspace_id", "default"\))'
payload_repl = '''workspace_id = payload.get("workspace_id")
    if not workspace_id or workspace_id == "default":
        raise HTTPException(400, "workspace_id (chatbot_id) is strictly required")'''
content = re.sub(payload_pattern, payload_repl, content)

# 2. Ingest Data
data_pattern = r'(workspace_id = data\.get\("workspace_id", "default"\))'
data_repl = '''workspace_id = data.get("workspace_id")
    if not workspace_id or workspace_id == "default":
        return {"error": "workspace_id (chatbot_id) is strictly required"}'''
content = re.sub(data_pattern, data_repl, content)

# 3. Form and Query params
content = content.replace('workspace_id: str = Form("default")', 'workspace_id: str = Form(...)')
content = content.replace('workspace_id: str = Query("default")', 'workspace_id: str = Query(...)')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
