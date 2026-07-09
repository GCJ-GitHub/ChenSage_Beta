# infra/docker

本地 Docker Compose 和依赖配置。

第一阶段包含：

- PostgreSQL + pgvector。
- RabbitMQ。
- Redis。
- MinIO。
- gateway。
- agent-svc。
- model-svc。
- task-svc。
- agent-worker。
- tool-registry。
- living-memory-svc。
- eval-svc。
- policy-svc。

Compose 用于本地端到端验证，不代表所有能力必须一开始都独立成熟。
