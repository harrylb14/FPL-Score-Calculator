from app.app import app
import requests

def test_index():
    tester = app.test_client()
    response = tester.get("/", content_type="html/text")
    assert response.status_code == 200
    assert 'Enter Group Name' in str(response.data)

def test_view_scores_boys():
    tester = app.test_client()
    response = tester.post('/scores', data = {'groupname': 'boys'})
    assert response.status_code == 200
    assert 'JH Score' in str(response.data)

def test_view_scores_ctl():
    tester = app.test_client()
    response = tester.post('/scores', data = {'groupname': 'ctl'})
    assert response.status_code == 200
    assert 'TomT Score' in str(response.data)

# def test_incorrect_group_name():
#     tester = app.test_client()
#     response = tester.post('/scores', data = {'groupname': 'ctl'})
#     assert 