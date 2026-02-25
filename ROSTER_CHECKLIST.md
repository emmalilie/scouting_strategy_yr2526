# ROSTER UPDATE CHECKLIST - 2025-26 Season

## COMPLETED ✓
- [x] USC - Updated with correct URL format (e.g., /17855)
- [x] Illinois - Updated with correct URL format (e.g., /15307)
- [x] Wisconsin - Updated with correct URL format

## TO DO - Visit each site and fill in:

### 1. UCLA
URL: https://uclabruins.com/sports/mens-tennis/roster
- Click each player → Copy full URL with /##### at end
- Format: https://uclabruins.com/sports/mens-tennis/roster/[name]/[ID]

### 2. Michigan  
URL: https://mgoblue.com/sports/mens-tennis/roster
- Same process

### 3. Ohio State
URL: https://ohiostatebuckeyes.com/sport/mten/roster/
- Same process

### 4. Penn State
URL: https://gopsusports.com/sports/mens-tennis/roster
- Same process

### 5. Indiana
URL: https://iuhoosiers.com/sports/mens-tennis/roster
- Same process

### 6. Northwestern
URL: https://nusports.com/sports/mens-tennis/roster
- Same process

### 7. Purdue
URL: https://purduesports.com/sports/mens-tennis/roster
- Same process

### 8. Nebraska
URL: https://huskers.com/sports/mens-tennis/roster
- Same process

### 9. Michigan State
URL: https://msuspartans.com/sports/mens-tennis/roster
- Same process

## HOW TO UPDATE EACH ROSTER:

1. Go to school's roster page
2. **VERIFY it says "2025-26" season** (usually in dropdown or header)
3. For EACH player:
   - Click on their name
   - Copy the FULL URL from browser (including /##### at end)
   - Note their Year (Fr, So, Jr, Sr)
   - Note their Hometown
4. Update the CSV file in `rosters/[school]_roster.csv`

## CSV FORMAT:
```csv
Player,Year,Hometown,UTR,Singles_Record,Doubles_Record,Profile_URL,UTR_URL
John Doe,Jr,Los Angeles CA,13.2,0-0,0-0,https://school.com/roster/john-doe/12345,N/A
```

## EXAMPLE (USC - Connor Church):
```csv
Connor Church,Jr,Newport Beach CA,13.5,0-0,0-0,https://usctrojans.com/sports/mens-tennis/roster/connor-church/17855,N/A
```

## NOTES:
- UTR can be left as "N/A" for now (we'll add later)
- UTR_URL can be left as "N/A" for now
- Singles_Record and Doubles_Record start at "0-0"
- Make sure URL includes the numeric ID at the end (e.g., /17855)
