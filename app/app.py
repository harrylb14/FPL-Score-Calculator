from flask import Flask, render_template
import requests
from collections import defaultdict
import collections 
import functools 
import operator 
import sys


app = Flask(__name__)

fpl_api_base_url = 'https://fantasy.premierleague.com/api/entry/'
player_list = [
        {'name': 'JH', 'team_id': '258789'},
        {'name': 'Harry', 'team_id': '278724'},
        {'name': 'Alex', 'team_id': '422587'}
    ]

  # players = [
    #     {'name': 'Muks(muks)', 'team_id': '4451140'},
    #     {'name': 'Harry', 'team_id': '278724'},
    #     {'name': 'TomT', 'team_id': '128932'},
    #     {'name': 'JB', 'team_id': '234477'} 
    # ]
def get_player_data(players): 
    for player in players:
        team_id = player['team_id']
        url = f'{fpl_api_base_url}{team_id}/history/'
        r = requests.get(url)
        json = r.json()
        data = json['current']
        player['data'] = data

    return players

def get_player_scores(player_data):
    players = player_data
    all_player_scores = []

    for player in players:
        player_scores = []
        name = player['name']
        for week in player['data']:
            player_scores.append({'GameWeek': week['event'], f'{name} Score': (week['points'] - week['event_transfers_cost'])})
        all_player_scores.append(player_scores)
   
    return all_player_scores

def group_scores_by_week(scores):
    all_player_scores = scores
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
    data = get_player_data(player_list)
    scores = get_player_scores(data)
    week_scores = group_scores_by_week(scores)
    colnames = [*(week_scores[0].keys())]
    scorenames = colnames[1:]
    totals = calculate_total_scores(week_scores)
    points = calculate_points(week_scores)
    winnings = dict(calculate_winnings(week_scores))

    return render_template('full_scores.html', records=week_scores, colnames=colnames, 
        scorenames=scorenames, totals=totals, points=points, winnings=winnings)

def calculate_total_scores(scores):
    scores = scores
    total_scores = dict(functools.reduce(operator.add, 
         map(collections.Counter, scores))) 
    del total_scores['GameWeek']

    return total_scores

def calculate_winnings(scores):
    points = calculate_points()
    number_of_weeks = len(scores)
    winnings = {}
    for player, score in points.items():
        score = score - number_of_weeks
        if score >= 1:
            cash_score = "£{:,.2f}".format(score)
        elif abs(score) >= 1:
            cash_score = "-£{:,.2f}".format(abs(score))
        else:
            cash_score = f"{int(score*100)}p"
        winnings[player] = cash_score

    return winnings

def calculate_points(scores):
    scores = scores
    
    weekly_scores = [
        sorted([(v, k) for k, v in week.items() if k[-6:] == " Score"], reverse=True)
        for week in scores
    ]
    total_scores = defaultdict(int)

    for week in weekly_scores:
        total_scores[week[0][1]] += ( #total_scores[name] += score
            2 if week[0][0] > week[1][0]
            else 1.5
        )
        total_scores[week[1][1]] += (
            1.5 if week[0][0] == week[1][0]
            else 1 if week[1][0] > week[2][0]
            else 0.5
        )
        total_scores[week[2][1]] += (
            0.5 if week[1][0] == week[2][0]
            else 0
        )

    return dict(total_scores)

if __name__ == "__main__":
    app.run(debug = True)