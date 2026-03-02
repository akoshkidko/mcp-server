# Development Notes

## Migration History

- v0.1: initial user service with in-memory store
- v0.2: added auth token generation (BUG: no expiry)

<!-- TODO: cleanup migration notes after refactor -->

## Known Issues

1. `create_user` returns 500 when `external_id` is None — tracked in service.py
2. Auth token has no expiry — see auth.py `generate_token`
3. `UserRepository` is in-memory only — data lost on restart

## Architecture Decision Records

### ADR-001: In-memory storage

Chosen for simplicity during prototype phase.  Replace with PostgreSQL before launch.
