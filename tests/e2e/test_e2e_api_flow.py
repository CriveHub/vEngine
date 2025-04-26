import requests

BASE_URL = "http://localhost:5000"

def test_login_refresh_logout_flow():
    # Login
    resp = requests.post(f"{BASE_URL}/api/login", json={"username":"admin","password":"password"})
    assert resp.status_code == 200
    token = resp.json().get('access_token')
    assert token

    # Refresh token
    refresh_resp = requests.post(f"{BASE_URL}/token/refresh", headers={"Authorization":f"Bearer {token}"})
    assert refresh_resp.status_code == 200

    # Logout
    logout_resp = requests.post(f"{BASE_URL}/logout", headers={"Authorization":f"Bearer {token}"})
    assert logout_resp.status_code == 200

    # Access protected endpoint should fail now
    config_resp = requests.get(f"{BASE_URL}/api/config", headers={"Authorization":f"Bearer {token}"})
    assert config_resp.status_code == 401
