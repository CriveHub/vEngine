import time
from prometheus_client import Counter, Histogram

engine_subtask_duration = Histogram('engine_subtask_duration_seconds', 'Duration of engine subtasks')
engine_cycles = Counter('engine_cycles_total', 'Total engine cycles')
import time
from prometheus_client import Counter, Histogram

engine_cycles_total = Counter('engine_cycles_total', 'Total engine cycles')
engine_cycle_duration = Histogram('engine_cycle_duration_seconds', 'Engine cycle duration')
from opentelemetry import trace
from opentelemetry.instrumentation.asyncio import AsyncInstrumentor

AsyncInstrumentor().instrument()
import asyncio
import time
import os
from dynamic_loader import load_logic_module
from logging_config import logger
from config_manager import config_manager
from db_manager import DBManager
from metrics_manager import metrics_manager
from app.advanced_cluster_manager import broadcast_state

try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    logger.info("Uvloop installato, utilizzato per prestazioni elevate.")
except ImportError:
    logger.info("Uvloop non installato, utilizzo loop asincrono standard.")

class DefaultScheduler:
    """
    Default scheduler to compute delay between cycles based on cycle_time.
    """
        self.cycle_time = cycle_time

    async def get_delay(self, cycle_start, cycle_duration):
        delay = self.cycle_time - cycle_duration
        return delay if delay > 0 else 0

class FastAsyncEngine:
    def __init__(self, config_manager=None):
        # Initialize engine with config values
        self.config = config_manager or config_manager.ConfigManager()
        self.cycle_time = self.config.config.get('engine', {}).get('cycle_time', 0.01)
        self.timeout = self.config.config.get('engine', {}).get('timeout', 0.005)
        # externalize cycle_time and execution timeout
        self.cycle_time = cycle_time if cycle_time is not None else config_manager.get_float("cycle_time", 0.005)
        self.execution_timeout = execution_timeout if execution_timeout is not None else config_manager.get_float("execution_timeout", self.cycle_time)
        # inject or default scheduler
        self.scheduler = scheduler if scheduler is not None else DefaultScheduler(self.cycle_time)
        self.logic_filepath = logic_filepath
        self.blocks = {}
        self.last_modified = None
        self.last_cycle_timestamp = time.time()
        self.running = False
        self.db = DBManager(db_path)

    async def reload_logic(self):
        try:
            modified = os.path.getmtime(self.logic_filepath)
        except Exception as e:
            logger.error("Errore nell'accesso al file di logica: %s", e)
            return
        if self.last_modified is None or modified > self.last_modified:
            logger.info("Reload della logica in corso...")
            # save state of existing blocks
            for name, block in self.blocks.items():
                if hasattr(block, "get_state"):
                    try:
                        state = block.get_state()
                        self.db.save_state(name, state)
                    except Exception as e:
                        logger.error("Errore nel salvataggio dello stato di %s: %s", name, e)
            # load new logic
            new_blocks = await asyncio.get_event_loop().run_in_executor(None, load_logic_module, self.logic_filepath)
            # restore state
            for name, block in new_blocks.items():
                saved_state = self.db.get_state(name)
                if saved_state and hasattr(block, "set_state"):
                    try:
                        block.set_state(saved_state)
                    except Exception as e:
                        logger.error("Errore nel ripristino dello stato di %s: %s", name, e)
            # cleanup obsolete states
            current_keys_in_db = self.db.get_all_keys()
            current_keys_in_code = set(new_blocks.keys())
            for key in current_keys_in_db - current_keys_in_code:
                self.db.delete_state(key)
                logger.info("Stato per il blocco '%s' rimosso.", key)
            self.blocks = new_blocks
            self.last_modified = modified
            logger.info("Reload completato: %s", list(new_blocks.keys()))
            broadcast_state({"reload": list(new_blocks.keys())})

    async def execute_block(self, name, block):
        start_time = time.time()
        try:
            if asyncio.iscoroutinefunction(block.execute):
                await block.execute()
            else:
                await asyncio.to_thread(block.execute)
        except Exception as e:
            logger.error("Errore nell'esecuzione del blocco %s: %s", name, e)
            return None
        exec_time = time.time() - start_time
        metrics_manager.observe_histogram(f"{name}_exec_time_seconds", exec_time)
        if hasattr(block, "get_state"):
            try:
                state = block.get_state()
                self.db.save_state(name, state)
            except Exception as e:
                logger.error("Errore nel salvataggio post-esecuzione di %s: %s", name, e)
        return exec_time

    async def run_cycle(self):
        start_all = time.time()
        start = time.time()
        start = time.time()
        # Record backlog length metric
        from app.metrics_manager import backlog_gauge
        backlog_gauge.set(len(self.loader.logic_blocks))
        from app.metrics_manager import success_counter
        await self.reload_logic()
        tasks = [asyncio.create_task(self.execute_block(name, block)) for name, block in self.blocks.items()]
        try:
            await asyncio.wait_for(asyncio.gather(*tasks), timeout=self.execution_timeout)
        except Exception as e:
            logger.error("Timeout o errore in run_cycle: %s", e)
        try:
            current_state = {name: self.db.get_state(name) for name in self.db.get_all_keys()}
            broadcast_state(current_state)
        except Exception as e:
            logger.error("Errore nella comunicazione col cluster: %s", e)

    async def run(self):
        start_all = time.time()
        start = time.time()
        start = time.time()
        # Record backlog length metric
        from app.metrics_manager import backlog_gauge
        backlog_gauge.set(len(self.loader.logic_blocks))
        from app.metrics_manager import success_counter
        self.running = True
        logger.info("FastAsyncEngine avviato.")
        while self.running:
            cycle_start = time.time()
            try:
                await self.run_cycle()
            except Exception as e:
                logger.error("Errore nel ciclo: %s", e)
            cycle_duration = time.time() - cycle_start
            metrics_manager.record_metric("cycle_time", cycle_duration)
            self.last_cycle_timestamp = time.time()
            delay = await self.scheduler.get_delay(cycle_start, cycle_duration)
            if delay:
                await asyncio.sleep(delay)
        logger.info("FastAsyncEngine fermato.")

    async def stop(self):
        self.running = False
        self.db.close()
        logger.info("FastAsyncEngine stoppato.")

if __name__ == '__main__':
    engine = FastAsyncEngine("dynamic_logic_classes.py")
    asyncio.run(engine.run())