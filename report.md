# Report Version 1.5.0

_Data: 2025-04-26_

## Stato Attuale

La versione **1.5.0** include le seguenti funzionalità implementate:

- **Configurazione**  
  - Validazione completa con `config/schema.json`  
  - Reload TTL configurabile (`reload_ttl_seconds`)  

- **Gestione dinamica**  
  - Timeout per i blocchi logici (`block_timeout_seconds`) con log su timeout  
  - Blacklist moduli falliti  

- **Engine**  
  - Parametrizzazione di `cycle_time` e `timeout` da configurazione  
  - Modalità `--dry-run` per visualizzare la configurazione  

- **I/O Drivers**  
  - Circuit-breaker con backoff parametrico  
  - Test di unità per il circuito-breaker  

- **Persistenza**  
  - `DBManager.purge_history(days)` per gestione storico  
  - `DBManager.health_check()` con creazione indice su `history.timestamp`  
  - Test di health DB e purge  

- **Backup**  
  - Medoto di retention automatica basato su `retention_days`  
  - Metriche Prometheus per success/failure dei backup  

- **Monitoring & Logging**  
  - Esportazione metriche Prometheus (latency, error counter)  
  - OpenTelemetry di base nel `JsonFormatter`  
  - Health endpoint `/health`  

- **API & Documentazione**  
  - Endpoints protetti JWT e refresh/logout  
  - Integrazione **Swagger/OpenAPI** con `flask-smorest`  
  - Test API per `/api/config` e `/health`  

- **DevOps**  
  - CI GitHub Actions (lint, type-check, test, coverage)  
  - Docker image scanning, Helm charts (documentazione migrations)  
  - Changelog e CHANGELOG.md aggiornato  



















## Implementazioni Versione 3.3.0
- Dynamic Loader: isolated reload via subprocess in `dynamic_loader.py` and Prometheus gauges for modules down/up
- Engine: added `Counter('engine_cycles_total')` and `Histogram('engine_subtask_duration_seconds')`; cleanup hooks for DB and sockets on shutdown
- I/O Drivers: enhanced `MockDriver` with latency/error simulation; fixed `BatchIODriver` docs; added `tests/test_io_stress.py` for error scenarios
- Persistence & Audit: columns `old_json`/`new_json` added; API endpoint `GET /api/audit/full/<record_id>` returns full snapshots; added index and improved queries
- Backup & Alerting: Slack webhook with retry logic; email fallback; integration test simulating Slack down and retry in `tests/test_backup_alert_retry.py`
- Monitoring & Logging: Grafana dashboard JSON extended with panels for subtask durations, cycle throughput; added runbook in `docs/runbook.md`
- API & UI: React SPA expanded with Chart.js components, login form, protected routes; E2E Playwright test `tests/e2e/test_full_spa_flow.py`
- DevOps & CI: Docker multi-arch buildx in `release.yml`; added Bandit SAST scan; Helm lint and unittest steps; OWASP ZAP stub in `ci.yml`
