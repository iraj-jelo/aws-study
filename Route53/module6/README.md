### Module 6 — Route 53 Resolver DNS Firewall and DNS Security

### 1\. DNS Security Fundamentals and Common DNS Threats

Before configuring Route 53 DNS Firewall, it's important to understand what we're protecting and where DNS security fits into an AWS architecture.

DNS is a fundamental part of almost every application. Applications use DNS to discover:

* Public websites and APIs.

* Internal services and databases.

* AWS service endpoints.

* Third-party APIs.

* Software repositories and package registries.

* Identity providers and authentication services.

This makes DNS an attractive target for attackers.

### 1.1 DNS as an attack surface

Consider an application running on an EC2 instance inside a private subnet.

The application makes an HTTP request:

```python
import requests

response = requests.get("https://api.example.com")
```

Before establishing the HTTPS connection, the operating system must resolve:

```text
api.example.com
```

into an IP address.

A simplified resolution process looks like this:

![DNS Resolution: The Journey of a Domain Name | by Pratham Shah | Medium](https://images.openai.com/static-rsc-4/XzwiyWnjYpns_mq7XcPCGJoAL-Z9226NBheUNeJMAZOTlh0UeACnA9dTygzst9tmCshnGPu6bSDhTszXnyilTRig14O7F7DzyM_8va8rdMf1bXtUaXAMKUUXH9L1HJh2rgQQQQoMY4UBn-wDfSMFT9PwafwVKBrj_WNGMNTZDLd51b01iSHUBF1I2VWHstJZ?purpose=fullsize)

* The application requests the IP address of `api.example.com`.

* The operating system checks its DNS cache.

* If necessary, the request goes to the configured DNS resolver.

* The resolver obtains the answer from its cache or queries authoritative DNS infrastructure.

* The IP address is returned to the application.

* The application connects to the destination.

An attacker who can manipulate, redirect, or abuse this process may compromise application communication without directly attacking the application itself.

### 1.2 Common DNS threats

Let's examine the most important DNS-related threats.

A. DNS tunneling

DNS tunneling uses DNS queries and responses to transfer data through DNS infrastructure.

For example, an infected machine might generate queries such as:

```text
aGVsbG8td29ybGQ.attacker.example.com
```

The encoded portion may contain data that an attacker wants to exfiltrate.

The attacker controls the authoritative DNS server for `attacker.example.com` and extracts information from incoming DNS queries.

DNS tunneling can be used for:

* Data exfiltration.

* Command-and-control communication.

* Bypassing network restrictions.

* Maintaining communication with compromised systems.

B. Malware command and control (C2)

Malware frequently communicates with attacker-controlled domains.

For example:

```text
malware-client.internal
        |
        | DNS query
        v
controller.attacker-domain.com
        |
        v
Attacker-controlled infrastructure
```

If the malware successfully resolves the domain, it may establish an outbound connection and receive instructions.

Blocking known malicious domains at the DNS layer can disrupt this communication.

C. DNS spoofing and cache poisoning

An attacker attempts to provide a resolver with false DNS information.

For example, a legitimate domain:

```text
bank.example.com
```

might be associated with an attacker-controlled IP address.

If a resolver accepts the forged response, clients may connect to the wrong destination.

DNSSEC helps protect against forged DNS data by allowing resolvers to cryptographically validate DNS responses.

D. DNS amplification attacks

DNS amplification is a type of distributed denial-of-service (DDoS) attack.

An attacker sends small DNS queries to open resolvers using a spoofed victim IP address.

The resolvers return larger responses to the victim.

```text
Attacker
   |
   | Small DNS query (spoofed source IP)
   v
Open DNS resolvers
   |
   | Large DNS responses
   v
Victim
```

This attack amplifies the amount of traffic directed at the victim.

E. Domain generation algorithms (DGA)

Some malware generates large numbers of seemingly random domain names.

For example:

```text
xk29ab.example.com
q91mz2.example.com
p8d7ka.example.com
```

The malware attempts to find a domain registered and controlled by its operator.

This makes domain-based detection more difficult.

F. Unauthorized DNS resolution

An organization may want its workloads to resolve only approved domains.

For example, an application server might need:

```text
api.stripe.com
packages.example.org
internal.example.com
```

But it should not access:

```text
malicious-domain.example
unknown-download.example
```

DNS Firewall can enforce domain-based DNS resolution policies for VPC workloads.

### 1.3 Where Route 53 DNS security fits

AWS provides several DNS-related security capabilities.

| Security capability             | Purpose                                       |
| ------------------------------- | --------------------------------------------- |
| Route 53 DNS Firewall           | Filter DNS queries based on domain names      |
| DNSSEC                          | Cryptographically authenticate DNS data       |
| Route 53 Resolver query logging | Record DNS queries and responses              |
| AWS Network Firewall            | Inspect and filter network traffic            |
| Security Groups                 | Control network traffic to and from resources |
| AWS WAF                         | Protect supported web applications            |

An important distinction:

* DNS Firewall controls which domain names workloads can resolve through the protected Resolver path.

* DNSSEC protects the authenticity and integrity of DNS data.

* Network Firewall provides network-layer traffic inspection and filtering.

These technologies solve different problems and can complement each other.

### 2\. DNS Firewall Architecture and Capabilities

Amazon Route 53 Resolver DNS Firewall is a managed DNS filtering service that protects DNS queries originating from resources in your Amazon VPCs.

It integrates with the Route 53 Resolver.

### 2.1 Understanding the architecture

Every VPC has access to the Route 53 Resolver through its VPC DNS infrastructure.

The default Resolver address is:

```text
VPC CIDR + 2
```

For example, if your VPC CIDR is:

```text
10.0.0.0/16
```

The Resolver address is:

```text
10.0.0.2
```

When a workload sends a DNS query through this Resolver, DNS Firewall can evaluate the query against associated firewall rule groups.

![Secure your Amazon VPC DNS resolution with Amazon Route 53 Resolver DNS Firewall | Networking & Content Delivery](https://images.openai.com/static-rsc-4/HU2R8WaLMmHyMUhqnt_yKYzkX3B6Qnzc6KDVtO3iSKPoYPAHA25_OagUwkO9prWsehCxPNhdHqJarmYZYt6uzn3osE84LC54qx5qYp22Hpz8iB3Gpon8UPdJ7O97Ppu66qksFwBtzOpMJJoR6GJgtqsbWBhcIDqJYZA7OQieDvdCzmQ9yChWrzYSMlAQd7PD?purpose=fullsize)

The simplified flow is:

* An EC2 instance sends a DNS query.

* The query reaches the Route 53 Resolver.

* DNS Firewall evaluates the query against applicable rule groups.

* A matching rule determines whether the query is allowed, blocked, or monitored.

* The Resolver processes the query according to the applicable policy.

* DNS Firewall logs can record the matching activity.

For example:

```text
EC2 Instance
    |
    | Query: malicious.example.com
    v
Route 53 Resolver
    |
    v
DNS Firewall
    |
    | Match: Block rule
    v
DNS response: Blocked
```

The application cannot obtain a normal DNS answer through that protected resolution path.

### 2.2 What DNS Firewall can protect

DNS Firewall can help protect workloads against:

* Known malicious domains.

* Phishing domains.

* Malware command-and-control domains.

* Suspicious domain categories.

* Unauthorized external DNS destinations.

* Domains associated with unwanted applications or content.

It can also provide visibility into DNS queries that match monitoring rules.

### 2.3 Important limitation

DNS Firewall is not a complete network security solution.

For example, suppose an EC2 instance uses a hardcoded IP address:

```bash
curl https://203.0.113.10
```

This connection does not require resolving a domain name.

DNS Firewall cannot prevent this connection simply by blocking a DNS domain.

Similarly, workloads using external DNS resolvers directly, DNS over HTTPS, or other resolution paths may bypass the filtering path unless additional network controls enforce the intended DNS architecture.

Therefore, DNS Firewall should be combined with appropriate network controls.

### 3\. DNS Firewall Rule Groups

A DNS Firewall rule group is a reusable collection of DNS filtering rules.

Instead of configuring domain filtering independently for every EC2 instance, you create a rule group and associate it with one or more VPCs.

For example:

```text
                    DNS Firewall
                         |
                  Production Rules
                         |
             +-----------+-----------+
             |           |           |
          VPC-A        VPC-B       VPC-C
             |           |           |
           EC2         ECS         EKS
```

All three VPCs can use the same DNS filtering policy.

### 3.1 Domain lists

A domain list contains domain names or domain patterns that DNS Firewall evaluates.

For example, you might create the following custom domain list:

```text
malicious-domains

malware.example.com
phishing.example.com
*.suspicious.example.org
```

Another domain list could contain trusted domains:

```text
approved-domains

api.example.com
packages.example.org
registry.example.net
```

You can use:

* Custom domain lists that you maintain.

* AWS-managed domain lists.

* Domain lists associated with threat intelligence and security categories, where supported.

Domain specifications can include exact domains and wildcard patterns.

For example:

```text
example.com
*.example.com
```

These are not necessarily equivalent:

* `example.com` identifies the exact domain.

* `*.example.com` identifies matching subdomains.

When designing policies, consider whether you need to allow the apex domain, its subdomains, or both.

### 3.2 AWS-managed domain lists

AWS provides managed domain lists to help identify potentially dangerous domains.

Depending on regional availability and the DNS Firewall feature set, these can include categories associated with:

* Malware.

* Botnet command-and-control infrastructure.

* Other known security threats.

The advantage is that you don't need to maintain every malicious domain yourself.

AWS maintains the managed lists, and you can reference them from DNS Firewall rules.

However, managed lists should not replace other security controls. AWS recommends testing managed domain lists using the `ALERT` action before enforcing blocking in production. Amazon Route 53

### 3.3 Creating a DNS Firewall rule group

Suppose we want to create a security policy for our production VPC.

Our requirements:

* Allow trusted domains.

* Block known malicious domains.

* Monitor suspicious domains.

* Permit other DNS queries normally.

We can organize the rules as follows:

```text
ProductionFirewall
|
+-- Rule 100: Allow trusted domains
|
+-- Rule 200: Block malicious domains
|
+-- Rule 300: Alert on suspicious domains
```

The numbers represent rule priorities.

Important: Lower numerical priorities are evaluated first.

### 3.4 Rule evaluation order

Suppose an application queries:

```text
api.example.com
```

The Resolver Firewall evaluates the rules in priority order.

```text
DNS Query: api.example.com
          |
          v
Rule 100: Trusted domains?
          |
          +-- Match --> ALLOW
          |
          +-- No match
                 |
                 v
Rule 200: Malicious domains?
          |
          +-- Match --> BLOCK
          |
          +-- No match
                 |
                 v
Rule 300: Suspicious domains?
          |
          +-- Match --> ALERT
          |
          +-- No match
                 |
                 v
             Normal DNS
```

Once a rule matches, its action is applied and evaluation stops.

This is why rule priority is important.

For example, if you put a broad blocking rule before a trusted-domain exception, the exception may never be evaluated.

AWS documentation: [Configure and manage DNS Firewall rules](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/gr-configure-manage-firewall-rules.html?utm_source=chatgpt.com).

### 4\. Allow, Block, and Alert Actions

DNS Firewall supports three primary actions for domain-list-based rules.

### 4.1 ALLOW

The `ALLOW` action permits a matching DNS query.

Example:

```text
Domain list: trusted-domains

api.example.com
packages.example.org
registry.example.net
```

Rule:

```text
Priority: 100
Action: ALLOW
```

If an application queries `api.example.com`, DNS Firewall permits the query and stops evaluating subsequent rules.

This is particularly useful when implementing an allowlist architecture.

### 4.2 BLOCK

The `BLOCK` action prevents a matching DNS query from receiving its normal DNS answer through the protected Resolver.

Example:

```text
Domain list: malicious-domains

malware.example.com
phishing.example.com
```

Rule:

```text
Priority: 200
Action: BLOCK
```

DNS Firewall supports three block response types:

| Response | Behavior                                                                  |
| -------- | ------------------------------------------------------------------------- |
| NODATA   | Returns an empty answer without indicating that the domain does not exist |
| NXDOMAIN | Indicates that the queried domain does not exist                          |
| OVERRIDE | Returns a configured custom DNS response                                  |

The `OVERRIDE` response supports a custom CNAME record.

For example, you could redirect a blocked domain to an internal security notification service, although this should be designed carefully.

### 4.3 ALERT

The `ALERT` action permits the DNS query but generates an alert in the configured Resolver query logs.

This is useful when you want to understand DNS behavior before enforcing restrictions.

Suppose you want to block all domains associated with a particular category.

You initially configure:

```text
Priority: 300
Action: ALERT
```

You monitor the results for several days.

If you discover that legitimate applications depend on some of those domains, you can create exceptions.

After validating the policy, change the action to:

```text
Priority: 300
Action: BLOCK
```

This approach reduces the risk of accidentally breaking production workloads.

Important: `ALERT` is not the same as blocking. The DNS query is still permitted.

AWS documentation: [DNS Firewall rule actions](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-rule-actions.html?utm_source=chatgpt.com).

### 5\. DNS Firewall Rule Priorities and Evaluation Order

There are two separate priority mechanisms that you need to understand.

* Rule group association priority.

* Rule priority inside a rule group.

### 5.1 Rule group association priority

A VPC can have multiple DNS Firewall rule groups associated with it.

For example:

```text
VPC: Production
|
+-- Association priority 100
|       |
|       +-- ProductionSecurityRules
|
+-- Association priority 200
|       |
|       +-- CorporateDomainRules
|
+-- Association priority 300
        |
        +-- MonitoringRules
```

DNS Firewall processes rule groups starting with the lowest numerical association priority.

### 5.2 Rule priority inside each group

Each rule group has its own independent rule priorities.

For example:

```text
ProductionSecurityRules
|
+-- Rule priority 100: Allow trusted domains
|
+-- Rule priority 200: Block malicious domains
|
+-- Rule priority 300: Alert suspicious domains
```

The Resolver evaluates the rule groups and their rules in order until it finds a match or exhausts the applicable rules.

### 5.3 Example of a priority mistake

Imagine this configuration:

```text
Rule 100: BLOCK *.example.com
Rule 200: ALLOW api.example.com
```

You might expect `api.example.com` to be allowed.

However, the first rule matches before the second rule is evaluated.

The correct configuration is:

```text
Rule 100: ALLOW api.example.com
Rule 200: BLOCK *.example.com
```

Now the exception is evaluated first.

This is an important principle when designing DNS allowlists and blocklists.

### 5.4 Default behavior

What happens if no rule matches?

DNS Firewall allows the query to proceed through normal DNS resolution.

Therefore, if your security requirement is to allow only explicitly approved domains, you need a final catch-all blocking rule.

For example:

```text
Rule 100: ALLOW approved-domains
Rule 200: BLOCK malicious-domains
Rule 300: BLOCK *
```

The last rule blocks everything that hasn't matched an earlier rule.

Be careful with this design: it can break software updates, package downloads, AWS service access, authentication, and application dependencies.

For production environments, build and test the allowlist carefully.

### 6\. VPC Associations and Firewall Policies

Creating a DNS Firewall rule group doesn't automatically protect a VPC.

You must associate the rule group with the VPC.

### 6.1 VPC association

Consider this architecture:

```text
AWS Account
|
+-- VPC: Development
|      |
|      +-- EC2 instances
|      +-- ECS services
|
+-- VPC: Staging
|      |
|      +-- EC2 instances
|      +-- ECS services
|
+-- VPC: Production
       |
       +-- EC2 instances
       +-- ECS services
```

You might create two rule groups:

```text
CommonSecurityRules
ProductionSecurityRules
```

Then associate them as follows:

| VPC         | Associated rule groups                        |
| ----------- | --------------------------------------------- |
| Development | CommonSecurityRules                           |
| Staging     | CommonSecurityRules                           |
| Production  | CommonSecurityRules + ProductionSecurityRules |

This allows you to reuse common security rules while applying additional restrictions to production.

### 6.2 Firewall configuration and failure behavior

DNS Firewall has a VPC-level configuration that controls how DNS resolution behaves if DNS Firewall becomes unavailable.

Two important modes are:

* `FAIL_OPEN`: DNS queries continue through normal resolution if DNS Firewall cannot be reached.

* `FAIL_CLOSED`: DNS queries are blocked if DNS Firewall cannot be reached.

This is a security-versus-availability decision.

| Mode        | Security                       | Availability |
| ----------- | ------------------------------ | ------------ |
| FAIL_OPEN   | Lower during firewall failure  | Higher       |
| FAIL_CLOSED | Higher during firewall failure | Lower        |

For example:

A production application that must remain available might use `FAIL_OPEN`, while a highly restricted environment might choose `FAIL_CLOSED`.

Neither choice is universally correct. Evaluate the operational consequences before selecting a mode.

### 6.3 Pulumi implementation

We can manage DNS Firewall resources using Pulumi's AWS provider.

The main resource types are:

* `aws.route53.ResolverFirewallDomainList`

* `aws.route53.ResolverFirewallRuleGroup`

* `aws.route53.ResolverFirewallRule`

* `aws.route53.ResolverFirewallRuleGroupAssociation`

* `aws.route53.ResolverConfig`

Here is a simplified Python example:

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")

# 1. Create a custom domain list.
malicious_domains = aws.route53.ResolverFirewallDomainList(
    "malicious-domains",
    name="malicious-domains",
    domains=[
        "malware.example.com",
        "phishing.example.com",
        "*.suspicious.example.org",
    ],
)

# 2. Create a reusable rule group.
rule_group = aws.route53.ResolverFirewallRuleGroup(
    "production-dns-firewall",
    name="production-dns-firewall",
)

# 3. Add a blocking rule.
block_rule = aws.route53.ResolverFirewallRule(
    "block-malicious-domains",
    name="block-malicious-domains",
    firewall_rule_group_id=rule_group.id,
    priority=100,
    action="BLOCK",
    block_response="NXDOMAIN",
    firewall_domain_list_id=malicious_domains.id,
)

# 4. Associate the rule group with a VPC.
association = aws.route53.ResolverFirewallRuleGroupAssociation(
    "production-firewall-association",
    name="production-firewall-association",
    firewall_rule_group_id=rule_group.id,
    vpc_id=vpc_id,
    priority=100,
)

pulumi.export("firewall_rule_group_id", rule_group.id)
pulumi.export("firewall_association_id", association.id)
```

Configuration:

```bash
pulumi config set vpcId vpc-0123456789abcdef0
```

Deploy:

```bash
pulumi preview
pulumi up
```

This example creates a custom domain list, a firewall rule group, a blocking rule, and a VPC association.

For production, you should also add trusted-domain exceptions, monitoring rules, appropriate IAM permissions, and the required VPC failure configuration.

### 7\. DNS Firewall Logging and Monitoring

A DNS security policy without monitoring is difficult to operate.

You need visibility into:

* Which domains applications are requesting.

* Which queries are being blocked.

* Which queries are triggering alerts.

* Which VPCs are generating suspicious requests.

* Whether legitimate application traffic is being blocked accidentally.

### 7.1 Resolver query logging

Route 53 Resolver supports query logging.

You can send query logs to:

* Amazon CloudWatch Logs.

* Amazon S3.

* Amazon Data Firehose.

The logs can contain information such as:

* Query name.

* Query type.

* Source IP address.

* VPC ID.

* Instance information when available.

* Query response information.

* DNS Firewall rule group and action information for applicable queries.

DNS Firewall-specific fields include:

```text
firewall_rule_group_id
firewall_rule_action
firewall_domain_list_id
```

These fields are particularly useful for identifying which security rule caused a query to be blocked.

Amazon Route 53 +1

### 7.2 Example DNS Firewall log analysis

Imagine the following queries:

```text
api.example.com
malware.example.com
packages.example.org
phishing.example.com
```

Your DNS Firewall logs might indicate:

| Domain               | Action   | Result               |
| -------------------- | -------- | -------------------- |
| api.example.com      | ALLOW    | Permitted            |
| malware.example.com  | BLOCK    | Blocked              |
| packages.example.org | No match | Normal resolution    |
| phishing.example.com | ALERT    | Permitted and logged |

This helps security engineers distinguish between normal application behavior and suspicious activity.

### 7.3 CloudWatch monitoring

DNS Firewall provides CloudWatch metrics for monitoring rule groups.

You can use these metrics to identify:

* Blocked DNS queries.

* Alerted DNS queries.

* DNS Firewall rule activity.

* Changes in DNS query behavior.

For example, a sudden increase in blocked queries might indicate:

* A compromised workload.

* A malware infection.

* A misconfigured application.

* A newly introduced dependency that violates the DNS policy.

A practical production monitoring architecture:

```text
EC2 / ECS / EKS
       |
       v
Route 53 Resolver
       |
       v
DNS Firewall
       |
       +------> CloudWatch Metrics
       |
       +------> Resolver Query Logs
                       |
                       v
                CloudWatch Logs
                       |
                       v
               Logs Insights
                       |
                       v
                CloudWatch Alarms
```

### 8\. DNSSEC Fundamentals and Cryptographic DNS Validation

Now let's move to the second major subject of this module: DNSSEC.

DNS Firewall and DNSSEC solve different security problems.

DNS Firewall filters DNS queries based on domain policies.

DNSSEC provides cryptographic authentication of DNS data.

### 8.1 Why DNSSEC exists

Consider a client querying:

```text
bank.example.com
```

The authoritative DNS server returns:

```text
bank.example.com -> 192.0.2.10
```

But how does the client know that this response is authentic?

Traditional DNS does not inherently provide cryptographic authentication of DNS records.

An attacker who can manipulate DNS responses may attempt to provide a forged answer:

```text
bank.example.com -> 198.51.100.20
```

The client might then connect to an attacker-controlled server.

HTTPS certificate validation provides another important layer of protection, but DNSSEC protects the authenticity of DNS data itself.

### 8.2 What is DNSSEC?

DNSSEC stands for Domain Name System Security Extensions.

It extends DNS with cryptographic signatures.

Instead of simply returning DNS records, a DNSSEC-enabled authoritative server also provides cryptographic signatures that allow validating resolvers to verify the authenticity and integrity of DNS data.

DNSSEC helps protect against:

* DNS response spoofing.

* DNS cache poisoning.

* Unauthorized DNS data modification.

* Certain DNS redirection attacks.

DNSSEC does not encrypt DNS queries or responses.

It also does not hide the domains users are querying.

### 8.3 How DNSSEC works

Consider this simplified DNSSEC resolution process:

![Domain Name System Security Extensions (DNSSEC) | Cyber Security Agency of Singapore](https://images.openai.com/static-rsc-4/M3HvRBEpWg8uJ9zEMnzETVPm5HSne8wGuYxhrFJyY5cqnTX28vBtG8Y82MYNHQl7cpd9lIVqu844AHUOXWMeQIrKmMa8ss5IcyZC39tOnq5NS50-a_ISdw7prwnVI3R7HglWo6Hd_jKYh3Pg88QK67k_O0tKFQT4xyQl-yk6DF9EzMnxIAixbLrbrkIAN81i?purpose=fullsize)

* A client asks a DNSSEC-validating resolver for a domain.

* The resolver obtains the DNS records and their signatures.

* The resolver validates the signatures using the appropriate public keys.

* It verifies that the public keys are trusted through the DNSSEC chain of trust.

* If validation succeeds, the DNS response can be trusted as authentic.

* If validation fails, the validating resolver returns a failure instead of accepting forged data.

### 8.4 Important DNSSEC record types

DNSSEC introduces several additional DNS record types.

| Record | Purpose                                             |
| ------ | --------------------------------------------------- |
| DNSKEY | Publishes public keys used for DNSSEC validation    |
| RRSIG  | Contains digital signatures for DNS record sets     |
| DS     | Connects a child zone to its parent zone            |
| NSEC   | Provides authenticated proof of nonexistence        |
| NSEC3  | Provides hashed authenticated proof of nonexistence |

Let's examine the most important ones.

DNSKEY

Publishes the public key associated with a DNSSEC-enabled zone.

Example:

```text
example.com. IN DNSKEY 257 3 13 ...
```

The key is used by validating resolvers to verify DNSSEC signatures.

RRSIG

Contains the digital signature associated with a DNS record set.

For example, an A record set can have an associated RRSIG record.

The resolver uses the relevant public key to validate that signature.

DS — Delegation Signer

The DS record exists in the parent zone.

It contains a cryptographic digest associated with a DNSKEY in the child zone.

For example:

```text
Parent zone: com
Child zone: example.com
```

The `.com` zone contains a DS record that authenticates the DNSSEC key of `example.com`.

This establishes a connection between the parent and child zones.

NSEC and NSEC3

These records provide authenticated evidence that a requested DNS record does not exist.

Without authenticated denial of existence, an attacker could potentially manipulate negative DNS responses.

### 8.5 DNSSEC versus HTTPS

These technologies are complementary.

| Feature                              | DNSSEC | HTTPS/TLS    |
| ------------------------------------ | ------ | ------------ |
| Protects DNS data authenticity       | Yes    | No           |
| Encrypts communication               | No     | Yes          |
| Authenticates DNS records            | Yes    | No           |
| Authenticates server identity        | No     | Yes          |
| Protects against DNS cache poisoning | Yes    | Not directly |

A secure application should use HTTPS even when its domain uses DNSSEC.

### 9\. Key-Signing Keys (KSK) and Zone-Signing Keys (ZSK)

DNSSEC uses cryptographic keys to sign and validate DNS data.

Two key types are particularly important:

* Key-Signing Key (KSK).

* Zone-Signing Key (ZSK).

### 9.1 Zone-Signing Key (ZSK)

The ZSK signs the DNS record sets within a DNS zone.

For example, suppose your hosted zone contains:

```text
example.com

A       example.com          192.0.2.10
AAAA    example.com          2001:db8::10
MX      example.com          mail.example.com
TXT     example.com          "v=spf1 ..."
CNAME   www.example.com      example.com
```

The ZSK is used to generate signatures for the relevant DNS record sets.

These signatures are published as RRSIG records.

When a resolver receives the DNS response, it can validate the signatures using the corresponding public DNSKEY.

### 9.2 Key-Signing Key (KSK)

The KSK signs the DNSKEY record set.

The DNSKEY record set contains the public keys associated with the zone.

The KSK therefore protects the integrity of the zone's key information.

The parent zone uses a DS record to establish trust in the child zone's KSK.

### 9.3 KSK versus ZSK

| Property               | KSK                           | ZSK                         |
| ---------------------- | ----------------------------- | --------------------------- |
| Purpose                | Signs DNSKEY record set       | Signs other DNS record sets |
| Main responsibility    | Protects zone key information | Protects DNS records        |
| Parent DS relationship | Yes                           | No direct DS relationship   |
| Route 53 management    | Customer-managed KMS key      | Managed by Route 53         |
| Rotation               | Customer responsibility       | Managed automatically       |

The separation provides operational flexibility.

For example, you can rotate the ZSK without necessarily changing the DS record in the parent zone.

### 9.4 DNSSEC signing architecture in Route 53

Amazon Route 53 manages much of the DNSSEC signing process for public hosted zones.

However, you must provide or create a suitable AWS KMS customer-managed key for the KSK.

The architecture looks like this:

![End-to-End Integrity with IPFS](https://images.openai.com/static-rsc-4/Audo335Ew6-Hi74PCvZ9iHKd0AQJkmmZVmGHQeobWf0eRSLSuS7mbeTnPtg58Ah3030UrTtWQkdHSQpLYb2KvqG46NUpTiF1QLWqosWn82Sr61PGPRmQbHfQcJbqvSZOJVGx9BjIoqksfnoyCkt5wF-tf3HvDbMh_tMlAEbSXrsfvip80d5c9gt9Nx-HLZuG?purpose=fullsize)

The general process:

* You create or select an appropriate KMS key.

* Route 53 associates that key with a KSK.

* Route 53 uses the KSK to sign the DNSKEY record set.

* Route 53 manages the ZSK and signs other DNS record sets.

* Route 53 publishes DNSKEY and RRSIG records.

* You establish the chain of trust by publishing a DS record in the parent zone.

AWS currently manages ZSK generation and rotation for DNSSEC-enabled hosted zones. The customer is responsible for the KSK and its associated KMS key. Amazon Route 53 +2

### 10\. Route 53 DNSSEC Signing and Key Management with AWS KMS

Let's examine how DNSSEC signing works specifically in AWS.

### 10.1 KMS requirements

Route 53 uses AWS KMS for KSK operations.

The KMS key must meet specific requirements.

Important properties include:

| Property          | Required configuration |
| ----------------- | ---------------------- |
| Key type          | Asymmetric             |
| Key usage         | SIGN_VERIFY            |
| Key specification | ECC_NIST_P256          |
| Signing algorithm | ECDSA_SHA_256          |
| Key state         | Enabled                |
| Key ownership     | Customer-managed key   |

The KMS key must also be in the appropriate AWS Region for Route 53 DNSSEC signing, which is US East (N. Virginia), `us-east-1`.

Its key policy must permit the Route 53 DNSSEC service to use the key.

See AWS documentation: [Configuring DNSSEC signing in Route 53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec.html?utm_source=chatgpt.com).

### 10.2 Create a KMS key

Using AWS CLI:

```bash
aws kms create-key \
  --region us-east-1 \
  --description "Route53 DNSSEC KSK" \
  --key-spec ECC_NIST_P256 \
  --key-usage SIGN_VERIFY
```

The output contains a key ARN.

You will need this ARN when creating the KSK.

Important: Creating a key is not sufficient. You must configure the KMS key policy and the permissions required by Route 53.

Do not use a symmetric encryption key for this purpose.

### 10.3 Create a Key-Signing Key

Suppose you already have:

```bash
HOSTED_ZONE_ID="Z123456789EXAMPLE"
KMS_KEY_ARN="arn:aws:kms:us-east-1:123456789012:key/example-key-id"
```

Create the KSK:

```bash
aws route53 create-key-signing-key \
  --region us-east-1 \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --key-management-service-arn "$KMS_KEY_ARN" \
  --name production-ksk \
  --status ACTIVE \
  --caller-reference "production-ksk-001"
```

The KSK is now associated with the hosted zone.

### 10.4 Enable DNSSEC signing

Next, enable DNSSEC signing:

```bash
aws route53 enable-hosted-zone-dnssec \
  --region us-east-1 \
  --hosted-zone-id "$HOSTED_ZONE_ID"
```

Check the configuration:

```bash
aws route53 get-dnssec \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --region us-east-1
```

This allows you to inspect the DNSSEC status and KSK information.

### 10.5 Establish the chain of trust

Enabling DNSSEC signing is not the final step.

You must establish the chain of trust.

Consider:

```text
Root DNS zone
      |
      v
.com DNS zone
      |
      | DS record
      v
example.com hosted zone
      |
      | DNSKEY + RRSIG
      v
DNS records
```

Route 53 provides the information required to create the DS record.

You must publish that DS record in the parent zone.

If the domain is registered through Route 53, you can configure the DS information through the domain registration interface.

If the domain is registered elsewhere, you must configure the DS record with the external registrar.

The important point is that the DS record belongs in the parent zone, not as an ordinary record in the child hosted zone.

AWS documentation: [Enabling DNSSEC signing and establishing a chain of trust](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-enable-signing.html?utm_source=chatgpt.com).

### 10.6 Why the chain of trust matters

Imagine that you enable DNSSEC signing on:

```text
example.com
```

But you forget to publish the DS record in the parent zone.

Your hosted zone might contain valid DNSKEY and RRSIG records, but validating resolvers cannot establish the complete chain of trust.

This can cause DNSSEC validation failures.

The complete chain must be established from the root through the parent zone to your domain.

### 11\. DNSSEC Validation and DS Records

Let's examine what happens when a DNSSEC-validating resolver queries your domain.

Suppose the application requests:

```text
www.example.com
```

The resolver needs to verify the DNSSEC chain.

### 11.1 Validation process

The simplified validation process is:

* The resolver starts with trusted DNSSEC information from the root.

* It validates the root zone's DNSKEY information.

* It validates the DS record for the `.com` zone.

* It validates the DNSKEY information for `.com`.

* It validates the DS record for `example.com`.

* It validates the DNSKEY information for `example.com`.

* It validates the RRSIG associated with the requested DNS record.

* If all required validations succeed, it accepts the answer.

![Loading site please wait...](https://images.openai.com/static-rsc-4/2fDSj7Xpd3Gdr1HxDeA5gCooKnfvXC5rKF7sCEOaQMvGpnEIOZbkWWD0kWVQEdgpr2ZX0ma7xft0oJxPqqI90LNaOVXqNRtjSArYowDia0wim9bZhK3msWFKiF2vQljxHobBGSmeLA0IiuF-wP6AJaX-dRLnD3unvoCTezHYAPLKVpSmhfqAs1y-SBzhxpfG?purpose=fullsize)

This is called the DNSSEC chain of trust.

### 11.2 What happens when validation fails?

Suppose you enable DNSSEC signing and later accidentally delete the DS record from the registrar.

Or perhaps you change your KSK but forget to update the DS record.

A validating resolver may detect that the DNSSEC chain is invalid.

Instead of returning an unverified answer, it returns a DNS resolution failure, commonly `SERVFAIL`.

This is important because a DNSSEC misconfiguration can make an otherwise healthy domain inaccessible to validating clients.

### 11.3 DNSSEC verification using dig

The `dig` utility is particularly useful for DNSSEC troubleshooting.

Query a domain with DNSSEC information requested:

```bash
dig example.com A +dnssec
```

The `+dnssec` option requests DNSSEC-related records, including signatures where available.

Look for:

```text
RRSIG
DNSKEY
```

You can also query DNSKEY directly:

```bash
dig example.com DNSKEY
```

Query the DS record:

```bash
dig example.com DS
```

Query the parent zone:

```bash
dig com DNSKEY
```

To check whether a recursive resolver reports DNSSEC validation status, query the EDNS DNSSEC OK flag and inspect the response flags:

```bash
dig @1.1.1.1 example.com A +dnssec
```

Look for:

```text
ad
```

The `ad` flag means the recursive resolver considers the returned data authenticated.

However, `+dnssec` alone does not prove that validation succeeded. It requests DNSSEC data; the `ad` flag from a validating recursive resolver provides additional evidence.

For more detailed diagnostics, use:

```bash
dig +trace example.com
```

This helps investigate delegation and the DNS resolution path.

### 12\. DNSSEC Troubleshooting and Operational Considerations

DNSSEC requires careful operational management.

A configuration mistake can cause an entire domain to become inaccessible to validating resolvers.

### 12.1 Common DNSSEC problems

| Problem                           | Possible consequence                  |
| --------------------------------- | ------------------------------------- |
| Missing DS record                 | Incomplete chain of trust             |
| Incorrect DS record               | DNSSEC validation failure             |
| Incorrect KMS key policy          | KSK cannot perform signing operations |
| Disabled KMS key                  | Signing problems                      |
| Inactive or failed KSK            | DNSSEC signing problems               |
| Incorrect key rotation            | Validation failures                   |
| Incorrect registrar configuration | Broken delegation chain               |
| Expired or missing signatures     | Validation failure                    |

### 12.2 KMS key accessibility

Route 53 needs access to the KMS key associated with the KSK.

If you accidentally modify the key policy and remove the required permissions, Route 53 may no longer be able to generate signatures.

This is a particularly important production concern.

Monitor the KSK status and the DNSSEC-related CloudWatch metrics.

AWS recommends alarms for:

```text
DNSSECInternalFailure
DNSSECKeySigningKeysNeedingAction
```

These conditions should be investigated promptly. Amazon Route 53 +1

### 12.3 DNSSEC and TTL

DNSSEC changes the operational considerations around DNS caching.

Route 53 enforces a maximum effective TTL of one week for records in a DNSSEC-enabled hosted zone.

If you configure a longer TTL, Route 53 enforces the one-week limit.

This matters when planning DNS migrations and key changes.

### 12.4 DNSSEC key rotation

KSK rotation requires coordination between:

* Route 53.

* AWS KMS.

* The parent DNS zone.

* The domain registrar, where applicable.

A safe KSK rotation generally involves:

* Creating a replacement KSK.

* Activating the new KSK.

* Publishing the corresponding DS information in the parent zone.

* Allowing the DNSSEC chain and cached information to converge.

* Removing the old KSK only after the replacement is properly established.

Never delete the old KSK before the new chain of trust is working.

### 12.5 DNSSEC is not DNS encryption

Remember:

```text
DNSSEC != DoH
DNSSEC != DoT
```

* DNSSEC authenticates DNS data.

* DNS over HTTPS (DoH) encrypts DNS communication over HTTPS.

* DNS over TLS (DoT) encrypts DNS communication over TLS.

These technologies address different security requirements.

### 13\. Practical Labs

Now let's put the concepts into practice.

We'll use the following environment:

```text
AWS Account
|
+-- VPC: 10.0.0.0/16
|     |
|     +-- Public Subnet
|     |
|     +-- Private Subnet
|           |
|           +-- EC2 Instance
|
+-- Route 53
      |
      +-- DNS Firewall
      |
      +-- Public Hosted Zone
            |
            +-- DNSSEC Signing
```

We will use Pulumi with Python for infrastructure management and Bash for operational commands.

### Lab 1 — Create DNS Firewall Domain Lists

Objective: Create custom domain lists for trusted and malicious domains.

We'll create two lists:

```text
trusted-domains
malicious-domains
```

Example trusted list:

```text
api.example.com
packages.example.org
registry.example.net
```

Example malicious list:

```text
malware.example.com
phishing.example.com
*.suspicious.example.org
```

For this lab, use test domains rather than real malicious domains.

Using Pulumi, create the domain lists:

```python
import pulumi_aws as aws

trusted_domains = aws.route53.ResolverFirewallDomainList(
    "trusted-domains",
    name="trusted-domains",
    domains=[
        "api.example.com",
        "packages.example.org",
        "registry.example.net",
    ],
)

malicious_domains = aws.route53.ResolverFirewallDomainList(
    "malicious-domains",
    name="malicious-domains",
    domains=[
        "malware.example.com",
        "phishing.example.com",
        "*.suspicious.example.org",
    ],
)
```

Deploy:

```bash
pulumi preview
pulumi up
```

The resulting domain lists can be reused by multiple firewall rules.

### Lab 2 — Configure DNS Firewall Rule Groups

Objective: Create a reusable firewall policy.

Create a rule group:

```python
rule_group = aws.route53.ResolverFirewallRuleGroup(
    "lab-firewall",
    name="lab-firewall",
)
```

Add an allow rule:

```python
allow_rule = aws.route53.ResolverFirewallRule(
    "allow-trusted",
    name="allow-trusted",
    firewall_rule_group_id=rule_group.id,
    firewall_domain_list_id=trusted_domains.id,
    priority=100,
    action="ALLOW",
)
```

Add a blocking rule:

```python
block_rule = aws.route53.ResolverFirewallRule(
    "block-malicious",
    name="block-malicious",
    firewall_rule_group_id=rule_group.id,
    firewall_domain_list_id=malicious_domains.id,
    priority=200,
    action="BLOCK",
    block_response="NXDOMAIN",
)
```

Add an alert rule using another domain list:

```python
monitor_domains = aws.route53.ResolverFirewallDomainList(
    "monitor-domains",
    name="monitor-domains",
    domains=[
        "suspicious.example.net",
        "*.untrusted.example.org",
    ],
)

alert_rule = aws.route53.ResolverFirewallRule(
    "alert-suspicious",
    name="alert-suspicious",
    firewall_rule_group_id=rule_group.id,
    firewall_domain_list_id=monitor_domains.id,
    priority=300,
    action="ALERT",
)
```

Your policy now looks like:

```text
Lab Firewall
|
+-- 100: ALLOW trusted domains
|
+-- 200: BLOCK malicious domains
|
+-- 300: ALERT suspicious domains
```

Deploy:

```bash
pulumi up
```

### Lab 3 — Block Malicious and Unwanted DNS Queries

Objective: Associate the firewall rule group with a VPC and verify blocking behavior.

Create the association:

```python
association = aws.route53.ResolverFirewallRuleGroupAssociation(
    "lab-firewall-association",
    name="lab-firewall-association",
    firewall_rule_group_id=rule_group.id,
    vpc_id=vpc_id,
    priority=100,
)
```

Deploy:

```bash
pulumi up
```

Connect to an EC2 instance inside the associated VPC.

Test an ordinary DNS query:

```bash
dig api.example.com
```

Test a blocked DNS query:

```bash
dig malware.example.com
```

Because the blocking response is `NXDOMAIN`, you should see a response indicating that the domain does not exist.

For comparison, try:

```bash
dig suspicious.example.net
```

That query should be permitted but generate an alert.

Important: These test domains are illustrative. Use an owned domain with appropriate DNS records if you want to test successful resolution rather than just filtering behavior.

### Lab 4 — Configure Alert-Only DNS Firewall Rules

Objective: Understand how to introduce DNS security policies without immediately blocking application traffic.

Change a blocking rule to:

```python
action="ALERT"
```

Deploy:

```bash
pulumi up
```

Now matching queries are permitted, but their activity is logged.

Generate several queries:

```bash
dig suspicious.example.net
dig suspicious.example.net
dig suspicious.example.net
```

Inspect the logs and determine:

* Which domain matched the rule?

* Which VPC generated the query?

* Which rule group was involved?

* How many queries matched?

* Are any legitimate applications using these domains?

Once the policy has been validated, you can change the action to `BLOCK`.

This is a useful production deployment strategy because it minimizes accidental service disruption.

### Lab 5 — Associate Firewall Rule Groups with VPCs

Objective: Protect multiple VPCs using reusable security policies.

Suppose you have:

```text
VPC-Development
VPC-Staging
VPC-Production
```

Associate the same rule group with multiple VPCs:

```python
development_association = aws.route53.ResolverFirewallRuleGroupAssociation(
    "development-firewall",
    name="development-firewall",
    firewall_rule_group_id=rule_group.id,
    vpc_id=development_vpc_id,
    priority=100,
)

production_association = aws.route53.ResolverFirewallRuleGroupAssociation(
    "production-firewall",
    name="production-firewall",
    firewall_rule_group_id=rule_group.id,
    vpc_id=production_vpc_id,
    priority=100,
)
```

You can also create additional production-specific rule groups.

Study how multiple associations and rule-group priorities affect DNS query evaluation.

Inspect associations:

```bash
aws route53resolver list-firewall-rule-group-associations
```

Inspect firewall rules:

```bash
aws route53resolver list-firewall-rules \
  --firewall-rule-group-id "$RULE_GROUP_ID"
```

### Lab 6 — Enable DNS Firewall Logging and Inspect Query Logs

Objective: Centralize DNS security visibility.

Create a CloudWatch log group:

```bash
aws logs create-log-group \
  --log-group-name /aws/route53/dns-firewall
```

Create a Resolver query logging configuration:

```bash
aws route53resolver create-resolver-query-log-config \
  --name dns-firewall-logging \
  --destination-arn "$LOG_GROUP_ARN"
```

Associate the logging configuration with your VPC:

```bash
aws route53resolver associate-resolver-query-log-config \
  --resolver-query-log-config-id "$LOG_CONFIG_ID" \
  --resource-id "$VPC_ID"
```

For this integration, configure the necessary IAM permissions for Route 53 Resolver to deliver logs to CloudWatch Logs.

Generate DNS queries from your EC2 instance:

```bash
dig api.example.com
dig malware.example.com
dig suspicious.example.net
```

Inspect the log stream:

```bash
aws logs describe-log-streams \
  --log-group-name /aws/route53/dns-firewall
```

You can also query the logs using CloudWatch Logs Insights.

For example:

```sql
fields @timestamp,
       query_name,
       query_type,
       firewall_rule_action,
       firewall_rule_group_id
| filter firewall_rule_action = "BLOCK"
| sort @timestamp desc
| limit 50
```

The exact available field names depend on the Resolver query log record format.

### Lab 7 — Enable DNSSEC Signing for a Public Hosted Zone

Advanced Lab

Objective: Enable DNSSEC signing for a public hosted zone using AWS KMS.

Prerequisites:

* An existing public hosted zone.

* A registered domain.

* Access to the domain's parent-zone DS configuration.

* Appropriate IAM permissions.

* An asymmetric KMS key in `us-east-1`.

First, prepare your environment:

```bash
export AWS_REGION=us-east-1
export HOSTED_ZONE_ID=Z123456789EXAMPLE
```

Create the KMS key:

```bash
aws kms create-key \
  --region "$AWS_REGION" \
  --key-spec ECC_NIST_P256 \
  --key-usage SIGN_VERIFY \
  --description "Route53 DNSSEC KSK"
```

Configure the required KMS key policy.

Then create the KSK:

```bash
aws route53 create-key-signing-key \
  --region "$AWS_REGION" \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --key-management-service-arn "$KMS_KEY_ARN" \
  --name production-ksk \
  --status ACTIVE \
  --caller-reference "dnssec-lab-001"
```

Enable DNSSEC:

```bash
aws route53 enable-hosted-zone-dnssec \
  --region "$AWS_REGION" \
  --hosted-zone-id "$HOSTED_ZONE_ID"
```

Inspect the configuration:

```bash
aws route53 get-dnssec \
  --hosted-zone-id "$HOSTED_ZONE_ID" \
  --region "$AWS_REGION"
```

Once signing is enabled, retrieve the DS information provided by Route 53.

Configure the DS record at your domain registrar or in the appropriate parent hosted zone.

Do not consider DNSSEC fully operational until the chain of trust is established and independently validated.

### Lab 8 — Verify DNSSEC Using dig

Objective: Verify DNSKEY, DS, RRSIG, and DNSSEC validation.

Start by querying your domain:

```bash
dig example.com A +dnssec
```

Inspect DNSSEC records:

```bash
dig example.com DNSKEY
dig example.com DS
dig example.com A +dnssec
```

Inspect the DNS resolution path:

```bash
dig +trace example.com
```

Use a validating public resolver:

```bash
dig @1.1.1.1 example.com A +dnssec
```

Inspect the `ad` flag in the response.

You can also use external DNSSEC validation tools, such as:

* [DNSViz](https://dnsviz.net/?utm_source=chatgpt.com) — Visualizes DNSSEC chains and identifies configuration problems.

* [Verisign DNSSEC Analyzer](https://dnssec-analyzer.verisignlabs.com/?utm_source=chatgpt.com) — Analyzes DNSSEC configuration.

Your objective is to verify:

* DNSKEY records are published.

* RRSIG records are present.

* The parent zone contains the correct DS record.

* The chain of trust is valid.

* A validating resolver successfully authenticates the DNS response.

### Lab 9 — Troubleshoot DNSSEC Configuration Errors

Objective: Understand how DNSSEC misconfiguration affects production DNS resolution.

Investigate these scenarios in a controlled environment:

| Scenario                 | Expected behavior                          |
| ------------------------ | ------------------------------------------ |
| Missing DS record        | Chain of trust is incomplete               |
| Incorrect DS record      | DNSSEC validation fails                    |
| KMS key disabled         | KSK signing operations are affected        |
| Incorrect KMS key policy | Route 53 cannot use the KMS key correctly  |
| Incorrect key rotation   | DNSSEC validation may fail                 |
| DNSSEC signing disabled  | DNSSEC signatures are no longer maintained |

Useful commands:

```bash
# Inspect DNSSEC configuration
aws route53 get-dnssec \
  --hosted-zone-id "$HOSTED_ZONE_ID"

# Inspect hosted zone records
aws route53 list-resource-record-sets \
  --hosted-zone-id "$HOSTED_ZONE_ID"

# Inspect KMS key
aws kms describe-key \
  --key-id "$KMS_KEY_ARN"

# Inspect DNSKEY
dig example.com DNSKEY

# Inspect DS
dig example.com DS

# Inspect DNSSEC signatures
dig example.com A +dnssec

# Trace DNS delegation
dig +trace example.com
```

Also inspect CloudWatch metrics and alarms for DNSSEC-related failures.

Production warning: Never deliberately remove a production DS record, disable a production KMS key, or break a production KSK to test recovery. Use a separate test domain and hosted zone.

### Module 6 — Key Takeaways

By completing this module, you should understand the distinction between DNS filtering and DNS authentication.

| Technology             | Main responsibility                              |
| ---------------------- | ------------------------------------------------ |
| DNS Firewall           | Controls which domains workloads can resolve     |
| Domain lists           | Define trusted and unwanted domains              |
| Rule groups            | Organize reusable DNS filtering policies         |
| ALLOW                  | Permits matching DNS queries                     |
| BLOCK                  | Blocks matching DNS queries                      |
| ALERT                  | Allows matching queries and records alerts       |
| Resolver query logging | Provides DNS visibility                          |
| DNSSEC                 | Authenticates DNS data cryptographically         |
| KSK                    | Signs the DNSKEY record set                      |
| ZSK                    | Signs other DNS record sets                      |
| DS                     | Establishes trust between parent and child zones |
| AWS KMS                | Provides cryptographic operations for the KSK    |

One particularly important architectural distinction:

DNS Firewall protects your workloads from resolving unwanted domains, while DNSSEC helps clients verify that DNS responses are authentic. Neither replaces HTTPS, network security controls, or comprehensive threat detection.

### Official AWS documentation

For further technical reference:

* [How Resolver DNS Firewall works](https://docs.aws.amazon.com/hi_in/Route53/latest/DeveloperGuide/resolver-dns-firewall-overview.html?utm_source=chatgpt.com).

* [Getting started with Resolver DNS Firewall](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-getting-started.html?utm_source=chatgpt.com).

* [AWS Managed Domain Lists](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-dns-firewall-managed-domain-lists.html?utm_source=chatgpt.com).

* [Resolver query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs.html?utm_source=chatgpt.com).

* [Enabling DNSSEC signing and establishing a chain of trust](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-enable-signing.html?utm_source=chatgpt.com).

* [KMS key and ZSK management in Route 53](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-configuring-dnssec-zsk-management.html?utm_source=chatgpt.com).

Next: Module 7 — Route 53 Traffic Management and Advanced Architectures. This will build on the routing policies and health checks from earlier modules to design multi-region, multi-account, and highly available DNS architectures.
