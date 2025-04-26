import pytest
from app.engine import FastAsyncEngine

@pytest.mark.asyncio
async def test_engine_instantiation():
    engine = FastAsyncEngine(cycle_time=0.1)
    assert engine.cycle_time == 0.1

@pytest.mark.asyncio
async def test_engine_runs_one_cycle(monkeypatch):
    # Monkeypatch dynamic loader to have one dummy block
    class DummyBlock:
        async def execute(self, context):
            return "ok"
    from app.dynamic_loader import DynamicLoader
    loader = DynamicLoader()
    loader.logic_blocks = {'dummy': DummyBlock()}
    engine = FastAsyncEngine(cycle_time=0.01)
    engine.loader = loader
    # Run one iteration and then stop
    import asyncio
    task = asyncio.create_task(engine.run())
    await asyncio.sleep(0.05)
    engine.stop()
    await task
    # If no exceptions, test passes
