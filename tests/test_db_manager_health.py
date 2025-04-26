from app.db_manager import DBManager

def test_db_health():
    db = DBManager()
    assert db.health_check() is True
