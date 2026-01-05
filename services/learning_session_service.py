from datetime import datetime
from typing import Dict, Any, Optional
from db.connection import get_db_connection
from bson.objectid import ObjectId

class LearningSessionService:
    def __init__(self):
        self.db = get_db_connection()
        self.plans = self.db.get_collection("learning_plans") if self.db is not None else None
        self.sessions = self.db.get_collection("learning_sessions") if self.db is not None else None

    def create_session(self, plan_id: str, student_id: str) -> str:
        """
        Creates a new learning session for a given plan.
        """
        print(f"Creating session for Plan ID: {plan_id}, Student: {student_id}")

        if self.sessions is None or self.plans is None:
            print("DB Collection is None")
            raise Exception("Database unavailable")

        try:
            oid = ObjectId(plan_id)
        except Exception as e:
            print(f"Invalid Plan ID format: {plan_id} -> {e}")
            raise ValueError(f"Invalid Plan ID: {plan_id}")

        # Verify Plan Exists
        plan = self.plans.find_one({"_id": oid})
        if not plan:
            print(f"Plan not found with ID: {oid}")
            raise ValueError(f"Learning Plan not found: {plan_id}")

        session_doc = {
            "plan_id": oid,
            "student_id": student_id,
            "status": "NOT_STARTED",
            "created_at": datetime.now(),
            "last_accessed_at": datetime.now(),
            
            "progress": {
                "completed_topics": [], 
                "current_topic_id": None, # Will default to first in UI
                "percent_complete": 0.0
            },
            
            "state_metadata": {
                "notes": "",
                "last_position_index": 0
            }
        }
        
        try:
            result = self.sessions.insert_one(session_doc)
            print(f"Inserted Session ID: {result.inserted_id}")
            return str(result.inserted_id)
        except Exception as e:
            print(f"Mongo Insert Error: {e}")
            raise Exception(f"Failed to save session: {e}")

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the session AND the linked plan data.
        """
        if self.sessions is None or self.plans is None:
            return None
            
        try:
            # 1. Get Session
            session = self.sessions.find_one({"_id": ObjectId(session_id)})
            if not session:
                return None
                
            # 2. Get Linked Plan
            plan = self.plans.find_one({"_id": session["plan_id"]})
            if not plan:
                return None # Corrupt State: Session without Plan
                
            # 3. Merge for UI
            # Convert ObjectIds to strings
            session["_id"] = str(session["_id"])
            session["plan_id"] = str(session["plan_id"])
            plan["_id"] = str(plan["_id"])
            
            return {
                "session": session,
                "plan": plan
            }
        except Exception as e:
            print(f"Get Session Error: {e}")
            return None

    def get_sessions_by_student(self, student_id: str) -> list[Dict[str, Any]]:
        """
        Retrieves all active sessions for a specific student, joined with plan info.
        """
        if self.sessions is None or self.plans is None:
            return []
            
        cursor = self.sessions.find({"student_id": student_id}).sort("last_accessed_at", -1)
        sessions = []
        for session in cursor:
            # Join with Plan to get the Title/Goal
            plan = self.plans.find_one({"_id": session["plan_id"]})
            
            session["_id"] = str(session["_id"])
            session["plan_id"] = str(session["plan_id"])
            
            # Enrich with basic display info from plan
            if plan:
                session["goal_title"] = plan.get("normalized_goal") or plan.get("original_goal", "Untitled Goal")
                session["goal_topics_count"] = len(plan.get("curriculum", {}).get("structure", []))
            
            sessions.append(session)
            
        return sessions

    def delete_session(self, session_id: str) -> bool:
        """
        Permanently deletes a learning session. 
        Does NOT delete the linked plan.
        """
        if self.sessions is None:
            return False
            
        try:
            result = self.sessions.delete_one({"_id": ObjectId(session_id)})
            return result.deleted_count > 0
        except Exception as e:
            print(f"Error deleting session {session_id}: {e}")
            return False
