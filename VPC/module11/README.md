### Module 11 — IPv6 and Modern IP Address Management

This module follows your AWS VPC course curriculum, using Pulumi with Python, AWS CLI v2, hands-on implementation, and current AWS networking practices. We'll focus on how IPv6 works in Amazon VPC, how to introduce it safely into an existing IPv4 network, and how to manage address space at scale with Amazon VPC IP Address Manager (IPAM).

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Distinguish dual-stack, IPv6-only, and IPv4-only architectures.

* Design IPv6 CIDR allocations for VPCs and subnets.

* Configure IPv6 routes, security groups, and outbound connectivity.

* Understand egress-only internet gateways and NAT64/DNS64.

* Diagnose IPv6 DNS and connectivity failures.

* Evaluate IPv4 address exhaustion and public IPv4 costs.

* Use Amazon VPC IPAM for centralized allocation, tracking, and governance.

* Plan a gradual IPv6 migration without disrupting existing workloads.

### 2\. IPv6 fundamentals in AWS

### 2.1 Why IPv6 matters

IPv4 uses 32-bit addresses, providing approximately 4.3 billion possible addresses before accounting for reserved ranges and allocation constraints. IPv6 uses 128-bit addresses, providing a vastly larger address space.

An IPv6 address consists of eight 16-bit hexadecimal groups.

Example:

```text
2001:0db8:1234:0001:0000:0000:0000:0010
```

It can be shortened to:

```text
2001:db8:1234:1::10
```

Rules for shortening IPv6 addresses:

* Leading zeros in a group can be omitted.

* One continuous sequence of zero groups can be replaced with `::`.

* `::` can appear only once in an address.

The `2001:db8::/32` range is reserved for documentation and examples. It is not an address range to deploy for real internet connectivity.

### 2.2 IPv4 versus IPv6

| Property                   | IPv4                      | IPv6                                                |
| -------------------------- | ------------------------- | --------------------------------------------------- |
| Address size               | 32 bits                   | 128 bits                                            |
| Example                    | 10.0.1.10                 | 2001:db8:1234:1::10                                 |
| Typical private addressing | RFC 1918 addresses        | Unique local addresses or AWS-assigned IPv6 ranges  |
| Subnet size                | Variable, often /24       | Commonly /64                                        |
| NAT for outbound access    | Commonly used             | Often unnecessary for globally addressed workloads  |
| Security controls          | Security groups and NACLs | Security groups and NACLs, with IPv6-specific rules |
| DNS record                 | A                         | AAAA                                                |

An important distinction: IPv6 does not eliminate the need for firewalls. A globally routable IPv6 address does not automatically mean the instance accepts inbound connections, but security groups and routing must be configured correctly to prevent unwanted access.

### 2.3 How IPv6 fits into a VPC

A dual-stack VPC can have both IPv4 and IPv6 CIDR blocks. An Elastic Network Interface (ENI) can have IPv4 and IPv6 addresses, subject to the capabilities and configuration of the service using it.

```text
                    Internet
                   /        \
             IPv4 traffic   IPv6 traffic
                 |               |
             Internet GW     Internet GW
                 |               |
          +---------------------------+
          |       Dual-stack VPC      |
          |                           |
          |  Public subnet            |
          |  IPv4 + IPv6 addresses    |
          |            |              |
          |       Load balancer       |
          |            |              |
          |  Private application      |
          |  subnet                   |
          |            |              |
          |       Application         |
          |            |              |
          |  Isolated database subnet |
          +---------------------------+
```

This diagram illustrates the logical architecture. Actual IPv4 and IPv6 paths depend on each subnet's route table, the resource's addressing, security rules, and service support.

An IPv4 default route and an IPv6 default route are separate routes:

```text
0.0.0.0/0  -> igw-...     # IPv4
::/0       -> igw-...     # IPv6
```

Adding one does not create the other.

### 3\. Dual-stack versus IPv6-only architectures

These are two different migration strategies, and choosing the right one affects application compatibility, routing, security, and cost.

![Architect dual stack Amazon VPC with multiple IPv6 CIDR blocks | Networking & Content Delivery](https://images.openai.com/static-rsc-4/-qNz4lP22LEiQVcTirj25oCeCLLTTZzgLj8nANY2Cf7rKGQjGvOT2VzjNpkMlxSeOLyU6hU7MTw0-KX4R_8lQyTYwD_2s3X2NA-DUm6pGUmNUzaN1uiBdnysS3DmctTwaMXBiJ3pxZoW2Pk65waIjUxpaGnTkoAB4ZGBYVrpd-bgoWfG2jKC1W_02w3u_SlD?purpose=fullsize)

A. Dual-stack

Best starting point for many migrations

Resources have IPv4 and IPv6 connectivity where supported. Existing IPv4 clients can continue working while IPv6-capable clients use IPv6.

Advantages: gradual migration, broad compatibility, simpler rollback.

Trade-off: you still operate and secure both protocol families.

![Let's talk about IPv6 DNS64 & DNSSEC | APNIC Blog](https://images.openai.com/static-rsc-4/26jzI4WRqavtUXy9Nj6MxFweAYamIQS6PTMgjpF8KWubK24Erk3-tkELdb3doFhU6J564DqhsaQE_EtgTQPrS4R13_KqTY8iPpoPkEs2v-ZvRLxnxX_GQhKAuDaLUryrZc7S7wo5IMie6w1LUvrLPMrJ4Qcjyk6UbxO_XNT05ugYL600HjnOqxQvnzgTzRZ7?purpose=fullsize)

B. IPv6-only

Workloads use IPv6 addresses, without assigning them IPv4 addresses. Access to IPv4-only destinations may require DNS64/NAT64 or another supported translation path.

Advantages: reduces demand for private IPv4 addresses and can simplify address planning.

Trade-off: application dependencies, DNS, load balancers, monitoring, and AWS service endpoints must support the intended configuration.

An IPv6-only subnet is not simply a dual-stack subnet with its IPv4 route deleted. You must configure subnet addressing appropriately, verify the resource type supports IPv6-only operation, and account for services that still require IPv4.

### 3.1 Choosing an architecture

| Workload                               | Practical starting point                                                              |
| -------------------------------------- | ------------------------------------------------------------------------------------- |
| Existing web application               | Dual-stack                                                                            |
| Existing database tier                 | Keep the existing protocol until database connectivity and dependencies are validated |
| New service with verified IPv6 support | Consider IPv6-only                                                                    |
| Workload calling legacy IPv4 APIs      | Dual-stack or IPv6-only with an appropriate translation path                          |
| Internet-facing application            | Choose address families based on client requirements and load-balancer support        |
| Large multi-account AWS estate         | Establish IPAM governance and an IPv6 adoption plan                                   |

Key principle: enable IPv6 because it meets a defined architectural need, not merely because an address block is available.

### 4\. IPv6 CIDR allocation and subnet design

### 4.1 AWS IPv6 CIDRs

For many VPC designs, AWS can associate an Amazon-provided IPv6 CIDR block with a VPC. You then allocate IPv6 ranges to subnets from the VPC's IPv6 range.

A commonly encountered VPC allocation is `/56`, while VPC subnet IPv6 ranges are typically `/64`. The precise choices available depend on the allocation source and AWS feature.

Consider this example:

```text
VPC IPv4: 10.20.0.0/16
VPC IPv6: 2001:db8:1234:ab00::/56  # Documentation example only

                  /64 per subnet
        ┌──────────────────────────┐
        │ Public AZ-a              │
        │ 10.20.1.0/24              │
        │ IPv6 subnet /64           │
        ├──────────────────────────┤
        │ Private AZ-a             │
        │ 10.20.11.0/24             │
        │ IPv6 subnet /64           │
        ├──────────────────────────┤
        │ Private AZ-b             │
        │ 10.20.12.0/24             │
        │ IPv6 subnet /64           │
        └──────────────────────────┘
```

The IPv6 addresses above illustrate the allocation strategy, not deployable addresses. In a real environment, use the IPv6 block AWS allocates or an eligible block you bring to AWS.

Why `/64`? It is the standard subnet size for many AWS IPv6 subnet configurations and provides an enormous number of addresses. Unlike IPv4 subnet design, IPv6 subnet sizing is generally about allocating clean prefixes and meeting service requirements, rather than conserving individual host addresses.

### 4.2 Planning a hierarchy

For a multi-environment deployment, reserve space by Region and environment before creating individual VPCs.

| Allocation level        | Example purpose                    |
| ----------------------- | ---------------------------------- |
| Organization-level pool | Central address governance         |
| Regional pool           | Separate allocations by AWS Region |
| Environment pool        | Development, staging, production   |
| VPC allocation          | A dedicated VPC prefix             |
| Subnet allocation       | /64 subnet ranges within the VPC   |

This hierarchy reduces accidental overlaps and makes future growth easier. AWS IPAM can manage the allocation process rather than relying on a spreadsheet alone.

### 5\. IPv6 routing and outbound connectivity

IPv6 has distinct routing behavior and must be configured separately from IPv4.

### 5.1 Internet gateway routing

For a subnet that should support direct IPv6 internet connectivity, the relevant route table commonly includes:

```text
Destination       Target
-----------       ------
10.20.0.0/16      local
2001:...::/56     local
0.0.0.0/0         igw-0123456789abcdef0
::/0              igw-0123456789abcdef0
```

The IPv4 route and IPv6 route serve different traffic. A route table with `::/0` pointing to an internet gateway provides an IPv6 path, but it does not by itself ensure that a resource is reachable from the internet. Address assignment, security groups, network ACLs, and the destination's behavior also matter.

### 5.2 Egress-only internet gateway

An egress-only internet gateway (EIGW) allows IPv6 workloads in a VPC to initiate outbound connections to the internet while preventing unsolicited inbound internet connections through that gateway.

Example private-subnet routing:

```text
IPv6 workload
     |
     v
Private subnet route table
     |
     | ::/0
     v
Egress-only internet gateway
     |
     v
IPv6 internet destination
```

The corresponding route looks like this:

```text
Destination    Target
-----------    ------
::/0           eigw-0123456789abcdef0
```

Use an EIGW when a workload needs outbound IPv6 connectivity but should not accept new, unsolicited inbound connections through its internet egress path.

It is not a general-purpose firewall replacement, nor does it replace the need for security groups and network ACLs. It is also not an IPv4 NAT gateway.

### 5.3 Which gateway should you choose?

| Requirement                                               | Appropriate design                                         |
| --------------------------------------------------------- | ---------------------------------------------------------- |
| Public IPv4 and IPv6 connectivity                         | Internet gateway and suitable routes for both families     |
| Private workload initiating IPv6 internet connections     | Egress-only internet gateway                               |
| Private IPv4 workload reaching IPv4 internet destinations | NAT gateway or another suitable IPv4 egress design         |
| IPv6-only workload reaching IPv4-only destinations        | DNS64/NAT64 with a suitable NAT gateway and routes         |
| Private access to supported AWS services                  | Consider VPC endpoints rather than general internet egress |

An EIGW does not translate IPv6 to IPv4. That distinction becomes important when designing IPv6-only workloads.

### 6\. DNS64 and NAT64

Some services remain IPv4-only. An IPv6-only workload cannot communicate with such a destination through native IPv6 alone.

AWS supports a translation pattern using DNS64 and NAT64. DNS64 synthesizes an IPv6 address for a destination that has only an IPv4 DNS record; the NAT gateway then translates the traffic to IPv4.

### IPv6-only workload → IPv4-only API

IPv6-only application

DNS query

DNS64 synthesizes an IPv6 destination

IPv6 packet to the NAT64 prefix

NAT gateway translates IPv6 traffic to IPv4

IPv4-only destination

AWS implementation requirements include:

* An IPv6-only subnet with DNS64 enabled.

* A suitable NAT gateway in a subnet with IPv4 connectivity.

* An IPv6 route for the NAT64 traffic, commonly the well-known translation prefix `64:ff9b::/96`, pointing to the NAT gateway.

* A route from the NAT gateway's subnet to the IPv4 destination, typically through an internet gateway for internet destinations.

* Appropriate security and network rules along the path.

AWS's official [DNS64 and NAT64 documentation](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-nat64-dns64.html?utm_source=chatgpt.com) provides the configuration details.

Important limitations: NAT64 is not a universal compatibility layer for every application. Hard-coded IPv4 literals, protocol assumptions, unsupported endpoints, and DNS behavior can prevent a workload from working correctly. Validate the actual client libraries and dependencies before removing IPv4 addresses.

### 7\. Public IPv4 costs and IPv4 exhaustion

IPv6 helps address IPv4 scarcity, but adopting IPv6 does not automatically remove IPv4 charges from a dual-stack architecture.

AWS charges for public IPv4 addresses under its public IPv4 pricing model. This can affect Elastic IP addresses, automatically assigned public IPv4 addresses, and public addresses used by certain services. Exact charges depend on the resource, Region, and current pricing rules.

Review the official [Amazon VPC pricing page](https://aws.amazon.com/vpc/pricing/?utm_source=chatgpt.com) before deploying a lab.

### 7.1 Cost-reduction strategy

A sensible migration sequence is:

* Inventory public IPv4 addresses and identify why each is needed.

* Enable IPv6 for suitable workloads.

* Test client compatibility, monitoring, DNS, and security controls.

* Remove public IPv4 assignments only when the workload no longer needs them.

* Review NAT gateways, load balancers, endpoints, and other network resources for unnecessary cost.

* Monitor public IPv4 usage and charges over time.

Remember that IPv6 adoption may reduce address pressure without reducing every networking cost. For example, an IPv6-only application that must access IPv4-only internet services through NAT64 still needs a NAT gateway.

### 8\. Amazon VPC IP Address Manager (IPAM)

IPAM is AWS's centralized service for planning, allocating, tracking, and monitoring IP address space. It can manage IPv4 and IPv6 address allocations, help detect noncompliant CIDR assignments, and support cross-account network governance.

### 8.1 The problem IPAM solves

Imagine a company has 30 AWS accounts, several Regions, and separate development and production environments.

Without centralized allocation:

* Two teams might independently choose overlapping VPC CIDRs.

* Nobody may know how much address space remains.

* New VPCs might violate organizational allocation rules.

* Investigating which account owns a CIDR can take time.

IPAM provides a managed allocation hierarchy and a view of address utilization.

### 8.2 IPAM terminology

IPAM

Central management and monitoring service

Scope

Separates address-management contexts. IPAM creates a default private scope and a default public scope.

Top-level pool

Contains the organization's larger address allocation.

Regional pool

Makes address space available for a specific Region.

Environment pool → VPC allocation

Separates development and production address space, then allocates a CIDR to a VPC.

AWS distinguishes between two operations:

* Provision: add a CIDR range to an IPAM pool.

* Allocate: assign part of that pool's available space to a resource or child pool.

These are important lifecycle concepts when managing address space through the AWS console, CLI, or infrastructure as code.

### 8.3 Example allocation policy

A production organization might use a structure like this:

| Pool                | Illustrative purpose                           |
| ------------------- | ---------------------------------------------- |
| Global private pool | Organization-wide private IPv4 address space   |
| Region A pool       | VPCs in one AWS Region                         |
| Production pool     | Production VPC allocations                     |
| Non-production pool | Development and staging allocations            |
| IPv6 pool           | Centrally managed IPv6 space for eligible VPCs |

Pools can use allocation rules to enforce requirements such as permitted netmask lengths, required resource tags, and Region-specific placement. Pools can also be shared across accounts using AWS Resource Access Manager (RAM), subject to the relevant permissions and organizational setup.

### 8.4 IPAM monitoring and governance

Use IPAM to answer operational questions such as:

* Which VPC owns this CIDR?

* Which allocations belong to a particular pool?

* How much address space remains available?

* Are VPC allocations compliant with pool rules?

* Where are address assignments concentrated?

* Which teams or accounts are consuming the available ranges?

For current pool utilization and allocation details, see the official [IPAM allocation documentation](https://docs.aws.amazon.com/vpc/latest/ipam/view-alloc-ipam.html?utm_source=chatgpt.com).

One important distinction: IPAM is an address-management and governance service. It does not replace VPC route tables, security groups, DNS configuration, or network connectivity testing.

### 9\. Hands-on lab — Add IPv6 to an existing VPC

We'll use Pulumi Python to create an isolated dual-stack VPC with public and private subnets, then verify IPv6 routing and security. This lab builds on the VPC concepts covered in earlier modules.

Before deploying

* A real AWS account and a configured AWS CLI v2 profile.

* Pulumi CLI and Python installed.

* Permission to create VPCs, subnets, route tables, an internet gateway, an egress-only internet gateway, and security groups.

* An AWS Region that supports the resources being created.

Cost note: VPCs, route tables, and security groups generally do not have hourly charges, but this lab's internet gateway does not itself incur an hourly gateway charge. Avoid launching EC2 instances unless needed. Public IPv4 addresses, NAT gateways, data transfer, and other added resources can incur charges.

### 9.1 Architecture

```text
                        Internet
                       /        \
                  IPv4            IPv6
                    |               |
                Internet Gateway
                       |
             +---------------------+
             |      Dual-stack     |
             |         VPC         |
             |                     |
             | Public subnet       |
             | IPv4 + IPv6          |
             |                     |
             | Private subnet      |
             | IPv4 + IPv6          |
             |       |             |
             |       +-- EIGW -----+--> IPv6 outbound
             +---------------------+
```

For this lab, the private subnet will have IPv6 outbound routing through an egress-only internet gateway. It will not have a public IPv4 route through a NAT gateway.

### 9.2 Create the Pulumi project

Project structure:

```text
vpc-ipv6-lab/
├── Pulumi.yaml
├── requirements.txt
└── __main__.py
```

`Pulumi.yaml`:

```yaml
name: vpc-ipv6-lab
runtime:
  name: python
description: Dual-stack AWS VPC and IPv6 routing lab
```

`requirements.txt`:

```text
pulumi
pulumi-aws
```

Create the environment and install dependencies:

```powershell
mkdir vpc-ipv6-lab
cd vpc-ipv6-lab

pulumi new aws-python
```

Alternatively, create the three files manually, then create a stack and install the dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt

pulumi stack init dev
pulumi config set aws:region eu-west-3
```

Choose a Region supported by your account and resources; `eu-west-3` is Paris. If you used `pulumi new aws-python`, follow the generated project's setup instructions and keep its configuration where appropriate.

### 9.3 Implement the network

The following example creates a VPC with an Amazon-provided IPv6 CIDR, one public subnet, one private subnet, and separate IPv4 and IPv6 routes. The subnets are placed in distinct Availability Zones where the Region offers the selected zones.

`__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
azs = aws.get_availability_zones(state="available")

vpc = aws.ec2.Vpc(
    "ipv6-vpc",
    cidr_block="10.40.0.0/16",
    assign_generated_ipv6_cidr_block=True,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "ipv6-lab-vpc"},
)

igw = aws.ec2.InternetGateway(
    "ipv6-igw",
    vpc_id=vpc.id,
)

public_subnet = aws.ec2.Subnet(
    "ipv6-public-subnet",
    vpc_id=vpc.id,
    cidr_block="10.40.1.0/24",
    availability_zone=azs.names[0],
    ipv6_cidr_block=(
        vpc.ipv6_cidr_block.apply(
            lambda cidr: cidr.replace("::/56", "::/64")
        )
    ),
    assign_ipv6_address_on_creation=True,
    map_public_ip_on_launch=False,
    tags={"Name": "ipv6-lab-public"},
)

private_subnet = aws.ec2.Subnet(
    "ipv6-private-subnet",
    vpc_id=vpc.id,
    cidr_block="10.40.11.0/24",
    availability_zone=azs.names[1],
    ipv6_cidr_block=(
        vpc.ipv6_cidr_block.apply(
            lambda cidr: cidr.replace("::/56", ":1::/64")
        )
    ),
    assign_ipv6_address_on_creation=True,
    tags={"Name": "ipv6-lab-private"},
)

public_rt = aws.ec2.RouteTable(
    "ipv6-public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
        aws.ec2.RouteTableRouteArgs(
            ipv6_cidr_block="::/0",
            gateway_id=igw.id,
        ),
    ],
)

private_rt = aws.ec2.RouteTable(
    "ipv6-private-rt",
    vpc_id=vpc.id,
)

eigw = aws.ec2.EgressOnlyInternetGateway(
    "ipv6-eigw",
    vpc_id=vpc.id,
)

# The private subnet can initiate IPv6 connections outward.
private_ipv6_route = aws.ec2.Route(
    "private-ipv6-egress",
    route_table_id=private_rt.id,
    destination_ipv6_cidr_block="::/0",
    egress_only_gateway_id=eigw.id,
)

public_assoc = aws.ec2.RouteTableAssociation(
    "public-route-association",
    subnet_id=public_subnet.id,
    route_table_id=public_rt.id,
)

private_assoc = aws.ec2.RouteTableAssociation(
    "private-route-association",
    subnet_id=private_subnet.id,
    route_table_id=private_rt.id,
)

pulumi.export("vpc_id", vpc.id)
pulumi.export("vpc_ipv6_cidr", vpc.ipv6_cidr_block)
pulumi.export("public_subnet_id", public_subnet.id)
pulumi.export("private_subnet_id", private_subnet.id)
pulumi.export("public_route_table_id", public_rt.id)
pulumi.export("private_route_table_id", private_rt.id)
```

Important correction before running: do not derive IPv6 subnet CIDRs with string replacement as shown in the illustrative snippet above. AWS-assigned IPv6 CIDRs must be subdivided correctly as CIDR networks, not by editing their textual representation. The safe approach is to calculate subnet prefixes using an IPv6-aware network library, then associate the resulting valid `/64` blocks.

Use this implementation for subnet allocation instead.

Add `netaddr` to `requirements.txt`:

```text
pulumi
pulumi-aws
netaddr
```

Then replace the two `ipv6_cidr_block` expressions with:

```python
from netaddr import IPNetwork, IPSet

def ipv6_subnet_cidrs(vpc_cidr: str) -> list[str]:
    network = IPNetwork(vpc_cidr)
    if network.prefixlen > 64:
        raise ValueError("VPC IPv6 prefix must be /64 or larger")
    return [str(subnet) for subnet in network.subnet(64)]

# After the VPC is created:
ipv6_blocks = vpc.ipv6_cidr_block.apply(ipv6_subnet_cidrs)
```

Because Pulumi outputs are asynchronous, select the subnet CIDRs with `.apply()`:

```python
ipv6_cidr_block=ipv6_blocks.apply(lambda blocks: blocks[0])
```

For the private subnet:

```python
ipv6_cidr_block=ipv6_blocks.apply(lambda blocks: blocks[1])
```

This avoids assuming the textual format of AWS's allocated IPv6 block. For a production implementation, also validate that the selected prefix contains enough `/64` subnets and that the Availability Zones are distinct.

### 9.4 Deploy and verify

Review the proposed changes before deployment:

```powershell
pulumi preview
```

Deploy:

```powershell
pulumi up
```

Inspect the VPC:

```powershell
aws ec2 describe-vpcs `
  --filters "Name=tag:Name,Values=ipv6-lab-vpc" `
  --query "Vpcs[].{VpcId:VpcId,IPv4:CidrBlock,IPv6:Ipv6CidrBlockAssociationSet[].Ipv6CidrBlock}"
```

Inspect subnet IPv6 assignments:

```powershell
aws ec2 describe-subnets `
  --filters "Name=vpc-id,Values=<VPC_ID>" `
  --query "Subnets[].{SubnetId:SubnetId,AZ:AvailabilityZone,IPv4:CidrBlock,IPv6:Ipv6CidrBlockAssociationSet[].Ipv6CidrBlock}"
```

Inspect routes:

```powershell
aws ec2 describe-route-tables `
  --filters "Name=vpc-id,Values=<VPC_ID>" `
  --query "RouteTables[].{Id:RouteTableId,Routes:Routes}"
```

Replace `<VPC_ID>` with the exported ID from Pulumi.

Expected results:

* The VPC has both IPv4 and IPv6 CIDRs.

* Both subnets have valid IPv6 `/64` ranges.

* The public route table contains IPv4 and IPv6 default routes to the internet gateway.

* The private route table has an IPv6 default route through the egress-only internet gateway.

* No private IPv4 internet route exists in this lab.

The existence of these routes does not prove that application connectivity works. Actual traffic testing requires an appropriately configured workload and security rules.

### 10\. Security and production considerations

IPv6 needs its own security review. Do not assume existing IPv4 controls automatically protect IPv6 traffic.

### 10.1 Security group rules

For an IPv6-enabled web service, a security group might allow HTTPS from IPv6 clients:

```python
web_sg = aws.ec2.SecurityGroup(
    "ipv6-web-sg",
    vpc_id=vpc.id,
    description="Allow HTTPS from IPv6 clients",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            description="HTTPS over IPv6",
            protocol="tcp",
            from_port=443,
            to_port=443,
            ipv6_cidr_blocks=["2001:db8:1234::/48"],
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            description="Allow outbound IPv6",
            protocol="-1",
            from_port=0,
            to_port=0,
            ipv6_cidr_blocks=["::/0"],
        ),
    ],
)
```

The CIDR above is an example only. Replace it with a real, authorized client range. For a public website, use an appropriate public client range and consider whether the application should instead be exposed through a load balancer.

Also note that this security group is illustrative: attaching it to a workload is a separate step, and the egress rule is broad. Production egress rules should be restricted when practical.

### 10.2 Production checklist

* Review IPv4 and IPv6 ingress rules independently.

* Confirm network ACL rules permit the required traffic and return paths.

* Verify the correct route table is associated with each subnet.

* Validate DNS `A` and `AAAA` records and client address-selection behavior.

* Test the actual application path rather than relying solely on route inspection.

* Check whether third-party APIs, agents, and monitoring systems support IPv6.

* Review public IPv4 usage and charges before removing any addresses.

* Ensure IPAM allocation policies match your organization's account and Region boundaries.

* Document rollback steps before migrating critical workloads.

### 11\. Troubleshooting IPv6 connectivity

| Symptom                                | Common causes                                           | What to inspect                             |
| -------------------------------------- | ------------------------------------------------------- | ------------------------------------------- |
| IPv6 address missing                   | IPv6 CIDR not associated or subnet not configured       | describe-vpcs, describe-subnets             |
| Outbound IPv6 fails                    | Missing ::/0, wrong gateway, security rules             | Route tables, security groups, NACLs        |
| Inbound IPv6 fails                     | Missing route or ingress permission                     | Internet gateway route and security group   |
| DNS returns only IPv4                  | No AAAA record or DNS64 not enabled                     | DNS records and resolver configuration      |
| IPv6-only client cannot reach IPv4 API | Missing DNS64/NAT64 path or application incompatibility | DNS answers, NAT gateway, routes            |
| VPC CIDR allocation fails              | Pool unavailable, wrong Region, exhausted address space | IPAM pool state, locale, allocations        |
| New VPC gets an unexpected CIDR        | Incorrect pool selection or allocation policy           | IPAM pools, allocation rules, resource tags |

Useful commands:

```powershell
aws ec2 describe-egress-only-internet-gateways
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<VPC_ID>"
aws ec2 describe-security-groups --filters "Name=vpc-id,Values=<VPC_ID>"
aws ec2 describe-ipam-pools
aws ec2 describe-ipam-pool-allocations --ipam-pool-id <IPAM_POOL_ID>
```

For DNS testing from a Linux workload:

```bash
dig AAAA example.com
getent ahosts example.com
curl -6 -v https://example.com/
```

These tests check different things: DNS resolution, system resolver behavior, and actual IPv6 HTTPS connectivity. A successful DNS query alone does not establish network reachability.

### 12\. Cleanup

After you finish testing, remove the lab resources if you no longer need them.

First inspect the planned deletion:

```powershell
pulumi preview --diff
```

Then destroy the stack resources:

```powershell
pulumi destroy
```

Review the proposed deletions carefully before approving. This lab is intended to contain only its own VPC resources; never use these commands against a shared or production stack without an explicit deletion review.

IPAM resources created separately are not necessarily part of this stack. Review and remove any separately created pools or IPAM resources only if they are no longer used by other workloads.

### 13\. Official AWS references

The following documentation is useful for deeper study and implementation details.

* [IPv6 addressing in your VPC](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ip-addressing.html?utm_source=chatgpt.com)

* [Egress-only internet gateways](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html?utm_source=chatgpt.com)

* [DNS64 and NAT64](https://docs.aws.amazon.com/vpc/latest/userguide/nat-gateway-nat64-dns64.html?utm_source=chatgpt.com)

* [What is Amazon VPC IPAM?](https://docs.aws.amazon.com/vpc/latest/ipam/what-it-is-ipam.html?utm_source=chatgpt.com)

* [How IPAM works](https://docs.aws.amazon.com/vpc/latest/ipam/how-it-works-ipam.html?utm_source=chatgpt.com)

* [Planning IP address provisioning](https://docs.aws.amazon.com/vpc/latest/ipam/planning-ipam.html?utm_source=chatgpt.com)

* [Amazon VPC pricing](https://aws.amazon.com/vpc/pricing/?utm_source=chatgpt.com)

### Module 11 summary

The key operational takeaway is that IPv6 adoption involves more than adding an IPv6 CIDR. You must plan subnet allocations, configure routing independently for each protocol, validate security and DNS, and account for IPv4-only dependencies. For larger environments, IPAM provides a structured way to govern allocations across accounts and Regions.

The next module is Module 12 — VPC Observability and Troubleshooting, covering VPC Flow Logs, CloudWatch, Reachability Analyzer, Network Access Analyzer, DNS diagnostics, and systematic investigation of connectivity failures.
