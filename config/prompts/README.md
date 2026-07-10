# config/prompts

提示词模板目录。Beta1.0 先把模板作为可版本化配置管理，后续如果模板编辑、权限、发布、回滚变复杂，再拆 `prompt-svc`。

目录建议：

```text
content/      内容创作与改写
interview/    模拟面试
research/     信息搜集
arxiv/        arXiv 日报
```

模板规则：

- 每个模板声明 `id`、`task_type`、`version`、`variables` 和 `template`。
- 模板内只放通用提示词，不放用户隐私、API Key 或真实任务数据。
- 任务运行时由 `agent-svc` 注入 task input、memory snapshot 和 tool output。
- 修改模板时递增 version，便于历史任务复现。
