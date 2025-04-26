import pytest
import asyncio
from app.io_manager import BatchIODriver

class DummyDriver:
    async def read(self):
        return 1
    async def write(self, data):
        return True
    async def heartbeat(self):
        return True

@pytest.mark.asyncio
async def test_batch_io_driver():
    drivers = [DummyDriver(), DummyDriver()]
    batch = BatchIODriver(drivers)
    reads = await batch.read_all()
    assert reads == [1, 1]
    writes = await batch.write_all([10, 20])
    assert writes is None  # no return
    hb = await batch.heartbeat()
    assert hb is None
