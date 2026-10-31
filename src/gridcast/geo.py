import json
import urllib.parse
import urllib.request

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

# Commercial = small shops/services; anchor = productive or institutional loads that drive
# load factor (mills, markets, telecom, industry, water pumping, health, schools, fuel).
_BUILDING = ['way["building"]', 'relation["building"]']
_COMMERCIAL = ['nwr["shop"]', 'nwr["amenity"~"restaurant|cafe|bar|fast_food|bank"]', 'nwr["office"]']
_ANCHOR = ['nwr["amenity"~"hospital|clinic|doctors|health_post|school|college|university|marketplace|fuel"]',
           'nwr["man_made"~"works|water_well|water_tower|communications_tower|mast|tower"]',
           'nwr["tower:type"="communication"]', 'nwr["building"~"industrial|warehouse"]',
           'nwr["craft"~"grain_mill|sawmill"]']


def _group(tags: list[str], lat: float, lon: float, radius_m: int, label: str) -> str:
    items = "".join(f"{t}(around:{radius_m},{lat},{lon});" for t in tags)
    return f"({items})->.{label};"


def _overpass_counts(lat: float, lon: float, radius_m: int) -> list[int]:
    body = (_group(_BUILDING, lat, lon, radius_m, "b") + _group(_COMMERCIAL, lat, lon, radius_m, "c")
            + _group(_ANCHOR, lat, lon, radius_m, "a"))
    query = f"[out:json][timeout:120];{body}.b out count;.c out count;.a out count;"
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
