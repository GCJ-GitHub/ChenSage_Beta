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

阶段 2 起，`model-svc` 提供默认 Provider 配置、连通性测试和内部生成入口：

```bash
GET  /model-providers/default
PUT  /model-providers/default
POST /model-providers/default/test
POST /internal/generate
```

默认 `MODEL_PROVIDER_TYPE=deterministic`，不调用真实大模型，也不需要 API Key。
它返回稳定的 Markdown、summary、provider/model 元数据和 token usage，用于验证
agent-svc -> model-svc -> task-svc 的模型调用边界。

阶段 6 起，deterministic provider 会对 `content-agent` 的内容创作、改写和脱口秀稿
返回更接近真实产品输出的 Markdown 初稿 / 改写稿，同时保留 Prompt Snapshot，方便
在没有真实模型 Key 的本地环境里验证内容主链路。

切换为 `openai_compatible` 后，`model-svc` 会通过
`<base_url>/chat/completions` 调用真实 Provider。API Key 可以来自环境变量或
运行时设置接口；响应只返回 `api_key_configured` 和脱敏后的 `api_key_preview`，
不会回显完整 Key。

当前运行时设置是进程内存储，服务重启后回到环境变量配置。后续可在这个边界下替换为
数据库 + 加密存储，而不改变 `agent-svc` 或 worker 的调用方式。

Run tests:

```bash
make test-model-svc
```
