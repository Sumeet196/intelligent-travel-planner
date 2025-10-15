from typing import Dict, Any, List
from models import HotelOption
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from serpapi import GoogleSearch

class SerpAPIHotelTool:
    '''Hotel search using SerpAPI with Runnables'''
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def _search_hotels(self, params: Dict) -> Dict:
        print("📡 Calling SerpAPI with params:", params)
        search_params = {
            "engine": "google_hotels",
            "q": f"hotels in {params['destination']}",
            "check_in_date": params.get('check_in'),
            "check_out_date": params.get('check_out'),
            "adults": params.get('adults', 1),
            "currency": params.get('currency', 'USD'),
            "gl": "us",
            "hl": "en",
            "api_key": self.api_key
        }
        
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        print("📥 Raw SerpAPI response keys:", results.keys())
        print("📥 Full SerpAPI response preview:", results if len(str(results)) < 500 else str(results)[:500] + "...")
    
        return results
    
    def _parse_hotels(self, data: Dict, budget: float) -> List[HotelOption]:
        hotels = []
        
        properties = data.get("properties", [])
        print(f"🏨 Found {len(properties)} properties in raw data")
        
        if not properties:
            print("⚠️ No 'properties' key or empty list in SerpAPI data")

        for prop in properties[:10]:
            try:
                print(f"➡️ Processing property: {prop.get('name', 'Unnamed')}")
                price_str = prop.get("rate_per_night", {}).get("lowest", "0")
                price = float(price_str.replace("$", "").replace(",", ""))
                
                if price==0 or price>budget:
                    print(f"   ❌ Skipping due to price: ${price}")
                    continue
                
                hotel = HotelOption(
                    name=prop.get("name", "Unknown Hotel"),
                    location=prop.get("description", ""),
                    price_per_night=price,
                    rating=prop.get("overall_rating", 0.0),
                    amenities=prop.get("amenities", [])[:5],
                    url=prop.get("link", ""),
                    distance_from_center=None
                )
                
                hotels.append(hotel)
                
            except Exception as e:
                print(f"   ⚠️ Error parsing hotel: {e}")
                continue
        print(f"✅ Parsed {len(hotels)} hotel(s) under budget")
        return sorted(hotels, key=lambda x: x.price_per_night)
    
    def search_hotels_runnable(self):
        def search_lambda(x: Dict[str, Any]):
            return self._search_hotels(x)
        def parse_lambda(x: Dict[str, Any]):
            return self._parse_hotels(
                x['data'],
                x['budget']
            )
        search_runnable = RunnableLambda(search_lambda)
        parse_runnable = RunnableLambda(parse_lambda)
        
        chain = (
            RunnablePassthrough.assign(data=search_runnable) | parse_runnable
        )
        return chain
    
    def search_hotels(self, destination: str, check_in: str, check_out: str, budget: float, adults: int = 1) -> List[HotelOption]:
        """Search for hotels using Runnable"""
        try:
            runnable = self.search_hotels_runnable()
            budget_per_night = budget * 0.3 / 7  # Assume 30% budget, 7 nights
            
            result = runnable.invoke({
                "destination": destination,
                "check_in": check_in,
                "check_out": check_out,
                "adults": adults,
                "currency": "USD",
                "budget": budget_per_night
            })
            
            return result
        except Exception as e:
            print(f"Hotel search error: {e}")
            return []