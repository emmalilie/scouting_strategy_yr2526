# 2025-26 Roster Update Instructions

## What I've Done
✅ Updated UCLA roster with current players (Kaylan Bigun, Alexander Hoogmartens, etc.)
✅ Updated USC roster 
✅ Updated Michigan roster
✅ Removed numeric IDs from all profile URLs

## What You Need To Do

### Step 1: Visit Each School's Official Roster Page

| School | Roster URL |
|--------|-----------|
| UCLA | https://uclabruins.com/sports/mens-tennis/roster |
| USC | https://usctrojans.com/sports/mens-tennis/roster |
| Michigan | https://mgoblue.com/sports/mens-tennis/roster |
| Ohio State | https://ohiostatebuckeyes.com/sport/mten/roster/ |
| Penn State | https://gopsusports.com/sports/mens-tennis/roster |
| Indiana | https://iuhoosiers.com/sports/mens-tennis/roster |
| Illinois | https://fightingillini.com/sports/mens-tennis/roster |
| Northwestern | https://nusports.com/sports/mens-tennis/roster |
| Purdue | https://purduesports.com/sports/mens-tennis/roster |
| Wisconsin | https://uwbadgers.com/sports/mens-tennis/roster |
| Nebraska | https://huskers.com/sports/mens-tennis/roster |
| Michigan State | https://msuspartans.com/sports/mens-tennis/roster |

### Step 2: For Each School, Collect:
1. **Player Name** - Full name as shown on roster
2. **Year** - Fr, So, Jr, Sr
3. **Hometown** - City, State/Country
4. **Profile URL** - Click on player, copy URL (remove numeric ID at end)
   - Format: `https://[school].com/sports/mens-tennis/roster/[player-name]`
5. **UTR** - Search player on https://app.utrsports.net/search
6. **UTR URL** - Copy profile URL from UTR site
   - Format: `https://app.utrsports.net/profiles/[PROFILE_ID]`

### Step 3: Update CSV Files

Files to update in `dashboard/backend/rosters/`:
- ✅ `ucla_roster.csv` (DONE - but verify UTR URLs)
- ✅ `usc_roster.csv` (DONE - but verify UTR URLs)
- ✅ `michigan_roster.csv` (DONE - but verify UTR URLs)
- ❌ `ohio_state_roster.csv` (NEEDS UPDATE)
- ❌ `penn_state_roster.csv` (NEEDS UPDATE)
- ❌ `indiana_roster.csv` (NEEDS UPDATE)
- ❌ `illinois_roster.csv` (NEEDS UPDATE)
- ❌ `northwestern_roster.csv` (NEEDS UPDATE)
- ❌ `purdue_roster.csv` (NEEDS UPDATE)
- ❌ `wisconsin_roster.csv` (NEEDS UPDATE)
- ❌ `nebraska_roster.csv` (NEEDS UPDATE)
- ❌ `michigan_state_roster.csv` (NEEDS UPDATE)

### CSV Format:
```csv
Player,Year,Hometown,UTR,Singles_Record,Doubles_Record,Profile_URL,UTR_URL
John Doe,Jr,Los Angeles CA,13.2,0-0,0-0,https://school.com/sports/mens-tennis/roster/john-doe,https://app.utrsports.net/profiles/1234567
```

### Step 4: Test
1. Restart backend: `cd dashboard/backend && python main.py`
2. Restart frontend: `cd dashboard/frontend && npm start`
3. Select different schools and verify:
   - Player names are current
   - Profile links work
   - UTR links work

## Quick Reference: UCLA 2025-26 Roster (Example)
- Kaylan Bigun (Fr)
- Alexander Hoogmartens (Jr)
- Aadarsh Tripathi (So)
- Emon van Loben Sels (Jr)
- Rudy Quan (So)
- Giacomo Revelli (So)
- Gianluca Ballotta (Jr)
- Spencer Johnson (So)

## Notes
- Remove any graduated seniors (Sr from 2024-25)
- Update year for returning players (Fr→So, So→Jr, Jr→Sr)
- Singles_Record and Doubles_Record start at 0-0 for new season
- UTR ratings may have changed - verify on UTR website
