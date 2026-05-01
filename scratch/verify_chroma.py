import chromadb
import os

PERSIST_DIR = os.path.join(os.getcwd(), "local_data", "vector_store")
client = chromadb.PersistentClient(path=PERSIST_DIR)
collection = client.get_collection("lectures")

# 1. Count total documents
count = collection.count()
print(f"Total documents in 'lectures': {count}")

# 2. Query for the specific collection_id
target_id = "batch_1773116210723_zxyml"
results = collection.get(
    where={"collection_id": target_id},
    limit=5
)

print(f"Documents with collection_id '{target_id}': {len(results['ids'])}")
if len(results['ids']) > 0:
    print("Sample metadata:", results['metadatas'][0])

# 3. Check what collection_ids DO exist
all_results = collection.get(limit=100)
ids = set()
for meta in all_results['metadatas']:
    if meta and 'collection_id' in meta:
        ids.add(meta['collection_id'])

print(f"Existing collection_ids (first 100 docs): {ids}")
