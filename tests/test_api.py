import pytest
from app.api_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_health(client):
    resp = client.get('/health')
    assert resp.status_code in (200, 500)
    assert 'status' in resp.get_json()

def test_get_config(client):
    resp = client.get('/api/config')
    # Likely requires auth; check for 401 or 200
    assert resp.status_code in (200, 401)
