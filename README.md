# ChenSage_Beta

> 晨枢 AI Beta1.0：个人 AI 任务中枢平台的本地云原生微服务化设计仓库。

## 项目简介

ChenSage（晨枢 AI）是一个面向个人知识工作者的 AI 任务中枢平台。MVP1.0 已经完成了本地单体版本的核心功能探索，包括内容生成、信息搜集、arXiv 日报、提示词模板、历史任务与导出等能力。

本仓库是 ChenSage_Beta1.0 阶段的设计与工程化规划仓库，目标是把 MVP1.0 从本地单体逐步演进为可容器化、可观测、可扩展、可部署的本地云原生系统。

Beta1.0 当前重点不是立刻上线多人企业 SaaS，而是：

- 保持个人自用体验稳定。
- 引入企业级工程约束，练习云原生与微服务能力。
- 建立清晰的服务边界、数据边界、任务队列、日志、监控、CI/CD 和安全基线。
- 为未来上线个人版或小规模私有部署预留演进空间。

## 当前阶段

当前仓库处于 Beta1.0 架构设计阶段，主要内容是文档，不是完整可运行代码仓库。

已完成文档：

- `文档/架构设计与技术选型.md`
- `文档/技术决策Q&A.md`

后续代码落地会围绕这些文档逐步补齐：

- Docker Compose 本地开发环境
- PostgreSQL / RabbitMQ / Redis / MinIO 基础设施
- FastAPI 微服务
- Celery Worker
- Next.js 前端
- OpenTelemetry / Prometheus / Grafana / Loki 可观测性
- kind / Kubernetes 本地集群部署
- GitHub Actions CI/CD

## 目标架构

Beta1.0 推荐架构：

```text
Browser
  |
  v
Ingress / Nginx
  |
  v
gateway
  |
  +--> auth-svc
  +--> model-svc
  +--> file-svc
  +--> task-svc
  +--> content-svc
  +--> interview-svc
  +--> research-svc

task-svc  <--> RabbitMQ <--> worker
worker    <--> model-svc
file-svc  <--> MinIO
services  <--> PostgreSQL
services  <--> Redis

Observability:
Prometheus + Grafana + Loki + OpenTelemetry
```

## 核心技术选型

| 层级 | 选型 | 说明 |
|------|------|------|
| 后端语言 | Python 3.12 / 3.13 | 优先稳定生态，复用 MVP Python 资产 |
| Web 框架 | FastAPI | 适合 OpenAPI、异步 API 和快速迭代 |
| 前端 | Next.js 16 + React 19 | 延续 MVP 前端技术栈 |
| 数据库 | PostgreSQL 16 | 替代 SQLite，支持多 schema |
| ORM / Migration | SQLAlchemy 2.x + Alembic | 每服务独立 migration |
| 队列 | RabbitMQ + Celery | 可靠长任务、重试、死信队列 |
| 缓存 | Redis 7 | 缓存、限流、短状态 |
| 对象存储 | MinIO | 本地 S3 兼容对象存储 |
| 本地容器 | Docker / Docker Compose | 日常开发主入口 |
| 本地 Kubernetes | kind + kubectl + Helm | 本地云原生学习与验证 |
| 可观测性 | OpenTelemetry + Prometheus + Grafana + Loki | 日志、指标、链路追踪 |
| CI/CD | GitHub Actions | 测试、构建、扫描、交付 |

## 推荐本地环境

建议在 Windows + WSL2 或 Linux 环境下开发。

基础环境：

- Git
- Docker Desktop，启用 WSL2 backend
- WSL2 Ubuntu
- Node.js 20 LTS 或更高 LTS 版本
- npm / pnpm
- Python 3.12 或 3.13
- pip / uv

云原生工具：

- Docker Compose
- kubectl
- kind
- Helm

Beta 基础设施组件建议优先通过 Docker Compose 启动，不建议直接安装到宿主机：

- PostgreSQL 16
- RabbitMQ
- Redis 7
- MinIO
- Prometheus
- Grafana
- Loki

## 环境检查命令

```powershell
git --version
docker --version
docker compose version
wsl --status
node --version
npm --version
python --version
pip --version
kubectl version --client
kind version
helm version
```

## 计划中的本地启动方式

后续代码落地后，优先提供：

```powershell
docker compose up -d
```

以及：

```powershell
make compose-up
make compose-down
make kind-deploy
```

当前仓库还没有完整服务代码和 Compose 文件，因此上述命令属于 Beta1.0 后续落地目标。

## 服务拆分原则

本项目虽然是个人项目，但 Beta1.0 会按企业级工程约束设计服务边界：

- 不按页面菜单机械拆服务。
- 按领域边界、数据归属、任务状态和运行特征拆分。
- `task-svc` 只负责任务生命周期，不收纳所有业务逻辑。
- `shared` 只共享 DTO、client、事件契约和通用工具，不共享全量 ORM Model。
- PostgreSQL 初期采用单实例多 schema，每个服务拥有自己的 schema 和 migration。

## 任务系统设计

MVP 阶段的本地线程任务会在 Beta1.0 中替换为：

```text
task-svc -> RabbitMQ -> Celery Worker -> model-svc / external APIs
```

原因：

- AI 任务耗时较长。
- 模型 API 可能超时、限流或失败。
- 任务需要持久化、ack、重试、超时、取消和死信队列。

Redis 不再作为关键任务事件机制，只用于缓存、限流和短期状态。

## 安全与可观测性

Beta1.0 会补齐以下工程能力：

- JWT 登录与刷新 Token
- API Key / Secret 管理
- 上传文件类型和大小限制
- SSRF 防护
- 审计日志
- JSON 结构化日志
- Prometheus 指标
- OpenTelemetry Trace
- Grafana 可视化面板
- Loki 日志收集
- GitHub Actions 自动测试与构建

## 路线图

1. 文档和边界确认
2. 本地 Compose 云原生底座
3. PostgreSQL 替换 SQLite
4. RabbitMQ + Celery 替换本地线程
5. MinIO 替换本地文件路径
6. API / Web / Worker 容器化
7. gateway / model-svc / task-svc / file-svc / research-svc 等服务拆分
8. 可观测性、安全和 CI/CD
9. kind 本地 Kubernetes 集群部署
10. 小规模上线准备

## 文档索引

建议按以下顺序阅读：

1. `文档/架构设计与技术选型.md`
2. `文档/技术决策Q&A.md`

其中：

- 架构设计文档是主文档，描述目标架构、技术选型、服务边界和阶段路线。
- Q&A 文档记录本次架构审阅发现的问题、修改方式和决策理由。

## 项目定位提醒

ChenSage_Beta1.0 是个人项目的本地云原生微服务化版本，不是大型企业团队的通用模板。

它保留“个人自用优先”的约束，同时引入更严谨的工程设计，用于支撑后续上线和长期演进。
