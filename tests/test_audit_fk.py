from app.db_manager import DBManager, Audit
from sqlalchemy import Column, Integer
def test_audit_fk(tmp_path):
    db = DBManager(db_url=f"sqlite:///{tmp_path/'db.db'}")
    # create history and audit
    session = db.Session()
    hist = db.History(timestamp=datetime.utcnow())
    session.add(hist); session.commit()
    db.log_audit('histo', 'tester', record_id=hist.id)
    entry = session.query(Audit).first()
    assert entry.record_id == hist.id
