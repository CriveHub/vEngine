from prometheus_client import Histogram
io_latency = Histogram('io_latency_seconds','I/O operation latency')
db_write_duration = Histogram('db_write_duration_seconds','DB write duration')
from prometheus_client import Histogram
engine_cycle_duration = Histogram('engine_cycle_duration_seconds', 'Duration of engine cycle in seconds')
import threading
import time
import inspect
from prometheus_client import Gauge, Counter, Histogram, start_http_server
port = int(os.getenv('METRICS_PORT', '8000'))  # configurable via env
start_http_server(port)
from config_manager import config_manager

app_latency_histogram = Histogram('app_request_latency_seconds', 'Latenza delle richieste dell\'app')
app_error_counter = Counter('app_error_rate_total', 'Numero totale di errori nell\'app')
app_throughput_counter = Counter('app_throughput_total', 'Throughput totale dell\'app')

def track_global_metrics(func):
    if inspect.iscoroutinefunction(func):
        async def wrapper(*args, **kwargs):
            app_throughput_counter.inc()
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception:
                app_error_counter.inc()
                raise
            finally:
                app_latency_histogram.observe(time.time() - start)
        return wrapper
    else:
        def wrapper(*args, **kwargs):
            app_throughput_counter.inc()
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception:
                app_error_counter.inc()
                raise
            finally:
                app_latency_histogram.observe(time.time() - start)
        return wrapper

class MetricsManager:
    def __init__(self):
        self.metrics = {}
        self.lock = threading.Lock()
        self.prometheus_metrics = {}
        self.prometheus_counters = {}
        self.prometheus_histograms = {}

    def record_metric(self, name, value):
        """Registra o aggiorna la metrica di tipo Gauge con il valore specificato."""
        with self.lock:
            self.metrics[name] = value
            if name not in self.prometheus_metrics:
                self.prometheus_metrics[name] = Gauge(name, f'Metrica per {name}')
            self.prometheus_metrics[name].set(value)

    def increment_counter(self, name, amount=1):
        """Incrementa il contatore specificato del valore amount."""
        with self.lock:
            if name not in self.prometheus_counters:
                self.prometheus_counters[name] = Counter(name, f'Contatore per {name}')
            self.prometheus_counters[name].inc(amount)

    def observe_histogram(self, name, value):
        """Osserva un valore nel istogramma specificato."""
        with self.lock:
            if name not in self.prometheus_histograms:
                self.prometheus_histograms[name] = Histogram(name, f'Istopogramma per {name}')
            self.prometheus_histograms[name].observe(value)

    def get_metric(self, name):
        """Recupera il valore della metrica specificata."""
        with self.lock:
            return self.metrics.get(name)

    def get_all_metrics(self):
        """Restituisce una copia di tutte le metriche registrate."""
        with self.lock:
            return self.metrics.copy()

    def track(self, name):
        """
        Decorator to track execution metrics for functions:
        - <name>_calls_total (Counter)
        - <name>_errors_total (Counter)
        - <name>_duration_seconds (Histogram)
        """
        counter = self.prometheus_counters.setdefault(f"{name}_calls_total",
            Counter(f"{name}_calls_total", f"Numero di chiamate a {name}"))
        error_counter = self.prometheus_counters.setdefault(f"{name}_errors_total",
            Counter(f"{name}_errors_total", f"Numero di errori in {name}"))
        histogram = self.prometheus_histograms.setdefault(f"{name}_duration_seconds",
            Histogram(f"{name}_duration_seconds", f"Durata delle chiamate a {name}"))

        def decorator(func):
            if inspect.iscoroutinefunction(func):
                async def wrapper(*args, **kwargs):
                    counter.inc()
                    start = time.time()
                    try:
                        result = await func(*args, **kwargs)
                        return result
                    except Exception:
                        error_counter.inc()
                        raise
                    finally:
                        histogram.observe(time.time() - start)
                return wrapper
            else:
                def wrapper(*args, **kwargs):
                    counter.inc()
                    start = time.time()
                    try:
                        result = func(*args, **kwargs)
                        return result
                    except Exception:
                        error_counter.inc()
                        raise
                    finally:
                        histogram.observe(time.time() - start)
                return wrapper
            return wrapper
        return decorator

metrics_manager = MetricsManager()
metrics_port = config_manager.get_int("metrics_port", 8000)
start_http_server(metrics_port)  # Espone l'endpoint /metrics sulla porta configurata
port = int(os.getenv('METRICS_PORT', '8000'))  # configurable via env
start_http_server(port)
# Visita http://localhost:8000/metrics per visualizzare le metriche esposte.