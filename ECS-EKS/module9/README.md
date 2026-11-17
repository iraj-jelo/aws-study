Worked for 58s

### Module 9 — Capstone: ECS and EKS Production Deployment Strategy

AWS ECS/EKS Course · Module 9 of 9 · Capstone Lab

### 1\. Learning objectives

By the end of this module, you will be able to:

* Design and deploy the same FastAPI application on Amazon ECS Fargate and Amazon EKS.

* Provision and manage AWS infrastructure using Pulumi with Python, without Terraform.

* Separate development and production environments using Pulumi stacks and reusable components.

* Implement container image delivery through Amazon ECR, HTTPS access, health checks, logging, and scaling.

* Design repeatable CI/CD workflows and understand blue/green and canary deployment strategies.

* Apply least-privilege IAM, private networking, secret management, and operational monitoring.

* Compare ECS and EKS based on operational overhead, flexibility, reliability, and total cost of ownership.

* Make an architecture recommendation based on application and team requirements.

### 2\. Capstone architecture

We will deploy one FastAPI application using two alternative architectures. Both deployments use the same source code and container image so that the comparison focuses on the orchestration platforms rather than application differences.

FastAPI application

Docker · Health endpoints · Structured logs

Amazon ECR

Versioned container images · Image scanning · Immutable digests

Two independent deployment paths

### Architecture A: ECS

![Getting Started with Terraform Provisioners: File, Local-Exec & Remote-Exec Explained | by Kajal | Medium](https://images.openai.com/static-rsc-4/FnwRJd3IhbPVlaWGl6rwCC5Z5i2MUzZynSy7vb_DlZLCcTYV8j5Viz86UM98ser6Zon2mVyRGrdPCFlE6YQA4RGtIU2JqrQMcp5F2NYQCI4Sn5YKuYeOoZnq-dGSgXEfRGhJiYs6aG9P5rR9ost0DjwzSUInvMR6CzmnSP8ARB5YCVQAZ5DqMkAz1xGTvAUZ?purpose=fullsize)

Route 53 / ACM HTTPS

Application Load Balancer

ECS Fargate service

Private tasks · IAM task role · CloudWatch Logs · ECS Service Auto Scaling

### Architecture B: EKS

![Journey of the web request from a laptop to containerized application | by Oleksandr Pochapskyy | Medium](https://images.openai.com/static-rsc-4/txAJxh0s7qJfxHV3hPJ66BDEUf9OZnIofbK2aKWqHhK6injURMG_9ra7G6MZFVd_KsMtge24Vf2QOdrFE3qshxAbGt1APNskbgC4S24PE-LkW6SUzQ90BVTfx0gtiB-SAUrAfBWBRZbcGQbkBilgwTJ30k8ZFy7jyjU2C12aRSvBtbS5rFGblvBNT0PSgNya?purpose=fullsize)

Route 53 / ACM HTTPS

Application Load Balancer

EKS Deployment and Service

Managed nodes · Pod identity · CloudWatch observability · HPA

These are logical architecture views. The lab will create the actual resources through Pulumi, and the EKS ingress path will use the AWS Load Balancer Controller.

### Shared and platform-specific resources

| Shared resources     | ECS-specific resources        | EKS-specific resources            |
| -------------------- | ----------------------------- | --------------------------------- |
| VPC and subnets      | ECS cluster and service       | EKS cluster and node group        |
| ECR repository       | Task definition               | Kubernetes Deployment and Service |
| Route 53 and ACM     | Task execution and task roles | Pod Identity or IRSA              |
| ALB and CloudWatch   | ECS service scaling           | HPA and cluster capacity          |
| Pulumi configuration | ECS deployment strategy       | Kubernetes rollout strategy       |

For a fair comparison, use the same application image, region, traffic assumptions, and comparable availability targets. Resource configurations may still differ because ECS and EKS have different operational requirements.

### 3\. Choosing the right AWS container platform

The goal is not to prove that one platform is universally better. It is to understand which operational model best fits the workload.

| Deployment option | Best suited for                                                                | Main trade-off                                                                     |
| ----------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------- |
| ECS Fargate       | APIs, web services, event-driven containers                                    | Simple operations, but less control over the underlying compute                    |
| ECS on EC2        | Predictable workloads requiring host-level control or specialized capacity     | You manage the EC2 capacity and its lifecycle                                      |
| EKS managed nodes | Kubernetes workloads needing ecosystem integrations and scheduling flexibility | More operational complexity, including cluster and add-on management               |
| EKS Fargate       | Selected Kubernetes workloads without managing worker nodes                    | Restricted workload and infrastructure capabilities compared with nodes you manage |

### Practical decision criteria

* Choose ECS Fargate when you want a straightforward AWS-native container platform with minimal infrastructure management.

* Choose ECS on EC2 when host-level customization, specialized instance capacity, or carefully optimized compute costs justify managing the fleet.

* Choose EKS managed nodes when Kubernetes APIs, Helm, Kubernetes controllers, advanced scheduling, or an established Kubernetes platform are important.

* Choose EKS Fargate when selected Kubernetes workloads benefit from serverless pod compute and fit Fargate's constraints.

Remember that EKS Fargate does not eliminate the EKS control plane, and it does not support every Kubernetes workload or DaemonSet-based operating model. Similarly, ECS Fargate removes host management but does not remove the need to manage networking, IAM, application health, deployments, or costs.

### 4\. Pulumi architecture and environment strategy

The capstone should reuse the infrastructure created in earlier modules rather than recreate the VPC, ECR repository, or EKS cluster unnecessarily.

The existing learning project uses:

* Project directory: `aws-containers`

* AWS region: `eu-west-2`

* Application: FastAPI

* Container port: `8000`

* Health endpoint: `/health`

* ECR repository: `fastapi-api`

* Existing development image: `fastapi-api:1.0.0`

* EKS cluster: `aws-containers-eks-dev`

* Kubernetes namespace: `applications`

* Kubernetes Deployment: `fastapi-api`

### 4.1 Recommended repository structure

```text
aws-containers/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
├── infrastructure/
│   ├── components/
│   │   ├── ecr.py
│   │   ├── ecs.py
│   │   └── eks.py
│   ├── Pulumi.yaml
│   ├── requirements.txt
│   └── __main__.py
└── .github/
    └── workflows/
        └── deploy.yml
```

Keep the ECS and EKS deployments independently deployable. They can share application code and ECR, but they should not have to update one another just because a deployment changes.

For an existing repository, retain your current component implementations and add only the missing resources. The code below illustrates the configuration and deployment workflow rather than replacing the previous modules wholesale.

### 4.2 Understand Pulumi stacks

A Pulumi stack is an independently configured instance of a project. For example, the `dev` and `prod` stacks can use the same infrastructure code but different settings.

Shared infrastructure code

Components, resources, dependencies, and deployment logic

dev

Lower capacity

Test deployments

Development configuration

prod

Higher availability

Controlled releases

Production configuration

Create a separate stack for the ECS deployment and another for EKS if that matches your existing project layout. Separate projects can also be appropriate when their resource lifecycles and ownership differ.

From the `infrastructure/` directory, inspect your current stacks:

```bash
pulumi stack ls
pulumi stack select dev
pulumi config
pulumi preview
```

If you use distinct stack names for the two platforms, select those exact existing names rather than creating duplicates. For example, you might use `ecs-dev` and `eks-dev` in separate projects.

Set the AWS region where it is not already configured:

```bash
pulumi config set aws:region eu-west-2
```

For a production environment, use separate configuration and appropriate access boundaries. Separate AWS accounts are preferable when stronger production isolation is required.

### 4.3 Configuration and secrets

Keep deployment-specific values out of the application and infrastructure source code.

Examples of ordinary configuration:

```bash
pulumi config set appPort 8000
pulumi config set environment dev
pulumi config set desiredCount 2
```

These keys must also be declared or read by your Pulumi program. Use names consistent with the configuration schema in your existing project.

For sensitive values, use Pulumi secret configuration:

```bash
pulumi config set --secret databasePassword 'replace-with-a-secure-value'
```

Do not commit plaintext credentials, exported secret values, or state files containing sensitive data. Prefer AWS IAM roles and temporary credentials for deployment and runtime access. For application secrets, use AWS Secrets Manager or another approved secret store rather than baking credentials into a container image.

### 4.4 Preview before applying

For every infrastructure change, follow this workflow:

```bash
pulumi preview
pulumi up
pulumi stack output
```

Review the preview for unintended replacements or deletions, particularly for the shared EKS cluster, ECR repository, VPC, and ALB.

Important: `pulumi up` applies changes to the selected stack. Do not select a shared stack casually, and do not destroy the existing development environment as part of this capstone.

### 5\. Lab 1 — Prepare the shared application image

The same image will be deployed on ECS and EKS. This helps ensure that application differences do not distort the comparison.

### Step 1: Inspect the application

From the project root:

```bash
cd aws-containers

sed -n '1,240p' app/main.py
cat app/Dockerfile
```

Verify that the application listens on port `8000` and exposes `/health`.

A minimal health endpoint could look like this:

```python
from fastapi import FastAPI

app = FastAPI(title="AWS Containers Capstone")

@app.get("/")
async def root():
    return {"service": "fastapi-api", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

If your application already implements these endpoints, keep it rather than overwriting it.

### Step 2: Build and test the image

```bash
docker build -t fastapi-api:1.0.0 ./app

docker run --rm -d \
  --name fastapi-capstone \
  -p 8000:8000 \
  fastapi-api:1.0.0

curl --fail http://localhost:8000/health

docker stop fastapi-capstone
```

Expected health response:

```json
{"status":"healthy"}
```

A successful local test confirms the image starts and responds to the health endpoint. It does not yet validate AWS networking or IAM.

### Step 3: Publish the image to ECR

Use the existing ECR repository from Module 2. Retrieve its URI from the Pulumi stack output, or inspect the repository using the AWS CLI.

```bash
aws ecr describe-repositories \
  --repository-names fastapi-api \
  --region eu-west-2 \
  --query 'repositories[0].repositoryUri' \
  --output text
```

Assign the actual returned URI to a shell variable:

```bash
export AWS_REGION="eu-west-2"
export ECR_URI="$(aws ecr describe-repositories \
  --repository-names fastapi-api \
  --region "$AWS_REGION" \
  --query 'repositories[0].repositoryUri' \
  --output text)"

export IMAGE_TAG="1.0.0"
```

Authenticate and push:

```bash
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login \
      --username AWS \
      --password-stdin "${ECR_URI%%/*}"

docker tag fastapi-api:1.0.0 "$ECR_URI:$IMAGE_TAG"
docker push "$ECR_URI:$IMAGE_TAG"
```

Confirm the image exists:

```bash
aws ecr describe-images \
  --repository-name fastapi-api \
  --region "$AWS_REGION" \
  --query 'imageDetails[].{Tags:imageTags,Digest:imageDigest}' \
  --output table
```

For production releases, prefer unique release tags and deploy using the verified image digest. Avoid relying on mutable tags such as `latest` to identify what is running.

### 6\. Lab 2 — Deploy the image on ECS Fargate

This lab reuses the ECS infrastructure from Modules 3 and 4. The target architecture is a private Fargate service behind an Application Load Balancer.

### Step 1: Update the ECS image

In your ECS component, make sure the task definition takes its image URI from configuration or the existing ECR component output rather than hard-coding the image.

A typical Pulumi Python task-definition fragment looks like this:

```python
import json
import pulumi_aws as aws

# image_uri should come from the existing ECR component
# or an explicit Pulumi configuration value.

task_definition = aws.ecs.TaskDefinition(
    "fastapi-api-task",
    family="fastapi-api",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.json_dumps([
        {
            "name": "fastapi-api",
            "image": image_uri,
            "essential": True,
            "portMappings": [
                {
                    "containerPort": 8000,
                    "protocol": "tcp",
                }
            ],
            "healthCheck": {
                "command": [
                    "CMD-SHELL",
                    "python -c \"import urllib.request; "
                    "urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)\" "
                    "|| exit 1",
                ],
                "interval": 30,
                "timeout": 5,
                "retries": 3,
                "startPeriod": 20,
            },
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": log_group.name,
                    "awslogs-region": "eu-west-2",
                    "awslogs-stream-prefix": "fastapi",
                },
            },
        }
    ]),
)
```

This is a task-definition fragment to integrate into the existing ECS component, not a standalone stack. It assumes that `pulumi`, the IAM roles, log group, and `image_uri` are already defined. The container image must include Python and the required application dependencies for the shown health-check command.

Keep the service's target group health check pointed at `/health`, and ensure the ALB security group can reach the task security group on port `8000`. The task execution role needs permission to pull the ECR image and write logs.

### Step 2: Deploy the ECS service

From the existing ECS infrastructure project:

```bash
pulumi stack select dev
pulumi preview
pulumi up
```

If your ECS project uses a different stack name, select that stack instead.

Inspect the running service:

```bash
aws ecs list-clusters --region eu-west-2

aws ecs list-services \
  --cluster YOUR_ECS_CLUSTER_NAME \
  --region eu-west-2
```

Replace `YOUR_ECS_CLUSTER_NAME` with the real cluster name. Then inspect task health:

```bash
aws ecs describe-services \
  --cluster YOUR_ECS_CLUSTER_NAME \
  --services YOUR_ECS_SERVICE_NAME \
  --region eu-west-2 \
  --query 'services[0].{Desired:desiredCount,Running:runningCount,Pending:pendingCount,Events:events[0:5]}' \
  --output json
```

### Step 3: Test the deployment

Retrieve the ALB DNS name from your Pulumi outputs or the EC2 load balancer API:

```bash
aws elbv2 describe-load-balancers \
  --region eu-west-2 \
  --query 'LoadBalancers[].{Name:LoadBalancerName,DNS:DNSName}' \
  --output table
```

Test the HTTP endpoint if your existing lab exposes HTTP:

```bash
curl --fail http://YOUR_ALB_DNS_NAME/health
```

If you configured HTTPS in Module 4, test the actual HTTPS hostname and certificate instead:

```bash
curl --fail https://YOUR_APPLICATION_DOMAIN/health
```

Use your configured DNS name, not the ALB's raw DNS name, for a certificate issued to your application domain.

### Step 4: Inspect scaling and logs

```bash
aws ecs describe-services \
  --cluster YOUR_ECS_CLUSTER_NAME \
  --services YOUR_ECS_SERVICE_NAME \
  --region eu-west-2
```

```bash
aws logs describe-log-groups \
  --region eu-west-2 \
  --log-group-name-prefix /ecs/
```

For this capstone, verify that the service can maintain its desired task count and that failed health checks lead to replacement or rollback behavior appropriate to the configured deployment strategy.

### 7\. Lab 3 — Deploy the same image on EKS

Reuse the cluster, namespace, and Kubernetes resources from Modules 5–8. Do not provision another cluster solely for the comparison.

### Step 1: Connect to the existing cluster

```bash
aws eks update-kubeconfig \
  --region eu-west-2 \
  --name aws-containers-eks-dev

kubectl config current-context
kubectl get nodes
kubectl get namespace applications
kubectl -n applications get deployment fastapi-api
```

If the namespace or Deployment has a different name in your existing stack, use the actual resource name.

### Step 2: Update the image

For a Kubernetes Deployment named `fastapi-api` in the `applications` namespace:

```bash
kubectl -n applications set image \
  deployment/fastapi-api \
  fastapi-api="$ECR_URI:$IMAGE_TAG"
```

This demonstrates a direct image update. In a Pulumi-managed production environment, update the image configuration in the Pulumi program and apply the change through Pulumi so that the live resource and declared infrastructure remain consistent.

Watch the rollout:

```bash
kubectl -n applications rollout status deployment/fastapi-api

kubectl -n applications get pods -o wide

kubectl -n applications describe deployment fastapi-api
```

Check the health endpoint through the configured ingress hostname:

```bash
curl --fail https://YOUR_APPLICATION_DOMAIN/health
```

If ECS and EKS use different hostnames, use each platform's hostname and TLS configuration. If they share one hostname, configure routing explicitly rather than allowing two unrelated DNS records to compete.

### Step 3: Verify scaling and health

```bash
kubectl -n applications get hpa
kubectl -n applications get pods
kubectl -n applications get events --sort-by=.lastTimestamp
```

If HPA is configured, inspect its metrics and scaling conditions. An HPA requires a working metrics source and appropriate CPU or memory requests; creating the HPA alone does not guarantee that it will scale.

For logs:

```bash
kubectl -n applications logs \
  deployment/fastapi-api \
  --all-pods=true \
  --prefix=true
```

For diagnosis:

```bash
kubectl -n applications describe pods
kubectl get events -A --sort-by=.lastTimestamp
```

Use CloudWatch or your configured observability stack to inspect historical metrics and logs; `kubectl logs` is mainly for current container output and may not preserve history after pod replacement.

### 8\. Lab 4 — Make the deployments repeatable

A production workflow should build an image once, publish it once, and deploy the same artifact to the intended environments.

1\. Source control

Review and merge application changes

2\. Build and verify

Build image · Run automated checks · Scan image

3\. Publish to ECR

Unique release tag · Record image digest

ECS pipeline

Update task definition and service

EKS pipeline

Update Deployment via Pulumi

4\. Verify and observe

Health checks · Rollout status · Logs · Alarms · Rollback if necessary

### 8.1 Separate build and deployment responsibilities

Use CI for application validation and image creation. Use a deployment job with appropriate AWS permissions to update infrastructure and services.

For GitHub Actions, prefer short-lived AWS credentials through GitHub's OIDC federation rather than storing long-lived AWS access keys in repository secrets.

A typical deployment sequence is:

* Authenticate to AWS through OIDC.

* Build and scan the container image.

* Push the image to ECR using a unique release identifier.

* Record the immutable image digest.

* Run `pulumi preview` and review infrastructure changes.

* Deploy the selected ECS or EKS stack.

* Verify application health and rollout completion.

* Monitor alarms and initiate a controlled rollback if required.

Do not give an application build job unrestricted production infrastructure permissions. Separate image-publishing permissions from deployment permissions when practical, and require approval before production changes.

### 8.2 Example Bash deployment commands

These commands illustrate the final deployment stage after the image has already been published. Run them in the correct infrastructure project and stack.

For ECS:

```bash
pulumi stack select ecs-dev
pulumi config set imageTag "$IMAGE_TAG"
pulumi preview
pulumi up
```

For EKS:

```bash
pulumi stack select eks-dev
pulumi config set imageTag "$IMAGE_TAG"
pulumi preview
pulumi up
```

The stack names and `imageTag` configuration key are examples: adapt them to your actual projects and code. Your Pulumi program must use the configured image tag or digest to construct the image URI. Do not run both sequences from a directory that manages only one platform.

### 9\. Deployment strategies: rolling, blue/green, and canary

Different release strategies solve different problems.

| Strategy   | How it works                                              | Main consideration                                                           |
| ---------- | --------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Rolling    | Replaces existing application instances gradually         | Simple, but old and new versions may run simultaneously                      |
| Blue/green | Runs two versions and switches traffic between them       | Easier traffic cutover and rollback, but needs capacity for both versions    |
| Canary     | Sends a small portion of traffic to the new version first | Limits initial exposure, but requires controlled routing and good monitoring |

### ECS implementation options

* Rolling deployments with ECS deployment configuration.

* Deployment circuit breakers and automatic rollback for supported deployment scenarios.

* Blue/green deployment using AWS CodeDeploy with an ALB and two target groups.

* Canary or linear traffic shifting with supported CodeDeploy deployment configurations.

### EKS implementation options

* Rolling updates using Kubernetes Deployments.

* Blue/green using separate Deployments and Services with controlled traffic switching.

* Canary routing using an appropriate ingress controller, Gateway API implementation, or progressive delivery controller.

The specific capabilities depend on the controller, deployment tooling, and traffic-routing setup. Kubernetes does not automatically provide every canary or weighted-routing capability merely because the application runs on EKS.

### Lab task: simulate a release

Deploy version `1.0.0`, then build a second version with a visible response change. Publish it as a unique tag and update each platform independently.

For each deployment, record:

* How long the rollout takes.

* Whether old and new instances coexist.

* What happens when the new version fails its health check.

* Whether traffic is interrupted.

* How you restore the previous image.

* Which metrics and logs help confirm a successful release.

Use a non-production environment for failure simulation. Do not deliberately break the shared production service.

### 10\. Lab 5 — Security, observability, and operational readiness

The capstone is not complete just because both applications return HTTP 200. You must also establish that each platform is reasonably secure and operable.

### 10.1 Security checklist

Security review

0 of 6

IAM least privilege

Use separate ECS execution and task roles; use EKS Pod Identity or IRSA for AWS permissions needed by individual workloads.

Private workloads

Keep ECS tasks and EKS worker nodes in private subnets where appropriate; restrict inbound traffic to the required sources.

Image security

Use ECR scanning, controlled image releases, immutable digests, and a process for addressing vulnerabilities.

Secret management

Retrieve runtime secrets from an approved secret store; never bake credentials into images or commit them to Git.

TLS and access

Validate HTTPS certificates, DNS routing, security group rules, and access to the EKS API endpoint.

Infrastructure access

Use short-lived deployment credentials, protected production approvals, and encrypted Pulumi state with appropriate access controls.

### 10.2 Observability checklist

Verify these signals for both deployments:

* Availability: ALB target health, successful health checks, and application error rates.

* Capacity: ECS CPU and memory metrics; EKS pod resource usage, node capacity, and HPA status.

* Logs: Application logs, ECS task logs, EKS control-plane logs where enabled, and Kubernetes events.

* Alerts: CloudWatch alarms for elevated errors, unhealthy targets, resource pressure, and failed deployments.

* Recovery: A documented procedure for rolling back an application image or restoring the previous known-good configuration.

Example ECS commands:

```bash
aws ecs describe-services \
  --cluster YOUR_ECS_CLUSTER_NAME \
  --services YOUR_ECS_SERVICE_NAME \
  --region eu-west-2 \
  --query 'services[0].events[0:10]' \
  --output table
```

Example EKS commands:

```bash
kubectl -n applications get deployments,pods,services,hpa

kubectl -n applications get events \
  --sort-by=.lastTimestamp

kubectl -n applications rollout history deployment/fastapi-api
```

These commands provide immediate operational information. Historical trends, alert evaluation, and incident investigation should also use the monitoring system configured for the environment.

### 11\. Lab 6 — Compare costs and operational complexity

Do not assume that EKS is always more expensive or that ECS is always cheaper. Cost depends on workload utilization, capacity choices, availability requirements, networking, and operational tooling.

### 11.1 Cost categories

| Cost category          | ECS Fargate                                               | EKS managed nodes                                                          |
| ---------------------- | --------------------------------------------------------- | -------------------------------------------------------------------------- |
| Compute                | Allocated task vCPU and memory                            | EC2 instances, including unused node capacity                              |
| Orchestration          | ECS service, without an EKS cluster control-plane charge  | EKS cluster control-plane charge                                           |
| Load balancing         | ALB and associated traffic                                | ALB and associated traffic                                                 |
| Networking             | NAT gateways, data transfer, public IPv4 where applicable | Similar networking costs, potentially with different capacity requirements |
| Logging and monitoring | CloudWatch and any additional tools                       | CloudWatch plus Kubernetes-specific tooling as needed                      |
| Operations             | Generally fewer platform components to maintain           | Additional cluster, node, add-on, and Kubernetes operations                |

EKS Fargate has a different compute billing model from EKS managed nodes, so compare it separately if you evaluate that option. Also account for the EKS control plane and other shared services.

### 11.2 Build a realistic comparison

Collect the same set of measurements from each deployment:

* Number of running application replicas or tasks.

* CPU and memory utilization under representative traffic.

* Idle capacity and scale-out behavior.

* ALB, NAT gateway, data-transfer, and logging costs.

* Cluster and compute costs.

* Time required to deploy, diagnose, and recover from a failed release.

Use the [AWS Pricing Calculator](https://calculator.aws/?utm_source=chatgpt.com) to estimate costs using the actual region, capacity, and traffic assumptions. Use AWS Cost Explorer or billing data to validate the estimates when available.

Do not compare a single small Fargate task against an EKS cluster configured for multiple nodes and conclude that the result applies to every workload. Compare equivalent availability and performance targets.

### 12\. Final architecture recommendation

Use the following as a starting point for the capstone report.

| Requirement                                                           | Initial recommendation                                            |
| --------------------------------------------------------------------- | ----------------------------------------------------------------- |
| Small API or internal service with a small platform team              | ECS Fargate                                                       |
| AWS-native application with minimal orchestration overhead            | ECS Fargate                                                       |
| Specialized host requirements or carefully managed compute fleet      | ECS on EC2                                                        |
| Existing Kubernetes expertise and extensive Kubernetes integrations   | EKS managed nodes                                                 |
| Kubernetes workloads suited to serverless pod compute                 | EKS Fargate                                                       |
| Large platform supporting many teams and diverse Kubernetes workloads | Evaluate EKS against the additional operating cost and complexity |

These are starting recommendations, not absolute rules. For example, a team already operating a mature Kubernetes platform may find EKS simpler organizationally than introducing ECS, while a small team may benefit from ECS even when Kubernetes is technically capable of running the same application.

### 13\. Capstone completion criteria

### Capstone checklist

0/9

Build and publish the FastAPI image to ECR.

Deploy the same image on ECS Fargate and verify its health.

Deploy the same image on EKS and verify its health.

Manage both deployments through Pulumi and inspect previews before applying changes.

Verify HTTPS, networking, IAM permissions, and secret handling.

Inspect logs, scaling behavior, deployment status, and failure recovery.

Compare deployment strategies and document the rollback procedure.

Estimate costs using equivalent workload and availability assumptions.

Write an architecture recommendation explaining the trade-offs.

### Cleanup and cost control

After collecting your results, remove only the resources created specifically for the capstone when they are no longer needed. Before deleting anything, inspect the selected Pulumi stack and its preview.

```bash
pulumi stack
pulumi preview
```

If the ECS and EKS environments share the VPC, ECR repository, or other resources with previous modules, do not destroy those shared resources as part of cleanup. Review the resource ownership and dependency graph first.

Final deliverable: A version-controlled capstone repository containing the FastAPI application, Pulumi infrastructure code, repeatable Bash deployment instructions, operational notes, and an ECS-versus-EKS architecture decision report.

The main outcome is not simply two running deployments. It is the ability to explain which platform you would choose for a real workload, why you would choose it, how you would operate it, and what trade-offs you are accepting.
