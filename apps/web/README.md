# apps/web

Next.js + React + TypeScript 前端应用。

当前阶段先提供一个不依赖构建工具的静态原型：

```text
index.html
styles.css
app.js
```

可以直接用浏览器打开 `apps/web/index.html` 预览 AgentOS 工作台。后续进入正式前端开发时，再把这个静态原型迁移到 Next.js 页面和组件。

职责：

- 展示 Agent 任务入口、任务进度、审批卡点和最终结果。
- 通过 gateway 调用后端 API。
- 使用 SSE / WebSocket 展示 task event、loop step、tool call 和 eval report。
- 不直接访问内部服务、数据库、对象存储或模型 Provider。

当前静态原型还没有 gateway 代理层，所以临时通过
`window.CHENSAGE_TASK_API_URL`、`window.CHENSAGE_MODEL_API_URL` 和
`window.CHENSAGE_AGENT_API_URL` 直连 `task-svc`、`model-svc`、`agent-svc`，
用于验证任务中心、模型设置页和提示词模板选择。迁移到正式 Next.js 后，这些调用应
收敛到 gateway。

第一版页面建议：

- 任务创建页。
- 任务详情页。
- 模型设置页。
- 提示词模板选择。
- 审批队列页。
- 记忆治理页。
- Agent trace / eval report 查看页。
