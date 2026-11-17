### Module 3 — Amazon ECS Fundamentals and Fargate Deployments

AWS ECS/EKS Course · Module 3 of 9 · Pulumi with Python · Bash on Linux, macOS, or Git Bash

### Learning objectives

By the end of this module, you will be able to:

* Explain how ECS clusters, task definitions, tasks, and services work together.

* Deploy a container image from Amazon ECR to AWS Fargate using Pulumi.

* Configure CPU, memory, environment variables, IAM roles, and container logging.

* Understand the difference between an ECS task execution role and a task role.

* Configure networking, security groups, and application health checks.

* Control the desired number of tasks and understand ECS deployment behavior.

* Update an application image and observe an ECS rolling deployment.

### 1\. ECS architecture

Amazon Elastic Container Service (ECS) is AWS's managed container orchestration service. You define how your application should run, and ECS works to maintain that desired state.

![ECS Fargate 성능 측정하기 - 구축부터 Benchmark까지 (상) | dealicious-inc.github.io](https://images.openai.com/static-rsc-4/WyrydTgdSj2r3dpE9knDg4fTnR5F2ofLQUEi-pvJ8Z_WvWVnVdipCq1QegZFNWde-ImkP5-JDUBedrjMEuViERdOzM0XtY4Oe-dBGgOLtezEy5PIhrgIY5dm_54wTECp3Lq6acVqMOGr9wTxoKD_JZN7jrdV9Jk4qbDqdeBu1i1m0wXZGhFV5Hqg3n-M7Mvc?purpose=fullsize)

### 1.1 The core ECS resources

ECS cluster

A logical grouping for ECS workloads. With Fargate, you do not need to provision or maintain EC2 container hosts.

Task definition

A versioned blueprint describing container images, CPU and memory, ports, environment settings, IAM roles, logging, and health checks.

Task

A running instance of a task definition. A task can contain one or more related containers that share the task's networking environment.

Service

Maintains a desired number of running tasks and replaces tasks that stop unexpectedly. It can also coordinate deployments and integrate with load balancers.

For example, an ECS service with `desiredCount = 2` attempts to keep two tasks running. If one task stops, ECS attempts to start a replacement, provided capacity, permissions, image access, and networking are available.

### 1.2 How the resources fit together

Amazon ECR

Stores the FastAPI container image

ECS task definition

Image, CPU, memory, roles, ports, logging

ECS service

Desired count and deployment management

Fargate task 1

Fargate task 2

Illustrative configuration: two desired tasks.

The distinction matters: a task definition describes a workload, a task runs it, and a service manages the number and lifecycle of those running tasks.

### 2\. Amazon ECS on AWS Fargate

Fargate provides serverless compute for ECS tasks. AWS manages the underlying compute infrastructure, while you specify the resources your tasks require.

### 2.1 Fargate versus ECS on EC2

| Feature              | ECS on Fargate                         | ECS on EC2                                                        |
| -------------------- | -------------------------------------- | ----------------------------------------------------------------- |
| Host management      | Managed by AWS                         | You manage EC2 capacity                                           |
| Capacity planning    | Task-level CPU and memory              | Hosts plus task placement                                         |
| OS-level host access | Not available                          | Available                                                         |
| Scaling              | Tasks and services                     | Hosts and tasks                                                   |
| Billing model        | Requested task resources and runtime   | EC2 and related infrastructure                                    |
| Best fit             | Simpler operations, variable workloads | Host control, specialized capacity, some cost-sensitive workloads |

Fargate is a useful starting point because it removes the need to manage an ECS container fleet. It does not eliminate networking, IAM, deployment, or application operations.

### 2.2 CPU and memory

An ECS Fargate task definition specifies task-level CPU and memory. The selected combination must be supported by Fargate.

For our example, we'll use:

* Task CPU: `256` CPU units (0.25 vCPU).

* Task memory: `512` MiB.

* Container port: `8000`.

* Desired task count: `1`.

These settings are suitable for a small learning application, but actual requirements depend on application behavior and traffic.

### 3\. IAM: execution role versus task role

This is one of the most important ECS concepts.

Task execution role

Used by the ECS/Fargate infrastructure on behalf of the task to perform operations such as pulling private images from ECR, writing logs to CloudWatch, and retrieving supported secrets at startup.

Typical managed policy: `AmazonECSTaskExecutionRolePolicy`.

Task role

Provides AWS credentials to your application code inside the container. For example, a FastAPI application that reads from S3 or publishes to SQS needs appropriate permissions through this role.

Grant only the AWS permissions the application actually requires.

These roles are not interchangeable. Giving an application S3 permissions through the execution role does not grant the application those permissions. See the [official ECS task execution role documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task_execution_IAM_role.html?utm_source=chatgpt.com) and [task IAM role documentation](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/task-iam-roles.html?utm_source=chatgpt.com).

For our initial FastAPI service, the task role will have no additional application permissions. The execution role will receive the permissions required for ECR image pulls and CloudWatch logging.

### 4\. ECS networking and service discovery

Fargate tasks use the `awsvpc` network mode. Each task receives its own elastic network interface (ENI) in a selected subnet and uses the configured security groups. Amazon Elastic Container Service +1

### Public versus private subnets

| Configuration              | Public subnet                                                       | Private subnet                                        |
| -------------------------- | ------------------------------------------------------------------- | ----------------------------------------------------- |
| Public IP                  | Can be assigned                                                     | Normally not assigned                                 |
| Internet access            | Requires a route to an internet gateway and suitable security rules | Usually uses NAT or VPC endpoints for outbound access |
| Direct inbound access      | Possible when routes and security groups allow it                   | Not directly reachable from the public internet       |
| Typical production pattern | Public load balancer                                                | Application tasks behind the load balancer            |

For this first deployment, we'll use the default VPC and public IP assignment to keep the lab manageable. We'll restrict inbound access to TCP port `8000` and test the service directly.

This is a learning configuration, not the recommended production exposure pattern. Module 4 will introduce private Fargate tasks behind an Application Load Balancer.

### ECS service discovery

When applications need to communicate internally, ECS can integrate with AWS Cloud Map for service discovery. Instead of hard-coding task IP addresses, applications can resolve a service name to the relevant endpoints.

For example:

* `api.internal` resolves to the API service.

* `worker.internal` resolves to a worker service.

* Security groups restrict which services can communicate.

We won't create a Cloud Map namespace in this lab because our application is a single service. We'll revisit service-to-service communication when multiple workloads are deployed.

### 5\. Lab preparation — Deploy FastAPI on ECS Fargate with Pulumi

We'll continue the course project from Modules 1 and 2.

Project continuity

Module 1: FastAPI application

`aws-containers/app` · Python 3.14 slim image · port 8000 · `/health` endpoint

Module 2: Amazon ECR

Build and publish the versioned application image.

Module 3: ECS Fargate

Provision IAM, ECS, networking, logging, and the running service with Pulumi.

### 5.1 Prerequisites

You'll need:

* Docker.

* Python 3.14 and a working virtual environment.

* AWS CLI configured with credentials that can provision the required resources.

* Pulumi CLI.

* The Module 2 ECR repository and a successfully pushed image.

* Bash, either in Linux/macOS or Git Bash on Windows.

Verify the tools:

```bash
aws --version
pulumi version
python --version
docker --version
aws sts get-caller-identity
```

Use a dedicated learning account or sandbox where possible. ECS, CloudWatch Logs, networking resources, and data transfer may incur charges.

### 5.2 Expected directory structure

From the repository created in Module 1:

```text
aws-containers/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
└── infrastructure/
    ├── Pulumi.yaml
    ├── __main__.py
    ├── requirements.txt
    └── ...
```

We'll keep the application and infrastructure separate. The application image is built and pushed to ECR, while Pulumi manages the AWS infrastructure.

### 5.3 Find the ECR image URI

Use the exact repository and image tag you created in Module 2. The following command lists repositories in the current AWS region:

```bash
aws ecr describe-repositories \
  --query 'repositories[*].[repositoryName,repositoryUri]' \
  --output table
```

Then list the images in your repository, replacing `YOUR_REPOSITORY`:

```bash
aws ecr describe-images \
  --repository-name YOUR_REPOSITORY \
  --query 'imageDetails[*].[imageTags,imageDigest]' \
  --output table
```

Your image URI will resemble:

```text
123456789012.dkr.ecr.eu-west-2.amazonaws.com/fastapi-api:1.0.0
```

The account ID, region, repository name, and tag above are examples. Use your actual values.

For repeatable releases, prefer an immutable image tag or digest. In this lab, we'll pass the image URI into Pulumi as configuration instead of hard-coding it in the program.

### 6\. Create the Pulumi infrastructure

### 6.1 Initialize the project

From the `infrastructure` directory, use Bash:

```bash
cd aws-containers/infrastructure

pulumi stack
```

If you are continuing the project from Module 2, keep its existing stack and configuration. Otherwise, initialize a new Python project:

```bash
pulumi new python
```

Install the AWS provider:

```bash
source venv/bin/activate
python -m pip install pulumi pulumi-aws
```

If your existing project uses a virtual environment named `.venv`, activate that environment instead. Pulumi Python projects can use either convention.

Configure the stack:

```bash
pulumi config set aws:region eu-west-2
pulumi config set imageUri "YOUR_ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com/YOUR_REPOSITORY:1.0.0"
pulumi config set desiredCount 1
```

Replace the image URI with the real value from Module 2. If you are using another AWS region, keep the provider region and image URI consistent.

### 6.2 Install the dependencies

Ensure `requirements.txt` contains:

```text
pulumi
pulumi-aws
```

Then install them into your active virtual environment:

```bash
python -m pip install -r requirements.txt
```

### 6.3 Configure Pulumi outputs

The infrastructure program will export the ECS cluster name, service name, task definition ARN, security group ID, and application URL.

We'll use the default VPC for this first lab and discover its subnets automatically. This avoids hard-coding subnet IDs and makes the example easier to reuse in another AWS account.

### 7\. Implement the ECS infrastructure

Replace the contents of `__main__.py` with the following complete program.

The implementation creates an ECS cluster, CloudWatch log group, execution and task roles, an ECR-backed task definition, a security group, and a Fargate service. It uses Pulumi's AWS provider resources for infrastructure management. Pulumi Registry +2

```python

import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
image_uri = config.require("imageUri")
desired_count = config.get_int("desiredCount") or 1

aws_config = pulumi.Config("aws")
region = aws_config.require("region")

# --------------------------------------------------
# 1. Discover the default VPC and its subnets
# --------------------------------------------------

default_vpc = aws.ec2.get_vpc(default=True)

subnets = aws.ec2.get_subnets(
    filters=[
        {
            "name": "vpc-id",
            "values": [default_vpc.id],
        }
    ]
)

if len(subnets.ids) == 0:
    raise ValueError("No subnets found in the default VPC.")

# --------------------------------------------------
# 2. ECS cluster
# --------------------------------------------------

cluster = aws.ecs.Cluster(
    "fastapi-cluster",
    name="fastapi-cluster",
    settings=[
        {
            "name": "containerInsights",
            "value": "enabled",
        }
    ],
)

# --------------------------------------------------
# 3. CloudWatch Logs
# --------------------------------------------------

log_group = aws.cloudwatch.LogGroup(
    "fastapi-log-group",
    name="/ecs/fastapi-api",
    retention_in_days=7,
)

# --------------------------------------------------
# 4. IAM roles
# --------------------------------------------------

execution_role = aws.iam.Role(
    "ecs-execution-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
)

execution_policy = aws.iam.RolePolicyAttachment(
    "ecs-execution-policy",
    role=execution_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AmazonECSTaskExecutionRolePolicy"
    ),
)

# The application currently requires no AWS API permissions.
task_role = aws.iam.Role(
    "ecs-task-role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "ecs-tasks.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole",
                }
            ],
        }
    ),
)

# --------------------------------------------------
# 5. ECS task definition
# --------------------------------------------------

container_definitions = [
    {
        "name": "fastapi",
        "image": image_uri,
        "essential": True,
        "portMappings": [
            {
                "containerPort": 8000,
                "protocol": "tcp",
            }
        ],
        "environment": [
            {
                "name": "APP_ENV",
                "value": "development",
            }
        ],
        "healthCheck": {
            "command": [
                "CMD-SHELL",
                "python -c \"import urllib.request; "
                "urllib.request.urlopen("
                "'http://127.0.0.1:8000/health', "
                "timeout=3)\" "
                "|| exit 1",
            ],
            "interval": 30,
            "timeout": 5,
            "retries": 3,
            "startPeriod": 30,
        },
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": log_group.name,
                "awslogs-region": region,
                "awslogs-stream-prefix": "ecs",
            },
        },
    }
]

task_definition = aws.ecs.TaskDefinition(
    "fastapi-task-definition",
    family="fastapi-api",
    requires_compatibilities=["FARGATE"],
    network_mode="awsvpc",
    cpu="256",
    memory="512",
    execution_role_arn=execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=pulumi.Output.json_dumps(
        container_definitions
    ),
    opts=pulumi.ResourceOptions(
        depends_on=[execution_policy]
    ),
)

# --------------------------------------------------
# 6. Security group
# --------------------------------------------------

task_security_group = aws.ec2.SecurityGroup(
    "fastapi-task-security-group",
    description="Learning lab: FastAPI on ECS Fargate",
    vpc_id=default_vpc.id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 8000,
            "to_port": 8000,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Temporary public lab access",
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

# --------------------------------------------------
# 7. ECS Fargate service
# --------------------------------------------------

service = aws.ecs.Service(
    "fastapi-service",
    name="fastapi-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=desired_count,
    launch_type="FARGATE",
    platform_version="LATEST",
    deployment_minimum_healthy_percent=100,
    deployment_maximum_percent=200,
    wait_for_steady_state=True,
    network_configuration={
        "subnets": subnets.ids,
        "security_groups": [task_security_group.id],
        "assign_public_ip": True,
    },
    opts=pulumi.ResourceOptions(
        depends_on=[execution_policy]
    ),
)

# --------------------------------------------------
# 8. Export useful values
# --------------------------------------------------

pulumi.export("clusterName", cluster.name)
pulumi.export("serviceName", service.name)
pulumi.export("taskDefinitionArn", task_definition.arn)
pulumi.export("securityGroupId", task_security_group.id)
pulumi.export("logGroupName", log_group.name)
pulumi.export("applicationUrl", service.name.apply(
    lambda _: "Use the public task IP on port 8000"
))
```

### Understand the important implementation details

Task definition: `cpu="256"` and `memory="512"` are a valid Fargate size combination. The task definition references the image from ECR and configures port `8000`, an environment variable, a health check, and CloudWatch Logs. Amazon Elastic Container Service +1

Execution role: The managed policy provides the standard permissions needed for ECR image pulls and CloudWatch logging. If you later inject secrets from Secrets Manager or Parameter Store, you may need additional narrowly scoped permissions.

Task role: This role is separate and currently has no additional permissions. Add permissions only when the application needs to call AWS services.

Networking: The example enables public IP assignment and allows inbound port `8000` from any IPv4 address. This is intentionally permissive for a short learning lab. Restrict it to your own public IP when practical, and remove direct public access when moving to the private-task/ALB architecture in Module 4.

Health check: The container uses Python's standard library to request `/health`, avoiding a dependency on `curl` being installed in the image. Make sure your FastAPI application actually exposes this endpoint and returns a successful HTTP status.

Deployment configuration: The service is configured for a rolling deployment with a minimum healthy percentage of 100 and a maximum of 200. ECS can start replacement tasks before stopping old ones, subject to available resources and health checks.

The example assumes that the default VPC has usable subnets and routes, and that your AWS identity is authorized to create the resources. If you use a custom VPC from an earlier networking module, configure its subnet IDs and security group rules instead.

### 8\. Preview and deploy

Before provisioning anything, check the Pulumi stack and validate the program.

```bash
pulumi stack
pulumi config
python -m py_compile __main__.py
pulumi preview
```

Review the preview. You should see resources for the cluster, IAM roles and policy attachment, log group, task definition, security group, and service.

If the preview is correct, deploy:

```bash
pulumi up
```

Review the proposed changes and confirm when prompted.

Because the service uses `wait_for_steady_state=True`, Pulumi waits for ECS to reach a steady state. The initial deployment may take several minutes.

Read the outputs:

```bash
pulumi stack output
pulumi stack output clusterName
pulumi stack output serviceName
```

### 9\. Verify the ECS deployment

### 9.1 Check the ECS service

```bash
aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --query 'services[0].{Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount,Deployments:deployments[*].status}' \
  --output json
```

For a healthy deployment, expect the service to be `ACTIVE`, with one desired task and one running task, and no tasks remaining pending.

### 9.2 Inspect the running task

```bash
aws ecs list-tasks \
  --cluster fastapi-cluster \
  --service-name fastapi-service \
  --desired-status RUNNING \
  --output table
```

Retrieve its task ARN:

```bash
TASK_ARN=$(aws ecs list-tasks \
  --cluster fastapi-cluster \
  --service-name fastapi-service \
  --desired-status RUNNING \
  --query 'taskArns[0]' \
  --output text)

echo "$TASK_ARN"
```

Inspect its status and container details:

```bash
aws ecs describe-tasks \
  --cluster fastapi-cluster \
  --tasks "$TASK_ARN" \
  --query 'tasks[0].{LastStatus:lastStatus,Health:healthStatus,TaskDefinition:taskDefinitionArn,StoppedReason:stoppedReason,Containers:containers[*].{Name:name,Status:lastStatus,Reason:reason}}' \
  --output json
```

If no task is running, don't assume deployment succeeded. Inspect the service events and stopped-task reasons in the following sections.

### 9.3 Find the public IP and call the API

First, get the task's network interface ID:

```bash
ENI_ID=$(aws ecs describe-tasks \
  --cluster fastapi-cluster \
  --tasks "$TASK_ARN" \
  --query "tasks[0].attachments[0].details[?name=='networkInterfaceId'].value | [0]" \
  --output text)

echo "$ENI_ID"
```

Then obtain the assigned public IP:

```bash
PUBLIC_IP=$(aws ec2 describe-network-interfaces \
  --network-interface-ids "$ENI_ID" \
  --query 'NetworkInterfaces[0].Association.PublicIp' \
  --output text)

echo "$PUBLIC_IP"
```

Test the health endpoint:

```bash
curl --fail --show-error "http://${PUBLIC_IP}:8000/health"
```

If your application also has a root endpoint, test it:

```bash
curl --fail --show-error "http://${PUBLIC_IP}:8000/"
```

If the health check fails, check that the app listens on `0.0.0.0:8000` inside the container, rather than only on `127.0.0.1:8000`. The container health check should use the loopback address, but external requests must be able to reach the application through its container network interface.

### 9.4 Inspect application logs

```bash
aws logs describe-log-streams \
  --log-group-name /ecs/fastapi-api \
  --order-by LastEventTime \
  --descending \
  --max-items 5
```

To follow the logs in real time:

```bash
aws logs tail /ecs/fastapi-api --follow
```

You should see the FastAPI/Uvicorn startup messages and requests reaching the application.

### 10\. Understand ECS service health and replacement

A service's `desiredCount` describes the number of tasks ECS should maintain; it doesn't guarantee the application is healthy or reachable.

Inspect recent service events:

```bash
aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --query 'services[0].events[:10].[createdAt,message]' \
  --output table
```

Common failure scenarios include:

| Symptom                  | Likely cause                                                                                         |
| ------------------------ | ---------------------------------------------------------------------------------------------------- |
| CannotPullContainerError | Incorrect image URI, missing execution-role permissions, or no network path to ECR                   |
| Tasks stop immediately   | Application startup failure, invalid command, or incorrect container configuration                   |
| Health check fails       | Missing /health endpoint, wrong port, or insufficient startup time                                   |
| Tasks remain pending     | Networking, capacity, quota, or service configuration issues                                         |
| No CloudWatch logs       | Missing log permissions, incorrect log group configuration, or failure before logging initializes    |
| API cannot be reached    | Missing public IP, incorrect routes, restrictive security group rules, or app bound to loopback only |

For a stopped task, retrieve the diagnostic fields:

```bash
aws ecs list-tasks \
  --cluster fastapi-cluster \
  --service-name fastapi-service \
  --desired-status STOPPED \
  --query 'taskArns' \
  --output json
```

Then inspect an actual stopped task ARN:

```bash
aws ecs describe-tasks \
  --cluster fastapi-cluster \
  --tasks "PASTE_STOPPED_TASK_ARN_HERE" \
  --query 'tasks[0].{StoppedReason:stoppedReason,StopCode:stopCode,Containers:containers[*].{Name:name,ExitCode:exitCode,Reason:reason}}' \
  --output json
```

ECS may replace stopped service tasks, so the most recent stopped task is often the best place to start investigating repeated failures.

### 11\. Update the application and observe a rolling deployment

One of the most important benefits of ECS services is that you can update a running application by publishing a new image and registering a new task definition revision.

### 11.1 Build and publish a new image

Make a small change to `app/main.py`, such as changing the response from the root endpoint to include a release identifier:

```python
@app.get("/")
def root():
    return {
        "message": "Hello from ECS Fargate",
        "release": "2.0.0",
    }
```

Preserve the existing application routes and imports. Then, from the repository root, build and push the updated image using a new tag:

```bash
export AWS_REGION="eu-west-2"
export ECR_REPOSITORY="YOUR_REPOSITORY"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"

export IMAGE_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:2.0.0"

docker build -t "$IMAGE_URI" ./app
docker push "$IMAGE_URI"
```

Use the same build platform as your ECS task definition. If necessary, explicitly build for `linux/amd64` or `linux/arm64` to match the configured architecture.

### 11.2 Update Pulumi configuration

Point the existing stack to the new image:

```bash
pulumi config set imageUri "$IMAGE_URI"
pulumi preview
pulumi up
```

Pulumi detects that the task definition has changed and registers a new revision. The ECS service then deploys the new revision according to its deployment configuration. Pulumi Registry +1

### 11.3 Observe the deployment

While the update is running, inspect the service:

```bash
watch -n 5 'aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service \
  --query "services[0].deployments[*].[status,desiredCount,runningCount,taskDefinition]" \
  --output table'
```

The `watch` command is available on most Linux systems; if you're using Git Bash without it, run the `aws ecs describe-services` command repeatedly.

With a desired count of one and a maximum deployment percentage of 200, ECS may start a second task before stopping the old one. This requires sufficient capacity and successful health checks.

Once the deployment stabilizes, call the API again and verify that it returns the new release identifier.

Key distinction: Publishing an image to ECR does not, by itself, update an existing ECS service. The service must be directed to a new task definition revision or explicitly redeployed to pick up a changed image reference.

### 12\. Environment variables and secrets

Environment variables are useful for non-sensitive configuration, such as an environment name, feature flags, and log levels.

For example, the current task definition sets:

```python
"environment": [
    {
        "name": "APP_ENV",
        "value": "development",
    }
]
```

For passwords, API tokens, and database credentials, use AWS Secrets Manager or Systems Manager Parameter Store rather than placing plaintext secrets in the task definition or source code.

A container definition can reference a secret using its ARN:

```python
"secrets": [
    {
        "name": "DATABASE_PASSWORD",
        "valueFrom": "YOUR_SECRET_ARN",
    }
]
```

This is an illustrative fragment, not a replacement for the complete container definition. The execution role must also be granted the appropriate permission to retrieve the secret, and customer-managed KMS keys may require additional permissions.

Environment variables supplied through ECS secrets are injected when the container starts. Rotating a secret does not automatically replace the value already present in a running container; a new task launch is generally needed to retrieve the updated value.

### 13\. Clean up the lab

Fargate tasks, CloudWatch Logs, and other AWS resources can incur charges. Once you have finished testing, remove the infrastructure created by this stack:

```bash
pulumi destroy
```

Review the proposed deletions and confirm. Then check that the ECS service and tasks have been removed:

```bash
aws ecs describe-services \
  --cluster fastapi-cluster \
  --services fastapi-service
```

AWS may report that the service or cluster no longer exists, which is expected after successful cleanup.

Important: Pulumi destroys resources managed by this stack, not every resource created in previous modules. The ECR repository from Module 2 may remain and can incur storage charges. Review it separately before deleting it, especially if you want to retain your images for Module 4.

### Module 3 — Completion summary

You have now covered the core lifecycle of a containerized ECS application:

* Understand ECS clusters, task definitions, tasks, and services.

* Provision ECS infrastructure using Pulumi and Python.

* Configure Fargate resources and IAM execution/task roles.

* Deploy an ECR image with networking, health checks, and CloudWatch Logs.

* Inspect task status, service events, and stopped-task diagnostics.

* Publish a new image and observe an ECS rolling deployment.

* Understand how ECS retrieves secrets and why application credentials require separate permissions.

* Clean up the resources created for the lab.

### What comes next?

Module 4 builds on this deployment by placing ECS tasks in private subnets behind an Application Load Balancer, adding service auto scaling, configuring secure application settings, and exploring deployment rollback and production operations.

The key progression is from a directly accessible Fargate service to a production-style ECS application with controlled ingress, scaling, and operational monitoring.
