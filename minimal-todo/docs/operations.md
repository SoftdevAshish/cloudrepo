# 4. Deployment and operations (SDLC phases: Deployment, Maintenance)

## Configuration (environment variables)
| Variable | Meaning | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy URL (`sqlite:///./todo.db`, `postgresql+psycopg://user:pw@host/db`) | SQLite file |
| `SECRET_KEY` | JWT signing key, at least 32 random characters. **Must be set in production.** Generate: `python -c "import secrets;print(secrets.token_urlsafe(48))"` | insecure dev value |
| `ACCESS_TOKEN_MINUTES` | Token lifetime | 30 |
| `ADMIN_EMAILS` | Emails that become `admin` on registration | empty |

## Run
```bash
make install
cp .env.example .env     # then edit SECRET_KEY
make run                 # http://localhost:8000/docs
```

## Release checklist
- [ ] CI green on the release commit
- [ ] `SECRET_KEY` and `DATABASE_URL` provided by the platform's secret store
- [ ] Database is PostgreSQL (not SQLite) for multi-instance deployments
- [ ] HTTPS terminates in front of the app (tokens must never travel over plain HTTP)
- [ ] Health probe configured on `GET /health`
- [ ] Previous version noted for rollback

## Maintenance
- Update dependencies regularly and run the tests; add `pip-audit` to CI for known vulnerabilities.
- Rotate `SECRET_KEY` on suspicion of leakage (this logs everyone out).
- New permission? Edit `app/policies.py` and add tests in `tests/test_policies.py`.
