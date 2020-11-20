from flask import Flask, flash, redirect, render_template, \
     request, url_for
import requests
from collections import defaultdict
import collections 
import functools 
import operator 
import os
from .groups import player_list_boys, player_list_ctl


app = Flask(__name__)
app.secret_key = os.urandom(24)
fpl_api_base_url = 'https://fantasy.premierleague.com/api/entry/'

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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route("/scores", methods=['GET', 'POST', 'PUT'])
def display_all_week_scores():
    req = request.form
    group_name = req.get("groupname")

    if group_name in ('boys', 'Boys'):
        player_list = player_list_boys
    elif group_name in ('CTL', 'ctl'):
        player_list = player_list_ctl
    else:
        flash('No group with this name!', 'invalid group')
        return redirect(url_for('home'))

    player_data = get_player_data(player_list)
    player_scores = get_player_scores(player_data)
    weekly_scores = group_scores_by_week(player_scores)
    total_scores = calculate_total_scores(weekly_scores)
    total_points = calculate_points(weekly_scores)
    number_of_weeks_passed = len(weekly_scores) 
    colnames = [*(weekly_scores[0].keys())]
    scorenames = colnames[1:]
    winnings = calculate_winnings(total_points, number_of_weeks_passed)

    return render_template('full_scores.html', records=weekly_scores, colnames=colnames, 
        scorenames=scorenames, totals=total_scores, points=total_points, winnings=winnings, groupname = group_name)

def calculate_total_scores(scores):
    scores = scores
    total_scores = dict(functools.reduce(operator.add, 
         map(collections.Counter, scores))) 
    del total_scores['GameWeek']

    return total_scores

def calculate_points(scores, winning_points = 2, second_points = 1):
    scores = scores
    draw_win_points = (winning_points + second_points)/2
    draw_second_points = second_points/2
    
    weekly_scores = [
        sorted([(v, k) for k, v in week.items() if k[-6:] == " Score"], reverse=True)
        for week in scores
    ]
    total_scores = defaultdict(int)

    for week in weekly_scores:
        total_scores[week[0][1]] += ( #total_scores[name] += score
            winning_points if week[0][0] > week[1][0]
            else draw_win_points
        )
        total_scores[week[1][1]] += (
            draw_win_points if week[0][0] == week[1][0]
            else second_points if week[1][0] > week[2][0]
            else draw_second_points
        )
        total_scores[week[2][1]] += (
            draw_second_points if week[1][0] == week[2][0]
            else 0
        )

    return dict(total_scores)

def calculate_winnings(points, number_of_weeks):
    number_of_weeks = number_of_weeks
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

    return dict(winnings)

if __name__ == "__main__":
    app.run(debug = True)