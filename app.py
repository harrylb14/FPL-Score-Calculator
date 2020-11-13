from flask import Flask, render_template
import requests
import pandas as pd
import numpy as np
app = Flask(__name__)

@app.route("/", methods=['GET', 'POST', 'PUT'])
def home():
    return render_template('index.html')

@app.route("/scores", methods=['GET', 'POST', 'PUT'])
def gameweek_scores():
    players = [
        {'name': 'JH', 'team_id': '258789'},
        {'name': 'Harry', 'team_id': '278724'},
        {'name': 'Alex', 'team_id': '422587'}
    ]
    scores = []
    for player in players:
        player_score = []
        team_id = player['team_id']
        url = f'https://fantasy.premierleague.com/api/entry/{team_id}/history/'
        r = requests.get(url)
        json = r.json()
        data = json['current']
        for week in data:
            player_score.append(week['points'] - week['event_transfers_cost'])
        scores.append(player_score)

        print(scores)

    return render_template('full_scores.html', records=scores, colnames=['GameWeek', 'JH Score', 'Haz Score', 'Alex Score'])



app.run(debug = True)