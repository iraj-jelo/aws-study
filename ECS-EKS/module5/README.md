### Module 5 — Kubernetes Fundamentals and Amazon EKS Architecture

AWS ECS/EKS Course · Module 5 of 9 · Pulumi Python · Bash

In this module, we'll move from Amazon ECS to Kubernetes and Amazon EKS. We'll reuse the existing `aws-containers` project and the FastAPI image published to ECR in the previous modules, rather than rebuilding the application or introducing a different stack.

The goal is to provision an EKS cluster with Pulumi, configure access securely, deploy FastAPI using native Kubernetes resources, and learn how to inspect and troubleshoot the workload.

### Learning objectives

By the end of this module, you'll be able to:

* Explain the Kubernetes control plane and worker-node architecture.

* Distinguish EKS managed node groups from Fargate profiles.

* Understand Pods, Deployments, ReplicaSets, Services, and Namespaces.

* Configure Kubernetes resources using YAML manifests.

* Provision an EKS cluster and managed node group using Pulumi.

* Configure AWS IAM authentication and Kubernetes RBAC.

* Understand the Amazon VPC CNI and basic EKS networking.

* Configure resource requests, limits, and health probes.

* Inspect application health, events, logs, and node placement using `kubectl`.

### 1\. Kubernetes architecture

Kubernetes is a container orchestration platform that continuously works to make the actual state of your applications match the desired state you've declared.

For example, if you declare that your application should have two replicas, Kubernetes attempts to keep two healthy replicas running. If a Pod fails, Kubernetes can create a replacement.

![Medium](https://images.openai.com/static-rsc-4/C3sdNZB86KrYDlGbuCymh7bQNnxVRRHacPyATgIRMbW7w7pECs0ZL8KAyJO_bY3UWZxjhcLLOemLNpFPh0tG1p2H26HrNoOQe7WDkHsmx5AiEZ95QwNAkTbjmMr5-wOijG86IG9gGvq_d7c4A8AfqbjYx-0TH0ImxTPVbfIsx1oMUlRs2j63ZvrTCUjbL4Fn?purpose=fullsize)

### 1.1 The control plane

The control plane manages the cluster and makes decisions about workload placement and cluster state.

| Component          | Responsibility                                            |
| ------------------ | --------------------------------------------------------- |
| API server         | Exposes the Kubernetes API and validates requests.        |
| Scheduler          | Selects suitable nodes for unscheduled Pods.              |
| Controller manager | Runs controllers that reconcile desired and actual state. |
| etcd               | Stores Kubernetes cluster state and configuration.        |

In Amazon EKS, AWS operates the Kubernetes control plane, including its highly available managed infrastructure. You interact with it through Kubernetes APIs, primarily using `kubectl` and automation tools.

You generally do not manage the EKS control-plane hosts or their etcd instances yourself.

### 1.2 Worker nodes

Worker nodes provide the compute capacity on which your Pods run.

On EC2-backed EKS, important node components include:

* kubelet: Ensures Pods assigned to the node are running as specified.

* Container runtime: Pulls images and runs containers, typically containerd.

* Networking components: Provide Pod networking and Kubernetes service connectivity. EKS commonly uses the Amazon VPC CNI for Pod networking.

With a managed node group, AWS manages the underlying EC2 Auto Scaling group and integrates node lifecycle operations with EKS. You still need to consider node configuration, capacity, updates, and workload scheduling.

### 1.3 What happens when you deploy an application?

* You submit a Deployment manifest to the API server.

* Kubernetes stores the desired state.

* The Deployment controller creates or updates a ReplicaSet.

* The ReplicaSet ensures the desired number of Pods exists.

* The scheduler assigns unscheduled Pods to appropriate nodes.

* The kubelet on each selected node starts the containers.

* Health probes and controllers help maintain the intended state.

The important distinction is that a Deployment describes the desired state; it does not directly start containers on a particular machine.

### 2\. Amazon EKS compute options

EKS provides the Kubernetes control plane, while you choose how workloads obtain compute capacity.

![Amazon EKS (Elastic Kubernetes Service) architecture on AWS | by casimirrex antony | Medium](https://images.openai.com/static-rsc-4/nnXW1XtTaIBRKFxFY4QWXzEa6of1Q1E8Io4EpdIQ-L1U-NRyqtXUi0YzomdtIx2Ndkz8lLPPmaddRSr-h-eOFVR4PMB9JcX8x7GNCMroRhb_QQsk9pp7lal4bHHws_YyT0fF_e-6AHeVNhE_swO4xFL5e_uhGNHy8TgaAYpXjgcwc3M6Rm4vmNEghzuXk98B?purpose=fullsize)

Managed node groups

Run Kubernetes workloads on EC2 instances. AWS integrates node provisioning, Auto Scaling group management, and managed node updates with EKS.

Best fit for this module's lab: a general-purpose EC2-backed cluster.

![Amazon Elastic Kubernetes Service - Overview of Deployment Options on AWS](https://images.openai.com/static-rsc-4/oLcSd8f5pUHEGQwqJQMUuKaMOOhfBbP3SuN0nHCjxYlkCJDaY-2ySE5fi8-C7JhLjH623mwqjB3vIReSZfPpY2vzvsljS79ObEguv2TUftTl-ijefMv7BOskgZyUQ3cX3bD2zkxdqhywsdm__-G0ja6IaP1RIyos6Q9LPu3A7rJkJ0d6qmqDJHK9c8jAH5f_?purpose=fullsize)

Fargate profiles

Allow eligible Pods to run on AWS-managed serverless compute according to namespace and label selectors. You don't manage worker EC2 instances.

Useful when you want to avoid managing worker nodes, subject to Fargate's workload and Kubernetes feature limitations.

For this module, we'll use a managed node group. It makes node placement, resource allocation, and troubleshooting easier to observe. Fargate profiles will be covered conceptually and can be explored separately later.

### 3\. Core Kubernetes resources

Kubernetes resources are API objects that describe applications, configuration, networking, and access.

| Resource   | Purpose                                                                                               |
| ---------- | ----------------------------------------------------------------------------------------------------- |
| Pod        | Smallest deployable unit; contains one or more closely coupled containers.                            |
| Deployment | Manages stateless application rollouts and desired replicas.                                          |
| ReplicaSet | Maintains the requested number of matching Pods; normally managed by a Deployment.                    |
| Service    | Provides a stable network endpoint for a group of Pods.                                               |
| Namespace  | Groups resources within a cluster.                                                                    |
| ConfigMap  | Stores non-sensitive configuration.                                                                   |
| Secret     | Holds sensitive configuration data, although additional encryption and access controls are important. |

### 3.1 Pod and Deployment

A Pod wraps one or more containers and provides them with shared networking and storage context. Pods are replaceable; you should not treat a Pod's IP address or lifetime as permanent.

A Deployment manages the desired number of application replicas and supports controlled updates.

For example, a Deployment with two replicas could create two FastAPI Pods. If one Pod fails, the controllers work toward restoring the replica count.

### 3.2 Service

Pod IP addresses can change when Pods are replaced. A Kubernetes Service provides a stable way to reach matching Pods.

* `ClusterIP`: Internal access within the cluster.

* `NodePort`: Exposes a port on cluster nodes.

* `LoadBalancer`: Requests an external or internal load-balancing integration, depending on the environment.

In this module, we'll use a `ClusterIP` Service. It will make the application reachable inside the cluster without exposing it directly to the public internet. Public-facing ALB ingress is the focus of Module 6.

### 3.3 Labels, selectors, and annotations

Labels are key-value pairs used to identify and group resources. Selectors use those labels to find matching objects.

Annotations store additional metadata that tools and controllers may use.

For example, a Deployment might label Pods with `app: fastapi-api`, and its Service can select Pods with the same label. If these labels don't match, the Service may have no endpoints even though the Pods are running.

### 3.4 ConfigMaps and Secrets

A ConfigMap is appropriate for non-sensitive values such as application settings. Kubernetes Secrets are intended for sensitive values, but base64 encoding alone is not encryption.

For production, configure appropriate IAM permissions, Kubernetes RBAC, encryption at rest, and controlled access to secrets. AWS Secrets Manager integration will be covered as part of the broader course.

### 4\. EKS authentication and authorization

EKS access involves two related but distinct decisions.

* Authentication: Who are you? AWS IAM credentials identify the caller.

* Authorization: What are you allowed to do? EKS access policies and Kubernetes RBAC determine the permitted operations.

### 4.1 Configure the AWS CLI

Use the same AWS account and region as the previous modules (`eu-west-2` in our example).

```bash
aws sts get-caller-identity

aws configure list

aws eks list-clusters --region eu-west-2
```

The first command verifies the identity associated with your current AWS credentials. It does not, by itself, prove that the identity has permission to administer an EKS cluster.

### 4.2 EKS access entries and RBAC

Modern EKS clusters can use access entries to associate IAM identities with cluster access. EKS access policies can grant Kubernetes permissions, while Kubernetes RBAC uses `Role`, `ClusterRole`, `RoleBinding`, and `ClusterRoleBinding` objects to control authorization.

Avoid assuming that IAM authentication alone grants administrative access. The identity must also have appropriate cluster access and permissions.

After creating the cluster, update your local kubeconfig:

```bash
aws eks update-kubeconfig \
  --region eu-west-2 \
  --name aws-containers-eks-dev
```

Verify the active context and API connectivity:

```bash
kubectl config current-context
kubectl cluster-info
kubectl get nodes
kubectl get namespaces
```

If access is denied, check the AWS identity, EKS access configuration, and Kubernetes authorization rather than immediately granting administrator permissions.

### 5\. EKS networking and resource management

### 5.1 Amazon VPC CNI

EKS commonly uses the Amazon VPC CNI to provide network connectivity for Kubernetes Pods. In its standard configuration, Pods receive IP addresses from the VPC address space.

This has several consequences:

* VPC subnet address capacity can limit how many Pods you can schedule.

* Instance types and networking configuration affect Pod density.

* Security groups and routing affect communication between workloads and external services.

* Private-subnet workloads need appropriate outbound connectivity to reach external endpoints when required.

For production deployments, consider subnet sizing, IP address consumption, and the placement of nodes across Availability Zones.

### 5.2 Resource requests and limits

Kubernetes uses resource requests and limits to manage CPU and memory allocation.

| Setting        | Meaning                                                                         |
| -------------- | ------------------------------------------------------------------------------- |
| CPU request    | CPU amount used when scheduling a Pod and allocating resources.                 |
| CPU limit      | Upper bound on CPU usage; containers can be throttled.                          |
| Memory request | Memory amount considered when scheduling a Pod.                                 |
| Memory limit   | Memory usage boundary; exceeding it can result in an out-of-memory termination. |

Requests should reflect the workload's normal requirements, while limits should account for realistic peaks and application behavior.

### 5.3 Health probes

Kubernetes provides three useful probe types:

* Startup probe: Determines whether an application has completed startup.

* Readiness probe: Determines whether a container should receive application traffic.

* Liveness probe: Determines whether a container should be restarted.

A readiness failure does not automatically mean the container needs restarting. A liveness failure can trigger a restart. This distinction is important for applications that take time to initialize or depend on temporary external services.

### Lab — Provision EKS and deploy FastAPI with Pulumi

### Lab overview

Project

`aws-containers`

Pulumi stack

`dev`

AWS region

`eu-west-2`

Application port

`8000`

Architecture: Pulumi provisions an EKS cluster and managed EC2 node group. Kubernetes Deployments and Services run the existing FastAPI image from ECR.

### 6\. Lab prerequisites

Make sure these tools are installed and available in your Bash environment:

* AWS CLI

* Pulumi CLI

* Python and `venv`

* `kubectl`

* Docker, if you need to inspect or rebuild the image

* Valid AWS credentials with permission to create EKS, EC2, IAM, networking, and related resources

The cluster and worker nodes incur AWS charges. We'll use a small managed node group and clean up the resources at the end.

### 6.1 Verify the previous lab's image

The application from the earlier modules uses the ECR repository `fastapi-api`, image tag `1.0.0`, port `8000`, and `/health` endpoint.

```bash
export AWS_REGION="eu-west-2"
export CLUSTER_NAME="aws-containers-eks-dev"
export ECR_REPOSITORY="fastapi-api"
export IMAGE_TAG="1.0.0"

export AWS_ACCOUNT_ID="$(
  aws sts get-caller-identity \
    --query Account \
    --output text
)"

export IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:${IMAGE_TAG}"

aws ecr describe-images \
  --region "$AWS_REGION" \
  --repository-name "$ECR_REPOSITORY" \
  --image-ids imageTag="$IMAGE_TAG"
```

If the image tag does not exist, return to Module 2 and publish the image before continuing.

### 7\. Create the Pulumi EKS project

We'll use Pulumi's EKS component package to provision the cluster and its managed node group, and Pulumi's Kubernetes provider to deploy the application. This keeps AWS infrastructure and Kubernetes workload definitions in the same Python-based infrastructure project. Pulumi Registry +1

From the root of the existing `aws-containers` project:

```bash
cd aws-containers/infrastructure

pulumi stack select dev

mkdir -p components/eks
```

Install the dependencies in the infrastructure project's Python environment:

```bash
source .venv/bin/activate

pip install pulumi-eks pulumi-kubernetes
```

If the project uses a different virtual environment path, activate that environment instead. Record the final package versions in the project's `requirements.txt` so the infrastructure can be reproduced.

Add the EKS dependencies to `requirements.txt` if they're not already present:

```text
pulumi-aws
pulumi-eks
pulumi-kubernetes
```

Preserve the other dependencies required by your existing project.

Configure the stack:

```bash
pulumi config set aws:region eu-west-2
pulumi config set imageUri "$IMAGE_URI"
```

The `imageUri` configuration stores the image reference used by the Kubernetes Deployment. Ensure the value is saved in your Pulumi stack configuration before moving to the next step.

### 8\. Define the EKS cluster and Kubernetes resources

Create or replace `infrastructure/components/eks/__init__.py` with the following component. It defines an EKS cluster, a two-node managed node group, a Kubernetes provider, a FastAPI Deployment, and an internal Service.

```python

import pulumi
import pulumi_eks as eks
import pulumi_kubernetes as k8s

config = pulumi.Config()
image_uri = config.require("imageUri")

# Create the EKS cluster and its default managed node group.
cluster = eks.Cluster(
    "aws-containers-eks",
    name="aws-containers-eks-dev",
    desired_capacity=2,
    min_size=2,
    max_size=2,
    instance_type="t3.medium",
    skip_default_node_group=False,
    tags={
        "Project": "aws-containers",
        "Environment": "dev",
    },
)

# Explicitly bind Kubernetes resources to this cluster.
k8s_provider = k8s.Provider(
    "aws-containers-k8s-provider",
    kubeconfig=cluster.kubeconfig,
)

labels = {"app": "fastapi-api"}

# Deploy the existing ECR image.
app = k8s.apps.v1.Deployment(
    "fastapi-api",
    metadata={
        "name": "fastapi-api",
    },
    spec={
        "replicas": 2,
        "selector": {"matchLabels": labels},
        "strategy": {
            "type": "RollingUpdate",
            "rollingUpdate": {
                "maxSurge": 1,
                "maxUnavailable": 0,
            },
        },
        "template": {
            "metadata": {"labels": labels},
            "spec": {
                "containers": [{
                    "name": "fastapi-api",
                    "image": image_uri,
                    "ports": [{
                        "name": "http",
                        "containerPort": 8000,
                    }],
                    "resources": {
                        "requests": {
                            "cpu": "100m",
                            "memory": "128Mi",
                        },
                        "limits": {
                            "cpu": "500m",
                            "memory": "256Mi",
                        },
                    },
                    "readinessProbe": {
                        "httpGet": {
                            "path": "/health",
                            "port": 8000,
                        },
                        "initialDelaySeconds": 5,
                        "periodSeconds": 10,
                    },
                    "livenessProbe": {
                        "httpGet": {
                            "path": "/health",
                            "port": 8000,
                        },
                        "initialDelaySeconds": 15,
                        "periodSeconds": 20,
                    },
                }],
            },
        },
    },
    opts=pulumi.ResourceOptions(
        provider=k8s_provider,
        depends_on=[cluster],
    ),
)

# Provide stable internal access to the FastAPI Pods.
service = k8s.core.v1.Service(
    "fastapi-api-service",
    metadata={
        "name": "fastapi-api",
    },
    spec={
        "type": "ClusterIP",
        "selector": labels,
        "ports": [{
            "name": "http",
            "port": 8000,
            "targetPort": 8000,
        }],
    },
    opts=pulumi.ResourceOptions(provider=k8s_provider),
)

pulumi.export("cluster_name", cluster.eks_cluster.name)
pulumi.export("kubeconfig", cluster.kubeconfig)
pulumi.export("deployment_name", app.metadata["name"])
pulumi.export("service_name", service.metadata["name"])
pulumi.export("service_type", service.spec["type"])
```

This uses the Pulumi EKS component's default node group. Review the component's current Python API and version-specific defaults before deployment; the intended result is an EC2-backed managed node group, not an EKS Fargate profile. Pulumi Registry +1

Now create `infrastructure/__main__.py` or update it to import the component:

```python

import components.eks  # noqa: F401
```

If your existing `__main__.py` already provisions resources from other modules, preserve those imports and add the EKS component rather than replacing the entire file.

### 8.1 Understand the important configuration

* `desired_capacity=2` requests two worker nodes initially.

* `min_size=2` and `max_size=2` keep the node group's configured size fixed for this lab.

* `instance_type="t3.medium"` specifies the worker instance type.

* `replicas=2` requests two FastAPI Pods.

* The Deployment's label selector must match the Pod template labels.

* The Service selector must match the same labels.

* Resource requests and limits define the Pod's CPU and memory requirements and boundaries.

* Readiness and liveness probes use the existing `/health` endpoint.

Two Pods do not guarantee that each Pod runs on a different node. The scheduler places Pods according to resource availability and scheduling constraints. We'll inspect actual placement later.

### 9\. Preview and deploy

Review the proposed infrastructure changes first:

```bash
pulumi preview
```

Check the proposed cluster, node group, IAM resources, and networking changes. This component may create supporting resources such as a VPC, depending on its configuration and package version.

If the preview matches your intended deployment, apply it:

```bash
pulumi up
```

Review the final plan and confirm the deployment.

EKS provisioning can take several minutes. Once Pulumi finishes, inspect the outputs:

```bash
pulumi stack output cluster_name
pulumi stack output deployment_name
pulumi stack output service_name
```

Security note: The exported kubeconfig is a credential-bearing access configuration and should be treated as sensitive. Avoid printing it into logs, committing it to source control, or sharing it. If Pulumi's default output handling does not mark it secret, explicitly mark the kubeconfig export as secret before using this stack in shared environments.

### 10\. Configure `kubectl` and verify cluster access

Configure your local Kubernetes context using the actual cluster name:

```bash
aws eks update-kubeconfig \
  --region "$AWS_REGION" \
  --name "$CLUSTER_NAME"
```

Check that the cluster is reachable:

```bash
kubectl config current-context
kubectl cluster-info
kubectl get nodes -o wide
kubectl get namespaces
```

Expected results include two worker nodes in a `Ready` state and standard namespaces such as `default`, `kube-system`, and `kube-public`. Actual node names, IP addresses, and Kubernetes versions will vary.

Check the permissions available to your current identity:

```bash
kubectl auth can-i get pods --all-namespaces
kubectl auth can-i create deployments
kubectl auth can-i get nodes
```

If you receive `Unauthorized` or `Forbidden`, verify your AWS credentials and the cluster's access-entry and authorization configuration. Don't solve an access issue by automatically granting unrestricted administrator access.

### 11\. Inspect the FastAPI deployment

### 11.1 Check Deployments, ReplicaSets, and Pods

```bash
kubectl get deployments
kubectl get replicasets
kubectl get pods -o wide
kubectl get services
```

Inspect the application Deployment:

```bash
kubectl describe deployment fastapi-api
```

Inspect an individual Pod:

```bash
kubectl describe pod \
  "$(kubectl get pods \
    -l app=fastapi-api \
    -o jsonpath='{.items[0].metadata.name}')"
```

Look at the `Events` section when investigating scheduling problems, image-pull failures, probe failures, or container restarts.

### 11.2 Inspect logs

Read logs from one of the application Pods:

```bash
POD_NAME="$(
  kubectl get pods \
    -l app=fastapi-api \
    -o jsonpath='{.items[0].metadata.name}'
)"

kubectl logs "$POD_NAME"
```

Follow the logs in real time:

```bash
kubectl logs -f "$POD_NAME"
```

For a container that restarted, inspect its previous logs:

```bash
kubectl logs "$POD_NAME" --previous
```

The last command only works when a previous container instance exists.

### 11.3 Test the internal Service

The Service is a `ClusterIP`, so it isn't directly exposed to the public internet. Use port forwarding to test it from your local machine:

```bash
kubectl port-forward service/fastapi-api 8000:8000
```

Leave that command running. In another Bash terminal, execute:

```bash
curl -i http://localhost:8000/health
```

Expected application response:

```json

{
  "status": "healthy"
}
```

If local port `8000` is already occupied, use a different local port, such as `8080:8000`, and call `http://localhost:8080/health`.

### 12\. Understand scheduling and resource usage

Inspect which nodes are running your application Pods:

```bash
kubectl get pods \
  -l app=fastapi-api \
  -o custom-columns='NAME:.metadata.name,NODE:.spec.nodeName,STATUS:.status.phase'
```

Inspect the requested resources:

```bash
kubectl get deployment fastapi-api \
  -o jsonpath='{.spec.template.spec.containers[0].resources}'
echo
```

If the Kubernetes Metrics Server is available, you can inspect current resource usage:

```bash
kubectl top nodes
kubectl top pods
```

If `kubectl top` reports that metrics are unavailable, check whether a compatible metrics provider is installed and healthy. Resource requests and limits do not themselves install a metrics provider.

Common symptoms to recognize:

| Symptom                  | What to investigate                                                      |
| ------------------------ | ------------------------------------------------------------------------ |
| Pending Pods             | Node capacity, scheduling constraints, resource requests, and events.    |
| ImagePullBackOff         | Image URI, ECR repository and tag, and registry access.                  |
| CrashLoopBackOff         | Application errors, container command, configuration, and previous logs. |
| 0/2 ready replicas       | Pod readiness, probe failures, or scheduling problems.                   |
| Service has no endpoints | Service selectors, Pod labels, and Pod readiness.                        |
| Forbidden                | EKS access configuration and Kubernetes RBAC.                            |

### 13\. Lab cleanup

EKS clusters and EC2 worker nodes incur costs even when you aren't actively deploying applications. Delete the resources when you're finished if you don't need them for Module 6.

First, confirm that you're operating on the intended stack:

```bash
pulumi stack
pulumi preview --diff
```

Then destroy the infrastructure managed by this stack:

```bash
pulumi destroy
```

Confirm the operation when prompted. Wait for the operation to finish and verify the stack no longer manages the resources you created.

If your `dev` stack also manages resources from earlier modules, do not destroy the whole stack blindly. In that case, isolate EKS into a dedicated stack, such as `eks-dev`, or use a component-specific resource lifecycle strategy before cleanup.

### Module 5 summary

You have covered the Kubernetes control plane, worker nodes, workload resources, EKS access, networking, resource management, and health probes. The lab brings these concepts together using Pulumi and the existing FastAPI image.

For the next module, we'll build on this cluster and focus on EKS networking, application exposure, ALB ingress, TLS, and secure routing.

### Further reading

* [Amazon EKS architecture and concepts](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html?utm_source=chatgpt.com)

* [Kubernetes Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/?utm_source=chatgpt.com)

* [Kubernetes Services](https://kubernetes.io/docs/concepts/services-networking/service/?utm_source=chatgpt.com)

* [Pulumi EKS Cluster component](https://www.pulumi.com/registry/packages/eks/api-docs/cluster/?utm_source=chatgpt.com)

* [Pulumi Kubernetes provider](https://www.pulumi.com/registry/packages/kubernetes/?utm_source=chatgpt.com)
