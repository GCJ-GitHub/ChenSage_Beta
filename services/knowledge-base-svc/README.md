# services/knowledge-base-svc

知识库服务。

职责：

- 管理历史生成内容和版本。
- 管理用户确认过的高质量内容案例。
- 管理 URL、PDF、JSON、RSS、arXiv 等资料来源和摘要。
- 管理内容评价反馈沉淀出的经验条目。
- 支持按任务类型、主题、来源、质量分、标签和用户偏好检索。
- 通过 pgvector 提供语义检索。
- 向 context-engine 返回带来源、质量分、状态和适用范围的知识片段。

核心对象：

```text
knowledge_items
knowledge_chunks
knowledge_sources
content_versions
content_feedback
evaluation_reports
learning_candidates
prompt_optimization_suggestions
```

边界：

- 不保存模型 Provider Secret。
- 不替代 living-memory-svc 的长期偏好治理。
- 不把所有生成内容默认提升为高质量知识。
- 高质量案例、长期风格偏好、禁用表达、流程经验需要用户确认或满足明确治理规则。
