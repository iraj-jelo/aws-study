### Module 4 — NAT and Outbound Connectivity

AWS VPC Course · Pulumi Python · October 2026

In Module 3, we covered public and private subnets, route tables, Internet Gateways, and IPv4/IPv6 routing. Now we'll build on that foundation to understand how workloads in private subnets can initiate outbound connections without becoming directly reachable from the public internet.

We'll use Pulumi with Python, AWS CLI v2, practical traffic-flow diagrams, and a hands-on lab. We'll focus on current AWS networking practices, label legacy approaches clearly, avoid quizzes, and identify billable resources before deployment.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Design outbound IPv4 connectivity using NAT Gateways.

* Choose between one NAT Gateway per Availability Zone and a shared NAT Gateway.

* Explain how routing, source NAT, connection tracking, and return traffic work.

* Configure IPv6 outbound connectivity using an egress-only Internet Gateway.

* Access supported AWS services privately without routing traffic through the general internet.

* Estimate NAT processing and data-transfer costs.

* Build a resilient egress architecture using Pulumi.

* Troubleshoot outbound connectivity by examining routes, security rules, DNS, and service behavior.

### 2\. The problem: private workloads need outbound access

Imagine a SaaS application running in a VPC:

* A public Application Load Balancer accepts incoming HTTPS requests.

* Private application instances or containers process requests.

* A private database stores application data.

* Application workloads need to download packages, call external APIs, or retrieve updates.

You want the application workloads to initiate outbound connections, but you don't want to assign them public IPv4 addresses or expose them directly to the internet.

![AWS NAT Gateway and Private/Public Subnets](https://images.openai.com/static-rsc-4/8hY0aTY0-Pm5E2s0YFJeo3xDySc52w3e76CXTe_T23S-Ny1zKqCEmNumC41Gnu0Hl2ERYabyQo_eUI5al28ki8moC0BeEdK450Wi9TzCaXNVH_p-ivK_mGZacCkMgQsP0x7LTMF0HYkdvwJWAmO3CeeMngRny11b3eXYT6KpeooJEtAI4b_wtQhuzk66dJw8?purpose=fullsize)

The key distinction is that private subnet does not mean no outbound connectivity. It means the subnet's routing and addressing do not provide the workload with direct public IPv4 internet connectivity.

A private workload can still reach the internet through a NAT Gateway, access supported AWS services through VPC endpoints, or use other explicitly configured network paths.

### Three common egress designs

![If AWS Networking Confuses You — This Guide Is Your Missing Map | by Muhammad Shahbaj | Medium](https://images.openai.com/static-rsc-4/Ec2waY3UUyc1VWBggxuUzdfoVHvbLPI5-S-K86JtCemubcBW2C7QpASLKmy0UbPTAEIkqYQGAqaSPHeU92vVncM4zfpeLagYdbsWWaTJ-_QbFzftYA4RTFxBOu9hCZZEtM8q1dfuss-R4XX3NB-wJvECN4EkaMZ9pTBALSDzJAv2hrm2-PnXRnI4YKOiLdbr?purpose=fullsize)

1\. General IPv4 internet access

Private workloads → NAT Gateway → Internet Gateway → Internet.

Useful for external APIs, package repositories, and destinations without private connectivity.

![Four AWS VPC blueprints that will save your MLOps pipeline | by <devtips/> | Apr, 2026 | Medium](https://images.openai.com/static-rsc-4/B_S85WfgXg6KXFqvC6JtO5YGK1asSG8Hf4eTqkhNlQaTlMKciNcWyFMgq2OesJaYMX8X3Xg_AlIMJv9izlOfhKsu7cDAjIXXXUdvahQn3g_ZlPA9VGoLv3tzOsWr-9Q_epfal-5QPyleI0IveSBODobFnvj7z41BohD4sW6dHGZUf4RHFfZBtHh2Z1TDY5Ad?purpose=fullsize)

2\. Private access to AWS services

Private workloads → VPC endpoint → supported AWS service.

Useful when a workload needs S3, DynamoDB, or other supported services without general-purpose internet egress.

![How to Work With IPv6 in AWS and Don't Die in the Process · Sergio Cambelo's Blog](https://images.openai.com/static-rsc-4/xYww7s3twGOQ6E-DGJA6aeLWEXV6QpPL7pk9O-SdXJ9ytCmN_vRd5L64Aj_-vp9B_fRxrMUNzXO2CsSIVhfIHqIzVNBiOITlxPTL9qstA7iXMuB1e3x9tVo44KVZSoxQWHvbv9sa9I6R1DnhKrqDQaJz1-V0prPKLE124wWtbh4hg3KfeFu8DL6r0OUJNIyw?purpose=fullsize)

3\. Outbound IPv6 connectivity

IPv6-enabled workload → Egress-Only Internet Gateway → Internet.

Supports outbound IPv6 connections while preventing the gateway from being used to initiate unsolicited inbound connections.

These designs solve different problems. A NAT Gateway is not a universal replacement for VPC endpoints, and an IPv6 egress-only gateway does not provide IPv4 NAT.

### 3\. NAT fundamentals: what actually happens to a packet?

NAT stands for Network Address Translation. In the private-subnet internet-access scenario, AWS uses address translation together with port translation to let many private IPv4 workloads share a public IPv4 address.

Suppose an EC2 instance has these addresses:

* Private IPv4 address: `10.20.11.25`

* External API: `203.0.113.80:443` (documentation-only example address)

* NAT Gateway's Elastic IP: `198.51.100.10` (documentation-only example address)

The instance initiates an HTTPS connection. Conceptually, the translation looks like this:

Private EC2 workload

Source: 10.20.11.25:49152

Route: 0.0.0.0/0 → NAT Gateway

Public NAT Gateway

Translates the source address and tracks the connection mapping.

Internet Gateway maps the NAT Gateway's private IPv4 to its Elastic IP

External HTTPS API

Sees the public source address of the NAT Gateway.

The addresses above illustrate the mechanism; they are not a real deployed connection.

### 3.1 Forward traffic and return traffic

When the connection leaves the private subnet:

* The instance creates an outbound packet with its private IPv4 address as the source.

* The private subnet's route table selects the NAT Gateway for the destination.

* The NAT Gateway translates the source address to its own private IPv4 address and tracks the connection.

* The Internet Gateway performs the public-address mapping for the public NAT Gateway.

* The destination receives the packet and replies to the public source address.

* AWS translates the return traffic back through the NAT Gateway to the original private workload.

The NAT Gateway is a managed service; you do not configure its Linux networking stack, connection-tracking rules, or packet-forwarding software.

A NAT Gateway permits return traffic associated with outbound connections. It does not give an internet host the ability to initiate an arbitrary new connection to the private instance. This is not a substitute for security groups, network ACLs, or application-level access controls.

### 3.2 NAT is not a firewall policy

A NAT Gateway does not provide a configurable list of allowed internet domains, URLs, or destination ports.

For example, a private workload with a default route through a NAT Gateway may be able to reach multiple external HTTPS services. If you need to allow only approved destinations, consider additional egress controls, such as an appropriate network firewall or an explicit proxy architecture.

Security groups control traffic associated with network interfaces; network ACLs filter subnet traffic. Neither should be confused with the address-translation function itself.

### 4\. Public and private NAT Gateways

AWS supports two NAT Gateway connectivity types. Choose based on the destination network, not simply on whether the source subnet is private.

Public NAT Gateway

Internet egress

* Created in a public subnet.

* Requires an Elastic IP address at creation.

* Uses a route through an Internet Gateway for internet access.

* Commonly serves IPv4 workloads in private subnets.

* Can also support specific private-network connectivity designs.

Private NAT Gateway

Private-network translation

* Does not use an Elastic IP address.

* Translates source private IPv4 addresses.

* Can provide connectivity to other VPCs or on-premises networks through appropriate routing infrastructure.

* Is not an internet-egress replacement: an Internet Gateway drops traffic routed from a private NAT Gateway to the internet.

For our lab, we'll use a public NAT Gateway so that private IPv4 workloads can reach an external HTTPS endpoint. AWS documents both NAT types and their forwarding behavior in its [NAT Gateway documentation](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html?utm_source=chatgpt.com).

### 5\. Routing design: one NAT Gateway or one per Availability Zone?

A NAT Gateway is created in a particular Availability Zone and has redundancy within that zone. It is not a single regional NAT resource that automatically moves between AZs.

Consider a VPC with two Availability Zones.

### Option A — One shared NAT Gateway

AZ A — Private subnet

10.20.11.0/24

Default route

AZ B — Public NAT Gateway

AZ B — Public subnet / Internet Gateway

Internet egress path

AZ B — Private subnet

10.20.21.0/24 · Also routes to the same NAT Gateway

Simplified topology: both private subnet route tables use the same NAT Gateway ID as their default-route target.

Advantages:

* One NAT Gateway hourly charge.

* Straightforward configuration.

* Can be reasonable for a development environment or a low-traffic workload where the availability trade-off is acceptable.

Disadvantages:

* Traffic from AZ A crosses AZ boundaries to reach the NAT Gateway in AZ B.

* Cross-AZ data transfer can add cost.

* If AZ B or its NAT Gateway becomes unavailable, AZ A loses its outbound path through that gateway.

* The NAT Gateway is a shared dependency for both AZs.

### Option B — A NAT Gateway in each AZ

AZ A

Private subnet

NAT A

Internet Gateway

AZ B

Private subnet

NAT B

Internet Gateway

Each private subnet uses the NAT Gateway in its own AZ. Both NAT Gateways are in public subnets.

Advantages:

* Avoids the cross-AZ NAT path during normal operation.

* Reduces dependence on a single AZ's NAT Gateway.

* Usually the better baseline for production workloads that require multi-AZ egress resilience.

Disadvantages:

* Two hourly NAT Gateway charges, plus their respective data-processing charges.

* Additional Elastic IP address usage and more resources to manage.

* Each private subnet needs the correct route-table association and default route.

Important: Two NAT Gateways do not automatically provide failover for every routing configuration. If one fails, a route that still points to it does not magically switch to the other gateway. Any failover design must explicitly address route changes, health detection, recovery behavior, and possible cross-AZ traffic. AWS recommends placing NAT Gateways in the same AZ as the workloads where resilience is important.

### 5.1 An important current option: Regional NAT Gateways

AWS also documents Regional NAT Gateways, which change the traditional design choice. Rather than creating and managing a separate zonal NAT Gateway and route target for each AZ, a Regional NAT Gateway can automatically expand across AZs where your workloads are present. AWS manages its zonal expansion and associated routing model.

This is important for an up-to-date architecture decision:

| Design                       | Main trade-off                                                                                                                                |
| ---------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| One zonal NAT Gateway        | Lowest NAT hourly-resource count, but shared AZ dependency and possible cross-AZ charges                                                      |
| One zonal NAT Gateway per AZ | Explicit zonal affinity and fault isolation, with a charge for each gateway                                                                   |
| Regional NAT Gateway         | Simplifies multi-AZ egress and automatically expands with workload presence; evaluate its pricing, supported modes, and regional availability |

Regional NAT Gateways are not suitable for every use case: AWS documents that they do not support private NAT. Their automatic expansion can also take time when workloads appear in a new AZ. Check the current [Regional NAT Gateway documentation](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html?utm_source=chatgpt.com) before choosing this mode.

For learning routing fundamentals, we'll implement the explicit zonal model first. That makes the relationship between subnet route tables, AZs, and NAT Gateway IDs easy to inspect.

### 6\. IPv6 outbound connectivity

IPv6 requires a different mental model because globally unique IPv6 addresses do not require IPv4-style NAT to communicate with the internet.

For an IPv6-enabled private workload that needs outbound-only internet access, AWS provides the Egress-Only Internet Gateway.

A private subnet's IPv6 route table can contain:

| Destination        | Target                       |
| ------------------ | ---------------------------- |
| 10.20.0.0/16       | local                        |
| Your VPC IPv6 CIDR | local                        |
| ::/0               | Egress-Only Internet Gateway |

The `::/0` route matches IPv6 destinations not covered by a more specific route.

IPv6-enabled private workload

Globally unique IPv6 address

Route `::/0`

Egress-Only Internet Gateway

Stateful outbound IPv6 connectivity

Internet IPv6 destination

The gateway allows outbound IPv6 connections and their return traffic, but prevents the internet from initiating a new inbound connection through it. Security groups and network ACLs remain relevant.

An Egress-Only Internet Gateway:

* Supports IPv6 only.

* Does not perform IPv4 NAT.

* Has no hourly gateway charge according to AWS documentation, although data transfer may be chargeable.

* Requires an IPv6 CIDR and the appropriate route.

See [AWS: Egress-Only Internet Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html?utm_source=chatgpt.com).

### 6.1 IPv6 workloads calling IPv4-only services: NAT64

A different situation arises when a workload has only IPv6 connectivity but must reach an IPv4-only destination.

AWS NAT Gateway supports NAT64, used with DNS64, for this scenario.

Conceptually:

* The workload resolves an IPv4-only destination using DNS64-enabled resolution.

* DNS64 synthesizes an IPv6 address representing the IPv4 destination.

* The workload sends IPv6 traffic to that synthesized address.

* The NAT Gateway translates the IPv6 traffic to IPv4.

* The IPv4 destination receives the request, and the response returns through the translation path.

This is distinct from ordinary outbound IPv4 NAT. NAT64 is useful for IPv6-only architectures that must retain compatibility with IPv4-only endpoints. See [AWS NAT Gateway basics](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html?utm_source=chatgpt.com).

### 7\. Private service access without general internet egress

A NAT Gateway is often deployed because workloads need AWS APIs. But if the destination is a supported AWS service, you should evaluate a VPC endpoint before routing that traffic through NAT.

Two major endpoint types are relevant.

### 7.1 Gateway endpoints

Gateway endpoints provide private connectivity to Amazon S3 and DynamoDB through route-table entries.

Private workload

Route-table prefix-list entry → Gateway endpoint

Amazon S3 or DynamoDB

Gateway endpoints:

* Do not require a NAT Gateway or Internet Gateway for those service paths.

* Are associated with selected route tables.

* Have no additional endpoint charge.

* Can use endpoint policies to restrict access, in addition to IAM and service resource policies.

They are often the simplest and most economical option when the workload primarily needs S3 or DynamoDB.

### 7.2 Interface endpoints and AWS PrivateLink

Interface endpoints create endpoint network interfaces in selected subnets. Workloads can reach supported AWS services through these private addresses.

Examples include supported integrations for Systems Manager, CloudWatch, and ECR, although the exact endpoint services needed depend on the workload and Region.

Interface endpoints have hourly and data-processing charges. For resilience, AWS recommends endpoint coverage across multiple AZs when the workload requires it.

The design goal is not necessarily to remove every NAT Gateway. It is to route each destination through the most appropriate path:

* S3 and DynamoDB → gateway endpoints where appropriate.

* Other supported AWS services → interface endpoints where justified.

* External public APIs and package repositories → controlled internet egress, often through NAT.

* Private corporate networks → appropriate private routing, VPN, or Transit Gateway connectivity.

Security distinction: An endpoint is not a blanket permission to access all data in the service. Endpoint policies, IAM permissions, resource policies, and network controls still matter.

### 8\. NAT instances: legacy context

A NAT instance is an EC2 instance configured to forward traffic and perform address translation.

It can be useful to recognize in older VPCs, but a NAT instance should not be the default recommendation for a new deployment. AWS recommends NAT Gateways because they offer managed availability, higher bandwidth, and less operational maintenance.

| Concern         | NAT Gateway                                         | NAT instance                                            |
| --------------- | --------------------------------------------------- | ------------------------------------------------------- |
| Maintenance     | AWS-managed                                         | You maintain the OS and NAT configuration               |
| Scaling         | Managed scaling                                     | Depends on instance size and configuration              |
| Security groups | Cannot attach one directly to the NAT Gateway       | Can attach a security group to the instance             |
| Port forwarding | Not supported as a configurable NAT Gateway feature | Can be configured manually                              |
| Failover        | Design around AZs and gateway mode                  | Requires instance-level failover and routing management |
| Cost model      | Hourly and data-processing charges                  | EC2, storage, data transfer, and operational overhead   |

When inspecting an existing deployment, look for a route such as `0.0.0.0/0 → i-...` or a route targeting a NAT instance's network interface. A modern managed NAT route instead targets a NAT Gateway ID, typically `nat-...`.

Do not replace an existing NAT instance blindly. Identify its routing dependencies, custom filtering, port forwarding, and any other functions before migration. AWS provides a [NAT instance migration guide](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-comparison.html?utm_source=chatgpt.com).

### 9\. NAT Gateway cost model

NAT costs have a fixed component and a traffic-dependent component. Exact prices depend on the AWS Region, pricing model, and applicable data-transfer rules.

The main components to investigate are:

* NAT Gateway hourly charges.

* NAT Gateway data-processing charges per GB.

* Applicable regional or inter-AZ data-transfer charges.

* Internet data-transfer charges.

* Elastic IP/public IPv4 charges where applicable.

AWS documents the hourly and data-processing charges, and specifically recommends placing workloads and NAT Gateways in the same AZ or considering service endpoints to reduce costs.

### 9.1 A simple cost equation

Let:

* = number of NAT Gateways.

* = billable hours per gateway.

* = hourly charge per gateway.

* = total GB processed by NAT Gateways.

* = processing charge per GB.

* = applicable cross-AZ transfer costs.

* = other applicable data-transfer costs.

Then the approximate cost is:

C_{\\text{total}} = NH P_h + D P_d + C_x + C_i

This is a model for comparison, not a live AWS quote.

For example, a single shared NAT Gateway and two zonal NAT Gateways have different hourly costs. But the shared design may add cross-AZ transfer charges and increase the cost of an AZ outage. The cheaper design on a bill may not be the better production design.

To obtain current regional rates, consult [AWS NAT Gateway pricing](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-pricing.html?utm_source=chatgpt.com) and [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/?utm_source=chatgpt.com).

### 10\. Hands-on lab — controlled outbound connectivity with Pulumi

We'll create a small two-AZ VPC and compare a single shared zonal NAT Gateway with one NAT Gateway per AZ.

The lab will create:

* One VPC with CIDR `10.20.0.0/16`.

* Two public subnets.

* Two private subnets.

* An Internet Gateway.

* Public route tables with a default route to the Internet Gateway.

* Either one or two public NAT Gateways.

* Private route tables whose default routes point to the selected NAT Gateway.

* Outputs that help you inspect the routing design.

Billable AWS resources

NAT Gateways incur hourly and data-processing charges. This lab also uses Elastic IP addresses and public IPv4 connectivity. A NAT Gateway may continue to incur charges even when no traffic is passing through it. Review current regional prices and delete the resources when finished.

### 10.1 Prerequisites

Install and configure:

* Pulumi CLI.

* Python 3.11 or another currently supported Python version compatible with your chosen Pulumi AWS provider.

* AWS CLI v2.

* AWS credentials for an account where you are authorized to create VPC networking resources.

Verify your account and Region:

```bash
aws sts get-caller-identity
aws configure get region
pulumi version
python --version
```

Choose an AWS Region with at least two available AZs. The IAM identity used for deployment must be allowed to create and inspect the VPC, subnets, route tables, Internet Gateway, Elastic IP addresses, and NAT Gateways.

### 10.2 Project structure

Create a project:

```text
vpc-egress-lab/
├── Pulumi.yaml
├── requirements.txt
└── __main__.py
```

`Pulumi.yaml`:

```yaml
name: vpc-egress-lab
runtime:
  name: python
description: Two-AZ AWS VPC NAT egress comparison
```

`requirements.txt`:

```text
pulumi
pulumi-aws
```

For a reproducible environment, resolve and pin the dependency versions you have tested rather than leaving production deployments unpinned.

Install the dependencies and create a stack:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pulumi stack init dev
pulumi config set aws:region eu-west-1
```

Change `eu-west-1` to your intended Region.

### 10.3 Pulumi implementation

This implementation uses zonal NAT Gateways. The `natPerAz` configuration selects the topology.

* `true`: two NAT Gateways, one per AZ.

* `false`: one NAT Gateway shared by both private subnets.

`__main__.py`:

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

# Set to true for one zonal NAT Gateway per AZ.
nat_per_az = config.get_bool("natPerAz")
if nat_per_az is None:
    nat_per_az = True

az_result = aws.get_availability_zones(state="available")
if len(az_result.names) < 2:
    raise RuntimeError("This lab requires at least two available AZs.")

azs = az_result.names[:2]

vpc = aws.ec2.Vpc(
    "egress-vpc",
    cidr_block="10.20.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "egress-vpc"},
)

igw = aws.ec2.InternetGateway(
    "egress-igw",
    vpc_id=vpc.id,
    tags={"Name": "egress-igw"},
)

public_subnets = []
private_subnets = []

for i, az in enumerate(azs):
    public_subnets.append(
        aws.ec2.Subnet(
            f"public-{i+1}",
            vpc_id=vpc.id,
            availability_zone=az,
            cidr_block=f"10.20.{i}.0/24",
            map_public_ip_on_launch=True,
            tags={"Name": f"public-{i+1}"},
        )
    )

    private_subnets.append(
        aws.ec2.Subnet(
            f"private-{i+1}",
            vpc_id=vpc.id,
            availability_zone=az,
            cidr_block=f"10.20.{10+i}.0/24",
            map_public_ip_on_launch=False,
            tags={"Name": f"private-{i+1}"},
        )
    )

# Public subnet routing: internet-bound IPv4 traffic
# goes to the VPC's Internet Gateway.
public_rt = aws.ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    routes=[
        {
            "cidr_block": "0.0.0.0/0",
            "gateway_id": igw.id,
        }
    ],
    tags={"Name": "public-rt"},
)

for i, subnet in enumerate(public_subnets):
    aws.ec2.RouteTableAssociation(
        f"public-association-{i+1}",
        subnet_id=subnet.id,
        route_table_id=public_rt.id,
    )

# A public NAT Gateway needs an Elastic IP and a public subnet.
nat_count = 2 if nat_per_az else 1
nat_gateways = []

for i in range(nat_count):
    eip = aws.ec2.Eip(
        f"nat-eip-{i+1}",
        domain="vpc",
        tags={"Name": f"nat-eip-{i+1}"},
    )

    nat = aws.ec2.NatGateway(
        f"nat-{i+1}",
        allocation_id=eip.id,
        subnet_id=public_subnets[i].id,
        connectivity_type="public",
        tags={"Name": f"nat-{i+1}"},
        opts=pulumi.ResourceOptions(depends_on=[igw]),
    )

    nat_gateways.append(nat)

# Private subnet routing.
# In shared mode, both AZs use NAT Gateway 1.
# In per-AZ mode, each subnet uses its local NAT Gateway.
for i, subnet in enumerate(private_subnets):
    nat_index = i if nat_per_az else 0

    private_rt = aws.ec2.RouteTable(
        f"private-rt-{i+1}",
        vpc_id=vpc.id,
        routes=[
            {
                "cidr_block": "0.0.0.0/0",
                "nat_gateway_id": nat_gateways[nat_index].id,
            }
        ],
        tags={"Name": f"private-rt-{i+1}"},
    )

    aws.ec2.RouteTableAssociation(
        f"private-association-{i+1}",
        subnet_id=subnet.id,
        route_table_id=private_rt.id,
    )

pulumi.export("vpc_id", vpc.id)
pulumi.export("availability_zones", azs)
pulumi.export(
    "public_subnet_ids",
    [s.id for s in public_subnets],
)
pulumi.export(
    "private_subnet_ids",
    [s.id for s in private_subnets],
)
pulumi.export(
    "nat_gateway_ids",
    [n.id for n in nat_gateways],
)
pulumi.export("nat_per_az", nat_per_az)
```

The code deliberately does not launch EC2 instances. That keeps the lab focused on network architecture and avoids adding compute costs before you've inspected the design.

A few important details:

* Public subnets route `0.0.0.0/0` to the Internet Gateway.

* Private subnets route `0.0.0.0/0` to a NAT Gateway.

* `map_public_ip_on_launch=False` prevents automatic public IPv4 assignment for newly launched instances in the private subnets.

* The NAT Gateway is created in a public subnet and depends on the Internet Gateway.

* Route-table associations explicitly bind each subnet to the intended route table.

The code establishes routing, but it does not itself create security groups or workloads. You must still configure network security and deploy a test workload before verifying application-level connectivity.

### 10.4 Deploy and inspect the topology

First, preview the changes:

```bash
pulumi config set natPerAz true
pulumi preview
```

Inspect the planned resources and their replacements. Then deploy:

```bash
pulumi up
```

Confirm the resource outputs:

```bash
pulumi stack output vpc_id
pulumi stack output availability_zones
pulumi stack output nat_gateway_ids
pulumi stack output private_subnet_ids
```

Wait until the NAT Gateways report an `Available` state before attempting outbound tests.

Use the AWS CLI to inspect the NAT Gateways:

```bash
aws ec2 describe-nat-gateways \
  --filter Name=vpc-id,Values="$(pulumi stack output vpc_id)" \
  --query 'NatGateways[].{Id:NatGatewayId,State:State,Subnet:SubnetId,IPs:NatGatewayAddresses[].PublicIp}'
```

Inspect the route tables:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values="$(pulumi stack output vpc_id)" \
  --query 'RouteTables[].{Id:RouteTableId,Routes:Routes[].{Destination:DestinationCidrBlock,Gateway:GatewayId,NAT:NatGatewayId,State:State}}'
```

The key verification is that both private route tables target different NAT Gateway IDs in per-AZ mode, while the public route table points its default IPv4 route to the Internet Gateway.

### 10.5 Compare the two configurations

For the shared configuration:

```bash
pulumi config set natPerAz false
pulumi preview
pulumi up
```

Pulumi will update the topology to use one NAT Gateway. Review the preview before approving the update because resource changes can interrupt existing connections.

Inspect the private route tables again. Both should now point to the same NAT Gateway.

Return to the two-AZ design when you want the stronger zonal isolation:

```bash
pulumi config set natPerAz true
pulumi preview
pulumi up
```

This comparison changes the routing architecture without changing the VPC's CIDR plan or the private subnets.

### 11\. Verify real outbound connectivity

The Pulumi lab above establishes the network path, but it does not prove that a workload can successfully connect. To verify connectivity, deploy a temporary EC2 instance into one of the private subnets and give it an appropriate security group.

For a safer operational pattern, use an SSM-managed instance if your environment has the required Systems Manager connectivity and permissions. This avoids opening SSH to the internet.

Your test instance needs:

* No public IPv4 address.

* A private-subnet route to the NAT Gateway.

* Outbound security-group rules allowing the test traffic.

* Network ACLs that permit the traffic and return packets.

* A suitable way to access the instance for testing, such as Systems Manager.

From the instance, test DNS resolution and HTTPS:

```bash
# Check DNS resolution
getent hosts example.com

# Test outbound HTTPS
curl -I --connect-timeout 5 https://example.com

# Check the route table associated with the subnet
ip route
```

These commands run on a Linux test instance, not in your Windows PowerShell terminal.

A successful HTTPS request confirms that the workload can resolve the destination and establish an outbound connection. It does not prove that every destination or protocol is reachable.

To verify that the workload has no direct public IPv4 address, inspect its network interface or instance metadata through the AWS CLI.

```bash
aws ec2 describe-instances \
  --filters Name=subnet-id,Values=<private-subnet-id> \
  --query 'Reservations[].Instances[].{Id:InstanceId,PrivateIP:PrivateIpAddress,PublicIP:PublicIpAddress,State:State.Name}'
```

Replace `<private-subnet-id>` with the actual ID from your Pulumi outputs.

### 12\. Troubleshooting outbound connectivity

Use a layered diagnostic process instead of immediately assuming the NAT Gateway is broken.

1\. Routing

Verify the private subnet's associated route table and its `0.0.0.0/0` target. Confirm the target NAT Gateway exists and is available.

2\. NAT and public routing

Confirm the NAT Gateway is public, resides in the intended public subnet, has an Elastic IP, and can route through the Internet Gateway.

3\. Security controls

Check outbound security-group rules, return-traffic behavior, subnet network ACLs, and any network firewall or proxy between the workload and destination.

4\. DNS and application behavior

If DNS fails, investigate resolution separately. If DNS succeeds but HTTPS fails, check destination reachability, port 443, TLS, proxies, and application errors.

### Useful AWS CLI commands

Check NAT Gateway state and addresses:

```bash
aws ec2 describe-nat-gateways \
  --nat-gateway-ids <nat-gateway-id>
```

Inspect route-table associations:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=<vpc-id>
```

Inspect subnet configuration:

```bash
aws ec2 describe-subnets \
  --subnet-ids <private-subnet-id>
```

Inspect NAT Gateway CloudWatch metrics such as `BytesOutToDestination`, `BytesInFromDestination`, and connection-related metrics:

```bash
aws cloudwatch list-metrics \
  --namespace AWS/NATGateway
```

For deeper diagnosis, use VPC Flow Logs and CloudWatch NAT Gateway metrics. Flow Logs can help identify accepted and rejected traffic at the monitored network interface, but they do not capture every possible failure or explain all application-layer problems.

### Common symptoms

| Symptom                                   | What to investigate first                                                                   |
| ----------------------------------------- | ------------------------------------------------------------------------------------------- |
| DNS resolution fails                      | VPC DNS settings, resolver configuration, DNS security rules                                |
| DNS works but HTTPS times out             | Default route, NAT state, security groups, network ACLs                                     |
| NAT Gateway is unavailable                | NAT deployment state, subnet, Elastic IP and dependencies                                   |
| One AZ works but another fails            | Private route-table association and NAT target for each AZ                                  |
| AWS API calls work but external APIs fail | Endpoint routing, DNS differences, external destination restrictions                        |
| Intermittent outbound failures            | Connection limits, NAT metrics, packet drops, destination behavior, and application retries |

### 13\. Security and production design recommendations

For a production VPC, I would use the following decision process:

* Identify destinations first. Do not send all traffic through NAT if a gateway endpoint or interface endpoint is a better fit.

* Prefer zonal affinity or a supported Regional NAT Gateway design. Evaluate failure domains, cross-AZ charges, and regional support.

* Control egress deliberately. NAT translates addresses; it is not a domain allowlist or an egress firewall.

* Avoid public addresses on private workloads unless there is a specific reason.

* Monitor traffic and cost. Set budgets and review NAT data-processing usage.

* Make failover explicit. Don't assume a route will automatically move to another zonal NAT Gateway.

* Treat IPv6 independently. IPv6 routing and security controls must be configured even when IPv4 NAT is already working.

For a SaaS application with two AZs, I would start with one zonal NAT Gateway per AZ when explicit zonal control is needed, or evaluate Regional NAT Gateways where their capabilities and pricing fit. I'd add gateway endpoints for S3 and DynamoDB where appropriate and consider interface endpoints for other AWS APIs that generate significant traffic.

### 14\. Cleanup

Do not leave this lab running unnecessarily. NAT Gateways are billable even when idle.

If you've deployed the Pulumi stack, remove its resources with:

```bash
pulumi destroy
```

Review the planned deletions and approve them. Verify that the NAT Gateways and Elastic IP allocations created by this stack are released.

If you launched a separate test instance or created any resources outside Pulumi, delete those separately. Do not delete shared resources that existed before the lab.

### 15\. Official references

* [NAT Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-gateway.html?utm_source=chatgpt.com)

* [NAT Gateway basics](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-basics.html?utm_source=chatgpt.com)

* [Regional NAT Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateways-regional.html?utm_source=chatgpt.com)

* [NAT Gateway pricing](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-pricing.html?utm_source=chatgpt.com)

* [NAT Gateway vs. NAT instance](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-nat-comparison.html?utm_source=chatgpt.com)

* [Egress-Only Internet Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html?utm_source=chatgpt.com)

* [Gateway endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html?utm_source=chatgpt.com)

* [AWS PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/?utm_source=chatgpt.com)

* [Pulumi AWS provider](https://www.pulumi.com/registry/packages/aws/?utm_source=chatgpt.com)

### Module 4 summary

You now have the core model for designing controlled outbound connectivity: IPv4 workloads can use NAT Gateways, IPv6 workloads can use Egress-Only Internet Gateways, and supported AWS services can often be accessed through VPC endpoints instead of general internet egress.

The most important operational lesson is that routing, availability, security, and cost must be designed together. A working NAT Gateway alone does not guarantee a secure or resilient egress architecture.
