from typing import Dict, Any, cast
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from state_types import TripPlannerState
from config import Config

langsmith_api_key = Config.GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    temperature=0.7,
    api_key = langsmith_api_key
)

def alternative_suggestion_node(state: TripPlannerState) -> TripPlannerState:
    """Node to suggest alternatives - shows WHY alternatives are needed"""
    print("\\n" + "="*60)
    print("💡 ALTERNATIVE SUGGESTIONS")
    print("="*60)
    
    try:
        weather = state.get("weather_data")
        if weather:
            weather_desc = f"{weather.temperature}°C, {weather.condition}"
            weather_favorable = weather.is_favorable
        else:
            weather_desc = "Weather data unavailable"
            weather_favorable = False
        flights = state.get("flights", [])
        trip_request = state["trip_request"]
        
        if trip_request is None:
            state["errors"].append("Trip request is missing")
            return state
        
        # Determine WHY we're showing alternatives
        reason = state.get("alternative_reason", "unknown")
        
        print(f"\\n🎯 Original Destination: {trip_request.destination}")
        print(f"💰 Budget: ${trip_request.budget:,.2f}")
        
        # Display specific reason
        if reason == "unfavorable_weather":
            print(f"\\n⚠️  REASON: Weather conditions are unfavorable")
            if weather and weather.alert:
                print(f"   Alert: {weather.alert}")
                print(f"   Temperature: {weather.temperature}°C")
                print(f"   Condition: {weather.condition}")
            reason_text = f"unfavorable weather conditions ({weather.condition}, {weather.temperature}°C)"
            
        elif reason == "no_flights_available":
            print(f"\\n⚠️  REASON: No flights available")
            print(f"   Route: {trip_request.origin} → {trip_request.destination}")
            print(f"   Date: {trip_request.start_date}")
            reason_text = "no flights available for this route"
            
        elif reason == "flights_too_expensive":
            expensive_price = state.get("expensive_flight_price")
            if expensive_price:
                percentage = (expensive_price / trip_request.budget) * 100
                print(f"\\n⚠️  REASON: Flights exceed budget")
                print(f"   Cheapest flight: ${expensive_price:,.2f}")
                print(f"   Budget usage: {percentage:.0f}%")
                print(f"   Remaining for hotels/activities: ${trip_request.budget - expensive_price:,.2f}")
                reason_text = f"flights are too expensive (${expensive_price:,.2f}, {percentage:.0f}% of budget)"
            else:
                reason_text = "flights exceed budget threshold"
        else:
            print(f"\\n⚠️  REASON: General availability issues")
            reason_text = "availability issues"
        
        print(f"\\n🔍 Searching for better alternatives...")
        
        # Use LLM to suggest alternatives
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel expert. Suggest 3 alternative destinations based on the issue.
Focus on destinations that solve the specific problem (better weather, cheaper flights, or better availability)."""),
            ("user", """The trip to {destination} cannot proceed due to: {reason}.

Budget: ${budget}
Travel Type: {travel_type}
Duration: {duration} days

Suggest 3 alternative destinations that:
1. Address the specific issue
2. Match the travel type and preferences
3. Are within or below the budget

For each alternative, provide:
- Destination name
- Why it solves the problem
- Expected weather
- Approximate flight cost from {origin}
- Top 2-3 attractions

Format as a clear, numbered list.""")
        ])
        
        chain = prompt | llm | StrOutputParser()
        
        response = chain.invoke({
            "destination": trip_request.destination,
            "reason": reason_text,
            "budget": trip_request.budget,
            "travel_type": trip_request.travel_type.value,
            "duration": trip_request.duration_days or 7,
            "origin": trip_request.origin
        })
        
        # Format the output
        header = f"\\n{'─'*60}\\n"
        header += f"💡 ALTERNATIVE DESTINATIONS\\n"
        header += f"{'─'*60}\\n"
        header += f"📍 Original: {trip_request.destination}\\n"
        header += f"⚠️  Issue: {reason_text.capitalize()}\\n"
        header += f"💰 Budget: ${trip_request.budget:,.2f}\\n"
        header += f"{'─'*60}\\n\\n"
        
        full_message = header + response
        
        state["messages"].append(full_message)
        state["current_step"] = "alternatives_suggested"
        
        print(f"\\n✅ Alternative suggestions generated!")
        print("="*60 + "\\n")
        
    except Exception as e:
        state["errors"].append(f"Alternative suggestion failed: {str(e)}")
        state["messages"].append(f"❌ Could not generate alternatives: {str(e)}")
        print(f"❌ Error: {str(e)}")
    

    return state
