# packages/shared/events

Shared event contracts for RabbitMQ and service integration.

Initial event families:

- `task.created`
- `task.started`
- `task.completed`
- `task.failed`
- `task.cancelled`
- `approval.requested`
- `tool.called`
- `model.called`

Events should be versioned before consumers depend on them.
