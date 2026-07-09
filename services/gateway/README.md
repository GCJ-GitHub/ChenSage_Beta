# services/gateway

统一 API 入口服务。

职责：

- 认证和用户上下文注入。
- API 路由和基础限流。
- request_id / trace_id 注入。
- SSE / WebSocket 代理。
- 将前端请求转发给 task-svc、agent-svc、file-svc 等内部服务。

边界：

- 不保存业务数据。
- 不直接调用模型 Provider。
- 不绕过 task-svc 修改任务状态。
