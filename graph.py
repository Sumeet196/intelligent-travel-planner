from langgraph.graph import StateGraph, END
from state_types import TripPlannerState
from models import TripRequest
from typing import cast, Generator

from nodes import (
    weather_check_node,
    weather_decision_node,
    hotel_search_node,
    flight_search_node,
    attraction_search_node,
    itinerary_generation_node,
    alternative_suggestion_node,
    flight_budget_decision
)


def create_trip_planner_graph():
    """
    Create and configure LangGraph workflow
    Order: Weather -> Flights -> Hotels -> Attractions -> Itinerary -> Alternatives
    """
    workflow = StateGraph(TripPlannerState)

    # Add all nodes
    workflow.add_node("check_weather", weather_check_node)
    workflow.add_node("search_flights", flight_search_node)
    workflow.add_node("search_hotels", hotel_search_node)
    workflow.add_node("search_attractions", attraction_search_node)
    workflow.add_node("generate_itinerary", itinerary_generation_node)
    workflow.add_node("suggest_alternatives", alternative_suggestion_node)

    # Set entry point to weather check
    workflow.set_entry_point("check_weather")
    
    # After weather check: favorable → flights, unfavorable → alternatives
    workflow.add_conditional_edges(
        "check_weather",
        weather_decision_node,
        {
            "proceed_to_flights": "search_flights",
            "suggest_alternatives": "suggest_alternatives"
        }
    )

    # After flights: available & affordable → hotels, otherwise → alternatives
    workflow.add_conditional_edges(
        "search_flights",
        flight_budget_decision,
        {
            "proceed_to_hotels": "search_hotels",
            "suggest_alternatives": "suggest_alternatives"
        }
    )

    # Continue normal flow
    workflow.add_edge("search_hotels", "search_attractions")
    workflow.add_edge("search_attractions", "generate_itinerary")
    workflow.add_edge("generate_itinerary", END)
    workflow.add_edge("suggest_alternatives", END)
    
    app = workflow.compile()
    return app

def run_trip_planner(trip_request: TripRequest) -> dict:
    """
    Execute the trip planner workflow
    """
    app = create_trip_planner_graph()

    initial_state = {
        "trip_request": trip_request,
        "weather_data": None,
        "hotels": [],
        "flights": [],
        "attractions": [],
        "itinerary": None,
        "errors": [],
        "current_step": "init",
        "should_replan": False,
        "messages": [],
        "alternative_reason": None,
        "expensive_flight_price": None
    }

    initial_state = TripPlannerState(**initial_state)
    final_state = app.invoke(initial_state)

    return final_state

def run_trip_planner_stepwise(trip_request: TripRequest) -> Generator[TripPlannerState, None, None]:
    """
    Yield intermediate states after each node with proper decision logic.
    Order: Weather -> Flights -> Hotels -> Attractions -> Itinerary (or Alternatives)

    This allows UI to update in real-time after each step.
    """
    state: TripPlannerState = cast(TripPlannerState, {
        "trip_request": trip_request,
        "weather_data": None,
        "hotels": [],
        "flights": [],
        "attractions": [],
        "itinerary": None,
        "errors": [],
        "current_step": "init",
        "should_replan": False,
        "messages": [],
        "alternative_reason": None,
        "expensive_flight_price": None
    })

    # Step 1: Weather Check
    try:
        from nodes import weather_check_node, weather_decision_node

        state = weather_check_node(state)
        state["current_step"] = "check_weather"
        yield state

        # Check weather decision
        weather_decision = weather_decision_node(state)

        if weather_decision == "suggest_alternatives":
            # Weather is bad - go to alternatives
            state["alternative_reason"] = "unfavorable_weather"
            state["current_step"] = "weather_unfavorable"

            try:
                from nodes import alternative_suggestion_node
                state = alternative_suggestion_node(state)
                state["current_step"] = "alternatives_suggested"
                yield state
            except Exception as e:
                state["errors"].append(f"Alternative suggestion failed: {str(e)}")
                yield state
            return

    except Exception as e:
        state["errors"].append(f"Weather step failed: {str(e)}")
        yield state
        return

    # Step 2: Flight Search (only if weather is good)
    try:
        from nodes import flight_search_node, flight_budget_decision

        state = flight_search_node(state)
        state["current_step"] = "search_flights"
        yield state

        # Check flight availability and budget
        flight_decision = flight_budget_decision(state)

        if flight_decision == "suggest_alternatives":
            # Flights are unavailable or too expensive
            state["current_step"] = "flights_issue"

            try:
                from nodes import alternative_suggestion_node
                state = alternative_suggestion_node(state)
                state["current_step"] = "alternatives_suggested"
                yield state
            except Exception as e:
                state["errors"].append(f"Alternative suggestion failed: {str(e)}")
                yield state
            return

    except Exception as e:
        state["errors"].append(f"Flight step failed: {str(e)}")
        state["messages"].append("❌ Flight search failed. Cannot proceed with itinerary.")
        yield state
        return

    # Step 3: Hotel Search (only if flights are good)
    try:
        from nodes import hotel_search_node
        state = hotel_search_node(state)
        state["current_step"] = "search_hotels"
        yield state
    except Exception as e:
        state["errors"].append(f"Hotel step failed: {str(e)}")
        yield state

    # Step 4: Attractions
    try:
        from nodes import attraction_search_node
        state = attraction_search_node(state)
        state["current_step"] = "search_attractions"
        yield state
    except Exception as e:
        state["errors"].append(f"Attraction step failed: {str(e)}")
        yield state

    # Step 5: Itinerary Generation (final step)
    try:
        from nodes import itinerary_generation_node
        state = itinerary_generation_node(state)
        state["current_step"] = "generate_itinerary"
        yield state
    except Exception as e:
        state["errors"].append(f"Itinerary step failed: {str(e)}")
        yield state