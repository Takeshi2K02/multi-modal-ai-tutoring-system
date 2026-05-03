from typing import List, Dict, Any
from services.vector_interface import VectorDBInterface
import os

def get_vector_db() -> VectorDBInterface:
    # Switched from LocalVectorDB to PineconeVectorDB
    from services.local_vectordb import PineconeVectorDB
    return PineconeVectorDB()
