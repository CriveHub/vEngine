from opentelemetry import trace
from opentelemetry.instrumentation.asyncio import AsyncInstrumentor

AsyncInstrumentor().instrument()
import asyncio
import socket
from logging_config import logger
from io_manager import BaseIODriver
from global_context import data_pool
from config_manager import config_manager
from metrics_manager import metrics_manager
import abc

class RetryMixin(abc.ABC):
    """
    Mixin for retry with exponential backoff, with metrics instrumentation.
    Expects the consuming class to define:
    - self.retries (int)
    - self.backoff_base (float)
    - self.timeout (float)
    - self.name (str)
    """
    async def retry_with_backoff(self, coro_func, *args, **kwargs):
        for attempt in range(self.retries):
            start_time = asyncio.get_event_loop().time()
            try:
                result = await asyncio.wait_for(coro_func(*args, **kwargs), timeout=self.timeout)
                duration = asyncio.get_event_loop().time() - start_time
                metrics_manager.observe_histogram(f"{self.name}_operation_duration_seconds", duration)
                return result
            except Exception as e:
                wait_time = self.backoff_base * (2 ** attempt)
                metrics_manager.increment_counter(f"{self.name}_retry_attempts_total")
                logger.warning("Tentativo %d fallito per %s: %s. Riprovo in %.2f secondi.", attempt + 1, self.name, e, wait_time)
                await asyncio.sleep(wait_time)
        metrics_manager.increment_counter(f"{self.name}_failures_total")
        logger.error("Tutti i tentativi falliti per %s", self.name)
        raise Exception(f"Operazione fallita dopo {self.retries} tentativi.")

# Modifica a BaseIODriver: aggiunta metodi astratti read e write
class BaseIODriver(abc.ABC):
    def __init__(self, name):
        self.name = name
        self.active = False
        self._last_heartbeat = None

    def update_heartbeat(self):
        self._last_heartbeat = asyncio.get_event_loop().time()

    @abc.abstractmethod
    async def read(self):
        raise NotImplementedError

    @abc.abstractmethod
    async def write(self, data):
        raise NotImplementedError

# ProfinetDriver implementato con socket UDP
# Supporta mocking tramite interfaccia base
class ProfinetDriver(RetryMixin, BaseIODriver):
    def __init__(self, name, ip, port=102, timeout=None, retries=None, backoff_base=None, handshake_delay=None, circuit_breaker_enabled=False):
        super().__init__(name)
        self.ip = ip
        self.port = port
        self.timeout = timeout if timeout is not None else config_manager.get("comms_timeout", 1.0)
        self.retries = retries if retries is not None else config_manager.get("comms_retries", 3)
        self.backoff_base = backoff_base if backoff_base is not None else config_manager.get("comms_backoff_base", 0.1)
        self.handshake_delay = handshake_delay if handshake_delay is not None else config_manager.get("comms_handshake_delay", 0.01)
        self.sock = None
        self.circuit_breaker_enabled = circuit_breaker_enabled
        self._failure_count = 0
        self._circuit_open = False
        self._circuit_open_until = None
        self._circuit_open_duration = 10  # seconds

    async def _send_handshake(self):
        await asyncio.to_thread(self.sock.sendto, b'PROFINET_HANDSHAKE', (self.ip, self.port))

    async def initialize(self):
        logger.info("Inizializzazione ProfinetDriver %s verso %s:%d", self.name, self.ip, self.port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        try:
            await self.retry_with_backoff(self._send_handshake)
            await asyncio.sleep(self.handshake_delay)
            self.active = True
            self.update_heartbeat()
            self._failure_count = 0
            self._circuit_open = False
            self._circuit_open_until = None
            logger.info("ProfinetDriver %s inizializzato.", self.name)
        except Exception as e:
            logger.error("Errore in ProfinetDriver %s: %s", self.name, e)
            raise e

    async def _send_read(self):
        await asyncio.to_thread(self.sock.sendto, b'PROFINET_READ', (self.ip, self.port))
        await asyncio.sleep(self.timeout if self.timeout is not None else config_manager.get("comms_timeout", 1.0))
        return b'\x00\x2A'

    async def read(self):
        if self.circuit_breaker_enabled:
            now = asyncio.get_event_loop().time()
            if self._circuit_open and self._circuit_open_until and now < self._circuit_open_until:
                raise Exception(f"Circuit breaker aperto per {self.name}, operazione bloccata.")
            elif self._circuit_open and self._circuit_open_until and now >= self._circuit_open_until:
                self._circuit_open = False
                self._failure_count = 0

        if not self.sock:
            raise Exception("Socket non inizializzato.")
        try:
            data = await self.retry_with_backoff(self._send_read)
            self.update_heartbeat()
            self._failure_count = 0
            value = int.from_bytes(data, byteorder='big')
            logger.info("ProfinetDriver %s lettura: %s", self.name, value)
            data_pool.update_variable("profinet_value", value)
            return {"profinet_value": value}
        except Exception as e:
            if self.circuit_breaker_enabled:
                self._failure_count += 1
                if self._failure_count >= 3:
                    self._circuit_open = True
                    self._circuit_open_until = asyncio.get_event_loop().time() + self._circuit_open_duration
                    logger.error("Circuit breaker aperto per %s per %d secondi", self.name, self._circuit_open_duration)
            logger.error("Errore in read di ProfinetDriver %s: %s", self.name, e)
            raise e

    async def _send_write(self, data_bytes):
        await asyncio.to_thread(self.sock.sendto, data_bytes, (self.ip, self.port))

    async def write(self, data):
        if self.circuit_breaker_enabled:
            now = asyncio.get_event_loop().time()
            if self._circuit_open and self._circuit_open_until and now < self._circuit_open_until:
                raise Exception(f"Circuit breaker aperto per {self.name}, operazione bloccata.")
            elif self._circuit_open and self._circuit_open_until and now >= self._circuit_open_until:
                self._circuit_open = False
                self._failure_count = 0

        if not self.sock:
            raise Exception("Socket non inizializzato.")
        try:
            data_bytes = str(data).encode('utf-8')
            await self.retry_with_backoff(self._send_write, data_bytes)
            self.update_heartbeat()
            self._failure_count = 0
            logger.info("ProfinetDriver %s scrittura: %s", self.name, data)
            data_pool.update_variable("profinet_value", data)
        except Exception as e:
            if self.circuit_breaker_enabled:
                self._failure_count += 1
                if self._failure_count >= 3:
                    self._circuit_open = True
                    self._circuit_open_until = asyncio.get_event_loop().time() + self._circuit_open_duration
                    logger.error("Circuit breaker aperto per %s per %d secondi", self.name, self._circuit_open_duration)
            logger.error("Errore in write di ProfinetDriver %s: %s", self.name, e)
            raise e

    def health_check(self):
        self.update_heartbeat()
        return True

# ModbusTCPDriver
try:
    from pymodbus.client import AsyncModbusTcpClient  # type: ignore[reportMissingImports]
    PYMODBUS_AVAILABLE = True
except ImportError:
    PYMODBUS_AVAILABLE = False
    from io_manager import BaseIODriver
    logger.error("pymodbus non installato.")

class ModbusTCPDriver(RetryMixin, BaseIODriver):
    def __init__(self, name, host, port=502, unit=1, timeout=None, retries=None, backoff_base=None, circuit_breaker_enabled=False):
        super().__init__(name)
        self.host = host
        self.port = port
        self.unit = unit
        self.timeout = timeout if timeout is not None else config_manager.get("comms_timeout", 1.0)
        self.retries = retries if retries is not None else config_manager.get("comms_retries", 3)
        self.backoff_base = backoff_base if backoff_base is not None else config_manager.get("comms_backoff_base", 0.1)
        self.client = None
        self.circuit_breaker_enabled = circuit_breaker_enabled
        self._failure_count = 0
        self._circuit_open = False
        self._circuit_open_until = None
        self._circuit_open_duration = 10  # seconds

    async def _connect(self):
        self.client = AsyncModbusTcpClient(self.host, port=self.port)
        connection = await self.client.connect()
        if not connection:
            raise Exception("Connessione Modbus fallita.")
        return connection

    async def initialize(self):
        if not PYMODBUS_AVAILABLE:
            raise Exception("pymodbus non disponibile.")
        logger.info("Inizializzazione ModbusTCPDriver %s verso %s:%d", self.name, self.host, self.port)
        try:
            connection = await self.retry_with_backoff(self._connect)
            if connection:
                self.active = True
                self.update_heartbeat()
                self._failure_count = 0
                self._circuit_open = False
                self._circuit_open_until = None
                logger.info("ModbusTCPDriver %s inizializzato.", self.name)
        except Exception as e:
            logger.error("Errore in initialize di ModbusTCPDriver %s: %s", self.name, e)
            raise e

    async def _read_registers(self, address, count):
        return await self.client.read_holding_registers(address, count, unit=self.unit)

    async def read(self, address=0, count=1):
        if self.circuit_breaker_enabled:
            now = asyncio.get_event_loop().time()
            if self._circuit_open and self._circuit_open_until and now < self._circuit_open_until:
                raise Exception(f"Circuit breaker aperto per {self.name}, operazione bloccata.")
            elif self._circuit_open and self._circuit_open_until and now >= self._circuit_open_until:
                self._circuit_open = False
                self._failure_count = 0

        if not self.client:
            raise Exception("Client Modbus non inizializzato.")
        try:
            response = await self.retry_with_backoff(self._read_registers, address, count)
            self.update_heartbeat()
            if response.isError():
                logger.error("Errore in read ModbusTCPDriver %s: %s", self.name, response)
                raise Exception("Errore in read Modbus")
            data = response.registers
            self._failure_count = 0
            logger.info("ModbusTCPDriver %s lettura da address %d: %s", self.name, address, data)
            data_pool.update_variable("modbus_value", data)
            return data
        except Exception as e:
            if self.circuit_breaker_enabled:
                self._failure_count += 1
                if self._failure_count >= 3:
                    self._circuit_open = True
                    self._circuit_open_until = asyncio.get_event_loop().time() + self._circuit_open_duration
                    logger.error("Circuit breaker aperto per %s per %d secondi", self.name, self._circuit_open_duration)
            logger.error("Errore in read di ModbusTCPDriver %s: %s", self.name, e)
            raise e

    async def _write_register(self, address, value):
        return await self.client.write_register(address, value, unit=self.unit)

    async def write(self, address, value):
        if self.circuit_breaker_enabled:
            now = asyncio.get_event_loop().time()
            if self._circuit_open and self._circuit_open_until and now < self._circuit_open_until:
                raise Exception(f"Circuit breaker aperto per {self.name}, operazione bloccata.")
            elif self._circuit_open and self._circuit_open_until and now >= self._circuit_open_until:
                self._circuit_open = False
                self._failure_count = 0

        if not self.client:
            raise Exception("Client Modbus non inizializzato.")
        try:
            response = await self.retry_with_backoff(self._write_register, address, value)
            self.update_heartbeat()
            if response.isError():
                logger.error("Errore in write ModbusTCPDriver %s: %s", self.name, response)
                raise Exception("Errore in write Modbus")
            self._failure_count = 0
            logger.info("ModbusTCPDriver %s scrittura: address %d, value %s", self.name, address, value)
            data_pool.update_variable("modbus_value", value)
        except Exception as e:
            if self.circuit_breaker_enabled:
                self._failure_count += 1
                if self._failure_count >= 3:
                    self._circuit_open = True
                    self._circuit_open_until = asyncio.get_event_loop().time() + self._circuit_open_duration
                    logger.error("Circuit breaker aperto per %s per %d secondi", self.name, self._circuit_open_duration)
            logger.error("Errore in write di ModbusTCPDriver %s: %s", self.name, e)
            raise e

    def health_check(self):
        self.update_heartbeat()
        return True