### AWS ECS/EKS — Module 4: Production ECS: Load Balancing, Scaling, and Operations

In this module, we'll extend the FastAPI application and ECS Fargate deployment from Modules 1–3 into a production-style architecture using Pulumi with Python.

We'll keep the existing `aws-containers` project, reuse the `fastapi-api` image in Amazon ECR, preserve the `/health` endpoint, and use Bash for all shell commands and scripts.

By the end, your application will run in private subnets behind an internet-facing Application Load Balancer (ALB), with service auto scaling, CloudWatch monitoring, secure configuration, and deployment rollback protection.

### 1\. Target architecture

![Accelerate Migration and Modernization with a Reusable Solution to Deploy Container Applications on AWS | AWS Partner Network (APN) Blog](https://images.openai.com/static-rsc-4/wS6JIqqWzwYcnxuuSjNJA0V7i6t9U9ceNDoupl5n09zMpWNhoJCbOwvrUlVW6EIXDDuH77V7i5ZzzdTyKGeMGevvy8xfDgfrM4smklSoCTSLju3Md9jJdIXoRyutPVxmWECr3lcbIjdiJahM0vlJ-RDYb2dEqczagb-EA_GbQhMMz9kgKnZi5hxtkGQ3Ka-Z?purpose=fullsize)

Internet clients

HTTPS / HTTP requests

Application Load Balancer

Public subnets across two Availability Zones

Listener · Target group · Health checks

Private subnets — ECS Fargate tasks

Task A

FastAPI :8000

Task B

FastAPI :8000

ECS service maintains the desired task count and replaces unhealthy tasks.

CloudWatch

Logs, metrics, alarms

Secrets Manager

Runtime configuration

The architecture has several important security boundaries:

* Only the ALB accepts public inbound application traffic.

* ECS tasks have no public IP addresses and accept traffic only from the ALB security group.

* The ECS task execution role pulls images from ECR, publishes logs, and retrieves configured startup secrets.

* The ECS task role is reserved for AWS API access by the application itself.

* CloudWatch tracks application logs, infrastructure metrics, and alarms.

* Private-subnet outbound access to AWS APIs must be provided through NAT or suitable VPC endpoints. This matters for image pulls, logging, and secret retrieval.

For this lab, we'll create a self-contained Pulumi stack with a new VPC, two public subnets, two private subnets, a NAT gateway, an ALB, and an ECS Fargate service. This avoids depending on undocumented subnet IDs from an earlier lab.

Cost warning: NAT gateways, ALBs, Fargate tasks, and CloudWatch resources can incur charges. We'll use a single NAT gateway and a small Fargate service for the lab, then remove the infrastructure afterward.

### 2\. Understand the production components

### Application Load Balancer and target groups

An ALB is the public entry point for HTTP and HTTPS traffic. It forwards requests to healthy ECS tasks registered in a target group.

For Fargate tasks using `awsvpc` networking, the target group must use IP targets, because each task has its own network interface and IP address.

| Component     | Responsibility                                                                 |
| ------------- | ------------------------------------------------------------------------------ |
| ALB           | Accepts HTTP/HTTPS requests and distributes traffic                            |
| Listener      | Listens on a port such as 80 or 443                                            |
| Listener rule | Routes requests by host, path, or other supported conditions                   |
| Target group  | Tracks ECS task IP addresses and their health                                  |
| Health check  | Calls /health and determines whether a task can receive traffic                |
| ECS service   | Maintains the desired number of tasks and registers them with the target group |

For production HTTPS, use an ACM certificate and a listener on port 443. We'll use HTTP for the initial lab to avoid requiring a domain and certificate; do not use that HTTP-only setup for sensitive production traffic.

### ECS service auto scaling

ECS service auto scaling adjusts the number of running tasks in response to demand.

* CPU utilization: useful for CPU-intensive workloads.

* Memory utilization: useful when memory consumption grows with traffic.

* ALB request count per target: useful for request-driven workloads, provided the target metric and scaling policy are configured appropriately.

We'll use target tracking based on average CPU utilization, with a minimum of two tasks and a maximum of four. This allows the service to maintain capacity across two Availability Zones while controlling costs.

### Deployment safety

ECS rolling deployments gradually replace old tasks with new ones. Two settings are particularly useful:

* `deployment_minimum_healthy_percent`: controls the minimum healthy capacity during a deployment.

* `deployment_maximum_percent`: limits how many tasks can run relative to the desired count during a deployment.

The deployment circuit breaker can detect failures and roll back to the last completed deployment when possible. It is not a substitute for application testing or database migration safeguards.

### 3\. Prepare the lab environment

We'll use the following layout, continuing from the project established in the earlier modules:

```text
aws-containers/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
└── infrastructure/
    ├── ecr-fastapi/
    └── ecs-production/
        ├── Pulumi.yaml
        ├── requirements.txt
        ├── __main__.py
        └── Pulumi.dev.yaml
```

The `ecr-fastapi` stack is the existing Module 2 repository stack, and `ecs-production` is our new stack for this module.

### 3.1 Verify AWS access

Run these commands in Bash from your terminal:

```bash
aws sts get-caller-identity
aws configure get region
pulumi version
python --version
docker --version
```

If the AWS region isn't configured, use the same region as the previous modules:

```bash
aws configure set region eu-west-2
```

Confirm that the account and region are correct before creating resources.

### 3.2 Retrieve the existing ECR image

Get your AWS account ID and the repository URI:

```bash
export AWS_REGION="eu-west-2"
export AWS_ACCOUNT_ID="$(aws sts get-caller-identity \
  --query Account --output text)"

export ECR_REPOSITORY="fastapi-api"
export ECR_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}:1.0.0"

aws ecr describe-repositories \
  --repository-names "$ECR_REPOSITORY" \
  --region "$AWS_REGION"

aws ecr describe-images \
  --repository-name "$ECR_REPOSITORY" \
  --image-ids imageTag=1.0.0 \
  --region "$AWS_REGION"
```

If your previous module used a different immutable image tag, use that tag instead of `1.0.0`.

Your FastAPI application must expose `/health` and listen on port `8000`, as established earlier.

### 4\. Create the Pulumi stack

Create the new infrastructure directory:

```bash
cd aws-containers/infrastructure

mkdir -p ecs-production
cd ecs-production

pulumi new aws-python
```

If Pulumi asks for a project name, use `ecs-production`. If the project already exists, retain its existing `Pulumi.yaml` rather than initializing it again.

Install the dependencies:

```bash
cat > requirements.txt <<'EOF'
pulumi>=3.0.0,<4.0.0
pulumi-aws>=7.0.0,<8.0.0
pulumi-awsx>=3.0.0,<4.0.0
EOF

python -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

These are major-version constraints rather than exact pins. For a reproducible production pipeline, lock and test the dependency versions used by your project.

Configure the stack:

```bash
pulumi stack select dev 2>/dev/null || pulumi stack init dev

pulumi config set aws:region eu-west-2
pulumi config set appName fastapi-api
pulumi config set imageTag 1.0.0
```

We will read the image tag and AWS region from Pulumi configuration rather than hard-coding them throughout the program.

### 5\. Implement the production ECS infrastructure

Create `__main__.py` in `infrastructure/ecs-production/`.

This program provisions the VPC, ALB, ECS cluster and Fargate service, CloudWatch log group, task IAM roles, CPU-based auto scaling, and deployment circuit breaker. It also supports an optional existing Secrets Manager secret.

File: `infrastructure/ecs-production/__main__.py`

```python

import json

import pulumi
import pulumi_aws as aws
import pulumi_awsx as awsx

config = pulumi.Config()
aws_config = pulumi.Config("aws")

region = aws_config.require("region")
app_name = config.get("appName") or "fastapi-api"
image_tag = config.get("imageTag") or "1.0.0"
secret_arn = config.get("secretArn")

caller = aws.get_caller_identity_output()
image_uri = pulumi.Output.concat(
    caller.account_id,
    ".dkr.ecr.",
    region,
    ".amazonaws.com/",
    app_name,
    ":",
    image_tag,
)

# ---------------------------------------------------------
# Networking: two AZs, public ALB, private ECS tasks.
# A single NAT gateway is a cost-saving lab configuration.
# ---------------------------------------------------------

vpc = awsx.ec2.Vpc(
    "production-vpc",
    number_of_availability_zones=2,
    nat_gateways=awsx.ec2.NatGatewayConfigurationArgs(
        strategy=awsx.ec2.NatGatewayStrategy.SINGLE,
    ),
    tags={"Project": "aws-containers", "Environment": "dev"},
)

# ---------------------------------------------------------
# Security groups
# ---------------------------------------------------------

alb_sg = aws.ec2.SecurityGroup(
    "alb-security-group",
    vpc_id=vpc.vpc_id,
    description="Public HTTP access to the ALB",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTP listener for lab",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

task_sg = aws.ec2.SecurityGroup(
    "ecs-task-security-group",
    vpc_id=vpc.vpc_id,
    description="Allow application traffic only from ALB",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            security_groups=[alb_sg.id],
            description="FastAPI traffic from ALB",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        ),
    ],
)

# ---------------------------------------------------------
# ALB, target group, listener and application health checks
# ---------------------------------------------------------

alb = aws.lb.LoadBalancer(
    "fastapi-alb",
    load_balancer_type="application",
    internal=False,
    security_groups=[alb_sg.id],
    subnets=vpc.public_subnet_ids,
    tags={"Name": "fastapi-alb"},
)

target_group = aws.lb.TargetGroup(
    "fastapi-target-group",
    port=8000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.vpc_id,
    deregistration_delay=30,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/health",
        protocol="HTTP",
        port="traffic-port",
        matcher="200",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
)

listener = aws.lb.Listener(
    "http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        ),
    ],
)

# ---------------------------------------------------------
# ECS cluster and CloudWatch Logs
# ---------------------------------------------------------

cluster = aws.ecs.Cluster(
    "fastapi-cluster",
    settings=[
        aws.ecs.ClusterSettingArgs(
            name="containerInsights",
            value="enabled",
        ),
    ],
)

log_group = aws.cloudwatch.LogGroup(
    "fastapi-log-group",
    name=f"/ecs/{app_name}/production-lab",
    retention_in_days=7,
)

# ---------------------------------------------------------
# IAM: task execution role and optional secret permission
# ---------------------------------------------------------

execution_role = aws.iam.Role(
    "ecs-task-execution-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

execution_policy = aws.iam.RolePolicyAttachment(
    "ecs-execution-managed-policy",
    role=execution_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AmazonECSTaskExecutionRolePolicy"
    ),
)

if secret_arn:
    secret_policy = aws.iam.RolePolicy(
        "ecs-secret-read-policy",
        role=execution_role.id,
        policy=pulumi.Output.all(secret_arn).apply(
            lambda values: json.dumps({
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": ["secretsmanager:GetSecretValue"],
                    "Resource": values[0],
                }],
            })
        ),
    )

task_role = aws.iam.Role(
    "ecs-application-task-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ecs-tasks.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

# ---------------------------------------------------------
# Task definition
# ---------------------------------------------------------

container_definition = pulumi.Output.all(
    image_uri, log_group.name
).apply(
    lambda values: json.dumps([{
        "name": "fastapi",
        "image": values[0],
        "essential": True,
        "cpu": 256,
        "memory": 512,
        "portMappings": [{
            "containerPort": 8000,
            "hostPort": 8000,
            "protocol": "tcp",
        }],
        "healthCheck": {
            "command": [
                "CMD",
                "python",
                "-c",
                (
                    "import urllib.request; "
                    "urllib.request.urlopen("
                    "'http://127.0.0.1:8000/health', timeout=3)"
                ),
            ],
            "interval": 30,
            "timeout": 5,
            "retries": 3,
            "startPeriod": 20,
        },
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": values[1],
                "awslogs-region": region,
                "awslogs-stream-prefix": "fastapi",
            },
        },
        **({
            "secrets": [{
                "name": "APP_SECRET",
                "valueFrom": secret_arn,
            }]
        } if secret_arn else {}),
    }])
)

task_definition = aws.ecs.TaskDefinition(
    "fastapi-task-definition",
    family=f"{app_name}-production-lab",
    requires_compatibilities=["FARGATE"],
    network_mode="awsvpc",
    cpu="256",
    memory="512",
    execution_role_arn=execution_role.arn,
    task_role_arn=task_role.arn,
    container_definitions=container_definition,
)

# ---------------------------------------------------------
# ECS service: private tasks, ALB target group, safe rollout
# ---------------------------------------------------------

service = aws.ecs.Service(
    "fastapi-service",
    cluster=cluster.arn,
    task_definition=task_definition.arn,
    desired_count=2,
    launch_type="FARGATE",
    enable_execute_command=True,
    health_check_grace_period_seconds=60,
    deployment_minimum_healthy_percent=100,
    deployment_maximum_percent=200,
    deployment_circuit_breaker=(
        aws.ecs.ServiceDeploymentCircuitBreakerArgs(
            enable=True,
            rollback=True,
        )
    ),
    network_configuration=aws.ecs.ServiceNetworkConfigurationArgs(
        subnets=vpc.private_subnet_ids,
        security_groups=[task_sg.id],
        assign_public_ip=False,
    ),
    load_balancers=[
        aws.ecs.ServiceLoadBalancerArgs(
            target_group_arn=target_group.arn,
            container_name="fastapi",
            container_port=8000,
        ),
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[listener, execution_policy],
    ),
)

# ---------------------------------------------------------
# Service auto scaling: desired task count from 2 to 4
# ---------------------------------------------------------

scaling_target = aws.appautoscaling.Target(
    "ecs-scaling-target",
    min_capacity=2,
    max_capacity=4,
    resource_id=pulumi.Output.concat(
        "service/", cluster.name, "/", service.name
    ),
    scalable_dimension="ecs:service:DesiredCount",
    service_namespace="ecs",
)

cpu_scaling_policy = aws.appautoscaling.Policy(
    "ecs-cpu-target-tracking",
    policy_type="TargetTrackingScaling",
    resource_id=scaling_target.resource_id,
    scalable_dimension=scaling_target.scalable_dimension,
    service_namespace=scaling_target.service_namespace,
    target_tracking_scaling_policy_configuration=(
        aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationArgs(
            target_value=60.0,
            predefined_metric_specification=(
                aws.appautoscaling.PolicyTargetTrackingScalingPolicyConfigurationPredefinedMetricSpecificationArgs(
                    predefined_metric_type=(
                        "ECSServiceAverageCPUUtilization"
                    ),
                )
            ),
            scale_in_cooldown=120,
            scale_out_cooldown=60,
        )
    ),
)

# ---------------------------------------------------------
# CloudWatch alarm: high CPU utilization
# ---------------------------------------------------------

cpu_alarm = aws.cloudwatch.MetricAlarm(
    "fastapi-high-cpu",
    alarm_description="ECS service CPU utilization is elevated",
    namespace="AWS/ECS",
    metric_name="CPUUtilization",
    statistic="Average",
    period=60,
    evaluation_periods=3,
    threshold=80,
    comparison_operator="GreaterThanThreshold",
    dimensions={
        "ClusterName": cluster.name,
        "ServiceName": service.name,
    },
    treat_missing_data="notBreaching",
)

# ---------------------------------------------------------
# Outputs
# ---------------------------------------------------------

pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("application_url", pulumi.Output.concat(
    "http://", alb.dns_name
))
pulumi.export("ecs_cluster_name", cluster.name)
pulumi.export("ecs_service_name", service.name)
pulumi.export("log_group_name", log_group.name)
pulumi.export("target_group_arn", target_group.arn)
```

The design follows Pulumi's ECS and load-balancing resource model. [Pulumi's ECS guide](https://www.pulumi.com/docs/iac/clouds/aws/guides/ecs/?utm_source=chatgpt.com) provides further context for the load-balanced service pattern. Pulumi Docs +1

### Important implementation notes

* The AWSX VPC component supplies the public/private subnet layout and NAT configuration. Review the generated subnet and route-table plan before deploying.

* The task definition includes a container health check as well as an ALB target-group health check. These monitor different layers.

* The execution role has the standard ECS execution policy. The optional secret policy is scoped to the configured secret ARN; if the secret uses a customer-managed KMS key, the role may also require narrowly scoped `kms:Decrypt` permission.

* The application task role intentionally has no additional permissions. Add only the AWS API permissions your application actually needs.

* The example uses HTTP and an open public listener for learning purposes. Before production, configure HTTPS, restrict administrative access, review outbound egress, and apply least-privilege policies.

* The CPU alarm reports elevated utilization but does not automatically notify anyone. For notifications, connect it to an SNS topic and subscription.

* ECS Exec requires the appropriate task-role permissions and SSM connectivity. The execution role and task role are not interchangeable.

### 6\. Review and deploy the infrastructure

### 6.1 Preview before creating resources

Run these commands from the `ecs-production` directory:

```bash
pulumi preview
```

Review the planned changes. You should see resources for networking, security groups, the ALB, ECS, IAM, scaling, and CloudWatch.

Then deploy:

```bash
pulumi up
```

Review the plan and approve it when you're ready.

Wait for the ECS service to stabilize. Then retrieve the application URL and service identifiers:

```bash
export APP_URL="$(pulumi stack output application_url)"
export ECS_CLUSTER="$(pulumi stack output ecs_cluster_name)"
export ECS_SERVICE="$(pulumi stack output ecs_service_name)"
export LOG_GROUP="$(pulumi stack output log_group_name)"

printf 'Application URL: %s\n' "$APP_URL"
```

### 6.2 Test the application

Check the health endpoint:

```bash
curl --fail --show-error "$APP_URL/health"
```

Expected response:

```json
{"status":"healthy"}
```

You can also inspect the root endpoint:

```bash
curl --fail --show-error "$APP_URL/"
```

If the request fails, don't immediately change the security groups. First check whether the ALB has healthy targets.

### 6.3 Inspect ECS tasks

```bash
aws ecs describe-services \
  --cluster "$ECS_CLUSTER" \
  --services "$ECS_SERVICE" \
  --query 'services[0].{Status:status,Desired:desiredCount,Running:runningCount,Pending:pendingCount,Events:events[0:5]}' \
  --output json
```

List the task ARNs:

```bash
aws ecs list-tasks \
  --cluster "$ECS_CLUSTER" \
  --service-name "$ECS_SERVICE" \
  --desired-status RUNNING \
  --query 'taskArns' \
  --output text
```

Inspect the target group health:

```bash
export TARGET_GROUP_ARN="$(pulumi stack output target_group_arn)"

aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --query 'TargetHealthDescriptions[*].{IP:Target.Id,Port:Target.Port,State:TargetHealth.State,Reason:TargetHealth.Reason}' \
  --output table
```

The target group should eventually show healthy targets corresponding to your running ECS tasks.

### 7\. Configure and observe auto scaling

The stack uses target tracking to maintain average ECS service CPU utilization near 60%, with a minimum of two tasks and a maximum of four.

Inspect the scaling target and policy:

```bash
aws application-autoscaling describe-scalable-targets \
  --service-namespace ecs \
  --resource-ids "service/$ECS_CLUSTER/$ECS_SERVICE"
```

```bash
aws application-autoscaling describe-scaling-policies \
  --service-namespace ecs \
  --resource-id "service/$ECS_CLUSTER/$ECS_SERVICE"
```

Watch service task counts:

```bash
watch -n 10 "aws ecs describe-services \
  --cluster '$ECS_CLUSTER' \
  --services '$ECS_SERVICE' \
  --query 'services[0].{Desired:desiredCount,Running:runningCount,Pending:pendingCount}' \
  --output table"
```

The `watch` command is available in most Linux environments and Git Bash may not include it by default. If it isn't available, run the AWS CLI command repeatedly or use a Bash loop.

For a request-driven workload, you can later use the `ALBRequestCountPerTarget` predefined metric. That policy requires the ALB target group's resource label and a suitable requests-per-target target value.

### Fargate and Fargate Spot

This service uses regular Fargate capacity. Fargate Spot can reduce costs for interruptible workloads, but it can be reclaimed by AWS. It is best suited to fault-tolerant workloads that can handle task interruption.

For a production service, choose a capacity strategy based on availability requirements, interruption tolerance, and cost. Don't assume Fargate Spot is an automatic replacement for regular Fargate capacity.

### 8\. CloudWatch logs, alarms, and ECS Exec

### 8.1 Read application logs

The task definition sends container output to the log group created by Pulumi.

```bash
aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime \
  --descending \
  --limit 5
```

Read recent log events:

```bash
aws logs tail "$LOG_GROUP" \
  --since 15m \
  --follow
```

Stop following the logs with `Ctrl+C`.

If the log group exists but no events appear, check the task's startup status, execution role permissions, and the container's stdout/stderr output.

### 8.2 Inspect CloudWatch metrics

Query the service's CPU utilization:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/ECS \
  --metric-name CPUUtilization \
  --dimensions \
    Name=ClusterName,Value="$ECS_CLUSTER" \
    Name=ServiceName,Value="$ECS_SERVICE" \
  --start-time "$(date -u -d '30 minutes ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Average Maximum
```

This command uses GNU `date`, as commonly available on Linux. If your Bash environment uses a different `date` implementation, supply the UTC timestamps manually.

The alarm created by Pulumi evaluates CPU utilization every minute across three evaluation periods. A high CPU reading does not necessarily indicate a failed application; correlate it with request volume, latency, memory usage, and task counts.

### 8.3 Enable ECS Exec properly

The sample service enables ECS Exec, but the task role must also permit the SSM Messages channel actions. Add the following resource after the `task_role` declaration in `__main__.py`:

```python
ecs_exec_policy = aws.iam.RolePolicy(
    "ecs-exec-ssm-messages-policy",
    role=task_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "ssmmessages:CreateControlChannel",
                "ssmmessages:CreateDataChannel",
                "ssmmessages:OpenControlChannel",
                "ssmmessages:OpenDataChannel",
            ],
            "Resource": "*",
        }],
    }),
)
```

Add `ecs_exec_policy` to the ECS service's `depends_on` list alongside the listener and execution policy. Then apply the changes:

```bash
pulumi preview
pulumi up
```

The operator also needs suitable IAM permissions for ECS Exec. Private tasks must be able to reach the required SSM Messages service, either through NAT or the appropriate VPC endpoints. Existing tasks may need to be replaced after enabling ECS Exec or changing the relevant task configuration.

Once the service is ready, retrieve a running task ARN:

```bash
export TASK_ARN="$(aws ecs list-tasks \
  --cluster "$ECS_CLUSTER" \
  --service-name "$ECS_SERVICE" \
  --desired-status RUNNING \
  --query 'taskArns[0]' \
  --output text)"

printf '%s\n' "$TASK_ARN"
```

Start a shell in the container:

```bash
aws ecs execute-command \
  --cluster "$ECS_CLUSTER" \
  --task "$TASK_ARN" \
  --container fastapi \
  --interactive \
  --command "/bin/sh"
```

ECS Exec uses the SSM Messages channel rather than opening an inbound SSH port. The container image must contain the required ECS Exec support, and the task must be running with a compatible Fargate platform version.

### 9\. Integrate AWS Secrets Manager

The stack accepts an optional existing secret ARN. It doesn't create a secret or store a plaintext secret in Pulumi configuration.

Create a secret for the lab using a placeholder value:

```bash
aws secretsmanager create-secret \
  --name fastapi-production-lab \
  --description "Demo secret for the ECS lab" \
  --secret-string '{"demo":"replace-with-a-non-production-value"}'
```

Capture the returned ARN:

```bash
export SECRET_ARN="$(aws secretsmanager describe-secret \
  --secret-id fastapi-production-lab \
  --query ARN \
  --output text)"

pulumi config set secretArn "$SECRET_ARN"
```

The program injects the configured secret as the `APP_SECRET` environment variable at container startup. This example is only a demonstration: the current FastAPI application may not use that variable, and you should not treat the placeholder as a real credential.

For this configuration to work:

* The task execution role needs `secretsmanager:GetSecretValue` for the secret.

* If you use a customer-managed KMS key, the required decryption permission must also be granted.

* The task needs network access to Secrets Manager.

* Secret changes aren't automatically reflected in already-running containers; force a new deployment or replace tasks to retrieve the updated value.

Parameter Store `SecureString` is another option for configuration. It has its own IAM and KMS permission requirements.

Security note: Secret values should not be printed in logs, exported as stack outputs, or passed as ordinary plaintext Pulumi configuration.

### 10\. Troubleshoot common production failures

Use the following workflow to diagnose problems systematically.

### Problem 1 — ALB returns HTTP 503

Likely cause: no healthy targets.

* Run `describe-target-health` for the target group.

* Confirm that ECS tasks are running.

* Verify the container listens on `0.0.0.0:8000`, not just `127.0.0.1:8000`.

* Confirm `/health` returns HTTP 200.

* Verify the ALB security group can reach port 8000 on the task security group.

### Problem 2 — ECS tasks repeatedly stop

Likely cause: application startup failure, resource limits, or missing permissions.

```bash
aws ecs describe-services \
  --cluster "$ECS_CLUSTER" \
  --services "$ECS_SERVICE" \
  --query 'services[0].events[0:10]' \
  --output table
```

Retrieve stopped tasks and their stop reasons:

```bash
aws ecs list-tasks \
  --cluster "$ECS_CLUSTER" \
  --service-name "$ECS_SERVICE" \
  --desired-status STOPPED
```

Use the returned task ARN with `aws ecs describe-tasks` and inspect `stoppedReason`, `stopCode`, and the container's `reason` and `exitCode`.

### Problem 3 — ECR image pull or logging failure

Likely cause: execution role or private-subnet connectivity.

* Check the ECS task execution role and its managed policy.

* Verify the image URI and tag.

* Check NAT gateway routes or required VPC endpoints.

* Check whether the task can retrieve startup secrets.

* Inspect ECS service events and stopped-task reasons.

### Problem 4 — Deployment rollback

Likely cause: replacement tasks failed to become healthy.

* Inspect the ECS service deployment state and service events.

* Check target-group health and container health checks.

* Confirm the image starts correctly with the expected environment.

* Check CPU/memory allocation and IAM permissions.

* Deploy a corrected image and verify the new deployment before proceeding.

### 11\. Review the infrastructure and clean up

Before finishing, verify the service is healthy and review the infrastructure you created.

```bash
pulumi stack output
pulumi preview
```

For a short-lived lab, destroy the resources when you're done:

```bash
pulumi destroy
```

Confirm the deletion when prompted. This removes the resources managed by this stack, including the NAT gateway, ALB, ECS service, and networking resources. Check for any remaining resources or charges in AWS afterward. The ECR repository from Module 2 and the separately created Secrets Manager secret may remain because they belong to, or were created outside, this stack.

If you no longer need the lab secret, delete it separately:

```bash
aws secretsmanager delete-secret \
  --secret-id fastapi-production-lab \
  --recovery-window-in-days 7
```

The recovery window is intentional: it allows recovery if the deletion was accidental.

### Module 4 completion checklist

### Lab progress

0 of 10

Provisioned public and private subnets across two Availability Zones.

Deployed ECS Fargate tasks without public IP addresses.

Exposed FastAPI through an ALB and verified /health.

Configured target-group health checks and ECS deployment rollback.

Configured CPU-based ECS service auto scaling.

Inspected CloudWatch logs, metrics, and alarms.

Reviewed ECS task execution roles versus application task roles.

Configured optional Secrets Manager integration and reviewed ECS Exec.

Diagnosed a target-health, task-startup, or IAM-related failure.

Destroyed lab resources and reviewed remaining AWS resources.

### What you've learned

You now have a blueprint for running FastAPI on ECS Fargate with load balancing, private networking, auto scaling, deployment safeguards, secure configuration, and operational visibility.

One important production distinction remains: a healthy ECS deployment is not automatically a highly available application. Availability also depends on application behavior, multi-AZ capacity, dependency health, deployment strategy, observability, and recovery procedures.

Next, Module 5 moves to Kubernetes fundamentals and Amazon EKS, where we'll compare the Kubernetes control plane, workloads, networking, and operational responsibilities with the ECS model.
