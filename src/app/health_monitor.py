import time
from prometheus_client import Gauge
from logging_config import logger

uptime_gauge = Gauge('app_uptime_seconds', 'Application uptime in seconds')
last_check_gauge = Gauge('app_last_health_check_timestamp', 'Timestamp of last health check')

import time
import threading
from logging_config import logger

class HealthMonitor:
    def __init__(self, engine, api_server_thread, dashboard_server_thread,
                 engine_threshold=5, check_interval=2,
                 restart_engine_callback=None, restart_api_callback=None,
                 restart_dashboard_callback=None):
        self.engine = engine
        self.api_server_thread = api_server_thread
        self.dashboard_server_thread = dashboard_server_thread
        self.engine_threshold = engine_threshold
        self.check_interval = check_interval
        self.restart_engine_callback = restart_engine_callback
        self.restart_api_callback = restart_api_callback
        self.restart_dashboard_callback = restart_dashboard_callback
        self.running = False
        self.thread = None

    def monitor(self):
        while self.running:
            now = time.time()
            if self.engine:
                last_cycle = getattr(self.engine, "last_cycle_timestamp", None)
                if last_cycle is None:
                    logger.error("Engine health: last_cycle_timestamp non impostato.")
                else:
                    if now - last_cycle > self.engine_threshold:
                        logger.error("Engine heartbeat stale: %.2f secondi", now - last_cycle)
                        if self.restart_engine_callback:
                            self.restart_engine_callback()
            if self.api_server_thread and not self.api_server_thread.is_alive():
                logger.error("API server thread non attivo.")
                if self.restart_api_callback:
                    self.restart_api_callback()
            if self.dashboard_server_thread and not self.dashboard_server_thread.is_alive():
                logger.error("Dashboard server thread non attivo.")
                if self.restart_dashboard_callback:
                    self.restart_dashboard_callback()
            time.sleep(self.check_interval)

    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self.monitor, daemon=True)
        self.thread.start()

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()