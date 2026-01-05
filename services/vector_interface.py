from abc import ABC, abstractmethod
from typing import List, Dict, Any

class VectorDBInterface(ABC):
    @abstractmethod
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for documents relevant to the query.
        Returns a list of dicts with keys: id, title, text, metadata, score.
        """
        pass

    @abstractmethod
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add documents to the store.
        documents: List of dicts with: id, text, metadata
        """
        pass
