import pytest, asyncio
from app.io_manager import ConfigurableMockDriver, BatchIODriver

@pytest.mark.asyncio
async def test_io_stress_extended():
    driver = ConfigurableMockDriver(latency=0.1, error_rate=0.5)
    batch = BatchIODriver([driver]*3)
    errors = 0
    for _ in range(20):
        try:
            await batch.read_all()
        except:
            errors += 1
    assert errors > 0
