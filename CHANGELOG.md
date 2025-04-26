# Changelog

## [1.2.0] - 2025-04-26
- Added Swagger/OpenAPI documentation via flask-smorest integration
- Added HTTP health-check endpoint `/health` in `api_server.py`
- Implemented history retention policy `purge_history(days)` in `db_manager.py`
- Added API and health endpoint tests in `tests/test_api.py`
- Integrated basic OpenTelemetry instrumentation in `logging_config.py`

## [1.3.0] - 2025-04-26
- Implemented backup retention policy in BackupManager
- Added DBManager.purge_history test and BackupManager retention tests

## [1.4.0] - 2025-04-26
- Added reload TTL and metric in config_manager.py
- Implemented DBManager.health_check and index on history.timestamp
- Added timeout wrapper in dynamic_loader.py for logic blocks
- Created docs/migrations.txt with migration guidance
- Added tests for dynamic_loader, config_manager reload, and DB health
