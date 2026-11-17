### Module 7 — Amazon ECR and ECS Fundamentals

Theme: Container images and managed container orchestration

In this module, you'll learn how to package a Python application into a Docker image, store that image in Amazon Elastic Container Registry (ECR), and run it on Amazon Elastic Container Service (ECS) using AWS Fargate.

We'll use Pulumi with Python to provision AWS infrastructure, Docker to build the application image, and FastAPI for the application itself.

### 1\. Learning objectives

By the end of this module, you should be able to:

* Explain containers, images, layers, registries, and container runtimes.

* Write a production-oriented Dockerfile for a FastAPI application.

* Build, tag, and publish container images to Amazon ECR.

* Explain ECS clusters, task definitions, tasks, and services.

* Deploy an ECS service using AWS Fargate.

* Distinguish task execution roles from task IAM roles.

* Configure logging, health checks, networking, and security.

* Troubleshoot failed deployments and clean up resources safely.

### 2\. Understand the architecture

Before writing code, understand how the components work together.

Request and deployment flow

```text
Developer
   |
   | Build Docker image
   v
Docker image
   |
   | Push image
   v
Amazon ECR
   |
   | ECS pulls image
   v
Amazon ECS
   |
   | Schedules and manages tasks
   v
AWS Fargate
   |
   v
FastAPI container
   |
   +---- CloudWatch Logs
   |
   +---- Application responses
```

These services have distinct responsibilities:

| Component         | Responsibility                                              |
| ----------------- | ----------------------------------------------------------- |
| Docker            | Builds and packages the application image.                  |
| Amazon ECR        | Stores and distributes container images.                    |
| Amazon ECS        | Schedules, runs, and manages containers.                    |
| AWS Fargate       | Provides serverless compute capacity for ECS tasks.         |
| IAM               | Controls which AWS resources and APIs workloads can access. |
| Amazon CloudWatch | Collects container logs and monitoring data.                |
| Pulumi            | Provisions and manages the AWS infrastructure as code.      |

Key distinction: ECR stores your images. ECS manages your running workloads. Fargate supplies the compute capacity without requiring you to manage EC2 worker instances.

### 3\. Container fundamentals

### 3.1 Containers versus virtual machines

A virtual machine runs its own guest operating system on virtualized hardware. A container packages an application and its dependencies while sharing the host operating system's kernel.

| Characteristic      | Virtual machine                   | Container                      |
| ------------------- | --------------------------------- | ------------------------------ |
| Isolation           | Virtualized hardware and guest OS | Process and OS-level isolation |
| Operating system    | Typically includes a guest OS     | Shares the host kernel         |
| Packaging           | Machine image                     | Container image                |
| Startup             | Usually slower                    | Usually faster                 |
| Resource overhead   | Generally higher                  | Generally lower                |
| Typical AWS service | EC2                               | ECS, EKS                       |

Containers are not automatically secure simply because they are isolated. Image vulnerabilities, excessive privileges, exposed ports, and leaked credentials remain important risks.

### 3.2 Image, container, registry, and runtime

These terms describe different things:

* Image: An immutable template containing application code, dependencies, and filesystem layers.

* Container: A running instance of an image, with its own process environment and writable layer.

* Registry: A service that stores and distributes images, such as ECR.

* Runtime: Software responsible for starting and managing containers.

* Orchestrator: A system that schedules containers and maintains the desired state. ECS is an orchestrator.

A useful mental model is:

`Dockerfile → Image → Registry → Running container`

### 3.3 Image layers and caching

A Docker image consists of filesystem layers. Docker can reuse unchanged layers between builds, reducing build time and image transfer.

For example:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Dependencies are copied and installed before the application source. When only `main.py` changes, Docker can reuse the dependency-installation layer.

Best practices:

* Choose a suitable, maintained base image.

* Use `.dockerignore` to exclude virtual environments, Git metadata, secrets, and caches.

* Avoid copying credentials into images.

* Pin dependencies and control base-image updates.

* Run the application as a non-root user when practical.

* Scan images for vulnerabilities and rebuild when security updates are needed.

### 4\. Docker lab — Containerize FastAPI

We'll create a minimal application that returns JSON and exposes a health endpoint.

### Step 1: Create the project

```text
ecs-fastapi/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── Pulumi.yaml
├── __main__.py
└── requirements.txt
```

Create `app/main.py`:

```python
from fastapi import FastAPI

app = FastAPI(title="AWS ECS Learning Lab")

@app.get("/")
def root():
    return {
        "message": "Hello from FastAPI on Amazon ECS!",
        "service": "ecs-fastapi",
    }

@app.get("/health")
def health():
    return {"status": "ok"}
```

Create `app/requirements.txt`:

```text
fastapi
uvicorn[standard]
```

For a reproducible production build, pin dependencies to tested versions or use a lock file. These unpinned requirements keep the introductory example simple.

### Step 2: Create the Dockerfile

Create `app/Dockerfile`:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser main.py .

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Create `app/.dockerignore`:

```text
__pycache__/
*.py[cod]
.venv/
venv/
.env
.git/
```

The application listens on `0.0.0.0` inside the container so that traffic forwarded to the container can reach it. `EXPOSE 8000` documents the port; it does not publish the port to your computer by itself.

### Step 3: Build and run locally

From the project root:

```bash
docker build -t ecs-fastapi:1.0.0 ./app

docker run --rm -d \
  --name ecs-fastapi \
  -p 8000:8000 \
  ecs-fastapi:1.0.0
```

Test the application:

```bash
curl http://localhost:8000/
curl http://localhost:8000/health
```

Expected health response:

```json
{"status":"ok"}
```

Inspect the container:

```bash
docker ps
docker logs ecs-fastapi
docker inspect ecs-fastapi
```

Clean up the local container:

```bash
docker stop ecs-fastapi
```

Checkpoint: You now have a working container image. The next step is to publish that image so AWS can retrieve it.

### 5\. Amazon ECR — Store container images

Amazon Elastic Container Registry is a managed registry for Docker and OCI-compatible container images. Private ECR repositories integrate with ECS, allowing tasks to retrieve images using AWS IAM permissions. Amazon Web Services, Inc. +1

### 5.1 Important concepts

* Registry: Your account's ECR registry in a particular AWS Region.

* Repository: A named location for an application's images.

* Tag: A human-readable image label, such as `1.0.0`.

* Image digest: A content-addressed identifier for an image manifest.

* Lifecycle policy: Rules for expiring images that are no longer needed.

* Image scanning: Detection of known vulnerabilities in image packages.

Prefer versioned tags or immutable image digests for deployments. The `latest` tag alone is not a reliable deployment version because its meaning can change.

### 5.2 Create an ECR repository using Pulumi

We'll create the repository first, push the image, and then deploy the ECS service. This two-stage process makes the image publication step easier to understand.

Create the root `requirements.txt`:

```text
pulumi
pulumi-aws
```

Create `Pulumi.yaml`:

```yaml
name: ecs-fastapi
runtime:
  name: python
description: FastAPI application on Amazon ECS Fargate
```

Create `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
repository_name = config.get("repository_name") or "ecs-fastapi"

repository = aws.ecr.Repository(
    "app-repository",
    name=repository_name,
    image_tag_mutability="IMMUTABLE",
    image_scanning_configuration={
        "scan_on_push": True,
    },
    force_delete=False,
)

pulumi.export("repository_url", repository.repository_url)
pulumi.export("repository_arn", repository.arn)
```

This repository configuration makes tags immutable and enables image scanning on push. `force_delete=False` helps prevent accidental removal of a repository containing images.

Install the dependencies and initialize the stack:

```bash
python -m venv .venv
```

Activate the virtual environment:

```bash
# Linux / macOS
source .venv/bin/activate
```

```powershell
# Windows PowerShell
.venv\Scripts\Activate.ps1
```

Then run:

```bash
pip install -r requirements.txt

pulumi stack init dev
pulumi config set aws:region eu-west-3
pulumi preview
pulumi up
```

The example uses Paris (`eu-west-3`); choose a Region appropriate for your account and workload if needed.

After deployment, retrieve the repository URL:

```bash
pulumi stack output repository_url
```

### 5.3 Authenticate and push the image

Make sure the AWS CLI is configured with credentials authorized to access ECR. Use your actual configured Region and account, not an invented account ID.

For Linux or macOS, set the repository URL and Region:

```bash
REPOSITORY_URL=$(pulumi stack output repository_url)
AWS_REGION=$(pulumi config get aws:region)
```

Authenticate Docker to ECR:

```bash
aws ecr get-login-password --region "$AWS_REGION" \
  | docker login \
      --username AWS \
      --password-stdin "$REPOSITORY_URL"
```

Tag and push the image:

```bash
docker tag ecs-fastapi:1.0.0 "$REPOSITORY_URL:1.0.0"

docker push "$REPOSITORY_URL:1.0.0"
```

For PowerShell, assign the outputs using `$REPOSITORY_URL = ...` and `$AWS_REGION = ...`; the authentication and push commands are otherwise equivalent.

Verify the image exists:

```bash
aws ecr describe-images \
  --repository-name ecs-fastapi \
  --region "$AWS_REGION"
```

If you chose a custom repository name, substitute it in the verification command.

You have now completed the image publication workflow. Pulumi manages the repository; Docker builds and pushes the image.

### 6\. Amazon ECS — Run and manage containers

ECS is AWS's managed container orchestration service. You describe how your application should run, and ECS manages the lifecycle of the tasks that implement that desired state. Pulumi Docs +1

### 6.1 The four core concepts

| ECS concept     | Meaning                                                 | Example                                                   |
| --------------- | ------------------------------------------------------- | --------------------------------------------------------- |
| Cluster         | Logical grouping for ECS workloads                      | learning-cluster                                          |
| Task definition | Blueprint describing containers and their configuration | ecs-fastapi with 0.25 vCPU, 512 MiB memory, and port 8000 |
| Task            | A running instance of a task definition                 | One running FastAPI task                                  |
| Service         | Maintains the desired number of running tasks           | Keep two FastAPI tasks running                            |

A task definition specifies details such as:

* Container image and version.

* CPU and memory allocation.

* Port mappings.

* Environment variables and secret references.

* Logging configuration.

* Task execution role and task IAM role.

* Health checks and other container settings.

A task is a running workload. A service maintains the desired task count, replaces failed tasks, and coordinates deployments.

For example, if a service is configured with `desired_count = 2`, ECS attempts to maintain two running tasks. If one task fails, ECS can launch a replacement.

### 6.2 Fargate versus ECS on EC2

| Consideration      | ECS on Fargate                              | ECS on EC2                                             |
| ------------------ | ------------------------------------------- | ------------------------------------------------------ |
| Compute management | AWS manages the underlying compute capacity | You manage the EC2 container instances                 |
| Capacity model     | Allocate supported task CPU and memory      | Choose and manage EC2 instance capacity                |
| Host access        | No direct host administration               | Greater control over the host                          |
| Scaling            | Scale tasks; capacity is managed by Fargate | Scale tasks and underlying EC2 capacity                |
| Operational burden | Generally lower                             | Generally higher                                       |
| Suitable for       | Many web applications and services          | Workloads needing host control or specialized capacity |

For this lab, Fargate is the simplest starting point because you can learn ECS without first configuring an EC2 container fleet. Pulumi Docs +1

### 6.3 Task execution role versus task IAM role

This distinction is fundamental to ECS security.

Two different identities

```text
ECS / Fargate infrastructure
          |
          | Task execution role
          |
          +--> Pull image from ECR
          +--> Send logs to CloudWatch
          +--> Retrieve configured secrets

FastAPI application container
          |
          | Task IAM role
          |
          +--> Read authorized S3 objects
          +--> Send messages to an authorized SQS queue
          +--> Call other permitted AWS APIs
```

The task execution role gives the ECS/Fargate agent the permissions it needs to set up and run the task. The task IAM role supplies credentials for AWS API calls made by your application code. AWS for Industries +1

For example, if FastAPI needs to read files from S3, grant the required S3 permissions to the task IAM role—not just to the execution role.

Avoid putting long-lived AWS access keys in environment variables or inside your Docker image.

### 7\. Hands-on lab — Deploy FastAPI to ECS Fargate

We'll extend the Pulumi project from the ECR exercise. The lab uses your existing VPC and subnets so that networking builds on the earlier VPC modules.

### Lab architecture

```text
Internet
   |
   | TCP port 8000
   v
Security group
   |
   v
ECS Fargate service
   |
   +-- FastAPI task
   |
   +-- ECR image
   |
   +-- CloudWatch log group
```

This first deployment exposes the application directly on port 8000 to make the ECS concepts easy to inspect. It is a learning configuration, not the recommended production design. Later, put an Application Load Balancer in public subnets and run ECS tasks in private subnets.

### Step 1: Configure the network and image

First, obtain the ID of your existing VPC and the subnet IDs where your Fargate tasks will run. For this introductory configuration, use subnets that can route to the internet and assign public IP addresses to tasks so they can pull images and receive requests.

Configure Pulumi:

```bash
pulumi config set vpc_id vpc-REPLACE_ME
pulumi config set subnet_ids '["subnet-REPLACE_ME1","subnet-REPLACE_ME2"]'
pulumi config set image_uri 'ACCOUNT_ID.dkr.ecr.eu-west-3.amazonaws.com/ecs-fastapi:1.0.0'
```

Replace the example values with your real VPC ID, subnet IDs, and ECR image URI. Keep the VPC and subnets in the same AWS Region as the ECS service and image repository.

For this direct-public-access lab, the chosen subnets must support public IP assignment and outbound internet routing. A private-subnet design instead needs appropriate outbound connectivity or suitable VPC endpoints.

### Step 2: Add the ECS resources to Pulumi

Replace the repository-only `__main__.py` with the following program. It keeps the ECR repository, creates an ECS cluster, defines the execution role, and deploys the Fargate service.

```python
import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

region = aws.get_region().name
vpc_id = config.require("vpc_id")
subnet_ids = config.require_object("subnet_ids")
image_uri = config.require("image_uri")

# ECR repository
repository = aws.ecr.Repository(
    "app-repository",
    name="ecs-fastapi",
    image_tag_mutability="IMMUTABLE",
    image_scanning_configuration={
        "scan_on_push": True,
    },
    force_delete=False,
)

# CloudWatch Logs
log_group = aws.cloudwatch.LogGroup(
    "app-logs",
    name="/ecs/ecs-fastapi",
    retention_in_days=7,
)

# ECS cluster
cluster = aws.ecs.Cluster(
    "app-cluster",
    name="ecs-fastapi-cluster",
)

# Execution role: used by ECS/Fargate infrastructure
execution_role = aws.iam.Role(
    "task-execution-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

aws.iam.RolePolicyAttachment(
    "execution-policy",
    role=execution_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AmazonECSTaskExecutionRolePolicy"
    ),
)

# Task role: permissions used by application code.
# No additional application permissions are granted in this lab.
task_role = aws.iam.Role(
    "app-task-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

# Security group for the learning application
app_sg = aws.ec2.SecurityGroup(
    "app-security-group",
    vpc_id=vpc_id,
    description="Public ingress for ECS FastAPI learning lab",
    ingress=[{
        "protocol": "tcp",
        "from_port": 8000,
        "to_port": 8000,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "Learning lab HTTP access",
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
)

# ECS task definition
container_definitions = pulumi.Output.all(
    log_group.name,
    image_uri,
).apply(lambda values: json.dumps([{
    "name": "fastapi",
    "image": values[1],
    "essential": True,
    "portMappings": [{
        "containerPort": 8000,
        "protocol": "tcp",
    }],
    "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
            "awslogs-group": values[0],
            "awslogs-region": region,
            "awslogs-stream-prefix": "fastapi",
        },
    },
    "healthCheck": {
        "command": [
            "CMD-SHELL",
            "python -c \"import urllib.request; "
            "urllib.request.urlopen('http://127.0.0.1:8000/health', "
            "timeout=3)\" || exit 1",
        ],
        "interval": 30,
        "timeout": 5,
        "retries": 3,
        "startPeriod": 15,
    },
}]))

task_definition = aws.ecs.TaskDefinition(
    "app-task-definition",
    family="ecs-fastapi",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=container_definitions,
)

# ECS service
service = aws.ecs.Service(
    "app-service",
    name="ecs-fastapi-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=1,
    launch_type="FARGATE",
    platform_version="LATEST",
    network_configuration={
        "subnets": subnet_ids,
        "security_groups": [app_sg.id],
        "assign_public_ip": True,
    },
    opts=pulumi.ResourceOptions(
        depends_on=[aws.iam.RolePolicyAttachment(
            "execution-policy-dependency",
            role=execution_role.name,
            policy_arn=(
                "arn:aws:iam::aws:policy/"
                "service-role/AmazonECSTaskExecutionRolePolicy"
            ),
        )],
    ),
)

pulumi.export("cluster_name", cluster.name)
pulumi.export("service_name", service.name)
pulumi.export("task_definition_arn", task_definition.arn)
pulumi.export("security_group_id", app_sg.id)
pulumi.export("image_uri", image_uri)
```

Important correction to the Pulumi example: Define the execution policy attachment once and use that resource as the service dependency. Replace the `RolePolicyAttachment` section and the `opts` section above with this corrected pattern:

```python
execution_policy = aws.iam.RolePolicyAttachment(
    "execution-policy",
    role=execution_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AmazonECSTaskExecutionRolePolicy"
    ),
)

# In the ECS service:
opts=pulumi.ResourceOptions(
    depends_on=[execution_policy],
),
```

Keep the `opts` argument inside the existing `aws.ecs.Service(...)` call. This ensures Pulumi creates the role's policy attachment before deploying the service, without creating a second attachment resource.

### Step 3: Deploy the service

Install the Pulumi dependencies if you have not already:

```bash
pip install -r requirements.txt
```

Review the infrastructure changes:

```bash
pulumi preview
```

Deploy:

```bash
pulumi up
```

Pulumi will create or update the ECR repository, log group, IAM roles, security group, ECS cluster, task definition, and ECS service.

Check the service status:

```bash
aws ecs describe-services \
  --cluster "$(pulumi stack output cluster_name)" \
  --services "$(pulumi stack output service_name)" \
  --query 'services[0].{status:status,running:runningCount,desired:desiredCount,events:events[0:5]}'
```

Wait until the service reports one running task and a desired count of one. If it fails to stabilize, inspect the service events and task stopped reasons rather than repeatedly redeploying.

### Step 4: Find the running task

Get the cluster and service names:

```bash
CLUSTER=$(pulumi stack output cluster_name)
SERVICE=$(pulumi stack output service_name)
```

List the running tasks:

```bash
aws ecs list-tasks \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --desired-status RUNNING
```

Describe a task to inspect its state:

```bash
aws ecs describe-tasks \
  --cluster "$CLUSTER" \
  --tasks TASK_ARN
```

Replace `TASK_ARN` with an ARN returned by the previous command.

### Step 5: Test the application

Find the public IP address assigned to the Fargate task:

```bash
TASK_ARN=$(aws ecs list-tasks \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --desired-status RUNNING \
  --query 'taskArns[0]' \
  --output text)

ENI_ID=$(aws ecs describe-tasks \
  --cluster "$CLUSTER" \
  --tasks "$TASK_ARN" \
  --query 'tasks[0].attachments[0].details[?name==`networkInterfaceId`].value | [0]' \
  --output text)

aws ec2 describe-network-interfaces \
  --network-interface-ids "$ENI_ID" \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text
```

Open the returned address using port 8000:

```bash
curl http://PUBLIC_IP:8000/
curl http://PUBLIC_IP:8000/health
```

Replace `PUBLIC_IP` with the actual address.

If you cannot reach the application, verify that the task is running, the public IP exists, the subnet has a valid internet route, and the security group allows inbound TCP port 8000. Also verify that the container is listening on `0.0.0.0:8000`.

Add this output to the Pulumi program so the repository URL remains available after you expand the program:

```python
pulumi.export("repository_url", repository.repository_url)
```

This is useful when publishing future image versions.

### 8\. Troubleshooting common ECS failures

| Symptom                     | Likely cause                                                    | What to inspect                                         |
| --------------------------- | --------------------------------------------------------------- | ------------------------------------------------------- |
| CannotPullContainerError    | Incorrect image URI, missing image, or insufficient permissions | ECR repository, tag, and execution role                 |
| ResourceInitializationError | Registry, log, secret, or network initialization failure        | Task stopped reason, subnet routing, endpoints, and IAM |
| Task repeatedly stops       | Application crash or failed container health check              | Container exit code, logs, health-check configuration   |
| Service never stabilizes    | Tasks fail to start or pass health checks                       | ECS service events and stopped tasks                    |
| HTTP connection times out   | Incorrect IP, security group, routing, or task state            | Task ENI, public IP, routes, and inbound rules          |
| Access denied to S3         | Application lacks the required permissions                      | Task IAM role and its attached policies                 |
| No CloudWatch logs          | Logging configuration or execution-role permissions are wrong   | Log group, task definition, execution role              |

Inspect service events:

```bash
aws ecs describe-services \
  --cluster "$CLUSTER" \
  --services "$SERVICE" \
  --query 'services[0].events[0:10]'
```

Inspect stopped tasks:

```bash
aws ecs list-tasks \
  --cluster "$CLUSTER" \
  --service-name "$SERVICE" \
  --desired-status STOPPED
```

Then describe a stopped task to read its `stoppedReason`, `stopCode`, and container exit details.

View application logs:

```bash
aws logs tail /ecs/ecs-fastapi --since 15m
```

These checks help distinguish application problems from IAM, image-pull, and networking problems.

### 9\. Security and production improvements

The introductory lab deliberately keeps the architecture simple. Before using a similar setup in production, address the following:

* Network exposure: Restrict inbound access. Prefer an ALB in public subnets with ECS tasks in private subnets.

* IAM: Keep execution and task roles separate. Give the application only the AWS permissions it actually needs.

* Image integrity: Deploy versioned images or immutable digests and avoid relying on mutable tags.

* Image security: Scan images, update vulnerable dependencies, and rebuild images when base-image security fixes are released.

* Secrets: Retrieve sensitive configuration from Secrets Manager or Parameter Store. Do not bake secrets into images.

* Logging: Configure retention, useful log fields, and alarms for repeated task failures.

* Availability: Increase desired task count and distribute tasks across Availability Zones when appropriate.

* Cost: Remove unused resources after exercises and monitor Fargate, load balancer, image storage, and networking charges.

For production, also consider an ALB health check, deployment circuit breakers, autoscaling, and a deployment strategy that allows safe rollback.

### 10\. ECS on EC2 versus Fargate: a practical comparison

You have deployed the same container image to Fargate. Consider what changes if you choose ECS on EC2 instead.

With ECS on EC2, you must manage the EC2 capacity that runs your containers, including the container-instance role, host patching, instance scaling, and available CPU and memory. With Fargate, AWS manages the underlying compute infrastructure.

For example, if you run ten small services, Fargate lets you configure each task's resource requirements without managing an EC2 fleet. ECS on EC2 can be attractive when you need greater host-level control or want to optimize costs for predictable, consistently high utilization.

Neither option is universally cheaper. The right choice depends on workload utilization, operational overhead, scaling patterns, and specialized requirements.

### 11\. Cleanup the lab safely

AWS resources can continue to incur charges after you finish experimenting. Clean up the stack when you no longer need it.

First, delete the image from ECR because the repository was configured with `force_delete=False`:

```bash
REPOSITORY_NAME=ecs-fastapi
AWS_REGION=$(pulumi config get aws:region)

aws ecr batch-delete-image \
  --repository-name "$REPOSITORY_NAME" \
  --region "$AWS_REGION" \
  --image-ids imageTag=1.0.0
```

Then destroy the Pulumi-managed resources:

```bash
pulumi destroy
```

Review the proposed deletions and confirm them.

Finally, verify that the ECS service and repository are gone. Resources outside the Pulumi stack, such as your existing VPC, should remain intact.

### 12\. Exercises

Try these independently after the initial deployment works.

Exercise 1 — Image versions

* Change the FastAPI response.

* Build and push version `1.0.1`.

* Update the Pulumi `image_uri` configuration.

* Deploy and verify the new response.

Remember that immutable tags cannot be overwritten. Keep the previous image available until you no longer need to roll back.

Exercise 2 — Desired task count

* Change `desired_count` from `1` to `2`.

* Deploy the change.

* Verify that ECS runs two tasks.

* Compare their task IDs and private IP addresses.

Exercise 3 — IAM permissions

* Add a small S3-reading operation to the application.

* Grant only the required S3 permissions to the task IAM role.

* Verify that authorized requests work.

* Remove the permission and observe the access-denied error.

Exercise 4 — Troubleshooting

Intentionally deploy an incorrect image tag or an invalid application startup command. Inspect ECS service events, stopped task reasons, and CloudWatch logs to determine the failure.

Exercise 5 — Production architecture

Extend the lab with an Application Load Balancer and private ECS subnets. Restrict inbound access to the application so that clients reach it through the ALB rather than connecting directly to task IP addresses.

### 13\. Module 7 knowledge check

1. Which service stores your Docker images?

Amazon ECS

Amazon ECR

AWS Fargate

2. What does an ECS service do?

Builds Docker images

Maintains the desired number of running tasks

Stores container image layers

3. Which role allows Fargate to pull an image from private ECR?

Task IAM role

Task execution role

Developer's local IAM user

4. Where should permissions for application code to read S3 objects go?

Task IAM role

ECR repository tag

Dockerfile

5. What happens if a service has desired_count = 2 and one task fails?

ECS permanently stops the service

ECS attempts to replace the failed task

ECR rebuilds the image

Check answers

### Further reading

Use these official guides as references while working through the lab:

* [Pulumi: Amazon ECR](https://www.pulumi.com/docs/iac/clouds/aws/guides/ecr/?utm_source=chatgpt.com) — repositories and image publishing.

* [Pulumi: Amazon ECS](https://www.pulumi.com/docs/iac/clouds/aws/guides/ecs/?utm_source=chatgpt.com) — ECS services and Fargate deployments.

* [AWS: Using ECR images with ECS](https://docs.aws.amazon.com/AmazonECR/latest/userguide/ECR_on_ECS.html?utm_source=chatgpt.com) — image-pull permissions and image references.

* [AWS: IAM roles for ECS tasks](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-iam-roles.html?utm_source=chatgpt.com) — execution roles, task roles, and security best practices.

Module completion goal: You can build a FastAPI container, publish a versioned image to ECR, deploy it as an ECS Fargate service using Pulumi, verify that it works, troubleshoot failures, and safely clean up the infrastructure.
