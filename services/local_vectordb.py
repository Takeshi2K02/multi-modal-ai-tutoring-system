import os
from typing import List, Dict, Any
from pinecone import Pinecone
from sentence_transformers import SentenceTransformer
from services.vector_interface import VectorDBInterface

class PineconeVectorDB(VectorDBInterface):
    """
    Pinecone-backed Vector Database implementation.
    Generates embeddings locally using all-MiniLM-L6-v2 (384-dim).
    (Project ID: 25-26J-130)
    """
    def __init__(self):
        self.api_key = os.getenv("PINECONE_API_KEY")
        self.host = os.getenv("PINECONE_HOST")
        self.index_name = os.getenv("PINECONE_INDEX_NAME")
        
        if not self.api_key or not self.host:
            print("[VectorDB] ⚠️ Pinecone credentials missing. Ensure .env is configured.")
            
        self.pc = Pinecone(api_key=self.api_key)
        self.index = self.pc.Index(host=self.host)
        
        # Initialize local embedding model as requested
        # Dimension: 384
        print("[VectorDB] 🧠 Initializing local SentenceTransformer (all-MiniLM-L6-v2)...")
        self.model = SentenceTransformer('all-MiniLM-L6-v2')

    def search(self, query: str, top_k: int = 10, filter: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant documents in Pinecone.
        """
        print(f"[VectorDB] Searching Pinecone for: '{query}' with filter: {filter}")
        
        # 1. Generate query embedding locally
        query_vector = self.model.encode(query).tolist()
        
        # 2. Query Pinecone
        try:
            results = self.index.query(
                vector=query_vector,
                top_k=top_k,
                filter=filter,
                include_metadata=True
            )
        except Exception as e:
            print(f"[VectorDB] ❌ Pinecone Query Failed: {e}")
            return []
        
        print(f"[VectorDB] Found {len(results.get('matches', []))} results.")
        
        # 3. Transform to standard format
        output = []
        for match in results.get("matches", []):
            meta = match.get("metadata", {})
            source_id = meta.get("source_file") or meta.get("lecture_id") or "local"
            
            output.append({
                "id": match["id"],
                "title": meta.get("lecture_title", "Unknown Title"),
                "text": meta.get("text", ""), # Retrieved from metadata
                "score": round(match["score"], 3),
                "metadata": {
                    "source": source_id,
                    "lecture_id": source_id,
                    "page": meta.get("page_number"),
                    "lecture_title": meta.get("lecture_title"),
                    "week": 0
                }
            })
        return output

    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Generates embeddings locally and upserts to Pinecone.
        """
        vectors = []
        for doc in documents:
            # Generate embedding locally
            embedding = self.model.encode(doc["text"]).tolist()
            
            # Prepare metadata
            metadata = doc.get("metadata", {})
            metadata["text"] = doc["text"] # Ensure text is stored for retrieval
            
            vectors.append({
                "id": doc["id"],
                "values": embedding,
                "metadata": metadata
            })
            
        # Batch upsert
        try:
            self.index.upsert(vectors=vectors)
            print(f"[VectorDB] ✅ Pinecone: Upserted {len(documents)} documents.")
        except Exception as e:
            print(f"[VectorDB] ❌ Pinecone Upsert Failed: {e}")

    def delete_documents_by_source(self, source_filename: str):
        """
        Deletes documents filtered by source filename.
        """
        try:
            self.index.delete(filter={"source_file": source_filename})
            print(f"[VectorDB] ✅ Pinecone: Deleted documents from {source_filename}.")
        except Exception as e:
            print(f"[VectorDB] ❌ Pinecone Delete Failed: {e}")
