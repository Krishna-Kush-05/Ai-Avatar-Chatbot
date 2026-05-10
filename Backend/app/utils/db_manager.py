# app/utils/db_manager.py
import os
import shutil
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma


class ChromaDBManager:

    def __init__(self, persist_directory: str = "./data/chroma_db", collection_name: str = "document_chunks"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        os.makedirs(self.persist_directory, exist_ok=True)

        self.embedding_function = HuggingFaceEmbeddings(
            model_name="BAAI/bge-base-en-v1.5"

        )

        self.vectordb = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
            collection_name=self.collection_name
        )

    def add_documents(self, docs: List[Document], workspace_id: str = "default"):
        if not docs:
            return

        for d in docs:
            if not d.metadata:
                d.metadata = {}
            d.metadata["workspace_id"] = workspace_id

        print(f"Adding {len(docs)} documents to workspace {workspace_id}")
        self.vectordb.add_documents(docs)

    def similarity_search(self, query: str, workspace_id: str = "default", top_k: int = 4):
        return self.vectordb.similarity_search(
            query,
            k=top_k,
            filter={"workspace_id": workspace_id}
        )

    def delete_documents_by_source(self, source_path: str, workspace_id: str = "default"):
        """Delete all chunks belonging to a specific source file in a workspace."""
        try:
            count = self.vectordb._collection.count()
            if not count:
                return

            docs_with_metadata = self.vectordb.get(
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
                self.vectordb.delete(ids=ids_to_delete)
        except Exception as e:
            print(f"Warning: delete_documents_by_source error: {e}")

    def clear_workspace(self, workspace_id: str = "default"):
        """Delete all chunks belonging to a specific workspace (for reset)."""
        try:
            count = self.vectordb._collection.count()
            if not count:
                return

            docs = self.vectordb.get(
                where={"workspace_id": {"$eq": workspace_id}}
            )
            ids_to_delete = docs.get("ids", [])
            if ids_to_delete:
                print(f"Clearing {len(ids_to_delete)} chunks for workspace: {workspace_id}")
                self.vectordb.delete(ids=ids_to_delete)
        except Exception as e:
            print(f"Warning: clear_workspace error: {e}")

    def clear_database(self):
        """Nuke the entire chroma DB (admin use only)."""
        print(f"Clearing entire collection '{self.collection_name}'")
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        self.__init__(self.persist_directory, self.collection_name)

    def count_unique_sources(self, workspace_id: str = "default") -> int:
        """
        FIX: Returns the number of unique source documents (files) in a workspace,
        NOT the total chunk count. This fixes the confusing Documents == Chunks stat.
        """
        try:
            count = self.vectordb._collection.count()
            if not count:
                return 0

            docs = self.vectordb.get(
                where={"workspace_id": {"$eq": workspace_id}},
                include=["metadatas"]
            )
            metadatas = docs.get("metadatas", [])
            # Extract unique source paths
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
            count = self.vectordb._collection.count()
            return {
                "collections": 1,
                "total_documents": count,
                "indexed_chunks": count,
                "model": self.embedding_function.model_name
            }
        except Exception:
            return {
                "collections": 1,
                "total_documents": 0,
                "indexed_chunks": 0,
                "model": self.embedding_function.model_name
            }
