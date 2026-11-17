### AWS Load Balancing — Module 3

### Network Load Balancer (NLB) and Gateway Load Balancer (GWLB)

Level: Intermediate to advanced · Infrastructure as code: Pulumi Python · Commands: Bash

### Learning objectives

By the end of this module, you will understand how AWS Network Load Balancer distributes Layer 4 traffic, when to use static IP addresses, how client IP preservation works, and how TLS termination differs from TCP pass-through. You will also understand how Gateway Load Balancer integrates transparent network appliances into traffic paths.

You will build an NLB-based TCP service, configure TLS termination, inspect target health, and examine a GWLB inspection architecture.

### 1\. Network Load Balancer architecture

An NLB operates primarily at Layer 4 of the OSI model, distributing TCP, UDP, and TLS connections or flows without performing ALB-style HTTP request routing.

Unlike an ALB, an NLB doesn't select targets using URL paths, HTTP headers, or hostnames. It is designed for applications that need low-latency network traffic distribution, high connection rates, static IP addresses, or protocols beyond HTTP.

![Exploring Data Transfer Costs for AWS Network Load Balancers | Networking & Content Delivery](https://images.openai.com/static-rsc-4/Q53_V0rICAaWRfjkNijt6l4ybDbmZ2SiVJRjXwX3CFqS89CoTtSPpKHs2AWI1dzx-iD6_VwC9GoDXVowspgNQkk9Iw0PlAPtt0hFJfbc9V-Nk3rNnT2a3lZxBWlyWLtNrJmcpmpTvaIBT2umNuT3PlAIOLMRlUP2y-C4Upzpe4gG3G_5vGJHr6dYiryMSG6Y?purpose=fullsize)

![AWSのロードバランサ機能・使い分けについて（ALB作成手順付き）｜クラウドテクノロジーブログ｜ソフトバンク](https://images.openai.com/static-rsc-4/zm7WceKheIAYGDpIClbcegieawzecaoR8yOZ70XxWl87y_JiywKXyXlpHhRkE5iYjg0kDn2dmwqCNjYYIglfhxnluB5DBtIgqqFSuLcX3RSyPIrfENLq2Jd2k7NHclmx_q-WUuOOYvfjMq1FKsWlQr48DskYOB1pszkgsBXXXJfooUh-8Uf0tOXGGA6jcpAL?purpose=fullsize)

![AWS Elastic Load Balancer Demos](https://images.openai.com/static-rsc-4/tQWf6ATLu5pcBMQ352Y31PLBvhcVDcXMKEbf7Ar578fqthMhm1mqy61cjgfacKG7kpzVD3hFHj9nZ1cwA4HdfggkVBRPwijz5S6mtdm2BFIuNlsqxcJEQI5btN9gbaoY6VAe-WMlTaO_gfMIl3tLiYo11sRkIvKC6HKuzvYFYTQ10SxrODdgctLalrK5K01Q?purpose=fullsize)

### Core components

* NLB: The regional load-balancing resource that receives client traffic.

* Listener: Defines a protocol and port, such as TCP port 9000 or TLS port 443.

* Target group: Defines the destinations receiving traffic and the health-check configuration.

* Targets: EC2 instances, private IP addresses, or supported Application Load Balancers, depending on the target-group type and configuration.

* Health checks: Determine whether targets are eligible to receive new traffic.

* Availability Zones: Provide zonal endpoints and distribute traffic across configured zones.

A typical traffic flow is:

* A client connects to the NLB's DNS name or an assigned static IP address.

* The NLB accepts traffic on a configured listener.

* The listener forwards traffic to its target group.

* The NLB distributes traffic among eligible targets.

* Health checks continuously evaluate target availability.

The NLB does not need to inspect HTTP request paths to perform this selection. That makes it suitable for TCP services, databases, custom protocols, and certain high-performance network workloads.

### NLB versus ALB

| Capability               | NLB                                                   | ALB                                             |
| ------------------------ | ----------------------------------------------------- | ----------------------------------------------- |
| Primary layer            | Layer 4                                               | Layer 7                                         |
| TCP/UDP traffic          | Yes, with protocol-specific listeners                 | Not as a general TCP/UDP proxy                  |
| HTTP path routing        | No                                                    | Yes                                             |
| Static IP per enabled AZ | Supported                                             | Not directly provided as a fixed per-AZ address |
| Elastic IP association   | Supported for eligible internet-facing configurations | Not directly associated with ALB nodes          |
| TLS termination          | Supported                                             | Supported                                       |
| Client IP handling       | Network-level behavior                                | HTTP headers such as X-Forwarded-For            |
| Typical use              | TCP/UDP, static IPs, high-performance networking      | Web applications, APIs, HTTP routing            |

A key distinction: an NLB can forward TCP traffic without interpreting HTTP semantics, even when the TCP payload happens to contain HTTP.

### 2\. Listeners: TCP, TLS, and UDP

NLB listeners define the protocol and port on which the load balancer accepts traffic. The selected listener protocol determines whether the NLB terminates TLS or forwards encrypted traffic without terminating it.

| Listener | Behavior                                                   | Typical use                                         |
| -------- | ---------------------------------------------------------- | --------------------------------------------------- |
| TCP      | Forwards TCP traffic without TLS termination               | Custom TCP protocols, encrypted application traffic |
| TLS      | Terminates TLS at the NLB, then forwards to a target group | Centralized certificate management                  |
| UDP      | Distributes UDP flows                                      | DNS, gaming, real-time applications                 |
| TCP_UDP  | Supports both TCP and UDP on the same port                 | Services using both transport protocols             |

TLS listeners require a server certificate, typically provisioned or imported through AWS Certificate Manager (ACM). UDP and TCP_UDP listeners do not perform TLS termination.

### TLS termination versus TCP pass-through

### Option A — TLS termination at the NLB

Client

HTTPS / TLS

NLB TLS listener

Presents certificate and decrypts traffic

Backend target

Usually receives plaintext TCP; encryption can be added separately

### Option B — TCP pass-through

Client

TLS-encrypted connection

NLB TCP listener

Forwards encrypted TCP traffic without decrypting it

Backend target

Terminates TLS and presents its own certificate

Use TLS termination when you want centralized certificate handling at the load balancer. Use TCP pass-through when the application must terminate TLS itself, or when the backend requires control over the TLS session.

Important: TLS termination at the NLB does not automatically encrypt the connection to the backend. If encryption is required end to end, configure TLS at the backend as well and choose an appropriate target-group protocol.

### 3\. Static IP addresses, Elastic IPs, and zonal endpoints

A major NLB advantage is its ability to provide stable network endpoints.

An internet-facing NLB can use a static IP address for each enabled Availability Zone. You can also associate an Elastic IP address with each enabled zone when configuring an eligible IPv4 NLB. This is useful when clients, partners, or external firewalls require IP allowlisting.

### Regional DNS versus zonal DNS

* Regional DNS name: Resolves to the NLB's available addresses across its enabled zones.

* Zonal DNS name: Identifies a specific Availability Zone endpoint.

* Elastic IP: Provides a static public IPv4 address associated with an eligible zonal NLB endpoint.

* Internal NLB: Uses private addresses for internal connectivity.

For example, an application might expose a regional endpoint such as `my-service.example.com`, with Route 53 pointing to the NLB's AWS DNS name. Clients do not need to know the individual backend addresses.

### When static IPs matter

Static NLB addresses are particularly useful for:

* Partner integrations that require source or destination IP allowlisting.

* Legacy TCP services that cannot use HTTP-aware routing.

* Hybrid environments connecting on-premises systems to AWS.

* Services that require predictable network endpoints.

Remember that a static frontend IP does not make the backend target addresses static. Targets can still be replaced, scaled, or registered dynamically.

### 4\. Client IP preservation and Proxy Protocol v2

Source IP handling is one of the most important NLB concepts to understand correctly.

When a client connects through an NLB, the backend may see the original client address or an address associated with the load balancer. The result depends on the target type, target-group protocol, network topology, and configuration. Elastic Load Balancing +1

### Client IP preservation

For supported target groups, the `preserve_client_ip.enabled` attribute controls whether the original client IP is preserved.

* Instance-type TCP target groups generally preserve the client IP by default.

* IP-type TCP and TLS target groups have client IP preservation disabled by default.

* UDP and TCP_UDP target groups preserve client IP by default, and this cannot be disabled.

* PrivateLink traffic and some address-family translation scenarios have special behavior.

Always verify the defaults for the exact target-group configuration you deploy. Elastic Load Balancing +1

### Proxy Protocol v2

Proxy Protocol v2 is a binary header that carries connection metadata, including source and destination addresses. It is useful when the backend cannot obtain the original client IP from the network connection itself.

However, enabling it changes what the backend receives: the application or protocol server must understand the header before processing its normal payload. An ordinary HTTP server or custom TCP service may fail if it expects application data immediately. Health-check connections can also include this header when Proxy Protocol v2 is enabled. Elastic Load Balancing +1

Example: inspect a target group's attributes with Bash and the AWS CLI.

```bash
export AWS_REGION="eu-west-2"
export TARGET_GROUP_ARN="arn:aws:elasticloadbalancing:..."

aws elbv2 describe-target-group-attributes \
  --region "$AWS_REGION" \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --query 'Attributes[?Key==`preserve_client_ip.enabled` || Key==`proxy_protocol_v2.enabled` || Key==`load_balancing.cross_zone.enabled`]' \
  --output table
```

Use the actual target-group ARN from your deployment.

Practical rule: Use client IP preservation when the network path supports it. Use Proxy Protocol v2 when you need connection metadata and the backend explicitly supports it. Do not enable both blindly without understanding how your application interprets the incoming connection.

### 5\. Target groups, health checks, and cross-zone load balancing

NLB target groups support instance and IP targets, and also support ALB targets in supported configurations. The target-group protocol determines how traffic is forwarded to those targets. Elastic Load Balancing

### Health-check configuration

A target group can use TCP, HTTP, or HTTPS health checks, subject to the supported listener and target-group configuration.

* TCP health check: Tests whether a TCP connection can be established.

* HTTP health check: Checks whether an application endpoint responds with an acceptable status.

* HTTPS health check: Checks an endpoint over TLS.

For application services, an HTTP health endpoint can provide a more meaningful signal than a TCP port alone. A port might accept connections while the application is unable to serve requests.

### Cross-zone load balancing

Cross-zone load balancing determines whether an NLB node can distribute traffic to healthy targets in other enabled Availability Zones.

With cross-zone balancing disabled, traffic handled by a zonal NLB node is distributed among targets in that zone. With it enabled, the node can distribute traffic across the enabled zones.

This has important operational implications:

* Uneven target counts can create uneven load when cross-zone balancing is disabled.

* Cross-zone balancing can improve distribution when client traffic is uneven across zones.

* Cross-zone traffic can affect data-transfer costs.

* Zonal failure behavior and health-based DNS failover should be designed and tested deliberately.

NLB cross-zone balancing is disabled by default at the load-balancer level, unless overridden by the applicable configuration. Elastic Load Balancing +1

### 6\. Lab 1 — Provision an NLB using Pulumi Python

Hands-on lab

### Architecture

For this lab, deploy an internet-facing NLB across two public subnets and forward TCP traffic to two existing EC2 instances running a TCP service on port `8080`.

Client

TCP connection to port 9000

Network Load Balancer

TCP listener · Port 9000

EC2 · AZ A

TCP :8080

EC2 · AZ B

TCP :8080

### Prerequisites

You need:

* An AWS account with permissions to create ELB resources and update security groups.

* A VPC with two suitable subnets in different Availability Zones.

* Two running EC2 instances with a TCP service listening on port `8080`.

* A security group attached to those instances.

* AWS CLI credentials and Pulumi configured.

Use a dedicated lab environment. The following code assumes your EC2 instances and their security group already exist.

### Step 1 — Create the Pulumi project

```bash
mkdir aws-nlb-lab
cd aws-nlb-lab

pulumi new aws-python
```

Install dependencies if necessary:

```bash
uv add pulumi pulumi-aws
```

Configure the AWS region:

```bash
pulumi config set aws:region eu-west-2
```

Replace the example region with your preferred AWS region.

### Step 2 — Configure the environment

Set the following Pulumi configuration values using the IDs of your existing resources:

```bash
pulumi config set vpcId vpc-0123456789abcdef0
pulumi config set subnetA subnet-0123456789abcdef0
pulumi config set subnetB subnet-0abcdef0123456789
pulumi config set instanceA i-0123456789abcdef0
pulumi config set instanceB i-0abcdef0123456789
pulumi config set backendSecurityGroup sg-0123456789abcdef0
```

These IDs are illustrative placeholders. Replace them with real IDs from your AWS account.

### Step 3 — Define the NLB resources

Create or replace `__main__.py` with the following program.

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
subnet_a = config.require("subnetA")
subnet_b = config.require("subnetB")
instance_a = config.require("instanceA")
instance_b = config.require("instanceB")
backend_sg_id = config.require("backendSecurityGroup")

# NLB security group: allow inbound TCP on port 9000.
nlb_sg = aws.ec2.SecurityGroup(
    "nlb-security-group",
    description="Allow lab TCP traffic to NLB",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=9000,
            to_port=9000,
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

# Internet-facing NLB.
nlb = aws.lb.LoadBalancer(
    "tcp-nlb",
    load_balancer_type="network",
    internal=False,
    subnets=[subnet_a, subnet_b],
    security_groups=[nlb_sg.id],
    enable_cross_zone_load_balancing=True,
)

# TCP backend target group.
target_group = aws.lb.TargetGroup(
    "tcp-target-group",
    port=8080,
    protocol="TCP",
    target_type="instance",
    vpc_id=vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        protocol="TCP",
        port="traffic-port",
        interval=30,
    ),
)

# Register existing EC2 instances.
target_a = aws.lb.TargetGroupAttachment(
    "target-a",
    target_group_arn=target_group.arn,
    target_id=instance_a,
    port=8080,
)

target_b = aws.lb.TargetGroupAttachment(
    "target-b",
    target_group_arn=target_group.arn,
    target_id=instance_b,
    port=8080,
)

# TCP listener.
listener = aws.lb.Listener(
    "tcp-listener",
    load_balancer_arn=nlb.arn,
    port=9000,
    protocol="TCP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        )
    ],
)

pulumi.export("nlb_dns_name", nlb.dns_name)
pulumi.export("target_group_arn", target_group.arn)
pulumi.export("listener_port", listener.port)
```

Security note: The NLB security group permits traffic from all IPv4 addresses for this lab. For production, restrict the allowed source ranges where possible. You must also configure the backend security group to allow port `8080` from the intended traffic sources. If you intend to restrict traffic to the NLB security group, verify the NLB security-group reference and client-IP-preservation behavior for your chosen target configuration.

### Step 4 — Deploy

Preview the infrastructure changes:

```bash
pulumi preview
```

Deploy:

```bash
pulumi up
```

After confirming the proposed changes, Pulumi creates the NLB, target group, listener, and target registrations.

Retrieve the DNS name:

```bash
pulumi stack output nlb_dns_name
```

### Step 5 — Validate TCP connectivity

```bash
NLB_DNS="$(pulumi stack output nlb_dns_name)"

nc -vz "$NLB_DNS" 9000
```

If your application uses a text-based TCP protocol, you can also connect interactively:

```bash
nc "$NLB_DNS" 9000
```

A successful TCP handshake demonstrates network reachability, but it does not prove that the application protocol itself is functioning correctly.

### Step 6 — Inspect target health

```bash
TARGET_GROUP_ARN="$(pulumi stack output target_group_arn)"

aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --query 'TargetHealthDescriptions[].{Instance:Target.Id,Port:Target.Port,State:TargetHealth.State,Reason:TargetHealth.Reason}' \
  --output table
```

Both targets should eventually report `healthy` if the service is listening, network access is correct, and health checks succeed.

### Troubleshooting checklist

* Confirm that the EC2 service listens on `0.0.0.0:8080` or the appropriate instance interface, rather than only `127.0.0.1`.

* Verify backend security-group rules and subnet network ACLs.

* Confirm both instances belong to the configured VPC.

* Check target health reason codes.

* Check whether the application protocol requires a specific handshake before sending data.

* Inspect the NLB listener and target group in the AWS console if the TCP connection fails.

### 7\. Lab 2 — Configure TCP and TLS listeners

### A. TCP pass-through on port 443

If your backend service terminates TLS itself, add a TCP listener on port `443` that forwards encrypted bytes to the target group.

```python
tls_passthrough_listener = aws.lb.Listener(
    "tcp-443-passthrough",
    load_balancer_arn=nlb.arn,
    port=443,
    protocol="TCP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        )
    ],
)
```

This reuses the existing target group on port `8080`. Your application must actually speak TLS on that backend port for an HTTPS-style connection to succeed.

### B. TLS termination at the NLB

For TLS termination, create a target group and listener that explicitly use the desired TLS configuration.

First, configure a certificate ARN for an ACM certificate in the same AWS Region as your NLB:

```bash
pulumi config set certificateArn \
  arn:aws:acm:eu-west-2:123456789012:certificate/REPLACE-ME
```

Then add the following to the Pulumi program:

```python
certificate_arn = config.require("certificateArn")

tls_target_group = aws.lb.TargetGroup(
    "tls-backend-target-group",
    port=8080,
    protocol="TCP",
    target_type="instance",
    vpc_id=vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        protocol="TCP",
        port="traffic-port",
    ),
)

tls_target_a = aws.lb.TargetGroupAttachment(
    "tls-target-a",
    target_group_arn=tls_target_group.arn,
    target_id=instance_a,
    port=8080,
)

tls_target_b = aws.lb.TargetGroupAttachment(
    "tls-target-b",
    target_group_arn=tls_target_group.arn,
    target_id=instance_b,
    port=8080,
)

tls_listener = aws.lb.Listener(
    "tls-listener",
    load_balancer_arn=nlb.arn,
    port=443,
    protocol="TLS",
    certificate_arn=certificate_arn,
    ssl_policy="ELBSecurityPolicy-TLS13-1-2-Res-2021-06",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=tls_target_group.arn,
        )
    ],
)
```

The backend receives ordinary TCP traffic after the NLB decrypts the client connection. If the backend application expects TLS, configure a TLS target-group protocol instead, and ensure the backend supports TLS. NLB does not validate the certificates presented by targets in a TLS target group. Elastic Load Balancing +1

For the example above, the certificate must be valid for the DNS hostname you use, and the DNS record must point to the NLB.

### C. Validate the TLS endpoint

```bash
NLB_DNS="$(pulumi stack output nlb_dns_name)"

openssl s_client \
  -connect "${NLB_DNS}:443" \
  -servername app.example.com \
  -brief
```

Replace `app.example.com` with a hostname covered by your certificate. A certificate or hostname validation error can occur if you use the automatically assigned NLB DNS name instead of your own certificate hostname.

You can also inspect the HTTPS response:

```bash
curl -v https://app.example.com/
```

For TLS pass-through, the backend must terminate TLS. For a TLS listener, the NLB terminates the client connection. These are different configurations, not interchangeable listener settings. Elastic Load Balancing +1

### 8\. Lab 3 — Test client IP preservation and target health

Use this lab to understand what the backend sees when requests pass through the NLB.

### Step 1 — Inspect the target group

```bash
aws elbv2 describe-target-groups \
  --region eu-west-2 \
  --query 'TargetGroups[].{Name:TargetGroupName,Protocol:Protocol,Port:Port,Type:TargetType}' \
  --output table
```

Then inspect the relevant target group's attributes:

```bash
aws elbv2 describe-target-group-attributes \
  --region eu-west-2 \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --output table
```

### Step 2 — Compare client IP behavior

Use the following cases as your reference:

| Configuration                            | Expected source-IP behavior                      |
| ---------------------------------------- | ------------------------------------------------ |
| Instance target, TCP                     | Original client IP normally preserved            |
| IP target, TCP                           | Preservation disabled by default                 |
| IP target, TCP with preservation enabled | Original client IP preserved when supported      |
| Proxy Protocol v2 enabled                | Connection metadata delivered in a binary header |

Actual behavior depends on the target-group configuration and network path. Elastic Load Balancing +1

To enable preservation on a compatible IP target group:

```bash
aws elbv2 modify-target-group-attributes \
  --region eu-west-2 \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --attributes Key=preserve_client_ip.enabled,Value=true
```

To enable Proxy Protocol v2 instead, first ensure that the backend can parse it:

```bash
aws elbv2 modify-target-group-attributes \
  --region eu-west-2 \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --attributes Key=proxy_protocol_v2.enabled,Value=true
```

Do not enable Proxy Protocol v2 for an ordinary application that does not support it. The additional header can cause application connections and health checks to fail. Elastic Load Balancing +1

### Step 3 — Observe target health during failure

Check health continuously:

```bash
watch -n 5 \
  "aws elbv2 describe-target-health \
    --region eu-west-2 \
    --target-group-arn '$TARGET_GROUP_ARN' \
    --query 'TargetHealthDescriptions[].{ID:Target.Id,State:TargetHealth.State,Reason:TargetHealth.Reason}' \
    --output table"
```

On systems without `watch`, run the AWS CLI command repeatedly.

In a controlled lab, stop the backend service on one instance and observe its target state. Restore the service and watch the target return to healthy after successful checks.

What you should learn: NLB target health is not a guarantee that your application can process every request. It is a signal based on the configured health-check behavior.

### 9\. Gateway Load Balancer (GWLB) architecture

A Gateway Load Balancer is designed for a different problem than NLB: inserting and scaling network appliances transparently in a traffic path.

Typical appliances include:

* Next-generation firewalls.

* Intrusion detection and prevention systems (IDS/IPS).

* Deep packet inspection systems.

* Network traffic analysis appliances.

* Virtual network security appliances.

GWLB operates at Layer 3 and forwards IP packets to virtual appliances using GENEVE encapsulation over UDP port `6081`. It maintains flow stickiness so packets belonging to the same flow are directed to the appropriate appliance. Elastic Load Balancing +1

![Getting started with Gateway Load Balancers using the AWS CLI - Elastic Load Balancing](https://images.openai.com/static-rsc-4/mjnfmcMKgOuA9jJOH3RinHr5LZfXh50Ld_2hptUAmjJZ_pJiR7QiZkrq60fJUAA41mt93l-Roe55gsB7DZHoubfZb6pdHfBZIpBYluSBFD47GqX7qGPL4F9dXc3tNaLUmlguo9-cUCkIFtNlbCAFIGHsWEX6szseGKpr2AkXWgYTrlyAvkdxmurFRC-TNNr0?purpose=fullsize)

![Integrate your custom logic or appliance with AWS Gateway Load Balancer | Networking & Content Delivery](https://images.openai.com/static-rsc-4/rOppK4edgW3-rjAHqKOx66Ru5PIcqige6zXDqYwlcohm9fLeQgM6CQ-rSXr8FANm6E2aOVS_B23X7Y5SwiDsDJlKxFxVrrjCsV5r9tsEMEh5NuV_Lmk0Xm7uvTfFen15INHmAHUbWbOhN-vMjCth5Nj3e77zvca1GWCbGueXLWnPVyHfIlwBBKwViSTqjrJw?purpose=fullsize)

![Scaling network traffic inspection using AWS Gateway Load Balancer | Networking & Content Delivery](https://images.openai.com/static-rsc-4/5GM_mx8GZ3NZyzH3H4LfFlcNIAVtHR1iDJfpiZY2_xq3xBNGzUsDyeYBfoT5jEhu6V4wwSc9WQRIFmQyiMG8_PAZhhLUEHktwWtmVnmNY98PkMEZWs5hTWgZ2ry5WrgcsM10NZsivpf7TRSoFbTy1Fo8XbrnkRvo971k_ewvaFAV7yhE-DVQhAmDxG8kIgF_?purpose=fullsize)

### GWLB components

* Gateway Load Balancer: Distributes traffic across healthy appliance targets.

* Appliance target group: Registers virtual appliances using instance or IP targets.

* Gateway Load Balancer endpoint (GWLBe): Provides private connectivity to the GWLB service across VPC boundaries.

* Route tables: Direct selected traffic through the endpoint so that inspection cannot be bypassed accidentally.

* GENEVE: Encapsulates the original IP packet for delivery to an appliance.

### How traffic inspection works

* An application subnet sends traffic toward a destination.

* Its route table directs that traffic through a GWLB endpoint.

* The GWLB forwards the encapsulated traffic to a healthy appliance.

* The appliance decapsulates and inspects the original packet.

* The appliance returns the packet through the intended inspection path.

* Routing delivers the traffic to its destination.

The exact routing configuration depends on whether you deploy the appliances in the application VPC or in a centralized inspection VPC.

Critical design consideration: Both directions of a flow must traverse the intended inspection path consistently. Asymmetric routing can break inspection and reduce performance. GWLB encapsulation also introduces MTU considerations; the GWLB data plane supports packets up to 8,500 bytes, and appliances must accommodate the additional encapsulation overhead. GitHub +1

### 10\. Lab 4 — Design a conceptual GWLB inspection architecture

This lab focuses on architecture and routing rather than deploying a commercial firewall appliance. A full deployment requires a GENEVE-compatible appliance and appropriate licensing or software.

Application VPC

Private application subnet

GWLB endpoint

Traffic steering through VPC route tables

Centralized inspection VPC

GWLB → GENEVE → firewall appliance fleet

Destination

Internet, on-premises network, or another VPC

### Step 1 — Identify the routing requirements

Document the following before creating resources:

* Application VPC CIDR and subnet CIDRs.

* Inspection VPC CIDR and appliance subnets.

* Availability Zones used by both VPCs.

* Which destinations require inspection.

* The forward and return routes for each traffic flow.

* The location of GWLB endpoints and the GWLB service.

* The appliance health-check and failover behavior.

### Step 2 — Map the AWS resources

A production design generally includes:

* A GWLB in the inspection VPC.

* A GENEVE target group on port `6081`.

* Healthy appliance instances or IP targets.

* A GWLB endpoint service and consumer endpoint where cross-VPC connectivity is required.

* Route-table entries that steer selected traffic through the endpoint.

* Security controls and monitoring for the appliance fleet.

### Step 3 — Inspect routes with Bash

Use the AWS CLI to list route tables:

```bash
aws ec2 describe-route-tables \
  --region eu-west-2 \
  --query 'RouteTables[].{RouteTable:RouteTableId,VPC:VpcId,Routes:Routes}' \
  --output json
```

Inspect VPC endpoints:

```bash
aws ec2 describe-vpc-endpoints \
  --region eu-west-2 \
  --query 'VpcEndpoints[].{ID:VpcEndpointId,Type:VpcEndpointType,State:State,VPC:VpcId,Service:ServiceName}' \
  --output table
```

Inspect GWLB resources:

```bash
aws elbv2 describe-load-balancers \
  --region eu-west-2 \
  --query 'LoadBalancers[?Type==`gateway`].{Name:LoadBalancerName,State:State.Code,DNS:DNSName}' \
  --output table
```

These commands help you discover the current architecture. They do not create the resources or validate the complete bidirectional routing design.

### Step 4 — Define the Pulumi implementation plan

When implementing the design in Pulumi Python, organize the infrastructure into reusable components:

* `InspectionVpc`: VPC, subnets, and routing.

* `FirewallFleet`: appliance instances and security configuration.

* `GatewayLoadBalancer`: GWLB, target group, and listeners.

* `InspectionEndpoints`: endpoint service, endpoint connections, and route-table associations.

* `TrafficSteering`: forward and return routes.

For a real deployment, explicitly model route dependencies and validate every intended flow. Avoid applying a generic route-table configuration without first accounting for the topology and return paths.

### 11\. Choosing between ALB, NLB, and GWLB

| Requirement                            | Best starting point                                              | Reason                                                |
| -------------------------------------- | ---------------------------------------------------------------- | ----------------------------------------------------- |
| HTTP APIs with path routing            | ALB                                                              | Understands HTTP requests                             |
| TCP service with static public IPs     | NLB                                                              | Supports Layer 4 traffic and stable zonal addresses   |
| UDP application                        | NLB                                                              | Supports UDP listeners                                |
| TLS termination for TCP-based services | NLB                                                              | Supports TLS listeners and certificate configuration  |
| Backend must terminate TLS             | NLB with TCP listener                                            | Passes encrypted TCP traffic through                  |
| Transparent firewall inspection        | GWLB                                                             | Designed for scalable appliance insertion             |
| HTTP-aware web protection              | ALB with AWS WAF                                                 | Combines application-layer routing with web filtering |
| Global application entry points        | Route 53 or Global Accelerator with an appropriate load balancer | Adds global traffic management                        |

For ordinary websites and REST APIs, start with ALB. Choose NLB when the protocol, static IP, or Layer 4 requirements justify it. Choose GWLB when the core requirement is transparent network traffic inspection rather than application request routing.

### 12\. Lab cleanup

Load balancers and related resources can incur charges while they exist. Remove the lab resources when you have finished testing.

If all resources in the Pulumi stack belong to this lab:

```bash
pulumi destroy
```

Review the proposed deletions and confirm the operation. This removes resources managed by the stack, but it does not delete the pre-existing EC2 instances, their security group, or other infrastructure created outside the stack.

### Module 3 — Key takeaways

* NLB provides Layer 4 load balancing for TCP, TLS, UDP, and supported additional transport protocols.

* Static zonal IP addresses are valuable for allowlisting and predictable connectivity.

* Client IP preservation and Proxy Protocol v2 solve different source-address visibility problems.

* Health checks and cross-zone balancing are essential parts of availability design.

* TLS listeners terminate TLS; TCP listeners can pass encrypted traffic to backend targets.

* GWLB uses GENEVE encapsulation to distribute traffic across network appliances.

* GWLB inspection depends on correct routing, symmetric traffic paths, and MTU planning.

* Pulumi makes these resources reproducible, reviewable, and easier to manage as infrastructure code.

### Official documentation

* AWS Network Load Balancer — [Architecture and concepts](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/introduction.html?utm_source=chatgpt.com)

* [NLB listeners](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/load-balancer-listeners.html?utm_source=chatgpt.com)

* [Target-group attributes and Proxy Protocol v2](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/edit-target-group-attributes.html?utm_source=chatgpt.com)

* AWS Gateway Load Balancer — [GWLB documentation](https://docs.aws.amazon.com/elasticloadbalancing/latest/gateway/gateway-load-balancers.html?utm_source=chatgpt.com)

* [Pulumi AWS load-balancer resources](https://www.pulumi.com/registry/packages/aws/api-docs/lb/?utm_source=chatgpt.com)

7

8

7

8
