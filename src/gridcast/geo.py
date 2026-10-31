import json
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def _overpass_counts(lat: float, lon: float, radius_m: int) -> list[int]:
    query = f"""[out:json][timeout:120];
(way["building"](around:{radius_m},{lat},{lon}); relation["building"](around:{radius_m},{lat},{lon}); )->.b;
(nwr["shop"](around:{radius_m},{lat},{lon}); nwr["amenity"="marketplace"](around:{radius_m},{lat},{lon}); )->.c;
(nwr["amenity"~"hospital|clinic|doctors|school|college"](around:{radius_m},{lat},{lon}); nwr["man_made"="water_well"](around:{radius_m},{lat},{lon}); )->.a;
.b out count; .c out count; .a out count;"""
    payload = urllib.parse.urlencode({"data": query}).encode()
    request = urllib.request.Request(OVERPASS_URL, data=payload,
                                     headers={"User-Agent": "gridcast/0.1 (hackathon research)"})
    with urllib.request.urlopen(request, timeout=150) as response:
        parsed = json.load(response)
    return [int(e["tags"]["total"]) for e in parsed["elements"] if e.get("type") == "count"]


def segment_counts_from_osm(lat: float, lon: float, radius_m: int = 2000) -> tuple[dict, int]:
    # OSM undercounts rural African buildings; Google Open Buildings is the production source.
    buildings, commercial, anchor = _overpass_counts(lat, lon, radius_m)
    household = max(buildings - commercial - anchor, 0)
    return {"household": household, "commercial": commercial, "anchor": anchor}, buildings
