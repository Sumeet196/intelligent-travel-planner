from typing import List, Dict, Any, cast
from serpapi import GoogleSearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda, RunnablePassthrough
from models import Attraction
from config import Config

langsmith_api_key = Config.GEMINI_API_KEY

llm = ChatGoogleGenerativeAI(
    model = "gemini-2.5-flash",
    temperature=0.7,
    api_key = langsmith_api_key
)

class SerpAPIAttractionTool:
    """Attraction search using SerpAPI with Runnable and LLM"""
    
    def __init__(self, api_key: str, llm=llm):
        self.api_key = api_key
        self.llm = llm
    
    def _search_attractions(self, destination: str) -> Dict:
        """Search for attractions using SerpAPI"""
        search_params = {
            "engine": "google",
            "q": f"top tourist attractions in {destination}",
            "num": 10,
            "api_key": self.api_key
        }
        
        search = GoogleSearch(search_params)
        results = search.get_dict()
        return results
    
    def _parse_llm_response(self, response: str) -> List[Attraction]:
        """Parse LLM JSON response into Attraction objects"""
        import json
        import re
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                return [Attraction(**item) for item in data]
        except:
            pass
        
        # Fallback: return empty list
        return []
    
    def _extract_attractions_with_llm(self, search_results: Dict, destination: str) -> List[Attraction]:
        """Use LLM to extract and structure attraction data"""
        # Extract organic results
        organic_results = search_results.get("organic_results", [])
        
        if not organic_results:
            return []
        
        # Create text summary of results
        results_text = "\n".join([
            f"- {r.get('title', '')}: {r.get('snippet', '')}"
            for r in organic_results[:5]
        ])
        
        # Runnable chain with LLM
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a travel expert. Extract tourist attractions from search results.
Return a JSON array with format: [{{"name": "...", "description": "...", "category": "...", "rating": 4.5}}]
Categories: Museum, Landmark, Nature, Entertainment, Shopping, Religious, Historical"""),
            ("user", "Destination: {destination}\n\nSearch Results:\n{results}\n\nExtract top 5 attractions:")
        ])

        chain = (
            prompt 
            | self.llm 
            | StrOutputParser()
            | RunnableLambda(lambda x: self._parse_llm_response(cast(str, x)))
        )
        
        attractions = chain.invoke({
            "destination": destination,
            "results": results_text
        })
        
        return attractions
    
    def search_attractions_runnable(self):
        """Create Runnable for attraction search"""
        
        def search_lambda(x: Dict[str, Any]):
            return self._search_attractions(x['destination'])
        def parse_lambda(x: Dict[str, Any]):
            return self._extract_attractions_with_llm(
                x['data'],
                x['destination']
            )
        search_runnable = RunnableLambda(search_lambda)
        extract_runnable = RunnableLambda(parse_lambda)
        
        chain = (
            RunnablePassthrough.assign(data=search_runnable)
            | extract_runnable
        )
        
        return chain
    
    def search_attractions(self, destination: str) -> List[Attraction]:
        """Search for attractions using Runnable"""
        try:
            runnable = self.search_attractions_runnable()
            result = runnable.invoke({"destination": destination})
            return result
        except Exception as e:
            print(f"Attraction search error: {e}")
            return []