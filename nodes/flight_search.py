from typing import Dict, Any, cast
from tools.flight_tool import SerpAPIFlightTool
from tools.airport_lookup import get_airport_code_llm
from state_types import TripPlannerState
from config import Config

serp_api = cast(str, Config.SERPAPI_KEY)
flight_tool = SerpAPIFlightTool(serp_api)

def flight_search_node(state: TripPlannerState) -> TripPlannerState:
    """Node to search for flights using SerpAPI Runnable"""
    print("✈️  Searching for flights with SerpAPI...")
    
    try:
        trip_request = state["trip_request"]
        
        if trip_request is None:
            state["errors"].append("Trip request is missing")
            return state
        
        print(f"🛫 Origin: {trip_request.origin}")
        print(f"🛬 Destination: {trip_request.destination}")
        print(f"📅 Departure: {trip_request.start_date}")
        print(f"💰 Budget: ${trip_request.budget:,.2f}")
        
        # Get airport codes
        origin_code = get_airport_code_llm(trip_request.origin)
        dest_code = get_airport_code_llm(trip_request.destination)
        
        print(f"\\n🔍 Searching flights: {origin_code} → {dest_code}")
        
        # Search flights
        flights = flight_tool.search_flights(
            origin=origin_code,
            destination=dest_code,
            date=trip_request.start_date or "",
            return_date=trip_request.end_date or "",
            budget=trip_request.budget
        )
        print("="*60)
        print("DEBUG: Full SerpAPI Response:")
        print(json.dumps(result, indent=2)[:1000])  # First 1000 chars
        print("="*60)
        
        state["flights"] = flights[:3]
        state["current_step"] = "flights_found"
        
        # Analyze flight availability and budget
        if not flights or len(flights) == 0:
            print("\\n❌ NO FLIGHTS FOUND")
            print("   Will suggest alternative destinations")
            state["messages"].append("❌ No flights available for this route")
        else:
            print(f"\\n✅ Found {len(flights)} flights")
            
            # Show top 3 flights
            for idx, flight in enumerate(flights[:3], 1):
                print(f"\\n  {idx}. {flight.airline}")
                print(f"     Price: ${flight.price:,.2f}")
                print(f"     Duration: {flight.duration}")
                print(f"     Stops: {flight.stops}")
            
            # Check budget
            cheapest = min(flights, key=lambda f: f.price)
            flight_percentage = (cheapest.price / trip_request.budget) * 100
            
            print(f"\\n💵 Cheapest flight: ${cheapest.price:,.2f}")
            print(f"📊 Budget usage: {flight_percentage:.1f}% of total budget")
            
            if flight_percentage > 60:
                print(f"\\n⚠️  BUDGET ALERT: Flights consume {flight_percentage:.0f}% of budget")
                print("   This leaves insufficient budget for accommodation and activities")
                print("   Will suggest alternative destinations with cheaper flights")
                state["messages"].append(
                    f"⚠️ Flights too expensive: ${cheapest.price:,.2f} ({flight_percentage:.0f}% of budget)"
                )
            else:
                print(f"\\n✅ Flights are WITHIN BUDGET - proceeding to hotels")
                state["messages"].append(
                    f"✅ Found {len(flights)} flights from {trip_request.origin}"
                )
        
        print("="*60 + "\\n")
        
    except Exception as e:
        print(f"❌ Error searching flights: {str(e)}")
        state["errors"].append(f"Flight search failed: {str(e)}")
        state["messages"].append("⚠️ Flight search had issues")
    

    return state
