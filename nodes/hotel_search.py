from typing import Dict, Any, cast
from tools.hotel_tool import SerpAPIHotelTool
from state_types import TripPlannerState
from config import Config

serpapi_key = cast(str, Config.SERPAPI_KEY)
hotel_tool = SerpAPIHotelTool(serpapi_key)

def hotel_search_node(state: TripPlannerState) -> TripPlannerState:
    """Node to search for hotels using SerpAPI Runnable"""
    print("🏨 Searching for hotels with SerpAPI...")
    
    try:
        trip_request = state["trip_request"]
        
        if trip_request is None:
            state["errors"].append("Trip request is missing")
            return state
        
        # Use Runnable chain for hotel search
        hotels = hotel_tool.search_hotels(
            destination=trip_request.destination,
            check_in=trip_request.start_date or "",
            check_out=trip_request.end_date or "",
            budget=trip_request.budget,
            adults=trip_request.num_travelers
        )
        
        state["hotels"] = hotels[:5]
        state["current_step"] = "hotels_found"
        state["messages"].append(f"🏨 Found {len(hotels)} hotels within budget")
        
    except Exception as e:
        state["errors"].append(f"Hotel search failed: {str(e)}")
        state["messages"].append("❌ Hotel search encountered issues")
    
    return state