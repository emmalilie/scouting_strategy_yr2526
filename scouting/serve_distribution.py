import pandas as pd

import pandas as pd
import numpy as np
import os
import json
import ipywidgets as widgets
from IPython.display import display

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

combined_data_shots = pd.read_excel(f'../../data/mens/{player_name}/combined.xlsx', sheet_name='Shots')
combined_data_points = pd.read_excel(f'../../data/mens/{player_name}/combined.xlsx', sheet_name='Points')
combined_data_games = pd.read_excel(f'../../data/mens/{player_name}/combined.xlsx', sheet_name='Games')
combined_data_sets = pd.read_excel(f'../../data/mens/{player_name}/combined.xlsx', sheet_name='Sets')
combined_data_stats = pd.read_excel(f'../../data/mens/{player_name}/combined.xlsx', sheet_name='Stats')

def average_service_time(data):

    # Use combined_data_games 
    # Subset 'Server' column name for only host (host is always UCLA player)
    # find the mean of the 'Duration' Column

    avg_seconds = data[data['Server'] == 'host']['Duration'].mean() # Automatically coerces NA
    total = int(round(avg_seconds))
    mins, secs = divmod(total, 60)    

    return f"{mins}:{secs:02d}"

# Output Average Service Game Duration
avg_service_game_duration = average_service_time(combined_data_games)
min, sec = avg_service_game_duration.split(':')
min, sec


def service_games_won_percentage(df):
    
    # Subset Dataframe to only be UCLA Player serving
    service_games = df[df["Server"] == "host"]

    # Subset to only complete games
    service_games = service_games[service_games["Game Winner"] != "draw"]

    # Find the percentage of the "Game Winner" column everytime the value is "host"
    percentage = service_games["Game Winner"].value_counts(normalize=True).get('host', 0) * 100

    # Round and make number into an integer
    percentage = int(round(percentage, 0))

    return percentage

average_games_held = str(service_games_won_percentage(combined_data_games)) + '%'
average_games_held


def breakpoints_saved_function(data):

    # Filter Data
    filtered_data = data[(data['Match Server'] == 'host') & 
                         (data['Break Point'] == True)
                         ].copy()

    percentage = int(round(filtered_data['Point Winner'].value_counts(normalize=True).get('host', 0) * 100, 0))

    return percentage


breakpoints_saved_percentage = str(breakpoints_saved_function(combined_data_points)) + '%'
breakpoints_saved_percentage


def average_aces(df):

    # Filter for the row where 'Stat Name' is 'Aces'
    aces_row = df[df['Stat Name'] == 'Aces']

    if aces_row.empty:
        print("No 'Aces' row found.")
        return None
    
    # Columns that contain the per-set values
    set_columns = [col for col in df.columns if 'Host Set' in col]

    # Extract ace counts per match from those columns
    aces_per_match = aces_row[set_columns].sum(axis=1)
    
    # Calculate and return the average
    average = aces_per_match.mean()
    return round(average, 1)

# Output Average Aces
average_aces = average_aces(combined_data_stats)
average_aces


def average_doubleFaults(df):

    # Filter only rows with Stat Name = '2nd Serves' and '2nd Serves In'
    second_serves = df[df['Stat Name'].str.strip() == '2nd Serves'].copy()
    second_serves_in = df[df['Stat Name'].str.strip() == '2nd Serves In'].copy()

    set_columns = [col for col in df.columns if 'Host Set' in col]

    second_serves_vals = second_serves[set_columns].sum(axis=1).reset_index(drop=True)
    second_serves_in_vals = second_serves_in[set_columns].sum(axis=1).reset_index(drop=True)
    average_double_faults = (second_serves_vals - second_serves_in_vals).mean()

    # Return average
    return round(average_double_faults, 1)


average_double_faults = average_doubleFaults(combined_data_stats)
average_double_faults

# Helper Function
def find_stat(df, stat_name):
    # Subset to only get rows of specified Statistic
    stat_total = df.loc[df['Stat Name'] == stat_name]

    # Grab column names
    column_names = stat_total.columns 

    # Subset column names that only start with 'Host Set'
    column_names_subset = column_names[column_names.str.startswith('Host Set')]

    # 
    stat_total_value = stat_total[column_names_subset].sum().sum()
    return stat_total_value


first_serves = find_stat(combined_data_stats, '1st Serves')   
first_serves_in = find_stat(combined_data_stats, '1st Serves In') 
first_serves_won = find_stat(combined_data_stats, '1st Serves Won')   

second_serves = find_stat(combined_data_stats, '2nd Serves')   
second_serves_in = find_stat(combined_data_stats, '2nd Serves In') 
second_serves_won = find_stat(combined_data_stats, '2nd Serves Won')   


first_serve_in_percentage = int(round((first_serves_in / first_serves) * 100, 0))
first_serve_won_percentage = int(round((first_serves_won / first_serves_in) * 100, 0))
second_serve_in_percentage = int(round((second_serves_in / second_serves) * 100, 0))
second_serve_won_percentage = int(round((second_serves_won / second_serves_in) * 100, 0))

print(f"Serve Performance Summary for {player_name}:\n")
print(f"  1st Serve In %:        {first_serve_in_percentage}%")
print(f"  1st Serve Won %:       {first_serve_won_percentage}%")
print(f"  2nd Serve In %:        {second_serve_in_percentage}%")
print(f"  2nd Serve Won %:       {second_serve_won_percentage}%")

total_serves = combined_data_points[combined_data_points['Match Server'] == 'host'].shape[0]
# total_serves = find_stat(combined_data_stats, '1st Serves') # OR this too
serve_points_won = combined_data_points[combined_data_points['Match Server'] == 'host']['Point Winner'].value_counts().get(0, 'host')

total_serve_points_won = int(round((serve_points_won / total_serves) * 100, 0))
total_serve_points_won


def serve_placement_labels(df_shots, df_points, serve_type):
    # only use matches with complete data
    # df_shots = df_shots[df_shots['__source_file__'].isin(df_points['__source_file__'])] # UPDATE: Temporary fix

    # add column for winner of the point
    combined = pd.merge(df_shots, df_points[['Point', 'Game', 'Set', 'Point Winner', 'Match Server', '__source_file__']], on=['Point', 'Game', 'Set', '__source_file__'], how='left')

    # serves = combined[(combined['Stroke'] == 'Serve') & (combined['Match Server'] == 'host')] # Added Player Name Filter (CHANGED)
    serves = combined[(combined['Type'].isin(['first_serve', 'second_serve'])) & (combined['Match Server'] == 'host')] # Added Player Name Filter
    serves_in = serves[serves['Result'] == 'In'].copy()

    # zone classification
    serves_in.loc[:, 'x_coord'] = serves_in['Bounce (x)'] * 38.2764654418
    serves_in.loc[:, 'y_coord'] = (serves_in['Bounce (y)'] - 11.8872) * 38.2764654418
    serves_in[['side', 'serve_zone']] = serves_in.apply(classify_zone, axis=1)

    # Subset by First or Second Serve
    serves_in = serves_in[(serves_in['Type'] == serve_type)]
    
    # Step 1: Get the counts for each side/zone combination
    # Chat Gpt this shi
    counts = serves_in[['side', 'serve_zone', 'Point Winner']].value_counts().reset_index(name='count')
    
    # Step 2: Group by side and zone, calculate total serves and number of wins
    summary = (
        counts
        .groupby(['side', 'serve_zone'])
        .apply(lambda df: pd.Series({
            'total': df['count'].sum(),
            'won': df[df['Point Winner'] == 'host']['count'].sum()
        }))
        .reset_index()
    )

    # Step 3: Add win percentage column
    summary['win_percentage'] = (summary['won'] / summary['total'] * 100).round(1)

    # Step 4: Extract into variables
    # Initialize dictionaries to hold count and win %
    zone_counts = {}
    zone_win_percentages = {}

    for _, row in summary.iterrows():
        key = f"{row['side'].lower()}_{row['serve_zone'].lower()}"
        zone_counts[key] = row['total']
        zone_win_percentages[key] = row['win_percentage']

    return zone_counts, zone_win_percentages

# First Serve
first_serve_zone_counts, first_serve_zone_win_percentages = serve_placement_labels(combined_data_shots, combined_data_points, 'first_serve')
first_serve_zone_counts, first_serve_zone_win_percentages

# Second Serve
second_serve_zone_counts, second_serve_zone_win_percentages = serve_placement_labels(combined_data_shots, combined_data_points, 'second_serve')
second_serve_zone_counts, second_serve_zone_win_percentages

# splits zone into two columns
def classify_zone_split(df):
    x = df['x']
    y = df['y']
    sign = x * y # if sign is pos, it's on ad side, if neg, it's deuce

    if (x < -105) or (x > 105):
        if sign > 0:
            return pd.Series(['Ad', 'Wide'])
        else:
            return pd.Series(['Deuce', 'Wide'])
    elif (-105 <= x <= -52.5) or (52.5 <= x <= 105):
        if sign > 0:
            return pd.Series(['Ad', 'Body'])
        else:
            return pd.Series(['Deuce', 'Body'])
    elif -52.5 < x < 52.5:
        if sign > 0:
            return pd.Series(['Ad', 'T'])
        else:
            return pd.Series(['Deuce', 'T'])
    else:
        return pd.Series([np.nan, np.nan])
    
def generate_placement_jsons(df_shots, df_points, serve_type):
    # only use matches with complete data
    df_shots = df_shots[df_shots['__source_file__'].isin(df_points['__source_file__'])]

    # add column for winner of the point
    combined = pd.merge(df_shots, df_points[['Point', 'Game', 'Set', 'Point Winner', 'Match Server', 'Detail', '__source_file__']], on=['Point', 'Game', 'Set', '__source_file__'], how='left')

    serves = combined[(combined['Type'] == serve_type) & (combined['Match Server'] == 'host')]
    serves_in = serves[serves['Result'] == 'In'].copy()

    # zone classification
    serves_in.loc[:, 'x'] = serves_in['Bounce (x)'] * 38.2764654418
    serves_in.loc[:, 'y'] = (serves_in['Bounce (y)'] - 11.8872) * 38.2764654418
    serves_in[['side', 'serveInPlacement']] = serves_in.apply(classify_zone_split, axis=1)

    # modify coordinates based on the y-value
    serves_in['x'] = np.where(serves_in['y'] < 0, -serves_in['x'], serves_in['x'])
    serves_in['y'] = np.where(serves_in['y'] < 0, -serves_in['y'], serves_in['y'])

    # add serve outcome
    serves_in['serveOutcome'] = serves_in['Point Winner'].apply(lambda x: 'Won' if x == 'host' else 'Lost')
    serves_in['serveOutcome'] = np.where(serves_in['Detail'] == 'Ace', 'Ace', serves_in['serveOutcome'])

    # rename some columns to match json
    serves_in = serves_in.rename(columns={'Point': 'pointNumber', 'Player': 'serverName'})

    # only get required columns
    placement = serves_in[['pointNumber', 'serverName', 'x', 'y', 'side', 'serveInPlacement', 'serveOutcome']]
    placement.to_json(f'data/{serve_type}_place.json', orient='records') # save json


    ### LABELS JSON ###

    # group by side and serveInPlacement, and calculate count and serves won
    distribution = serves_in.groupby(['side', 'serveInPlacement']).agg(
        count=('pointNumber', 'size'),
        serves_won=('Point Winner', lambda x: (x == 'host').sum())
    ).reset_index()

    # calculate the win percentage (proportion)
    distribution['proportion'] = distribution['serves_won'] / distribution['count']

    # find the min and max proportions
    min_proportion = distribution['proportion'].min()
    max_proportion = distribution['proportion'].max()

    # create labels df and determine if each value is max, min, or neither
    labels = distribution.copy()
    labels['proportion_label'] = (labels['proportion'] * 100).round(1).astype(str) + "%"
    labels['count_label'] = labels['count']

    labels['x'] = np.where(
        (labels['side'] == 'Ad') & (labels['serveInPlacement'] == 'Wide'), 131.25,
        np.where(
            (labels['side'] == 'Ad') & (labels['serveInPlacement'] == 'Body'), 78.75,
            np.where(
                (labels['side'] == 'Ad') & (labels['serveInPlacement'] == 'T'), 26.25,
                np.where(
                    (labels['side'] == 'Deuce') & (labels['serveInPlacement'] == 'T'), -26.25,
                    np.where(
                        (labels['side'] == 'Deuce') & (labels['serveInPlacement'] == 'Body'), -78.75,
                        np.where(
                            (labels['side'] == 'Deuce') & (labels['serveInPlacement'] == 'Wide'), -131.25,
                            np.nan
                        )
                    )
                )
            )
        )
    )

    # determine max/min status
    labels['max_min'] = np.where(
        labels['proportion'] == max_proportion, "max",
        np.where(labels['proportion'] == min_proportion, "min", "no")
    )

    # save labels to json
    labels.to_json(f'data/{serve_type}_place_labels.json', orient='records')

    return

generate_placement_jsons(combined_data_shots, combined_data_points, 'first_serve')
generate_placement_jsons(combined_data_shots, combined_data_points, 'second_serve')


# Formatted ratings
first_serve_in_percentage_rating_updated = '+' + str(first_serve_in_percentage_rating) + '%'
first_serve_won_percentage_rating_updated = '+' + str(first_serve_won_percentage_rating) + '%'
second_serve_won_percentage_rating_updated = '+' + str(second_serve_won_percentage_rating) + '%'
service_games_won_percentage_rating_updated = '+' + str(service_games_won_percentage_rating) + '%'
aces_average_rating_updated = '+' + str(aces_average_rating)
doubleFaults_average_rating_updated = '-' + str(doubleFaults_average_rating)

