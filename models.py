from pydantic import BaseModel, Field
from typing import Optional, List, Dict, TypedDict, Any
from enum import Enum

class TravelType(str, Enum):
    '''Types of travel preferences'''
    RELAXATION = "relaxation"
    ADVENTURE = "adventure"
    SIGHTSEEING = "sightseeing"
    BUSINESS = "business"
    FAMILY = "family"
    
class TripRequest(BaseModel):
    """User's trip requirements"""
    origin: str = Field(..., description="Origin/departure city")
    destination: str = Field(..., description="Destination city or country")
    start_date: Optional[str] = Field(None, description="Trip start date (YYYY-MM-DD)")
    end_date: Optional[str] = Field(None, description="Trip end date (YYYY-MM-DD)")
    duration_days: Optional[int] = Field(None, description="Trip duration in days")
    budget: float = Field(..., description="Total budget for the trip")
    currency: str = Field(default="USD", description="Currency code")
    travel_type: TravelType = Field(default=TravelType.SIGHTSEEING)
    num_travelers: int = Field(default=1, description="Number of travelers")
    preferences: Optional[List[str]] = Field(default_factory=list)

class WeatherData(BaseModel):
    '''Weather information for destination'''
    location: str
    date: str
    temperature: float
    condition: str
    humidity: int
    wind_speed: float
    precipitation_chance: float
    is_favorable: bool
    alert: Optional[str] = None

    
class HotelOption(BaseModel):
    """Hotel search result"""
    name: str
    location: str
    price_per_night: float
    rating: Optional[float] = None
    amenities: List[str] = Field(default_factory=list)
    url: Optional[str] = None
    distance_from_center: Optional[float] = None


class FlightOption(BaseModel):
    """Flight search result"""
    airline: str
    departure_time: str
    arrival_time: str
    duration: str
    price: float
    stops: int = 0
    booking_url: Optional[str] = None


class Attraction(BaseModel):
    """Tourist attraction information"""
    name: str
    description: str
    category: str
    rating: Optional[float] = None
    estimated_time: Optional[str] = None
    cost: Optional[float] = None


class DayPlan(BaseModel):
    """Single day itinerary"""
    day: int
    date: str
    activities: List[Dict[str, str]]
    meals: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class TripItinerary(BaseModel):
    """Complete trip itinerary"""
    destination: str
    start_date: str
    end_date: str
    total_budget: float
    estimated_cost: float
    hotels: List[HotelOption]
    flights: Optional[List[FlightOption]] = Field(default_factory=list)
    daily_plans: List[Dict[str, Any]]
    attractions: List[Attraction]
    weather_summary: str
    alternative_dates: Optional[List[str]] = Field(default_factory=list)
    notes: Optional[str] = None


class GraphState(BaseModel):
    """State for LangGraph workflow"""
    trip_request: Optional[TripRequest] = None
    weather_data: Optional[WeatherData] = None
    hotels: List[HotelOption] = Field(default_factory=list)
    flights: List[FlightOption] = Field(default_factory=list)
    attractions: List[Attraction] = Field(default_factory=list)
    itinerary: Optional[TripItinerary] = None
    errors: List[str] = Field(default_factory=list)
    current_step: str = "init"
    should_replan: bool = False

    messages: List[str] = Field(default_factory=list)
