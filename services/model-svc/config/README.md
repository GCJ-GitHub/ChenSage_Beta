# services/model-svc/config

`model-svc` 是唯一读取模型 Provider Secret 的服务。

配置来源：

- 非敏感 Provider 结构：`config/models/providers.example.yaml`。
- 本地 Secret：根目录 `.env`。
- 生产 Secret：Kubernetes Secret 或外部 Secret Manager。

必须遵守：

- 不把真实 API Key 写进 Git。
- 日志和 trace 不输出完整 API Key。
- 其他服务不能直接读取模型 Secret，只能通过 `model-svc` API 调用模型。
- 前端模型设置页提交配置后，由 `model-svc` 负责校验、加密保存和连通性测试。
