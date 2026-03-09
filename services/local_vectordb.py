import chromadb
import uuid
import os
from typing import List, Dict, Any
from services.vector_interface import VectorDBInterface

# Directory where ChromaDB will persist data
PERSIST_DIR = os.path.join(os.getcwd(), "local_data", "vector_store")

_CLIENT_INSTANCE = None

class LocalVectorDB(VectorDBInterface):
    def __init__(self):
        global _CLIENT_INSTANCE
        if _CLIENT_INSTANCE is None:
            print(f"Initializing LocalVectorDB Client at {PERSIST_DIR}")
            _CLIENT_INSTANCE = chromadb.PersistentClient(path=PERSIST_DIR)
        
        self.client = _CLIENT_INSTANCE
        
        # Create or get collection
        self.collection = self.client.get_or_create_collection(
            name="lectures",
            metadata={"hnsw:space": "cosine"}
        )

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        # Query Chroma
        results = self.collection.query(
            query_texts=[query],
            n_results=top_k
        )
        
        # Transform to standard format
        # Chroma returns lists of lists (one per query)
        output = []
        if results["ids"]:
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            documents = results["documents"][0]
            distances = results["distances"][0]
            
            for i in range(len(ids)):
                # Chroma uses 'distance', we want 'score' (similiarity)
                # For cosine distance: score = 1 - distance
                score = 1.0 - distances[i]
                
                meta = metadatas[i] or {}
                
                # Standardize return format matching MockVectorDB
                source_id = meta.get("source_file") or meta.get("lecture_id") or meta.get("filename") or "local"
                doc = {
                    "id": ids[i],
                    "title": meta.get("lecture_title", "Unknown Title"),
                    "text": documents[i],
                    "score": round(score, 3),
                    "metadata": {
                        "source": source_id,
                        "lecture_id": source_id,
                        "page": meta.get("page_number"),
                        "lecture_title": meta.get("lecture_title"),
                        "week": 0
                    }
                }
                output.append(doc)
                
        return output

    def add_documents(self, documents: List[Dict[str, Any]]):
        ids = [doc["id"] for doc in documents]
        texts = [doc["text"] for doc in documents]
        metadatas = [doc["metadata"] for doc in documents]
        
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        print(f"LocalVectorDB: Added {len(documents)} documents.")
