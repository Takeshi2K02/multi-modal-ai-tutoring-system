import os
import uuid
import json
from pypdf import PdfReader
from pymongo import MongoClient
from dotenv import load_dotenv
import chromadb
from datetime import datetime

# Load env
load_dotenv()

# Config
PDF_DIR = "pdf"
VECTOR_STORE_PATH = "local_data/vector_store"
STUDENT_EMAIL = "takeshidilshan10@gmail.com"

# 1. Generate Batch ID
collection_id = str(uuid.uuid4())
print(f"Generated Batch ID (collection_id): {collection_id}")

# 2. Setup ChromaDB
# Note: Re-initializing to ensure fresh state
client = chromadb.PersistentClient(path=VECTOR_STORE_PATH)
collection = client.get_or_create_collection(
    name="lectures",
    metadata={"hnsw:space": "cosine"}
)

def chunk_text(text, filename, page_num):
    CHUNK_SIZE = 500
    OVERLAP = 50
    words = text.split()
    chunks = []
    chunk_counter = 0
    
    for j in range(0, len(words), CHUNK_SIZE - OVERLAP):
        chunk_words = words[j:j + CHUNK_SIZE]
        chunk_text = " ".join(chunk_words)
        if len(chunk_text) < 5: continue
        
        chunks.append({
            "chunk_id": f"{filename}_p{page_num}_c{chunk_counter}",
            "text": chunk_text
        })
        chunk_counter += 1
    return chunks

# 3. Process PDFs
if not os.path.exists(PDF_DIR):
    print(f"Error: PDF directory '{PDF_DIR}' not found.")
    exit(1)

pdf_files = sorted([f for f in os.listdir(PDF_DIR) if f.endswith(".pdf")])
print(f"Found {len(pdf_files)} PDFs in {PDF_DIR}")

total_chunks_added = 0

for filename in pdf_files:
    file_path = os.path.join(PDF_DIR, filename)
    print(f"Processing {filename}...")
    
    try:
        reader = PdfReader(file_path)
        topic = filename.replace(".pdf", "").replace("_", " ").title()
        
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if not text: continue
            
            page_chunks = chunk_text(text, filename, i + 1)
            
            ids = []
            documents = []
            metadatas = []
            
            for chunk in page_chunks:
                ids.append(chunk["chunk_id"])
                documents.append(chunk["text"])
                metadatas.append({
                    "collection_id": collection_id,
                    "source": filename,
                    "topic": topic,
                    "chunk_id": chunk["chunk_id"]
                })
                
            if ids:
                collection.add(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas
                )
                total_chunks_added += len(ids)
    except Exception as e:
        print(f"Error processing {filename}: {e}")

print(f"\nIngestion complete. Total chunks added: {total_chunks_added}")

# 4. Verify
all_results = collection.get()
count_total = len(all_results['ids'])
count_with_id = len([m for m in all_results['metadatas'] if m.get('collection_id') == collection_id])

# Filter query
filter_results = collection.query(
    query_texts=["data warehouse"],
    n_results=5,
    where={"collection_id": collection_id}
)
filter_count = len(filter_results['ids'][0]) if filter_results['ids'] else 0

print(f"\n[Verify] Total chunks: {count_total}")
print(f"[Verify] Chunks with collection_id: {count_with_id}")
print(f"[Verify] Filter query returned: {filter_count} results")

# 5. Update MongoDB
mongo_uri = os.getenv('MONGO_URI', 'mongodb://localhost:27017/ai_tutor_db')
try:
    m_client = MongoClient(mongo_uri)
    db = m_client.get_database()
    res = db.learning_sessions.update_one(
        {"student_id": STUDENT_EMAIL},
        {"$set": {"collection_id": collection_id}}
    )

    if res.modified_count > 0:
        print(f"\n[Mongo] Updated session for {STUDENT_EMAIL} with collection_id: {collection_id}")
    else:
        print(f"\n[Mongo] Failed to update session or session already had this collection_id.")
except Exception as e:
    print(f"\n[Mongo] Error updating MongoDB: {e}")
