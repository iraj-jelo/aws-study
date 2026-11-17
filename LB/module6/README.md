### Module 6 — Load Balancing with Amazon ECS and Amazon EKS

### 1\. Module objectives

In this module, we will connect AWS load-balancing concepts to container orchestration platforms: Amazon ECS and Amazon EKS.

In previous modules, we explored ALB, NLB, health checks, TLS, networking, and traffic management. Now we'll bring those concepts together and learn how AWS integrates load balancers with container workloads.

By the end of this module, you should understand how to:

* Integrate ALB with ECS services and automatically register container tasks.

* Expose ECS Fargate and ECS on EC2 applications through load balancers.

* Understand dynamic host-port mapping and IP-based target registration.

* Configure ECS deployment health, traffic shifting, and graceful task replacement.

* Understand Kubernetes Service types and their relationship with AWS load balancers.

* Deploy the AWS Load Balancer Controller on EKS.

* Expose Kubernetes applications through ALB Ingress resources.

* Provision NLB-backed Kubernetes Services.

* Coordinate Kubernetes readiness probes and AWS load-balancer health checks.

* Implement container autoscaling, connection draining, and rolling deployments.

* Design private application and microservice architectures.

### 2\. ECS and EKS load-balancing architecture

Before implementing anything, let's understand the responsibilities of each component.

### 2.1 Amazon ECS integration

Amazon ECS integrates with Elastic Load Balancing through ECS services.

When an ECS service is associated with a load balancer, ECS manages target registration and deregistration as tasks are created, replaced, or stopped.

![Getting Started with Terraform Provisioners: File, Local-Exec & Remote-Exec Explained | by Kajal | Medium](https://images.openai.com/static-rsc-4/FnwRJd3IhbPVlaWGl6rwCC5Z5i2MUzZynSy7vb_DlZLCcTYV8j5Viz86UM98ser6Zon2mVyRGrdPCFlE6YQA4RGtIU2JqrQMcp5F2NYQCI4Sn5YKuYeOoZnq-dGSgXEfRGhJiYs6aG9P5rR9ost0DjwzSUInvMR6CzmnSP8ARB5YCVQAZ5DqMkAz1xGTvAUZ?purpose=fullsize)

The architecture looks like this:

* A client sends an HTTP request to the ALB.

* The ALB evaluates listener rules.

* The listener forwards the request to an appropriate target group.

* The target group forwards the request to a healthy ECS task.

* The container processes the request and returns a response.

The important point is that ECS manages the relationship between service tasks and the target group. You don't need to manually register every newly created task.

### 2.2 Amazon EKS integration

EKS uses Kubernetes networking abstractions, but AWS load balancers are external infrastructure.

The AWS Load Balancer Controller bridges Kubernetes resources and AWS networking services.

![Deploying AWS Load Balancer Controller on Amazon EKS | Networking & Content Delivery](https://images.openai.com/static-rsc-4/KJqZWQusekoGeG7_bOJM92p_ZtYaFsC2CRb1C2g6fy1N6MAiJXdHZVYefk5NxaEKSc7DbSwGLlyx7KHEhHIYTCagUz4zxYRRjlLtT19uzCYF7qFDDzbmqgFQwLZS-D0_w632VQ5NRYk_p6BDq4hu1ketn-26wflvot-5cTZ_eaNtSHqUxy7kVVgbVyJr5yCX?purpose=fullsize)

It watches Kubernetes resources and provisions or configures AWS resources accordingly.

Two important integration patterns are:

| Kubernetes resource       | AWS resource | Typical use                         |
| ------------------------- | ------------ | ----------------------------------- |
| Ingress                   | ALB          | HTTP/HTTPS routing                  |
| Service type LoadBalancer | NLB          | TCP, UDP, and network-level traffic |

The controller is particularly important because it automates the lifecycle of these AWS resources.

### 3\. ECS and Application Load Balancer integration

### 3.1 ECS services and target groups

An ECS service maintains a desired number of running tasks.

For example:

```text
ECS Cluster
  └── FastAPI Service
        ├── Task 1
        ├── Task 2
        └── Task 3
```

When an ALB is associated with the service, its target group tracks the corresponding running tasks.

```text
                  ALB
                   |
             Target Group
              /    |    \
             /     |     \
          Task 1 Task 2 Task 3
```

The integration requires several resources:

* ECS cluster.

* ECS task definition.

* ECS service.

* Application Load Balancer.

* ALB listener.

* Target group.

* IAM roles.

* Security groups.

* VPC subnets and routing.

The ECS service configuration references the target group and identifies the container name and container port.

For example:

```python
load_balancers=[
    {
        "target_group_arn": target_group.arn,
        "container_name": "fastapi",
        "container_port": 8000,
    }
]
```

This tells ECS which container and port should receive traffic from the target group.

Important: The target group must use a target type compatible with the ECS launch type and networking configuration.

### 3.2 Fargate and IP target groups

For ECS Fargate, tasks use the `awsvpc` network mode.

Each task receives its own elastic network interface (ENI) and private IP address.

Therefore, the ALB target group should use:

```python
target_type="ip"
```

The traffic path is:

```text
ALB
 |
Target Group (IP)
 |
Task ENI private IP
 |
FastAPI container:8000
```

The target is the task's private IP address rather than an EC2 instance.

This is particularly important because Fargate does not expose an underlying EC2 host that you can use as the application target.

### 3.3 ECS on EC2 and dynamic host-port mapping

ECS on EC2 supports multiple networking modes.

One common configuration is `bridge` networking.

With dynamic host-port mapping, ECS can assign an available host port to each task.

For example:

| Container | Container port | Host port |
| --------- | -------------- | --------- |
| Task 1    | 8000           | 32768     |
| Task 2    | 8000           | 32769     |
| Task 3    | 8000           | 32770     |

The target group registers the EC2 instance and its dynamically assigned host port.

```text
ALB
 |
Target Group (Instance)
 |
EC2 instance:32768
EC2 instance:32769
EC2 instance:32770
```

This allows multiple application tasks to use the same container port on one EC2 instance.

For ECS on EC2, the target type depends on the networking mode:

* `bridge`: commonly uses `instance` targets with dynamic host-port mapping.

* `host`: commonly uses `instance` targets with fixed host ports.

* `awsvpc`: uses `ip` targets.

For production ECS deployments, `awsvpc` is often preferable when task-level network isolation and security-group control are important.

### 3.4 ECS deployment health and traffic shifting

ECS deployments need to coordinate application startup, target registration, and health checks.

Consider a service with three running tasks.

When ECS replaces an old task:

* ECS starts a replacement task.

* The task receives its network configuration.

* ECS registers the task with the target group.

* The load balancer performs health checks.

* The new task becomes healthy.

* ECS can continue replacing old tasks according to deployment configuration.

Important ECS deployment parameters include:

| Parameter                  | Purpose                                                                        |
| -------------------------- | ------------------------------------------------------------------------------ |
| Desired count              | Number of tasks the service should maintain                                    |
| Minimum healthy percent    | Minimum percentage of desired tasks that must remain healthy during deployment |
| Maximum percent            | Maximum percentage of desired tasks that may run during deployment             |
| Health check grace period  | Time ECS waits before acting on load-balancer health-check failures            |
| Deployment circuit breaker | Detects deployment failures and can roll back a deployment                     |

For example:

```python
deployment_configuration={
    "maximum_percent": 200,
    "minimum_healthy_percent": 100,
    "deployment_circuit_breaker": {
        "enable": True,
        "rollback": True,
    },
}
```

With a desired count of three:

* Minimum healthy percentage of 100% requires three healthy tasks.

* Maximum percentage of 200% permits up to six tasks during deployment.

This provides room to start replacement tasks before stopping existing ones.

### 3.5 ECS deployment strategies

ECS supports different deployment approaches, depending on the deployment controller and configuration.

* Rolling deployment: gradually replaces existing tasks.

* Blue/green deployment: shifts traffic between separate application environments.

* Canary-style traffic shifting: gradually exposes a new version through controlled routing strategies.

For ECS blue/green deployments, understand the relationship between ECS deployment controllers, CodeDeploy, ALB listeners, and multiple target groups.

Do not confuse ordinary ECS rolling deployment with CodeDeploy-managed blue/green deployment: they use different deployment mechanisms.

### 4\. Kubernetes networking and Service types

Before using AWS load balancers with EKS, we need to understand how Kubernetes exposes applications.

### 4.1 ClusterIP

`ClusterIP` is the default Kubernetes Service type.

It exposes an application through an internal cluster IP address.

```text
Other Pods
    |
    v
ClusterIP Service
    |
    +---- Pod 1
    +---- Pod 2
    +---- Pod 3
```

Example:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  type: ClusterIP
  selector:
    app: fastapi
  ports:
    - port: 80
      targetPort: 8000
      protocol: TCP
```

Here:

* `port: 80` is the Service port.

* `targetPort: 8000` is the application container port.

* The selector identifies matching Pods.

ClusterIP is commonly used for internal microservice communication and as the backend of an ALB Ingress.

### 4.2 NodePort

NodePort exposes a Service on a port across the Kubernetes worker nodes.

```text
              Client
                 |
                 v
          Worker Node
           NodePort
                 |
                 v
          ClusterIP Service
                 |
             Application
```

Example:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  type: NodePort
  selector:
    app: fastapi
  ports:
    - port: 80
      targetPort: 8000
      nodePort: 30080
      protocol: TCP
```

The application can be accessed through:

```text
http://WORKER_NODE_IP:30080
```

NodePort is important when using an ALB or NLB with instance targets because the load balancer forwards traffic to the worker node's NodePort.

### 4.3 LoadBalancer

A Kubernetes Service with:

```yaml
type: LoadBalancer
```

requests an external load-balancing implementation.

On EKS, the AWS integration can provision an AWS Network Load Balancer.

```text
             Internet
                 |
                 v
                 NLB
                 |
          Worker Nodes / Pods
                 |
             Kubernetes
               Service
                 |
                Pods
```

The AWS Load Balancer Controller supports both instance and IP target modes for NLBs. Amazon EKS +1

### 4.4 Comparing Kubernetes Service types

| Feature           | ClusterIP         | NodePort          | LoadBalancer                      |
| ----------------- | ----------------- | ----------------- | --------------------------------- |
| Internal access   | Yes               | Yes               | Yes                               |
| Node-level port   | No                | Yes               | Usually                           |
| AWS load balancer | No                | Not automatically | Yes, with appropriate integration |
| Common use        | Internal services | Node exposure     | External TCP/UDP traffic          |

An important distinction:

Ingress is not a Service type. It is a separate Kubernetes API resource for describing HTTP/HTTPS routing. An Ingress normally references a Kubernetes Service as its backend.

### 5\. AWS Load Balancer Controller

### 5.1 What is the AWS Load Balancer Controller?

The AWS Load Balancer Controller (LBC) is a Kubernetes controller that manages AWS Elastic Load Balancing resources.

It watches Kubernetes resources and reconciles the desired configuration with AWS.

Its primary integrations are:

| Kubernetes resource          | AWS resource              |
| ---------------------------- | ------------------------- |
| Ingress                      | Application Load Balancer |
| Service of type LoadBalancer | Network Load Balancer     |
| TargetGroupBinding           | Existing target groups    |

The controller supports annotations that let you configure AWS load-balancer behavior directly through Kubernetes manifests. Amazon EKS +1

### 5.2 Controller architecture

Consider the following architecture:

```text
          Kubernetes API Server
                   |
                   v
       AWS Load Balancer Controller
                   |
             Watch resources
                   |
          +--------+--------+
          |                 |
          v                 v
       Ingress            Service
          |                 |
          v                 v
         ALB               NLB
          |                 |
          v                 v
       Target Groups and Targets
                   |
                   v
              Application Pods
```

The controller performs several operations:

* Watches Ingress and Service resources.

* Reads their specifications and annotations.

* Creates or updates AWS load balancers.

* Creates listeners and target groups.

* Configures security groups and networking.

* Registers and deregisters application targets.

* Reconciles AWS infrastructure when Kubernetes resources change.

This is an example of the Kubernetes controller pattern: continuously reconciling actual state with desired state.

### 5.3 Controller prerequisites

Before installing the controller, you need:

* A working EKS cluster.

* An appropriately configured VPC and subnets.

* Kubernetes API access.

* AWS IAM permissions for the controller.

* An IAM role associated with its Kubernetes service account.

* AWS VPC CNI, CoreDNS, and kube-proxy.

* Helm or the official installation manifests.

* Correct subnet discovery tags or explicit subnet configuration.

For IAM integration, you will commonly encounter:

* IAM Roles for Service Accounts (IRSA).

* EKS Pod Identity.

Both provide AWS credentials to workloads without storing long-lived access keys in Kubernetes.

For an IRSA-based installation, the EKS cluster needs an IAM OIDC provider, and the controller's IAM role needs a trust relationship with its Kubernetes service account. Amazon EKS +1

### 5.4 Installing the controller

We will use Helm for the installation.

First, identify the EKS cluster and AWS account:

```bash
aws sts get-caller-identity

aws eks describe-cluster \
  --name my-eks-cluster \
  --region eu-west-2 \
  --query "cluster.status"
```

Configure kubectl:

```bash
aws eks update-kubeconfig \
  --name my-eks-cluster \
  --region eu-west-2
```

Verify cluster access:

```bash
kubectl get nodes
kubectl get pods -A
```

Check whether the cluster has an OIDC provider:

```bash
aws eks describe-cluster \
  --name my-eks-cluster \
  --region eu-west-2 \
  --query "cluster.identity.oidc.issuer" \
  --output text
```

The controller installation requires an IAM policy and role. The policy should come from the official AWS Load Balancer Controller release corresponding to the version you install.

After configuring the IAM role and service account, install the controller:

```bash
helm repo add eks https://aws.github.io/eks-charts

helm repo update

helm upgrade --install aws-load-balancer-controller \
  eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName=my-eks-cluster \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller
```

Check the deployment:

```bash
kubectl get deployment \
  aws-load-balancer-controller \
  -n kube-system

kubectl get pods -n kube-system
```

Check controller logs:

```bash
kubectl logs \
  -n kube-system \
  deployment/aws-load-balancer-controller \
  --tail=100
```

Important: The commands above assume the IAM role, IAM policy, OIDC integration, and Kubernetes service account have already been created. Follow the official installation procedure for the selected controller release rather than skipping those prerequisites.

Official installation documentation: [Install AWS Load Balancer Controller with Helm](https://docs.aws.amazon.com/eks/latest/userguide/lbc-helm.html?utm_source=chatgpt.com).

### 6\. Kubernetes Ingress with ALB

### 6.1 Understanding Ingress

Ingress provides HTTP and HTTPS routing into Kubernetes applications.

For example, consider a microservice architecture:

```text
                     ALB
                      |
              Ingress Resource
                      |
           +----------+----------+
           |                     |
       /api/users             /api/orders
           |                     |
           v                     v
      Users Service         Orders Service
           |                     |
       Users Pods            Orders Pods
```

One ALB can route requests to multiple Kubernetes Services.

This avoids creating a separate public load balancer for every HTTP microservice.

### 6.2 Ingress configuration

Let's deploy a simple FastAPI application.

Create `deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
        - name: fastapi
          image: public.ecr.aws/docker/library/python:3.14-slim
          command: ["/bin/sh", "-c"]
          args:
            - |
              pip install fastapi uvicorn &&
              cat > /tmp/main.py <<'EOF'
              from fastapi import FastAPI
              app = FastAPI()

              @app.get("/")
              def root():
                  return {"message": "Hello from EKS"}

              @app.get("/health")
              def health():
                  return {"status": "healthy"}
              EOF
              uvicorn main:app --app-dir /tmp --host 0.0.0.0 --port 8000
          ports:
            - containerPort: 8000
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi-service
spec:
  type: ClusterIP
  selector:
    app: fastapi
  ports:
    - port: 80
      targetPort: 8000
```

This is a teaching example. For production, build the application into an immutable Docker image, push it to ECR, pin the image by digest, and avoid installing dependencies at container startup.

Apply the manifest:

```bash
kubectl apply -f deployment.yaml
```

Check the resources:

```bash
kubectl get deployments
kubectl get pods
kubectl get services
```

### 6.3 Creating an ALB through Ingress

Create `ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi-ingress
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80}]'
spec:
  ingressClassName: alb
  rules:
    - http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: fastapi-service
                port:
                  number: 80
```

Apply it:

```bash
kubectl apply -f ingress.yaml
```

Watch the Ingress:

```bash
kubectl get ingress -w
```

Once provisioning completes:

```bash
kubectl describe ingress fastapi-ingress
```

The Ingress should eventually receive an ALB DNS hostname.

Test the application:

```bash
ALB_DNS=$(kubectl get ingress fastapi-ingress \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

curl "http://${ALB_DNS}/"

curl "http://${ALB_DNS}/health"
```

### 6.4 Instance targets versus IP targets

The AWS Load Balancer Controller supports two target modes for ALB.

Instance target mode

Node-based

```text
ALB
 |
Target Group
 |
EKS Worker Node
 |
NodePort
 |
Kubernetes Service
 |
Pod
```

* Registers worker nodes.

* Uses NodePort to reach Kubernetes Services.

* Requires a compatible NodePort or LoadBalancer Service.

IP target mode

Pod-based

```text
ALB
 |
Target Group
 |
Pod Private IP
 |
Application Container
```

* Registers individual Pod IP addresses.

* Sends traffic directly to Pods.

* Required for Fargate workloads.

* Avoids the additional NodePort forwarding path.

The distinction is important when designing EKS networking. For Fargate, IP target mode is required. Amazon EKS +1

### 7\. NLB integration with Kubernetes Services

ALB is primarily designed for HTTP/HTTPS routing. NLB is appropriate when you need Layer 4 connectivity.

Common use cases include:

* TCP applications.

* UDP applications.

* gRPC deployments where network-level forwarding is appropriate.

* Applications requiring static IP addresses.

* Services requiring client IP preservation.

* Private network services.

### 7.1 NLB-backed Service

Create `nlb-service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: fastapi-nlb
  annotations:
    service.beta.kubernetes.io/aws-load-balancer-type: "external"
    service.beta.kubernetes.io/aws-load-balancer-nlb-target-type: "ip"
    service.beta.kubernetes.io/aws-load-balancer-scheme: "internet-facing"
spec:
  type: LoadBalancer
  selector:
    app: fastapi
  ports:
    - name: http
      port: 80
      targetPort: 8000
      protocol: TCP
```

Apply it:

```bash
kubectl apply -f nlb-service.yaml
```

Check the Service:

```bash
kubectl get svc fastapi-nlb -w
```

Retrieve its hostname:

```bash
NLB_DNS=$(kubectl get svc fastapi-nlb \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

curl "http://${NLB_DNS}/"
```

The controller provisions an NLB and registers the appropriate targets.

### 7.2 NLB target types

| Target type | Traffic path                | Main characteristic  |
| ----------- | --------------------------- | -------------------- |
| Instance    | NLB → Node → NodePort → Pod | Uses worker nodes    |
| IP          | NLB → Pod IP                | Direct Pod targeting |

IP targets are particularly useful with Fargate and when you want to avoid the NodePort forwarding path.

The AWS Load Balancer Controller supports both modes, subject to networking and workload requirements. Amazon EKS +1

### 7.3 ALB versus NLB in EKS

| Feature             | ALB                       | NLB                  |
| ------------------- | ------------------------- | -------------------- |
| Layer               | Layer 7                   | Layer 4              |
| Kubernetes resource | Ingress                   | LoadBalancer Service |
| Protocols           | HTTP, HTTPS               | TCP, UDP, TLS        |
| Path routing        | Yes                       | No                   |
| Host routing        | Yes                       | No                   |
| Target types        | Instance, IP              | Instance, IP         |
| Typical use         | Web applications and APIs | Network services     |

### 8\. Readiness probes versus load-balancer health checks

This is one of the most important operational topics in containerized load balancing.

Kubernetes and AWS use different health-check mechanisms.

### 8.1 Kubernetes readiness probes

A readiness probe determines whether a Pod is ready to receive traffic.

Example:

```yaml
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 5
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 3
```

If the readiness probe fails:

* The Pod remains running.

* The Pod is marked not ready.

* The Pod is removed from the ready endpoints used by Services.

* Kubernetes avoids sending normal Service traffic to it.

Readiness is different from liveness:

| Probe     | Purpose                                 | Failure behavior                           |
| --------- | --------------------------------------- | ------------------------------------------ |
| Readiness | Can this application receive traffic?   | Removes Pod from ready endpoints           |
| Liveness  | Is this container still functioning?    | May restart the container                  |
| Startup   | Has this application finished starting? | Delays other probes until startup succeeds |

### 8.2 AWS target-group health checks

AWS ALB independently checks registered targets.

For example:

```text
Protocol: HTTP
Path: /health
Port: traffic-port
Interval: 30 seconds
Timeout: 5 seconds
Healthy threshold: 2
Unhealthy threshold: 2
```

These checks determine whether the load balancer should send traffic to the target.

A Pod can be Kubernetes-ready but not yet healthy in the ALB target group.

This can happen because:

* Kubernetes readiness succeeds.

* The Pod is added to an EndpointSlice.

* The controller discovers the Pod.

* The controller registers the Pod IP with the ALB.

* ALB health checks begin.

* The target eventually becomes healthy.

The two health systems are related, but they do not operate on exactly the same timeline.

### 8.3 Pod Readiness Gates

Pod Readiness Gates solve an important deployment problem.

Suppose Kubernetes considers a new Pod ready before the ALB has finished registering it.

During a rolling deployment, Kubernetes might terminate an old Pod while the new Pod is not yet receiving ALB traffic.

This can temporarily reduce application availability.

Pod Readiness Gates allow additional readiness conditions to be attached to Pods.

With AWS Load Balancer Controller, the Pod can remain unready until its ALB target is healthy.

Conceptually:

```text
New Pod Created
      |
      v
Kubernetes Readiness Probe
      |
      v
Pod Ready Internally
      |
      v
ALB Target Registration
      |
      v
ALB Health Check
      |
      v
Target Healthy
      |
      v
Readiness Gate Satisfied
      |
      v
Pod Fully Ready
      |
      v
Old Pod Can Be Terminated
```

This is particularly valuable for rolling deployments.

AWS recommends using readiness gates when you need to coordinate Pod readiness with external load-balancer target health. Amazon EKS +1

### 8.4 Graceful termination and connection draining

Kubernetes also needs to coordinate application shutdown with load-balancer deregistration.

A Pod should not immediately terminate while it is processing active requests.

Relevant mechanisms include:

* `terminationGracePeriodSeconds`.

* `preStop` lifecycle hooks.

* Kubernetes endpoint removal.

* ALB target deregistration delay.

* NLB connection draining behavior.

Example:

```yaml
spec:
  terminationGracePeriodSeconds: 60
  containers:
    - name: fastapi
      lifecycle:
        preStop:
          exec:
            command: ["/bin/sh", "-c", "sleep 10"]
```

The delay gives the system time to remove the endpoint from service routing before the process exits.

However, `sleep 10` is only a simplified example. A production application should implement graceful shutdown and stop accepting new requests while allowing in-flight requests to finish.

Important: A `preStop` hook alone does not guarantee zero downtime. The termination grace period, endpoint propagation, target deregistration, application shutdown, and load-balancer delay must be designed together.

### 9\. Container autoscaling and rolling deployments

Load balancing and autoscaling solve different problems, but they work together.

* Load balancing distributes incoming traffic.

* Autoscaling adjusts the number of application instances or containers.

* Health checks prevent traffic from reaching unhealthy targets.

* Deployment strategies replace application versions while maintaining availability.

### 9.1 ECS Service Auto Scaling

ECS Service Auto Scaling can adjust the desired number of tasks based on CloudWatch metrics.

Common scaling metrics include:

* ECSServiceAverageCPUUtilization.

* ECSServiceAverageMemoryUtilization.

* ALBRequestCountPerTarget.

For example:

```text
Incoming Traffic Increases
          |
          v
ALB Request Count Increases
          |
          v
CloudWatch Metric
          |
          v
Application Auto Scaling
          |
          v
ECS Desired Count Increases
          |
          v
New ECS Tasks Start
          |
          v
ALB Registers New Targets
```

A target-tracking scaling policy might maintain average CPU utilization around 60%.

Pulumi Python example:

```python
import pulumi
import pulumi_aws as aws

scalable_target = aws.appautoscaling.Target(
    "ecs-scalable-target",
    max_capacity=6,
    min_capacity=2,
    resource_id=pulumi.Output.concat(
        "service/",
        cluster.name,
        "/",
        service.name,
    ),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)

scaling_policy = aws.appautoscaling.Policy(
    "ecs-cpu-scaling",
    policy_type="TargetTrackingScaling",
    resource_id=scalable_target.resource_id,
    scalable_dimension=scalable_target.scalable_dimension,
    service_namespace=scalable_target.service_namespace,
    target_tracking_scaling_policy_configuration={
        "target_value": 60,
        "predefined_metric_specification": {
            "predefined_metric_type": "ECSServiceAverageCPUUtilization",
        },
        "scale_in_cooldown": 120,
        "scale_out_cooldown": 60,
    },
)
```

This assumes `cluster` and `service` are ECS resources already declared in the same Pulumi program.

### 9.2 EKS Horizontal Pod Autoscaler

EKS workloads can scale using Kubernetes Horizontal Pod Autoscaler (HPA).

Example:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: fastapi-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: fastapi
  minReplicas: 2
  maxReplicas: 10
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
```

Apply:

```bash
kubectl apply -f hpa.yaml
```

Inspect scaling:

```bash
kubectl get hpa
kubectl describe hpa fastapi-hpa
```

HPA requires resource metrics, normally provided through Metrics Server for CPU and memory resource metrics.

Remember that HPA scales Pods, not necessarily worker-node capacity. If the cluster lacks resources to schedule new Pods, you also need node-capacity scaling, such as Cluster Autoscaler or Karpenter.

### 9.3 Rolling deployments in Kubernetes

A Deployment can gradually replace old Pods with new Pods.

Example:

```yaml
spec:
  replicas: 4
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

This configuration allows one additional Pod during deployment and prevents the desired number of available replicas from decreasing during the rollout, subject to readiness and scheduling constraints.

Check the rollout:

```bash
kubectl rollout status deployment/fastapi

kubectl rollout history deployment/fastapi

kubectl get pods -w
```

Roll back:

```bash
kubectl rollout undo deployment/fastapi
```

### 9.4 ECS versus EKS scaling

| Capability                 | ECS                          | EKS                            |
| -------------------------- | ---------------------------- | ------------------------------ |
| Application scaling        | ECS Service Auto Scaling     | HPA                            |
| CPU/memory scaling         | CloudWatch metrics           | Kubernetes metrics             |
| Node capacity scaling      | EC2 Auto Scaling             | Cluster Autoscaler / Karpenter |
| Load-balancer registration | ECS service integration      | AWS Load Balancer Controller   |
| Deployment management      | ECS deployment configuration | Kubernetes Deployment          |
| Health management          | Container and ELB checks     | Probes and ELB checks          |

### 10\. Hands-on labs

We will now implement the concepts through five labs.

Lab environment

| Component               | Technology          |
| ----------------------- | ------------------- |
| Infrastructure as Code  | Pulumi Python       |
| Container application   | FastAPI             |
| Container registry      | Amazon ECR          |
| Container orchestration | ECS Fargate and EKS |
| Load balancing          | ALB and NLB         |
| Container image         | Docker              |
| Kubernetes deployment   | kubectl             |
| Package management      | Helm                |
| CLI                     | AWS CLI             |
| Shell                   | Bash                |

AWS region: `eu-west-2` in the examples. Change it if your existing infrastructure uses another region.

Important: The ECS lab creates its own resources. For the EKS labs, we'll assume you have an operational EKS cluster from the previous EKS modules.

### Lab 1 — Deploy FastAPI to ECS Fargate behind an ALB using Pulumi

Main lab

### Objective

Build a complete deployment where:

* FastAPI runs inside Docker containers.

* The image is stored in Amazon ECR.

* ECS Fargate runs multiple application tasks.

* An ALB distributes incoming traffic.

* ECS automatically registers and deregisters task IPs.

* Health checks verify application availability.

### Step 1. Create the FastAPI application

Create the project:

```bash
mkdir aws-ecs-alb-lab
cd aws-ecs-alb-lab

mkdir app
```

Create `app/main.py`:

```python
from fastapi import FastAPI
import os

app = FastAPI()

VERSION = os.getenv("APP_VERSION", "1.0.0")

@app.get("/")
def root():
    return {
        "message": "Hello from ECS Fargate",
        "version": VERSION,
    }

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/info")
def info():
    return {
        "application": "FastAPI",
        "version": VERSION,
        "environment": os.getenv("ENVIRONMENT", "development"),
    }
```

Create `app/requirements.txt`:

```text
fastapi
uvicorn[standard]
```

### Step 2. Create the Dockerfile

Create `Dockerfile`:

```dockerfile
FROM python:3.14-slim

WORKDIR /app

COPY app/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

ENV APP_VERSION=1.0.0

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and test locally:

```bash
docker build -t fastapi-ecs:1.0 .

docker run -d \
  --name fastapi-test \
  -p 8000:8000 \
  fastapi-ecs:1.0

curl http://localhost:8000/

curl http://localhost:8000/health
```

Clean up:

```bash
docker rm -f fastapi-test
```

### Step 3. Create an ECR repository

```bash
aws ecr create-repository \
  --repository-name fastapi-ecs \
  --region eu-west-2
```

Retrieve the account ID:

```bash
ACCOUNT_ID=$(aws sts get-caller-identity \
  --query Account \
  --output text)

REGION=eu-west-2

ECR_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/fastapi-ecs"
```

Authenticate Docker:

```bash
aws ecr get-login-password \
  --region "$REGION" \
  | docker login \
      --username AWS \
      --password-stdin \
      "${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"
```

Build, tag, and push:

```bash
docker build -t fastapi-ecs:1.0 .

docker tag fastapi-ecs:1.0 "$ECR_URI:1.0"

docker push "$ECR_URI:1.0"
```

### Step 4. Configure Pulumi

Initialize the project:

```bash
pulumi new aws-python
```

Install the AWS provider if needed:

```bash
uv add pulumi-aws
```

Set the AWS region:

```bash
pulumi config set aws:region eu-west-2
```

We will provision:

```text
VPC
├── Public Subnets (2 AZs)
│   └── Application Load Balancer
│
└── Private Subnets (2 AZs)
    └── ECS Fargate Tasks
        ├── Task 1
        └── Task 2
```

For a production deployment, private Fargate tasks need an outbound path to pull images and communicate with required AWS services. You can use NAT gateways or appropriate VPC endpoints.

### Step 5. Define the infrastructure

Create `__main__.py`.

The following is a compact Pulumi implementation of the essential architecture. It uses existing VPC subnet IDs supplied through configuration, keeping networking reusable rather than duplicating the VPC from earlier modules.

```python
import json
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
public_subnets = config.require_object("publicSubnetIds")
private_subnets = config.require_object("privateSubnetIds")

image = config.require("image")

# -------------------------
# Security Groups
# -------------------------

alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    vpc_id=vpc_id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)

task_sg = aws.ec2.SecurityGroup(
    "task-sg",
    vpc_id=vpc_id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "security_groups": [alb_sg.id],
        }
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
)

# -------------------------
# ALB
# -------------------------

alb = aws.lb.LoadBalancer(
    "fastapi-alb",
    load_balancer_type="application",
    internal=False,
    security_groups=[alb_sg.id],
    subnets=public_subnets,
)

target_group = aws.lb.TargetGroup(
    "fastapi-targets",
    port=8000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc_id,
    health_check={
        "enabled": True,
        "path": "/health",
        "protocol": "HTTP",
        "matcher": "200",
        "interval": 30,
        "timeout": 5,
        "healthy_threshold": 2,
        "unhealthy_threshold": 3,
    },
)

listener = aws.lb.Listener(
    "http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        {
            "type": "forward",
            "target_group_arn": target_group.arn,
        }
    ],
)

# -------------------------
# ECS Cluster
# -------------------------

cluster = aws.ecs.Cluster("fastapi-cluster")

# -------------------------
# IAM Execution Role
# -------------------------

execution_role = aws.iam.Role(
    "ecs-execution-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole",
        }],
    }),
)

execution_policy = aws.iam.RolePolicyAttachment(
    "ecs-execution-policy",
    role=execution_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AmazonECSTaskExecutionRolePolicy"
    ),
)

# -------------------------
# Task Definition
# -------------------------

task_definition = aws.ecs.TaskDefinition(
    "fastapi-task",
    family="fastapi",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=execution_role.arn,
    container_definitions=pulumi.Output.json_dumps([
        {
            "name": "fastapi",
            "image": image,
            "essential": True,
            "portMappings": [{
                "containerPort": 8000,
                "protocol": "tcp",
            }],
        }
    ]),
)

# -------------------------
# ECS Service
# -------------------------

service = aws.ecs.Service(
    "fastapi-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=2,
    launch_type="FARGATE",
    health_check_grace_period_seconds=60,
    deployment_minimum_healthy_percent=100,
    deployment_maximum_percent=200,
    deployment_circuit_breaker={
        "enable": True,
        "rollback": True,
    },
    network_configuration={
        "subnets": private_subnets,
        "security_groups": [task_sg.id],
        "assign_public_ip": False,
    },
    load_balancers=[{
        "target_group_arn": target_group.arn,
        "container_name": "fastapi",
        "container_port": 8000,
    }],
    opts=pulumi.ResourceOptions(
        depends_on=[
            listener,
            execution_policy,
        ]
    ),
)

pulumi.export("alb_dns", alb.dns_name)
pulumi.export("ecs_cluster", cluster.name)
pulumi.export("ecs_service", service.name)
```

Configure the infrastructure:

```bash
pulumi config set vpcId vpc-xxxxxxxx

pulumi config set --path \
  'publicSubnetIds[0]' subnet-public-a

pulumi config set --path \
  'publicSubnetIds[1]' subnet-public-b

pulumi config set --path \
  'privateSubnetIds[0]' subnet-private-a

pulumi config set --path \
  'privateSubnetIds[1]' subnet-private-b

pulumi config set image "$ECR_URI:1.0"
```

The execution role allows ECS to retrieve the image and send logs when configured. It is not a replacement for a separate application task role if your FastAPI application needs AWS API permissions.

Deploy:

```bash
pulumi preview

pulumi up
```

### Step 6. Test the deployment

Retrieve the ALB DNS name:

```bash
ALB_DNS=$(pulumi stack output alb_dns)
```

Test:

```bash
curl "http://${ALB_DNS}/"

curl "http://${ALB_DNS}/health"

curl "http://${ALB_DNS}/info"
```

Inspect the ECS service:

```bash
aws ecs describe-services \
  --cluster "$(pulumi stack output ecs_cluster)" \
  --services "$(pulumi stack output ecs_service)" \
  --region eu-west-2
```

Inspect target health:

```bash
TARGET_GROUP_ARN=$(aws elbv2 describe-target-groups \
  --names fastapi-targets \
  --region eu-west-2 \
  --query 'TargetGroups[0].TargetGroupArn' \
  --output text)

aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --region eu-west-2
```

You should see two healthy targets after the service stabilizes.

### Step 7. Configure ECS autoscaling

Create the scaling target and CPU tracking policy using the Pulumi example in Section 9.1.

After deployment, inspect the scaling configuration:

```bash
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --region eu-west-2
```

Inspect scaling policies:

```bash
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs \
  --region eu-west-2
```

### Step 8. Clean up

```bash
pulumi destroy
```

The ECR repository is a separately managed resource in this example. Remove it after confirming you no longer need its images:

```bash
aws ecr delete-repository \
  --repository-name fastapi-ecs \
  --force \
  --region eu-west-2
```

Important networking consideration: The compact example assumes the supplied subnets already have suitable routing, and that your ECS tasks can reach ECR and the required AWS APIs. It also assumes the ALB can reach the private task ENIs. A production implementation should explicitly manage NAT/VPC endpoints, logging, IAM least privilege, deletion protection, and HTTPS.

### Lab 2 — ECS target registration, health checks, and autoscaling

ECS operations

### Objective

Understand how ECS and ALB coordinate when tasks are created, become healthy, and are removed.

### Step 1. Inspect registered targets

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --region eu-west-2
```

Observe:

* Target IP addresses.

* Target health states.

* Health-check failure reasons.

* Registration and deregistration behavior.

### Step 2. Increase the desired task count

```bash
aws ecs update-service \
  --cluster fastapi-cluster \
  --service fastapi-service \
  --desired-count 4 \
  --region eu-west-2
```

Wait for stabilization:

```bash
aws ecs wait services-stable \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --region eu-west-2
```

Inspect target registration again:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --region eu-west-2
```

You should eventually see four healthy targets.

### Step 3. Test an unhealthy deployment

Deploy an application version with an invalid health endpoint or configure an incorrect target-group health-check path.

Observe:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --region eu-west-2
```

Then inspect ECS deployment events:

```bash
aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --region eu-west-2 \
  --query 'services[0].events[:10]'
```

Understand how the ECS scheduler responds to unhealthy tasks.

### Step 4. Test rolling deployment

Build a new version:

```bash
docker build -t fastapi-ecs:2.0 .

docker tag fastapi-ecs:2.0 "$ECR_URI:2.0"

docker push "$ECR_URI:2.0"
```

Update Pulumi configuration:

```bash
pulumi config set image "$ECR_URI:2.0"

pulumi up
```

Observe:

* New task creation.

* Target registration.

* Health-check completion.

* Old task deregistration.

* Deployment stabilization.

Expected outcome: You understand how ECS deployments and ALB target health work together rather than treating the load balancer as an independent component.

### Lab 3 — Deploy an EKS application behind an ALB

EKS · ALB Ingress

### Objective

Deploy an application into your existing EKS cluster and expose it through an ALB managed by AWS Load Balancer Controller.

### Step 1. Connect to EKS

```bash
aws eks update-kubeconfig \
  --name my-eks-cluster \
  --region eu-west-2

kubectl get nodes
```

Check the controller:

```bash
kubectl get pods \
  -n kube-system \
  -l app.kubernetes.io/name=aws-load-balancer-controller
```

### Step 2. Deploy the application

Use the FastAPI Deployment and ClusterIP Service manifests from Section 6.2.

```bash
kubectl apply -f deployment.yaml

kubectl rollout status deployment/fastapi

kubectl get pods -o wide
```

### Step 3. Deploy the Ingress

```bash
kubectl apply -f ingress.yaml
```

Watch the ALB provisioning:

```bash
kubectl get ingress -w
```

Inspect the generated resources:

```bash
kubectl describe ingress fastapi-ingress

kubectl get targetgroupbindings -A
```

The controller creates the ALB, listener, and target group and manages Pod registration.

### Step 4. Test traffic

```bash
ALB_DNS=$(kubectl get ingress fastapi-ingress \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')

curl "http://${ALB_DNS}/"
```

Check the AWS target group:

```bash
aws elbv2 describe-target-groups \
  --region eu-west-2 \
  --query 'TargetGroups[*].[TargetGroupName,TargetType]'
```

You should find an IP-based target group associated with the application.

### Step 5. Scale the application

```bash
kubectl scale deployment fastapi --replicas=5
```

Inspect the Pods:

```bash
kubectl get pods -o wide
```

Inspect target registration:

```bash
kubectl get targetgroupbindings -A

kubectl get ingress fastapi-ingress
```

Verify that the new Pod IPs become healthy targets.

### Lab 4 — Configure an NLB-backed Kubernetes Service

EKS · NLB

### Objective

Expose a Kubernetes application through an NLB instead of an ALB.

### Step 1. Apply the NLB Service

Use the `nlb-service.yaml` manifest from Section 7.1.

```bash
kubectl apply -f nlb-service.yaml
```

Wait for provisioning:

```bash
kubectl get service fastapi-nlb -w
```

### Step 2. Retrieve the NLB hostname

```bash
NLB_DNS=$(kubectl get service fastapi-nlb \
  -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
```

Test:

```bash
curl "http://${NLB_DNS}/"

curl "http://${NLB_DNS}/health"
```

### Step 3. Inspect the NLB

```bash
aws elbv2 describe-load-balancers \
  --region eu-west-2 \
  --query 'LoadBalancers[*].[LoadBalancerName,Type,DNSName]'
```

Find the target groups:

```bash
aws elbv2 describe-target-groups \
  --region eu-west-2 \
  --query 'TargetGroups[*].[TargetGroupName,TargetType,Protocol,Port]'
```

### Step 4. Compare ALB and NLB

Compare the two architectures:

```text
ALB:
Client → ALB → HTTP Routing → Target Group → Pod

NLB:
Client → NLB → TCP Forwarding → Target Group → Pod
```

Understand why you would use ALB for HTTP application routing and NLB for network-level traffic distribution.

### Lab 5 — Rolling deployments, readiness, and target-health troubleshooting

Advanced operations

### Objective

Understand one of the most important problems in Kubernetes production environments: a Pod can be ready inside Kubernetes while its load-balancer target is not yet healthy.

### Step 1. Configure rolling deployment behavior

Update your FastAPI Deployment:

```yaml
spec:
  replicas: 4
  minReadySeconds: 10
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
```

Apply:

```bash
kubectl apply -f deployment.yaml
```

### Step 2. Observe Pod readiness

```bash
kubectl get pods -w
```

Inspect Pod conditions:

```bash
kubectl describe pod POD_NAME
```

Look for:

* Initialized.

* ContainersReady.

* Ready.

* Any additional readiness-gate conditions.

### Step 3. Inspect ALB target health

Retrieve the target group ARN associated with your Ingress, then:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --region eu-west-2
```

Compare the Kubernetes Pod readiness state with the ALB target state.

### Step 4. Configure Pod Readiness Gates

For the AWS Load Balancer Controller, readiness gates can be injected into Pods when the appropriate target group and namespace prerequisites are satisfied.

One important requirement is that the namespace must have the readiness-gate injection label before the Deployment creates its Pods.

Example:

```bash
kubectl label namespace default \
  elbv2.k8s.aws/pod-readiness-gate-inject=enabled
```

For an existing Deployment, recreate its Pods after enabling the label so the admission webhook can inject the readiness gates.

Inspect the resulting Pod:

```bash
kubectl get pod POD_NAME -o yaml
```

Look for:

```yaml
status:
  conditions:
    - type: target-health.elbv2.k8s.aws/...
      status: "True"
```

The exact condition name is generated for the associated target group.

### Step 5. Simulate an unhealthy application

Temporarily change the health endpoint or configure an incorrect ALB health-check path.

Inspect:

```bash
kubectl get pods

kubectl get endpointslices

kubectl describe ingress fastapi-ingress

kubectl logs \
  -n kube-system \
  deployment/aws-load-balancer-controller \
  --tail=100
```

Inspect AWS target health:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --region eu-west-2
```

### Step 6. Restore the application

Restore the correct health endpoint and configuration.

```bash
kubectl rollout restart deployment/fastapi

kubectl rollout status deployment/fastapi
```

Verify that:

* New Pods become ready.

* ALB targets become healthy.

* Old Pods are terminated safely.

* Application traffic remains available.

AWS discusses this synchronization problem and readiness gates in its [EKS load-balancing best practices](https://docs.aws.amazon.com/eks/latest/best-practices/load-balancing.html?utm_source=chatgpt.com).

### 11\. Troubleshooting reference

These are common problems you should be able to diagnose without relying exclusively on the AWS console.

| Problem                            | Possible cause                                             | Where to investigate                   |
| ---------------------------------- | ---------------------------------------------------------- | -------------------------------------- |
| ECS targets unhealthy              | Incorrect health endpoint or security group                | Target group health and ECS events     |
| ECS tasks fail to start            | Image pull or IAM execution-role issue                     | ECS stopped reasons and task logs      |
| ECS tasks remain pending           | Insufficient resources or subnet IP exhaustion             | ECS service events and VPC             |
| ALB Ingress has no hostname        | Controller IAM, subnet discovery, or configuration problem | Controller logs                        |
| EKS targets not registered         | Incorrect target mode or controller permissions            | TargetGroupBinding and controller logs |
| NLB Service stuck pending          | Subnet, IAM, or security-group issue                       | Kubernetes events and controller logs  |
| HTTP 502                           | Backend connection or application response problem         | ALB logs and application logs          |
| HTTP 503                           | No healthy targets or unavailable backend capacity         | Target-group health                    |
| Rolling deployment causes downtime | Incorrect readiness or draining configuration              | Pod conditions and target health       |
| New Pods receive no traffic        | Pod not ready or ALB registration incomplete               | EndpointSlices and target groups       |

Useful commands:

```bash
# ECS service events
aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --region eu-west-2 \
  --query 'services[0].events[:15]'

# ECS stopped tasks
aws ecs list-tasks \
  --cluster fastapi-cluster \
  --desired-status STOPPED \
  --region eu-west-2

# Kubernetes events
kubectl get events -A \
  --sort-by='.lastTimestamp'

# Controller logs
kubectl logs \
  -n kube-system \
  deployment/aws-load-balancer-controller \
  --tail=200

# Kubernetes endpoints
kubectl get endpointslices -A

# Kubernetes Ingress
kubectl describe ingress fastapi-ingress

# Target health
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --region eu-west-2
```

### 12\. Important architectural decisions

Before moving to the next module, understand these design decisions.

| Requirement                                  | Recommended approach                                          |
| -------------------------------------------- | ------------------------------------------------------------- |
| Public FastAPI application on ECS Fargate    | ALB + IP target group                                         |
| Multiple HTTP microservices on ECS           | ALB + multiple target groups and listener rules               |
| ECS on EC2 using bridge networking           | ALB + instance targets and dynamic host ports                 |
| Public HTTP application on EKS               | ALB + Ingress                                                 |
| EKS application running on Fargate           | ALB + IP targets                                              |
| TCP application on EKS                       | NLB + LoadBalancer Service                                    |
| Internal microservice communication          | ClusterIP                                                     |
| Global application traffic                   | Route 53 / Global Accelerator with regional load balancers    |
| Zero-downtime Kubernetes rolling deployments | Readiness probes + Pod Readiness Gates + appropriate draining |

### 13\. Official documentation and further reading

These AWS references are particularly useful for this module:

* [Amazon ECS service definition parameters](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/service_definition_parameters.html?utm_source=chatgpt.com) — Load-balancer configuration, deployment parameters, and health-check grace periods.

* [ALB target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html?utm_source=chatgpt.com) — Target registration and target types.

* [Install AWS Load Balancer Controller](https://docs.aws.amazon.com/eks/latest/userguide/lbc-helm.html?utm_source=chatgpt.com) — IAM and Helm installation.

* [ALB Ingress on Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/alb-ingress.html?utm_source=chatgpt.com) — Ingress configuration and target modes.

* [NLB on Amazon EKS](https://docs.aws.amazon.com/eks/latest/userguide/network-load-balancing.html?utm_source=chatgpt.com) — Kubernetes Service integration.

* [AWS EKS load-balancing best practices](https://docs.aws.amazon.com/eks/latest/best-practices/load-balancing.html?utm_source=chatgpt.com) — Health checks, Pod lifecycle, and readiness gates.

* [ECS blue/green deployment resources](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/alb-resources-for-blue-green.html?utm_source=chatgpt.com) — ALB target groups and deployment traffic shifting.

### Module 6 completion

By completing these five labs, you should be able to build and operate two different container load-balancing architectures:

ECS architecture

Client → ALB → ECS Target Group → Fargate Tasks

EKS architecture

Client → ALB → Pod IP Targets → Kubernetes Pods

Network-level EKS architecture

Client → NLB → Pod IP Targets → Kubernetes Pods

The most important concepts to retain are:

* ECS automatically manages target registration for associated services.

* Fargate generally requires IP target groups.

* AWS Load Balancer Controller translates Kubernetes resources into AWS load-balancing infrastructure.

* ALB Ingress is appropriate for HTTP/HTTPS routing, while NLB-backed Services provide Layer 4 connectivity.

* Kubernetes readiness and AWS target health are separate mechanisms.

* Readiness Gates help coordinate Kubernetes rolling deployments with ALB target registration.

* Graceful termination and connection draining are essential for reliable deployments.

Next module: Module 7 — Observability, Performance, and Cost Optimization.
