file_path = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\main.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace my overly strict check with a proper presence check
content = content.replace('if not workspace_id or workspace_id == "default":', 'if not workspace_id:')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
