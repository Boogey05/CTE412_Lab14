# Campus Notice Board — CTE412 Practical 06 (02230129)

## Software versions
- Windows 11 / WSL2; Docker Desktop 4.x; kind v0.23+; kubectl v1.30+; Kubernetes v1.30 (kind node image)
- Application: Python 3.12 on `python:3.12-alpine`

## Rebuild from scratch
```powershell
kind create cluster --name cte412-02230129 --config cluster/kind-cluster.yaml
docker build -t notice-board:02230129-1.0.0 app/
docker build --build-arg APP_VERSION=02230129-1.1.0 -t notice-board:02230129-1.1.0 app/
docker build -f app/Dockerfile.broken -t notice-board:02230129-1.2.0 app/
kind load docker-image notice-board:02230129-1.0.0 --name cte412-02230129
kind load docker-image notice-board:02230129-1.1.0 --name cte412-02230129
kind load docker-image notice-board:02230129-1.2.0 --name cte412-02230129
kubectl apply -f manifests/base/
kubectl config set-context --current --namespace=nb-02230129
kubectl apply -f manifests/bluegreen/
kubectl rollout status deployment/notice-board-blue
kubectl rollout status deployment/notice-board-green