Worked for 1m 30s

### Module 15 — Pulumi and Production Network Operations

AWS VPC Course · Production Engineering · Pulumi Python · GitHub Actions

This module brings together the networking concepts from Modules 1–14 and applies them to production infrastructure management. The goal is not merely to create a VPC with Pulumi, but to build a networking project that can be safely reused, reviewed, deployed, updated, and maintained across development and production environments.

We'll use Pulumi with Python, the AWS provider, AWS CLI v2, and GitHub Actions with OIDC federation. We'll avoid Terraform and keep the examples focused on current production practices.

### 1\. Learning objectives

By the end of this module, you should be able to:

* Build reusable Pulumi networking components rather than duplicate VPC definitions.

* Separate development and production configuration, resources, and state using Pulumi stacks.

* Understand resource dependencies, replacement operations, and their effect on network availability.

* Safely import existing AWS networking resources and investigate configuration drift.

* Review previews, protect critical infrastructure, and control destructive changes.

* Deploy through GitHub Actions using short-lived AWS credentials and OIDC.

* Enforce network security rules through policy as code and automated validation.

* Estimate costs, standardize tags, document network decisions, and plan safe production changes.

### 2\. The production infrastructure-as-code lifecycle

A production networking change is a controlled lifecycle, not just a command that updates AWS resources.

1\. Define

Python components, configuration, stack settings

2\. Validate and preview

Tests, policy checks, IAM review, Pulumi preview

3\. Review and approve

Inspect route changes, replacements, deletions, and cost

4\. Deploy

Short-lived credentials, controlled update, recorded state

5\. Verify and operate

AWS CLI checks, connectivity tests, drift detection, documentation

The key distinction is that Pulumi state describes the resources Pulumi manages, while AWS contains the actual infrastructure. Production operations must account for both.

For example, a preview might propose replacing a subnet. The code change could look harmless, but the resulting infrastructure operation could disrupt workloads, IP assignments, route-table associations, and dependent resources.

### 3\. Structuring reusable Pulumi components

### 3.1 Why components matter

Imagine maintaining three environments:

* Development: a small VPC for experimentation.

* Staging: a production-like VPC for integration tests.

* Production: a multi-AZ VPC supporting customer workloads.

Copying an entire `__main__.py` file three times causes configuration drift. Eventually, someone fixes a security-group rule in production but forgets staging.

Instead, define the network architecture once and pass environment-specific values into a reusable component.

Reusable `Network` component

VPC · subnets · route tables · security boundaries

dev

Small lab

10.40.0.0/16

staging

Test

10.41.0.0/16

prod

Customer workloads

10.42.0.0/16

These CIDRs are illustrative. Your organization must select ranges that do not overlap with existing VPCs, on-premises networks, VPNs, or connected environments.

A reusable component should encapsulate stable architecture decisions while exposing the choices that genuinely vary between environments.

Good component inputs include:

* VPC CIDR.

* Availability Zone count.

* Public and private subnet CIDRs.

* Whether public subnets are required.

* Environment name and mandatory tags.

Avoid making every AWS resource property configurable without a clear reason. Excessive parameters make the component harder to review and easier to misuse.

### 3.2 Project structure

We'll build a small, reusable, multi-AZ networking project.

```text
pulumi-vpc/
├── Pulumi.yaml
├── requirements.txt
├── __main__.py
├── network.py
├── Pulumi.dev.yaml
├── Pulumi.prod.yaml
└── tests/
    └── test_network_config.py
```

The project creates a VPC, public and private subnets, route tables, and internet routing. To keep the initial lab manageable and limit costs, it does not create NAT gateways, load balancers, interface endpoints, or compute resources.

Private subnets will have no default route to the internet. They will be private in the routing sense, not necessarily isolated from every other network path that might exist in a more elaborate architecture.

### 3.3 Project configuration

`Pulumi.yaml`

```yaml
name: pulumi-vpc
runtime:
  name: python
description: Reusable multi-AZ AWS VPC networking
```

`requirements.txt`

```text
pulumi>=3.0.0,<4.0.0
pulumi-aws>=7.0.0,<8.0.0
```

These are major-version compatibility ranges, not a reproducible lockfile. For production, test a specific provider release and lock Python dependencies in your CI environment.

Install the tools on Windows, preferably in a Python virtual environment:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

python -m pip install -r requirements.txt

pulumi version
aws --version
aws sts get-caller-identity
```

The AWS identity command confirms which account and IAM principal your CLI credentials currently use. Do not proceed if the account is not the intended lab account.

Initialize the project and its stacks:

```powershell
pulumi login
pulumi stack init dev
pulumi stack init prod
```

This example assumes you have a configured Pulumi backend and AWS credentials. A remote backend such as Pulumi Cloud can provide centralized state, collaboration, and deployment history. Pulumi also supports self-managed backends.

### 3.4 Implement the reusable `Network` component

Create `network.py`:

```python
from typing import Any

import pulumi
import pulumi_aws as aws

class Network(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        *,
        cidr_block: str,
        availability_zones: list[str],
        public_subnet_cidrs: list[str],
        private_subnet_cidrs: list[str],
        tags: dict[str, str],
        protect_vpc: bool = True,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__(
            "example:network:Network",
            name,
            None,
            opts,
        )

        if not availability_zones:
            raise ValueError("At least one AZ is required")

        count = len(availability_zones)

        if len(public_subnet_cidrs) != count:
            raise ValueError("One public subnet CIDR per AZ is required")

        if len(private_subnet_cidrs) != count:
            raise ValueError("One private subnet CIDR per AZ is required")

        self.vpc = aws.ec2.Vpc(
            f"{name}-vpc",
            cidr_block=cidr_block,
            enable_dns_support=True,
            enable_dns_hostnames=True,
            tags={**tags, "Name": f"{name}-vpc"},
            opts=pulumi.ResourceOptions(
                parent=self,
                protect=protect_vpc,
            ),
        )

        self.igw = aws.ec2.InternetGateway(
            f"{name}-igw",
            vpc_id=self.vpc.id,
            tags={**tags, "Name": f"{name}-igw"},
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.public_subnets = []
        self.private_subnets = []

        self.public_route_table = aws.ec2.RouteTable(
            f"{name}-public-rt",
            vpc_id=self.vpc.id,
            tags={**tags, "Name": f"{name}-public-rt"},
            opts=pulumi.ResourceOptions(parent=self),
        )

        aws.ec2.Route(
            f"{name}-public-default-route",
            route_table_id=self.public_route_table.id,
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.igw.id,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.private_route_table = aws.ec2.RouteTable(
            f"{name}-private-rt",
            vpc_id=self.vpc.id,
            tags={**tags, "Name": f"{name}-private-rt"},
            opts=pulumi.ResourceOptions(parent=self),
        )

        for index, az in enumerate(availability_zones):
            suffix = f"{index + 1}"

            public_subnet = aws.ec2.Subnet(
                f"{name}-public-{suffix}",
                vpc_id=self.vpc.id,
                availability_zone=az,
                cidr_block=public_subnet_cidrs[index],
                map_public_ip_on_launch=False,
                tags={
                    **tags,
                    "Name": f"{name}-public-{suffix}",
                    "Tier": "public",
                },
                opts=pulumi.ResourceOptions(parent=self),
            )

            private_subnet = aws.ec2.Subnet(
                f"{name}-private-{suffix}",
                vpc_id=self.vpc.id,
                availability_zone=az,
                cidr_block=private_subnet_cidrs[index],
                tags={
                    **tags,
                    "Name": f"{name}-private-{suffix}",
                    "Tier": "private",
                },
                opts=pulumi.ResourceOptions(parent=self),
            )

            aws.ec2.RouteTableAssociation(
                f"{name}-public-assoc-{suffix}",
                subnet_id=public_subnet.id,
                route_table_id=self.public_route_table.id,
                opts=pulumi.ResourceOptions(parent=self),
            )

            aws.ec2.RouteTableAssociation(
                f"{name}-private-assoc-{suffix}",
                subnet_id=private_subnet.id,
                route_table_id=self.private_route_table.id,
                opts=pulumi.ResourceOptions(parent=self),
            )

            self.public_subnets.append(public_subnet)
            self.private_subnets.append(private_subnet)

        self.register_outputs({
            "vpc_id": self.vpc.id,
            "internet_gateway_id": self.igw.id,
            "public_subnet_ids": [
                subnet.id for subnet in self.public_subnets
            ],
            "private_subnet_ids": [
                subnet.id for subnet in self.private_subnets
            ],
            "public_route_table_id": self.public_route_table.id,
            "private_route_table_id": self.private_route_table.id,
        })
```

A few design choices are intentional.

Explicit routing: Every subnet receives a custom route-table association. The public route table has an IPv4 default route to the internet gateway; the private route table has no such route. Explicit associations make the intended routing easier to audit. AWS otherwise associates subnets without an explicit association with the VPC's main route table.

No automatic public IP assignment: The public subnets don't automatically assign public IPv4 addresses to newly launched network interfaces. A subnet can have an internet-gateway route without every resource in it receiving a public address.

Protection: The VPC is protected by default. This is a useful safeguard, but it is not a complete deletion policy for all the resources in the component.

Validation: The component checks subnet-list lengths. It does not yet validate CIDR overlap, subnet containment, address capacity, or Availability Zone uniqueness. Those checks belong in a fuller configuration-validation layer.

The `Network` component is a logical grouping, not an AWS networking service. Its children remain individual AWS resources managed by Pulumi.

### 3.5 Configure separate stacks

Create `Pulumi.dev.yaml`:

```yaml
config:
  aws:region: eu-west-3
  pulumi-vpc:environment: dev
  pulumi-vpc:cidrBlock: 10.40.0.0/16

  pulumi-vpc:availabilityZones:
    - eu-west-3a
    - eu-west-3b

  pulumi-vpc:publicSubnetCidrs:
    - 10.40.0.0/24
    - 10.40.1.0/24

  pulumi-vpc:privateSubnetCidrs:
    - 10.40.10.0/24
    - 10.40.11.0/24
```

Create `Pulumi.prod.yaml`:

```yaml
config:
  aws:region: eu-west-3
  pulumi-vpc:environment: prod
  pulumi-vpc:cidrBlock: 10.42.0.0/16

  pulumi-vpc:availabilityZones:
    - eu-west-3a
    - eu-west-3b
    - eu-west-3c

  pulumi-vpc:publicSubnetCidrs:
    - 10.42.0.0/24
    - 10.42.1.0/24
    - 10.42.2.0/24

  pulumi-vpc:privateSubnetCidrs:
    - 10.42.10.0/24
    - 10.42.11.0/24
    - 10.42.12.0/24
```

These AZ names are illustrative and must be checked for availability in your target account and Region. AZ names can map to different physical zones across AWS accounts. In a production organization, verify zone IDs and coordinate the AZ mapping across connected accounts.

Now create `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

from network import Network

config = pulumi.Config()

environment = config.require("environment")
cidr_block = config.require("cidrBlock")

availability_zones = config.require_object(
    "availabilityZones"
)
public_cidrs = config.require_object("publicSubnetCidrs")
private_cidrs = config.require_object("privateSubnetCidrs")

# Fail early if the stack configuration is inconsistent.
if len(set(availability_zones)) != len(availability_zones):
    raise ValueError("Availability Zones must be unique")

tags = {
    "Project": "networking-course",
    "Environment": environment,
    "ManagedBy": "Pulumi",
    "CostCenter": "training",
}

network = Network(
    f"{environment}-network",
    cidr_block=cidr_block,
    availability_zones=availability_zones,
    public_subnet_cidrs=public_cidrs,
    private_subnet_cidrs=private_cidrs,
    tags=tags,
    protect_vpc=(environment == "prod"),
)

pulumi.export("vpc_id", network.vpc.id)
pulumi.export(
    "public_subnet_ids",
    [subnet.id for subnet in network.public_subnets],
)
pulumi.export(
    "private_subnet_ids",
    [subnet.id for subnet in network.private_subnets],
)
```

This gives us one program and two environment-specific configurations. The production stack gets explicit VPC protection; the development stack can be cleaned up more easily.

A stack separates configuration and state, but it does not automatically provide account-level or permission-level isolation. For stronger production isolation, use separate AWS accounts and deployment roles.

Also, this initial component deliberately uses a single public route table and a single private route table per VPC. That's a reasonable starting point, but more complex production designs may need separate route tables for different trust zones, egress paths, or inspection requirements.

### 4\. Configuration, secrets, and stack separation

### 4.1 How Pulumi configuration works

Pulumi configuration is stored per stack. Your Python program reads the selected stack's configuration when it runs.

```powershell
pulumi stack select dev
pulumi config
pulumi config get aws:region
pulumi stack output
```

Switching stacks changes the active deployment target. Always verify the selected stack before deploying:

```powershell
pulumi stack
pulumi whoami
aws sts get-caller-identity
```

In automation, explicitly specify the stack rather than relying on whichever stack happens to be selected locally.

### 4.2 Managing secrets

The current network component doesn't need application passwords or API keys. A real networking project might need secrets for third-party integrations, VPN-related automation, or other services.

Store sensitive Pulumi configuration using the secret mechanism:

```powershell
pulumi config set --secret vpnSharedSecret
```

The CLI prompts for the value. Avoid placing secrets directly in command-line arguments, shell history, logs, or committed plaintext files.

Read a secret in Python:

```python
import pulumi

config = pulumi.Config()
vpn_shared_secret = config.require_secret("vpnSharedSecret")
```

`require_secret()` returns a Pulumi output that preserves the secret designation through dependent computations. Don't convert it to plaintext merely to simplify debugging.

Important distinctions:

* Ordinary configuration, such as a CIDR block, is not secret.

* Secret configuration is encrypted using the stack's configured secrets provider.

* Encryption of Pulumi state does not replace access controls, backups, or careful handling of decrypted values.

* AWS access keys should not be stored as Pulumi application configuration when short-lived AWS credentials can be used instead.

### 4.3 Development and production are different operational boundaries

Separate stacks provide separate state and configuration, but the same AWS account can still contain resources from both stacks.

For production, a stronger pattern is:

```text
GitHub repository
       |
       +---- dev workflow ----> Dev AWS account
       |
       +---- prod workflow ---> Prod AWS account
                                  |
                                  +-- Production VPC
                                  +-- Production subnets
                                  +-- Production routes
```

Use distinct IAM deployment roles, distinct account IDs, and protected production deployment approvals. Do not give a development workflow unrestricted access to the production account.

### 5\. Dependencies and resource replacement risks

Pulumi builds a dependency graph from resource inputs and explicit dependencies.

For example:

```text
VPC
 |
 +-- Internet Gateway
 |
 +-- Public Route Table
 |      |
 |      +-- Default Route --> Internet Gateway
 |      |
 |      +-- Public Subnet Association
 |
 +-- Private Route Table
        |
        +-- Private Subnet Association
```

When you write:

```python
vpc_id=self.vpc.id
```

the output reference tells Pulumi that the resource depends on the VPC. Pulumi can therefore order operations appropriately.

### 5.1 Implicit versus explicit dependencies

Prefer implicit dependencies when a resource consumes another resource's output.

Use `depends_on` when a genuine dependency exists but is not represented through resource inputs.

For example, a custom validation or operational prerequisite might require an explicit dependency, but adding `depends_on` everywhere makes the graph unnecessarily complicated.

### 5.2 Understand replacement before applying changes

A Pulumi preview can show operations such as:

| Preview operation          | Meaning                                                         |
| -------------------------- | --------------------------------------------------------------- |
| +                          | Create a resource                                               |
| ~                          | Update a resource                                               |
| -                          | Delete a resource                                               |
| +- or replacement notation | Replace a resource, potentially creating and deleting resources |

The exact display varies by CLI version and output format.

Some AWS properties can be updated in place; others require resource replacement. Changing a subnet's CIDR, for example, is not equivalent to changing a descriptive tag.

For a subnet replacement, dependent resources might need updates or replacement too. Existing ENIs, EC2 instances, and other workloads can prevent deletion or require migration.

Pulumi normally attempts to create a replacement before deleting the old resource when the provider and resource permit it. This does not guarantee zero downtime. `delete_before_replace` should not be used as a general fix for replacement errors because it can increase downtime and cascade into dependent resources.

Production rule: Never approve a network replacement solely because the final desired configuration looks correct. Review the entire dependency chain and determine how traffic will move during the change.

### 5.3 Resource naming and refactoring

Pulumi tracks resources using their URNs, which include the stack, project, resource type, and logical name.

Renaming a resource in Python can make Pulumi interpret it as a deletion plus creation. If the intent is to rename or refactor a resource without replacing the real AWS resource, consider using an appropriate `aliases` migration.

For example:

```python
opts=pulumi.ResourceOptions(
    parent=self,
    aliases=[
        pulumi.Alias(name="old-public-route-table"),
    ],
)
```

This is illustrative; use the actual previous logical name and ensure the resource type and parent relationship match the migration. Incorrect aliases can produce unexpected state transitions.

Read the preview after refactoring before running an update.

### 6\. Importing existing infrastructure and managing drift

Production teams often inherit VPCs created manually, by CloudFormation, or by older automation.

There are two separate jobs:

* Bring an existing AWS resource under Pulumi management.

* Reconcile Pulumi's state and program with the resource's actual configuration.

### 6.1 Inspect the existing resource

For example, find VPCs:

```powershell
aws ec2 describe-vpcs `
  --query "Vpcs[*].[VpcId,CidrBlock,IsDefault]" `
  --output table
```

Inspect a particular VPC:

```powershell
aws ec2 describe-vpcs `
  --vpc-ids vpc-0123456789abcdef0
```

Replace the sample ID with the real VPC ID.

Before importing, record the existing CIDRs, DNS attributes, tags, subnets, route tables, associations, and gateways. Importing a VPC does not automatically mean every associated resource is now managed by Pulumi.

### 6.2 Import a resource

A simplified example for an existing VPC is:

```python
import pulumi
import pulumi_aws as aws

vpc = aws.ec2.Vpc(
    "existing-vpc",
    cidr_block="10.50.0.0/16",
    enable_dns_support=True,
    enable_dns_hostnames=True,
    opts=pulumi.ResourceOptions(
        import_="vpc-0123456789abcdef0",
        protect=True,
    ),
)

pulumi.export("vpc_id", vpc.id)
```

Use the actual current VPC settings, not assumed defaults. Confirm the installed Pulumi AWS provider's resource arguments before using this pattern.

Then preview the import. The first preview should show adoption of the existing resource, not an unexpected replacement or destructive change. After successful adoption, remove the one-time import option and review the next preview.

For a production VPC with many dependent resources, use a deliberate migration plan. Import and reconcile the VPC, subnets, route tables, associations, gateways, and routes in an order that respects their dependencies.

### 6.3 Detect configuration drift

Drift means the real infrastructure differs from the configuration Pulumi expects to manage.

For example, someone adds a default route through the AWS console to a private route table. Your code still says there is no default route, and the state may not yet reflect the manual modification.

First, inspect the real AWS configuration:

```powershell
aws ec2 describe-route-tables `
  --filters "Name=vpc-id,Values=vpc-0123456789abcdef0"
```

Then refresh the Pulumi state and review the proposed changes:

```powershell
pulumi refresh --preview-only
```

The exact flags supported by your installed CLI should be confirmed with `pulumi refresh --help`. Alternatively, use the more explicit two-step workflow:

```powershell
pulumi refresh
pulumi preview
```

The second workflow updates the recorded state before showing what the program would change. `pulumi refresh` does not itself rewrite your Python program to match the observed infrastructure. If a manual change is intentional, update the code too; otherwise, a later deployment may revert it.

Do not automatically run `pulumi up --refresh` as a substitute for reviewing an unexplained drift event in production.

### 7\. Previewing, protecting, and safely deleting infrastructure

### 7.1 The safe deployment sequence

For development:

```powershell
pulumi stack select dev

pulumi preview
pulumi up
```

For production:

```powershell
pulumi stack select prod

pulumi preview --diff
pulumi up --preview-only
```

The final command is a preview-only update, not a deployment. After reviewing the plan, run the actual update in an approved deployment session:

```powershell
pulumi up
```

You can save preview output or use a reviewed update plan when your team's Pulumi workflow supports it. A saved plan should be treated as a specific proposal, not a guarantee that AWS conditions cannot change before deployment.

Before approving a production change, examine:

* Resources to be created or deleted.

* Replacements of VPCs, subnets, gateways, and route tables.

* CIDR and route destination changes.

* Security-group ingress and egress modifications.

* Changes to endpoint policies and private DNS.

* Dependencies that might interrupt traffic.

* Cost changes and the possibility of stranded resources.

### 7.2 Protect critical resources

Pulumi supports resource protection through `protect=True`.

In our component, we protect the production VPC:

```python
opts=pulumi.ResourceOptions(
    parent=self,
    protect=protect_vpc,
)
```

This blocks deletion of that VPC while protection remains enabled. It does not mean every child resource is protected: the protection setting here is applied directly to the VPC resource, not to the `Network` component.

For more comprehensive protection, apply it to the component and ensure the setting propagates to all children, or explicitly protect each critical child. Pulumi's resource protection feature can also be managed through stack state.

### 7.3 Controlled deletion

A safe cleanup workflow for a disposable development stack is:

```powershell
pulumi stack select dev
pulumi preview --diff
pulumi destroy
```

Review the proposed deletions and confirm the stack really is disposable before proceeding.

Production cleanup is different. It requires explicit approval, dependency analysis, and a migration or decommissioning plan. Do not casually unprotect and destroy a production VPC.

Also, `protect=True` is a Pulumi deployment safeguard, not a complete AWS authorization boundary. AWS IAM permissions, account controls, backups, and operational approvals remain important.

### 8\. GitHub Actions with AWS OIDC

Long-lived AWS access keys stored in GitHub repository secrets create a credential-management burden. OIDC lets a GitHub Actions job exchange a trusted identity token for temporary AWS credentials through an IAM role.

### 8.1 Trust relationship

```text
GitHub Actions workflow
       |
       | OIDC identity token
       v
AWS IAM OIDC identity provider
       |
       | Trust policy checks issuer, audience,
       | and repository/branch or environment
       v
Restricted IAM deployment role
       |
       | Temporary STS credentials
       v
Pulumi AWS provider
       |
       v
AWS VPC resources
```

There are two distinct authentication relationships to consider:

* GitHub Actions must authenticate to the Pulumi backend.

* The Pulumi program must authenticate to AWS.

AWS OIDC solves the second relationship. If you use Pulumi Cloud, its own OIDC authentication can also remove the need for a long-lived Pulumi access token.

### 8.2 Configure an AWS deployment role

Register GitHub's OIDC provider in the AWS account, using the issuer `https://token.actions.githubusercontent.com` and audience `sts.amazonaws.com`.

The role's trust policy should constrain the token subject to the intended repository and deployment context. For example, a branch-restricted subject condition might look like:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:YOUR_ORG/YOUR_REPO:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

Replace the account ID, organization, and repository placeholders. The exact `sub` claim can vary with repository and GitHub environment settings. Verify the claims emitted by your workflow and use a condition appropriate to your deployment model. Avoid wildcard trust policies that allow unrelated repositories to assume the role.

The role also needs an appropriate permissions policy. Do not grant unrestricted administrator access just to make the first workflow succeed. Pulumi operations can require a broader set of read and write permissions than a single VPC API call; derive the policy from the resources the project actually manages and test it in development.

### 8.3 Example GitHub Actions workflow

Create `.github/workflows/network-preview.yml`:

```yaml
name: Network preview

on:
  pull_request:
    branches: [main]

permissions:
  contents: read
  id-token: write

jobs:
  preview:
    runs-on: ubuntu-latest

    steps:
      - name: Check out repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ vars.AWS_DEV_ROLE_ARN }}
          aws-region: eu-west-3

      - name: Verify AWS identity
        run: aws sts get-caller-identity

      - name: Set up Pulumi
        uses: pulumi/actions@v6
        with:
          command: version
          stack-name: YOUR_ORG/pulumi-vpc/dev
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}

      - name: Preview development stack
        run: |
          pulumi stack select YOUR_ORG/pulumi-vpc/dev
          pulumi preview --diff
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

This is a workflow template: verify the current supported action versions and input names before using it, and pin actions to reviewed immutable commit SHAs for hardened production pipelines. The example assumes Pulumi Cloud and a configured `PULUMI_ACCESS_TOKEN`; that token is separate from AWS credentials.

For a production workflow, use a separate role and a protected GitHub environment with required reviewers. Do not let pull-request code from untrusted contributors receive production credentials. A production update job should require approval and should not automatically apply arbitrary changes just because a preview passed.

See the and .

### 9\. Policy as code and network guardrails

Policy as code makes organizational rules executable. Instead of relying only on reviewers to notice a risky configuration, policies can reject noncompliant deployments.

Examples of network guardrails:

* Production VPCs must use approved CIDR ranges.

* Public subnets must not automatically assign public IPv4 addresses.

* Production resources must have an `Environment` and `CostCenter` tag.

* Public ingress must not allow unrestricted SSH or RDP.

* Production VPCs and other critical resources must have deletion protection.

* Only approved Regions and resource types may be deployed.

Pulumi Policy Packs can evaluate resources during previews and updates. A policy pack is associated with a policy group to determine which stacks it governs and whether violations are advisory or blocking.

### 9.1 A practical validation layer

Start with local Python validation for properties that don't require AWS API access.

Create `tests/test_network_config.py`:

```python
import ipaddress
import unittest

class NetworkConfigTests(unittest.TestCase):
    def test_environment_cidrs_do_not_overlap(self):
        ranges = [
            ipaddress.ip_network("10.40.0.0/16"),
            ipaddress.ip_network("10.41.0.0/16"),
            ipaddress.ip_network("10.42.0.0/16"),
        ]

        for i, first in enumerate(ranges):
            for second in ranges[i + 1:]:
                self.assertFalse(first.overlaps(second))

    def test_subnets_are_inside_vpc(self):
        vpc = ipaddress.ip_network("10.40.0.0/16")

        subnets = [
            ipaddress.ip_network("10.40.0.0/24"),
            ipaddress.ip_network("10.40.10.0/24"),
            ipaddress.ip_network("10.40.11.0/24"),
        ]

        for subnet in subnets:
            self.assertTrue(subnet.subnet_of(vpc))

if __name__ == "__main__":
    unittest.main()
```

Run:

```powershell
python -m unittest discover -s tests -v
```

These tests check CIDR relationships only. They do not validate actual AWS state, account permissions, subnet availability, routing reachability, or all configuration values in the Pulumi program.

In a mature project, extract CIDR and topology validation into a reusable Python module and test every environment configuration. Add tests for duplicate CIDRs, duplicate AZs, subnet containment, required tags, and forbidden public routes.

### 9.2 Network security policies

A good validation pipeline has multiple layers:

Layer 1 — Static validation

Python tests, configuration checks, linting, dependency checks.

Layer 2 — Policy as code

Enforce resource, CIDR, tagging, and public-exposure requirements.

Layer 3 — Reviewed preview

Inspect actual proposed AWS operations and obtain approval for production changes.

Layer 4 — Runtime verification

Inspect deployed routes, security groups, endpoints, logs, and reachability.

No single layer is sufficient. For example, a policy may correctly reject an unrestricted SSH ingress rule in the Pulumi program, but it won't necessarily detect every manually created security group elsewhere in the account. Use AWS-native governance and inventory tools where account-wide enforcement is required.

### 10\. Cost estimation, tagging, and operational documentation

### 10.1 Understand the cost of the networking lab

The initial component creates a VPC, an internet gateway, subnets, route tables, routes, and route-table associations. These resources are generally not the major direct cost drivers of this lab.

However, the networking services introduced in earlier modules can create substantial ongoing charges.

| Resource                 | Cost consideration                                                             |
| ------------------------ | ------------------------------------------------------------------------------ |
| VPC and subnets          | No separate hourly charge for the basic constructs                             |
| Internet gateway         | No separate hourly charge for the gateway itself; data transfer can cost money |
| NAT gateway              | Hourly charges plus data processing and applicable data transfer               |
| Interface endpoints      | Hourly charges per endpoint/AZ plus data processing                            |
| Public IPv4 addresses    | Applicable public IPv4 charges                                                 |
| Transit Gateway          | Attachment and data processing charges                                         |
| Load balancers           | Hourly/capacity charges and applicable data processing                         |
| VPN / Direct Connect     | Connection, data transfer, and related service charges                         |
| Flow Logs and monitoring | Charges for the chosen log destination, ingestion, storage, and analysis       |

Actual pricing depends on Region, service configuration, traffic, and applicable discounts. Check the before deploying additional services.

Pulumi previews show planned resource changes; they are not, by themselves, a complete AWS bill forecast. Use the AWS Pricing Calculator and a cost review to estimate hourly and traffic-related expenses.

### 10.2 Standardize tags

The component applies tags such as:

```python
tags = {
    "Project": "networking-course",
    "Environment": environment,
    "ManagedBy": "Pulumi",
    "CostCenter": "training",
}
```

In production, consider additional organizational tags such as `Owner`, `Application`, `DataClassification`, and `Lifecycle`.

Tags help with cost allocation, ownership, inventory, and operational queries. They are not a security boundary: IAM policies and service-specific authorization should enforce actual access restrictions.

### 10.3 Write a network operations record

For every production VPC, maintain a short, version-controlled document describing:

* VPC CIDR and IPAM allocation.

* Availability Zones and subnet CIDRs.

* Route tables, route targets, and routing intent.

* Security-group boundaries and ingress/egress policy.

* DNS and endpoint design.

* Dependencies and external connectivity.

* Estimated monthly costs and cost owners.

* Deployment role, stack name, and approval process.

* Rollback strategy and known limitations.

* Monitoring, troubleshooting commands, and incident contacts.

A useful network document explains not just what exists, but why each route and trust boundary exists.

### 11\. Safe changes to routes, subnets, endpoints, and connectivity

Networking changes deserve extra care because a small route-table modification can affect an entire tier of workloads.

### 11.1 Route changes

Suppose a private subnet currently has no default internet route. Someone proposes adding:

```python
aws.ec2.Route(
    "private-default-route",
    route_table_id=network.private_route_table.id,
    destination_cidr_block="0.0.0.0/0",
    nat_gateway_id="nat-0123456789abcdef0",
)
```

This is an illustrative change, not part of the current lab. It would send unmatched IPv4 traffic through the specified NAT gateway, assuming that gateway exists, is in a suitable state, and has the required routing.

Before deploying it, verify:

* The NAT gateway is in the intended VPC and has the required connectivity.

* The subnet's existing routes are understood.

* The change doesn't bypass a centralized inspection or egress-control design.

* The security and cost implications are accepted.

* Rollback can restore the previous routing behavior.

### 11.2 Subnet expansion and replacement

Do not treat a subnet CIDR change as an ordinary in-place resize. Plan new subnets when an existing subnet cannot accommodate the intended address space.

A safer migration pattern is:

```text
Existing subnet
      |
      | Deploy new subnet and required routes
      v
New subnet validated
      |
      | Migrate workloads and dependent interfaces
      v
Traffic verified on new subnet
      |
      | Remove old dependencies and subnet
      v
Old subnet retired
```

This strategy requires application-specific planning. Some resources can be migrated with controlled replacement; others require downtime, IP changes, or special migration procedures.

### 11.3 VPC endpoints

When adding an interface endpoint, review:

* Subnet and Availability Zone placement.

* Endpoint security-group rules.

* Private DNS behavior and potential DNS conflicts.

* Endpoint policies and the interaction with IAM.

* Whether the endpoint is replacing a NAT-dependent access path.

* Availability, quotas, and recurring costs.

An endpoint does not automatically make every request private or authorized. Confirm the actual DNS resolution and traffic path from the workload.

### 11.4 Connectivity changes

For a route, peering connection, VPN, Transit Gateway attachment, or centralized inspection change, maintain an explicit change plan:

* Current path and intended path.

* Affected source and destination CIDRs.

* Required forward and return routes.

* Security-group and network ACL implications.

* DNS dependencies.

* Verification commands and rollback steps.

AWS routing changes can interrupt existing connections when the new route does not preserve the relevant path. AWS specifically documents that changing a subnet's route-table association can drop existing connections when the new table does not contain equivalent routes.

### 12\. Hands-on lab: reusable development and production VPCs

We will deploy the project from Section 3, validate it, inspect it, and practice reviewing changes.

Lab cost and safety

This lab creates real AWS infrastructure. The basic VPC resources are not the major cost drivers, but public IPv4 addresses, data transfer, and any additional resources you add can incur charges. No NAT gateway, load balancer, or compute resource is required for the base lab.

Use a dedicated development account when possible. The production stack is a configuration and operational exercise until you intentionally deploy it into a suitable account.

### Step 1 — Check the environment

Verify the AWS identity, Region, Pulumi CLI, and Python dependencies.

```powershell
aws sts get-caller-identity
aws configure get region

pulumi version
python --version
python -m pip install -r requirements.txt
```

Make sure the AWS credentials refer to the intended lab account. The configured AWS CLI Region and the Region in Pulumi configuration should agree.

### Step 2 — Validate configuration

Run the unit tests:

```powershell
python -m unittest discover -s tests -v
```

Confirm that each stack's subnet CIDRs fall within its VPC CIDR and do not overlap with one another.

For a production deployment, extend these tests to validate the complete topology before continuing.

### Step 3 — Preview development

```powershell
pulumi stack select dev
pulumi preview --diff
```

Review the resource graph. You should see a VPC, an internet gateway, public and private subnets, route tables, a public default route, and route-table associations.

No NAT gateway or interface endpoint should be present.

### Step 4 — Deploy development

```powershell
pulumi up
```

Review the final plan and approve the update when you are satisfied.

Record the exported VPC and subnet IDs:

```powershell
pulumi stack output
pulumi stack output vpc_id
```

### Step 5 — Verify the deployed infrastructure

```powershell
$VpcId = pulumi stack output vpc_id

aws ec2 describe-vpcs `
  --vpc-ids $VpcId

aws ec2 describe-subnets `
  --filters "Name=vpc-id,Values=$VpcId" `
  --query "Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,MapPublicIpOnLaunch]" `
  --output table

aws ec2 describe-route-tables `
  --filters "Name=vpc-id,Values=$VpcId" `
  --query "RouteTables[*].[RouteTableId,Routes[*].[DestinationCidrBlock],Associations[*].SubnetId]" `
  --output json
```

Expected results:

* The VPC has the configured IPv4 CIDR.

* The subnets are placed in the configured Availability Zones.

* Automatic public IPv4 assignment is disabled on the public subnets.

* The public route table has a default route through the internet gateway.

* The private route table has no default internet route.

* Both subnet groups have explicit route-table associations.

These checks verify configuration, not application-level connectivity. Since this lab doesn't create compute resources, it does not demonstrate actual packet transmission.

### Step 6 — Preview production without deploying it

```powershell
pulumi stack select prod
pulumi preview --diff
```

Check the production CIDRs and Availability Zones carefully. Confirm that the preview targets the expected AWS account and Region.

If you are using the same account for both stacks, the development and production CIDRs should still be distinct, and the resources must remain separately identifiable.

### Step 7 — Practice a safe change

In the development stack only, change one public subnet's tag or another clearly in-place property.

Then run:

```powershell
pulumi stack select dev
pulumi preview --diff
```

Inspect whether the plan is an in-place update or a replacement. A tag-only change would ordinarily be expected to update the resource without replacing the subnet.

Do not intentionally change a production subnet CIDR merely to practice replacement behavior.

### Step 8 — Inspect state and drift

Review the stack's resources:

```powershell
pulumi stack
pulumi stack --show-ids
pulumi stack output
```

You can also run a refresh preview to inspect potential drift:

```powershell
pulumi refresh --preview-only
```

Check `pulumi refresh --help` if your installed CLI uses different supported flags. Do not manually alter the AWS route tables during the lab unless you're prepared to restore them.

### Step 9 — Clean up development

First preview the deletion:

```powershell
pulumi stack select dev
pulumi preview --diff
pulumi destroy
```

The development VPC isn't protected by the example's production-specific protection setting. If you have added protected resources, you'll need to handle their protection deliberately before they can be deleted.

After cleanup, verify that the development stack no longer owns the lab resources. Keep production intact unless you have an explicit, approved production decommissioning plan.

### 13\. Troubleshooting production deployments

| Symptom                                            | Likely cause                                                                               | Recommended response                                                          |
| -------------------------------------------------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------------- |
| pulumi preview unexpectedly proposes replacements  | Immutable property changed, resource renamed, or state/configuration mismatch              | Inspect the replacement diff, resource URN, and dependencies                  |
| AWS returns UnauthorizedOperation                  | Deployment role lacks a required permission                                                | Identify the denied API operation and add only the necessary permission       |
| InvalidSubnet.Range                                | Invalid CIDR, overlap, or CIDR outside the VPC                                             | Validate the CIDR plan and existing subnet allocations                        |
| DependencyViolation during deletion                | A subnet, VPC, or route table still has dependent resources or associations                | Inspect dependencies and remove them in a planned order                       |
| GitHub OIDC returns AccessDenied                   | Trust-policy subject/audience mismatch or insufficient role permissions                    | Inspect the workflow context, IAM trust policy, and role permissions          |
| A manual AWS change isn't reflected in the preview | Pulumi state hasn't been refreshed                                                         | Inspect AWS, run a refresh preview, and reconcile state and code              |
| Private workload cannot reach an AWS service       | Missing endpoint, DNS problem, route issue, security group, endpoint policy, or IAM denial | Trace DNS, routing, network filtering, endpoint policy, and IAM independently |
| A deployment fails because a resource is protected | A destructive operation targets a protected resource                                       | Reassess the plan; unprotect only through an approved change process          |

A disciplined diagnosis separates four questions:

* What does the Python program declare?

* What does Pulumi state record?

* What actually exists in AWS?

* What change does Pulumi propose?

Don't edit Pulumi state manually just to make a failed deployment succeed. State repair is an advanced recovery operation, not the default response to a confusing preview.

### 14\. Production readiness checklist

Use this checklist when reviewing a real networking project.

### Readiness review

0 of 16 complete

Architecture and configuration

Reusable components with documented inputs and outputs

Non-overlapping CIDRs and validated subnet placement

Separate development and production stacks

Explicit route-table associations and reviewed routing

State and change safety

Shared, backed-up state with controlled access

Secrets encrypted and never logged in plaintext

Critical resources protected against accidental deletion

Previews reviewed for replacements, deletions, and connectivity risks

CI/CD and governance

Short-lived AWS credentials through OIDC

Separate, least-privilege deployment roles

Production approval and trusted workflow restrictions

Automated tests, policy checks, and dependency review

Operations

Tags and cost ownership defined

AWS CLI verification and troubleshooting documented

Drift detection and recovery procedures defined

Rollback plan and network change records maintained

### 15\. Official documentation and further reading

These references cover the principal mechanisms used in this module.

![AWS Marketplace: Pulumi](https://images.openai.com/static-rsc-4/sx2SrGXur_Olo3De8pIuU4OqWUh4Wi4mbkPP-areUshoqnSnZIfxJc8JHcMafq0CiJrzWuH5TMaY3_KlxmfPabn0h7RTNYHHGE3UQSsgh1VP5dlDqMmK0SwWGSGZ2HqS11W6Vvdg-sKAE7pBXnFu4PHwiLEh8ggiDBN6uEY-Aw0WlUQ0-Jmo-PxKclutkp4e?purpose=fullsize)

Pulumi components and state

Reusable resources, stack state, backends, and resource protection.

![AWS Signature Version 4 - Overview (ODC) | OutSystems](https://images.openai.com/static-rsc-4/4aZdy5Y4miY4IrrhzfjgTiAod8Yyk6fUpd9pfl50qZNoOQUH1MX9LQQjCJXadXq7XNtcdvO_7oO7-FZ4k_docPOzD-IElq7VJqYp5h6qP5TGgPUHfgGDIM-LT_jFk4e2vrLbNStwpbi7lDGT7bpMZHRXTAQ-F0ZkAEunufuZHrxTxT8DAuy1x0kWLeaEQc4O?purpose=fullsize)

AWS VPC operations

Route tables, subnet associations, and network cost considerations.

![Phase 5: Setting up CI/CD with Github Actions | Cloud Connections](https://images.openai.com/static-rsc-4/hZh7v3A_-41AGW_6VxITUouK1Kwk6WrmqB7v3FQdsyD0mU-tdtIgH4uBv2QzUpYBKtOXrjW8o4vteVNGF5CIdXWcS4w2namJldEgpKfegyzcs46tYKaL4UVt_6suJb24T7x0BbIojUIi7AN37l07VJnycJPdgEjO-TEbACoomUndZhXYqm-hyFyX7_6dHh9T?purpose=fullsize)

CI/CD and identity federation

Short-lived credentials, workflow trust, and deployment automation.

### Module 15 summary

The central lesson is that production networking requires more than correct resource definitions. You need reusable architecture, explicit environment boundaries, reliable state management, careful replacement planning, least-privilege deployment identities, automated guardrails, and operational procedures.

The lab gives you the foundation: one reusable Pulumi Python component, separate development and production configurations, explicit route tables, deployment previews, and a safe cleanup process.

Next: Module 16 — Capstone Production Architecture, where we bring the course together to design a secure, highly available AWS network for a realistic SaaS platform.
