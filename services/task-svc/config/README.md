# services/task-svc/config

任务服务配置边界。

配置来源：

- task 状态机、超时、重试：`config/app/*.yaml`。
- RabbitMQ 连接：环境变量。
- 数据库连接：环境变量。

原则：

- `task-svc` 是 task、task_event、task_result 的唯一写入入口。
- 其他服务通过 API 或事件推进状态。
- 配置中可以定义默认超时和重试次数，但具体任务可以按 task_type 覆盖。
