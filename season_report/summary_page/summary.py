import pandas as pd
import re
import json
#import ipywidgets as widgets
#from IPython.display import display
import argparse

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawTextHelpFormatter,
    description="Player Selector"
)
parser.add_argument("player", help='''Use initials
    RQ - Rudy Quan
    ES -> Emon
    KB -> Kaylan
    AH -> Alex
    SJ -> Spencer
    AT -> Aadarsh
    GR -> Giac
    GB -> Gian''')
args = parser.parse_args()

# Non-Player Specific Data
mens_results = pd.read_csv('../../data/mens/mens_results.csv')[:253]
mens_results['Date'] = pd.to_datetime(mens_results['Date'])

# Class to run functions
class gen:
    def __init__(self, player):
        self.player = player
        self.combined_data_shots = pd.read_excel(f'../../data/mens/{player}/combined.xlsx', sheet_name='Shots')
        self.combined_data_points = pd.read_excel(f'../../data/mens/{player}/combined.xlsx', sheet_name='Points')
        self.combined_data_games = pd.read_excel(f'../../data/mens/{player}/combined.xlsx', sheet_name='Games')
        self.combined_data_sets = pd.read_excel(f'../../data/mens/{player}/combined.xlsx', sheet_name='Sets')
        self.combined_data_stats = pd.read_excel(f'../../data/mens/{player}/combined.xlsx', sheet_name='Stats')
        self.combined_data_settings = pd.read_excel(f'../../data/mens/{player}/combined.xlsx', sheet_name='Settings')
        
        self.results = None
        self.uclaresults = None
    
    def getmatches(self):
        data = mens_results[(mens_results['Player1'] == self.player) | (mens_results['Player2'] == self.player)]
        data = data[data['Event Name'].str.startswith(('Dual Match', '2024 ITA', '2024-25 NCAA Division'))]
        self.results = data.reset_index()

        ucla = pd.read_csv('../../data/mens/matches_2025.csv')
        ucla['player1_name'] = ucla['player1_name'].str.title()
        ucla['player2_name'] = ucla['player2_name'].str.title()
        ucla['match_winner'] = ucla['match_winner'].str.title()
        ucla = ucla[(ucla['player1_name'] == player_name) | (ucla['player2_name'] == player_name)]
        self.uclaresults = ucla
    
    def longest_rally(self):
        # Error Check
        if "Shot" not in data.columns:
            raise ValueError("The column 'Shot' was not found in the 'Shots' sheet.")
        
        # Find the index of the max shot value
        max_rally_length = data["Shot"].max()  

        # Return the value of the max shot
        return max_rally_length
    
    def average_court_time(self):
        pass
        



# Create an instance of the class to run functions that you want!
players = ['Rudy Quan', 'Emon Van Loben Sels', 'Kaylan Bigun', 'Alexander Hoogmartens', 
           'Spencer Johnson', 'Aadarsh Tripathi', 'Giacomo Revelli', 'Gianluca Ballotta']
p_map = {
    ''.join([name.split()[0][0], name.split()[-1][0]]): name
    for name in players
}
PLAYER = p_map[args.player]
instance = gen(PLAYER)
instance.getmatches()

# Run functions
print(instance.results)

