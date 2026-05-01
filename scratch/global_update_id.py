from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
mongo_uri = os.getenv('MONGO_URI')
client = MongoClient(mongo_uri)
email = 'takeshidilshan10@gmail.com'
new_id = '362aad49-6c75-4d60-adc5-40bfd4701797'

print(f"Starting global update for {email} to collection_id: {new_id}")

for db_name in client.list_database_names():
    db = client.get_database(db_name)
    colls = db.list_collection_names()
    
    if 'learning_sessions' in colls:
        res = db.learning_sessions.update_many(
            {'student_id': email}, 
            {'$set': {'collection_id': new_id}}
        )
        if res.matched_count > 0:
            print(f"Matched {res.matched_count}, Updated {res.modified_count} sessions in {db_name}")
            
    if 'learning_plans' in colls:
        res = db.learning_plans.update_many(
            {'student_id': email}, 
            {'$set': {'system_metadata.collection_id': new_id}}
        )
        if res.matched_count > 0:
            print(f"Matched {res.matched_count}, Updated {res.modified_count} plans in {db_name}")

print("Update complete.")
