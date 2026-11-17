### Module 5 — Private Hosted Zones and Hybrid DNS with Route 53 Resolver

### 1\. Private Hosted Zone Architecture

Amazon Route 53 Private Hosted Zones allow you to manage DNS namespaces that are accessible only from associated Amazon VPCs.

Unlike public hosted zones, private hosted zones are not intended to be resolved through the public DNS infrastructure. They provide DNS resolution for internal applications, services, databases, and infrastructure.

### 1.1 Understanding Private Hosted Zones

* What is a private hosted zone?

* Differences between public and private hosted zones.

* Private DNS namespaces and internal domain names.

* Authoritative DNS resolution inside a VPC.

* Private hosted zone visibility and accessibility.

* How Route 53 Resolver handles queries for private hosted zones.

* DNS record types supported in private hosted zones.

* Internal service discovery using DNS records.

* Private hosted zone naming strategies:

    * `internal.example.com`

    * `services.example.com`

    * `corp.example.com`

    * `dev.internal.example.com`

### 1.2 Private Hosted Zone Resolution Architecture

* DNS resolution flow inside a VPC.

* Amazon-provided DNS server and Route 53 Resolver.

* VPC-local DNS resolution.

* Resolving private hosted zone records from EC2 instances.

* Private hosted zone association requirements.

* DNS resolution behavior when a hosted zone is not associated with a VPC.

* DNS resolution conflicts and overlapping namespaces.

### 1.3 VPC DNS Configuration

* `enableDnsSupport` and its role in DNS resolution.

* `enableDnsHostnames` and its relationship with DNS hostnames.

* Amazon-provided DNS server addresses.

* DHCP option sets and DNS configuration.

* Custom DNS servers versus Amazon-provided DNS.

* DNS resolution behavior across VPC subnets.

* DNS configuration requirements for private hosted zones.

### 1.4 Split-Horizon DNS

* Split-horizon DNS architecture.

* Public and private DNS namespaces using the same domain.

* Internal and external DNS responses.

* Public hosted zone and private hosted zone coexistence.

* Different record values for internal and external clients.

* Common split-horizon DNS use cases.

* DNS namespace design for multi-environment architectures.

### 2\. VPC Association and Private DNS Management

### 2.1 Associating VPCs with Private Hosted Zones

* Associating a private hosted zone with a VPC.

* Creating a private hosted zone with an initial VPC association.

* Associating additional VPCs with an existing hosted zone.

* Cross-account VPC association architecture.

* Authorizing VPC associations across AWS accounts.

* Accepting cross-account VPC association authorizations.

* Disassociating VPCs from private hosted zones.

* VPC association limitations and considerations.

### 2.2 DNS Resolution Across Multiple VPCs

* Private hosted zone resolution across associated VPCs.

* Internal DNS communication between VPCs.

* DNS resolution versus network connectivity.

* VPC peering and private DNS resolution.

* Transit Gateway and multi-VPC DNS architectures.

* Shared services VPC patterns.

* Centralized private DNS architecture.

* Overlapping private DNS namespaces.

* Private hosted zone association management at scale.

### 2.3 Internal Service Discovery

* DNS-based service discovery.

* Mapping internal applications to private DNS records.

* Internal load balancers and Alias records.

* DNS naming conventions for microservices.

* Environment-specific DNS namespaces.

* Service discovery across multiple AWS accounts.

* DNS-based application configuration.

### 3\. Route 53 Resolver Architecture

Amazon Route 53 Resolver is the DNS resolution service provided by AWS. It handles DNS queries originating from resources within VPCs and enables DNS communication between AWS environments and external networks.

### 3.1 Understanding Route 53 Resolver

* Route 53 Resolver architecture and components.

* Inbound and outbound DNS resolution.

* Resolver endpoints and network interfaces.

* Resolver endpoint IP addresses.

* DNS query processing and forwarding.

* Resolver availability and multi-AZ architecture.

* Resolver endpoints versus VPC-provided DNS resolution.

* DNS query paths in hybrid architectures.

### 3.2 Resolver Inbound Endpoints

* Purpose and architecture of inbound endpoints.

* Allowing on-premises networks to resolve AWS private DNS records.

* Inbound endpoint IP addresses.

* Creating inbound endpoints across multiple Availability Zones.

* Subnet and security group requirements.

* DNS queries sent from external DNS servers to inbound endpoints.

* TCP and UDP port 53 requirements.

* Inbound endpoint availability and scaling considerations.

### 3.3 Resolver Outbound Endpoints

* Purpose and architecture of outbound endpoints.

* Forwarding DNS queries from AWS to external DNS servers.

* Outbound endpoint network interfaces.

* Availability Zone placement.

* Security group and routing requirements.

* TCP and UDP port 53.

* Outbound endpoint availability and scaling.

* Resolver endpoint connectivity troubleshooting.

### 3.4 Resolver Endpoints and Network Architecture

* Endpoint subnet selection.

* Resolver endpoint IP address allocation.

* Security group configuration.

* VPC route table requirements.

* Network ACL considerations.

* Routing through VPN and Direct Connect.

* Endpoint redundancy and failure considerations.

* Resolver endpoint pricing and operational costs.

### 4\. Resolver Forwarding Rules and Conditional DNS Forwarding

Resolver forwarding rules determine how DNS queries are forwarded from a VPC to external DNS servers.

They are essential when applications in AWS need to resolve DNS names managed by on-premises DNS infrastructure or other DNS environments.

### 4.1 Resolver Forwarding Rules

* What are Route 53 Resolver forwarding rules?

* Forwarding rule architecture and components.

* Rule types:

    * Forward.

    * System.

    * Recursive.

* Domain-based forwarding rules.

* Configuring forwarding destinations.

* Forwarding rules and target DNS server IP addresses.

* Rule associations with VPCs.

* Reusing forwarding rules across multiple VPCs.

* Resolver rule sharing through AWS Resource Access Manager (AWS RAM).

* Cross-account Resolver rule management.

* Rule precedence and matching behavior.

* Forwarding rule limitations and considerations.

### 4.2 Conditional DNS Forwarding

* Conditional DNS forwarding fundamentals.

* Forwarding queries based on DNS suffixes.

* Forwarding specific namespaces to on-premises DNS servers.

* Configuring multiple forwarding destinations.

* Conditional forwarding for internal corporate domains.

* Forwarding AWS private DNS namespaces to appropriate DNS infrastructure.

* DNS forwarding between multiple VPCs.

* Managing overlapping DNS namespaces.

* Forwarding rule conflicts and precedence.

### 4.3 System and Recursive Resolution

* System rules and their behavior.

* Recursive DNS resolution through Route 53 Resolver.

* How Resolver processes matching forwarding rules.

* Forwarding rules versus normal recursive resolution.

* Overriding forwarding behavior for specific domains.

* Special considerations for private hosted zones and AWS-managed DNS namespaces.

### 4.4 Resolver Rule Sharing and Centralized DNS

* Sharing Resolver rules between AWS accounts.

* AWS RAM resource shares.

* Centralized DNS management.

* Shared services VPC architecture.

* DNS administration in AWS Organizations.

* Centralized forwarding rules for multiple application VPCs.

* Managing Resolver rules through Pulumi.

### 5\. Hybrid DNS Integration with On-Premises Environments

Hybrid DNS enables resources in AWS and on-premises networks to resolve each other's private DNS records.

A common architecture uses inbound and outbound Resolver endpoints together with conditional forwarding rules.

### 5.1 Hybrid DNS Architecture

* Hybrid DNS fundamentals.

* AWS-to-on-premises DNS resolution.

* On-premises-to-AWS DNS resolution.

* DNS forwarding across network boundaries.

* DNS resolution over Site-to-Site VPN.

* DNS resolution over AWS Direct Connect.

* Hybrid DNS architecture using a shared services VPC.

* Redundant DNS infrastructure.

* Hybrid DNS availability and disaster recovery.

### 5.2 AWS-to-On-Premises DNS Resolution

* Outbound Resolver endpoint architecture.

* Forwarding AWS DNS queries to on-premises DNS servers.

* Creating forwarding rules for corporate DNS namespaces.

* Configuring on-premises DNS server destinations.

* Routing DNS traffic through VPN or Direct Connect.

* Security group and firewall requirements.

* DNS query and response paths.

* Troubleshooting outbound DNS forwarding.

### 5.3 On-Premises-to-AWS DNS Resolution

* Inbound Resolver endpoint architecture.

* Configuring on-premises DNS servers to forward AWS domain queries.

* Forwarding AWS private hosted zone queries.

* Configuring conditional forwarding on Linux DNS servers.

* Forwarding internal AWS namespaces to inbound endpoint IP addresses.

* DNS query and response paths.

* Redundant inbound endpoints.

* Troubleshooting inbound DNS resolution.

### 5.4 Hybrid DNS Namespace Design

* Designing DNS namespaces across AWS and on-premises environments.

* Corporate domain integration.

* Split-horizon DNS in hybrid environments.

* Managing overlapping DNS namespaces.

* DNS delegation versus conditional forwarding.

* Centralized versus distributed DNS architectures.

* DNS forwarding hierarchy.

* Avoiding circular DNS dependencies.

### 6\. DNS Forwarding Loops, Security, and Troubleshooting

### 6.1 DNS Forwarding Loops

* Understanding DNS forwarding loops.

* Common causes of forwarding loops.

* Circular forwarding between AWS and on-premises DNS.

* Overlapping forwarding rules.

* Resolver rules that conflict with private hosted zones.

* DNS delegation mistakes.

* Detecting recursive query loops.

* DNS timeout and retry behavior.

* Designing loop-free DNS forwarding architectures.

### 6.2 Route 53 Resolver Security

* Resolver endpoint security architecture.

* Security groups for inbound endpoints.

* Security groups for outbound endpoints.

* Restricting DNS traffic to authorized networks.

* TCP and UDP port 53 security requirements.

* Network ACL considerations.

* Private network connectivity and DNS exposure.

* Securing on-premises DNS forwarding.

* Resolver query logging and sensitive DNS information.

* Cross-account Resolver rule permissions.

* Least-privilege IAM policies for DNS administration.

### 6.3 DNS Troubleshooting

* Troubleshooting private hosted zone resolution.

* Debugging VPC DNS attributes.

* Troubleshooting missing VPC associations.

* Debugging Resolver inbound endpoints.

* Debugging Resolver outbound endpoints.

* Troubleshooting forwarding rule associations.

* Diagnosing security group and routing problems.

* Analyzing DNS response codes:

    * `NOERROR`

    * `NXDOMAIN`

    * `SERVFAIL`

    * `REFUSED`

* Diagnosing DNS timeouts and unexpected responses.

* Troubleshooting UDP-to-TCP DNS fallback.

* Using `dig`, `nslookup`, `host`, and `tcpdump`.

* Analyzing Resolver query logs.

* Identifying DNS forwarding and recursion problems.

### 7\. Hands-on Labs

The following labs progressively build a hybrid DNS environment. We will use Pulumi Python for AWS infrastructure and Bash for Linux configuration and DNS diagnostics.

### Lab 1 — Create Private Hosted Zones Using Pulumi

Objectives:

* Create a VPC with DNS support enabled.

* Create a private hosted zone.

* Associate the hosted zone with the VPC.

* Configure internal DNS records.

* Verify private DNS resolution from an EC2 instance.

Infrastructure:

![AWS Solutions Architect Professional Cheat Sheet ·](https://images.openai.com/static-rsc-4/xvR8bu43PsDrVZRWgV9Bvffu1IK6krup-5xnIJcVqijdy6xfProGXNNAiHVM5Ng4i6rz7ipRRtMLly2l-5Kd2PcFAl2-CnY5EEzgd8ckkAkGkwGMIgxvf3i4IJFbnbSXlvwaFyZGiWOV72M6tEEWCPrWC6Yp-xi55yLH5b0bF_XnfNTNv5c1WC7-trPPJhSn?purpose=fullsize)

Pulumi implementation:

```bash
mkdir route53-private-dns
cd route53-private-dns

pulumi new aws-python
```

Install dependencies if necessary:

```bash
uv add pulumi pulumi-aws
```

Example `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
vpc_id = config.require("vpcId")

zone = aws.route53.Zone(
    "internal-zone",
    name="internal.example.com",
    vpcs=[
        aws.route53.ZoneVpcArgs(
            vpc_id=vpc_id,
        )
    ],
)

api_record = aws.route53.Record(
    "api-record",
    zone_id=zone.zone_id,
    name="api.internal.example.com",
    type="A",
    ttl=30,
    records=["10.0.1.10"],
)

pulumi.export("private_zone_id", zone.zone_id)
pulumi.export("api_record", api_record.fqdn)
```

Configure and deploy:

```bash
pulumi config set vpcId vpc-xxxxxxxx
pulumi up
```

Verify DNS resolution from an EC2 instance in the associated VPC:

```bash
dig api.internal.example.com

nslookup api.internal.example.com
```

Expected result: The private DNS record resolves to `10.0.1.10` from the associated VPC, but it is not publicly resolvable through public DNS.

### Lab 2 — Associate Private Hosted Zones with Multiple VPCs

Objectives:

* Create two separate VPCs.

* Associate a private hosted zone with both VPCs.

* Configure DNS records for internal services.

* Verify resolution from both VPCs.

* Understand cross-account association requirements.

Architecture:

![Route 53 Resolver endpoints and forwarding rules - Hybrid Cloud DNS Options for Amazon VPC](https://images.openai.com/static-rsc-4/OG_5CpWFU6SUvFkiFPRlYhWiI2gopJWwW9v2WwjkuqmilmfQrH6xyFSJqKy7FmwYVbvvWHPi5dveCa9KXGnIOznOXYnLkn6ew39jt-slcSJCRdFLI7b4RN0QscYn3Ru319dPCU524KlZq9C8NLoqvik9ZeF1W9OqYTfDXjJU54PY9VjQgOPyNxA7NCmqrs_T?purpose=fullsize)

Topics covered:

* Creating additional VPC associations.

* Using `aws.route53.ZoneAssociation` in Pulumi.

* Cross-account authorization using `aws.route53.VpcAssociationAuthorization`.

* Cross-account association acceptance.

* Verifying DNS resolution from both VPCs.

* Understanding the distinction between DNS resolution and network connectivity.

Example additional association:

```python
association = aws.route53.ZoneAssociation(
    "second-vpc-association",
    zone_id=zone.zone_id,
    vpc_id="vpc-xxxxxxxx",
    vpc_region=aws.config.region,
)
```

Test:

```bash
dig api.internal.example.com
```

Run the command from instances in both VPCs.

### Lab 3 — Build Route 53 Resolver Inbound and Outbound Endpoints

Objectives:

* Create a Resolver inbound endpoint.

* Create a Resolver outbound endpoint.

* Configure endpoint network interfaces in multiple Availability Zones.

* Configure security groups.

* Inspect endpoint IP addresses.

* Verify DNS connectivity.

Architecture:

![An Update to Hybrid DNS for the Enterprise on AWS — Introducing Route 53 Resolver for Hybrid Cloud! | by Matt Adorjan | Medium](https://images.openai.com/static-rsc-4/VBcW3EFn0GtyqYA_VaAlzvnQF4GtfvVrnfMSPqhaxCthQkzPwOAiqWDGzdwFEdiKfL_pLlWZJaucxgkN958qw_sVfOjzYcUqRLkeDp1bGGeG0DEDopnaNJHrwXCiZ5-i2K7USG2MSAtpkkvdVSeeVUjTbaR_fGRGHhwkouG_bVWUZhGUKUvOK9ZFp6lgJzVr?purpose=fullsize)

Pulumi implementation:

Example security group:

```python
dns_sg = aws.ec2.SecurityGroup(
    "resolver-security-group",
    vpc_id=vpc_id,
    description="DNS Resolver endpoint security group",
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="udp",
            from_port=53,
            to_port=53,
            cidr_blocks=["10.100.0.0/16"],
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=53,
            to_port=53,
            cidr_blocks=["10.100.0.0/16"],
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

Create an inbound endpoint:

```python
inbound = aws.route53.ResolverEndpoint(
    "inbound-endpoint",
    direction="INBOUND",
    security_group_ids=[dns_sg.id],
    ip_addresses=[
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-xxxxxxxx",
        ),
        aws.route53.ResolverEndpointIpAddressArgs(
            subnet_id="subnet-yyyyyyyy",
        ),
    ],
)
```

Create an outbound endpoint using the same general resource structure, changing the direction to `OUTBOUND` and selecting appropriate subnets.

Inspect the endpoint:

```bash
aws route53resolver list-resolver-endpoints
```

Important: Each endpoint needs at least two IP addresses in different Availability Zones. The selected subnets must have appropriate connectivity, and the security groups must permit the required DNS traffic.

### Lab 4 — Configure Conditional Forwarding Rules

Objectives:

* Create a forwarding rule.

* Configure target DNS server IP addresses.

* Associate the rule with a VPC.

* Forward selected DNS namespaces to an external DNS server.

* Verify query forwarding.

Example architecture:

```text
EC2 Instance
     |
     v
VPC Resolver
     |
     v
Outbound Endpoint
     |
     v
On-Premises DNS Server
     |
     v
corp.example.com
```

Pulumi example:

```python
rule = aws.route53.ResolverRule(
    "corporate-forwarding-rule",
    domain_name="corp.example.com",
    rule_type="FORWARD",
    resolver_endpoint_id=outbound.id,
    target_ips=[
        aws.route53.ResolverRuleTargetIpArgs(
            ip="10.100.1.10",
            port=53,
        ),
        aws.route53.ResolverRuleTargetIpArgs(
            ip="10.100.2.10",
            port=53,
        ),
    ],
)

rule_association = aws.route53.ResolverRuleAssociation(
    "corporate-rule-association",
    resolver_rule_id=rule.id,
    vpc_id=vpc_id,
)
```

Test:

```bash
dig app.corp.example.com
dig @10.0.0.2 app.corp.example.com
```

Explore:

* Forwarding rules.

* System rules.

* Rule association.

* Multiple target DNS servers.

* Most-specific domain matching.

* Rule precedence over matching private hosted zones.

### Lab 5 — Simulate an On-Premises DNS Environment Using Linux

Objectives:

* Deploy a Linux VM to simulate an on-premises DNS server.

* Install and configure BIND9.

* Create a private DNS zone.

* Configure internal DNS records.

* Test DNS queries from the simulated corporate network.

We will use Ubuntu Server and BIND9.

Install BIND9:

```bash
sudo apt update

sudo apt install -y bind9 bind9-utils dnsutils
```

Configure a DNS zone in:

```bash
sudo nano /etc/bind/named.conf.local
```

Add:

```bind
zone "corp.example.com" {
    type master;
    file "/etc/bind/zones/db.corp.example.com";
};
```

Create the zone directory:

```bash
sudo mkdir -p /etc/bind/zones
```

Create the zone file:

```bash
sudo nano /etc/bind/zones/db.corp.example.com
```

Example DNS records:

```dns
$TTL 300

@ IN SOA ns1.corp.example.com. admin.corp.example.com. (
    2026103101
    3600
    1800
    604800
    300
)

@       IN NS ns1.corp.example.com.

ns1     IN A  10.100.1.10
app     IN A  10.100.1.20
db      IN A  10.100.1.30
```

Validate the configuration:

```bash
sudo named-checkconf

sudo named-checkzone \
    corp.example.com \
    /etc/bind/zones/db.corp.example.com
```

Restart BIND9:

```bash
sudo systemctl restart bind9

sudo systemctl enable bind9
```

Test:

```bash
dig @127.0.0.1 app.corp.example.com

dig @127.0.0.1 db.corp.example.com
```

Expected result: The simulated corporate DNS server resolves internal application and database records.

### Lab 6 — Implement Hybrid DNS Resolution Between AWS and On-Premises

Objectives:

* Connect an AWS VPC to the simulated on-premises network.

* Configure a Resolver inbound endpoint.

* Configure a Resolver outbound endpoint.

* Forward corporate DNS queries from AWS to BIND9.

* Forward AWS private DNS queries from BIND9 to the inbound endpoint.

* Verify bidirectional DNS resolution.

Architecture:

![An Update to Hybrid DNS for the Enterprise on AWS — Introducing Route 53 Resolver for Hybrid Cloud! | by Matt Adorjan | Medium](https://images.openai.com/static-rsc-4/VBcW3EFn0GtyqYA_VaAlzvnQF4GtfvVrnfMSPqhaxCthQkzPwOAiqWDGzdwFEdiKfL_pLlWZJaucxgkN958qw_sVfOjzYcUqRLkeDp1bGGeG0DEDopnaNJHrwXCiZ5-i2K7USG2MSAtpkkvdVSeeVUjTbaR_fGRGHhwkouG_bVWUZhGUKUvOK9ZFp6lgJzVr?purpose=fullsize)

The architecture contains two DNS resolution paths:

Path A — AWS to on-premises

```text
AWS EC2
   |
   v
VPC Resolver
   |
   v
Outbound Endpoint
   |
   v
BIND9 DNS Server
   |
   v
app.corp.example.com
```

Path B — On-premises to AWS

```text
On-Premises Client
   |
   v
BIND9 DNS Server
   |
   v
Inbound Endpoint
   |
   v
VPC Resolver
   |
   v
api.internal.example.com
```

Configure BIND9 conditional forwarding:

```bind
zone "internal.example.com" {
    type forward;
    forward only;
    forwarders {
        10.0.1.100;
        10.0.2.100;
    };
};
```

Replace the example addresses with the actual Resolver inbound endpoint IP addresses.

Validate and reload:

```bash
sudo named-checkconf

sudo systemctl reload bind9
```

From AWS:

```bash
dig app.corp.example.com
```

From on-premises:

```bash
dig @127.0.0.1 api.internal.example.com
```

Expected result: AWS workloads can resolve corporate DNS records, and on-premises workloads can resolve AWS private DNS records.

For a real hybrid deployment, use Site-to-Site VPN or Direct Connect. The lab can simulate this connectivity using a routed Linux environment or an appropriately connected test network.

### Lab 7 — Troubleshoot DNS Forwarding and Resolution Failures

Objectives:

* Diagnose private hosted zone resolution problems.

* Identify incorrect VPC DNS attributes.

* Troubleshoot Resolver endpoint connectivity.

* Diagnose forwarding rule problems.

* Identify DNS forwarding loops.

* Inspect DNS traffic and query responses.

Useful commands:

```bash
# Inspect DNS configuration
cat /etc/resolv.conf

# Query a DNS record
dig api.internal.example.com

# Query a specific DNS server
dig @10.0.1.100 app.corp.example.com

# Inspect DNS response details
dig +trace example.com

# Test TCP DNS
dig +tcp @10.0.1.100 app.corp.example.com

# Inspect DNS traffic
sudo tcpdump -ni any port 53
```

Inspect AWS resources:

```bash
aws route53 list-hosted-zones

aws route53 list-resource-record-sets \
    --hosted-zone-id ZONE_ID

aws route53resolver list-resolver-endpoints

aws route53resolver list-resolver-rules

aws route53resolver list-resolver-rule-associations
```

Troubleshooting scenarios:

* Private hosted zone exists but records return `NXDOMAIN`.

* Private hosted zone is associated with the wrong VPC.

* VPC DNS support is disabled.

* Inbound endpoint is unreachable from on-premises.

* Outbound endpoint cannot reach the corporate DNS server.

* Forwarding rule exists but is not associated with the VPC.

* Security group blocks UDP or TCP port 53.

* DNS query times out because of incorrect routing.

* A forwarding rule overrides a private hosted zone.

* Circular DNS forwarding causes repeated queries.

Use CloudWatch Resolver query logging to investigate query behavior and identify forwarding problems.

### 8\. Pulumi Project Organization and Cleanup

Throughout the labs, infrastructure should be organized into reusable Pulumi components.

Suggested project structure:

```text
route53-hybrid-dns/
│
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
│
├── __main__.py
│
├── components/
│   ├── vpc.py
│   ├── private_zone.py
│   ├── resolver_endpoint.py
│   ├── resolver_rules.py
│   └── security_groups.py
│
├── dns/
│   ├── private_records.py
│   └── forwarding.py
│
└── scripts/
    ├── test_dns.sh
    ├── diagnose_dns.sh
    └── cleanup.sh
```

Topics:

* Separating DNS infrastructure into reusable components.

* Managing multiple environments using Pulumi stacks.

* Using Pulumi configuration for VPC IDs, subnet IDs, and DNS server addresses.

* Managing infrastructure dependencies.

* Protecting important DNS resources from accidental deletion.

* Reviewing infrastructure changes with `pulumi preview`.

* Deploying infrastructure using `pulumi up`.

* Inspecting resources using `pulumi stack`.

* Destroying lab infrastructure safely using `pulumi destroy`.

* Understanding Resolver endpoint and DNS query charges.

Example cleanup script:

```bash
#!/usr/bin/env bash

set -euo pipefail

echo "Previewing infrastructure cleanup..."
pulumi preview --diff

read -r -p "Destroy lab infrastructure? (yes/no): " answer

if [[ "$answer" == "yes" ]]; then
    pulumi destroy
else
    echo "Cleanup cancelled."
fi
```

### Important Technical Notes

A few Route 53 behaviors deserve particular attention during this module:

1\. Private hosted zone resolution: If a matching private hosted zone exists but the requested record does not, Resolver returns `NXDOMAIN` rather than falling back to public DNS. Amazon Route 53 +1

2\. Forwarding rule precedence: A matching Resolver forwarding rule takes precedence over a private hosted zone with the same domain. This is particularly important when designing hybrid DNS namespaces. Amazon Route 53 +1

3\. Resolver rule types: AWS supports `FORWARD`, `SYSTEM`, and `DELEGATE` custom rule types. `RECURSIVE` is an automatically created rule type, not a normal custom forwarding rule. Amazon Route 53 +1

4\. Endpoint availability: Inbound and outbound endpoints require at least two IP addresses in different Availability Zones. Amazon Route 53

5\. Forwarding loops: Avoid configurations where an outbound forwarding rule sends queries to an inbound endpoint that ultimately routes those queries back to the same outbound endpoint. Amazon Route 53

### Recommended AWS Documentation

* [Working with Private Hosted Zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html?utm_source=chatgpt.com)

* [What is Route 53 VPC Resolver?](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html?utm_source=chatgpt.com)

* [Inbound DNS Forwarding](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-forwarding-inbound-queries.html?utm_source=chatgpt.com)

* [Outbound DNS Forwarding](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-overview-forward-vpc-to-network.html?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 Resources](https://www.pulumi.com/registry/packages/aws/api-docs/route53/?utm_source=chatgpt.com)

Module 5 completion goal: You should be able to design, deploy, and troubleshoot private DNS architectures spanning multiple VPCs, AWS accounts, and on-premises networks, using Route 53 Resolver and Pulumi.

The next module will build on this foundation by covering Route 53 Resolver DNS Firewall and DNS Security.
