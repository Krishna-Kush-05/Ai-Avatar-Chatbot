import re

# Update db_manager.py
db_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\utils\db_manager.py'
with open(db_file, 'r', encoding='utf-8') as f:
    db_content = f.read()

# Add import
if 'from app.utils.embeddings import embedding_manager' not in db_content:
    db_content = 'from app.utils.embeddings import embedding_manager\n' + db_content

# Replace instantiation
old_db_embed = '''self.embedding_function = HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-en-v1.5"
        )'''
new_db_embed = '''self.embedding_function = embedding_manager.get_document_embedding_model()'''
db_content = db_content.replace(old_db_embed, new_db_embed)

with open(db_file, 'w', encoding='utf-8') as f:
    f.write(db_content)

# Update kb_manager.py
kb_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\utils\kb_manager.py'
with open(kb_file, 'r', encoding='utf-8') as f:
    kb_content = f.read()

# Add import
if 'from app.utils.embeddings import embedding_manager' not in kb_content:
    kb_content = 'from app.utils.embeddings import embedding_manager\n' + kb_content

# Replace instantiation
old_kb_embed = 'self.model = SentenceTransformer("all-MiniLM-L6-v2")'
new_kb_embed = 'self.model = embedding_manager.get_qa_embedding_model()'
kb_content = kb_content.replace(old_kb_embed, new_kb_embed)

with open(kb_file, 'w', encoding='utf-8') as f:
    f.write(kb_content)
