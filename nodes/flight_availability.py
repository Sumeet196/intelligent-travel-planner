from state_types import TripPlannerState

def flight_budget_decision(state: TripPlannerState) -> str:
    """Decision: Check if flights are available and within budget"""
    flights = state.get("flights", [])
    trip_request = state.get("trip_request")
    
    if trip_request is None:
        state["errors"].append("Trip request is missing")
        return 'suggest_alternatives'
    
    # No flights found
    if not flights or len(flights) == 0:
        state["alternative_reason"] = "no_flights_available"
        return "suggest_alternatives"
    
    # Check if cheapest flight is within reasonable budget
    cheapest_flight = min(flights, key=lambda f: f.price)
    
    # Flight should not consume more than 60% of total budget
    flight_percentage = (cheapest_flight.price / trip_request.budget) * 100
    
    if flight_percentage > 60:
        state["alternative_reason"] = "flights_too_expensive"
        state["expensive_flight_price"] = cheapest_flight.price
        return "suggest_alternatives"
    
    # Flights are good, proceed
    return "proceed_to_hotels"