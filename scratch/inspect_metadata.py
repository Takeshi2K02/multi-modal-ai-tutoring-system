import os
from services.vector_factory import get_vector_db

# Switched to use factory to support Pinecone migration
vectordb = get_vector_db()

# Sample search to inspect metadata
query = "Linear Algebra"
print(f"Inspecting metadata for query: {query}")

results = vectordb.search(query, top_k=5)

for i, res in enumerate(results):
    print(f"Doc {i} ID: {res['id']}")
    print(f"  Metadata: {res.get('metadata')}")
    print(f"  Text Sample: {res.get('text')[:100]}...")
