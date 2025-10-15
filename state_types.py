from typing import TypedDict, Annotated, Optional, List
import operator
from models import TripRequest, WeatherData, HotelOption, FlightOption, Attraction, TripItinerary

class TripPlannerState(TypedDict):
    """State type for the graph"""
    trip_request: Optional[TripRequest]
    weather_data: Optional[WeatherData]
    hotels: List[HotelOption]
    flights: List[FlightOption]
    attractions: List[Attraction]
    itinerary: Optional[TripItinerary]
    errors: Annotated[List[str], operator.add]
    current_step: str
    should_replan: bool
    messages: Annotated[List[str], operator.add]
    
    alternative_reason: Optional[str]  # "unfavorable_weather", "no_flights_available", "flights_too_expensive"
    expensive_flight_price: Optional[float]  # Store flight price if too expensive
