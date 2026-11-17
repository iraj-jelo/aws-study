### Module 4 — Elastic Load Balancing (ELB)

Phase 4 — Compute · AWS course · Hands-on with Pulumi and Python

Elastic Load Balancing distributes incoming application traffic across multiple targets, such as EC2 instances, containers, and IP addresses. It helps applications remain available when individual targets fail and provides a central place to manage traffic routing and TLS termination.

In this module, you'll build on your VPC, subnet, routing, and security group knowledge to deploy a public Application Load Balancer (ALB) with HTTPS and two EC2 application targets in different Availability Zones.

### Learning objectives

By the end of this module, you'll be able to:

* Distinguish ALB, NLB, and GWLB and select the right load balancer for a workload.

* Design public and internal load balancers.

* Configure listeners, target groups, routing rules, and health checks.

* Understand TLS termination, ACM certificates, and security group relationships.

* Explain cross-zone load balancing, Availability Zone resilience, and connection draining.

* Provision and troubleshoot a load-balanced application using Pulumi with Python.

### 1\. Why load balancing matters

Suppose you deploy a FastAPI application on one EC2 instance. All incoming requests go to that instance. If it fails, becomes overloaded, or needs maintenance, your application may become unavailable.

A load balancer provides a stable entry point and distributes requests across healthy application instances.

Clients

HTTPS requests

Application Load Balancer

TLS termination · HTTP routing · Health checks

EC2 target A

Availability Zone A

Healthy

EC2 target B

Availability Zone B

Healthy

Conceptual architecture. The ALB uses target health to decide where it can route requests; actual traffic distribution depends on its routing behavior and configuration.

The load balancer doesn't make your application stateless or replicate its data. Your application must still handle shared state, session storage, database availability, and other dependencies correctly.

### What problems does ELB solve?

* Availability: Route traffic to healthy targets when other targets become unhealthy.

* Distribution: Spread incoming requests across multiple application targets.

* Scalability: Add or remove targets as application capacity changes.

* TLS management: Terminate HTTPS at the load balancer when appropriate.

* Routing: Send requests to different target groups based on hostnames, paths, or other supported rules.

A load balancer is not an automatic replacement for Auto Scaling. ELB distributes traffic across registered targets; EC2 Auto Scaling manages the number and lifecycle of instances.

### 2\. The three Elastic Load Balancing types

AWS provides three primary load balancer types. Choose according to the traffic you need to handle rather than assuming one type is universally best.

![Introducing Application Load Balancer – Unlocking and Optimizing Architectures | AWS DevOps & Developer Productivity Blog](https://images.openai.com/static-rsc-4/K-W346HUIPPGbbKYtW5CHREr8HxbXhzDJWXhUZuZC1rGbviBVFYM5THYoLlAQ5HrcFXj9Ax8ZP4EquSahxMJj7tM1i4qjp5P0GW30MpzKjovOfg4zFqQCS43Ad3fP5ECAmVgZ6sHW7Rj0U2_o4_DINa1nVS1gZkBHis8BP2K_NGydiMO-R90aOSspu7d2QEU?purpose=fullsize)

### Application Load Balancer (ALB)

Best fit for this lab

Operates at the application layer (Layer 7). Supports HTTP/HTTPS routing, host-based and path-based rules, and integration with web applications and container services.

Example: Route `/api/*` to a FastAPI service and `/admin/*` to a separate service.

![로드밸런서(Load Balancer)란? : AWS와 로드 밸런싱(Load Balancing) 개념 정리](https://images.openai.com/static-rsc-4/k5mtTbHe9PYLngcTyq3ExQyUhF6pKcIWjLK_AAwhRkupm24JX073TMdD5VJtVLfX9RC3iZvNx-W8ATUFfb4itQ66nqS_w_7R2TjxGTKJ58-C4IbrxOzrTQ4l5_Fb9Ryvdq6a8w5ysL9r64tiDaFm3y5_KccBfyvCn_9kIJzyOjk3qfYMAZksKo9pIEkZvyME?purpose=fullsize)

### Network Load Balancer (NLB)

Operates primarily at Layer 4, handling TCP, UDP, and supported TLS traffic. It is designed for high-performance, low-latency network traffic and supports static IP addresses per enabled Availability Zone.

Example: Expose a TCP service or a workload that requires NLB-specific networking behavior.

![Guida introduttiva ai sistemi Gateway Load Balancer utilizzando AWS CLI - Elastic Load Balancing](https://images.openai.com/static-rsc-4/mjnfmcMKgOuA9jJOH3RinHr5LZfXh50Ld_2hptUAmjJZ_pJiR7QiZkrq60fJUAA41mt93l-Roe55gsB7DZHoubfZb6pdHfBZIpBYluSBFD47GqX7qGPL4F9dXc3tNaLUmlguo9-cUCkIFtNlbCAFIGHsWEX6szseGKpr2AkXWgYTrlyAvkdxmurFRC-TNNr0?purpose=fullsize)

### Gateway Load Balancer (GWLB)

Distributes traffic to virtual network appliances using GENEVE encapsulation. It is designed for transparent deployment and scaling of appliances such as firewalls and intrusion detection systems.

Example: Send network traffic through a fleet of security inspection appliances.

| Capability             | ALB                  | NLB                          | GWLB                                             |
| ---------------------- | -------------------- | ---------------------------- | ------------------------------------------------ |
| Primary layer          | Layer 7              | Layer 4                      | Layer 3 traffic steering with appliance delivery |
| HTTP path/host routing | Yes                  | No                           | No                                               |
| Typical workload       | Web apps and APIs    | TCP/UDP and network services | Network security appliances                      |
| Target types           | Instance, IP, Lambda | Instance, IP, ALB            | Instance, IP, appliance targets                  |
| HTTPS/TLS support      | TLS termination      | TLS listener support         | Not a web TLS termination service                |

For most HTTP APIs and websites, start by evaluating ALB. For workloads requiring network-level traffic handling or static frontend IPs, evaluate NLB. For scaling transparent network inspection, evaluate GWLB.

### 3\. How an ALB processes a request

An ALB uses several related resources. Understanding each one makes configuration and troubleshooting much easier.

1\. Listener

A listener checks for incoming connections on a configured protocol and port, such as HTTPS on port 443. It evaluates its default action and any configured listener rules.

2\. Listener rules

Rules can match conditions such as hostname or URL path. A matching rule forwards the request to a target group, redirects it, or returns a fixed response.

3\. Target group

A target group identifies the registered destinations and defines settings such as the destination port, protocol, health checks, and deregistration delay.

4\. Health checks

The load balancer periodically checks target health. Healthy targets can receive normal traffic; unhealthy targets are generally excluded while healthy alternatives exist.

### Example: listener rules

Imagine an application with two services:

| Priority | Condition                 | Action                        |
| -------- | ------------------------- | ----------------------------- |
| 10       | Path is /api/*            | Forward to API target group   |
| 20       | Host is admin.example.com | Forward to admin target group |
| Default  | No other rule matches     | Return a fixed 404 response   |

Lower-numbered priorities are evaluated first. The default action handles requests that don't match a higher-priority rule.

For this module's lab, we'll use a simpler configuration: an HTTPS listener forwarding all requests to one target group containing two EC2 instances.

### 4\. Public versus internal load balancers

An internet-facing load balancer is reachable through publicly routable addresses, subject to its network configuration and security controls. An internal load balancer is intended for private access within a network environment.

![Building an AWS Application Load Balancer with EC2 and NGINX | D Manjunath posted on the topic | LinkedIn](https://images.openai.com/static-rsc-4/_fb73OOVdJMfX2b0OUCsYGPBqAWqHYB2N2wTWFqgbPwP_fXMSmbZ0AucJnlNTi0ONGECFn0nFlouRqDTLTo56umVy8TCkEwhfsUMYLzpWQX6uz6RkJnvtKr_jvTzfB117ogaudP5NNsWKkv-wyrZ6dxCbNRAnrh3dYc6uBWIYSzde6i9WOC_jKIiISuiSlXV?purpose=fullsize)

Internet-facing ALB

* Receives traffic from the internet.

* Deployed into public subnets.

* Commonly forwards to private application instances.

![Raghuraman: AWS VPC, Internal Load Balancer and Scaling Databases](https://images.openai.com/static-rsc-4/tdw143tuxD5VfELui_MVEQd8JQtVy4-soIdb73PjxaIOMrI9vKzdxoYsR8eSxSYH8R-tfZBHRNQn1d4m9Gx7_im-_kixDZe2GE9LPFb-m5kyo2CGjLy3CTLaoHGiMsL3aUyT7CMvXGdUrPBsxAPBoJs3rfvMS7FoMgAXORPbeO72B2Db8Unu9E2jzlurHWCn?purpose=fullsize)

Internal ALB

* Intended for private clients.

* Deployed into private subnets.

* Commonly serves internal APIs and services.

A critical distinction: the load balancer's scheme does not automatically determine whether its targets are public or private. An internet-facing ALB can forward to EC2 instances in private subnets, which is a common production architecture.

For a production design, place application targets in private subnets where practical. The public ALB accepts external requests; the application instances should accept application traffic only from the ALB's security group.

### 5\. Health checks and target registration

A target can be registered but unhealthy. Registration alone does not prove the application is ready to serve traffic.

For an HTTP application, a target group's health check might use:

* Protocol: HTTP

* Port: traffic port

* Path: `/health`

* Success codes: `200`

* Interval: 30 seconds

* Timeout: 5 seconds

The health endpoint should respond quickly and report whether the application can serve requests. Avoid making it depend on every optional downstream service unless that is intentional.

### Health-check troubleshooting

| Symptom                      | Common causes                                                                           |
| ---------------------------- | --------------------------------------------------------------------------------------- |
| Target.Timeout               | Network rules block traffic, application isn't listening, or it responds too slowly     |
| Target.ResponseCodeMismatch  | Health endpoint returns an unexpected status                                            |
| Target.FailedHealthChecks    | Application startup failure, wrong port, wrong protocol, or connection errors           |
| No healthy targets           | All targets fail checks, are not registered, or aren't reachable                        |
| Intermittent health failures | Resource exhaustion, slow startup, application instability, or an overly strict timeout |

The ALB security group must permit outbound traffic to the application port, and the EC2 security group must permit inbound traffic on that port from the ALB security group.

### Health checks versus connection draining

Health checks answer, "Can this target serve traffic?"

Deregistration delay (connection draining) addresses a different question: "What happens to in-flight requests when this target is being removed?"

When a target is deregistered, the load balancer allows existing requests or connections time to complete within the configured delay, subject to protocol behavior and the configured timeout. Long-running requests may require an appropriate delay and application-level graceful shutdown.

### 6\. TLS termination and HTTPS

TLS encrypts traffic between clients and the endpoint they connect to. With ALB TLS termination, the client establishes HTTPS to the load balancer, which decrypts the request before forwarding it to the target group.

Client

HTTPS · TCP 443

ALB HTTPS listener

ACM certificate · TLS termination

Target group

HTTP · TCP 80 · private application traffic

This design encrypts the client-to-ALB connection, but the ALB-to-target connection is HTTP and is not encrypted. If your security requirements call for end-to-end encryption, configure HTTPS from the ALB to the targets as well and verify certificate and trust behavior.

### ACM certificates

AWS Certificate Manager (ACM) can provide and manage certificates for an ALB. For a typical public HTTPS endpoint:

* Register or use a domain you control.

* Request a public certificate in ACM in the same AWS Region as the ALB.

* Complete domain validation, commonly through DNS.

* Attach the certificate to the ALB's HTTPS listener.

* Create a DNS record that points your hostname to the ALB.

A certificate doesn't make a domain resolve to the ALB by itself. DNS configuration is a separate step.

For the lab, you'll need a validated ACM certificate ARN and a hostname covered by that certificate. If you don't have a domain yet, you can complete the infrastructure portion first and add HTTPS after certificate validation.

### 7\. Security groups: the most important relationship

Use separate security groups for the ALB and the EC2 targets.

| Resource           | Inbound                                                       | Outbound                                      |
| ------------------ | ------------------------------------------------------------- | --------------------------------------------- |
| ALB security group | TCP 443 from intended clients; optionally TCP 80 for redirect | TCP 80 to target security group               |
| EC2 security group | TCP 80 from ALB security group only                           | Required application dependencies and updates |

Security groups are stateful, so response traffic for allowed connections is permitted automatically.

Avoid opening the EC2 application's port to `0.0.0.0/0` simply because the instance has a public IP. The application should be reachable through the ALB, not directly from arbitrary clients.

Also remember that a security group is only one part of the connectivity path. Subnet route tables, network ACLs, target registration, and application listening addresses all matter.

### 8\. Hands-on lab — Deploy an HTTPS ALB with two EC2 targets

### Lab architecture

You'll provision the following resources with Pulumi and Python:

* One internet-facing ALB.

* Two public ALB subnets in different Availability Zones.

* One ALB security group.

* One target security group.

* Two EC2 instances running a small HTTP application.

* One target group with HTTP health checks.

* One HTTPS listener using an ACM certificate.

For a learning lab, the instances will use public subnets to simplify operating-system package installation. Their security group will still restrict inbound application traffic to the ALB. For production, prefer private target subnets with suitable outbound connectivity.

Estimated duration: 60–90 minutes

Cost warning: ALB and EC2 resources can incur charges even during idle periods. Delete the lab when finished.

Prerequisites: AWS CLI credentials, Pulumi CLI, Python, an existing VPC, two public subnets in different AZs, and a validated ACM certificate.

### Step 1 — Prepare your configuration

Create a project directory:

```bash
mkdir aws-elb-lab
cd aws-elb-lab

pulumi new aws-python
```

Install dependencies if your generated project doesn't already include them:

```bash
pip install pulumi pulumi-aws
```

Set the AWS Region and required configuration. Use your actual resource IDs:

```bash
pulumi config set aws:region us-east-1

pulumi config set vpcId vpc-0123456789abcdef0
pulumi config set --path 'publicSubnetIds[0]' subnet-0123456789abcdef0
pulumi config set --path 'publicSubnetIds[1]' subnet-0abcdef0123456789

pulumi config set certificateArn arn:aws:acm:us-east-1:123456789012:certificate/YOUR-CERTIFICATE-ID
```

The two subnets must belong to the same VPC, be in different Availability Zones, and have routes that permit internet-facing ALB connectivity. The certificate ARN must identify a validated certificate in the selected Region.

The sample intentionally doesn't create or modify your VPC. It builds on the networking foundation from the earlier modules.

### Step 2 — Implement the infrastructure

Replace the generated `__main__.py` with the following code. It creates the security groups, ALB, target group, EC2 instances, health checks, and HTTPS listener.

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
public_subnet_ids = config.require_object("publicSubnetIds")
certificate_arn = config.require("certificateArn")

if len(public_subnet_ids) != 2:
    raise ValueError("Provide exactly two public subnet IDs.")

# Find a current Amazon Linux 2023 x86_64 AMI.
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        aws.ec2.GetAmiFilterArgs(
            name="name",
            values=["al2023-ami-2023.*-x86_64"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="architecture",
            values=["x86_64"],
        ),
        aws.ec2.GetAmiFilterArgs(
            name="virtualization-type",
            values=["hvm"],
        ),
    ],
)

# Public entry point: HTTPS only.
alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    description="Allow HTTPS from the internet",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTPS clients",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            security_groups=[],
            cidr_blocks=["0.0.0.0/0"],
            description="Allow HTTP egress to targets",
        ),
    ],
    tags={"Name": "elb-lab-alb-sg"},
)

# Target ingress is restricted to the ALB security group.
# Keep the outbound rule broad for this simple lab;
# tighten it for production workloads.
target_sg = aws.ec2.SecurityGroup(
    "target-sg",
    description="Allow application traffic from ALB",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            security_groups=[alb_sg.id],
            description="HTTP from ALB only",
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
    tags={"Name": "elb-lab-target-sg"},
)

alb = aws.lb.LoadBalancer(
    "app-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=public_subnet_ids,
    tags={"Name": "elb-lab-alb"},
)

target_group = aws.lb.TargetGroup(
    "app-tg",
    vpc_id=vpc_id,
    port=80,
    protocol="HTTP",
    target_type="instance",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        protocol="HTTP",
        path="/",
        matcher="200",
        interval=30,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
    deregistration_delay=30,
    tags={"Name": "elb-lab-tg"},
)

# Each instance reports its own identity so you can
# observe traffic reaching different targets.
user_data = """#!/bin/bash
set -eux
dnf install -y python3
mkdir -p /opt/elblab
cat > /opt/elblab/index.html <<'EOF'
<html>
  <body>
    <h1>ELB Lab</h1>
    <p>Served by an EC2 target.</p>
    <p>Hostname: PLACEHOLDER</p>
  </body>
</html>
EOF
sed -i "s/PLACEHOLDER/$(hostname)/" /opt/elblab/index.html
cat > /etc/systemd/system/elblab.service <<'EOF'
[Unit]
Description=ELB lab HTTP server
After=network.target

[Service]
WorkingDirectory=/opt/elblab
ExecStart=/usr/bin/python3 -m http.server 80 --bind 0.0.0.0
Restart=always

[Install]
WantedBy=multi-user.target
EOF
systemctl daemon-reload
systemctl enable --now elblab
"""

instances = []
attachments = []

for index, subnet_id in enumerate(public_subnet_ids):
    instance = aws.ec2.Instance(
        f"app-{index + 1}",
        ami=ami.id,
        instance_type="t3.micro",
        subnet_id=subnet_id,
        vpc_security_group_ids=[target_sg.id],
        associate_public_ip_address=True,
        user_data=user_data,
        user_data_replace_on_change=True,
        metadata_options=aws.ec2.InstanceMetadataOptionsArgs(
            http_tokens="required",
            http_endpoint="enabled",
        ),
        tags={
            "Name": f"elb-lab-app-{index + 1}",
            "Purpose": "elb-learning-lab",
        },
    )
    instances.append(instance)

    attachment = aws.lb.TargetGroupAttachment(
        f"app-{index + 1}-attachment",
        target_group_arn=target_group.arn,
        target_id=instance.id,
        port=80,
    )
    attachments.append(attachment)

https_listener = aws.lb.Listener(
    "https-listener",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn=certificate_arn,
    ssl_policy="ELBSecurityPolicy-TLS13-1-2-2021-06",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        ),
    ],
)

pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("alb_url", pulumi.Output.concat("https://", alb.dns_name))
pulumi.export("target_instance_ids", pulumi.Output.all(
    *[instance.id for instance in instances]
))
pulumi.export("target_group_arn", target_group.arn)
```

Important implementation notes

* The code assumes both supplied subnet IDs belong to different AZs. Verify that before deployment.

* The EC2 user-data script installs Python and starts a basic HTTP server. Initial health checks may fail until installation finishes.

* The ALB's HTTPS listener uses your ACM certificate, but the generated ALB DNS name will not necessarily match your certificate's hostname. Use the DNS name of a hostname covered by the certificate for browser testing.

* The target instances are assigned public IP addresses for lab convenience, but their security group doesn't allow direct inbound HTTP from the internet. The user-data installation does require working outbound connectivity.

* The example uses a simple HTTP server for learning. It is not a production application server or a hardened deployment.

One additional detail: the ALB security group's outbound rule above is intentionally written with broad CIDR egress for simplicity. For stricter production security, use a rule that references the target security group directly, with the appropriate Pulumi provider arguments for that security-group reference.

### Step 3 — Preview and deploy

Always inspect the proposed infrastructure changes before creating resources.

```bash
pulumi preview
pulumi up
```

Review the resource plan and approve it only after verifying that the VPC, subnet IDs, certificate, and security groups are correct.

When the deployment finishes, retrieve the ALB DNS name:

```bash
pulumi stack output alb_dns_name
pulumi stack output alb_url
```

Check that the instances are running and the ALB has finished provisioning. The EC2 user-data script may need a few minutes to finish.

### Step 4 — Verify the targets

Open the AWS Console and navigate to EC2 → Target Groups → your target group → Targets.

Both targets should eventually show as healthy.

You can also inspect the target health with AWS CLI:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$(pulumi stack output target_group_arn)"
```

Check the health state and reason codes if either target remains unhealthy.

### Step 5 — Test HTTPS and traffic distribution

Use the hostname covered by your ACM certificate. If you've configured a DNS record for `app.example.com`, for example:

```bash
curl -i https://app.example.com/
```

Repeat the request to observe the hostname returned by different instances:

```bash
for i in $(seq 1 10); do
  curl -s https://app.example.com/ | grep Hostname
done
```

If your domain and certificate aren't configured yet, you can test the ALB's HTTP health and target registration first, but the HTTPS listener still requires a valid certificate.

Don't assume every request must alternate between the two instances. Load-balancer routing, connection reuse, and client behavior can affect which target serves each request.

### 9\. Troubleshooting exercises

Try diagnosing these scenarios before reading the suggested fixes.

Scenario 1 — Both targets are unhealthy

The ALB returns HTTP 503.

Reveal solution

Scenario 2 — The ALB times out

The browser reports a timeout or cannot connect.

Reveal solution

Scenario 3 — HTTPS shows a certificate warning

The certificate hostname doesn't match the URL.

Reveal solution

Scenario 4 — One instance never becomes healthy

One target is healthy while the other remains unhealthy.

Reveal solution

### 10\. Clean up your lab

After completing the exercises, destroy the resources created by this Pulumi stack:

```bash
pulumi destroy
```

Review the deletion plan and approve it. The existing VPC, subnets, and ACM certificate were supplied as inputs, so they aren't created by this program and shouldn't be deleted by it.

Check the AWS Console afterward to confirm the ALB, EC2 instances, target group, and associated security groups are gone.

### Knowledge check

1. Which load balancer is best suited to routing HTTP requests by URL path?

NLB

ALB

GWLB

2. Which security group rule is appropriate for the EC2 targets?

Allow HTTP from any IPv4 address

Allow HTTP only from the ALB security group

Allow all inbound traffic from the VPC

3. What does an ALB health check determine?

Whether the EC2 instance has a public IP

Whether the target responds according to the health-check configuration

Whether the target has enough CPU capacity for every possible workload

4. What is required to use an ACM certificate on an HTTPS listener?

A certificate valid for the requested hostname and available in the ALB's Region

An EC2 key pair

A public IP address attached to every target

Check answers

### Module 4 completion checklist

Before moving on, make sure you can:

* Explain the differences between ALB, NLB, and GWLB.

* Explain listeners, rules, target groups, and health checks.

* Describe the security group relationships between the ALB and EC2 targets.

* Explain ACM certificate validation and TLS termination.

* Deploy two targets in separate AZs with Pulumi.

* Diagnose unhealthy targets and HTTP 503 responses.

* Destroy the lab resources safely.

Next up: Module 5 — EC2 Auto Scaling, where you'll use launch templates and Auto Scaling groups to manage application capacity automatically and integrate scaling with the load balancer.
