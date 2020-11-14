from flask import Flask, render_template
import requests
import pandas as pd
import numpy as np
import logging
from collections import defaultdict
import collections 
import functools 
import operator 


app = Flask(__name__)

def get_player_data():
    players = [
        {'name': 'JH', 'team_id': '258789'},
        {'name': 'Harry', 'team_id': '278724'},
        {'name': 'Alex', 'team_id': '422587'}
    ]

    # players = [
    #     {'name': 'Muks(muks)', 'team_id': '4451140'},
    #     {'name': 'Harry', 'team_id': '278724'},
    #     {'name': 'TomT', 'team_id': '128932'}
    # ]
    
    for player in players:
        team_id = player['team_id']
        url = f'https://fantasy.premierleague.com/api/entry/{team_id}/history/'
        r = requests.get(url)
        json = r.json()
        data = json['current']
        player['data'] = data

    return players

def get_player_scores():
    players = get_player_data()
    all_player_scores = []

    for player in players:
        player_scores = []
        name = player['name']
        for week in player['data']:
            player_scores.append({'GameWeek': week['event'], f'{name} Score': (week['points'] - week['event_transfers_cost'])})
        all_player_scores.append(player_scores)

    return all_player_scores

def group_scores_by_week():
    all_player_scores = get_player_scores()
    array_of_week_scores = list(map(list, zip(*all_player_scores)))
    scores_grouped_by_week = []
    for gmwks in array_of_week_scores:
        wk = {}
        for dic in gmwks:
            wk = {**wk, **dic}
        scores_grouped_by_week.append(wk)

    return scores_grouped_by_week

@app.route("/", methods=['GET', 'POST', 'PUT'])
def home():
    return render_template('index.html')

@app.route("/scores", methods=['GET', 'POST', 'PUT'])
def display_all_week_scores():
    week_scores = group_scores_by_week()
    colnames = week_scores[0].keys()
    totals = calculate_total_scores()
    print(totals)

    return render_template('full_scores.html', records=week_scores, colnames=colnames, totals=totals)

def calculate_total_scores():
    scores = group_scores_by_week()
    total_scores = dict(functools.reduce(operator.add, 
         map(collections.Counter, scores))) 
    del total_scores['GameWeek']
    return total_scores

app.run(debug = True)