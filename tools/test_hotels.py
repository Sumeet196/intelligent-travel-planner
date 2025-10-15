from tools.hotel_tool import SerpAPIHotelTool  # Adjust the import path to your module
import os
from dotenv import load_dotenv

# Load your SerpAPI key from environment (recommended)
load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")

def test_hotel_search():
    if not API_KEY:
        print("❌ SERPAPI_KEY not found in environment variables.")
        return

    tool = SerpAPIHotelTool(api_key=API_KEY)
    
    # Sample parameters for test search
    destination = "Mumbai"
    check_in = "2025-11-01"
    check_out = "2025-11-04"
    budget = 5000
    adults = 1

    print(f"🔍 Searching hotels in {destination} from {check_in} to {check_out}...")
    results = tool.search_hotels(destination, check_in, check_out, budget, adults)

    if not results:
        print("❌ No hotels found or API error occurred.")
    else:
        print(f"✅ Found {len(results)} hotel(s):\n")
        for i, hotel in enumerate(results, start=1):
            print(f"{i}. {hotel.name}")
            print(f"   Price: ${hotel.price_per_night:.2f}/night")
            print(f"   Rating: {hotel.rating}")
            print(f"   Location: {hotel.location}")
            print(f"   Amenities: {', '.join(hotel.amenities)}")
            print(f"   URL: {hotel.url}\n")

if __name__ == "__main__":
    test_hotel_search()
