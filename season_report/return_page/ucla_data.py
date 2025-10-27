import requests
import json
import pandas as pd
from collections import defaultdict
from collections import Counter
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("team", help="M or W")
args = parser.parse_args()
TEAM = args.team
"""_summary_ 
To use, type either "python ucla_data.py m" or "python ucla_data.py w" to generate the tennis_matches_data.csv 's 
that are located in the mens / womens folders!

If you need an explanation on what any of the columns mean, look through the api links below!
"""
if TEAM.lower() == 'w':
    api_url = "https://uclabruins.com/api/v2/EventsResults/results?sportId=21&$pageIndex=0&$pageSize=50"
    OUT_LINK = r'C:\Users\pavan\Documents\Programming Stuff\Tennis_Consult\consulting-spring2025\data\womens\tennis_matches_data.csv'
elif TEAM.lower() == 'm':
    api_url = "https://uclabruins.com/api/v2/EventsResults/results?sportId=9&$pageIndex=0&$pageSize=50"
    OUT_LINK = r'C:\Users\pavan\Documents\Programming Stuff\Tennis_Consult\consulting-spring2025\data\mens\tennis_matches_data.csv'

print(OUT_LINK)
response = requests.get(api_url)

bsurllist = []
box_score_api_urls = []

if response.status_code == 200:
    data = response.json()

    for game in data["items"]:
        date = game.get("date", "No date available")
        location = game.get("location", "No location available")
        opponent = game.get("opponent", {}).get("title", "No opponent title available")

        result = game.get("result", {})
        boxScore = result.get("boxScore", None) if isinstance(result, dict) else None

        if boxScore:
            if boxScore.startswith("/"):
                boxScore = "https://uclabruins.com/api/v2/Stats/boxscore/" + boxScore.split("=")[-1]
            bsurllist.append(boxScore)  
else:
    print(f"Error: Unable to fetch data (Status Code: {response.status_code})")

box_score_api_urls = [url for url in bsurllist if url]

player_stats = []
all_match_data = [] 

for url in box_score_api_urls:
    try:
        response = requests.get(url, timeout=10) 
        response.raise_for_status() 
        data1 = response.json() 

    except requests.exceptions.RequestException as e:
        continue 

    games1 = data1.get("singles", [])
    if not games1:
        continue 

    matches = {
        "1": [],
        "2": [],
        "3": [],
        "4": [],
        "5": [],
        "6": []
    }
    winningteam_list = data1.get("finishOrderSingles", [])
    winningteam = winningteam_list[-1] if winningteam_list else 0

    for game1 in games1:
        match_num = game1.get("matchNum", "").strip()
        if match_num not in matches:
            continue

        player_info = {
            "date": game1.get("date"),
            "name1": game1.get("name1", "Unknown"),
            "team": game1.get("team", ""),
            "gamestatus": game1.get("isWinner", ""),
            "setlist": [
                game1.get("set1"),
                game1.get("set2"),
                game1.get("set3"),
                game1.get("set4"),
                game1.get("set5"),
            ],
        }

        matches[match_num].append(player_info)

    for match_num, players in matches.items():
        for player in players:
            all_match_data.append({
                "URL": url,
                #"Date": player_info.get["date"], 
                "Winning Team": 1 if match_num == winningteam else 0,
                "Match": match_num, 
                "Player": player["name1"],
                "Team": player["team"],
                "Set 1": player["setlist"][0] if player["setlist"][0] else "",
                "Set 2": player["setlist"][1] if player["setlist"][1] else "",
                "Set 3": player["setlist"][2] if player["setlist"][2] else "",
                "Set 4": player["setlist"][3] if player["setlist"][3] else "",
                "Set 5": player["setlist"][4] if player["setlist"][4] else "",
                "Game Status": player["gamestatus"]
            })

df = pd.DataFrame(all_match_data)
df['player_num'] = df.groupby(['URL', 'Match']).cumcount() + 1

columns_to_pivot = ['Player', 'Team', 'Game Status', 'Winning Team', 'Set 1', 'Set 2', 'Set 3', 'Set 4', 'Set 5']

pivot_df = df.pivot_table(
    index=['URL', 'Match'], 
    columns='player_num',                   
    values=columns_to_pivot,
    aggfunc='first'                          
)

pivot_df.columns = [f"{col[0]}_{col[1]}" for col in pivot_df.columns]
pivot_df = pivot_df.reset_index()

pivot_df['Match'] = pivot_df['Match'].astype(str)
winningmatch_str = str(winningteam)

pivot_df['Winning Team_1'] = pivot_df.apply(
    lambda row: 1 if (row.get('Game Status_1') == 1 or str(row.get('Game Status_1')) == "1") and row['Match'] == winningmatch_str else 0,
    axis=1
)

for col in pivot_df.columns:
    if col.startswith("Winning Team_") and col != "Winning Team_1":
        pivot_df[col] = 0

if 'Winning Team_2' in pivot_df.columns:
    pivot_df = pivot_df.drop(columns=['Winning Team_2'])

pivot_df.to_csv(OUT_LINK, index=False)
print(pivot_df.head())
print(df)
