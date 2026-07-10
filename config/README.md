# config

项目级配置目录。这里存放可以提交到 GitHub 的非敏感配置、示例配置和提示词模板。

配置分层：

```text
config/app/                 应用级非敏感配置
config/models/              模型 Provider 示例配置，不放真实 API Key
config/prompts/             可版本化的提示词模板
services/*/config/          服务自己的配置读取边界和 settings 代码
infra/docker/.env.example   本地 Docker Compose 环境变量示例
.env.example                根级本地开发环境变量示例
```

安全规则：

- 真实 `.env` 不提交。
- 真实 API Key 不写进 YAML、README、代码或测试样例。
- `model-svc` 是唯一读取模型 Provider Secret 的服务。
- 生产配置文件 `config/app/production.yaml` 不提交，只提交 `production.example.yaml`。
- Kubernetes Secret 只提交 `*.example.yaml`，真实 `secrets.yaml` 不提交。

配置读取建议：

- 普通非敏感配置来自 `config/app/*.yaml`。
- 敏感值来自环境变量或 Secret。
- 服务启动时由 `services/*/config/settings.py` 组合 YAML、环境变量和默认值。
- 前端只读取公开配置，例如 gateway 地址；不读取任何后端 Secret。
