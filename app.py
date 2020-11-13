from flask import Flask, render_template
import requests
import pandas as pd
import numpy as np
import logging

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST', 'PUT'])
def home():
    return render_template('index.html')

def player_scores():
    players = [
        {'name': 'JH', 'team_id': '258789'},
        {'name': 'Harry', 'team_id': '278724'},
        {'name': 'Alex', 'team_id': '422587'}
    ]
    all_player_scores = []
    for player in players:
        player_scores = []
        team_id = player['team_id']
        url = f'https://fantasy.premierleague.com/api/entry/{team_id}/history/'
        r = requests.get(url)
        json = r.json()
        data = json['current']

        for week in data:
            player_scores.append(week['points'] - week['event_transfers_cost'])
        all_player_scores.append(player_scores)
    print(all_player_scores)
    return all_player_scores

@app.route("/scores", methods=['GET', 'POST', 'PUT'])
def get_week_scores():
    all_player_scores = player_scores()
    array_of_week_scores = map(list, zip(*all_player_scores))
    print(array_of_week_scores)
    dataframe=pd.DataFrame(all_player_scores, columns=['GameWeek', 'JH Score', 'Haz Score', 'Alex Score'])  
    return dataframe



    # return render_template('full_scores.html', records=player_scores, colnames=['GameWeek', 'JH Score', 'Haz Score', 'Alex Score'])



app.run(debug = True)