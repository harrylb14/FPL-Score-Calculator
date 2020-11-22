from flask import Flask, flash, redirect, render_template, \
     request, url_for
import requests
import numpy as np
from collections import defaultdict, Counter
import collections 
import functools 
import operator 
import os
from .groups import player_list_boys, player_list_ctl


app = Flask(__name__)
app.secret_key = os.urandom(24)
fpl_api_base_url = 'https://fantasy.premierleague.com/api/entry'
live_scores_base_url = 'https://fantasy.premierleague.com/api/event'

def get_player_data(players): 
    for player in players:
        team_id = player['team_id']
        url = f'{fpl_api_base_url}/{team_id}/history/'
        r = requests.get(url)
        json = r.json()
        if json == 'The game is being updated.':
            return 'Updating'
            
        data = json['current']
        player['data'] = data
    
    return players

def get_managers_live_gameweek_score(managers, gameweek):
    player_scores = requests.get(f'{live_scores_base_url}/{gameweek}/live/').json()

    live_scores = {}

    for manager in managers:
        score = 0
        team_id = manager['team_id']
        name = manager['name']
        current_week_players = requests.get(f'{fpl_api_base_url}/{team_id}/event/{gameweek}/picks/').json()
        transfer_penalty = current_week_players['entry_history']['event_transfers_cost']
        player_list = current_week_players['picks']
  
        for player in player_list:
            player_id = player['element']
            player_data = player_scores['elements'][player_id - 1]
            player_live_score = player_data['stats']['total_points']
             
            score += int(player['multiplier'])*player_live_score
            
        live_scores[f'{name} Score'] = score - transfer_penalty

    return live_scores

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

    if group_name.lower() == 'boys':
        player_list = player_list_boys
    elif group_name.lower() == 'ctl':
        player_list = player_list_ctl
    else:
        flash('No group with this name!', 'invalid group')
        return redirect(url_for('home'))

    player_data = get_player_data(player_list)
    if player_data == 'Updating':
        return render_template('updating.html')
    else: 
        player_scores = get_player_scores(player_data)
        weekly_scores = group_scores_by_week(player_scores)
        gameweek = len(weekly_scores)
        live_scores = get_managers_live_gameweek_score(player_list, gameweek)
        weekly_scores[-1] = live_scores
        # xx, yy = Counter(current_week), Counter(live_scores)
        # xx.update(yy)
        # updated_current_week = xx
        # weekly_scores[-1] = updated_current_week
        total_scores = calculate_total_scores(weekly_scores)
        total_points = calculate_points(weekly_scores)
        colnames = [*(weekly_scores[0].keys())]
        scorenames = colnames[1:]
        winnings = calculate_winnings(total_points, gameweek)

    return render_template('full_scores.html', records=weekly_scores, colnames=colnames, 
        scorenames=scorenames, totals=total_scores, points=total_points, winnings=winnings, groupname = group_name, live_scores = live_scores, gameweek = gameweek)

def calculate_total_scores(scores):
    scores = scores
    total_scores = dict(functools.reduce(operator.add, 
         map(collections.Counter, scores))) 
    del total_scores['GameWeek']

    return total_scores

def calculate_points(scores, winner_points = 2, second_points = 1):
    scores = scores
    
    weekly_scores = [
        sorted([(v, k) for k, v in week.items() if k[-6:] == " Score"], reverse=True)
        for week in scores
    ]
    total_points = defaultdict(int)

    for week in weekly_scores:

        score_distribution = Counter(score[0] for score in week)
        highest_score = week[0][0]
        number_of_first_place = score_distribution[highest_score]
        second_place_score = list(score_distribution)[1] if len(list(score_distribution)) > 1 else 0
        number_of_second_place = score_distribution[second_place_score] if len(list(score_distribution)) > 1 else 0
        
        if number_of_first_place > 1: 
            winning_points = (winner_points + second_points)/number_of_first_place
            second_place_points = 0
        else:
            winning_points = winner_points
            second_place_points = second_points/number_of_second_place

        for score in week:
            points = score[0]
            name = score[1]
            if points == highest_score: 
                total_points[name] += winning_points
            elif points == second_place_score:
                total_points[name] += second_place_points
            else:
                total_points[name] += 0

    # formatting to remove .0 from whole numbers and rounds decimals to 2.dp
    total_points = {k: (int(v) if (v%1 == 0) else np.round(v, 2)) for k, v in dict(total_points).items() }

    return total_points

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