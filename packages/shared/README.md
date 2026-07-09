# packages/shared

跨服务共享契约包。

允许放：

- DTO / Pydantic schema。
- OpenAPI 生成 client。
- 事件契约。
- 错误码。
- 日志、配置、trace 工具。

禁止放：

- 全量 ORM Model。
- Repository。
- 业务 Service。
- 数据库 Session。

原则：shared 用来共享契约，不共享数据所有权。
