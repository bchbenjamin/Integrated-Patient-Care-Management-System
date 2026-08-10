import time
import httpx
from typing import List, Dict, Tuple

# In-memory cache: lowercase_query -> (result_list, expiry_timestamp)
_rxnorm_cache: Dict[str, Tuple[List[str], float]] = {}
CACHE_TTL = 300.0

async def search_medicines_rxnorm(query: str) -> List[str]:
    query = query.strip()
    if not query:
        return []
    
    cache_key = query.lower()
    now = time.time()
    
    # Check cache
    if cache_key in _rxnorm_cache:
        cached_results, expiry = _rxnorm_cache[cache_key]
        if now < expiry:
            return cached_results
            
    # Fetch from API
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://rxnav.nlm.nih.gov/REST/approximateTerm.json?term={query}&maxEntries=10",
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results = []
                approximate_group = data.get("approximateGroup", {})
                candidates = approximate_group.get("candidate", [])
                
                if candidates:
                    for candidate in candidates:
                        name = candidate.get("name")
                        if name and name not in results:
                            results.append(name)
                
                _rxnorm_cache[cache_key] = (results, now + CACHE_TTL)
                return results
                
    except Exception:
        pass
        
    return []


async def get_medicine_full_details(name: str) -> dict:
    """Get comprehensive medicine details including cost and image.
    Delegates to medicine_details service."""
    from app.services.medicine_details import get_medicine_details
    return await get_medicine_details(name)
