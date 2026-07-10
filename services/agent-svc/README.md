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
