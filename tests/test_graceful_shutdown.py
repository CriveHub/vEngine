import pytest
import asyncio
from app.run_async_engine import main
@pytest.mark.asyncio
async def test_graceful_shutdown(monkeypatch):
    # simulate loop and cancellation
    loop = asyncio.get_event_loop()
    async def dummy():
        await asyncio.sleep(1)
    task = loop.create_task(dummy())
    main_args = ['--dry-run']
    # Should exit cleanly
    main()
    assert task.cancelled() or task.done()
