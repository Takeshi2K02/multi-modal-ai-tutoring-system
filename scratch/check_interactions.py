from db.connection import get_db_connection, get_interactions_collection
db = get_db_connection()
interactions = get_interactions_collection(db)
if interactions is not None:
    interaction = interactions.find_one()
    print("Interaction Keys:", interaction.keys() if interaction else "No interactions found")
    if interaction:
        print("Sample Interaction student_id:", interaction.get('student_id', 'No student_id'))
else:
    print("Interactions collection not found")
