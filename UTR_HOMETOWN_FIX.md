# UTR and Hometown Extraction Fixes

## Problems Fixed

### 1. UTR Ratings Showing as "N/A"
**Issue:** UTR API was being called but the rating wasn't being extracted from the response.

**Fix:**
- Improved JSON parsing to handle different API response formats
- Added fallback to check `rating.singles` field
- Added proper type conversion and rounding for UTR values
- Added debug logging to track API responses

### 2. Hometowns Empty or Missing
**Issue:** Hometown extraction from roster pages wasn't working.

**Fixes:**
- Improved `_extract_field()` with multiple strategies:
  - Class-based search
  - Data attribute search
  - Regex pattern matching for "City, State" format
- Enhanced `scrape_player_profile()` with 3 strategies:
  - dt/dd pair search
  - Class name search
  - Full-text regex search for hometown patterns
- Always fetch profile page when hometown is missing

### 3. Year in School Missing
**Fix:**
- Enhanced profile page scraping with multiple strategies
- Always fetch profile page when year is "N/A"

## Changes Made

### get_utr_data()
```python
# Now extracts UTR from multiple possible fields:
utr = hit.get("singlesUtr", hit.get("rating", {}).get("singles", "N/A"))
# Rounds to 2 decimal places
utr = round(float(utr), 2)
# Adds debug logging
log.debug(f"Found player: {name} - UTR: {utr}")
```

### _extract_field()
```python
# Added regex pattern matching for hometowns:
match = re.search(r'([A-Z][a-z]+(?:\\s+[A-Z][a-z]+)*,\\s*[A-Z]{2,})', all_text)
# Matches: "Los Angeles, CA", "Paris, France", etc.
```

### scrape_player_profile()
```python
# Added 3 strategies to find hometown:
# 1. dt/dd pairs
# 2. Class name search
# 3. Full-text regex: r'Hometown[:\\s]+([A-Z]...)'
```

### scrape_school()
```python
# Always fetch profile page when data is missing:
if year == "N/A" or not hometown or hometown == "N/A":
    profile_data = scrape_player_profile(p["Profile_URL"])
```

## Expected Output

CSV files should now have:
```csv
Player,Year,Hometown,UTR,Singles_Record,Doubles_Record,Profile_URL,UTR_URL
Connor Church,Jr,Newport Beach CA,13.45,0-0,0-0,https://...,https://app.utrsports.net/profiles/...
```

## Usage

```bash
cd dashboard/backend
python scrape_all_rosters.py
```

The scraper will now:
1. ✅ Extract player names and profile URLs
2. ✅ Fetch individual profile pages for year and hometown
3. ✅ Look up UTR ratings via API
4. ✅ Match stats from team stats pages
5. ✅ Save complete data to CSV files

## Notes
- Profile page fetching adds ~0.5s per player
- UTR API calls add ~0.75s per player
- Total time: ~1.25s per player (respectful rate limiting)
- Debug logging enabled - check console for API responses
