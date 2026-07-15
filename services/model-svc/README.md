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

阶段 2 起，`model-svc` 提供内部 deterministic 生成入口：

```bash
POST /internal/generate
```

当前 provider 不调用真实大模型，也不需要 API Key。它返回稳定的 Markdown、
summary、provider/model 元数据和 token usage，用于验证
agent-svc -> model-svc -> task-svc 的模型调用边界。

Run tests:

```bash
make test-model-svc
```
