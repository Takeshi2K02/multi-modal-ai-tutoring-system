import sys
from db.connection import get_db_connection
from bson.objectid import ObjectId

STUDENT_ID = sys.argv[1] if len(sys.argv) > 1 else "test_user"

def migrate():
    db = get_db_connection()
    collections = [
        'learning_plans', 
        'learning_sessions', 
        'interactions', 
        'StudentEngagement', 
        'Performance', 
        'PedagogicalStrategy', 
        'generated_content', 
        'student_progress'
    ]
    
    print(f">>> Starting Data Migration to {STUDENT_ID}...")
    
    for coll_name in collections:
        coll = db.get_collection(coll_name)
        
        # Migrate student_id
        res = coll.update_many(
            {"student_id": "student_001"},
            {"$set": {"student_id": STUDENT_ID}}
        )
        if res.modified_count > 0:
            print(f"Migrated {res.modified_count} docs in {coll_name} (student_id)")
            
        # Migrate user_id
        res_user = coll.update_many(
            {"user_id": "student_001"},
            {"$set": {"user_id": STUDENT_ID}}
        )
        if res_user.modified_count > 0:
            print(f"Migrated {res_user.modified_count} docs in {coll_name} (user_id)")

    print(">>> Migration Complete.")

if __name__ == '__main__':
    migrate()
