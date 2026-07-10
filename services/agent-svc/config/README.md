# services/agent-svc/config

Agent 运行配置边界。

配置来源：

- Agent loop 默认预算：`config/app/*.yaml`。
- 提示词模板：`config/prompts/`。
- 模型调用策略：通过 `model-svc` 获取，不直接读取模型 Secret。
- 工具权限：通过 `tool-registry` 和 `policy-svc` 判断。

建议后续实现：

```text
settings.py
prompt_loader.py
agent_registry.py
```
