from db.connection import get_db_connection, get_users_collection
db = get_db_connection()
users = get_users_collection(db)
if users is not None:
    user = users.find_one({"email": "takeshidilshan10@gmail.com"})
    if user:
        print("Learning Profile:", user.get('learning_profile'))
    else:
        print("User not found")
