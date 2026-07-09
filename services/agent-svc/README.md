# services/agent-svc

Agent 编排服务。Beta1.0 中 `agent-orchestrator`、`agent-harness`、`loop-engine`、`context-engine` 可以先在这个服务内实现。

建议目录：

```text
agents/
orchestrator/
harness/
loop_engine/
context_engine/
schemas/
```

职责：

- 理解用户目标并创建执行计划。
- 选择 planner、research、content、critic、memory、file 等 Agent。
- 运行 Agent loop：plan、act、observe、evaluate、revise、stop。
- 通过 model-svc 调用模型。
- 通过 tool-registry 调用非模型工具。
- 通过 living-memory-svc 检索或提交记忆写入建议。

边界：

- 不作为 task 状态唯一事实源。
- 不直接读取模型 Key。
- 不直接绕过 tool-registry 执行外部工具。
