# CTE412 Practical — Campus Notice Board: Rolling, Recreate and Blue/Green Releases on Kubernetes

**Student:** Kinley Phuntsho (`02230132`)
**Course:** CTE412 Integrated Systems Technology, BE in Information Technology, Year 3, College of Science and Technology, Royal University of Bhutan
**Semester:** Autumn 2026

Throughout this repository `<sid>` = `02230132`.

## 1. Purpose

The Campus Notice Board API is deployed to a local `kind` Kubernetes cluster and released using three strategies: **Recreate**, **RollingUpdate** and **Blue/Green**. A monitor Pod requests `/version` every 0.5 s for the whole session, so each strategy is judged by a measured number of failed requests rather than an assumption. The practical also covers a failed release with automatic failure detection and rollback, and a feature flag delivered through a ConfigMap.

## 2. Software Versions

| Tool | Version |
|---|---|
| Host OS | Windows 11 + WSL2 (PowerShell) |
| Docker Desktop / Engine | _fill in: output of `docker version --format '{{.Server.Version}}'`_ |
| kind | _fill in: output of `kind version`_ |
| kubectl | _fill in: output of `kubectl version --client`_ |
| Kubernetes (cluster) | v1.37.0 (`kindest/node:v1.37.0`, containerd 2.3.4) |
| Application | Python 3.12 on `python:3.12-alpine` |
| Monitor image | `busybox:1.36` |

## 3. Repository Structure

```
.
├── README.md
├── cluster/
│   └── kind-cluster.yaml          # 1 control-plane + 2 workers, 127.0.0.1:30090 -> node 30090
├── app/                           # Application source + Dockerfiles (1.0.0, 1.1.0, 1.2.0-broken)
├── manifests/
│   ├── base/                      # Namespace, ResourceQuota, LimitRange, monitor Pod
│   ├── rolling/                   # Single-Deployment release manifests + Services (Tasks 3, 5, 6)
│   └── bluegreen/                 # Blue/green Deployments, Services, feature-flag ConfigMap (Tasks 7, 8)
├── scripts/
│   └── summarise.sh               # Monitor-log summariser
├── evidence/                      # All captured output (tN-<description>.txt)
└── report/
    └── p06-report.md              # Assessed report
```

## 4. Rebuild the Final State (Task 8) from an Empty Machine

Run every command from the repository root in PowerShell. Prerequisite: Docker is running, and `kind` and `kubectl` are installed.

### 4.1 Create the cluster

```powershell
kind create cluster --name cte412-02230132 --config cluster/kind-cluster.yaml
kubectl get nodes -o wide                      # expect 3 Ready nodes
```

### 4.2 Build the three images (local only, no registry)

```powershell
docker build -t notice-board:02230132-1.0.0 app/
docker build --build-arg APP_VERSION=02230132-1.1.0 -t notice-board:02230132-1.1.0 app/
docker build -f app/Dockerfile.broken -t notice-board:02230132-1.2.0 app/
docker images --filter "reference=notice-board"
```

### 4.3 Load the images into every kind node

```powershell
kind load docker-image notice-board:02230132-1.0.0 --name cte412-02230132
kind load docker-image notice-board:02230132-1.1.0 --name cte412-02230132
kind load docker-image notice-board:02230132-1.2.0 --name cte412-02230132

# Confirm from inside a worker node
docker exec cte412-02230132-worker crictl images | Select-String notice-board
```

### 4.4 Create the namespace, quota, limit range and monitor

```powershell
kubectl apply -f manifests/base/
kubectl config set-context --current --namespace=nb-02230132
kubectl config view --minify | Select-String "namespace"
kubectl get pod monitor                        # must stay Running; never restart it
```

### 4.5 Deploy the blue/green stack, ConfigMap and Services

```powershell
kubectl apply -f manifests/bluegreen/
kubectl rollout status deployment/notice-board-blue
kubectl rollout status deployment/notice-board-green
kubectl get pods,svc,deploy -n nb-02230132
```

### 4.6 Verify

```powershell
# Production through the NodePort (answered by several Pods)
1..6 | ForEach-Object { curl.exe -s http://127.0.0.1:30090/version; Start-Sleep -Milliseconds 300 }

# Notices, including the feature flag state
curl.exe -s http://127.0.0.1:30090/notices

# Availability summary from the monitor
kubectl logs monitor -n nb-02230132 > evidence/monitor-now.log
bash scripts/summarise.sh evidence/monitor-now.log
```

## 5. Release Procedures Used in the Practical

All state changes are made by editing a manifest and running `kubectl apply`. The single exception is the rollback in Task 6.

| Task | Action | Command |
|---|---|---|
| 3 | Deploy 1.0.0 + Services | `kubectl apply -f manifests/rolling/deployment.yaml` then `kubectl apply -f manifests/rolling/service.yaml` |
| 4 | Start the monitor | `kubectl apply -f manifests/base/monitor.yaml` |
| 5 | Recreate release of 1.1.0 | `kubectl apply -f manifests/rolling/deployment-recreate.yaml` |
| 5 | RollingUpdate release of 1.1.0 | `kubectl apply -f manifests/rolling/deployment-rolling.yaml` |
| 6 | Broken release 1.2.0 | `kubectl apply -f manifests/rolling/deployment-broken.yaml` |
| 6 | Rollback (only imperative change) | `kubectl rollout undo deployment/notice-board` |
| 6 | Prove manifest = live object | `kubectl diff -f manifests/rolling/deployment.yaml` (exit code 0) |
| 7 | Blue/green switch | edit `selector.slot` in `manifests/bluegreen/services.yaml`, then `kubectl apply -f manifests/bluegreen/services.yaml` |
| 8 | Flag change | set `FEATURE_PINNED: "true"` in `manifests/bluegreen/flags.yaml`, then `kubectl apply -f manifests/bluegreen/flags.yaml` |

Useful observation commands (read-only):

```powershell
kubectl rollout history deployment/notice-board
kubectl get pods -l app=notice-board -w
kubectl get endpointslice -l kubernetes.io/service-name=notice-board -o wide
kubectl describe quota nb-quota -n nb-02230132
```

## 6. Prove the Rebuild Sequence (Task 9)

Delete every object in the namespace except the namespace, quota and limit range, then repeat sections 4.4 to 4.5:

```powershell
kubectl delete -f manifests/bluegreen/
kubectl delete pod monitor
kubectl get all -n nb-02230132                 # should be empty
kubectl get quota,limitrange -n nb-02230132    # quota and limit range remain

kubectl apply -f manifests/base/monitor.yaml
kubectl apply -f manifests/bluegreen/
kubectl get pods,svc,deploy -n nb-02230132 > evidence/t9-rebuild.txt
```

## 7. Clean-up

```powershell
# Reset the context namespace to default
kubectl config set-context --current --namespace=default

# Delete the cluster
kind delete cluster --name cte412-02230132

# Prove it is gone
kind get clusters > evidence/t9-cluster-deleted.txt

# Optional: remove local images
docker rmi notice-board:02230132-1.0.0 notice-board:02230132-1.1.0 notice-board:02230132-1.2.0
```

## 8. Evidence and Report

* Captured command output is in `evidence/`, named `tN-<description>.txt`.
* The assessed report is `report/p06-report.md`.

