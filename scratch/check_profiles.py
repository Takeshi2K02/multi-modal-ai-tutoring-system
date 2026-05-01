from db.connection import get_db_connection, get_profiles_collection
db = get_db_connection()
profiles = get_profiles_collection(db)
if profiles is not None:
    profile = profiles.find_one()
    print("Profile Keys:", profile.keys() if profile else "No profiles found")
    if profile:
        print("Sample Profile student_id:", profile.get('student_id', 'No student_id'))
else:
    print("Profiles collection not found")
