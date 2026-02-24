from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from start import get_all_data
import pandas as pd
import logging
import os

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    return {"message": "UCLA Tennis API", "status": "running"}

@app.get("/roster")
def get_roster():
    """Get current roster with stats from CSV"""
    try:
        # First try to get data from get_all_data
        data = get_all_data()
        roster_df = data.get('roster', pd.DataFrame())
        
        # If empty, try to read CSV directly
        if roster_df.empty:
            csv_path = "ucla_mens_tennis_roster.csv"
            if os.path.exists(csv_path):
                logger.info(f"Reading roster directly from {csv_path}")
                roster_df = pd.read_csv(csv_path)
                
                # Clean up the data
                # Strip whitespace from all string columns
                for col in roster_df.columns:
                    if roster_df[col].dtype == 'object':
                        roster_df[col] = roster_df[col].astype(str).str.strip()
                
                # Replace empty strings and 'nan' with 'N/A'
                roster_df = roster_df.replace('', 'N/A')
                roster_df = roster_df.replace('nan', 'N/A')
                roster_df = roster_df.fillna('N/A')
                
                logger.info(f"Successfully loaded {len(roster_df)} players from CSV")
                logger.info(f"CSV columns: {list(roster_df.columns)}")
            else:
                logger.error(f"CSV file not found at {csv_path}")
                raise HTTPException(
                    status_code=503, 
                    detail=f"Roster CSV file not found. Expected at: {os.path.abspath(csv_path)}"
                )
        
        if roster_df.empty:
            raise HTTPException(status_code=503, detail="Roster data is empty")
        
        # Convert to dict and ensure all values are strings (not NaN)
        result = roster_df.to_dict('records')
        
        # Additional cleanup of the result
        for player in result:
            for key, value in player.items():
                if pd.isna(value) or value == 'nan':
                    player[key] = 'N/A'
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching roster: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching roster: {str(e)}")

@app.get("/schedule")
def get_current_schedule():
    """Get current season schedule"""
    try:
        data = get_all_data()
        schedule_df = data.get('current_schedule', pd.DataFrame())
        
        if schedule_df.empty:
            logger.warning("Schedule data is empty")
            return []
        
        # Clean the data
        schedule_df = schedule_df.fillna('')
        
        return schedule_df.to_dict('records')
    except Exception as e:
        logger.error(f"Error fetching schedule: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching schedule: {str(e)}")

@app.get("/seasons")
def get_seasons():
    """Get list of available seasons"""
    try:
        data = get_all_data()
        seasons = data.get('seasons', {})
        return sorted(list(seasons.keys()), reverse=True)
    except Exception as e:
        logger.error(f"Error fetching seasons: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching seasons: {str(e)}")

@app.get("/seasons/{season}")
def get_season_data(season: str):
    """Get data for a specific season with cumulative scores"""
    try:
        data = get_all_data()
        seasons = data.get('seasons', {})
        
        if season not in seasons:
            raise HTTPException(status_code=404, detail=f"Season {season} not found")
        
        df = seasons[season].copy()
        
        if df.empty:
            return []
        
        # Filter out rows with no result (games not yet played)
        # Results like "N -", "-", or empty mean no game played yet
        def has_valid_result(result):
            if pd.isna(result) or result == "":
                return False
            result_str = str(result).strip()
            # Filter out placeholder results
            if result_str in ["-", "N -", "N-"]:
                return False
            # Only keep results that start with W or L
            return result_str.upper().startswith("W") or result_str.upper().startswith("L")
        
        df = df[df["Result"].apply(has_valid_result)]
        
        # Compute score change
        def compute_score(result):
            result_str = str(result).upper().strip()
            if result_str.startswith("W"):
                return 1
            elif result_str.startswith("L"):
                return -1
            return 0
        
        if not df.empty:
            df["ScoreChange"] = df["Result"].apply(compute_score)
            
            # Parse dates and sort
            df["DateParsed"] = pd.to_datetime(df["Date"], format="%m-%d-%Y", errors="coerce")
            df = df.dropna(subset=["DateParsed"]).sort_values("DateParsed")
            
            # Calculate cumulative score
            df["CumulativeScore"] = df["ScoreChange"].cumsum()
        
        # Add January 1st starting point with score 0
        # Extract the year from the season (e.g., "2025-26" -> start year 2026 for Jan 1)
        season_parts = season.split("-")
        if len(season_parts) == 2:
            start_year = season_parts[0]
            end_year = season_parts[1]
            # Use the second year (spring semester) for Jan 1
            full_end_year = "20" + end_year if len(end_year) == 2 else end_year
            jan_first = f"01-01-{full_end_year}"
            
            # Create Jan 1 starting point
            jan_first_row = pd.DataFrame([{
                "Date": jan_first,
                "Opponent": "Season Start",
                "Location": "",
                "Result": "",
                "Season": season,
                "Last_Updated": "",
                "ScoreChange": 0,
                "CumulativeScore": 0,
                "DateParsed": pd.to_datetime(jan_first, format="%m-%d-%Y")
            }])
            
            # Combine with existing data
            if not df.empty:
                df = pd.concat([jan_first_row, df], ignore_index=True)
                df = df.sort_values("DateParsed")
                # Recalculate cumulative score to ensure Jan 1 is 0
                df["CumulativeScore"] = df["ScoreChange"].cumsum()
            else:
                df = jan_first_row
        
        if df.empty:
            return []
        
        # Drop the DateParsed column before returning (keep original Date)
        df = df.drop(columns=["DateParsed"])
        
        # Clean up NaN values
        df = df.fillna('')
        
        return df.to_dict('records')
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching season data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching season data: {str(e)}")

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "UCLA Tennis API"}

@app.get("/compare/big10")
def compare_big10_schools():
    """Compare UCLA with other Big Ten schools"""
    # This is a placeholder - you'll need to add scraping logic for other schools
    # or manually maintain their data
    schools_data = {
        "UCLA": {
            "record": "1-0",
            "conference_record": "0-0",
            "ranking": "TBD",
            "last_5": ["W"]
        },
        "Ohio State": {
            "record": "0-0",
            "conference_record": "0-0",
            "ranking": "TBD",
            "last_5": []
        },
        "Michigan": {
            "record": "0-0",
            "conference_record": "0-0",
            "ranking": "TBD",
            "last_5": []
        },
        "USC": {
            "record": "0-0",
            "conference_record": "0-0",
            "ranking": "TBD",
            "last_5": []
        },
        "Penn State": {
            "record": "0-0",
            "conference_record": "0-0",
            "ranking": "TBD",
            "last_5": []
        }
    }
    return schools_data

@app.get("/schools/{school}/seasons/{season}")
def get_school_season_data(school: str, season: str):
    """Get season data for a specific school (will trigger scraping)"""
    try:
        from start import fetch_school_season_schedule
        
        # Map school names to their website URLs and formats
        school_configs = {
            "USC": {"url": "https://usctrojans.com/sports/mens-tennis/schedule/", "format": "text"},
            "Ohio State": {"url": "https://ohiostatebuckeyes.com/sports/mens-tennis/schedule/", "format": "text"},
            "Michigan": {"url": "https://mgoblue.com/sports/mens-tennis/schedule/", "format": "text"},
            "Penn State": {"url": "https://gopsusports.com/sports/mens-tennis/schedule/", "format": "season"},
            "Illinois": {"url": "https://fightingillini.com/sports/mens-tennis/schedule/", "format": "season"},
            "Northwestern": {"url": "https://nusports.com/sports/mens-tennis/schedule/", "format": "text"},
            "Indiana": {"url": "https://iuhoosiers.com/sports/mens-tennis/schedule/", "format": "text"},
            "Purdue": {"url": "https://purduesports.com/sports/mens-tennis/schedule/", "format": "season"},
            "Wisconsin": {"url": "https://uwbadgers.com/sports/mens-tennis/schedule/", "format": "text"},
            "Nebraska": {"url": "https://huskers.com/sports/mens-tennis/schedule/", "format": "season"},
            "Michigan State": {"url": "https://msuspartans.com/sports/mens-tennis/schedule/", "format": "text"}
        }
        
        if school not in school_configs:
            raise HTTPException(status_code=404, detail=f"School {school} not found")
        
        config = school_configs[school]
        df = fetch_school_season_schedule(config["url"], season, school, config["format"])
        
        if df.empty:
            logger.warning(f"No data found for {school} season {season}")
            return []
        
        # Process the data same way as UCLA
        def has_valid_result(result):
            if pd.isna(result) or result == "":
                return False
            result_str = str(result).strip()
            if result_str in ["-", "N -", "N-"]:
                return False
            return result_str.upper().startswith("W") or result_str.upper().startswith("L")
        
        df = df[df["Result"].apply(has_valid_result)]
        
        def compute_score(result):
            result_str = str(result).upper().strip()
            if result_str.startswith("W"):
                return 1
            elif result_str.startswith("L"):
                return -1
            return 0
        
        if not df.empty:
            df["ScoreChange"] = df["Result"].apply(compute_score)
            df["DateParsed"] = pd.to_datetime(df["Date"], format="%m-%d-%Y", errors="coerce")
            df = df.dropna(subset=["DateParsed"]).sort_values("DateParsed")
            df["CumulativeScore"] = df["ScoreChange"].cumsum()
        
        # Add January 1st starting point
        season_parts = season.split("-")
        if len(season_parts) == 2:
            start_year = season_parts[0]
            end_year = season_parts[1]
            full_end_year = "20" + end_year if len(end_year) == 2 else end_year
            jan_first = f"01-01-{full_end_year}"
            
            jan_first_row = pd.DataFrame([{
                "Date": jan_first,
                "Opponent": "Season Start",
                "Location": "",
                "Result": "",
                "Season": season,
                "ScoreChange": 0,
                "CumulativeScore": 0,
                "DateParsed": pd.to_datetime(jan_first, format="%m-%d-%Y")
            }])
            
            if not df.empty:
                df = pd.concat([jan_first_row, df], ignore_index=True)
                df = df.sort_values("DateParsed")
                df["CumulativeScore"] = df["ScoreChange"].cumsum()
            else:
                df = jan_first_row
        
        if df.empty:
            return []
        
        df = df.drop(columns=["DateParsed"], errors='ignore')
        df = df.fillna('')
        
        return df.to_dict('records')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching {school} season data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching {school} data: {str(e)}")

@app.get("/debug/csv")
def debug_csv():
    """Debug endpoint to check CSV file"""
    try:
        csv_path = "ucla_mens_tennis_roster.csv"
        
        if not os.path.exists(csv_path):
            return {
                "error": "CSV file not found",
                "expected_path": os.path.abspath(csv_path),
                "current_dir": os.getcwd(),
                "files_in_dir": os.listdir('.')
            }
        
        df = pd.read_csv(csv_path)
        
        return {
            "csv_found": True,
            "csv_path": os.path.abspath(csv_path),
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": list(df.columns),
            "first_3_rows": df.head(3).to_dict('records'),
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/debug/scrape/{school}/{season}")
def debug_scrape(school: str, season: str):
    """Debug endpoint to see raw scraped data"""
    try:
        from start import fetch_school_season_schedule
        
        school_urls = {
            "Penn State": "https://gopsusports.com/sports/mens-tennis/schedule/",
            "Purdue": "https://purduesports.com/sports/mens-tennis/schedule/",
            "Nebraska": "https://huskers.com/sports/mens-tennis/schedule"
        }
        
        if school not in school_urls:
            return {"error": f"School {school} not in debug list"}
        
        base_url = school_urls[school]
        df = fetch_school_season_schedule(base_url, season, school)
        
        return {
            "school": school,
            "season": season,
            "url_used": base_url + season,
            "rows_found": len(df),
            "columns": list(df.columns) if not df.empty else [],
            "raw_data": df.to_dict('records') if not df.empty else [],
            "first_5_rows": df.head(5).to_dict('records') if not df.empty else []
        }
    except Exception as e:
        return {"error": str(e), "traceback": str(e.__traceback__)}

@app.get("/schools/{school}/roster")
def get_school_roster(school: str):
    """Get roster for a specific school"""
    try:
        school_file_map = {
            "UCLA": "rosters/ucla_roster.csv",
            "USC": "rosters/usc_roster.csv",
            "Purdue": "rosters/purdue_roster.csv",
            "Penn State": "rosters/pennstate_roster.csv",
            "Nebraska": "rosters/nebraska_roster.csv",
            "Ohio State": "rosters/ohio_state_roster.csv",
            "Michigan": "rosters/michigan_roster.csv",
            "Illinois": "rosters/illinois_roster.csv",
            "Northwestern": "rosters/northwestern_roster.csv",
            "Indiana": "rosters/indiana_roster.csv",
            "Wisconsin": "rosters/wisconsin_roster.csv",
            "Michigan State": "rosters/michigan_state_roster.csv"
        }
        
        if school not in school_file_map:
            raise HTTPException(status_code=404, detail=f"Roster for {school} not found")
        
        csv_path = school_file_map[school]
        
        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail=f"Roster file not found for {school}")
        
        df = pd.read_csv(csv_path)
        df = df.fillna('N/A')
        
        return df.to_dict('records')
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching {school} roster: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching {school} roster: {str(e)}")