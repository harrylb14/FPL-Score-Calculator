import requests
from app.app import app

def test_index():
    tester = app.test_client()
    response = tester.get("/", content_type="html/text")
    assert response.status_code == 200
    assert 'Hi there, Fellas!' in str(response.data)