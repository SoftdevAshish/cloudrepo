# 4. Deployment & Release

## Environments
| Env | How |
|---|---|
| Local | `make run` / `make worker` / `make beat`, or `make up` (Docker Compose) |
| Production | Kubernetes via `k8s/` (Kustomize), deployed by `.github/workflows/cd.yml` |

## Pipeline
1. PR: `ci.yml` runs lint, typecheck, tests + coverage, dependency audit, image build.
2. Merge to `main`: `cd.yml` re-runs tests, pushes `ghcr.io/<repo>:<sha>` and `:latest`, sets the image with Kustomize, `kubectl apply -k`, then waits for api/worker/beat rollouts.
3. Production deploy is gated by the `production` GitHub environment (configure required reviewers).

## One-time setup
- Secret `KUBE_CONFIG` (base64 kubeconfig); environment `production`.
- Replace the placeholder password in `k8s/config.yaml` with a real secret manager entry.
- Set the ingress host in `k8s/app.yaml`.

## Release
Tag `vX.Y.Z` after updating `CHANGELOG.md` (Semantic Versioning).

## Rollback
`kubectl -n todo rollout undo deploy/api deploy/worker deploy/beat`, or redeploy a previous SHA tag.
