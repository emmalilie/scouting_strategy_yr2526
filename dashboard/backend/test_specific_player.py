import requests
import json

# Test players that returned 0.0
test_players = [
    ("Gianluca Ballotta", "2920230"),
    ("Cassius Chinlund", "5329395"),
    ("Andrei Crabel", "4270236"),
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

for name, pid in test_players:
    print(f"\n{'='*60}")
    print(f"Testing: {name} (ID: {pid})")
    
    try:
        r = requests.get(
            "https://api.utrsports.net/v2/search/players",
            headers=headers,
            params={"query": name, "top": 5},
            timeout=10
        )
        
        if r.status_code == 200:
            data = r.json()
            hits = data.get("hits", [])
            
            if hits:
                hit = hits[0]
                source = hit.get("source", {})
                
                print(f"Found ID: {source.get('id')}")
                print(f"singlesUtr: {source.get('singlesUtr')}")
                print(f"doublesUtr: {source.get('doublesUtr')}")
                print(f"ratingStatusSingles: {source.get('ratingStatusSingles')}")
                print(f"playerCollege: {source.get('playerCollege', {}).get('name')}")
                
                # Check if rating is 0 or None
                utr = source.get("singlesUtr")
                if utr == 0 or utr == 0.0:
                    print(f"WARNING: UTR is exactly 0.0 - player may be unrated")
            else:
                print("No hits found")
                
    except Exception as e:
        print(f"Error: {e}")
