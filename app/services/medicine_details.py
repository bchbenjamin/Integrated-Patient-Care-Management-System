"""
medicine_details.py — Aggregated medicine information service.
Provides medicine cost estimates and pill images from public APIs.
"""
import time
import httpx
from typing import Dict, Optional, List, Tuple

# In-memory cache for medicine details
_details_cache: Dict[str, Tuple[dict, float]] = {}
DETAILS_CACHE_TTL = 600.0  # 10 minutes


async def get_medicine_image(medicine_name: str) -> Optional[str]:
    """Get medicine pill image URL from NLM RxImage API."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://rximage.nlm.nih.gov/api/rximage/1/rxbase",
                params={"name": medicine_name, "rxtty": "SCD", "resolution": 2},
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("nlmRxImages", [])
                if results:
                    return results[0].get("imageUrl")
    except Exception:
        pass
    return None


async def get_medicine_cost(medicine_name: str) -> Optional[dict]:
    """Get medicine cost estimate from OpenFDA pricing data.
    Falls back to a reference database for common medicines."""
    # Reference costs for common medicines (average US retail price per unit)
    REFERENCE_COSTS = {
        "amoxicillin": {"cost": 0.50, "unit": "capsule", "range": "$4-$15 for 30 capsules"},
        "ibuprofen": {"cost": 0.15, "unit": "tablet", "range": "$4-$10 for 100 tablets"},
        "acetaminophen": {"cost": 0.10, "unit": "tablet", "range": "$3-$8 for 100 tablets"},
        "metformin": {"cost": 0.15, "unit": "tablet", "range": "$4-$12 for 60 tablets"},
        "lisinopril": {"cost": 0.20, "unit": "tablet", "range": "$4-$15 for 30 tablets"},
        "atorvastatin": {"cost": 0.30, "unit": "tablet", "range": "$9-$20 for 30 tablets"},
        "metoprolol": {"cost": 0.25, "unit": "tablet", "range": "$4-$15 for 60 tablets"},
        "omeprazole": {"cost": 0.35, "unit": "capsule", "range": "$7-$20 for 30 capsules"},
        "losartan": {"cost": 0.30, "unit": "tablet", "range": "$9-$18 for 30 tablets"},
        "amlodipine": {"cost": 0.20, "unit": "tablet", "range": "$4-$12 for 30 tablets"},
        "sertraline": {"cost": 0.40, "unit": "tablet", "range": "$10-$25 for 30 tablets"},
        "gabapentin": {"cost": 0.25, "unit": "capsule", "range": "$8-$20 for 90 capsules"},
        "hydrochlorothiazide": {"cost": 0.10, "unit": "tablet", "range": "$4-$10 for 30 tablets"},
        "prednisone": {"cost": 0.15, "unit": "tablet", "range": "$5-$12 for 30 tablets"},
        "azithromycin": {"cost": 1.50, "unit": "tablet", "range": "$8-$20 for 6 tablets"},
        "ciprofloxacin": {"cost": 0.80, "unit": "tablet", "range": "$10-$25 for 14 tablets"},
        "pantoprazole": {"cost": 0.40, "unit": "tablet", "range": "$10-$22 for 30 tablets"},
        "cetirizine": {"cost": 0.15, "unit": "tablet", "range": "$4-$12 for 30 tablets"},
        "montelukast": {"cost": 0.50, "unit": "tablet", "range": "$10-$25 for 30 tablets"},
        "albuterol": {"cost": 5.00, "unit": "inhaler", "range": "$25-$60 per inhaler"},
        "aspirin": {"cost": 0.05, "unit": "tablet", "range": "$3-$8 for 100 tablets"},
        "paracetamol": {"cost": 0.08, "unit": "tablet", "range": "$3-$7 for 100 tablets"},
        "diclofenac": {"cost": 0.30, "unit": "tablet", "range": "$8-$18 for 30 tablets"},
        "cephalexin": {"cost": 0.60, "unit": "capsule", "range": "$10-$20 for 28 capsules"},
        "doxycycline": {"cost": 0.75, "unit": "capsule", "range": "$10-$25 for 20 capsules"},
        "ranitidine": {"cost": 0.20, "unit": "tablet", "range": "$5-$12 for 30 tablets"},
    }
    
    name_lower = medicine_name.strip().lower()
    
    # Check reference database first
    for key, data in REFERENCE_COSTS.items():
        if key in name_lower or name_lower in key:
            return data
    
    # Try real-time lookup via NLM RxNorm + NADAC pricing
    try:
        async with httpx.AsyncClient() as client:
            # First get RxCUI
            resp = await client.get(
                f"https://rxnav.nlm.nih.gov/REST/rxcui.json?name={medicine_name}&search=1",
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                rxcui_group = data.get("idGroup", {})
                rxcui_list = rxcui_group.get("rxnormId", [])
                if rxcui_list:
                    # Try NADAC pricing API
                    rxcui = rxcui_list[0]
                    price_resp = await client.get(
                        f"https://data.medicaid.gov/resource/tau9-gfwr.json?ndc_description={medicine_name}",
                        timeout=5.0
                    )
                    if price_resp.status_code == 200:
                        price_data = price_resp.json()
                        if price_data:
                            nadac = price_data[0].get("nadac_per_unit")
                            if nadac:
                                return {
                                    "cost": float(nadac),
                                    "unit": "unit",
                                    "range": f"${float(nadac):.2f} per unit (NADAC)",
                                    "source": "NADAC"
                                }
    except Exception:
        pass
    
    return None


async def get_medicine_details(medicine_name: str) -> dict:
    """Get comprehensive medicine details including cost, image, and FDA info."""
    cache_key = medicine_name.strip().lower()
    now = time.time()
    
    # Check cache
    if cache_key in _details_cache:
        cached, expiry = _details_cache[cache_key]
        if now < expiry:
            return cached
    
    details = {
        "name": medicine_name,
        "image_url": None,
        "cost": None,
        "fda_info": None
    }
    
    # Fetch image and cost in parallel
    import asyncio
    image_task = asyncio.create_task(get_medicine_image(medicine_name))
    cost_task = asyncio.create_task(get_medicine_cost(medicine_name))
    
    # Fetch FDA info
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"https://api.fda.gov/drug/label.json?search=openfda.brand_name:{medicine_name}+openfda.generic_name:{medicine_name}&limit=1",
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                results = data.get("results", [])
                if results:
                    item = results[0]
                    details["fda_info"] = {
                        "brand_name": item.get("openfda", {}).get("brand_name", [""])[0] if item.get("openfda", {}).get("brand_name") else "",
                        "generic_name": item.get("openfda", {}).get("generic_name", [""])[0] if item.get("openfda", {}).get("generic_name") else "",
                        "purpose": item.get("purpose", [""])[0] if item.get("purpose") else "",
                        "warnings": item.get("warnings", [""])[0][:500] if item.get("warnings") else "",
                        "dosage_forms": item.get("openfda", {}).get("dosage_form", []),
                        "route": item.get("openfda", {}).get("route", []),
                    }
    except Exception:
        pass
    
    details["image_url"] = await image_task
    details["cost"] = await cost_task
    
    _details_cache[cache_key] = (details, now + DETAILS_CACHE_TTL)
    return details
