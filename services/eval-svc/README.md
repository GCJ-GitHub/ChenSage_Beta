# services/eval-svc

Agent 输出评价与学习反馈服务。

职责：

- 检查事实性、格式、引用来源、完整性和风格一致性。
- 判断输出是否满足用户目标。
- 生成分维度评分。
- 为每个分数写出理由。
- 标出具体问题位置，例如段落、句子、结构或引用。
- 给出可执行修改建议。
- 标出值得保留的优点。
- 生成 learning candidates，供 memory-agent 判断是否沉淀。
- 生成 eval report。
- 为 memory-agent 提供可沉淀经验建议。

边界：

- 不替代 critic-agent 的专业审稿能力。
- 不直接改写 task 最终结果，只返回评估报告和建议。
- 不自动修改提示词模板。
- 不自动把评价经验写入长期知识库。

Eval report 建议结构：

```text
scores
score_reasons
issue_locations
revision_advice
usable_highlights
source_risks
learning_candidates
```
