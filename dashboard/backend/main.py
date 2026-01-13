from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from start import get_all_data
import pandas as pd

app = FastAPI(title="UCLA Tennis API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "UCLA Tennis API"}

@app.get("/roster")
def get_roster():
    # UCLA Men's Tennis 2025-26 current roster
    return [
        {"Player": "Bryce Pereira", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"},
        {"Player": "Govind Nanda", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"},
        {"Player": "Mathis Debru", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"},
        {"Player": "Nico Godsick", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"},
        {"Player": "Ben Goldberg", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"},
        {"Player": "Keegan Smith", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"},
        {"Player": "Logan Staggs", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"},
        {"Player": "Garrett Johns", "Singles_Wins": "N/A", "Singles_Losses": "N/A", "Doubles_Wins": "N/A", "Doubles_Losses": "N/A"}
    ]

@app.get("/schedule")
def get_current_schedule():
    try:
        data = get_all_data()
        return data['current_schedule'].to_dict('records') if not data['current_schedule'].empty else []
    except:
        return []

@app.get("/seasons")
def get_seasons():
    try:
        data = get_all_data()
        return list(data['seasons'].keys())
    except:
        return []

@app.get("/seasons/{season}")
def get_season_data(season: str):
    try:
        data = get_all_data()
        if season in data['seasons']:
            df = data['seasons'][season].copy()
            
            def compute_score(result):
                if pd.isna(result) or result == "":
                    return 0
                return 1 if result.upper().startswith("W") else -1 if result.upper().startswith("L") else 0
            
            df["ScoreChange"] = df["Result"].apply(compute_score)
            df["DateParsed"] = pd.to_datetime(df["Date"], format="%m-%d-%Y", errors="coerce")
            df = df.dropna(subset=["DateParsed"]).sort_values("DateParsed")
            df["CumulativeScore"] = df["ScoreChange"].cumsum()
            
            return df.to_dict('records')
        return []
    except:
        return []