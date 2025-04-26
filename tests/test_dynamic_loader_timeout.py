import pytest
import asyncio
from app.dynamic_loader import DynamicLoader
from app.config_manager import ConfigManager

class SlowBlock:
    async def execute(self, context):
        await asyncio.sleep(0.1)
        return 'done'

@pytest.mark.asyncio
async def test_block_timeout(monkeypatch):
    cfg = ConfigManager(env='test')
    cfg.config['loader'] = {'block_timeout_seconds': 0.01}
    loader = DynamicLoader()
    loader.logic_blocks = {'slow': SlowBlock()}
    with pytest.raises(asyncio.TimeoutError):
        await loader.run()  # or execute_all depending on implementation
