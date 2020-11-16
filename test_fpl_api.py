import requests
from app import app, get_player_data

base_fpl_url = 'https://fantasy.premierleague.com/api/entry'
def test_index():
    tester = app.test_client()
    response = tester.get("/", content_type="html/text")
    assert response.status_code == 200
    assert 'Hi there, Fellas!' in str(response.data)

def test_get_player_data(requests_mock):
    test_player = [{'name': 'Test', 'team_id': '111111'}]
    requests_mock.get(f'{base_fpl_url}/111111/history/', json= {'current':{'data': 'mock_data'}})
    resp = get_player_data(test_player)

    assert resp == [{'name': 'Test', 'team_id': '111111', 'data': {'data': 'mock_data'}}]


