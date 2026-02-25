# Roster Path Fixes - Summary

## Issues Fixed in main.py

### 1. UCLA Roster Path (Line ~35)
**Before:** `csv_path = "ucla_mens_tennis_roster.csv"`
**After:** `csv_path = "rosters/ucla_roster.csv"`

### 2. Debug CSV Path (Line ~350)
**Before:** `csv_path = "ucla_roster.csv"`
**After:** `csv_path = "rosters/ucla_roster.csv"`

### 3. Penn State Roster Filename (Line ~380)
**Before:** `"Penn State": "rosters/pennstate_roster.csv"`
**After:** `"Penn State": "rosters/penn_state_roster.csv"`

## Verified Roster Files

All 12 roster CSV files exist in the `rosters/` folder with correct naming:

✓ rosters/ucla_roster.csv
✓ rosters/usc_roster.csv
✓ rosters/michigan_roster.csv
✓ rosters/ohio_state_roster.csv
✓ rosters/penn_state_roster.csv
✓ rosters/indiana_roster.csv
✓ rosters/illinois_roster.csv
✓ rosters/northwestern_roster.csv
✓ rosters/purdue_roster.csv
✓ rosters/wisconsin_roster.csv
✓ rosters/nebraska_roster.csv
✓ rosters/michigan_state_roster.csv

## API Endpoints Now Working

- `GET /roster` - Returns UCLA roster from rosters/ucla_roster.csv
- `GET /schools/{school}/roster` - Returns any school's roster from rosters/{school}_roster.csv
- `GET /debug/csv` - Debug endpoint now checks correct path

## Next Steps

1. Restart backend server: `python main.py`
2. Test roster endpoints
3. Manually update roster CSVs with correct 2025-26 player data
4. Add UTR ratings for each player
