import pandas as pd
import os

# ── Config ────────────────────────────────────────────────────────────────────
CONF_START = pd.Timestamp('2026-01-01')
CONF_END   = pd.Timestamp('2026-05-31')

# ── Load data ─────────────────────────────────────────────────────────────────
mens_results = pd.read_csv('C:\\Users\\emmal\\OneDrive\\Desktop\\scounting_strategy_yr2526\\dashboard\\backend\\match_results.csv')
mens_results['Date'] = pd.to_datetime(mens_results['Date'])

# ── Helpers ───────────────────────────────────────────────────────────────────
def count_sets_won(score):
    if not isinstance(score, str) or not score.strip():
        return 0, 0
    p1, p2 = 0, 0
    for set_score in score.split():
        parts = set_score.split('-')
        if len(parts) != 2:
            continue
        try:
            a, b = int(parts[0]), int(parts[1].split('(')[0])
            if a > b:
                p1 += 1
            elif b > a:
                p2 += 1
        except ValueError:
            continue
    return p1, p2


def get_winner(row):
    p1_sets = row.get('player1_sets', 0)
    p2_sets = row.get('player2_sets', 0)
    if p1_sets == p2_sets:
        return 'Unfinished'
    return row['Player1'] if p1_sets > p2_sets else row['Player2']


def filter_player(data, player_name):
    data = data[(data['Player1'] == player_name) | (data['Player2'] == player_name)]
    data = data[data['Event Name'].str.startswith(
        ('Dual Match', '2025 ITA', '2025-26 NCAA Division'), na=False
    )]
    data = data[data['Date'] > '2025-08-01']
    return data


def compute_records(player_name):
    player_matches = filter_player(mens_results, player_name)

    if player_matches.empty:
        return "0-0", "0-0"

    df = player_matches.copy()
    df[['player1_sets', 'player2_sets']] = (
        df['Score'].apply(count_sets_won).apply(pd.Series)
    )
    df['result'] = df.apply(get_winner, axis=1)
    conf = df[(df['Date'] >= CONF_START) & (df['Date'] <= CONF_END)]

    ow = int((df['result'] == player_name).sum())
    ol = int(((df['result'] != player_name) & (df['result'] != 'Unfinished')).sum())
    cw = int((conf['result'] == player_name).sum())
    cl = int(((conf['result'] != player_name) & (conf['result'] != 'Unfinished')).sum())

    return f"{ow}-{ol}", f"{cw}-{cl}"


# ── Apply to every player ─────────────────────────────────────────────────────
SCHOOL_KEYS = [
    "ucla", "usc", "michigan", "ohio_state", "penn_state",
    "indiana", "illinois", "northwestern", "purdue",
    "wisconsin", "nebraska", "michigan_state",
]

for school_key in SCHOOL_KEYS:
    roster_path = f"C:\\Users\\emmal\\OneDrive\\Desktop\\scounting_strategy_yr2526\\dashboard\\backend\\rosters\\{school_key}_roster.csv"
    if not os.path.exists(roster_path):
        print(f"[SKIP] {roster_path} not found")
        continue

    roster_df = pd.read_csv(roster_path)
    
    results = roster_df['Player'].apply(lambda name: pd.Series(
        compute_records(name.strip()),
        index=['Overall_Record', 'Conference_Record']
    ))

    roster_df['Overall_Record']    = results['Overall_Record']
    roster_df['Conference_Record'] = results['Conference_Record']

    roster_df.to_csv(roster_path, index=False)
    print(f"Saved -> {roster_path}")