from datetime import datetime
from typing import Dict, Any, Optional
from db.connection import get_db_connection
from bson.objectid import ObjectId

from services.learning_plan_service import LearningPlanService

class LearningSessionService:
    # In-memory Mock Store
    MOCK_DB = {}

    def __init__(self):
        self.db = get_db_connection()
        self.plans = self.db.get_collection("learning_plans") if self.db is not None else None
        self.sessions = self.db.get_collection("learning_sessions") if self.db is not None else None

    def create_session(self, plan_id: str, student_id: str) -> str:
        """
        Creates a new learning session for a given plan.
        """
        print(f"Creating session for Plan ID: {plan_id}, Student: {student_id}")

        # Real DB Path
        if self.sessions is not None and self.plans is not None:
             try:
                oid = ObjectId(plan_id)
                plan = self.plans.find_one({"_id": oid})
                if not plan:
                    raise ValueError(f"Learning Plan not found: {plan_id}")

                session_doc = self._create_session_doc(oid, student_id)
                result = self.sessions.insert_one(session_doc)
                print(f"Inserted Session ID: {result.inserted_id}")
                return str(result.inserted_id)

             except Exception as e:
                print(f"Mongo Insert Error: {e}")
                raise Exception(f"Failed to save session: {e}")

        # Mock DB Path
        else:
            print(">>> Using Mock DB for Learning Session")
            # Verify Plan in Mock
            plan = LearningPlanService.MOCK_DB.get(plan_id)
            if not plan:
                print(f"Mock Plan not found: {plan_id}")
                raise ValueError(f"Learning Plan not found: {plan_id}")
            
            # Create Session
            # Note: We use string ID for mock consistency
            session_doc = self._create_session_doc(plan_id, student_id)
            mock_id = str(ObjectId())
            session_doc["_id"] = mock_id
            LearningSessionService.MOCK_DB[mock_id] = session_doc
            return mock_id

    def _create_session_doc(self, plan_id, student_id):
        return {
            "plan_id": plan_id,
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

    def get_session_details(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the session AND the linked plan data.
        """
        if self.sessions is not None and self.plans is not None:
            try:
                # 1. Get Session
                session = self.sessions.find_one({"_id": ObjectId(session_id)})
                if not session:
                    return None
                    
                # 2. Get Linked Plan
                plan = self.plans.find_one({"_id": session["plan_id"]})
                if not plan:
                    return None 
                    
                # 3. Merge for UI
                session["_id"] = str(session["_id"])
                session["plan_id"] = str(session["plan_id"])
                plan["_id"] = str(plan["_id"])
                
                return {"session": session, "plan": plan}
            except Exception as e:
                print(f"Get Session Error: {e}")
                return None
        else:
             # Mock Retrieval
             session = LearningSessionService.MOCK_DB.get(session_id)
             if not session: return None

             plan = LearningPlanService.MOCK_DB.get(session["plan_id"])
             if not plan: return None

             return {"session": session, "plan": plan}

    def get_sessions_by_student(self, student_id: str) -> list[Dict[str, Any]]:
        """
        Retrieves all active sessions for a specific student, joined with plan info.
        """
        if self.sessions is not None and self.plans is not None:
            cursor = self.sessions.find({"student_id": student_id}).sort("last_accessed_at", -1)
            sessions = []
            for session in cursor:
                plan = self.plans.find_one({"_id": session["plan_id"]})
                session["_id"] = str(session["_id"])
                session["plan_id"] = str(session["plan_id"])
                if plan:
                    session["goal_title"] = plan.get("normalized_goal") or plan.get("original_goal", "Untitled Goal")
                    session["goal_topics_count"] = len(plan.get("curriculum", {}).get("structure", []))
                sessions.append(session)
            return sessions
        else:
            # Mock Implementation
            sessions = []
            for sess in LearningSessionService.MOCK_DB.values():
                if sess["student_id"] == student_id:
                     # Join Check
                     plan = LearningPlanService.MOCK_DB.get(sess["plan_id"])
                     sess_display = sess.copy()
                     if plan:
                         sess_display["goal_title"] = plan.get("normalized_goal")
                         sess_display["goal_topics_count"] = len(plan.get("curriculum", {}).get("structure", []))
                     sessions.append(sess_display)
            # Sort mock results if needed, skipping for now
            return sessions

    def delete_session(self, session_id: str) -> bool:
        if self.sessions is not None:
            try:
                result = self.sessions.delete_one({"_id": ObjectId(session_id)})
                return result.deleted_count > 0
            except Exception as e:
                print(f"Error deleting session {session_id}: {e}")
                return False
        else:
            if session_id in LearningSessionService.MOCK_DB:
                del LearningSessionService.MOCK_DB[session_id]
                return True
            return False
