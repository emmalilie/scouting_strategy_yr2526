import requests
import json

player_name = "Rudy Quan"
school = "UCLA"

endpoints = [
    "https://api.utrsports.net/v2/search/players",
    "https://app.utrsports.net/api/v1/search/players",
]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
}

for ep in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing: {ep}")
    print(f"Query: {player_name}")
    
    try:
        r = requests.get(
            ep,
            headers=headers,
            params={"query": player_name, "top": 5},
            timeout=10
        )
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            print(f"\nResponse keys: {data.keys()}")
            
            hits = data.get("hits") or data.get("players") or []
            print(f"Number of hits: {len(hits)}")
            
            if hits:
                print(f"\nFirst hit keys: {hits[0].keys()}")
                hit = hits[0]
                
                # Extract fields like the working version
                pid = hit.get("id", "")
                utr = hit.get("singlesUtr") or hit.get("singles_utr") or "N/A"
                membership = hit.get("membership", "") or hit.get("membershipType", "")
                
                print(f"\nExtracted data:")
                print(f"  ID: {pid}")
                print(f"  singlesUtr: {utr}")
                print(f"  membership: {membership}")
                print(f"  UTR URL: https://app.utrsports.net/profiles/{pid}")
                
                print(f"\nFull hit structure:")
                print(json.dumps(hit, indent=2))
        else:
            print(f"Error: {r.text[:200]}")
            
    except Exception as e:
        print(f"Exception: {e}")
