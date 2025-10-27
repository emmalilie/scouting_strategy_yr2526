import pandas as pd
import numpy as np

# For clinches + lineup numbers!


def out_clinch(loc):
    df = pd.read_csv(loc)
    #print(data.head())
    df['clinches'] = df['Player_1'].where(df['Team_1'] == 'UCLA', df['Player_2'])
    clinches = df[df['Winning Team_1'] == 1].groupby('clinches').size().to_dict()
    return clinches
    
def clinch_comp(loc):
    df = pd.read_csv(loc)
    #print(data.head())
    df['clinches'] = df['Player_1'].where(df['Team_1'] == 'UCLA', df['Player_2'])
    df['Team'] = df['Team_1'].where(df['Team_1'] != 'UCLA', df['Team_2'])
    
    clinch_df = df[df['Winning Team_1'] == 1]
    
    groups = clinch_df.groupby('clinches').agg(
        clinch_c = ('Winning Team_1', 'count'),
        opps = ('Team',list)
    )
    
    clinches = groups.apply(lambda row: [row['clinch_c'], row['opps']],axis=1).to_dict()
    return clinches

def position(loc):
    df = pd.read_csv(loc)
    df['Team'] = df['Player_1'].where(df['Team_1'] == 'UCLA', df['Player_2'])
    
    groups = df.groupby(['Match','Team']).size()
    
    print(df.head)
    result = {}
    
    for (pos, name), count in groups.items():
        result.setdefault(pos, {})[name] = count
    
    sorted_result = {
        position: dict(sorted(nc.items(), key = lambda item: item[1], reverse=True))
        for position, nc in result.items()
    }
    
    maxxers = [max(x.items(), key=lambda item: item[1])[0] for x in sorted_result.values()]
    return sorted_result, maxxers

    
loc = r'C:\Users\pavan\Documents\Programming Stuff\Tennis_Consult\consulting-spring2025\data\womens\tennis_matches_data.csv'
print(out_clinch(loc))

print(clinch_comp(loc))

t = position(loc)
print(t[0])
print(t[1])
