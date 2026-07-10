# services/knowledge-base-svc/config

Knowledge base service configuration boundary.

Configuration sources:

- Retrieval limits and quality thresholds: `config/app/*.yaml`.
- Embedding model routing: through `model-svc`.
- Knowledge write governance: through `policy-svc` and memory governance rules.

Rules:

- Historical content can be stored as versions.
- High-quality examples require user confirmation or explicit governance rules.
- Retrieval responses must include source refs, quality score, status, and scope.
