# infra/docker

本地 Docker Compose 和依赖配置。

阶段 0 只启动基础依赖：

- PostgreSQL + pgvector。
- RabbitMQ。
- Redis。
- MinIO。

业务服务在阶段 0 先通过本机 Python 进程启动，避免每改一次代码都重建镜像。后续进入端到端验证时，再把 gateway、task-svc、model-svc、agent-svc 和 agent-worker 加入 Compose。

## 使用方式

在项目根目录执行：

```bash
make setup-env
make infra-up
make infra-ps
```

服务地址：

| 服务 | 地址 |
|------|------|
| PostgreSQL | `localhost:5432` |
| RabbitMQ | `localhost:5672` |
| RabbitMQ Management | `http://localhost:15672` |
| Redis | `localhost:6379` |
| MinIO API | `http://localhost:9000` |
| MinIO Console | `http://localhost:9001` |

MinIO 会自动创建 `MINIO_BUCKET` 指定的 bucket，默认是 `chensage-artifacts`。

停止基础依赖：

```bash
make infra-down
```
