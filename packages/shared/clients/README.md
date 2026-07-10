# packages/shared/clients

Internal service clients.

Preferred sources:

- Generated clients from OpenAPI specs.
- Thin handwritten clients for early Beta work.

Clients should not hide cross-service ownership. For example, task state writes still go through task-svc APIs.
