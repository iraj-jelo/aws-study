Worked for 39s

### Module 8 — VPC Peering and Transit Gateway

This module builds on the VPC routing, security groups, DNS, and VPC endpoints concepts from Modules 2–7. We'll compare direct VPC peering with AWS Transit Gateway, then design segmented multi-VPC networks using Pulumi and Python.

The goal is to understand not just how to connect VPCs, but how routing, isolation, scalability, and operational complexity change as your AWS environment grows.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Design VPC peering connections and configure routes in both directions.

* Explain why VPC peering is non-transitive and why overlapping IPv4 CIDRs are a problem.

* Design multi-VPC networks with AWS Transit Gateway (TGW).

* Configure TGW attachments, route tables, associations, and route propagation.

* Isolate development, staging, and production networks using separate routing domains.

* Understand centralized inspection, shared services, and cross-Region connectivity.

* Deploy a hands-on networking lab with Pulumi Python and verify its behavior using AWS CLI.

* Compare the cost, availability, security, and operational trade-offs of both approaches.

### 2\. VPC peering: the fundamentals

### 2.1 What is VPC peering?

VPC peering creates a direct network connection between two VPCs using AWS's private networking infrastructure. Resources can communicate using private IP addresses, provided that routing and security rules permit the traffic.

![Amazon Virtual Private Cloud Connectivity Options Whitepaper (2018) :: My New Hugo Site](https://images.openai.com/static-rsc-4/pvT3ZabloEdD9Idvr_YFZ8XP8d7KGiL7NgXF3JfPDkeoc5nFzGvnGqMbD4BIJoJc1l2maTGaFbGr2e_1xg7DWOPVrOovDEFaXiOZWrw-sz3P_37Pme5_ryN7slhl5WvUM-ibZfynp3g_bbngEGRgfvDitzfrJbQS-RcPfSBEdbBsYUG-F1HQuFvG7GINNOyC?purpose=fullsize)

A peering connection consists of:

* Two VPCs: the requester and accepter.

* A peering connection that must be accepted when required.

* Routes in the relevant subnet route tables on both sides.

* Security group and network ACL rules that allow the desired traffic.

* DNS settings, if cross-VPC DNS resolution is needed.

Suppose we have two VPCs:

| Property         | VPC A        | VPC B        |
| ---------------- | ------------ | ------------ |
| Purpose          | Application  | Database     |
| CIDR             | 10.10.0.0/16 | 10.20.0.0/16 |
| Private subnet   | 10.10.1.0/24 | 10.20.1.0/24 |
| Example workload | 10.10.1.10   | 10.20.1.20   |

The desired traffic path is:

VPC A — Application

10.10.0.0/16 · EC2 10.10.1.10

Route: 10.20.0.0/16 → pcx-identifier

VPC peering connection

Private IP routing · No NAT required

VPC B — Database

10.20.0.0/16 · EC2 10.20.1.20

Route: 10.10.0.0/16 → pcx-identifier

The important detail is that creating the peering connection alone does not establish end-to-end connectivity. You must also configure the routes and permit the traffic through the applicable security controls.

### 2.2 How routing works

Assume an application at `10.10.1.10` connects to a database at `10.20.1.20` on TCP port `5432`.

* The application sends a packet to `10.20.1.20`.

* Its subnet's route table matches `10.20.0.0/16` and selects the peering connection as the target.

* AWS forwards the packet over the peering connection.

* The database subnet's route table must have a return route for `10.10.0.0/16` through the same peering connection.

* The database security group must allow the inbound PostgreSQL connection, and the application security group and network ACLs must not block the flow.

Example route tables:

VPC A

| Destination  | Target         |
| ------------ | -------------- |
| 10.10.0.0/16 | local          |
| 10.20.0.0/16 | pcx-identifier |

VPC B

| Destination  | Target         |
| ------------ | -------------- |
| 10.20.0.0/16 | local          |
| 10.10.0.0/16 | pcx-identifier |

The `local` route represents communication within the VPC's own address space. The peering route sends matching traffic to the other VPC.

Remember the principle from Module 3: AWS uses longest-prefix matching to select the most specific applicable route. A route to a more specific subnet can take precedence over a broader route.

### 3\. VPC peering limitations

### 3.1 Non-transitive routing

This is the most important VPC peering limitation.

Imagine three VPCs:

VPC A

10.10.0.0/16

VPC B

10.20.0.0/16

A ↔ B: peering exists

VPC C

10.30.0.0/16

A ↔ C: peering exists

B ↛ C through A

Even if A is peered with both B and C, B cannot use A as a router to reach C. Peering is a direct, one-to-one relationship, not a transit service.

If all three VPCs must communicate directly, create three connections:

* A ↔ B

* A ↔ C

* B ↔ C

The number of connections in a full mesh of VPCs is:

E=\\frac{n(n-1)}{2}

For example:

| VPCs | Peering connections |
| ---- | ------------------- |
| 2    | 1                   |
| 3    | 3                   |
| 5    | 10                  |
| 10   | 45                  |
| 20   | 190                 |

The operational problem is not merely the number of connections. Each connection may require route updates, security changes, ownership coordination, and troubleshooting across multiple VPCs.

When to use peering: two or a small number of VPCs with a clear, direct communication requirement, especially when you don't need a transit routing layer.

### 3.2 Overlapping CIDR blocks

VPC peering cannot be established if the VPCs have overlapping IPv4 or IPv6 CIDR blocks. The restriction applies to the VPC address ranges, not just the subnets you intend to connect.

For example:

* VPC A: `10.0.0.0/16`

* VPC B: `10.0.5.0/24`

The ranges overlap, so the peering connection is not supported.

Plan address space before creating VPCs, ideally with an IPAM allocation strategy across accounts and Regions. If overlapping networks already exist, consider address translation or application-layer connectivity patterns where appropriate. Do not assume that Transit Gateway automatically resolves overlapping CIDRs; it is not a general solution to address collisions.

### 3.3 Inter-Region VPC peering

VPC peering can connect VPCs in different AWS Regions, including across AWS accounts, subject to the service's supported Region and account requirements.

Key characteristics:

* Traffic uses private IP addressing.

* Routes must be configured on both sides.

* The CIDRs must not overlap.

* Inter-Region data transfer can incur charges.

* Peering still does not provide transitive routing.

* Security groups and DNS behavior must be configured appropriately.

This is useful for direct connectivity between a production VPC in one Region and a small service VPC in another. For a larger multi-Region network, compare direct peering with Transit Gateway peering and AWS Cloud WAN.

Official reference: [VPC peering basics](https://docs.aws.amazon.com/vpc/latest/peering/vpc-peering-basics.html?utm_source=chatgpt.com).

### 4\. AWS Transit Gateway

### 4.1 What is Transit Gateway?

AWS Transit Gateway is a managed network hub that connects multiple VPCs and supported network attachments, including Site-to-Site VPN and Direct Connect gateway connectivity.

Instead of connecting every VPC to every other VPC, each VPC attaches to the transit gateway. The TGW routes packets between attachments according to its route tables.

![Field Notes: How to Scale Your Networks on Amazon Web Services | AWS Architecture Blog](https://images.openai.com/static-rsc-4/8yOm1AgGb4iryK94mAxD85kjpjnCFoqpJlYj1vi03uhqMq7ShpaRnvm029U_C-HlkYzGRJpkEFi9OOcaUCAPo7dev2nN0GNV-OoZtjejk7wGdJFXOWsTSOjJ677Iq8Wl2mWnFV8-XXeDqJAuxVl2yP6MFZYZKzUo4DNTwSzDK9TYVfVnTJKbSZWlcHs8FglH?purpose=fullsize)

Example architecture:

```text
                +----------------------+
                | AWS Transit Gateway  |
                |                      |
                | TGW route tables     |
                +--+-------+--------+--+
                   |       |        |
                   |       |        |
               +---+--+ +--+---+ +--+---+
               | VPC A| | VPC B| | VPC C|
               | App  | | Data | |Shared|
               +------+ +------+ +------+
```

Each VPC still has its own VPC route tables. A typical VPC subnet route table contains a route to the TGW for destinations outside that VPC's local address space.

The TGW then makes another routing decision to select the destination attachment.

This creates two separate routing decisions:

* The VPC route table decides whether to send traffic to the TGW.

* The TGW route table decides which attachment should receive that traffic.

Both decisions must be correct.

### 4.2 Core Transit Gateway components

| Component              | Responsibility                                                                   |
| ---------------------- | -------------------------------------------------------------------------------- |
| Transit gateway        | Regional routing hub                                                             |
| VPC attachment         | Connects a VPC to the TGW through selected subnets                               |
| TGW route table        | Selects the next attachment for matching destinations                            |
| Association            | Selects the TGW route table used for traffic arriving from an attachment         |
| Propagation            | Installs an attachment's routes into a TGW route table                           |
| Static route           | Explicitly defines a destination and target attachment                           |
| Blackhole route        | Intentionally drops matching traffic                                             |
| TGW peering attachment | Connects two transit gateways, typically in different Regions or network domains |

An attachment can be associated with exactly one TGW route table but can propagate routes to multiple TGW route tables. This distinction is essential for segmentation.

### 4.3 Association versus propagation

These terms are easy to confuse.

Association answers: Which TGW route table will be consulted for packets arriving from this attachment?

Propagation answers: Into which TGW route table or tables should this attachment's destination routes be installed?

Suppose we have three attachments:

* `att-app` — application VPC

* `att-db` — database VPC

* `att-shared` — shared-services VPC

We create two TGW route tables:

* `rt-isolated` — used by application and database VPCs

* `rt-shared` — used by the shared-services VPC

The intended design is:

| Attachment      | Associated route table | Routes propagated into |
| --------------- | ---------------------- | ---------------------- |
| App             | rt-isolated            | rt-shared              |
| Database        | rt-isolated            | rt-shared              |
| Shared services | rt-shared              | rt-isolated            |

This allows the shared-services network to route toward the app and database VPCs, while the isolated route table does not automatically learn the other isolated VPC's routes.

However, this table alone does not prove that all desired traffic flows. The isolated route table still needs the intended destination routes, and the shared-services attachment must be reachable from the source VPC route tables. Security groups and subnet route tables also matter.

For a production segmentation design, use explicit associations and carefully controlled propagation rather than blindly accepting every default route-table behavior.

### 5\. Transit Gateway route tables and segmentation

### 5.1 Development, staging, and production

Consider a SaaS platform with four VPCs:

| VPC             | CIDR         | Purpose                         |
| --------------- | ------------ | ------------------------------- |
| Development     | 10.10.0.0/16 | Engineering workloads           |
| Staging         | 10.20.0.0/16 | Pre-production testing          |
| Production      | 10.30.0.0/16 | Customer workloads              |
| Shared services | 10.40.0.0/16 | DNS, monitoring, internal tools |

The requirement is:

* Development must not directly reach production.

* Staging must not directly reach production.

* All environments may access selected shared services.

* Production must not initiate arbitrary connections into development.

* Security inspection may be required for selected flows.

One possible TGW routing model is:

```text
                   Transit Gateway
                 /        |         \
                /         |          \
       Development      Staging    Production
                \         |          /
                 \        |         /
                   Shared services
```

This diagram represents logical connectivity, not a guarantee that all three environments can reach one another.

Create separate route tables such as:

* `rt-dev`

* `rt-staging`

* `rt-prod`

* `rt-shared`

Associate each environment's attachment with its own table. Propagate or add only the destination routes that the environment should be able to reach.

For example, `rt-dev` might contain routes to the shared-services CIDR, but no route to `10.30.0.0/16`. `rt-prod` can similarly have a route to shared services without a route to development.

A route table can also contain a blackhole route to explicitly discard matching traffic. Remember that route selection follows destination-prefix matching; a more-specific route can override a broader one.

Important security distinction: TGW route tables control network reachability. They are not application authorization policies. Use security groups, network ACLs where appropriate, and application-level identity and authorization controls as additional layers.

### 5.2 Centralized shared services

A shared-services VPC may host internal services such as:

* Internal DNS resolvers or directory services.

* Monitoring and logging collectors.

* Patch management and artifact repositories.

* Shared application services.

The TGW provides the routing path, but the shared service must also be configured to accept the intended traffic. For example, a private DNS resolver requires correct resolver rules and endpoint configuration; merely adding a TGW route does not make DNS work.

### 6\. Centralized inspection and shared-services network designs

### 6.1 Why centralized inspection matters

In some architectures, application traffic must pass through a stateful firewall or network inspection appliance before reaching another VPC or the internet.

A basic TGW connection does not automatically inspect traffic. You must deliberately design the routing path through an inspection VPC and ensure return traffic traverses the correct appliance.

Application VPC

Source workload

Transit Gateway

Route toward inspection attachment

Inspection VPC

Firewall or stateful network appliance

Destination VPC

Approved destination

The design generally needs:

* A TGW route table for application attachments that directs selected traffic to the inspection VPC.

* An inspection VPC attachment and subnet routes that forward packets to the appliance.

* Appliance routing that sends inspected traffic back to the TGW.

* Appropriate destination routes and security controls.

* Symmetric forwarding for stateful inspection.

AWS supports appliance mode on the inspection VPC attachment. It helps keep a flow associated with the same Availability Zone in the appliance VPC for the lifetime of the flow. This is important when firewalls maintain connection state.

Do not assume that enabling appliance mode alone creates an inspection architecture: route tables, appliance forwarding, security policy, and high availability still require configuration.

### 6.2 Transit Gateway peering across Regions

For larger environments, you can deploy a TGW in each Region and connect the transit gateways with a peering attachment.

```text
Region A                                  Region B
+--------------------+                   +--------------------+
| Transit Gateway A  |                   | Transit Gateway B  |
|   |          |     |                   |    |          |    |
| VPC A      VPC B   |                   | VPC C       VPC D  |
+--------+-----------+                   +----------+---------+
         |                                          |
         +-------- TGW peering attachment ----------+
```

Important routing details:

* Create the TGW peering attachment and accept it on the peer side when required.

* Configure static routes in the relevant TGW route tables on both sides.

* Configure VPC subnet routes pointing to each Region's local TGW.

* Ensure return routes exist.

* Plan for unique, non-overlapping network address spaces.

* Consider DNS resolution separately; TGW peering does not automatically provide cross-Region private hosted-zone name resolution.

TGW peering supports inter-Region connectivity and requires static routes for destinations reachable through the peering attachment.

For a large number of Regions, AWS Cloud WAN is another option worth evaluating in Module 13.

### 7\. Cost, availability, and operational trade-offs

| Consideration      | VPC peering                                            | Transit Gateway                                                             |
| ------------------ | ------------------------------------------------------ | --------------------------------------------------------------------------- |
| Architecture       | Direct VPC-to-VPC                                      | Managed routing hub                                                         |
| Transitive routing | No                                                     | Yes, when routes permit it                                                  |
| Segmentation       | Separate connections and VPC routes                    | Multiple TGW route tables and controlled propagation                        |
| Scale              | Mesh complexity grows quickly                          | Easier to centralize many attachments                                       |
| CIDR overlap       | Not supported                                          | Overlapping attached CIDRs still cause routing limitations                  |
| Availability       | Managed connection; dependent on endpoints and routing | Managed regional service; attachment AZ design still matters                |
| Central inspection | Requires a separately designed path                    | Well suited to centralized routing and inspection                           |
| Cost               | Data-transfer charges may apply                        | Attachment-hour and data-processing charges, plus applicable transfer costs |
| Operations         | Straightforward for small networks                     | More centralized, but requires TGW route-table governance                   |

AWS documents hourly attachment and traffic-processing charges for Transit Gateway. Exact costs depend on Region, attachment type, and traffic volume.

For availability, enable a TGW attachment subnet in each Availability Zone from which workloads need to access the TGW. AWS recommends multiple Availability Zones for resilience. A subnet in an AZ without a TGW attachment cannot directly use that VPC attachment to reach the TGW.

Before deploying a real lab, check current regional pricing and the current service quotas. Transit Gateway is not a free substitute for peering.

### 8\. Hands-on lab — Peering versus Transit Gateway

We'll use a small, real AWS lab with Pulumi Python. The lab requires an AWS account because LocalStack does not reproduce every real TGW routing and networking behavior.

### 8.1 Lab design

Create three VPCs:

| VPC    | CIDR         | Purpose        |
| ------ | ------------ | -------------- |
| app-a  | 10.10.0.0/16 | Application A  |
| app-b  | 10.20.0.0/16 | Application B  |
| shared | 10.30.0.0/16 | Shared service |

We'll compare two connectivity models:

* Peering: `app-a` and `app-b` communicate through a direct peering connection.

* Transit Gateway: all three VPCs attach to one TGW, with route tables that permit access to shared services without allowing direct transit between `app-a` and `app-b`.

### Part A — Direct peering

app-a

10.10/16

app-b

10.20/16

### Part B — Transit Gateway

Transit Gateway

Isolated and shared route tables

app-a

app-b

shared

The comparison is about routing and isolation, not application performance. We'll use routes and attachment state to verify the configuration; actual packet-level testing requires workloads or network test instances.

### 8.2 Prerequisites

Install the AWS CLI v2, Pulumi CLI, and Python. Configure AWS credentials through an approved profile or another supported credential mechanism.

Check your identity and Region:

```bash
aws sts get-caller-identity
aws configure get region

pulumi version
python --version
```

Choose a Region where you can create the required VPC and TGW resources. You need IAM permissions for VPCs, subnets, route tables, peering, TGW, attachments, and route management.

Cost warning: TGW attachments incur hourly charges, and TGW traffic incurs processing charges. This lab is not guaranteed to be free. We'll omit NAT gateways, load balancers, and EC2 instances to keep the baseline infrastructure smaller.

### 8.3 Pulumi project setup

Create a project:

```bash
mkdir vpc-connectivity-lab
cd vpc-connectivity-lab

pulumi new aws-python
```

If prompted, choose a development stack and configure the desired AWS Region.

The main infrastructure resources will be declared in `__main__.py`. The essential Pulumi resource types are:

```python
aws.ec2.Vpc
aws.ec2.Subnet
aws.ec2.RouteTable
aws.ec2.RouteTableAssociation
aws.ec2.VpcPeeringConnection
aws.ec2.TransitGateway
aws.ec2.TransitGatewayVpcAttachment
aws.ec2.TransitGatewayRouteTable
aws.ec2.TransitGatewayRouteTableAssociation
aws.ec2.TransitGatewayRouteTablePropagation
aws.ec2.Route
aws.ec2.TransitGatewayRoute
```

The precise constructor arguments should follow the installed stable Pulumi AWS provider version. The provider's generated API reference is available at [Pulumi AWS EC2](https://www.pulumi.com/registry/packages/aws/api-docs/ec2/?utm_source=chatgpt.com).

### 8.4 Implement the network

Use the following as the core of `__main__.py`. It creates the three VPCs, a direct peering connection between `app-a` and `app-b`, a TGW, three attachments, and separate routing domains.

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config("aws")
region = aws.get_region().name

az = aws.get_availability_zones(
    state="available",
).names[0]

cidrs = {
    "app_a": "10.10.0.0/16",
    "app_b": "10.20.0.0/16",
    "shared": "10.30.0.0/16",
}

vpcs = {}
subnets = {}
rtables = {}

for name, cidr in cidrs.items():
    vpc = aws.ec2.Vpc(
        f"{name}-vpc",
        cidr_block=cidr,
        enable_dns_support=True,
        enable_dns_hostnames=True,
        tags={"Name": f"{name}-vpc", "Lab": "vpc-connectivity"},
    )

    subnet = aws.ec2.Subnet(
        f"{name}-subnet",
        vpc_id=vpc.id,
        cidr_block=cidr.replace("/16", ".1.0/24"),
        availability_zone=az,
        tags={"Name": f"{name}-subnet"},
    )

    rt = aws.ec2.RouteTable(
        f"{name}-rt",
        vpc_id=vpc.id,
        tags={"Name": f"{name}-rt"},
    )

    aws.ec2.RouteTableAssociation(
        f"{name}-subnet-rta",
        subnet_id=subnet.id,
        route_table_id=rt.id,
    )

    vpcs[name] = vpc
    subnets[name] = subnet
    rtables[name] = rt

# Part A: direct VPC peering between app-a and app-b.
peer = aws.ec2.VpcPeeringConnection(
    "app-a-app-b-peer",
    vpc_id=vpcs["app_a"].id,
    peer_vpc_id=vpcs["app_b"].id,
    auto_accept=True,
    tags={"Name": "app-a-app-b-peer"},
)

aws.ec2.Route(
    "app-a-to-app-b",
    route_table_id=rtables["app_a"].id,
    destination_cidr_block=cidrs["app_b"],
    vpc_peering_connection_id=peer.id,
)

aws.ec2.Route(
    "app-b-to-app-a",
    route_table_id=rtables["app_b"].id,
    destination_cidr_block=cidrs["app_a"],
    vpc_peering_connection_id=peer.id,
)

# Part B: create the Transit Gateway.
tgw = aws.ec2.TransitGateway(
    "lab-tgw",
    description="VPC connectivity learning lab",
    default_route_table_association="disable",
    default_route_table_propagation="disable",
    tags={"Name": "lab-tgw"},
)

attachments = {}

for name in cidrs:
    attachments[name] = aws.ec2.TransitGatewayVpcAttachment(
        f"{name}-tgw-attachment",
        transit_gateway_id=tgw.id,
        vpc_id=vpcs[name].id,
        subnet_ids=[subnets[name].id],
        dns_support="enable",
        tags={"Name": f"{name}-attachment"},
    )

# Separate route tables: app spokes and shared services.
isolated_rt = aws.ec2.TransitGatewayRouteTable(
    "isolated-tgw-rt",
    transit_gateway_id=tgw.id,
    tags={"Name": "isolated-tgw-rt"},
)

shared_rt = aws.ec2.TransitGatewayRouteTable(
    "shared-tgw-rt",
    transit_gateway_id=tgw.id,
    tags={"Name": "shared-tgw-rt"},
)

# Associate each attachment with exactly one TGW route table.
for name in ("app_a", "app_b"):
    aws.ec2.TransitGatewayRouteTableAssociation(
        f"{name}-isolated-association",
        transit_gateway_attachment_id=attachments[name].id,
        transit_gateway_route_table_id=isolated_rt.id,
    )

aws.ec2.TransitGatewayRouteTableAssociation(
    "shared-association",
    transit_gateway_attachment_id=attachments["shared"].id,
    transit_gateway_route_table_id=shared_rt.id,
)

# Shared routes are visible to app spokes.
aws.ec2.TransitGatewayRouteTablePropagation(
    "shared-to-isolated-propagation",
    transit_gateway_attachment_id=attachments["shared"].id,
    transit_gateway_route_table_id=isolated_rt.id,
)

# App routes are visible to shared services.
for name in ("app_a", "app_b"):
    aws.ec2.TransitGatewayRouteTablePropagation(
        f"{name}-to-shared-propagation",
        transit_gateway_attachment_id=attachments[name].id,
        transit_gateway_route_table_id=shared_rt.id,
    )

# VPC route tables must direct shared-service traffic to the TGW.
for name in ("app_a", "app_b"):
    aws.ec2.Route(
        f"{name}-to-shared",
        route_table_id=rtables[name].id,
        destination_cidr_block=cidrs["shared"],
        transit_gateway_id=tgw.id,
    )

# Shared services needs return routes to both app VPCs.
for name in ("app_a", "app_b"):
    aws.ec2.Route(
        f"shared-to-{name}",
        route_table_id=rtables["shared"].id,
        destination_cidr_block=cidrs[name],
        transit_gateway_id=tgw.id,
    )

pulumi.export("vpc_ids", {
    name: vpc.id for name, vpc in vpcs.items()
})
pulumi.export("peering_id", peer.id)
pulumi.export("transit_gateway_id", tgw.id)
pulumi.export("isolated_tgw_route_table_id", isolated_rt.id)
pulumi.export("shared_tgw_route_table_id", shared_rt.id)
```

One correction to make before deployment: the generated subnet CIDRs must be valid children of their respective VPC CIDRs. The expression above yields `10.10.0.0.1.0/24`, which is invalid. Use an explicit subnet mapping instead:

```python
subnet_cidrs = {
    "app_a": "10.10.1.0/24",
    "app_b": "10.20.1.0/24",
    "shared": "10.30.1.0/24",
}
```

Then change the subnet resource to:

```python
cidr_block=subnet_cidrs[name],
```

This also illustrates why explicit IP planning is safer than constructing CIDRs with string replacement.

### 8.5 Deployment and verification

Review the proposed changes before creating resources:

```bash
pulumi preview
pulumi up
```

After deployment, inspect the TGW and its attachments:

```bash
aws ec2 describe-transit-gateways \
  --filters Name=tag:Name,Values=lab-tgw

aws ec2 describe-transit-gateway-vpc-attachments \
  --filters Name=transit-gateway-id,Values=<tgw-id>
```

Check the TGW route tables:

```bash
aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id <isolated-route-table-id> \
  --filters Name=state,Values=active

aws ec2 search-transit-gateway-routes \
  --transit-gateway-route-table-id <shared-route-table-id> \
  --filters Name=state,Values=active
```

Inspect VPC subnet routes:

```bash
aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=<vpc-id>
```

Wait for attachments to reach `available` before interpreting routing results.

Expected behavior:

* `app-a` has a direct route to `app-b` through peering.

* `app-a` and `app-b` can route to `shared` through TGW.

* `shared` has routes back to both application VPCs.

* The isolated TGW route table does not learn the other application's route through propagation.

* The direct peering connection remains a separate route between `app-a` and `app-b`.

Because the app VPC route tables have explicit peering routes for each other, that direct path takes precedence over any broader route that might otherwise direct traffic to the TGW.

Lab limitation: The VPCs currently contain no EC2 instances, and the sample security configuration does not establish application-level connectivity tests. Route inspection verifies the control-plane configuration, not successful end-to-end packet delivery. To prove reachability, add temporary test workloads and narrowly scoped security group rules, then test the permitted flows and verify that prohibited flows fail.

### 8.6 Troubleshooting checklist

| Symptom                                  | Likely cause                                                     | What to inspect                              |
| ---------------------------------------- | ---------------------------------------------------------------- | -------------------------------------------- |
| Peering is pending                       | Accepter has not accepted the request                            | Peering connection status                    |
| TGW attachment is pending                | Attachment creation or acceptance is incomplete                  | Attachment state                             |
| No TGW route to destination              | Propagation or static route missing                              | TGW route table                              |
| Traffic times out                        | Missing return route or blocked security rule                    | Both VPC route tables and security groups    |
| Shared service works from one VPC only   | Missing route or incorrect TGW association                       | Route tables and attachment associations     |
| Cross-VPC access is unexpectedly allowed | An unintended route or overly permissive security rule exists    | All applicable routing and security controls |
| TGW traffic fails in one AZ              | Missing attachment subnet for that AZ or incorrect subnet routes | Attachment subnet coverage and route tables  |

For systematic troubleshooting, trace the packet in both directions:

* Source subnet route table.

* TGW attachment and associated TGW route table.

* Destination attachment and destination subnet.

* Destination security controls.

* Return path through the destination route table and TGW.

A valid forward route is not enough if the response cannot return.

### 8.7 Cleanup

After collecting the results, destroy the lab:

```bash
pulumi destroy
```

Review the proposed deletions and confirm the operation. Then verify that the lab's VPCs, peering connection, TGW, and attachments have been removed. Do not delete shared infrastructure or state that belongs to another project.

### 9\. Security and production recommendations

* Allocate non-overlapping CIDRs across VPCs and Regions before deployment.

* Disable unnecessary default TGW associations and propagation when building segmented networks.

* Keep routing permissions and security group permissions as separate controls.

* Use multiple AZs for production TGW attachments where appropriate.

* For centralized stateful inspection, design symmetric routing and evaluate appliance mode.

* Share TGWs across accounts carefully using AWS Resource Access Manager (RAM), with clear ownership and change-control procedures.

* Monitor attachment state, route changes, traffic volume, and costs.

* Avoid relying on the default TGW route table as a substitute for an explicit network segmentation policy.

### 10\. Official AWS references

![AWS_Amazon_VPC_Connectivity_Options · AWS-certificate Notes](https://images.openai.com/static-rsc-4/_DSn0AxcFRkHzZi6ANGamXaAGQqLo7-0_pB9ez8I5xU0PoX5tELcb3dZC5-ENTXSH4PxQ_MD7SlmOmeBYFZl1Y-D2653TLti83H4iZicow2Il9hBVxX_aNWFlnHIUgJeEYk14Ht5r-uZN-dtp6k4Mw5Ym04pNc7N5jghs2ouanfyrdDDu2mQE5mi8jJNNYye?purpose=fullsize)

[VPC peering basics](https://docs.aws.amazon.com/vpc/latest/peering/vpc-peering-basics.html?utm_source=chatgpt.com)

Connection lifecycle, routing, limitations, and non-transitive behavior.

![AWS — Difference between VPC Peering and Transit Gateway | by Ashish Patel | Awesome Cloud | Medium](https://images.openai.com/static-rsc-4/y3VRrOqvZ8o3uOzwqTNU0-hfZnTZDdr8VIH1-Y-olzKPpV1HVtG_vpOOmKm_uuxn1CLGf-ei2eRqi_KcQS727Ga54p83qb5kBB2Kd6AhJ1ajDfT-jeZjwCqfdsNpyxH-ZGNbAHb9y9Ua8iBO_bBaAzeEm4zuY-2gMC0jzbm121y_mJsLDBX8FCymJroM0VyO?purpose=fullsize)

[AWS Transit Gateway documentation](https://docs.aws.amazon.com/vpc/latest/tgw/?utm_source=chatgpt.com)

Attachments, route tables, propagation, peering, and architecture patterns.

![Segmenting Your Network with AWS Transit Gateway Using Terraform | by Renatogentil | Mar, 2026 | Medium](https://images.openai.com/static-rsc-4/1cS_w3vWXIqrAa_aTbKk-JaPW2a9pM8_o-uHzm2uSpxoY2QWMI1bhl9pr3uve3T0XpsrJU6-Bv61kAr7hoZCf3KA_JmeN9GzkwBidW-ksD2SIGX1gNqZruwdh51OeNLiJr9sr-Fi_Bpo0_25kaNrD4CDJuIz_Bv0EC-6tf-_H8il7zhfrfOUZOWxHtvwSWVG?purpose=fullsize)

[Transit Gateway route tables](https://docs.aws.amazon.com/vpc/latest/tgw/tgw-route-tables.html?utm_source=chatgpt.com)

Associations, propagation, static routes, and route management.

![Deployment models for AWS Network Firewall | Networking & Content Delivery](https://images.openai.com/static-rsc-4/Uucf7CkshJ-5L5Wkksc70OmrgN_jdJRCMD0hUfWng1Jtu_m9jItUx2COB__kAGr0vO8RwGmT66uItzCFzj_gTwdPOCLJsWoFPZS_vx4KWM84wspPh74PxhBCZ72ElUQOGO7ztxscOdvm-42beJzShw5dJhPfCuFtAZ9kSkf7-xBSTwe1FzRVpHmA40srftG2?purpose=fullsize)

[How Transit Gateway works](https://docs.aws.amazon.com/vpc/latest/tgw/how-transit-gateways-work.html?utm_source=chatgpt.com)

Availability Zones, appliance mode, routing, and centralized inspection scenarios.

![Infrastructure as code with Pulumi](https://images.openai.com/static-rsc-4/G4uyppsUteFzhk-jeSFBfXF48H-ZaC-zW3RUzYe_8Q4eexjAaY4xdBvweZ69ThA9fZKJ3tiLidbpmX0Uy8rF4t1mrJpzEgEYHikK1ZEI72NCpbiZqZcQj1AsNIclqX5QRcyzZBCh4nJgY8QFDTC1Z8yE-HVFowKyB1xOmVDDJSBZK944Izysjt360ei5bIBu?purpose=fullsize)

[Pulumi AWS EC2 API reference](https://www.pulumi.com/registry/packages/aws/api-docs/ec2/?utm_source=chatgpt.com)

Current resource schemas and Python configuration examples.

### Module summary

The key architectural decision is whether you need a direct connection or a centrally managed routing layer.

* VPC peering is simple for a small number of direct connections, but it does not provide transit routing.

* Transit Gateway simplifies large-scale connectivity and enables routing segmentation, but adds cost and operational responsibilities.

* Neither mechanism replaces security policy. Routing determines where packets can go; security controls determine which traffic is allowed.

The next module is Module 9 — Hybrid Connectivity, covering Site-to-Site VPN, Direct Connect, BGP, routing advertisements, redundancy, and connectivity between AWS and on-premises networks.
