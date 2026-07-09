# ChenSage AgentOS

> 个人 AI 任务中枢 + 多 Agent 编排 + 活记忆 + 工具协议 + 可靠任务执行。

ChenSage AgentOS 是 ChenSage_Beta 的新版架构方向。项目定位从原来的“本地云原生微服务平台”升级为“Agent-native 个人 AI 操作系统”。

它不再只是内容生成、信息搜集、面试训练、arXiv 日报等功能集合，而是一个面向个人知识工作者的 Agent 平台：

```text
用户提出目标
  -> 系统理解意图
  -> planner-agent 拆解任务
  -> 多个 subagent 协作
  -> 调用工具和模型
  -> 读写活记忆
  -> 形成结果
  -> 自动评估和复盘
  -> 把经验沉淀回记忆
```

原有的 PostgreSQL、RabbitMQ、Redis、MinIO、Docker Compose、OpenTelemetry 等工程能力不会丢，它们会成为 AgentOS 的可靠底座。

## 核心定位

ChenSage AgentOS 面向个人知识工作者，目标是把 AI 从“单次问答工具”升级为“能规划、执行、协作、记忆和复盘的个人任务系统”。

Beta 阶段优先解决五件事：

- 多 Agent 协作：让 planner、research、content、critic、memory、file 等 agent 各司其职。
- 可靠任务执行：长任务进入队列，支持状态管理、重试、取消、审批和失败恢复。
- 活记忆：系统能持续沉淀用户偏好、任务经验、工作流程和复盘结论。
- 工具协议：把搜索、arXiv、文件解析、导出、记忆检索、模型调用等能力统一成可治理工具。
- Agent 可观测性：看清每一步 plan、act、observe、evaluate、revise 的过程、成本和质量。

Beta1.0 的范围有意偏向“首次平台底座验证”。它不是只做一个窄功能 demo，而是用一条端到端 Agent 任务链路验证前端、网关、任务队列、Agent 运行、模型调用、工具、记忆、评估和观测这些核心边界是否能协同工作。实现时可以先把部分能力放在同一个代码服务或模块内，但目录、接口和数据所有权要按平台边界设计。

## Beta1.0 产品功能范围

Beta1.0 不是另起一个脱离原 MVP 的平台项目，而是把 MVP 已验证过的个人知识工作功能迁移到 AgentOS 架构中，让它们具备统一任务、队列、模型配置、模板、工具、文件、导出和可观测能力。

| 产品功能 | Beta1.0 目标 |
|------|------|
| 内容创作 | 支持论文、专利、小说、剧本、歌词、小红书、知乎、公众号等内容生成与改写 |
| 模拟面试 | 基于简历和岗位描述生成简历分析、面试问题、回答评价和复盘报告 |
| 信息搜集 | 支持单 URL / PDF / JSON / RSS、批量多任务、站内信息发现与汇总报告 |
| arXiv 日报 | 支持研究方向管理、关键词 / 分类配置、按日期和篇数拉取论文、收藏论文、按范围生成日报 |
| 模型设置 | 支持 OpenAI-compatible API 配置、默认模型、连通性测试 |
| 提示词模板 | 支持按任务类型维护模板，并在信息搜集、arXiv 日报、内容创作等功能中复用 |
| 文件管理 | 支持上传并解析 PDF、DOCX、TXT、MD |
| 历史任务与导出 | 支持统一查看任务、重试、导出 Markdown |

这些功能在 Beta 架构中的归属：

| MVP 功能 | AgentOS 模块 |
|------|------|
| 内容创作 / 改写 | `content-agent` + prompt templates + `model-svc` + Markdown 导出 |
| 模拟面试 | `interview-agent` + `file-svc` 简历解析 + `eval-svc` 回答评价 |
| 信息搜集 | `research-agent` + URL / PDF / JSON / RSS 工具 + 批量 task |
| arXiv 日报 | `research-agent` 的 arXiv workflow，后续可拆 `arxiv-agent` |
| 模型设置 | `model-svc` |
| 提示词模板 | `agent-svc` 内 prompt registry，后续可拆 `prompt-svc` |
| 文件管理 | `file-svc` + `tool-registry` 文件解析工具 |
| 历史任务与导出 | `task-svc` + export tools + `file-svc` |

## 目标架构

```text
Browser / Next.js
  |
  v
gateway
  |
  v
agent-orchestrator
  |
  +--> planner-agent
  +--> research-agent
  +--> content-agent
  +--> interview-agent
  +--> critic-agent
  +--> memory-agent
  +--> file-agent

agent-orchestrator
  |
  +--> agent-harness
  +--> loop-engine
  +--> context-engine
  +--> tool-registry
  +--> living-memory-svc
  +--> eval-svc
  +--> policy-svc
  +--> task-svc

task-svc -> RabbitMQ -> worker
worker -> model-svc
worker -> tool-registry
file-svc -> MinIO

services -> PostgreSQL + pgvector
services -> Redis

observability:
OpenTelemetry + Prometheus + Grafana + Loki
```

## 新概念速览

### Agent-native

Agent-native 表示系统不是把 AI 当作某个接口的附属能力，而是以 Agent 的规划、执行、观察、评估、修正为核心运行模型。页面、API、任务队列和数据库都围绕 Agent 工作流设计。

### Agent Orchestrator

`agent-orchestrator` 是新版核心服务。它负责任务理解、Agent 调度、执行计划管理、Agent 间协作和任务状态同步。它不直接吞掉所有业务逻辑，而是决定“谁来做、按什么顺序做、失败后怎么办”。

### Agent Harness

`agent-harness` 是 Agent 的运行套件。每个 Agent 都挂在统一 harness 上，避免重复实现工具调用、记忆访问、模型路由、重试、日志、权限和输出校验。

### Loop Engine

`loop-engine` 负责 Agent 循环执行机制：

```text
plan -> act -> observe -> evaluate -> revise -> stop
```

它必须内置 `max_steps`、`max_tokens`、`max_cost`、`max_duration`、`stop_condition`、`human_approval_required` 等限制，防止无限循环和成本失控。

### Context Engine

`context-engine` 负责上下文工程。它决定 Agent 每一步能看到什么、不能看到什么、哪些信息要压缩、哪些信息必须带来源。

### Living Memory

`living-memory-svc` 是活记忆系统。它不是普通聊天历史，而是会持续更新、合并、过期、冲突检测，并接受用户治理的动态记忆系统。

记忆类型包括：

- working memory：当前任务临时记忆。
- episodic memory：任务经历和事件。
- semantic memory：稳定知识和用户偏好。
- procedural memory：做事方法和流程经验。
- reflective memory：Agent 复盘总结。
- governed memory：用户确认、冻结、删除的记忆。

### Tool Registry

`tool-registry` 是工具注册中心，统一管理内部工具和 MCP-style 工具。每个工具都要有权限、输入 schema、输出 schema、审计日志和调用成本。

### Eval Service

`eval-svc` 负责评估 Agent 输出质量，例如事实性、格式、引用来源、完整性、风格一致性，以及是否满足用户目标。

### Policy Service

`policy-svc` 负责权限、安全、审批和成本控制，例如敏感工具调用前审批、外部请求白名单、文件访问权限、模型预算限制、记忆写入规则和高风险操作拦截。

## 第一阶段 Agent

第一阶段建议实现这些 Agent：

| Agent | 职责 |
|------|------|
| `planner-agent` | 任务拆解、步骤规划、选择其他 Agent |
| `research-agent` | 网页搜索、arXiv、资料筛选、信息归纳 |
| `content-agent` | 文章、短视频脚本、小红书、知乎、歌词、报告创作 |
| `interview-agent` | 简历分析、问题生成、回答评价、复盘建议 |
| `critic-agent` | 审稿、挑错、事实核查、质量评估 |
| `memory-agent` | 整理任务经验，决定哪些内容进入活记忆 |
| `file-agent` | 文件解析、摘要、导出、格式转换 |

第一版不建议每个 Agent 都独立部署成微服务。更稳的方式是先放在同一个 `agent-svc` 中：

```text
agent-svc
  agents/
    planner_agent.py
    research_agent.py
    content_agent.py
    interview_agent.py
    critic_agent.py
    memory_agent.py
    file_agent.py
```

等边界稳定后，再把重型 Agent 独立拆服务。

## Beta1.0 首次平台验证范围

第一版要优先跑通这条链路：

```text
Browser / Next.js
  -> gateway
  -> task-svc 创建 task
  -> RabbitMQ
  -> worker
  -> agent-svc 内部 orchestrator + harness + loop-engine
  -> model-svc
  -> tool-registry
  -> living-memory-svc
  -> eval-svc
  -> task-svc 持久化状态和结果
  -> 前端展示进度、审批和最终输出
```

关键边界：

- `task-svc` 是任务状态唯一事实源，负责 queued、running、waiting_approval、succeeded、failed、cancelled、expired 等状态。
- `agent-svc` 负责 Agent 编排和循环决策，不直接成为任务状态数据库。
- `model-svc` 是唯一模型调用入口，模型调用不作为普通工具暴露给 Agent。
- `tool-registry` 负责非模型工具的注册、权限、schema 和审计。
- 活记忆第一版采用“自动临时记忆 + 用户确认长期记忆”的策略，避免错误记忆静默长期生效。
- PostgreSQL 采用单实例多 schema，但每个服务独立账号、独立 migration、禁止跨 schema join。

## 技术选型

| 层级 | 选型 |
|------|------|
| 主语言 | Python 3.12 / 3.13 |
| 后端 | FastAPI, SQLAlchemy 2.x, Alembic |
| 任务队列 | RabbitMQ + Celery |
| 缓存和短状态 | Redis |
| 数据库 | PostgreSQL + pgvector |
| 对象存储 | MinIO |
| Agent 层 | Python agent runtime, LangGraph 可选 |
| 工具协议 | MCP-style tool interface |
| 模型抽象 | OpenAI / Anthropic / Gemini 等 Provider 抽象 |
| 前端 | Next.js, React, TypeScript |
| 可观测性 | OpenTelemetry, Prometheus, Grafana, Loki |
| 本地开发 | Docker Compose |
| 部署验证 | kind, Kubernetes, Helm / Kustomize |

## 项目目录

```text
apps/
  web/                         Next.js 前端应用
services/
  gateway/                     统一 API 入口、认证上下文、SSE / WebSocket 代理
  agent-svc/                   Agent 编排、harness、loop-engine、context-engine
  task-svc/                    任务状态唯一事实源
  model-svc/                   模型 Provider、Key、路由、限流和成本统计
  tool-registry/               非模型工具注册、schema、权限和审计
  living-memory-svc/           活记忆写入、检索、确认、冲突和过期
  eval-svc/                    输出质量评估和 eval report
  policy-svc/                  权限、审批、预算和安全策略
  file-svc/                    文件元数据、解析任务和 MinIO 对象索引
workers/
  agent-worker/                RabbitMQ / Celery 长任务执行器
packages/
  shared/                      DTO、client、事件契约、错误码和通用工具
infra/
  docker/                      Docker Compose、本地依赖和开发配置
  kubernetes/                  kind / K8s / Helm / Kustomize 验证配置
scripts/                       本地开发、校验和运维脚本
tests/                         跨服务契约、集成和端到端测试
文档/                          架构、技术决策和项目说明
```

## 推荐落地路线

1. 架构文档重写：把项目定位改为 Agent-native 个人 AI 操作系统。
2. 基础底座：落 PostgreSQL、pgvector、RabbitMQ、Redis、MinIO、Docker Compose。
3. Agent MVP：实现 `agent-svc` 内部的 `agent-orchestrator`、`agent-harness`、`loop-engine`，以及 `model-svc`、`task-svc`、`worker`。
4. 跑通第一条链路：用户输入目标 -> planner -> research-agent -> content-agent -> critic-agent -> 输出结果。
5. 活记忆：实现 `living-memory-svc`，支持写入、检索、用户确认、冲突检测、过期降权。
6. 工具系统：实现 `tool-registry`，把 arXiv、网页搜索、文件解析、导出都工具化。
7. 观测和评估：补齐 agent trace、tool call trace、token/cost、loop step、eval report。
8. Kubernetes：Compose 稳定后，再迁移到 kind / K8s 验证部署能力。

## 文档索引

建议按以下顺序阅读：

1. `文档/架构设计与技术选型.md`
2. `文档/功能开发顺序.md`
3. `文档/技术决策Q&A.md`
