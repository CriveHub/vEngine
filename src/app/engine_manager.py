import asyncio
import threading
from logging_config import logger
from engine import FastAsyncEngine  # Assicurati di avere il modulo engine.py implementato
from config_manager import config_manager

class EngineInstance:
    def __init__(self, engine_id, logic_filepath, cycle_time, db_path):
        self.engine_id = engine_id
        self.engine = FastAsyncEngine(logic_filepath, cycle_time, db_path)
        self.task = None  # Riferimento all'asyncio.Task in cui viene eseguito l'engine
        self.paused = False

    async def start(self):
        logger.info("Avvio engine %s", self.engine_id)
        self.task = asyncio.create_task(self.engine.run())

    async def stop(self):
        logger.info("Fermo engine %s", self.engine_id)
        await self.engine.stop()
        if self.task:
            self.task.cancel()

    async def pause(self):
        logger.info("Metto in pausa engine %s", self.engine_id)
        # Implementazione base della pausa: qui puoi inserire logica specifica per sospendere le operazioni
        self.paused = True

    async def resume(self):
        logger.info("Riprendo engine %s", self.engine_id)
        # Implementazione base della ripresa: qui puoi ripristinare le operazioni sospese
        self.paused = False

    def status(self):
        return {
            "engine_id": self.engine_id,
            "running": self.engine.running,
            "paused": self.paused,
            "last_cycle": self.engine.last_cycle_timestamp
        }

class EngineManager:
    def __init__(self):
        self.engines = {}
        self.lock = threading.Lock()

    async def add_engine(self, engine_id, logic_filepath, cycle_time, db_path):
        with self.lock:
            if engine_id in self.engines:
                raise Exception(f"Engine {engine_id} già esistente.")
            instance = EngineInstance(engine_id, logic_filepath, cycle_time, db_path)
            self.engines[engine_id] = instance
        await instance.start()
        logger.info("Engine %s aggiunto e avviato.", engine_id)

    async def remove_engine(self, engine_id):
        with self.lock:
            if engine_id not in self.engines:
                raise Exception(f"Engine {engine_id} non trovato.")
            instance = self.engines.pop(engine_id)
        await instance.stop()
        logger.info("Engine %s rimosso.", engine_id)

    async def pause_engine(self, engine_id):
        with self.lock:
            if engine_id not in self.engines:
                raise Exception(f"Engine {engine_id} non trovato.")
            instance = self.engines[engine_id]
        await instance.pause()
        logger.info("Engine %s messo in pausa.", engine_id)

    async def resume_engine(self, engine_id):
        with self.lock:
            if engine_id not in self.engines:
                raise Exception(f"Engine {engine_id} non trovato.")
            instance = self.engines[engine_id]
        await instance.resume()
        logger.info("Engine %s ripreso.", engine_id)

    def list_engines(self):
        with self.lock:
            return {eid: inst.status() for eid, inst in self.engines.items()}

engine_manager = EngineManager()

# Esempio di utilizzo asincrono (demo):
async def demo():
    # Aggiunge un engine con ID "eng1"
    await engine_manager.add_engine("eng1", "dynamic_logic_classes.py", config_manager.get("cycle_time", 0.005), config_manager.get("db_path", "states_test.db"))
    print("Engines attivi:", engine_manager.list_engines())
    await asyncio.sleep(5)
    await engine_manager.pause_engine("eng1")
    await asyncio.sleep(2)
    await engine_manager.resume_engine("eng1")
    await asyncio.sleep(5)
    await engine_manager.remove_engine("eng1")

if __name__ == '__main__':
    asyncio.run(demo())