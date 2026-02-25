# UTR Fetching Fix - scrape_all_rosters.py

## Problem
The scraper had incomplete/broken UTR fetching code that required cookie authentication and wasn't working.

## Solution
Replaced with working public UTR API implementation that:
- Uses `https://api.utrsports.net/v2/search/players` endpoint
- No authentication required
- Searches by player name
- Searches by player name + school for better matching
- Prefers college players in results
- Returns UTR rating and profile URL

## Changes Made

### Removed:
- Cookie-based authentication code
- `_utr_headers()` function
- `_fetch_ranked_teams()` function  
- `_get_club_id()` function
- `_fetch_utr_roster()` function
- Old `get_utr_data()` with cookie/roster parameters

### Added:
- New `get_utr_data(player_name, school)` function
- Uses public API endpoint
- No authentication needed
- Automatic retry with school name for disambiguation

## How It Works

```python
# For each player:
utr_rating, utr_url = get_utr_data("John Doe", "UCLA Bruins")

# Returns:
# utr_rating: "13.5" or "N/A"
# utr_url: "https://app.utrsports.net/profiles/12345" or "N/A"
```

## Usage

```bash
cd dashboard/backend
python scrape_all_rosters.py
```

The scraper will:
1. Fetch roster pages for all schools
2. Parse player names, years, hometowns, profile URLs
3. Fetch stats from team stats pages
4. Look up UTR rating for each player (with 0.75s delay between requests)
5. Save to `rosters/<school>_roster.csv`

## Output Format

CSV files with columns:
```
Player, Year, Hometown, UTR, Singles_Record, Doubles_Record, Profile_URL, UTR_URL
```

## Notes
- UTR API is rate-limited - scraper includes 0.75s delay between requests
- If UTR lookup fails, values default to "N/A"
- Searches try player name alone first, then with school name for better matching
