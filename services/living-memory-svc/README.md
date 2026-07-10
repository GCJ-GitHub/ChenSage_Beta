# services/living-memory-svc

活记忆服务。

职责：

- 管理 working、episodic、semantic、procedural、reflective、governed memory。
- 支持记忆写入、检索、合并、冲突检测、过期降权。
- 支持用户确认、冻结、删除和反馈。
- 生成 memory snapshot。
- 接收 eval-svc 的 learning candidates，并判断哪些适合作为长期偏好或流程经验。

Beta1.0 策略：

- working memory 可自动写入，任务结束后过期或归档。
- 长期 semantic / procedural / governed memory 必须用户确认后长期生效。
- 冲突记忆进入 pending_confirmation。

和 knowledge-base-svc 的边界：

- living-memory-svc 管用户偏好、流程经验、长期记忆和治理状态。
- knowledge-base-svc 管历史内容、资料来源、高质量案例、知识分片和评价经验。
- 评价反馈不能直接长期生效，必须经过 memory-agent 判断和治理规则。
