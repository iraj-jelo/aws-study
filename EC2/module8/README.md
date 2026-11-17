### Module 8 — Amazon ECS Networking and Production Operations

Phase 4 — Compute · Hands-on AWS course · Pulumi with Python

In this module, you'll take the ECS Fargate service from the previous module and make it behave more like a production application: private networking, controlled outbound connectivity, load-balancer integration, safe deployments, centralized logging, and least-privilege IAM.

We'll build on the VPC, subnets, route tables, security groups, NAT Gateway, and VPC endpoints you learned in Phase 3, rather than treating ECS as an isolated service.

### 1\. Learning objectives

By the end of this module, you should be able to:

* Explain how ECS tasks receive network interfaces and IP addresses.

* Design public and private subnet placement for Fargate tasks.

* Configure outbound connectivity using NAT Gateways or VPC endpoints.

* Register ECS tasks with an Application Load Balancer (ALB).

* Configure container health checks and ALB target health checks.

* Perform rolling deployments and understand deployment circuit breakers and rollback.

* Send application logs to CloudWatch Logs.

* Retrieve secrets securely and assign the correct IAM permissions.

* Diagnose common ECS networking, deployment, and startup failures.

* Estimate the costs of running an ECS service in a private VPC.

### 2\. Architecture: what we're building

Internet clients

HTTPS requests

Public Application Load Balancer

Public subnets in two Availability Zones

HTTP to application port

### Private application subnets

ECS task A

Fargate · AZ A

ECS task B

Fargate · AZ B

Tasks use private IP addresses and accept application traffic only from the ALB security group.

Outbound connectivity

NAT Gateway or appropriate VPC endpoints

CloudWatch

Logs, metrics, alarms

The core security principle is that the ALB is public, but the application tasks are not. External clients reach the ALB, and the ALB forwards permitted requests to healthy tasks.

The tasks do not need public IP addresses to serve incoming requests through the ALB. However, they may need outbound connectivity to pull container images, retrieve secrets, or call external APIs.

### 3\. Understand ECS task networking

### 3.1 The `awsvpc` network mode

For Fargate tasks, `awsvpc` is the standard network mode. Each task receives its own Elastic Network Interface (ENI) in your VPC and a private IP address.

This means security groups can be attached directly to the task's network interface.

Task-level security groups

Restrict inbound application traffic to the ALB security group rather than allowing access from arbitrary IP addresses.

Private IP addressing

Tasks can communicate within permitted VPC network paths without being directly exposed to the public internet.

Independent task lifecycle

Tasks can be replaced during scaling and deployments. Their IP addresses can change, so clients should use the ALB DNS name or service discovery instead of hard-coded task IPs.

### 3.2 Security group relationships

Configure the security groups to express which component is allowed to talk to which other component.

| Security group | Inbound rules                                                              | Outbound rules                                     |
| -------------- | -------------------------------------------------------------------------- | -------------------------------------------------- |
| ALB            | TCP 443 from permitted client networks; optionally TCP 80 for redirects    | Application port to ECS task security group        |
| ECS tasks      | Application port, such as TCP 8000, from the ALB security group only       | Required destinations for application dependencies |
| VPC endpoints  | HTTPS (TCP 443) from authorized workload security groups, where applicable | Managed by the endpoint service and AWS networking |

Security groups are stateful, so response traffic for allowed connections is automatically permitted. Restrictive egress policies still need careful design: allowing an outbound connection to a destination is not the same as allowing the destination's inbound connection.

Important: Do not open the ECS application port to `0.0.0.0/0` just because the ALB is internet-facing.

### 4\. Private subnets and outbound connectivity

A private subnet does not have a direct route to an Internet Gateway for public internet access. Depending on its configuration, it may have no outbound connectivity at all, or it may route outbound internet traffic through a NAT Gateway.

There are two common designs.

![If AWS Networking Confuses You — This Guide Is Your Missing Map | by Muhammad Shahbaj | Medium](https://images.openai.com/static-rsc-4/Ec2waY3UUyc1VWBggxuUzdfoVHvbLPI5-S-K86JtCemubcBW2C7QpASLKmy0UbPTAEIkqYQGAqaSPHeU92vVncM4zfpeLagYdbsWWaTJ-_QbFzftYA4RTFxBOu9hCZZEtM8q1dfuss-R4XX3NB-wJvECN4EkaMZ9pTBALSDzJAv2hrm2-PnXRnI4YKOiLdbr?purpose=fullsize)

Option A — NAT Gateway

Private tasks send internet-bound traffic through a NAT Gateway in a public subnet. This supports destinations such as external APIs and public container registries.

Trade-off: simpler general outbound access, but NAT Gateway hourly and data-processing charges can add up.

![AWS VPC Interface Endpoint vs Gateway Endpoint](https://images.openai.com/static-rsc-4/LSucx_8GzFpEbvOGzS4iFZrgoUy5xcneCbFCUYfvklSFJa7Sleny9u9Qgq3FTGuZfOwTOj2ewfCXEDqQHDwlYPp-vjacTRm-1kgWe7QIIZaUoW3kF0Od2Z1OViAIvoFmdje4TdH-4d1IUcHJgneqteo48etQ3NNULH0A2qfauPk3QiictaItldtJ39MFZHog?purpose=fullsize)

Option B — VPC endpoints

Private tasks reach supported AWS services through private network paths without requiring NAT for those service calls.

Trade-off: less dependence on NAT, but endpoint coverage, DNS, policies, security groups, and endpoint charges must be considered.

### 4.1 What does an ECS task need to reach?

Consider the lifecycle of a Fargate task:

| Dependency        | Why it matters                                       | Typical network requirement                                            |
| ----------------- | ---------------------------------------------------- | ---------------------------------------------------------------------- |
| Amazon ECR API    | Retrieve image metadata and authenticate image pulls | ECR API interface endpoint or NAT                                      |
| ECR image storage | Download image layers                                | ECR Docker interface endpoint plus the required S3 access path, or NAT |
| CloudWatch Logs   | Send container logs                                  | Logs interface endpoint or NAT                                         |
| Secrets Manager   | Retrieve configured secrets                          | Secrets Manager interface endpoint or NAT                              |
| External APIs     | Call services on the public internet                 | NAT or another suitable egress design                                  |

For a private, NAT-independent design, the required endpoints must be configured correctly. For ECR, this generally includes the `ecr.api` and `ecr.dkr` interface endpoints and an S3 gateway endpoint for image-layer downloads, with appropriate routing and endpoint policies.

The exact dependencies vary with your application and configuration. Creating one VPC endpoint does not automatically provide access to every AWS service.

### 4.2 The two IAM roles that are easy to confuse

* Task execution role: Used by ECS/Fargate infrastructure to pull images, send logs, and retrieve configured secrets during task startup, as applicable.

* Task role: Supplies AWS permissions to code running inside the container, such as permission to read a particular S3 bucket.

These roles serve different purposes. Your application should not need broad ECR permissions merely because ECS needs to pull its image.

### 5\. Connect ECS to an Application Load Balancer

An ALB distributes incoming requests among healthy ECS task targets.

The integration consists of four main resources:

* An ALB deployed in public subnets.

* A target group configured for IP targets.

* A listener that forwards requests to that target group.

* An ECS service configured to register its tasks with the target group.

For Fargate using `awsvpc`, the target group must use target type `ip`, because the task's network interface—not an EC2 instance—is the registered target.

### 5.1 Health checks are different from container checks

A healthy container does not necessarily mean a healthy application target.

| Check                   | What it validates                                                                        |
| ----------------------- | ---------------------------------------------------------------------------------------- |
| Container health check  | Whether the container's configured health command succeeds                               |
| ALB target health check | Whether the ALB can reach the task on the configured port and health-check path          |
| ECS service health      | Whether the service has the required running tasks and meets its deployment requirements |

For example, a FastAPI application might expose `/health` on port `8000`. The ALB can use that endpoint to decide whether a task should receive traffic.

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Hello from ECS"}

@app.get("/health")
def health():
    return {"status": "ok"}
```

Your container must listen on `0.0.0.0:8000`, not just `127.0.0.1:8000`, so that requests arriving through the task's network interface can reach it.

### 5.2 Service discovery

An ALB is appropriate when clients need HTTP or HTTPS access to your application. ECS service discovery can be useful when services need to communicate directly using stable service names inside a private network.

Do not add service discovery automatically to every application. Use it when direct service-to-service discovery is part of the architecture.

### 6\. Rolling deployments and rollback

When you deploy a new task definition, ECS can replace old tasks with new ones progressively.

Important service settings include:

* Desired task count.

* Minimum and maximum healthy task percentages during deployment.

* Deployment health-check grace period.

* Health-check configuration.

* Deployment circuit breaker and rollback behavior.

A deployment circuit breaker can detect a deployment that fails to reach a steady state and, when configured for rollback, return the service to its last completed deployment.

For example, a deployment can fail because:

* The new image cannot be pulled.

* The container exits on startup.

* A required secret cannot be retrieved.

* The application listens on the wrong port.

* The ALB health check uses the wrong path.

* The security group blocks ALB-to-task traffic.

A rollback restores the previous service deployment configuration; it does not necessarily reverse external side effects such as database schema changes.

### Deployment troubleshooting sequence

* Inspect the ECS service events for the first meaningful failure.

* Inspect stopped tasks and their stop reasons.

* Check CloudWatch container logs for startup exceptions.

* Verify image availability, execution-role permissions, and secret access.

* Check the task security group, target group port, and ALB health-check path.

* Confirm the deployment reaches steady state before declaring success.

### 7\. Centralized logging, secrets, and permissions

### 7.1 Send container logs to CloudWatch

Configure the task definition with the `awslogs` log driver. This allows you to inspect application output centrally without connecting to individual containers.

Typical configuration:

```python
log_configuration = aws.ecs.TaskDefinitionLogConfigurationArgs(
    log_driver="awslogs",
    options={
        "awslogs-group": "/ecs/fastapi",
        "awslogs-region": aws.config.region,
        "awslogs-stream-prefix": "app",
    },
)
```

Create the CloudWatch log group explicitly so you can control retention and avoid keeping logs indefinitely.

For example, use a retention period appropriate for the lab, such as seven days. Production retention should be based on operational, security, and compliance requirements.

### 7.2 Store secrets outside the container image

Never bake database passwords, API tokens, or AWS credentials into a Docker image or commit them to source control.

Use AWS Secrets Manager or Systems Manager Parameter Store, and reference the secret from the ECS task definition. Grant the task execution role permission to retrieve a secret injected during task startup.

If a secret is injected as an environment variable, rotating the secret does not automatically update the value in an already-running task. You may need to launch replacement tasks.

### 8\. Hands-on lab — Private ECS Fargate behind an ALB

### Lab checklist

0 of 11 completed

Reset

Confirm the VPC has public and private subnets in at least two Availability Zones.

Create an ECR repository and publish the FastAPI image.

Create security groups for the ALB and ECS tasks.

Create a CloudWatch log group with finite retention.

Create the ECS task execution role and task definition.

Create an IP-type target group and public ALB listener.

Deploy an ECS Fargate service in private subnets.

Configure outbound connectivity using NAT or VPC endpoints.

Test the application, health checks, and logs.

Deploy a deliberately invalid revision in a safe test environment and observe failure handling.

Correct the issue, verify recovery, and clean up the lab resources.

### 8.1 Lab assumptions

This lab assumes:

* You have an AWS account and a working Pulumi CLI installation.

* You have completed the earlier ECS fundamentals module.

* You have a VPC with two public and two private subnets, or will provision one separately.

* You have a container image in ECR, built for the appropriate CPU architecture.

* You have configured AWS credentials using a suitable developer identity.

We'll use the following sample configuration:

| Setting               | Example                        |
| --------------------- | ------------------------------ |
| Application           | FastAPI                        |
| Container port        | 8000                           |
| ECS launch type       | Fargate                        |
| Desired task count    | 2                              |
| Task subnet placement | Private subnets across two AZs |
| Load balancer         | Public ALB                     |
| Target type           | ip                             |
| Logs                  | CloudWatch Logs                |
| Infrastructure code   | Pulumi with Python             |

The subnet IDs and image URI will be supplied through Pulumi configuration rather than hard-coded into the program.

### 8.2 Create a Pulumi project

```bash
mkdir ecs-production-lab
cd ecs-production-lab

pulumi new aws-python
python -m pip install --upgrade pulumi pulumi-aws
```

Set the configuration values for the VPC and subnets you intend to use:

```bash
pulumi config set vpcId vpc-REPLACE_ME
pulumi config set publicSubnetIds '["subnet-PUBLIC_A","subnet-PUBLIC_B"]'
pulumi config set privateSubnetIds '["subnet-PRIVATE_A","subnet-PRIVATE_B"]'
pulumi config set imageUri 'ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/fastapi:1.0.0'
```

Replace all example IDs and the image URI with real values. Ensure that the private subnets have the routing and endpoints needed for the chosen deployment design.

### 8.3 Provision the ALB and ECS service

The following Pulumi example illustrates the main resource relationships. It assumes the VPC, subnets, ECR image, and execution role are already available.

File: `__main__.py` — core service deployment

```python
import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
public_subnet_ids = json.loads(
    config.require("publicSubnetIds")
)
private_subnet_ids = json.loads(
    config.require("privateSubnetIds")
)
image_uri = config.require("imageUri")

region = aws.get_region().name

# CloudWatch log group with finite retention.
log_group = aws.cloudwatch.LogGroup(
    "fastapi-logs",
    name="/ecs/fastapi",
    retention_in_days=7,
)

# ALB security group: HTTPS ingress is shown here.
# Add an ACM certificate and HTTPS listener for production.
alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    vpc_id=vpc_id,
    description="Allow HTTPS from clients",
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        protocol="tcp",
        from_port=443,
        to_port=443,
        cidr_blocks=["0.0.0.0/0"],
    )],
    egress=[aws.ec2.SecurityGroupEgressArgs(
        protocol="tcp",
        from_port=8000,
        to_port=8000,
        security_groups=[],
    )],
)

# Task security group: application traffic only from the ALB.
task_sg = aws.ec2.SecurityGroup(
    "task-sg",
    vpc_id=vpc_id,
    description="Allow application traffic from ALB",
    ingress=[aws.ec2.SecurityGroupIngressArgs(
        protocol="tcp",
        from_port=8000,
        to_port=8000,
        security_groups=[alb_sg.id],
    )],
    egress=[aws.ec2.SecurityGroupEgressArgs(
        protocol="-1",
        from_port=0,
        to_port=0,
        cidr_blocks=["0.0.0.0/0"],
    )],
)

# Correct the ALB egress relationship by referencing
# the task SG. A standalone rule avoids circular
# security-group references.
alb_egress = aws.ec2.SecurityGroupRule(
    "alb-to-tasks",
    type="egress",
    security_group_id=alb_sg.id,
    protocol="tcp",
    from_port=8000,
    to_port=8000,
    source_security_group_id=task_sg.id,
)

alb = aws.lb.LoadBalancer(
    "fastapi-alb",
    load_balancer_type="application",
    internal=False,
    subnets=public_subnet_ids,
    security_groups=[alb_sg.id],
)

target_group = aws.lb.TargetGroup(
    "fastapi-targets",
    port=8000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/health",
        protocol="HTTP",
        port="traffic-port",
        matcher="200",
        interval=30,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
)

# An ACM certificate must be supplied for a real HTTPS
# listener. This HTTP listener is for a lab variant only.
http_listener = aws.lb.Listener(
    "fastapi-http",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[aws.lb.ListenerDefaultActionArgs(
        type="forward",
        target_group_arn=target_group.arn,
    )],
)

cluster = aws.ecs.Cluster("fastapi-cluster")

execution_role_arn = config.require(
    "executionRoleArn"
)

task_definition = aws.ecs.TaskDefinition(
    "fastapi-task",
    family="fastapi",
    cpu="256",
    memory="512",
    network_mode="awsvpc",
    requires_compatibilities=["FARGATE"],
    execution_role_arn=execution_role_arn,
    container_definitions=pulumi.Output.all(
        log_group.name
    ).apply(lambda values: json.dumps([{
        "name": "fastapi",
        "image": image_uri,
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
                "awslogs-stream-prefix": "app",
            },
        },
    }])),
)

service = aws.ecs.Service(
    "fastapi-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=2,
    launch_type="FARGATE",
    platform_version="LATEST",
    health_check_grace_period_seconds=60,
    deployment_circuit_breaker=(
        aws.ecs.ServiceDeploymentCircuitBreakerArgs(
            enable=True,
            rollback=True,
        )
    ),
    network_configuration=(
        aws.ecs.ServiceNetworkConfigurationArgs(
            subnets=private_subnet_ids,
            security_groups=[task_sg.id],
            assign_public_ip=False,
        )
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=target_group.arn,
            container_name="fastapi",
            container_port=8000,
        )
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[http_listener, alb_egress]
    ),
)

pulumi.export(
    "albDnsName",
    alb.dns_name,
)
pulumi.export(
    "ecsClusterName",
    cluster.name,
)
pulumi.export(
    "ecsServiceName",
    service.name,
)
```

Important implementation notes before deploying:

* Add `executionRoleArn` to Pulumi configuration and ensure the role trusts `ecs-tasks.amazonaws.com` and has the required image-pull and log permissions.

* The code defines HTTP on port 80 as a lab listener. For an internet-facing production service, configure an ACM certificate, an HTTPS listener on port 443, and normally redirect HTTP to HTTPS.

* The ALB security group shown permits HTTPS ingress, while the illustrative listener is HTTP. For a working HTTP-only lab, allow inbound TCP 80 instead; for production HTTPS, add the certificate and HTTPS listener.

* The task security group has broad egress for simplicity. Tighten it for production, and add explicit rules for required endpoints and dependencies.

* This example does not create the VPC endpoints or NAT Gateway, nor does it create the execution role. Those are prerequisites to provision separately or add to the Pulumi program.

* Configure the task role separately if the application needs to call AWS APIs. Do not reuse the execution role as the application's general-purpose identity.

### 8.4 Validate the deployment

Run a preview before provisioning resources:

```bash
pulumi preview
pulumi up
```

Once deployment completes, retrieve the ALB DNS name:

```bash
pulumi stack output albDnsName
```

Test the HTTP lab listener:

```bash
curl -i http://$(pulumi stack output albDnsName)/health
```

Expected response:

```json
{"status":"ok"}
```

If the request fails, work through this checklist:

* ALB returns 503: Check target group health and whether ECS tasks are registered.

* Targets are unhealthy: Check the health-check path, application port, and task security group.

* Tasks stop during startup: Inspect ECS service events and stopped-task reasons.

* Image pull fails: Verify the image URI, execution-role permissions, and ECR/S3 network access.

* Logs are missing: Verify the execution role's CloudWatch Logs permissions, log group, and network connectivity.

* Tasks cannot reach AWS APIs: Check task-role permissions, DNS, endpoint policies, security groups, and routes.

Use the AWS CLI to inspect the service:

```bash
aws ecs describe-services \
  --cluster "$(pulumi stack output ecsClusterName)" \
  --services "$(pulumi stack output ecsServiceName)"
```

For target health, use the ELBv2 API to inspect the target group returned by your stack's resources.

### 8.5 Production improvements

Before treating this as production-ready, add the following:

* An ACM certificate and HTTPS listener.

* HTTP-to-HTTPS redirection.

* Explicitly managed security group rules without unintended default egress.

* A least-privilege execution role and a separate task role.

* NAT Gateway or the necessary VPC endpoints.

* A secrets-injection strategy where required.

* Deployment alarms and appropriate health-check settings.

* CloudWatch metrics, alarms, and suitable log retention.

* A documented rollback procedure.

Also consider enabling ECS deployment alarms and configuring autoscaling based on CPU, memory, or request load. A desired count of two is not, by itself, a complete high-availability or autoscaling strategy.

### 9\. Cost controls

The main costs to watch in this lab are:

| Resource                  | Cost consideration                                         |
| ------------------------- | ---------------------------------------------------------- |
| Fargate tasks             | vCPU and memory duration, plus applicable platform charges |
| Application Load Balancer | Time running and load-balancer capacity units              |
| NAT Gateway               | Hourly charges and data processing                         |
| VPC interface endpoints   | Hourly charges per endpoint/AZ and data processing         |
| CloudWatch Logs           | Ingestion, retention, and storage                          |
| ECR                       | Image storage and applicable data transfer                 |

For a small lab, the ALB and NAT Gateway can cost more than the application compute itself. Plan the lab in a short session, use a budget alert, and destroy the infrastructure when finished. Deleting the ECS service alone will not remove every billable resource.

### 10\. Clean up

After testing, remove the resources managed by your Pulumi stack:

```bash
pulumi destroy
```

Review the proposed deletions before confirming. Then verify that any separately managed resources—such as the ECR repository, VPC, NAT Gateway, endpoints, and IAM roles—are either intentionally retained or removed when safe to do so.

### 11\. Knowledge check

1. Why does a Fargate service using awsvpc normally require an IP-type target group?

Fargate tasks register their own network-interface IP addresses

Fargate tasks share the ALB's public IP

The ALB can only route to public subnets

2. What does the ECS task execution role primarily support?

Giving every application unrestricted AWS access

Image pulls, log delivery, and supported startup-time secret retrieval

Allowing inbound traffic through the ALB

3. Which configuration helps private Fargate tasks pull ECR images without NAT?

Only an Internet Gateway route in the private subnet

ECR API and Docker interface endpoints plus the required S3 image-layer access path

An ALB listener on port 443

4. What does an ECS deployment circuit breaker with rollback do?

Restarts the NAT Gateway automatically

Reverts a failed deployment to the last completed deployment when rollback is enabled

Restores deleted EBS snapshots

Reset quiz

### Module 8 completion criteria

You have completed this module when you can deploy a Fargate service in private subnets, route traffic through an ALB, retrieve centralized logs, explain the IAM roles involved, and diagnose a failed task or deployment.

The key lesson is that running containers is only one part of operating a service. Networking, identity, health checks, deployment behavior, observability, and cost controls must all work together.
