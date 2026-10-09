# 4. Deployment & Release

## Environments
| Env | How |
|---|---|
| Local | `make run` / `make worker` / `make beat`, or `make up` (Docker Compose) |
| Production | Kubernetes via `k8s/` (Kustomize), deployed by `.github/workflows/cd.yml` |

## Pipeline
1. PR: `ci.yml` runs lint, typecheck, tests + coverage, dependency audit, image build.
2. Merge to `main`: `cd.yml` re-runs lint, types and tests, pushes `ghcr.io/<repo>:<sha>` and `:latest`, then deploys in three steps: (1) apply namespace, config and databases; (2) recreate and run the `migrate` Job (`python -m scripts.migrate`: default + all named databases) and wait for it; (3) `kubectl apply -k` and wait for api/worker/beat rollouts. A failed migration stops the deploy before any new pod starts.
3. Production deploy is gated by the `production` GitHub environment (configure required reviewers).

## One-time setup
- Generate a real JWT secret (`openssl rand -hex 32`) and set `JWT_SECRET_KEY`; with `ENVIRONMENT=production` the app **will not start** with a placeholder. Set `ADMIN_EMAIL` / `ADMIN_PASSWORD` for the first admin, then rotate that password via `PATCH /api/v1/users/{id}`.
- Secret `KUBE_CONFIG` (base64 kubeconfig); environment `production`.
- Replace the placeholder password in `k8s/config.yaml` with a real secret manager entry.
- Set the ingress host in `k8s/app.yaml`.

## Release
Tag `vX.Y.Z` after updating `CHANGELOG.md` (Semantic Versioning).

## Database migrations
- Production sets `AUTO_MIGRATE=false`; migrations run only in the Job so replicas never race each other.
- Old and new application versions briefly run against the new schema during a rollout, so write migrations **backward compatible** (expand, deploy, then contract in a later release: add nullable columns first, drop or rename only after no running code uses them).
- Local: `make migrate`. New migration: `make revision m="..."`, review, commit.

## Rollback
`kubectl -n todo rollout undo deploy/api deploy/worker deploy/beat`, or redeploy a previous SHA tag. Schema changes are not rolled back automatically; because migrations are backward compatible the previous version keeps working. To undo one deliberately: `alembic downgrade -1` (use `-x db=<name>` for a named database).
