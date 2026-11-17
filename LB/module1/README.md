Worked for 48s

### Module 1 — Load Balancing Fundamentals and AWS Architecture

AWS Load Balancing Course · Module 1 of 8

In this module, you'll learn how load balancing works, how AWS Elastic Load Balancing distributes traffic, and how to prepare a practical AWS environment using AWS CLI, Pulumi with Python, Docker, and Bash.

We'll begin by deploying a simple HTTP application on two EC2 instances in different Availability Zones. Before introducing a load balancer, you'll connect to each instance directly, observe how traffic reaches the applications, and explore what happens when one instance becomes unhealthy.

### Learning objectives

By the end of this module, you'll understand:

* Why load balancing matters for availability, scalability, and fault tolerance.

* The differences between Layer 4 and Layer 7 load balancing.

* How AWS Application Load Balancer (ALB), Network Load Balancer (NLB), Gateway Load Balancer (GWLB), and Classic Load Balancer differ.

* The roles of listeners, rules, target groups, targets, and health checks.

* How Availability Zones and cross-zone load balancing affect traffic distribution.

* When to use public versus internal load balancers.

* How load balancers differ from reverse proxies, API gateways, and DNS-based routing.

* How to prepare an AWS environment and deploy a small application across two Availability Zones.

### 1\. What is load balancing?

Imagine that you run a web application on a single server.

Multiple clients

Browser · Mobile app · API client

Single application server

All requests depend on one machine

If the server fails, the application becomes unavailable.

This design is simple, but it creates a single point of failure. As traffic grows, the server may also run out of CPU, memory, network capacity, or available application workers.

A load balancer provides a stable entry point and distributes incoming requests or connections across multiple backend targets.

Clients

Load balancer

Routes traffic to eligible targets

Server A

Healthy

Server B

Healthy

The load balancer can send traffic to both servers, avoid targets that fail health checks, and provide a common endpoint even as backend instances change.

### 1.1 The main benefits

* Availability: traffic can continue reaching healthy targets when another target fails, provided sufficient healthy capacity remains.

* Scalability: you can add or remove backend instances as demand changes.

* Fault tolerance: distributing targets across independent Availability Zones reduces dependence on a single failure domain.

* Traffic management: requests can be routed using hostnames, URL paths, protocols, ports, or other supported conditions.

* Operational flexibility: backends can be replaced or updated without requiring clients to use a new application endpoint.

A load balancer does not automatically make an application highly available. If every target depends on one database, one Availability Zone, or one failing downstream service, that dependency can still cause an outage.

### 1.2 Load balancing versus scaling

These are related but different concepts.

| Concept            | Responsibility                                                |
| ------------------ | ------------------------------------------------------------- |
| Load balancing     | Distributes traffic among eligible targets                    |
| Horizontal scaling | Adds or removes instances or application replicas             |
| Vertical scaling   | Increases or decreases the resources of an individual machine |
| Health checking    | Determines whether targets satisfy configured health criteria |
| Auto Scaling       | Adjusts capacity according to policies and desired state      |

For example, an ALB can distribute requests across two EC2 instances. An EC2 Auto Scaling group can launch a third instance when demand increases. Together, they support both traffic distribution and dynamic capacity management.

### 2\. Layer 4 versus Layer 7 load balancing

The OSI model helps explain the distinction.

Layer 4

Transport

Network Load Balancer (NLB)

Distributes connections using transport-level information such as IP addresses, ports, and protocols. It does not route based on URL paths or HTTP headers.

Examples: TCP applications, UDP services, TLS traffic.

Layer 7

Application

Application Load Balancer (ALB)

Understands HTTP and HTTPS requests, allowing routing decisions based on hostnames, URL paths, HTTP headers, and other application-level information.

Examples: `/api/*` to an API service and `/images/*` to an image service.

Consider these requests:

```text
https://shop.example.com/products/123
https://shop.example.com/api/orders
```

An ALB can route `/products/*` to a frontend service and `/api/*` to a backend API. An NLB can distribute TCP connections to a service, but it cannot make that path-based decision.

| Requirement                                          | Typical choice                                             |
| ---------------------------------------------------- | ---------------------------------------------------------- |
| Route HTTP requests by hostname or path              | ALB                                                        |
| Route TCP or UDP traffic                             | NLB                                                        |
| Preserve a stable zonal IP address                   | NLB                                                        |
| Inspect and distribute traffic to network appliances | GWLB                                                       |
| Support an existing legacy ELB deployment            | Evaluate Classic Load Balancer; generally prefer migration |

AWS recommends ALB for HTTP application routing, NLB for transport-level traffic, and GWLB for virtual network appliances. Classic Load Balancer is the previous generation. Amazon Web Services +2

### 3\. AWS Elastic Load Balancing architecture

Elastic Load Balancing (ELB) is an AWS-managed service. AWS operates the load-balancing infrastructure, handles its capacity scaling, and integrates it with monitoring and other AWS services.

You configure how traffic enters the service and where it should go.

### 3.1 The main components

Load balancer

The stable service endpoint that accepts incoming connections and distributes traffic.

Listener

Accepts connections on a configured protocol and port, such as HTTP on port 80 or HTTPS on port 443.

Listener rules

For supported load balancers, evaluate conditions and determine the action, such as forwarding, redirecting, or returning a fixed response.

Target group

Defines the backend targets, protocol, port, health checks, and associated routing configuration.

Targets

The actual destinations receiving traffic, such as EC2 instances, private IP addresses, containers, or supported Lambda targets, depending on load-balancer type.

For example, an ALB might have:

* Listener: HTTPS on port `443`.

* Rule: requests with path `/api/*` match a condition.

* Action: forward matching requests to an API target group.

* Target group: EC2 instances listening on port `8080`.

* Health check: send HTTP requests to `/health`.

A target must be registered and eligible to receive traffic. Health checks help the load balancer determine whether registered targets are healthy. Elastic Load Balancing +1

### 3.2 Health checks

A health check is a probe sent to a target to determine whether it satisfies the configured health criteria.

For an HTTP target, you might configure:

```text
Protocol: HTTP
Port: traffic port
Path: /health
Expected status code: 200
```

The application could return:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{"status":"healthy"}
```

If the target starts returning failures or stops responding, the load balancer can mark it unhealthy and stop routing traffic to it under normal health-based routing behavior.

However, a health check is only as meaningful as the endpoint behind it. A `/health` endpoint that always returns `200 OK` may report a healthy process even when a critical dependency is broken.

In later modules, we'll configure health checks and deliberately make targets fail so you can observe this behavior.

### 4\. The four AWS load balancer types

![Zero-Code Authentication: Unleashing AWS Application Load Balancer's Built-in capabilities for simplifying user login - DEV Community](https://images.openai.com/static-rsc-4/yH2hL3XmmHelz8rIeVvGULGo6RwZEUduyeel62xKt3Kq-JCwd7MzN5SKp-qGuUt0j-a5wLGcSlXG-NZJmrVoNKmdBg4zkykARw7Wiss6wtYz0mSES4sfBvXyyny7IB_ebZqLkxecPTeJrWM4Vh3N3stI0fhZBQ7B_kZrszb9Xh5gdmr57FAwyTxcyldm93Qh?purpose=fullsize)

Application Load Balancer (ALB)

Layer 7

Designed for HTTP, HTTPS, and supported application protocols. Provides content-based routing, redirects, fixed responses, and integration with containerized applications.

![로드밸런서(Load Balancer)란? : AWS와 로드 밸런싱(Load Balancing) 개념 정리](https://images.openai.com/static-rsc-4/k5mtTbHe9PYLngcTyq3ExQyUhF6pKcIWjLK_AAwhRkupm24JX073TMdD5VJtVLfX9RC3iZvNx-W8ATUFfb4itQ66nqS_w_7R2TjxGTKJ58-C4IbrxOzrTQ4l5_Fb9Ryvdq6a8w5ysL9r64tiDaFm3y5_KccBfyvCn_9kIJzyOjk3qfYMAZksKo9pIEkZvyME?purpose=fullsize)

Network Load Balancer (NLB)

Layer 4

Designed for TCP, UDP, and TLS traffic. Useful for high connection volumes, low-latency transport-level routing, and static IP requirements.

![Getting started with Gateway Load Balancers using the AWS CLI - Elastic Load Balancing](https://images.openai.com/static-rsc-4/mjnfmcMKgOuA9jJOH3RinHr5LZfXh50Ld_2hptUAmjJZ_pJiR7QiZkrq60fJUAA41mt93l-Roe55gsB7DZHoubfZb6pdHfBZIpBYluSBFD47GqX7qGPL4F9dXc3tNaLUmlguo9-cUCkIFtNlbCAFIGHsWEX6szseGKpr2AkXWgYTrlyAvkdxmurFRC-TNNr0?purpose=fullsize)

Gateway Load Balancer (GWLB)

Network appliances

Deploys and scales virtual appliances such as firewalls and deep-packet-inspection systems using transparent traffic steering and the GENEVE protocol.

![Introduction To AWS ELB - Part Two](https://images.openai.com/static-rsc-4/D-CrOz6WY9_dX9noHzLv85qE_Ii-EhG_-rlIMJhhBl-sDiFx75BwxPtowEscNpmQzOf5EjqjbkCdsA8LioyC3fQiQNMsZkfcwjIwt2Kc-fGPxmhse2E56F5PQSL2-Y25EApZqhb90plFGMBWnQT1IhcJbwzl7GhJweu-YnqDs1E6pX6dMCiHXViukiYvWhaQ?purpose=fullsize)

Classic Load Balancer (CLB)

Previous generation

Supports legacy Layer 4 and Layer 7 use cases. For new designs, choose a current-generation load balancer unless a specific compatibility requirement dictates otherwise.

These products solve different problems rather than representing four interchangeable versions of the same feature. Amazon Web Services +2

### 5\. Availability Zones and cross-zone load balancing

An AWS Region contains multiple Availability Zones (AZs). Each AZ consists of one or more data centers with independent infrastructure and failure domains.

A resilient application should avoid depending on a single AZ.

AWS Region

One regional application deployment

### Availability Zone A

EC2 instance A

One application target

### Availability Zone B

EC2 instance B

Another application target

A multi-AZ deployment reduces dependence on one failure domain. The application must still have enough healthy capacity to handle a failure.

### 5.1 What is cross-zone load balancing?

Cross-zone load balancing determines whether a load balancer node can distribute traffic across targets in other enabled AZs.

Suppose AZ A contains one target and AZ B contains three targets.

* With cross-zone distribution enabled, a load balancer node can distribute its traffic across eligible targets in both AZs.

* With cross-zone distribution disabled, a node generally distributes traffic only to targets in its own AZ.

The precise default and configuration behavior depends on the load balancer type and its attributes. ALB distributes across registered targets in enabled AZs; NLB has cross-zone configuration considerations, including per-load-balancer or per-target-group settings. Elastic Load Balancing +1

Important: Multi-AZ placement and cross-zone load balancing solve different problems. Multi-AZ placement provides geographic redundancy within a Region; cross-zone distribution affects how traffic is distributed among targets. Neither replaces health checks, sufficient capacity, or resilient application dependencies.

### 6\. Public versus internal load balancers

AWS load balancers have a scheme that determines whether their frontend is internet-facing or internal.

Internet-facing load balancer

* Has publicly reachable frontend addresses.

* Used for websites and public APIs.

* Typically placed in public subnets with appropriate routes.

* Can forward requests to private backend targets.

Internal load balancer

* Uses private frontend addresses.

* Used for internal APIs, application tiers, and private services.

* Requires network connectivity to the VPC or connected networks.

* Is not directly internet-facing.

A common three-tier architecture looks like this:

```text
Internet
   |
   v
Public ALB
   |
   v
Private application targets
   |
   v
Private database
```

The ALB can be public while the application instances have no public IP addresses. The instance security group should allow application traffic only from the ALB's security group, rather than from the entire internet.

An internal load balancer is not automatically accessible to every resource inside a VPC: routing, security groups, network ACLs, and other access controls still apply. Elastic Load Balancing +1

### 7\. Load balancing versus related technologies

| Technology    | Primary responsibility                                               | Example                                                                     |
| ------------- | -------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Load balancer | Distributes traffic across eligible targets                          | An ALB routes requests to multiple EC2 instances                            |
| Reverse proxy | Receives requests on behalf of backend services                      | NGINX forwards HTTP requests to application servers                         |
| API gateway   | Manages API access and API-specific policies                         | Amazon API Gateway handles authentication, throttling, and API integrations |
| DNS routing   | Resolves names to destinations according to DNS records and policies | Route 53 provides weighted or failover DNS responses                        |
| CDN           | Caches and serves content from edge locations                        | CloudFront caches static website assets                                     |

These technologies can complement one another.

For example:

```text
Client
  |
  v
Route 53
  |
  v
CloudFront
  |
  v
Application Load Balancer
  |
  +----> Frontend targets
  |
  +----> API targets
```

Route 53 determines DNS answers, CloudFront provides edge delivery, and the ALB routes application requests. Each operates at a different point in the request path.

DNS-based routing also differs from per-request load balancing: DNS responses are cached, and clients may continue using a previously resolved address until their cached answer expires.

Amazon API Gateway is useful when API management features such as authorization, quotas, request transformations, and API-specific throttling are important. An ALB is generally a better fit when you primarily need HTTP routing to application targets. The appropriate choice depends on your requirements.

### Lab 1 — Prepare your AWS development environment

We'll use AWS CLI for inspection, Pulumi Python for infrastructure, Docker for container concepts, and Bash for commands.

### 8\. Prerequisites and installation

You can run these commands in WSL2 Ubuntu or a Linux terminal. On Windows, Git Bash is useful for many shell commands, but WSL2 is preferable when working with Linux tooling and dependencies.

### 8.1 Verify Python and Docker

```bash
python3 --version
python3 -m pip --version
docker --version
docker compose version
```

If you're using Ubuntu or WSL2 and the tools are missing:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip curl unzip git
```

Install Docker using the official Docker Engine instructions for your distribution, or use Docker Desktop with WSL integration.

### 8.2 Install AWS CLI v2

For supported x86-64 Linux systems, use the official AWS installer:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" \
  -o "awscliv2.zip"

unzip awscliv2.zip
sudo ./aws/install
```

Verify the installation:

```bash
aws --version
```

For ARM64 Linux, use the corresponding ARM64 installer. Follow the official [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html?utm_source=chatgpt.com) for other environments. AWS Command Line Interface

### 8.3 Install Pulumi CLI

On Linux:

```bash
curl -fsSL https://get.pulumi.com | sh
```

Add the Pulumi binary directory to your current shell's `PATH` if the installer requests it. Then verify:

```bash
pulumi version
```

Install Pulumi's Python AWS provider in a project virtual environment later, rather than globally. The official [Pulumi installation guide](https://www.pulumi.com/docs/install/?utm_source=chatgpt.com) covers alternative installation methods. Pulumi Docs +1

### 8.4 Configure AWS credentials

Use an AWS IAM Identity Center profile or another supported short-lived credential mechanism when possible. For a simple local learning environment, you can configure an existing AWS CLI profile:

```bash
aws configure --profile learning
```

Enter the requested credentials, default Region, and output format. Never commit credentials to source control or embed them in Pulumi code.

Activate the profile:

```bash
export AWS_PROFILE=learning
export AWS_REGION=us-east-1
```

Choose a Region in which you can create EC2 instances and use at least two Availability Zones. The commands below use `us-east-1` as an example; substitute your chosen Region.

Check access:

```bash
aws sts get-caller-identity
aws configure get region
```

If you use temporary credentials, ensure the session is valid. Your identity needs permissions for the EC2, VPC, security group, SSM parameter read, and related resources used in this lab.

### 9\. Lab 2 — Deploy two HTTP servers in different Availability Zones

Hands-on lab

Goal: Deploy two independent EC2 instances, each running a small HTTP server, using Pulumi. We'll access them individually before adding a load balancer in Module 2.

### Step 1 — Discover your VPC and subnets

First, inspect the default VPC:

```bash
aws ec2 describe-vpcs \
  --filters Name=isDefault,Values=true \
  --query 'Vpcs[].{VpcId:VpcId,Cidr:CidrBlock}' \
  --output table
```

Then list the default subnets and their Availability Zones:

```bash
aws ec2 describe-subnets \
  --filters Name=default-for-az,Values=true \
  --query 'Subnets[].[SubnetId,AvailabilityZone,AvailableIpAddressCount]' \
  --output table
```

Choose two subnets in different Availability Zones within the same VPC.

If your account doesn't have a default VPC or the required subnets, use an existing suitable VPC or create a VPC with two public subnets. For this introductory lab, the default VPC is the simplest option.

### Step 2 — Create a Pulumi project

```bash
mkdir aws-lb-module1
cd aws-lb-module1

pulumi new aws-python
```

Follow the prompts, select your project name, and set the AWS Region.

Create a virtual environment and install the required Python packages if the template hasn't already done so:

```bash
python3 -m venv .venv
source .venv/bin/activate

python -m pip install --upgrade pip
python -m pip install pulumi pulumi-aws
```

Configure the two subnet IDs you selected:

```bash
pulumi config set subnetA subnet-REPLACE_WITH_FIRST_SUBNET
pulumi config set subnetB subnet-REPLACE_WITH_SECOND_SUBNET
```

Replace both example values with actual subnet IDs. These configuration values are not secrets.

### Step 3 — Write the Pulumi program

Replace the generated `__main__.py` with the following code.

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

subnet_a_id = config.require("subnetA")
subnet_b_id = config.require("subnetB")

# Resolve both subnets so that we can verify their AZ placement.
subnet_a = aws.ec2.get_subnet(id=subnet_a_id)
subnet_b = aws.ec2.get_subnet(id=subnet_b_id)

if subnet_a.vpc_id != subnet_b.vpc_id:
    raise ValueError("Both subnets must belong to the same VPC.")

if subnet_a.availability_zone == subnet_b.availability_zone:
    raise ValueError("Choose subnets in different Availability Zones.")

# Resolve the latest Amazon Linux 2023 AMI published through SSM.
ami = aws.ssm.get_parameter(
    name="/aws/service/ami-amazon-linux-latest/"
         "al2023-ami-kernel-default-x86_64"
)

# This lab intentionally exposes HTTP for direct testing.
# Do not reuse this public ingress rule for production workloads.
web_sg = aws.ec2.SecurityGroup(
    "module1-web-sg",
    description="Module 1 HTTP learning lab",
    vpc_id=subnet_a.vpc_id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "Temporary public HTTP access",
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
    tags={"Course": "AWS-Load-Balancing", "Module": "1"},
)

def make_user_data(server_name: str) -> str:
    return f"""#!/bin/bash
set -euxo pipefail

dnf install -y python3
mkdir -p /var/www/html

cat > /var/www/html/index.html <<'HTML'
<!doctype html>
<html>
<head><title>AWS Load Balancing Lab</title></head>
<body>
  <h1>{server_name}</h1>
  <p>Module 1: direct EC2 access before load balancing.</p>
</body>
</html>
HTML

cat > /etc/systemd/system/lab-web.service <<'SERVICE'
[Unit]
Description=Module 1 HTTP server
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 -m http.server 80 --directory /var/www/html
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable --now lab-web.service
"""

server_a = aws.ec2.Instance(
    "module1-web-a",
    ami=ami.value,
    instance_type="t3.micro",
    subnet_id=subnet_a_id,
    vpc_security_group_ids=[web_sg.id],
    associate_public_ip_address=True,
    user_data=make_user_data("Server A"),
    user_data_replace_on_change=True,
    tags={
        "Name": "module1-web-a",
        "Course": "AWS-Load-Balancing",
    },
)

server_b = aws.ec2.Instance(
    "module1-web-b",
    ami=ami.value,
    instance_type="t3.micro",
    subnet_id=subnet_b_id,
    vpc_security_group_ids=[web_sg.id],
    associate_public_ip_address=True,
    user_data=make_user_data("Server B"),
    user_data_replace_on_change=True,
    tags={
        "Name": "module1-web-b",
        "Course": "AWS-Load-Balancing",
    },
)

pulumi.export("server_a_public_ip", server_a.public_ip)
pulumi.export("server_a_az", server_a.availability_zone)
pulumi.export("server_b_public_ip", server_b.public_ip)
pulumi.export("server_b_az", server_b.availability_zone)
pulumi.export("http_url_a", server_a.public_dns.apply(
    lambda dns: f"http://{dns}"
))
pulumi.export("http_url_b", server_b.public_dns.apply(
    lambda dns: f"http://{dns}"
))
```

This program creates a security group and two EC2 instances. It uses the current Amazon Linux 2023 AMI published through AWS Systems Manager Parameter Store rather than hard-coding an AMI ID.

The instances run a basic Python HTTP server on port 80 and serve different HTML pages. The startup script is executed through EC2 user data; no SSH key pair is required.

Security note: The lab allows public HTTP access to both instances because we're deliberately testing them directly. Do not use this security group design in production. Later, we'll put the application behind an ALB and restrict backend access to the load balancer.

### Step 4 — Preview and deploy

Always inspect the proposed infrastructure changes before deployment:

```bash
pulumi preview
```

Deploy:

```bash
pulumi up
```

Review the plan and approve it when prompted.

After deployment, inspect the exported outputs:

```bash
pulumi stack output
pulumi stack output server_a_az
pulumi stack output server_b_az
```

Verify that the AZ outputs differ.

### Step 5 — Test both servers directly

```bash
URL_A=$(pulumi stack output http_url_a)
URL_B=$(pulumi stack output http_url_b)

curl --fail --show-error --retry 12 --retry-delay 10 \
  --retry-connrefused "$URL_A"

curl --fail --show-error --retry 12 --retry-delay 10 \
  --retry-connrefused "$URL_B"
```

You should receive different HTML responses identifying Server A and Server B.

If a request fails, investigate the following:

* EC2 instance state and system status checks.

* Whether the subnet assigns a public IP and has a route to an Internet Gateway.

* Security group ingress rules for TCP port 80.

* Whether the EC2 user-data script completed successfully.

* Whether `lab-web.service` is active.

For example, check instance status:

```bash
aws ec2 describe-instance-status \
  --include-all-instances \
  --query 'InstanceStatuses[].{Instance:InstanceId,State:InstanceState.Name,System:SystemStatus.Status,InstanceStatus:InstanceStatus.Status}' \
  --output table
```

For startup diagnostics, use EC2's system log and console output where available, or use AWS Systems Manager Session Manager if you have configured the necessary instance role, agent, connectivity, and permissions.

### 10\. Lab 3 — Inspect load-balancing resources using AWS CLI

We haven't created a load balancer yet. This is intentional: you will learn to inspect the AWS resources that will be connected in Module 2.

### Step 1 — Inspect existing load balancers

List load balancers in your selected Region:

```bash
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[].{Name:LoadBalancerName,Type:Type,Scheme:Scheme,State:State.Code,DNS:DNSName}' \
  --output table
```

This command queries the ELBv2 API, which covers ALB, NLB, and GWLB. Classic Load Balancers use the older ELB API:

```bash
aws elb describe-load-balancers \
  --query 'LoadBalancerDescriptions[].{Name:LoadBalancerName,DNS:DNSName}' \
  --output table
```

If you haven't created any load balancers, empty results are expected.

### Step 2 — Inspect target groups

```bash
aws elbv2 describe-target-groups \
  --query 'TargetGroups[].{Name:TargetGroupName,Protocol:Protocol,Port:Port,Type:TargetType,VPC:VpcId}' \
  --output table
```

Target groups belong to load-balancer configurations; your two EC2 instances are not yet registered with any target group.

### Step 3 — Inspect listeners

```bash
aws elbv2 describe-listeners \
  --load-balancer-arn REPLACE_WITH_LOAD_BALANCER_ARN
```

This command requires a load balancer ARN. Since this module does not create one, run it later after deploying an ALB in Module 2.

You can also explore the AWS Management Console:

* Open the EC2 console in your selected Region.

* Under Load Balancing, open Load Balancers.

* Inspect the load balancer list and available types.

* Open Target Groups and review the target registration and health-check configuration screens.

For the official resource and architecture reference, see the [Elastic Load Balancing documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html?utm_source=chatgpt.com). Elastic Load Balancing +1

### 11\. Lab 4 — Observe traffic and failure behavior

This experiment demonstrates the limitations of running two independent servers without a load balancer.

### Step 1 — Observe repeated requests

```bash
for i in $(seq 1 5); do
  echo "Request $i"
  curl --silent --show-error "$URL_A"
  echo
done
```

Every successful request to `URL_A` reaches Server A. Repeating requests to the same public IP does not distribute traffic to Server B.

That is the core problem this course will address.

### Step 2 — Compare the two endpoints

```bash
printf 'Server A: %s\n' "$URL_A"
printf 'Server B: %s\n' "$URL_B"

curl -sS -o /dev/null -w 'A: HTTP %{http_code}\n' "$URL_A"
curl -sS -o /dev/null -w 'B: HTTP %{http_code}\n' "$URL_B"
```

Both endpoints should return HTTP `200` once the web services have started successfully.

### Step 3 — Understand a failure

Suppose Server A stops responding. Requests sent to Server A's public address fail, while requests to Server B may still succeed.

Without a load balancer, clients must know which endpoint to contact. There is no shared entry point that automatically avoids the failed server.

In later modules, we will register these kinds of backends with a target group and configure a load balancer to route traffic according to target health.

You can inspect the running services with Session Manager if it is configured. For this lab, you don't need to stop or terminate either instance to understand the failure scenario.

### 12\. Optional Docker exercise — Run the same application locally

Docker is part of the course toolchain, although the main infrastructure lab uses EC2 directly.

Create a directory:

```bash
mkdir -p docker-demo
cd docker-demo
```

Create `index.html`:

```html
<!doctype html>
<html>
<body>
  <h1>Local HTTP application</h1>
  <p>Running in a Docker container.</p>
</body>
</html>
```

Create a `Dockerfile`:

```dockerfile
FROM python:3.14-slim

WORKDIR /app
COPY index.html /app/index.html

EXPOSE 8080

CMD ["python", "-m", "http.server", "8080", "--directory", "/app"]
```

Build and run:

```bash
docker build -t aws-lb-demo:1.0 .

docker run --rm -d \
  --name aws-lb-demo \
  -p 8080:8080 \
  aws-lb-demo:1.0
```

Test it:

```bash
curl http://localhost:8080
```

Clean up the container:

```bash
docker stop aws-lb-demo
cd ..
```

This local application illustrates the same backend concept used by load balancers: a process listens on a port and responds to requests. Docker itself does not provide the AWS load-balancing architecture we will build in the next modules.

### 13\. Clean up the AWS resources

EC2 instances and other AWS resources can incur charges while running. Once you've finished testing, destroy the lab infrastructure unless you intend to continue using it.

From the Pulumi project directory:

```bash
pulumi destroy
```

Review the proposed deletions and approve them. Confirm the stack no longer manages the instances and security group:

```bash
pulumi stack
pulumi stack output
```

If you retain the project for Module 2, keep the source code but recreate the resources when needed. Do not leave public test servers running unnecessarily.

### 14\. Module 1 recap

You now have the foundation for the rest of the course:

* Layer 4 load balancing distributes transport-level connections; Layer 7 load balancing can make HTTP-aware routing decisions.

* ALB, NLB, GWLB, and Classic Load Balancer serve different architectural needs.

* Listeners accept traffic, rules determine routing actions, target groups define backend configurations, and health checks evaluate target health.

* Multi-AZ deployments improve resilience, but applications still need sufficient capacity and healthy dependencies.

* Public load balancers can route traffic to private backends.

* Route 53, CloudFront, API Gateway, reverse proxies, and load balancers perform different but complementary roles.

* Pulumi lets you define and manage AWS infrastructure using Python, while Bash and AWS CLI provide repeatable workflows for deployment and troubleshooting.

### Official references

* AWS Elastic Load Balancing documentation — [Architecture and fundamentals](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/what-is-load-balancing.html?utm_source=chatgpt.com).

* Pulumi AWS documentation — [Pulumi with AWS](https://www.pulumi.com/docs/clouds/aws/get-started/?utm_source=chatgpt.com).

* AWS CLI documentation — [AWS CLI user guide](https://docs.aws.amazon.com/cli/latest/userguide/?utm_source=chatgpt.com).

Next module: Module 2 — Application Load Balancer (ALB) and HTTP Routing, where we'll create an ALB with Pulumi, register backend targets, configure listeners and path-based routing, and test the shared endpoint.
