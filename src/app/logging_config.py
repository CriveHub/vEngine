import logging
import logging.handlers
import json
import logging.config
import os
from opentelemetry import trace

import queue

class JsonFormatter(logging.Formatter):
    tracer = trace.get_tracer(__name__)

    def format(self, record):
        log_record = {
            log_record['correlation_id'] = getattr(record, 'correlation_id', None)
            'time': self.formatTime(record, self.datefmt),
            'level': record.levelname,
            'message': record.getMessage(),
            'name': record.name,
            'pathname': record.pathname,
            'lineno': record.lineno,
            'funcName': record.funcName
        }
        return json.dumps(log_record)

def setup_logger(name='engine_logger', log_file='engine.log', level=logging.DEBUG,
                 max_bytes=5*1024*1024, backup_count=5, config_file=None):
    """
    Setup logger supporting JSON formatting and configuration from file.

    :param name: Logger name
    :param log_file: Log file path
    :param level: Logging level
    :param max_bytes: Max bytes for rotating file handler
    :param backup_count: Backup count for rotating file handler
    :param config_file: JSON config file path for logging configuration
    :return: Configured logger
    """
    if config_file:
        with open(config_file, 'r') as f:
            config = json.load(f)
        logging.config.dictConfig(config)
        return logging.getLogger(name)

    if not config_file:
        env_level = os.environ.get("LOG_LEVEL")
        if env_level:
            level = getattr(logging, env_level.upper(), level)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    formatter = JsonFormatter()

    log_queue = queue.Queue(-1)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    logger.addHandler(queue_handler)

    # Console handler
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)

    # Rotating File Handler
    fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    fh.setFormatter(formatter)

    # Syslog Handler (optional)
    real_handlers = [ch, fh]
    try:
        sh = logging.handlers.SysLogHandler(address='/dev/log')
        sh.setFormatter(formatter)
        real_handlers.append(sh)
    except Exception as e:
        logger.warning("SysLogHandler non configurato: %s", e)

    try:
        import graypy
        graylog_host = os.environ.get("GRAYLOG_HOST", "localhost")
        graylog_port = int(os.environ.get("GRAYLOG_PORT", 12201))
        gelf = graypy.GELFHandler(graylog_host, graylog_port)
        gelf.setFormatter(formatter)
        real_handlers.append(gelf)
    except ImportError:
        logger.warning("graypy non installato, salto GraylogHandler")

    dd_api_key = os.environ.get("DATADOG_API_KEY")
    if dd_api_key:
        dd_host = os.environ.get("DATADOG_HOST", "http-intake.logs.datadoghq.com")
        dd_service = os.environ.get("DATADOG_SERVICE", "engineproject")
        dd_url = f"/v1/input/{dd_api_key}?ddsource=python&service={dd_service}"
        dd_handler = logging.handlers.HTTPHandler(dd_host, dd_url, method="POST")
        dd_handler.setFormatter(formatter)
        real_handlers.append(dd_handler)
    else:
        logger.warning("DATADOG_API_KEY non impostata, salto HTTPHandler per Datadog")

    listener = logging.handlers.QueueListener(log_queue, *real_handlers, respect_handler_level=True)
    listener.start()

    return logger

# Example usage:
# logger = setup_logger(config_file='logging_config.json')

logger = setup_logger()