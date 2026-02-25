# Scraper Column Name Fixes

## Problem
The Python scraper files were creating CSV files with wrong column names that didn't match what main.py expects.

## Expected Column Names (from main.py)
```
Player, Year, Hometown, UTR, Singles_Record, Doubles_Record, Profile_URL, UTR_URL
```

## Files Fixed

### 1. scrape_js_schools.py
**Before:**
- School, Season, Player, Player_Slug, Year_In_School, Hometown, Profile_URL, UTR_Rating, UTR_URL, Singles_W, Singles_L, Singles_Record, Doubles_W, Doubles_L, Doubles_Record

**After:**
- Player, Year, Hometown, UTR, Singles_Record, Doubles_Record, Profile_URL, UTR_URL

### 2. scrape_all_rosters.py
**Before:**
- School, Season, Player, Year_In_School, Hometown, Profile_URL, UTR_Rating, UTR_URL, Singles_W, Singles_L, Singles_Record, Doubles_W, Doubles_L, Doubles_Record

**After:**
- Player, Year, Hometown, UTR, Singles_Record, Doubles_Record, Profile_URL, UTR_URL

## How to Use

### Run scrapers to update rosters:

```bash
# Scrape all schools (Sidearm-based)
python scrape_all_rosters.py

# Scrape JS-heavy schools (Penn State, Purdue, Nebraska)
python scrape_js_schools.py
```

### Output files will be created in:
```
rosters/
├── ucla_roster.csv
├── usc_roster.csv
├── michigan_roster.csv
├── ohio_state_roster.csv
├── penn_state_roster.csv
├── indiana_roster.csv
├── illinois_roster.csv
├── northwestern_roster.csv
├── purdue_roster.csv
├── wisconsin_roster.csv
├── nebraska_roster.csv
└── michigan_state_roster.csv
```

## Notes
- All CSV files now have consistent column names
- main.py will correctly read and serve the roster data
- Restart backend after running scrapers to see updated data
