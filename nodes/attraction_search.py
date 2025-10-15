from typing import Dict, Any, cast
from tools.attraction_tool import SerpAPIAttractionTool
from state_types import TripPlannerState
from config import Config

serp_api = cast(str, Config.SERPAPI_KEY)
attraction_tool = SerpAPIAttractionTool(serp_api)

def attraction_search_node(state: TripPlannerState) -> TripPlannerState:
    """Node to find attractions using SerpAPI + LLM Runnable"""
    print("🎯 Finding attractions with SerpAPI + LLM...")
    
    try:
        trip_request = state["trip_request"]
        
        if trip_request is None:
            state["errors"].append("Trip request is missing")
            return state
        
        # Use Runnable chain for attraction search
        attractions = attraction_tool.search_attractions(trip_request.destination)
        
        state["attractions"] = attractions
        state["current_step"] = "attractions_found"
        state["messages"].append(f"🎯 Found {len(attractions)} attractions")
        
    except Exception as e:
        state["errors"].append(f"Attraction search failed: {str(e)}")
    
    return state