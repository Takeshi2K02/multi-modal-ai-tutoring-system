import os
import json
from services.vector_factory import get_vector_db

CHUNKS_DIR = "local_data/processed_chunks"

def reingest():
    if not os.path.exists(CHUNKS_DIR):
        print(f"Directory not found: {CHUNKS_DIR}")
        return

    vectordb = get_vector_db()
    files = [f for f in os.listdir(CHUNKS_DIR) if f.endswith(".json")]
    
    print(f"Found {len(files)} chunk files.")
    
    total_docs = 0
    for fname in files:
        path = os.path.join(CHUNKS_DIR, fname)
        try:
            with open(path, "r") as f:
                chunks = json.load(f)
                
            docs_to_add = []
            for chunk in chunks:
                docs_to_add.append({
                    "id": chunk["doc_id"],
                    "text": chunk["text"],
                    "metadata": {
                        "source_file": chunk.get("source_file", fname),
                        "lecture_title": chunk.get("lecture_title", "Unknown"),
                        "page_number": chunk.get("page_number", 0),
                        "chunk_index": chunk.get("chunk_index", 0)
                    }
                })
            
            if docs_to_add:
                vectordb.add_documents(docs_to_add)
                total_docs += len(docs_to_add)
                print(f"Ingested {len(docs_to_add)} chunks from {fname}")
        except Exception as e:
            print(f"Failed to ingest {fname}: {e}")
            
    print(f"DONE. Total re-ingested: {total_docs}")

if __name__ == "__main__":
    reingest()
