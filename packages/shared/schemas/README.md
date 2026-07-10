# packages/shared/schemas

Shared DTOs that are safe to import across services.

Allowed:

- Request / response schemas.
- Value objects without database behavior.
- Contract snapshots generated from OpenAPI.

Not allowed:

- SQLAlchemy ORM models.
- Repository objects.
- Database sessions.
