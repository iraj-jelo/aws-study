Here’s a reusable prompt for creating a comprehensive, up-to-date AWS VPC course, following your preferences: no quizzes, Pulumi instead of Terraform whenever possible, and no deprecated or obsolete practices.

# Prompt: Create a Comprehensive AWS VPC Course

Act as a senior AWS networking architect, cloud infrastructure engineer, and technical instructor. Create a comprehensive, hands-on tutorial for **Amazon Virtual Private Cloud (Amazon VPC)**, progressing from fundamental networking concepts to advanced, production-grade AWS network architecture.

The course should teach me to design, implement, troubleshoot, secure, and operate AWS networks in real-world environments.

## 1. Teaching Requirements

- Teach the course sequentially, one module at a time. Start with Module 1 and wait for my instruction before proceeding to the next module.
- Assume I want deep technical understanding, not just a high-level overview.
- Explain networking concepts clearly, including the underlying mechanisms and how AWS implements them.
- Use realistic architectures, practical scenarios, ASCII diagrams, Mermaid diagrams when useful, CLI commands, configuration examples, and hands-on labs.
- Explain why a particular design is appropriate, its alternatives, its trade-offs, and its operational implications.
- Include common mistakes, troubleshooting techniques, security considerations, cost implications, and production best practices.
- Do not include quizzes, multiple-choice questions, knowledge checks, or repetitive exercises. They consume tokens without adding sufficient value.
- Avoid unnecessary repetition, filler, and overly long introductions. Prioritize useful technical content.

## 2. Technology and Currency Requirements

- Keep the material current as of the date the course is generated.
- Verify version-sensitive and service-specific claims against the latest official AWS documentation.
- Prefer current, generally available AWS capabilities and recommended architectural patterns.
- Do not teach deprecated services, obsolete workflows, outdated console procedures, or legacy networking patterns as recommended practice.
- If a legacy feature is necessary for migration or compatibility, label it clearly and explain its current status and modern alternative.
- Distinguish generally available features from preview, limited availability, and region-dependent features.
- Explain relevant quotas, regional limitations, IPv4/IPv6 support, and service-specific constraints when they materially affect a design.
- Cite authoritative AWS documentation for important or version-sensitive claims.

## 3. Infrastructure as Code

Use **Pulumi instead of Terraform whenever possible**.

Preferred tools:

- Pulumi with Python as the primary infrastructure-as-code approach.
- AWS CLI v2 for inspection, troubleshooting, and verification.
- Python and Boto3 for network-related automation and AWS API interaction.
- Docker for reproducible local tooling and application examples.
- GitHub Actions with OIDC federation for CI/CD examples when relevant.

For Pulumi examples:

- Use the current stable Pulumi AWS provider and supported APIs.
- Provide complete, runnable project structures when appropriate, including `Pulumi.yaml`, `__main__.py`, configuration, and dependency declarations.
- Explain resources, dependencies, outputs, configuration, secrets, state management, previews, updates, and destruction.
- Include deployment and verification commands.
- Use appropriate resource protection, retention, and deletion safeguards for important resources.
- Explain how to avoid accidentally exposing services or incurring unnecessary charges.
- Never substitute Terraform for Pulumi merely because a Terraform example is easier to find.

Use the AWS console only when it provides a useful learning advantage or when the relevant operation is better demonstrated there.

## 4. Course Curriculum

Build the course around the following modules. Adjust the ordering when necessary to create a coherent learning progression, and add missing topics that are important for professional AWS networking.

### Module 1 — Networking Foundations for AWS

- TCP/IP networking fundamentals and the OSI model where relevant.
- IPv4, IPv6, CIDR notation, subnet masks, and address calculations.
- Public vs. private IP addresses.
- Routing, next hops, default routes, and longest-prefix matching.
- Ethernet, ARP, DNS, TCP, UDP, ICMP, and MTU fundamentals.
- NAT, packet filtering, stateful vs. stateless filtering, and firewalls.
- How these concepts map to AWS networking.
- Address planning and avoiding overlapping CIDRs.

Lab: Design an IP addressing plan for a multi-environment AWS application.

### Module 2 — Amazon VPC Fundamentals

- What an Amazon VPC is and how it differs from a traditional virtual network.
- Regional VPCs and Availability Zone-scoped resources.
- Default VPCs vs. custom VPCs.
- VPC CIDR blocks, secondary CIDRs, and IPv6 addressing.
- Subnets, route tables, and subnet associations.
- VPC attributes, DNS resolution, and DNS hostnames.
- Network interface fundamentals and private IP assignment.
- AWS-managed infrastructure and the shared responsibility model.

Lab: Create a custom VPC with Pulumi and inspect its resources using the AWS CLI.

### Module 3 — Subnets, Routes, and Internet Connectivity

- Public, private, and isolated subnet design.
- Main route tables and explicit route-table associations.
- Internet gateways and default routes.
- Elastic IP addresses and their current usage model.
- Public IPv4 addressing and automatic public IP assignment.
- IPv6 internet connectivity and egress-only internet gateways.
- Route propagation and static routes.
- Route precedence and troubleshooting unexpected paths.
- Multi-AZ subnet architecture.

Lab: Build a multi-AZ VPC with public, private, and isolated subnets using Pulumi.

### Module 4 — NAT and Outbound Connectivity

- NAT gateways and their supported deployment patterns.
- NAT gateways per Availability Zone and cross-AZ traffic trade-offs.
- NAT instances: legacy context, limitations, and when to recognize existing deployments.
- IPv4 outbound access from private subnets.
- IPv6 outbound connectivity and egress-only internet gateways.
- Private service access without general internet egress.
- NAT gateway data processing and regional data-transfer costs.
- Highly available egress architectures.
- Troubleshooting outbound connections.

Lab: Give private workloads controlled outbound connectivity and compare cost, availability, and routing behavior.

### Module 5 — Security Groups and Network ACLs

- Security group fundamentals and ENI association.
- Stateful connection tracking and return traffic.
- Network ACL rules, numbering, and stateless filtering.
- Security groups vs. network ACLs.
- Rule evaluation, ephemeral ports, and common protocol requirements.
- Security group references and layered security.
- Least privilege and segmentation patterns.
- VPC Flow Logs for network troubleshooting.
- Troubleshooting timeouts, rejected traffic, and asymmetric paths.

Lab: Secure a multi-tier application with separate load-balancer, application, and database security groups.

### Module 6 — DNS and Private Name Resolution

- Amazon Route 53 and Route 53 Resolver.
- VPC DNS resolution and DNS hostnames.
- Private hosted zones and VPC associations.
- Public vs. private DNS resolution.
- DNS forwarding, inbound endpoints, and outbound endpoints.
- Resolver rules and hybrid DNS.
- DNS Firewall and DNS security controls.
- Split-horizon DNS.
- Diagnosing DNS failures and resolution paths.

Lab: Configure private DNS for internal services and validate name resolution from application workloads.

### Module 7 — VPC Endpoints and Private AWS Service Access

- Gateway endpoints for supported AWS services.
- Interface endpoints powered by AWS PrivateLink.
- Endpoint policies and their interaction with IAM.
- Private DNS for interface endpoints.
- Endpoint security groups and subnet placement.
- Private access to services such as S3, DynamoDB, ECR, CloudWatch, and Systems Manager where supported.
- PrivateLink for exposing and consuming services across VPC boundaries.
- Endpoint quotas, availability, and cost considerations.
- Designing workloads without general-purpose internet egress.

Lab: Configure private access to selected AWS services and verify that workloads do not need a NAT gateway for those paths.

### Module 8 — VPC Peering and Transit Gateway

- VPC peering architecture and routing limitations.
- Non-transitive routing and overlapping CIDR restrictions.
- Inter-Region VPC peering.
- AWS Transit Gateway architecture.
- Transit Gateway attachments, route tables, propagation, and associations.
- Segmentation using multiple Transit Gateway route tables.
- Centralized inspection and shared-services network designs.
- Transit Gateway peering and regional network topologies.
- Cost, availability, and operational trade-offs.

Lab: Connect multiple VPCs using both peering and Transit Gateway, then compare their routing and isolation properties.

### Module 9 — Hybrid Connectivity

- Site-to-Site VPN and IPsec fundamentals.
- AWS Direct Connect and dedicated or hosted connectivity models.
- Direct Connect gateways and transit virtual interfaces.
- Virtual private gateways and Transit Gateway integration.
- BGP, autonomous system numbers, route advertisements, and failover.
- Redundant tunnels and connection resilience.
- Hybrid DNS and address planning.
- Encryption, routing asymmetry, MTU, and troubleshooting.
- High availability and hybrid connectivity costs.

Lab: Design a hybrid AWS network and, where practical, implement a VPN-based lab using available resources.

### Module 10 — Load Balancing and Application Networking

- How VPC networking supports Elastic Load Balancing.
- Application, Network, and Gateway Load Balancers.
- Public vs. internal load balancers.
- Target registration, health checks, and security group relationships.
- Cross-zone load balancing and Availability Zone behavior.
- TLS termination and network traffic paths.
- Integration with private subnets and application tiers.
- Connection draining, health-check troubleshooting, and failure analysis.

Lab: Deploy a private application behind an appropriately scoped load balancer.

### Module 11 — IPv6 and Modern IP Address Management

- Dual-stack vs. IPv6-only architectures.
- IPv6 CIDR allocation and subnet design.
- IPv6 addressing, routing, security, and outbound access.
- Egress-only internet gateways.
- DNS considerations for IPv6-enabled workloads.
- NAT64/DNS64 and applicable AWS service constraints.
- IPv4 exhaustion and public IPv4 cost considerations.
- Amazon VPC IP Address Manager (IPAM).
- Centralized IP allocation, utilization tracking, and CIDR governance.
- Planning IPv6 adoption and migration.

Lab: Add IPv6 to an existing VPC and verify connectivity, security, and DNS behavior.

### Module 12 — VPC Observability and Troubleshooting

- VPC Flow Logs and their limitations.
- CloudWatch metrics and logging.
- Reachability Analyzer.
- Network Access Analyzer.
- Network Manager and applicable network visualization capabilities.
- Route analysis, security group analysis, and packet-path reasoning.
- DNS diagnostics.
- Traffic Mirroring where appropriate.
- Diagnosing intermittent connectivity, MTU problems, routing mistakes, and dropped packets.
- Separating network failures from IAM, application, and DNS failures.

Lab: Investigate several realistic connectivity failures using AWS tools and CLI commands.

### Module 13 — Advanced VPC Architecture

- Multi-account networking with AWS Organizations.
- Centralized networking and shared-services VPCs.
- Hub-and-spoke, mesh, and segmented network topologies.
- AWS Cloud WAN and Transit Gateway: when to choose each.
- Centralized inspection using supported AWS network security services.
- AWS Network Firewall and routing design.
- Ingress and egress control architectures.
- Network segmentation for development, staging, and production.
- Cross-Region connectivity and disaster recovery.
- Resilience, fault isolation, and blast-radius reduction.
- Multi-account IPAM and governance.
- Architecture decisions involving cost, complexity, security, and operations.

Lab: Design a multi-account network for a SaaS platform with centralized inspection, shared services, and isolated production workloads.

### Module 14 — VPC for Containers and Kubernetes

- VPC networking for Amazon ECS and Amazon EKS.
- Amazon VPC CNI and Kubernetes pod addressing.
- Pod networking modes and supported alternatives.
- Security groups for pods where supported.
- Subnet sizing, IP exhaustion, and prefix delegation.
- Public and private EKS endpoint access.
- Load balancers and AWS Load Balancer Controller networking.
- Cluster egress and private access to AWS APIs.
- Network policies and the distinction between AWS and Kubernetes enforcement.
- VPC design for multiple clusters and tenants.
- Troubleshooting pod-to-pod, pod-to-service, and pod-to-AWS-service connectivity.

Lab: Design an EKS network and diagnose a pod connectivity issue.

### Module 15 — Pulumi and Production Network Operations

- Structuring reusable Pulumi components for VPC infrastructure.
- Managing configuration, secrets, and stack separation.
- Reusable networking components and environment-specific configuration.
- Dependency management and resource replacement risks.
- Importing existing infrastructure and managing drift.
- Previewing and reviewing changes safely.
- Protecting critical resources and handling deletion.
- GitHub Actions OIDC-based deployment identities.
- Policy as code and network configuration guardrails.
- Automated validation and security checks.
- Cost estimation, tagging, and operational documentation.
- Safe changes to routes, subnets, endpoints, and connectivity.

Lab: Build a reusable Pulumi networking project with separate development and production stacks.

### Module 16 — Capstone Production Architecture

Design and implement a secure AWS network for a realistic SaaS platform.

Requirements:

- Separate development, staging, and production environments.
- Multi-AZ application subnets.
- Public ingress through a suitable load balancer.
- Private application and database tiers.
- Controlled outbound connectivity.
- Private access to selected AWS services.
- Centralized DNS and logging where appropriate.
- Network segmentation and least-privilege security rules.
- Infrastructure deployed with Pulumi.
- CI/CD using short-lived AWS credentials.
- Documented routing, availability, and security decisions.
- Cost analysis and operational runbooks.
- Failure scenarios and troubleshooting procedures.

Provide architecture diagrams, Pulumi source code, deployment commands, verification procedures, security review, and cleanup instructions.

## 5. Required Format for Each Module

Structure each module as follows:

1. **Learning objectives:** Briefly describe what I will be able to design or implement.
2. **Concepts and architecture:** Explain the relevant networking mechanisms and AWS abstractions.
3. **Diagrams:** Show traffic paths, routing, trust boundaries, and resource relationships.
4. **Configuration and code:** Include realistic Pulumi Python examples, AWS CLI commands, and relevant configuration files.
5. **Hands-on lab:** Provide ordered steps, prerequisites, expected outcomes, and verification commands.
6. **Troubleshooting:** Explain common failures, their causes, and systematic diagnostic procedures.
7. **Security and production considerations:** Cover least privilege, resilience, operational risks, and cost.
8. **References:** Link to relevant official AWS documentation.

Do not force every section into every lesson if it adds no value. Keep related concepts together and avoid repeating explanations already covered.

## 6. Lab and Cost-Safety Requirements

- Prefer small, isolated, reproducible lab environments.
- Identify billable resources before deployment, including NAT gateways, interface endpoints, public IPv4 addresses, Transit Gateways, load balancers, VPNs, and data transfer.
- Do not claim that an AWS lab is free unless its costs and applicable Free Tier eligibility have been verified.
- Explain regional and Availability Zone constraints.
- Include cleanup instructions, but explicitly identify persistent resources and potential data loss.
- Avoid exposing administrative services directly to the public internet.
- Use least-privilege permissions for deployment and application identities.
- Do not assume LocalStack or another emulator reproduces every real AWS networking behavior.
- Clearly distinguish locally simulated labs from labs that require actual AWS infrastructure.

## 7. Expected Outcome

By completing this course, I should be able to:

- Explain AWS VPC routing and packet flows in detail.
- Design secure, highly available VPC architectures.
- Implement AWS networking infrastructure using Pulumi and Python.
- Troubleshoot connectivity, DNS, routing, and security failures systematically.
- Design private service access and hybrid connectivity.
- Build networking foundations for production ECS and EKS workloads.
- Evaluate architectural trade-offs involving security, reliability, cost, and complexity.
- Review and operate AWS networking infrastructure in production.

**Begin with Module 1, Lesson 1. Teach one module at a time, and wait for me to request the next module. Do not include quizzes.**

Suggested usage: Paste this prompt into a new conversation. Then proceed with requests such as “Go ahead with Module 1,” “Continue with Module 2,” or “Check whether Module 5 covers all the topics in the curriculum.”