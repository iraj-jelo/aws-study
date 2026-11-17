### AWS Route 53 — Complete Course Outline

### Course Overview

This course provides a practical, in-depth understanding of Amazon Route 53, from DNS fundamentals to production-grade DNS architectures, routing policies, health checks, hybrid DNS, and multi-region application deployments.

The course uses Pulumi (Python) for infrastructure as code and Bash for CLI commands and automation scripts.

All labs will use AWS CLI, Pulumi, and Python where appropriate.

### Module 1 — DNS Fundamentals and Route 53 Architecture

* DNS fundamentals: hierarchical namespace, DNS zones, resolvers, and authoritative name servers.

* DNS resolution process: recursive versus iterative queries.

* DNS records: A, AAAA, CNAME, MX, TXT, NS, SOA, SRV, and CAA.

* DNS TTL, caching, negative caching, and propagation.

* Public DNS versus private DNS.

* Amazon Route 53 architecture and global infrastructure.

* Hosted zones, record sets, name servers, and domain registration.

* Route 53 Resolver and its role in DNS resolution.

* DNS over UDP and TCP, port 53, and EDNS.

* Route 53 pricing fundamentals and query billing.

Labs:

* Install and configure AWS CLI and Pulumi.

* Explore DNS resolution using `dig`, `nslookup`, and `host`.

* Inspect DNS records and authoritative name servers.

* Create a public hosted zone using Pulumi.

* Configure DNS records and inspect their resolution.

* Explore hosted zone properties and Route 53 CLI commands.

### Module 2 — Hosted Zones, DNS Records, and Domain Management

* Public hosted zones and their architecture.

* Private hosted zones and VPC associations.

* Hosted zone delegation and authoritative name servers.

* Registering domains through Route 53.

* Domain registration, renewal, transfer, and expiration.

* DNS record types and their use cases.

* Alias records versus CNAME records.

* Route 53 Alias support for AWS resources.

* Apex domain restrictions and alias record behavior.

* Weighted and simple record configurations.

* Record creation, modification, and deletion.

* Importing existing Route 53 resources into Pulumi.

* Managing hosted zones across Pulumi stacks.

Labs:

* Register or use an existing domain for DNS configuration.

* Create public and private hosted zones using Pulumi.

* Configure A, AAAA, CNAME, MX, TXT, and CAA records.

* Configure Alias records pointing to an Application Load Balancer.

* Delegate a subdomain to another hosted zone.

* Manage DNS records using AWS CLI and Pulumi.

* Import an existing hosted zone into Pulumi state.

### Module 3 — Route 53 Routing Policies

* Simple routing policy and its limitations.

* Weighted routing policy and traffic distribution.

* Latency-based routing and AWS regional latency measurements.

* Failover routing policy and primary/secondary configurations.

* Geolocation routing and geographic traffic distribution.

* Geoproximity routing and traffic bias.

* IP-based routing policies and CIDR collections.

* Multivalue answer routing.

* Routing policies versus load balancing.

* Routing policy combinations and record-set configuration.

* DNS caching implications for routing decisions.

* Choosing routing policies for different application architectures.

Labs:

* Configure simple routing for a web application.

* Implement weighted routing between two ALBs.

* Perform gradual traffic shifting using weighted records.

* Configure latency-based routing across AWS regions.

* Implement primary/secondary failover routing.

* Configure geolocation routing for different geographic regions.

* Experiment with geoproximity routing and traffic bias.

* Implement IP-based routing using CIDR collections.

* Compare DNS responses across routing policies using `dig`.

### Module 4 — Route 53 Health Checks and DNS Failover

* Route 53 health-check architecture.

* Endpoint health checks and supported protocols.

* HTTP, HTTPS, and TCP health checks.

* String matching and response validation.

* Health-check intervals, failure thresholds, and status evaluation.

* Calculated health checks and combining multiple health checks.

* CloudWatch alarm-based health checks.

* Health-check regions and distributed monitoring.

* Health checks associated with DNS records.

* Primary and secondary failover configurations.

* Active-active and active-passive architectures.

* DNS failover limitations and recovery considerations.

* Health-check monitoring and CloudWatch integration.

Labs:

* Create HTTP and HTTPS health checks.

* Configure health checks for application endpoints.

* Implement calculated health checks.

* Integrate CloudWatch alarms with Route 53 health checks.

* Build a primary/secondary failover architecture.

* Simulate application failures and observe DNS responses.

* Monitor health-check status through AWS CLI.

* Investigate DNS caching and failover recovery behavior.

### Module 5 — Private Hosted Zones and Hybrid DNS with Route 53 Resolver

* Private hosted zone architecture.

* VPC association and DNS resolution requirements.

* VPC DNS attributes: `enableDnsSupport` and `enableDnsHostnames`.

* Split-horizon DNS and internal/external DNS namespaces.

* Route 53 Resolver architecture.

* Resolver inbound endpoints.

* Resolver outbound endpoints.

* Resolver forwarding rules and rule associations.

* Conditional DNS forwarding.

* DNS resolution between multiple VPCs.

* Hybrid DNS integration with on-premises environments.

* DNS forwarding loops and troubleshooting.

* Route 53 Resolver security considerations.

Labs:

* Create private hosted zones using Pulumi.

* Associate private hosted zones with multiple VPCs.

* Configure internal service DNS records.

* Build Resolver inbound and outbound endpoints.

* Configure conditional forwarding rules.

* Simulate an on-premises DNS environment using a Linux DNS server.

* Implement hybrid DNS resolution between AWS and a simulated on-premises network.

* Troubleshoot DNS forwarding and resolution failures.

### Module 6 — Route 53 Resolver DNS Firewall and DNS Security

* DNS security fundamentals and common DNS threats.

* DNS Firewall architecture and capabilities.

* DNS Firewall rule groups.

* Domain lists and managed domain lists.

* Allow, block, and alert actions.

* DNS Firewall rule priorities and evaluation order.

* VPC associations and firewall policies.

* DNS Firewall logging and monitoring.

* DNSSEC fundamentals and cryptographic DNS validation.

* DNSSEC signing for public hosted zones.

* Key-signing keys (KSK) and zone-signing keys (ZSK).

* Route 53 DNSSEC signing and key management with AWS KMS.

* DNSSEC validation and DS records.

* DNSSEC troubleshooting and operational considerations.

Labs:

* Create DNS Firewall domain lists.

* Configure DNS Firewall rule groups.

* Block malicious and unwanted domain queries.

* Configure alert-only DNS Firewall rules.

* Associate firewall rule groups with VPCs.

* Enable DNS Firewall logging and inspect query logs.

* Enable DNSSEC signing for a public hosted zone.

* Verify DNSSEC using `dig +dnssec` and external DNS validation tools.

* Troubleshoot DNSSEC configuration errors.

### Module 7 — Route 53 Traffic Management and Advanced Architectures

* Route 53 traffic-flow concepts.

* Traffic Flow policies and visual policy management.

* Traffic Flow policy records and versioning.

* DNS-based traffic management across multiple AWS regions.

* Combining latency, weighted, geolocation, and failover routing.

* Multi-region application architectures.

* Active-active and active-passive deployments.

* Integration with ALB, NLB, CloudFront, API Gateway, and S3.

* Route 53 health checks and AWS service endpoints.

* Multi-account DNS architecture.

* Cross-account hosted-zone management.

* Centralized DNS management patterns.

* Route 53 ARC and DNS failover considerations.

Labs:

* Design a multi-region application DNS architecture.

* Route traffic between regional ALBs.

* Combine weighted and latency-based routing.

* Build a multi-region active-active architecture.

* Implement a multi-region active-passive architecture.

* Configure DNS records for CloudFront distributions.

* Delegate subdomains across AWS accounts.

* Automate DNS infrastructure across multiple Pulumi stacks.

### Module 8 — DNS Monitoring, Logging, Troubleshooting, and Cost Optimization

* Route 53 query logging.

* DNS query logging for public and private hosted zones.

* Route 53 Resolver query logging.

* Integration with CloudWatch Logs.

* Integration with Amazon S3 and centralized log storage.

* CloudTrail management events and Route 53 API auditing.

* Route 53 metrics and CloudWatch monitoring.

* Health-check monitoring and alarm configuration.

* DNS troubleshooting methodologies.

* Common DNS resolution failures and their causes.

* Debugging delegation, TTL, caching, and record configuration.

* Troubleshooting private DNS and Resolver endpoints.

* DNS propagation versus caching misconceptions.

* Route 53 pricing: hosted zones, queries, health checks, and Resolver endpoints.

* Query volume optimization and TTL trade-offs.

* Operational monitoring and alerting strategies.

Labs:

* Enable Route 53 query logging.

* Configure Resolver query logging.

* Analyze DNS queries using CloudWatch Logs Insights.

* Track Route 53 changes through CloudTrail.

* Create CloudWatch dashboards and alarms.

* Troubleshoot common DNS resolution failures.

* Investigate DNS latency and caching behavior.

* Analyze Route 53 usage and estimate monthly costs.

* Build Bash scripts for DNS diagnostics and operational monitoring.

### Module 9 — Production Route 53 Automation and Capstone Project

* Route 53 resource management with Pulumi.

* Pulumi project structure, stacks, configuration, and secrets.

* Managing hosted zones and DNS records as reusable components.

* Dynamic DNS record management.

* Pulumi state management and resource imports.

* Infrastructure deployment and change previews.

* DNS automation using AWS CLI and Bash.

* Route 53 API automation with Python and Boto3.

* DNS record synchronization and reconciliation.

* Safe DNS migrations and delegation changes.

* Blue-green deployments using weighted routing.

* Multi-region disaster recovery architecture.

* Multi-account DNS governance and operational practices.

* Production DNS security, availability, and cost considerations.

Capstone Lab — Production-Grade Multi-Region DNS Architecture

Build a production-style DNS infrastructure with the following components:

![Manual Failover and Failback Strategy with Amazon Route53 | Networking & Content Delivery](https://images.openai.com/static-rsc-4/Dxv52zQxry-AxQHqESifZTji4MsPkWYIweIDPz4h1ExnpzR75nybChZsmGXx-siBN-dFM6_yNFkeS8wTpRntNHLn8f5y-6S2u8hiSLBodwAzVje_IaYAokSzKkFRHNY_SdMNB19zphAaFso3xRrxMESo9JJqFmIyZ5OXBpveSEZA1eFOgRRRsRXB-Jriivm-?purpose=fullsize)

* A public hosted zone managed through Pulumi.

* Two AWS regions hosting separate application environments.

* Regional ALBs distributing traffic to application instances or ECS services.

* Latency-based routing for normal traffic distribution.

* Health checks and failover routing for regional failures.

* Weighted routing for controlled blue-green deployments.

* A private hosted zone for internal service discovery.

* Route 53 Resolver for hybrid DNS integration.

* DNS Firewall for outbound DNS protection.

* CloudWatch logging, monitoring, and operational alarms.

* Bash scripts for DNS diagnostics and deployment automation.

* Pulumi components for reusable and repeatable infrastructure.

Final architecture: A multi-region AWS application with automated DNS management, regional traffic distribution, health-based failover, private service discovery, and centralized monitoring.

### Recommended course technology stack

| Component              | Technology                    |
| ---------------------- | ----------------------------- |
| Infrastructure as Code | Pulumi (Python)               |
| Cloud platform         | AWS                           |
| CLI                    | AWS CLI v2                    |
| Scripting              | Bash                          |
| DNS diagnostics        | dig, nslookup, host           |
| DNS automation         | Python + Boto3                |
| Monitoring             | CloudWatch                    |
| Logging                | CloudWatch Logs, S3           |
| DNS security           | Route 53 DNS Firewall, DNSSEC |
| Version control        | Git                           |

Course progression: DNS fundamentals → Hosted zones → Routing policies → Health checks → Private DNS → DNS security → Advanced architectures → Monitoring → Production automation.

The labs will build progressively toward the final multi-region architecture, reusing infrastructure where practical rather than creating unrelated standalone environments.
