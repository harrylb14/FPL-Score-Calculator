from app.app import app
import requests

def test_index():
    tester = app.test_client()
    response = tester.get("/", content_type="html/text")
    assert response.status_code == 200
    assert 'Hi there, Friends!' in str(response.data)

def test_view_scores():
    tester = app.test_client()
    response = tester.get('/scores', content_type="html/text")
    assert response.status_code == 200