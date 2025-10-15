from typing import Dict, Any

def should_continue(state: Dict[str, Any]) -> str:
    """Router function to determine next step"""
    current_step = state.get("current_step", "init")
    
    if current_step == "weather_checked":
        return "check_weather"
    elif current_step in ["hotels_found", "flights_found", "attractions_found"]:
        return "continue"
    elif current_step == "itinerary_complete":
        return "end"
    else:
        return "continue"