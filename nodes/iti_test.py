# from models import HotelOption, Attraction
# from state_types import TripPlannerState
# from nodes.itinerary_generation import itinerary_generation_node  # or wherever the node is
# from enum import Enum

# # Mock TravelType enum (if you have one in your TripRequest model)
# class TravelType(Enum):
#     RELAXATION = "relaxation"
#     ADVENTURE = "adventure"

# # Mock TripRequest object
# class TripRequestMock:
#     destination = "Paris"
#     start_date = "2025-10-15"
#     end_date = "2025-10-20"
#     duration_days = 5
#     travel_type = TravelType.RELAXATION
#     budget = 2000

# # Mock hotels
# mock_hotels = [
#     HotelOption(name="Paris Grand Hotel", location="City Center", price_per_night=150, rating=4.5, amenities=["WiFi"], distance_from_center=0.5),
#     HotelOption(name="Budget Inn Paris", location="City Center", price_per_night=80, rating=4.0, amenities=["WiFi"], distance_from_center=1.0)
# ]

# # Mock attractions
# mock_attractions = [
#     Attraction(name="Eiffel Tower", description="Iconic tower", cost=25),
#     Attraction(name="Louvre Museum", description="Famous museum", cost=20)
# ]

# # Mock weather
# class WeatherMock:
#     temperature = 22
#     condition = "Clear"
#     is_favorable = True

# # Build the state
# mock_state: TripPlannerState = {
#     "trip_request": TripRequestMock(),
#     "hotels": mock_hotels,
#     "attractions": mock_attractions,
#     "flights": [],       # optional
#     "weather_data": WeatherMock(),
#     "messages": [],
#     "errors": [],
#     "current_step": "init",
#     "should_replan": False,
#     "itinerary": None
# }

# # Run the node
# updated_state = itinerary_generation_node(mock_state)

# # Inspect the result
# print(updated_state["messages"])
# print(updated_state["itinerary"])
