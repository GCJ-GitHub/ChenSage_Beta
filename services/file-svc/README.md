# services/file-svc

文件服务。

职责：

- 管理上传文件、解析结果、导出产物和 MinIO object key。
- 记录文件元数据、所属用户、所属任务、解析状态和审计信息。
- 向 tool-registry 暴露受控的文件解析和导出能力。

边界：

- 数据库只保存元数据和对象 key。
- 原始文件和导出产物存储在 MinIO。
- 文件访问必须经过 policy-svc 授权。
