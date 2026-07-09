# services/tool-registry

非模型工具注册中心。

职责：

- 注册 web_search、arxiv_search、file_parse、pdf_export、markdown_export、database_query、memory_search、eval_check、citation_check 等工具。
- 管理 input_schema、output_schema、permission_scope、approval_required、cost_policy、timeout、retry_policy、audit_fields。
- 调用 policy-svc 判断工具权限和审批。
- 记录工具调用审计和成本。

边界：

- 不负责模型 Provider 调用。
- 不绕过 policy-svc 执行高风险工具。
