### Module 5 — EC2 Auto Scaling

Phase 4: Compute · AWS hands-on course · Pulumi with Python

### Learning objectives

By the end of this module, you will be able to:

* Explain how EC2 Auto Scaling maintains application capacity and availability.

* Create launch templates and Auto Scaling groups.

* Configure minimum, maximum, and desired capacity.

* Implement target tracking, step scaling, and scheduled scaling.

* Configure health checks and replace unhealthy EC2 instances.

* Integrate Auto Scaling with an Application Load Balancer (ALB).

* Deploy instances across multiple Availability Zones.

* Provision and manage the infrastructure using Pulumi and Python.

### 1\. Why do we need Auto Scaling?

Imagine you have deployed a FastAPI application on two EC2 instances behind an Application Load Balancer.

At first, the application handles traffic comfortably. Later, traffic increases significantly. The instances become overloaded, requests slow down, and users experience timeouts.

You could manually launch more instances, but that creates operational problems:

* You must monitor traffic and decide when to add capacity.

* You must configure each new instance consistently.

* You must replace failed instances.

* You must remove unnecessary capacity when traffic decreases.

* You must maintain availability when an Availability Zone experiences problems.

EC2 Auto Scaling automates the management of your EC2 instance fleet. It can launch and terminate instances to maintain desired capacity, respond to scaling policies, and replace instances it identifies as unhealthy.

### The basic architecture

Users

HTTP and HTTPS traffic

Application Load Balancer

Routes requests to healthy targets

### EC2 Auto Scaling group

EC2 instance A

Availability Zone A

EC2 instance B

Availability Zone B

The group launches, maintains, and replaces instances according to its configuration and policies.

The key idea is that you manage a group of instances, rather than manually managing each individual server.

### 2\. Core components

### 2.1 Launch templates

A launch template defines how Auto Scaling should create an EC2 instance.

It can specify:

* AMI ID.

* Instance type.

* SSH key pair, if needed.

* Security groups.

* IAM instance profile.

* EBS volume configuration.

* User data for bootstrapping.

* Metadata and resource tags.

For example, a launch template might specify an Amazon Linux AMI, a `t3.micro` instance, an application security group, and a startup script that installs and starts your FastAPI application.

When Auto Scaling needs another instance, it uses the launch template to create one consistently.

Important: A launch template defines the instance configuration; it does not manage the number of instances. That responsibility belongs to the Auto Scaling group.

### 2.2 Auto Scaling groups

An Auto Scaling group (ASG) manages a fleet of EC2 instances across selected subnets and Availability Zones.

Its primary capacity settings are:

| Setting          | Meaning                      | Example |
| ---------------- | ---------------------------- | ------- |
| Minimum capacity | Lowest permitted group size  | 2       |
| Desired capacity | Target number of instances   | 2       |
| Maximum capacity | Highest permitted group size | 6       |

Suppose the configuration is:

Minimum

### 2

Desired

### 2

Maximum

### 6

Illustrative capacity range

1

2

3

4

5

6

The group starts with two instances. Scaling policies can increase capacity up to six, while scale-in policies must respect the minimum of two.

If demand increases, a scaling policy can increase desired capacity from two to four. If demand falls, it can reduce desired capacity again, but not below the configured minimum.

Desired capacity can also be changed manually. Auto Scaling then attempts to reconcile the actual fleet with the desired capacity, subject to service limits, availability, and the group's configuration.

### 2.3 Availability Zones and subnet placement

For high availability, configure the Auto Scaling group to use subnets in at least two Availability Zones.

For example:

* `us-west-2a`: application subnet A.

* `us-west-2b`: application subnet B.

The Auto Scaling group distributes instances across the selected zones as best it can. If an instance fails, it can launch a replacement. If an Availability Zone becomes impaired, Auto Scaling can launch capacity in another usable zone, provided the configuration and available capacity permit it.

Remember the distinction:

* Multiple instances protect against individual instance failures.

* Multiple Availability Zones reduce dependence on a single zone.

* An ALB distributes requests and checks target health.

* An Auto Scaling group manages instance capacity and replacement.

Using multiple AZs improves resilience, but does not guarantee that the application itself is fault tolerant. Your application must also handle lost instances, interrupted requests, and shared dependencies appropriately.

### 3\. Scaling policies

Auto Scaling supports several approaches to deciding when and how much to scale.

Target tracking scaling

Maintain a metric around a target value, such as average CPU utilization of 50%.

Best starting point for most web applications.

Step scaling

Change capacity by different amounts depending on how far a CloudWatch alarm metric crosses its thresholds.

Useful when you need more explicit control over the scaling response.

Scheduled scaling

Adjust capacity at known times, such as increasing desired capacity before a predictable morning traffic spike.

Useful for workloads with predictable schedules.

### 3.1 Target tracking example

Suppose you configure:

* Minimum capacity: 2.

* Maximum capacity: 6.

* Target average CPU utilization: 50%.

As demand rises, average CPU utilization increases. Auto Scaling adjusts the desired capacity to help maintain the target. As demand decreases, it can reduce capacity.

The policy is not a rigid rule that instantly forces CPU to exactly 50%. Scaling takes time, and the metric is affected by traffic, application startup, and metric evaluation periods.

For web applications, CPU is not always the best signal. Depending on the workload, you might use:

* ALB requests per target.

* Average CPU utilization.

* Average network throughput.

* A custom application metric.

Important: If the application is slow because of database contention or a downstream API, adding more EC2 instances may not fix the bottleneck. Scaling policies must reflect the actual capacity constraint.

### 3.2 Step scaling example

Imagine a CloudWatch alarm monitors average CPU utilization.

| Average CPU | Example scaling adjustment |
| ----------- | -------------------------- |
| Below 40%   | No scale-out action        |
| 60–75%      | Add 1 instance             |
| Above 75%   | Add 2 instances            |

These are illustrative thresholds, not universal recommendations. You configure CloudWatch alarms and step adjustments explicitly.

### 3.3 Scheduled scaling example

A service typically experiences high traffic from 9 AM to 5 PM.

You could increase desired capacity before 9 AM and reduce it after 5 PM. Scheduled scaling is especially useful when the workload pattern is known in advance.

Keep a suitable minimum capacity if the service must remain available outside those hours.

### 4\. Health checks and unhealthy-instance replacement

Auto Scaling needs a way to identify instances that should be replaced.

### EC2 health checks

EC2 health checks can detect problems at the instance level, such as an instance entering a failed status.

### Elastic Load Balancing health checks

When you integrate an ASG with a target group, you can configure the group to use ELB health checks as well as EC2 health checks.

The ALB periodically checks registered targets using the target group's health-check configuration. For example, your FastAPI application might expose:

`GET /health`

The endpoint should return a successful response only when the application can serve requests according to your chosen health-check contract.

A healthy instance can receive traffic. An unhealthy target is generally removed from normal routing. When ELB health checks are enabled for the ASG, Auto Scaling can also replace an instance marked unhealthy.

### Health-check grace period

New instances need time to boot, install dependencies, and start the application. A health-check grace period helps prevent Auto Scaling from prematurely replacing an instance before it has had time to initialize.

The grace period is not a substitute for a correct health-check endpoint. Set it based on actual startup behavior.

### Instance replacement lifecycle

### 1

Instance becomes unhealthy

An EC2 or enabled ELB health check detects a failure.

### 2

Auto Scaling marks it for replacement

The group initiates the configured termination and replacement process.

### 3

A replacement instance launches

The launch template supplies its AMI, instance type, security groups, and startup configuration.

### 4

The application starts

User data bootstraps the instance and the health endpoint becomes available.

### 5

The target becomes healthy

The ALB can route normal traffic to the replacement target.

A crucial distinction: an ALB health check can stop routing traffic to a failed target, but without ELB health checks enabled for the ASG, an ALB-unhealthy target is not necessarily replaced by Auto Scaling.

### 5\. Lifecycle hooks and graceful termination

Sometimes an instance must perform an operation before it terminates or before it starts serving traffic.

Auto Scaling lifecycle hooks provide a way to pause an instance's lifecycle at certain transition points. You can then perform actions such as:

* Drain application work before termination.

* Finish background tasks.

* Send notifications to an event handler.

* Collect diagnostic information.

* Register or prepare an instance for application initialization.

A lifecycle hook typically works with a notification or event-processing mechanism and a completion action. If the hook is not completed before its timeout and default result take effect, the lifecycle proceeds according to the hook's configured behavior.

For a stateless FastAPI web service, lifecycle hooks are not always necessary in a basic lab. They become more valuable when instances perform background jobs, hold work that must be drained, or need controlled shutdown.

### 6\. Integrating Auto Scaling with an ALB

The integration connects three resources:

* An Application Load Balancer receives client requests.

* A target group identifies the application instances and checks their health.

* The Auto Scaling group registers launched instances with the target group and deregisters instances as they leave the group.

The ALB and the EC2 instances need appropriate security groups:

* The ALB security group allows inbound HTTP or HTTPS from the intended clients.

* The EC2 security group allows application traffic from the ALB security group, rather than permitting unrestricted public access to the application port.

This follows the same network segmentation principles you learned in the VPC modules.

For a production HTTPS endpoint, you would normally add an ACM certificate and an HTTPS listener. The lab below uses HTTP to keep the first deployment focused on Auto Scaling; do not use that simplified setup as a production security recommendation.

### 7\. Hands-on lab — Build an ALB-backed Auto Scaling group

Practical lab

### Lab architecture

You will provision these resources using Pulumi and Python:

* An Application Load Balancer.

* A target group with a `/health` health check.

* A launch template with EC2 user data.

* An Auto Scaling group across two private or public application subnets.

* Security groups that restrict application traffic to the ALB.

* A target tracking scaling policy based on CPU utilization.

For simplicity, the example uses a small Python HTTP server instead of installing a full FastAPI application. It provides the same infrastructure learning objectives: bootstrapping, health checks, load balancing, and instance replacement. You can replace the application with FastAPI afterward.

### Step 1 — Prerequisites

You need:

* An AWS account and credentials configured through an AWS-supported authentication method.

* Python 3.11 or later.

* The Pulumi CLI.

* An AWS VPC with two subnets in different Availability Zones.

* The ability to create EC2 instances, load balancers, security groups, and Auto Scaling resources.

Install the Pulumi AWS SDK:

```bash
mkdir ec2-autoscaling-lab
cd ec2-autoscaling-lab

pulumi new aws-python
```

Follow the prompts to create a stack, choose a region, and configure the project.

If you already have a VPC from your networking labs, use it rather than creating a separate network.

Configure the VPC and subnet IDs as stack configuration:

```bash
pulumi config set vpcId vpc-xxxxxxxxxxxxxxxxx
pulumi config set subnetIds '["subnet-aaaaaaaa","subnet-bbbbbbbb"]'
```

Replace these example IDs with your actual VPC and subnet IDs. Ensure the two subnets belong to different Availability Zones.

### Step 2 — Understand the security groups

We will create two security groups:

| Security group     | Inbound traffic                                   |
| ------------------ | ------------------------------------------------- |
| ALB security group | HTTP on port 80 from your intended client network |
| EC2 security group | HTTP on port 80 from the ALB security group only  |

For this lab, the ALB rule below permits traffic from `0.0.0.0/0`, making the HTTP endpoint publicly reachable. Restrict that CIDR to your own IP address if appropriate, or use a private ALB for an internal-only exercise.

### Step 3 — Implement the infrastructure

Replace the generated `__main__.py` with the following code.

```python

import base64

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
subnet_ids = config.require_object("subnetIds")

if len(subnet_ids) < 2:
    raise ValueError("Provide at least two subnets in different AZs.")

# --------------------------------------------------
# 1. Security groups
# --------------------------------------------------

alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    description="Allow HTTP traffic to the public ALB",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

instance_sg = aws.ec2.SecurityGroup(
    "instance-sg",
    description="Allow application traffic only from the ALB",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            security_groups=[alb_sg.id],
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
        )
    ],
)

# --------------------------------------------------
# 2. Application Load Balancer and target group
# --------------------------------------------------

alb = aws.lb.LoadBalancer(
    "app-alb",
    load_balancer_type="application",
    internal=False,
    security_groups=[alb_sg.id],
    subnets=subnet_ids,
)

target_group = aws.lb.TargetGroup(
    "app-targets",
    port=80,
    protocol="HTTP",
    vpc_id=vpc_id,
    target_type="instance",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/health",
        protocol="HTTP",
        matcher="200",
        interval=15,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=2,
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
        )
    ],
)

# --------------------------------------------------
# 3. Find the latest Amazon Linux 2023 x86_64 AMI
# --------------------------------------------------

ami = aws.ec2.get_ami_output(
    most_recent=True,
    owners=["amazon"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["al2023-ami-*-x86_64"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="architecture",
            values=["x86_64"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="state",
            values=["available"],
        ),
    ],
)

# --------------------------------------------------
# 4. Bootstrap a small HTTP application
# --------------------------------------------------

user_data = """#!/bin/bash
set -euxo pipefail

dnf install -y python3

cat > /opt/app.py <<'PY'
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket
import time

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
            return

        if self.path == "/fail":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"simulated failure")
            return

        body = (
            f"Hello from {socket.gethostname()}\\n"
            f"Time: {time.time()}\\n"
        ).encode()

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

HTTPServer(("0.0.0.0", 80), Handler).serve_forever()
PY

cat > /etc/systemd/system/lab-app.service <<'SERVICE'
[Unit]
Description=Auto Scaling Lab HTTP Application
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/app.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now lab-app
"""

launch_template = aws.ec2.LaunchTemplate(
    "app-launch-template",
    image_id=ami.id,
    instance_type="t3.micro",
    vpc_security_group_ids=[instance_sg.id],
    user_data=base64.b64encode(
        user_data.encode()
    ).decode(),
    update_default_version=True,
    metadata_options=aws.ec2.LaunchTemplateMetadataOptionsArgs(
        http_endpoint="enabled",
        http_tokens="required",
    ),
    tag_specifications=[
        aws.ec2.LaunchTemplateTagSpecificationArgs(
            resource_type="instance",
            tags={
                "Name": "autoscaling-lab-instance",
                "Project": "ec2-autoscaling-lab",
            },
        )
    ],
)

# --------------------------------------------------
# 5. Auto Scaling group
# --------------------------------------------------

asg = aws.autoscaling.Group(
    "app-asg",
    min_size=2,
    desired_capacity=2,
    max_size=6,
    vpc_zone_identifiers=subnet_ids,
    target_group_arns=[target_group.arn],
    health_check_type="ELB",
    health_check_grace_period=180,
    launch_template=aws.autoscaling.GroupLaunchTemplateArgs(
        id=launch_template.id,
        version=launch_template.latest_version.apply(str),
    ),
    tags=[
        aws.autoscaling.GroupTagArgs(
            key="Project",
            value="ec2-autoscaling-lab",
            propagate_at_launch=True,
        )
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[listener],
    ),
)

# --------------------------------------------------
# 6. Target tracking scaling policy
# --------------------------------------------------

cpu_policy = aws.autoscaling.Policy(
    "cpu-target-tracking",
    autoscaling_group_name=asg.name,
    policy_type="TargetTrackingScaling",
    target_tracking_configuration=(
        aws.autoscaling.PolicyTargetTrackingConfigurationArgs(
            target_value=50.0,
            predefined_metric_specification=(
                aws.autoscaling.PolicyTargetTrackingConfigurationPredefinedMetricSpecificationArgs(
                    predefined_metric_type="ASGAverageCPUUtilization",
                )
            ),
        )
    ),
)

pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("target_group_arn", target_group.arn)
pulumi.export("autoscaling_group_name", asg.name)
pulumi.export("launch_template_id", launch_template.id)
pulumi.export("cpu_policy_arn", cpu_policy.arn)
```

### Step 4 — Deploy

Run:

```bash
pulumi preview
pulumi up
```

Review the proposed changes before confirming deployment.

After the deployment completes, retrieve the ALB address:

```bash
pulumi stack output alb_dns_name
```

Open the address in a browser or query it from a terminal:

```bash
curl "http://$(pulumi stack output alb_dns_name)/"
```

Repeated requests should eventually show different instance hostnames, although target distribution is not guaranteed to alternate perfectly.

Check the health endpoint:

```bash
curl "http://$(pulumi stack output alb_dns_name)/health"
```

Expected response:

```text
ok
```

If the target group reports unhealthy targets, check the instance bootstrap logs, security groups, subnet routing, and target-group health-check settings.

Networking note: This example requires the EC2 instances to have outbound access to install Python through `dnf`. If your subnets are private, provide suitable outbound connectivity, such as a NAT Gateway, or bake the application dependencies into a custom AMI. A NAT Gateway can add significant cost.

### 8\. Test scaling and instance replacement

Now verify that the infrastructure actually behaves as expected.

### Test A — Verify initial capacity

In the AWS Console, open EC2 → Auto Scaling Groups → app-asg.

Verify:

* Desired capacity is 2.

* Two instances are running.

* The instances are distributed across your selected Availability Zones as far as placement permits.

* The target group shows both instances as healthy.

* The ALB responds successfully.

You can also use the AWS CLI:

```bash
aws autoscaling describe-auto-scaling-groups \
  --auto-scaling-group-names app-asg
```

Use the actual Auto Scaling group name from:

```bash
pulumi stack output autoscaling_group_name
```

### Test B — Simulate an instance failure

The simplest test is to terminate an EC2 instance managed by the ASG.

* Open the EC2 console.

* Find an instance belonging to your Auto Scaling group.

* Terminate that instance.

* Watch the Auto Scaling activity history.

* Confirm that a replacement launches.

* Wait for the new target to become healthy.

* Confirm that the group returns to its desired capacity.

You can also terminate an instance using the CLI, substituting the actual instance ID:

```bash
aws ec2 terminate-instances \
  --instance-ids i-0123456789abcdef0
```

Do not terminate an instance that belongs to another workload.

Expected result: Auto Scaling detects the reduction in healthy group capacity and attempts to launch a replacement.

This tests instance replacement, but it does not yet test ELB health-based replacement.

### Test C — Test ELB health-based replacement

The application in the lab returns HTTP 500 from `/fail`, but its health endpoint `/health` remains healthy. Therefore, requesting `/fail` will not trigger replacement.

To test ELB health-based replacement, deliberately make the health endpoint fail on one instance:

* Connect to one instance through Systems Manager Session Manager, if you have configured the required instance role and permissions, or another authorized administrative access method.

* Stop the `lab-app` systemd service on that instance.

* Wait for the target group's health checks to mark it unhealthy.

* Confirm that the ASG detects the ELB health failure and begins replacing the instance.

* Verify that the replacement starts and becomes healthy.

For example, on the selected instance:

```bash
sudo systemctl stop lab-app
```

Because the application service is configured with `Restart=always`, systemd may restart it after the stop operation. For a reliable test, temporarily disable its restart behavior or use an approved test-specific failure mechanism. Restore the service configuration after the test.

Allow time for health-check thresholds, the grace period, and instance startup. A replacement is not necessarily immediate.

### Test D — Test target tracking scaling

The lab's target tracking policy uses average CPU utilization with a target of 50%.

To test it:

* Connect to the application instances through an approved administration method.

* Generate sustained CPU load on the instances.

* Observe average CPU utilization in CloudWatch.

* Inspect the ASG activity history and desired capacity.

* Stop the load and observe whether capacity eventually scales in.

For example, if `stress-ng` is already installed on a test instance:

```bash
stress-ng --cpu 2 --timeout 5m
```

This runs CPU stress for five minutes. Install tools only on your test instances, and monitor the actual CPU metrics before concluding that the scaling policy should activate.

Scaling can take several minutes. A short burst might end before the metric evaluation and scaling response complete.

Do not expect an immediate increase in instance count. Target tracking is a feedback mechanism, not an instantaneous threshold trigger. The small `t3.micro` instances also use burstable CPU credits, which can affect the results.

### 9\. Troubleshooting guide

| Symptom                             | What to investigate                                                                                              |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------- |
| ALB returns 503                     | Whether healthy targets are registered and the application is listening on port 80                               |
| Targets remain unhealthy            | Health-check path, response code, security groups, startup logs, and application status                          |
| Instances fail to launch            | EC2 quotas, instance availability, subnet IP capacity, launch-template settings, and IAM permissions             |
| ASG launches but does not scale out | CPU metrics, scaling policy configuration, cooldown or warmup behavior, and current maximum capacity             |
| ASG replaces instances repeatedly   | Health-check grace period, bootstrap failures, bad AMI, application startup time, and target-group health checks |
| ALB cannot reach instances          | Whether the instance security group allows traffic from the ALB security group                                   |
| Instances cannot install packages   | NAT Gateway or other outbound connectivity, DNS, routes, and package repository access                           |

A good troubleshooting habit is to inspect the Auto Scaling group's Activity history first. It often explains whether an instance launch or termination succeeded and, if not, why it failed.

### 10\. Production considerations

Before using this design for a real application, address these areas:

* HTTPS: Add an ACM certificate and an HTTPS listener.

* Instance identity: Use a least-privilege IAM instance profile where AWS API access is required.

* Management access: Prefer Systems Manager Session Manager over opening SSH to the internet.

* Application readiness: Use health checks that accurately reflect whether the application can serve requests.

* Deployment updates: Use launch-template versions and an appropriate instance refresh strategy when rolling out new AMIs or application versions.

* Scaling signals: Choose metrics that represent real capacity pressure, not just whichever metric is easiest to collect.

* State management: Keep application state in suitable shared services rather than relying on local instance storage.

* Observability: Monitor CPU, target health, request latency, errors, and Auto Scaling activities.

* Cost: Remember that instances, load balancers, EBS volumes, NAT Gateways, and data transfer may all incur charges.

For Pulumi-managed infrastructure, preview changes before applying them, protect critical resources where appropriate, and understand which resources might be replaced when configuration changes.

### 11\. Cleanup

After finishing the lab, destroy the resources that Pulumi created:

```bash
pulumi destroy
```

Review the proposed deletions and confirm them.

Verify that the load balancer, target group, Auto Scaling group, scaling policy, launch template, and security groups created by the lab have been removed. If you used an existing VPC and subnets, those should remain intact.

Also check for any resources you created outside Pulumi, such as extra EBS volumes, snapshots, or other test resources.

### 12\. Knowledge check

### Check your understanding

0 of 5

1. Which component defines the AMI and instance configuration used for new EC2 instances?

Auto Scaling policy

Launch template

Target group

Application Load Balancer

2. An ASG has minimum 2, desired 3, and maximum 6. What happens when desired capacity is increased to 5?

The group must remain at 3

The group attempts to maintain 5 instances

The group immediately terminates two instances

The maximum becomes 5

3. An ALB target is unhealthy, but ELB health checks are not enabled for the ASG. What should you expect?

The ASG must replace it immediately

The ALB stops routing normal traffic to it, but ASG replacement is not guaranteed by that health result alone

The ASG automatically increases maximum capacity

The launch template is deleted

4. Which scaling policy is a sensible starting point for maintaining average CPU around a target value?

Target tracking

Scheduled scaling only

A launch template

A target-group listener

5. Why deploy the ASG across multiple Availability Zones?

It eliminates all failures

It guarantees zero downtime

It reduces dependence on a single Availability Zone

It removes the need for health checks

Check answers

### Module summary

You have now covered the main building blocks of EC2 Auto Scaling:

* Launch templates define how instances are created.

* Auto Scaling groups maintain desired capacity within configured limits.

* Scaling policies adjust capacity in response to metrics or schedules.

* Health checks help detect failures and trigger replacement when configured appropriately.

* ALB integration distributes requests and connects target health to capacity management.

* Multi-AZ deployments improve resilience.

* Pulumi makes the infrastructure reproducible and easier to review.

The next module in the course is Module 6 — AWS Lambda: Serverless Compute and Event-Driven Execution.
