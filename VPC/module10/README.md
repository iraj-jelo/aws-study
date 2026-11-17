
Worked for 39s

### Module 10 — Load Balancing and Application Networking

AWS VPC Course · Advanced networking · Pulumi Python · October 2026

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Explain how Elastic Load Balancing (ELB) interacts with VPC subnets, route tables, network interfaces, security groups, and Availability Zones.

* Choose between an Application Load Balancer (ALB), Network Load Balancer (NLB), and Gateway Load Balancer (GWLB).

* Design public-facing and internal load-balancing architectures.

* Configure target groups, health checks, security group relationships, TLS termination, and connection draining.

* Deploy a private application behind an internal load balancer using Pulumi and Python.

* Diagnose unhealthy targets, routing failures, security group mistakes, and Availability Zone problems.

We'll focus on modern, production-relevant AWS patterns rather than legacy load-balancing designs.

### 2\. How Elastic Load Balancing fits into a VPC

Elastic Load Balancing is an AWS-managed service that distributes incoming connections or requests across registered targets. Depending on the load balancer type, those targets can include EC2 instances, IP addresses, containers, or other supported resources.

A load balancer is not a replacement for VPC routing or security controls. It works with them.

### A typical three-tier architecture

Client or upstream service

HTTP/HTTPS request

Application Load Balancer

Public or internal · Listener · TLS · Routing rules

Forward to healthy targets

Private subnet A

App instance A

TCP 8000

Private subnet B

App instance B

TCP 8000

Database tier

Private database subnet · Restricted database security group

This architecture separates three responsibilities:

* The load balancer accepts connections, evaluates listeners and rules, and selects healthy targets.

* The application tier processes requests without needing public IP addresses or direct public ingress.

* The database tier accepts traffic only from explicitly authorized application resources.

For a genuinely private application, use an internal load balancer. An internal load balancer is reachable through private networking, such as from the same VPC, connected VPCs, or an authorized on-premises network. It does not automatically become reachable from every private network; routing and security still apply.

### 3\. Choose the right load balancer

AWS has three major Elastic Load Balancing types relevant to this module. They solve different problems.

![Load balancer subnets and routing - AWS Prescriptive Guidance](https://images.openai.com/static-rsc-4/3m5kLrWfDVVPF2dCUOAGX8PcBQg-gee8NacTgVzmJSuvX8Fr16PaCan6kgPDYVOCGVT7EwgOf8nRh5H5a0UEondz_LohJFDs1UhWxbEvMvQb-XrXvkeyrpYZ-3wAJkh7a5Eiko2Cc2Lzy5i_9_yxU3k4lFwYc22aIp66VQL2QfKn_oNha_rSE8HVkgSWQmvE?purpose=fullsize)

Application Load Balancer (ALB)

Layer 7

Best for HTTP/HTTPS applications, REST APIs, web apps, and microservices. Supports host-based and path-based routing, redirects, and TLS termination.

Example: `/api/*` goes to FastAPI; `/admin/*` goes to an admin service.

[AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html?utm_source=chatgpt.com)

![What is AWS Network Load Balancer (NLB)?](https://images.openai.com/static-rsc-4/eXD7VRXPngVNSU0aBSwL9Jnd3FsHQD8bLHtLKa3XGlsVVViz2VFmjTtSgah2teToPO9G9sVgnUUG_VJ7856V4fIsVbPsT-3SUK9gd87fAKIs-K-IKgN11og6hzNZvJxoHZVoL9wOXbjr3Djkzq_F_OOl2hMRh7sfZFq-j5RjGcm59SDDXVb8E26XgKrpPmEa?purpose=fullsize)

Network Load Balancer (NLB)

Layer 4

Best for TCP, UDP, and TLS connection-level load balancing, static IP requirements, and workloads requiring high-performance network traffic handling.

Example: a TCP service or a protocol that isn't HTTP.

[AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html?utm_source=chatgpt.com)

![AWS Gateway Load Balancer 1O1. Digital equipment such as firewalls… | by Piyush Jalan | Medium](https://images.openai.com/static-rsc-4/3o4mHL1h56WZ2bPpSPnVGLGBeZTSwHEZAi2FaSPJD7vYWg3ROhGctbgeMvdQRyzs-9Mm0d7Rj-1CEiDMp-4WFru_qX6AzYOzaJ2PiSDgGAc5iFsf3Sw01gBS6BWNYGDC-sEaeV12ZLDY9dP-p87g3niPEkWNhF1NDiJ-OhoTElTMdK1p2j_2I4UaTr7KrhEi?purpose=fullsize)

Gateway Load Balancer (GWLB)

Layer 3/4 traffic handling

Designed to deploy, scale, and distribute traffic across virtual network appliances, such as firewalls and intrusion detection systems, using GENEVE encapsulation.

Example: transparently directing network traffic through a fleet of inspection appliances.

[AWS documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/introduction.html?utm_source=chatgpt.com)

### Which should you use?

| Requirement                                     | Recommended starting point |
| ----------------------------------------------- | -------------------------- |
| FastAPI, Django, web applications               | ALB                        |
| Path- or hostname-based HTTP routing            | ALB                        |
| TCP/UDP application                             | NLB                        |
| Static IP addresses for the load balancer       | NLB is often appropriate   |
| Firewall appliance fleet                        | GWLB                       |
| Internal HTTP microservices                     | Internal ALB               |
| TLS pass-through or specialized TLS connections | Evaluate NLB               |

These are starting points, not absolute rules. NLB also supports TLS listeners that terminate TLS, and an ALB can forward traffic to targets using HTTP or HTTPS. Choose based on the protocol, routing requirements, client behavior, security model, and operational constraints.

### 4\. Public vs. internal load balancers

The `scheme` property determines whether an ALB or NLB is internet-facing or internal.

![負載平衡器子網路和路由 - AWS 方案指引](https://images.openai.com/static-rsc-4/WePil2GUCtONeFf5mCOaUJiO4Y90YVzZSmAeY2PxWRL57JGZ1sla589C9OpD4LY3hWV_vWqTm4iIMYX0pa8Zi9qtq2_S76Xu64ReiD4YHF1J1b1gTWDg_pxT5CoW4mlgvUqPjLrRUbSVpz55XAaCyNLgZBFqAqRCJClenc13Lw1otEZoPvtB0IZJMxtjWoH-?purpose=fullsize)

Internet-facing

* Accepts traffic from internet-reachable clients when routing and security permit.

* Usually deployed into public subnets in at least two Availability Zones.

* Can forward to application targets in private subnets.

* Common for public websites and APIs.

![AWS VPC Internal ALB Architecture — Diagrams.so](https://images.openai.com/static-rsc-4/YlRx_4dY5mxV21UdNA_7Opb27jEGqjKyLBzdvSWFmD3NnqElrxJJ3cgo5Pl_OZwImEIkxZw-fLy0ARyX9ZPZ7BEbUavzOrJpv_XE4nxUUEnnKEFRixY7MAO9O_RzLM1JIx5MJORRSJG5FrdYXmDdEp1bH1LGernPQnC0RacYNykHnJ_FY6Ihb11SVsP7Pj0O?purpose=fullsize)

Internal

* Uses private load-balancer addresses.

* Accessible through authorized private network paths.

* Suitable for internal APIs and private services.

* Does not require a public ingress path.

Important distinction: a public load balancer can forward to private targets. The application servers do not need public IP addresses simply because the load balancer is internet-facing.

Likewise, an internal load balancer is not secured by its internal scheme alone. Security groups, routing, application authentication, and network boundaries still matter.

### How VPC routing participates

For an internet-facing ALB, a typical request follows this path:

* The client resolves the ALB DNS name.

* The client connects to an address associated with an enabled load-balancer Availability Zone.

* The ALB security group permits the listener traffic.

* The ALB selects a healthy target from its target group.

* The ALB establishes a separate backend connection to the target's private address.

* The target security group permits the connection from the ALB security group.

* The response returns through the load balancer to the client.

The backend response does not normally travel directly from the application instance to the original client. The load balancer handles the frontend and backend connections.

For an internal ALB, the first connection originates from a client with an appropriate private route to the load balancer.

### 5\. Target groups, listeners, and health checks

An ALB has three important configuration layers.

Listener

Accepts traffic on a protocol and port, such as HTTP:80 or HTTPS:443.

Listener rules

Evaluate conditions such as hostname, path, or headers and select an action.

Target group

Defines the backend protocol, port, health-check configuration, and registered targets.

Registered targets

EC2 instances, private IP addresses, containers, or other supported target types.

An ALB target group supports routing configuration and health checks independently of the listener. The listener must reference the target group for the ALB to use it for that traffic.

### Health checks

Suppose your FastAPI application listens on port `8000` and exposes `/health`.

A reasonable starting configuration is:

| Setting               | Example      |
| --------------------- | ------------ |
| Health-check protocol | HTTP         |
| Health-check port     | Traffic port |
| Health-check path     | /health      |
| Success codes         | 200          |
| Interval              | 15 seconds   |
| Timeout               | 5 seconds    |
| Healthy threshold     | 2            |
| Unhealthy threshold   | 3            |

These are example values, not universal production defaults. Tune them to the application's startup time, response latency, and failure-detection requirements.

The health endpoint should return a successful status only when the application can serve requests at the level of health you intend to measure. Be careful about making a brief database outage cause every application target to be removed simultaneously.

### Target health states

* `initial`: registration or initial health checks are in progress.

* `healthy`: health checks are passing.

* `unhealthy`: health checks are failing.

* `draining`: the target is being deregistered while existing requests or connections are allowed to finish.

* `unused`: the target is not currently usable by the load balancer, for example because it isn't referenced by a listener rule or its Availability Zone isn't enabled.

For ALBs, consult the target group's reported reason codes instead of diagnosing by status alone.

### 6\. Security group relationships

This is one of the most important parts of the lab.

Use two security groups:

* `alb-sg`: controls who can connect to the internal ALB and what backend traffic it can send.

* `app-sg`: allows application traffic only from `alb-sg`.

Internal ALB security group

Inbound: TCP 80 from the VPC CIDR, or a narrower approved client CIDR.

Outbound: TCP 8000 to the application security group.

TCP 8000 — permitted by source security-group reference

Application security group

Inbound: TCP 8000 from the ALB security group only.

No public inbound rule and no SSH rule required.

Security groups are stateful, so return traffic for permitted connections is allowed automatically. Ensure that the ALB security group permits the target port and health-check port, and that the target security group permits traffic from the ALB security group.

Avoid opening port `8000` to `0.0.0.0/0`. Doing so would undermine the intended isolation even if the load balancer itself is internal.

### 7\. Cross-zone load balancing and Availability Zones

Cross-zone load balancing determines whether a load-balancer node can distribute traffic to targets in other Availability Zones.

Consider this example:

* AZ A: 2 healthy application targets.

* AZ B: 6 healthy application targets.

* Incoming traffic: 800 requests per second, evenly distributed between the two load-balancer zones.

If cross-zone load balancing is disabled, each zone's load-balancer node generally distributes traffic only among targets in its own zone. With even incoming distribution, that could mean approximately 400 requests per second per zone, despite the unequal target counts.

If cross-zone load balancing is enabled, each zone's load-balancer node can distribute requests across targets in both zones. With an ideal even distribution across all eight targets, each target would receive approximately 100 requests per second.

These numbers are illustrative, not a guarantee of AWS's request distribution.

### Default behavior by load balancer type

| Type | Cross-zone behavior                                                                           |
| ---- | --------------------------------------------------------------------------------------------- |
| ALB  | Enabled by default; can be disabled at target-group level in supported configurations.        |
| NLB  | Disabled by default; can be enabled at load-balancer or supported target-group configuration. |
| GWLB | Disabled by default; supports cross-zone configuration.                                       |

Check the current service documentation when selecting the behavior for a particular target-group type.

Production implications

* Cross-zone distribution can help compensate for unequal target counts between zones.

* Without cross-zone distribution, each zone needs enough local capacity to handle its own traffic.

* Cross-zone traffic can introduce data-transfer charges depending on the service and configuration.

* A multi-AZ load balancer alone does not guarantee application availability. You also need healthy targets, sufficient capacity, and an application that can recover from a zone failure.

For a typical web application, starting with an ALB and healthy targets in at least two Availability Zones is a sensible design.

### 8\. TLS termination and traffic paths

TLS termination is the point where encrypted HTTPS traffic is decrypted.

For a public web application, a common architecture is:

```text
Client
  |
  | HTTPS :443
  v
Application Load Balancer
  |-- TLS certificate (ACM)
  |-- HTTPS listener
  |-- HTTP routing rules
  |
  | HTTP :8000 over the VPC
  v
Private FastAPI target
```

The client-to-ALB connection is encrypted, but the ALB-to-target connection uses HTTP. Traffic on the backend leg is not protected by TLS merely because the client used HTTPS.

For applications with stricter security requirements, use HTTPS between the load balancer and targets as well:

```text
Client -- HTTPS --> ALB -- HTTPS --> Application
```

The backend HTTPS connection requires the application to serve TLS. AWS documents that ALB HTTPS target connections use certificates installed on targets, but the ALB does not validate those target certificates in the conventional certificate-chain validation sense. Consider the threat model and requirements before treating backend HTTPS as equivalent to end-to-end authenticated TLS.

### Recommended TLS practices

* Store public certificates in AWS Certificate Manager (ACM) where appropriate.

* Prefer HTTPS on public-facing application listeners.

* Configure a suitable current TLS security policy.

* Use HTTP on the backend only when it meets your internal transport-security requirements.

* Avoid placing secrets, tokens, or credentials in URLs.

* Configure application logging to avoid recording sensitive headers and cookies.

For an internal-only lab, we'll use HTTP to focus on VPC networking. In production, an internal ALB can also have an HTTPS listener and a suitable certificate.

### 9\. Connection draining and target replacement

When an instance is removed from a target group, the load balancer should not immediately terminate every request already being processed by that instance.

Deregistration delay, often called connection draining, gives existing work time to complete. The exact behavior depends on the load balancer and target protocol.

For a web application, consider this deployment sequence:

* Start a replacement application instance.

* Wait until it passes health checks.

* Begin sending traffic to the replacement.

* Deregister the old instance.

* Allow in-flight requests to finish within the configured delay.

* Terminate the old instance.

This reduces failed requests during deployments. It does not guarantee that every long-running request will finish: clients can disconnect, requests can exceed timeouts, and connections can be reset.

Coordinate deregistration delay with application shutdown behavior, request timeouts, container termination grace periods, and deployment orchestration.

### 10\. Hands-on lab — Private FastAPI-style application behind an internal ALB

We'll deploy an isolated VPC with two private subnets, an internal ALB, and two private EC2 application targets.

Lab design

VPC — `10.40.0.0/16`

No internet gateway or NAT gateway

Internal ALB

Private listener · TCP 80 · HTTP health checks

Private subnet A

EC2 target A

10.40.1.0/24

Private subnet B

EC2 target B

10.40.2.0/24

The application instances have no public IP addresses. A client must have an authorized private route to the ALB to make requests.

### Lab prerequisites and cost warning

You need:

* An AWS account with permissions to create VPCs, subnets, security groups, EC2 instances, target groups, and load balancers.

* AWS CLI v2 configured with appropriate credentials.

* Python and Pulumi installed locally.

* The Pulumi AWS provider.

This lab is not guaranteed to be free. The ALB incurs charges while provisioned, and EC2 instances, storage, and data transfer may also incur charges. No NAT gateway is created, avoiding its hourly and data-processing charges. The instances have no public IPv4 addresses.

We'll use Amazon Linux 2023 and its built-in Python runtime for a small HTTP health-check application. No external package installation is required by the user-data script. This is a networking demonstration, not a production application deployment.

### Step 1 — Create the Pulumi project

```bash
mkdir vpc-module10-alb
cd vpc-module10-alb

pulumi new aws-python
```

Choose a stack name such as `dev`, and select your AWS region.

Set the region if needed:

```bash
pulumi config set aws:region eu-west-3
```

Use the following project structure:

```text
vpc-module10-alb/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── __main__.py
└── requirements.txt
```

The `pulumi new` command generates the initial project files. Keep the generated project configuration and replace the example program with the code below.

### Step 2 — Declare the infrastructure

Replace `__main__.py` with this complete example:

```python

import pulumi
import pulumi_aws as aws

# -------------------------------------------------------
# 1. VPC and two private subnets
# -------------------------------------------------------

vpc = aws.ec2.Vpc(
    "app-vpc",
    cidr_block="10.40.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "module10-app-vpc"},
)

azs = aws.get_availability_zones(
    state="available",
)

subnet_a = aws.ec2.Subnet(
    "private-a",
    vpc_id=vpc.id,
    cidr_block="10.40.1.0/24",
    availability_zone=azs.names[0],
    map_public_ip_on_launch=False,
    tags={"Name": "module10-private-a"},
)

subnet_b = aws.ec2.Subnet(
    "private-b",
    vpc_id=vpc.id,
    cidr_block="10.40.2.0/24",
    availability_zone=azs.names[1],
    map_public_ip_on_launch=False,
    tags={"Name": "module10-private-b"},
)

# No internet gateway or NAT gateway is created.
# The VPC's local route is sufficient for ALB-to-target traffic.

# -------------------------------------------------------
# 2. Security groups
# -------------------------------------------------------

alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    vpc_id=vpc.id,
    description="Allow HTTP from approved VPC clients",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["10.40.0.0/16"],
            description="Internal HTTP clients",
        )
    ],
    egress=[],
)

app_sg = aws.ec2.SecurityGroup(
    "app-sg",
    vpc_id=vpc.id,
    description="Allow app traffic only from the ALB",
    ingress=[],
    egress=[],
)

# Explicit ALB egress to the application listener.
alb_to_app = aws.ec2.SecurityGroupRule(
    "alb-to-app",
    type="egress",
    security_group_id=alb_sg.id,
    source_security_group_id=app_sg.id,
    protocol="tcp",
    from_port=8000,
    to_port=8000,
    description="ALB to app listener and health checks",
)

# Targets accept traffic only from the ALB security group.
app_from_alb = aws.ec2.SecurityGroupRule(
    "app-from-alb",
    type="ingress",
    security_group_id=app_sg.id,
    source_security_group_id=alb_sg.id,
    protocol="tcp",
    from_port=8000,
    to_port=8000,
    description="Application traffic from ALB",
)

# -------------------------------------------------------
# 3. Application target group
# -------------------------------------------------------

target_group = aws.lb.TargetGroup(
    "app-targets",
    vpc_id=vpc.id,
    port=8000,
    protocol="HTTP",
    target_type="instance",
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        protocol="HTTP",
        port="traffic-port",
        path="/health",
        matcher="200",
        interval=15,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
    deregistration_delay=30,
)

# -------------------------------------------------------
# 4. Internal Application Load Balancer
# -------------------------------------------------------

alb = aws.lb.LoadBalancer(
    "internal-alb",
    internal=True,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=[subnet_a.id, subnet_b.id],
    enable_deletion_protection=False,
    tags={"Name": "module10-internal-alb"},
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

# -------------------------------------------------------
# 5. Minimal application for each private EC2 instance
# -------------------------------------------------------

user_data = """#!/bin/bash
set -eu

cat >/opt/module10-app.py <<'PYTHON'
from http.server import BaseHTTPRequestHandler, HTTPServer
import socket

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"healthy\\n")
            return

        if self.path == "/":
            body = (
                "Hello from private target: "
                + socket.gethostname()
                + "\\n"
            ).encode()
            self.send_response(200)
            self.end_headers()
            self.wfile.write(body)
            return

        self.send_response(404)
        self.end_headers()

HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()
PYTHON

cat >/etc/systemd/system/module10-app.service <<'UNIT'
[Unit]
Description=Module 10 sample application
After=network.target

[Service]
ExecStart=/usr/bin/python3 /opt/module10-app.py
Restart=always
User=nobody

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now module10-app.service
"""

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

instance_a = aws.ec2.Instance(
    "app-instance-a",
    ami=ami.id,
    instance_type="t3.micro",
    subnet_id=subnet_a.id,
    vpc_security_group_ids=[app_sg.id],
    associate_public_ip_address=False,
    user_data=user_data,
    user_data_replace_on_change=True,
    tags={"Name": "module10-app-a"},
    opts=pulumi.ResourceOptions(
        depends_on=[app_from_alb],
    ),
)

instance_b = aws.ec2.Instance(
    "app-instance-b",
    ami=ami.id,
    instance_type="t3.micro",
    subnet_id=subnet_b.id,
    vpc_security_group_ids=[app_sg.id],
    associate_public_ip_address=False,
    user_data=user_data,
    user_data_replace_on_change=True,
    tags={"Name": "module10-app-b"},
    opts=pulumi.ResourceOptions(
        depends_on=[app_from_alb],
    ),
)

registration_a = aws.lb.TargetGroupAttachment(
    "register-app-a",
    target_group_arn=target_group.arn,
    target_id=instance_a.id,
    port=8000,
)

registration_b = aws.lb.TargetGroupAttachment(
    "register-app-b",
    target_group_arn=target_group.arn,
    target_id=instance_b.id,
    port=8000,
)

pulumi.export("vpc_id", vpc.id)
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("alb_scheme", alb.internal.apply(
    lambda value: "internal" if value else "internet-facing"
))
pulumi.export("target_group_arn", target_group.arn)
pulumi.export("instance_ids", [
    instance_a.id,
    instance_b.id,
])
```

### Step 3 — Review and deploy

Install the provider dependency if needed:

```bash
python -m pip install pulumi pulumi-aws
```

Preview the changes before provisioning:

```bash
pulumi preview
```

Review the planned VPC, subnets, security groups, instances, target group, listener, and load balancer. Then deploy:

```bash
pulumi up
```

Confirm the update when prompted.

The first deployment may take several minutes. EC2 user data runs during instance initialization, so an instance being `running` does not necessarily mean the application is ready.

Important: This lab deliberately has no NAT gateway and no internet gateway. That makes the targets private, but it also means they cannot download packages or contact arbitrary public services. If you later add Systems Manager access or logging, plan the required IAM permissions, service endpoints, and connectivity separately.

### Step 4 — Verify the load balancer and target health

First, retrieve the deployed outputs:

```bash
pulumi stack output vpc_id
pulumi stack output alb_dns_name
pulumi stack output target_group_arn
pulumi stack output instance_ids
```

Check the load balancer's state:

```bash
aws elbv2 describe-load-balancers \
  --names internal-alb \
  --query 'LoadBalancers[].{DNSName:DNSName,Scheme:Scheme,State:State.Code,Type:Type}' \
  --output table
```

Depending on the generated physical resource name, use the ARN from Pulumi if `--names internal-alb` doesn't match.

Expected properties:

* `Scheme`: `internal`

* `Type`: `application`

* `State`: eventually `active`

Next, inspect the target group:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$(pulumi stack output target_group_arn)" \
  --query 'TargetHealthDescriptions[].{ID:Target.Id,Port:Target.Port,State:TargetHealth.State,Reason:TargetHealth.Reason,Description:TargetHealth.Description}' \
  --output table
```

Both targets should eventually report `healthy`.

Check the instances' networking:

```bash
aws ec2 describe-instances \
  --instance-ids $(pulumi stack output instance_ids | tr -d '[],"') \
  --query 'Reservations[].Instances[].{ID:InstanceId,State:State.Name,PrivateIP:PrivateIpAddress,PublicIP:PublicIpAddress,Subnet:SubnetId}' \
  --output table
```

The expected result is two running instances with private IP addresses and no public IP addresses.

### Step 5 — Test the application

Because the ALB is internal, run this test from a machine with a valid route into the VPC, such as an existing private test instance or an appropriately configured VPN-connected workstation.

```bash
curl -i http://YOUR_INTERNAL_ALB_DNS_NAME/
```

Expected response:

```text
HTTP/1.1 200 OK

Hello from private target: ip-10-40-1-...
```

Repeat the request. The hostname in the response should indicate which target handled the request, although consecutive requests are not guaranteed to alternate between targets.

Test the health endpoint too:

```bash
curl -i http://YOUR_INTERNAL_ALB_DNS_NAME/health
```

Expected response:

```text
HTTP/1.1 200 OK

healthy
```

If you run these commands from your ordinary laptop without VPN or another route into the VPC, the request should not be expected to work. That is intentional: an internal ALB is not publicly reachable.

### Step 6 — Clean up

After the lab, destroy the provisioned infrastructure:

```bash
pulumi destroy
```

Review the proposed deletions and confirm when ready.

This removes the lab's ALB, EC2 instances, security groups, subnets, target group, and VPC. Check the Pulumi result to confirm successful deletion and investigate any retained or failed resources.

Do not use `pulumi stack rm` as a substitute for infrastructure cleanup. Removing the stack metadata does not itself delete AWS resources.

### 11\. Troubleshooting and failure analysis

Use this diagnostic sequence rather than changing security rules randomly.

Problem: Target is unhealthy

Check the target group's reason code, health-check path, listener port, application process, and both security groups.

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TG_ARN"
```

Problem: Connection times out

Confirm that the client can route to the internal ALB, the ALB security group allows inbound traffic, ALB egress permits port 8000, and the target security group allows port 8000 from the ALB security group.

```bash
aws ec2 describe-security-groups \
  --group-ids "$ALB_SG" "$APP_SG"
```

Problem: Target reports `unused`

Verify that the target group is referenced by a listener action, the target is registered, and its Availability Zone is enabled for the load balancer.

```bash
aws elbv2 describe-target-groups \
  --target-group-arns "$TG_ARN"
```

Problem: Instances are running but the app doesn't respond

A running EC2 instance does not guarantee that user data completed successfully. Check the application's systemd service, process, port binding, and cloud-init logs through an authorized management path.

```bash
systemctl status module10-app
journalctl -u module10-app
```

Run these commands on the instance, not on your local workstation.

### Common failure patterns

| Symptom                                    | Likely cause                                                                                      |
| ------------------------------------------ | ------------------------------------------------------------------------------------------------- |
| ALB DNS name doesn't resolve               | DNS configuration, incorrect hostname, or client resolver issue                                   |
| DNS resolves but connection times out      | Missing private route, security-group restriction, or unreachable client                          |
| HTTP 503                                   | No usable healthy targets for the relevant routing action                                         |
| HTTP 502                                   | Backend connection failure, invalid backend response, or protocol mismatch                        |
| HTTP 504                                   | Backend connection or response timeout                                                            |
| Targets flap between healthy and unhealthy | Slow responses, overloaded targets, intermittent connectivity, or overly aggressive health checks |
| One zone fails while another works         | Zone-specific target failure, capacity imbalance, or configuration differences                    |

These HTTP responses are diagnostic clues, not definitive proof of a single cause.

For more detail, inspect the ALB access logs, CloudWatch metrics, target-health reason codes, and VPC Flow Logs. Flow Logs can help establish whether traffic was accepted or rejected at network interfaces, but they do not show the complete application request or prove that an HTTP request succeeded.

### 12\. Security, resilience, and production considerations

Before applying this architecture to a real application, account for the following:

* Availability: Use at least two suitable Availability Zones and enough targets to survive a target or zone failure.

* Least privilege: Restrict application ingress to the ALB security group. Restrict ALB ingress to approved clients.

* TLS: Use HTTPS for sensitive traffic and define your backend encryption requirements explicitly.

* Health checks: Separate lightweight liveness checks from deeper dependency checks when necessary.

* Deployments: Set an appropriate deregistration delay and allow the application to shut down gracefully.

* Capacity: Monitor healthy host counts, latency, request volume, and target saturation.

* Cost: Budget for load-balancer hours, capacity usage, data processing, data transfer, logging, and any associated public IPv4 addresses.

* Infrastructure as code: Use Pulumi previews, stack separation, controlled changes, and deletion safeguards for important production resources.

For production, consider enabling deletion protection on the load balancer and adding explicit monitoring and alarms. The lab intentionally omits those extras to keep its lifecycle simple.

### 13\. Official references

These AWS and Pulumi documents provide the detailed service behavior and current resource configuration options used in this module.

[Application Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/introduction.html?utm_source=chatgpt.com)

Listeners, rules, request routing, and ALB architecture.

[Network Load Balancers](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html?utm_source=chatgpt.com)

TCP/UDP/TLS, zonal behavior, and target distribution.

[ALB security groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-update-security-groups.html?utm_source=chatgpt.com)

Inbound and outbound rules, target access, and health-check connectivity.

[ALB target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html?utm_source=chatgpt.com)

Target registration, health checks, target attributes, and failure handling.

[Pulumi AWS load-balancing resources](https://www.pulumi.com/registry/packages/aws/api-docs/lb/?utm_source=chatgpt.com)

Python IaC reference for load balancers, listeners, and target groups.

### Module 10 recap

The central principle is that a load balancer is one component in a larger network design. Successful traffic delivery depends on DNS, routing, listener configuration, target registration, health checks, and security-group rules all working together.

In the lab, you created an internal ALB with private EC2 targets across two Availability Zones, restricted application traffic to the ALB's security group, verified target health using the AWS CLI, and learned how to diagnose failures.

The next module is Module 11 — IPv6 and Modern IP Address Management, covering dual-stack and IPv6-only architectures, egress-only internet gateways, NAT64/DNS64, public IPv4 costs, and Amazon VPC IP Address Manager (IPAM).
