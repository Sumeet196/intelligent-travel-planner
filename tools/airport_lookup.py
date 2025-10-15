from config import Config
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

langsmith_api_key = Config.GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash", 
    temperature=0.7,
    api_key = langsmith_api_key
)

def get_airport_code_llm(city_name: str) -> str:
    """Use LLM to get the main airport code for a city"""
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an aviation expert. Return ONLY the 3-letter IATA airport code for the main international airport of the given city. No explanation, just the code."),
        ("user", "City: {city}\nAirport code:")
    ])
    
    chain = prompt | llm | StrOutputParser()
    
    try:
        code = chain.invoke({"city": city_name}).strip().upper()
        # Validate it's 3 letters
        if len(code) == 3 and code.isalpha():
            return code
        return city_name.upper()[:3]
    except:
        return city_name.upper()[:3]
