# Project ID: 25-26J-130: Intervention Control State
active_prefetch_tasks = set()
active_student_synthesis = set()
is_tot_running = False

# Cooldown registry: interaction_id -> {"count": int, "last_trigger": float}
triggered_interventions = {} 

active_lesson = {} # student_id -> topic_id or None
shadow_tot_in_progress = False

# student_id -> timestamp of when they were put in 'awaiting' state
waiting_for_user_decision = {} 
