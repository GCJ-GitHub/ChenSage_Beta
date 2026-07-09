# services/living-memory-svc

活记忆服务。

职责：

- 管理 working、episodic、semantic、procedural、reflective、governed memory。
- 支持记忆写入、检索、合并、冲突检测、过期降权。
- 支持用户确认、冻结、删除和反馈。
- 生成 memory snapshot。

Beta1.0 策略：

- working memory 可自动写入，任务结束后过期或归档。
- 长期 semantic / procedural / governed memory 必须用户确认后长期生效。
- 冲突记忆进入 pending_confirmation。
