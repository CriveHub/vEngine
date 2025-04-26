from abc import ABC, abstractmethod

class BaseIODriver(ABC):
    """Abstract base class for I/O drivers."""

    @abstractmethod
    async def read(self):
        pass

    @abstractmethod
    async def write(self, data):
        pass

    @abstractmethod
    async def heartbeat(self):
        pass

import time
import threading
import asyncio
from logging_config import logger
from event_bus import event_bus

class BaseIODriver:
    def __init__(self, name):
        self.name = name
        self.last_update = time.time()
        self.lock = threading.Lock()
        self.active = False

    def initialize(self):
        raise NotImplementedError("Il metodo initialize() deve essere implementato.")

    def read(self):
        raise NotImplementedError("Il metodo read() deve essere implementato.")

    def write(self, data):
        raise NotImplementedError("Il metodo write() deve essere implementato.")

    def health_check(self):
        with self.lock:
            return (time.time() - self.last_update) < 5

    def update_heartbeat(self):
        with self.lock:
            self.last_update = time.time()

class DriverManager:
    def __init__(self, health_check_interval=2):
        self.drivers = {}
        self.health_check_interval = health_check_interval
        self.running = False
        self.thread = None
        self.lock = threading.Lock()

    def register_driver(self, driver: BaseIODriver):
        with self.lock:
            self.drivers[driver.name] = driver
            logger.info("Driver registrato: %s", driver.name)

    def unregister_driver(self, driver_name):
        with self.lock:
            if driver_name in self.drivers:
                del self.drivers[driver_name]
                logger.info("Driver rimosso: %s", driver_name)

    def initialize_drivers(self):
        with self.lock:
            for driver in self.drivers.values():
                try:
                    driver.initialize()
                    driver.active = True
                    logger.info("Driver inizializzato: %s", driver.name)
                except Exception as e:
                    logger.error("Errore nell'inizializzazione del driver %s: %s", driver.name, e)
                    driver.active = False

    def poll_drivers(self):
        while self.running:
            with self.lock:
                for driver in self.drivers.values():
                    if not driver.health_check():
                        logger.error("Driver non sano: %s", driver.name)
                        event_bus.publish("driver_error", {"driver": driver.name})
            time.sleep(self.health_check_interval)

    def start(self):
        self.initialize_drivers()
        self.running = True
        self.thread = threading.Thread(target=self.poll_drivers, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    async def read_driver(self, driver_name):
        with self.lock:
            driver = self.drivers.get(driver_name)
        if not driver:
            raise Exception(f"Driver {driver_name} non trovato")
        if asyncio.iscoroutinefunction(driver.read):
            return await driver.read()
        else:
            return await asyncio.to_thread(driver.read)

    async def write_driver(self, driver_name, data):
        with self.lock:
            driver = self.drivers.get(driver_name)
        if not driver:
            raise Exception(f"Driver {driver_name} non trovato")
        if asyncio.iscoroutinefunction(driver.write):
            return await driver.write(data)
        else:
            return await asyncio.to_thread(driver.write, data)

if __name__ == '__main__':
    # Esempio di test con un driver dummy
    dm = DriverManager()
    
    class DummyIODriver(BaseIODriver):
        def initialize(self):
            logger.info("DummyIODriver inizializzato.")
            self.active = True
            self.update_heartbeat()

        def read(self):
            self.update_heartbeat()
            return {"dummy": 123}

        def write(self, data):
            self.update_heartbeat()
            logger.info("DummyIODriver write: %s", data)

        def health_check(self):
            self.update_heartbeat()
            return True

    dummy = DummyIODriver("Dummy1")
    dm.register_driver(dummy)
    dm.start()

    async def test():
        data = await dm.read_driver("Dummy1")
        print("Dati letti:", data)

    asyncio.run(test())
    dm.stop()

class BatchIODriver(BaseIODriver):
    """Driver for batch I/O operations in parallel."""
    def __init__(self, drivers):
        self.drivers = drivers  # list of BaseIODriver

    async def read_all(self):
        results = await asyncio.gather(*(drv.read() for drv in self.drivers))
        return results

    async def write_all(self, data_list):
        await asyncio.gather(*(drv.write(data) for drv, data in zip(self.drivers, data_list)))

    async def heartbeat(self):
        await asyncio.gather(*(drv.heartbeat() for drv in self.drivers))


# Example usage of BatchIODriver:
# batch = BatchIODriver([ModbusDriver(...), ProfinetDriver(...)])
# results = await batch.read_all()


class MockDriver(BaseIODriver):
    """Mock driver for integration tests."""
    async def read(self): return 'mock'
    async def write(self, data): return True
    async def heartbeat(self): return True

# Example: batch = BatchIODriver([MockDriver(), ...]); await batch.read_all()


class ConfigurableMockDriver(MockDriver):
    import random
    from asyncio import sleep
    async def read(self):
        await sleep(self.latency + random.uniform(0, self.latency))
        if random.random() < self.error_rate:
            raise Exception('Simulated error')
        return 'data'
    def __init__(self, latency=0, error_rate=0):
        self.latency = latency
        self.error_rate = error_rate
    async def read(self):
        time.sleep(self.latency)
        if random.random() < self.error_rate:
            raise Exception('Simulated error')
        return 'data'

# End of IO enhancements
