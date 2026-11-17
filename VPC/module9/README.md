Worked for 42s

### Module 9 — Hybrid Connectivity

AWS Networking Course · Pulumi with Python · October 2026

This module builds on the VPC routing, security, DNS, and Transit Gateway concepts from Modules 1–8. We’ll focus on connecting an existing private network—such as an office, on-premises data center, or home lab—to AWS securely and reliably.

The emphasis is on understanding actual packet paths, route advertisements, redundancy, troubleshooting, and production design. We’ll use Pulumi with Python where practical, AWS CLI v2 for verification, and a local VPN lab when AWS resources are unavailable or too expensive.

### 1\. Learning objectives

By the end of this module, you should be able to:

* Design site-to-site connectivity between AWS and an external network.

* Explain IPsec tunnels, IKE negotiation, encryption, and tunnel health.

* Compare AWS Site-to-Site VPN with AWS Direct Connect.

* Choose between a Virtual Private Gateway (VGW) and a Transit Gateway (TGW) for hybrid connectivity.

* Understand BGP, autonomous system numbers (ASNs), route advertisements, and failover.

* Design redundant connections and hybrid DNS.

* Diagnose routing asymmetry, MTU problems, and tunnel failures.

* Estimate connectivity costs and choose an appropriate availability design.

### 2\. Hybrid connectivity architecture

Hybrid connectivity means joining AWS networks to networks outside AWS while preserving the required routing, security, and operational boundaries.

Typical scenarios include:

* An office accessing a private application running in a VPC.

* An on-premises database communicating with applications in AWS.

* Multiple branch offices reaching shared services in AWS.

* A company connecting multiple VPCs through a central network hub.

* A data center maintaining private connectivity to AWS during a gradual migration.

### Reference architecture

On-premises network

Office / data center · 10.20.0.0/16

Routers · Firewall · Internal DNS

IPsec VPN over the internet

Encrypted tunnels · BGP or static routes

AWS hybrid connectivity

Customer Gateway (CGW) ↔ Site-to-Site VPN ↔ VGW or TGW

VPC attachment and route-table decisions

Application VPC

10.100.0.0/16

Private application subnets

Data VPC

10.110.0.0/16

Private database subnets

The central principle is that establishing a VPN tunnel does not automatically establish end-to-end connectivity. The routes, security rules, address ranges, DNS resolution, and return path must also be correct.

### 3\. Site-to-Site VPN fundamentals

### 3.1 The main components

AWS Site-to-Site VPN connects an external VPN device to an AWS VPN endpoint using encrypted tunnels.

Customer gateway device

Your physical router, firewall, or software VPN appliance. It establishes the tunnels from your network.

Customer Gateway (CGW) resource

An AWS configuration object representing your external gateway, including its public IP address and, for BGP-based designs, its ASN. Creating this object does not install a VPN device.

VPN connection

The AWS resource that defines the site-to-site connection and its two IPsec tunnels.

Virtual Private Gateway or Transit Gateway

The AWS-side routing attachment that receives traffic from the VPN and forwards it toward the destination network.

AWS documents these components and the supported gateway configurations in its [Site-to-Site VPN guide](https://docs.aws.amazon.com/vpn/latest/s2svpn/?utm_source=chatgpt.com).

### 3.2 What IPsec actually does

IPsec protects IP traffic between two VPN endpoints. It provides confidentiality, integrity, and peer authentication, according to the negotiated algorithms and configuration.

A common IPsec VPN uses two protocols or stages:

* IKE (Internet Key Exchange): Authenticates the peers, negotiates cryptographic parameters, and establishes security associations.

* IPsec ESP (Encapsulating Security Payload): Encrypts and authenticates the actual network traffic carried through the tunnel.

For IKEv2, the simplified negotiation sequence is:

Phase 1 — IKE SA

The endpoints negotiate IKE parameters and authenticate each other, for example with a pre-shared key or supported certificates.

Phase 2 — IPsec Child SA

The peers negotiate the protection parameters for data traffic and establish the IPsec security association.

Encrypted data plane

Packets travel through the established tunnel. Routing determines which traffic should use it.

This is a conceptual sequence, not a complete description of every IKEv2 exchange. Rekeying, liveness detection, and additional Child SAs may occur later.

### Encapsulation and packet flow

Suppose a server at `10.20.1.10` needs to access an application at `10.100.1.20`.

Original IP packet

Source: 10.20.1.10

Destination: 10.100.1.20

IPsec encapsulation and encryption

Outer packet

VPN endpoint A → VPN endpoint B

Encrypted inner packet

Internet transport, then decapsulation

Original packet forwarded

10.20.1.10 → 10.100.1.20

The inner source and destination addresses are normally preserved. IPsec adds overhead, so the outer packet is larger than the original packet. This matters for MTU and fragmentation.

### 3.3 Two tunnels and redundancy

Each AWS Site-to-Site VPN connection includes two tunnels. Configure both on the customer gateway rather than treating the second tunnel as an unused spare. AWS can perform maintenance that temporarily affects a tunnel.

A critical distinction:

* Two tunnels provide tunnel-level redundancy.

* They do not, by themselves, provide independent customer routers, independent ISPs, or independent power supplies.

* A single customer gateway and a single internet circuit remain potential failure points.

* Two healthy tunnels do not guarantee that traffic is load-balanced across them.

AWS recommends allowing asymmetric routing because the return traffic may use a different tunnel from the forward traffic. With a Virtual Private Gateway, AWS selects a primary tunnel; Equal Cost Multipath (ECMP) is supported for eligible Site-to-Site VPN connections on Transit Gateway, but not on VGW.

### 3.4 BGP versus static routing

You can use either static routes or dynamic routing with BGP, subject to the gateway and VPN configuration.

| Property               | Static routing                                   | BGP dynamic routing                                    |
| ---------------------- | ------------------------------------------------ | ------------------------------------------------------ |
| Route configuration    | Administratively entered                         | Exchanged between peers                                |
| Topology changes       | Often require manual changes                     | Routes can be updated automatically                    |
| Failover               | Depends on configured routes and tunnel behavior | Can respond to BGP session and route changes           |
| Operational complexity | Lower for small, fixed networks                  | Higher initially, better suited to changing topologies |
| Best fit               | Simple, stable networks                          | Redundant, growing hybrid networks                     |

BGP does not encrypt traffic; IPsec provides encryption. BGP exchanges reachability information and helps each side determine which networks can be reached through a connection.

For production networks with multiple sites or redundant paths, BGP is often the more flexible choice.

### 4\. AWS Direct Connect

A VPN uses an encrypted tunnel over an underlying IP network, usually the public internet. AWS Direct Connect provides a dedicated network connection from a Direct Connect location to AWS. It is commonly selected for more predictable network performance, sustained traffic volumes, or private connectivity requirements.

Direct Connect is not inherently an encrypted transport. If confidentiality in transit is required, consider an appropriate encryption layer, such as IPsec over a supported Direct Connect design, or MACsec where supported by the connection and equipment.

### 4.1 Dedicated versus hosted connections

![AWS Direct Connect Resiliency Toolkit - AWS Direct Connect](https://images.openai.com/static-rsc-4/WXF5RjuGh84O8EX28oa4K5VU7HVAD_oueLR5UrgOTS6bpIC5dklcIN96LIadY_EkkovqFfkPNE1OQRho7HpVmuhhiMpFS4fS3UVDcYiy4T0rngVVcSKewp0phXcDcavbrEF6yzGF73rs3pdlHznwN0bu5Te0xmt1F6erONk4uZ1DoCeLCI7mYe79Jr3W5pGi?purpose=fullsize)

Dedicated connection

A physical connection provisioned for a single customer. It supports multiple virtual interfaces, subject to current service requirements and configuration.

![Cloud Networking Fundamentals - DEV Community](https://images.openai.com/static-rsc-4/Xnh6krdTFdZYqA8Q0YgV7tlpkBvVA0l_Q_w5f7yz0s3IXdMkcSI0PPAAtiCJ_NIHqkD03It78SA8HXe6bLRKTYpKLbNbtbylbJyOIsOtIKRaGRP4yCky1Uk6J_iWKsatluCh-Q9wKXgjB06JNOyrUP7g7DwUzLXpWCJb-Pf49B6AkSReIUHIVH-yaz_9lxJq?purpose=fullsize)

Hosted connection

A Direct Connect partner provisions connectivity for you over partner infrastructure. Hosted connections support a single virtual interface per hosted connection; available speeds and features depend on the offering.

A dedicated connection and a hosted connection are different provisioning models, not guarantees of end-to-end availability. Resilience still depends on independent connections, locations, providers, and routing.

Official reference: [AWS Direct Connect getting started](https://aws.amazon.com/directconnect/getting-started/?utm_source=chatgpt.com).

### 4.2 Virtual interfaces (VIFs)

A virtual interface is a logical Layer 3 connection established over Direct Connect.

| VIF type    | Purpose                                                                                                           |
| ----------- | ----------------------------------------------------------------------------------------------------------------- |
| Private VIF | Access VPC resources through private IP addressing, typically using a VGW or Direct Connect gateway architecture. |
| Public VIF  | Access supported AWS public services using public IP addresses.                                                   |
| Transit VIF | Access one or more Transit Gateways through an associated Direct Connect gateway.                                 |

A Direct Connect gateway (DXGW) is a global resource used to associate eligible Direct Connect connectivity with supported AWS gateway architectures. For Transit Gateway access, a transit VIF connects the Direct Connect connection to a DXGW, which can then be associated with Transit Gateways in supported Regions.

A DXGW is not itself a general-purpose packet-forwarding router between arbitrary customer networks. The relevant gateway associations, allowed prefixes, VIFs, and route advertisements determine which destinations are reachable.

See [Direct Connect virtual interfaces](https://docs.aws.amazon.com/directconnect/latest/UserGuide/WorkingWithVirtualInterfaces.html?utm_source=chatgpt.com).

### 4.3 Direct Connect versus Site-to-Site VPN

| Consideration        | Site-to-Site VPN                                                              | Direct Connect                                                                     |
| -------------------- | ----------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- |
| Underlying transport | Usually public internet                                                       | Dedicated connectivity from a Direct Connect location                              |
| Encryption           | IPsec tunnel encryption                                                       | Not encrypted by default at the network layer                                      |
| Provisioning         | Generally quicker                                                             | Requires connectivity at an eligible location or through a partner                 |
| Performance          | Depends on internet path and VPN design                                       | More predictable network path; actual performance depends on circuit and design    |
| Resilience           | Two tunnels per VPN connection; separate gateways and ISPs improve resilience | Requires appropriately independent connections and locations                       |
| Costs                | VPN connection charges and data transfer                                      | Port/connection and data-transfer costs, plus provider or colocation costs         |
| Typical role         | Fast deployment, backup, or moderate traffic                                  | Consistent private connectivity, larger traffic volumes, or enterprise integration |

Important: Direct Connect and VPN are not mutually exclusive. A common architecture uses Direct Connect for primary traffic and Site-to-Site VPN as a backup. Failover behavior must be designed and tested; simply provisioning both does not guarantee that the intended path wins.

### 5\. VGW versus Transit Gateway for hybrid connectivity

Both can terminate Site-to-Site VPN connections, but they serve different architectural needs.

![AI 驅動下的部署策略：公有雲 vs. 地端部署，企業該如何選擇？｜銓鍇國際](https://images.openai.com/static-rsc-4/64itmVXyWR7e2R9uqf1Llc2Xs9XgfgsMJ6oVav-AuEU6uC3ZykLRxskduEyXayKIFu7mzGbuKG4xNxkSauob7j9Xvb6Q9SdSEO3ctX_bduqC2gHMBJdiXHA2Hc18ReTHAGbQI0x26_49rI7bT7PwEPrIuvRAtUADTZQWwlYEt-UVnGZIe0nMzbPPGt_h5n3h?purpose=fullsize)

Virtual Private Gateway (VGW)

A VPN endpoint associated with one VPC. A good fit for a straightforward connection between one VPC and one external network.

Simpler topology · Fewer routing components

![AWS — Transit Gateway Overview. Introduction to AWS Transit Gateway —… | by Ashish Patel | Awesome Cloud | Medium](https://images.openai.com/static-rsc-4/52g0mSGDVUGfOpeaI0DnSIspvfNc7qxTi-wz-QGmwzeRbA4t57Ie3H9_OReXJ2v-VHkF1MW-8xbFcI1173GiZrpTEk9hscJnIPijK-JOY-tYo31TL8es-H2DdxFO0vuMXve3aGVMwp3lJZh7sGnQkr-bs3NxqAF1Ykh0BFa8LlPkqdhlncUdftmqGciMAFW0?purpose=fullsize)

Transit Gateway (TGW)

A regional routing hub for multiple VPCs and external connections, with route-table associations and propagation to control reachability.

Centralized routing · Network segmentation

### 5.1 Routing with a VGW

In a simple VGW architecture, you need to coordinate two sets of routing:

* The AWS VPC subnet route tables must direct on-premises destinations toward the VGW, either through appropriate route propagation or explicit routes.

* The external network must know how to route AWS VPC destinations toward the customer gateway.

A VGW is associated with a single VPC. It is therefore useful for a simple hybrid connection, but it is less suited to being the central routing hub for a large multi-VPC network.

### 5.2 Routing with a TGW

With a Transit Gateway, traffic traverses multiple routing decisions:

* The source VPC subnet route table selects the TGW.

* The TGW route table associated with that VPC attachment selects the VPN attachment.

* The VPN tunnel carries traffic to the external gateway.

* The external router forwards the packet to the destination subnet.

The return path must be configured as well.

For example, consider these networks:

| Network         | CIDR          |
| --------------- | ------------- |
| Office          | 10.20.0.0/16  |
| Application VPC | 10.100.0.0/16 |
| Data VPC        | 10.110.0.0/16 |

A VPC route table might contain:

| Destination   | Target       |
| ------------- | ------------ |
| 10.100.0.0/16 | local        |
| 10.20.0.0/16  | tgw-xxxxxxxx |

The TGW route table associated with the application VPC attachment must have a route for `10.20.0.0/16` targeting the VPN attachment. The VPN attachment's associated TGW route table must have routes to the VPCs that the office is permitted to access.

These are distinct route tables with distinct responsibilities. A route in one does not automatically configure the others.

### 5.3 Route association versus propagation

These terms are especially important for the TGW lab.

* Association selects the TGW route table used to route packets arriving from a particular attachment.

* Propagation installs eligible routes learned from an attachment into a TGW route table.

* Static route explicitly defines a destination and target.

A useful design is to use separate route tables for different trust zones. For example, production VPCs may be allowed to reach approved office subnets while development VPCs are isolated from production. This requires deliberate associations, propagation choices, and static routes where appropriate—not merely attaching everything to the same TGW.

### 6\. BGP, ASNs, and route advertisements

### 6.1 What BGP does

Border Gateway Protocol (BGP) exchanges network reachability information between routing peers.

For hybrid connectivity, BGP lets the AWS VPN endpoint and your external router exchange prefixes dynamically. If a tunnel or route fails, the BGP session and resulting route changes can help direct traffic onto a surviving path.

An Autonomous System Number (ASN) identifies a routing domain in BGP.

For example, a lab might use:

| Component            | Example ASN |
| -------------------- | ----------- |
| On-premises router   | 65000       |
| AWS-side routing ASN | 64512       |

These are illustrative private ASNs. Choose values that fit your existing network and the requirements of the AWS gateway. For a VGW, the AWS-side ASN can be configured on the gateway. For a TGW, the ASN is configured on the Transit Gateway. Avoid unintended ASN conflicts, especially when connecting multiple routing domains.

### 6.2 BGP route exchange

Suppose the on-premises router advertises:

```text
10.20.0.0/16
```

AWS learns that the office network is reachable through the VPN. AWS advertises eligible VPC routes back to the external router, which can then install routes for those AWS destinations.

The simplified exchange is:

On-premises BGP router

Advertises 10.20.0.0/16

BGP session over the VPN tunnel

AWS VPN gateway

Learns the office route and advertises eligible AWS routes

AWS route tables

Must still direct packets to the appropriate gateway

BGP advertisements do not override every other routing requirement. For example, a VPC subnet route table still needs the correct route toward the VGW or TGW.

With a TGW, route propagation can populate the relevant TGW route table with routes learned through a dynamic VPN attachment. The routes installed and advertised depend on the attachment's routing configuration and the applicable TGW route tables.

### 6.3 Failover and asymmetric routing

Imagine that both VPN tunnels are operational. One is selected as the preferred egress path. If it fails, routing can converge onto the remaining healthy path.

The operational sequence is approximately:

* A tunnel or BGP session becomes unhealthy.

* The affected route becomes unavailable or less preferred.

* Routing selects an available alternative.

* Traffic resumes once the data plane and routing converge.

This is not necessarily instantaneous. Application timeouts and dropped packets can occur during convergence.

For resilient designs:

* Configure both VPN tunnels.

* Allow asymmetric routing where the architecture requires it.

* Test failure of each tunnel independently.

* Monitor tunnel status and BGP sessions.

* Consider two independent external gateways and internet circuits.

* If using multiple eligible TGW VPN paths, evaluate ECMP and its requirements.

* Avoid assuming that a tunnel being `UP` proves the end-to-end application path works.

AWS's VPN guide explains its tunnel selection behavior, endpoint updates, and routing recommendations.

### 7\. Hybrid DNS and address planning

Connectivity is incomplete if hosts cannot resolve each other's private names.

A common design uses Route 53 Resolver endpoints to bridge DNS between an AWS VPC and an on-premises DNS environment.

On-premises DNS

`corp.example.internal`

Forwarded DNS queries over hybrid connectivity

Route 53 Resolver endpoints

Inbound and outbound resolution paths

Private hosted zones and VPC workloads

Internal application names and service discovery

The direction matters:

* Inbound Resolver endpoint: DNS queries from an external network enter AWS for resolution.

* Outbound Resolver endpoint: DNS queries from AWS are forwarded to external DNS servers using configured Resolver rules.

The DNS packets must be able to traverse the network, and security rules must allow the required DNS traffic, typically UDP and TCP port 53. DNS forwarding is a separate configuration from IP routing; a healthy VPN alone does not configure it.

See the [Route 53 Resolver documentation](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html?utm_source=chatgpt.com).

### Address planning

Use non-overlapping address ranges for all participating networks.

| Network             | Example CIDR  |
| ------------------- | ------------- |
| Office              | 10.20.0.0/16  |
| AWS application     | 10.100.0.0/16 |
| AWS data            | 10.110.0.0/16 |
| AWS shared services | 10.120.0.0/16 |

Overlapping CIDRs create ambiguous routing and may prevent the desired direct connectivity. Avoid choosing a VPC CIDR without considering existing office, data center, partner, VPN client, and future cloud address ranges.

### 8\. Encryption, MTU, and troubleshooting

### 8.1 MTU and fragmentation

IPsec adds overhead to the original packet. Consequently, a packet that fits the local Ethernet MTU may exceed the usable size of the tunnel path.

Potential symptoms include:

* Small pings succeed but large transfers stall.

* TCP connections establish but application requests hang.

* Some protocols work while others fail.

* Large packets are dropped because required ICMP messages are filtered.

A practical diagnostic approach is to compare small and large packets, test path MTU where supported, and inspect tunnel and device counters.

For Linux endpoints, useful tools include:

```bash
ip route
ip -s link
ping -c 4 10.100.1.20
tracepath 10.100.1.20
```

`tracepath` may not be installed, and ICMP-based tests can be blocked by security rules. A failed ping does not necessarily prove the VPN is broken.

### 8.2 A systematic troubleshooting sequence

* Check the tunnel

    Inspect AWS tunnel status and logs. Verify IKE negotiation, authentication, IPsec security associations, and tunnel liveness.

* Check BGP or static routes

    Confirm that the expected prefixes exist on both peers and that BGP sessions are established if dynamic routing is used.

* Check AWS routing

    Inspect the VPC subnet route table and, when applicable, the TGW route-table association, propagation, and destination route.

* Check the return path

    Confirm the external router has a route to the AWS destination and that the response is not routed through an incompatible firewall or gateway.

* Check security controls

    Verify security groups, network ACLs, external firewall rules, host firewalls, and allowed application ports.

* Check DNS and MTU

    Test using a destination IP first. Then investigate DNS forwarding, packet size, fragmentation, and dropped ICMP messages.

Useful AWS CLI commands include:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-xxxxxxxx

aws ec2 describe-vpn-gateways

aws ec2 describe-transit-gateways

aws ec2 describe-transit-gateway-route-tables

aws ec2 describe-transit-gateway-attachments

aws ec2 describe-route-tables \
  --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

Replace the example IDs with your own resource identifiers. These commands inspect configuration and state; the TGW route-table command alone does not show every route, so inspect the routes for the relevant route-table ID separately.

For a TGW, also use `describe-transit-gateway-route-table-associations`, `describe-transit-gateway-route-table-propagations`, and `search-transit-gateway-routes` to diagnose the correct attachment and destination prefix.

### 9\. Pulumi implementation: a VGW-based Site-to-Site VPN

We'll now translate the architecture into infrastructure as code.

This example creates the AWS-side resources for a VPN between an existing VPC and an external VPN device. It assumes the external device has a reachable public IP address and is configured separately.

Billable AWS resources

A VPN connection can incur hourly charges even when little or no data is transferred. A VGW-based example avoids the additional TGW attachment and routing-hub components, but it is not free. Check the [current AWS VPN pricing](https://aws.amazon.com/vpn/pricing/?utm_source=chatgpt.com) before deployment.

### 9.1 Project structure

```text
hybrid-vpn/
├── Pulumi.yaml
├── requirements.txt
└── __main__.py
```

`Pulumi.yaml`:

```yaml
name: hybrid-vpn
runtime:
  name: python
description: VGW-based AWS Site-to-Site VPN lab
```

`requirements.txt`:

```text
pulumi>=3.0.0,<4.0.0
pulumi-aws>=7.0.0,<8.0.0
```

These are major-version compatibility ranges, not a claim that the newest release is exactly the minimum listed. For reproducible deployment, resolve and lock a currently supported provider version, then test the preview before applying changes.

### 9.2 Infrastructure code

The example uses an existing VPC and subnet route table, supplied through Pulumi configuration.

`__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
route_table_id = config.require("routeTableId")

# Public IP of your actual on-premises VPN gateway.
customer_gateway_ip = config.require("customerGatewayIp")

# Example private ASN for the on-premises BGP router.
customer_asn = config.get_int("customerAsn") or 65000

# Existing VPC: this is the AWS-side VPN endpoint.
vpn_gateway = aws.ec2.VpnGateway(
    "hybrid-vgw",
    vpc_id=vpc_id,
    amazon_side_asn=64512,
    tags={"Name": "hybrid-vgw"},
)

# AWS representation of the external VPN device.
customer_gateway = aws.ec2.CustomerGateway(
    "office-cgw",
    bgp_asn=customer_asn,
    ip_address=customer_gateway_ip,
    type="ipsec.1",
    tags={"Name": "office-cgw"},
)

# Dynamic routing: BGP is used rather than static VPN routes.
vpn_connection = aws.ec2.VpnConnection(
    "office-vpn",
    type="ipsec.1",
    customer_gateway_id=customer_gateway.id,
    vpn_gateway_id=vpn_gateway.id,
    static_routes_only=False,
    tags={"Name": "office-vpn"},
)

# Install eligible routes learned through the VGW into
# the specified existing VPC subnet route table.
route_propagation = aws.ec2.VpnGatewayRoutePropagation(
    "office-vpn-route-propagation",
    vpn_gateway_id=vpn_gateway.id,
    route_table_id=route_table_id,
)

pulumi.export("vpn_gateway_id", vpn_gateway.id)
pulumi.export("customer_gateway_id", customer_gateway.id)
pulumi.export("vpn_connection_id", vpn_connection.id)
pulumi.export("route_propagation_id", route_propagation.id)
```

This is the AWS-side foundation, not a complete production deployment. In particular, the code does not create the VPC, configure your on-premises router, configure DNS forwarding, or create independent redundant customer gateways.

### 9.3 Configure and deploy

First, authenticate using a suitable AWS CLI profile or another supported AWS credential provider. Avoid hardcoding access keys.

```bash
pulumi stack init dev

pulumi config set aws:region eu-west-3

pulumi config set vpcId vpc-xxxxxxxx
pulumi config set routeTableId rtb-xxxxxxxx
pulumi config set customerGatewayIp 203.0.113.10
pulumi config set customerAsn 65000
```

`203.0.113.10` is a documentation-only address. Replace it with the actual public IP of your external VPN gateway.

Preview the proposed infrastructure changes:

```bash
pulumi preview
```

Deploy only after reviewing the plan and costs:

```bash
pulumi up
```

The configuration creates a VPN connection that expects BGP. Your external gateway must support the required AWS Site-to-Site VPN configuration.

### 9.4 Retrieve the VPN configuration

After deployment, use the connection ID exported by Pulumi:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-xxxxxxxx
```

AWS provides the tunnel endpoints and connection options required to configure the external device. You can download the vendor-specific configuration through the AWS console or supported APIs.

Treat downloaded VPN configuration as sensitive: it may contain pre-shared keys and other connection details. Do not commit it to Git, paste it into public issue trackers, or print it unnecessarily in CI logs.

### 9.5 Verify the route propagation

Inspect the existing VPC route table:

```bash
aws ec2 describe-route-tables \
  --route-table-ids rtb-xxxxxxxx
```

Once the VPN and BGP session are operational, eligible routes learned from the external network can appear in the route table through propagation.

Remember that route propagation does not install routes into every route table automatically. You must associate the appropriate propagation with each relevant route table, or configure explicit routes where appropriate.

Official Pulumi reference: [AWS EC2 VpnConnection](https://www.pulumi.com/registry/packages/aws/api-docs/ec2/vpnconnection/?utm_source=chatgpt.com).

### 10\. Hands-on lab: build a hybrid network

We'll divide the lab into a local exercise that you can perform without AWS charges and an optional real AWS deployment.

### Lab A — Local VPN simulation

No AWS resources required

Use Docker on your Windows machine with Linux containers to model two separate networks and two VPN gateways.

Office LAN

10.20.0.0/24

Client: 10.20.0.10

AWS-like LAN

10.100.0.0/24

Server: 10.100.0.10

strongSwan IPsec gateways

IKEv2 · ESP · Private test network

Use strongSwan as the IPsec implementation. Its official documentation contains a site-to-site example with two security gateways and distinct protected subnets.

Suggested steps:

* Create two isolated Linux gateway containers and two test endpoints, one on each LAN.

* Assign the two LAN CIDRs shown above. Ensure they do not overlap.

* Configure strongSwan with IKEv2 and matching IPsec traffic selectors.

* Configure IP forwarding and the required LAN routes.

* Establish the tunnel and verify the IPsec security associations.

* Test connectivity between `10.20.0.10` and `10.100.0.10`.

* Stop one gateway or deliberately break a route, then observe the failure and recovery behavior.

Useful strongSwan commands include:

```bash
swanctl --list-sas
ip route
ip -s link
```

This local exercise demonstrates IPsec, routing, and failure analysis. It does not reproduce AWS VPN endpoints, AWS-managed tunnel redundancy, AWS BGP integration, or actual Direct Connect behavior. Docker networking and Linux privileges may also require adjustments in Docker Desktop with WSL2.

### Lab B — Optional real AWS VPN

If you have AWS access and an externally reachable VPN device:

* Create or select a test VPC and subnet route table.

* Deploy the VGW, Customer Gateway, VPN connection, and route propagation with Pulumi.

* Configure both AWS tunnels on the external device.

* Establish BGP and verify the advertised prefixes.

* Test connectivity in both directions.

* Disable one tunnel and observe the effect on connectivity and routing.

* Remove the test resources when finished.

A software VPN gateway on a public VPS may be an option, but it adds hosting costs and requires correct public reachability, forwarding, firewall rules, and IPsec configuration.

### 11\. High availability and cost planning

### 11.1 Choose the right resilience level

Level 1 — Basic VPN

One external gateway, one internet circuit, one AWS VPN connection with both tunnels configured. Protects against certain tunnel failures, but not all site failures.

Level 2 — Independent network paths

Two external gateways and independent internet connections, with properly configured redundant VPN paths. Reduces the impact of router, ISP, and circuit failures.

Level 3 — Direct Connect plus VPN backup

Primary private connectivity through redundant Direct Connect infrastructure, with VPN connectivity as a backup. Requires explicit routing preferences, independent failure domains, and failover testing.

The appropriate design depends on recovery time objectives, traffic volume, budget, and the consequences of losing connectivity. Redundancy must be end-to-end: two tunnels sharing the same failed router or ISP do not provide full network resilience.

### 11.2 Cost components

| Component        | Cost considerations                                                                               |
| ---------------- | ------------------------------------------------------------------------------------------------- |
| Site-to-Site VPN | Connection-hour charges, data transfer out, and applicable public IPv4 charges                    |
| Transit Gateway  | Hourly attachment charges and applicable data processing                                          |
| Direct Connect   | Connection or port charges, data transfer, and potentially partner, circuit, and colocation costs |
| DNS              | Resolver endpoint hourly and query charges where applicable                                       |
| Monitoring       | CloudWatch log ingestion, storage, and related usage                                              |

Prices vary by Region, connection type, capacity, and traffic. Consult the official [VPN pricing page](https://aws.amazon.com/vpn/pricing/?utm_source=chatgpt.com) and [Direct Connect pricing page](https://aws.amazon.com/directconnect/pricing/?utm_source=chatgpt.com) before choosing a production design.

### 11.3 Safe cleanup

After completing the optional AWS lab:

```bash
pulumi destroy
```

Review the proposed deletions and confirm that only lab resources are being removed. The existing VPC and subnet route table are supplied as configuration inputs and are not created by the example, so Pulumi should not manage their lifecycle through this project.

Also verify the VPN connection and route propagation are gone:

```bash
aws ec2 describe-vpn-connections \
  --vpn-connection-ids vpn-xxxxxxxx
```

Do not delete a shared production gateway or route table just to clean up this lab. Check any resources that were created outside Pulumi, including temporary compute instances and external VPN hosts, separately.

### 12\. Production design checklist

Before deploying hybrid connectivity into production, verify these areas:

* Non-overlapping IPv4 and IPv6 address plans.

* Explicitly defined routing in both directions.

* Both VPN tunnels configured and monitored.

* BGP or static routes selected intentionally.

* Independent failure paths where the availability target requires them.

* TGW route-table associations and propagation reviewed for isolation.

* Security groups, network ACLs, and external firewall rules validated.

* Hybrid DNS forwarding tested from both networks.

* MTU and large-packet behavior tested.

* Tunnel failures and routing convergence tested.

* Costs reviewed, including resources that remain billable while idle.

* Secrets and VPN configuration protected.

* Monitoring, escalation procedures, and recovery runbooks documented.

### 13\. Official references

[AWS Site-to-Site VPN User Guide](https://docs.aws.amazon.com/vpn/latest/s2svpn/?utm_source=chatgpt.com)

VPN components, tunnels, BGP, routing, configuration, and troubleshooting.

[AWS Direct Connect User Guide](https://docs.aws.amazon.com/directconnect/latest/UserGuide/?utm_source=chatgpt.com)

Dedicated and hosted connections, virtual interfaces, and Direct Connect gateways.

[AWS Transit Gateway Guide](https://docs.aws.amazon.com/vpc/latest/tgw/?utm_source=chatgpt.com)

VPN attachments, routing, propagation, and network segmentation.

[Pulumi AWS Provider](https://www.pulumi.com/registry/packages/aws/?utm_source=chatgpt.com)

Python infrastructure resources and API reference.

[strongSwan Documentation](https://docs.strongswan.org/?utm_source=chatgpt.com)

Local IPsec implementation and site-to-site configuration examples.

Module 9 complete. The key lesson is that hybrid connectivity is more than creating an encrypted tunnel: reliable connectivity requires coordinated routing, security, DNS, address planning, and tested failover behavior.

Next is Module 10 — Load Balancing and Application Networking.