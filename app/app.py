from flask import Flask, flash, redirect, render_template, \
     request, url_for
import requests
import numpy as np
import collections
from collections import defaultdict, Counter
import functools
import operator
import os
from app.groups import groups
from app.captains import captains


app = Flask(__name__)
app.secret_key = os.urandom(24)
fpl_api_base_url = 'https://fantasy.premierleague.com/api/entry'
live_scores_base_url = 'https://fantasy.premierleague.com/api/event'

session = requests.session()


def retrieve_manager_data(managers):
    for manager in managers:
        team_id = manager['team_id']
        url = f'{fpl_api_base_url}/{team_id}/history/'
        r = session.get(url)
        json = r.json()
        if json == 'The game is being updated.':
            return 'Updating'

        data = json['current']
        chips = json['chips']
        manager['data'] = data
        manager['chips'] = chips

    return managers


def retrieve_managers_scores_current_gameweek(managers, gameweek):
    live_scores = {}
    player_scores = session.get(f'{live_scores_base_url}/{gameweek}/live/').json()
    # retrieves the list of players owned by a manager in a given gameweek
    for manager in managers:
        score = 0
        team_id = manager['team_id']
        name = manager['name']
        current_gameweek_players = session.get(f'{fpl_api_base_url}/{team_id}/event/{gameweek}/picks/').json()
        transfer_penalty = current_gameweek_players['entry_history']['event_transfers_cost']
        player_list = current_gameweek_players['picks']

        # gets the live score of each player and adds it to the total, including their multipler
        for player in player_list:
            player_id = player['element']
            player_data = player_scores['elements'][player_id - 1]
            player_live_score = player_data['stats']['total_points']
            score += int(player['multiplier'])*player_live_score

        live_scores[f'{name} Score'] = score - transfer_penalty

    return live_scores


def retrieve_manager_scores_previous_gameweeks(manager_data):
    manager_scores = []

    for manager in manager_data:
        manager_score = []
        name = manager['name']
        for week in manager['data']:
            manager_score.append({'GameWeek': week['event'], f'{name} Score': (week['points'] - week['event_transfers_cost'])})
        manager_scores.append(manager_score)

    return manager_scores


def group_manager_scores_by_week(manager_scores):
    array_of_week_scores = list(map(list, zip(*manager_scores)))
    scores_grouped_by_week = []
    for gmwks in array_of_week_scores:
        wk = {}
        for dic in gmwks:
            wk = {**wk, **dic}
        scores_grouped_by_week.append(wk)

    return scores_grouped_by_week


def retrieve_chip_information(manager_data):
    chip_information = []
    gameweeks_passed = len(manager_data[0]['data'])
    player_data = session.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    for week in range(1,gameweeks_passed+1):
        week_chips={}
        for manager in manager_data:
            name = manager['name']
            week_chips[f'{name} Score'] = ''

        chip_information.append(week_chips)

    for manager in manager_data:
        name = manager['name']
        chips = manager['chips']
        for chip in chips:
            chip_week = chip['event']
            chip_type = chip['name']
            player_scores = session.get(f'{live_scores_base_url}/{chip_week}/live/').json()
            if chip_type == 'wildcard':
                chip_type = 'Wildcard'
            elif chip_type == 'bboost':
                score = calculate_bench_boost_score(chip_week, manager)
                chip_type = f'Bench Boost: {score}'
            elif chip_type == '3xc':
                score = calculate_captain_score(chip_week, manager, player_scores, player_data)
                chip_type = f'Triple Captain {score[0]}: {score[1] * 3}'
            elif chip_type == 'freehit':
                score = calculate_free_hit_score(chip_week, manager)
                chip_type = f'Free Hit: {score}'

            chip_information[chip_week - 1][f'{name} Score'] = chip_type

    return chip_information


def retrieve_captain_information(manager_data):
    captain_information = []
    player_data = session.get('https://fantasy.premierleague.com/api/bootstrap-static/').json()
    for week in range(1, len(manager_data[0]['data']) + 1):
        player_scores = session.get(f'{live_scores_base_url}/{week}/live/').json()
        week_captains = {}
        for manager in manager_data:
            name = manager['name']
            captain = calculate_captain_score(week, manager, player_scores, player_data)
            captain_name = captain[0]
            captain_score = captain[1]
            captain_string = f'{captain_name}: {captain_score}'
            week_captains[f'{name} Score'] = captain_string

        captain_information.append(week_captains)

    return captain_information


@app.route("/", methods=['GET', 'POST', 'PUT'])
def home():
    return render_template('index.html')


@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.route('/scores', methods=['POST'])
def direct_to_scores():
    req = request.form
    groupname = req.get("groupname").lower()

    #search groups for entered groupname
    if not any(group['groupname'] == groupname for group in groups):
        flash('No group with this name!', 'invalid group')
        return redirect(url_for('home'))

    return redirect(url_for('.display_all_scores', groupname = groupname))


@app.route("/scores/<groupname>", methods=['GET', 'POST', 'PUT'])
def display_all_scores(groupname):
    group = next(group for group in groups if group["groupname"] == groupname)
    manager_list = group['managers']
    manager_data = retrieve_manager_data(manager_list)

    if manager_data == 'Updating':
        return render_template('updating.html')
    else:
        manager_scores = retrieve_manager_scores_previous_gameweeks(manager_data)
        weekly_scores = group_manager_scores_by_week(manager_scores)
        chip_information = retrieve_chip_information(manager_data)
        captains = retrieve_captain_information(manager_data)
        gameweek = len(weekly_scores)
        live_scores = retrieve_managers_scores_current_gameweek(manager_list, gameweek)
        weekly_scores[-1] = live_scores
        total_scores = calculate_total_scores(weekly_scores)
        total_points = calculate_manager_points(weekly_scores)

        colnames = [*(weekly_scores[0].keys())]
        scorenames = colnames[1:]
        winnings = calculate_winnings(total_points, gameweek)

    return render_template('full_scores.html', records=weekly_scores, captains=captains, chips=chip_information, colnames=colnames,
        scorenames=scorenames, totals=total_scores, points=total_points, winnings=winnings,
        groupname = groupname, live_scores = live_scores, gameweek = gameweek)


# totals scores of each gameweek
def calculate_total_scores(scores):
    total_scores = dict(functools.reduce(operator.add,
         map(collections.Counter, scores)))
    del total_scores['GameWeek']

    return total_scores

# manager points are allocated based on weekly performances. Winner_points are distributed
# amongst those in first place, and if there is only one winner, second place points
# are distributed amongst those in second place.


def calculate_manager_points(scores, winner_points=2.5, second_points=1.5, third_points=1):
    weekly_scores_sorted_descending = [
        sorted([(v, k) for k, v in week.items() if k[-6:] == " Score"], reverse=True)
        for week in scores
    ]
    total_manager_points = defaultdict(int)

    for week in weekly_scores_sorted_descending:

        score_distribution = Counter(score[0] for score in week)
        highest_score = week[0][0]
        number_of_first_place = score_distribution[highest_score]

        second_place_score = list(score_distribution)[1] if len(list(score_distribution)) > 1 else 0
        number_of_second_place = score_distribution[second_place_score] if len(list(score_distribution)) > 1 else 0

        third_place_score = list(score_distribution)[2] if len(list(score_distribution)) > 2 else 0
        number_of_third_place = score_distribution[third_place_score] if len(list(score_distribution)) > 2 else 0


        if number_of_first_place > 2:
            winning_points = (winner_points + second_points + third_points)/number_of_first_place
            second_place_points = third_place_points = 0
        elif number_of_first_place == 2:
            winning_points = (winner_points + second_points)/number_of_first_place
            second_place_points = third_points/number_of_second_place
            third_place_points = 0
        else:
            winning_points = winner_points
            if number_of_second_place == 1:
                second_place_points = second_points
                third_place_points = third_points/number_of_third_place
            else:
                second_place_points = (second_points + third_points) / number_of_second_place
                third_place_points = 0

        # if number_of_first_place > 1:
        #     winning_points = (winner_points + second_points)/number_of_first_place
        #     second_place_points = 0
        # else:
        #     winning_points = winner_points
        #     second_place_points = second_points/number_of_second_place



        for score in week:
            points = score[0]
            name = score[1]
            if points == highest_score:
                total_manager_points[name] += winning_points
            elif points == second_place_score:
                total_manager_points[name] += second_place_points
            elif points == third_place_score:
                total_manager_points[name] += third_place_points
            else:
                total_manager_points[name] += 0

    # formatting to remove .0 from whole numbers and rounds decimals to 2.dp
    total_manager_points = {k: (int(v) if (v % 1 == 0) else np.round(v, 2)) for k, v in dict(total_manager_points).items() }

    return total_manager_points


# winnings are calculated as number of manager points minus number of gameweeks passed
def calculate_winnings(manager_points, number_of_weeks):
    winnings = {}
    for player, score in manager_points.items():
        score = score - number_of_weeks
        if score >= 1:
            cash_score = "£{:,.2f}".format(score)
        elif abs(score) >= 1:
            cash_score = "-£{:,.2f}".format(abs(score))
        else:
            cash_score = f"{int(score*100)}p"
        winnings[player] = cash_score

    return dict(winnings)


def calculate_bench_boost_score(gameweek, manager):
    player_scores = session.get(f'{live_scores_base_url}/{gameweek}/live/').json()
    team_id = manager['team_id']
    gameweek_players = session.get(f'{fpl_api_base_url}/{team_id}/event/{gameweek}/picks/').json()
    player_list = gameweek_players['picks']
    bench_score = 0
    for player in player_list[11:]:
        player_id = player['element']
        player_data = player_scores['elements'][player_id - 1]
        player_live_score = player_data['stats']['total_points']
        bench_score += int(player['multiplier'])*player_live_score
    return bench_score


def calculate_captain_score(gameweek, manager, player_scores, player_data):
    team_id = manager['team_id']
    gameweek_players = session.get(f'{fpl_api_base_url}/{team_id}/event/{gameweek}/picks/').json()
    player_list = gameweek_players['picks']
    for player in player_list:
        if player['multiplier'] == 2 or player['multiplier'] == 3:
            captain_id = player['element']
            break

    captain_data = player_scores['elements'][captain_id - 1]
    captain_score = captain_data['stats']['total_points']

    for captain in captains:
        if captain_id == captain['id']:
            captain_name = captain['name']
            return [captain_name, captain_score]

    captain = [player for player in player_data['elements'] if player['id'] == captain_id][0]

    return [captain['web_name'], captain_score]


def calculate_free_hit_score(gameweek, manager):
    week_score = manager['data'][gameweek - 1]['points']
    team_id = manager['team_id']
    score_no_free_hit = 0
    original_team = session.get(f'{fpl_api_base_url}/{team_id}/event/{gameweek - 1}/picks/').json()
    player_scores = session.get(f'{live_scores_base_url}/{gameweek}/live/').json()
    original_players = original_team['picks']

    for player in original_players:     
        player_id = player['element']
        player_data = player_scores['elements'][player_id - 1]
        player_live_score = player_data['stats']['total_points']
        score_no_free_hit += int(player['multiplier'])*player_live_score

    return week_score - score_no_free_hit


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)
