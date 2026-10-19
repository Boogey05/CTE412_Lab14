Campus Notice Board - Kubernetes Deployment StrategiesPurposeThis repository contains the Kubernetes manifests, application source code, analysis scripts, and captured evidence for deploying and benchmarking release strategies for the Campus Notice Board API. The objective is to deploy the service to a local kind cluster and empirically measure availability, failed requests, and mixed-version windows across Recreate, RollingUpdate, Blue/Green, and Feature Flag deployments rather than assuming zero-downtime behavior. All cluster objects, images, and evidence files are scoped to student ID <sid>.   Software Versions & PrerequisitesDocker Engine / Desktop: v24.0 or later   kind: v0.20.0 or later   kubectl: v1.27.0 or later (within one minor version of the cluster)   Git: v2.x   Operating System: Linux, macOS, or WSL2   Repository StructurePlaintext.
├── README.md                   # Purpose, versions, rebuild sequence, and cleanup commands
├── app/                        # Application source code and Dockerfile[cite: 2]
├── cluster/
│   └── kind-cluster.yaml       # kind cluster configuration (1 control-plane, 2 worker nodes)[cite: 2, 3]
├── manifests/
│   ├── base/                   # Namespace, ResourceQuota, LimitRange, Availability Monitor[cite: 2]
│   ├── rolling/                # Single-Deployment manifests for Recreate & RollingUpdate[cite: 2]
│   └── bluegreen/              # Blue/Green Deployments, Services, and Feature Flag ConfigMap[cite: 2]
├── scripts/
│   └── summarise.sh            # Shell script to parse and summarise monitor output logs[cite: 2]
├── evidence/                   # Command output logs (tN-*.txt) and monitor logs
└── report/
    └── p06-report.md           # Assessed practical lab report
Complete Command Sequence (Rebuild Final State)Follow these commands sequentially from the repository root to reconstruct the final Task 8 state on an empty machine[cite: 2, 7]. Replace <sid> with your actual student number[cite: 2].1. Cluster & Namespace InitializationBash# 1. Create kind cluster with node port 30090 bound to host 127.0.0.1[cite: 3]
kind create cluster --config cluster/kind-cluster.yaml --name cte412-<sid>[cite: 3]

# 2. Apply core namespace, quota, and limit range manifests[cite: 2, 3]
kubectl apply -f manifests/base/namespace.yaml[cite: 2, 3]
kubectl apply -f manifests/base/quota.yaml[cite: 2, 3]
kubectl apply -f manifests/base/limitrange.yaml[cite: 2, 3]

# 3. Set nb-<sid> as the default namespace for the kubectl context[cite: 3]
kubectl config set-context --current --namespace=nb-<sid>[cite: 3]
2. Build & Load Release Container ImagesBash# 1. Build local Alpine-based images for all three release tags[cite: 2, 4]
docker build -t notice-board:<sid>-1.0.0 app/[cite: 2, 4]
docker build -t notice-board:<sid>-1.1.0 app/[cite: 2, 4]
docker build -t notice-board:<sid>-1.2.0-broken app/[cite: 2, 4]

# 2. Load images directly into the kind cluster without an external registry[cite: 2, 4]
kind load docker-image notice-board:<sid>-1.0.0 --name cte412-<sid>[cite: 4]
kind load docker-image notice-board:<sid>-1.1.0 --name cte412-<sid>[cite: 4]
kind load docker-image notice-board:<sid>-1.2.0-broken --name cte412-<sid>[cite: 4]
3. Deploy Availability MonitorBash# Deploy continuous HTTP availability monitoring Pod in manifests/base/[cite: 2, 5]
kubectl apply -f manifests/base/monitor.yaml[cite: 2, 5]
4. Deploy Blue/Green Infrastructure & Feature Flag (Task 8 Final State)Bash# 1. Apply feature flag ConfigMap (FEATURE_PINNED=true)[cite: 2, 7]
kubectl apply -f manifests/bluegreen/configmap-flags.yaml[cite: 2, 7]

# 2. Deploy Blue (1.0.0) and Green (1.1.0) Deployments[cite: 2, 6]
kubectl apply -f manifests/bluegreen/deployment-blue.yaml[cite: 2, 6]
kubectl apply -f manifests/bluegreen/deployment-green.yaml[cite: 2, 6]

# 3. Deploy production and preview Services[cite: 2, 6]
kubectl apply -f manifests/bluegreen/service-production.yaml[cite: 2, 6]
kubectl apply -f manifests/bluegreen/service-preview.yaml[cite: 2, 6]

# 4. Trigger declarative Pod refresh to pick up updated ConfigMap flag[cite: 7]
kubectl rollout restart deployment/notice-board-green[cite: 7]
5. Verify StateBash# Verify Pod status, Services, and ResourceQuota usage[cite: 3, 6]
kubectl get pods -o wide[cite: 3, 6]
kubectl get services[cite: 6]
kubectl get resourcequota[cite: 3, 6]

# Test local NodePort routing and feature flag response[cite: 3, 4, 7]
curl http://127.0.0.1:30090/version[cite: 3, 4]
curl http://127.0.0.1:30090/notices[cite: 4, 7]
Clean-up CommandsTo clean up cluster resources and reset your context after testing[cite: 2, 7]:Bash# 1. Reset kubectl context default namespace[cite: 7]
kubectl config set-context --current --namespace=default[cite: 7]

# 2. Delete the local kind cluster[cite: 7]
kind delete cluster --name cte412-<sid>[cite: 7]
