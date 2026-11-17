### Module 13 — Advanced VPC Architecture

AWS Networking Course · Advanced Architecture · Pulumi with Python · October 2026

This module moves from connecting individual VPCs to designing a governed, multi-account AWS network. You'll learn how to centralize shared infrastructure and traffic inspection while keeping production isolated, supporting multiple Regions, and limiting the impact of network failures.

The focus is on architectural decisions you might make as a cloud or platform engineer operating a production SaaS platform.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Design a multi-account network using AWS Organizations and dedicated networking accounts.

* Choose between AWS Transit Gateway, VPC peering, and AWS Cloud WAN.

* Design centralized ingress, egress, and traffic inspection with AWS Network Firewall.

* Implement network segmentation for development, staging, production, and shared services.

* Plan cross-Region connectivity and disaster recovery.

* Govern IP address allocation across accounts using Amazon VPC IP Address Manager (IPAM).

* Evaluate resilience, operational complexity, security boundaries, and cost.

* Build an architecture for a SaaS platform and implement its core networking resources with Pulumi.

### 2\. The multi-account networking model

### 2.1 Why one VPC is not enough

A small application can start with one VPC. As the organization grows, however, several problems emerge:

* Development workloads should not have unrestricted access to production.

* Multiple teams need shared DNS, logging, security inspection, and connectivity services.

* Different AWS accounts need independent permissions, billing, and deployment lifecycles.

* Security teams may need centralized control over internet-bound traffic.

* Acquisitions, additional Regions, and new applications make a flat network difficult to manage.

A common solution is to separate account ownership, network connectivity, security enforcement, and application workloads.

### 2.2 AWS Organizations and organizational units

AWS Organizations provides centralized account management, consolidated billing, and organization-level governance. Organizational units (OUs) group accounts by purpose, while service control policies (SCPs) establish permission guardrails.

SCPs do not grant permissions themselves; IAM policies and other applicable authorization controls must still permit the action.

A typical structure looks like this:

AWS Organizations

Organization management and governance

Security OU

Security tooling, audit, centralized findings

Infrastructure OU

Network, DNS, shared services, IPAM

Non-production OU

Development and staging accounts

Production OU

Isolated production accounts

This is an illustrative organizational layout, not a mandatory AWS structure. For example, an organization may separate networking and shared services into different OUs, or use separate production accounts for different business units.

Important distinction: an OU is a governance boundary, not a network boundary. Actual network isolation comes from the VPC topology, routes, security controls, and resource permissions.

### 2.3 Recommended account responsibilities

| Account          | Responsibility                                                                                |
| ---------------- | --------------------------------------------------------------------------------------------- |
| Management       | Organization administration and billing; avoid hosting workloads here                         |
| Network          | Transit Gateway, Cloud WAN integration where used, centralized inspection, network operations |
| Security / Audit | Security monitoring, delegated security services, audit collection                            |
| Shared Services  | Internal DNS, directory services, shared tooling, approved internal endpoints                 |
| Development      | Developer workloads and experimentation                                                       |
| Staging          | Pre-production validation                                                                     |
| Production       | Customer-facing workloads and production data                                                 |

A dedicated network account makes it easier to control changes to central routing without giving application teams ownership of the entire network. The network account is not automatically a security boundary against every organization administrator; protect its administration separately.

### 3\. Reference architecture for the SaaS platform

We'll use the following design throughout the module:

* One AWS Region initially, with a path to multi-Region expansion.

* Separate accounts for development, staging, production, networking, and shared services.

* AWS Transit Gateway as the regional connectivity hub.

* AWS Network Firewall for centralized inspection of selected traffic.

* Public application ingress through an appropriate load balancer in the production account.

* Private application and database subnets.

* Explicit segmentation between environments.

* Centralized IP address allocation and network logging.

The following diagram illustrates the logical architecture. Each workload account owns its VPCs, while the network account owns the shared transit and inspection infrastructure.

AWS Organization

SCP guardrails · account governance · centralized identity

Network account

Transit Gateway · inspection VPC · Network Firewall · network logs

Shared Services VPC

Internal DNS · shared tools · private endpoints

Inspection VPC

Firewall endpoints in multiple AZs

Controlled routing through Transit Gateway

Dev VPC

Isolated development workloads

Staging VPC

Pre-production testing

Production VPC

Private app and database tiers

Illustrative logical topology. Public ingress, internet egress, and east-west inspection require explicit route and security designs; the diagram does not imply every packet automatically traverses the firewall.

A key principle is that connectivity does not mean trust. Attaching two VPCs to the same Transit Gateway does not mean they should be allowed to communicate freely.

### 4\. Network topologies: mesh, hub-and-spoke, and segmentation

### 4.1 Full mesh

In a full-mesh architecture, each VPC connects directly to every other VPC that needs connectivity.

Conceptual mesh: each node may need multiple connections and independently maintained routes.

For VPCs, the number of pairwise connections in a complete mesh is:

E = \\frac{n(n-1)}{2}

For 10 VPCs, that means 45 pairwise connections.

Advantages

* Direct connectivity without a central transit router.

* Useful for a small number of isolated VPC pairs.

* Can avoid Transit Gateway attachment and data-processing costs for particular workloads.

Disadvantages

* Connection and route management grows rapidly.

* Central inspection and consistent policy enforcement are harder.

* Network changes require coordination across multiple VPCs.

VPC peering is not transitive. If VPC A peers with VPC B, and VPC B peers with VPC C, A does not automatically reach C through B. Peering is therefore rarely the right foundation for a large, dynamically growing enterprise network.

### 4.2 Hub-and-spoke

A hub-and-spoke architecture connects many VPCs to a shared routing hub, usually AWS Transit Gateway.

One hub can provide centralized route control and shared connectivity, without granting every spoke access to every other spoke.

Transit Gateway is a Regional network transit service. It supports VPC and supported hybrid network attachments, with route tables controlling which attachments can exchange traffic.

Advantages

* Fewer connectivity relationships to manage.

* Central routing and segmentation.

* Easier integration with shared services and inspection.

* Scales more cleanly as accounts and VPCs are added.

Trade-offs

* Attachment, data-processing, and potentially inter-Region transfer costs.

* Routing mistakes in a shared hub can affect many workloads.

* The network team becomes responsible for a critical shared service.

### 4.3 Segmented hub-and-spoke

For a SaaS platform, a single Transit Gateway route table that allows every spoke to reach every other spoke is usually too permissive.

Instead, create separate route tables for distinct traffic classes.

| Transit Gateway route table | Associated attachments       | Intended connectivity                                |
| --------------------------- | ---------------------------- | ---------------------------------------------------- |
| prod-rt                     | Production VPCs              | Production services and approved shared services     |
| nonprod-rt                  | Development and staging VPCs | Non-production services and approved shared services |
| inspection-rt               | Inspection VPC               | Routes back to workload networks after inspection    |
| egress-rt                   | Approved egress path         | Controlled internet-bound traffic                    |

These names are design conventions, not AWS-enforced special route-table types.

Remember the distinction between association and propagation:

* Association determines which Transit Gateway route table is used to route packets arriving from an attachment.

* Propagation installs routes learned from an attachment into a Transit Gateway route table.

* Static routes explicitly direct traffic to a specified attachment.

For example, a production VPC may have its attachment associated with `prod-rt`, while its CIDR is propagated into `inspection-rt` so that inspected return traffic can be routed back to production.

Route tables should be designed from the actual packet paths, not simply copied from environment names.

### 5\. AWS Transit Gateway versus AWS Cloud WAN

Both services help build larger networks, but their scope and operational models differ.

![Hub-and-Spoke Network with Centralized Egress and Traffic Inspection use AWS Transit Gateway and AWS Firewall | Python | Pulumi Registry](https://images.openai.com/static-rsc-4/MQChPHI_6hmX5tAdJLP8PEWrcOjvaqEa6106Ei70iOAQ26F7Icc_RE6evnLCnJvy3vpXjTojrWSn7KSe6H6gB4t0iSnYfdL0elzsBrCuIL8Uk-b9WqB84YcUFpKXMoAkPnII0bCz6DKV7HVmjHCTtoznrqClSoZVISrPMIwT2QMR9j8Rad3g0UOLCRCe-usS?purpose=fullsize)

AWS Transit Gateway

Regional connectivity and routing hub

Choose it when you need to connect VPCs in a Region, integrate hybrid connectivity, segment traffic with route tables, and maintain detailed routing control.

![Achieving a successful implementation of AWS Cloud WAN - AWS Cloud Chronicles](https://images.openai.com/static-rsc-4/580uFqc9dFgAEGEfhXFuMGzLY2G5moIoTeu9cfrpXrhvS83Ustk1Zq6Byc59bAKh1xvLIpAcpP67hoWLKzSv0zVA4Y6Yd2_fWHuGgfIEkBWQBkU7Xnf1NyuuTcWGw_GGUACtxXBbRD6fYorYDFxpx29Fm2uhag-YzkI3lX1DOkqjAIJep7UsqgXGsJTRiICs?purpose=fullsize)

AWS Cloud WAN

Policy-driven global network

Choose it when your organization needs a centrally managed network spanning multiple AWS Regions and supported on-premises connections, with network segments and a core network policy.

AWS's comparison describes Transit Gateway as a strong fit for regional hub connectivity and Cloud WAN as a fit for unified global networking.

| Decision factor     | Transit Gateway                                                   | Cloud WAN                                                                     |
| ------------------- | ----------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| Primary design      | Regional routing hub                                              | Global network and policy                                                     |
| Routing control     | Explicit route tables, associations, propagation                  | Core network policy and segments                                              |
| Multi-Region        | Inter-Region peering between gateways                             | Global core network with supported Regional edges                             |
| Hybrid connectivity | Direct integration with supported VPN and Direct Connect patterns | Integrates supported AWS and on-premises connectivity into the global network |
| Best fit            | Regional multi-VPC architecture                                   | Multi-Region, multi-site network governance                                   |
| Main trade-off      | More topology and route management as the network grows           | Additional service concepts, policy management, and cost                      |

These are not mutually exclusive. Cloud WAN can coexist with Transit Gateways; an organization can retain existing regional TGW deployments while adopting Cloud WAN for broader global connectivity.

Practical decision rule: begin with Transit Gateway for a predominantly single-Region platform. Evaluate Cloud WAN when the challenge becomes global network consistency, cross-Region segmentation, and governance across many sites—not merely because the organization has more than one VPC.

Before selecting either service, verify the current Regional availability, attachment types, quotas, supported routing features, and pricing for your specific topology.

### 6\. Centralized traffic inspection

Centralized inspection is a security architecture in which selected network traffic passes through an inspection layer before reaching its destination.

Common requirements include:

* Filtering internet-bound traffic.

* Inspecting traffic between VPCs.

* Applying consistent network firewall policies.

* Logging network security events centrally.

* Controlling access to on-premises networks and shared services.

AWS Network Firewall provides managed stateful and stateless network filtering, with supported rule capabilities including network-layer filtering, application protocol inspection, and intrusion-prevention-related controls.

### 6.1 Inspection VPC architecture

A conventional centralized design places Network Firewall in a dedicated inspection VPC attached to Transit Gateway.

Workload VPC A

Application subnet → TGW attachment

Transit Gateway route table directs traffic to inspection

Inspection VPC

AWS Network Firewall

Dedicated endpoint subnets in multiple AZs

Inspects the traffic permitted by firewall policy

Forward traffic using the appropriate routes

Workload VPC B or approved destination

The architecture is incomplete until both directions of every inspected flow have been accounted for. AWS specifically warns that Network Firewall does not support asymmetric routing: the request and response must traverse the appropriate same firewall endpoint.

### 6.2 How the routing works

Suppose:

* Production VPC CIDR: `10.20.0.0/16`

* Staging VPC CIDR: `10.30.0.0/16`

* Inspection VPC CIDR: `10.250.0.0/16`

A production workload sends a packet to a staging workload.

* The production subnet route table sends `10.30.0.0/16` to Transit Gateway.

* The TGW route table associated with the production attachment directs the destination toward the inspection VPC attachment.

* The inspection VPC subnet route table directs the packet to the appropriate Network Firewall endpoint.

* The firewall evaluates its rules.

* If allowed, the packet follows the route toward staging.

* The response follows a deliberately designed return path through inspection.

The destination CIDR and route tables must make this path possible. Firewall rules do not create routes, and a Transit Gateway attachment alone does not enforce inspection.

### 6.3 Appliance mode and symmetry

When a centralized stateful appliance requires flow affinity, Transit Gateway appliance mode on the inspection VPC attachment can help keep the traffic in the same Availability Zone for a flow. You must still configure forward and return routes correctly. Appliance mode is not a substitute for route-table analysis.

Plan firewall endpoints and their routes across the Availability Zones used by workloads. Also consider what happens when an AZ or firewall endpoint becomes unavailable.

### 6.4 A newer integration option: network function attachments

AWS Transit Gateway now documents network function attachments, including an AWS Network Firewall integration that can manage the underlying firewall connectivity without requiring you to build and maintain the traditional inspection VPC infrastructure yourself. The service-managed approach changes the attachment and routing model, so verify current support and limitations before choosing it.

The architectural objective is the same: route selected flows through inspection and preserve symmetry. The implementation differs.

Use the traditional inspection VPC model when you need its specific VPC-based routing and service-chain architecture or have an established deployment. Evaluate the newer attachment model for a simpler supported integration. Do not combine route examples from the two models without checking the relevant AWS documentation.

### 7\. Ingress and egress architecture

Ingress and egress are different security problems and should be designed separately.

* Ingress: traffic entering an application from customers, partners, or approved external networks.

* Egress: traffic leaving workloads for public APIs, package repositories, SaaS providers, or other external destinations.

* East-west traffic: traffic between internal VPCs, services, and environments.

### 7.1 Public ingress for a SaaS application

A common production pattern is to expose an application through a public Application Load Balancer (ALB), while keeping application and database workloads in private subnets.

Internet / customers

Public ALB

HTTPS listener · TLS certificate · WAF integration if required

Private application subnets

Application targets accept traffic only from the ALB security group

Private database subnets

Database ports permitted only from authorized application workloads

For this design:

* The ALB security group accepts HTTPS from approved public sources, commonly the internet when the service is public.

* The application security group accepts its application port from the ALB security group.

* The database security group accepts its database port from the application security group.

* The database subnets do not need a route to the internet for ordinary internal database communication.

A public ALB does not mean its targets must have public IP addresses.

When should ingress traffic pass through centralized inspection?

That depends on the threat model and required inspection controls. Many applications use AWS WAF at an ALB or CloudFront, while other architectures require network-layer inspection through Network Firewall or another supported inspection service.

Do not assume a public ALB's traffic automatically traverses the Transit Gateway inspection path. Ingress inspection requires explicit routing and a supported deployment model. Network Firewall's architecture documentation identifies supported traffic paths and limitations.

### 7.2 Centralized egress

Centralized egress sends approved internet-bound traffic from multiple VPCs through a common security and NAT layer.

A conventional IPv4 path is:

```text
Private workload subnet
        |
        v
Workload VPC route table
        |
        v
Transit Gateway
        |
        v
Inspection VPC / Network Firewall
        |
        v
NAT Gateway
        |
        v
Internet Gateway
        |
        v
Internet destination
```

The actual subnet and Transit Gateway routes must implement this path, including the return direction. The NAT gateway translates private IPv4 source addresses; Network Firewall itself does not perform NAT.

Centralized egress can reduce duplicated infrastructure and standardize outbound controls, but it introduces additional routing dependencies and data-transfer charges. Cross-AZ traffic and centralized bottlenecks must be considered.

A distributed egress model, with per-VPC or per-AZ egress infrastructure, may be preferable when workload isolation, low latency, or fault containment matters more than centralization.

### 7.3 Egress alternatives

| Pattern                           | Appropriate when                                  | Main trade-off                                       |
| --------------------------------- | ------------------------------------------------- | ---------------------------------------------------- |
| Per-VPC NAT gateways              | Independent workload egress and isolation         | More duplicated infrastructure                       |
| Centralized inspection and NAT    | Organization-wide outbound policy                 | More routing complexity and shared dependencies      |
| VPC endpoints / PrivateLink       | Workloads need selected AWS or private services   | Endpoint costs and service-specific constraints      |
| No general internet egress        | Highly restricted workloads                       | Requires deliberate dependency and update management |
| IPv6 egress-only internet gateway | IPv6 workloads need outbound-only internet access | It is not a replacement for IPv4 NAT                 |

Prefer private service access where practical rather than routing every AWS API request through a general-purpose internet path.

### 8\. Development, staging, and production isolation

A multi-account architecture is valuable because it separates ownership and permissions as well as network resources.

However, separate accounts do not automatically prevent communication. Connectivity still depends on routes, security controls, shared resources, and any other enabled network path.

For our SaaS platform, use the following policy as a starting point.

| Source            | Destination                      | Default policy                                                          |
| ----------------- | -------------------------------- | ----------------------------------------------------------------------- |
| Development       | Staging                          | Deny unless a specific testing need is approved                         |
| Development       | Production                       | Deny                                                                    |
| Staging           | Production                       | Deny by default; allow only a documented deployment or integration path |
| Production        | Shared DNS and approved services | Allow required protocols and destinations                               |
| Production        | Development                      | Deny                                                                    |
| All workloads     | Central logging                  | Allow required telemetry paths                                          |
| Private workloads | Public internet                  | Permit only through approved egress paths                               |

This is a policy intent, not a substitute for implementation. For example, AWS Systems Manager access to an instance, DNS resolution, or an application integration may require different service-specific paths.

### A layered isolation strategy

Use several controls together:

* Separate accounts and IAM roles for environment ownership.

* Separate VPCs and non-overlapping CIDRs.

* Transit Gateway route-table segmentation.

* Security groups that allow only required application flows.

* Network Firewall for traffic requiring centralized network inspection.

* SCPs and infrastructure policies to prevent unauthorized network changes.

* Monitoring for route changes, attachment creation, and security-rule modifications.

For stricter production isolation, consider a separate Transit Gateway or a distinct network connectivity domain for sensitive production workloads. This reduces shared routing dependencies, but it also increases cost and operational complexity.

Least privilege should apply to network administration too. Application teams can be allowed to manage their application VPC resources without being allowed to alter central Transit Gateway routes or firewall policies.

### 9\. Cross-Region networking and disaster recovery

Multi-Region architecture should begin with the recovery objective, not with a decision to connect every VPC to every other Region.

Three common models are:

![Leverage AWS Resilience Lifecycle Framework to assess and improve the resilience of application using AWS Resilience Hub | AWS Cloud Operations Blog](https://images.openai.com/static-rsc-4/abqlURUbYNfML0JxyLPpV8oLtv6FT4ngGLHqSvR8OpSsneMSgkCHLwZlQz8dUADnClL0rOUmV-1cLnUpSwc79akLdRu6Is-65X1JTL2lo0cGNZG1I_rSFO9vLNFbk0Q8S7pkFZom8hlNg3kuP5QU6gz57kLdn9G4NjsNHWSKxZzUwMdHy0DyX4LgQS77_Aos?purpose=fullsize)

Multi-AZ, single Region

Best starting point for many SaaS applications.

Protects against individual Availability Zone failures. It does not protect the application from a Region-wide outage.

![AWS Warm Standby Disaster Recovery: A Cost-Effective Approach | CloudEliteTraining posted on the topic | LinkedIn](https://images.openai.com/static-rsc-4/NCHegw9fwXuwpmKLWdTvZ-pxLXAkJ8Z7j_83G8V7Ri87ZboCKmYeqf5jkX7VGXXTE1HTFLoWOYcx1eqafIbN4qnIM1datt1PVXNU7Als5dhci7Ozvmsbr526bm38vjwEDwDnKLNtdgbi3JmK14hqLwQBwZFCYLfIWBxRNJhZsuHmpNRU0lcKvK77IXI2nL16?purpose=fullsize)

Warm standby

A second Region has a reduced but functional deployment.

Can offer a faster recovery than rebuilding everything from scratch, at the cost of operating more infrastructure.

![REL13-BP02 Utiliser des stratégies de reprise définies pour répondre aux objectifs de reprise - AWS Well-Architected Framework](https://images.openai.com/static-rsc-4/-uQEK4wqMyqm_ZqEwc2HCXLH6DVQIb929iqO9FdOodTD6FQZ7Lvzev35plpytWvYaLusF5bo6QdFitoneIS6vin-qURk1N6QIj9pZLykkzZbef6sKD1JOiputs4UIYVaSjRTEH43EDvmLi4kAv-O6xlbm2IPUf1ZMG7O0T401wY8yEZLxpD04VLhHG9vy2gO?purpose=fullsize)

Active-active

Multiple Regions actively serve customers.

Can improve regional resilience and latency, but requires careful data consistency, traffic steering, and failure-handling design.

### 9.1 Cross-Region connectivity options

* Transit Gateway peering: connect regional Transit Gateways where regional hub routing is the desired model.

* Cloud WAN: use a policy-driven global network where supported when many Regions and sites need a unified topology.

* VPC peering: use for selected direct connections when the limited topology and non-transitive behavior are acceptable.

* Private application endpoints: expose only the services that need cross-Region access instead of connecting entire network domains.

Do not assume Transit Gateway peering automatically provides transitive routing between all connected VPCs or supports every inspection design. Routing and inspection must be evaluated at each regional boundary.

### 9.2 Define RTO and RPO

Two important disaster-recovery targets are:

* RTO (Recovery Time Objective): the maximum acceptable time to restore the service.

* RPO (Recovery Point Objective): the maximum acceptable data loss measured in time.

A network design alone cannot guarantee either target. DNS failover, application deployment, database replication, identity access, secret distribution, and external dependencies all affect recovery.

For example, a warm-standby architecture with replicated data can still fail to meet its RTO if network routes, firewall policies, or application configuration must be rebuilt manually during an incident.

### 9.3 Avoid making the network hub a single point of failure

A centralized Transit Gateway and inspection service may be highly available within a Region, but a Region-level failure can still affect regional connectivity.

For stronger resilience:

* Deploy workload subnets across multiple AZs.

* Plan inspection coverage for the AZs in use.

* Maintain a tested alternate Region where the recovery objectives justify it.

* Keep critical network configuration and deployment permissions available during recovery.

* Test route changes, firewall failures, and regional failover in controlled exercises.

* Avoid relying on undocumented manual changes to restore connectivity.

### 10\. Resilience and blast-radius reduction

Centralization improves consistency, but central services can amplify failures.

Consider a firewall rule deployed incorrectly in a shared inspection layer. If all VPC-to-VPC traffic and internet egress depends on that firewall, a single change can disrupt many applications.

The goal is not to eliminate all shared components. It is to ensure that failures are bounded, observable, and recoverable.

| Risk                                               | Mitigation                                                                    |
| -------------------------------------------------- | ----------------------------------------------------------------------------- |
| Incorrect central route                            | Review and validate route changes; stage changes where practical              |
| Firewall policy blocks legitimate traffic          | Version policies, test rule changes, monitor drops, prepare rollback          |
| One AZ becomes unavailable                         | Multi-AZ deployment and route design                                          |
| Production routes leak into development            | Separate route tables and tightly controlled propagation                      |
| Network account compromised                        | Strong IAM boundaries, audited administration, independent security oversight |
| One Region fails                                   | Documented recovery design and tested alternate Region                        |
| CIDR overlaps with a new VPC                       | Organization-wide IPAM pools and allocation governance                        |
| Central egress becomes a bottleneck or cost driver | Measure traffic, evaluate distributed egress, and review cross-AZ paths       |

A useful design review asks: If this component or policy fails, which applications lose connectivity, and can unrelated workloads continue operating?

### 11\. Multi-account IP address management with IPAM

As VPCs multiply, IP address allocation becomes an organizational problem rather than an individual VPC task.

Suppose three teams independently create networks:

* Production: `10.20.0.0/16`

* Staging: `10.20.0.0/16`

* Shared services: `10.30.0.0/16`

Production and staging now overlap. That creates problems for Transit Gateway routing, hybrid connectivity, and network inspection.

### 11.1 Establish organization-wide address pools

Amazon VPC IP Address Manager (IPAM) can monitor address usage across an AWS Organization and share IP address pools with member accounts. A delegated IPAM administrator can manage pools centrally without using the organization management account as the IPAM account.

An illustrative allocation plan:

| Network purpose              | Example CIDR | Allocation intent             |
| ---------------------------- | ------------ | ----------------------------- |
| Regional production pool     | 10.0.0.0/12  | Production VPCs               |
| Regional non-production pool | 10.16.0.0/12 | Development and staging       |
| Shared infrastructure pool   | 10.32.0.0/16 | DNS, tooling, shared services |
| Inspection pool              | 10.33.0.0/16 | Inspection VPCs               |
| Future expansion             | 10.64.0.0/10 | Reserved for future needs     |

These are illustrative private IPv4 allocations, not prescribed AWS ranges. Check the entire enterprise address plan—including on-premises, VPN, Direct Connect, partner networks, and other Regions—before reserving pools.

The objective is to allocate address space hierarchically, leaving room for growth and avoiding overlaps.

### 11.2 Governance model

A practical workflow is:

* The networking team defines IPAM scopes and address pools.

* Each environment or Region receives an approved pool.

* VPC creation workflows request CIDRs from the appropriate pool.

* IPAM tracks utilization and identifies allocation issues.

* Policy checks reject unauthorized or out-of-range CIDRs.

* Periodic reviews identify unused space and plan future expansion.

IPAM improves allocation and visibility, but it does not automatically repair overlapping networks or guarantee that all external networks have compatible addressing.

Official reference: [Integrate IPAM with AWS Organizations](https://docs.aws.amazon.com/vpc/latest/ipam/enable-integ-ipam.html?utm_source=chatgpt.com).

### 12\. Implementing the core architecture with Pulumi

We'll implement the core regional transit layer first. The full inspection VPC, firewall, egress, and workload attachments require additional resources and carefully coordinated routes, so we'll treat those as separate deployment components rather than pretending a few resources create a production-ready security architecture.

The following example creates:

* A Transit Gateway.

* Separate route tables for production and non-production.

* A route table intended for inspection traffic.

* An AWS RAM resource share for cross-account use.

* Explicit outputs for subsequent infrastructure components.

It does not create workload VPCs, firewall rules, or production routing paths yet.

### 12.1 Project structure

```text
saas-network/
├── Pulumi.yaml
├── requirements.txt
└── __main__.py
```

`Pulumi.yaml`

```yaml
name: saas-network
runtime:
  name: python
description: Regional multi-account SaaS networking foundation
```

`requirements.txt`

```text
pulumi
pulumi-aws
```

Install dependencies in a virtual environment and use the current stable Pulumi AWS provider version appropriate for your environment. For repeatable deployments, pin and lock the exact versions you validate rather than leaving dependencies floating indefinitely.

```bash
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pulumi login
pulumi stack init dev
pulumi config set aws:region eu-west-3
```

Use an AWS identity authorized to create the resources in the network account. For CI/CD, prefer short-lived credentials via GitHub Actions OIDC instead of long-lived access keys.

### 12.2 Core Transit Gateway resources

`__main__.py`

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

# These IDs should be supplied from your approved
# AWS Organizations account inventory.
organization_arn = config.require("organizationArn")

# Central regional routing hub.
tgw = aws.ec2transitgateway.TransitGateway(
    "saas-regional-tgw",
    description="SaaS regional transit gateway",
    amazon_side_asn=64520,
    auto_accept_shared_attachments="disable",
    default_route_table_association="disable",
    default_route_table_propagation="disable",
    dns_support="enable",
    vpn_ecmp_support="enable",
    tags={
        "Project": "saas-network",
        "ManagedBy": "pulumi",
        "Environment": pulumi.get_stack(),
    },
)

# Explicit routing domains.
prod_rt = aws.ec2transitgateway.RouteTable(
    "prod-route-table",
    transit_gateway_id=tgw.id,
    tags={"Name": "prod-rt"},
)

nonprod_rt = aws.ec2transitgateway.RouteTable(
    "nonprod-route-table",
    transit_gateway_id=tgw.id,
    tags={"Name": "nonprod-rt"},
)

inspection_rt = aws.ec2transitgateway.RouteTable(
    "inspection-route-table",
    transit_gateway_id=tgw.id,
    tags={"Name": "inspection-rt"},
)

# Share the hub with the organization.
# This does not grant member accounts permission
# to administer the owner's TGW route tables.
network_share = aws.ram.ResourceShare(
    "saas-network-share",
    name="saas-regional-transit-share",
    allow_external_principals=False,
    tags={"Project": "saas-network"},
)

share = aws.ram.ResourceAssociation(
    "share-transit-gateway",
    resource_arn=tgw.arn,
    resource_share_arn=network_share.arn,
)

organization_share = aws.ram.PrincipalAssociation(
    "share-with-organization",
    principal=organization_arn,
    resource_share_arn=network_share.arn,
)

pulumi.export("transitGatewayId", tgw.id)
pulumi.export("productionRouteTableId", prod_rt.id)
pulumi.export("nonproductionRouteTableId", nonprod_rt.id)
pulumi.export("inspectionRouteTableId", inspection_rt.id)
pulumi.export("resourceShareArn", network_share.arn)
```

Important implementation notes

* Verify the exact Pulumi AWS provider schema for the selected version before deployment; provider versions can change supported arguments and resource behavior.

* `organizationArn` should be the ARN for your actual AWS Organization, not a guessed value.

* AWS RAM organization sharing requires the appropriate organization integration and permissions.

* A resource share does not itself create attachments, associate them with route tables, or grant access to workloads.

* Disabling default route-table association and propagation makes routing explicit, but means every attachment must be configured intentionally.

* The ASN must be compatible with the rest of your routing plan, particularly if you later introduce BGP-based hybrid connectivity.

### 12.3 Configuration and preview

Configure the organization ARN:

```powershell
pulumi config set organizationArn "arn:aws:organizations::123456789012:organization/o-exampleorg"
```

The example above uses a placeholder. Replace it with the actual ARN before deploying.

Preview first:

```bash
pulumi preview
```

Review the plan for unintended replacements, permissions, resource-sharing changes, and costs. If it is correct, deploy:

```bash
pulumi up
```

Retrieve the identifiers:

```bash
pulumi stack output
```

Never commit real credentials or secrets to source control. Pulumi state also contains infrastructure metadata, so use a properly secured state backend and restrict access to it.

### 12.4 What must be added before this is production-ready?

The transit resources above are only the foundation. The full design needs:

* Workload VPCs and multi-AZ subnets.

* Cross-account VPC attachments, created and accepted under the correct account ownership.

* Explicit attachment-to-route-table associations and appropriate route propagation.

* Static routes directing selected flows to the inspection path.

* Network Firewall and its supported attachment or inspection architecture.

* VPC route tables that direct packets to Transit Gateway where appropriate.

* Approved egress paths, including NAT gateways if required.

* Shared DNS and endpoint access.

* Network logging and monitoring.

* Validation of both forward and return paths.

AWS RAM allows Transit Gateway sharing across accounts. The resource owner retains control over the shared Transit Gateway and its route tables; consumer accounts can create attachments in their own VPCs subject to the relevant permissions.

For the firewall portion, evaluate both the traditional inspection VPC design and the newer Transit Gateway-attached Network Firewall integration before choosing the implementation. The latter has its own routing and attachment requirements.

### 13\. Hands-on lab — Design a multi-account SaaS network

Architecture-first, Pulumi-ready

The goal is to design a network that isolates production, provides centralized inspection, and enables approved shared services. Start by validating the topology before deploying billable infrastructure.

### 13.1 Requirements

Assume the following illustrative environment:

| Environment     | Account                      | VPC CIDR      |
| --------------- | ---------------------------- | ------------- |
| Network         | Dedicated networking account | 10.250.0.0/16 |
| Shared services | Infrastructure account       | 10.32.0.0/16  |
| Development     | Development account          | 10.16.0.0/16  |
| Staging         | Staging account              | 10.20.0.0/16  |
| Production      | Production account           | 10.0.0.0/16   |

These ranges are examples; verify that they don't overlap with any existing corporate or cloud networks.

### 13.2 Draw the traffic paths

Your design must support the following paths:

Path A — Customer to production

Internet → public ALB → private application → private database.

Only the required application ports are permitted between tiers.

Path B — Production to an external API

Production → Transit Gateway → approved inspection path → NAT / internet gateway → API.

Return traffic must follow a compatible stateful inspection path.

Path C — Production to shared DNS

Production → approved private DNS resolution path → shared DNS service.

Configure the necessary DNS associations or forwarding rules, routes where applicable, and security permissions.

Path D — Development to production database

Denied by default.

There should be no accidental route or permissive security rule enabling this connection.

### 13.3 Implementation sequence

* Establish the accounts. Confirm AWS Organizations, account ownership, deployment roles, and least-privilege permissions.

* Allocate CIDRs. Use IPAM or an approved address inventory to prevent overlaps.

* Deploy the Transit Gateway. Use the network account and share it through AWS RAM with approved workload accounts.

* Create the VPCs. Use Pulumi to deploy multi-AZ subnets, route tables, and security groups in each account.

* Attach the VPCs. Create attachments from the workload accounts and complete any required acceptance in the network account.

* Configure segmentation. Associate attachments with the appropriate TGW route tables and create explicit routes.

* Deploy inspection. Select a supported Network Firewall architecture, configure firewall policies, and validate forward and return routing.

* Implement egress. Configure the approved NAT and internet-gateway path, or private endpoints where public internet access is unnecessary.

* Enable observability. Collect VPC Flow Logs and firewall logs; monitor routing and attachment changes.

* Validate isolation. Test approved connections and confirm prohibited connections fail for the intended reason.

### 13.4 Inspect and verify with AWS CLI

Run these commands with an identity authorized to inspect the corresponding account and Region.

List Transit Gateways:

```bash
aws ec2 describe-transit-gateways \
  --region eu-west-3
```

Inspect Transit Gateway attachments:

```bash
aws ec2 describe-transit-gateway-attachments \
  --region eu-west-3 \
  --filters Name=transit-gateway-id,Values=tgw-xxxxxxxx
```

Inspect route tables:

```bash
aws ec2 describe-transit-gateway-route-tables \
  --region eu-west-3 \
  --filters Name=transit-gateway-id,Values=tgw-xxxxxxxx
```

Inspect the routes of a particular route table:

```bash
aws ec2 search-transit-gateway-routes \
  --region eu-west-3 \
  --transit-gateway-route-table-id tgw-rtb-xxxxxxxx \
  --filters Name=state,Values=active
```

Inspect a VPC's subnet route tables:

```bash
aws ec2 describe-route-tables \
  --region eu-west-3 \
  --filters Name=vpc-id,Values=vpc-xxxxxxxx
```

These commands are for inspection, not configuration. Replace the example IDs and Region with actual values.

A route being marked `active` does not prove that the complete application connection works. Validate security groups, Network ACLs, firewall policy, DNS, the return path, and application listeners as well.

### 13.5 Troubleshooting scenarios

| Symptom                                      | First places to investigate                                                          |
| -------------------------------------------- | ------------------------------------------------------------------------------------ |
| Production cannot reach shared services      | TGW association, propagated or static routes, destination VPC route, security groups |
| Internet egress times out                    | Default routes, inspection path, firewall rules, NAT gateway, internet gateway       |
| Firewall allows traffic but connection fails | Return routes, asymmetric routing, destination security rules                        |
| Development reaches production unexpectedly  | TGW route propagation, static routes, alternative peering paths, security groups     |
| Cross-Region connection fails                | Inter-Region connectivity, route tables on both sides, CIDR overlap, firewall rules  |
| A new VPC cannot obtain the intended CIDR    | IPAM pool allocation, permissions, pool capacity, allocation rules                   |

Use Reachability Analyzer for supported configuration-level path analysis, VPC Flow Logs for observed traffic, and Network Firewall logs for firewall decisions. No single tool proves that every layer of the application is functioning.

### 14\. Cost and operational trade-offs

Centralized networking introduces ongoing charges, so model the costs before deployment.

| Resource                  | Cost considerations                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| Transit Gateway           | Attachment hours and traffic processing                                                      |
| Network Firewall          | Endpoint hours, traffic processing, and optional inspection or threat-protection features    |
| Cloud WAN                 | Core network edges, attachment hours, data processing, peering, and applicable data transfer |
| NAT Gateway               | Hourly charges and data processing, subject to applicable pricing adjustments                |
| VPC endpoints             | Endpoint type, Region, AZ deployment, and traffic                                            |
| IPAM                      | Tier and applicable active-IP pricing                                                        |
| Cross-Region connectivity | Inter-Region data transfer and service-specific charges                                      |

AWS documents these pricing dimensions in its official guides.

Do not assume centralized inspection is always cheaper. It can reduce duplicated endpoints, but it can also increase cross-AZ traffic, route complexity, and the volume of traffic processed by central services.

For a lab, start with an architecture diagram, Pulumi previews, and configuration validation. Deploy real AWS infrastructure only when you can accept the associated charges. This lab is not guaranteed to be free.

### 15\. Security and production review

Before considering the design ready for production, confirm:

* Production has a clearly defined connectivity boundary.

* Environment-to-environment routes are explicitly controlled.

* Only approved traffic passes through the central inspection path.

* Network Firewall routes preserve symmetric inspection.

* Critical services have appropriate multi-AZ coverage.

* Internet ingress and egress are designed independently.

* IP address allocations are centrally governed.

* Network changes are reviewed, audited, and reversible.

* Cross-Region recovery has defined RTO and RPO targets.

* Logging is available to the teams responsible for incident response.

* Network administration is separated from routine workload administration.

* Costs and resource cleanup responsibilities are documented.

### 16\. Cleanup

If you deployed the Pulumi foundation, inspect the resources before removing them:

```bash
pulumi preview --diff
```

To remove the resources managed by that stack:

```bash
pulumi destroy
```

Review the plan carefully. Deleting the Transit Gateway or modifying its sharing can disrupt connected workloads, and a shared attachment may remain after a resource is unshared. Remove dependencies in a controlled order, and never destroy a shared production network simply to clean up a lab.

For this module, the safest approach is to use a dedicated lab account and stack.

### 17\. Official AWS references

These are the primary references for further study and for verifying implementation details.

[AWS Transit Gateway documentation](https://docs.aws.amazon.com/vpc/latest/tgw/?utm_source=chatgpt.com)

Attachments, routing, sharing, segmentation, and inspection integration.

[AWS Network Firewall Developer Guide](https://docs.aws.amazon.com/network-firewall/latest/developerguide/?utm_source=chatgpt.com)

Firewall policies, routing architectures, and symmetric traffic inspection.

[AWS Cloud WAN documentation](https://docs.aws.amazon.com/network-manager/latest/cloudwan/?utm_source=chatgpt.com)

Global network policies, segments, and attachment management.

[Amazon VPC IPAM documentation](https://docs.aws.amazon.com/vpc/latest/ipam/?utm_source=chatgpt.com)

IP allocation, organizational integration, pools, and address governance.

[AWS Resource Access Manager documentation](https://docs.aws.amazon.com/ram/latest/userguide/?utm_source=chatgpt.com)

Sharing networking resources between accounts.

[Pulumi AWS provider documentation](https://www.pulumi.com/registry/packages/aws/?utm_source=chatgpt.com)

Current resource schemas and supported Python infrastructure APIs.

### Module 13 summary

The most important architectural lesson is that a scalable AWS network is not simply a collection of connected VPCs. It is a controlled system of routing domains, security boundaries, shared services, address-allocation policies, and recovery mechanisms.

For the SaaS platform in this course, a strong starting design is AWS Organizations + Transit Gateway + segmented route tables + centralized inspection + shared services + IPAM, with Cloud WAN evaluated as global networking requirements grow.

The next module is Module 14 — VPC for Containers and Kubernetes, covering Amazon ECS, Amazon EKS, pod addressing, VPC CNI, IP exhaustion, load balancers, private AWS service access, and Kubernetes network policies.
