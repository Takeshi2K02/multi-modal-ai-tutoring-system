from db.connection import get_db_connection
from bson.objectid import ObjectId

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
    
    print(">>> Starting Data Migration to alex_123...")
    
    for coll_name in collections:
        coll = db.get_collection(coll_name)
        
        # Migrate student_id
        res = coll.update_many(
            {"student_id": "student_001"},
            {"$set": {"student_id": "alex_123"}}
        )
        if res.modified_count > 0:
            print(f"Migrated {res.modified_count} docs in {coll_name} (student_id)")
            
        # Migrate user_id
        res_user = coll.update_many(
            {"user_id": "student_001"},
            {"$set": {"user_id": "alex_123"}}
        )
        if res_user.modified_count > 0:
            print(f"Migrated {res_user.modified_count} docs in {coll_name} (user_id)")

    print(">>> Migration Complete.")

if __name__ == '__main__':
    migrate()
