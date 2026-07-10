# services/eval-svc/config

Evaluation service configuration boundary.

Configuration sources:

- Evaluation dimensions and thresholds: `config/app/*.yaml` or future eval config.
- Prompt templates for evaluation: `config/prompts/evaluation/`.
- Model calls: through `model-svc`, not direct Provider Secrets.

Rules:

- Evaluation reports must include reasons, issue locations, and revision advice.
- Learning candidates are suggestions, not automatically accepted knowledge.
