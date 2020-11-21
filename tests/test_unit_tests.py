import requests
from app.app import get_player_data, get_player_scores, group_scores_by_week, \
    calculate_total_scores, calculate_points, fpl_api_base_url

def test_get_player_data(requests_mock):
    test_player = [{'name': 'Test', 'team_id': '111111'}]
    requests_mock.get(f'{fpl_api_base_url}111111/history/', json= {'current':{'data': 'mock_data'}})
    resp = get_player_data(test_player)

    assert resp == [{'name': 'Test', 'team_id': '111111', 'data': {'data': 'mock_data'}}]

# def test_scores_updating_page(requests_mock):
#     test_player = [{'name': 'Test', 'team_id': '111112'}]
#     requests_mock.get(f'{fpl_api_base_url}11111/history/', json={'The game is being updated.'}) 
#     resp = get_player_data(test_player)
#     print(resp)

#     assert resp == 'Updating'

def test_get_player_scores():
    test_player_data = [
        {'name': 'Test', 'team_id': '111111', 'data': [{'event': 1, 'points': 71, 'event_transfers_cost': 0},{'event': 2, 'points': 50, 'event_transfers_cost': 0}]},
        {'name': 'Test 2', 'team_id': '111112', 'data': [{'event': 1, 'points': 30, 'event_transfers_cost': 4},{'event': 2, 'points': 80, 'event_transfers_cost': 0}]}
        ]
    result = get_player_scores(test_player_data)

    assert result == [[{'GameWeek': 1, 'Test Score': 71}, {'GameWeek': 2, 'Test Score': 50}], [{'GameWeek': 1, 'Test 2 Score': 26}, {'GameWeek': 2, 'Test 2 Score': 80}]]

def test_group_scores_by_week():
    test_score_data = [
        [{'GameWeek': 1, 'Test Score': 71}, {'GameWeek': 2, 'Test Score': 50}], 
        [{'GameWeek': 1, 'Test 2 Score': 26}, {'GameWeek': 2, 'Test 2 Score': 80}]
    ]
    result = group_scores_by_week(test_score_data)

    assert result == [{'GameWeek': 1, 'Test Score': 71, 'Test 2 Score': 26}, {'GameWeek': 2, 'Test Score': 50, 'Test 2 Score': 80}]

def test_calculate_total_scores():
    test_score_data = [
        {'GameWeek': 1, 'Test Score': 71, 'Test 2 Score': 26}, 
        {'GameWeek': 2, 'Test Score': 50, 'Test 2 Score': 80}
    ]
    result = calculate_total_scores(test_score_data)

    assert result == {'Test Score': 121, 'Test 2 Score': 106}

def test_calculate_points_no_draw():
    test_score_data = [
        {'GameWeek': 1, 'Test Score': 71, 'Test 2 Score': 26, 'Test 3 Score': 70}, 
        {'GameWeek': 2, 'Test Score': 50, 'Test 2 Score': 80, 'Test 3 Score': 30}
    ]
    result = calculate_points(test_score_data)

    assert result ==  {'Test Score': 3, 'Test 2 Score': 2, 'Test 3 Score': 1}

def test_calculate_points_with_draw():
    test_score_data = [
        {'GameWeek': 1, 'Test Score': 71, 'Test 2 Score': 71, 'Test 3 Score': 70}, 
        {'GameWeek': 2, 'Test Score': 50, 'Test 2 Score': 80, 'Test 3 Score': 50}
    ]
    result = calculate_points(test_score_data)

    assert result ==  {'Test Score': 2, 'Test 2 Score': 3.5, 'Test 3 Score': 0.5}

def test_calculate_points_with_all_scores_draw():
    test_score_data = [
        {'GameWeek': 1, 'Test Score': 71, 'Test 2 Score': 71, 'Test 3 Score': 71}, 
    ]
    result = calculate_points(test_score_data)

    assert result ==  {'Test Score': 1, 'Test 2 Score': 1, 'Test 3 Score': 1}