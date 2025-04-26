import argparse
import asyncio
from engine_manager import EngineManager

def main():
    parser = argparse.ArgumentParser(description="Run Async Engine")
    parser.add_argument('--config', default='config/config_prod.json', help='Path to config file')
    parser.add_argument('--env', default='prod', choices=['prod','test'], help='Environment')
    args = parser.parse_args()
    manager = EngineManager(env=args.env, config_file=args.config)

import signal
def shutdown(loop):
    for task in asyncio.all_tasks(loop):
        task.cancel()
signal.signal(signal.SIGTERM, lambda s,f: shutdown(loop))
signal.signal(signal.SIGINT, lambda s,f: shutdown(loop))

    
import signal

def _cleanup_all():
    from app.db_manager import DBManager
    from app.comms_driver import CommsDriver
    DBManager().Session().close_all()
    CommsDriver.cleanup_all()

def _shutdown(signum, frame):
    _cleanup_all()
    for task in asyncio.all_tasks():
        task.cancel()

signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)

asyncio.run(manager.start())

# Cancel all pending tasks on shutdown
import signal
def _shutdown(signum, frame):
    loop = asyncio.get_event_loop()
    for task in asyncio.all_tasks(loop):
        task.cancel()
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


# Centralized graceful shutdown
import signal
def _shutdown(signum, frame):
    engine.stop()
signal.signal(signal.SIGTERM, _shutdown)
signal.signal(signal.SIGINT, _shutdown)


    # Auto-run DB migrations
    from alembic import command
    from alembic.config import Config as AlembicConfig
    alembic_cfg = AlembicConfig(os.path.join(os.path.dirname(__file__), '..', 'alembic.ini'))
    command.upgrade(alembic_cfg, 'head')

if __name__ == "__main__":
    main()