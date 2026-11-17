### Module 5 — Security Groups and Network ACLs

This module builds on the VPC, subnet, routing, and NAT concepts from Modules 1–4. We'll learn how AWS filters network traffic, how to design least-privilege rules, and how to troubleshoot connectivity failures systematically.

The hands-on lab will use Pulumi with Python, AWS CLI v2, and a three-tier application architecture. No quizzes, and no Terraform.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Explain how security groups attach to Elastic Network Interfaces (ENIs) and filter traffic.

* Understand stateful connection tracking versus stateless packet filtering.

* Configure Network ACLs (NACLs), including numbered rules and ephemeral ports.

* Design layered security using references between security groups.

* Troubleshoot rejected traffic, timeouts, and asymmetric routing.

* Use VPC Flow Logs to investigate network problems.

* Deploy a multi-tier security design with separate load-balancer, application, and database security groups.

### 2\. The big picture: where security controls fit

Security groups and Network ACLs operate at different levels of the VPC network.

Client

Browser or API client

Inbound TCP connection

Public subnet

Network ACL filters subnet traffic

Application Load Balancer

Load-balancer security group

Application traffic, e.g. TCP 8000

Private application subnet

Network ACL filters subnet traffic

Application servers

Application security group

Database traffic, e.g. TCP 5432

Isolated database subnet

Network ACL filters subnet traffic

PostgreSQL

Database security group

There are two distinct filtering layers:

* Security groups: attached to network interfaces; stateful; allow rules only.

* Network ACLs: associated with subnets; stateless; support allow and deny rules.

Both layers must permit the relevant traffic. A permissive security group cannot override a blocking NACL, and a permissive NACL cannot override a blocking security group.

### 3\. Security groups in depth

### 3.1 What is a security group?

A security group is a virtual firewall associated with one or more network interfaces. For an EC2 instance, its security groups govern traffic to and from its ENIs.

A security group consists of:

* Inbound rules — which incoming connections are allowed.

* Outbound rules — which outgoing connections are allowed.

* Rules that specify a protocol, port or port range, and a source or destination.

Security groups are allow-list based: there are no deny rules. If traffic doesn't match an applicable allow rule, it is not permitted by that security group.

A newly created security group initially has no inbound allow rules. AWS ordinarily creates it with an outbound rule allowing all traffic; you can remove or narrow that rule.

### 3.2 Security groups attach to ENIs

An Elastic Network Interface (ENI) is a virtual network interface in your VPC. It has properties such as private IP addresses, a MAC address, and associated security groups.

EC2 instance

Elastic Network Interface (ENI)

Private IP: 10.0.20.15

sg-appsg-monitoring

Both associated security groups contribute their allowed rules.

An instance can have multiple security groups, and an ENI can have multiple security groups subject to AWS quotas. Their allow rules combine: a matching allow rule in any associated group can permit traffic, provided no other control blocks it. Adding a restrictive security group does not cancel a permissive rule in another group.

For example, if `sg-app` permits TCP 8000 only from the load balancer, but another group attached to the same ENI permits TCP 8000 from `0.0.0.0/0`, the second rule can defeat your intended restriction.

Production lesson: audit all security groups attached to an interface, not just the group you intended to use.

### 3.3 Stateful connection tracking

Security groups are stateful. AWS tracks connections so that response traffic for an allowed connection is automatically permitted by the security group, even if there is no matching outbound or inbound rule for that response direction.

Suppose a client at `198.51.100.25` connects to your HTTPS listener:

```text
Client: 198.51.100.25:53000
             |
             | TCP SYN
             v
Server: 10.0.10.20:443
             |
             | TCP SYN-ACK
             v
Client: 198.51.100.25:53000
```

The client selected port `53000` as its source port. The server's response uses source port `443` and destination port `53000`.

If the security group allows the incoming HTTPS connection, it automatically allows the response traffic associated with that connection. You don't need to add a separate outbound security-group rule for client ephemeral ports just to allow that response.

However, this does not mean that a security group automatically permits every new outbound connection. A new connection initiated by the server must satisfy the outbound rules.

Connection tracking also has implementation details involving connection timeouts and certain traffic patterns, so statefulness shouldn't be interpreted as unlimited or permanent permission.

### 4\. Network ACLs (NACLs)

### 4.1 What they do

A Network ACL is a subnet-level traffic filter. Every subnet is associated with exactly one NACL at a time. Multiple subnets can share the same NACL.

Unlike security groups, NACLs support both `ALLOW` and `DENY` rules and are stateless. Inbound and outbound packets are evaluated independently, including response packets.

### 4.2 Rule numbering and evaluation

A custom NACL may contain rules such as these:

| Rule number | Direction | Protocol / port | Source or destination | Action |
| ----------- | --------- | --------------- | --------------------- | ------ |
| 100         | Inbound   | TCP 443         | 0.0.0.0/0             | ALLOW  |
| 110         | Inbound   | TCP 22          | 203.0.113.10/32       | DENY   |
| *           | Inbound   | All             | All remaining traffic | DENY   |

AWS evaluates rules in ascending numerical order and stops at the first match. The `*` rule is the final catch-all.

This creates an important rule-ordering consideration: a broad allow at rule 100 can match traffic before a narrower deny at rule 110. Put the intended exception or deny first.

The table is illustrative, not a recommended complete production NACL. A real inbound HTTPS configuration must also account for return traffic in the outbound direction.

### 4.3 Why stateless filtering requires ephemeral ports

Consider a client connecting to a web server.

```text
Request:
Client:53000  --->  Server:443

Response:
Client:53000  <---  Server:443
```

For a custom NACL to permit the entire exchange, it needs rules for both directions:

* Inbound: permit the request to TCP port 443.

* Outbound: permit the response to the client's ephemeral port, such as 53000.

For a public-facing application, the client's source port is not predictable. The appropriate ephemeral range depends on the client type. AWS documentation notes that requests originating from Elastic Load Balancing use ports in the range `1024–65535`, while many Linux clients use narrower ranges.

This is why NACLs can be deceptively difficult to configure: the inbound request may be allowed while the response is dropped.

### 4.4 Security groups vs. NACLs

| Property        | Security group                                | Network ACL                          |
| --------------- | --------------------------------------------- | ------------------------------------ |
| Scope           | Network interface                             | Subnet                               |
| Stateful?       | Yes                                           | No                                   |
| Allow rules     | Yes                                           | Yes                                  |
| Deny rules      | No                                            | Yes                                  |
| Rule evaluation | Applicable allows combine                     | Lowest-numbered matching rule wins   |
| Return traffic  | Automatically allowed for tracked connections | Must be allowed by directional rules |
| Typical role    | Primary workload firewall                     | Secondary subnet-level guardrail     |

Practical recommendation: use security groups for most workload-to-workload segmentation. Introduce custom NACLs when you have a clear subnet-wide requirement, such as a specific deny control or additional defense in depth. NACLs are not a substitute for least-privilege security groups.

### 5\. Rule design for common protocols

A rule needs more than a port number: it needs the correct protocol and source or destination.

| Workload               | Protocol / port | Recommended source                                            |
| ---------------------- | --------------- | ------------------------------------------------------------- |
| Public HTTPS listener  | TCP 443         | Approved client CIDRs, or 0.0.0.0/0 when intentionally public |
| HTTP redirect listener | TCP 80          | Same intended public client scope                             |
| FastAPI application    | TCP 8000        | Load balancer security group                                  |
| PostgreSQL             | TCP 5432        | Application security group                                    |
| MySQL                  | TCP 3306        | Application security group                                    |
| SSH administration     | TCP 22          | Restricted management path or approved management CIDRs       |

Ports here are examples; configure the port on which your actual application listens.

### Security group references

Instead of writing an application's private subnet CIDR as the source of a database rule, reference the application security group itself.

```text
sg-lb
  |
  | TCP 8000 allowed
  v
sg-app
  |
  | TCP 5432 allowed
  v
sg-db
```

This means the database rule permits matching traffic from network interfaces associated with `sg-app`, rather than every host in the application subnet. It also makes the architecture easier to maintain when application instances change addresses.

Security group references work within the same VPC and in certain supported cross-VPC configurations, such as VPC peering and Transit Gateway arrangements. They don't magically provide routing or make an otherwise unreachable network reachable.

### 6\. Hands-on lab — secure a three-tier application

We'll create three security groups in an existing VPC using Pulumi Python. The lab focuses on security rules, so it reuses the VPC from the earlier modules rather than creating another VPC or incurring unnecessary networking costs.

### 6.1 Target architecture

Internet clients

HTTPS / TCP 443

Public ingress

Load balancer — `sg-lb`

Inbound: TCP 443 from intended clients

Outbound: TCP 8000 to `sg-app`

TCP 8000

Private application tier

FastAPI — `sg-app`

Inbound: TCP 8000 from `sg-lb`

Outbound: TCP 5432 to `sg-db`

TCP 5432

Isolated database tier

PostgreSQL — `sg-db`

Inbound: TCP 5432 from `sg-app`

No general outbound access in this example

This is the intended application flow. Replies for established connections are permitted by security-group state tracking; separate rules for response ephemeral ports aren't necessary in these groups.

### 6.2 Prerequisites and cost

You need:

* Python and a current Pulumi CLI.

* AWS CLI v2, credentials, and permission to manage security groups and rules.

* An existing VPC ID from the earlier VPC modules.

* The AWS Region where that VPC exists.

The security groups themselves do not have a separate hourly charge. This lab does not create an ALB, EC2 instances, NAT gateways, or databases, all of which may incur charges if you create them separately.

### 6.3 Create the Pulumi project

Directory layout:

```text
module5-security/
├── Pulumi.yaml
├── requirements.txt
└── __main__.py
```

`Pulumi.yaml`

```yaml
name: module5-security
runtime:
  name: python
description: Three-tier AWS security group lab
```

`requirements.txt`

```text
pulumi
pulumi-aws
```

Create and activate a Python virtual environment, then install the dependencies:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Configure your existing VPC and Region:

```powershell
pulumi stack init dev
pulumi config set aws:region eu-west-1
pulumi config set vpcId vpc-0123456789abcdef0
```

Replace the example VPC ID and Region with your actual values. If your stack already exists, select it instead of initializing it again.

### 6.4 Implement the security groups

Create `__main__.py`:

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
vpc_id = config.require("vpcId")

# Load balancer: public HTTPS ingress.
lb_sg = aws.ec2.SecurityGroup(
    "lb-sg",
    name="module5-lb-sg",
    description="Public HTTPS ingress for the load balancer",
    vpc_id=vpc_id,
    ingress=[],
    egress=[],
)

# Application: receives traffic only from the load balancer.
app_sg = aws.ec2.SecurityGroup(
    "app-sg",
    name="module5-app-sg",
    description="FastAPI traffic from the load balancer",
    vpc_id=vpc_id,
    ingress=[],
    egress=[],
)

# Database: receives PostgreSQL traffic only from the application.
db_sg = aws.ec2.SecurityGroup(
    "db-sg",
    name="module5-db-sg",
    description="PostgreSQL access from the application tier",
    vpc_id=vpc_id,
    ingress=[],
    egress=[],
)

def rule(name, sg, direction, protocol, from_port, to_port,
         peer_sg=None, cidr=None):
    args = {
        "security_group_id": sg.id,
        "type": direction,
        "protocol": protocol,
        "from_port": from_port,
        "to_port": to_port,
        "description": name,
    }

    if peer_sg is not None:
        args["source_security_group_id" if direction == "ingress"
             else "source_security_group_id"] = peer_sg.id
    elif cidr is not None:
        args["cidr_blocks"] = [cidr]

    return aws.ec2.SecurityGroupRule(name, **args)

# Inbound rules.
lb_https = rule(
    "lb-https-ingress", lb_sg, "ingress",
    "tcp", 443, 443, cidr="0.0.0.0/0"
)

app_from_lb = rule(
    "app-from-lb", app_sg, "ingress",
    "tcp", 8000, 8000, peer_sg=lb_sg
)

db_from_app = rule(
    "db-from-app", db_sg, "ingress",
    "tcp", 5432, 5432, peer_sg=app_sg
)

# Explicit outbound permissions for newly initiated connections.
lb_to_app = rule(
    "lb-to-app", lb_sg, "egress",
    "tcp", 8000, 8000, peer_sg=app_sg
)

app_to_db = rule(
    "app-to-db", app_sg, "egress",
    "tcp", 5432, 5432, peer_sg=db_sg
)

pulumi.export("lbSecurityGroupId", lb_sg.id)
pulumi.export("appSecurityGroupId", app_sg.id)
pulumi.export("dbSecurityGroupId", db_sg.id)
```

Important provider detail: the example intentionally sets `ingress=[]` and `egress=[]` and manages rules as separate resources. Verify the preview removes any default allow-all egress rule; the desired final state has only the explicit rules shown above. The code's outbound rules use the security-group-reference field supported by the AWS provider for egress as well as ingress. If your installed provider version rejects that field for egress, use its documented destination security-group field (`source_security_group_id` is the AWS API field name used for this purpose) and verify the resulting rule with the CLI.

A public HTTPS rule permits clients worldwide to initiate TCP 443 connections to the load balancer. For a production service that is intentionally public, this may be appropriate; otherwise restrict the CIDR to approved clients. This rule does not itself create a load balancer or expose an application.

### 6.5 Preview and deploy

```powershell
pulumi preview
pulumi up
```

Review the preview before confirming. In particular, check that no broad outbound rule remains and that the database group has no inbound rule from the internet.

Exported values can be inspected with:

```powershell
pulumi stack output
```

### 6.6 Verify with AWS CLI

First, confirm the account and Region:

```powershell
aws sts get-caller-identity
aws configure get region
```

List the groups:

```powershell
aws ec2 describe-security-groups `
  --filters Name=vpc-id,Values=vpc-0123456789abcdef0 `
  --query "SecurityGroups[].{Name:GroupName,Id:GroupId}" `
  --output table
```

Inspect a particular security group:

```powershell
aws ec2 describe-security-groups `
  --group-ids sg-0123456789abcdef0 `
  --query "SecurityGroups[0].{Ingress:IpPermissions,Egress:IpPermissionsEgress}" `
  --output json
```

Replace the IDs with those returned by Pulumi. Verify that:

* `sg-lb` permits the intended HTTPS clients and egress to the application on TCP 8000.

* `sg-app` accepts TCP 8000 from `sg-lb` and permits new PostgreSQL connections to `sg-db`.

* `sg-db` accepts TCP 5432 from `sg-app`.

* No unintended broad egress or inbound rules remain.

These commands verify configuration, not end-to-end application connectivity. Since this lab creates no compute resources, actual connection tests require a running load balancer, application, and database.

### 7\. VPC Flow Logs for troubleshooting

VPC Flow Logs record metadata about IP traffic to and from network interfaces. You can enable them for a VPC, subnet, or individual ENI and publish records to CloudWatch Logs, Amazon S3, or Amazon Data Firehose.

### 7.1 Understand the `ACCEPT` and `REJECT` actions

A flow log record contains fields such as source IP, destination IP, source port, destination port, protocol, and action.

| Action   | Meaning                                                                                                                  |
| -------- | ------------------------------------------------------------------------------------------------------------------------ |
| ACCEPT   | The recorded traffic was permitted by the applicable network controls.                                                   |
| REJECT   | The traffic was rejected, for example by a security group or NACL, or because packets arrived after a connection closed. |
| NODATA   | No traffic was recorded during the aggregation interval.                                                                 |
| SKIPDATA | Some records were skipped.                                                                                               |

`ACCEPT` does not prove that the application processed a request successfully. The application might not be listening on the port, might be unhealthy, or might reject the request itself.

### 7.2 Enable Flow Logs using the AWS CLI

For an existing VPC, first identify the VPC ID:

```powershell
aws ec2 describe-vpcs `
  --query "Vpcs[].{VpcId:VpcId,CIDR:CidrBlock}" `
  --output table
```

You can enable Flow Logs from the VPC console or CLI. The following command assumes you already have a CloudWatch log group and an IAM role that grants the Flow Logs service the required permissions to publish to it.

```powershell
aws ec2 create-flow-logs `
  --resource-type VPC `
  --resource-ids vpc-0123456789abcdef0 `
  --traffic-type ALL `
  --log-destination-type cloud-watch-logs `
  --log-group-name /aws/vpc/module5-flow-logs `
  --deliver-logs-permission-arn arn:aws:iam::123456789012:role/VPCFlowLogsRole
```

Replace the VPC ID, account ID, Region, log group, and role with your actual values. The log group and role must exist and be configured appropriately; this command alone does not create them.

Inspect the Flow Logs configuration:

```powershell
aws ec2 describe-flow-logs `
  --filter Name=resource-id,Values=vpc-0123456789abcdef0 `
  --output table
```

Flow Logs aren't instantaneous packet captures. Delivery is best effort and can take several minutes. They also don't show packet payloads or fully replace application logs or packet-level diagnostics. Publishing logs may incur charges.

### 8\. Troubleshooting connectivity systematically

When an application connection fails, don't immediately open every port. Follow the packet path and isolate the layer responsible.

Step 1 — Routing

Verify the source and destination subnets, route tables, and relevant next hops. A security group cannot fix a missing route.

Step 2 — Security groups

Check all groups attached to the relevant ENIs, the correct protocol and port, and the referenced security group or CIDR.

Step 3 — NACLs

Check inbound and outbound rules, first-match numbering, and ephemeral-port rules for response traffic.

Step 4 — Flow Logs and Reachability Analyzer

Use `REJECT` records as clues. Use Reachability Analyzer to identify configuration-level blockers on supported paths.

Step 5 — Application

Confirm the process is listening on the intended interface and port, and inspect load-balancer health checks, application logs, and database configuration.

Reachability Analyzer performs static configuration analysis rather than sending actual packets. It can identify a missing route or a security control blocking a supported network path, but it cannot prove that your application is healthy.

### Common failure scenarios

| Symptom                                 | Likely causes                                                  | What to inspect                                       |
| --------------------------------------- | -------------------------------------------------------------- | ----------------------------------------------------- |
| HTTPS connection times out              | Route, NACL, security group, or listener problem               | Client-to-ALB path, TCP 443, listener configuration   |
| ALB reports unhealthy targets           | Wrong target port, app listener, health-check path, or SG rule | ALB-to-app path, TCP 8000, health-check configuration |
| FastAPI cannot connect to PostgreSQL    | Database SG or routing issue, database not listening           | App-to-DB path, TCP 5432, database status             |
| Request reaches server but reply fails  | NACL return rule, asymmetric path, or application issue        | Both directions, ephemeral ports, Flow Logs           |
| New connections fail after rule changes | Changed rules, tracked connections, or other controls          | Current SG rules and connection state                 |

### Asymmetric paths

Asymmetric routing means traffic takes different network interfaces or paths in opposite directions. This can complicate connection tracking and reduce network performance in some architectures. Keep traffic paths consistent where possible, particularly when appliances, multiple ENIs, or stateful network controls are involved.

### 9\. Production security principles

* Prefer security-group references over broad CIDRs for tier-to-tier traffic.

* Restrict outbound rules intentionally. Remember that a permissive rule in any attached security group can allow traffic.

* Keep the database private. Permit database access only from the application tier or other explicitly authorized clients.

* Use NACLs deliberately. A complex NACL with missing ephemeral-port rules can break otherwise valid connections.

* Audit changes. Security group rule modifications are security-sensitive infrastructure changes; use controlled IAM permissions and review Pulumi previews.

* Monitor traffic. Flow Logs and Reachability Analyzer complement each other but answer different questions.

* Don't assume stateful filtering overrides everything. Routes, NACLs, application listeners, and other network controls still matter.

### 10\. Cleanup

Because this lab creates only security groups and rules, cleanup is straightforward:

```powershell
pulumi destroy
```

Review the proposed deletions before confirming. Do not destroy a shared VPC or resources managed by another stack. If you enabled Flow Logs separately, remove them when no longer needed and review any retained CloudWatch log data and associated charges.

### 11\. Official AWS references

* [Security group rules](https://docs.aws.amazon.com/vpc/latest/userguide/security-group-rules.html?utm_source=chatgpt.com)

* [Control subnet traffic with network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/vpc-network-acls.html?utm_source=chatgpt.com)

* [Custom network ACLs and ephemeral ports](https://docs.aws.amazon.com/vpc/latest/userguide/custom-network-acl.html?utm_source=chatgpt.com)

* [Logging IP traffic using VPC Flow Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html?utm_source=chatgpt.com)

* [Security group connection tracking](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/security-group-connection-tracking.html?utm_source=chatgpt.com)

* [Troubleshoot reachability with Reachability Analyzer](https://docs.aws.amazon.com/vpc/latest/userguide/reachability-analyzer.html?utm_source=chatgpt.com)

* [Pulumi AWS EC2 security group resources](https://www.pulumi.com/registry/packages/aws/api-docs/ec2/securitygroup/?utm_source=chatgpt.com)

Module 5 complete. You now have the concepts and a Pulumi starting point for implementing layered network security. The next module is Module 6 — DNS and Private Name Resolution, covering Route 53, VPC DNS, private hosted zones, Resolver endpoints, and hybrid DNS.
