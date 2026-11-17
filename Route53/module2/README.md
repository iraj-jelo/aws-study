### Module 2 — Hosted Zones, DNS Records, and Domain Management

### 1\. Learning Objectives

By the end of this module, you will understand how Amazon Route 53 manages DNS namespaces, hosted zones, DNS records, and domain registration.

You will learn to:

* Create and manage public and private hosted zones.

* Understand DNS delegation and authoritative name servers.

* Configure common DNS record types.

* Understand the differences between Alias and CNAME records.

* Integrate Route 53 with AWS services such as Application Load Balancers.

* Manage DNS records programmatically using Pulumi and AWS CLI.

* Import existing Route 53 resources into Pulumi.

* Organize DNS infrastructure across multiple Pulumi stacks.

We will use Python for Pulumi programs and Bash for AWS CLI commands.

### 2\. Public Hosted Zones

### 2.1 What Is a Public Hosted Zone?

A public hosted zone is a container for DNS records that define how traffic is routed for a publicly accessible domain.

For example, suppose you own:

```text
example.com
```

You might configure the following DNS records:

| Record           | Type  | Purpose                     |
| ---------------- | ----- | --------------------------- |
| example.com      | A     | Root domain IPv4 address    |
| www.example.com  | CNAME | Website alias               |
| api.example.com  | A     | API endpoint                |
| mail.example.com | A     | Mail server                 |
| example.com      | MX    | Mail delivery servers       |
| example.com      | TXT   | Domain verification and SPF |

A public hosted zone is authoritative for its DNS namespace. When a DNS resolver queries an authoritative name server for a record within that namespace, Route 53 can return the corresponding DNS record.

### 2.2 Public Hosted Zone Architecture

When you create a public hosted zone, Route 53 automatically creates several default records:

* NS record: Identifies the authoritative name servers assigned to the hosted zone.

* SOA record: Contains administrative information about the DNS zone, including the primary name server and refresh-related parameters.

For example:

```text
example.com.    NS    ns-123.awsdns-45.com.
example.com.    NS    ns-456.awsdns-78.net.
example.com.    NS    ns-789.awsdns-12.org.
example.com.    NS    ns-012.awsdns-34.co.uk.
```

These name servers are responsible for answering authoritative DNS queries for the hosted zone.

![How to move your DNS to Amazon Route 53 - Edge Cloud](https://images.openai.com/static-rsc-4/evX1s_QCG5IWtnueopcxkK50ZhPO_IsyMOtpo_GSSZwjbzBH6F_nxJSx3JKfx5XI5IIEf54Y-uo9P7eQVPCJc0MiPtU8dVTwz0p10LUASpJjzfQkN5gaXslGD9vGKjf6RshDyiDcFHlq4ZceT0B5t6PLjwsNnlXKBI6tS_-JRBZBFuRjTd6E7qesfr7SFTgc?purpose=fullsize)

### 2.3 Hosted Zone and Domain Registration Are Different

An important distinction:

* A domain registration establishes your ownership or registration rights for a domain.

* A hosted zone stores the DNS records that control how the domain resolves.

You can register a domain through Route 53 and use its hosted zone, but these are separate resources with separate billing.

You can also register a domain with another registrar and use Route 53 for DNS hosting.

### 2.4 Inspecting a Public Hosted Zone

Using AWS CLI:

```bash
aws route53 list-hosted-zones
```

Retrieve information about a particular hosted zone:

```bash
aws route53 get-hosted-zone \
  --id Z123456789ABCDEFG
```

List its DNS records:

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789ABCDEFG
```

Inspect the authoritative name servers:

```bash
aws route53 get-hosted-zone \
  --id Z123456789ABCDEFG \
  --query 'DelegationSet.NameServers'
```

### 2.5 DNS Resolution and Delegation

Creating a public hosted zone does not automatically make it authoritative on the public internet.

You must configure the domain's delegation at the parent DNS level.

For a registered domain, this normally means configuring the domain's name servers at the registrar.

For example:

```text
example.com
    |
    v
Parent zone (.com)
    |
    | NS delegation
    v
Route 53 authoritative name servers
    |
    v
DNS records in the hosted zone
```

Without correct delegation, public DNS resolvers might continue querying the previous authoritative name servers.

### 3\. Private Hosted Zones

### 3.1 What Is a Private Hosted Zone?

A private hosted zone contains DNS records that are resolvable only within associated Amazon VPCs through the VPC's DNS resolution infrastructure.

For example, consider an application running inside a VPC:

```text
api.internal.example.com
database.internal.example.com
redis.internal.example.com
```

These names can resolve to private IP addresses without exposing the DNS namespace to the public internet.

Typical use cases include:

* Internal application service discovery.

* Database endpoint naming.

* Private microservice communication.

* Internal infrastructure management.

* Hybrid cloud and on-premises DNS integration.

![AWS - Route 53](https://images.openai.com/static-rsc-4/xWIBk-hliVWHclcgbJORotCOQSmsuVvkYh8JnM2CjK72mv5Lps8ROhdB4bQVCJbcJUK2Ksa7KOBYCePLZC6gikEdydMsBeIEmy_61ECAv924GqhrOus8IX0rqykiYNpfoThZlnMemv04VhhtFbizjLTNnVIQzR1vvNR1hiGpTrBrdYx35HGrNqfwiuBesxrv?purpose=fullsize)

### 3.2 Private Hosted Zone and VPC Association

A private hosted zone must be associated with at least one VPC.

Important properties:

* A hosted zone can be associated with multiple VPCs.

* VPCs can belong to different AWS accounts.

* Cross-account association requires an authorization and association workflow.

* The VPC must have DNS resolution enabled.

* Private hosted zones are not publicly authoritative DNS zones.

Two important VPC attributes are:

DNS resolution

```text
enableDnsSupport = true
```

Allows instances in the VPC to query the Amazon-provided DNS server.

DNS hostnames

```text
enableDnsHostnames = true
```

Enables DNS hostnames for instances that receive public IP addresses and supports private hosted zone functionality.

For private hosted zones, keep both attributes enabled.

### 3.3 Split-Horizon DNS

Split-horizon DNS means returning different DNS answers depending on the network from which a query originates.

For example:

| DNS name             | Public DNS         | Private DNS              |
| -------------------- | ------------------ | ------------------------ |
| api.example.com      | Public ALB address | Internal ALB address     |
| database.example.com | No record          | Private database address |

You can achieve this by creating public and private hosted zones with the same domain name and associating the private zone with the appropriate VPCs.

Be careful: the private hosted zone takes precedence for matching queries inside an associated VPC. A missing record in that private zone does not automatically cause Route 53 to fall back to the public hosted zone.

### 3.4 Inspecting Private Hosted Zones

List hosted zones:

```bash
aws route53 list-hosted-zones
```

Inspect a particular zone:

```bash
aws route53 get-hosted-zone \
  --id Z123456789ABCDEFG
```

Inspect its VPC associations:

```bash
aws route53 get-hosted-zone \
  --id Z123456789ABCDEFG \
  --query 'VPCs'
```

### 4\. Hosted Zone Delegation and Authoritative Name Servers

### 4.1 What Is DNS Delegation?

DNS delegation allows a parent DNS zone to assign authority over a subdomain to another set of authoritative name servers.

Suppose you have:

```text
example.com
```

You want to manage:

```text
dev.example.com
```

independently.

You can create two hosted zones:

```text
example.com
dev.example.com
```

The parent zone contains an NS record for `dev.example.com` pointing to the authoritative name servers of the child zone.

![How the Web Works: Exploring Its Architecture and Components | Security Mates](https://images.openai.com/static-rsc-4/ecuKVU7Dk1yzO5cG30JS2bf2ylCsw-BYYXeVlE1_OobDvzNHgbQPSZKCYbd21L1WQeIzupknOzHnDE11c7QNik2Orr-tRcqKDp0uUmjE_PJ_GR1JIqrTHOCM8St4iG-XlhY2FBwPcLPKfTH5r6gdQ1XnSeFYhBEzzxWUrWRrPG2SJyiIEoFkIv5ngyQJXz0A?purpose=fullsize)

### 4.2 Parent and Child Hosted Zones

Parent hosted zone:

```text
example.com
```

Child hosted zone:

```text
dev.example.com
```

The parent contains:

```dns
dev.example.com. NS ns-111.awsdns-22.com.
dev.example.com. NS ns-333.awsdns-44.net.
```

The child zone contains its own DNS records:

```dns
dev.example.com. A 192.0.2.10
api.dev.example.com. A 192.0.2.20
```

The parent does not need to contain every record in the child zone.

### 4.3 Important Delegation Concepts

* NS records establish delegation.

* The child zone has its own SOA record.

* The parent and child zones are independently managed.

* Delegation can cross AWS accounts.

* Incorrect NS records can cause DNS resolution failures.

* Parent-zone delegation and registrar-level delegation are different operations.

### 4.4 Verifying Delegation

Use:

```bash
dig NS example.com
```

Check the subdomain:

```bash
dig NS dev.example.com
```

Trace the DNS resolution path:

```bash
dig +trace api.dev.example.com
```

You should be able to identify the parent zone, delegation records, and child authoritative name servers.

### 5\. Domain Registration and Management

### 5.1 Domain Registration Through Route 53

Amazon Route 53 Domains allows you to register and manage domain names.

The domain registration process generally includes:

* Checking domain availability.

* Selecting an available domain.

* Providing registrant contact information.

* Completing registration requirements.

* Configuring authoritative name servers.

* Managing domain renewal and expiration.

Domain registration and DNS hosting are separate Route 53 capabilities.

### 5.2 Domain Lifecycle

A domain has a lifecycle that includes:

* Registration.

* Active registration.

* Renewal.

* Transfer.

* Expiration.

* Possible restoration or deletion, depending on the TLD and registrar policies.

Automatic renewal can help prevent accidental expiration, but you should still monitor renewal status and payment configuration.

### 5.3 Domain Transfers

You can transfer a domain from another registrar to Route 53 or transfer it away from Route 53.

Important concepts:

* Domain authorization codes (EPP/Auth codes).

* Domain transfer locks.

* Registrar transfer eligibility.

* Registration contact verification.

* TLD-specific transfer restrictions.

* DNS continuity during a registrar transfer.

A registrar transfer does not necessarily require changing DNS hosting. You can keep your existing authoritative DNS provider during the transfer.

### 5.4 Domain Registration CLI

Inspect available Route 53 Domains CLI commands:

```bash
aws route53domains help
```

Check domain availability:

```bash
aws route53domains check-domain-availability \
  --domain-name example.com
```

Inspect domain registration details:

```bash
aws route53domains get-domain-detail \
  --domain-name example.com
```

Note: Route 53 Domains operations have supported-region and TLD restrictions. Domain registration also has separate permissions and billing requirements.

### 6\. DNS Record Types and Their Use Cases

DNS records define how domain names map to IP addresses, other domain names, mail servers, and application-related information.

### 6.1 A Record

An A record maps a domain name to an IPv4 address.

Example:

```dns
api.example.com.  300  IN  A  192.0.2.10
```

Common use cases:

* Mapping domains to IPv4 addresses.

* Directing traffic to EC2 instances.

* Configuring DNS for externally hosted applications.

* Publishing static IPv4 endpoints.

AWS CLI:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789ABCDEFG \
  --change-batch '{
    "Changes": [{
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {"Value": "192.0.2.10"}
        ]
      }
    }]
  }'
```

### 6.2 AAAA Record

An AAAA record maps a domain name to an IPv6 address.

Example:

```dns
api.example.com. 300 IN AAAA 2001:db8::10
```

Use cases:

* IPv6-enabled applications.

* Dual-stack infrastructure.

* IPv6 connectivity to web servers and network endpoints.

Example query:

```bash
dig AAAA api.example.com
```

### 6.3 CNAME Record

A CNAME record creates an alias from one DNS name to another DNS name.

Example:

```dns
www.example.com. 300 IN CNAME example.com.
```

When a resolver queries `www.example.com`, the CNAME directs it to resolve `example.com`.

Important restrictions:

* A CNAME cannot coexist with other record types at the same DNS name.

* A CNAME cannot be created at the zone apex.

* A CNAME points to another domain name, not directly to an IP address.

Example:

```bash
dig CNAME www.example.com
```

### 6.4 MX Record

An MX record specifies which mail servers receive email for a domain.

Example:

```dns
example.com. 300 IN MX 10 mail1.example.com.
example.com. 300 IN MX 20 mail2.example.com.
```

The numeric values represent priorities. Lower values have higher priority.

Use cases:

* Configuring email hosting.

* Integrating with Google Workspace or Microsoft 365.

* Defining primary and backup mail servers.

### 6.5 TXT Record

TXT records store arbitrary text information associated with a DNS name.

Example:

```dns
example.com. IN TXT "v=spf1 include:example.net -all"
```

Common applications:

* SPF email authentication.

* Domain ownership verification.

* DKIM public-key publication.

* DMARC policy publication.

* Third-party service verification.

Example:

```bash
dig TXT example.com
```

Remember that SPF, DKIM, and DMARC have different DNS record locations and purposes.

For example:

```dns
example.com.             TXT "v=spf1 ..."
selector1._domainkey.example.com. TXT "v=DKIM1; ..."
_dmarc.example.com.      TXT "v=DMARC1; ..."
```

### 6.6 CAA Record

CAA (Certification Authority Authorization) records specify which certificate authorities are permitted to issue TLS certificates for a domain.

Example:

```dns
example.com. IN CAA 0 issue "letsencrypt.org"
```

You can also configure:

```dns
example.com. IN CAA 0 issuewild "letsencrypt.org"
example.com. IN CAA 0 iodef "mailto:security@example.com"
```

The main CAA properties are:

| Property | Purpose                                |
| -------- | -------------------------------------- |
| Flags    | Controls criticality behavior          |
| Tag      | issue, issuewild, or iodef             |
| Value    | CA identifier or reporting destination |

CAA records are useful for reducing the risk of unauthorized certificate issuance.

### 6.7 Additional DNS Record Types

Although this module focuses on A, AAAA, CNAME, MX, TXT, and CAA, you should recognize these additional record types:

| Record | Purpose                                              |
| ------ | ---------------------------------------------------- |
| NS     | Identifies authoritative name servers                |
| SOA    | Contains DNS zone administrative information         |
| SRV    | Specifies service location, port, and priority       |
| PTR    | Reverse DNS lookup                                   |
| DS     | DNSSEC delegation information                        |
| HTTPS  | Publishes HTTPS service connection information       |
| TLSA   | Associates certificates or public keys with services |

You can inspect DNS records using:

```bash
dig A example.com
dig AAAA example.com
dig MX example.com
dig TXT example.com
dig CAA example.com
dig NS example.com
dig SOA example.com
```

### 7\. Alias Records versus CNAME Records

One of the most important Route 53 concepts is the difference between Alias and CNAME records.

### 7.1 What Is a Route 53 Alias Record?

An Alias record is an AWS-specific DNS record mechanism that allows a DNS name to point to supported AWS resources or another record in the same hosted zone.

For example:

```text
example.com
    |
    v
Application Load Balancer
    |
    v
EC2 / ECS / EKS targets
```

You can configure the root domain directly to point to an ALB without using a CNAME.

### 7.2 Alias versus CNAME

| Feature                             | Alias                             | CNAME                              |
| ----------------------------------- | --------------------------------- | ---------------------------------- |
| AWS-specific                        | Yes                               | No                                 |
| Zone apex support                   | Yes, for supported target types   | No                                 |
| Points to DNS names                 | Yes                               | Yes                                |
| Points to AWS resources             | Yes, supported resources          | Indirectly through DNS names       |
| Requires TTL configuration          | AWS-managed for supported aliases | Yes                                |
| Can coexist with other record types | Yes, subject to DNS record rules  | No                                 |
| Routing policies                    | Supported                         | Supported                          |
| AWS resource health evaluation      | Supported where applicable        | No direct target-health evaluation |

An important detail: Alias records do not have a user-configurable TTL. Route 53 uses the TTL behavior of the target service.

### 7.3 Supported Alias Targets

Common supported targets include:

* Application Load Balancers.

* Network Load Balancers.

* Classic Load Balancers.

* CloudFront distributions.

* API Gateway custom domain names.

* S3 website endpoints.

* AWS Global Accelerator.

* Other records in the same hosted zone.

Not every AWS resource is supported. For example, you cannot create an Alias record directly to an ordinary EC2 instance.

### 7.4 Alias Record for an Application Load Balancer

Suppose your ALB has:

```text
DNS name:
my-app-alb-123456.us-east-1.elb.amazonaws.com
```

Its Route 53 hosted zone ID is:

```text
Z35SXDOTRQ7X7K
```

You can configure:

```text
example.com  A (Alias)  my-app-alb-123456.us-east-1.elb.amazonaws.com
```

Notice that the target hosted zone ID is the ALB's canonical hosted zone ID, not your Route 53 domain's hosted zone ID.

For an actual deployment, retrieve both values from the ALB resource instead of hardcoding them.

### 7.5 Apex Domain Restrictions

Consider:

```text
example.com
```

This is the zone apex.

A CNAME at the apex is not permitted because the apex must also contain SOA and NS records.

However, you can configure:

```text
example.com       A (Alias)      ALB
www.example.com   CNAME          example.com
```

This is one of the major advantages of Route 53 Alias records.

### 7.6 Evaluate Target Health

Alias records support the `EvaluateTargetHealth` property.

When enabled, Route 53 evaluates the health of the referenced AWS resource where supported.

For an ALB, the health evaluation considers the associated target groups:

* A target group with registered targets must have at least one healthy target.

* A target group containing only unhealthy targets can make the ALB unhealthy.

* A target group with no registered targets is considered unhealthy.

This is particularly important when Alias records are combined with failover or weighted routing policies. Amazon Route 53 +2

### 8\. Simple and Weighted DNS Record Configurations

Route 53 supports different routing policies. We will explore simple and weighted configurations here; advanced routing policies will be covered in Module 3.

### 8.1 Simple Routing

Simple routing returns a single DNS answer or a configured set of answers.

Example:

```text
api.example.com
    |
    v
192.0.2.10
```

You can also configure multiple values for a simple record:

```text
api.example.com A 192.0.2.10
api.example.com A 192.0.2.20
```

However, simple routing does not provide controlled percentage-based traffic distribution.

### 8.2 Weighted Routing

Weighted routing allows you to distribute DNS responses across multiple resources according to configured weights.

Suppose you have two application environments:

| Environment | Weight |
| ----------- | ------ |
| Production  | 90     |
| New version | 10     |

The approximate DNS response distribution is:

* Production: 90%.

* New version: 10%.

Example architecture:

![Blue/Green Deployment on AWS Elastic Load Balancer](https://images.openai.com/static-rsc-4/qxiIuRBW7ll8BR8QZ0_RGUqrij4JM0N7Plb0QrF41Te3sE1nccTjTw0FrWFouyHErirAZL6P4eh9xsVTzTorQooyXGtZMLr0ZPkRL5ab4YQkFGnHAYkpDU8t1CvhYYpF3c6s4l7mAyQZlBtTUH8SgJF-ZoY6lj2cbmggD2G5rv77rcrjxZTLY8uqKqx-btJW?purpose=fullsize)

Weighted routing is useful for:

* Blue-green deployments.

* Canary releases.

* Gradual traffic migration.

* Splitting traffic between application versions.

Important considerations:

* Weighted records with the same name and type need unique set identifiers.

* Weights are relative values, not absolute percentages.

* A weight of zero stops normal traffic selection for that record, subject to routing and health-check behavior.

* DNS caching means the actual application request distribution may differ from configured weights.

For example, weights of 90 and 10 produce a 90/10 selection ratio, while weights of 9 and 1 represent the same ratio.

### 9\. Route 53 with Pulumi (Python)

Now we will manage hosted zones and DNS records using Pulumi.

### 9.1 Project Structure

Create a new Pulumi project:

```bash
mkdir route53-hosted-zones
cd route53-hosted-zones

pulumi new aws-python
```

Recommended structure:

```text
route53-hosted-zones/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
├── __main__.py
└── components/
    ├── __init__.py
    └── dns.py
```

Install dependencies:

```bash
python -m pip install pulumi pulumi-aws
```

For reproducible deployments, pin compatible package versions in `requirements.txt`.

### 9.2 Create a Public Hosted Zone

In `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

domain_name = config.require("domainName")

public_zone = aws.route53.Zone(
    "public-zone",
    name=domain_name,
    comment="Public DNS hosted zone managed by Pulumi",
)

pulumi.export("public_zone_id", public_zone.zone_id)
pulumi.export("name_servers", public_zone.name_servers)
```

Configure the domain:

```bash
pulumi config set domainName example.com
```

Preview the deployment:

```bash
pulumi preview
```

Deploy:

```bash
pulumi up
```

Retrieve the hosted zone information:

```bash
pulumi stack output public_zone_id
pulumi stack output name_servers
```

Important: Creating this zone does not automatically update your registrar's delegation. You must configure the assigned name servers at the registrar.

### 9.3 Create DNS Records

Add the following to `__main__.py`:

```python
www_record = aws.route53.Record(
    "www-record",
    zone_id=public_zone.zone_id,
    name=f"www.{domain_name}",
    type="CNAME",
    ttl=300,
    records=[domain_name],
)

api_record = aws.route53.Record(
    "api-record",
    zone_id=public_zone.zone_id,
    name=f"api.{domain_name}",
    type="A",
    ttl=300,
    records=["192.0.2.10"],
)

ipv6_record = aws.route53.Record(
    "ipv6-record",
    zone_id=public_zone.zone_id,
    name=f"ipv6.{domain_name}",
    type="AAAA",
    ttl=300,
    records=["2001:db8::10"],
)
```

For TXT records:

```python
verification_record = aws.route53.Record(
    "verification-record",
    zone_id=public_zone.zone_id,
    name=domain_name,
    type="TXT",
    ttl=300,
    records=['"verification-token=abc123"'],
)
```

For MX records:

```python
mx_record = aws.route53.Record(
    "mx-record",
    zone_id=public_zone.zone_id,
    name=domain_name,
    type="MX",
    ttl=300,
    records=[
        "10 mail1.example.net",
        "20 mail2.example.net",
    ],
)
```

For CAA records:

```python
caa_record = aws.route53.Record(
    "caa-record",
    zone_id=public_zone.zone_id,
    name=domain_name,
    type="CAA",
    ttl=300,
    records=[
        '0 issue "letsencrypt.org"',
    ],
)
```

The examples use documentation IP addresses and illustrative DNS values. Replace them with valid endpoints and records for your environment.

TXT record detail: Route 53 TXT values require correct quoting and escaping. Long TXT values can also be split into multiple character strings according to DNS TXT record conventions.

### 9.4 Create a Private Hosted Zone

Suppose you already have a VPC.

You can retrieve it using Pulumi:

```python
vpc = aws.ec2.get_vpc(
    default=True,
)
```

Create a private hosted zone:

```python
private_zone = aws.route53.Zone(
    "private-zone",
    name="internal.example.com",
    vpcs=[
        aws.route53.ZoneVpcArgs(
            vpc_id=vpc.id,
            vpc_region=aws.get_region().region,
        )
    ],
    comment="Internal DNS namespace",
)
```

Create an internal record:

```python
database_record = aws.route53.Record(
    "database-record",
    zone_id=private_zone.zone_id,
    name="database.internal.example.com",
    type="A",
    ttl=60,
    records=["10.0.10.25"],
)
```

Export the private zone ID:

```python
pulumi.export("private_zone_id", private_zone.zone_id)
```

The example assumes the VPC is in the AWS region selected by your Pulumi AWS provider.

### 9.5 Configure Alias Records for an ALB

Suppose an ALB is already managed by Pulumi or retrieved from AWS.

You need two values:

* The ALB DNS name.

* The ALB canonical hosted zone ID.

Example:

```python
alb = aws.lb.get_load_balancer(
    name="my-app-alb",
)
```

Create the Alias record:

```python
alb_alias = aws.route53.Record(
    "alb-alias",
    zone_id=public_zone.zone_id,
    name=domain_name,
    type="A",
    aliases=[
        aws.route53.RecordAliasArgs(
            name=alb.dns_name,
            zone_id=alb.zone_id,
            evaluate_target_health=True,
        )
    ],
)
```

This creates:

```text
example.com → ALB
```

Notice that we use:

```python
zone_id=alb.zone_id
```

inside the Alias configuration.

This is the ALB's canonical hosted zone ID, which is different from:

```python
zone_id=public_zone.zone_id
```

The latter identifies the hosted zone in which the record is created.

For an ALB that does not have healthy registered targets, target-health evaluation can affect DNS responses. Do not enable it blindly in a production deployment without considering your routing architecture.

### 9.6 Pulumi Stack Outputs

You can export DNS infrastructure information:

```python
pulumi.export("domain_name", domain_name)

pulumi.export(
    "public_zone_id",
    public_zone.zone_id,
)

pulumi.export(
    "public_name_servers",
    public_zone.name_servers,
)

pulumi.export(
    "private_zone_id",
    private_zone.zone_id,
)
```

Other Pulumi stacks can retrieve these outputs using `StackReference`.

For example:

```python
network_stack = pulumi.StackReference(
    "organization/network/dev"
)

vpc_id = network_stack.require_output("vpc_id")
```

This allows the DNS stack to consume infrastructure created by a separate networking stack rather than duplicating resources.

Pulumi resource reference: [AWS Route 53 Record resource documentation](https://www.pulumi.com/registry/packages/aws%406.x/api-docs/route53/record/?utm_source=chatgpt.com).

### 10\. Managing DNS Records with AWS CLI

Pulumi is our primary infrastructure management tool, but AWS CLI is useful for inspecting resources, debugging, and performing controlled DNS changes.

### 10.1 List DNS Records

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789ABCDEFG \
  --output table
```

Filter records by type:

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789ABCDEFG \
  --query "ResourceRecordSets[?Type=='A']"
```

### 10.2 Create or Update Records

Route 53 uses `UPSERT` to create a record or update an existing record with the same identity.

Create a JSON file:

`change-record.json`

```json
{
  "Comment": "Update application DNS record",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "192.0.2.50"
          }
        ]
      }
    }
  ]
}
```

Apply the change:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789ABCDEFG \
  --change-batch file://change-record.json
```

### 10.3 Delete Records

To delete a record, provide the same record identity and values that currently exist.

Example:

```json
{
  "Changes": [
    {
      "Action": "DELETE",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "192.0.2.50"
          }
        ]
      }
    }
  ]
}
```

Execute:

```bash
aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789ABCDEFG \
  --change-batch file://delete-record.json
```

### 10.4 Monitor DNS Change Propagation

Route 53 returns a change ID when you submit a DNS change.

Check its status:

```bash
aws route53 get-change \
  --id /change/C123456789
```

Possible statuses include:

* `PENDING`

* `INSYNC`

`INSYNC` means the change has propagated to Route 53's authoritative DNS infrastructure. It does not mean every recursive resolver worldwide has discarded its cached responses.

### 10.5 Bash DNS Diagnostic Script

Create `dns-check.sh`:

```bash
#!/usr/bin/env bash

set -euo pipefail

DOMAIN="${1:?Usage: ./dns-check.sh <domain>}"

RECORD_TYPES=(
    A
    AAAA
    CNAME
    MX
    TXT
    NS
    SOA
    CAA
)

echo "DNS diagnostics for: ${DOMAIN}"
echo "================================"

for TYPE in "${RECORD_TYPES[@]}"; do
    echo
    echo "Record type: ${TYPE}"
    dig "${DOMAIN}" "${TYPE}" +noall +answer
done

echo
echo "================================"
echo "Authoritative DNS trace"
dig +trace "${DOMAIN}"
```

Make it executable:

```bash
chmod +x dns-check.sh
```

Run:

```bash
./dns-check.sh example.com
```

This script provides a quick overview of DNS records and the delegation chain.

### 11\. Importing Existing Route 53 Resources into Pulumi

In real AWS environments, DNS infrastructure often already exists.

You might have hosted zones created through:

* AWS Management Console.

* AWS CLI.

* CloudFormation.

* Another infrastructure automation tool.

* Manual administrative operations.

Recreating these resources through Pulumi is generally unnecessary and potentially dangerous.

Instead, you can import existing resources into Pulumi state.

### 11.1 What Is Resource Import?

Importing allows Pulumi to adopt an existing cloud resource and manage it through infrastructure as code.

The process is:

* Identify the existing AWS resource.

* Retrieve its resource ID.

* Define the corresponding resource in Pulumi.

* Import it into Pulumi state.

* Compare the declared configuration with the actual configuration.

* Resolve any differences before making changes.

Import does not create a new hosted zone.

### 11.2 Find an Existing Hosted Zone

List hosted zones:

```bash
aws route53 list-hosted-zones \
  --output table
```

Find a particular hosted zone:

```bash
aws route53 list-hosted-zones-by-name \
  --dns-name example.com
```

Inspect it:

```bash
aws route53 get-hosted-zone \
  --id Z123456789ABCDEFG
```

### 11.3 Import a Hosted Zone

Pulumi supports importing Route 53 hosted zones using their hosted zone IDs.

Command:

```bash
pulumi import \
  aws:route53/zone:Zone \
  imported-zone \
  Z123456789ABCDEFG
```

The command imports the existing zone under the logical Pulumi resource name `imported-zone`.

Alternatively, you can declare the resource directly in Python using an import option:

```python
import pulumi
import pulumi_aws as aws

existing_zone = aws.route53.Zone(
    "imported-zone",
    name="example.com",
    opts=pulumi.ResourceOptions(
        import_="Z123456789ABCDEFG",
    ),
)

pulumi.export("zone_id", existing_zone.zone_id)
```

After importing, review the generated state and configuration carefully.

### 11.4 Import Existing DNS Records

You can also import individual DNS records.

For example:

```bash
pulumi import \
  aws:route53/record:Record \
  imported-api-record \
  Z123456789ABCDEFG_api.example.com_A
```

The record import identity contains:

```text
HOSTED_ZONE_ID_RECORD_NAME_RECORD_TYPE
```

For records with a routing-policy set identifier, append that identifier.

For example:

```bash
pulumi import \
  aws:route53/record:Record \
  imported-weighted-record \
  Z123456789ABCDEFG_api.example.com_A_production
```

### 11.5 Important Import Considerations

Importing a hosted zone does not automatically mean every record inside it is managed by Pulumi.

You must explicitly import the individual records you want Pulumi to manage.

Also:

* Match existing TTLs and record values.

* Preserve existing routing policies.

* Avoid accidentally replacing existing records.

* Be especially careful with NS and SOA records.

* Inspect `pulumi preview` before applying changes.

* Keep a backup of the existing DNS configuration.

A useful inspection command is:

```bash
pulumi preview
```

Your objective is to reach a state where Pulumi understands the existing infrastructure without proposing unintended replacements or deletions.

Pulumi documentation:

* [AWS Route 53 Zone resource and import](https://www.pulumi.com/registry/packages/aws/api-docs/route53/zone/?utm_source=chatgpt.com)

* [AWS Route 53 Record resource and import](https://www.pulumi.com/registry/packages/aws%406.x/api-docs/route53/record/?utm_source=chatgpt.com)

* [Pulumi resource import concepts](https://www.pulumi.com/docs/iac/concepts/resources/options/import/?utm_source=chatgpt.com)

### 12\. Managing Hosted Zones Across Multiple Pulumi Stacks

As infrastructure grows, managing everything in one Pulumi project becomes difficult.

A better approach is to separate networking, DNS, and application infrastructure into independent stacks.

### 12.1 Example Architecture

```text
AWS Infrastructure
│
├── Network Project
│   ├── dev stack
│   └── prod stack
│
├── DNS Project
│   ├── dev stack
│   └── prod stack
│
└── Application Project
    ├── dev stack
    └── prod stack
```

Responsibilities:

| Project     | Responsibility                                 |
| ----------- | ---------------------------------------------- |
| Network     | VPCs, subnets, routing, NAT                    |
| DNS         | Public/private hosted zones and DNS records    |
| Application | ALBs, ECS services, application infrastructure |

### 12.2 Share Infrastructure Outputs

Suppose your network stack exports:

```python
pulumi.export("vpc_id", vpc.id)
pulumi.export("private_subnet_ids", private_subnet_ids)
```

Your DNS stack can retrieve the VPC ID:

```python
network = pulumi.StackReference(
    "organization/network/dev"
)

vpc_id = network.require_output("vpc_id")
```

You can then use the exported VPC ID when creating a private hosted zone.

Similarly, an application stack can export:

```python
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("alb_zone_id", alb.zone_id)
```

The DNS stack can consume these values to create Alias records.

### 12.3 Environment-Specific DNS

Use separate Pulumi stacks for development and production.

For example:

```text
dev:
  dev.example.com

prod:
  example.com
  api.example.com
```

Set environment-specific configuration:

```bash
pulumi stack select dev

pulumi config set domainName dev.example.com
```

For production:

```bash
pulumi stack select prod

pulumi config set domainName example.com
```

This approach makes it easier to manage DNS changes independently across environments.

### 12.4 Avoiding Cross-Stack Resource Conflicts

A critical rule:

One Pulumi resource should have one authoritative owner.

For example, if the DNS stack manages `api.example.com`, avoid having the application stack independently manage the same record.

Otherwise, multiple stacks may attempt to modify the same DNS record, creating unpredictable infrastructure drift.

Use `StackReference` to share outputs instead of managing the same resources from multiple stacks.

### 13\. Hands-on Labs

The following labs progressively build a DNS environment using Pulumi and AWS CLI.

### Lab 1 — Register or Use an Existing Domain

Objective: Prepare a domain for Route 53 DNS management.

Tasks:

* Register a domain through Route 53 or use an existing domain.

* Create a public hosted zone.

* Retrieve its four assigned authoritative name servers.

* Configure the name servers at your registrar.

* Verify domain delegation using `dig`.

* Inspect the hosted zone's default NS and SOA records.

Verification:

```bash
dig NS example.com
dig SOA example.com
dig +trace example.com
```

### Lab 2 — Create Public and Private Hosted Zones

Objective: Understand public and private DNS namespaces.

Tasks:

* Create a VPC using Pulumi or reuse an existing VPC.

* Enable VPC DNS support and DNS hostnames.

* Create a public hosted zone.

* Create a private hosted zone.

* Associate the private zone with the VPC.

* Create internal DNS records.

* Verify public and private DNS resolution.

Verification:

```bash
aws route53 list-hosted-zones

aws route53 get-hosted-zone \
  --id Z123456789ABCDEFG
```

From an EC2 instance inside the VPC:

```bash
dig database.internal.example.com
```

### Lab 3 — Configure DNS Record Types

Objective: Work with commonly used DNS records.

Tasks:

* Create A and AAAA records.

* Create CNAME records for application subdomains.

* Configure MX records for a mail domain.

* Publish TXT records for domain verification.

* Configure CAA records.

* Inspect all records using AWS CLI.

* Verify DNS responses using `dig`.

Use Pulumi to manage all records.

### Lab 4 — Configure Alias Records for an ALB

Objective: Connect Route 53 to an application endpoint.

![aws-route53-alb - AWS Solutions Constructs](https://images.openai.com/static-rsc-4/5xrrYuT8qTREh0Z6Z--Ti10Ydor5sLPxmgsxReOIVh1ZeCA2QjT_frc_RNyGIgMWnuJZjC-csgxXu9eNYGCqDftNwra2fQ-tCH0uoMkCXPBFtofeTWvdE6VuGDm0OnYkaMWtfHJzIrjklparTHjBs-FBxrq-Itq9wt7cSPEHZxOf3x0KY4kyy-_gtCNp9G4-?purpose=fullsize)

Tasks:

* Create an Application Load Balancer.

* Configure a target group and register application targets.

* Verify target health.

* Retrieve the ALB DNS name and canonical hosted zone ID.

* Create an Alias A record for the root domain.

* Create a CNAME record for `www`.

* Enable target-health evaluation.

* Test application access through the domain.

Verification:

```bash
dig example.com

curl -I https://example.com
```

### Lab 5 — Delegate a Subdomain

Objective: Understand parent-child DNS delegation.

Tasks:

* Create a parent hosted zone: `example.com`.

* Create a child hosted zone: `dev.example.com`.

* Retrieve the child zone's name servers.

* Create NS records in the parent zone.

* Create A and CNAME records in the child zone.

* Verify delegation.

* Inspect the resolution chain.

Verification:

```bash
dig NS dev.example.com

dig api.dev.example.com

dig +trace api.dev.example.com
```

### Lab 6 — Manage DNS Records with AWS CLI and Pulumi

Objective: Understand DNS record lifecycle management.

Tasks:

* Create records using AWS CLI.

* Update records using `UPSERT`.

* Delete records using `DELETE`.

* Inspect Route 53 change IDs.

* Monitor change propagation.

* Reconcile DNS configuration with Pulumi.

* Identify and resolve infrastructure drift.

Write Bash scripts to automate DNS inspection and record management.

### Lab 7 — Import Existing Hosted Zones into Pulumi

Objective: Adopt existing DNS infrastructure without recreating it.

Tasks:

* Create a hosted zone manually through AWS Console or AWS CLI.

* Inspect its configuration and records.

* Retrieve its hosted zone ID.

* Import it into Pulumi.

* Import selected DNS records.

* Reconstruct the Pulumi resource declarations.

* Run `pulumi preview`.

* Resolve configuration differences without unintentionally replacing DNS resources.

### 14\. Important Commands Reference

| Task                   | Command                                 |
| ---------------------- | --------------------------------------- |
| List hosted zones      | aws route53 list-hosted-zones           |
| Inspect hosted zone    | aws route53 get-hosted-zone             |
| List DNS records       | aws route53 list-resource-record-sets   |
| Create/update records  | aws route53 change-resource-record-sets |
| Check DNS changes      | aws route53 get-change                  |
| Inspect domain         | aws route53domains get-domain-detail    |
| Inspect name servers   | dig NS example.com                      |
| Trace DNS resolution   | dig +trace example.com                  |
| Inspect A record       | dig A example.com                       |
| Inspect MX records     | dig MX example.com                      |
| Preview infrastructure | pulumi preview                          |
| Deploy infrastructure  | pulumi up                               |
| Import hosted zone     | pulumi import                           |
| Inspect stack outputs  | pulumi stack output                     |

### 15\. Cleanup and Resource Management

After completing the labs:

* Remove temporary DNS records.

* Remove child hosted zones after removing their parent delegation records.

* Disassociate VPCs from private hosted zones before deleting the zones when necessary.

* Delete temporary hosted zones.

* Remove temporary ALBs and target groups.

* Remove unused VPC resources.

* Verify that no unintended domain registration or renewal remains.

Example:

```bash
pulumi destroy
```

Do not destroy a production hosted zone or change registrar delegation as part of cleanup. Domain registration and hosted zone deletion are separate operations.

### 16\. Official Documentation and References

These are the primary references for this module:

* [Working with hosted zones — AWS](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-working-with.html?utm_source=chatgpt.com)

* [Supported DNS record types — AWS](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ResourceRecordTypes.html?utm_source=chatgpt.com)

* [Routing traffic to an ELB load balancer](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-to-elb-load-balancer.html?utm_source=chatgpt.com)

* [Private hosted zone considerations](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zone-private-considerations.html?utm_source=chatgpt.com)

* [Registering and managing domains](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/domain-register.html?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 Zone](https://www.pulumi.com/registry/packages/aws/api-docs/route53/zone/?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 Record](https://www.pulumi.com/registry/packages/aws%406.x/api-docs/route53/record/?utm_source=chatgpt.com)

* [Pulumi resource import](https://www.pulumi.com/docs/iac/concepts/resources/options/import/?utm_source=chatgpt.com)

### Module 2 — Completion

By completing this module, you should be comfortable managing Route 53 hosted zones, configuring DNS records, connecting domains to AWS services, and adopting existing DNS infrastructure with Pulumi.

Next module: Module 3 — Route 53 Routing Policies.

We will build on the hosted zones and DNS records from this module to explore simple, weighted, latency-based, failover, geolocation, geoproximity, IP-based, and multivalue answer routing.
