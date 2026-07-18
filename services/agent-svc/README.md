# services/agent-svc

Agent 编排服务。Beta1.0 中 `agent-orchestrator`、`agent-harness`、`loop-engine`、`context-engine` 可以先在这个服务内实现。

建议目录：

```text
agents/
orchestrator/
harness/
loop_engine/
context_engine/
conversation/
prompt_optimizer/
schemas/
```

职责：

- 理解用户目标并创建执行计划。
- 支持 conversation-agent 的对话式任务理解、澄清问题和任务路由。
- 选择 planner、research、content、critic、memory、file 等 Agent。
- 运行 Agent loop：plan、act、observe、evaluate、revise、stop。
- 通过 model-svc 调用模型。
- 通过 tool-registry 调用非模型工具。
- 通过 knowledge-base-svc 检索历史内容、资料来源、高质量案例和评价经验。
- 通过 living-memory-svc 检索或提交记忆写入建议。
- 根据 eval-svc 的多次评价报告提出 prompt template 优化建议。

边界：

- 不作为 task 状态唯一事实源。
- 不直接读取模型 Key。
- 不直接绕过 tool-registry 执行外部工具。
- 不静默修改提示词模板；优化建议需要用户确认或审核。

阶段 2 起，`agent-svc` 提供 worker 内部调用入口：

```bash
POST /internal/execute
```

当前实现是 deterministic orchestrator skeleton：根据 `task_type` 选择 content、
research、arXiv、interview、file 或 generic executor，通过 Agent Harness 和
Loop Engine 生成 `plan -> act -> observe -> finalize` trace，并经由 model-svc
的 deterministic provider 生成内容。后续真实模型、工具、记忆和 eval 会逐步替换
这些 executor 内部实现。

阶段 3 起，`agent-svc` 开始加载 `config/prompts/**/*.yaml` 作为提示词模板
registry：

```bash
GET /prompt-templates
GET /prompt-templates?task_type=content
GET /prompt-templates/{template_id}
```

`PromptBuilder` 会按 `task.template` 解析模板 id，渲染 `task.input`、目标、
任务类型和输出格式后再交给 `model-svc`。如果某个任务类型暂时没有专属模板，会回落到
`generic.default`，保证未知任务和后续功能原型不会因为模板缺失而中断。

阶段 4 起，`agent-svc` 内置最小 `context-engine`：

- 执行前按 `task_type` 归一化为 `content`、`research`、`arxiv`、`interview` 或 `file`。
- 通过 `knowledge-base-svc` 的 `/knowledge-items/search` 检索 active 知识条目。
- 将知识标题、摘要、片段和来源注入 Prompt。
- 将检索事件写入 trace，并把来源摘要写入 result artifacts。
- 如果 `knowledge-base-svc` 暂不可用，任务继续执行，trace 记录 `context.knowledge_unavailable`。

阶段 5 起，`agent-svc` 提供对话式任务理解入口：

```bash
POST /conversation/interpret
```

当前实现会根据用户消息识别 `content_generation` 和 `content_rewrite`，
选择内容创作或脱口秀稿模板，预取匹配知识库来源，返回澄清问题、模板选择、
Agent 选择和可直接提交到 `task-svc` 的任务草稿。

阶段 6 起，`content-agent` 的执行链路开始区分内容创作、内容改写和脱口秀稿：

- 内容任务会归一化 `content_type`、`audience`、`tone`、`length`、`generated_content` 和 `rewrite_instruction`。
- `content_generation` 默认使用 `content.default`，`content_rewrite` 默认使用 `content.rewrite`，脱口秀稿优先使用 `content.standup_script`。
- 执行结果会写入 `content_task_spec` artifact，保留本次内容类型、受众、语气、长度和改写原文预览。

Run tests:

```bash
make test-agent-svc
```
