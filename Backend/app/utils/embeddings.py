import threading

class EmbeddingManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(EmbeddingManager, cls).__new__(cls)
                cls._instance._doc_model = None
                cls._instance._qa_model = None
                cls._instance._doc_lock = threading.Lock()
                cls._instance._qa_lock = threading.Lock()
        return cls._instance

    def get_document_embedding_model(self):
        with self._doc_lock:
            if self._doc_model is None:
                try:
                    from langchain_huggingface import HuggingFaceEmbeddings
                    self._doc_model = HuggingFaceEmbeddings(
                        model_name="BAAI/bge-base-en-v1.5"
                    )
                except Exception as e:
                    raise RuntimeError(f"Document embedding model failed to load: {e}")
            return self._doc_model

    def get_qa_embedding_model(self):
        with self._qa_lock:
            if self._qa_model is None:
                try:
                    from sentence_transformers import SentenceTransformer
                    self._qa_model = SentenceTransformer("all-MiniLM-L6-v2")
                except Exception as e:
                    raise RuntimeError(f"QA embedding model failed to load: {e}")
            return self._qa_model

embedding_manager = EmbeddingManager()
