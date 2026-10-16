# ADR 0002: Stateless JWT bearer authentication

- Status: accepted
- Context: The API is consumed by SPAs, mobile apps and scripts.
- Decision: Short-lived (30 min) HS256 JWT access tokens in the `Authorization: Bearer` header; passwords hashed with bcrypt.
- Consequences:
  - (+) No server-side session storage; scales horizontally.
  - (-) A token cannot be revoked before expiry; mitigated by short lifetime and by loading the user (and `is_active`) on every request.
  - (-) No refresh tokens yet; users log in again after 30 minutes. Add refresh tokens when needed.
