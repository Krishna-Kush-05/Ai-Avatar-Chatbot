import re
import os

file_path = r'd:\Git Desk\Ai-Avatar-Chatbot\backend\app\utils\db_manager.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace ChromaDBManager class methods

new_class = '''class ChromaDBManager:

    def __init__(self, persist_directory: str = "./data/chroma_db"):
        self.persist_directory = persist_directory
        import os
        os.makedirs(self.persist_directory, exist_ok=True)

        self.embedding_function = HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-en-v1.5"
        )
        self._collections = {}

    def _get_collection(self, workspace_id: str):
        if not workspace_id:
            workspace_id = "default"
        # Chroma collection names must be valid: alphanumeric, underscores, hyphens, 3-63 chars
        import re
        safe_name = re.sub(r'[^a-zA-Z0-9_-]', '_', workspace_id)
        if len(safe_name) < 3:
            safe_name = safe_name + "_col"
        safe_name = safe_name[:63]
        
        if safe_name not in self._collections:
            self._collections[safe_name] = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embedding_function,
                collection_name=safe_name
            )
        return self._collections[safe_name]

    def add_documents(self, docs: List[Document], workspace_id: str = "default"):
        if not docs:
            return

        for d in docs:
            if not d.metadata:
                d.metadata = {}
            d.metadata["workspace_id"] = workspace_id

        print(f"Adding {len(docs)} documents to workspace {workspace_id}")
        db = self._get_collection(workspace_id)
        db.add_documents(docs)

    def similarity_search(self, query: str, workspace_id: str = "default", top_k: int = 4):
        db = self._get_collection(workspace_id)
        return db.similarity_search(
            query,
            k=top_k,
            filter={"workspace_id": workspace_id}
        )

    def delete_documents_by_source(self, source_path: str, workspace_id: str = "default"):
        try:
            db = self._get_collection(workspace_id)
            count = db._collection.count()
            if not count:
                return

            docs_with_metadata = db.get(
                where={
                    "$and": [
                        {"source": {"$eq": source_path}},
                        {"workspace_id": {"$eq": workspace_id}}
                    ]
                }
            )

            ids_to_delete = docs_with_metadata.get("ids", [])
            if ids_to_delete:
                print(f"Deleting {len(ids_to_delete)} chunks for source: {source_path}")
                db.delete(ids=ids_to_delete)
        except Exception as e:
            print(f"Warning: delete_documents_by_source error: {e}")

    def clear_workspace(self, workspace_id: str = "default"):
        try:
            db = self._get_collection(workspace_id)
            count = db._collection.count()
            if not count:
                return

            docs = db.get(
                where={"workspace_id": {"$eq": workspace_id}}
            )
            ids_to_delete = docs.get("ids", [])
            if ids_to_delete:
                print(f"Clearing {len(ids_to_delete)} chunks for workspace: {workspace_id}")
                db.delete(ids=ids_to_delete)
        except Exception as e:
            print(f"Warning: clear_workspace error: {e}")

    def clear_database(self):
        print(f"Clearing entire chroma DB")
        import shutil
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        self._collections = {}

    def count_unique_sources(self, workspace_id: str = "default") -> int:
        try:
            db = self._get_collection(workspace_id)
            count = db._collection.count()
            if not count:
                return 0

            docs = db.get(
                where={"workspace_id": {"$eq": workspace_id}},
                include=["metadatas"]
            )
            metadatas = docs.get("metadatas", [])
            sources = set()
            for meta in metadatas:
                if meta and "source" in meta:
                    sources.add(meta["source"])
            return len(sources)
        except Exception as e:
            print(f"Warning: count_unique_sources error: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        try:
            # We will just return the stats of the first loaded collection or zeros if none
            total_docs = sum([db._collection.count() for db in self._collections.values()])
            return {
                "collections": len(self._collections) or 1,
                "total_documents": total_docs,
                "indexed_chunks": total_docs,
                "model": self.embedding_function.model_name
            }
        except Exception:
            return {
                "collections": 1,
                "total_documents": 0,
                "indexed_chunks": 0,
                "model": self.embedding_function.model_name
            }
'''

# Replace from 'class ChromaDBManager:' to end of file
content = re.sub(r'class ChromaDBManager:.*', new_class, content, flags=re.DOTALL)
# Make sure we add import re at the top if not present
if 'import re' not in content:
    content = 'import re\n' + content

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
