# Player URL Verification Guide

## What I've Done
1. Removed numeric IDs from all profile URLs (they were causing incorrect redirects)
2. Updated UCLA, USC, and Michigan roster files with simplified URLs

## What You Need To Do

### Step 1: Verify Profile URLs
For each school, visit their roster page and verify the player URLs:

**UCLA:** https://uclabruins.com/sports/mens-tennis/roster
- Format: `https://uclabruins.com/sports/mens-tennis/roster/[player-name-slug]`
- Click on each player and copy the actual URL from the browser

**USC:** https://usctrojans.com/sports/mens-tennis/roster
- Format: `https://usctrojans.com/sports/mens-tennis/roster/[player-name-slug]`

**Michigan:** https://mgoblue.com/sports/mens-tennis/roster
- Format: `https://mgoblue.com/sports/mens-tennis/roster/[player-name-slug]`

### Step 2: Verify UTR URLs
1. Go to https://app.utrsports.net/search
2. Search for each player by name
3. Click on their profile
4. Copy the URL from the browser (format: `https://app.utrsports.net/profiles/[PROFILE_ID]`)

### Step 3: Update CSV Files
Update the following files with correct URLs:
- `rosters/ucla_roster.csv`
- `rosters/usc_roster.csv`
- `rosters/michigan_roster.csv`
- `rosters/ohio_state_roster.csv`
- `rosters/penn_state_roster.csv`
- `rosters/indiana_roster.csv`
- `rosters/illinois_roster.csv`
- `rosters/northwestern_roster.csv`
- `rosters/purdue_roster.csv`
- `rosters/wisconsin_roster.csv`
- `rosters/nebraska_roster.csv`
- `rosters/michigan_state_roster.csv`

## Current Status

### UCLA Roster (NEEDS VERIFICATION)
- Gianluca Ballotta
- Cassius Chinlund
- Andrei Crabel
- Spencer Johnson
- Andy Nguyen
- Rudy Quan
- Bengt Reinhard
- Emon van Loben Sels
- Aadarsh Tripathi

### USC Roster (NEEDS VERIFICATION)
- Bradley Frye
- Peter Makk
- Lodewijk Weststrate
- Daniel Cukierman
- Stefan Leustian
- Jake Sands

### Michigan Roster (NEEDS VERIFICATION)
- Patrick Maloney
- Andrew Fenty
- Ondrej Styler
- Gavin Young
- Nino Ehrenschneider
- Jacob Bickersteth

## Quick Test
After updating URLs:
1. Restart backend: `cd dashboard/backend && python main.py`
2. Restart frontend: `cd dashboard/frontend && npm start`
3. Click on player names and UTR links to verify they go to correct profiles

## Notes
- The numeric IDs at the end of URLs were causing redirects to wrong players
- Without the IDs, the URLs should redirect to the correct player based on the name slug
- If a URL still doesn't work, you may need to manually find the correct URL format for that school
