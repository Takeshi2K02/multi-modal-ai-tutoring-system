from db.connection import get_db_connection, get_users_collection
db = get_db_connection()
users = get_users_collection(db)
if users is not None:
    user = users.find_one()
    print("User Keys:", user.keys() if user else "No users found")
    if user:
        print("Sample User:", user.get('email', 'No email'))
else:
    print("Users collection not found")
