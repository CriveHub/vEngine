import pytest
import asyncio
from app.io_manager import BatchIODriver, BaseIODriver

class MockDriver(BaseIODriver):
    async def read(self): return 'ok'
    async def write(self, data): return True
    async def heartbeat(self): return True

@pytest.mark.asyncio
async def test_io_integration():
    drivers = [MockDriver(), MockDriver()]
    batch = BatchIODriver(drivers)
    reads = await batch.read_all()
    assert reads == ['ok', 'ok']
