# model-svc migrations

Alembic migrations owned by `model-svc`.

Expected tables:

- `model_providers`
- `model_configs`
- `model_call_logs`
- `model_budget_events`

Provider secrets should be encrypted or stored in Secret Manager, not committed to Git.
