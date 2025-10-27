import pandas as pd
# Path to the Excel file
file_path = "combined.xlsx"

# Read all sheets into a dict of DataFrames
df_dict = pd.read_excel(file_path, sheet_name=None)

# Access each sheet like this:
settings_df = df_dict.get("settings")
shots_df = df_dict.get("shots")
points_df = df_dict.get("points")
games_df = df_dict.get("games")
sets_df = df_dict.get("sets")
stats_df = df_dict.get("stats")
