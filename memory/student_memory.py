from datetime import datetime
from typing import Dict, Any, List, Optional
from db.connection import get_db_connection, get_students_collection, get_interactions_collection
from mocks.data_generators import get_mock_student_profile

class MemoryManager:
    def __init__(self):
        self.db = get_db_connection()
        self.students = get_students_collection(self.db)
        self.interactions = get_interactions_collection(self.db)

    def get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """
        Retrieves student profile from DB. 
        Falls back to mock if not found or DB unavailable.
        """
        if self.students is not None:
            profile = self.students.find_one({"student_id": student_id})
            if profile:
                # Remove MongoDB _id for clean return
                if "_id" in profile:
                    del profile["_id"]
                return profile
        
        print(f"Memory: Student {student_id} not found in DB (or DB unavailable). Using mock.")
        return get_mock_student_profile(student_id, randomized=False)

    def save_interaction(self, interaction_data: Dict[str, Any]):
        """
        Logs the interaction to the database.
        """
        if self.interactions is not None:
            # Ensure timestamp is present
            if "timestamp" not in interaction_data:
                interaction_data["timestamp"] = datetime.now()
            
            try:
                self.interactions.insert_one(interaction_data)
                print("Memory: Interaction saved to DB.")
            except Exception as e:
                print(f"Memory: Failed to save interaction: {e}")
        else:
            print("Memory: DB unavailable. Interaction not saved.")

    def get_recent_history(self, student_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieves recent interactions for context.
        """
        if self.interactions is not None:
            cursor = self.interactions.find(
                {"student_id": student_id}
            ).sort("timestamp", -1).limit(limit)
            
            history = []
            for doc in cursor:
                if "_id" in doc:
                    del doc["_id"]
                history.append(doc)
            return history
        
        return []
