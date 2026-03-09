from datetime import datetime
from typing import Dict, Any, List, Optional
from db.connection import get_db_connection, get_students_collection, get_interactions_collection
from mocks.data_generators import get_mock_student_profile

class MemoryManager:
    def __init__(self):
        self.db = get_db_connection()
        from db.connection import get_profiles_collection
        self.profiles = get_profiles_collection(self.db)
        self.interactions = get_interactions_collection(self.db)

    def get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """
        Retrieves student profile from DB. 
        Falls back to mock if not found or DB unavailable.
        Ensures 'preferred_modality' field exists.
        """
        profile = None
        if self.profiles is not None:
            profile = self.profiles.find_one({"student_id": student_id})
            if profile and "_id" in profile:
                del profile["_id"]
        
        if not profile:
            print(f"Memory: Student {student_id} not found in DB. Using mock.")
            profile = get_mock_student_profile(student_id, randomized=False)

        # Ensure preferred_modality exists (Project ID: 25-26J-130)
        if "preferred_modality" not in profile:
            profile["preferred_modality"] = {"visual": 0.33, "textual": 0.33, "interactive": 0.34}
        
        return profile

    def update_learning_preference(self, student_id: str, strategy_type: str, success: bool):
        """
        Updates the confidence score for a learning strategy based on outcome.
        Rule: confidence = (successes + 1) / (trials + 2)  [Laplace Smoothing]
        """
        if self.students is None:
            return

        # Fetch current profile
        profile = self.get_student_profile(student_id)
        prefs = profile.get("learning_preferences", {})
        
        if strategy_type not in prefs:
            prefs[strategy_type] = {"confidence": 0.5, "trials": 0, "successes": 0, "last_updated": None}
            
        stat = prefs[strategy_type]
        stat["trials"] += 1
        if success:
            stat["successes"] += 1
            
        # Outcomes Update Rule (Laplace Smoothing / Beta Mean)
        stat["confidence"] = (stat["successes"] + 1) / (stat["trials"] + 2)
        stat["last_updated"] = datetime.now()
        
        # Save back to DB
        self.students.update_one(
            {"student_id": student_id},
            {"$set": {"learning_preferences": prefs}},
            upsert=True
        )
        print(f"Memory: Updated preference for {strategy_type} -> {stat['confidence']:.2f}")

    def save_interaction(self, interaction_data: Dict[str, Any]) -> Optional[str]:
        """
        Logs the interaction to the database.
        Returns the interaction ID.
        """
        if self.interactions is not None:
            # Ensure timestamp is present
            if "timestamp" not in interaction_data:
                interaction_data["timestamp"] = datetime.now()
            
            try:
                result = self.interactions.insert_one(interaction_data)
                print(f"Memory: Interaction saved to DB (ID: {result.inserted_id}).")
                return str(result.inserted_id)
            except Exception as e:
                print(f"Memory: Failed to save interaction: {e}")
        else:
            print("Memory: DB unavailable. Interaction not saved.")
        return None

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
