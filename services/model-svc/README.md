# services/model-svc

唯一模型调用入口。

职责：

- Provider 配置和 API Key 管理。
- 模型路由、限流、重试和超时控制。
- token / cost 统计。
- 模型调用 trace 和审计。

边界：

- Agent 不直接持有模型 Key。
- 模型调用不注册成普通 tool-registry 工具。
- 日志和 trace 不能记录完整 Secret、Cookie 或 Authorization header。
