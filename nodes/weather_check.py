from tools.weather_tool import WeatherTool
from typing import Dict, Any, cast
from config import Config
from state_types import TripPlannerState

openweather_api_key = cast(str, Config.OPENWEATHERMAP_API_KEY)
weather_tool = WeatherTool(openweather_api_key)

def weather_check_node(state: TripPlannerState) -> TripPlannerState:
    '''Node to check weather conditions using Runnable'''
    print("🌤️  Checking weather conditions...")
    
    try:
        trip_request = state['trip_request']
        
        if trip_request is None:
            state["errors"].append("Trip request is missing")
            return state
        
        print(f"📍 Checking weather for: {trip_request.destination}")
        print(f"📅 Travel date: {trip_request.start_date}")
        
        # Fetch weather
        weather_runnable = weather_tool.get_weather_runnable()
        weather = weather_runnable.invoke({
            "city": trip_request.destination,
            "date": trip_request.start_date
        })
        
        state['weather_data'] = weather
        state['current_step'] = "weather_checked"
        
        # Print detailed weather report
        print(f"\\n🌡️  Temperature: {weather.temperature}°C")
        print(f"☁️  Condition: {weather.condition}")
        print(f"💧 Humidity: {weather.humidity}%")
        print(f"🌧️  Rain Chance: {weather.precipitation_chance}%")
        
        if not weather.is_favorable:
            print(f"\\n⚠️  WEATHER ALERT: {weather.alert}")
            print("❌ Weather is UNFAVORABLE - will suggest alternatives")
            state['messages'].append(
                f"⚠️ Weather alert for {trip_request.destination}: {weather.alert}"
            )
            state['should_replan'] = True
        else:
            print(f"\\n✅ Weather is FAVORABLE - proceeding to flight search")
            state['messages'].append(
                f"✅ Weather looks good in {trip_request.destination}! Temp: {weather.temperature}°C"
            )
        
        print("="*60 + "\\n")
        
    except Exception as e:
        print(f"❌ Error checking weather: {str(e)}")
        state['errors'].append(f"Weather check failed: {str(e)}")
        state['messages'].append("❌ Could not fetch weather data. Proceeding with caution.")
    
    return state