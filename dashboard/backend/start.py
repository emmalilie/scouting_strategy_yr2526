import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

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
    url = "https://uclabruins.com/sports/mens-tennis/schedule/text/2025-26"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        return pd.DataFrame()

    data = []
    for row in table.find_all("tr")[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 4:
            continue
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
    url = BASE_URL + season
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        return pd.DataFrame()

    start_year, end_year = season.split("-")
    start_year = int(start_year)
    end_year = int("20" + end_year) if len(end_year) == 2 else int(end_year)

    rows = []
    for tr in table.find_all("tr")[1:]:
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        tds += [""] * (7 - len(tds))

        date_str = tds[0]
        formatted_date = ""

        if date_str:
            date_str = date_str.split("(")[0].strip()
            try:
                date_obj = datetime.strptime(date_str, "%b %d")
                month = date_obj.month
                if month >= 1 and month <= 5:
                    year = end_year
                else:
                    year = start_year
                date_obj = datetime(year, date_obj.month, date_obj.day)
                formatted_date = date_obj.strftime("%m-%d-%Y")
            except ValueError:
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
    url = "https://static.uclabruins.com/custompages/Stats/2025-26/MTEN/teamcume.htm"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        return pd.DataFrame()

    stats = []
    for row in table.find_all("tr")[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 5 or cols[0].lower() in {"total", "team"}:
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
    roster_url = "https://uclabruins.com/sports/mens-tennis/roster"
    response = requests.get(roster_url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    players = []
    seen_urls = set()

    for a in soup.find_all("a", href=True):
        href = a["href"]
        name = a.get_text(strip=True)

        if "/sports/mens-tennis/roster/" not in href:
            continue
        if "/coaches/" in href:
            continue
        if name.lower().startswith("full bio"):
            continue
        if len(name.split()) < 2:
            continue

        full_url = f"https://uclabruins.com{href}"
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)

        players.append({
            "Player": name,
            "Profile_URL": full_url
        })

    roster_df = pd.DataFrame(players)
    stats_df = fetch_player_stats()

    if not stats_df.empty:
        roster_df = roster_df.merge(stats_df, on="Player", how="left")

    roster_df["Last_Updated"] = datetime.now().isoformat()
    return roster_df

def get_all_data():
    schedule_df = fetch_schedule()
    roster_df = fetch_roster_with_stats()
    
    seasons_data = {}
    for season in SEASONS:
        df = fetch_season_schedule(season)
        if not df.empty:
            seasons_data[season] = df
    
    return {
        'current_schedule': schedule_df,
        'roster': roster_df,
        'seasons': seasons_data
    }