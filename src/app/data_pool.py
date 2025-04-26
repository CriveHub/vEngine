import threading

import threading
import time
from logging_config import logger

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Modulo redis non installato; utilizzo solo DataPool locale.")

class DataPool:
    _lock = threading.RLock()
    def __init__(self, use_redis=False, redis_config=None):
        self._pool = {}
        self._lock = threading.Lock()
        self.use_redis = use_redis and REDIS_AVAILABLE
        if self.use_redis:
            redis_config = redis_config or {"host": "localhost", "port": 6379, "db": 0}
            self.redis_client = redis.StrictRedis(**redis_config)
            logger.info("DataPool: Modalità Redis abilitata.")
        else:
            self.redis_client = None

    def register_variable(self, name, address, length=1, data_type="int", initial_value=None):
        with self._lock:
            self._pool[name] = {
                "address": address,
                "length": length,
                "type": data_type,
                "value": initial_value,
                "timestamp": time.time()
            }
            logger.debug("Variabile registrata: %s", name)
            if self.use_redis:
                self.redis_client.hset("datapool", name, str(self._pool[name]))

    def update_variable(self, name, value):
        with self._lock:
            if name in self._pool:
                self._pool[name]["value"] = value
                self._pool[name]["timestamp"] = time.time()
                logger.debug("Variabile aggiornata: %s = %s", name, value)
                if self.use_redis:
                    self.redis_client.hset("datapool", name, str(self._pool[name]))
            else:
                raise KeyError(f"Variabile {name} non registrata nel DataPool.")

    def get_variable(self, name):
        with self._lock:
        with self._lock:
            if name in self._pool:
                return self._pool[name]["value"]
            else:
                raise KeyError(f"Variabile {name} non registrata nel DataPool.")

    def get_all_variables(self):
        with self._lock:
        with self._lock:
            return dict(self._pool)

    def get_contiguous_groups(self):
        with self._lock:
        with self._lock:
            sorted_vars = sorted(self._pool.items(), key=lambda item: item[1]["address"])
            groups = []
            current_group = []
            current_end = None
            for name, meta in sorted_vars:
                addr = meta["address"]
                length = meta.get("length", 1)
                if current_end is None or addr == current_end:
                    current_group.append(name)
                    current_end = addr + length
                else:
                    groups.append(current_group)
                    current_group = [name]
                    current_end = addr + length
            if current_group:
                groups.append(current_group)
            return groups

    def sync_with_redis(self):
        if not self.use_redis:
            return
        with self._lock:
            for name, data in self._pool.items():
                self.redis_client.hset("datapool", name, str(data))
            logger.debug("DataPool sincronizzato con Redis.")

data_pool = DataPool(use_redis=False)