### Module 5 — Private Hosted Zones and Hybrid DNS with Route 53 Resolver

### 1\. Introduction

So far, we've focused primarily on public DNS and how Route 53 routes users to publicly accessible application endpoints.

However, real-world AWS architectures also need internal DNS.

Consider a SaaS application running across multiple VPCs:

* A frontend service runs in one VPC.

* Backend APIs run in another VPC.

* PostgreSQL runs in a private subnet.

* Internal services communicate using private DNS names.

* An on-premises environment needs to communicate with AWS services.

* AWS workloads sometimes need to resolve DNS names hosted by an on-premises DNS server.

You don't want internal services to depend on public DNS records or expose private infrastructure to the internet.

This is where Route 53 Private Hosted Zones and Route 53 Resolver become important.

By the end of this module, you'll understand how to build DNS architectures that work across multiple VPCs and hybrid AWS/on-premises environments.

### 2\. Private Hosted Zone Architecture

### 2.1 What is a Private Hosted Zone?

A Route 53 Private Hosted Zone is a DNS container that stores DNS records accessible only from associated VPCs.

Unlike a public hosted zone, its records aren't published through the public DNS hierarchy.

For example, imagine you have an internal application with these services:

| Service  | Private DNS name              | Private IP |
| -------- | ----------------------------- | ---------- |
| Frontend | frontend.internal.example.com | 10.10.1.10 |
| Backend  | api.internal.example.com      | 10.10.2.10 |
| Database | db.internal.example.com       | 10.10.3.10 |
| Redis    | redis.internal.example.com    | 10.10.4.10 |

You can create a private hosted zone:

```text
internal.example.com
```

Then configure records:

```dns
frontend.internal.example.com  A  10.10.1.10
api.internal.example.com       A  10.10.2.10
db.internal.example.com        A  10.10.3.10
redis.internal.example.com     A  10.10.4.10
```

Applications can use DNS names instead of hardcoding IP addresses.

For example:

```python
DATABASE_URL = "postgresql://app:password@db.internal.example.com:5432/app"
```

If the database IP changes, you update the DNS record rather than changing every application configuration.

### 2.2 Private Hosted Zone Architecture

![Inbound + Outbound Resolver Endpoints on AWS: A Practical Guide | by Jayantgulati | Medium](https://images.openai.com/static-rsc-4/dI5SLTTfLIx2QGFySUgv3h9_yOpo342tKz6gtmuJQd31SxL_U_TLYIK3CvYGDLbynfJQFSNTaw87XxABWL6ryQqyUVM6r4x4tNOw67ahD8_-N4sbWO9nT8Z-ZJR9U39HvLu-5ICtCEUIljAW5bU_gohRJPCPBxf7lFIsbbiSJPUUev6L6ebdvuxBOUhaNPRN?purpose=fullsize)

The architecture contains:

* A private hosted zone.

* One or more associated VPCs.

* DNS records stored inside the private hosted zone.

* EC2 instances or other VPC resources querying DNS.

* The Amazon-provided DNS resolver handling queries.

An important distinction:

A private hosted zone is not a DNS server that you deploy.

Route 53 manages the authoritative DNS service. You manage the zone and its records.

The VPC's built-in DNS resolver makes those records available to resources in associated VPCs.

### 2.3 Private versus Public Hosted Zones

| Feature         | Public hosted zone       | Private hosted zone     |
| --------------- | ------------------------ | ----------------------- |
| DNS visibility  | Public internet          | Associated VPCs         |
| Resolution      | Public DNS hierarchy     | VPC DNS resolver        |
| VPC association | Not required             | Required                |
| Internet access | Public DNS queries       | Not inherently required |
| Typical use     | Public websites and APIs | Internal services       |
| Example         | example.com              | internal.example.com    |

A private hosted zone can use a domain name that also exists in public DNS.

This leads to an important concept: split-horizon DNS.

### 3\. VPC Association and DNS Resolution Requirements

Creating a private hosted zone isn't enough. The VPC must also be configured correctly.

### 3.1 Associate a VPC with a Private Hosted Zone

Suppose you have:

```text
VPC: production-vpc
CIDR: 10.10.0.0/16
```

You create:

```text
Private Hosted Zone:
internal.example.com
```

You then associate the hosted zone with `production-vpc`.

Resources inside that VPC can resolve records belonging to the private zone.

For example:

```bash
dig api.internal.example.com
```

Expected result:

```text
api.internal.example.com.  300  IN  A  10.10.2.10
```

The DNS response contains the private IP address.

### 3.2 Associate Multiple VPCs

Private hosted zones can be associated with multiple VPCs, including VPCs in different AWS accounts, subject to the cross-account association procedure.

Consider:

```text
Production VPC: 10.10.0.0/16
Development VPC: 10.20.0.0/16
Shared Services VPC: 10.30.0.0/16
```

All three VPCs can use:

```text
internal.example.com
```

The DNS namespace can be shared across environments.

![Scaling your hybrid DNS setup with Amazon Route 53 Resolver endpoint metrics | Networking & Content Delivery](https://images.openai.com/static-rsc-4/U8R4uIhYGACydXTgcEbBjTkkbbvdO5aiAk6pnMXRIEKVqssblmWqt17eNFPunKqv7h6cS5z4VU5bPEjDeOsrnSXof4V7qDVpRuiTEoJsV2oLm6iCDiw2qgxrNhA80kHvM2xSyoVFiQ2BNQ89qLqn0V9B3zXU97tn8X0OmGcbmfLQNgJvM2FJwFYyOo4rj14C?purpose=fullsize)

There are two separate concerns:

* DNS visibility: whether a VPC can resolve the private hosted-zone records.

* Network connectivity: whether the VPC can actually reach the IP address returned by DNS.

Associating a private hosted zone does not automatically connect VPCs.

For example, Development VPC might resolve:

```text
db.internal.example.com -> 10.10.3.10
```

But it still needs appropriate routing and security-group permissions to reach that database in Production VPC.

This distinction is fundamental to AWS networking.

### 3.3 Cross-Account VPC Association

Suppose:

* Account A owns the private hosted zone.

* Account B owns another VPC.

The process is:

* Account A authorizes the VPC association.

* Account B creates the association.

* Route 53 completes the association.

AWS CLI:

```bash
aws route53 create-vpc-association-authorization \
  --hosted-zone-id Z123456789EXAMPLE \
  --vpc VPCRegion=ap-southeast-1,VPCId=vpc-0123456789abcdef0
```

In Account B:

```bash
aws route53 associate-vpc-with-hosted-zone \
  --hosted-zone-id Z123456789EXAMPLE \
  --vpc VPCRegion=ap-southeast-1,VPCId=vpc-0123456789abcdef0
```

After successful association, the VPC can resolve records in the private hosted zone.

The authorization can subsequently be removed without removing the completed association.

### 4\. VPC DNS Attributes

Two important VPC attributes control DNS functionality:

* `enableDnsSupport`

* `enableDnsHostnames`

Understanding their differences is essential.

### 4.1 enableDnsSupport

This attribute controls whether DNS resolution through the Amazon-provided VPC DNS resolver is supported.

When enabled:

* Instances can query the VPC DNS resolver.

* Private hosted zone records can be resolved.

* AWS-provided DNS functionality is available.

When disabled, instances cannot use the Amazon-provided resolver.

Enable it:

```bash
aws ec2 modify-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --enable-dns-support
```

### 4.2 enableDnsHostnames

This attribute controls whether instances launched in the VPC receive DNS hostnames.

It is particularly relevant to public DNS hostnames and certain AWS-managed DNS hostname behaviors.

Enable it:

```bash
aws ec2 modify-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --enable-dns-hostnames
```

### 4.3 Differences

| Attribute          | Purpose                                            |
| ------------------ | -------------------------------------------------- |
| enableDnsSupport   | Enables DNS resolution through Amazon-provided DNS |
| enableDnsHostnames | Enables DNS hostnames for instances in the VPC     |

For a typical VPC that uses Route 53 private hosted zones, enable both.

A common configuration is:

```python
enable_dns_support=True,
enable_dns_hostnames=True,
```

Important: Enabling DNS hostnames does not make private hosted zones work by itself. DNS support and the correct hosted-zone association are also necessary.

### 5\. Split-Horizon DNS

### 5.1 What is Split-Horizon DNS?

Split-horizon DNS means returning different DNS answers depending on where the DNS query originates.

Consider a company with a public application:

```text
app.example.com
```

External users should reach a public load balancer:

```text
app.example.com -> 203.0.113.10
```

Internal employees should reach a private load balancer:

```text
app.example.com -> 10.10.1.10
```

You can achieve this using two hosted zones with the same name:

* Public hosted zone: `example.com`

* Private hosted zone: `example.com`

![Split-Horizon DNS: routing users to different websites | Bibin Wilson posted on the topic | LinkedIn](https://images.openai.com/static-rsc-4/ylb_D07OKc1aKYkNtsjBtkZgnJa5sg3Ca03zXTVOtL6rjg3vKQNY06OTb9isrhduSpt5J9AX_D7uupeVblDstIbPTC1nGRIygPSvJGFls6nfDHwEY7jbskaQHQbj4fsQiO0WjdAvPkg_oZ6d3zfeIdVY8Ptcjb9F4jgoJ-out3MMU9GySvK8DlW7hZRLTZhF?purpose=fullsize)

The behavior is:

| Query origin     | DNS answer                                   |
| ---------------- | -------------------------------------------- |
| Internet user    | Public IP                                    |
| Associated VPC   | Private IP                                   |
| Unassociated VPC | Public DNS resolution, if publicly available |

This allows internal and external users to use the same application hostname.

### 5.2 Important DNS Behavior

When a matching private hosted zone is associated with a VPC, Route 53 uses it for queries from that VPC.

If a record is missing from the private zone, Route 53 generally returns `NXDOMAIN` rather than falling back to the corresponding public hosted zone.

For example:

Public zone:

```dns
api.example.com       A  203.0.113.10
www.example.com       A  203.0.113.20
```

Private zone:

```dns
api.example.com       A  10.10.1.10
```

From an associated VPC:

```bash
dig api.example.com
```

Returns:

```text
10.10.1.10
```

But:

```bash
dig www.example.com
```

May return:

```text
NXDOMAIN
```

This happens because the private zone is authoritative for the matching namespace inside that VPC.

Production consideration: When using split-horizon DNS, make sure the private hosted zone contains every record that internal clients need.

### 6\. Route 53 Resolver Architecture

Now we reach one of the most important parts of this module.

A private hosted zone handles private DNS records inside AWS, but what happens when DNS queries need to travel between AWS and an external network?

For example:

* An EC2 instance needs to resolve `server.corp.example.com`, which is hosted by an on-premises DNS server.

* An on-premises application needs to resolve `api.internal.example.com`, which is hosted in Route 53.

* Applications in different VPCs need to resolve DNS records hosted in another network.

The solution is Amazon Route 53 Resolver.

### 6.1 What is Route 53 Resolver?

Route 53 Resolver is the DNS resolution service associated with Amazon VPCs.

It provides:

* DNS resolution for AWS resources.

* Resolution of private hosted zone records.

* Forwarding DNS queries to external DNS servers.

* Receiving DNS queries from external networks.

* Hybrid DNS integration between AWS and on-premises environments.

Every VPC has access to an Amazon-provided DNS resolver.

Its IPv4 address is generally the VPC network address plus two.

For example:

```text
VPC CIDR: 10.10.0.0/16

VPC Resolver:
10.10.0.2
```

The reserved VPC+2 resolver address is available through the VPC's local networking infrastructure.

However, you should not configure on-premises DNS servers to send queries directly to the VPC+2 address. For cross-network DNS resolution, use Resolver endpoints.

### 6.2 Resolver Architecture

Route 53 Resolver provides two important endpoint types:

* Inbound endpoints.

* Outbound endpoints.

![Top 20 Amazon CloudFront Interview Questions and Answers (2025 Edition) | by Shivani Kumari @CloudDevOps Engineer | Medium](https://images.openai.com/static-rsc-4/tLzTs0pe2QbSCqHoWxV9OCBFfdxLsXbb6Qb1fRxV3XIh0e2vHFqL41uBO4zOf-pVxbKejrPNPjM7GVmdwNuFjl4bv1odXyvgfKsiMj70bOraj1UbTYNVpDfeI7U-SnIGE-IeE_TEpSrCwLfeXxAcWdYhlBSNEMSUg3tnfRRIgRWppyc2A3qYvheT5ylDpRvp?purpose=fullsize)

Think of them as two different directions of DNS traffic.

| Endpoint | DNS query direction    | Purpose                                         |
| -------- | ---------------------- | ----------------------------------------------- |
| Inbound  | External network → AWS | Allow external DNS servers to query AWS DNS     |
| Outbound | AWS → External network | Forward AWS DNS queries to external DNS servers |

Let's examine each one.

### 7\. Resolver Inbound Endpoints

### 7.1 What Is an Inbound Endpoint?

An inbound endpoint allows DNS queries originating outside a VPC to enter the VPC Resolver.

Suppose your company has:

```text
On-premises network:
192.168.0.0/16

AWS VPC:
10.10.0.0/16

Private hosted zone:
internal.example.com
```

The private hosted zone contains:

```dns
api.internal.example.com   A   10.10.2.10
db.internal.example.com    A   10.10.3.10
```

Your on-premises DNS server cannot directly query the Route 53 private hosted zone through public DNS.

Instead, create an inbound endpoint.

![An Update to Hybrid DNS for the Enterprise on AWS — Introducing Route 53 Resolver for Hybrid Cloud! | by Matt Adorjan | Medium](https://images.openai.com/static-rsc-4/VBcW3EFn0GtyqYA_VaAlzvnQF4GtfvVrnfMSPqhaxCthQkzPwOAiqWDGzdwFEdiKfL_pLlWZJaucxgkN958qw_sVfOjzYcUqRLkeDp1bGGeG0DEDopnaNJHrwXCiZ5-i2K7USG2MSAtpkkvdVSeeVUjTbaR_fGRGHhwkouG_bVWUZhGUKUvOK9ZFp6lgJzVr?purpose=fullsize)

The DNS resolution flow:

* An on-premises application requests `api.internal.example.com`.

* Its local DNS server receives the query.

* The local DNS server forwards the query to the Route 53 inbound endpoint.

* The inbound endpoint passes the query to the VPC Resolver.

* The VPC Resolver finds the matching private hosted zone.

* Route 53 returns `10.10.2.10`.

* The answer travels back to the on-premises DNS server.

The application can now use an AWS private DNS name.

### 7.2 Inbound Endpoint IP Addresses

An inbound endpoint consists of network interfaces in your selected VPC subnets.

For production architectures, configure at least two IP addresses in different Availability Zones.

Example:

```text
Inbound Endpoint:

VPC: 10.10.0.0/16

Availability Zone A:
10.10.1.100

Availability Zone B:
10.10.2.100
```

Your on-premises DNS server can forward queries to either IP address.

This provides availability across Availability Zones.

The endpoint's security group must allow DNS traffic from the appropriate on-premises source addresses.

DNS normally uses:

```text
UDP 53
TCP 53
```

Both protocols should be considered when configuring network security.

### 7.3 Inbound Endpoint Use Cases

* On-premises applications accessing AWS private services.

* Corporate DNS servers resolving AWS private hosted zones.

* Centralized DNS architecture across hybrid environments.

* Accessing private service names without exposing them publicly.

Important: Creating an inbound endpoint does not automatically make private hosted zones available through it. The private hosted zone must be associated with the VPC containing the inbound endpoint.

Also, your on-premises network needs network connectivity to the endpoint, such as Site-to-Site VPN or Direct Connect.

### 8\. Resolver Outbound Endpoints

### 8.1 What Is an Outbound Endpoint?

An outbound endpoint allows DNS queries originating inside a VPC to be forwarded to DNS servers outside AWS.

Consider this environment:

```text
AWS VPC:
10.10.0.0/16

On-premises network:
192.168.0.0/16

Corporate DNS server:
192.168.10.10
```

Your company hosts these DNS records on-premises:

```dns
server.corp.example.com    A    192.168.10.20
ldap.corp.example.com      A    192.168.10.30
git.corp.example.com       A    192.168.10.40
```

An EC2 instance inside AWS wants to resolve:

```text
server.corp.example.com
```

Route 53 doesn't automatically know about the records hosted on your corporate DNS server.

You need an outbound endpoint and a forwarding rule.

![Inbound/Outbound Endpoint :: AWS Workshop](https://images.openai.com/static-rsc-4/kLrF9JzzYfAHrUzWEvx3RXijOXi85YFEOf1NB8HhdBVYPdndGowuZpDnXbnw9F0kbUOk6Un8Af0heqzSiV8xcnuux8WnYxPIASJayz5frKCPeH3VD0Uxu5M_Q_u2oKUqYtbfu2pxxlgztFv_Ny2H5qVFNhc2799ZF-qhy-Amx7XCG_1yu_ukgOg3P-28y5-P?purpose=fullsize)

### 8.2 Outbound DNS Resolution Flow

* An EC2 instance requests `server.corp.example.com`.

* The query reaches the VPC Resolver.

* The Resolver checks its associated forwarding rules.

* It finds a rule for `corp.example.com`.

* The query is sent through the outbound endpoint.

* The outbound endpoint forwards the query to `192.168.10.10`.

* The corporate DNS server resolves the hostname.

* The DNS response returns through the outbound endpoint.

* The VPC Resolver returns the answer to the EC2 instance.

The application receives:

```text
server.corp.example.com -> 192.168.10.20
```

### 8.3 Outbound Endpoint Configuration

Like inbound endpoints, outbound endpoints use network interfaces in selected VPC subnets.

For production deployments, use at least two IP addresses in different Availability Zones.

Example:

```text
Outbound Endpoint:

VPC: 10.10.0.0/16

AZ A:
10.10.3.100

AZ B:
10.10.4.100
```

The outbound endpoint security group needs to allow outbound DNS traffic to the target DNS servers.

Your VPC route tables, network ACLs, and VPN or Direct Connect connectivity must also permit the traffic.

### 8.4 Inbound versus Outbound

| Characteristic  | Inbound                                | Outbound                                  |
| --------------- | -------------------------------------- | ----------------------------------------- |
| Direction       | Into AWS                               | Out of AWS                                |
| DNS source      | External DNS server                    | VPC Resolver                              |
| DNS destination | VPC Resolver                           | External DNS server                       |
| Main purpose    | Resolve AWS private records externally | Resolve external private records from AWS |
| Used by         | Corporate DNS                          | AWS workloads                             |

A useful way to remember:

* Inbound = Let external DNS queries enter AWS.

* Outbound = Let AWS DNS queries reach external DNS servers.

AWS recommends designing endpoint capacity and availability around query volume, endpoint IP addresses, and Availability Zone redundancy. Amazon Route 53 +1

### 9\. Resolver Forwarding Rules and Rule Associations

An outbound endpoint alone doesn't tell Route 53 where to send DNS queries.

You need forwarding rules.

### 9.1 What Is a Forwarding Rule?

A Resolver forwarding rule defines which DNS domain should be forwarded to which DNS server.

For example:

```text
Domain:
corp.example.com

Target DNS server:
192.168.10.10

Outbound endpoint:
outbound-endpoint
```

This tells Route 53:

"When a VPC DNS client requests a hostname belonging to `corp.example.com`, forward the query to `192.168.10.10` through the outbound endpoint."

### 9.2 Forwarding Rule Types

Route 53 Resolver supports several rule types.

| Rule type | Behavior                                              |
| --------- | ----------------------------------------------------- |
| FORWARD   | Forward matching DNS queries to specified DNS servers |
| SYSTEM    | Use the Resolver's normal system resolution behavior  |
| RECURSIVE | Resolve queries recursively using the Resolver        |

The most important rule for hybrid DNS is `FORWARD`.

`SYSTEM` rules are useful when you need to override a broader forwarding rule and return resolution to the Resolver's normal behavior.

`RECURSIVE` rules explicitly request recursive resolution rather than forwarding to specified target servers.

### 9.3 Creating a Forwarding Rule

Example configuration:

```text
Rule name: corporate-dns
Domain: corp.example.com
Rule type: FORWARD

Target:
192.168.10.10

Outbound endpoint:
rslvr-out-123456
```

The rule can then be associated with one or more VPCs.

### 9.4 Rule Associations

A forwarding rule does not automatically apply to every VPC.

You must associate it with the VPCs that need the rule.

Consider:

```text
Shared Services VPC
       |
       |-- corporate-dns rule
       |
       +-- Production VPC
       |
       +-- Development VPC
       |
       +-- Testing VPC
```

You can also share Resolver rules across AWS accounts using AWS Resource Access Manager (AWS RAM).

This is particularly useful for organizations with multiple accounts.

### 9.5 Rule Priority and Longest Matching Domain

Suppose you have these rules:

```text
corp.example.com       -> 192.168.10.10
dev.corp.example.com   -> 192.168.20.10
```

A query for:

```text
git.dev.corp.example.com
```

matches the more specific domain:

```text
dev.corp.example.com
```

This is an important property when designing hierarchical DNS forwarding.

### 9.6 Pulumi Example: Resolver Forwarding Rule

Using Python:

```python
import pulumi
import pulumi_aws as aws

outbound = aws.route53.ResolverEndpoint(
    "corporate-outbound",
    name="corporate-outbound",
    direction="OUTBOUND",
    security_group_ids=["sg-0123456789abcdef0"],
    ip_addresses=[
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-0123456789abcdef0"
        ),
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-abcdef0123456789"
        ),
    ],
)

rule = aws.route53.ResolverRule(
    "corporate-dns",
    domain_name="corp.example.com",
    name="corporate-dns",
    rule_type="FORWARD",
    resolver_endpoint_id=outbound.id,
    target_ips=[
        aws.route53.ResolverRuleTargetIpArgs(
            ip="192.168.10.10",
            port=53,
        ),
        aws.route53.ResolverRuleTargetIpArgs(
            ip="192.168.10.11",
            port=53,
        ),
    ],
)

association = aws.route53.ResolverRuleAssociation(
    "corporate-dns-production",
    resolver_rule_id=rule.id,
    vpc_id="vpc-0123456789abcdef0",
)
```

This example assumes that the VPC, subnets, and security group already exist.

The target DNS servers must also be reachable through your network connection.

The relevant Pulumi resources are `ResolverEndpoint`, `ResolverRule`, and `ResolverRuleAssociation`. Pulumi Registry +1

### 10\. Conditional DNS Forwarding

### 10.1 What Is Conditional Forwarding?

Conditional DNS forwarding means forwarding DNS queries to a specific DNS server based on the queried domain.

Instead of forwarding every DNS query to an external DNS server, you forward only queries belonging to specific namespaces.

For example:

```text
corp.example.com       -> Corporate DNS
partner.example.net    -> Partner DNS
internal.example.com   -> Route 53 private hosted zone
```

This is useful when different organizations or networks manage different DNS namespaces.

### 10.2 Example Architecture

Imagine a company with three DNS environments:

![How to achieve DNS high availability with Route 53 Resolver endpoints | Networking & Content Delivery](https://images.openai.com/static-rsc-4/U7ML0WAClDNsrM1G_a7a1Ylacq4jr1PlUZfQmvcgbKU9eqoCE8xoaDjK2L7KK0op3FZaa5IXqYLx1k8M724LptOc20TH98nrJzrTjnwlc4tSy21oAvEje0AzHN6gOQ215zTDqds5E-JhK09la8HJXJMJhYHWuyXtlfmel90fzRaIieW8YJZv4b8iyJD_I9zg?purpose=fullsize)

| DNS namespace        | Authoritative DNS            |
| -------------------- | ---------------------------- |
| internal.example.com | Route 53 private hosted zone |
| corp.example.com     | Corporate DNS                |
| partner.example.net  | Partner DNS                  |

An EC2 instance sends queries to the VPC Resolver.

Depending on the domain, the Resolver chooses the appropriate destination.

For example:

```bash
dig api.internal.example.com
```

Resolved through Route 53 private hosted zones.

```bash
dig git.corp.example.com
```

Forwarded to corporate DNS.

```bash
dig service.partner.example.net
```

Forwarded to partner DNS.

### 10.3 Why Conditional Forwarding Matters

Without conditional forwarding, you might need to configure custom DNS servers across every VPC or manually maintain DNS records.

Conditional forwarding provides:

* Centralized DNS management.

* Separation of DNS responsibilities.

* Integration with existing corporate DNS infrastructure.

* Consistent resolution across multiple VPCs.

* Reduced DNS configuration duplication.

### 10.4 Forwarding Rules and Private Hosted Zones

An important detail: private hosted zones and Resolver forwarding rules are separate DNS mechanisms.

For a given name, the matching DNS namespace and applicable Resolver rules determine how the query is resolved.

Do not assume that configuring a forwarding rule automatically overrides a matching private hosted zone. Test overlapping namespaces carefully, particularly when implementing split-horizon DNS.

### 11\. DNS Resolution Between Multiple VPCs

In a multi-VPC AWS architecture, DNS resolution and network connectivity are two different problems.

Let's explore how to solve both.

### 11.1 Scenario: Three VPCs

Suppose you have:

```text
Production VPC:
10.10.0.0/16

Development VPC:
10.20.0.0/16

Shared Services VPC:
10.30.0.0/16
```

Your Shared Services VPC contains:

* Internal DNS services.

* Monitoring systems.

* Shared APIs.

* Centralized infrastructure services.

You create a private hosted zone:

```text
internal.example.com
```

And configure:

```dns
monitoring.internal.example.com   A   10.30.1.10
logging.internal.example.com      A   10.30.2.10
api.internal.example.com          A   10.30.3.10
```

You want all three VPCs to resolve these names.

### 11.2 Approach 1: Associate the Private Hosted Zone with Multiple VPCs

The simplest solution is to associate the same private hosted zone with all three VPCs.

![Scaling DNS management across multiple accounts and VPCs - Hybrid Cloud DNS Options for Amazon VPC](https://images.openai.com/static-rsc-4/4j2MWFmxhykFNaNhMb3TCB_f0XJ21Gi1GdL3FuUBTH2j6sgC6EOEmZUt-NcyKJklvN9LoUq6R6acuLKpv1uIIkavWrkmaWL9hg_xn3_dmMGaIOiqz5dbitFz3aMr4JYS4lIH3o_4k5iENghtCe5WcDs_9LwSb8MvvK9OJBkZc5xBZCV8DFjHtxne4kOEiy8D?purpose=fullsize)

The process:

* Create the private hosted zone.

* Associate Production VPC.

* Associate Development VPC.

* Associate Shared Services VPC.

* Configure the DNS records.

All three VPCs can now resolve the private records.

However, remember that VPC association doesn't create network connectivity.

You still need an appropriate networking architecture, such as VPC peering or Transit Gateway, and corresponding security-group and route-table configuration.

### 11.3 Approach 2: Centralized DNS Using Resolver Endpoints

Another approach is to centralize DNS resolution in a Shared Services VPC.

For example:

```text
Production VPC
      |
      |
Development VPC ---- Transit Gateway
      |                    |
      |              Shared Services VPC
      |                    |
      +------------- Resolver inbound endpoint
                           |
                     Private Hosted Zone
```

The other VPCs forward DNS queries to the inbound endpoint.

This approach is particularly useful when you want centralized DNS infrastructure and centralized management of DNS forwarding.

However, there is an important architectural detail:

A private hosted zone associated with the Shared Services VPC can be resolved through an inbound endpoint in that VPC. You must configure the forwarding path from the other VPCs, including routing and security.

### 11.4 Approach 3: AWS RAM and Shared Resolver Rules

For organizations using multiple AWS accounts, AWS Resource Access Manager (RAM) allows you to share Resolver rules.

For example:

```text
AWS Organization
│
├── Network Account
│   ├── Outbound Resolver Endpoint
│   └── Corporate DNS Forwarding Rules
│
├── Production Account
│   └── Production VPC
│
├── Development Account
│   └── Development VPC
│
└── Testing Account
    └── Testing VPC
```

The Network Account owns the DNS forwarding infrastructure.

The other accounts consume shared rules and associate them with their VPCs.

This provides centralized DNS governance.

### 11.5 Comparing the Approaches

| Approach                       | Best use case                   |
| ------------------------------ | ------------------------------- |
| Multiple VPC associations      | Simple shared private namespace |
| Centralized Resolver endpoints | Centralized DNS forwarding      |
| AWS RAM                        | Multi-account DNS management    |

You can combine these approaches depending on the architecture.

### 12\. Hybrid DNS Integration with On-Premises Environments

Now let's combine the concepts we've learned.

Hybrid DNS is one of the most important Route 53 use cases in enterprise environments.

Organizations often have existing DNS infrastructure that cannot simply be replaced when they migrate workloads to AWS.

They need DNS resolution in both directions.

### 12.1 Hybrid Network Architecture

Imagine the following environment:

![How to achieve DNS high availability with Route 53 Resolver endpoints | Networking & Content Delivery](https://images.openai.com/static-rsc-4/LU88nLPHxmQSOFVrTri6xvYIZLb1Gl0ePoyTezZ4U52zlFlfJb54XsHSkYD4VM5bRnKprKuzoxa-Y-V-Anjg1OOmoiEzzOY8GS8tipd5z3_JScaS44aRaoPmku3bwW-U-kwymPo-aj7fyPSjQR95mCvhuSEWeYhUkhtYp8fxrMtxM3PRlJkyuVObv8wOrxFD?purpose=fullsize)

```text
                ON-PREMISES
             192.168.0.0/16
                     |
              Corporate DNS
              192.168.10.10
                     |
              Site-to-Site VPN
                     |
                AWS VPC
               10.10.0.0/16
                     |
              Route 53 Resolver
                /          \
           Inbound        Outbound
           Endpoint       Endpoint
               |              |
        Private Hosted    Corporate DNS
             Zone          Forwarding
```

The network connection can be established using:

* AWS Site-to-Site VPN.

* AWS Direct Connect.

* Another private network connection with appropriate routing.

The DNS endpoints themselves do not establish network connectivity.

They depend on the network connection already being available.

### 12.2 AWS-to-On-Premises DNS Resolution

Suppose your on-premises DNS server contains:

```dns
git.corp.example.com      A   192.168.10.20
ldap.corp.example.com     A   192.168.10.30
files.corp.example.com    A   192.168.10.40
```

An EC2 instance wants to resolve:

```text
git.corp.example.com
```

You configure:

```text
Resolver outbound endpoint
       |
Forwarding rule
       |
corp.example.com
       |
192.168.10.10
```

The EC2 instance can now resolve corporate hostnames.

### 12.3 On-Premises-to-AWS DNS Resolution

Now reverse the direction.

Your private hosted zone contains:

```dns
api.internal.example.com      A   10.10.2.10
db.internal.example.com       A   10.10.3.10
monitor.internal.example.com  A   10.10.4.10
```

Your on-premises DNS server needs to resolve these names.

Configure conditional forwarding on the corporate DNS server:

```text
internal.example.com
       |
       v
Route 53 Inbound Endpoint
       |
       v
VPC Resolver
       |
       v
Private Hosted Zone
```

The corporate DNS server forwards matching queries to the inbound endpoint IP addresses.

Now both environments can resolve each other's private DNS names.

### 12.4 Complete DNS Resolution Example

| Query                    | Direction         | Mechanism         |
| ------------------------ | ----------------- | ----------------- |
| git.corp.example.com     | AWS → On-premises | Outbound endpoint |
| ldap.corp.example.com    | AWS → On-premises | Outbound endpoint |
| api.internal.example.com | On-premises → AWS | Inbound endpoint  |
| db.internal.example.com  | On-premises → AWS | Inbound endpoint  |

This is the foundation of hybrid DNS.

### 12.5 Why Not Use Public DNS?

You could technically publish some records publicly, but that is usually inappropriate for internal infrastructure.

Private DNS allows you to:

* Keep internal hostnames out of public DNS.

* Avoid exposing private infrastructure records.

* Preserve existing corporate namespaces.

* Use consistent service discovery across hybrid environments.

* Maintain control over internal DNS policies.

### 13\. Simulating an On-Premises DNS Server with Linux

For our labs, we don't need a physical on-premises environment.

We can simulate one using a Linux server running BIND9.

BIND9 is a widely used DNS server that supports authoritative DNS zones, recursive resolution, and forwarding.

### 13.1 Example Lab Architecture

```text
AWS VPC: 10.10.0.0/16
    |
    |-- EC2 Application Server
    |
    |-- Route 53 Inbound Endpoint
    |
    |-- Route 53 Outbound Endpoint
    |
    |-- Private Hosted Zone
    |
    +---- VPN / Private Connectivity ----+
                                         |
                                  Linux DNS Server
                                    192.168.10.10
                                         |
                                    BIND9 Server
```

For a fully connected lab, you can use a second VPC to represent the on-premises network, connected to the AWS VPC through VPN or an appropriate private routing arrangement.

If you're only testing BIND9 locally on your laptop, you can validate DNS zone behavior and forwarding configuration, but that alone doesn't establish hybrid connectivity.

### 13.2 Install BIND9

On Ubuntu:

```bash
sudo apt update

sudo apt install -y bind9 bind9-utils dnsutils
```

Check the service:

```bash
sudo systemctl status named
```

Depending on the Linux distribution, the service may be called `bind9` instead of `named`.

### 13.3 Create a Corporate DNS Zone

Edit:

```bash
sudo nano /etc/bind/named.conf.local
```

Add:

```bind
zone "corp.example.com" {
    type master;
    file "/etc/bind/db.corp.example.com";
};
```

Create the zone file:

```bash
sudo nano /etc/bind/db.corp.example.com
```

Add:

```dns
$TTL 300

@ IN SOA ns1.corp.example.com. admin.corp.example.com. (
    2026103101
    3600
    900
    604800
    300
)

@       IN NS ns1.corp.example.com.

ns1     IN A 192.168.10.10
git     IN A 192.168.10.20
ldap    IN A 192.168.10.30
files   IN A 192.168.10.40
```

Validate the configuration:

```bash
sudo named-checkconf

sudo named-checkzone \
    corp.example.com \
    /etc/bind/db.corp.example.com
```

Restart BIND9:

```bash
sudo systemctl restart bind9
```

### 13.4 Test DNS Resolution

Run:

```bash
dig @192.168.10.10 git.corp.example.com
```

Expected answer:

```text
git.corp.example.com. 300 IN A 192.168.10.20
```

You now have a working simulated corporate DNS zone.

### 13.5 Configure Conditional Forwarding

To forward AWS private DNS queries to Route 53, configure a conditional forwarder in BIND9.

For example:

```bind
zone "internal.example.com" {
    type forward;
    forward only;
    forwarders {
        10.10.1.100;
        10.10.2.100;
    };
};
```

Here:

* `10.10.1.100` is an inbound Resolver endpoint IP.

* `10.10.2.100` is the second inbound Resolver endpoint IP.

Validate:

```bash
sudo named-checkconf
sudo systemctl reload bind9
```

Now queries for `internal.example.com` are forwarded to Route 53.

The BIND9 server must have network connectivity to the inbound endpoint IP addresses, and the endpoint security group must allow DNS queries from the BIND9 server.

### 13.6 Configure AWS-to-Corporate Forwarding

The opposite direction is configured in Route 53.

Create a forwarding rule:

```text
Domain:
corp.example.com

Target:
192.168.10.10

Endpoint:
Outbound Resolver Endpoint
```

Associate the rule with the VPC.

Now AWS workloads can resolve corporate DNS names.

This gives us bidirectional DNS resolution.

### 14\. DNS Forwarding Loops and Troubleshooting

DNS forwarding is powerful, but incorrect configurations can create DNS loops.

### 14.1 What Is a DNS Forwarding Loop?

A forwarding loop occurs when two DNS resolvers continually forward the same query to each other.

Consider:

```text
AWS Resolver
      |
      v
Corporate DNS
      |
      v
AWS Resolver
      |
      v
Corporate DNS
      |
      ...
```

Neither resolver provides an authoritative answer.

The query keeps circulating until it eventually times out or fails.

### 14.2 Example of an Incorrect Configuration

Suppose:

* AWS forwards `corp.example.com` to Corporate DNS.

* Corporate DNS forwards `corp.example.com` back to AWS.

* Neither side is authoritative for the requested record.

This creates a loop.

Another dangerous configuration involves associating a forwarding rule with the same VPC that hosts the inbound endpoint receiving the forwarded query.

AWS explicitly warns against this configuration because it can cause a loop between inbound and outbound endpoints. Amazon Route 53

### 14.3 How to Prevent DNS Loops

Follow these principles:

* Decide which DNS server is authoritative for each namespace.

* Avoid forwarding the same namespace back to its origin.

* Use specific conditional forwarding rules.

* Avoid circular forwarding between AWS and corporate DNS.

* Separate DNS responsibilities across namespaces.

* Document DNS forwarding paths.

* Test every forwarding path before production deployment.

### 14.4 DNS Troubleshooting Commands

These commands are particularly useful during the labs.

Inspect DNS resolution:

```bash
dig api.internal.example.com
```

Query a specific DNS server:

```bash
dig @10.10.1.100 api.internal.example.com
```

Trace DNS resolution:

```bash
dig +trace example.com
```

Note that `+trace` traces the public DNS delegation path. It is not a substitute for inspecting private hosted-zone resolution.

Check the authoritative answer:

```bash
dig api.internal.example.com +norecurse
```

Check TCP DNS:

```bash
dig +tcp @10.10.1.100 api.internal.example.com
```

Inspect DNS response details:

```bash
dig api.internal.example.com +stats
```

Capture DNS traffic:

```bash
sudo tcpdump -ni any port 53
```

### 14.5 Common Problems

| Problem                              | Possible cause                                   |
| ------------------------------------ | ------------------------------------------------ |
| NXDOMAIN                             | Missing record or incorrect private zone         |
| SERVFAIL                             | Resolver or upstream DNS failure                 |
| Timeout                              | Routing, security group, NACL, or firewall issue |
| Wrong IP returned                    | Overlapping namespaces or incorrect records      |
| Queries work in one VPC only         | Missing VPC association or rule association      |
| AWS cannot resolve corporate names   | Outbound endpoint or forwarding rule problem     |
| On-premises cannot resolve AWS names | Inbound endpoint or corporate forwarding problem |
| Intermittent resolution              | DNS server availability or network connectivity  |
| DNS loop                             | Circular forwarding configuration                |

### 14.6 Troubleshooting Checklist

When a DNS query fails, investigate in this order:

Step 1 — Verify the DNS record

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789EXAMPLE
```

Step 2 — Verify the hosted-zone VPC association

```bash
aws route53 get-hosted-zone \
  --id Z123456789EXAMPLE
```

Step 3 — Check VPC DNS attributes

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport
```

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

Step 4 — Verify Resolver endpoints

```bash
aws route53resolver list-resolver-endpoints
```

Step 5 — Verify forwarding rules

```bash
aws route53resolver list-resolver-rules
```

Step 6 — Check network connectivity

```bash
nc -zvu 192.168.10.10 53
```

Remember that UDP connectivity tests are not definitive proof of successful DNS resolution. Follow up with an actual `dig` query.

Step 7 — Inspect DNS traffic

```bash
sudo tcpdump -ni any 'port 53'
```

This helps determine whether queries are being sent, forwarded, and answered.

### 15\. Route 53 Resolver Security Considerations

DNS infrastructure is part of your network security boundary.

Incorrectly configured Resolver endpoints can expose internal DNS information or allow unauthorized DNS queries.

### 15.1 Security Groups

Resolver endpoints use security groups.

For inbound endpoints, allow DNS traffic from authorized external DNS servers.

Example:

```text
Inbound endpoint security group:

Inbound:
UDP 53 from 192.168.0.0/16
TCP 53 from 192.168.0.0/16
```

For outbound endpoints, allow DNS traffic to the designated corporate DNS servers.

Avoid broad rules such as:

```text
0.0.0.0/0
```

unless there is a specific, justified requirement.

### 15.2 Network ACLs and Routing

Security groups aren't the only controls.

Check:

* Subnet network ACLs.

* Route tables.

* Transit Gateway routes.

* VPN routes.

* Direct Connect routing.

* Corporate firewall rules.

DNS queries and responses must be able to travel in both directions.

### 15.3 DNS Firewall

Route 53 Resolver DNS Firewall provides DNS-level filtering for outbound queries from VPCs.

You can create rules to:

* Block malicious domains.

* Allow approved domains.

* Monitor suspicious DNS queries.

* Enforce domain-based policies.

For example, a company may allow:

```text
*.amazonaws.com
*.internal.example.com
```

while blocking known malicious domains.

DNS Firewall is a complementary security control; it doesn't replace security groups, routing, or application-level security.

### 15.4 Resolver Query Logging

Resolver query logging allows you to monitor DNS queries originating from VPCs.

You can send logs to:

* CloudWatch Logs.

* Amazon S3.

* Amazon Kinesis Data Firehose.

Useful information includes:

* Queried domain.

* Query type.

* Source IP address.

* Response code.

* DNS response information.

This helps identify suspicious queries, troubleshooting issues, and unexpected DNS traffic.

### 15.5 Least Privilege IAM

DNS infrastructure should also follow IAM least-privilege principles.

Separate permissions for:

* Creating hosted zones.

* Modifying DNS records.

* Creating Resolver endpoints.

* Managing forwarding rules.

* Associating VPCs.

* Managing DNS logging.

Avoid giving application deployment roles unrestricted Route 53 administration permissions.

### 16\. Hands-on Labs

We'll now put the concepts together using Pulumi, AWS CLI, Bash, and a Linux DNS server.

The labs are designed to build progressively toward a working hybrid DNS architecture.

### Lab 1 — Create Private Hosted Zones Using Pulumi

Objective: Create a VPC and a private hosted zone, then configure internal DNS records.

### Step 1. Create a Pulumi project

```bash
mkdir route53-private-dns
cd route53-private-dns

pulumi new aws-python
```

Install dependencies if necessary:

```bash
uv add pulumi pulumi-aws
```

### Step 2. Create the VPC

In `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

vpc = aws.ec2.Vpc(
    "private-dns-vpc",
    cidr_block="10.10.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={
        "Name": "private-dns-vpc",
    },
)
```

### Step 3. Create a private hosted zone

```python
zone = aws.route53.Zone(
    "internal-zone",
    name="internal.example.com",
    vpcs=[
        aws.route53.ZoneVpcArgs(
            vpc_id=vpc.id,
        )
    ],
    comment="Internal application DNS",
)
```

### Step 4. Create DNS records

```python
api = aws.route53.Record(
    "api-record",
    zone_id=zone.zone_id,
    name="api.internal.example.com",
    type="A",
    ttl=300,
    records=["10.10.2.10"],
)

database = aws.route53.Record(
    "database-record",
    zone_id=zone.zone_id,
    name="db.internal.example.com",
    type="A",
    ttl=300,
    records=["10.10.3.10"],
)

pulumi.export("vpc_id", vpc.id)
pulumi.export("zone_id", zone.zone_id)
```

### Step 5. Deploy

```bash
pulumi config set aws:region ap-southeast-1

pulumi preview
pulumi up
```

### Step 6. Verify

Launch or use an EC2 instance inside the VPC and execute:

```bash
dig api.internal.example.com
```

```bash
dig db.internal.example.com
```

Expected results:

```text
api.internal.example.com -> 10.10.2.10
db.internal.example.com  -> 10.10.3.10
```

Remember that these are DNS records only. The example IP addresses do not automatically represent running services.

### Lab 2 — Associate Private Hosted Zones with Multiple VPCs

Objective: Allow multiple VPCs to resolve the same internal DNS namespace.

Create two additional VPCs:

```python
dev_vpc = aws.ec2.Vpc(
    "development-vpc",
    cidr_block="10.20.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
)

shared_vpc = aws.ec2.Vpc(
    "shared-vpc",
    cidr_block="10.30.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
)
```

Associate them with the existing private zone:

```python
dev_association = aws.route53.ZoneAssociation(
    "development-zone-association",
    zone_id=zone.zone_id,
    vpc_id=dev_vpc.id,
)

shared_association = aws.route53.ZoneAssociation(
    "shared-zone-association",
    zone_id=zone.zone_id,
    vpc_id=shared_vpc.id,
)
```

The Pulumi provider supports managing these additional associations through `ZoneAssociation`. Avoid managing the same associations simultaneously through both inline VPC configuration and standalone association resources. Pulumi Registry +1

Deploy:

```bash
pulumi preview
pulumi up
```

Expected architecture:

![Set up DNS resolution for hybrid networks in a multi-account AWS environment - AWS Prescriptive Guidance](https://images.openai.com/static-rsc-4/Zwwo4hAn1kyqHaax4NO2Nf4dGSnFl6r7iZ203sPK2DpmR48QD47jIrCcJ2UpV6OP4Wxx6ihzUXCrwnKKvnt7kie7Dyjne3pUjflgG7GssknMKfJJx5keJFCwOdVGmBiZ83Yiwf3oTXQaX0H5dr73GzKb43I2PIrpGoocFCcjMDbku697h4y2VTmGzKbOgjIE?purpose=fullsize)

Verify that instances in each associated VPC can resolve:

```bash
dig api.internal.example.com
```

Note: This lab demonstrates DNS sharing. To actually communicate with services across VPCs, configure VPC peering or Transit Gateway separately.

### Lab 3 — Configure Internal Service DNS Records

Objective: Build a practical internal service discovery namespace.

Create records for:

```text
api.internal.example.com
db.internal.example.com
redis.internal.example.com
monitoring.internal.example.com
```

You can organize the namespace using subdomains:

```text
internal.example.com
│
├── api.internal.example.com
├── db.internal.example.com
├── redis.internal.example.com
│
├── monitoring.internal.example.com
│
└── dev.internal.example.com
```

Use Pulumi to manage records as infrastructure resources.

For example:

```python
services = {
    "api": "10.10.2.10",
    "db": "10.10.3.10",
    "redis": "10.10.4.10",
    "monitoring": "10.10.5.10",
}

for service, address in services.items():
    aws.route53.Record(
        f"{service}-record",
        zone_id=zone.zone_id,
        name=f"{service}.internal.example.com",
        type="A",
        ttl=300,
        records=[address],
    )
```

Test:

```bash
for service in api db redis monitoring; do
    dig +short "${service}.internal.example.com"
done
```

This pattern is useful when managing many internal services.

### Lab 4 — Build Resolver Inbound and Outbound Endpoints

Objective: Create endpoints that allow DNS traffic to travel between AWS and an external network.

First, create two subnets in different Availability Zones and a security group that allows DNS traffic from your authorized network.

Example:

```python
resolver_sg = aws.ec2.SecurityGroup(
    "resolver-security-group",
    vpc_id=vpc.id,
    description="DNS access for Route 53 Resolver",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="udp",
            from_port=53,
            to_port=53,
            cidr_blocks=["192.168.0.0/16"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=53,
            to_port=53,
            cidr_blocks=["192.168.0.0/16"],
        ),
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
```

For a production configuration, restrict outbound rules to approved DNS destinations and other required traffic.

Create the inbound endpoint:

```python
inbound = aws.route53.ResolverEndpoint(
    "inbound-endpoint",
    name="corporate-inbound",
    direction="INBOUND",
    security_group_ids=[resolver_sg.id],
    ip_addresses=[
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-aaaaaaaa",
        ),
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-bbbbbbbb",
        ),
    ],
)
```

Create the outbound endpoint:

```python
outbound = aws.route53.ResolverEndpoint(
    "outbound-endpoint",
    name="corporate-outbound",
    direction="OUTBOUND",
    security_group_ids=[resolver_sg.id],
    ip_addresses=[
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-aaaaaaaa",
        ),
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-bbbbbbbb",
        ),
    ],
)
```

The subnet IDs are placeholders: replace them with actual subnets in different Availability Zones.

Also, configure the VPC routing and security rules needed for the external DNS servers.

Export the endpoint IDs:

```python
pulumi.export("inbound_endpoint_id", inbound.id)
pulumi.export("outbound_endpoint_id", outbound.id)
```

Deploy:

```bash
pulumi preview
pulumi up
```

Inspect:

```bash
aws route53resolver list-resolver-endpoints
```

### Lab 5 — Configure Conditional Forwarding Rules

Objective: Forward AWS DNS queries for corporate namespaces to external DNS servers.

Assume:

```text
Corporate DNS 1: 192.168.10.10
Corporate DNS 2: 192.168.10.11

DNS namespace: corp.example.com
```

Create the forwarding rule:

```python
corporate_rule = aws.route53.ResolverRule(
    "corporate-forwarding-rule",
    name="corporate-forwarding",
    domain_name="corp.example.com",
    rule_type="FORWARD",
    resolver_endpoint_id=outbound.id,
    target_ips=[
        aws.route53.ResolverRuleTargetIpArgs(
            ip="192.168.10.10",
            port=53,
        ),
        aws.route53.ResolverRuleTargetIpArgs(
            ip="192.168.10.11",
            port=53,
        ),
    ],
)
```

Associate it with the VPC:

```python
rule_association = aws.route53.ResolverRuleAssociation(
    "corporate-rule-association",
    resolver_rule_id=corporate_rule.id,
    vpc_id=vpc.id,
)
```

Deploy:

```bash
pulumi preview
pulumi up
```

Test from an EC2 instance:

```bash
dig git.corp.example.com
```

Expected result:

```text
git.corp.example.com -> 192.168.10.20
```

The external DNS servers must be reachable from the outbound endpoint.

### Lab 6 — Simulate an On-Premises DNS Environment

Objective: Deploy a Linux DNS server running BIND9 to represent an existing corporate DNS infrastructure.

Use a Linux VM or EC2 instance in a separate network.

Install BIND9:

```bash
sudo apt update

sudo apt install -y bind9 bind9-utils dnsutils
```

Configure:

```text
corp.example.com
```

Create records:

```dns
git.corp.example.com       A   192.168.10.20
ldap.corp.example.com      A   192.168.10.30
files.corp.example.com     A   192.168.10.40
```

Validate:

```bash
sudo named-checkconf

sudo named-checkzone \
  corp.example.com \
  /etc/bind/db.corp.example.com
```

Test:

```bash
dig @192.168.10.10 git.corp.example.com
```

Then configure the networking between the simulated corporate environment and AWS.

For a complete hybrid lab, use a Site-to-Site VPN or another routed private connection.

### Lab 7 — Implement Hybrid DNS Resolution

Objective: Enable DNS resolution in both directions.

Your final environment should contain:

![什麼是 Route 53 VPC Resolver？ - Amazon Route 53](https://images.openai.com/static-rsc-4/2-FlvArgdyWRmnDO7y1DNa8Pdk_1vGl20L6X6uj3SVy37Ff-cbvamkUYtchExUlmX5IJEZjEUawuk_eSRGuzjXsE_HpvsjcW5A-PbEJkbMQjJeHA_iPUZ130lVtQcvX9M6ucTQTTX4anHLWJXtzZPr7pBbuPrk_yYxBC0ImVdUK01W_oLHcHyclQbrAXtS-R?purpose=fullsize)

AWS → On-premises

Configure:

```text
corp.example.com
       |
       v
Outbound Resolver Endpoint
       |
       v
Corporate DNS: 192.168.10.10
```

Test:

```bash
dig git.corp.example.com
```

On-premises → AWS

Configure BIND9 conditional forwarding:

```bind
zone "internal.example.com" {
    type forward;
    forward only;
    forwarders {
        10.10.1.100;
        10.10.2.100;
    };
};
```

Test:

```bash
dig @192.168.10.10 api.internal.example.com
```

Expected result:

```text
api.internal.example.com -> 10.10.2.10
```

At this point, your simulated corporate network and AWS environment can resolve each other's private DNS namespaces.

### Lab 8 — Troubleshoot DNS Forwarding and Resolution Failures

Objective: Understand and diagnose real-world DNS problems.

Introduce several intentional configuration errors:

| Scenario | Configuration error                        |
| -------- | ------------------------------------------ |
| 1        | Remove a DNS record                        |
| 2        | Disable VPC DNS support                    |
| 3        | Remove a private hosted zone association   |
| 4        | Remove a Resolver rule association         |
| 5        | Block UDP port 53                          |
| 6        | Block TCP port 53                          |
| 7        | Configure an unreachable forwarding target |
| 8        | Create a circular forwarding configuration |

Use:

```bash
dig api.internal.example.com
```

```bash
dig @10.10.1.100 api.internal.example.com
```

```bash
dig +tcp @10.10.1.100 api.internal.example.com
```

```bash
sudo tcpdump -ni any port 53
```

Inspect AWS resources:

```bash
aws route53resolver list-resolver-endpoints

aws route53resolver list-resolver-rules

aws route53resolver list-resolver-rule-associations

aws route53 list-hosted-zones
```

Your goal is to identify where each query fails:

* Client-side DNS configuration.

* VPC DNS resolution.

* Hosted-zone configuration.

* Resolver endpoint.

* Forwarding rule.

* Network connectivity.

* External DNS server.

### 17\. Module 5 — Final Architecture

By completing these labs, you'll have developed the following architecture:

![Hybrid DNS resolution using Route 53 Endpoints |
    tecRacer Amazon AWS Blog](https://images.openai.com/static-rsc-4/OIVs7F1qVg4EkooEIO1Lwspp4UTYIfhVLSE8-KDLfr96gu4t9zy14iXkH_mwbWtnW4pH1_rjyME1NsqWPVckNbDjewgCTy0aXROOGm_7DjX7EOh1LOtxDQQohGaHHyPJAC2s3t5dWuwyZVgDgjZTg1k2yCftWc26qVCgasZpzsK-PxhOf3u2ixSlvhZj2SWI?purpose=fullsize)

The architecture includes:

| Component            | Responsibility                  |
| -------------------- | ------------------------------- |
| Private hosted zone  | Internal DNS namespace          |
| VPC associations     | DNS visibility across VPCs      |
| Inbound endpoint     | On-premises-to-AWS DNS          |
| Outbound endpoint    | AWS-to-on-premises DNS          |
| Forwarding rules     | Conditional DNS forwarding      |
| BIND9                | Simulated corporate DNS         |
| VPN / Direct Connect | Network connectivity            |
| Security groups      | DNS traffic access control      |
| Pulumi               | Infrastructure automation       |
| Bash + dig           | DNS testing and troubleshooting |

### 18\. Important Takeaways

You should understand these distinctions particularly well:

* Private hosted zones provide private authoritative DNS records to associated VPCs.

* VPC associations provide DNS visibility, not network connectivity.

* Inbound endpoints allow external DNS servers to query AWS private DNS.

* Outbound endpoints allow AWS DNS queries to reach external DNS servers.

* Forwarding rules determine which domains should be forwarded and where.

* Conditional forwarding allows multiple DNS namespaces to use different authoritative DNS servers.

* Hybrid DNS combines AWS DNS with existing corporate DNS infrastructure.

* DNS forwarding loops must be prevented through careful namespace and forwarding design.

* Security groups, routing, and DNS logging are essential operational considerations.

### 19\. Official Documentation

For further technical reference:

* [Route 53 Private Hosted Zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html?utm_source=chatgpt.com)

* [Route 53 Resolver](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html?utm_source=chatgpt.com)

* [Resolving DNS queries between VPCs and your network](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-overview-DSN-queries-to-vpc.html?utm_source=chatgpt.com)

* [Resolver endpoint considerations](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-choose-vpc.html?utm_source=chatgpt.com)

* [Resolver endpoint best practices](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/best-practices-resolver-endpoints.html?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 resources](https://www.pulumi.com/registry/packages/aws/api-docs/route53/?utm_source=chatgpt.com)

Next module: Module 6 — Route 53 Resolver DNS Firewall and DNS Security.
