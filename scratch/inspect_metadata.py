import chromadb
import os

PERSIST_DIR = os.path.join(os.getcwd(), "local_data", "vector_store")
client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_collection("lectures")

all_results = collection.get(limit=10)
for i, meta in enumerate(all_results['metadatas']):
    print(f"Doc {i} metadata keys: {list(meta.keys()) if meta else 'None'}")
    if meta:
        print(f"  Sample metadata: {meta}")
