### Module 3 — Subnets, Routes, and Internet Connectivity

This module builds on the VPC fundamentals from Module 2. We'll use Pulumi with Python to design a multi-Availability Zone VPC, understand how AWS decides where packets go, and configure public, private, and isolated subnets.

We'll use real AWS networking concepts and current AWS documentation, avoid quizzes, and identify billable resources before deploying anything.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Design public, private, and isolated subnets across multiple Availability Zones (AZs).

* Explain how main and explicitly associated route tables control packet forwarding.

* Configure Internet Gateways (IGWs), default routes, public IPv4 addresses, and Elastic IP addresses.

* Understand IPv6 internet connectivity and egress-only Internet Gateways.

* Distinguish static routes from propagated routes and troubleshoot route selection.

* Build, inspect, and safely destroy a multi-AZ VPC using Pulumi.

### 2\. Architecture: three subnet types

The most important idea is that a subnet is not inherently public or private. Its routing configuration determines its internet reachability, while public IP addressing and security controls determine whether a resource can actually communicate over the internet.

![06. Internet Gateway | KCnote Dev Blog](https://images.openai.com/static-rsc-4/s2btoDTVKfVwOjBcuCMBos8AafA3N2PkwkkXnYjByCiYTTE9ajB7Xah3mmTs0zetmNBMdT2pZKOSPXe7wDisyjmeQLdT-h-Ug945C2QFWfAFYbvPWbhsou9GYvyxDyVkrdafPD7Xi_1RRhgz43K0unR8zVLZSOuNwleXgDV_kcPYRT49qtFsL9wJlViFl9sI?purpose=fullsize)

Public subnet

Its associated route table has a route to an Internet Gateway for internet-bound IPv4 traffic, typically `0.0.0.0/0 → igw-...`. An instance generally also needs a public IPv4 address and permissive-enough security controls for direct internet communication.

![Example: VPC with servers in private subnets and NAT - Amazon Virtual Private Cloud](https://images.openai.com/static-rsc-4/jHifz1qN8MfVais0ivLSoB5c8P1PfMRCe9kFETBIUap4ESSo-SFH9OhlCKFjMc1CWs2Sby9tqxExvTolqB6U_0lqLmSt82sXPPUSuf2SuDgtMBSd4BFCUfMBt1TNV1u6AafZ0sx6NXssEtmEAEoY_FbW0vBDEzohcSgu-mbBWBAeBqmltJetZtj_xLg4okhi?purpose=fullsize)

Private subnet

Resources do not have direct inbound internet reachability through an Internet Gateway. A private subnet may have a route through a NAT Gateway for outbound IPv4 connections; we'll cover NAT Gateway design in Module 4.

![Terraforming an AWS VPC Part 4 - using modules](https://images.openai.com/static-rsc-4/s7S2M5HedTmdpnVbWB0sSZMQb0mB3AUxpe6qG8Ch-VrvujHZkyNdBQsz5erH-zpuL5BFVos-ej-ziv5pWG-VF2JyWgpHGdG5G91LUnUqKsB3N01RbVDXNhWbNAN2ku-0I6x5aMISFTHsK4hRQjvOPIzFvkS_Bhi99aKsW5ZN5C3vJ9URVvheVPwOAYnr-Qzq?purpose=fullsize)

Isolated subnet

Its route table contains only local VPC routes, plus any deliberately configured non-internet routes. There is no default route to an Internet Gateway or NAT Gateway. This is useful for databases and workloads that should not have general internet connectivity.

A subnet with no Internet Gateway route isn't automatically secure against all unwanted traffic. Security groups, network ACLs, routing to other networks, and application-level controls still matter.

### 3\. Multi-AZ architecture

We'll build a VPC spanning two Availability Zones. Each AZ gets a public, private, and isolated subnet, with an explicit route-table association for every subnet.

### VPC — 10.20.0.0/16

One regional virtual network

Internet Gateway

Attached to the VPC

### Availability Zone A

Public subnet

10.20.1.0/24

Route: 0.0.0.0/0 → IGW

Private subnet

10.20.11.0/24

No direct IGW route

Isolated subnet

10.20.21.0/24

Local route only

### Availability Zone B

Public subnet

10.20.2.0/24

Route: 0.0.0.0/0 → IGW

Private subnet

10.20.12.0/24

No direct IGW route

Isolated subnet

10.20.22.0/24

Local route only

Conceptual architecture. The lab initially omits NAT Gateways and IPv6 to keep the deployment small and focused.

Why two AZs?

* Availability: resources can be deployed in separate failure domains.

* Resilience: an application can continue serving traffic if one AZ becomes unavailable, provided the application itself is deployed redundantly.

* Segmentation: workloads can have different routing policies according to their role.

* Independent scaling: subnet address capacity can be allocated separately per AZ.

A subnet belongs to exactly one AZ. A VPC can contain subnets in multiple AZs within its Region. AWS recommends multi-AZ deployment for resilient applications.

### 4\. Route tables: how AWS chooses a path

A route table contains destination prefixes and their targets.

| Destination  | Target                       | Meaning                                                                                                |
| ------------ | ---------------------------- | ------------------------------------------------------------------------------------------------------ |
| 10.20.0.0/16 | local                        | Route traffic within the VPC                                                                           |
| 0.0.0.0/0    | Internet Gateway             | Send otherwise-unmatched IPv4 traffic toward the internet                                              |
| 10.30.0.0/16 | VPC peering connection       | Send matching traffic to another VPC                                                                   |
| ::/0         | Egress-only Internet Gateway | Permit outbound IPv6 internet connectivity without allowing unsolicited internet-initiated connections |

These are examples; a route is effective only when its target is valid and the surrounding network configuration permits the traffic.

### 4.1 Main route table vs. custom route tables

When you create a VPC, AWS creates a main route table automatically. New subnets initially use it unless explicitly associated with another route table.

A production-friendly approach is to leave the main route table with only the VPC's local route, then explicitly associate subnets with purpose-specific custom route tables. This reduces the risk that a newly created subnet accidentally inherits an internet-facing route.

For our lab, we'll create three custom route tables:

* `public-rt`: local route and IPv4 default route to the IGW.

* `private-rt`: local route only for now; NAT will be introduced in Module 4.

* `isolated-rt`: local route only.

A route table can be shared by multiple subnets, but each subnet can be associated with only one route table at a time.

### 4.2 Longest-prefix match

AWS generally chooses the most specific matching route. Consider this table:

| Destination  | Target             |
| ------------ | ------------------ |
| 10.20.0.0/16 | local              |
| 10.30.0.0/16 | Peering connection |
| 10.30.5.0/24 | Network interface  |
| 0.0.0.0/0    | Internet Gateway   |

A packet destined for `10.30.5.12` matches both `10.30.0.0/16` and `10.30.5.0/24`. AWS chooses the `/24` route because it is more specific.

The default route is the fallback for destinations not matched by a more-specific route. When equally specific routes overlap, route-target and propagation priority rules can also matter.

### 4.3 Static vs. propagated routes

Static routes are configured explicitly, such as an IPv4 default route to an IGW or a route to a peering connection.

Propagated routes are learned from supported routing integrations, such as VPN or Direct Connect connections through a virtual private gateway or Transit Gateway.

AWS does not automatically propagate every possible network route into every route table. Propagation must be supported and configured for the relevant routing resource. When a static route and propagated route have the same destination, static routes generally take priority under AWS's documented route-selection rules.

### 5\. Internet Gateway and public IPv4 addressing

### 5.1 An IGW does not make every subnet public

An Internet Gateway is attached to the VPC, not separately to each subnet. For ordinary public IPv4 connectivity, several conditions must align:

* The VPC has an attached IGW.

* The subnet's route table directs internet-bound IPv4 traffic to the IGW.

* The resource has a public IPv4 address or Elastic IP address.

* Security groups and network ACLs permit the relevant traffic.

* The destination is reachable and the application is listening where expected.

An IGW provides the internet-facing connectivity and IPv4 address translation required for supported public IPv4 communication. A route to an IGW alone does not assign a public IP to an instance.

### 5.2 Public IPv4 address vs. Elastic IP

* Automatically assigned public IPv4: AWS can assign a public IPv4 address when an instance launches in a subnet configured for automatic public IPv4 assignment. It generally changes when the instance is stopped and started.

* Elastic IP (EIP): a static public IPv4 address allocated to your AWS account and associated with a supported resource. It is useful when a stable address is needed, for example for a controlled external allowlist.

An EIP is not the same as the instance's private IPv4 address. AWS maps public IPv4 traffic to the resource's private address through the IGW.

Cost consideration: AWS charges for public IPv4 addresses, including Elastic IPs, under its current public IPv4 pricing model. Do not assume an EIP is free simply because it is attached to a running instance. Check current regional pricing before allocating addresses.

For this module, we won't allocate EIPs or create EC2 instances. We'll verify the routing architecture without incurring those additional resource costs.

### 6\. IPv6 internet connectivity

IPv6 differs from IPv4 in an important way: a globally routable IPv6 address does not require the same public/private address translation model used for public IPv4.

### Internet Gateway vs. egress-only Internet Gateway

| Feature                         | Internet Gateway                        | Egress-only Internet Gateway            |
| ------------------------------- | --------------------------------------- | --------------------------------------- |
| IPv4                            | Supports public IPv4 connectivity       | Not supported                           |
| IPv6                            | Supports IPv6 internet connectivity     | Supports outbound IPv6 connectivity     |
| Unsolicited inbound connections | Possible if routing and security permit | Blocked for new inbound connections     |
| Typical use                     | Public-facing IPv4/IPv6 workloads       | Private workloads needing outbound IPv6 |

An egress-only Internet Gateway is stateful. Return traffic for connections initiated from within the VPC is allowed, while new internet-initiated connections are not. Security groups and network ACLs still apply.

Typical dual-stack routes look like this:

```text
Public route table
------------------
10.20.0.0/16  -> local
0.0.0.0/0     -> Internet Gateway
::/0          -> Internet Gateway

Private route table
-------------------
10.20.0.0/16  -> local
0.0.0.0/0     -> NAT Gateway          # Module 4
::/0          -> Egress-only IGW
```

The IPv6 route is useful only if the VPC and relevant subnets have IPv6 CIDR allocations and the workload has IPv6 addressing. Adding `::/0` by itself does not configure IPv6 end to end.

### 7\. Hands-on lab: build the VPC with Pulumi

We'll create the six-subnet architecture with one IGW and three custom route tables. We will deliberately leave private and isolated subnets without an internet default route.

### 7.1 Prerequisites

You'll need:

* Python 3.11 or newer.

* Pulumi CLI.

* AWS CLI v2.

* An AWS account and credentials configured for the CLI.

* IAM permissions to create and inspect VPCs, subnets, route tables, route associations, and Internet Gateways.

This lab requires real AWS infrastructure. The VPC components demonstrated here generally have no hourly charge of their own, but check the current pricing applicable to your account and Region. We avoid NAT Gateways, EC2 instances, load balancers, and public IPv4 allocations to keep costs down.

### 7.2 Project structure

```text
module-3-vpc/
├── Pulumi.yaml
├── requirements.txt
└── __main__.py
```

Create the project directory and files.

`Pulumi.yaml`

```yaml
name: module-3-vpc
runtime:
  name: python
description: Multi-AZ AWS VPC routing lab
```

`requirements.txt`

```text
pulumi
pulumi-aws
```

Install dependencies and initialize a stack:

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

Choose an AWS Region available to your account. The example uses `eu-west-1`; change it if needed.

Authenticate with your usual AWS CLI profile or supported credential provider. Do not put access keys directly in your Pulumi source code.

### 7.3 Pulumi implementation

The following implementation creates the VPC, chooses two available AZs, creates the subnet tiers, and explicitly associates each subnet with its intended route table.

`__main__.py`

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
vpc_cidr = config.get("vpcCidr") or "10.20.0.0/16"

# Discover available AZs in the configured Region.
azs = aws.get_availability_zones(state="available")

if len(azs.names) < 2:
    raise RuntimeError("This lab requires at least two available AZs.")

az_a, az_b = azs.names[:2]

# 1. Create the VPC.
vpc = aws.ec2.Vpc(
    "lab-vpc",
    cidr_block=vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "module-3-vpc"},
)

# 2. Attach one Internet Gateway to the VPC.
igw = aws.ec2.InternetGateway(
    "lab-igw",
    vpc_id=vpc.id,
    tags={"Name": "module-3-igw"},
)

# 3. Create three custom route tables.
public_rt = aws.ec2.RouteTable(
    "public-rt",
    vpc_id=vpc.id,
    routes=[
        aws.ec2.RouteTableRouteArgs(
            cidr_block="0.0.0.0/0",
            gateway_id=igw.id,
        ),
    ],
    tags={"Name": "module-3-public-rt"},
)

private_rt = aws.ec2.RouteTable(
    "private-rt",
    vpc_id=vpc.id,
    tags={"Name": "module-3-private-rt"},
)

isolated_rt = aws.ec2.RouteTable(
    "isolated-rt",
    vpc_id=vpc.id,
    tags={"Name": "module-3-isolated-rt"},
)

# 4. Define the six subnet configurations.
subnet_specs = [
    ("public-a",   "10.20.1.0/24",  az_a, public_rt, True),
    ("public-b",   "10.20.2.0/24",  az_b, public_rt, True),
    ("private-a",  "10.20.11.0/24", az_a, private_rt, False),
    ("private-b",  "10.20.12.0/24", az_b, private_rt, False),
    ("isolated-a", "10.20.21.0/24", az_a, isolated_rt, False),
    ("isolated-b", "10.20.22.0/24", az_b, isolated_rt, False),
]

subnets = {}

for name, cidr, az, route_table, public_ip in subnet_specs:
    subnet = aws.ec2.Subnet(
        name,
        vpc_id=vpc.id,
        cidr_block=cidr,
        availability_zone=az,
        map_public_ip_on_launch=public_ip,
        tags={
            "Name": name,
            "Tier": name.split("-")[0],
        },
    )

    aws.ec2.RouteTableAssociation(
        f"{name}-route-association",
        subnet_id=subnet.id,
        route_table_id=route_table.id,
    )

    subnets[name] = subnet

# 5. Export identifiers for verification.
pulumi.export("vpc_id", vpc.id)
pulumi.export("internet_gateway_id", igw.id)
pulumi.export("availability_zones", [az_a, az_b])

pulumi.export(
    "subnet_ids",
    {name: subnet.id for name, subnet in subnets.items()},
)

pulumi.export(
    "route_table_ids",
    {
        "public": public_rt.id,
        "private": private_rt.id,
        "isolated": isolated_rt.id,
    },
)
```

Important implementation details

* The public route table has the IPv4 default route to the IGW.

* The private and isolated route tables receive AWS's automatically created local route but no internet default route.

* Public subnets enable automatic public IPv4 assignment for newly created eligible network interfaces. This lab does not launch any instances or allocate any public IPv4 addresses.

* Private and isolated subnets disable automatic public IPv4 assignment.

* All six subnets have explicit route-table associations, so their intended routing does not depend on the main route table.

* The VPC's automatically created main route table remains separate from the three custom route tables.

The public IPv4 assignment setting is a subnet default, not a firewall rule. An instance launched into a public subnet may override that default at launch.

### 7.4 Preview and deploy

Before creating resources, review the planned changes:

```powershell
pulumi preview
```

You should see a plan containing the VPC, Internet Gateway, three custom route tables, six subnets, and six route-table associations.

Deploy:

```powershell
pulumi up
```

Review the plan and approve it when you're ready. Then inspect the outputs:

```powershell
pulumi stack output
pulumi stack output vpc_id
pulumi stack output subnet_ids
pulumi stack output route_table_ids
```

Pulumi tracks the resources in the stack's state, allowing it to plan subsequent changes and identify resources it manages.

### 7.5 Verify the deployed network with AWS CLI

Get the VPC ID from Pulumi:

```powershell
$vpc = pulumi stack output vpc_id
```

List the subnets and their AZs:

```powershell
aws ec2 describe-subnets `
  --filters "Name=vpc-id,Values=$vpc" `
  --query "Subnets[].{ID:SubnetId,CIDR:CidrBlock,AZ:AvailabilityZone,AutoPublicIP:MapPublicIpOnLaunch}" `
  --output table
```

Expected: six subnets, with three in each of two AZs.

Inspect route tables:

```powershell
aws ec2 describe-route-tables `
  --filters "Name=vpc-id,Values=$vpc" `
  --query "RouteTables[].{ID:RouteTableId,Main:Associations[?Main==`true`].Main,Routes:Routes[].{Destination:DestinationCidrBlock,Target:GatewayId}}" `
  --output json
```

Check subnet associations:

```powershell
aws ec2 describe-route-tables `
  --filters "Name=vpc-id,Values=$vpc" `
  --query "RouteTables[].{RouteTable:RouteTableId,Associations:Associations[].SubnetId}" `
  --output json
```

Confirm the following:

* The public route table has `0.0.0.0/0` targeting the IGW.

* The private and isolated route tables do not have an IPv4 default route.

* Each of the six subnets is explicitly associated with the intended custom route table.

* All route tables contain the VPC's local route.

You can also inspect the architecture in the AWS VPC console by opening your VPC and selecting its Resource map tab. This is a convenient way to see subnets, route tables, associations, and gateways together.

### 8\. Optional extension: add IPv6 egress

After the IPv4 lab works, you can extend it to dual-stack networking. This is an extension, not part of the initial deployment.

The high-level Pulumi resources are:

```python
# Allocate an AWS-provided IPv6 CIDR to the VPC.
# Add this argument to the VPC definition:
assign_generated_ipv6_cidr_block=True

# Create an egress-only Internet Gateway.
egress_igw = aws.ec2.EgressOnlyInternetGateway(
    "lab-egress-only-igw",
    vpc_id=vpc.id,
)

# Add an IPv6 default route to a private route table
# after assigning an IPv6 CIDR to the relevant subnet.
```

To finish this extension, allocate non-overlapping `/64` IPv6 ranges to the subnets, enable IPv6 addressing where required, and create an `aws.ec2.Route` with destination `::/0` and target `egress_igw.id` for the private route table.

Do not enable the IPv6 route until the VPC and subnet IPv6 addressing is configured. Also, remember that an egress-only IGW handles IPv6 only; it does not replace a NAT Gateway for IPv4.

### 9\. Troubleshooting common problems

| Symptom                                       | Likely cause                                                           | What to inspect                                           |
| --------------------------------------------- | ---------------------------------------------------------------------- | --------------------------------------------------------- |
| Public instance cannot reach the internet     | Missing IGW route, public IP, or permitted outbound traffic            | Route table, subnet settings, security group, network ACL |
| Instance has no public IPv4 address           | Automatic assignment disabled or launch configuration overrides it     | MapPublicIpOnLaunch, instance network interface           |
| Private instance cannot reach an IPv4 website | No NAT route or no NAT Gateway                                         | Private route table and NAT configuration                 |
| Isolated subnet reaches an unexpected network | Additional route, connectivity resource, or another access path exists | Route table, peering, Transit Gateway, VPN, endpoints     |
| Traffic uses the wrong network path           | More-specific route or conflicting destination prefix                  | Route destinations, targets, propagation                  |
| New subnet has unexpected internet routing    | It inherited the main route table                                      | Main route table and explicit associations                |
| IPv6 connection fails but IPv4 works          | Missing IPv6 CIDR, address, route, or security rule                    | IPv6 subnet configuration and ::/0 route                  |

Use this sequence when diagnosing a routing failure:

* Identify the source and destination IP addresses.

* Determine which subnet contains the source.

* Find the route table associated with that subnet.

* Identify the most-specific matching route for the destination address family.

* Verify that the route target exists and is configured correctly.

* Inspect security groups, network ACLs, destination routing, and application-level behavior.

A route table showing an active route does not prove that the complete connection will succeed. Routing, security controls, address assignment, and the remote endpoint must all align.

### 10\. Security, resilience, and cost considerations

* Keep the main route table conservative. Explicitly associate subnets with the appropriate custom tables.

* Do not expose private workloads unnecessarily. A public subnet does not require you to assign public IPv4 addresses to every resource.

* Plan for AZ failures. Put critical application tiers in multiple AZs, and ensure their dependencies are also resilient.

* Avoid unnecessary public IPv4 addresses. AWS's public IPv4 pricing applies even to addresses attached to running instances.

* Be deliberate about IPv6. IPv6 internet routing and IPv4 internet routing are separate configurations. An IPv6-enabled workload can have internet reachability even if its IPv4 route table has no internet default route.

* Use Pulumi previews before production changes. Route changes can disrupt live connectivity. Review changes before applying them.

* Clean up the lab. Avoid leaving test infrastructure in your account after the exercise.

### 11\. Clean up the lab

Once you've finished inspecting the VPC and route tables, destroy the stack:

```powershell
pulumi destroy
```

Review the proposed deletions, then approve them. Finally, confirm the stack has no remaining managed resources:

```powershell
pulumi stack
pulumi stack output
```

Do not remove the stack itself until you no longer need its state or outputs.

### 12\. Official references

* [AWS — Subnets for your VPC](https://docs.aws.amazon.com/vpc/latest/userguide/configure-subnets.html?utm_source=chatgpt.com)

* [AWS — Subnet route tables](https://docs.aws.amazon.com/vpc/latest/userguide/subnet-route-tables.html?utm_source=chatgpt.com)

* [AWS — How route priority works](https://docs.aws.amazon.com/vpc/latest/userguide/route-tables-priority.html?utm_source=chatgpt.com)

* [AWS — Egress-only Internet Gateways](https://docs.aws.amazon.com/vpc/latest/userguide/egress-only-internet-gateway.html?utm_source=chatgpt.com)

* [AWS — IP addressing for your VPCs and subnets](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-ip-addressing.html?utm_source=chatgpt.com)

* [Pulumi AWS — VPC resource](https://www.pulumi.com/registry/packages/aws/api-docs/ec2/vpc/?utm_source=chatgpt.com)

* [Pulumi AWS — Route table resource](https://www.pulumi.com/registry/packages/aws/api-docs/ec2/routetable/?utm_source=chatgpt.com)

* [Pulumi AWS — Subnet resource](https://www.pulumi.com/registry/packages/aws/api-docs/ec2/subnet/?utm_source=chatgpt.com)

Module 3 complete. You've covered subnet segmentation, route selection, internet gateways, IPv4/IPv6 connectivity, and a reusable multi-AZ Pulumi implementation. The next module builds on this architecture by adding NAT Gateways and controlled outbound connectivity for private workloads.
