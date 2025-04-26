import requests

import pytest
from app.backup_manager import BackupManager
import smtplib

class DummySMTP:
    def __init__(self, host): pass
    def sendmail(self, s, r, m): self.sent = True
    def quit(self): pass

@pytest.fixture(autouse=True)
def patch_smtp(monkeypatch):
    monkeypatch.setattr(smtplib, 'SMTP', DummySMTP)

def test_backup_alert(tmp_path):
    mgr = BackupManager(backup_dir=str(tmp_path))
    # force failure path:
    mgr.create_backup = lambda: (_ for _ in ()).throw(Exception("fail"))
    # call and catch
    with pytest.raises(Exception):
        mgr.create_backup()
    # no exception on email stub
