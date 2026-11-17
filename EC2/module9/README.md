### Module 9 — Amazon EKS Overview

Phase 4 — Compute · Kubernetes architecture on AWS · Hands-on with Pulumi and Python

Amazon Elastic Kubernetes Service (EKS) is AWS's managed Kubernetes service. It lets you run containerized applications using Kubernetes while AWS manages the Kubernetes control plane.

In the previous modules, you learned how to run applications on EC2, scale them with Auto Scaling, and deploy containers using ECR and ECS. In this module, you'll learn how EKS runs containers using Kubernetes, how it integrates with your VPC and IAM, and when it makes sense to choose EKS over ECS or Lambda.

### Learning objectives

By the end of this module, you should be able to:

* Explain Kubernetes clusters, control planes, worker nodes, pods, and deployments.

* Understand EKS clusters, managed node groups, and Fargate profiles.

* Explain pod IP addressing, the Amazon VPC CNI, and subnet capacity.

* Understand EKS authentication, IAM access, and Kubernetes RBAC.

* Expose an application using Kubernetes Services and AWS load balancing.

* Understand persistent storage and observability in EKS.

* Provision a small EKS environment with Pulumi and Python, deploy an application, test it, and clean up the resources.

* Choose between EKS, ECS, and Lambda for different workloads.

### 1\. What is Kubernetes?

Kubernetes is a container orchestration platform. It manages the lifecycle of containerized applications across a group of compute resources.

Running one container is relatively simple. Running hundreds of containers reliably introduces more challenges:

* What happens when a container crashes?

* How do you run multiple replicas of an application?

* How do you distribute traffic between replicas?

* How do you deploy a new application version without taking the service offline?

* How do you manage configuration, secrets, networking, and storage?

Kubernetes provides APIs and controllers to manage these tasks declaratively.

For example, instead of manually starting three containers, you declare that your application should have three replicas. Kubernetes works to maintain that desired state.

### 2\. Kubernetes architecture

![Kubernetes Architecture Explained Like You’re Sitting in the Control Room of a Real Cluster | by Franklin Osede Prieto | Medium](https://images.openai.com/static-rsc-4/Gy457EaL9Ou7fZyHNOMbbEBMA9vy0bxf8w0_0IZi-bENKWMdAzutAzMOg3O6vGkws35wAMMqZDMIlFdEr3gmxhRLbI23SOzXl3AXu-ktkZthDOIfl_1aWn1Wo1GBOGjT4om_Ml3B8ZUx-jD06ITX1we9fAwhGy3Y1OFAhK2PdDpd5w0JLYoiyq-rCnOKGmUG?purpose=fullsize)

A Kubernetes cluster has two main parts: the control plane and the worker nodes.

### Control plane

Manages the cluster's desired state and coordinates workloads.

* API server: Entry point for Kubernetes API requests.

* etcd: Stores Kubernetes cluster state.

* Scheduler: Selects suitable nodes for pods.

* Controller manager: Runs controllers that reconcile actual state with desired state.

Kubernetes API and cluster management

### Worker nodes

Node A

Kubelet

Container runtime

Application pods

Node B

Kubelet

Container runtime

Application pods

Worker nodes provide compute capacity for running application workloads.

### How the components work together

Suppose you request three replicas of a web application.

* You submit a Kubernetes Deployment manifest to the API server.

* Kubernetes stores the desired configuration.

* The Deployment controller creates the required ReplicaSet.

* The ReplicaSet ensures that three pods exist.

* The scheduler assigns unscheduled pods to suitable nodes.

* The kubelet on each selected node ensures the assigned pods run.

If a pod fails, Kubernetes attempts to restore the desired state.

Important: Kubernetes does not guarantee that every replacement pod will run on the same node or keep the same IP address. Applications should be designed to tolerate pod replacement.

### 3\. The core Kubernetes resources

![Kubernetes network stack fundamentals: How containers inside a pod communicate](https://images.openai.com/static-rsc-4/3HJJ_yLPiRJeuxrJ1j_kIMro_hgiDxTvH7hRB30b9NHzj-sQPr8L5TYjMFFjvbP7RHPptYEE-hhspk7rl3eZXkvMDmPtDhP38t5o7yKKbj8V5AUkgUWIl_1MePc5QX6djks3EmoRUiKcoDNhamLpwgW6CBiLQpwbBe292ZzOcrQFGIWdnwH6Nk6FchvVFHmB?purpose=fullsize)

Pod

The smallest deployable Kubernetes unit. It contains one or more closely related containers that share networking and can share storage volumes.

![Kubernetes ReplicaSets and Deployments | Coding Shuttle](https://images.openai.com/static-rsc-4/Jgv2svlB7XsuK9YBLCdLdqmUcZZU9gt4UeATHrkMQbEPYOPP_nUGfmNEFFGB3H8XELysAwrEbDlgtxCtggBS7RFA9IeimCYJxMGfyax-oIM5yI-8spv7lwfIrcPISgIBgE1H-vr-kV5_gouystpjFE0D3yyvJ5pweVFIWNsUceg7TOu955WGdEv4EP0n1UWT?purpose=fullsize)

Deployment

Declares the desired number of replicas and manages application updates through ReplicaSets. It is the usual starting point for stateless applications.

![ClusterIP vs NodePort vs LoadBalancer vs Ingress - Red Hat Learning Community](https://images.openai.com/static-rsc-4/jyXwQdezrLnbRvbjAv1QwVuj_v4OJ79QIwpRIq0E8XwnBxanVcZKXnSaXzxyNY-MPhbWlCDG9itisa_B5V4b63a83jBYJcAkWV4hSexx3kXyyEa2iITEbVaViJz8A1fHbD2f8AppwLj8zonpOoIX0OuMZRe-SAr2Juk6c4bnmpgwXu0VwEpLvJLlsbvGbAf9?purpose=fullsize)

Service

Provides a stable network endpoint for a changing set of pods. Common types include ClusterIP, NodePort, and LoadBalancer.

![Configuration and Secret Management for Real Environments : Course Kubernetes for Developers: Deploy, Scale, and Operate Modern Apps with Helm, GitOps, and Observability | Cursa](https://images.openai.com/static-rsc-4/3knCZH8tLLWVhu3OlIRDQE--kvQpH9tNIfJvTlaViS4xii4_mH97z-CyeOBAxQgeiZD07p9sVKfvy2xzCU9hhCK-i9JnbVIZZjFHXr9d67vKv_BhQl1iPbeytUOFXqa5dXP2iXjApiSW90ufv99emM9b9-M9OZM9Ods7yAskTCYIF_GP5u8OFVNVynb8bGIz?purpose=fullsize)

ConfigMap and Secret

Supply configuration and sensitive values to workloads. Kubernetes Secrets need appropriate access controls and encryption-at-rest considerations.

A Deployment manages pods, but it does not itself provide a stable network endpoint. That is one of the reasons Services exist.

### 4\. What Amazon EKS manages

Amazon EKS provides a managed Kubernetes control plane. AWS operates the control-plane infrastructure, including the Kubernetes API server and its underlying availability architecture.

You still need to configure and manage important parts of your application platform, including worker capacity, networking, permissions, application manifests, and observability.

### EKS compute options

![Amazon EKS (Elastic Kubernetes Service) architecture on AWS | by casimirrex antony | Medium](https://images.openai.com/static-rsc-4/nnXW1XtTaIBRKFxFY4QWXzEa6of1Q1E8Io4EpdIQ-L1U-NRyqtXUi0YzomdtIx2Ndkz8lLPPmaddRSr-h-eOFVR4PMB9JcX8x7GNCMroRhb_QQsk9pp7lal4bHHws_YyT0fF_e-6AHeVNhE_swO4xFL5e_uhGNHy8TgaAYpXjgcwc3M6Rm4vmNEghzuXk98B?purpose=fullsize)

Managed node groups

AWS manages the lifecycle and integration of EC2 worker nodes, including node provisioning and managed updates. You remain responsible for choosing instance types, scaling capacity, and configuring workloads.

![Amazon Elastic Kubernetes Service - Overview of Deployment Options on AWS](https://images.openai.com/static-rsc-4/oLcSd8f5pUHEGQwqJQMUuKaMOOhfBbP3SuN0nHCjxYlkCJDaY-2ySE5fi8-C7JhLjH623mwqjB3vIReSZfPpY2vzvsljS79ObEguv2TUftTl-ijefMv7BOskgZyUQ3cX3bD2zkxdqhywsdm__-G0ja6IaP1RIyos6Q9LPu3A7rJkJ0d6qmqDJHK9c8jAH5f_?purpose=fullsize)

Fargate profiles

Match eligible pods to serverless compute. AWS manages the underlying compute infrastructure, so you do not manage EC2 worker nodes for those pods. Fargate has workload and Kubernetes feature limitations.

![Demystifying EKS Cluster Creation: A Comprehensive Guide | by Dharshitha Senevirathne | Medium](https://images.openai.com/static-rsc-4/lZ0sbj6fiHA8csjt8j6JY5sqt9XM2D-pou7iaVuR6wqkGst_NK58ppkgJTignjM5xuT6Gh_MKzfmaIAGcAM06xxjSXRuE0SqOoJbUerFVKqvKlw4f43dIWRwQxJJlBMfA0WCeJCiw-4thFDjfmwL3hwZQZOXSshB4MuXgG8-bDEgbjZJakvaxFvyZavTBUJm?purpose=fullsize)

Self-managed nodes

You manage more of the worker-node lifecycle yourself. This provides flexibility but increases operational responsibility.

For this introductory lab, we'll use EKS with a managed node group. It makes the relationship between Kubernetes, EC2, IAM, and VPC networking easier to understand.

### EKS versus ECS

Both services run containers, but their operating models differ.

| Feature        | Amazon EKS                                                     | Amazon ECS                              |
| -------------- | -------------------------------------------------------------- | --------------------------------------- |
| Orchestration  | Kubernetes                                                     | AWS-native orchestration                |
| Workload model | Pods, Deployments, Services                                    | Tasks, task definitions, services       |
| Learning curve | Higher                                                         | Usually lower                           |
| Portability    | Kubernetes ecosystem across many environments                  | Strong AWS-native integration           |
| Operations     | Kubernetes APIs, add-ons, upgrades, policies                   | Generally simpler platform model        |
| Best fit       | Kubernetes skills, ecosystem, and advanced orchestration needs | Straightforward AWS container workloads |

EKS is not automatically better because it is more flexible. ECS is often the simpler choice when Kubernetes compatibility is not a requirement.

### 5\. EKS networking and the VPC CNI

EKS networking builds on the VPC knowledge from Phase 3.

With the standard Amazon VPC Container Network Interface (VPC CNI), pods commonly receive IP addresses from the VPC address space. This lets VPC resources communicate with pods using VPC networking, subject to routes and security controls.

![CNI Amazon VPC - Amazon EKS](https://images.openai.com/static-rsc-4/oJ3heiyq_acYH0Kd_GVGDiacmxASLt2UIpnWA9o-AE16EYIneIxQ2v61USU1AXJr-RhprBlnKZwz4tda244iF6OhZE9uZUPxsKpytauzGX1Swexno_Fhmjblc4N2t6ywQctjftwCWfjc6bWB_fB82UZj_E-lhlcUhRP16rPBCkTQj4T_ztVGeiXaiGN8f6ez?purpose=fullsize)

Consider a VPC with:

* Public subnets for an internet-facing load balancer.

* Private subnets for worker nodes.

* Additional subnet IP capacity for pod networking.

* Security groups controlling permitted traffic.

* NAT gateways or VPC endpoints for required outbound AWS service access.

### Why subnet capacity matters

Pod IP addresses consume address capacity. Depending on the networking configuration, the CNI may allocate additional addresses or prefixes to worker-node network interfaces.

A subnet that has enough IPs for EC2 instances might still run out of capacity when many pods are scheduled.

When planning an EKS deployment, account for:

* The number of nodes.

* The expected number of pods per node.

* CNI address allocation behavior.

* Load balancer and other network interface requirements.

* Growth and rolling-deployment headroom.

Key distinction: Kubernetes scheduling capacity and VPC IP address capacity are different limits. A cluster can have available CPU and memory yet fail to start pods because it cannot allocate network addresses.

### 6\. Cluster endpoints and access management

An EKS cluster exposes a Kubernetes API endpoint. Access depends on both network reachability and authorization.

### Endpoint access

* Public endpoint: The API endpoint is reachable over the internet, subject to configured access restrictions.

* Private endpoint: The API endpoint is reachable through the cluster VPC's private networking.

* Public and private: Both access paths are enabled.

For a learning lab, public endpoint access with restricted source CIDRs can be convenient. For production, evaluate private access and a secure administrative path.

Do not open the Kubernetes API to every IP address just to make a lab easier.

### IAM authentication and Kubernetes authorization

There are two related but separate questions:

* Authentication: Who is making the request?

* Authorization: What is that identity allowed to do?

EKS integrates IAM identities with Kubernetes access. EKS access entries can associate IAM principals with cluster access and, when configured, Kubernetes permissions or supported EKS access policies.

Kubernetes RBAC then controls permissions through resources such as Roles, ClusterRoles, RoleBindings, and ClusterRoleBindings.

For application workloads, use workload-specific identities rather than reusing an administrator's AWS credentials.

### Two IAM concepts to keep separate

* EKS cluster role: Allows the EKS service to manage the cluster's AWS resources.

* Node IAM role: Gives worker nodes the AWS permissions needed for node operation and relevant integrations.

Pod workloads may also need their own AWS permissions. Common approaches include EKS Pod Identity and IAM Roles for Service Accounts (IRSA). These avoid granting every application the full permissions of the worker-node role.

### 7\. Load balancing, storage, and observability

### Exposing an application

A typical request path looks like this:

Client

AWS Application Load Balancer

Ingress or Gateway integration, as configured

Kubernetes Service

Stable endpoint for selected pods

Pod 1

Pod 2

An ALB can be provisioned and integrated with Kubernetes using the AWS Load Balancer Controller. That controller requires its own installation and IAM permissions; an EKS cluster does not automatically have every load-balancing integration configured.

For a simple lab, a Kubernetes `Service` of type `LoadBalancer` is another option, but the resulting AWS load balancer type and controller behavior depend on the cluster's configured integrations.

### Persistent storage

Containers and pods can be replaced. Data that must survive replacement needs appropriate persistent storage.

* Amazon EBS: Block storage, commonly used with EKS through the EBS CSI driver. An EBS volume is generally attached within one Availability Zone at a time.

* Amazon EFS: Shared file storage that can support access from multiple pods and nodes.

* Ephemeral storage: Suitable for temporary files that can be recreated.

PersistentVolumeClaims request storage for applications, while StorageClasses describe how storage can be provisioned. A persistent volume is not a backup strategy by itself.

### Observability

Useful observability components include:

* CloudWatch: Container logs, metrics, and alarms through the relevant integrations.

* Kubernetes events: Scheduling failures, image-pull errors, and other cluster events.

* Container logs: Application output for diagnosing runtime failures.

* Metrics and health probes: Resource usage, readiness, and liveness.

A successful pod status does not necessarily mean your application is reachable. Verify the entire request path, from the load balancer through the Service to the application container.

### 8\. Hands-on lab — Deploy an application to EKS using Pulumi

### Lab goals

* Provision an EKS cluster and managed EC2 worker nodes.

* Use Pulumi with Python to manage infrastructure.

* Deploy a containerized application to Kubernetes.

* Expose it through a Kubernetes Service.

* Inspect the cluster and application.

* Remove the lab resources when finished.

    Cost note: EKS charges for the cluster while it exists, in addition to EC2, networking, and any load balancer charges. Use a dedicated lab environment and clean it up promptly.

### Step 1 — Prepare your environment

You'll need:

* An AWS account with permissions to create EKS, IAM, EC2, and related resources.

* AWS CLI v2, configured with your lab identity.

* Python 3 and Pulumi CLI.

* `kubectl` to manage Kubernetes resources.

* Docker or another way to build and publish container images if you choose to use your own application.

Check your tools:

```bash
aws sts get-caller-identity
pulumi version
kubectl version --client
python --version
```

Configure AWS credentials using your preferred profile or federated identity. Avoid embedding long-lived AWS access keys in your Pulumi project.

### Step 2 — Create the Pulumi project

Create a new project:

```bash
mkdir eks-pulumi-lab
cd eks-pulumi-lab

pulumi new aws-python
```

Install the EKS component package:

```bash
pip install pulumi-eks
```

If you use a virtual environment, activate it before installing packages. Commit the generated dependency lock information so your lab can be reproduced.

The following example uses an existing VPC and its public subnets to keep the networking setup focused on EKS. It is a learning configuration, not a production network design. In a production setup, prefer appropriately designed private worker subnets and restricted cluster API access.

### Step 3 — Define the EKS cluster in Python

Replace the generated `__main__.py` with the following example. It assumes that your AWS account has a suitable existing VPC with at least two public subnets in different Availability Zones.

```python

import pulumi
import pulumi_aws as aws
import pulumi_eks as eks

config = pulumi.Config()
vpc_id = config.require("vpcId")
subnet_ids = config.require_object("subnetIds")

# Use an existing VPC and subnets for this introductory lab.
# The subnet IDs should span at least two Availability Zones.
cluster = eks.Cluster(
    "compute-eks-lab",
    vpc_id=vpc_id,
    public_subnet_ids=subnet_ids,
    instance_type="t3.medium",
    desired_capacity=2,
    min_size=1,
    max_size=2,
    endpoint_public_access=True,
    endpoint_private_access=True,
)

pulumi.export("clusterName", cluster.eks_cluster.name)
pulumi.export("kubeconfig", cluster.kubeconfig)
```

Configure the values for your environment:

```bash
pulumi config set aws:region eu-west-3
pulumi config set vpcId vpc-REPLACE_ME
pulumi config set --path 'subnetIds[0]' subnet-REPLACE_ME_1
pulumi config set --path 'subnetIds[1]' subnet-REPLACE_ME_2
```

Use actual resource IDs from your account. The example region is illustrative; choose the region where your VPC and subnets exist.

Important lab considerations:

* Confirm that your selected subnets have enough available IP addresses for nodes and pods.

* Public subnets need suitable routes and public IP behavior for the chosen node configuration.

* The EKS component package's supported arguments and Kubernetes version defaults can vary by package release. Check the installed `pulumi-eks` version's API documentation before deployment.

* Restrict cluster API access to your trusted source IP ranges when possible. This example enables public endpoint access for easier learning, but does not itself restrict the endpoint's allowed CIDRs.

* A `t3.medium` instance may be insufficient for workloads with large resource requests. Keep the lab workload small.

### Step 4 — Provision the infrastructure

Preview the changes:

```bash
pulumi preview
```

If the preview is correct, deploy:

```bash
pulumi up
```

Review the proposed resources and approve the update.

The deployment can take several minutes. Pulumi will create the resources represented by the EKS component, which typically include the cluster, required IAM resources, and worker-node infrastructure.

Once it finishes, inspect the exported cluster name and kubeconfig output. Treat kubeconfig as sensitive because it provides access to the cluster according to your AWS identity and EKS access configuration.

### Step 5 — Connect `kubectl` to the cluster

The exported kubeconfig can be used with `kubectl`. If you prefer to generate a context through the AWS CLI, use the cluster name exported by Pulumi:

```bash
aws eks update-kubeconfig \
  --region eu-west-3 \
  --name YOUR_CLUSTER_NAME
```

Verify connectivity:

```bash
kubectl get nodes
kubectl get namespaces
kubectl get pods -A
```

You should see registered worker nodes once they have joined successfully.

If no nodes appear, investigate node-group status, node IAM permissions, subnet routing, security group rules, and the cluster's networking configuration.

### Step 6 — Deploy a sample application

Create a file named `app.yaml`:

```yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: web-demo
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web-demo
  template:
    metadata:
      labels:
        app: web-demo
    spec:
      containers:
        - name: web
          image: public.ecr.aws/nginx/nginx:stable
          ports:
            - containerPort: 80
          resources:
            requests:
              cpu: "100m"
              memory: "64Mi"
            limits:
              cpu: "250m"
              memory: "128Mi"
          readinessProbe:
            httpGet:
              path: /
              port: 80
            initialDelaySeconds: 3
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: web-demo
spec:
  type: LoadBalancer
  selector:
    app: web-demo
  ports:
    - port: 80
      targetPort: 80
```

This sample uses a public NGINX container image. It demonstrates Kubernetes deployment and service behavior without requiring you to build an image.

Apply it:

```bash
kubectl apply -f app.yaml
```

Watch the rollout:

```bash
kubectl rollout status deployment/web-demo
kubectl get deployments
kubectl get pods -o wide
kubectl get services
```

The `LoadBalancer` Service requests an AWS load balancer through a compatible controller or integration. The precise result depends on the cluster's installed load-balancing components. If a load balancer is not provisioned, inspect the Service events instead of assuming that EKS automatically installed every required controller.

When an external address is assigned, inspect it:

```bash
kubectl describe service web-demo
```

Then open the reported address in your browser using HTTP if the provisioned endpoint supports it.

### Step 7 — Observe and troubleshoot the workload

Use these commands to inspect the application:

```bash
kubectl get pods -o wide
kubectl logs deployment/web-demo
kubectl describe deployment web-demo
kubectl describe service web-demo
kubectl get events --sort-by=.metadata.creationTimestamp
```

Practice diagnosing these scenarios:

| Symptom                       | What to investigate                                                            |
| ----------------------------- | ------------------------------------------------------------------------------ |
| Pod stuck in Pending          | Node capacity, scheduling constraints, and available pod IPs                   |
| ImagePullBackOff              | Image name, registry access, and image availability                            |
| Pod repeatedly restarts       | Container logs, resource limits, and application errors                        |
| Service has no endpoints      | Pod labels, Service selectors, and readiness                                   |
| Load balancer remains pending | Service events, controller installation, IAM permissions, and subnet discovery |
| Cannot reach the cluster API  | Endpoint configuration, network reachability, and IAM access                   |

Try scaling the application:

```bash
kubectl scale deployment web-demo --replicas=3
kubectl get pods -o wide
```

Then perform a rolling update by changing the container image in the Deployment. Observe how Kubernetes replaces pods while maintaining the desired replica count.

### Step 8 — Clean up all resources

First remove the application and its load balancer request:

```bash
kubectl delete -f app.yaml
```

Wait for the associated load balancer resources to be removed. Then destroy the Pulumi-managed cluster:

```bash
pulumi destroy
```

Review the proposed deletions and confirm them. Finally, verify that the cluster, node instances, and associated load balancer resources are gone.

If you used a VPC and subnets created separately for the lab, remove those only after verifying that no other resources depend on them. If you used shared networking, leave it intact.

Cost reminder: Deleting the Kubernetes Deployment alone does not delete the EKS cluster. The cluster and other infrastructure can continue generating charges until their respective resources are removed.

### 9\. Choosing between EKS, ECS, and Lambda

Choose EKS when

* You need the Kubernetes ecosystem or Kubernetes-compatible tooling.

* You need Kubernetes APIs, controllers, and orchestration capabilities.

* Your organization already operates Kubernetes across multiple environments.

Choose ECS when

* You want to run containers with less orchestration complexity.

* AWS-native integrations meet your requirements.

* You want to use Fargate without managing Kubernetes.

Choose Lambda when

* Your application can be split into event-driven functions.

* You want AWS to manage the underlying compute infrastructure.

* The execution limits and invocation model fit your workload.

There is no universal winner. Consider operational effort, workload characteristics, required flexibility, security, availability, and total cost.

### 10\. Knowledge check

### Test your understanding

5 questions

1. What is the primary responsibility of the Kubernetes control plane?

Run all application containers directly

Maintain cluster state and coordinate workloads

Allocate every VPC IP address manually

2. What is a Kubernetes Deployment primarily used for?

Managing replicated application pods and updates

Creating AWS IAM users

Replacing the VPC route table

3. What is a key responsibility of the Amazon VPC CNI?

Encrypt application source code

Allocate and configure pod networking

Upgrade every application dependency

4. Which statement about EKS IAM access is correct?

IAM authentication automatically grants every Kubernetes permission

IAM identities and Kubernetes authorization are separate concerns

Every pod must use the cluster administrator's credentials

5. When is ECS often a sensible choice over EKS?

When Kubernetes APIs are mandatory

When you want simpler AWS-native container orchestration

When the application must run only as a Kubernetes DaemonSet

Check answers

### Module 9 completion checklist

### Your progress

0 of 7

Explain the Kubernetes control plane and worker nodes

Understand pods, Deployments, and Services

Explain managed node groups and Fargate profiles

Understand VPC CNI and subnet IP capacity

Distinguish IAM authentication from Kubernetes authorization

Deploy and validate a sample application

Clean up the cluster and associated resources

Next step: Once you've completed the lab, you're ready to move on to the next phase of your AWS learning roadmap: storage and databases, beginning with Amazon S3.
