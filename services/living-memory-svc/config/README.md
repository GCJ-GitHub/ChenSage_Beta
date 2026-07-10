# services/living-memory-svc/config

Living memory service configuration boundary.

Configuration sources:

- Memory confidence and expiry rules: `config/app/*.yaml`.
- Long-term memory approval policy: `policy-svc`.

Rules:

- Long-term semantic, procedural, and governed memories require confirmation.
- Eval learning candidates must be reviewed before becoming long-term memory.
