from typing import List, Dict, Any
from serpapi import GoogleSearch
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from models import FlightOption

class SerpAPIFlightTool:
    """Flight search using SerpAPI with Runnable"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def _search_flights(self, params: Dict) -> Dict:
        """Internal method to search flights via SerpAPI"""
        print(f"🔍 DEBUG: Searching flights from {params.get('origin')} to {params.get('destination')}")
        
        search_params = {
            "engine": "google_flights",
            "departure_id": params['origin'],
            "arrival_id": params['destination'],
            "outbound_date": params['date'],
            "currency": params.get('currency', 'USD'),
            "hl": "en",
            "gl": "us",
            "api_key": self.api_key
        }
        
        if params.get('return_date'):
            search_params["return_date"] = params["return_date"]
        
        search = GoogleSearch(search_params)
        results = search.get_dict()
        
        # ✅ DEBUG: Check what we got back
        print(f"🔍 DEBUG: SerpAPI response keys: {results.keys() if results else 'None'}")
        if results:
            print(f"🔍 DEBUG: Has 'best_flights': {'best_flights' in results}")
            print(f"🔍 DEBUG: Has 'other_flights': {'other_flights' in results}")
            if 'best_flights' in results:
                print(f"🔍 DEBUG: Number of best_flights: {len(results.get('best_flights', []))}")
        
        return results
    
    def _parse_flights(self, data: Dict, budget: float) -> List[FlightOption]:
        """Parse SerpAPI flight results"""
        print(f"🔍 DEBUG: _parse_flights called with budget: ${budget:,.2f}")
        print(f"🔍 DEBUG: Data type: {type(data)}")
        print(f"🔍 DEBUG: Data keys: {data.keys() if isinstance(data, dict) else 'Not a dict'}")
        
        flights = []
        
        if not isinstance(data, dict):
            print("❌ DEBUG: Data is not a dictionary!")
            return []
        
        best_flights = data.get("best_flights", [])
        other_flights = data.get("other_flights", [])
        
        print(f"🔍 DEBUG: Found {len(best_flights)} best flights, {len(other_flights)} other flights")
        
        all_flights = best_flights + other_flights
        
        if not all_flights:
            print("❌ DEBUG: No flights found in response!")
            return []
        
        for idx, flight in enumerate(all_flights[:10]):
            try:
                price = flight.get("price", 999999)
                
                print(f"🔍 DEBUG: Flight {idx+1}: Price=${price}, Budget=${budget}")
                
                if price > budget:
                    print(f"   ⏭️ Skipping - too expensive")
                    continue
                
                # Get first flight segment
                segments = flight.get("flights", [])
                if not segments:
                    print(f"   ❌ No flight segments found")
                    continue
                
                print(f"   ✅ Flight has {len(segments)} segments")
                
                first_segment = segments[0]
                last_segment = segments[-1]
                
                airline = first_segment.get("airline", "Unknown")
                dep_time = first_segment.get("departure_airport", {}).get("time", "")
                arr_time = last_segment.get("arrival_airport", {}).get("time", "")
                
                print(f"   ✅ Parsed: {airline} - ${price}")
                
                flight_option = FlightOption(
                    airline=airline,
                    departure_time=dep_time,
                    arrival_time=arr_time,
                    duration=str(flight.get("total_duration", 0)) + " min",
                    price=float(price),
                    stops=len(segments) - 1,
                    booking_url=flight.get("booking_token", "")
                )
                flights.append(flight_option)
                
            except Exception as e:
                print(f"❌ DEBUG: Error parsing flight {idx+1}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
        
        print(f"✅ DEBUG: Successfully parsed {len(flights)} flights")
        return sorted(flights, key=lambda x: x.price)
    
    def search_flights_runnable(self):
        """Create a Runnable for flight search"""
        def search_lambda(x: Dict[str, Any]):
            result = self._search_flights(x)
            print(f"🔍 DEBUG: search_lambda returning type: {type(result)}")
            return result
        
        def parse_lambda(x: Dict[str, Any]):
            print(f"🔍 DEBUG: parse_lambda received: {type(x)}, keys: {x.keys() if isinstance(x, dict) else 'Not dict'}")
            
            # ✅ FIX: Check if data exists and handle it properly
            if 'data' in x:
                data = x['data']
                budget = x.get('budget', float('inf'))
            else:
                # If 'data' key doesn't exist, x itself might be the data
                print("⚠️ DEBUG: 'data' key not found, using x as data")
                data = x
                budget = x.get('budget', float('inf'))
            
            return self._parse_flights(data, budget)
        
        search_runnable = RunnableLambda(search_lambda)
        parse_runnable = RunnableLambda(parse_lambda)
        
        # Chain: search -> parse
        chain = (
            RunnablePassthrough.assign(data=search_runnable)
            | parse_runnable
        )
        
        return chain
    
    def search_flights(self, 
                       origin: str, 
                       destination: str, 
                       date: str, 
                       budget: float, 
                       return_date: str | None = None) -> List[FlightOption]:
        """Search for flights using Runnable"""
        print(f"\n{'='*60}")
        print(f"✈️ FLIGHT SEARCH: {origin} → {destination}")
        print(f"{'='*60}")
        
        try:
            runnable = self.search_flights_runnable()
            max_flight_budget = budget * 0.6
            
            print(f"💰 Total budget: ${budget:,.2f}")
            print(f"💰 Flight budget (60%): ${max_flight_budget:,.2f}")
            
            params = {
                "origin": origin,
                "destination": destination,
                "date": date,
                "currency": "USD",
                "budget": max_flight_budget
            }

            if return_date is not None:
                params["return_date"] = return_date
                params["type"] = "2"  # round trip
            else:
                params["type"] = "1"  # one-way

            print(f"🔍 DEBUG: Invoking runnable with params: {params.keys()}")
            result = runnable.invoke(params)
            
            print(f"✅ DEBUG: Runnable returned {len(result) if result else 0} flights")
            print(f"{'='*60}\n")
            
            return result
        except Exception as e:
            print(f"❌ Flight search error: {e}")
            import traceback
            traceback.print_exc()
            return []
