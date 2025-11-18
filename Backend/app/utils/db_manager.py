# app/utils/db_manager.py
import os
import shutil
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

class ChromaDBManager:
    def __init__(self, persist_directory: str = "./data/chroma_db", collection_name: str = "document_chunks"):
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        
        self.vectordb = Chroma(
            persist_directory=self.persist_directory,
            embedding_function=self.embedding_function,
            collection_name=self.collection_name
        )

    def add_documents(self, docs: List[Document]):
        """Add a list of Document objects to the vector DB."""
        if not docs:
            return
        print(f"Adding {len(docs)} documents to vector DB...")
        self.vectordb.add_documents(docs)
        print("Documents added and persisted.")

    def similarity_search(self, query: str, top_k: int = 4) -> List[Document]:
        """Return top-k similar documents for a given query."""
        return self.vectordb.similarity_search(query, k=top_k)

    def delete_documents_by_source(self, source_path: str):
        """Deletes all vector chunks associated with a specific source file path."""
        if not self.vectordb._collection.count():
             return

        docs_with_metadata = self.vectordb.get(where={"source": source_path})
        
        ids_to_delete = docs_with_metadata.get("ids")
        if ids_to_delete:
            print(f"Deleting {len(ids_to_delete)} chunks for source: {source_path}")
            self.vectordb.delete(ids=ids_to_delete)
            print("Deletion complete.")
        else:
            print(f"No chunks found for source: {source_path}")


    def clear_database(self):
        """
        Clears the persisted database directory and re-initializes an empty Chroma instance.
        """
        print(f"Clearing all documents and deleting directory for collection '{self.collection_name}'...")
        if os.path.exists(self.persist_directory):
            shutil.rmtree(self.persist_directory)
        os.makedirs(self.persist_directory, exist_ok=True)
        
        self.__init__(self.persist_directory, self.collection_name)
        print("Database cleared and re-initialized.")

    def get_stats(self) -> Dict[str, Any]:
        """Returns stats about the vector store."""
        try:
            count = self.vectordb._collection.count()
            return {
                "collections": 1,
                "total_documents": count,
                "indexed_chunks": count,
                "model": self.embedding_function.model_name
            }
        except Exception as e:
            print(f"Could not get stats, possibly empty DB: {e}")
            return {"collections": 1, "total_documents": 0, "indexed_chunks": 0, "model": self.embedding_function.model_name}