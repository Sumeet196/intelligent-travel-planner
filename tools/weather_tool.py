from typing import Optional, Dict, Any
from models import WeatherData
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
import requests
from datetime import datetime

class WeatherTool:
    '''OpenWeatherMap API Tool'''
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "http://api.openweathermap.org/data/2.5"
        
    def _fetch_weather(self, city: str) -> Dict:
        '''Fetch weather for the day'''
        url = f"{self.base_url}/weather"
        params = {
            "q": city,
            "appid": self.api_key,
            "units": "metric"
        }
            
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
            
    def _parse_weather(self, data: Dict, city: str, date: Optional[str]=None) -> WeatherData:
        '''
        Parse weather API response into WeatherData model
        '''
        temp = data['main']['temp']
        condition = data['weather'][0]['main']
        rain_chance = data.get("rain", {}).get("1h", 0)
            
        is_favorable = (
            15 <= temp <= 30 and
            condition not in ['Thunderstorm', 'Snow'] and
            rain_chance < 10
        )
        
        alert = None
        if not is_favorable:
            if temp < 15:
                alert = "Cold weather expected."
            elif temp > 30:
                alert = "Very hot weather expected."
            elif condition in ['Thunderstorm', 'Snow']:
                alert = f"Severe weather: {condition}"
            elif rain_chance >= 10:
                alert = "High chance of rain."
                
        return WeatherData(
            location=city,
            date=date or datetime.now().strftime("%Y-%m-%d"),
            temperature=temp,
            condition=condition,
            humidity=data['main']['humidity'],
            wind_speed=data['wind']['speed'],
            precipitation_chance=rain_chance,
            is_favorable=is_favorable,
            alert=alert
        )
    
    def get_weather_runnable(self):
        '''
        Create a Runnable for weather fetching and parsing
        '''
        def fetch_step(x: Dict[str, Any]) -> str:
            return x["city"]
        def parse_step(x: Dict[str, Any]) -> WeatherData:
            return self._parse_weather(
                x["data"],
                x["city"],
                x.get("date")
            )
        fetch_runnable = RunnableLambda(fetch_step) | RunnableLambda(self._fetch_weather)
        parse_runnable = RunnableLambda(parse_step)
        
        chain = (
            RunnablePassthrough.assign(data=fetch_runnable) | parse_runnable
        )
        return chain
    
    def get_weather_forecast(self, city: str, date: Optional[str]=None) -> WeatherData:
        try: 
            runnable = self.get_weather_runnable()
            result = runnable.invoke({
                "city": city,
                "date": date
            })
            return result
        except Exception as e:
            raise Exception(f"Weather API error: {str(e)}")