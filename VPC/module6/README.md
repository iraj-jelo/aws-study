### Module 6 — DNS and Private Name Resolution

AWS Networking Course · Module 6 of 16 · Pulumi with Python

### 1\. Learning objectives

By the end of this module, you will be able to:

* Explain how Amazon Route 53 and Route 53 Resolver work together.

* Configure VPC DNS resolution and DNS hostnames correctly.

* Create private hosted zones for internal applications.

* Understand public DNS, private DNS, and split-horizon DNS.

* Configure DNS forwarding between AWS and an on-premises network.

* Understand Resolver endpoints, forwarding rules, and DNS Firewall.

* Diagnose DNS failures systematically using AWS CLI and Linux tools.

* Implement private service discovery using Pulumi and validate it from application workloads.

We'll use a realistic SaaS architecture with private application servers, an internal API, and a private database. The examples use AWS-managed DNS rather than deploying and maintaining our own DNS servers.

Lab environment: an existing VPC from Module 2 or Module 3, plus a small application workload. The main private hosted zone lab can be implemented without creating NAT gateways or public-facing services. Some optional hybrid-DNS features require additional billable infrastructure.

### 2\. DNS fundamentals and AWS architecture

### 2.1 What DNS actually does

The Domain Name System translates names into records containing information such as IP addresses and service locations.

For example:

```text
orders.internal.example.com
              |
              | DNS query: A record
              v
        10.20.12.45
              |
              | TCP connection to port 8080
              v
        Internal Orders API
```

DNS resolution and application connectivity are two separate operations:

* Name resolution: determine the IP address for a name.

* Network connectivity: establish a connection to that address.

A successful DNS lookup does not prove that the application is reachable. Security groups, routes, network ACLs, application listeners, and other controls can still block the connection.

Common DNS record types include:

| Record | Purpose                   | Example                                    |
| ------ | ------------------------- | ------------------------------------------ |
| A      | IPv4 address              | api.internal.example.com → 10.20.12.45     |
| AAAA   | IPv6 address              | api.example.com → 2001:db8::45             |
| CNAME  | Alias to another DNS name | orders.example.com → orders-lb.example.net |
| MX     | Mail exchange             | Mail delivery destination                  |
| TXT    | Text metadata             | Domain ownership verification              |
| PTR    | Reverse lookup            | IP address to hostname                     |
| SRV    | Service location and port | Service discovery metadata                 |

DNS answers can be cached by clients, operating systems, recursive resolvers, and applications. A changed record may therefore take time to become visible everywhere, depending on TTLs and caching behavior.

### 2.2 The AWS DNS components

![Cloud Icons | Amazon Route 53 64@5x](https://images.openai.com/static-rsc-4/XEeBcFric-SnBy-Gcs6DojdBeaj_D8FCh4R-rcYGEi-B6RpbLlG2b0fn_let8GpyH62OJc7LwlkCRzpdAd7i6vKQ39JIN9Kjfp3kLvVY-k540vYKFbSCKGZQv-Nt2TS0zmCOkcXdYPbGOGPpPPAZ8a6DPQo37lhcwLLz3Z0_NCUuNOl5P9VhjOMqTEjLjWGY?purpose=fullsize)

Amazon Route 53

A managed DNS service for hosting public and private DNS zones, registering domains, and routing DNS queries according to configured policies.

![VPC に AWS の DNS サーバーは何台作られるか？ - ForgeVision Engineer Blog](https://images.openai.com/static-rsc-4/nA9TVVM5XUz4CnOfiPHwFeYK9k6HSp1nZt3HjnkK4duXgInNQRZkE89Z_-zjMUgIsAULgamt0RhjyjQ_84FFtdP5Nr4m_3yl7dfBJ1MiSD6SLbZ97jBQ0yFsDGwgm4upCp8eb0RuudHxEnvxxC6apfYlSadVBrxjQE_ngPN0hLDJ9LgCEWAjmXMTLJV-071G?purpose=fullsize)

Route 53 Resolver

The recursive DNS resolver associated with VPCs. It resolves supported AWS and public DNS names, handles private hosted-zone queries, and can forward queries using Resolver rules.

![Secure your Amazon VPC DNS resolution with Amazon Route 53 Resolver DNS Firewall | Networking & Content Delivery](https://images.openai.com/static-rsc-4/HU2R8WaLMmHyMUhqnt_yKYzkX3B6Qnzc6KDVtO3iSKPoYPAHA25_OagUwkO9prWsehCxPNhdHqJarmYZYt6uzn3osE84LC54qx5qYp22Hpz8iB3Gpon8UPdJ7O97Ppu66qksFwBtzOpMJJoR6GJgtqsbWBhcIDqJYZA7OQieDvdCzmQ9yChWrzYSMlAQd7PD?purpose=fullsize)

Route 53 Resolver DNS Firewall

Applies domain-based filtering policies to DNS queries from associated VPCs. It can block known unwanted domains or allow approved domains, depending on the rule configuration.

The key distinction is that Route 53 hosts DNS data and policies, while Route 53 Resolver handles DNS queries from workloads and forwarding between DNS environments.

Amazon Route 53 is not a replacement for security groups or network routing. It helps a workload discover where a service is located; the network still determines whether the workload can reach it.

### 3\. VPC DNS resolution and DNS hostnames

### 3.1 AmazonProvidedDNS

Each VPC has access to the Amazon Route 53 Resolver, commonly called `AmazonProvidedDNS`.

For a VPC with CIDR `10.20.0.0/16`, the resolver's IPv4 address is normally:

```text
10.20.0.2
```

This is the primary IPv4 network address of the VPC plus two. Other supported resolver addresses include:

* `169.254.169.253` — IPv4 link-local resolver address.

* `fd00:ec2::253` — IPv6 resolver address.

Workloads typically receive DNS configuration through their DHCP options and use the Amazon-provided resolver automatically. You generally don't need to configure a DNS server manually on every EC2 instance.

The resolver can answer queries involving AWS-provided private hostnames, Route 53 private hosted zones, and public DNS names. Its behavior depends on the query, VPC configuration, associated zones, and Resolver rules.

### 3.2 The two important VPC DNS attributes

Two VPC attributes are especially important for private DNS.

| Attribute          | Meaning                                                                                    |
| ------------------ | ------------------------------------------------------------------------------------------ |
| enableDnsSupport   | Enables DNS resolution through the Amazon-provided resolver.                               |
| enableDnsHostnames | Enables DNS hostname functionality, including public DNS hostnames for eligible instances. |

For a custom private hosted zone, both attributes must be enabled.

Check their current values:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport

aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

If you manage the VPC with Pulumi, configure the attributes declaratively:

```python
import pulumi_aws as aws

vpc_id = "vpc-0123456789abcdef0"

dns_support = aws.ec2.VpcDnsSupport(
    "vpc-dns-support",
    vpc_id=vpc_id,
    enabled=True,
)

dns_hostnames = aws.ec2.VpcDnsHostnames(
    "vpc-dns-hostnames",
    vpc_id=vpc_id,
    enabled=True,
)
```

This example assumes the VPC already exists. For a VPC created in the same Pulumi stack, use its output rather than hard-coding the ID.

Important: enabling DNS hostnames does not automatically create your application records. It enables hostname functionality; you still need to create DNS records or use another appropriate service-discovery mechanism.

### 3.3 How DNS fits into the packet path

Application workload

getaddrinfo(), dig, nslookup

DNS query

AmazonProvidedDNS

Route 53 Resolver

Private zone

Returns internal records such as `10.20.12.45`.

Public DNS

Resolves public names using recursive DNS resolution and caching.

The actual resolution path depends on matching private hosted zones, Resolver rules, and caching.

The resolver is a managed AWS service, not a DNS server that you deploy into a subnet. Ordinary security-group and network ACL rules cannot filter traffic to or from the Amazon-provided DNS resolver. For DNS policy enforcement, consider Route 53 Resolver DNS Firewall instead.

### 4\. Private hosted zones

### 4.1 What is a private hosted zone?

A private hosted zone is a DNS namespace that Route 53 resolves for associated VPCs and supported hybrid DNS configurations.

Suppose your SaaS platform contains:

* An internal Orders API.

* A private PostgreSQL database.

* An internal administration service.

You can create a zone named `internal.example.com` and populate it with records such as:

| DNS name                      | Type | Example target |
| ----------------------------- | ---- | -------------- |
| orders.internal.example.com   | A    | 10.20.12.45    |
| postgres.internal.example.com | A    | 10.20.22.18    |
| admin.internal.example.com    | A    | 10.20.13.60    |

These are illustrative addresses; use your actual workload addresses in a deployed environment.

AWS documentation: [Working with private hosted zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html?utm_source=chatgpt.com).

### 4.2 Private hosted-zone resolution

Application in an associated VPC

`orders.internal.example.com`

Route 53 Resolver

Finds a matching private hosted zone

Private A record

`10.20.12.45`

Application connects to the target

Subject to routes, security controls, and listener availability

The private zone does not publish its records to the public internet. A client outside the zone's supported resolution scope does not automatically receive the private answers.

To resolve these names from another VPC, associate that VPC with the private zone or build an appropriate DNS forwarding architecture. Merely connecting two VPCs with peering or Transit Gateway does not automatically extend private hosted-zone resolution to every connected network.

### 4.3 Private zone association and multi-VPC designs

Consider this architecture:

```text
                Shared-services VPC
                10.20.0.0/16
                Private zone:
                internal.example.com
                         |
             +-----------+-----------+
             |                       |
       orders.internal         postgres.internal
             |                       |
         App VPC                 Data VPC
       10.21.0.0/16             10.22.0.0/16
```

The diagram represents a logical design; actual DNS resolution and IP connectivity require their respective configurations.

A production design might associate a shared private zone with multiple VPCs, but remember:

* The VPC must have DNS support and DNS hostnames enabled.

* VPCs and hosted zones must satisfy AWS's association and regional requirements.

* Cross-account associations require an authorization step from the hosted-zone-owning account, followed by association from the VPC-owning account.

* DNS association does not establish network connectivity or authorize application access.

AWS documents the cross-account process in its [private hosted-zone association guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zone-private-associate-vpcs-different-accounts.html?utm_source=chatgpt.com).

### 5\. Public DNS, private DNS, and split-horizon DNS

### 5.1 Public versus private hosted zones

| Property                        | Public hosted zone           | Private hosted zone                                      |
| ------------------------------- | ---------------------------- | -------------------------------------------------------- |
| Intended audience               | Public DNS clients           | Associated VPCs and supported DNS forwarding paths       |
| Typical use                     | Website and public API names | Internal services and private endpoints                  |
| DNS records publicly queryable  | Yes, for published records   | No, private answers are not published through public DNS |
| Example                         | www.example.com              | orders.internal.example.com                              |
| Provides network access control | No                           | No                                                       |

A public DNS record is not the same thing as a public application endpoint. A name can resolve publicly while the application remains inaccessible because of network controls. Conversely, a private DNS record can resolve successfully while its target is unreachable.

### 5.2 Split-horizon DNS

Split-horizon DNS, also called split-view DNS, means using the same domain name with different answers depending on where the DNS query is resolved.

For example, you could use `api.example.com` both internally and externally:

```text
Internal client                         External client
      |                                       |
      v                                       v
VPC Route 53 Resolver                  Public recursive DNS
      |                                       |
      v                                       v
Private hosted zone                    Public hosted zone
      |                                       |
      v                                       v
10.20.12.45                            Public load balancer
```

Internal clients receive the private address, while external clients receive the public endpoint's DNS answer.

To implement this, create a public hosted zone and a private hosted zone with the same domain name, associating the private zone with the relevant VPCs. AWS Resolver uses the private zone for matching queries within those VPCs.

A subtle but important failure mode: if the private hosted zone matches `example.com`, but a requested record such as `api.example.com` does not exist in that private zone, Resolver can return `NXDOMAIN` instead of falling back to the public hosted zone. Ensure the private zone contains the internal names clients need.

Also, when a Resolver forwarding rule matches a domain that is also covered by a private hosted zone, the forwarding rule takes precedence. This can change the resolution path unexpectedly.

### 6\. Route 53 Resolver endpoints and DNS forwarding

This is the part of AWS DNS that becomes especially important when an organization connects AWS to its corporate network.

### 6.1 Inbound versus outbound endpoints

Resolver endpoints allow DNS queries to cross the boundary between a VPC and a connected network. They do not replace the underlying VPN or Direct Connect connection.

Inbound endpoint

Network → AWS

A DNS server in an on-premises network forwards queries to AWS so that clients can resolve private hosted-zone names.

Example: corporate clients resolving `orders.internal.example.com`.

Outbound endpoint

AWS → Network

AWS Resolver forwards matching queries to DNS servers in your corporate network.

Example: AWS workloads resolving `erp.corp.example.com`.

AWS documents these as separate forwarding configurations.

### 6.2 Hybrid DNS architecture

Imagine that your company has an internal DNS zone, `corp.example.com`, hosted on a corporate DNS server at `172.16.10.10`. AWS workloads must resolve `erp.corp.example.com`, while corporate users must resolve services in AWS.

Corporate network

Corporate DNS: 172.16.10.10

Site-to-Site VPN or Direct Connect

AWS VPC — 10.20.0.0/16

Inbound endpoint

Accepts forwarded corporate DNS queries.

Outbound endpoint

Sends matching queries to corporate DNS.

Route 53 Resolver

Private hosted zones + forwarding rules

The endpoint IP addresses are private addresses from the VPC. Inbound and outbound endpoints should be designed for availability, with IPs placed in appropriate subnets and network connectivity to the other DNS environment. Outbound forwarding requires a reachable target resolver; inbound forwarding requires the corporate network to reach the endpoint IPs.

### 6.3 Resolver rules

A Resolver rule tells AWS how to handle queries for a particular DNS suffix.

For example:

| Rule type | Domain               | Target                       | Behavior                                                |
| --------- | -------------------- | ---------------------------- | ------------------------------------------------------- |
| Forward   | corp.example.com     | 172.16.10.10                 | Forward matching queries to corporate DNS               |
| Forward   | dev.corp.example.com | 172.16.20.10                 | Forward a more specific namespace to another DNS server |
| System    | Applicable domain    | AWS Resolver behavior        | Use the normal Resolver path for the matching namespace |
| Recursive | .                    | Configured target DNS server | Forward all DNS queries, where configured and supported |

The final row represents a broad forwarding design and should not be added casually: it can redirect queries that would otherwise be resolved normally.

For ordinary conditional forwarding, create a Forward rule, configure the domain and target IP addresses, then associate the rule with each VPC that needs it. The target DNS servers must be reachable over the network, and their firewall policies must permit DNS traffic.

### 6.4 Example: AWS queries corporate DNS

Suppose an EC2 instance needs to resolve `erp.corp.example.com`.

* The application asks the VPC resolver for the address.

* Resolver matches the `corp.example.com` forwarding rule.

* The outbound endpoint sends the DNS query to `172.16.10.10`.

* The corporate DNS server returns an address, such as `172.16.40.25`.

* Resolver returns the answer to the EC2 instance.

* The application attempts a connection to `172.16.40.25`.

DNS resolution can succeed even if the last step fails because the VPN route, security rules, or corporate firewall do not allow the connection.

### 6.5 Production considerations

* Use redundant endpoint IPs in separate Availability Zones as appropriate for the endpoint design.

* Permit UDP and TCP port 53 between the DNS clients, endpoints, and target resolvers as required.

* Verify return routes as well as forward routes.

* Avoid forwarding rules that unintentionally overlap with private hosted zones.

* Configure DNS logging and monitor query failures.

* Consider the hourly and query-processing costs of Resolver endpoints.

* Do not expose endpoint IPs to the public internet; they are intended for private connectivity.

### 7\. Route 53 Resolver DNS Firewall

DNS Firewall filters DNS queries passing through Route 53 VPC Resolver. It can help block malicious domains, restrict DNS access to approved namespaces, and reduce certain DNS-based exfiltration risks.

### 7.1 How filtering works

```text
Application workload
        |
        v
Route 53 Resolver
        |
        v
DNS Firewall rule-group evaluation
        |
        +---- Matching BLOCK rule ---> Blocked response
        |
        +---- Matching ALLOW rule ---> Continue resolution
        |
        +---- No matching rule ------> Continue normal resolution
```

Rule groups contain ordered rules. Lower numerical priority values are evaluated first. DNS Firewall supports domain-list rules with allow, block, and alert actions, as well as advanced protections for certain DNS threats.

### 7.2 Example policy

Suppose a workload should resolve approved external domains, but DNS queries to known malicious domains must be blocked.

A typical block-list approach is:

* Create a domain list for known unwanted domains.

* Create a DNS Firewall rule group.

* Add a `BLOCK` rule referencing that list.

* Associate the rule group with the VPC.

* Enable logging and monitor the resulting metrics.

* Test both a blocked domain and a known-good domain.

For a strict allow-list design, order the rules so approved domains are allowed before a final rule blocks everything else. Be careful: an allow-list can break application dependencies, certificate validation, software updates, and other legitimate DNS lookups.

See the [official DNS Firewall getting-started guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-getting-started.html?utm_source=chatgpt.com).

### 7.3 DNS Firewall is not a general firewall

DNS Firewall makes decisions about DNS queries, not arbitrary TCP or UDP connections.

It does not, by itself:

* Block HTTPS connections to an IP address that an application already knows.

* Prevent applications from bypassing the resolver with an alternative DNS service unless the network also restricts that traffic.

* Replace security groups, network ACLs, AWS Network Firewall, or application authorization.

A further design decision is whether Resolver should fail open or fail closed if DNS Firewall cannot provide a filtering response. The default is fail closed, favoring security over availability.

### 8\. Hands-on lab — Private DNS with Pulumi

We'll now create a private hosted zone and a record for an internal service. This lab is suitable for an existing VPC with DNS support enabled. It does not require a NAT gateway, a Resolver endpoint, or an internet-facing application.

### 8.1 Target architecture

Application workload

EC2 instance or another workload in the VPC

Route 53 Resolver

Resolves the private DNS name

Private hosted zone

`internal.example.com`

A record

`orders.internal.example.com → 10.20.12.45`

We'll use `10.20.12.45` as an example address. For a real service, replace it with the actual private IPv4 address of a reachable target.

### 8.2 Prerequisites and cost safety

You need:

* Python and Pulumi CLI installed.

* An AWS CLI v2 profile with permissions to manage Route 53 hosted zones and records.

* An existing VPC in the selected Region.

* An application workload in that VPC for the final verification.

* `dig` or `nslookup` installed on the workload.

Creating a private hosted zone and its records has a small but nonzero cost under Route 53 pricing. An EC2 instance, if you create one for testing, may add compute and storage charges. Check the [Route 53 pricing page](https://aws.amazon.com/route53/pricing/?utm_source=chatgpt.com) before deploying.

First, identify your AWS account, Region, and VPC:

```bash
aws sts get-caller-identity
aws configure get region

aws ec2 describe-vpcs \
  --query 'Vpcs[].{VpcId:VpcId,CIDR:CidrBlock,State:State}' \
  --output table
```

Set the appropriate VPC ID and Region in the next steps. Do not assume the illustrative IDs or addresses in this lesson exist in your account.

### 8.3 Create the Pulumi project

Create a project directory:

```bash
mkdir aws-private-dns
cd aws-private-dns

pulumi new aws-python
```

Select the AWS Region where your VPC exists. The template may create starter files; we'll replace the main program with the following implementation.

Install or update the AWS provider dependency using the Python environment created by the Pulumi template:

```bash
python -m pip install --upgrade pulumi pulumi-aws
```

Create the configuration values:

```bash
pulumi config set aws:region eu-west-1
pulumi config set vpcId vpc-0123456789abcdef0
pulumi config set serviceIpv4 10.20.12.45
```

Replace the sample Region, VPC ID, and service IP address with your own values.

### 8.4 Implement the infrastructure

Replace `__main__.py` with:

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
service_ipv4 = config.require("serviceIpv4")
region = config.require("region")

# Ensure the existing VPC supports Route 53 private DNS.
dns_support = aws.ec2.VpcDnsSupport(
    "private-dns-support",
    vpc_id=vpc_id,
    enabled=True,
)

dns_hostnames = aws.ec2.VpcDnsHostnames(
    "private-dns-hostnames",
    vpc_id=vpc_id,
    enabled=True,
    opts=pulumi.ResourceOptions(
        depends_on=[dns_support],
    ),
)

# Create a private hosted zone associated with the VPC.
private_zone = aws.route53.Zone(
    "internal-zone",
    name="internal.example.com",
    comment="Private DNS for internal application services",
    vpcs=[
        aws.route53.ZoneVpcArgs(
            vpc_id=vpc_id,
            vpc_region=region,
        )
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[dns_hostnames],
    ),
)

# Register an internal service address.
orders_record = aws.route53.Record(
    "orders-record",
    zone_id=private_zone.zone_id,
    name="orders.internal.example.com",
    type="A",
    ttl=60,
    records=[service_ipv4],
)

pulumi.export("private_zone_id", private_zone.zone_id)
pulumi.export("private_zone_name", private_zone.name)
pulumi.export("orders_dns_name", orders_record.name)
pulumi.export("orders_ipv4", service_ipv4)
```

Add the missing project configuration:

```bash
pulumi config set region eu-west-1
```

The `region` value must match the actual Region of the VPC. In a more extensive project, you would typically obtain this from the AWS provider configuration instead of maintaining a duplicate setting.

What the code creates:

* `VpcDnsSupport` enables VPC DNS resolution.

* `VpcDnsHostnames` enables DNS hostname functionality.

* `route53.Zone` creates a private hosted zone associated with the existing VPC.

* `route53.Record` creates an A record for the Orders service.

* `depends_on` ensures the VPC DNS settings are applied before the hosted zone is created.

The record itself is just DNS metadata. It does not deploy an Orders API or verify that a service listens at the configured IP address.

### 8.5 Preview, deploy, and inspect

Review the proposed changes first:

```bash
pulumi preview
```

Check that the preview contains only the intended DNS resources and VPC attribute changes. Then deploy:

```bash
pulumi up
```

Review the plan and approve it when correct.

Display the stack outputs:

```bash
pulumi stack output
pulumi stack output private_zone_id
pulumi stack output orders_dns_name
```

You can inspect the hosted zone through the AWS CLI:

```bash
ZONE_ID=$(pulumi stack output private_zone_id)

aws route53 get-hosted-zone \
  --id "$ZONE_ID"

aws route53 list-resource-record-sets \
  --hosted-zone-id "$ZONE_ID"
```

To verify the VPC DNS attributes:

```bash
VPC_ID=$(pulumi config get vpcId)

aws ec2 describe-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --attribute enableDnsSupport

aws ec2 describe-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --attribute enableDnsHostnames
```

### 8.6 Verify from an application workload

Run these commands from an EC2 instance or another suitable workload inside the associated VPC. A command run on your local Windows computer will not normally have access to the private zone unless you've established an appropriate DNS forwarding or hybrid-resolution path.

First, inspect the resolver configuration:

```bash
cat /etc/resolv.conf
```

Then query the private record:

```bash
dig orders.internal.example.com A
```

You should see an answer similar to:

```text
;; ANSWER SECTION:
orders.internal.example.com. 60 IN A 10.20.12.45
```

The exact formatting and remaining TTL can differ.

If `dig` is unavailable, try:

```bash
nslookup orders.internal.example.com
```

Or, using Python's standard library:

```bash
python -c "import socket; print(socket.getaddrinfo('orders.internal.example.com', 8080))"
```

The Python example tests the operating system's name-resolution path. It does not establish a TCP connection to the service.

Finally, test application connectivity separately. If the service is listening on TCP port 8080:

```bash
curl --connect-timeout 3 \
  http://orders.internal.example.com:8080/health
```

This last command will succeed only if the example service is actually running, the DNS record points to its current address, and the network and application permit the request.

### 8.7 Test failure scenarios

| Test                                             | Expected result                               | What it demonstrates                                         |
| ------------------------------------------------ | --------------------------------------------- | ------------------------------------------------------------ |
| Query from the associated VPC                    | Private A record returned                     | Private DNS works                                            |
| Query a nonexistent name within the private zone | Usually NXDOMAIN                              | The private zone is authoritative for the matching namespace |
| Query from an unrelated network                  | No private answer through ordinary public DNS | Private DNS scope matters                                    |
| Resolve the name but block the service port      | DNS succeeds, connection fails                | DNS and network reachability are separate                    |
| Query after changing a record                    | May temporarily show a cached answer          | DNS caching and TTL behavior matter                          |

For repeatable testing, avoid using an address belonging to an unrelated production system. Use a test workload or a reserved lab address, and remember that a successful lookup of an example IP does not prove that the address is reachable.

### 8.8 Cleanup

After completing the lab, remove the resources created by this Pulumi stack:

```bash
pulumi destroy
```

Review the proposed deletions before approving them.

Important: the code manages DNS attributes on an existing VPC. Those settings are shared VPC configuration, not dedicated lab resources. Pulumi may restore their prior values or otherwise manage them as the stack is destroyed, depending on the recorded state and provider behavior. Check the VPC's DNS requirements before destroying the stack. If the VPC is shared with other workloads, consider keeping the DNS attributes under the ownership of the main VPC stack rather than this lab stack.

The hosted zone and record are the lab's dedicated resources; verify their removal with the AWS CLI if necessary.

### 9\. Troubleshooting DNS failures systematically

When DNS fails, don't immediately change routing tables or security groups. First determine whether the failure is actually DNS-related.

### 9.1 Understand the DNS response

| Response or symptom            | Likely meaning                                             | First investigation                                                                    |
| ------------------------------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| NXDOMAIN                       | The queried name does not exist in the applicable DNS view | Check record name, hosted zone, and private-zone matching                              |
| SERVFAIL                       | The resolver could not complete resolution                 | Investigate forwarding targets, DNSSEC where applicable, and DNS Firewall              |
| REFUSED                        | A DNS server refused the query                             | Inspect server policies and query permissions                                          |
| Timeout                        | No DNS response arrived                                    | Check resolver configuration, endpoint reachability, network paths, and DNS throttling |
| Correct IP, connection timeout | DNS may be working; application connectivity is failing    | Check routes, security groups, network ACLs, and service listeners                     |
| Stale IP                       | A cached answer may be outdated                            | Check TTLs and application-level DNS caching                                           |

These are diagnostic starting points, not definitive diagnoses. For example, an `NXDOMAIN` response may be perfectly correct if the name is missing from a matching private hosted zone.

### 9.2 A practical diagnostic sequence

Run the following commands from the affected workload.

Step 1 — Inspect the resolver configuration

```bash
cat /etc/resolv.conf
```

Check which DNS server the workload uses. If you're running a container, inspect its DNS configuration separately; Docker and Kubernetes can introduce their own DNS layers.

Step 2 — Query the intended name

```bash
dig orders.internal.example.com A
dig orders.internal.example.com A +noall +answer +comments
```

Inspect the status, returned address, and TTL.

Step 3 — Compare against the VPC resolver

For a VPC with IPv4 CIDR `10.20.0.0/16`:

```bash
dig @10.20.0.2 orders.internal.example.com A
```

Replace `10.20.0.2` with the resolver address appropriate to your VPC.

If an explicit resolver query succeeds but the application's normal lookup fails, investigate the workload's DNS configuration, local caches, or container DNS forwarding.

Step 4 — Inspect the hosted zone

```bash
aws route53 list-hosted-zones

aws route53 list-resource-record-sets \
  --hosted-zone-id Z0123456789EXAMPLE
```

Confirm the zone exists, the record name is correct, and the expected record type and address are present.

Step 5 — Check VPC attributes

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsSupport

aws ec2 describe-vpc-attribute \
  --vpc-id vpc-0123456789abcdef0 \
  --attribute enableDnsHostnames
```

Both should be enabled for custom private hosted-zone resolution.

Step 6 — If forwarding is involved, check the full path

For hybrid DNS, verify:

* The matching Resolver rule is associated with the correct VPC.

* The outbound endpoint is available.

* The target DNS server is reachable.

* UDP and TCP port 53 are allowed where needed.

* The corporate DNS server knows how to answer the queried domain.

* The return path is valid.

AWS warns that unreachable forwarding targets can cause extended DNS resolution times.

Step 7 — Test the application connection separately

```bash
curl --connect-timeout 3 \
  http://orders.internal.example.com:8080/health
```

If DNS returns the correct IP but this fails, move to the network and application troubleshooting process from Module 5.

### 9.3 Resolver query logging

For production troubleshooting, consider Route 53 Resolver query logging. It records DNS queries made through the VPC Resolver and can help identify query sources, names, response information, and patterns of failure. Query logs can be sent to supported destinations such as CloudWatch Logs, S3, and Firehose.

This is particularly useful when a failure is intermittent or occurs only in one application environment.

Official reference: [Route 53 Resolver query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs.html?utm_source=chatgpt.com).

### 10\. Security and production design

Use these practices when designing DNS for a production SaaS platform.

* Keep internal namespaces private. Use private hosted zones for internal service discovery, and avoid unnecessarily publishing internal infrastructure details in public DNS.

* Avoid hard-coded IP addresses in application configuration. Use stable DNS names for services where appropriate, while accounting for DNS caching and address changes.

* Design for multiple VPCs explicitly. Associate private zones or configure Resolver forwarding deliberately; do not assume network connectivity implies DNS visibility.

* Apply least privilege. Limit who can create, modify, associate, or delete hosted zones and DNS records.

* Use DNS Firewall where the threat model justifies it. Validate filtering rules and failure behavior before enforcing strict allow-lists.

* Monitor resolution failures. Use query logging, DNS Firewall metrics, and application telemetry to distinguish DNS issues from connectivity issues.

* Review DNS TTLs. Short TTLs can help when records change frequently but can increase query volume; long TTLs reduce repeated queries but may prolong stale answers.

* Protect DNS changes through IaC review. Use Pulumi previews and code review, and separate shared VPC configuration from application-specific DNS resources.

* Account for costs and quotas. Resolver endpoints, query logging, and DNS Firewall may add charges. AWS also documents a 1,024-packets-per-second aggregate limit for services using certain link-local addresses, including Resolver queries, IMDS, and other services.

### 11\. Module summary

You should now understand the major DNS resolution paths used in AWS:

* Route 53 hosted zones hold public or private DNS records.

* Route 53 Resolver handles DNS queries for VPC workloads.

* Private hosted zones provide internal service names within an explicitly configured DNS scope.

* Split-horizon DNS provides different answers to internal and external clients.

* Resolver inbound endpoints allow connected external networks to query DNS in AWS.

* Resolver outbound endpoints and rules forward matching AWS queries to external DNS servers.

* DNS Firewall applies domain-based filtering to queries passing through Resolver.

The essential troubleshooting principle is to separate name resolution from network connectivity. Confirm the DNS answer first, then investigate the path to the returned address.

### 12\. Official AWS references

* [Understanding Amazon DNS and VPC DNS attributes](https://docs.aws.amazon.com/vpc/latest/userguide/AmazonDNS-concepts.html?utm_source=chatgpt.com)

* [Working with private hosted zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-private.html?utm_source=chatgpt.com)

* [Private hosted-zone considerations and split-view DNS](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zone-private-considerations.html?utm_source=chatgpt.com)

* [Forwarding inbound DNS queries to VPCs](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-forwarding-inbound-queries.html?utm_source=chatgpt.com)

* [Forwarding outbound DNS queries to your network](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-forwarding-outbound-queries.html?utm_source=chatgpt.com)

* [Route 53 Resolver DNS Firewall](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall.html?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 Zone resource](https://www.pulumi.com/registry/packages/aws/api-docs/route53/zone/?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 Record resource](https://www.pulumi.com/registry/packages/aws/api-docs/route53/record/?utm_source=chatgpt.com)

Next: Module 7 — VPC Endpoints and Private AWS Service Access. We'll cover gateway endpoints, interface endpoints, PrivateLink, endpoint policies, private DNS for AWS services, and how to reduce reliance on general-purpose internet egress.
