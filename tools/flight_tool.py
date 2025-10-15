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
        return results
    
    def _parse_flights(self, data: Dict, budget: float) -> List[FlightOption]:
        """Parse SerpAPI flight results"""
        flights = []
        
        best_flights = data.get("best_flights", [])
        other_flights = data.get("other_flights", [])
        
        all_flights = best_flights + other_flights
        
        for flight in all_flights[:10]:
            try:
                price = flight.get("price", 999999)
                
                if price > budget:
                    continue
                
                # Get first flight segment
                segments = flight.get("flights", [])
                if not segments:
                    continue
                
                first_segment = segments[0]
                last_segment = segments[-1]
                
                flight_option = FlightOption(
                    airline=first_segment.get("airline", "Unknown"),
                    departure_time=first_segment.get("departure_airport", {}).get("time", ""),
                    arrival_time=last_segment.get("arrival_airport", {}).get("time", ""),
                    duration=str(flight.get("total_duration", 0)) + " min",
                    price=float(price),
                    stops=len(segments) - 1,
                    booking_url=flight.get("booking_token", "")
                )
                flights.append(flight_option)
            except Exception as e:
                continue
        
        return sorted(flights, key=lambda x: x.price)
    
    def search_flights_runnable(self):
        """Create a Runnable for flight search"""
        def search_lambda(x: Dict[str, Any]):
            return self._search_flights(x)
        def parse_lambda(x: Dict[str, Any]):
            return self._parse_flights(
                x['data'],
                x['budget']
            )
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
        try:
            runnable = self.search_flights_runnable()
            max_flight_budget = budget * 0.6
            params = {
                "origin": origin,
                "destination": destination,
                "date": date,
                "currency": "USD",
                "budget": max_flight_budget
            }

            # ✅ Only add return_date if it's not None
            if return_date is not None:
                params["return_date"] = return_date
                params["type"] = "2"  # round trip
            else:
                params["type"] = "1"  # one-way

            result = runnable.invoke(params)
            
            return result
        except Exception as e:
            print(f"Flight search error: {e}")
            return []