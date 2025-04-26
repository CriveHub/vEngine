from sqlalchemy import Text, JSON
from sqlalchemy import ForeignKey, Integer
import threading
import json
import time
from logging_config import logger
from sqlalchemy import create_engine, Column, String, Integer, Float, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from alembic.config import Config
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class Audit(Base):
    record_id = Column(Integer, ForeignKey('history.id'), nullable=True)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    __tablename__ = 'audit'
    id = Column(Integer, primary_key=True)
    action = Column(String)
    user = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

from alembic import command
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

class Audit(Base):
    record_id = Column(Integer, ForeignKey('history.id'), nullable=True)
    old_value = Column(String, nullable=True)
    new_value = Column(String, nullable=True)
    __tablename__ = 'audit'
    id = Column(Integer, primary_key=True)
    action = Column(String)
    user = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)

from config_manager import config_manager
from metrics_manager import metrics_manager
from sqlalchemy.exc import SQLAlchemyError

Base = declarative_base()

class State(Base):
    __tablename__ = 'states'
    block_name = Column(String, primary_key=True)
    state = Column(Text)

class History(Base):
    __tablename__ = 'history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    block_name = Column(String)
    timestamp = Column(Float)
    state = Column(Text)

class DBManager:
    def log_audit(self, action, user, record_id=None, old_json=None, new_json=None):(self, action, user, old_value=None, new_value=None):
        session = self.Session()
        session.add(Audit(action=action,user=user,record_id=record_id,old_json=old_json,new_json=new_json))(action=action, user=user, old_value=str(old_value), new_value=str(new_value)))
        session.commit()
    
# Ensure index on audit.record_id
self.engine.execute("CREATE INDEX IF NOT EXISTS idx_audit_record_id ON audit (record_id)")

def health_check(self):
        """Check DB connectivity and ensure history timestamp index exists"""
        try:
            session = self.Session()
            session.execute('SELECT 1')
            self.engine.execute("CREATE INDEX IF NOT EXISTS idx_history_timestamp ON history (timestamp)")
            session.close()
            return True
        except Exception as e:
            logger.error(f"DB health check failed: {e}")
            raise
    def purge_history(self, days: int):
        """Delete history entries older than given days."""
        from datetime import datetime, timedelta
        cutoff = datetime.utcnow() - timedelta(days=days)
        session = self.Session()
        session.query(self.History).filter(self.History.timestamp < cutoff).delete()
        session.commit()
        logger.info(f"Purged history older than {days} days")
    def __init__(self, db_path="states.db"):
        # Determine database URL and engine
        db_url = config_manager.get("db_url", f"sqlite:///{db_path}")
        engine_args = {"connect_args": {"check_same_thread": False}} if db_url.startswith("sqlite") else {}
        self.engine = create_engine(db_url, **engine_args)
        self.SessionLocal = scoped_session(sessionmaker(bind=self.engine))

        # Record initial DB URL for metrics
        metrics_manager.increment_counter("db_init_total")

        # Run migrations via Alembic; fallback to create_all
        alembic_cfg = Config(config_manager.get("alembic_config", "alembic.ini"))
        start = time.time()
        try:
            command.upgrade(alembic_cfg, "head")
        except Exception:
            Base.metadata.create_all(self.engine)
        finally:
            duration = time.time() - start
            metrics_manager.observe_histogram("db_migration_latency_seconds", duration)

        self.lock = threading.Lock()

    def save_state(self, block_name, state):
        start = time.time()
        state_json = json.dumps(state)
        session = self.SessionLocal()
        try:
            obj = session.query(State).get(block_name)
            if obj:
                obj.state = state_json
            else:
                obj = State(block_name=block_name, state=state_json)
                session.add(obj)
            history = History(block_name=block_name, timestamp=time.time(), state=state_json)
            session.add(history)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Errore nel salvataggio dello stato per %s: %s", block_name, e)
        finally:
            duration = time.time() - start
            metrics_manager.observe_histogram("db_save_latency_seconds", duration)
            session.close()

    def get_state(self, block_name):
        start = time.time()
        session = self.SessionLocal()
        try:
            obj = session.query(State).get(block_name)
            return json.loads(obj.state) if obj else None
        finally:
            duration = time.time() - start
            metrics_manager.observe_histogram("db_get_latency_seconds", duration)
            session.close()

    def get_history(self, block_name):
        start = time.time()
        session = self.SessionLocal()
        try:
            rows = session.query(History) \
                          .filter_by(block_name=block_name) \
                          .order_by(History.timestamp) \
                          .all()
            return [(row.timestamp, json.loads(row.state)) for row in rows]
        finally:
            duration = time.time() - start
            metrics_manager.observe_histogram("db_history_latency_seconds", duration)
            session.close()

    def get_all_keys(self):
        session = self.SessionLocal()
        try:
            rows = session.query(State.block_name).all()
            return {row[0] for row in rows}
        finally:
            session.close()

    def delete_state(self, block_name):
        start = time.time()
        session = self.SessionLocal()
        try:
            session.query(State).filter_by(block_name=block_name).delete()
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error("Errore nella cancellazione dello stato per %s: %s", block_name, e)
        finally:
            duration = time.time() - start
            metrics_manager.observe_histogram("db_delete_latency_seconds", duration)
            session.close()

    def close(self):
        self.SessionLocal.remove()
        self.engine.dispose()

    
# Ensure index on audit.record_id
self.engine.execute("CREATE INDEX IF NOT EXISTS idx_audit_record_id ON audit (record_id)")

def health_check(self):
        """
        Check database connectivity and latency.
        Returns True if healthy, False otherwise.
        """
        session = self.SessionLocal()
        start = time.time()
        try:
            session.execute("SELECT 1")
            healthy = True
        except SQLAlchemyError as e:
            logger.error("DB health check failed: %s", e)
            healthy = False
        finally:
            duration = time.time() - start
            metrics_manager.observe_histogram("db_health_latency_seconds", duration)
            metrics_manager.increment_counter("db_health_total")
            session.close()
        return healthy

if __name__ == '__main__':
    # Esempio di test per il DBManager
    dbm = DBManager("states.db")
    dbm.save_state("block1", {"counter": 1})
    print("Stato di block1:", dbm.get_state("block1"))
    print("Tutti i blocchi:", dbm.get_all_keys())
    dbm.delete_state("block1")
    dbm.close()