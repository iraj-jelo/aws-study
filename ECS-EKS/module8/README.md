### Module 8 — Production EKS: Scaling, Security, and Observability

AWS ECS/EKS course · Module 8 of 9 · Pulumi with Python · Bash commands

### Learning objectives

By the end of this module, you will be able to:

* Scale Kubernetes workloads automatically using the Horizontal Pod Autoscaler (HPA).

* Understand the relationship between pod scaling and cluster-node scaling.

* Compare EKS managed node groups, Cluster Autoscaler, and Karpenter.

* Design workloads for high availability across Availability Zones.

* Perform safe rolling deployments and recover from failed releases.

* Collect Kubernetes logs, metrics, events, and control-plane audit information.

* Apply Kubernetes RBAC, IAM workload identity, Pod Security Standards, and network restrictions.

* Diagnose common production failures involving scheduling, memory, DNS, and VPC IP capacity.

### 1\. Production EKS architecture

A production EKS environment has several cooperating layers. Understanding these layers helps you determine whether a problem belongs to the application, Kubernetes scheduler, worker-node capacity, or AWS infrastructure.

Application traffic

Users → Route 53 → ALB → Kubernetes Service

EKS workload layer

Deployments · Pods · HPA · Readiness/Liveness Probes

AZ A

Worker nodes and application pods

AZ B

Worker nodes and application pods

Infrastructure and operations

Managed node groups / Karpenter · CloudWatch · Prometheus · IAM · VPC

The key distinction is that HPA scales pods, while a node autoscaler provisions or removes worker-node capacity. These mechanisms solve different problems and are commonly used together.

### 2\. Prerequisites and environment

This module continues with the EKS cluster and FastAPI application from the previous modules. The commands use Bash, AWS CLI, `kubectl`, and Helm where needed.

Set the environment variables for your existing cluster:

```bash
export AWS_REGION="eu-west-2"
export CLUSTER_NAME="eks-production"
export APP_NAMESPACE="production"
export APP_NAME="fastapi"
```

Adjust the region, cluster, namespace, and deployment names to match your environment.

Check your tools and AWS identity:

```bash
aws --version
kubectl version --client
helm version
pulumi version

aws sts get-caller-identity

aws eks update-kubeconfig \
  --region "$AWS_REGION" \
  --name "$CLUSTER_NAME"

kubectl get nodes -o wide
kubectl get deployments,services,pods -A
```

If the cluster is not in your current kubeconfig, `update-kubeconfig` configures access; it does not create the cluster.

Install or verify the Metrics Server before working with HPA. EKS clusters do not necessarily have it installed by default.

```bash
kubectl get deployment metrics-server \
  -n kube-system

kubectl top nodes
kubectl top pods -A
```

If the deployment is missing, install Metrics Server using the official Kubernetes add-on manifests or the AWS-supported approach appropriate for your cluster. Verify its compatibility with your Kubernetes version before installing.

### Use the names from Modules 5–7

To keep this lab consistent with the earlier modules, use the existing `aws-containers` project and EKS cluster rather than creating a second cluster.

```bash
export AWS_REGION="eu-west-2"
export CLUSTER_NAME="aws-containers-eks-dev"
export NAMESPACE="applications"
export APP_NAME="fastapi-api"
export ECR_IMAGE_URI="YOUR_ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/fastapi-api:1.0.0"

aws eks update-kubeconfig \
  --region "$AWS_REGION" \
  --name "$CLUSTER_NAME"

kubectl get nodes -o wide
kubectl get deployment "$APP_NAME" -n "$NAMESPACE"
kubectl get pods -n "$NAMESPACE" -o wide
```

The image variable is an example; use the actual ECR URI from your existing deployment. The earlier modules use the `fastapi-api` Deployment, port `8000`, and `/health` endpoint.

### 3\. Workload scaling with the Horizontal Pod Autoscaler

### 3.1 How HPA works

The Horizontal Pod Autoscaler adjusts the number of replicas in a Deployment or another supported scalable resource based on observed metrics.

Incoming application workload

Metrics Server

Provides CPU and memory usage metrics

Horizontal Pod Autoscaler

Compares observed utilization with the target

Deployment replicas increase or decrease

HPA commonly uses CPU utilization relative to the CPU requests configured on containers. For example, a target of 60% means the autoscaler aims for average CPU usage near 60% of the requested CPU across the measured pods.

A simplified calculation is:

\\text{desired replicas} =
\\left\\lceil
\\text{current replicas}
\\times
\\frac{\\text{current utilization}}{\\text{target utilization}}
\\right\\rceil

The real controller also considers missing metrics, scaling behavior, stabilization windows, and other constraints.

### 3.2 Configure resource requests and limits

Create a patch file named `k8s/fastapi-resources.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-api
  namespace: applications
spec:
  template:
    spec:
      containers:
        - name: fastapi-api
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: "500m"
              memory: 512Mi
```

Confirm the actual container name before applying the patch:

```bash
kubectl get deployment fastapi-api \
  -n applications \
  -o jsonpath='{.spec.template.spec.containers[*].name}'

echo
```

If your container has a different name, update the YAML accordingly.

Apply the resource configuration:

```bash
kubectl apply -f k8s/fastapi-resources.yaml
kubectl rollout status deployment/fastapi-api -n applications

kubectl describe deployment fastapi-api -n applications
kubectl top pods -n applications
```

Resource requests influence scheduling and the CPU/memory utilization denominator used by HPA. Limits constrain resource consumption; a CPU limit can cause throttling, while exceeding a container's memory limit can cause an OOM kill.

These values are starting points for this lab, not universal production recommendations. Actual settings should reflect measured application behavior.

### 3.3 Create the HPA

Create `k8s/fastapi-hpa.yaml`:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-api
  namespace: applications
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi-api
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Pods
          value: 2
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 25
          periodSeconds: 60
```

Apply and inspect it:

```bash
kubectl apply -f k8s/fastapi-hpa.yaml

kubectl get hpa -n applications
kubectl describe hpa fastapi-api -n applications
kubectl get hpa fastapi-api -n applications --watch
```

The example allows two to six replicas, scales up by at most two pods per 60-second policy period, and uses a five-minute scale-down stabilization window. HPA reconciliation is not instantaneous, so do not expect every setting to take effect at an exact wall-clock time.

### 3.4 Generate controlled load

One option is to run a temporary load-generator pod using an approved image containing a load-testing utility. For example, using `busybox` with `wget` for basic repeated HTTP requests:

```bash
kubectl run load-generator \
  -n applications \
  --image=busybox:1.36 \
  --restart=Never \
  --command -- sh -c '
    while true; do
      wget -q -O /dev/null \
        http://fastapi-api:8000/health
    done
  '
```

This produces repeated requests but may not create enough CPU load to trigger scaling. A lightweight health endpoint can consume very little CPU. For a meaningful HPA test, use an authorized load-testing tool and a controlled application endpoint that performs enough computation to generate measurable CPU usage.

Watch the replicas and resource metrics:

```bash
kubectl get hpa,pods -n applications --watch
```

When finished, stop the generator:

```bash
kubectl delete pod load-generator \
  -n applications \
  --ignore-not-found
```

Important: HPA scaling only changes the desired number of pods. It does not guarantee that the cluster has enough worker-node capacity to schedule them.

### 4\. Node scaling: managed node groups, Cluster Autoscaler, and Karpenter

### 4.1 The difference between pod and node scaling

Suppose HPA increases your Deployment from two replicas to six. If the available nodes cannot fit the four additional pods, those pods may remain `Pending`.

The cluster needs a second scaling mechanism to add capacity.

| Mechanism              | Responsibility                                                                                        |
| ---------------------- | ----------------------------------------------------------------------------------------------------- |
| HPA                    | Adjusts the number of application replicas                                                            |
| EKS managed node group | Manages a configured group of EC2 worker nodes                                                        |
| Cluster Autoscaler     | Adjusts node-group size in response to unschedulable pods and utilization                             |
| Karpenter              | Provisions and consolidates compatible nodes based on workload requirements and cluster configuration |

### 4.2 Managed node group scaling

Check your existing node groups:

```bash
aws eks list-nodegroups \
  --cluster-name "$CLUSTER_NAME" \
  --region "$AWS_REGION"

aws eks describe-nodegroup \
  --cluster-name "$CLUSTER_NAME" \
  --nodegroup-name YOUR_NODEGROUP_NAME \
  --region "$AWS_REGION" \
  --query 'nodegroup.scalingConfig'
```

For the lab, inspect the minimum, desired, and maximum sizes before changing them. Your earlier cluster used a managed EC2 node group with two `t3.medium` nodes.

Node-group scaling configuration can be managed through Pulumi. For example, in the component that defines your existing managed node group, the configuration can be parameterized as follows:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

min_size = config.get_int("nodeMinSize") or 2
desired_size = config.get_int("nodeDesiredSize") or 2
max_size = config.get_int("nodeMaxSize") or 4

# Apply these values to the existing aws.eks.NodeGroup
# scaling_config, rather than creating a duplicate node group.
```

Use these values in the existing node-group resource's `scaling_config`:

```python
scaling_config=aws.eks.NodeGroupScalingConfigArgs(
    min_size=min_size,
    desired_size=desired_size,
    max_size=max_size,
)
```

The snippet illustrates the configuration; integrate it into your existing `aws.eks.NodeGroup` definition rather than adding a second node group. When changing the size of a node group managed by Cluster Autoscaler, coordinate with its ownership of the desired size to avoid conflicting changes.

### 4.3 Cluster Autoscaler versus Karpenter

Cluster Autoscaler

* Primarily changes the size of existing node groups.

* Fits well with managed node groups and established instance-type choices.

* Requires correct node-group discovery, IAM permissions, and scaling limits.

* Can be less flexible when workloads need a wide range of instance types.

Karpenter

* Provisions nodes based on pending pod requirements and configured scheduling constraints.

* Supports flexible instance selection, subject to NodePool requirements, EC2 availability, quotas, and configured limits.

* Can consolidate underutilized capacity and improve utilization.

* Requires careful configuration of IAM, networking, instance discovery, disruption, and capacity limits.

Do not install both node autoscalers without a deliberate capacity-management design. In particular, avoid having multiple controllers compete to manage the same node-group capacity.

For this module, first understand and test HPA with your existing managed node group. Treat Karpenter as a separate advanced configuration rather than installing it into the existing cluster without checking its current node-management setup.

### 5\. High availability and disruption management

Production workloads must tolerate pod restarts, node maintenance, and individual Availability Zone disruptions as far as the architecture allows.

### 5.1 Pod topology spread

Kubernetes topology spread constraints help distribute replicas across nodes or zones. They do not create additional nodes or guarantee that all zones have available capacity.

Create `k8s/fastapi-availability.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi-api
  namespace: applications
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fastapi-api
  template:
    metadata:
      labels:
        app: fastapi-api
    spec:
      topologySpreadConstraints:
        - maxSkew: 1
          topologyKey: topology.kubernetes.io/zone
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: fastapi-api
        - maxSkew: 1
          topologyKey: kubernetes.io/hostname
          whenUnsatisfiable: ScheduleAnyway
          labelSelector:
            matchLabels:
              app: fastapi-api
      containers:
        - name: fastapi-api
          image: REPLACE_WITH_YOUR_ECR_IMAGE_URI
          ports:
            - name: http
              containerPort: 8000
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 15
            periodSeconds: 20
          resources:
            requests:
              cpu: 100m
              memory: 128Mi
            limits:
              cpu: "500m"
              memory: 512Mi
```

This is a complete Deployment example. Replace the image placeholder with the existing ECR URI before applying it. It deliberately keeps the topology constraints soft (`ScheduleAnyway`) so the scheduler can still place pods if ideal distribution is unavailable. Use stricter scheduling only when the cluster has enough capacity and the desired availability policy requires it.

If you prefer to preserve your existing Deployment's configuration, merge the `topologySpreadConstraints` and probe settings into its existing manifest rather than replacing the whole resource.

### 5.2 Pod Disruption Budgets

A Pod Disruption Budget (PDB) limits how many matching pods can be voluntarily disrupted at once, such as during node draining.

Create `k8s/fastapi-pdb.yaml`:

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: fastapi-api
  namespace: applications
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: fastapi-api
```

Apply and inspect it:

```bash
kubectl apply -f k8s/fastapi-pdb.yaml

kubectl get pdb -n applications
kubectl describe pdb fastapi-api -n applications
```

This PDB requires at least one matching pod to remain available during supported voluntary disruptions. It does not protect against every failure, including sudden node loss, application crashes, or all pods being unavailable simultaneously.

A PDB can also prevent a node drain from completing if there is insufficient healthy replacement capacity. Check its status before planned maintenance.

### 5.3 Readiness, liveness, and startup probes

* Readiness probe: determines whether a pod should receive Service traffic.

* Liveness probe: determines whether Kubernetes should restart a container.

* Startup probe: gives slow-starting applications additional time before liveness checks begin.

Avoid using an expensive external dependency check as a liveness probe. A temporary database outage, for example, should not necessarily trigger continuous application restarts.

For a FastAPI service, `/health` should be lightweight and consistent with the health-check semantics you want. If the application has separate liveness and readiness requirements, expose distinct endpoints.

### 6\. Safe deployments and rollback

Kubernetes Deployments support rolling updates, allowing new pods to become ready while old pods are gradually replaced.

Inspect the current rollout:

```bash
kubectl rollout status deployment/fastapi-api \
  -n applications

kubectl rollout history deployment/fastapi-api \
  -n applications

kubectl get deployment fastapi-api \
  -n applications \
  -o yaml
```

A Deployment can use settings like these:

```yaml
spec:
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 0
      maxSurge: 1
```

These settings allow one extra pod during an update and aim to keep all desired replicas available. The cluster needs sufficient spare capacity to accommodate that extra pod.

To update the application image:

```bash
export NEW_IMAGE="YOUR_ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/fastapi-api:1.1.0"

kubectl set image deployment/fastapi-api \
  fastapi-api="$NEW_IMAGE" \
  -n applications

kubectl rollout status deployment/fastapi-api \
  -n applications
```

If the rollout fails:

```bash
kubectl rollout status deployment/fastapi-api \
  -n applications --timeout=180s || true

kubectl describe deployment fastapi-api -n applications
kubectl get pods -n applications
kubectl get events -n applications --sort-by=.lastTimestamp

kubectl rollout undo deployment/fastapi-api \
  -n applications

kubectl rollout status deployment/fastapi-api \
  -n applications
```

`kubectl rollout undo` restores a previous Deployment revision. It does not reverse database migrations, undo external side effects, or guarantee that a previously used image remains available in ECR. Immutable image tags and backward-compatible database changes make rollback safer.

### 7\. Observability: metrics, logs, and events

Production observability combines three different kinds of evidence:

| Signal  | Answers                                       | Typical source                           |
| ------- | --------------------------------------------- | ---------------------------------------- |
| Metrics | What is changing over time?                   | Metrics Server, CloudWatch, Prometheus   |
| Logs    | What did the application or component report? | Container stdout/stderr, CloudWatch Logs |
| Events  | What did Kubernetes observe or reject?        | Kubernetes Events, kubectl describe      |

### 7.1 Kubernetes events and pod inspection

```bash
kubectl get events -A \
  --sort-by=.lastTimestamp

kubectl get pods -n applications -o wide

kubectl describe deployment fastapi-api \
  -n applications

kubectl describe pods -n applications

kubectl logs deployment/fastapi-api \
  -n applications --all-pods=true --tail=100
```

For a crashing pod:

```bash
kubectl get pods -n applications

kubectl logs POD_NAME \
  -n applications --previous

kubectl describe pod POD_NAME \
  -n applications
```

`--previous` retrieves logs from the previous terminated container instance when available.

### 7.2 Enable EKS control-plane logs

EKS control-plane logging is configured at the cluster level and can send supported control-plane log types to CloudWatch Logs.

Inspect the current configuration:

```bash
aws eks describe-cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --query 'cluster.logging.clusterLogging'
```

Enable the commonly useful API, audit, authenticator, controller-manager, and scheduler logs:

```bash
aws eks update-cluster-config \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --logging '{
    "clusterLogging": [
      {
        "types": [
          "api",
          "audit",
          "authenticator",
          "controllerManager",
          "scheduler"
        ],
        "enabled": true
      }
    ]
  }'
```

Check the update status:

```bash
aws eks describe-update \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --update-id YOUR_UPDATE_ID
```

Use the update ID returned by the preceding command. Control-plane logs can incur CloudWatch ingestion and retention costs; enable only the log types that support your operational and security requirements.

### 7.3 CloudWatch Container Insights

Container Insights can provide aggregated metrics and dashboards for cluster, node, pod, and container performance. Its setup depends on the EKS observability configuration and installed components.

Before installing or upgrading monitoring components:

* Check whether the CloudWatch Observability EKS add-on is already installed.

* Review its compatibility with the cluster's Kubernetes version.

* Confirm the required IAM permissions or workload identity configuration.

* Decide which metrics and logs to collect and how long to retain them.

Inspect installed add-ons:

```bash
aws eks list-addons \
  --cluster-name "$CLUSTER_NAME" \
  --region "$AWS_REGION"

kubectl get pods -n amazon-cloudwatch
```

If the CloudWatch Observability add-on is absent, follow the current AWS installation procedure for your cluster. Avoid blindly reinstalling an existing logging agent, as duplicate collection can increase costs and complicate troubleshooting.

### 7.4 Prometheus and Grafana

Prometheus-compatible metrics are useful when you need application-specific measurements, request latency, throughput, error rates, and custom business metrics. Grafana provides dashboards and can visualize metrics from Prometheus-compatible sources, CloudWatch, and other supported data sources.

A practical production design should establish:

* Metrics for request rate, errors, and latency.

* Kubernetes metrics for pod readiness, restarts, CPU, memory, and scheduling.

* Alerts for sustained error rates, resource exhaustion, and insufficient replicas.

* Retention and access policies for monitoring data.

For AWS-managed monitoring, Amazon Managed Service for Prometheus and Amazon Managed Grafana are options. A self-managed Prometheus/Grafana deployment is another choice, but requires operating the monitoring stack itself.

### 8\. Security hardening

### 8.1 Kubernetes RBAC

Kubernetes RBAC controls what authenticated users and service accounts can do through the Kubernetes API. AWS IAM and Kubernetes RBAC are related but distinct authorization layers.

Inspect existing permissions:

```bash
kubectl get roles,rolebindings -n applications
kubectl get clusterroles,clusterrolebindings
kubectl auth can-i list pods -n applications
kubectl auth can-i create deployments -n applications
```

For an application service account that only needs to read its own namespace's pod information, use a narrowly scoped Role rather than granting cluster-admin privileges.

Create `k8s/readonly-role.yaml`:

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: fastapi-reader
  namespace: applications
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: applications
rules:
  - apiGroups: [""]
    resources: ["pods"]
    verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: fastapi-reader-pod-reader
  namespace: applications
subjects:
  - kind: ServiceAccount
    name: fastapi-reader
    namespace: applications
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: Role
  name: pod-reader
```

Apply and verify:

```bash
kubectl apply -f k8s/readonly-role.yaml

kubectl auth can-i list pods \
  --as=system:serviceaccount:applications:fastapi-reader \
  -n applications

kubectl auth can-i delete pods \
  --as=system:serviceaccount:applications:fastapi-reader \
  -n applications
```

Expected results are `yes` for listing pods and `no` for deleting them. The impersonation check requires your own Kubernetes identity to have permission to impersonate the service account.

### 8.2 IAM workload identity

Avoid giving application pods broad permissions through the worker-node IAM role.

For workloads that access AWS services, use EKS Pod Identity or IRSA, depending on your cluster setup and compatibility requirements.

The intended separation is:

* Node role: permissions required by the worker node and its infrastructure components.

* Pod identity role: permissions required by a specific application workload.

* Human or CI/CD identity: permissions to administer the cluster and deploy applications.

For the `fastapi-api` workload, grant only the AWS API permissions the application actually needs. For example, S3 access should be limited to the intended bucket and operations, rather than using `s3:*` on all resources.

### 8.3 Pod Security Standards

Pod Security Standards provide baseline security profiles for Kubernetes workloads. The `restricted` profile is a useful target for compatible application containers, but it may require changes to applications that expect elevated privileges or writable root filesystems.

Start by auditing the namespace:

```bash
kubectl label namespace applications \
  pod-security.kubernetes.io/audit=restricted \
  --overwrite

kubectl label namespace applications \
  pod-security.kubernetes.io/warn=restricted \
  --overwrite
```

These labels request audit and warning enforcement behavior; they do not enforce rejection of violating pods. Review the warnings and remediate incompatible workloads before enabling enforcement.

For a compatible workload, security settings may include:

```yaml
securityContext:
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault
containers:
  - name: fastapi-api
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop:
          - ALL
```

Merge these settings into the existing pod specification. Confirm that the image supports running as a non-root user and that the application can write to any required directories.

### 8.4 Network isolation and image security

Use NetworkPolicies to restrict pod-to-pod communication when your cluster's networking implementation supports enforcing them. The existence of a NetworkPolicy object alone does not guarantee enforcement.

For image security:

* Prefer immutable image digests or controlled immutable tags.

* Scan ECR images and review vulnerability findings.

* Rebuild images when base-image vulnerabilities are fixed.

* Run containers as non-root where practical.

* Avoid baking secrets into images or container environment defaults.

* Use Secrets Manager or another approved secret-management solution for sensitive configuration.

### 9\. Troubleshooting production failures

The following commands cover frequent EKS problems.

### Case 1 — Pods remain Pending

Likely causes: insufficient CPU/memory, node selectors, affinity constraints, taints, or storage binding.

```bash
kubectl get pods -n applications -o wide
kubectl describe pod POD_NAME -n applications
kubectl get nodes
kubectl describe nodes
```

Check scheduler events for `Insufficient cpu`, `Insufficient memory`, untolerated taints, or volume-binding failures. If HPA has already increased replicas, verify whether the node autoscaler can provision compatible capacity.

### Case 2 — CrashLoopBackOff or OOMKilled

Likely causes: application exceptions, startup errors, memory pressure, or an incorrect probe.

```bash
kubectl logs POD_NAME -n applications --previous
kubectl describe pod POD_NAME -n applications
kubectl top pods -n applications
```

Inspect termination reasons, exit codes, resource limits, and probe failures before changing replica counts.

### Case 3 — Service or DNS failures

Likely causes: incorrect selectors, missing endpoints, DNS issues, or blocked traffic.

```bash
kubectl get svc,endpointslices -n applications
kubectl get pods --show-labels -n applications
kubectl get pods -n kube-system
kubectl get events -n applications --sort-by=.lastTimestamp
```

Verify that Service selectors match pod labels, that ready endpoints exist, and that DNS and network policies permit the intended connection.

### Case 4 — VPC IP exhaustion

Likely causes: subnet address exhaustion, VPC CNI allocation behavior, or too many pod IPs for available subnet capacity.

```bash
kubectl get nodes -o wide
kubectl describe nodes
kubectl get pods -A -o wide
```

Check subnet free IP addresses, VPC CNI logs, ENI allocation, and applicable instance networking limits. Adding a node is not always sufficient if the subnet itself has no free addresses.

### Case 5 — HPA cannot scale

Likely causes: unavailable metrics, missing CPU requests, or capacity constraints.

```bash
kubectl describe hpa fastapi-api -n applications
kubectl top pods -n applications
kubectl get apiservices
kubectl get events -n applications --sort-by=.lastTimestamp
```

Resolve missing metrics first. Then determine whether the desired replicas are being scheduled and whether a node autoscaler is configured to provide the required capacity.

### 10\. Lab — Operate and scale the EKS application

This lab combines HPA, high availability, observability, security, and troubleshooting using the existing `aws-containers` infrastructure.

### Lab A — Establish a baseline

* Confirm the EKS cluster and `applications` namespace.

* Verify the `fastapi-api` Deployment, Service, and running pods.

* Check Metrics Server availability and inspect CPU/memory metrics.

* Record the initial replica count and node placement.

```bash
kubectl get nodes -o wide
kubectl get deployment,service,hpa,pdb -n applications
kubectl top nodes
kubectl top pods -n applications
```

### Lab B — Enable workload scaling and availability

* Configure CPU and memory requests and limits.

* Create the HPA with a two-to-six replica range.

* Add topology spread constraints and appropriate health probes.

* Create a PDB and inspect its status.

* Generate controlled load and observe HPA behavior.

```bash
kubectl apply -f k8s/fastapi-resources.yaml
kubectl apply -f k8s/fastapi-hpa.yaml
kubectl apply -f k8s/fastapi-availability.yaml
kubectl apply -f k8s/fastapi-pdb.yaml

kubectl get hpa,pdb -n applications
kubectl get pods -n applications -o wide
```

If you apply the complete availability Deployment manifest, ensure its image and container configuration match the existing application before doing so.

### Lab C — Configure observability

* Inspect application logs, pod events, and resource metrics.

* Enable appropriate EKS control-plane log types.

* Verify the CloudWatch observability configuration.

* Identify metrics and alert conditions for unhealthy pods, CPU pressure, and insufficient replicas.

### Lab D — Test recovery

* Deploy a new immutable application image.

* Inspect the rollout and confirm that new pods become ready.

* Perform a controlled rollback to a previous healthy revision.

* Investigate a deliberately misconfigured probe in a non-production test Deployment.

* Diagnose a scheduling failure using pod events and resource requests.

Avoid deliberately disrupting your only production workload. Use a separate test Deployment or non-production environment for failure simulation.

### Lab E — Review security

* Verify that application permissions are scoped to the required AWS resources.

* Check Kubernetes RBAC and service-account permissions.

* Audit Pod Security Standard warnings.

* Review image scanning, container security contexts, and network restrictions.

### Lab F — Review infrastructure and cleanup

Keep node-group definitions, IAM policies, add-ons, and other AWS resources managed by Pulumi wherever practical. Use `pulumi preview` before changing infrastructure and inspect the proposed operations before applying them.

```bash
cd infrastructure

pulumi stack
pulumi preview
```

Do not run `pulumi destroy` against the shared course environment just to clean up this module. The EKS cluster and its resources are reused in the next module. Remove only temporary resources created specifically for this lab.

### Module 8 — Completion criteria

You have completed this module when you can explain and demonstrate:

* The difference between pod autoscaling and node autoscaling.

* How resource requests influence scheduling and CPU-based HPA decisions.

* How topology spread constraints and PDBs contribute to availability.

* How to detect and recover from an unsuccessful rolling deployment.

* How Kubernetes events, CloudWatch logs, and metrics support troubleshooting.

* How IAM, Kubernetes RBAC, Pod Security Standards, and network controls provide separate security boundaries.

* How to identify common EKS scheduling, memory, DNS, and IP-capacity failures.

The next module is Module 9 — Capstone: ECS and EKS Production Deployment Strategy, where you will compare both orchestration platforms using Pulumi, ECR, application health checks, observability, and deployment workflows.
