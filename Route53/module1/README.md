Worked for 1m 9s

### Module 1 — DNS Fundamentals and Route 53 Architecture

### 1\. Learning Objectives

By the end of this module, you will be able to:

* Explain how DNS translates domain names into IP addresses.

* Understand DNS hierarchy, zones, resolvers, and authoritative name servers.

* Trace the complete DNS resolution process.

* Understand common DNS record types and their purposes.

* Explain TTL, caching, negative caching, and DNS propagation.

* Distinguish public DNS from private DNS.

* Understand Amazon Route 53 architecture and its major components.

* Explain how hosted zones, name servers, and domain registration work.

* Understand the role of Route 53 Resolver.

* Explain DNS communication over UDP and TCP port 53.

* Understand Route 53 pricing fundamentals.

* Create and manage a public hosted zone using Pulumi.

### 2\. DNS Fundamentals

### 2.1 What Is DNS?

The Domain Name System (DNS) is a distributed, hierarchical naming system that translates human-readable domain names into information that computers can use to communicate.

For example, when you access:

```text
https://www.example.com
```

Your browser needs to determine the IP address associated with `www.example.com`.

DNS performs this translation:

```text
www.example.com → 93.184.216.34
```

Without DNS, users would need to remember IP addresses instead of domain names.

DNS is not limited to translating names into IPv4 addresses. It also supports:

* IPv6 address resolution.

* Mail server discovery.

* Domain ownership verification.

* Service discovery.

* DNS-based traffic management.

* Domain authentication and security policies.

### 2.2 DNS Is a Distributed Hierarchical System

DNS does not rely on a single central database. Its namespace is distributed across multiple administrative levels.

Consider:

```text
api.dev.example.com.
```

Its hierarchy is:

| Component | Description            |
| --------- | ---------------------- |
| .         | DNS root               |
| com       | Top-level domain (TLD) |
| example   | Second-level domain    |
| dev       | Subdomain              |
| api       | Hostname               |

The trailing dot represents the DNS root. It is usually omitted in everyday usage.

### 2.3 DNS Namespace Hierarchy

The DNS namespace is organized into a tree.

Root (`.`)

com

org

net

example.com

www.example.com

api.example.com

Important concepts:

* Root domain: The top of the DNS hierarchy.

* TLD: A top-level domain such as `.com`, `.org`, or `.net`.

* Second-level domain: A registered domain such as `example.com`.

* Subdomain: A child namespace such as `api.example.com`.

* Fully Qualified Domain Name (FQDN): A complete domain name identifying a specific node in the DNS hierarchy.

### 2.4 DNS Zones and Delegation

A DNS zone is an administratively managed portion of the DNS namespace.

For example, an organization may manage:

```text
example.com
```

And delegate:

```text
dev.example.com
```

to another DNS administrator.

The parent zone contains delegation records pointing to the child zone's authoritative name servers.

Example:

```text
example.com
    |
    +-- www.example.com
    |
    +-- api.example.com
    |
    +-- dev.example.com  → Delegated zone
                               |
                               +-- app.dev.example.com
                               +-- db.dev.example.com
```

This distinction is important:

* A domain is a name in the DNS hierarchy.

* A zone is the administrative portion served by a set of authoritative DNS servers.

* A hosted zone is AWS's managed implementation of a DNS zone.

A zone does not necessarily contain every name beneath its domain. Delegation can divide the namespace into independently managed zones.

### 3\. DNS Resolvers and Name Servers

### 3.1 Stub Resolver

A stub resolver is the DNS client component on an operating system.

When an application requests:

```text
www.example.com
```

The operating system's resolver sends a query to a configured recursive DNS resolver.

The stub resolver generally does not perform the complete DNS hierarchy traversal itself.

Examples of DNS client tools:

```bash
dig www.example.com
nslookup www.example.com
host www.example.com
```

### 3.2 Recursive DNS Resolver

A recursive resolver performs the work of resolving a DNS query on behalf of a client.

It may:

* Check its local cache.

* Query a root name server.

* Query a TLD name server.

* Query the authoritative name server.

* Cache the response.

* Return the result to the client.

Examples of recursive resolvers include:

* Google Public DNS: `8.8.8.8`

* Cloudflare DNS: `1.1.1.1`

* Quad9: `9.9.9.9`

* ISP-provided DNS resolvers.

### 3.3 Root Name Servers

Root name servers operate at the top of the DNS hierarchy.

They do not normally provide the final IP address for a domain. Instead, they provide referrals to the appropriate TLD name servers.

For example:

```text
Query: www.example.com

Root server:
    "Ask the .com TLD name servers."
```

### 3.4 TLD Name Servers

TLD name servers manage information about domains within a top-level domain.

For example, `.com` name servers know which authoritative name servers are responsible for `example.com`.

They provide a referral to those authoritative servers.

### 3.5 Authoritative Name Servers

An authoritative name server stores or serves DNS information for a particular zone.

For example:

```text
example.com
```

Its authoritative server may provide:

```text
www.example.com → 203.0.113.10
```

Amazon Route 53 public hosted zones use authoritative name servers operated by AWS.

### 3.6 Recursive vs. Iterative DNS Queries

These are two important query behaviors.

| Feature               | Recursive query                  | Iterative query                     |
| --------------------- | -------------------------------- | ----------------------------------- |
| Expected response     | Final answer or failure          | Best available answer/referral      |
| Client responsibility | Resolver performs resolution     | Requester follows referrals         |
| Typical use           | Client to recursive resolver     | Recursive resolver to DNS hierarchy |
| Referrals             | Resolver handles them internally | Returned to requester               |

A typical DNS resolution flow is:

```text
Client
  |
  | Recursive query
  v
Recursive Resolver
  |
  | Iterative query
  v
Root Name Server
  |
  | Referral to .com
  v
TLD Name Server
  |
  | Referral to example.com
  v
Authoritative Name Server
  |
  | Final DNS answer
  v
Recursive Resolver
  |
  | Final answer
  v
Client
```

### 4\. DNS Record Types

DNS records associate names with different types of information.

### 4.1 A Record

Maps a hostname to an IPv4 address.

```dns
www.example.com.  300  IN  A  203.0.113.10
```

Common use cases:

* Web servers.

* Application servers.

* IPv4 endpoints.

### 4.2 AAAA Record

Maps a hostname to an IPv6 address.

```dns
www.example.com.  300  IN  AAAA  2001:db8::10
```

Used when applications support IPv6 connectivity.

### 4.3 CNAME Record

Creates an alias from one DNS name to another.

```dns
www.example.com.  300  IN  CNAME  example.com.
```

Important characteristics:

* Points to another domain name, not an IP address.

* The resolver follows the alias to obtain the final record.

* A CNAME cannot coexist with other ordinary record types at the same DNS name.

* A conventional CNAME cannot be used at the zone apex.

Route 53 supports Alias records, which provide an AWS-specific alternative for supported targets, including at the zone apex.

### 4.4 MX Record

Specifies mail servers responsible for receiving email.

```dns
example.com.  300  IN  MX  10 mail.example.com.
```

The number represents priority. Lower values have higher priority.

### 4.5 TXT Record

Stores arbitrary text associated with a DNS name.

Example:

```dns
example.com.  300  IN  TXT  "v=spf1 include:example.net -all"
```

Common applications:

* SPF records.

* Domain ownership verification.

* DKIM-related DNS information.

* DMARC policies.

* Application configuration.

### 4.6 NS Record

Identifies authoritative name servers for a DNS zone.

```dns
example.com.  IN  NS  ns-123.awsdns-45.com.
```

Route 53 creates NS records for public hosted zones.

### 4.7 SOA Record

The Start of Authority record contains administrative information about a DNS zone.

Example:

```dns
example.com. IN SOA ns-123.awsdns-45.com. awsdns-hostmaster.amazon.com. (
    1
    7200
    900
    1209600
    86400
)
```

The fields include:

* Primary name server.

* Responsible party's email address, represented in DNS notation.

* Serial number.

* Refresh interval.

* Retry interval.

* Expiration interval.

* Negative caching TTL.

### 4.8 SRV Record

Specifies the location of a service.

```dns
_sip._tcp.example.com. 300 IN SRV 10 60 5060 sip.example.com.
```

The fields represent:

```text
Priority Weight Port Target
```

SRV records are used by applications that need service discovery.

### 4.9 CAA Record

Specifies which certificate authorities are authorized to issue TLS certificates for a domain.

```dns
example.com. 300 IN CAA 0 issue "letsencrypt.org"
```

CAA records help control certificate issuance.

### 4.10 Summary

| Record | Purpose                             |
| ------ | ----------------------------------- |
| A      | IPv4 address                        |
| AAAA   | IPv6 address                        |
| CNAME  | Alias to another DNS name           |
| MX     | Mail server discovery               |
| TXT    | Text and domain verification        |
| NS     | Authoritative name servers          |
| SOA    | Zone administrative information     |
| SRV    | Service discovery                   |
| CAA    | Certificate authority authorization |

Important Route 53 consideration: Route 53 supports these standard record types, but some records have AWS-specific configuration requirements and limitations. We will explore Alias records and routing policies in later modules.

### 5\. DNS TTL, Caching, and Propagation

### 5.1 What Is TTL?

TTL stands for Time to Live.

It specifies how long a DNS response can remain cached before the resolver should consider it expired.

Example:

```dns
www.example.com.  300  IN  A  203.0.113.10
```

The TTL is 300 seconds, meaning five minutes.

If a recursive resolver caches this answer, it can reuse it until the TTL expires.

### 5.2 DNS Caching

DNS caching reduces:

* DNS query volume.

* Resolution latency.

* Load on authoritative name servers.

* Network traffic.

There are several places where DNS responses can be cached:

* Browser DNS cache.

* Operating system DNS cache.

* Recursive resolver cache.

* Intermediate DNS infrastructure caches.

### 5.3 Positive and Negative Caching

Positive caching occurs when a resolver stores a successful DNS response.

For example:

```text
www.example.com → 203.0.113.10
```

Negative caching occurs when a resolver caches information indicating that a requested DNS name or record does not exist.

For example:

```text
unknown.example.com → NXDOMAIN
```

Negative caching is controlled by DNS specifications and the zone's SOA information.

A nonexistent record can therefore continue to appear nonexistent to a resolver even after you create it.

### 5.4 DNS Propagation

DNS propagation is commonly used to describe the time required for DNS changes to become visible across different resolvers.

Technically, there is no single global propagation event.

When you change a record:

* The authoritative DNS data is updated.

* Existing cached responses may remain valid.

* Different recursive resolvers may observe the change at different times.

* Negative caches may delay visibility of newly created records.

For example:

```text
Before:
www.example.com → 203.0.113.10

After:
www.example.com → 203.0.113.20
```

A resolver with an existing cached answer may continue returning the old address until its cached TTL expires.

### 5.5 TTL Design Considerations

| TTL           | Typical use                  |
| ------------- | ---------------------------- |
| 30–60 seconds | Rapidly changing DNS records |
| 300 seconds   | Frequently updated records   |
| 3600 seconds  | Relatively stable records    |
| 86400 seconds | Very stable records          |

These are illustrative choices, not universal requirements.

Low TTL values provide greater flexibility but increase DNS query volume. High TTL values improve caching efficiency but can delay the visibility of changes.

Route 53 note: Changing a record's TTL does not retroactively change the TTL of responses already cached by recursive resolvers.

### 6\. Public DNS vs. Private DNS

### 6.1 Public DNS

Public DNS records are available through publicly accessible DNS infrastructure.

For example:

```text
www.example.com → 203.0.113.10
```

A public hosted zone in Route 53 serves authoritative DNS information for a domain on the public internet.

Typical applications:

* Public websites.

* APIs.

* Email infrastructure.

* Public application load balancers.

* CloudFront distributions.

### 6.2 Private DNS

Private DNS provides name resolution within private network environments.

For example:

```text
api.internal.example.com → 10.0.1.10
db.internal.example.com  → 10.0.2.20
```

These records can be made available through a Route 53 private hosted zone associated with one or more VPCs.

Typical applications:

* Internal APIs.

* Databases.

* Microservices.

* Private load balancers.

* Internal application infrastructure.

### 6.3 Comparison

| Feature             | Public hosted zone       | Private hosted zone                     |
| ------------------- | ------------------------ | --------------------------------------- |
| Visibility          | Public DNS               | Associated VPCs and configured networks |
| Typical IPs         | Public endpoints         | Private endpoints                       |
| VPC association     | Not required             | Required                                |
| Internet resolution | Publicly resolvable      | Not directly publicly resolvable        |
| Common use          | Websites and public APIs | Internal services                       |

![](https://images.openai.com/static-rsc-4/O9eVrNfKAEppbi8zVQBNMn9aYNemaepw84Aoe6s5uhfQz-aGdq2dkeznACZqTvsXnNJ5AG5RxH5-GAdzKfLmFunfIwlYfb2KKg-NYcXrYNyUFzMJg4000QAb1k95OnS9ZKuuuhcxpqo1OoCSfYVRW6Qj_XD7Nf7bVB9FpSwPm8CAkqKXy0cvRf2DcWchlfK4?purpose=fullsize)

### 6.4 Split-Horizon DNS

Split-horizon DNS allows the same domain name to return different answers depending on where the query originates.

For example:

```text
Public DNS:
api.example.com → 198.51.100.10

Private DNS:
api.example.com → 10.0.1.10
```

This is useful when a company wants:

* Public users to access an external application endpoint.

* Internal users to access a private application endpoint.

Route 53 supports this architecture using public and private hosted zones.

### 7\. Amazon Route 53 Architecture

### 7.1 What Is Amazon Route 53?

Amazon Route 53 is AWS's highly available and scalable DNS service.

It provides several capabilities:

* Domain registration.

* DNS hosting.

* DNS resolution.

* DNS-based traffic routing.

* Health checks.

* Private DNS.

* Hybrid DNS integration.

The name Route 53 refers to DNS's standard network port, 53.

### 7.2 Route 53 Major Components

![How DNS Works in AWS – Route 53 Explained](https://images.openai.com/static-rsc-4/uw6pGaTtaQ4HcJFG97wbhhGYVVJ_A38rEsXNDEiCqCS1TsawbgD67--9eA-M48_3Mjr_uhHYT6nMpOE9DCxqd9vTQrMcrYbjCLhLIi5pxcw32u2A7eZEhU0rUHCBqQl4wWhUi-15zO2ST3uARlwGuiX7AnGva6K1Y4ImHIsDgiM12MQcU07PXK0Xr6knF8qg?purpose=fullsize)

The major components are:

| Component           | Responsibility                                    |
| ------------------- | ------------------------------------------------- |
| Hosted zones        | Store DNS records                                 |
| Records             | Define DNS answers                                |
| Name servers        | Serve authoritative DNS responses                 |
| Route 53 Resolver   | DNS resolution within AWS and hybrid environments |
| Health checks       | Monitor endpoint availability                     |
| Routing policies    | Control DNS response selection                    |
| Domain registration | Register and manage domain names                  |

### 7.3 Hosted Zones

A hosted zone is a container for DNS records associated with a domain.

Route 53 supports two types:

Public hosted zone

Used to manage publicly resolvable DNS records.

Private hosted zone

Used to manage DNS records accessible within associated VPCs.

When creating a hosted zone, Route 53 automatically creates certain records, including:

* NS record.

* SOA record.

You can then add application-specific records.

### 7.4 Route 53 Name Servers

When you create a public hosted zone, AWS assigns four authoritative name servers.

Example:

```text
ns-123.awsdns-45.com
ns-456.awsdns-78.net
ns-789.awsdns-12.org
ns-101.awsdns-34.co.uk
```

These are illustrative names.

They serve DNS queries for your hosted zone.

If you register your domain through another registrar, you must configure the domain's delegation to point to the Route 53 name servers.

Creating a hosted zone alone does not make your domain's public DNS delegation automatically point to it.

### 7.5 Domain Registration vs. DNS Hosting

These are separate responsibilities.

| Domain registration                    | DNS hosting                           |
| -------------------------------------- | ------------------------------------- |
| Establishes control over a domain name | Stores and serves DNS records         |
| Managed through a domain registrar     | Managed through DNS hosting provider  |
| Includes registration and renewal      | Includes hosted zones and DNS queries |
| Uses registrar-level delegation        | Uses authoritative DNS servers        |

You can register a domain with one provider and host its DNS records in Route 53.

For example:

```text
Domain registrar: External registrar

DNS hosting: Amazon Route 53

Domain: example.com

Authoritative DNS:
    Route 53 name servers
```

### 7.6 Route 53 Resolver

Route 53 Resolver provides DNS resolution for AWS environments and supports integration with external DNS infrastructure.

It is important to distinguish two concepts:

* Route 53 authoritative DNS hosting: Answers queries for hosted zones.

* Route 53 Resolver: Resolves DNS queries and enables DNS forwarding between AWS and external networks.

Every VPC has a built-in Route 53 Resolver, accessible through the VPC's DNS resolver address, commonly the VPC network base address plus two.

For example:

```text
VPC CIDR: 10.0.0.0/16

VPC Resolver: 10.0.0.2
```

The built-in resolver supports queries for AWS resources and associated private hosted zones.

Later, we will explore:

* Inbound Resolver endpoints.

* Outbound Resolver endpoints.

* Conditional forwarding.

* Hybrid DNS architectures.

### 8\. DNS Transport: UDP, TCP, Port 53, and EDNS

### 8.1 UDP Port 53

DNS traditionally uses UDP port 53 for most standard queries.

Advantages:

* Low overhead.

* No connection establishment.

* Efficient for small DNS queries and responses.

Example:

```bash
dig example.com A
```

### 8.2 TCP Port 53

DNS also supports TCP port 53.

TCP is used in situations including:

* Responses that cannot be adequately handled over UDP.

* Zone transfers.

* Explicit TCP queries.

* Some DNSSEC-related responses and other large-message scenarios.

Example:

```bash
dig +tcp example.com A
```

DNS servers and resolvers must support both UDP and TCP DNS transport.

### 8.3 EDNS

EDNS (Extension Mechanisms for DNS) extends the original DNS protocol.

It allows DNS messages to carry additional capabilities, including larger UDP payload sizes and DNS-related extension information.

Without EDNS, traditional DNS messages have a 512-byte UDP size limit.

With EDNS, clients and servers can negotiate larger UDP message sizes.

This is especially important for:

* DNSSEC.

* Larger DNS responses.

* Modern DNS infrastructure.

Example:

```bash
dig example.com A +bufsize=1232
```

### 8.4 Useful DNS Diagnostic Commands

```bash
# Query an A record
dig example.com A

# Query an AAAA record
dig example.com AAAA

# Query MX records
dig example.com MX

# Query TXT records
dig example.com TXT

# Query NS records
dig example.com NS

# Query SOA records
dig example.com SOA

# Display the complete resolution trace
dig +trace example.com

# Query a specific recursive resolver
dig @1.1.1.1 example.com

# Query authoritative name servers directly
dig @ns1.example.com example.com A

# Display DNS response without additional sections
dig +noall +answer example.com

# Use TCP
dig +tcp example.com
```

Other useful commands:

```bash
nslookup example.com

host example.com

host -t MX example.com
```

### 9\. Route 53 Pricing Fundamentals

Route 53 pricing is based on several independent usage dimensions.

### 9.1 Hosted Zone Charges

Public and private hosted zones have monthly charges.

The exact cost depends on the hosted-zone type, quantity, and applicable pricing tiers.

### 9.2 DNS Query Charges

Route 53 charges for DNS queries according to query type and pricing rules.

Important considerations include:

* Standard DNS queries.

* Latency-based routing queries.

* Geolocation routing queries.

* Geoproximity routing queries.

* Health-check-related DNS behavior.

* Alias queries to supported AWS resources.

Some query categories have different pricing treatment. For example, queries to Alias records targeting certain AWS resources are not charged as ordinary standard DNS queries.

### 9.3 Health Check Charges

Route 53 health checks have separate pricing considerations.

Costs depend on the health-check configuration and applicable pricing category.

### 9.4 Resolver Charges

Route 53 Resolver features, including managed endpoints and DNS Firewall, can introduce additional charges.

For example:

* Inbound Resolver endpoints.

* Outbound Resolver endpoints.

* Resolver query processing.

* DNS Firewall rule groups and queries.

### 9.5 Pricing Summary

| Feature              | Pricing consideration                |
| -------------------- | ------------------------------------ |
| Public hosted zones  | Monthly hosted-zone charge           |
| Private hosted zones | Monthly hosted-zone charge           |
| DNS queries          | Query-based charges                  |
| Health checks        | Health-check charges                 |
| Domain registration  | Registration and renewal fees        |
| Resolver endpoints   | Endpoint and query charges           |
| DNS Firewall         | Rule group and query-related charges |

Always check the current [Amazon Route 53 pricing page](https://aws.amazon.com/route53/pricing/?utm_source=chatgpt.com) before deploying production infrastructure.

### Part 10 — Hands-on Labs

We will now implement the concepts using AWS CLI, Pulumi (Python), and Bash.

The labs will use a real AWS public hosted zone. You should have access to an AWS account and a domain you own (or a dedicated subdomain for experimentation).

Lab environment

| Component        | Configuration |
| ---------------- | ------------- |
| Operating system | Linux / WSL2  |
| Shell            | Bash          |
| Python           | Python 3      |
| AWS CLI          | AWS CLI v2    |
| IaC              | Pulumi        |
| Language         | Python        |
| AWS service      | Route 53      |
| AWS region       | us-east-1     |

Route 53 public hosted zones are global resources. The AWS provider still requires a region configuration.

Since you're working on Windows, WSL2 with Ubuntu is a convenient environment for these Bash-based labs. The same commands work on a suitable Linux environment.

### Lab 1 — Install and Configure AWS CLI and Pulumi

### Step 1.1 — Install AWS CLI v2

On Ubuntu or WSL2:

```bash
sudo apt update

sudo apt install -y \
    curl \
    unzip \
    jq \
    dnsutils \
    python3 \
    python3-venv \
    python3-pip \
    git
```

Install AWS CLI v2:

```bash
curl -fsSL https://awscli.amazonaws.com/v2/install.sh \
    | sudo bash
```

Verify:

```bash
aws --version
```

Expected output format:

```text
aws-cli/2.x.x Python/3.x.x Linux/...
```

### Step 1.2 — Configure AWS Authentication

For a learning environment, prefer AWS IAM Identity Center or another short-lived credential mechanism rather than permanent root or IAM access keys.

For IAM Identity Center:

```bash
aws configure sso
```

Follow the interactive configuration.

Then authenticate:

```bash
aws sso login --profile route53-lab
```

Set the profile for your current Bash session:

```bash
export AWS_PROFILE=route53-lab
export AWS_REGION=us-east-1
export AWS_DEFAULT_REGION="$AWS_REGION"
```

Verify your identity:

```bash
aws sts get-caller-identity
```

You should receive an account ID, ARN, and user identifier.

The identity needs permissions to manage Route 53 hosted zones and records.

### Step 1.3 — Install Pulumi

Install the Pulumi CLI:

```bash
curl -fsSL https://get.pulumi.com | sh
```

Reload your shell configuration:

```bash
source ~/.bashrc
```

Verify:

```bash
pulumi version
```

Authenticate with Pulumi Cloud:

```bash
pulumi login
```

Pulumi Cloud provides a convenient managed state backend for learning projects.

Alternatively, you can use local state:

```bash
pulumi login file://$HOME/.pulumi-local
```

### Step 1.4 — Verify the Environment

```bash
python3 --version
aws --version
pulumi version
git --version
dig -v
```

At this point, your environment is ready.

References:

* [AWS CLI installation documentation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html?utm_source=chatgpt.com)

* [Pulumi installation documentation](https://www.pulumi.com/docs/install/?utm_source=chatgpt.com)

* [Pulumi CLI reference](https://www.pulumi.com/docs/iac/cli/?utm_source=chatgpt.com)

### Lab 2 — Explore DNS Resolution Using dig, nslookup, and host

In this lab, we will investigate how DNS resolution works without creating any AWS resources.

### Step 2.1 — Query A and AAAA Records

```bash
dig example.com A

dig example.com AAAA
```

Focus on the following sections:

```text
;; QUESTION SECTION:

;; ANSWER SECTION:

;; AUTHORITY SECTION:

;; ADDITIONAL SECTION:
```

The answer section contains the returned DNS records.

### Step 2.2 — Inspect TTL

```bash
dig example.com A
```

Example answer:

```text
example.com.    300    IN    A    93.184.216.34
```

The value `300` represents the remaining TTL in seconds.

Run the query several times:

```bash
for i in {1..5}; do
    dig example.com A +noall +answer
    sleep 2
done
```

Observe how the TTL decreases when the resolver returns a cached answer.

Note that resolver behavior and cache policies can affect what you observe.

### Step 2.3 — Explore Different Record Types

```bash
dig example.com A

dig example.com AAAA

dig example.com NS

dig example.com SOA

dig example.com MX

dig example.com TXT
```

Not every domain publishes every record type.

### Step 2.4 — Identify Authoritative Name Servers

```bash
dig example.com NS
```

Choose one returned name server and query it directly:

```bash
dig @a.iana-servers.net example.com A
```

The server used here is illustrative; use an actual authoritative server returned by your query when investigating another domain.

Check the authoritative answer flag:

```text
;; flags: qr aa rd;
```

The `aa` flag indicates that the response is authoritative.

### Step 2.5 — Explore DNS Resolution Trace

```bash
dig +trace example.com A
```

This command follows the DNS delegation hierarchy.

Observe:

* Root name server responses.

* TLD name server referrals.

* Authoritative name server responses.

* Final DNS answer.

### Step 2.6 — Compare Recursive Resolvers

```bash
dig @1.1.1.1 example.com A

dig @8.8.8.8 example.com A
```

Compare:

* Answer records.

* TTL values.

* Response times.

* Resolver addresses.

* Answer and authority sections.

### Step 2.7 — Use nslookup and host

```bash
nslookup example.com

nslookup -type=NS example.com

nslookup -type=MX example.com
```

Using `host`:

```bash
host example.com

host -t AAAA example.com

host -t NS example.com

host -t SOA example.com
```

Expected result: You should be comfortable inspecting DNS responses and understanding the difference between recursive and authoritative answers.

### Lab 3 — Inspect DNS Records and Authoritative Name Servers

In this lab, we will investigate a domain's DNS configuration in more detail.

Use a domain you own if you want to perform the same investigation against your own DNS infrastructure.

### Step 3.1 — Inspect Delegation

```bash
dig example.com NS +noall +answer
```

### Step 3.2 — Inspect SOA

```bash
dig example.com SOA +noall +answer
```

Pay attention to:

* Primary name server.

* Responsible party.

* Serial number.

* Refresh interval.

* Retry interval.

* Expiration interval.

* Negative caching TTL.

### Step 3.3 — Inspect DNS Authority

```bash
dig +trace example.com
```

Then inspect a specific authoritative server:

```bash
dig @<authoritative-nameserver> example.com A
```

Replace the placeholder with a name server obtained in Step 3.1.

### Step 3.4 — Investigate Negative Responses

Query a deliberately nonexistent hostname:

```bash
dig nonexistent-12345.example.com A
```

Look for:

```text
status: NXDOMAIN
```

Inspect the authority section to understand how SOA information participates in negative caching.

### Step 3.5 — Investigate UDP and TCP

UDP query:

```bash
dig example.com A
```

TCP query:

```bash
dig +tcp example.com A
```

Compare:

```bash
dig example.com A +stats

dig +tcp example.com A +stats
```

The important difference is the transport protocol, not the DNS record itself.

### Lab 4 — Create a Public Hosted Zone Using Pulumi

Main AWS Infrastructure Lab

Now we will create our first Route 53 resource.

We will use Pulumi's AWS provider to create:

* One public hosted zone.

* One A record.

* One TXT record.

* DNS outputs containing the hosted-zone ID and authoritative name servers.

### Step 4.1 — Create the Project

Create a project directory:

```bash
mkdir route53-lab
cd route53-lab
```

Create a Python virtual environment:

```bash
python3 -m venv .venv

source .venv/bin/activate
```

Install Pulumi packages:

```bash
pip install --upgrade pip

pip install pulumi pulumi-aws
```

Create the Pulumi project:

```bash
pulumi new aws-python
```

Alternatively, if you want to create the project files manually, use the following structure:

```text
route53-lab/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── __main__.py
├── requirements.txt
└── .venv/
```

### Step 4.2 — Define the Pulumi Project

`Pulumi.yaml`:

```yaml
name: route53-lab
runtime:
  name: python
description: AWS Route 53 fundamentals lab
```

`requirements.txt`:

```text
pulumi
pulumi-aws
```

Install dependencies if you created the files manually:

```bash
pip install -r requirements.txt
```

### Step 4.3 — Create a Pulumi Stack

```bash
pulumi stack init dev
```

Configure AWS:

```bash
pulumi config set aws:region us-east-1
```

Set your domain:

```bash
pulumi config set domain YOUR_DOMAIN
```

Replace `YOUR_DOMAIN` with a domain or dedicated subdomain you control, for example:

```text
lab.example.com
```

Do not use an existing production hosted zone that you already manage independently.

### Step 4.4 — Implement the Hosted Zone

Create `__main__.py`:

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

domain = config.require("domain")

# Create a public hosted zone.
zone = aws.route53.Zone(
    "public-zone",
    name=domain,
    comment="Created using Pulumi - Route 53 fundamentals lab",
)

# Create an A record.
# 192.0.2.0/24 is reserved for documentation.
# This is not a real application endpoint.
a_record = aws.route53.Record(
    "www-record",
    zone_id=zone.zone_id,
    name=f"www.{domain}",
    type="A",
    ttl=300,
    records=["192.0.2.10"],
)

# Create a TXT record.
txt_record = aws.route53.Record(
    "verification-record",
    zone_id=zone.zone_id,
    name=domain,
    type="TXT",
    ttl=300,
    records=['"route53-pulumi-lab"'],
)

# Export useful information.
pulumi.export("hostedZoneId", zone.zone_id)
pulumi.export("domain", zone.name)
pulumi.export("nameServers", zone.name_servers)
pulumi.export("wwwRecord", a_record.fqdn)
pulumi.export("txtRecord", txt_record.fqdn)
```

The `192.0.2.10` address belongs to a documentation-only IP range. It is suitable for testing DNS record creation but will not provide a working website.

The Pulumi resources used here are:

* `aws.route53.Zone`

* `aws.route53.Record`

The hosted-zone resource creates the zone, while the record resources add DNS records to it.

Reference: [Pulumi Route 53 Record resource documentation](https://www.pulumi.com/registry/packages/aws/api-docs/route53/record/?utm_source=chatgpt.com).

### Step 4.5 — Preview the Infrastructure

```bash
pulumi preview
```

Review the planned resources.

You should see three resources to create:

```text
aws:route53:Zone
aws:route53:Record
aws:route53:Record
```

### Step 4.6 — Deploy the Infrastructure

```bash
pulumi up
```

Review the deployment and approve it.

Retrieve the outputs:

```bash
pulumi stack output
```

Retrieve the hosted-zone ID:

```bash
pulumi stack output hostedZoneId
```

Retrieve the authoritative name servers:

```bash
pulumi stack output nameServers
```

Your public hosted zone is now created.

Important: Creating a public hosted zone does not automatically delegate your registered domain to it. We will investigate this in the next lab.

### Lab 5 — Configure DNS Records and Inspect Their Resolution

In this lab, we will verify the DNS records created by Pulumi.

### Step 5.1 — Retrieve Hosted Zone Information

```bash
export ZONE_ID=$(pulumi stack output hostedZoneId)

export DOMAIN=$(pulumi stack output domain)

export NAME_SERVER=$(pulumi stack output nameServers --json | jq -r '.[0]')
```

Display the values:

```bash
echo "Zone ID: $ZONE_ID"
echo "Domain: $DOMAIN"
echo "Name server: $NAME_SERVER"
```

### Step 5.2 — Inspect Hosted Zone Name Servers

```bash
aws route53 get-hosted-zone \
    --id "$ZONE_ID"
```

Examine:

* Hosted zone ID.

* Hosted zone name.

* Hosted zone configuration.

* Name server delegation information.

* Associated VPCs, if applicable.

### Step 5.3 — Query the A Record Directly

Query the authoritative name server:

```bash
dig @"$NAME_SERVER" "www.$DOMAIN" A +norecurse
```

Expected answer:

```text
www.lab.example.com. 300 IN A 192.0.2.10
```

Your actual domain will differ.

Notice the `aa` flag in the response. It indicates that the DNS server is authoritative for the answer.

### Step 5.4 — Query the TXT Record

```bash
dig @"$NAME_SERVER" "$DOMAIN" TXT +norecurse
```

Expected answer:

```text
lab.example.com. 300 IN TXT "route53-pulumi-lab"
```

### Step 5.5 — Query Through a Recursive Resolver

```bash
dig @1.1.1.1 "www.$DOMAIN" A
```

There is an important distinction here:

* Querying the assigned authoritative name server directly should return your newly created record.

* Querying a public recursive resolver requires the domain to be properly delegated to the Route 53 hosted zone.

If you created a hosted zone for an existing domain or subdomain without configuring its parent delegation, the public recursive query may return a different result or `NXDOMAIN`.

### Step 5.6 — Configure Domain Delegation

If you own the domain and want the hosted zone to become publicly authoritative, configure its delegation at the domain registrar.

Retrieve the four Route 53 name servers:

```bash
pulumi stack output nameServers
```

At your registrar, replace the existing authoritative name server configuration with the four assigned Route 53 name servers.

Important

Only change delegation for a domain or subdomain dedicated to this lab. Changing production domain name servers without migrating existing DNS records can interrupt websites, email, and other services.

For a delegated subdomain, configure the appropriate NS records in its parent zone instead of changing the entire domain's registrar delegation.

After delegation, verify:

```bash
dig "$DOMAIN" NS

dig "www.$DOMAIN" A

dig +trace "www.$DOMAIN" A
```

### Step 5.7 — Understand DNS Propagation and TTL

Inspect the TTL:

```bash
dig @"$NAME_SERVER" "www.$DOMAIN" A +noall +answer
```

You should see a TTL of approximately 300 seconds.

Now change the TTL in `__main__.py`:

```python
ttl=60,
```

Preview and deploy:

```bash
pulumi preview

pulumi up
```

Query again:

```bash
dig @"$NAME_SERVER" "www.$DOMAIN" A +noall +answer
```

Observe the updated authoritative record.

Remember that previously cached responses at recursive resolvers can retain their original TTL.

### Lab 6 — Explore Hosted Zone Properties and Route 53 CLI Commands

Now we will explore Route 53 through AWS CLI instead of Pulumi.

This lab focuses on reading and inspecting resources. We will continue using Pulumi as the infrastructure owner to avoid configuration drift.

### Step 6.1 — List Public Hosted Zones

```bash
aws route53 list-hosted-zones
```

To display only hosted-zone names and IDs:

```bash
aws route53 list-hosted-zones \
    --query 'HostedZones[].{Name:Name,Id:Id,Private:Config.PrivateZone}' \
    --output table
```

### Step 6.2 — Retrieve Hosted Zone Details

```bash
aws route53 get-hosted-zone \
    --id "$ZONE_ID"
```

### Step 6.3 — List DNS Records

```bash
aws route53 list-resource-record-sets \
    --hosted-zone-id "$ZONE_ID"
```

Display a concise result:

```bash
aws route53 list-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --query 'ResourceRecordSets[].{Name:Name,Type:Type,TTL:TTL}' \
    --output table
```

You should see:

* SOA record.

* NS record.

* A record.

* TXT record.

### Step 6.4 — Inspect Individual Record Types

List only A records:

```bash
aws route53 list-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --query "ResourceRecordSets[?Type=='A']"
```

List TXT records:

```bash
aws route53 list-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --query "ResourceRecordSets[?Type=='TXT']"
```

List NS records:

```bash
aws route53 list-resource-record-sets \
    --hosted-zone-id "$ZONE_ID" \
    --query "ResourceRecordSets[?Type=='NS']"
```

### Step 6.5 — Explore Route 53 API Operations

Some useful commands for future modules:

| Command                     | Purpose                           |
| --------------------------- | --------------------------------- |
| list-hosted-zones           | List hosted zones                 |
| get-hosted-zone             | Retrieve hosted-zone details      |
| list-resource-record-sets   | List DNS records                  |
| change-resource-record-sets | Create, update, or delete records |
| get-change                  | Inspect DNS change status         |
| list-tags-for-resource      | Inspect resource tags             |
| list-health-checks          | List health checks                |

Explore the CLI documentation:

```bash
aws route53 help
```

And:

```bash
aws route53 list-resource-record-sets help
```

### Lab 7 — Clean Up AWS Resources

Since Route 53 public hosted zones can incur ongoing charges, clean up the resources after completing the lab if you do not need them.

First, inspect the deployment:

```bash
pulumi stack
```

Then destroy the resources:

```bash
pulumi destroy
```

Approve the operation.

Verify that the hosted zone is no longer present:

```bash
aws route53 list-hosted-zones
```

Optionally remove the Pulumi stack:

```bash
pulumi stack rm dev
```

This removes the Pulumi stack, not your AWS account or unrelated infrastructure.

### Module 1 — Final Lab Architecture

The infrastructure created during this module is intentionally simple:

Pulumi (Python)

Infrastructure deployment

Amazon Route 53

Public hosted zone: YOUR_DOMAIN

A Record

www → 192.0.2.10

TXT Record

Domain verification

DNS Clients

dig · nslookup · host · Recursive resolvers

### Additional References

These are useful official resources for studying this module:

* [Amazon Route 53 Developer Guide](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/Welcome.html?utm_source=chatgpt.com)

* [Working with hosted zones](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/hosted-zones-working-with.html?utm_source=chatgpt.com)

* [DNS record types supported by Route 53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/ResourceRecordTypes.html?utm_source=chatgpt.com)

* [Route 53 Resolver](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver.html?utm_source=chatgpt.com)

* [Pulumi Route 53 Zone resource](https://www.pulumi.com/registry/packages/aws/api-docs/route53/zone/?utm_source=chatgpt.com)

* [Pulumi Route 53 Record resource](https://www.pulumi.com/registry/packages/aws/api-docs/route53/record/?utm_source=chatgpt.com)

* [Route 53 pricing](https://aws.amazon.com/route53/pricing/?utm_source=chatgpt.com)

### Module 1 — Completion Summary

By completing this module, you should understand the following:

* DNS hierarchy, zones, and delegation.

* Recursive and iterative resolution.

* DNS record types and their use cases.

* TTL, caching, and negative caching.

* Public versus private DNS.

* Route 53 architecture and hosted zones.

* Authoritative name servers and domain registration.

* Route 53 Resolver fundamentals.

* UDP, TCP, port 53, and EDNS.

* Route 53 pricing fundamentals.

* AWS CLI and Pulumi setup.

* Public hosted-zone deployment with Pulumi.

* DNS inspection and Route 53 CLI operations.

Next module: Module 2 — Hosted Zones, DNS Records, and Domain Management. We will build on this infrastructure and explore Alias records, CNAME limitations, domain delegation, private hosted zones, and more advanced record management with Pulumi.
