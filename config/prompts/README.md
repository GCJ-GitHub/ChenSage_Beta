# config/prompts

提示词模板目录。Beta1.0 先把模板作为可版本化配置管理，后续如果模板编辑、权限、发布、回滚变复杂，再拆 `prompt-svc`。

目录建议：

```text
content/      内容创作与改写
interview/    模拟面试
research/     信息搜集
arxiv/        arXiv 日报
generic/      尚未接入专属模板的安全兜底
```

模板规则：

- 每个模板声明 `id`、`task_type`、`version`、`variables` 和 `template`。
- 模板内只放通用提示词，不放用户隐私、API Key 或真实任务数据。
- 任务运行时由 `agent-svc` 注入 task input、memory snapshot 和 tool output。
- 修改模板时递增 version，便于历史任务复现。
- 当前阶段模板由 `agent-svc` 的 `/prompt-templates` API 读取；如果模板 id 未命中，
  系统会先按 task_type 选择同类默认模板，再回落到 `generic.default`。

当前已提供：

- `content.default`：通用内容创作。
- `content.standup_script`：脱口秀 / 单口喜剧稿。
- `research.default`：通用信息搜集。
- `interview.default`：通用模拟面试。
- `arxiv.daily`：arXiv 日报。
- `conversation.default`：对话式任务理解。
- `evaluation.default`：内容评价与学习反馈。
- `generic.default`：通用安全兜底。
