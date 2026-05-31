import requests
import pandas as pd
import numpy as np
from datetime import datetime
from zoneinfo import ZoneInfo
import unicodedata

class UTRScraper:

    def get_user_id(self, name):
        num_results = 1
        try:
            page = requests.get(f'https://app.universaltennis.com/api/v2/search/players?query={name}&top={num_results}')
            data = page.json()
            # extract user id from either 'hits' or 'Hits' because utr has two JSON responses
            key = 'hits' if 'hits' in data else 'Hits'
            return data[key][0]['id'] if key == 'hits' else data[key][0]['Id']
        except (KeyError, IndexError, requests.exceptions.RequestException) as e:
            print(f'Error: Could not find user ID for {name}')
            
    def get_utr(self, name):
        user_id = self.get_user_id(name)
        # get player utr
        url = f'https://app.universaltennis.com/api/v1/player/{user_id}'
        page = requests.get(url)
        data = page.json()
        singles_utr = data['singlesUtr']
        return singles_utr
    
    # convert UTR scoring into a string
    def get_score_string(self, score):
        sets = []
        for i in range(1, 4):
            if str(i) in score:
                loser_score = score[str(i)]['loser'] if score[str(i)]['loser'] is not None else '0' # account for 0 stored as None in the UTR data
                set_score = f"{score[str(i)]['winner']}-{loser_score}"
                if score[str(i)]['tiebreak'] != None:
                    set_score += f"({score[str(i)]['tiebreak']})"
                sets.append(set_score)
        return ', '.join(sets)
    
    # convert date into a more readable format
    def convert_date(self, date):
        utc = datetime.fromisoformat(date).replace(tzinfo=ZoneInfo('UTC'))
        pst = utc.astimezone(ZoneInfo('America/Los_Angeles'))
        return pst.strftime('%Y-%m-%d')

    # clean the name
    def remove_accents(self, string):
        nfkd_form = unicodedata.normalize('NFKD', string)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])
    

    # get UTR rating at the time of the match
    def get_historical_UTR(self, name, match_date):
        print(name)
        # create dicitonary of (weekly) dates and UTR ratings
        user_id = self.get_user_id(name)
        url = f'https://app.universaltennis.com/api/v1/player/{user_id}/stats?type=singles&resultType=verified&Months=12&fetchAllResults=false'
        page = requests.get(url)
        stats = page.json()

        # for now, if there's no extendedRatingProfile history, return nan
        try:
            utr_history = stats['extendedRatingProfile']['history']
        except (KeyError, IndexError, TypeError):
            print(f'Error: Could not find UTR history for {name}')
            return np.nan
        if utr_history == None:
            print(f'Error: Could not find UTR history for {name}')
            return np.nan

        utr_dict = {}
        for week in utr_history:
            date = datetime.strptime(week['date'], '%Y-%m-%dT%H:%M:%S').date()
            rating = week['ratingDisplay']
            utr_dict[date] = rating

        # get the UTR rating from the closest date
        closest_date = None
        closest_diff = None
        for key in utr_dict.keys():
            diff = abs((key - match_date).days)
            if closest_diff is None or diff < closest_diff:
                closest_diff = diff
                closest_date = key

        # if closest date is more than a year away, return nan
        if closest_date is None or abs((closest_date - match_date).days) > 365:
            print(f'Error: UTR history not in range {name} on {match_date}')
            return np.nan

        return utr_dict[closest_date]



    def get_singles_results(self, name):
        user_id = self.get_user_id(name)

        # add ?type=singles for singles only
        url = f'https://app.universaltennis.com/api/v1/player/{user_id}/results?type=singles'
        page = requests.get(url)
        data = page.json()

        results = []
        for event in data['events']:
            event_name = event['name']

            if len(event['draws']) == 0:
                for result in event['results']:
                    date = self.convert_date(result['date'])
                    player1 = self.remove_accents(result['players']['winner1']['firstName'].split()[0] + ' ' + result['players']['winner1']['lastName'])
                    player2 = self.remove_accents(result['players']['loser1']['firstName'] + ' ' + result['players']['loser1']['lastName'])
                    player1_singles_utr = result['players']['winner1']['singlesUtr']
                    player2_singles_utr = result['players']['loser1']['singlesUtr']
                    player1_historical_utr = self.get_historical_UTR(player1, datetime.strptime(date, '%Y-%m-%d').date())
                    player2_historical_utr = self.get_historical_UTR(player2, datetime.strptime(date, '%Y-%m-%d').date())
                    score = self.get_score_string(result['score'])
                    results.append([event_name, date, player1, player2, score, player1_singles_utr, player2_singles_utr, player1_historical_utr, player2_historical_utr])
            else:
                for result in event['draws'][0]['results']:
                    date = self.convert_date(result['date'])
                    player1 = self.remove_accents(result['players']['winner1']['firstName'].split()[0] + ' ' + result['players']['winner1']['lastName'])
                    player2 = self.remove_accents(result['players']['loser1']['firstName'] + ' ' + result['players']['loser1']['lastName'])
                    player1_singles_utr = result['players']['winner1']['singlesUtr']
                    player2_singles_utr = result['players']['loser1']['singlesUtr']
                    player1_historical_utr = self.get_historical_UTR(player1, datetime.strptime(date, '%Y-%m-%d').date())
                    player2_historical_utr = self.get_historical_UTR(player2, datetime.strptime(date, '%Y-%m-%d').date())
                    score = self.get_score_string(result['score'])
                    results.append([event_name, date, player1, player2, score, player1_singles_utr, player2_singles_utr, player1_historical_utr, player2_historical_utr])

        singles_results = pd.DataFrame(results, columns=['Event Name', 'Date', 'Player1', 'Player2', 'Score', 'Player1 UTR', 'Player2 UTR', 'Player1 Historical UTR', 'Player2 Historical UTR'])
        return singles_results
    
    def get_doubles_results(self):
        # later?
        return


if __name__ == "__main__":

    # testing code
    scraper = UTRScraper()
    names = ["Spencer Johnson", "Gianluca Ballotta", "Cassius Chinlund", "Andrei Crabel",
            "Andy Nguyen", "Rudy Quan", "Bengt Reinhard", "Will Steinberg", "Aadarsh Tripathi",
            "Emon van Loben Sels", "Leo von Bismarck"]

    all_results = []
    for name in names:
        data = scraper.get_singles_results(name)
        all_results.append(data)

    pd.concat(all_results, ignore_index=True).to_csv('match_results.csv', index=False)


