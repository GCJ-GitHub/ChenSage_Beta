# apps/web

Next.js + React + TypeScript 前端应用。

职责：

- 展示 Agent 任务入口、任务进度、审批卡点和最终结果。
- 通过 gateway 调用后端 API。
- 使用 SSE / WebSocket 展示 task event、loop step、tool call 和 eval report。
- 不直接访问内部服务、数据库、对象存储或模型 Provider。

第一版页面建议：

- 任务创建页。
- 任务详情页。
- 审批队列页。
- 记忆治理页。
- Agent trace / eval report 查看页。
