import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

# ----------------------------------------
# SCRAPE MATCH SCHEDULE (2025–26)
# ----------------------------------------
def fetch_schedule():
    url = "https://uclabruins.com/sports/mens-tennis/schedule/text/2025-26"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        print("❌ Schedule table not found")
        return pd.DataFrame()

    data = []

    for row in table.find_all("tr")[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]
        if len(cols) < 4:
            continue

        cols += [""] * (7 - len(cols))  # pad to expected length

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

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SEASONS = [
    "2021-22",
    "2022-23",
    "2023-24",
    "2024-25",
    "2025-26"
]

BASE_URL = "https://uclabruins.com/sports/mens-tennis/schedule/text/"

# ----------------------------------------
# SCRAPE ONE SEASON
# ----------------------------------------
def fetch_season_schedule(season):
    """
    season: str, like "2025-26"
    returns: DataFrame with Date formatted as MM-DD-YYYY
    """
    url = BASE_URL + season
    response = requests.get(url, headers=HEADERS)

    if response.status_code != 200:
        print(f"❌ Failed to fetch {season}")
        return pd.DataFrame()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    if not table:
        print(f"⚠️ No table found for {season}")
        return pd.DataFrame()

    start_year, end_year = season.split("-")
    start_year = int(start_year)
    end_year = int("20" + end_year) if len(end_year) == 2 else int(end_year)

    rows = []
    for tr in table.find_all("tr")[1:]:
        tds = [td.get_text(strip=True) for td in tr.find_all("td")]
        tds += [""] * (7 - len(tds))

        date_str = tds[0]  # e.g., "Jan 15 (Wed)"
        formatted_date = ""

        if date_str:
            # Remove weekday part in parentheses
            date_str = date_str.split("(")[0].strip()  # "Jan 15"

            try:
                # Parse month and day
                date_obj = datetime.strptime(date_str, "%b %d")
                month = date_obj.month

                # Determine year based on month
                if month >= 1 and month <= 5:  # Jan-May = second year
                    year = end_year
                else:  # Jun-Dec = first year
                    year = start_year

                # Recreate full date with year
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

# ----------------------------------------
# SCRAPE PLAYER ROSTER
# ----------------------------------------
def fetch_player_stats():
    url = "https://static.uclabruins.com/custompages/Stats/2025-26/MTEN/teamcume.htm"
    response = requests.get(url, headers=HEADERS)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    table = soup.find("table")

    stats = []

    if not table:
        print("❌ Stats table not found")
        return pd.DataFrame()

    rows = table.find_all("tr")

    def val(x):
        return x if x else "N/A"

    for row in rows[1:]:
        cols = [c.get_text(strip=True) for c in row.find_all("td")]

        # Skip subtotal / team rows
        if len(cols) < 5 or cols[0].lower() in {"total", "team"}:
            continue

        stats.append({
            "Player": val(cols[0]),
            "Singles_Wins": val(cols[1]),
            "Singles_Losses": val(cols[2]),
            "Doubles_Wins": val(cols[3]),
            "Doubles_Losses": val(cols[4])
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

    # ---- MERGE PLAYER STATS ----
    stats_df = fetch_player_stats()

    if not stats_df.empty:
        roster_df = roster_df.merge(
            stats_df,
            on="Player",
            how="left"
        )

    roster_df["Last_Updated"] = datetime.now().isoformat()
    return roster_df



# ----------------------------------------
# MAIN
# ----------------------------------------
if __name__ == "__main__":
    print("🔄 Updating UCLA Men's Tennis data...")

    schedule_df = fetch_schedule()
    roster_df = fetch_roster_with_stats()

    if not schedule_df.empty:
        schedule_df.to_csv(
            "ucla_mens_tennis_schedule_2025_26.csv",
            index=False
        )
        print("✅ Schedule CSV updated")

    if not roster_df.empty:
        roster_df.to_csv(
            "ucla_mens_tennis_roster.csv",
            index=False
        )
        print("✅ Roster CSV updated")


    with pd.ExcelWriter(
        "ucla_mens_tennis_results_by_year.xlsx",
        engine="openpyxl"
    ) as writer:

        for season in SEASONS:
            print(f"📅 Processing {season}...")
            df = fetch_season_schedule(season)

            if df.empty:
                print(f"⚠️ No data for {season}")
                continue

            # Sheet names cannot exceed 31 chars
            df.to_excel(
                writer,
                sheet_name=season,
                index=False
            )

    print("✅ Excel file created: ucla_mens_tennis_results_by_year.xlsx")

    print("🏁 Done.")


