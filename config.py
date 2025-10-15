import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    OPENWEATHERMAP_API_KEY = os.getenv("OPENWEATHERMAP_API_KEY")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    SERPAPI_KEY = os.getenv("SERPAPI_KEY")
    
    LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
    LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "trip-planner-agent")
    LANGSMITH_TRACING = os.getenv("LANGSMITH_TRACING", "true")
    
    MODEL_NAME = 'gemini-2.5-flash'
    TEMPERATURE = 0.7
    MAX_TOKENS = 2000
    
    DEFAULT_CURRENCY = "USD"
    MAX_HOTEL_RESULTS = 10
    MAX_FLIGHT_RESULTS = 5
    
    @classmethod
    def validate(cls):
        '''Validate that required API keys are present'''
        required_keys = {
            "OPENWEATHERMAP_API_KEY": cls.OPENWEATHERMAP_API_KEY,
            "GEMINI_API_KEY": cls.GEMINI_API_KEY,
            "SERPAPI_KEY": cls.SERPAPI_KEY
        }
        
        missing = [k for k, v in required_keys.items() if not v]
        if missing:
            raise ValueError(f"Missing required API keys: {', '.join(missing)}")
        
        return True