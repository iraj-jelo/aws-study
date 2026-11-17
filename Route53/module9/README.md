Module 9 — Production Route 53 Automation and Capstone Project

(Advanced) (Pulumi + Python + Bash)

1. Introduction

So far, we've covered Route 53's major capabilities: hosted zones, DNS records, routing policies, health checks, private DNS, hybrid DNS, DNS Firewall, and monitoring.

In this final module, we'll bring those concepts together and focus on how Route 53 is managed in real production environments.

In production, manually creating DNS records through the AWS Console isn't a sustainable approach. DNS infrastructure needs to be:

- Automated: DNS records and hosted zones should be managed through infrastructure as code.
- Repeatable: The same DNS architecture should be deployable across environments and AWS accounts.
- Version-controlled: Every infrastructure change should be traceable.
- Safe: DNS changes should avoid accidental outages and unintended traffic shifts.
- Observable: DNS resolution, health checks, and infrastructure changes should be monitored.
- Recoverable: DNS configurations should support disaster recovery and regional failover.

We'll use three primary technologies:

Technology	Responsibility

Pulumi	Infrastructure provisioning and lifecycle management
AWS CLI + Bash	Operational automation and diagnostics
Python + Boto3	Programmatic DNS management and reconciliation


Let's start with the infrastructure automation architecture.


---

2. Route 53 Resource Management with Pulumi

2.1 Why use Pulumi for Route 53?

Pulumi allows us to define AWS infrastructure using general-purpose programming languages such as Python, TypeScript, Go, and C#.

Instead of manually creating hosted zones and DNS records, we define the desired infrastructure in code.

For example, suppose we need:

- One public hosted zone.
- One private hosted zone.
- Several DNS records.
- A health check.
- Multiple routing policies.

We can describe all these resources in a Pulumi project.

Pulumi communicates with AWS APIs through its AWS provider and manages the infrastructure lifecycle.

The general workflow is:

Pulumi Python Program

Declare the desired DNS infrastructure

Pulumi Engine

Compare program definitions with recorded state

AWS Provider

Execute the required AWS API operations

Amazon Route 53

Hosted zones, records, health checks, and routing policies

Pulumi also tracks the resources it manages, allowing it to determine which resources need to be created, updated, replaced, or deleted.

2.2 Installing Pulumi and configuring AWS

For this module, we'll use Python.

Install Pulumi and the AWS SDK:

curl -fsSL https://get.pulumi.com | sh

pip install pulumi pulumi-aws boto3

Configure AWS credentials:

aws configure

Alternatively, use an existing AWS CLI profile:

export AWS_PROFILE=production
export AWS_REGION=us-east-1

Check the identity:

aws sts get-caller-identity

This is important because DNS infrastructure is often managed through dedicated deployment accounts or administrative roles.

For production deployments, prefer short-lived credentials obtained through IAM roles or AWS IAM Identity Center rather than long-lived access keys.

2.3 Creating a Pulumi project

Create a project:

mkdir route53-infrastructure
cd route53-infrastructure

pulumi new aws-python

A typical project structure looks like this:

route53-infrastructure/
├── __main__.py
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── Pulumi.production.yaml
├── requirements.txt
└── components/
    ├── __init__.py
    ├── hosted_zone.py
    ├── dns_records.py
    └── health_checks.py

The __main__.py file is the main entry point.

The components/ directory contains reusable infrastructure definitions.

The Pulumi stack configuration files contain environment-specific settings.

For example:

- Development may use dev.example.com.
- Staging may use staging.example.com.
- Production may use example.com.

This makes it possible to maintain separate environments without duplicating the entire infrastructure implementation.

2.4 Creating a public hosted zone

Let's create a public hosted zone using Pulumi.

import pulumi
import pulumi_aws as aws

zone = aws.route53.Zone(
    "production-zone",
    name="example.com",
    comment="Production public hosted zone",
)

pulumi.export("zone_id", zone.zone_id)
pulumi.export("name_servers", zone.name_servers)

Deploy it:

pulumi stack init production

pulumi preview
pulumi up

Pulumi creates the hosted zone and exports its ID and authoritative name servers.

Important: Creating a hosted zone does not automatically make it authoritative for your domain. You must configure the domain's delegation at its registrar or parent DNS zone.

For an existing domain, update its NS records at the registrar to point to the name servers returned by Route 53.

2.5 Creating DNS records

We can define records using aws.route53.Record.

www_record = aws.route53.Record(
    "www-record",
    zone_id=zone.zone_id,
    name="www.example.com",
    type="A",
    ttl=300,
    records=["203.0.113.10"],
)

This creates:

www.example.com.  300  IN  A  203.0.113.10

We can also create multiple records dynamically using Python:

records = {
    "api": "203.0.113.20",
    "app": "203.0.113.30",
    "admin": "203.0.113.40",
}

for hostname, address in records.items():
    aws.route53.Record(
        f"{hostname}-record",
        zone_id=zone.zone_id,
        name=f"{hostname}.example.com",
        type="A",
        ttl=300,
        records=[address],
    )

This is one of the biggest advantages of using Pulumi: we can use Python loops, dictionaries, functions, classes, and configuration files to generate infrastructure.

Instead of writing hundreds of nearly identical DNS resource definitions, we can describe the desired records as data and generate them programmatically.


---

3. Pulumi Project Structure, Stacks, Configuration, and Secrets

Production DNS infrastructure usually has multiple environments.

For example:

Environment	Domain	Purpose

Development	dev.example.com	Development services
Staging	staging.example.com	Pre-production testing
Production	example.com	Customer-facing services


We don't want to maintain three independent implementations.

Instead, we create one reusable Pulumi project and use different stacks and configurations.

3.1 Pulumi stacks

A Pulumi stack is an isolated instance of a project.

Each stack has its own:

- Configuration.
- Infrastructure state.
- Resource outputs.
- Deployment history.

Create stacks:

pulumi stack init dev
pulumi stack init staging
pulumi stack init production

Select the production stack:

pulumi stack select production

Inspect the selected stack:

pulumi stack

This separation is particularly important when managing DNS infrastructure because accidentally applying development settings to production can cause significant availability problems.

3.2 Pulumi configuration

Instead of hardcoding domains and other environment-specific values, use configuration.

For example:

pulumi config set domain example.com
pulumi config set environment production
pulumi config set aws:region us-east-1

Read these values in Python:

import pulumi

config = pulumi.Config()

domain = config.require("domain")
environment = config.require("environment")

Now the same code can deploy different environments.

3.3 Pulumi secrets

Some infrastructure configurations contain sensitive information.

Examples include:

- API credentials.
- Private application configuration.
- DNS automation credentials.
- External DNS provider tokens.

Pulumi supports encrypted configuration values.

pulumi config set external-dns-token "secret-value" --secret

Retrieve the secret:

token = config.require_secret("external-dns-token")

Pulumi encrypts secret configuration in its state and configuration storage using its configured secrets provider.

For production environments, you should understand:

- Pulumi's default secrets provider.
- Passphrase-based encryption.
- Cloud-based secrets providers.
- AWS KMS integration.
- Secret rotation.
- Access permissions for state storage.

Never commit plaintext secrets or production credentials to Git.

3.4 Reusable Pulumi components

As your DNS infrastructure grows, putting everything in __main__.py becomes difficult to maintain.

We can create reusable components.

For example, a hosted-zone component:

import pulumi
import pulumi_aws as aws

class HostedZone(pulumi.ComponentResource):

    def __init__(self, name, domain, opts=None):
        super().__init__(
            "custom:route53:HostedZone",
            name,
            None,
            opts,
        )

        self.zone = aws.route53.Zone(
            f"{name}-zone",
            name=domain,
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.zone_id = self.zone.zone_id

        self.register_outputs({
            "zone_id": self.zone_id,
        })

Use it in the main program:

production_zone = HostedZone(
    "production",
    "example.com",
)

pulumi.export(
    "production_zone_id",
    production_zone.zone_id,
)

The benefit is that we can reuse the same component across development, staging, and production environments.

Other useful components include:

- DnsRecords
- HealthCheck
- WeightedRouting
- LatencyRouting
- PrivateHostedZone
- ResolverEndpoint
- DnsFirewall

This is especially useful when building infrastructure for multiple AWS accounts.


---

4. Dynamic DNS Record Management

Dynamic DNS record management means creating, updating, and removing DNS records programmatically based on application or infrastructure requirements.

Consider a SaaS application with multiple services:

api.example.com
auth.example.com
billing.example.com
storage.example.com
monitoring.example.com

As services are deployed, their DNS records need to be created or updated.

There are several approaches.

4.1 Infrastructure-driven DNS management

The simplest approach is to manage DNS records alongside the application infrastructure.

For example:

1. Pulumi creates an Application Load Balancer.
2. AWS returns its DNS name and hosted-zone ID.
3. Pulumi creates a Route 53 Alias record pointing to the ALB.
4. The application becomes accessible through its custom domain.

Conceptually:

Pulumi
  |
  +-- Create ALB
  |
  +-- Obtain ALB DNS name
  |
  +-- Create Route 53 Alias record
  |
  +-- api.example.com

The advantage is that the application infrastructure and DNS configuration have a consistent lifecycle.

If the ALB is replaced, Pulumi can update the corresponding DNS record.

4.2 Dynamic records using external configuration

We can also maintain records in a YAML or JSON file.

For example:

records:
  - name: api.example.com
    type: A
    ttl: 300
    values:
      - 203.0.113.10

  - name: auth.example.com
    type: A
    ttl: 300
    values:
      - 203.0.113.20

  - name: billing.example.com
    type: A
    ttl: 300
    values:
      - 203.0.113.30

Our Pulumi program can load this configuration and create the corresponding records.

This approach separates DNS data from infrastructure implementation.

It is useful when DNS records are maintained by a central platform team while application teams provide their own service endpoints.

4.3 Avoiding conflicting ownership

One important production principle is that a DNS record should have a clearly defined owner.

For example, suppose Pulumi manages:

api.example.com

But an external automation script also modifies the same record.

Now two independent systems are managing the same resource.

This can result in:

- Unexpected DNS changes.
- Configuration drift.
- Conflicting deployments.
- Difficult troubleshooting.
- Accidental record replacement.

A good rule is:

One authoritative management system per DNS record set.

You can still use multiple tools, but they should have clearly separated responsibilities.


---

5. Pulumi State Management and Resource Imports

5.1 Understanding Pulumi state

Pulumi maintains a state file that describes the resources managed by a stack.

The state contains information such as:

- Resource names and types.
- AWS resource identifiers.
- Resource dependencies.
- Configuration inputs.
- Provider information.
- Output values.

For example, a hosted zone may be represented by a Pulumi resource associated with an AWS hosted-zone ID.

Pulumi uses this information to compare the declared infrastructure with the previously deployed infrastructure.

This comparison determines which operations are necessary.

5.2 Previewing changes

Before modifying production DNS infrastructure, always inspect the proposed changes.

pulumi preview

Pulumi may report:

+ create
~ update
- delete
+- replace

These operations have different implications.

Operation	Meaning	DNS risk

Create	Create a resource	Usually low
Update	Modify an existing resource	Depends on the change
Delete	Remove a resource	Potential outage
Replace	Delete and recreate a resource	Potential disruption


For example, changing the target of a DNS record may be an update, while replacing a hosted zone can have serious consequences.

You should pay particular attention to replacements and deletions.

5.3 Importing existing hosted zones

Imagine your company already has a hosted zone created manually through the AWS Console.

You now want Pulumi to manage it.

You don't want Pulumi to create another hosted zone.

Instead, import the existing resource.

First, identify the hosted-zone ID:

aws route53 list-hosted-zones

Import it into the Pulumi project:

pulumi import \
  aws:route53/zone:Zone \
  production-zone \
  Z123456789EXAMPLE

Pulumi imports the existing AWS resource into its state.

After importing, update your Pulumi program to match the imported resource's actual configuration.

Then run:

pulumi preview

The goal is to achieve a deployment where Pulumi recognizes the existing resource rather than trying to recreate it.

5.4 State backends

For team environments, local state files are usually not appropriate.

Pulumi supports different state backends, including:

- Pulumi Cloud.
- AWS S3.
- Other supported object-storage backends.
- Local filesystem storage.

For an AWS-based organization, an S3 backend can be used for centralized state storage.

Example:

pulumi login s3://company-pulumi-state

The backend should have appropriate access controls, encryption, backups, and versioning.

Remember that Pulumi state can contain sensitive infrastructure information, even when secrets are encrypted.


---

6. Infrastructure Deployment and Change Previews

Production DNS changes deserve more caution than ordinary infrastructure changes.

A mistake in an application deployment might affect one service. A mistake in a central DNS zone can affect multiple applications or even an entire organization.

A production deployment workflow should look like this:

1. Developer modifies Pulumi code

   DNS configuration changes are committed to Git.

2. Continuous integration

   Run formatting, linting, and configuration validation.

3. Pulumi preview

   Generate the infrastructure change plan.

4. Review and approval

   Inspect DNS changes, deletions, replacements, and routing effects.

5. Pulumi deployment

   Apply approved changes to AWS.

6. Post-deployment verification

   Check DNS resolution, health checks, and application availability.

Typical commands:

pulumi stack select production

pulumi refresh

pulumi preview

pulumi up

pulumi refresh synchronizes Pulumi's recorded state with the actual infrastructure. It does not automatically reconcile all out-of-band changes back to the program's desired configuration.

This distinction matters:

- refresh updates the recorded state.
- preview identifies the difference between the program and refreshed state.
- up applies the changes required to reach the program's desired state.

For critical DNS changes, you can also save a reviewed deployment plan:

pulumi preview --save-plan production.plan

Then apply the saved plan:

pulumi up --plan production.plan

This helps ensure that the deployment applies the reviewed changes rather than an entirely new set of changes.


---

7. DNS Automation Using AWS CLI and Bash

Pulumi is responsible for infrastructure lifecycle management, but Bash and AWS CLI are useful for operational tasks.

Examples include:

- Checking DNS records.
- Inspecting hosted zones.
- Updating emergency DNS records.
- Validating DNS propagation.
- Investigating health-check status.
- Automating DNS diagnostics.

7.1 Listing hosted zones

aws route53 list-hosted-zones \
  --output table

Get details about one hosted zone:

aws route53 get-hosted-zone \
  --id Z123456789EXAMPLE

List records:

aws route53 list-resource-record-sets \
  --hosted-zone-id Z123456789EXAMPLE

7.2 Updating DNS records with Bash

The AWS CLI supports Route 53 record changes through change-resource-record-sets.

Create a JSON file:

cat > change-record.json <<'EOF'
{
  "Comment": "Update production API record",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "api.example.com",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [
          {
            "Value": "203.0.113.50"
          }
        ]
      }
    }
  ]
}
EOF

Apply the change:

CHANGE_ID=$(aws route53 change-resource-record-sets \
  --hosted-zone-id Z123456789EXAMPLE \
  --change-batch file://change-record.json \
  --query 'ChangeInfo.Id' \
  --output text)

Wait for Route 53 to report the change as synchronized:

aws route53 wait resource-record-sets-changed \
  --id "$CHANGE_ID"

The UPSERT operation is particularly useful because it creates a record if it doesn't exist or updates the existing record set.

However, INSYNC means the Route 53 change has propagated across its authoritative DNS infrastructure. It does not mean that every recursive resolver or client has discarded its cached DNS response.

7.3 DNS diagnostics with Bash

A simple diagnostic script:

#!/usr/bin/env bash

set -euo pipefail

DOMAIN="${1:?Usage: $0 domain-name}"

echo "Checking DNS for: $DOMAIN"

echo
echo "A records:"
dig "$DOMAIN" A +short

echo
echo "AAAA records:"
dig "$DOMAIN" AAAA +short

echo
echo "CNAME records:"
dig "$DOMAIN" CNAME +short

echo
echo "Name servers:"
dig "$DOMAIN" NS +short

echo
echo "DNS trace:"
dig "$DOMAIN" +trace

Run:

chmod +x dns-check.sh

./dns-check.sh api.example.com

This is useful during production incidents because it provides a quick overview of DNS resolution.

For deeper diagnostics, compare responses from:

- Authoritative name servers.
- The local recursive resolver.
- Public recursive resolvers.
- Internal VPC DNS resolvers.


---

8. Route 53 API Automation with Python and Boto3

AWS CLI is convenient for shell automation, but Python and Boto3 are better suited to more complex workflows.

Boto3 provides a Python interface to AWS services.

8.1 Creating a DNS record

import boto3

client = boto3.client("route53")

response = client.change_resource_record_sets(
    HostedZoneId="Z123456789EXAMPLE",
    ChangeBatch={
        "Comment": "Create API DNS record",
        "Changes": [
            {
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "api.example.com",
                    "Type": "A",
                    "TTL": 300,
                    "ResourceRecords": [
                        {"Value": "203.0.113.50"}
                    ],
                },
            }
        ],
    },
)

print(response["ChangeInfo"]["Id"])

8.2 Waiting for DNS changes

Route 53 changes are asynchronous.

The API returns a change ID, which can be used to check the deployment status.

import boto3

client = boto3.client("route53")

change_id = "/change/C123456789EXAMPLE"

waiter = client.get_waiter(
    "resource_record_sets_changed"
)

waiter.wait(
    Id=change_id,
    WaiterConfig={
        "Delay": 10,
        "MaxAttempts": 30,
    },
)

print("Route 53 change is INSYNC")

This is important when another automation step depends on the DNS change being synchronized.

For example, a deployment pipeline might:

1. Deploy a new application version.
2. Update the DNS record.
3. Wait for Route 53 synchronization.
4. Perform DNS verification.
5. Continue with post-deployment checks.

8.3 Listing DNS records

import boto3

client = boto3.client("route53")

paginator = client.get_paginator(
    "list_resource_record_sets"
)

for page in paginator.paginate(
    HostedZoneId="Z123456789EXAMPLE"
):
    for record in page["ResourceRecordSets"]:
        print(
            record["Name"],
            record["Type"],
        )

Using a paginator is important because hosted zones can contain thousands of record sets.

8.4 Handling errors

Production automation must handle AWS API failures.

Examples include:

- AccessDenied
- InvalidChangeBatch
- NoSuchHostedZone
- PriorRequestNotComplete
- API throttling.
- Network timeouts.

Use appropriate exception handling, retries with backoff where appropriate, logging, and explicit failure reporting.

Also remember that Boto3 can update Route 53 records independently of Pulumi. If both systems manage the same record, they can create configuration drift.


---

9. DNS Record Synchronization and Reconciliation

This is an important production concept.

Imagine your desired DNS configuration is:

api.example.com      → 203.0.113.10
auth.example.com     → 203.0.113.20
billing.example.com  → 203.0.113.30

But the actual Route 53 configuration is:

api.example.com      → 203.0.113.10
auth.example.com     → 203.0.113.25
billing.example.com  → 203.0.113.30
old.example.com      → 203.0.113.40

There are two problems:

1. auth.example.com has an incorrect target.
2. old.example.com is no longer part of the desired configuration.

This is called configuration drift.

9.1 Desired state versus actual state

A reconciliation system compares:

- Desired DNS configuration.
- Actual DNS configuration.

It identifies differences and determines what actions are needed.

Desired state

Git / Pulumi configuration


---

api → .10

auth → .20

billing → .30

Actual state

Route 53 records


---

api → .10

auth → .25

billing → .30

old → .40

Reconciliation

Identify and resolve differences

Correct auth and review removal of old.

Pulumi already implements much of this reconciliation model through its desired-state infrastructure management.

However, organizations sometimes build additional synchronization systems using Boto3.

9.2 Safe reconciliation

A good reconciliation process should:

1. Retrieve the desired configuration.
2. Retrieve the actual DNS record sets.
3. Normalize record names and values.
4. Compare both configurations.
5. Generate a change report.
6. Require approval for destructive changes.
7. Apply the required changes.
8. Verify the resulting configuration.

Never automatically delete every record that is not present in your configuration without considering ownership.

For example, AWS-managed validation records, email authentication records, and third-party service records may be intentionally managed outside your Pulumi project.


---

10. Safe DNS Migrations and Delegation Changes

DNS migrations are among the most sensitive Route 53 operations.

Imagine you are migrating a production domain from an existing DNS provider to Route 53.

Your current domain is:

example.com

You want Route 53 to become the authoritative DNS provider.

A careless migration can make your application, email, and other services unavailable.

10.1 Understand the migration process

A safe migration usually involves the following steps.

Step 1: Inventory existing DNS records

Collect all records from the current DNS provider.

Pay attention to:

- A and AAAA records.
- CNAME records.
- MX records.
- TXT records.
- SPF, DKIM, and DMARC records.
- CAA records.
- Subdomain delegations.
- Existing TTL values.

Missing MX or TXT records can break email delivery and domain verification even when the website continues working.

Step 2: Create the Route 53 hosted zone

Create a new public hosted zone in Route 53.

Do not change the registrar's name servers yet.

Step 3: Recreate DNS records

Import or recreate the existing records.

Compare the old and new configurations.

Step 4: Validate the new zone

Query the authoritative Route 53 name servers directly:

dig @ns-123.awsdns-45.com example.com A

Replace the example name server with one returned by Route 53.

Validate all important records, not just the website's A record.

Step 5: Lower TTL before migration

If practical, reduce TTL values at the existing DNS provider well before the migration.

For example:

Previous TTL: 86400 seconds
New TTL:       300 seconds

Allow the previous TTL period to expire before changing delegation.

This reduces the time some resolvers may retain old answers.

Step 6: Update registrar name servers

Replace the old authoritative name servers with the Route 53 name servers.

Step 7: Monitor the migration

Check:

dig example.com NS

dig example.com A

dig example.com MX

dig example.com TXT

Also verify actual application and email functionality.

10.2 Delegation changes

Delegation determines which name servers are authoritative for a DNS zone.

For example:

example.com
    |
    +-- Route 53 authoritative DNS
          |
          +-- api.example.com
          +-- app.example.com
          +-- dev.example.com

You can also delegate a subdomain to a separate hosted zone.

For example:

example.com
    |
    +-- api.example.com
    |
    +-- dev.example.com
          |
          +-- dev.example.com authoritative zone

This is useful when different teams manage different subdomains.

The parent zone must contain the appropriate NS records for the delegated child zone.

10.3 Rollback planning

A DNS migration must have a rollback strategy.

For example:

- Keep the old DNS provider configuration available.
- Preserve the previous authoritative name servers.
- Document the original TTL values.
- Record the old and new DNS configurations.
- Establish rollback decision criteria.
- Monitor application availability during the migration.

Changing name servers back is not instantaneous because DNS delegation and resolver caching can delay the effect.

A rollback plan should therefore be prepared before the migration begins.


---

11. Blue-Green Deployments Using Weighted Routing

Weighted routing is particularly useful for deploying new application versions without immediately moving all traffic.

Suppose we have two application environments:

- Blue: Current production version.
- Green: New application version.

Both environments have their own ALBs.

api.example.com
                        |
                 Route 53 DNS
                        |
                Weighted Routing
                  /          \
                 /            \
          Blue ALB           Green ALB
             |                   |
        Version 1            Version 2

11.1 Initial deployment

Initially, all traffic goes to Blue:

Environment	Weight

Blue	100
Green	0


11.2 Gradual traffic shifting

After validating Green, we can gradually shift traffic.

Deployment stage	Blue	Green

Initial	100	0
Stage 1	90	10
Stage 2	75	25
Stage 3	50	50
Stage 4	0	100


We modify the weights using Pulumi.

A simplified example of a weighted record:

blue_record = aws.route53.Record(
    "blue-api",
    zone_id=zone_id,
    name="api.example.com",
    type="A",
    set_identifier="blue",
    weighted_routing_policies=[
        aws.route53.RecordWeightedRoutingPolicyArgs(
            weight=90,
        )
    ],
    aliases=[
        aws.route53.RecordAliasArgs(
            name=blue_alb_dns,
            zone_id=blue_alb_zone_id,
            evaluate_target_health=True,
        )
    ],
)

The Green record would use:

weight=10

Both records must have the same DNS name and record type, with unique set identifiers.

For ALB targets, Alias records are preferable to ordinary CNAME records.

11.3 Important limitations

Weighted routing is DNS-based, not a precise request-level traffic distribution mechanism.

A weight of 10 does not guarantee that exactly 10% of HTTP requests reach Green.

Why?

Because:

- Recursive resolvers cache DNS responses.
- Clients may reuse DNS results.
- Some clients use their own DNS caching.
- Different resolvers receive different answers.

Therefore, weighted routing is useful for gradual DNS-based traffic shifting, but it is not a substitute for application-layer canary deployment.

If precise request-level traffic splitting is required, consider using an ALB or another application-layer traffic management mechanism.

11.4 Rollback

If Green has problems, return the weights to:

Blue: 100
Green: 0

However, clients that have already cached Green's DNS answer may continue connecting to it until their cached records expire.

This is why application health monitoring and deployment rollback should not depend exclusively on DNS changes.


---

12. Multi-Region Disaster Recovery Architecture

One of the most important applications of Route 53 is multi-region disaster recovery.

Imagine an application deployed in:

- US East (us-east-1)
- US West (us-west-2)

Each region has its own:

- Application Load Balancer.
- Application instances or ECS services.
- Networking infrastructure.
- Database or data replication architecture.

Route 53 manages how users reach these environments.

12.1 Active-active architecture

In an active-active architecture, both regions serve production traffic.

Users
                      |
                 Route 53
                      |
              Latency Routing
                /          \
               /            \
         US East          US West
            |                 |
           ALB               ALB
            |                 |
        Application       Application

Latency-based routing sends DNS queries to the region expected to provide lower latency.

If one region becomes unhealthy, health-check-based routing can prevent Route 53 from returning its endpoint, subject to the configured routing and health policies.

12.2 Active-passive architecture

In an active-passive architecture, one region serves traffic while another remains available as a standby.

Users
                    |
                Route 53
                    |
              Failover Routing
                    |
             Primary Region
                    |
                   ALB

             Secondary Region
                    |
                   ALB

The primary region receives traffic while healthy.

If it becomes unhealthy, Route 53 can return the secondary region.

12.3 Combining routing policies

A production architecture can use more sophisticated combinations.

For example:

- Latency routing for normal traffic distribution.
- Health checks for endpoint availability.
- Failover routing for disaster recovery.
- Weighted routing for controlled deployment.

One important design detail: Route 53 does not let you arbitrarily stack multiple independent routing policies on one record. To combine policies, you can use supported routing-policy configurations, including nested records where appropriate.

For example, latency-based records can direct users to regional endpoints, while regional failover logic is implemented through appropriate health-aware record configurations.

The routing design must be tested carefully because health-check evaluation and failover behavior depend on the complete record hierarchy.

12.4 DNS failover is not complete disaster recovery

This is a critical point.

Route 53 can redirect users, but it cannot automatically guarantee that the application is operational in the secondary region.

You also need:

- Database replication.
- Application deployment synchronization.
- Data consistency.
- Storage replication.
- Network readiness.
- Secrets and configuration synchronization.
- Capacity planning.
- Recovery time objectives (RTO).
- Recovery point objectives (RPO).

For example, if your database is only available in US East, redirecting traffic to US West won't make the application fully functional.

DNS failover is one part of a broader disaster recovery strategy.


---

13. Multi-Account DNS Governance and Operational Practices

Large AWS organizations often have multiple AWS accounts.

For example:

AWS account	Responsibility

Network account	Centralized networking and DNS
Production account	Production applications
Development account	Development applications
Security account	Security monitoring
Shared services account	Internal services


Managing DNS independently in every account can become difficult.

A centralized DNS architecture provides better governance.

13.1 Centralized DNS management

Consider this architecture:

AWS Organization
                       |
              Network Account
                       |
                 Route 53
                       |
              Public Hosted Zone
                 example.com
                       |
          +------------+------------+
          |            |            |
       Production    Development   Shared
        Account       Account      Services
          |            |            |
        ALBs         ALBs         Internal DNS

The network account can own the public hosted zone while application accounts own their application infrastructure.

This separation provides several benefits:

- Centralized DNS governance.
- Independent application deployments.
- Better separation of duties.
- Reduced accidental changes.
- Consistent security policies.
- Easier auditing.

13.2 Cross-account DNS management

Suppose the production application runs in Account A, but the public hosted zone belongs to Account B.

The application account needs to create or update DNS records in the central hosted zone.

There are several approaches:

Approach 1: Cross-account IAM roles

Create an IAM role in the DNS account that allows an authorized deployment identity from the application account to assume it.

The deployment process assumes the role and updates the DNS records.

Approach 2: Centralized DNS deployment pipeline

Application teams submit DNS changes through a centralized deployment pipeline.

The pipeline validates the request and applies approved changes using credentials belonging to the DNS account.

Approach 3: Delegated subdomains

Give individual teams responsibility for their own subdomains.

For example:

example.com
    |
    +-- api.example.com
    |
    +-- dev.example.com
    |
    +-- internal.example.com

The parent zone delegates selected subdomains to separately managed hosted zones.

This is often a good approach when teams need independent DNS management.

13.3 VPC associations across accounts

Private hosted zones can also be shared across AWS accounts.

For example, a private hosted zone owned by the network account can be associated with VPCs belonging to application accounts.

Cross-account private hosted-zone association requires authorization from the hosted-zone owner and an association request from the VPC owner.

The general process is:

1. Authorize the VPC association from the hosted-zone account.
2. Associate the VPC from the VPC-owning account.
3. Verify that DNS resolution works.
4. Review permissions and future association requirements.

AWS Resource Access Manager (RAM) can also be used for supported Route 53 sharing scenarios.

13.4 Operational governance

Production DNS should have clearly defined ownership and change policies.

Recommended practices include:

- Centralized ownership of critical hosted zones.
- Least-privilege IAM permissions.
- Separate deployment roles for different environments.
- Mandatory review for destructive DNS changes.
- CloudTrail auditing.
- Version-controlled DNS configuration.
- Regular hosted-zone configuration backups.
- Documented DNS migration and rollback procedures.
- Monitoring of important DNS records and endpoints.

You should also establish a clear policy for who can modify NS, MX, TXT, and CAA records because these records can affect domain ownership, email delivery, and certificate issuance.


---

14. Production DNS Security, Availability, and Cost Considerations

Before completing the capstone, let's bring together the major operational considerations.

14.1 DNS security

Route 53 infrastructure needs protection at multiple levels.

IAM security

Use least-privilege policies.

For example, an application deployment role might be allowed to modify only specific record sets in a particular hosted zone rather than having unrestricted Route 53 permissions.

Relevant permissions include:

- route53:ChangeResourceRecordSets
- route53:ListResourceRecordSets
- route53:GetHostedZone
- route53:GetChange

Where appropriate, use IAM condition keys to restrict which record names and types can be changed.

DNSSEC

Enable DNSSEC signing for supported public hosted zones.

This helps DNS resolvers validate that DNS responses have not been modified by an unauthorized party.

DNS Firewall

Use DNS Firewall to control outbound DNS queries from VPC workloads.

For example:

VPC Workloads
      |
Route 53 Resolver
      |
  DNS Firewall
      |
  Domain Evaluation
      |
  +---+---+
  |       |
 Allow   Block
  |       |
 DNS     Reject
 Query   Query

DNS Firewall can help block access to malicious domains and unwanted destinations.

It is important to understand that DNS Firewall protects DNS queries processed through the associated Route 53 Resolver configuration; it is not a general-purpose firewall for all network traffic.

Auditability

Use CloudTrail to track management operations, including changes to hosted zones and DNS records.

14.2 DNS availability

A production DNS architecture should avoid unnecessary dependencies on a single endpoint or region.

Important considerations:

- Use multiple application regions where justified.
- Configure appropriate health checks.
- Design failover behavior carefully.
- Monitor authoritative DNS and application health separately.
- Use sensible TTL values.
- Maintain backups of DNS configuration.
- Test recovery procedures regularly.

Remember that Route 53 is a globally distributed DNS service, but your application endpoints and supporting infrastructure may still be region-dependent.

14.3 Logging and monitoring

You should monitor both DNS infrastructure and application availability.

Service	Purpose

CloudTrail	Audit DNS management API operations
Route 53 health checks	Monitor configured endpoints
CloudWatch metrics	Monitor supported Route 53 and health-check metrics
CloudWatch Logs	Store query and Resolver logs
S3	Long-term centralized log storage
CloudWatch Alarms	Alert on important operational conditions


For example, a production monitoring system might alert when:

- A regional application endpoint becomes unhealthy.
- A Route 53 health check fails.
- Resolver query volume changes unexpectedly.
- DNS Firewall blocks a significant number of queries.
- Unexpected DNS management operations occur.

14.4 Cost optimization

Route 53 costs depend on which capabilities you use.

Important cost categories include:

Feature	Cost consideration

Hosted zones	Monthly hosted-zone charges
DNS queries	Query volume and applicable pricing tiers
Health checks	Number and type of health checks
Traffic Flow	Traffic policy usage and applicable policy-record charges
Resolver endpoints	Endpoint and associated IP-address-hour charges
Resolver query logging	Logging and CloudWatch ingestion/storage
DNS Firewall	Rule groups, queries, and applicable usage charges
Domain registration	Domain-specific registration and renewal fees


A few optimization strategies:

1. Choose TTL values carefully

Lower TTL values can help with traffic changes and recovery, but may increase query volume.

Higher TTL values reduce repeated DNS lookups but can make endpoint changes take longer to reach clients.

2. Avoid unnecessary Resolver endpoints

Resolver endpoints can introduce recurring costs. Create them according to actual hybrid DNS requirements.

3. Monitor query volume

Investigate unusually high DNS query volumes.

4. Review health checks

Remove obsolete health checks and avoid duplicating checks unnecessarily.

5. Centralize logging appropriately

Use retention policies and S3 lifecycle policies to control long-term log-storage costs.

6. Review Traffic Flow usage

Use Traffic Flow where its policy management capabilities justify the additional cost.

Always consult the current AWS pricing pages before estimating production costs because prices and regional charges can change.


---

15. Capstone Lab — Production-Grade Multi-Region DNS Architecture

Now let's bring everything together.

The final project will build a production-style DNS architecture for a SaaS application deployed in two AWS regions.

The application will be accessible through:

https://example.com
https://api.example.com

The infrastructure will use Route 53 for public DNS, private DNS, regional traffic management, and disaster recovery.

15.1 Architecture overview

Global users

Customers accessing the SaaS application

Amazon Route 53

Public hosted zone · Latency routing · Health checks

Weighted routing · Failover

(Region 1)

US East

ALB

ECS / EC2

Application

(Region 2)

US West

ALB

ECS / EC2

Application


---

Private DNS and hybrid connectivity

Private hosted zone · Route 53 Resolver endpoints · DNS Firewall · Query logging

Centralized observability

CloudWatch · CloudTrail · CloudWatch Logs · S3

The architecture contains four major layers:

1. Public DNS and global traffic management.
2. Regional application infrastructure.
3. Private DNS and hybrid DNS.
4. Security, monitoring, and automation.

15.2 Infrastructure design

We'll use the following example configuration:

Component	Configuration

Domain	example.com
Primary region	us-east-1
Secondary region	us-west-2
Public hosted zone	example.com
Private hosted zone	internal.example.com
API endpoint	api.example.com
Application endpoint	app.example.com
Routing	Latency-based
Deployment strategy	Weighted
Disaster recovery	Health-check-based failover
IaC	Pulumi Python
Automation	Bash + Boto3


The region names are examples. You can substitute other AWS regions if they better suit your deployment environment.

15.3 Pulumi project architecture

We'll organize the project into reusable components.

route53-capstone/
│
├── Pulumi.yaml
├── Pulumi.production.yaml
├── requirements.txt
│
├── __main__.py
│
├── config/
│   ├── dns.yaml
│   └── regions.yaml
│
├── components/
│   ├── __init__.py
│   ├── public_zone.py
│   ├── private_zone.py
│   ├── dns_records.py
│   ├── routing.py
│   ├── health_checks.py
│   ├── resolver.py
│   └── dns_firewall.py
│
├── automation/
│   ├── deploy.sh
│   ├── dns-check.sh
│   ├── failover-check.sh
│   └── sync-records.py
│
└── monitoring/
    └── alarms.py

The objective is to keep each infrastructure concern isolated and reusable.

For example:

- public_zone.py creates the public hosted zone.
- private_zone.py creates internal DNS infrastructure.
- routing.py defines routing policies.
- health_checks.py creates endpoint health checks.
- resolver.py manages hybrid DNS endpoints and rules.
- dns_firewall.py manages DNS Firewall rule groups.

The main program orchestrates these components.

Multi-region Pulumi design

There are two reasonable approaches:

Option A: One stack per region

production-us-east-1
production-us-west-2
production-global

Regional stacks create application infrastructure, while the global stack manages public DNS and traffic policies.

This provides clear ownership and independent regional deployments.

Option B: One deployment coordinating multiple regions

A single Pulumi program can instantiate multiple AWS providers, each configured for a different region.

This allows centralized orchestration but increases the coupling between regional deployments.

For a production environment, I recommend Option A because it separates regional application lifecycles from global DNS management.

The global stack can consume regional outputs through Pulumi stack references.


---

15.4 Implementation phases

We'll build the capstone progressively.

Phase 1 — Public hosted zone

Create:

- Public hosted zone.
- DNS records.
- NS and SOA verification.
- Domain delegation.

Use Pulumi to manage all records.

Phase 2 — Regional application infrastructure

Deploy:

- VPC in US East.
- VPC in US West.
- Regional ALBs.
- Application environments.
- HTTPS listeners and certificates.

The ALBs will expose their DNS names and hosted-zone IDs as outputs.

The global DNS stack will consume those outputs.

Phase 3 — Latency-based routing

Create DNS records that direct users toward the appropriate regional application endpoint.

Use Alias records pointing to the regional ALBs.

Each regional record needs a unique set identifier and the correct latency-routing region.

Phase 4 — Health checks and failover

Configure health checks for application endpoints.

For endpoints that can be reached publicly, use appropriate HTTP or HTTPS health checks.

For private application endpoints, do not assume that public Route 53 endpoint health checks can directly access them. Use CloudWatch alarm-based health checks or another suitable health-evaluation design.

Configure failover behavior and verify that unhealthy endpoints are handled as intended.

Phase 5 — Weighted blue-green deployment

Create separate Blue and Green application targets.

Configure weighted records and gradually change their weights.

Use application monitoring to determine whether to continue or roll back.

Phase 6 — Private hosted zone

Create:

internal.example.com

Configure internal records such as:

db.internal.example.com
cache.internal.example.com
auth.internal.example.com

Associate the private zone with the appropriate VPCs.

Phase 7 — Hybrid DNS and DNS Firewall

Configure:

- Resolver inbound endpoints.
- Resolver outbound endpoints.
- Forwarding rules.
- DNS Firewall rule groups.
- Resolver query logging.

For the lab, we can simulate an on-premises DNS environment using a Linux DNS server.

Phase 8 — Monitoring and logging

Configure:

- CloudTrail management-event auditing.
- Route 53 health-check monitoring.
- Resolver query logging.
- DNS Firewall logging.
- CloudWatch dashboards.
- Operational alarms.
- Centralized S3 log storage where appropriate.

Phase 9 — Automation and operational validation

Create Bash scripts and Boto3 automation for:

- Checking DNS resolution.
- Listing hosted zones.
- Checking record configurations.
- Monitoring health-check states.
- Detecting DNS configuration drift.
- Applying approved record changes.
- Validating DNS after deployments.

Finally, run a simulated regional failure and verify the complete recovery process.


---

15.5 Capstone validation and failure scenarios

A production architecture isn't complete just because Pulumi successfully created its resources.

We need to verify how the architecture behaves under normal and abnormal conditions.

Here are the scenarios we should validate.

Scenario	Expected behavior

Both regions healthy	Latency-based routing directs users to regional endpoints
US East becomes unhealthy	Traffic is directed to healthy alternatives according to the routing configuration
US West becomes unhealthy	Traffic is directed to healthy alternatives
Green deployment has errors	Weighted traffic is shifted back to Blue
Private DNS resolution fails	Resolver configuration and VPC DNS settings are investigated
Malicious domain queried	DNS Firewall applies its configured action
Unauthorized DNS change	CloudTrail records the management operation
Pulumi state becomes outdated	Refresh and reconciliation identify differences


Some additional operational commands:

Check authoritative DNS:

dig example.com NS

dig api.example.com A

Check the regional ALB:

dig api.example.com +short

Check DNS resolution through a particular resolver:

dig @1.1.1.1 api.example.com

dig @8.8.8.8 api.example.com

Check the Route 53 health-check status:

aws route53 get-health-check-status \
  --health-check-id HEALTH_CHECK_ID

Inspect DNS changes:

aws route53 list-resource-record-sets \
  --hosted-zone-id ZONE_ID

Finally, inspect the infrastructure:

pulumi refresh

pulumi preview

15.6 Production deployment pipeline

The final automation workflow should resemble this:

Git Repository
                   |
                   v
             GitHub Actions
                   |
                   v
          Validate Pulumi Code
                   |
                   v
             Pulumi Preview
                   |
                   v
           Approval Required
                   |
                   v
              Pulumi Up
                   |
                   v
             AWS Resources
                   |
                   v
          DNS Configuration
                   |
                   v
           DNS Verification
                   |
                   v
          Health Verification
                   |
             +-----+-----+
             |           |
           Success      Failure
             |           |
          Complete    Alert/Rollback

For authentication, configure GitHub Actions OIDC with AWS IAM roles so that the deployment workflow can obtain temporary AWS credentials without storing long-lived AWS access keys in GitHub secrets.

You can also separate deployment workflows:

- Regional infrastructure deployment.
- Global DNS deployment.
- DNS security deployment.
- Monitoring deployment.

This reduces unnecessary coupling between application infrastructure and global DNS management.

15.7 Cleanup and resource lifecycle

Because the capstone includes potentially expensive resources, cleanup deserves attention.

Some resources to review include:

- Route 53 Resolver endpoints.
- DNS Firewall rule groups and associations.
- Health checks.
- CloudWatch log groups.
- VPCs and NAT gateways.
- ALBs.
- ECS services and supporting resources.

Before destroying anything:

pulumi stack select production

pulumi preview --diff

Review the proposed deletions carefully.

For real production hosted zones, never destroy the zone simply because an application stack is being removed. Global DNS ownership should have an independent lifecycle.


---

16. Final Knowledge and Skills Acquired

After completing this module, you should understand how to:

1. Manage Route 53 infrastructure using reusable Pulumi components.
2. Organize infrastructure using Pulumi projects and multiple stacks.
3. Manage configuration and encrypted secrets.
4. Import existing AWS DNS resources into Pulumi.
5. Understand Pulumi state, refresh, preview, and deployment operations.
6. Automate DNS operations using AWS CLI and Bash.
7. Use Boto3 to create, update, retrieve, and synchronize DNS records.
8. Detect and reconcile DNS configuration drift.
9. Perform safe DNS migrations and delegation changes.
10. Implement weighted DNS traffic shifting for blue-green deployments.
11. Design multi-region DNS architectures.
12. Understand active-active and active-passive disaster recovery.
13. Implement centralized DNS governance across AWS accounts.
14. Apply production DNS security and monitoring practices.
15. Build and operate a production-style multi-region Route 53 architecture.

Final course architecture

The complete Route 53 learning path now looks like this:

Module	Subject	Level

1	DNS Fundamentals and Route 53 Architecture	Beginner
2	Hosted Zones, DNS Records, and Domain Management	Beginner
3	Route 53 Routing Policies	Intermediate
4	Health Checks and DNS Failover	Intermediate
5	Private Hosted Zones and Hybrid DNS	Advanced
6	DNS Firewall and DNS Security	Advanced
7	Traffic Management and Advanced Architectures	Advanced
8	Monitoring, Logging, Troubleshooting, and Cost Optimization	Advanced
9	Production Automation and Capstone Project	Expert


My recommendation: Treat Module 9 as the integration point for the entire course. Its most important learning outcome isn't simply knowing how to create Route 53 resources with Pulumi. It's understanding how to operate DNS as production infrastructure: controlled changes, clear resource ownership, automated reconciliation, safe deployments, multi-account governance, and tested disaster recovery.

That is what separates knowing Route 53 from being able to manage production DNS infrastructure.