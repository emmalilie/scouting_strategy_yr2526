import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

SEASONS = [
    "2021-22",
    "2022-23", 
    "2023-24",
    "2024-25",
    "2025-26"
]

BASE_URL = "https://uclabruins.com/sports/mens-tennis/schedule/text/"

def fetch_schedule():
    """Fetch current season schedule"""
    url = "https://uclabruins.com/sports/mens-tennis/schedule/text/2025-26"
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching schedule: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        logger.warning("No table found in schedule page")
        return pd.DataFrame()

    data = []
    for row in table.find_all("tr")[1:]:  # Skip header row
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 4:
            continue
        
        # Pad with empty strings if needed
        cols += [""] * (7 - len(cols))
        
        data.append({
            "Date": cols[0],
            "Time": cols[1], 
            "At": cols[2],
            "Opponent": cols[3],
            "Location": cols[4],
            "Tournament": cols[5],
            "Result": cols[6],
            "Last_Updated": datetime.now().isoformat()
        })
    
    return pd.DataFrame(data)

def fetch_season_schedule(season):
    """Fetch schedule for a specific season"""
    url = BASE_URL + season
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching season {season}: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        logger.warning(f"No table found for season {season}")
        return pd.DataFrame()

    # Parse season years
    try:
        start_year, end_year = season.split("-")
        start_year = int(start_year)
        end_year = int("20" + end_year) if len(end_year) == 2 else int(end_year)
    except ValueError as e:
        logger.error(f"Invalid season format {season}: {e}")
        return pd.DataFrame()

    rows = []
    for tr in table.find_all("tr")[1:]:  # Skip header
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        
        if len(tds) < 4:
            continue
        
        # Pad with empty strings
        tds += [""] * (7 - len(tds))

        date_str = tds[0]
        formatted_date = ""

        if date_str:
            # Remove day of week in parentheses if present
            date_str = date_str.split("(")[0].strip()
            try:
                date_obj = datetime.strptime(date_str, "%b %d")
                month = date_obj.month
                
                # Assign year based on academic calendar
                # Jan-May = end_year, Jun-Dec = start_year
                if month >= 1 and month <= 5:
                    year = end_year
                else:
                    year = start_year
                
                date_obj = datetime(year, date_obj.month, date_obj.day)
                formatted_date = date_obj.strftime("%m-%d-%Y")
            except ValueError as e:
                logger.warning(f"Could not parse date {date_str}: {e}")
                formatted_date = ""

        rows.append({
            "Date": formatted_date,
            "Opponent": tds[3],
            "Location": tds[4], 
            "Result": tds[6],
            "Season": season,
            "Last_Updated": datetime.now().isoformat()
        })
    
    return pd.DataFrame(rows)

def fetch_player_stats():
    """Fetch player statistics"""
    url = "https://static.uclabruins.com/custompages/Stats/2025-26/MTEN/teamcume.htm"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching player stats: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        logger.warning("No stats table found")
        return pd.DataFrame()

    stats = []
    for row in table.find_all("tr")[1:]:  # Skip header
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        
        if len(cols) < 5:
            continue
        
        # Skip total/team rows
        if cols[0].lower() in {"total", "team", ""}:
            continue
        
        stats.append({
            "Player": cols[0] if cols[0] else "N/A",
            "Singles_Wins": cols[1] if cols[1] else "N/A",
            "Singles_Losses": cols[2] if cols[2] else "N/A", 
            "Doubles_Wins": cols[3] if cols[3] else "N/A",
            "Doubles_Losses": cols[4] if cols[4] else "N/A"
        })
    
    return pd.DataFrame(stats)

def fetch_roster_with_stats():
    """Fetch roster from CSV file and merge with live stats"""
    try:
        # Read roster from CSV file
        roster_df = pd.read_csv("ucla_mens_tennis_roster.csv")
        logger.info(f"Loaded {len(roster_df)} players from CSV")
        
        # Fetch live stats
        stats_df = fetch_player_stats()
        
        if not stats_df.empty:
            # Update stats from live data, keeping CSV as fallback
            roster_df = roster_df.drop(columns=['Singles_Wins', 'Singles_Losses', 'Doubles_Wins', 'Doubles_Losses'], errors='ignore')
            roster_df = roster_df.merge(stats_df, on="Player", how="left")
            logger.info("Merged live stats with roster")
        
        # Fill NaN values with "N/A"
        roster_df = roster_df.fillna("N/A")
        
        # Update timestamp
        roster_df["Last_Updated"] = datetime.now().isoformat()
        
        return roster_df
        
    except FileNotFoundError:
        logger.error("ucla_mens_tennis_roster.csv not found")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading roster: {e}")
        return pd.DataFrame()

def get_all_data():
    """Fetch all data (schedule, roster, seasons)"""
    logger.info("Fetching all data...")
    
    schedule_df = fetch_schedule()
    roster_df = fetch_roster_with_stats()
    
    seasons_data = {}
    for season in SEASONS:
        logger.info(f"Fetching season {season}...")
        df = fetch_season_schedule(season)
        if not df.empty:
            seasons_data[season] = df
        else:
            logger.warning(f"No data for season {season}")
    
    logger.info(f"Data fetch complete. Seasons loaded: {list(seasons_data.keys())}")
    
    return {
        'current_schedule': schedule_df,
        'roster': roster_df,
        'seasons': seasons_data
    }

def fetch_school_season_schedule(base_url: str, season: str):
    """Fetch season schedule for any school given their base URL"""
    url = base_url + season
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Error fetching season {season} from {url}: {e}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        logger.warning(f"No table found for season {season} at {url}")
        return pd.DataFrame()

    # Parse season years
    try:
        start_year, end_year = season.split("-")
        start_year = int(start_year)
        end_year = int("20" + end_year) if len(end_year) == 2 else int(end_year)
    except ValueError as e:
        logger.error(f"Invalid season format {season}: {e}")
        return pd.DataFrame()

    rows = []
    for tr in table.find_all("tr")[1:]:  # Skip header
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        
        if len(tds) < 4:
            continue
        
        # Pad with empty strings
        tds += [""] * (7 - len(tds))

        date_str = tds[0]
        formatted_date = ""

        if date_str:
            # Remove day of week in parentheses if present
            date_str = date_str.split("(")[0].strip()
            try:
                date_obj = datetime.strptime(date_str, "%b %d")
                month = date_obj.month
                
                # Assign year based on academic calendar
                # Jan-May = end_year, Jun-Dec = start_year
                if month >= 1 and month <= 5:
                    year = end_year
                else:
                    year = start_year
                
                date_obj = datetime(year, date_obj.month, date_obj.day)
                formatted_date = date_obj.strftime("%m-%d-%Y")
            except ValueError as e:
                logger.warning(f"Could not parse date {date_str}: {e}")
                formatted_date = ""

        rows.append({
            "Date": formatted_date,
            "Opponent": tds[3],
            "Location": tds[4], 
            "Result": tds[6],
            "Season": season,
            "Last_Updated": datetime.now().isoformat()
        })
    
    return pd.DataFrame(rows)