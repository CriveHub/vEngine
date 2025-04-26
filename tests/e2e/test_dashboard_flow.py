import requests

BASE_URL = "http://localhost:5000"

def test_dashboard_flow():
    resp = requests.get(f"{BASE_URL}/")
    assert resp.status_code == 200
    assert "<title>Dashboard</title>" in resp.text
