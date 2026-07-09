# services/eval-svc

Agent 输出评估服务。

职责：

- 检查事实性、格式、引用来源、完整性和风格一致性。
- 判断输出是否满足用户目标。
- 生成 eval report。
- 为 memory-agent 提供可沉淀经验建议。

边界：

- 不替代 critic-agent 的专业审稿能力。
- 不直接改写 task 最终结果，只返回评估报告和建议。
