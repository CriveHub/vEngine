def test_audit_old_new(tmp_path):
    db = DBManager(db_url=f"sqlite:///{tmp_path/'test.db'}")
    # simulate change
    old = {'key':1}; new = {'key':2}
    db.log_audit('update', 'tester', old_value=old, new_value=new)
    session = db.Session()
    entry = session.query(Audit).first()
    assert entry.old_value == str(old)
    assert entry.new_value == str(new)
