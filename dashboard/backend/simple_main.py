from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from start import get_all_data
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "UCLA Tennis API"}

@app.get("/roster")
def get_roster():
    return [
        {"Player": "John Doe", "Singles_Wins": "10", "Singles_Losses": "2", "Doubles_Wins": "8", "Doubles_Losses": "1"},
        {"Player": "Jane Smith", "Singles_Wins": "8", "Singles_Losses": "3", "Doubles_Wins": "6", "Doubles_Losses": "2"}
    ]

@app.get("/schedule")
def get_schedule():
    try:
        data = get_all_data()
        return data['current_schedule'].to_dict('records') if not data['current_schedule'].empty else []
    except:
        return [
            {"Date": "01-15-2026", "Opponent": "USC", "Location": "Home", "Result": "W 6-1"},
            {"Date": "01-20-2026", "Opponent": "Stanford", "Location": "Away", "Result": "L 3-4"}
        ]

@app.get("/seasons")
def get_seasons():
    return ["2024-25", "2025-26"]

@app.get("/seasons/{season}")
def get_season_data(season: str):
    return [
        {"Date": "01-15-2026", "Opponent": "USC", "Result": "W 6-1", "ScoreChange": 1, "CumulativeScore": 1},
        {"Date": "01-20-2026", "Opponent": "Stanford", "Result": "L 3-4", "ScoreChange": -1, "CumulativeScore": 0}
    ]