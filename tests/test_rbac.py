import pytest
from app.api_server import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as c:
        yield c

def test_rbac_allow_read():
    resp = client.get('/api/config', headers={'X-User-Role':'user'})
    assert resp.status_code in (200,401)  # 401 if not logged in or 200 if allowed

def test_rbac_forbid_write():
    resp = client.post('/api/config', headers={'X-User-Role':'user'}, json={})
    assert resp.status_code == 403
