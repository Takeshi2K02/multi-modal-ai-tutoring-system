import os
import uuid
import json
from datetime import datetime
from typing import List, Dict, Any
from pypdf import PdfReader
from services.vector_factory import get_vector_db

RAW_PDF_DIR = os.path.join(os.getcwd(), "local_data", "raw_pdfs")
PROCESSED_CHUNKS_DIR = os.path.join(os.getcwd(), "local_data", "processed_chunks")

# Ensure dirs exist
os.makedirs(RAW_PDF_DIR, exist_ok=True)
os.makedirs(PROCESSED_CHUNKS_DIR, exist_ok=True)

async def ingest_pdf(file_content: bytes, filename: str):
    """
    Process a PDF file and ingest into VectorDB.
    """
    print(f"Ingesting {filename}...")
    
    # 1. Save Raw File
    file_path = os.path.join(RAW_PDF_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
        
    # 2. Extract Text & Chunk
    chunks = _process_pdf_text(file_path, filename)
    
    # 3. Save Parsed Chunks (Debug)
    debug_path = os.path.join(PROCESSED_CHUNKS_DIR, f"{filename}.json")
    with open(debug_path, "w") as f:
        json.dump(chunks, f, indent=2)
        
    # 4. Push to VectorDB
    vectordb = get_vector_db()
    
    # Format for VectorDB interface
    docs_to_add = []
    for chunk in chunks:
        docs_to_add.append({
            "id": chunk["doc_id"],
            "text": chunk["text"],
            "metadata": {
                "source_file": filename,
                "lecture_title": chunk["lecture_title"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"]
            }
        })
        
    vectordb.add_documents(docs_to_add)
    return {"status": "success", "chunks_count": len(chunks)}

def _process_pdf_text(file_path: str, filename: str) -> List[Dict[str, Any]]:
    reader = PdfReader(file_path)
    chunks = []
    
    # Simple chunking: Page-level or split by chars
    # Requirement says "Chunk extracted text using a configurable chunk size"
    CHUNK_SIZE = 500
    OVERLAP = 50
    
    lecture_title = filename.replace(".pdf", "").replace("_", " ").title()
    
    chunk_counter = 0
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if not text:
            continue
            
        # Split text into chunks
        words = text.split()
        for j in range(0, len(words), CHUNK_SIZE - OVERLAP):
            chunk_words = words[j:j + CHUNK_SIZE]
            chunk_text = " ".join(chunk_words)
            
            if len(chunk_text) < 50: # Skip tiny chunks
                continue
                
            chunks.append({
                "doc_id": f"{filename}_p{i}_c{chunk_counter}",
                "source_file": filename,
                "lecture_title": lecture_title,
                "page_number": i + 1,
                "chunk_index": chunk_counter,
                "text": chunk_text
            })
            chunk_counter += 1
            
    return chunks
