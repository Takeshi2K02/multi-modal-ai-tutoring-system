from datetime import datetime
from typing import Dict, Any, Optional
from db.connection import get_db_connection
from bson.objectid import ObjectId

class LearningPlanService:
    # In-memory Mock Store for Demo Mode
    MOCK_DB = {}

    def __init__(self):
        self.db = get_db_connection()
        self.collection = self.db.get_collection("learning_plans") if self.db is not None else None

    def save_learning_plan(self, data: Dict[str, Any]) -> str:
        """
        Validates and saves a learning plan.
        Returns the Inserted ID as a string.
        """
        # 1. Sanitize & Structure
        # Ensure we have required metadata
        plan_doc = {
            "student_id": "student_001", # Hardcoded for Single-Player MVP
            "original_goal": data.get("goal", ""),
            "normalized_goal": data.get("generatedTitle") or data.get("goal", "").title(), # Use generated title
            "status": "ACTIVE",
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            
            # The Curriculum
            "curriculum": {
                "structure": self._sanitize_structure(data.get("toc", []))
            },
            
            # Metadata
            "analysis_metadata": {
                "evidenceCoverage": data.get("evidenceCoverage", 0.0),
                "outlineConfidence": data.get("outlineConfidence", 0.0),
                "gaps": data.get("gaps", [])
            },
            
            "system_metadata": {
                "vector_provider": "local",
                "source_real_data": True, 
                "version": "1.0"
            }
        }

        # 2. Insert (Real or Mock)
        if self.collection is not None:
            result = self.collection.insert_one(plan_doc)
            return str(result.inserted_id)
        else:
            print(">>> Using Mock DB for Learning Plan")
            mock_id = str(ObjectId())
            plan_doc["_id"] = mock_id # Store ID as string for consistency in mock
            LearningPlanService.MOCK_DB[mock_id] = plan_doc
            return mock_id

    def _sanitize_structure(self, raw_toc: list) -> list:
        """
        Removes heavy text fields from the TOC structure to keep DB light.
        We only need references.
        """
        clean_toc = []
        for lecture in raw_toc:
            clean_lec = {
                "title": lecture.get("title", "Unknown"),
                "type": lecture.get("type", "LECTURE_GROUP"),
                "children": []
            }
            
            for topic in lecture.get("children", []):
                clean_topic = {
                    "title": topic.get("title", "Unknown"),
                    "type": topic.get("type", "TOPIC"),
                    "evidence_refs": []
                }
                
                # Extract refs from 'topChunks' but DROP the text
                ev = topic.get("evidence", {})
                clean_topic["evidence_source_summary"] = ev.get("sourceDocs", [])
                
                clean_lec["children"].append(clean_topic)
            
            clean_toc.append(clean_lec)
        return clean_toc

    def get_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        if self.collection is not None:
             try:
                doc = self.collection.find_one({"_id": ObjectId(plan_id)})
                if doc:
                    doc["_id"] = str(doc["_id"])
                return doc
             except Exception:
                return None
        else:
            # Mock Retrieval
            doc = LearningPlanService.MOCK_DB.get(plan_id)
            if doc:
                # Return deep copy if needed, but dict is fine for read
                return doc
            return None
