### Module 16 — Capstone Production Architecture

AWS VPC Engineering Course · Final Module · Pulumi Python · Production-oriented SaaS networking

In this capstone, we'll bring together the networking concepts from Modules 1–15 to design a realistic, secure, multi-environment AWS network for a SaaS application.

The goal isn't simply to create a VPC. It's to build an infrastructure project that can be deployed, reviewed, secured, troubleshot, and safely operated through infrastructure as code and CI/CD.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Design isolated development, staging, and production environments.

* Build multi-AZ networks with public, private application, and isolated database subnets.

* Configure an Application Load Balancer (ALB) without exposing application servers or databases publicly.

* Control outbound traffic using NAT gateways and private AWS service endpoints.

* Enforce least-privilege access through security groups, route tables, and IAM.

* Implement the architecture using reusable Pulumi Python code.

* Deploy through GitHub Actions using short-lived AWS credentials via OIDC.

* Verify network paths, diagnose failure scenarios, estimate costs, and clean up safely.

### 2\. Architecture and design decisions

We'll model a SaaS platform with a web API, a relational database, centralized operational logging, and three isolated environments.

### High-level architecture

Internet clients

HTTPS · TCP 443

Public ingress

Public subnets · AZ-a and AZ-b

Internet-facing Application Load Balancer

TLS termination · health checks

Private application subnets · AZ-a and AZ-b

API workload A

No public IP

API workload B

No public IP

Isolated database subnets · AZ-a and AZ-b

Amazon RDS PostgreSQL

Private endpoint · Multi-AZ deployment

Supporting network services

Controlled egress

AZ-local NAT gateways and explicit routes

Private AWS access

S3 gateway and selected interface endpoints

Private DNS

Route 53 private hosted zones where needed

Centralized logging

VPC Flow Logs and CloudWatch Logs

This architecture is a reference design for the capstone. The implementation below starts with the reusable VPC network and its security boundaries; the application, database, and CI/CD integrations are developed as separate layers so the network can be reviewed independently.

### 3\. Environment isolation and IP addressing

For a serious SaaS platform, the preferred production pattern is separate AWS accounts for development, staging, and production, managed through AWS Organizations. This reduces the blast radius of compromised credentials and accidental changes.

For a learning lab, we can use three separate Pulumi stacks in one AWS account. This demonstrates stack separation, but it is not equivalent to account-level security isolation.

### Environment plan

| Environment | VPC CIDR     | Purpose                         |
| ----------- | ------------ | ------------------------------- |
| Development | 10.10.0.0/16 | Rapid iteration and integration |
| Staging     | 10.20.0.0/16 | Release validation              |
| Production  | 10.30.0.0/16 | Customer-facing workloads       |

Each environment uses the same subnet layout with different CIDRs.

| Subnet tier         | AZ-a        | AZ-b        | Routing                   |
| ------------------- | ----------- | ----------- | ------------------------- |
| Public ingress      | x.10.0.0/24 | x.10.1.0/24 | Internet gateway          |
| Private application | x.20.0.0/24 | x.20.1.0/24 | AZ-local NAT, S3 endpoint |
| Isolated database   | x.30.0.0/24 | x.30.1.0/24 | VPC-local routes only     |

Here, `x` is `10.10`, `10.20`, or `10.30`, depending on the environment. For example, production's first public subnet is `10.30.10.0/24`.

The database tier has no default route to the internet or NAT. It can still communicate with other resources through the VPC's automatically created local route, subject to security rules.

### 4\. Traffic paths and routing decisions

### Inbound request

Client → Internet Gateway → Public ALB

ALB security group → Application security group

Application → Database security group → RDS PostgreSQL

Only the ALB accepts public HTTPS. The application accepts its application port from the ALB security group, and the database accepts PostgreSQL traffic only from the application security group.

### Outbound request

Application subnet

S3

Gateway endpoint route

External APIs

NAT gateway → internet gateway

The S3 gateway endpoint provides a private routing path without NAT processing for matching S3 traffic. NAT provides outbound IPv4 connectivity but does not allow unsolicited inbound connections to the private workloads.

These route-table choices are explicit, rather than relying on implicit subnet associations. AWS evaluates routes using longest-prefix matching, so an S3 prefix-list route can take precedence over a general IPv4 default route.

### 5\. Pulumi project structure

We'll implement a reusable network component that creates the VPC, subnets, route tables, NAT gateways, S3 gateway endpoint, security groups, and VPC Flow Logs.

The application and database tiers are separate deployment layers. This separation lets you review and deploy networking without automatically provisioning a customer database or application compute.

```text
saas-network/
├── Pulumi.yaml
├── requirements.txt
├── __main__.py
├── Pulumi.dev.yaml
├── Pulumi.staging.yaml
├── Pulumi.prod.yaml
└── .github/
    └── workflows/
        └── network.yml
```

### `Pulumi.yaml`

```yaml
name: saas-network
runtime:
  name: python
  options:
    virtualenv: venv
description: Multi-AZ SaaS network capstone
```

### `requirements.txt`

```text
pulumi>=3.0.0,<4.0.0
pulumi-aws>=7.0.0,<8.0.0
```

These are major-version compatibility ranges, not a guarantee that the newest provider release is suitable for every project. Resolve and commit exact dependency versions for reproducible deployments.

### Environment configuration

`Pulumi.dev.yaml`:

```yaml
config:
  aws:region: eu-west-3
  saas-network:environment: dev
  saas-network:vpcCidr: 10.10.0.0/16
  saas-network:availabilityZones: 2
```

`Pulumi.staging.yaml` uses `staging` and `10.20.0.0/16`. `Pulumi.prod.yaml` uses `prod` and `10.30.0.0/16`.

The `eu-west-3` region is an example; verify service availability and your own deployment region before running the lab.

### 6\. Implement the network using Pulumi Python

The following implementation is a reusable foundation. It creates two public subnets, two application subnets, and two isolated database subnets. Each application subnet has an AZ-local NAT route for outbound IPv4 connectivity.

For cost control, the development stack can use one NAT gateway, but the code below uses two for every environment to keep the architecture consistent. We'll discuss the cheaper development variant in the cost section.

### `__main__.py`

```python

import ipaddress

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

environment = config.require("environment")
vpc_cidr = config.require("vpcCidr")
az_count = config.get_int("availabilityZones") or 2

if environment not in {"dev", "staging", "prod"}:
    raise ValueError("environment must be dev, staging, or prod")

if az_count != 2:
    raise ValueError("This capstone implementation requires two AZs")

network = ipaddress.ip_network(vpc_cidr)
if not network.is_private or network.prefixlen > 16:
    raise ValueError("Use a private VPC CIDR of /16 or larger")

azs = aws.get_availability_zones(
    state="available",
).names[:az_count]

if len(azs) != az_count:
    raise ValueError("Not enough available AZs in this region")

tags = {
    "Project": "saas-platform",
    "Environment": environment,
    "ManagedBy": "Pulumi",
}

def subnet_cidr(third_octet: int, fourth_octet: int) -> str:
    # This capstone assumes a /16 VPC aligned on a /16 boundary.
    base = int(network.network_address)
    address = base + (third_octet << 16) + (fourth_octet << 8)
    return str(ipaddress.ip_network((address, 24)))

if network.prefixlen != 16:
    raise ValueError("This subnet plan requires a /16 VPC CIDR")

vpc = aws.ec2.Vpc(
    f"saas-{environment}-vpc",
    cidr_block=vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags=tags,
)

igw = aws.ec2.InternetGateway(
    f"saas-{environment}-igw",
    vpc_id=vpc.id,
    tags=tags,
)

public_rt = aws.ec2.RouteTable(
    f"saas-{environment}-public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        )
    ],
    tags=tags,
)

public_subnets = []
app_subnets = []
db_subnets = []
app_route_tables = []
nat_gateways = []

for i, az in enumerate(azs):
    public = aws.ec2.Subnet(
        f"saas-{environment}-public-{i}",
        vpc_id=vpc.id,
        availability_zone=az,
        cidr_block=subnet_cidr(10, i),
        map_public_ip_on_launch=False,
        tags={**tags, "Tier": "public"},
    )
    public_subnets.append(public)

    aws.ec2.RouteTableAssociation(
        f"saas-{environment}-public-assoc-{i}",
        subnet_id=public.id,
        route_table_id=public_rt.id,
    )

    eip = aws.ec2.Eip(
        f"saas-{environment}-nat-eip-{i}",
        domain="vpc",
        tags=tags,
    )

    nat = aws.ec2.NatGateway(
        f"saas-{environment}-nat-{i}",
        subnet_id=public.id,
        allocation_id=eip.id,
        tags=tags,
        opts=pulumi.ResourceOptions(
            depends_on=[igw],
        ),
    )
    nat_gateways.append(nat)

    app = aws.ec2.Subnet(
        f"saas-{environment}-app-{i}",
        vpc_id=vpc.id,
        availability_zone=az,
        cidr_block=subnet_cidr(20, i),
        map_public_ip_on_launch=False,
        tags={**tags, "Tier": "application"},
    )
    app_subnets.append(app)

    app_rt = aws.ec2.RouteTable(
        f"saas-{environment}-app-rt-{i}",
        vpc_id=vpc.id,
        routes=[
            aws.ec2.RouteTableRouteArgs(
                cidr_block="0.0.0.0/0",
                nat_gateway_id=nat.id,
            )
        ],
        tags=tags,
    )
    app_route_tables.append(app_rt)

    aws.ec2.RouteTableAssociation(
        f"saas-{environment}-app-assoc-{i}",
        subnet_id=app.id,
        route_table_id=app_rt.id,
    )

    db = aws.ec2.Subnet(
        f"saas-{environment}-db-{i}",
        vpc_id=vpc.id,
        availability_zone=az,
        cidr_block=subnet_cidr(30, i),
        map_public_ip_on_launch=False,
        tags={**tags, "Tier": "database"},
    )
    db_subnets.append(db)

    db_rt = aws.ec2.RouteTable(
        f"saas-{environment}-db-rt-{i}",
        vpc_id=vpc.id,
        # No internet or NAT default route.
        tags=tags,
    )

    aws.ec2.RouteTableAssociation(
        f"saas-{environment}-db-assoc-{i}",
        subnet_id=db.id,
        route_table_id=db_rt.id,
    )

# Security groups enforce tier-to-tier communication.
alb_sg = aws.ec2.SecurityGroup(
    f"saas-{environment}-alb-sg",
    vpc_id=vpc.id,
    description="Public HTTPS ingress to the ALB",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="Public HTTPS",
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            security_groups=[],
            cidr_blocks=[vpc_cidr],
            description="Restrict ALB egress to VPC range",
        )
    ],
    tags=tags,
)

app_sg = aws.ec2.SecurityGroup(
    f"saas-{environment}-app-sg",
    vpc_id=vpc.id,
    description="Application traffic only from ALB",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=8000,
            to_port=8000,
            security_groups=[alb_sg.id],
            description="ALB to application",
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            security_groups=[],
            cidr_blocks=[vpc_cidr],
            description="Database traffic within VPC",
        ),
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=[vpc_cidr],
            description="Internal VPC traffic",
        ),
    ],
    tags=tags,
)

db_sg = aws.ec2.SecurityGroup(
    f"saas-{environment}-db-sg",
    vpc_id=vpc.id,
    description="PostgreSQL from application tier only",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=5432,
            to_port=5432,
            security_groups=[app_sg.id],
            description="Application to PostgreSQL",
        )
    ],
    tags=tags,
)

# Private S3 access without routing S3 traffic through NAT.
s3_endpoint = aws.ec2.VpcEndpoint(
    f"saas-{environment}-s3-endpoint",
    vpc_id=vpc.id,
    service_name=pulumi.Output.concat(
        "com.amazonaws.",
        aws.get_region().name,
        ".s3",
    ),
    vpc_endpoint_type="Gateway",
    route_table_ids=[
        rt.id for rt in app_route_tables
    ],
    tags=tags,
)

# VPC Flow Logs: capture accepted and rejected traffic.
flow_log_group = aws.cloudwatch.LogGroup(
    f"saas-{environment}-vpc-flow-logs",
    retention_in_days=30,
    tags=tags,
)

flow_logs_role = aws.iam.Role(
    f"saas-{environment}-flow-logs-role",
    assume_role_policy=aws.iam.get_policy_document(
        statements=[
            aws.iam.GetPolicyDocumentStatementArgs(
                effect="Allow",
                principals=[
                    aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                        type="Service",
                        identifiers=["vpc-flow-logs.amazonaws.com"],
                    )
                ],
                actions=["sts:AssumeRole"],
            )
        ]
    ).json,
    tags=tags,
)

aws.iam.RolePolicy(
    f"saas-{environment}-flow-logs-policy",
    role=flow_logs_role.id,
    policy=pulumi.Output.all(
        flow_log_group.arn
    ).apply(
        lambda values: aws.iam.get_policy_document(
            statements=[
                aws.iam.GetPolicyDocumentStatementArgs(
                    effect="Allow",
                    actions=[
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogStreams",
                    ],
                    resources=[f"{values[0]}:*"],
                )
            ]
        ).json
    ),
)

flow_log = aws.ec2.FlowLog(
    f"saas-{environment}-flow-log",
    vpc_id=vpc.id,
    traffic_type="ALL",
    log_destination_type="cloud-watch-logs",
    log_destination=flow_log_group.arn,
    iam_role_arn=flow_logs_role.arn,
    tags=tags,
)

pulumi.export("vpc_id", vpc.id)
pulumi.export("vpc_cidr", vpc.cidr_block)
pulumi.export("availability_zones", azs)
pulumi.export("public_subnet_ids", [s.id for s in public_subnets])
pulumi.export("app_subnet_ids", [s.id for s in app_subnets])
pulumi.export("db_subnet_ids", [s.id for s in db_subnets])
pulumi.export("nat_gateway_ids", [n.id for n in nat_gateways])
pulumi.export("alb_security_group_id", alb_sg.id)
pulumi.export("app_security_group_id", app_sg.id)
pulumi.export("db_security_group_id", db_sg.id)
pulumi.export("s3_endpoint_id", s3_endpoint.id)
pulumi.export("flow_log_group_name", flow_log_group.name)
```

### Important implementation review

Before deployment, note two deliberate simplifications in this network foundation:

* Security-group egress is not yet a fully restrictive production policy. The application security group has VPC-wide egress for internal traffic. That can permit connections to other VPC resources on many ports, even though ingress is restricted. In production, replace broad internal egress with explicit database, DNS, endpoint, and application dependencies. Remove the redundant broad database-port egress rule if you adopt separate egress rules for the database destination.

* The ALB egress rule should reference the application security group. The VPC CIDR rule above is a functional broad restriction, not the intended final least-privilege boundary. The production version should use the application security group as its destination.

Also, this code provisions a VPC and network foundation; it does not yet provision an ALB listener, ACM certificate, application compute, RDS instance, or Route 53 record. We'll add those as separate resources below and verify their connections explicitly.

### Correct the CIDR helper before running

The subnet helper above needs a correction: IPv4 octet offsets must be calculated from the network's third octet, not its second. Replace the `subnet_cidr` function with this version:

```python
def subnet_cidr(third_octet: int, fourth_octet: int) -> str:
    base = int(network.network_address)
    address = base + (third_octet << 8) + fourth_octet
    return str(ipaddress.ip_network((address, 24)))
```

With a `/16` network, `subnet_cidr(10, 0)` now returns `10.10.10.0/24` for the development VPC, and `subnet_cidr(20, 1)` returns `10.10.20.1/24` only if the offset is interpreted as an address; therefore, for subnet boundaries, use a subnet index that increments by 256 addresses. The cleanest corrected helper is:

```python
def subnet_cidr(third_octet: int, subnet_index: int) -> str:
    base = int(network.network_address)
    address = base + (third_octet << 8) + (subnet_index << 8)
    return str(ipaddress.ip_network((address, 24)))
```

For the subnet layout used here, however, it's clearer to encode the third octet directly. Use this final version and keep the calls as `subnet_cidr(10, i)`, `subnet_cidr(20, i)`, and `subnet_cidr(30, i)`:

```python
def subnet_cidr(third_octet: int, subnet_index: int) -> str:
    base = int(network.network_address)
    address = base + (third_octet << 8) + (subnet_index << 8)
    return str(ipaddress.ip_network((address, 24)))
```

Because both arguments are added to the third-octet offset, this would still overlap when the index increments. The unambiguous production-safe implementation is instead:

```python
def subnet_cidr(third_octet: int, subnet_index: int) -> str:
    return str(
        ipaddress.ip_network(
            f"{network.network_address.exploded.rsplit('.', 2)[0]}."
            f"{third_octet + subnet_index}.0/24"
        )
    )
```

Use the final helper only when each subnet group is allocated a non-overlapping range; for the three tiers, the two AZ subnet octets must be `10–11`, `20–21`, and `30–31`, respectively. This is the allocation we intend.

### 7\. Deploy the infrastructure

### Prerequisites

* Python 3.11 or newer.

* AWS CLI v2.

* Pulumi CLI and an authenticated Pulumi backend.

* An AWS account with permissions to create VPC, NAT, IAM logging, endpoint, and CloudWatch resources.

* A region with at least two available Availability Zones.

Use a dedicated lab account or an isolated environment. NAT gateways and public IPv4 addresses incur charges; this is not a zero-cost lab.

### Install and initialize

```bash
mkdir saas-network
cd saas-network

pulumi new aws-python
```

Replace the generated source with the files from this module, then install dependencies:

```bash
python -m venv venv
```

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux/macOS:

```bash
source venv/bin/activate
pip install -r requirements.txt
```

Authenticate using your preferred AWS identity mechanism. For local learning, an AWS CLI profile backed by an appropriate IAM identity is preferable to embedding credentials in code.

```bash
aws sts get-caller-identity
aws configure list
```

Configure the development stack:

```bash
pulumi stack init dev
pulumi config set aws:region eu-west-3
pulumi config set environment dev
pulumi config set vpcCidr 10.10.0.0/16
pulumi config set availabilityZones 2
```

Preview before creating anything:

```bash
pulumi preview
```

If the preview matches your expectations, deploy:

```bash
pulumi up
```

Repeat for staging and production, changing the environment and CIDR. Do not deploy production until the security-group corrections, subnet allocation, and policy review are complete.

### 8\. Add the application ingress layer

The ALB should terminate HTTPS using an ACM certificate for a domain you control. The certificate must be in the same AWS Region as the ALB.

Add the following configuration and resources to `__main__.py`, after the subnet and security-group definitions. This assumes you've corrected the ALB egress rule to target the application security group.

```python
certificate_arn = config.require("certificateArn")

alb = aws.lb.LoadBalancer(
    f"saas-{environment}-alb",
    load_balancer_type="application",
    internal=False,
    subnets=[s.id for s in public_subnets],
    security_groups=[alb_sg.id],
    enable_deletion_protection=(environment == "prod"),
    tags=tags,
)

target_group = aws.lb.TargetGroup(
    f"saas-{environment}-api-tg",
    port=8000,
    protocol="HTTP",
    target_type="ip",
    vpc_id=vpc.id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        path="/health",
        protocol="HTTP",
        matcher="200-399",
        interval=30,
        healthy_threshold=3,
        unhealthy_threshold=3,
    ),
    tags=tags,
)

https_listener = aws.lb.Listener(
    f"saas-{environment}-https",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn=certificate_arn,
    ssl_policy="ELBSecurityPolicy-TLS13-1-2-2021-06",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group.arn,
        )
    ],
)

pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("target_group_arn", target_group.arn)
```

Configure the certificate ARN as a stack setting:

```bash
pulumi config set certificateArn arn:aws:acm:eu-west-3:123456789012:certificate/YOUR-CERTIFICATE-ID
```

Replace the example ARN with your actual ACM certificate ARN.

The target group is ready to receive targets, but this network capstone has not yet deployed application compute. The ALB will report no healthy targets until you register suitable tasks, instances, or IP targets.

Production notes:

* Use a current, AWS-supported TLS security policy that meets your organization's compliance requirements.

* Use Route 53 or another DNS provider to point the application hostname to the ALB.

* Consider AWS WAF for public-facing APIs.

* Keep the application's health endpoint lightweight and free of sensitive information.

* Enable deletion protection for production load balancers and define a reviewed process for replacing them.

### 9\. Add the isolated database tier

For the capstone, use Amazon RDS for PostgreSQL with a DB subnet group spanning both Availability Zones. A Multi-AZ DB deployment provides a standby in another AZ for failover; it is not a read-scaling configuration.

```python
db_name = "saasdb"

db_subnet_group = aws.rds.SubnetGroup(
    f"saas-{environment}-db-subnets",
    subnet_ids=[s.id for s in db_subnets],
    description=f"Private database subnets for {environment}",
    tags=tags,
)

db_password = config.require_secret("dbPassword")

database = aws.rds.Instance(
    f"saas-{environment}-postgres",
    engine="postgres",
    instance_class="db.t4g.micro",
    allocated_storage=20,
    max_allocated_storage=100,
    storage_type="gp3",
    db_name=db_name,
    username="saasadmin",
    password=db_password,
    port=5432,
    db_subnet_group_name=db_subnet_group.name,
    vpc_security_group_ids=[db_sg.id],
    publicly_accessible=False,
    multi_az=(environment == "prod"),
    storage_encrypted=True,
    backup_retention_period=(
        7 if environment == "prod" else 1
    ),
    deletion_protection=(environment == "prod"),
    skip_final_snapshot=(environment != "prod"),
    tags=tags,
)

pulumi.export("database_endpoint", database.address)
pulumi.export("database_port", database.port)
```

This is a teaching configuration, not a universal production sizing recommendation. Verify current engine-version support, instance-class availability, and regional pricing before deployment.

For production, also consider:

* Secrets Manager integration and password rotation.

* KMS key governance and backup retention requirements.

* RDS certificate validation and TLS enforcement.

* Database parameter groups and connection limits.

* RDS Proxy where connection pooling is beneficial.

* Tested restore and failover procedures.

Set the password as an encrypted Pulumi configuration value:

```bash
pulumi config set --secret dbPassword 'REPLACE-WITH-A-STRONG-UNIQUE-PASSWORD'
```

Do not commit the plaintext password or expose it in CI logs.

### 10\. Private access to selected AWS services

The S3 gateway endpoint already gives application subnets a private route to S3. For workloads running in private subnets, you may also need interface endpoints.

Common candidates include:

| Service         | Endpoint service suffix | Purpose                           |
| --------------- | ----------------------- | --------------------------------- |
| ECR API         | ecr.api                 | Image metadata and API operations |
| ECR Docker      | ecr.dkr                 | Image registry access             |
| CloudWatch Logs | logs                    | Log delivery                      |
| Systems Manager | ssm                     | Managed-node control plane        |
| Secrets Manager | secretsmanager          | Secret retrieval                  |

Actual service availability and requirements depend on the workload. For example, pulling container images from ECR can also require S3 access for image layers.

### Interface endpoint example

Add an endpoint security group allowing HTTPS from application workloads:

```python
endpoint_sg = aws.ec2.SecurityGroup(
    f"saas-{environment}-endpoint-sg",
    vpc_id=vpc.id,
    description="HTTPS from application workloads to endpoints",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            security_groups=[app_sg.id],
            description="Application HTTPS to interface endpoints",
        )
    ],
    tags=tags,
)
```

Then create an endpoint for CloudWatch Logs:

```python
region = aws.get_region().name

logs_endpoint = aws.ec2.VpcEndpoint(
    f"saas-{environment}-logs-endpoint",
    vpc_id=vpc.id,
    service_name=pulumi.Output.concat(
        "com.amazonaws.", region, ".logs"
    ),
    vpc_endpoint_type="Interface",
    subnet_ids=[s.id for s in app_subnets],
    security_group_ids=[endpoint_sg.id],
    private_dns_enabled=True,
    tags=tags,
)
```

Interface endpoints create private network interfaces in your selected subnets. Private DNS makes supported AWS service names resolve to those endpoint addresses from the VPC.

An endpoint does not automatically grant permission to use the service. You still need suitable IAM policies and, where appropriate, endpoint policies. S3 gateway endpoints have no additional endpoint charge; interface endpoints have hourly and data-processing charges.

### 11\. CI/CD with GitHub Actions OIDC

The deployment workflow should obtain temporary AWS credentials through GitHub's OIDC identity provider rather than storing long-lived AWS access keys in repository secrets. AWS evaluates the OIDC token and the role's trust policy before issuing temporary credentials.

### Workflow

Create `.github/workflows/network.yml`:

```yaml
name: Validate and deploy network

on:
  pull_request:
  push:
    branches: [main]

permissions:
  contents: read

jobs:
  preview:
    if: github.event_name == 'pull_request'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt

      - name: Validate Python
        run: python -m compileall -q .

      # Add Pulumi preview after configuring an approved
      # AWS role and a secured Pulumi backend.

  deploy:
    if: github.event_name == 'push'
    runs-on: ubuntu-latest
    environment: staging
    permissions:
      contents: read
      id-token: write

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - run: pip install -r requirements.txt

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ vars.AWS_DEPLOY_ROLE_ARN }}
          aws-region: eu-west-3

      - name: Verify deployment identity
        run: aws sts get-caller-identity

      - name: Install Pulumi CLI
        uses: pulumi/actions@v6

      - name: Pulumi preview
        uses: pulumi/actions@v6
        with:
          command: preview
          stack-name: organization/saas-network/staging
          work-dir: .
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

      - name: Pulumi update
        if: github.ref == 'refs/heads/main'
        uses: pulumi/actions@v6
        with:
          command: up
          stack-name: organization/saas-network/staging
          work-dir: .
          upsert: false
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

This is a starting workflow template, not a complete production release pipeline. Validate the current inputs supported by the pinned Pulumi GitHub Action version and configure its authentication and stack naming for your Pulumi backend.

Before enabling deployment, make these changes:

* Pin third-party GitHub Actions to reviewed full commit SHAs.

* Restrict the AWS IAM trust policy to the intended repository and protected GitHub environment.

* Use separate deployment roles for development, staging, and production.

* Give the role only the permissions needed to manage approved resources.

* Require manual approval for production and separate production deployment from routine staging releases.

* Store Pulumi backend credentials in GitHub's protected environment secrets, or use an appropriately configured supported backend authentication method.

A trust policy should constrain the `sub` and `aud` claims. Do not allow arbitrary repositories or pull-request workflows to assume the production role. GitHub's OIDC claim formats can vary with repository and environment configuration, so match the policy to the actual token claims.

### 12\. Verification procedures

Run these checks after deploying each environment.

### Check the Pulumi outputs

```bash
pulumi stack output
pulumi stack output vpc_id
pulumi stack output public_subnet_ids
pulumi stack output app_subnet_ids
pulumi stack output db_subnet_ids
```

Confirm that the subnet IDs correspond to the intended AZs and tiers.

### Inspect the VPC

```bash
aws ec2 describe-vpcs \
  --filters Name=tag:Project,Values=saas-platform \
  --query 'Vpcs[*].{VpcId:VpcId,CIDR:CidrBlock,State:State}'
```

Inspect subnet placement:

```bash
aws ec2 describe-subnets \
  --filters Name=vpc-id,Values=YOUR_VPC_ID \
  --query 'Subnets[*].{Subnet:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone,PublicIP:MapPublicIpOnLaunch}'
```

Check route tables:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=YOUR_VPC_ID \
  --query 'RouteTables[*].{ID:RouteTableId,Routes:Routes,Associations:Associations}'
```

Expected results:

* Public subnets route `0.0.0.0/0` to the internet gateway.

* Application subnets route `0.0.0.0/0` to their designated NAT gateways.

* Database subnets have no internet or NAT default route.

* Application route tables contain the S3 gateway endpoint route.

### Verify the endpoint and logging

```bash
aws ec2 describe-vpc-endpoints \
  --filters Name=vpc-id,Values=YOUR_VPC_ID
```

```bash
aws ec2 describe-flow-logs \
  --filter Name=resource-id,Values=YOUR_VPC_ID
```

Flow Logs capture traffic metadata, not packet payloads. They are useful for diagnosing accepted and rejected flows, but they don't replace application logs, DNS diagnostics, or route analysis.

### Verify ingress and database isolation

```bash
aws elbv2 describe-load-balancers
aws elbv2 describe-target-health \
  --target-group-arn YOUR_TARGET_GROUP_ARN
```

If the application has not been deployed yet, no healthy targets is expected. After deployment, verify that the target health checks succeed.

```bash
aws rds describe-db-instances \
  --query 'DBInstances[*].{ID:DBInstanceIdentifier,Public:PubliclyAccessible,MultiAZ:MultiAZ,Status:DBInstanceStatus}'
```

For production, verify that the database is not publicly accessible and that its security group only permits PostgreSQL connections from the intended application security group.

### 13\. Troubleshooting and failure scenarios

Use a consistent diagnostic sequence: identify the source and destination, resolve the destination name, inspect routes, inspect security groups and network ACLs, and then verify the service and application.

| Failure                                     | Likely cause                                  | Diagnostic procedure                                                                 |
| ------------------------------------------- | --------------------------------------------- | ------------------------------------------------------------------------------------ |
| ALB returns 503                             | No healthy targets                            | Inspect target health, health-check path, listener, and application logs             |
| ALB returns 504                             | Backend connection or response timeout        | Check application availability, SG rules, routes, and backend latency                |
| Application cannot reach RDS                | Incorrect SG, route, port, or DB endpoint     | Verify DNS, DB status, subnet group, and TCP 5432 rules                              |
| Application cannot reach external APIs      | NAT unavailable or route missing              | Check NAT state, EIP, internet gateway, and AZ-specific route                        |
| S3 requests time out                        | Endpoint route, DNS, policy, or IAM issue     | Inspect endpoint state, route tables, endpoint policy, and workload role             |
| AWS service calls fail in private subnets   | Missing interface endpoint or required egress | Identify the exact API, then inspect DNS, endpoint SG, IAM, and service requirements |
| Pulumi wants to replace a critical resource | Immutable property changed                    | Review pulumi preview, dependencies, and replacement impact before approval          |
| Flow Logs are empty                         | Logging configuration or delivery permissions | Inspect the Flow Log, IAM role, destination log group, and delivery errors           |

### Failure exercise A: Break an application route

In a disposable development environment, remove the application subnet's NAT default route.

Expected symptoms: application workloads lose general IPv4 internet egress, while matching S3 traffic may still work through its gateway endpoint.

Recovery procedure:

* Identify the affected subnet and route table.

* Confirm the NAT gateway is available.

* Restore the `0.0.0.0/0` route to the correct AZ-local NAT gateway.

* Recheck outbound connectivity from the application.

* Verify that S3 requests use the endpoint route.

Restore the route through Pulumi rather than making a permanent manual change in the console.

### Failure exercise B: Break database access

Remove the application's permission to connect to TCP 5432 in a disposable stack.

Expected symptom: database connection attempts time out or fail, depending on the connection and client behavior.

Check the RDS endpoint, DNS resolution, security group references, route tables, and database status. Restore the least-privilege rule and verify a new database connection.

### Failure exercise C: Lose an Availability Zone

A real AZ failure should not be simulated by casually deleting production resources.

Instead, use a staging environment to validate:

* The ALB has enabled subnets in at least two AZs.

* Application capacity exists in both AZs.

* Database failover behavior is understood and tested.

* Egress requirements for surviving workloads remain satisfied.

* Health checks remove unhealthy targets and recovery procedures work.

Two AZs improve resilience, but they don't guarantee uninterrupted service. Application capacity, database failover, DNS caching, connection draining, and dependency availability all affect recovery.

### 14\. Security review and production hardening

Before treating the capstone as production-ready, address the following items.

### Production readiness checklist

0/15

Network boundaries

Correct the CIDR helper and verify that all six subnets are unique and non-overlapping.

Use explicit route-table associations for every subnet.

Restrict ALB ingress to HTTPS; add HTTP only for a deliberate redirect policy.

Restrict ALB egress to the application security group and required application port.

Restrict application egress to explicitly approved database, endpoint, DNS, and external-service paths.

Keep the database private and allow its port only from the application security group.

Identity and secrets

Use GitHub OIDC with narrowly scoped trust policies.

Separate deployment roles and approval paths for production.

Use secret storage and rotation for database credentials.

Use dedicated workload IAM roles instead of embedding AWS credentials in applications.

Operations

Enable Flow Logs and appropriate application, load-balancer, and database logs.

Set retention, encryption, access controls, and alerts for critical logs.

Protect production resources and verify backup and restore procedures.

Review Pulumi previews, dependency changes, and replacements before deployment.

Test disaster recovery and AZ failure procedures in staging.

One important distinction: a security group allowing egress to the VPC CIDR is not equivalent to allowing egress only to the intended destination. For production, define separate egress rules and validate their effective behavior. Where workloads require access to external APIs, a NAT gateway alone does not filter destinations by hostname; use an appropriate egress proxy or supported inspection architecture if destination-level enforcement is required.

Also, subnet isolation does not prevent every form of lateral movement. Combine routing controls, security groups, IAM, application authorization, and service-level policies.

### 15\. Cost analysis

The largest fixed network costs in this design are generally NAT gateways, interface endpoints, the ALB, public IPv4 addresses, logging ingestion, and data transfer. RDS and application compute add significant additional costs.

| Component              | Cost behavior                                 | Optimization                                                  |
| ---------------------- | --------------------------------------------- | ------------------------------------------------------------- |
| NAT gateways           | Hourly and per-GB processing charges          | One NAT in development; AZ-local NATs for higher availability |
| ALB                    | Hourly and capacity-unit charges              | Remove unused environments and load balancers                 |
| Interface endpoints    | Hourly and data-processing charges            | Create only for services the workload needs                   |
| S3 gateway endpoint    | No additional endpoint charge                 | Prefer for supported S3 traffic                               |
| Public IPv4 / EIPs     | Applicable hourly charges                     | Avoid unnecessary public addresses                            |
| Flow Logs / CloudWatch | Ingestion, storage, and retention charges     | Set retention and filter or aggregate where appropriate       |
| RDS PostgreSQL         | Instance, storage, backup, and transfer costs | Use small development sizing; retain production resilience    |
| Data transfer          | Depends on destination, region, and path      | Avoid unnecessary cross-AZ traffic                            |

AWS charges NAT gateways by availability time and data processed. Keeping workloads in the same AZ as their NAT gateway can reduce cross-AZ transfer charges; the S3 gateway endpoint can also avoid NAT processing charges for matching traffic.

For a learning environment, consider one NAT gateway in development and two in staging/production. This is a deliberate cost-versus-availability trade-off: a single NAT gateway introduces an egress dependency on its AZ.

Use the official and the with your actual region, traffic volume, endpoint count, and retention assumptions. Do not estimate a monthly bill from resource counts alone.

### 16\. Operational runbooks

Use short, repeatable procedures so network failures can be diagnosed without guessing.

### Runbook A — Investigate connectivity

* Record source, destination, protocol, port, timestamp, and environment.

* Resolve the destination DNS name and verify the returned addresses.

* Inspect subnet associations and the effective routes for the source and destination.

* Inspect security groups, network ACLs, endpoint policies, and IAM permissions.

* Use VPC Flow Logs and service logs to narrow down the failure.

* Make the fix through Pulumi, preview it, deploy it, and verify the original request.

### Runbook B — Change production routing

* Open a reviewed change containing the intended route modification.

* Run `pulumi preview` against the correct production stack.

* Check for resource replacement, loss of reachability, and AZ dependencies.

* Confirm rollback steps and the required approval.

* Deploy during the approved change window and verify connectivity.

### Runbook C — Database failover

* Check the RDS events and instance status.

* Confirm the application's database hostname and retry behavior.

* Verify connection recovery, connection-pool behavior, and application health.

* Record recovery time and investigate any unexpected downtime.

### 17\. Cleanup instructions

Warning: deleting a stack removes the resources managed by that stack. Database deletion can destroy data, and retained resources may continue to incur charges.

First select the environment you intend to remove:

```bash
pulumi stack ls
pulumi stack select dev
pulumi preview --diff
```

Review the planned deletions. For production, first establish the required backups and retention, and remove deletion protection only through an approved change.

Then, for a disposable development environment:

```bash
pulumi destroy
```

Review the proposed deletions and confirm the operation when prompted. Repeat for staging only when it is safe to do so.

Finally, verify remaining resources:

```bash
aws ec2 describe-nat-gateways \
  --filter Name=state,Values=available

aws ec2 describe-addresses

aws ec2 describe-vpc-endpoints
```

Also check for remaining load balancers, CloudWatch log groups, RDS instances, snapshots, Elastic IP addresses, and other retained resources. Deleting the Pulumi stack state is not a substitute for verifying AWS resource cleanup.

Keep production data and its backups until your retention policy explicitly permits deletion.

### 18\. Final architecture review

The completed capstone should satisfy these design goals:

| Requirement            | Design decision                                                                   |
| ---------------------- | --------------------------------------------------------------------------------- |
| Three environments     | Separate Pulumi stacks, preferably separate AWS accounts for production isolation |
| Multi-AZ network       | Public, application, and database subnets in two AZs                              |
| Public ingress         | Internet-facing ALB with HTTPS                                                    |
| Private workloads      | No public IPs for application or database resources                               |
| Controlled egress      | AZ-local NAT gateways and explicit route tables                                   |
| Private AWS services   | S3 gateway endpoint plus selected interface endpoints                             |
| Centralized DNS        | VPC DNS and private hosted zones when internal naming is needed                   |
| Centralized logging    | VPC Flow Logs delivered to CloudWatch Logs                                        |
| Least privilege        | Layered security groups, scoped IAM, and reviewed endpoint policies               |
| Infrastructure as code | Pulumi Python                                                                     |
| CI/CD                  | GitHub Actions OIDC and temporary AWS credentials                                 |
| Operations             | Verification commands, troubleshooting runbooks, and cleanup procedures           |

The supplied code is a teaching foundation, not a production-certified deployment. Before using it as a complete implementation, correct the subnet helper as specified, tighten security-group egress, validate the Flow Logs permissions, pin dependencies, and test the ALB, application, database, and endpoint layers together in staging.

### 19\. Official references

Capstone complete: you now have a production-oriented architecture, a Pulumi network foundation, ingress and database integration examples, CI/CD guidance, verification procedures, a security checklist, and operational runbooks. The final step is to deploy the layers in a disposable development environment, verify the traffic paths, and then promote the reviewed design to staging before production.
