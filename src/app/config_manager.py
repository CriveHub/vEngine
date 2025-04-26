from cryptography.fernet import Fernet
import json
import os
from json import JSONDecodeError
from logging_config import logger
import threading
from string import Template
import time
try:
    import yaml
except ImportError:
    yaml = None
    logger.warning("PyYAML non installato, fallback solo a JSON")

try:
    import jsonschema
except ImportError:
    jsonschema = None
    logger.warning("jsonschema non installato, saltiamo la validazione dello schema")

class ConfigManager:
    def __init__(self, env=None, schema_file=None):
        # Vault integration stub
        try:
            import hvac
            client = hvac.Client()
            secret = client.secrets.kv.v2.read_secret_version(path='engineproject/config')
            self.vault_key = secret['data']['data']['encryption_key']
        except Exception:
            self.vault_key = os.getenv('CONFIG_KEY')
        self.last_loaded = None  # timestamp of last config load
        # Default schema file
        if schema_file is None:
            schema_file = os.path.join(os.path.dirname(__file__), '..', 'config', 'schema.json')
        if env is None:
            env = os.environ.get("ENV", "test")
        self.env = env.lower()
        self.config_file = f"config_{self.env}.json"
        self.config = {}
        self.last_modified = None
        # Schema file for validation
        self.schema_file = schema_file or f"config_schema_{self.env}.json"
        self.schema = None
        # Thread-safety
        self.lock = threading.RLock()
        # Load default config if exists
        self.defaults = {}
        default_file = f"config_default.json"
        try:
            with open(default_file, 'r') as df:
                self.defaults = json.load(df)
        except FileNotFoundError:
            logger.info("Default config non trovato: %s", default_file)
        except JSONDecodeError as e:
            logger.error("Default config malformato in %s: %s", default_file, e)
        self.config = self.defaults.copy()
        self.last_modified = 0
        # Load JSON schema if available
        try:
            with open(self.schema_file, 'r') as sf:
                self.schema = json.load(sf)
        except FileNotFoundError:
            logger.warning("Schema file non trovato: %s, salto la validazione", self.schema_file)
        except JSONDecodeError as e:
            logger.error("Errore nel parsing JSON dello schema da %s: %s", self.schema_file, e)
        self.load_config()

    def load_config(self):
        # decrypt config if needed
        key = os.getenv('CONFIG_KEY') or Fernet.generate_key()
        f = Fernet(key)
        try:
            data = f.decrypt(open(self.config_file, 'rb').read())
            self.config = json.loads(data)
        except Exception:
            pass
        ttl = self.schema.get('config',{}).get('reload_ttl_seconds', 5)
        now = time.time()
        if self.last_loaded and now - self.last_loaded < ttl:
            return self.config  # skip reload within TTL
        self.last_loaded = now
        with self.lock:
            try:
                modified = os.path.getmtime(self.config_file)
                if self.last_modified is None or modified > self.last_modified:
                    with open(self.config_file, 'r') as f:
                        # Support JSON or YAML based on file extension
                        if yaml is not None and self.config_file.lower().endswith(('.yaml', '.yml')):
                            data = yaml.safe_load(f)
                        else:
                            data = json.load(f)
                    # Merge defaults
                    merged = {**self.defaults, **data}
                    data = merged
                    # Interpolate env vars
                    data = self._interpolate_env(data)
                    # Validate if schema library available
                    if self.schema is not None and jsonschema is not None:
                        try:
                            jsonschema.validate(instance=data, schema=self.schema)
                        except jsonschema.ValidationError as ve:
                            logger.error("Configurazione non valida in %s: %s, uso defaults", self.config_file, ve)
                            return self.config
                    self.config = data
                    self.last_modified = modified
            except FileNotFoundError:
                logger.warning("File di configurazione non trovato (%s), uso defaults", self.config_file)
                # keep self.config as defaults
                return self.config
            except JSONDecodeError as e:
                logger.error("Errore di parsing in %s: %s, uso defaults", self.config_file, e)
                return self.config
            except Exception as e:
                logger.exception("Errore caricando la configurazione da %s: %s", self.config_file, e)
                return self.config
            return self.config

    def _interpolate_env(self, value):
        if isinstance(value, str):
            return Template(value).safe_substitute(os.environ)
        if isinstance(value, dict):
            return {k: self._interpolate_env(v) for k, v in value.items()}
        if isinstance(value, list):
            return [self._interpolate_env(v) for v in value]
        return value

    def get(self, key, default=None):
        with self.lock:
            self.load_config()
            # Env var override
            env_key = f"CONFIG_{key.upper().replace('.', '_')}"
            if env_key in os.environ:
                return os.environ[env_key]
            # Nested lookup
            parts = key.split('.')
            val = self.config
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    return default
            return val if val is not None else default

    def get_int(self, key, default=0):
        try:
            return int(self.get(key, default))
        except (ValueError, TypeError):
            return default

    def get_bool(self, key, default=False):
        val = self.get(key, default)
        if isinstance(val, bool):
            return val
        if isinstance(val, str):
            return val.lower() in ("1", "true", "yes", "on")
        try:
            return bool(int(val))
        except:
            return default

    def get_list(self, key, default=None):
        if default is None:
            default = []
        val = self.get(key, default)
        if isinstance(val, list):
            return val
        if isinstance(val, str):
            return [v.strip() for v in val.split(',')]
        return default

config_manager = ConfigManager()