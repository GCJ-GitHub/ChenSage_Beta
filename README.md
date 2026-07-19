# ChenSage AgentOS

> 个人 AI 任务中枢 + 多 Agent 编排 + 活记忆 + 工具协议 + 可靠任务执行。

ChenSage AgentOS 是 ChenSage_Beta 的新版架构方向。项目定位从原来的“本地云原生微服务平台”升级为“Agent-native 个人 AI 操作系统”。

它不再只是内容生成、信息搜集、面试训练、arXiv 日报等功能集合，而是一个面向个人知识工作者的 Agent 平台和对话式内容生产中枢：

```text
用户提出目标
  -> 系统理解意图
  -> planner-agent 拆解任务
  -> 多个 subagent 协作
  -> 调用工具和模型
  -> 读写活记忆
  -> 形成结果
  -> 自动评估、解释理由和给出修改建议
  -> 把用户反馈、评价理由和生产经验沉淀回知识库 / 活记忆 / 提示词模板
```

原有的 PostgreSQL、RabbitMQ、Redis、MinIO、Docker Compose、OpenTelemetry 等工程能力不会丢，它们会成为 AgentOS 的可靠底座。

## 本地开发快速开始

阶段 0 先保证基础依赖和服务边界能跑通：

```bash
make setup-env
make setup-python
make infra-up
make migrate-task-svc
make migrate-knowledge-base-svc
make test-task-svc
make test-model-svc
make test-agent-svc
make test-knowledge-base-svc
make test-agent-worker
make check-stage0
make compile-services
```

如果本机没有 `make`，Windows PowerShell 可直接执行：

```powershell
Copy-Item .env.example .env -ErrorAction SilentlyContinue
Copy-Item infra/docker/.env.example infra/docker/.env -ErrorAction SilentlyContinue
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
docker compose --env-file infra/docker/.env -f infra/docker/docker-compose.yml up -d
.\.venv\Scripts\python.exe -m alembic -c services/task-svc/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m alembic -c services/knowledge-base-svc/alembic.ini upgrade head
.\.venv\Scripts\python.exe -m pytest services/task-svc/tests
.\.venv\Scripts\python.exe -m pytest services/model-svc/tests
.\.venv\Scripts\python.exe -m pytest services/agent-svc/tests
.\.venv\Scripts\python.exe -m pytest services/knowledge-base-svc/tests
.\.venv\Scripts\python.exe -m pytest workers/agent-worker/tests
.\.venv\Scripts\python.exe scripts/check_stage0.py
.\.venv\Scripts\python.exe -m compileall services workers packages scripts
```

Stage 1-7 local task loop:

```bash
make dev-stage1
```

This starts Docker Compose dependencies, runs task-svc and knowledge-base-svc migrations, then starts
task-svc on `http://127.0.0.1:8011`, model-svc on `http://127.0.0.1:8012`,
agent-svc on `http://127.0.0.1:8013`, knowledge-base-svc on
`http://127.0.0.1:8014`, eval-svc on `http://127.0.0.1:8015`, and the
`agent-worker` consumer.

常用本地服务入口：

| 命令 | 说明 |
|------|------|
| `make run-gateway` | 启动统一 API 入口，默认 `http://localhost:8000` |
| `make run-task-svc` | 启动任务服务，默认 `http://localhost:8011` |
| `make run-model-svc` | 启动模型配置服务，默认 `http://localhost:8012` |
| `make run-agent-svc` | 启动 Agent 编排服务，默认 `http://localhost:8013` |
| `make run-knowledge-base-svc` | 启动知识库服务，默认 `http://localhost:8014` |
| `make run-eval-svc` | 启动评价服务，默认 `http://localhost:8015` |
| `make run-agent-worker` | 启动阶段 0 worker 占位入口 |

真实 `.env` 不进入 Git。大模型 API Key 只通过 `model-svc` 的配置边界读取。
默认 `MODEL_PROVIDER_TYPE=deterministic`，可以离线跑通阶段 2 主链路；切换
OpenAI-compatible Provider 时，只在 `.env` 或模型设置页交给 `model-svc`，
接口响应只返回脱敏后的 Key 预览。

## 核心定位

ChenSage AgentOS 面向个人知识工作者，目标是把 AI 从“单次问答工具”升级为“能规划、执行、协作、记忆和复盘的个人任务系统”。

Beta 阶段优先解决五件事：

- 多 Agent 协作：让 planner、research、content、critic、memory、file 等 agent 各司其职。
- 可靠任务执行：长任务进入队列，支持状态管理、重试、取消、审批和失败恢复。
- 活记忆：系统能持续沉淀用户偏好、任务经验、工作流程和复盘结论。
- 工具协议：把搜索、arXiv、文件解析、导出、记忆检索、模型调用等能力统一成可治理工具。
- Agent 可观测性：看清每一步 plan、act、observe、evaluate、revise 的过程、成本和质量。
- 内容评价与学习反馈：对生成内容给出评分、理由、问题定位、修改建议，并把高价值经验沉淀到知识库、记忆和提示词模板。
- 对话式生产窗口：用户可以通过统一对话入口描述任务，系统自动识别任务类型、检索相关知识库、选择 Agent 并生成内容。

Beta1.0 的范围有意偏向“首次平台底座验证”。它不是只做一个窄功能 demo，而是用一条端到端 Agent 任务链路验证前端、网关、任务队列、Agent 运行、模型调用、工具、记忆、评估和观测这些核心边界是否能协同工作。实现时可以先把部分能力放在同一个代码服务或模块内，但目录、接口和数据所有权要按平台边界设计。

## Beta1.0 产品功能范围

Beta1.0 不是另起一个脱离原 MVP 的平台项目，而是把 MVP 已验证过的个人知识工作功能迁移到 AgentOS 架构中，让它们具备统一任务、队列、模型配置、模板、工具、文件、导出和可观测能力。

| 产品功能 | Beta1.0 目标 |
|------|------|
| 内容创作 | 支持论文、专利、小说、剧本、歌词、脱口秀稿 / 单口喜剧稿、小红书、知乎、公众号等内容生成与改写 |
| 模拟面试 | 基于简历和岗位描述生成简历分析、面试问题、回答评价和复盘报告 |
| 信息搜集 | 支持单 URL / PDF / JSON / RSS、批量多任务、站内信息发现与汇总报告 |
| arXiv 日报 | 支持研究方向管理、关键词 / 分类配置、按日期和篇数拉取论文、收藏论文、按范围生成日报 |
| 模型设置 | 支持 OpenAI-compatible API 配置、默认模型、连通性测试 |
| 提示词模板 | 支持按任务类型维护模板，并在信息搜集、arXiv 日报、内容创作等功能中复用 |
| 文件管理 | 支持上传并解析 PDF、DOCX、TXT、MD |
| 历史任务与导出 | 支持统一查看任务、重试、导出 Markdown |
| 对话式生产窗口 | 支持在统一对话窗口中理解任务、调取知识库、选择模板和生成内容 |
| 知识库沉淀 | 支持沉淀历史内容、资料来源、高质量案例、用户偏好和评价经验 |
| 内容评价与反馈 | 支持评分、评分理由、问题定位、修改建议、版本对比和经验沉淀 |

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
| 对话式生产窗口 | `conversation-agent` + `agent-orchestrator` + `context-engine` |
| 知识库沉淀 | `knowledge-base-svc` + `living-memory-svc` + pgvector |
| 内容评价与反馈 | `eval-svc` + `memory-agent` + prompt optimizer |

## 对话式内容生产中枢

Beta1.0 的产品入口不只是功能按钮，也要逐步形成一个统一的内容生产工作台：

```text
用户在对话窗口描述目标
  -> conversation-agent 理解任务和澄清需求
  -> context-engine 判断需要哪些知识库和历史经验
  -> knowledge-base-svc 检索相关资料、历史内容、用户偏好、高分案例
  -> planner-agent 选择 content / research / interview / arXiv 等 Agent
  -> Agent 生成内容
  -> eval-svc 输出评分、理由、问题定位、修改建议
  -> 用户选择采纳、重写、局部修改或确认沉淀经验
  -> memory-agent / prompt optimizer 把稳定经验写入知识库、活记忆或模板建议
```

内容评价不是简单打分，而是结构化反馈闭环：

| 反馈项 | 含义 |
|------|------|
| 评分 | 对事实性、结构、风格、完整度、平台适配度、可用性等维度量化 |
| 理由 | 解释每个分数为什么这样给 |
| 问题定位 | 指出具体段落、句子、结构或引用上的问题 |
| 修改建议 | 给出可直接用于下一轮生成或人工修改的建议 |
| 学习沉淀 | 把高价值偏好、写法、禁用表达、结构经验沉淀为知识或模板建议 |

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
  +--> conversation-agent
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
  +--> knowledge-base-svc
  +--> living-memory-svc
  +--> eval-svc
  +--> prompt-optimizer
  +--> policy-svc
  +--> task-svc

task-svc -> RabbitMQ -> worker
worker -> model-svc
worker -> tool-registry
worker -> knowledge-base-svc
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

### Knowledge Base

`knowledge-base-svc` 负责沉淀历史内容、资料来源、高质量案例、用户偏好、评分理由、问题定位和修改建议。它让系统通过检索、上下文注入、模板优化和用户确认来学习，而不是直接训练模型参数。

### Conversation Workbench

对话式生产窗口是统一入口。用户可以直接描述目标，系统自动理解任务类型、调取知识库、选择模板和 Agent，并在生成后展示评分、理由、问题位置、修改建议和版本历史。

### Tool Registry

`tool-registry` 是工具注册中心，统一管理内部工具和 MCP-style 工具。每个工具都要有权限、输入 schema、输出 schema、审计日志和调用成本。

### Eval Service

`eval-svc` 负责生成内容评价与学习反馈报告，例如事实性、格式、引用来源、完整性、风格一致性、是否满足用户目标、分维度评分、评分理由、问题定位、修改建议和可沉淀经验。

### Policy Service

`policy-svc` 负责权限、安全、审批和成本控制，例如敏感工具调用前审批、外部请求白名单、文件访问权限、模型预算限制、记忆写入规则和高风险操作拦截。

## 第一阶段 Agent

第一阶段建议实现这些 Agent：

| Agent | 职责 |
|------|------|
| `conversation-agent` | 对话式任务理解、澄清问题、任务路由、知识库选择 |
| `planner-agent` | 任务拆解、步骤规划、选择其他 Agent |
| `research-agent` | 网页搜索、arXiv、资料筛选、信息归纳 |
| `content-agent` | 文章、短视频脚本、脱口秀稿 / 单口喜剧稿、小红书、知乎、歌词、报告创作 |
| `interview-agent` | 简历分析、问题生成、回答评价、复盘建议 |
| `critic-agent` | 审稿、挑错、事实核查、质量评估 |
| `memory-agent` | 整理任务经验和评价反馈，决定哪些内容进入活记忆或知识库 |
| `file-agent` | 文件解析、摘要、导出、格式转换 |

第一版不建议每个 Agent 都独立部署成微服务。更稳的方式是先放在同一个 `agent-svc` 中：

```text
agent-svc
  agents/
    conversation_agent.py
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
.github/
  workflows/                   CI 检查入口
apps/
  web/                         Next.js 前端应用
config/
  app/                         应用级非敏感配置
  models/                      模型 Provider 示例配置，不放真实 API Key
  prompts/                     内容、面试、研究、arXiv 等提示词模板
services/
  gateway/                     统一 API 入口、认证上下文、SSE / WebSocket 代理
  agent-svc/                   Agent 编排、harness、loop-engine、context-engine
  task-svc/                    任务状态唯一事实源
  model-svc/                   模型 Provider、Key、路由、限流和成本统计
  tool-registry/               非模型工具注册、schema、权限和审计
  knowledge-base-svc/          历史内容、资料来源、高质量案例和评价经验
  living-memory-svc/           活记忆写入、检索、确认、冲突和过期
  eval-svc/                    评分、理由、问题定位、修改建议和 eval report
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
tests/
  contract/                    API、事件、tool schema 契约测试
  integration/                 PostgreSQL、RabbitMQ、Redis、MinIO 集成测试
  e2e/                         端到端用户流程测试
  fixtures/                    测试夹具
文档/                          架构、技术决策和项目说明
pyproject.toml                 Python 工程、lint、type check、test 配置
```

核心后端服务采用一致的内部结构：

```text
services/<service-name>/
  app/
    api/                       HTTP API
    core/                      配置、常量、运行时策略
    db/                        数据库会话和连接
    models/                    本服务拥有的 ORM Model
    schemas/                   本服务拥有的 Pydantic Schema
    services/                  业务服务
  migrations/                  本服务独立 Alembic migration
  tests/                       本服务测试
```

`agent-svc` 额外包含：

```text
services/agent-svc/app/
  conversation/                对话式任务理解、澄清问题、任务路由
  prompt_optimizer/            基于评价反馈的提示词优化建议
```

## 配置体系

项目采用“示例配置可提交，真实密钥不入库”的配置策略：

```text
.env.example                   根级本地环境变量示例
config/app/*.yaml              应用级非敏感配置
config/models/*.example.yaml   模型 Provider 示例配置
config/prompts/                可版本化提示词模板
infra/docker/.env.example      本地 Compose 依赖配置示例
services/*/config/             服务自己的配置读取边界
```

关键规则：

- 真实 `.env`、生产配置和 Secret 不提交到 GitHub。
- `model-svc` 是唯一读取大模型 API Key 的服务。
- OpenAI-compatible API 的 base URL、API Key、默认模型通过环境变量或模型设置页交给 `model-svc` 管理；API Key 只接收、不回显完整值。
- 提示词模板先放在 `config/prompts/`，由 `agent-svc` 的 `/prompt-templates`
  API 加载并在任务执行时渲染；后续复杂后再考虑拆 `prompt-svc`。
- 知识库阶段由 `knowledge-base-svc` 提供 PostgreSQL 持久化 API：`/knowledge-items`
  支持创建、筛选和读取知识条目，`/knowledge-items/search` 支持按任务类型、标签、质量分和关键词检索；embedding 字段已预留给后续 pgvector 语义检索实现。
- `agent-svc` 的最小 `context-engine` 会在执行前按任务类型检索 active 知识条目，将知识片段和来源注入 Prompt，并把检索记录写入 trace / artifacts。
- `agent-svc` 的 `/conversation/interpret` 提供阶段 5 对话式任务理解入口，会识别内容创作 / 改写目标、选择提示词模板、预取知识库来源，并返回可直接交给 `task-svc` 创建任务的草稿。
- 阶段 6 起，内容创作 / 改写任务会携带内容类型、目标读者、语气、长度、改写原文和改写要求；`content-agent` 会输出内容任务参数 artifact，并在 deterministic provider 下返回可读的初稿或改写稿。
- 阶段 7 起，`eval-svc` 提供 `/internal/evaluate`，`agent-svc` 会在内容生成后写入 `eval_report` artifact；前端任务详情展示评分、理由、问题定位、修改建议和学习候选。

## 推荐落地路线

1. 架构文档重写：把项目定位改为 Agent-native 个人 AI 操作系统。
2. 基础底座：落 PostgreSQL、pgvector、RabbitMQ、Redis、MinIO、Docker Compose。
3. Agent MVP：实现 `agent-svc` 内部的 `agent-orchestrator`、`agent-harness`、`loop-engine`，以及 `model-svc`、`task-svc`、`worker`。
4. 跑通第一条链路：用户输入目标 -> conversation-agent -> knowledge retrieval -> content-agent -> eval feedback -> 版本结果。
5. 知识库和活记忆：实现 `knowledge-base-svc`、`living-memory-svc`，支持历史内容、资料来源、高质量案例、用户确认、冲突检测和过期降权。
6. 内容评价与学习反馈：实现评分、评分理由、问题定位、修改建议、learning candidates 和提示词优化建议。
7. 工具系统：实现 `tool-registry`，把 arXiv、网页搜索、文件解析、导出都工具化。
8. 观测和评估：补齐 agent trace、tool call trace、knowledge retrieval trace、token/cost、loop step、eval report。
9. Kubernetes：Compose 稳定后，再迁移到 kind / K8s 验证部署能力。

## 文档索引

建议按以下顺序阅读：

1. `文档/架构设计与技术选型.md`
2. `文档/功能开发顺序.md`
3. `文档/技术决策Q&A.md`
