import json
import subprocess
import time
from prometheus_client import Gauge

from app.config_manager import config_manager
import asyncio
import os
import importlib.util
from logging_config import logger
import time
from config_manager import config_manager
import threading
from metrics_manager import metrics_manager

# Keep track of modules disabled after repeated failures
_disabled_modules = set()
_disable_timestamps = {}
_module_cache = {}
_cache_lock = threading.RLock()

def safe_load_logic(func):
    """
    Decorator to catch unexpected errors during dynamic module loading,
    log them centrally, disable the failing module, and return an empty dict.
    """
    def wrapper(filepath):
        try:
            return func(filepath)
        except Exception as e:
            # Track failures and disable module if too many
            name = module_name
            self.failure_counts[name] = self.failure_counts.get(name, 0) + 1
                self.failure_timestamps[name] = time.time()
            if self.failure_counts[name] >= self.MAX_FAILURES:
                self.failure_timestamps[name] = time.time()
                logger.error(f"Disabilito il modulo {name} dopo {self.MAX_FAILURES} fallimenti consecutivi")
                continue  # skip further loading of this module
            logger.exception("Modulo %s disabilitato a causa di un errore inatteso: %s", filepath, e)
            metrics_manager.increment_counter("dynamic_loader_unexpected_failures_total")
            _disabled_modules.add(filepath)
            _disable_timestamps[filepath] = time.time()
            return {}
    return wrapper

@safe_load_logic
def load_logic_module(filepath):
    """
    Carica dinamicamente il modulo di logica dal percorso specificato.
    Se il modulo contiene una variabile 'logic_blocks' (dizionario), la restituisce.
    Altrimenti, cerca funzioni con attributo 'execute'.
    """
    # Check disabled modules TTL and cache before loading
    with _cache_lock:
        # Disabled modules: skip or re-enable after TTL
        if filepath in _disabled_modules:
            disabled_since = _disable_timestamps.get(filepath, 0)
            disable_duration = config_manager.get_int("dynamic_loader_disable_duration", 300)
            if time.time() - disabled_since < disable_duration:
                logger.warning("Modulo %s precedentemente disabilitato, skip caricamento", filepath)
                metrics_manager.increment_counter("dynamic_loader_skipped_total")
                return {}
            # Re-enable after TTL
            _disabled_modules.remove(filepath)
            _disable_timestamps.pop(filepath, None)
        # File existence and cache check
        try:
            mtime = os.path.getmtime(filepath)
        except OSError:
            logger.error("File non trovato per dynamic loading: %s", filepath)
            metrics_manager.increment_counter("dynamic_loader_missing_file_total")
            return {}
        if filepath in _module_cache:
            cached_mtime, cached_blocks = _module_cache[filepath]
            if mtime == cached_mtime:
                metrics_manager.increment_counter("dynamic_loader_cache_hits_total")
                return cached_blocks
    # Begin load attempt
    metrics_manager.increment_counter("dynamic_loader_load_attempts_total")
    start_time = time.time()
    module_name = os.path.splitext(os.path.basename(filepath))[0]
    spec = importlib.util.spec_from_file_location(module_name, filepath)
    module = importlib.util.module_from_spec(spec)
    # Attempt to load module with retries and exponential backoff
    retries = config_manager.get_int("dynamic_loader_retries", 3)
    backoff = float(config_manager.get("dynamic_loader_backoff_base", 0.5))
    for attempt in range(1, retries + 1):
        try:
            spec.loader.exec_module(module)
            break
        except Exception:
            logger.exception("Tentativo %d fallito per il modulo %s", attempt, filepath)
            if attempt < retries:
                time.sleep(backoff * (2 ** (attempt - 1)))
            else:
                logger.error("Modulo %s disabilitato dopo %d tentativi falliti", filepath, retries)
                metrics_manager.increment_counter("dynamic_loader_load_failures_total")
                _disabled_modules.add(filepath)
                _disable_timestamps[filepath] = time.time()
                return {}
    if hasattr(module, "logic_blocks"):
        blocks = getattr(module, "logic_blocks")
        if isinstance(blocks, dict):
            # Record successful load metrics and cache result
            duration = time.time() - start_time
            metrics_manager.observe_histogram("dynamic_loader_load_duration_seconds", duration)
            metrics_manager.increment_counter("dynamic_loader_load_success_total")
            with _cache_lock:
                _module_cache[filepath] = (mtime, blocks)
            return blocks
        else:
            logger.error("Modulo %s disabilitato: 'logic_blocks' non è un dizionario.", filepath)
            _disabled_modules.add(filepath)
            _disable_timestamps[filepath] = time.time()
            return {}
    # Se non è presente 'logic_blocks', cerca funzioni che hanno un metodo execute
    blocks = {name: obj for name, obj in module.__dict__.items()
              if callable(obj) and hasattr(obj, "execute")}
    if not blocks:
        logger.error("Modulo %s disabilitato: nessuna funzione con metodo 'execute' trovata.", filepath)
        _disabled_modules.add(filepath)
        _disable_timestamps[filepath] = time.time()
        metrics_manager.increment_counter("dynamic_loader_load_failures_total")
        return {}
    # Record successful load metrics and cache result
    duration = time.time() - start_time
    metrics_manager.observe_histogram("dynamic_loader_load_duration_seconds", duration)
    metrics_manager.increment_counter("dynamic_loader_load_success_total")
    with _cache_lock:
        _module_cache[filepath] = (mtime, blocks)
    return blocks

def execute_isolated(module_path, function_name, context):
    # execute module in subprocess for isolation
    proc = subprocess.Popen(['python', module_path, function_name], stdout=subprocess.PIPE)
    return proc.communicate()[0]

def execute_isolated_json(module_path, func, context):
    proc = subprocess.Popen(['python', module_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    inp = json.dumps({'func': func, 'context': context}).encode()
    out, _ = proc.communicate(inp)
    return json.loads(out)
