from datetime import datetime
from typing import Dict, Any, List, Optional
from db.connection import get_db_connection, get_students_collection, get_interactions_collection
from mocks.data_generators import get_mock_student_profile

class MemoryManager:
    def __init__(self):
        self.db = get_db_connection()
        from db.connection import get_profiles_collection, get_users_collection, get_students_collection
        self.profiles = get_profiles_collection(self.db)
        self.users = get_users_collection(self.db)
        self.students = get_students_collection(self.db) # For strategy weights
        self.interactions = get_interactions_collection(self.db)

    def get_student_profile(self, student_id: str) -> Dict[str, Any]:
        """
        Retrieves student profile from DB. 
        Identifier is email in the 'users' collection (Project ID: 25-26J-130)
        """
        user_doc = None
        if self.users is not None:
            user_doc = self.users.find_one({"email": student_id})
        
        if not user_doc:
            # Fallback to profiles if not found in users (for backward compatibility)
            if self.profiles is not None:
                user_doc = self.profiles.find_one({"student_id": student_id})
        
        if not user_doc:
            raise RuntimeError(f"CRITICAL: Student {student_id} not found in DB. Agentic Core cannot initialize without a valid profile.")

        # Flatten the user document
        profile = {k: v for k, v in user_doc.items() if k != "_id"}
        
        # Merge learning_profile into top level if it exists (Project ID: 25-26J-130)
        learning_profile = profile.get("learning_profile", {})
        if learning_profile:
            profile.update(learning_profile)

        # Map preferred_learning_style to preferred_modality if missing
        if "preferred_modality" not in profile:
            style = profile.get("preferred_learning_style", "textual").lower()
            if style == "visual":
                profile["preferred_modality"] = {"visual": 0.6, "textual": 0.2, "interactive": 0.2}
            elif style == "interactive" or style == "kinesthetic":
                profile["preferred_modality"] = {"visual": 0.2, "textual": 0.2, "interactive": 0.6}
            else: # Default to textual bias
                profile["preferred_modality"] = {"visual": 0.2, "textual": 0.6, "interactive": 0.2}
        
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
