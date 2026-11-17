Worked for 33s

### Module 2 — Application Load Balancer (ALB) and HTTP Routing

AWS Load Balancing Course · Module 2 of 8

### Learning objectives

By the end of this module, you will understand how an Application Load Balancer distributes HTTP and HTTPS traffic, how listener rules select backend services, and how to build a multi-service application architecture using Pulumi with Python and Bash.

You will learn to:

* Design ALB listeners, listener rules, and target groups.

* Route requests using hostnames, URL paths, HTTP headers, query strings, and source IP addresses.

* Configure HTTPS termination, redirects, fixed responses, and weighted forwarding.

* Understand target registration and health checks for EC2 instances, IP addresses, and Lambda functions.

* Work with HTTP/2, gRPC, WebSockets, and relevant ALB attributes.

* Deploy and manage ALB infrastructure using Pulumi, inspect it using the AWS CLI, and test routing with `curl`.

### 1\. Application Load Balancer architecture

An Application Load Balancer is a managed Layer 7 load balancer. It understands HTTP and HTTPS requests, allowing it to route traffic based on application-level information instead of distributing connections solely by IP address and port.

For example, one ALB can serve an entire application composed of several services:

* `app.example.com/` → frontend service

* `app.example.com/api/` → API service

* `admin.example.com/` → administration service

* `app.example.com/catalog/` → catalog service

This approach reduces the need to expose a separate public load balancer for every application component.

![Introducing Application Load Balancer – Unlocking and Optimizing Architectures | AWS DevOps & Developer Productivity Blog](https://images.openai.com/static-rsc-4/v8-v1zkiBV2bZezIBZOiAQOf5kyypLWdUsIl2foGLCLnt-E-Rl49-pXK0yUaV7ixjNg4AAKmknYxOSmnLEYsWgcVbSVXcEiaX7TyrZ195uYRQNPTOMjSjmWULLYoUazWUYEM1QwRmXqtGF2rt7WRX5s0TYgeFFg7P7vHgm5a9NjM9AkbXrG5fu2n6gaZl9QC?purpose=fullsize)

### Core components

Load balancer

The entry point that receives incoming connections and distributes requests to healthy targets. An internet-facing ALB is reachable through public networking; an internal ALB is intended for private application traffic.

Listener

Checks for connection requests on a configured protocol and port, such as HTTP on port 80 or HTTPS on port 443.

Listener rule

Evaluates request conditions in priority order and selects an action, such as forwarding, redirecting, or returning a fixed response.

Target group

Defines the backend targets, target protocol and port, health-check configuration, and related forwarding behavior.

Target

The destination receiving forwarded requests: an EC2 instance, an IP address, or a Lambda function.

The request flow is:

* A client resolves the application hostname and connects to the ALB.

* The listener accepts the connection on its configured port.

* The ALB evaluates the listener rules against the HTTP request.

* The selected action forwards the request to a target group, redirects the client, or returns a fixed response.

* When forwarding, the ALB selects an eligible healthy target and sends it the request.

A target group's health checks determine which targets are eligible for normal routing. If a target group has no healthy targets, the ALB may fail open and route to registered targets anyway, depending on the target-group health state. Therefore, health checks are important for resilience but should not be treated as an absolute guarantee that traffic will never reach an unhealthy application.

### 2\. HTTP and HTTPS listeners

A listener defines the protocol and port on which the ALB accepts connections. An ALB must have at least one listener before it can receive application traffic. ALB listeners support HTTP and HTTPS. Elastic Load Balancing +1

| Listener          | Typical port     | Purpose                                     |
| ----------------- | ---------------- | ------------------------------------------- |
| HTTP              | 80               | Accept unencrypted HTTP requests            |
| HTTPS             | 443              | Accept encrypted requests and terminate TLS |
| Custom HTTP/HTTPS | 8080, 8443, etc. | Application-specific entry points           |

### HTTP listener

An HTTP listener receives plain HTTP requests. A common production configuration redirects these requests to HTTPS rather than serving the application over an unencrypted connection.

### HTTPS listener

An HTTPS listener requires a server certificate. AWS Certificate Manager (ACM) is commonly used to provision and manage certificates for domain names you control.

With TLS termination at the ALB:

* The client establishes an encrypted TLS connection to the ALB.

* The ALB decrypts the incoming request.

* The ALB forwards the request to the selected target using the target group's configured protocol.

* The backend connection can use HTTP or HTTPS, depending on the target group.

TLS termination does not automatically encrypt the connection between the ALB and backend. Use HTTPS target groups when that additional encryption is required.

For multiple HTTPS hostnames, Server Name Indication (SNI) allows a listener to present the appropriate certificate for the requested domain. Amazon Web Services +1

### HTTP-to-HTTPS redirect

An ALB can redirect requests without sending them to a backend. A typical redirect preserves the path and query string while changing the protocol to HTTPS and the port to 443.

For example:

```bash
curl -sSI "http://app.example.com/api/products?page=2"
```

The response should contain a redirect status such as `HTTP/1.1 301 Moved Permanently` and a `Location` header pointing to the HTTPS URL, assuming the listener is configured with a 301 redirect.

Use `curl -I` or `curl -sSI` to inspect response headers. A redirect does not prove that the HTTPS application itself is healthy; test the HTTPS endpoint separately.

### 3\. Target groups and backend registration

A target group defines where forwarded requests go and how target health is evaluated. Each target group has its own protocol, port, target type, and health-check settings. A listener rule can forward to one or more target groups. Elastic Load Balancing +1

### Target types

| Target type | Registration identifier | Common use                                                 |
| ----------- | ----------------------- | ---------------------------------------------------------- |
| instance    | EC2 instance ID         | EC2-backed applications                                    |
| ip          | Private IP address      | ECS tasks, private endpoints, and supported hybrid targets |
| lambda      | Lambda function         | Serverless HTTP applications                               |

Choose the target type based on the backend's lifecycle and networking model. For example, ECS Fargate tasks commonly use IP targets because each task has its own network interface and private IP address.

The target type cannot be changed after the target group is created; create a new target group if the target type must change. Lambda targets also have different invocation and health-check semantics from instance and IP targets.

### Health checks

Health checks determine whether registered targets are eligible for normal traffic distribution.

Example configuration:

* Protocol: HTTP

* Port: traffic port

* Path: `/health`

* Healthy threshold: 2

* Unhealthy threshold: 3

* Timeout: 5 seconds

* Interval: 30 seconds

* Success matcher: `200`

These are illustrative settings, not universal recommendations. Tune them to your application's startup time, response time, and recovery requirements.

The backend must actually serve the configured health-check path and return an accepted response. A health-check path that requires authentication or returns a redirect may cause a target to be marked unhealthy.

Inspect target health with Bash:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --query 'TargetHealthDescriptions[].{
    Id:Target.Id,
    Port:Target.Port,
    State:TargetHealth.State,
    Reason:TargetHealth.Reason,
    Description:TargetHealth.Description
  }' \
  --output table
```

Common states and reasons include `initial`, `healthy`, `unhealthy`, `unused`, `Target.ResponseCodeMismatch`, `Target.Timeout`, and `Target.FailedHealthChecks`.

### 4\. Listener rules and request routing

A listener rule combines conditions with actions. Rules have priorities, and the ALB evaluates them from the lowest numerical priority to the highest. The default rule runs last if no other rule matches. Elastic Load Balancing +1

For example, consider this application:

| Priority | Condition                 | Action                          |
| -------- | ------------------------- | ------------------------------- |
| 10       | Host is admin.example.com | Forward to admin target group   |
| 20       | Path is /api/*            | Forward to API target group     |
| 30       | Path is /catalog/*        | Forward to catalog target group |
| Default  | No matching rule          | Return a fixed 404 response     |

The first matching rule wins. If multiple conditions exist in a rule, all conditions must match, while multiple values within an individual condition can provide alternatives.

### Host-based routing

Routes requests using the HTTP `Host` header.

```text
app.example.com    → frontend
api.example.com    → API
admin.example.com  → administration
```

Host-based routing is useful when multiple domains share the same ALB.

### Path-based routing

Routes requests based on the URL path.

```text
/                  → frontend
/api/*             → API
/catalog/*         → catalog
/images/*          → media service
```

Path-based routing is commonly used for microservices. Remember that your application may need to understand the original path or an explicitly configured path transformation.

### HTTP-header routing

Rules can match a named HTTP header and its values.

Example:

```text
X-Application-Version: beta
    → beta target group
```

This is useful for testing internal versions or routing requests carrying a known application header. Do not treat an arbitrary client-supplied header as proof of identity; use authentication and authorization for access control.

### Query-string routing

Rules can match query-string values.

```text
/products?category=books
    → books target group
```

Query-string routing can be useful for specialized routing patterns, but it should not replace normal application-level filtering or authorization.

### Source-IP routing

Rules can match source IPv4 or IPv6 CIDR ranges.

```text
198.51.100.0/24
    → restricted application
```

The source IP condition is based on the client address observed by the ALB, not an arbitrary `X-Forwarded-For` value. When traffic passes through a proxy or CDN, account for the actual network path and avoid relying on source-IP routing alone as an authorization mechanism.

### Fixed-response actions

A fixed response lets the ALB return a status code, content type, and optional body without forwarding the request.

Typical uses include:

* Returning a custom 404 response for unknown routes.

* Temporarily returning a maintenance message.

* Responding with a controlled status code during a migration.

For example, a default rule can return HTTP 404 rather than accidentally forwarding unmatched requests to the frontend.

### 5\. Forwarding to multiple target groups and weighted routing

A forward action can distribute traffic among multiple target groups using configured weights.

Suppose a deployment has two application versions:

* Stable version: weight 90

* New version: weight 10

The ALB uses the configured weights to distribute requests between the target groups. This is useful for canary deployments and gradual traffic migration.

However, weighted forwarding is not the same as session-level stickiness or a strict request-count guarantee. The observed distribution can vary with traffic volume, connection behavior, target health, and stickiness configuration. A weighted rule also does not automatically shift traffic away from an application that returns errors.

Target-group stickiness can be configured when appropriate, but it changes how traffic is distributed across requests from a client. For production deployments, combine weighted forwarding with health checks, monitoring, and an explicit rollback strategy.

### Example weighted-routing rule

```python

import pulumi_aws as aws

# Assumes stable_tg, canary_tg, and https_listener
# have already been created.

canary_rule = aws.lb.ListenerRule(
    "canary-routing",
    listener_arn=https_listener.arn,
    priority=50,
    actions=[{
        "type": "forward",
        "forward": {
            "target_groups": [
                {"arn": stable_tg.arn, "weight": 90},
                {"arn": canary_tg.arn, "weight": 10},
            ],
        },
    }],
    conditions=[{
        "path_pattern": {
            "values": ["/api/*"],
        },
    }],
)
```

This example assumes both target groups already exist and that the HTTPS listener is configured. In a complete Pulumi stack, the rule must also coexist with the other routing rules without duplicate priorities.

### 6\. HTTP/1.1, HTTP/2, gRPC, and WebSockets

The ALB can accept different application protocols, but the listener protocol and target-group protocol version must be compatible.

| Protocol   | Important behavior                                                                                                  |
| ---------- | ------------------------------------------------------------------------------------------------------------------- |
| HTTP/1.1   | Default target protocol version for conventional HTTP applications                                                  |
| HTTP/2     | Supported by ALB HTTPS listeners; can use HTTP/1.1 or HTTP/2 on the backend depending on target-group configuration |
| gRPC       | Requires an HTTPS listener and a compatible HTTP/2 or gRPC target-group protocol version                            |
| WebSockets | Supports HTTP/1.1 connection upgrades over HTTP or HTTPS listeners                                                  |

For HTTP/2 and gRPC, target-group protocol-version configuration matters. For example, a gRPC request cannot be sent successfully to a target group configured for ordinary HTTP/1.1. gRPC target groups also have specific health-check and routing requirements. Elastic Load Balancing +1

WebSockets are useful for persistent, bidirectional communication, such as live notifications, dashboards, and chat applications. Configure the application's idle-connection behavior and keepalive strategy appropriately; a persistent connection is not equivalent to a new HTTP request for every message.

### 7\. ALB attributes, connection behavior, and access logs

The ALB maintains a frontend connection to the client and a separate backend connection to a target. Consequently, the client connection and backend connection do not necessarily use the same protocol. Elastic Load Balancing +1

Important settings include:

* Idle timeout: controls how long a connection can remain idle before being closed.

* HTTP desynchronization mitigation: controls handling of potentially ambiguous HTTP request framing.

* Deletion protection: helps prevent accidental removal of a load balancer.

* Access logs: record request-level information for troubleshooting and analysis.

* Connection logs: provide information about TLS connections, including handshake details.

* Cross-zone load balancing: ALB enables this by default at the load-balancer level; target-group settings can affect behavior.

### Inspecting ALB attributes

```bash
aws elbv2 describe-load-balancer-attributes \
  --load-balancer-arn "$ALB_ARN" \
  --output table
```

### Inspecting listener rules

```bash
aws elbv2 describe-rules \
  --listener-arn "$LISTENER_ARN" \
  --query 'Rules[].{
    Priority:Priority,
    Conditions:Conditions,
    Actions:Actions
  }' \
  --output json
```

### Inspecting listeners

```bash
aws elbv2 describe-listeners \
  --load-balancer-arn "$ALB_ARN" \
  --output table
```

These commands are useful for verifying deployed configuration without relying solely on the AWS console.

### 8\. Hands-on lab — Build an ALB with Pulumi Python

This lab builds a working application with an ALB, two backend services, path-based routing, host-based routing, fixed responses, and an optional weighted canary route.

We'll use the same general environment as Module 1: AWS CLI, Pulumi Python, a Linux/Bash shell, the default VPC, and two subnets in different Availability Zones. The backend instances can be recreated for this lab or reused from Module 1.

### Lab architecture

Internet-facing ALB

HTTP :80 · listener rules

Frontend

`/`

API

`/api/*`

Admin hostname rule

`admin.example.com` → API target group for demonstration

For the initial lab, the backend applications run on EC2 instances in separate subnets. The ALB receives public traffic, while backend security-group rules allow HTTP traffic only from the ALB security group.

> Important: This initial lab uses HTTP to keep the setup self-contained. We will add HTTPS after the core routing works; an HTTPS listener requires an ACM certificate for a domain you control.

### 8.1. Prepare the project

Use Bash in Linux, WSL2, or another compatible shell.

```bash
mkdir aws-lb-module2
cd aws-lb-module2

pulumi new aws-python
```

If you already have the Module 1 project and want to preserve its stack, create a separate project for this lab rather than replacing its configuration.

Install the AWS Python provider if it is not already installed by the project template:

```bash
uv add pulumi pulumi-aws
```

If your project uses a standard Python virtual environment instead of `uv`, install the dependencies using that environment's package manager.

Choose your AWS region and verify credentials:

```bash
pulumi config set aws:region eu-west-2

aws sts get-caller-identity
```

The region above is an example. Use the region from your existing course stack if you want to keep the course resources together.

Find the default VPC:

```bash
VPC_ID=$(aws ec2 describe-vpcs \
  --filters Name=isDefault,Values=true \
  --query 'Vpcs[0].VpcId' \
  --output text)

echo "$VPC_ID"
```

List its subnets and Availability Zones:

```bash
aws ec2 describe-subnets \
  --filters "Name=vpc-id,Values=$VPC_ID" \
  --query 'Subnets[].{Subnet:SubnetId,AZ:AvailabilityZone,Public:MapPublicIpOnLaunch}' \
  --output table
```

Choose two subnets in different Availability Zones. For an internet-facing ALB, use suitable subnets with a route to an internet gateway. The default VPC usually provides public subnets, but verify the route tables and subnet configuration rather than assuming that every subnet is public.

Configure the project:

```bash
pulumi config set vpcId vpc-REPLACE_ME
pulumi config set subnetA subnet-REPLACE_ME_A
pulumi config set subnetB subnet-REPLACE_ME_B
```

Replace the example identifiers with actual values from your account.

### 8.2. Create the ALB and backend resources

Replace the contents of `__main__.py` with the following working baseline. It creates three EC2 backend instances: frontend, API stable, and API canary. The API target groups are used for weighted routing, while host and path rules select the services.

This example deliberately keeps the backend servers simple so you can focus on ALB behavior. It uses the Amazon Linux 2023 AMI published through AWS Systems Manager Parameter Store.

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
subnet_a = config.require("subnetA")
subnet_b = config.require("subnetB")

# Find a current Amazon Linux 2023 AMI in this region.
ami = aws.ssm.get_parameter(
    name="/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
)

# ALB accepts public HTTP traffic.
alb_sg = aws.ec2.SecurityGroup(
    "alb-sg",
    vpc_id=vpc_id,
    description="Allow public HTTP traffic to the ALB",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
            "description": "HTTP from the internet",
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
    tags={"Name": "aws-lb-module2-alb"},
)

# Backend instances accept HTTP only from the ALB.
backend_sg = aws.ec2.SecurityGroup(
    "backend-sg",
    vpc_id=vpc_id,
    description="Allow HTTP only from the ALB",
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "security_groups": [alb_sg.id],
            "description": "HTTP from ALB",
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
    tags={"Name": "aws-lb-module2-backends"},
)

def make_server(name, subnet_id, message):
    # Minimal web server with a health endpoint and service identity.
    script = f"""#!/bin/bash
set -euxo pipefail

cat > /opt/lb-server.py <<'PY'
from http.server import BaseHTTPRequestHandler, HTTPServer
import json

MESSAGE = {message!r}

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            status = 200
            body = {{"status": "healthy", "service": MESSAGE}}
        else:
            status = 200
            body = {{
                "service": MESSAGE,
                "path": self.path,
                "host": self.headers.get("Host"),
                "message": "Request served by ALB backend"
            }}

        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def log_message(self, fmt, *args):
        print(fmt % args, flush=True)

HTTPServer(("0.0.0.0", 80), Handler).serve_forever()
PY

cat > /etc/systemd/system/lb-server.service <<'UNIT'
[Unit]
Description=ALB lab web server
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /opt/lb-server.py
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now lb-server
"""

    return aws.ec2.Instance(
        name,
        ami=ami.value,
        instance_type="t3.micro",
        subnet_id=subnet_id,
        vpc_security_group_ids=[backend_sg.id],
        associate_public_ip_address=True,
        user_data=script,
        user_data_replace_on_change=True,
        metadata_options={
            "http_tokens": "required",
        },
        root_block_device={
            "encrypted": True,
            "volume_type": "gp3",
            "volume_size": 8,
        },
        tags={"Name": name, "Course": "aws-lb-module2"},
    )

frontend = make_server("frontend", subnet_a, "frontend")
api_stable = make_server("api-stable", subnet_b, "api-stable")
api_canary = make_server("api-canary", subnet_a, "api-canary")

# Target groups
frontend_tg = aws.lb.TargetGroup(
    "frontend-tg",
    vpc_id=vpc_id,
    port=80,
    protocol="HTTP",
    target_type="instance",
    health_check={
        "protocol": "HTTP",
        "path": "/health",
        "matcher": "200",
        "interval": 30,
        "timeout": 5,
        "healthy_threshold": 2,
        "unhealthy_threshold": 3,
    },
    tags={"Name": "frontend-tg"},
)

api_stable_tg = aws.lb.TargetGroup(
    "api-stable-tg",
    vpc_id=vpc_id,
    port=80,
    protocol="HTTP",
    target_type="instance",
    health_check={
        "protocol": "HTTP",
        "path": "/health",
        "matcher": "200",
    },
    tags={"Name": "api-stable-tg"},
)

api_canary_tg = aws.lb.TargetGroup(
    "api-canary-tg",
    vpc_id=vpc_id,
    port=80,
    protocol="HTTP",
    target_type="instance",
    health_check={
        "protocol": "HTTP",
        "path": "/health",
        "matcher": "200",
    },
    tags={"Name": "api-canary-tg"},
)

# Register the EC2 instances.
frontend_attachment = aws.lb.TargetGroupAttachment(
    "frontend-attachment",
    target_group_arn=frontend_tg.arn,
    target_id=frontend.id,
    port=80,
)

stable_attachment = aws.lb.TargetGroupAttachment(
    "api-stable-attachment",
    target_group_arn=api_stable_tg.arn,
    target_id=api_stable.id,
    port=80,
)

canary_attachment = aws.lb.TargetGroupAttachment(
    "api-canary-attachment",
    target_group_arn=api_canary_tg.arn,
    target_id=api_canary.id,
    port=80,
)

alb = aws.lb.LoadBalancer(
    "application-alb",
    internal=False,
    load_balancer_type="application",
    security_groups=[alb_sg.id],
    subnets=[subnet_a, subnet_b],
    enable_http2=True,
    idle_timeout=60,
    tags={"Name": "aws-lb-module2"},
)

# Default action: serve the frontend.
http_listener = aws.lb.Listener(
    "http-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[{
        "type": "forward",
        "target_group_arn": frontend_tg.arn,
    }],
)

# Path-based API routing: 90% stable, 10% canary.
api_rule = aws.lb.ListenerRule(
    "api-weighted-rule",
    listener_arn=http_listener.arn,
    priority=10,
    actions=[{
        "type": "forward",
        "forward": {
            "target_groups": [
                {"arn": api_stable_tg.arn, "weight": 90},
                {"arn": api_canary_tg.arn, "weight": 10},
            ],
        },
    }],
    conditions=[{
        "path_pattern": {
            "values": ["/api/*"],
        },
    }],
)

# Host-based rule: admin hostname routes to the API service.
admin_rule = aws.lb.ListenerRule(
    "admin-host-rule",
    listener_arn=http_listener.arn,
    priority=20,
    actions=[{
        "type": "forward",
        "target_group_arn": api_stable_tg.arn,
    }],
    conditions=[{
        "host_header": {
            "values": ["admin.example.com"],
        },
    }],
)

# Explicit fixed response for a maintenance path.
maintenance_rule = aws.lb.ListenerRule(
    "maintenance-rule",
    listener_arn=http_listener.arn,
    priority=30,
    actions=[{
        "type": "fixed-response",
        "fixed_response": {
            "content_type": "text/plain",
            "status_code": "503",
            "message_body": "Service temporarily unavailable",
        },
    }],
    conditions=[{
        "path_pattern": {
            "values": ["/maintenance"],
        },
    }],
)

pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("alb_url", pulumi.Output.concat("http://", alb.dns_name))
pulumi.export("frontend_target_group_arn", frontend_tg.arn)
pulumi.export("api_stable_target_group_arn", api_stable_tg.arn)
pulumi.export("api_canary_target_group_arn", api_canary_tg.arn)
pulumi.export("http_listener_arn", http_listener.arn)
```

The resource definitions use the current Pulumi AWS `aws.lb` resource family. Pulumi Registry +1

A few implementation details matter:

* The backend instances have public IPs for straightforward provisioning, but their security group does not allow direct inbound HTTP from the internet. Only the ALB security group can access port 80.

* The API stable and canary services are separate targets, each with its own target group.

* The `/maintenance` fixed-response rule has a higher priority number than the API rule, so `/api/maintenance` will match the API rule first, whereas `/maintenance` returns HTTP 503.

* The `admin.example.com` rule is for testing the Host header. You do not need to own that domain to test it using `curl`.

* This is a learning deployment, not a complete production architecture. For production, prefer private backend subnets, controlled outbound access, HTTPS, logging, and application deployment automation.

### 8.3. Deploy the stack

Review the planned changes:

```bash
pulumi preview
```

Deploy:

```bash
pulumi up
```

Confirm the deployment when prompted. Once it completes, export the ALB DNS name into your current shell:

```bash
ALB_DNS=$(pulumi stack output alb_dns_name)
echo "$ALB_DNS"
```

Wait for the targets to finish booting and pass health checks. Cloud-init and package startup can take a few minutes.

### 8.4. Test path-based routing

Send a request to the frontend:

```bash
curl -sS "http://$ALB_DNS/"
```

Expected response resembles:

```json
{
  "service": "frontend",
  "path": "/",
  "host": "aws-lb-module2-....elb.eu-west-2.amazonaws.com",
  "message": "Request served by ALB backend"
}
```

Test the API:

```bash
curl -sS "http://$ALB_DNS/api/products"
```

The response should identify either `api-stable` or `api-canary`. Repeat the request to observe weighted routing:

```bash
for i in $(seq 1 20); do
  curl -sS "http://$ALB_DNS/api/products"
  echo
done
```

The canary weight is 10, but twenty requests are too few to expect an exact 18-to-2 split. The purpose is to observe the distribution, not to prove a precise statistical ratio.

### 8.5. Test host-based routing

Send a request with a custom Host header:

```bash
curl -sS \
  -H "Host: admin.example.com" \
  "http://$ALB_DNS/"
```

The response should identify `api-stable`.

This demonstrates an important concept: DNS does not have to resolve the test hostname for ALB host-based routing to work. The ALB evaluates the HTTP `Host` header sent by the client.

### 8.6. Test the fixed response

```bash
curl -i "http://$ALB_DNS/maintenance"
```

Expected result:

```text
HTTP/1.1 503 Service Temporarily Unavailable
Content-Type: text/plain

Service temporarily unavailable
```

The response comes directly from the ALB. The backend application does not generate it.

### 8.7. Inspect target health

Retrieve the target group ARNs from Pulumi:

```bash
FRONTEND_TG=$(pulumi stack output frontend_target_group_arn)
STABLE_TG=$(pulumi stack output api_stable_target_group_arn)
CANARY_TG=$(pulumi stack output api_canary_target_group_arn)
```

Inspect each group:

```bash
for tg in "$FRONTEND_TG" "$STABLE_TG" "$CANARY_TG"; do
  echo "Target group: $tg"

  aws elbv2 describe-target-health \
    --target-group-arn "$tg" \
    --query 'TargetHealthDescriptions[].{
      Target:Target.Id,
      Port:Target.Port,
      State:TargetHealth.State,
      Reason:TargetHealth.Reason
    }' \
    --output table
done
```

All three targets should eventually become `healthy`. If they do not, check the EC2 system log, security groups, the `/health` endpoint, and the target group's health-check reason.

### 8.8. Add HTTP-to-HTTPS redirection

For this extension, first create or identify an ACM certificate for a domain you control and validate it in the same AWS Region as the ALB. Point a DNS record for that domain at the ALB before testing browser access.

Add the certificate ARN to Pulumi configuration:

```bash
pulumi config set certificateArn arn:aws:acm:eu-west-2:123456789012:certificate/REPLACE_ME
```

Then add the following resources to `__main__.py`. Replace the original port-80 listener's default action with a redirect action, and create an HTTPS listener that forwards to the frontend target group.

```python

certificate_arn = config.require("certificateArn")

# Replace the original HTTP listener default action with this:
# default_actions=[{
#     "type": "redirect",
#     "redirect": {
#         "protocol": "HTTPS",
#         "port": "443",
#         "status_code": "HTTP_301",
#     },
# }]

https_listener = aws.lb.Listener(
    "https-listener",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn=certificate_arn,
    ssl_policy="ELBSecurityPolicy-TLS13-1-2-2021-06",
    default_actions=[{
        "type": "forward",
        "target_group_arn": frontend_tg.arn,
    }],
)
```

For this extension, also add an inbound TCP/443 rule to the ALB security group and attach the existing path-based, host-based, and maintenance rules to the HTTPS listener instead of the HTTP listener. Keep port 80 open for redirects.

Because Pulumi manages resources by their logical names, update the existing HTTP listener's action in place rather than declaring a second listener resource with the same name. After making the changes:

```bash
pulumi preview
pulumi up
```

Test both endpoints:

```bash
curl -sSI "http://app.example.com/"
curl -sS "https://app.example.com/api/products"
```

The first request should return a redirect to HTTPS, and the second should reach the API routing rule if the HTTPS listener has been configured with the same rules.

### 8.9. Cleanup

The ALB and EC2 instances incur costs while running. When you finish the lab, destroy its resources:

```bash
pulumi destroy
```

Confirm the operation and verify that the resources have been removed.

### 9\. Troubleshooting guide

| Symptom                           | Likely cause                                          | What to inspect                                      |
| --------------------------------- | ----------------------------------------------------- | ---------------------------------------------------- |
| 503 Service Unavailable           | No eligible healthy targets, or a fixed-response rule | Target health and listener rule priority             |
| 502 Bad Gateway                   | Backend connection or response problem                | Application logs, target port, protocol              |
| 504 Gateway Timeout               | Backend response exceeded the timeout                 | Application latency, network reachability            |
| Request reaches the wrong service | A different rule matched first                        | Rule priorities, conditions, Host header             |
| Target stays unhealthy            | Health endpoint or security group is incorrect        | /health, target port, ALB-to-target ingress          |
| HTTPS fails                       | Certificate, listener, DNS, or port 443 configuration | ACM certificate status, TLS listener, security group |

Useful diagnostic commands:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$FRONTEND_TG" \
  --output json

aws elbv2 describe-rules \
  --listener-arn "$(pulumi stack output http_listener_arn)" \
  --output json

curl -v "http://$ALB_DNS/api/products"
```

For authoritative configuration details, refer to the AWS documentation for [ALB listener rules](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/listener-rules.html?utm_source=chatgpt.com), [target groups](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html?utm_source=chatgpt.com), and the [Pulumi ALB resources](https://www.pulumi.com/registry/packages/aws/api-docs/lb/?utm_source=chatgpt.com).

### 10\. Key takeaways

* The ALB is a Layer 7 load balancer that can route HTTP requests based on hostnames, paths, headers, query strings, and source IP addresses.

* Listeners define entry points; listener rules choose actions; target groups define backend destinations and health checks.

* Rule priorities determine which matching rule runs first, with the default action evaluated last.

* Weighted forwarding is useful for gradual deployments, but it does not guarantee an exact request ratio or automatically provide rollback.

* HTTPS requires a suitable certificate, and backend encryption must be configured separately.

* Pulumi makes the ALB, target groups, listeners, and routing rules repeatable and version-controlled.
