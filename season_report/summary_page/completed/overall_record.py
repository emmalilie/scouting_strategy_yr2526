import pandas as pd

file_path = '/Users/joshuajpark/Desktop/tc/consulting-spring2025/data/mens/mens_results.csv'
matches = pd.read_csv(file_path).drop_duplicates()
matches['Date'] = pd.to_datetime(matches['Date'])

def count_sets_won(score_str):
    if not isinstance(score_str, str):
        return 0, 0
    p1_sets = p2_sets = 0
    for s in score_str.split(','):
        s = s.strip()
        parts = s.split('-')
        if len(parts) < 2:
            continue
        try:
            p1 = int(parts[0].split('(')[0])
            p2 = int(parts[1].split('(')[0])
        except:
            continue
        if p1 > p2:
            p1_sets += 1
        else:
            p2_sets += 1
    return p1_sets, p2_sets

def get_winner(row):
    p1_sets, p2_sets = count_sets_won(row['Score'])
    if p1_sets > p2_sets:
        return row['Player1']
    elif p2_sets > p1_sets:
        return row['Player2']
    else:
        return None

if 'Winner' not in matches.columns:
    matches['Winner'] = matches.apply(get_winner, axis=1)

def get_player_record_table(player_name):
    season_start = pd.Timestamp('2024-09-19')
    conf_start = pd.Timestamp('2025-03-07')
    conf_end = pd.Timestamp('2025-04-20')
    
    player_matches = matches[
        ((matches['Player1'] == player_name) | (matches['Player2'] == player_name)) &
        (matches['Date'] >= season_start)
    ]

    player_conf_matches = player_matches[
        (player_matches['Date'] >= conf_start) & (player_matches['Date'] <= conf_end)
    ]
    
    finished_player_matches = player_matches[player_matches['Winner'].notna()]
    finished_player_conf_matches = player_conf_matches[player_conf_matches['Winner'].notna()]
    
    # Record counts
    overall_wins = (finished_player_matches['Winner'] == player_name).sum()
    overall_losses = (finished_player_matches['Winner'] != player_name).sum()
    conf_wins = (finished_player_conf_matches['Winner'] == player_name).sum()
    conf_losses = (finished_player_conf_matches['Winner'] != player_name).sum()
    
    # Return result as a DataFrame
    return pd.DataFrame([{
        'Player': player_name,
        'Overall Record': f"{overall_wins}-{overall_losses}",
        'Conference Record': f"{conf_wins}-{conf_losses}"
    }])

get_player_record_table('Rudy Quan')
