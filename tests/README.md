# tests

跨服务测试目录。

建议分层：

- contract：OpenAPI、事件契约和 tool schema 测试。
- integration：PostgreSQL、RabbitMQ、Redis、MinIO 集成测试。
- e2e：从前端任务创建到最终输出的端到端测试。
- eval：Agent 输出和 eval report 的回归样例。
