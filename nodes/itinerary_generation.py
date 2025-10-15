import os
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from models import DayPlan, TripItinerary
from state_types import TripPlannerState
from config import Config
import json

langsmith_api_key = Config.GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash", 
    temperature=0.7,
    api_key = langsmith_api_key
)

def parse_json_response(x: str) -> dict:
    """Parse JSON from LLM response, handling markdown code blocks"""
    import re

    if not isinstance(x, str):
        x = str(x)

    # Remove markdown code blocks
    x = re.sub(r'```json\s*', '', x)
    x = re.sub(r'```\s*', '', x)

    # Find JSON object
    json_match = re.search(r'\{.*\}', x, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group())
            print(f"✅ Successfully parsed JSON response")
            return parsed
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            print(f"Response preview: {x[:500]}")
            return {"daily_plans": []}

    print("⚠️ No JSON object found in response")
    return {"daily_plans": []}

def calculate_activity_costs(daily_plans):
    """Extract and sum all activity and meal costs from the itinerary"""
    import re
    total_cost = 0
    
    for day in daily_plans:
        # Extract costs from activities
        activities = day.get('activities', [])
        for activity in activities:
            cost_str = activity.get('estimated_cost', '')
            if cost_str:
                matches = re.findall(r'\$([0-9]+)', str(cost_str))
                if matches:
                    total_cost += int(matches[0])
        
        # Extract costs from meals
        meals = day.get('meals', [])
        for meal in meals:
            cost_str = meal.get('estimated_cost', '')
            if cost_str:
                matches = re.findall(r'\$([0-9]+)', str(cost_str))
                if matches:
                    total_cost += int(matches[0])
    
    return total_cost

def itinerary_generation_node(state: TripPlannerState) -> TripPlannerState:
    """Node to generate complete itinerary using LLM Runnable Chain"""
    print("\n" + "="*60)
    print("📋 GENERATING DETAILED ITINERARY")
    print("="*60)

    try:
        trip_request = state["trip_request"]
        hotels = state.get("hotels", [])
        flights = state.get("flights", [])
        attractions = state.get("attractions", [])
        weather = state.get("weather_data")

        if trip_request is None:
            state["errors"].append("Trip request is missing")
            return state

        # Check if flights are available before generating itinerary
        if not flights or len(flights) == 0:
            state["errors"].append("No flights available - cannot generate itinerary")
            state["messages"].append("❌ Itinerary not generated: No flights available for the requested route")
            print("⚠️ Skipping itinerary generation - no flights available")
            return state

        print(f"📍 Destination: {trip_request.destination}")
        print(f"📅 Duration: {trip_request.duration_days} days")
        print(f"💰 Budget: ${trip_request.budget}")
        print(f"🎯 Travel Type: {trip_request.travel_type.value}")
        
        # Create enhanced prompt with clear structure
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert travel planner creating detailed day-by-day itineraries.
You MUST provide complete information for each day including:
1. Activities with specific times (Morning, Afternoon, Evening)
2. THREE meal suggestions per day (Breakfast, Lunch, Dinner) with restaurant names
3. Estimated costs for activities
4. Travel times between locations

Always return valid JSON in the exact format specified."""),
            ("user", """Create a {duration}-day detailed itinerary for {destination}.

**Trip Details:**
- Travel Type: {travel_type}
- Total Budget: ${budget}
- Weather: {weather}
- Number of Travelers: {num_travelers}

**Available Hotels:**
{hotels}

**Top Attractions to Include:**
{attractions}

**REQUIRED JSON FORMAT:**
{{
  "daily_plans": [
    {{
      "day": 1,
      "date": "{start_date}",
      "activities": [
        {{
          "time_of_day": "Morning (9:00 AM - 12:00 PM)",
          "description": "Visit [Attraction Name] - [Details about what to do, see, and expect]",
          "travel_time": "15 minutes by metro from hotel",
          "estimated_cost": "$25 per person"
        }},
        {{
          "time_of_day": "Afternoon (2:00 PM - 5:00 PM)",
          "description": "Explore [Another Attraction] - [Specific details]",
          "travel_time": "10 minutes walk",
          "estimated_cost": "$15 per person"
        }},
        {{
          "time_of_day": "Evening (7:00 PM - 10:00 PM)",
          "description": "[Evening activity or attraction]",
          "travel_time": "20 minutes by taxi",
          "estimated_cost": "$30 per person"
        }}
      ],
      "meals": [
        {{
          "type": "Breakfast",
          "suggestion": "[Restaurant Name] - Try their [signature dishes]. Popular local breakfast spot.",
          "estimated_cost": "$15-20 per person"
        }},
        {{
          "type": "Lunch",
          "suggestion": "[Restaurant Name] - Known for [cuisine type]. Great [specific dishes].",
          "estimated_cost": "$25-30 per person"
        }},
        {{
          "type": "Dinner",
          "suggestion": "[Restaurant Name] - [Description, ambiance, specialties].",
          "estimated_cost": "$40-50 per person"
        }}
      ],
      "notes": "Useful tips for this day, weather considerations, or booking recommendations"
    }}
  ]
}}

**IMPORTANT INSTRUCTIONS:**
1. Include ALL {duration} days
2. Each day MUST have 3 activities (Morning, Afternoon, Evening)
3. Each day MUST have 3 meals (Breakfast, Lunch, Dinner) with SPECIFIC restaurant suggestions
4. Include realistic costs based on the destination
5. Suggest actual restaurants and locations in {destination}
6. Consider the {travel_type} travel type when planning activities
7. Return ONLY valid JSON, no additional text

Generate the complete itinerary now:""")
        ])
        
        # Format data for prompt
        hotels_text = "\n".join([
            f"- {h.name}: ${h.price_per_night}/night (⭐ {h.rating}/5) - {h.location}" 
            for h in hotels[:3]
        ]) if hotels else "Budget accommodation options available"

        attractions_text = "\n".join([
            f"- {a.name} ({a.category}): {a.description}" 
            for a in attractions[:8]
        ]) if attractions else "Popular tourist attractions in the area"

        # Create Runnable chain
        chain = (
            prompt 
            | llm 
            | StrOutputParser()
            | RunnableLambda(parse_json_response)
        )

        # Calculate start date
        from datetime import datetime, timedelta
        start_date_str = trip_request.start_date or datetime.now().strftime("%Y-%m-%d")
        try:
            start_date_obj = datetime.strptime(start_date_str, "%Y-%m-%d")
        except (ValueError, TypeError):
            start_date_obj = datetime.now()
            start_date_str = start_date_obj.strftime("%Y-%m-%d")

        print("\n🤖 Invoking LLM to generate itinerary...")

        response_data = chain.invoke({
            "duration": trip_request.duration_days or 7,
            "destination": trip_request.destination,
            "travel_type": trip_request.travel_type.value,
            "budget": trip_request.budget,
            "num_travelers": trip_request.num_travelers,
            "weather": f"{weather.temperature}°C, {weather.condition}" if weather else "N/A",
            "hotels": hotels_text,
            "attractions": attractions_text,
            "start_date": trip_request.start_date or datetime.now().strftime("%Y-%m-%d")
        })

        # Parse response
        daily_plans = response_data.get("daily_plans", [])
        
        if not daily_plans:
            print("⚠️ Warning: No daily plans generated by LLM")
            state["errors"].append("LLM did not generate daily plans")
        else:
            print(f"✅ Generated {len(daily_plans)} daily plans")

            # Verify each plan has meals
            for idx, plan in enumerate(daily_plans, 1):
                meals = plan.get("meals", [])
                activities = plan.get("activities", [])
                print(f"  Day {idx}: {len(activities)} activities, {len(meals)} meals")

                if not meals:
                    print(f"  ⚠️ Day {idx} has no meals!")

        # ✅ Calculate costs INCLUDING activities and meals
        hotel_cost = sum(h.price_per_night for h in hotels[:1]) * (trip_request.duration_days or 7) if hotels else 0
        flight_cost = sum(f.price for f in flights[:1]) if flights else 0
        attraction_cost = sum(a.cost or 0 for a in attractions)

        # ✅ NEW: Add activity and meal costs from itinerary
        activity_meal_cost = calculate_activity_costs(daily_plans)

        estimated_cost = hotel_cost + flight_cost + attraction_cost + activity_meal_cost

        print(f"\n💰 Cost Breakdown:")
        print(f"  Hotels: ${hotel_cost:,.2f}")
        print(f"  Flights: ${flight_cost:,.2f}")
        print(f"  Attractions: ${attraction_cost:,.2f}")
        print(f"  Activities & Meals: ${activity_meal_cost:,.2f}")  # ✅ NEW
        print(f"  Total Estimated: ${estimated_cost:,.2f}")

        # Create itinerary
        itinerary = TripItinerary(
            destination=trip_request.destination,
            start_date=trip_request.start_date or "TBD",
            end_date=trip_request.end_date or "TBD",
            total_budget=trip_request.budget,
            estimated_cost=estimated_cost,
            hotels=hotels[:3],
            flights=flights[:2],
            daily_plans=daily_plans,
            attractions=attractions,
            weather_summary=f"{weather.temperature}°C, {weather.condition}" if weather else "N/A",
            notes=f"Created for {trip_request.travel_type.value} travel"
        )

        state["itinerary"] = itinerary
        state["current_step"] = "itinerary_complete"
        state["messages"].append("✅ Itinerary created successfully!")

        print("\n✅ Itinerary generation complete!")
        print("="*60 + "\n")
        
    except Exception as e:
        print(f"\n❌ Error in itinerary generation: {str(e)}")
        import traceback
        traceback.print_exc()

        state["errors"].append(f"Itinerary generation failed: {str(e)}")
        state["messages"].append("❌ Could not generate complete itinerary")

    return state