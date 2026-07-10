# task-svc migrations

Alembic migrations owned by `task-svc`.

Expected tables:

- `tasks`
- `task_events`
- `task_results`
- `approval_gates`

Other services must not write these tables directly.
