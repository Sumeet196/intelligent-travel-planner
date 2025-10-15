from state_types import TripPlannerState

def weather_decision_node(state: TripPlannerState) -> str:
    """Decision: Check if weather is favorable"""
    weather_data = state.get("weather_data")
    
    if not weather_data or not weather_data.is_favorable:
        # Store reason for alternatives
        state["alternative_reason"] = "unfavorable_weather"
        return "suggest_alternatives"
    else:
        return "proceed_to_flights"