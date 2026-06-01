import re

# 1. Update embeddings.py to have try/except
emb_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\utils\embeddings.py'
with open(emb_file, 'r', encoding='utf-8') as f:
    emb_content = f.read()

emb_content = emb_content.replace('''                from langchain_huggingface import HuggingFaceEmbeddings
                self._doc_model = HuggingFaceEmbeddings(
                    model_name="BAAI/bge-base-en-v1.5"
                )''', '''                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                    self._doc_model = HuggingFaceEmbeddings(
                        model_name="BAAI/bge-base-en-v1.5"
                    )
                except Exception as e:
                    raise RuntimeError(f"Document embedding model failed to load: {e}")''')

emb_content = emb_content.replace('''                from sentence_transformers import SentenceTransformer
                self._qa_model = SentenceTransformer("all-MiniLM-L6-v2")''', '''                try:
                    from sentence_transformers import SentenceTransformer
                    self._qa_model = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception as e:
                    raise RuntimeError(f"QA embedding model failed to load: {e}")''')

with open(emb_file, 'w', encoding='utf-8') as f:
    f.write(emb_content)

# 2. Update db_manager.py
db_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\utils\db_manager.py'
with open(db_file, 'r', encoding='utf-8') as f:
    db_content = f.read()

db_content = db_content.replace('self.embedding_function = embedding_manager.get_document_embedding_model()', 'self._embedding_model_name = "BAAI/bge-base-en-v1.5 (lazy loaded)"')

new_get_col = '''    def _get_embedding_function(self):
        try:
            return embedding_manager.get_document_embedding_model()
        except Exception as e:
            raise ValueError(f"Embedding model unavailable: {str(e)}")

    def _get_collection(self, workspace_id: str):'''

db_content = db_content.replace('    def _get_collection(self, workspace_id: str):', new_get_col)

db_content = db_content.replace('embedding_function=self.embedding_function', 'embedding_function=self._get_embedding_function()')
db_content = db_content.replace('self.embedding_function.model_name', 'self._embedding_model_name')

with open(db_file, 'w', encoding='utf-8') as f:
    f.write(db_content)

# 3. Update kb_manager.py
kb_file = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\utils\kb_manager.py'
with open(kb_file, 'r', encoding='utf-8') as f:
    kb_content = f.read()

kb_content = kb_content.replace('self.model = embedding_manager.get_qa_embedding_model()', 'self._cache_built = False')

# Delay _build_cache call in __init__
kb_content = kb_content.replace('self._build_cache()', '# self._build_cache() deferred to lazy load')

new_ensure = '''    def _get_model(self):
        try:
            return embedding_manager.get_qa_embedding_model()
        except Exception as e:
            raise ValueError(f"QA embedding model unavailable: {str(e)}")

    def _ensure_cache(self):
        if not self._cache_built:
            self._build_cache()
            self._cache_built = True

    def _build_cache(self):'''

kb_content = kb_content.replace('    def _build_cache(self):', new_ensure)
kb_content = kb_content.replace('self.model.encode(', 'self._get_model().encode(')

# Inject _ensure_cache() to all public read/write methods
kb_content = kb_content.replace('def add_qa_pair(self, workspace_id: str, q: str, a: str, tags: Optional[str]):', 'def add_qa_pair(self, workspace_id: str, q: str, a: str, tags: Optional[str]):\n        self._ensure_cache()')
kb_content = kb_content.replace('def get_best_answer(self, workspace_id: str, question: str):', 'def get_best_answer(self, workspace_id: str, question: str):\n        self._ensure_cache()')
kb_content = kb_content.replace('def delete_qa_pair(self, qa_id: int, workspace_id: str):', 'def delete_qa_pair(self, qa_id: int, workspace_id: str):\n        self._ensure_cache()')
kb_content = kb_content.replace('def reset_knowledge_base(self, workspace_id: str):', 'def reset_knowledge_base(self, workspace_id: str):\n        self._ensure_cache()')

# Inside reset_knowledge_base and delete_qa_pair, it used to call self._build_cache(). 
# But the first regex '# self._build_cache() deferred to lazy load' replaced it globally. 
# We need to revert it back for the methods that actually *need* to rebuild the cache after writes.
kb_content = kb_content.replace('        # self._build_cache() deferred to lazy load\n', '        self._build_cache()\n')
# Now make sure the __init__ ONE is the only one commented out.
# Wait, let's just explicitly fix __init__
init_pattern = r'(def __init__.*?)(self\._build_cache\(\))'
kb_content = re.sub(init_pattern, r'\1# self._build_cache() deferred to lazy load', kb_content, flags=re.DOTALL)

with open(kb_file, 'w', encoding='utf-8') as f:
    f.write(kb_content)
