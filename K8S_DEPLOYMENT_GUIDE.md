# Kubernetes Deployment Guide for MCP PDF

This guide provides step-by-step instructions for deploying the MCP PDF application to a Kubernetes cluster.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Docker Image Preparation](#docker-image-preparation)
3. [Pre-deployment Configuration](#pre-deployment-configuration)
4. [Deploying to Kubernetes](#deploying-to-kubernetes)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)
7. [Monitoring and Logs](#monitoring-and-logs)

---

## Prerequisites

Before deploying to Kubernetes, ensure you have:

- **Kubernetes Cluster**: A running K8s cluster (local minikube, EKS, GKE, AKS, etc.)
- **kubectl**: Installed and configured to access your cluster
- **Docker**: Installed for building and pushing images
- **Docker Hub Account**: For pushing `vinumore/mcp-pdf-backend` and `vinumore/mcp-pdf-frontend` images

Verify your setup:
```bash
kubectl version --client
docker --version
```

---

## Docker Image Preparation

### 1. Build Docker Images

Navigate to your project root and build both images:

```bash
cd /Users/vinu__more/Projects/mcp_pdf

# Build backend image
docker build -f Dockerfile.backend -t vinumore/mcp-pdf-backend:latest .

# Build frontend image
docker build -f Dockerfile.frontend -t vinumore/mcp-pdf-frontend:latest .
```

### 2. Push Images to Docker Hub

Login to Docker Hub first:
```bash
docker login
```

Push both images:
```bash
docker push vinumore/mcp-pdf-backend:latest
docker push vinumore/mcp-pdf-frontend:latest
```

Verify images are available:
```bash
docker images | grep mcp-pdf
```

---

## Pre-deployment Configuration

### 1. Configure Secrets

Edit the [secret.yaml](k8s/secret.yaml) file and add your sensitive environment variables:

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: mcp-pdf-secret
  namespace: mcp-pdf
type: Opaque
stringData:
  PERPLEXITY_API_KEY: "your-actual-api-key-here"
  # Add other API keys or credentials as needed
```

### 2. Configure ConfigMap (Optional)

If you need to modify application configuration, edit [k8s/configmap.yaml](k8s/configmap.yaml):

```yaml
data:
  REACT_APP_API_URL: "http://mcp-pdf-backend-service:8000"
  PYTHONUNBUFFERED: "1"
  PYTHONPATH: "/app"
```

### 3. Configure Ingress (Optional)

For production deployments with a domain, update [k8s/ingress.yaml](k8s/ingress.yaml):

Replace `mcp-pdf.example.com` with your actual domain:
```yaml
- host: your-domain.com
  http:
    paths:
    - path: /api
      backend:
        service:
          name: mcp-pdf-backend-service
          port:
            number: 8000
```

---

## Deploying to Kubernetes

### Quick Deploy (Recommended)

Deploy all resources in order:

```bash
cd /Users/vinu__more/Projects/mcp_pdf

# Create namespace first
kubectl apply -f k8s/namespace.yaml

# Apply all configuration files
kubectl apply -f k8s/configmap.yaml
kubectl apply -f k8s/secret.yaml
kubectl apply -f k8s/pvc.yaml
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
kubectl apply -f k8s/hpa.yaml
kubectl apply -f k8s/ingress.yaml
```

### Deploy Everything at Once

```bash
kubectl apply -f k8s/
```

**Note**: This deploys all files alphabetically. For first-time deployment, use the ordered approach above to ensure namespace exists first.

### What Each File Does

| File | Purpose |
|------|---------|
| `namespace.yaml` | Creates isolated namespace for the app |
| `configmap.yaml` | Stores non-sensitive configuration |
| `secret.yaml` | Stores API keys and credentials |
| `pvc.yaml` | Persistent storage for uploads, cache, logs |
| `deployment.yaml` | Backend and frontend pod definitions (2 replicas each) |
| `service.yaml` | Internal services and NodePort access |
| `hpa.yaml` | Auto-scaling rules based on CPU/memory |
| `ingress.yaml` | External HTTP/HTTPS routing |

---

## Verification

### 1. Check Namespace Creation

```bash
kubectl get namespace mcp-pdf
```

Expected output:
```
NAME      STATUS   AGE
mcp-pdf   Active   2m
```

### 2. Check Pods

```bash
kubectl get pods -n mcp-pdf
```

Expected output (pods should transition from Pending → Running):
```
NAME                                   READY   STATUS    RESTARTS   AGE
mcp-pdf-backend-xxxxxx-xxxxx           1/1     Running   0          2m
mcp-pdf-backend-xxxxxx-xxxxx           1/1     Running   0          2m
mcp-pdf-frontend-yyyyyy-yyyyy          1/1     Running   0          2m
mcp-pdf-frontend-yyyyyy-yyyyy          1/1     Running   0          2m
```

Wait for all pods to reach `Running` status:
```bash
kubectl wait --for=condition=Ready pod -l app=mcp-pdf-backend -n mcp-pdf --timeout=300s
kubectl wait --for=condition=Ready pod -l app=mcp-pdf-frontend -n mcp-pdf --timeout=300s
```

### 3. Check Services

```bash
kubectl get svc -n mcp-pdf
```

Expected output:
```
NAME                          TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)    AGE
mcp-pdf-backend-service       ClusterIP   10.x.x.x        <none>        8000/TCP   2m
mcp-pdf-frontend-service      ClusterIP   10.x.x.x        <none>        80/TCP     2m
mcp-pdf-frontend-nodeport     NodePort    10.x.x.x        <none>        80:30080/TCP   2m
```

### 4. Check Storage

```bash
kubectl get pvc -n mcp-pdf
```

Expected output:
```
NAME                      STATUS   VOLUME   CAPACITY   ACCESS MODES   STORAGECLASS   AGE
mcp-pdf-cache-pvc         Bound    ...      20Gi       RWO            standard       2m
mcp-pdf-logs-pvc          Bound    ...      5Gi        RWO            standard       2m
mcp-pdf-uploads-pvc       Bound    ...      10Gi       RWO            standard       2m
```

### 5. Check Autoscaling

```bash
kubectl get hpa -n mcp-pdf
```

Expected output:
```
NAME                       REFERENCE                             TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
mcp-pdf-backend-hpa        Deployment/mcp-pdf-backend            <unknown>/70%   2         5         2          2m
mcp-pdf-frontend-hpa       Deployment/mcp-pdf-frontend           <unknown>/80%   2         4         2          2m
```

### 6. Access the Application

**Local Access (Using NodePort)**:
```bash
# Get the node's external IP or hostname
kubectl get nodes -o wide

# Access via: http://<node-ip>:30080
```

**Port Forward (Quick Testing)**:
```bash
# Frontend
kubectl port-forward -n mcp-pdf svc/mcp-pdf-frontend-service 3000:80

# Backend
kubectl port-forward -n mcp-pdf svc/mcp-pdf-backend-service 8000:8000

# Then access http://localhost:3000 and http://localhost:8000
```

**Production (Using Ingress)**:
```bash
kubectl get ingress -n mcp-pdf
```

---

## Troubleshooting

### Pods Not Starting

Check pod status and events:
```bash
kubectl describe pod <pod-name> -n mcp-pdf
kubectl get events -n mcp-pdf --sort-by='.lastTimestamp'
```

Common issues:
- **ImagePullBackOff**: Docker image not found or not pushed to registry
  ```bash
  docker push vinumore/mcp-pdf-backend:latest
  docker push vinumore/mcp-pdf-frontend:latest
  ```

- **CrashLoopBackOff**: Application error. Check logs:
  ```bash
  kubectl logs <pod-name> -n mcp-pdf --tail=50
  ```

- **Pending**: Insufficient resources or PVC not bound
  ```bash
  kubectl describe pod <pod-name> -n mcp-pdf
  ```

### Service Not Accessible

Verify service endpoints:
```bash
kubectl get endpoints -n mcp-pdf
kubectl describe svc mcp-pdf-backend-service -n mcp-pdf
```

### Environment Variables Not Set

Check if ConfigMap and Secret are properly mounted:
```bash
kubectl describe pod <pod-name> -n mcp-pdf | grep -A 10 "Environment:"
```

### Storage Issues

Check PVC status:
```bash
kubectl describe pvc mcp-pdf-uploads-pvc -n mcp-pdf
kubectl get pv
```

### Reset/Cleanup

If you need to restart everything:

```bash
# Delete all resources in the namespace
kubectl delete namespace mcp-pdf

# Recreate from scratch
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/
```

---

## Monitoring and Logs

### View Backend Logs

```bash
# Real-time logs
kubectl logs -n mcp-pdf -l app=mcp-pdf-backend -f

# Last 50 lines
kubectl logs -n mcp-pdf -l app=mcp-pdf-backend --tail=50

# From all backend pods
kubectl logs -n mcp-pdf -l app=mcp-pdf-backend --all-containers=true
```

### View Frontend Logs

```bash
# Real-time logs
kubectl logs -n mcp-pdf -l app=mcp-pdf-frontend -f

# Last 50 lines
kubectl logs -n mcp-pdf -l app=mcp-pdf-frontend --tail=50
```

### Check Resource Usage

```bash
# Current resource usage
kubectl top pods -n mcp-pdf
kubectl top nodes

# Persistent monitoring (requires metrics-server)
kubectl describe node
```

### Debug Pod

Execute commands inside a running pod:

```bash
# Get shell access
kubectl exec -it <pod-name> -n mcp-pdf -- /bin/bash

# Check environment variables
kubectl exec <pod-name> -n mcp-pdf -- env | grep -i api

# Check mounted volumes
kubectl exec <pod-name> -n mcp-pdf -- ls -la /app/output/
```

### Monitor HPA Status

```bash
# Watch autoscaler in action
kubectl get hpa -n mcp-pdf --watch

# Detailed HPA status
kubectl describe hpa mcp-pdf-backend-hpa -n mcp-pdf
```

---

## Useful Commands Reference

```bash
# Get all resources in namespace
kubectl get all -n mcp-pdf

# Describe all resources
kubectl describe all -n mcp-pdf

# Get resource YAML
kubectl get deployment mcp-pdf-backend -n mcp-pdf -o yaml

# Edit resources (opens editor)
kubectl edit deployment mcp-pdf-backend -n mcp-pdf

# Scale replicas manually
kubectl scale deployment mcp-pdf-backend --replicas=3 -n mcp-pdf

# Roll back deployment
kubectl rollout undo deployment/mcp-pdf-backend -n mcp-pdf

# Check rollout history
kubectl rollout history deployment/mcp-pdf-backend -n mcp-pdf

# Port forward for testing
kubectl port-forward pod/<pod-name> 8000:8000 -n mcp-pdf

# Copy files from pod
kubectl cp mcp-pdf/<pod-name>:/app/output/logs ./local-logs -n mcp-pdf

# Stream logs from all pods
kubectl logs -n mcp-pdf -f --all-containers=true -l app=mcp-pdf-backend
```

---

## Next Steps

1. **Set up monitoring**: Install Prometheus and Grafana for metrics
2. **Configure CI/CD**: Automate image building and deployment with GitHub Actions
3. **Add SSL/TLS**: Set up cert-manager for automatic certificate management
4. **Database**: If needed, add persistent database (PostgreSQL, MongoDB)
5. **Backups**: Configure volume snapshots for backup and recovery

---

## Support

For more information:
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [kubectl Cheat Sheet](https://kubernetes.io/docs/reference/kubectl/cheatsheet/)
- Check the main [README.md](README.md) for project overview
