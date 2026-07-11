# services/task-svc

任务状态唯一事实源。

职责：

- 管理 task、task_event、task_result、approval_gate。
- 负责 queued、running、waiting_approval、succeeded、failed、cancelled、expired 状态机。
- 投递 RabbitMQ 长任务。
- 接收 worker、agent-svc、gateway 的状态推进请求。
- 提供任务查询、取消、审批、结果索引 API。

当前阶段使用 PostgreSQL 持久化任务状态、事件和结果：

```bash
python -m alembic -c services/task-svc/alembic.ini upgrade head
```

默认 schema 是 `task_svc`，可通过 `TASK_DATABASE_SCHEMA` 覆盖。

边界：

- 不处理 Agent 专业业务逻辑。
- 不拼 Prompt。
- 不直接调用模型或外部工具。
