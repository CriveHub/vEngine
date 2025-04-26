from app.db_manager import DBManager

def test_audit_logging(tmp_path):
    db = DBManager(db_url=f"sqlite:///{tmp_path/'test.db'}")
    db.log_audit(action='test', user='tester')
    session = db.Session()
    audits = session.query(db.Base.classes.audit).all()
    assert len(audits) == 1
