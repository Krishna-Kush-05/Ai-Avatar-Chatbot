import re

kb_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\utils\kb_manager.py'
with open(kb_file, 'r', encoding='utf-8') as f:
    kb_content = f.read()

kb_content = kb_content.replace('def delete_qa_pair(self, qa_id: int):', 'def delete_qa_pair(self, qa_id: int, workspace_id: str):')
kb_content = kb_content.replace('conn.execute("DELETE FROM qa_pairs WHERE id = ?", (qa_id,))', 'conn.execute("DELETE FROM qa_pairs WHERE id = ? AND workspace_id = ?", (qa_id, workspace_id))')

with open(kb_file, 'w', encoding='utf-8') as f:
    f.write(kb_content)

main_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\main.py'
with open(main_file, 'r', encoding='utf-8') as f:
    main_content = f.read()

main_content = main_content.replace('async def delete_knowledge(qa_id: int, api_key: str = Depends(verify_api_key)):', 'async def delete_knowledge(qa_id: int, workspace_id: str = Query(...), api_key: str = Depends(verify_api_key)):')
main_content = main_content.replace('knowledge_db.delete_qa_pair(qa_id)', 'knowledge_db.delete_qa_pair(qa_id, workspace_id)')

main_content = main_content.replace('async def delete_kb(id: int, api_key: str = Depends(verify_api_key)):', 'async def delete_kb(id: int, workspace_id: str = Query(...), api_key: str = Depends(verify_api_key)):')
main_content = main_content.replace('knowledge_db.delete_qa_pair(id)', 'knowledge_db.delete_qa_pair(id, workspace_id)')

with open(main_file, 'w', encoding='utf-8') as f:
    f.write(main_content)

frontend_file = r'd:\Git Desk\Ai-Avatar-Chatbot\Frontend\app.py'
with open(frontend_file, 'r', encoding='utf-8') as f:
    front_content = f.read()

frontend_repl = '''def api_delete_knowledge(kid):
    """Proxy: delete a Q&A pair → FastAPI DELETE /knowledge/<id>."""
    workspace_id = _get_workspace_id()
    try:
        resp = requests.delete(
            f"{BASE_FASTAPI_URL}/delete_knowledge/{kid}",
            params={"workspace_id": workspace_id},'''

front_content = re.sub(r'def api_delete_knowledge\(kid\):\n.*?try:\n.*?resp = requests\.delete\(\n.*?f"\{BASE_FASTAPI_URL\}/delete_knowledge/\{kid\}",', frontend_repl, front_content, flags=re.DOTALL)

with open(frontend_file, 'w', encoding='utf-8') as f:
    f.write(front_content)
