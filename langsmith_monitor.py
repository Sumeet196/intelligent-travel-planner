import os
from config import Config
from langsmith import Client
from langsmith.run_helpers import traceable
from typing import Dict, Any, List
import json

if Config.LANGSMITH_API_KEY:
    os.environ["LANGSMITH_API_KEY"] = Config.LANGSMITH_API_KEY
    os.environ["LANGSMITH_TRACING_V2"] = Config.LANGSMITH_TRACING
    os.environ["LANGSMITH_PROJECT"] = Config.LANGSMITH_PROJECT
    
    langsmith_client = Client()
else:
    langsmith_client = None
    print("⚠️ LangSmith not configured. Tracing disabled.")

class TripPlanningMonitor:
    """Monitor and track trip planner executions"""
    
    def __init__(self):
        self.client = langsmith_client
        self.runs = []
        
    @traceable(name="trip_planning_session")
    def track_planning_session(self, trip_request: Dict, final_state: Dict) -> Dict:
        '''Track a planning session'''
        session_data = {
            "trip_request": trip_request,
            "destination": trip_request.get("destination"),
            "budget": trip_request.get("budget"),
            "duration": trip_request.get("duration_days"),
            "success": final_state.get("itinerary") is not None,
            "errors": final_state.get("errors", []),
            "steps_completed": final_state.get("current_step"),
            "messages": final_state.get("messages", [])
        }
        return session_data
    
    @traceable(name="weather_check")
    def track_weather_check(self, destination: str, weather_data: Dict) -> Dict:
        '''Track Weather API call'''
        return {
            "destination": destination,
            "temperature": weather_data.get("temperature"),
            "condition": weather_data.get("condition"),
            "is_favorable": weather_data.get("is_favorable"),
            "alert": weather_data.get("alert")
        }
        
    def get_session_metrics(self, session_id: str | None = None) -> Dict:
        """Retrieve metrics for a planning session"""
        if not self.client:
            return {"error": "LangSmith not configured"}
        
        try:
            # Get runs from LangSmith
            runs = list(self.client.list_runs(
                project_name=Config.LANGSMITH_PROJECT,
                limit=10
            ))
            
            metrics = {
                "total_runs": len(runs),
                "successful_runs": sum(1 for r in runs if not r.error),
                "avg_latency": sum(r.total_tokens or 0 for r in runs) / len(runs) if runs else 0,
            }
            
            return metrics
        
        except Exception as e:
            return {"error": str(e)}
    
monitor = TripPlanningMonitor()