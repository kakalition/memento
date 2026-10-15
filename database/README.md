# Database

agentkit persists everything in a single local database (libSQL/SQLite) via
SQLModel. Tables are created from model metadata at startup.

- Add models under `app/Models/` and repositories under `app/Repositories/`.
- `agentkit` repairs drifted columns automatically (`sync_missing_columns`).
- For complex schema evolution, see `agentkit.db.migrations` (Alembic helper).
