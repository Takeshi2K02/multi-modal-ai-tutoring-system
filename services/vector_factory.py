from typing import List, Dict, Any
from services.vector_interface import VectorDBInterface
import os

def get_vector_db() -> VectorDBInterface:
    # Always returning LocalVectorDB for now
    from services.local_vectordb import LocalVectorDB
    return LocalVectorDB()
