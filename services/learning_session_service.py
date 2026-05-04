from datetime import datetime
from typing import Dict, Any, Optional
from db.connection import get_db_connection
from bson.objectid import ObjectId

from services.learning_plan_service import LearningPlanService

class LearningSessionService:
    # In-memory Mock Store
    MOCK_DB = {}
    MOCK_PERFORMANCE = []

    def __init__(self):
        self.db = get_db_connection()
        self.plans = self.db.get_collection("learning_plans") if self.db is not None else None
        self.sessions = self.db.get_collection("learning_sessions") if self.db is not None else None
        self.performance = self.db.get_collection("performance") if self.db is not None else None
        self.generated_content = self.db.get_collection("generated_content") if self.db is not None else None
        self.student_progress = self.db.get_collection("student_progress") if self.db is not None else None

    def get_generated_content(self, student_id: str, topic_id: str, session_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Retrieves existing generated content for a topic and student.
        """
        if self.generated_content is not None:
            try:
                query = {
                    "student_id": student_id,
                    "topic_id": topic_id
                }
                if session_id:
                    query["session_id"] = session_id
                    
                content = self.generated_content.find_one(query)
                if content:
                    content["_id"] = str(content["_id"])
                    return content
                return None
            except Exception as e:
                print(f"Get Generated Content Error: {e}")
                return None
        return None

    def save_generated_content(self, content_data: Dict[str, Any]) -> bool:
        """
        Upserts generated content for a topic.
        """
        if self.generated_content is not None:
            try:
                query = {
                    "student_id": content_data["student_id"],
                    "topic_id": content_data["topic_id"]
                }
                if "session_id" in content_data:
                    query["session_id"] = content_data["session_id"]

                self.generated_content.update_one(
                    query,
                    {"$set": {**content_data, "updated_at": datetime.now()}},
                    upsert=True
                )
                return True
            except Exception as e:
                print(f"Save Generated Content Error: {e}")
                return False
        return True

    def save_student_progress(self, progress_data: Dict[str, Any]) -> bool:
        """
        Saves the full student progress state for a module.
        """
        if self.student_progress is not None:
            try:
                query = {
                    "student_id": progress_data["student_id"],
                    "topic_id": progress_data["topic_id"]
                }
                if "session_id" in progress_data:
                    query["session_id"] = progress_data["session_id"]

                self.student_progress.update_one(
                    query,
                    {"$set": {**progress_data, "updated_at": datetime.now()}},
                    upsert=True
                )
                return True
            except Exception as e:
                print(f"Save Student Progress Error: {e}")
                return False
        return True

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

    def update_session_progress(self, session_id: str, topic_id: str) -> bool:
        """
        Updates the session progress, marking a topic as completed and recalculating percentage.
        """
        print(f"Updating progress for Session={session_id}, Topic={topic_id}")
        
        if self.sessions is not None and self.plans is not None:
            try:
                # 1. Fetch Session and Plan
                session = self.sessions.find_one({"_id": ObjectId(session_id)})
                if not session: return False
                
                plan = self.plans.find_one({"_id": session["plan_id"]})
                if not plan: return False
                
                # 2. Update Completed Topics
                completed = session.get("progress", {}).get("completed_topics", [])
                if topic_id not in completed:
                    completed.append(topic_id)
                
                # 3. Calculate Percent Complete
                total_topics = 0
                for lecture in plan.get("curriculum", {}).get("structure", []):
                    total_topics += len(lecture.get("children", []))
                
                percent = (len(completed) / total_topics * 100) if total_topics > 0 else 100
                
                # 4. Save
                self.sessions.update_one(
                    {"_id": ObjectId(session_id)},
                    {
                        "$set": {
                            "progress.completed_topics": completed,
                            "progress.percent_complete": round(percent, 1),
                            "last_accessed_at": datetime.now()
                        }
                    }
                )
                return True
            except Exception as e:
                print(f"Update Progress Error: {e}")
                return False
        else:
            # Mock Implementation
            session = LearningSessionService.MOCK_DB.get(session_id)
            if not session: return False
            
            plan = LearningPlanService.MOCK_DB.get(session["plan_id"])
            if not plan: return False
            
            completed = session.get("progress", {}).get("completed_topics", [])
            if topic_id not in completed:
                completed.append(topic_id)
            
            total_topics = 0
            for lecture in plan.get("curriculum", {}).get("structure", []):
                total_topics += len(lecture.get("children", []))
            
            percent = (len(completed) / total_topics * 100) if total_topics > 0 else 100
            
            session["progress"]["completed_topics"] = completed
            session["progress"]["percent_complete"] = round(percent, 1)
            session["last_accessed_at"] = datetime.now()
            return True

    def start_session(self, session_id: str, topic_id: str) -> bool:
        """
        Updates session status to IN_PROGRESS and sets the current topic.
        (Project ID: 25-26J-130)
        """
        print(f"Starting session {session_id} for topic: {topic_id}")
        if self.sessions is not None:
            try:
                self.sessions.update_one(
                    {"_id": ObjectId(session_id)},
                    {
                        "$set": {
                            "status": "IN_PROGRESS",
                            "progress.current_topic_id": topic_id,
                            "last_accessed_at": datetime.now()
                        }
                    }
                )
                return True
            except Exception as e:
                print(f"Start Session Error: {e}")
                return False
        else:
            # Mock
            session = LearningSessionService.MOCK_DB.get(session_id)
            if session:
                session["status"] = "IN_PROGRESS"
                session["progress"]["current_topic_id"] = topic_id
                session["last_accessed_at"] = datetime.now()
                return True
            return False

    def save_performance_record(self, record: Dict[str, Any]) -> bool:
        """
        Saves a student's performance record for a topic.
        """
        print(f"Saving performance record for Student={record.get('student_id')}, Topic={record.get('topic_id')}")
        
        if self.performance is not None:
            try:
                self.performance.insert_one(record)
                return True
            except Exception as e:
                print(f"Save Performance Error: {e}")
                return False
        else:
            # Mock Implementation
            LearningSessionService.MOCK_PERFORMANCE.append(record)
            return True

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


def record_performance(student_id: str, payload: dict):
    """
    Called after quiz submission or subtopic completion.
    Writes to db.Performance for RL state vector consumption.
    """
    from datetime import datetime
    from db.connection import get_db_connection
    db = get_db_connection()
    
    quiz_accuracy = payload.get("quiz_score", 0.5)
    estimated_difficulty = round(1.0 - quiz_accuracy, 4)
    current_mastery = payload.get("mastery_level", 0.5)
    updated_mastery = round(min(1.0, max(0.0, current_mastery + (quiz_accuracy - 0.5) * 0.1)), 4)
    
    try:
        db.Performance.insert_one({
            "user_id": student_id,
            "subtopic": payload.get("subtopic", "unknown"),
            "accuracy": quiz_accuracy,
            "difficulty": estimated_difficulty,
            "mastery": updated_mastery,
            "timestamp": datetime.utcnow()
        })
        print(f"[Session] Performance record written: user={student_id}, difficulty={estimated_difficulty}, mastery={updated_mastery}")
    except Exception as e:
        print(f"[Session] WARNING: Failed to write Performance record: {e}")
