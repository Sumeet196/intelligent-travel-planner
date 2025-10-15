"""
Test script for itinerary generation and parsing
"""
import json
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from langchain_google_genai import ChatGoogleGenerativeAI
from config import Config

# Initialize LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash", 
    temperature=0.7,
    api_key=Config.GEMINI_API_KEY
)

def test_full_chain():
    """Test the complete chain with LLM"""
    print("\n" + "="*60)
    print("Testing Full LLM Chain")
    print("="*60)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an expert travel planner. Create a detailed day-by-day itinerary 
        based on the provided information. Be specific and practical."""),
        ("user", """Create a {duration}-day itinerary for {destination}.

Trip Type: {travel_type}
Budget: ${budget}
Weather: {weather}

Available Hotels:
{hotels}

Attractions:
{attractions}

Provide a JSON response with daily plans including:
- Morning, afternoon, and evening activities
- Meal suggestions
- Travel times
- Estimated costs

Format: {{"daily_plans": [{{"day": 1, "date": "2024-01-01", "activities": [...], "meals": [...]}}]}}
""")
    ])
    
    # Create chain
    chain = (
        prompt 
        | llm 
        | StrOutputParser()
        | RunnableLambda(lambda x: json.loads(str(x)) if isinstance(x, str) and x.strip().startswith('{') else {"daily_plans": []})
    )
    
    # Test input
    test_input = {
        "duration": 2,
        "destination": "Paris",
        "travel_type": "sightseeing",
        "budget": 2000,
        "weather": "20°C, Clear",
        "hotels": "- Hotel A: $150/night (Rating: 4.5)\n- Hotel B: $200/night (Rating: 4.8)",
        "attractions": "- Eiffel Tower: Iconic landmark\n- Louvre Museum: World-famous art museum"
    }
    
    print("\nInvoking chain with test data...")
    print(f"Destination: {test_input['destination']}")
    print(f"Duration: {test_input['duration']} days")
    
    try:
        result = chain.invoke(test_input)
        
        print("\n✅ Chain executed successfully!")
        print(f"\nResult type: {type(result)}")
        print(f"Result keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict):
            daily_plans = result.get("daily_plans", [])
            print(f"\nNumber of daily plans: {len(daily_plans)}")
            
            if daily_plans:
                print("\n📋 First Day Plan:")
                first_day = daily_plans[0]
                print(json.dumps(first_day, indent=2))
                
                # Validate structure
                required_keys = ["day", "date", "activities"]
                missing_keys = [key for key in required_keys if key not in first_day]
                
                if missing_keys:
                    print(f"\n⚠️ Missing keys: {missing_keys}")
                else:
                    print("\n✅ All required keys present!")
                    
                # Check activities structure
                if "activities" in first_day and first_day["activities"]:
                    print(f"\nNumber of activities: {len(first_day['activities'])}")
                    print("First activity:")
                    print(json.dumps(first_day['activities'][0], indent=2))
            else:
                print("\n⚠️ No daily plans generated")
        else:
            print(f"\n⚠️ Unexpected result type: {type(result)}")
            print(f"Result: {result}")
            
    except Exception as e:
        print(f"\n❌ Chain execution failed!")
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """Run all tests"""
    print("\n🧪 ITINERARY PARSING TEST SUITE\n")
    test_full_chain()
    
if __name__ == "__main__":
    main()