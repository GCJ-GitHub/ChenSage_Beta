# workers/agent-worker

RabbitMQ / Celery 长任务执行器。

职责：

- 消费 task-svc 投递的长任务。
- 调用 agent-svc 执行 Agent loop。
- 通过 task-svc 推进任务状态和写入 task event。
- 处理重试、超时、取消和失败恢复。

边界：

- 不直接写 task 数据表。
- 不绕过 agent-svc 执行 Agent 业务逻辑。
- 不直接读取模型 Key。

阶段 0 启动方式：

```bash
make run-agent-worker
```

Phase 2 routes RabbitMQ messages to `agent-svc` through `POST /internal/execute`
before writing results back to task-svc. Executor selection is owned by
agent-svc; the worker only consumes queue messages and advances task state.

Run worker tests:

```bash
make test-agent-worker
```
