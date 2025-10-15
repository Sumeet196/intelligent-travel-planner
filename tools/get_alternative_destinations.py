from typing import List

def get_alternative_destinations(original: str, reason: str) -> List[str]:
    """Suggest alternative destinations based on weather issues"""
    alternatives_map = {
        "cold": ["warmer locations"],
        "hot": ["cooler locations"],
        "rain": ["dry climate destinations"],
        "storm": ["safer destinations"]
    }
    
    return [f"Alternative to {original} 1", f"Alternative to {original} 2"]