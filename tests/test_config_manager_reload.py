import time
from app.config_manager import ConfigManager

def test_reload_ttl(tmp_path):
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text('{"key": 1}')
    cm = ConfigManager(env='test', config_file=str(cfg_file))
    cm.config_file = str(cfg_file)
    cm.config = {"key": 1}
    cm.last_loaded = time.time()
    cfg_file.write_text('{"key": 2}')
    cm.schema = {'config': {'reload_ttl_seconds': 1}}
    conf = cm.load_config()
    assert conf['key'] == 1
