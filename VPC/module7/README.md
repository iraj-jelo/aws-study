### Module 7 — VPC Endpoints and Private AWS Service Access

This module builds on the VPC routing, NAT, security groups, and DNS concepts from Modules 2–6. The central goal is to let private workloads communicate with AWS services without sending that traffic through a general-purpose internet gateway or NAT gateway.

We'll use Pulumi with Python for infrastructure as code, AWS CLI v2 for verification, and practical examples based on EC2 workloads and private application environments. No quizzes, and we'll focus on current AWS networking practices.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Distinguish gateway endpoints, interface endpoints, and AWS PrivateLink.

* Choose the appropriate endpoint type for S3, DynamoDB, ECR, CloudWatch, and Systems Manager.

* Understand how endpoint policies interact with IAM and resource policies.

* Configure private DNS and endpoint security groups.

* Design workloads that operate without NAT-based access to supported AWS services.

* Deploy and verify endpoints using Pulumi and AWS CLI.

* Diagnose endpoint connectivity, DNS, authorization, and cost issues.

### 2\. The fundamental problem: private workloads need AWS APIs

Imagine an application running on an EC2 instance in a private subnet. It needs to:

* Download an image from Amazon ECR.

* Send application logs to CloudWatch Logs.

* Retrieve configuration from Systems Manager Parameter Store.

* Read objects from an S3 bucket.

Without appropriate private service connectivity, the instance may need outbound connectivity through a NAT gateway to reach public AWS service endpoints.

That creates extra cost and an additional network dependency.

### Without VPC endpoints

Private EC2 instance

Private subnet

Default outbound route

NAT gateway

Public subnet + internet gateway route

AWS public service endpoint

The request depends on NAT routing, public service DNS, and the outbound network path.

### With VPC endpoints

Private EC2 instance

Private subnet

Service-specific routing or private DNS

VPC endpoint

Private service access

AWS service

The selected service traffic can avoid the NAT gateway entirely.

Important distinction: a VPC endpoint doesn't automatically eliminate every need for NAT. It provides a private path to specific supported services. Other internet destinations, third-party APIs, and unsupported endpoints may still require another egress design.

### 3\. Gateway endpoints vs. interface endpoints

AWS provides different endpoint types because services have different networking requirements. The most important distinction is between a route-table-based gateway endpoint and a private-IP-based interface endpoint.

### 3.1 Gateway endpoints

Gateway endpoints support Amazon S3 and Amazon DynamoDB. They add service-specific routes to selected VPC route tables, directing matching traffic to the endpoint instead of the normal default route. They do not create endpoint network interfaces and do not use AWS PrivateLink.

Source: [AWS gateway endpoints documentation](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html?utm_source=chatgpt.com).

Example route table:

| Destination             | Target              |
| ----------------------- | ------------------- |
| 10.20.0.0/16            | local               |
| 0.0.0.0/0               | NAT gateway         |
| S3 regional prefix list | S3 gateway endpoint |

Suppose an instance calls S3 in the same Region. The service-prefix-list route is more specific than `0.0.0.0/0`, so S3 traffic uses the gateway endpoint. Other IPv4 destinations still follow the default route.

Key properties:

* No additional hourly or data-processing charge for the gateway endpoint itself.

* No endpoint security group is needed.

* You select the route tables that should use it.

* The instance still needs appropriate IAM permissions and network rules.

* Gateway endpoints are regional and do not provide access to S3 or DynamoDB in another Region through that endpoint.

A gateway endpoint is usually the first choice for S3 and DynamoDB access from workloads in the same VPC and Region.

### 3.2 Interface endpoints

An interface endpoint uses AWS PrivateLink. AWS creates one or more requester-managed elastic network interfaces (ENIs) in subnets you select. Each ENI has a private IP address.

Your workload connects to the endpoint's private IP addresses over TCP, usually HTTPS on port 443.

Source: [AWS interface endpoint documentation](https://docs.aws.amazon.com/vpc/latest/privatelink/create-interface-endpoint.html?utm_source=chatgpt.com).

Example architecture:

Application EC2

Private subnet · Security group: app-sg

HTTPS · TCP 443

### Interface endpoint

AZ-a

Endpoint ENI

Private IP

AZ-b

Endpoint ENI

Private IP

AWS service API

For example, CloudWatch Logs or Systems Manager

Key properties:

* Supports many AWS services, including ECR, CloudWatch, and Systems Manager.

* Uses private IP addresses assigned to endpoint ENIs.

* Requires a security group associated with the endpoint ENIs.

* Can use private DNS so standard service names resolve to private endpoint addresses.

* Incurs hourly endpoint and data-processing charges.

* Can be deployed across multiple Availability Zones for resilience.

You do not need to place interface endpoints in every subnet. Instead, select suitable subnets, ideally across multiple AZs, and allow clients to reach the endpoint ENIs.

### 3.3 Comparison

| Property                 | Gateway endpoint                 | Interface endpoint                                         |
| ------------------------ | -------------------------------- | ---------------------------------------------------------- |
| Networking mechanism     | Route-table entries              | Private IP addresses on ENIs                               |
| Services                 | S3, DynamoDB                     | Many AWS services                                          |
| AWS PrivateLink          | No                               | Yes                                                        |
| Endpoint security group  | No                               | Yes                                                        |
| Route table modification | Required                         | Not usually required for endpoint access                   |
| Private DNS              | Not required for routing         | Commonly used                                              |
| Endpoint hourly charges  | None                             | Yes                                                        |
| Access from on-premises  | Not directly                     | Possible with appropriate hybrid routing and DNS           |
| Cross-Region access      | Not through the gateway endpoint | Depends on service and supported PrivateLink configuration |

S3 and DynamoDB support both gateway and interface endpoints, but that does not make the two options interchangeable in every architecture. In particular, interface endpoints are useful for certain hybrid and cross-VPC access scenarios that gateway endpoints do not support.

### 4\. How AWS PrivateLink works

AWS PrivateLink is the underlying technology used by interface endpoints to privately connect consumers to supported services.

There are two common use cases:

* Consuming AWS services: Your application connects privately to an AWS service such as ECR or CloudWatch.

* Consuming a service owned by another account: A provider exposes an application through a VPC endpoint service, commonly fronted by a Network Load Balancer. Consumers create interface endpoints in their own VPCs.

For example, imagine a SaaS provider offering an internal billing API to customer VPCs.

### Consumer VPC

Customer application

Interface endpoint

### Provider VPC

Billing API

Network Load Balancer

PrivateLink connection

The consumer doesn't need a route to the provider's entire VPC CIDR. The endpoint exposes the selected service, reducing network exposure.

The provider controls service permissions and can require manual acceptance of endpoint connection requests. The consumer controls the endpoint, its subnet placement, security groups, and its own application authorization.

This is useful when two VPCs have overlapping CIDRs or when you want to expose a single service without establishing broad network connectivity.

Official reference: [What is AWS PrivateLink?](https://docs.aws.amazon.com/vpc/latest/privatelink/what-is-privatelink.html?utm_source=chatgpt.com).

### 5\. Endpoint policies and IAM: separate security layers

Creating an endpoint does not automatically grant the application permission to use the service.

A request may be affected by several independent controls:

* Network controls: Routes, security groups, and network ACLs determine whether the connection can be established.

* Identity-based IAM policy: Determines which actions the workload's role or user may perform.

* Resource-based policy: For example, an S3 bucket policy can restrict which principals or endpoints may access the bucket.

* VPC endpoint policy: Restricts which principals and actions can pass through the endpoint to the service.

* Other applicable authorization controls: Such as permissions boundaries, session policies, and AWS Organizations service control policies.

An endpoint policy does not replace or override IAM or a service resource policy. It adds another layer of access control.

### Example: restrict an S3 gateway endpoint

Suppose your application only needs objects from one bucket, `company-private-data`, in account `123456789012`.

A restrictive gateway endpoint policy could be:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ListApprovedBucket",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::company-private-data"
    },
    {
      "Sid": "ReadApprovedObjects",
      "Effect": "Allow",
      "Principal": "*",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::company-private-data/*"
    }
  ]
}
```

This is an endpoint-level allowlist. It does not grant every caller access to the bucket: the caller must also satisfy the service's applicable authorization policies. For gateway endpoints, `Principal` must be `"*"`, with conditions such as `aws:PrincipalArn` used when principal-specific restrictions are needed.

In a production environment, scope the workload role's IAM policy to the exact required bucket and object paths as well.

### A common authorization failure

An EC2 instance can successfully establish an HTTPS connection to S3 but receive `AccessDenied`.

That points toward authorization rather than basic network connectivity. Check the IAM role, bucket policy, endpoint policy, and any applicable organization-level restrictions before changing routes or opening network access.

### 6\. Private DNS for interface endpoints

Private DNS is one of the most useful features of interface endpoints because it allows existing applications to keep using standard AWS service names.

For example, an application normally sends CloudWatch Logs requests to a regional hostname such as:

```text
logs.eu-west-1.amazonaws.com
```

With an interface endpoint and private DNS enabled, DNS resolution inside the VPC returns private IP addresses belonging to the endpoint ENIs instead of the usual public service addresses.

Application

Connects to logs.eu-west-1.amazonaws.com:443

DNS lookup via Route 53 Resolver

Private DNS answer

Private endpoint ENI addresses

Interface endpoint → CloudWatch Logs

To enable private DNS, the VPC must have both DNS resolution and DNS hostnames enabled. For a typical AWS service endpoint, you should normally leave private DNS enabled unless you have a specific reason not to.

### Why this matters

Without private DNS, an application might continue resolving the public service hostname to public IP addresses and attempt to use its normal route. A private endpoint can exist and still not be used by the application.

With private DNS, existing SDKs and AWS CLI commands can generally keep using their ordinary regional service URLs.

Useful diagnostics:

```bash
# Inspect VPC DNS attributes
aws ec2 describe-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --attribute enableDnsSupport

aws ec2 describe-vpc-attribute \
  --vpc-id "$VPC_ID" \
  --attribute enableDnsHostnames

# Inspect endpoint DNS entries
aws ec2 describe-vpc-endpoints \
  --vpc-endpoint-ids "$VPCE_ID" \
  --query 'VpcEndpoints[0].DnsEntries'
```

On an EC2 instance, test the normal hostname:

```bash
nslookup logs.eu-west-1.amazonaws.com
```

The exact output varies by service, Region, endpoint configuration, and DNS record selection. For an interface endpoint with private DNS enabled, you should see private endpoint addresses from inside the VPC.

### An S3-specific DNS detail

S3 supports both gateway and interface endpoints, and its private DNS behavior has additional options. For a common same-VPC workload, use an S3 gateway endpoint. AWS also supports configurations that combine an S3 interface endpoint with a gateway endpoint, including private DNS specifically for inbound Resolver traffic.

Do not blindly enable the S3 interface endpoint's inbound-only private DNS option without the required gateway endpoint. AWS documents this dependency explicitly.

### 7\. Which endpoints do common AWS workloads need?

The endpoint list depends on the API calls and features your application actually uses. An endpoint for one service does not automatically cover every related service.

| Workload requirement                              | Typical private connectivity                                                            |
| ------------------------------------------------- | --------------------------------------------------------------------------------------- |
| Read and write S3 objects                         | S3 gateway endpoint                                                                     |
| Access DynamoDB                                   | DynamoDB gateway endpoint                                                               |
| Pull private ECR images                           | ECR API + ECR Docker interface endpoints, plus S3 access for image layers               |
| Publish CloudWatch metrics                        | CloudWatch Monitoring interface endpoint                                                |
| Send logs to CloudWatch Logs                      | CloudWatch Logs interface endpoint                                                      |
| Use Systems Manager Run Command / Session Manager | SSM and ssmmessages endpoints; additional endpoints may be needed for specific features |
| Download SSM-managed files or patch artifacts     | S3 access, with any required bucket permissions and network rules                       |
| Use KMS APIs privately                            | KMS interface endpoint, when needed                                                     |

Service requirements and endpoint names can vary by feature, Region, and IP address configuration. Verify them against the service-specific documentation before deploying a production endpoint inventory.

Sources: [ECR VPC endpoints](https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html?utm_source=chatgpt.com), [Systems Manager VPC endpoints](https://docs.aws.amazon.com/us_en/systems-manager/latest/userguide/setup-create-vpc.html?utm_source=chatgpt.com), and [CloudWatch VPC endpoints](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/cloudwatch-and-interface-VPC.html?utm_source=chatgpt.com).

### ECR: a particularly important example

Private ECR image pulls demonstrate why endpoint planning must account for dependencies.

```text
EC2 / container runtime
        |
        v
ECR API endpoint
        |
        v
Image manifest and authorization
        |
        v
ECR Docker endpoint
        |
        v
S3 gateway endpoint
        |
        v
Image layers
```

The ECR API and Docker registry endpoints provide access to the registry operations, but image layers are stored in S3. Without the required S3 path, a pull can fail even when the ECR endpoints are healthy.

### 8\. Endpoint security groups and subnet placement

Interface endpoints have ENIs, so security groups are part of their access path.

A useful design is to separate the application security group from the endpoint security group.

* `app-sg`: attached to EC2 application instances.

* `vpce-sg`: attached to interface endpoint ENIs.

The endpoint security group should allow inbound TCP 443 from the application security group. The application security group must permit outbound HTTPS to the endpoint, and subnet network ACLs must allow the necessary traffic in both directions.

Example rules:

| Security group | Direction | Protocol / port | Source or destination |
| -------------- | --------- | --------------- | --------------------- |
| app-sg         | Outbound  | TCP 443         | vpce-sg               |
| vpce-sg        | Inbound   | TCP 443         | app-sg                |

Security group references are preferable to hardcoding endpoint IP addresses, because ENIs and their addresses may change if the endpoint is modified or recreated.

### Availability Zone strategy

For production workloads, consider endpoint ENIs in at least two Availability Zones, aligned with the workload's AZ distribution. A regional DNS name can resolve to endpoint ENIs across the configured AZs; a single-AZ endpoint creates a dependency on that AZ for clients using the regional DNS name.

A one-AZ endpoint can be adequate for a temporary lab, but its lower endpoint cost comes with reduced resilience. Also remember that endpoint ENIs consume subnet addresses, so include them in your IP capacity planning.

### 9\. Hands-on lab — private S3 and CloudWatch Logs access with Pulumi

We'll build a focused lab that demonstrates both endpoint types:

* An S3 gateway endpoint to avoid NAT for S3 traffic.

* A CloudWatch Logs interface endpoint to provide private access to the Logs API.

* Security groups that permit only the required HTTPS path.

* AWS CLI checks that confirm the endpoint resources and routing.

We'll reuse the VPC and private subnets created in earlier modules rather than recreate the entire network.

### 9.1 Prerequisites and cost safety

You need an AWS account and credentials with permission to manage VPC endpoints, security groups, route tables, and associated resources. The VPC must already have private subnets, and you should know its ID, private subnet IDs, and private route-table IDs.

This lab requires real AWS infrastructure. The S3 gateway endpoint has no additional endpoint charge; the CloudWatch Logs interface endpoint is billable per endpoint-AZ-hour and data processed. Other resources, including EC2, S3 storage, and CloudWatch Logs ingestion, may incur charges too.

Do not create a NAT gateway just for this lab. If your private subnets already have one, we can leave it in place initially and prove that the selected traffic uses endpoints instead.

### 9.2 Project structure

```text
vpc-endpoints-lab/
├── Pulumi.yaml
├── requirements.txt
├── __main__.py
└── Pulumi.dev.yaml
```

`Pulumi.yaml`:

```yaml
name: vpc-endpoints-lab
runtime:
  name: python
description: Private AWS service access using VPC endpoints
```

`requirements.txt`:

```text
pulumi
pulumi-aws
```

Create and activate a virtual environment, then install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

pulumi stack init dev
pulumi config set aws:region eu-west-1
```

Use a Region in which your existing VPC resides. The Region above is only an example.

### 9.3 Pulumi configuration

Supply the IDs of your existing resources:

```powershell
pulumi config set vpcId vpc-0123456789abcdef0
pulumi config set privateSubnetIds '["subnet-0123456789abcdef0","subnet-0abcdef0123456789"]'
pulumi config set privateRouteTableIds '["rtb-0123456789abcdef0","rtb-0abcdef0123456789"]'
```

Replace all example IDs with actual IDs from your account. The subnets and route tables must belong to the specified VPC and Region. For a high-availability setup, choose subnets in distinct Availability Zones.

`Pulumi.dev.yaml` is managed by Pulumi when you set stack configuration; do not manually paste placeholder IDs into it.

### 9.4 Infrastructure implementation

The following implementation creates a security group for the interface endpoint, an S3 gateway endpoint, and a CloudWatch Logs interface endpoint.

`__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
private_subnet_ids = config.require_object("privateSubnetIds")
private_route_table_ids = config.require_object(
    "privateRouteTableIds"
)

region = aws.get_region().name

# Discover the existing VPC and verify the lab's target.
vpc = aws.ec2.get_vpc(id=vpc_id)

if vpc.id != vpc_id:
    raise ValueError("Configured VPC was not found")

# Security group attached to the CloudWatch Logs endpoint ENIs.
endpoint_sg = aws.ec2.SecurityGroup(
    "vpce-logs-sg",
    description="Allow HTTPS from approved application clients",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=[vpc.cidr_block],
            description="HTTPS from inside the VPC",
        )
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Allow return and required outbound traffic",
        )
    ],
    tags={"Purpose": "vpc-endpoints-lab"},
)

# Gateway endpoint: S3.
s3_endpoint = aws.ec2.VpcEndpoint(
    "s3-gateway-endpoint",
    vpc_id=vpc_id,
    service_name=f"com.amazonaws.{region}.s3",
    vpc_endpoint_type="Gateway",
    route_table_ids=private_route_table_ids,
    tags={"Purpose": "vpc-endpoints-lab"},
)

# Interface endpoint: CloudWatch Logs.
logs_endpoint = aws.ec2.VpcEndpoint(
    "cloudwatch-logs-interface-endpoint",
    vpc_id=vpc_id,
    service_name=f"com.amazonaws.{region}.logs",
    vpc_endpoint_type="Interface",
    subnet_ids=private_subnet_ids,
    security_group_ids=[endpoint_sg.id],
    private_dns_enabled=True,
    tags={"Purpose": "vpc-endpoints-lab"},
)

pulumi.export("vpc_id", vpc_id)
pulumi.export("s3_endpoint_id", s3_endpoint.id)
pulumi.export("logs_endpoint_id", logs_endpoint.id)
pulumi.export("endpoint_security_group_id", endpoint_sg.id)
```

A few important details:

* The S3 endpoint attaches to the selected route tables. It does not need endpoint ENIs or a security group.

* The Logs endpoint creates ENIs in the selected subnets.

* Private DNS lets ordinary CloudWatch Logs API hostnames resolve through the endpoint.

* The example endpoint security group allows HTTPS from the VPC CIDR. This is convenient for the initial lab, but a production design should restrict inbound access to the application security group.

* The example's egress rule is broad. In a stricter environment, evaluate the required endpoint traffic and return-path behavior before narrowing it.

* The `vpc_id` lookup verifies that the VPC exists; validate subnet and route-table membership as well before applying the project to a production environment.

For endpoint policy restrictions, use the appropriate endpoint policy document and verify service-specific support. The lab initially uses AWS's default endpoint policy behavior so we can focus on network connectivity.

### 9.5 Preview and deploy

Inspect the proposed changes first:

```powershell
pulumi preview
```

If the plan contains only the resources you expect, deploy:

```powershell
pulumi up
```

Review the plan and explicitly approve the update when prompted.

Inspect the outputs:

```powershell
pulumi stack output
```

Record the endpoint IDs for the next steps.

### 9.6 Verify the endpoints

Set environment variables in PowerShell using your stack outputs:

```powershell
$S3_VPCE = pulumi stack output s3_endpoint_id
$LOGS_VPCE = pulumi stack output logs_endpoint_id
```

Inspect their status:

```powershell
aws ec2 describe-vpc-endpoints `
  --vpc-endpoint-ids $S3_VPCE $LOGS_VPCE `
  --query 'VpcEndpoints[*].{Id:VpcEndpointId,Service:ServiceName,Type:VpcEndpointType,State:State,PrivateDNS:PrivateDnsEnabled}'
```

Wait for both endpoints to reach `available`.

Inspect the S3 route-table entries:

```powershell
aws ec2 describe-route-tables `
  --route-table-ids rtb-0123456789abcdef0 rtb-0abcdef0123456789 `
  --query 'RouteTables[*].{Id:RouteTableId,Routes:Routes}'
```

Use your real route-table IDs. Look for the S3 prefix-list route whose target is the gateway endpoint ID.

Inspect the Logs endpoint ENIs and DNS names:

```powershell
aws ec2 describe-vpc-endpoints `
  --vpc-endpoint-ids $LOGS_VPCE `
  --query 'VpcEndpoints[0].{ENIs:NetworkInterfaceIds,DNS:DnsEntries}'
```

Then inspect the endpoint security group:

```powershell
aws ec2 describe-security-groups `
  --group-ids (pulumi stack output endpoint_security_group_id)
```

### 9.7 Verify connectivity from a private workload

Run these commands from an EC2 instance in one of the configured private subnets, using a suitable instance profile and AWS CLI installation.

Check the S3 DNS name and access:

```bash
getent hosts s3.eu-west-1.amazonaws.com

aws s3api list-buckets
```

The `list-buckets` call requires the instance role to have the relevant S3 permissions. It can fail with `AccessDenied` even when endpoint routing is correct. A more controlled test is to use a known test bucket and object for which the role has permission.

For CloudWatch Logs:

```bash
getent hosts logs.eu-west-1.amazonaws.com

aws logs describe-log-groups --region eu-west-1
```

The command needs the relevant CloudWatch Logs permissions. If it succeeds, you have demonstrated that the API call can work with the endpoint in place, but that alone does not prove that no NAT path was used.

To establish the routing behavior, combine DNS results, the endpoint configuration, route tables, and your network design. For the S3 request, confirm the S3 prefix-list route targets the gateway endpoint. For the Logs request, confirm the hostname resolves to the endpoint's private ENI addresses and that the security group permits the connection.

The lab's success criterion: the required S3 and CloudWatch Logs calls succeed from the private workload with the required IAM permissions, and the intended paths do not depend on NAT.

### 10\. Troubleshooting endpoint failures

Use a layered troubleshooting process. Do not immediately change route tables or open security groups: first identify which part of the connection is failing.

| Symptom                                  | Likely causes                                                         | What to inspect                                     |
| ---------------------------------------- | --------------------------------------------------------------------- | --------------------------------------------------- |
| DNS returns public IP addresses          | Private DNS disabled, wrong VPC DNS attributes, custom DNS forwarding | nslookup, endpoint DNS configuration                |
| Connection times out                     | Endpoint SG, NACL, missing route, wrong endpoint subnet               | Security groups, NACLs, endpoint ENIs               |
| AccessDenied                             | IAM, endpoint policy, resource policy, organization restrictions      | IAM policy evaluation and service-specific policies |
| S3 works but ECR image pull fails        | Missing ECR interface endpoint or S3 layer access                     | ECR API, ECR Docker, S3 endpoint                    |
| Session Manager cannot connect           | Missing ssmmessages, incorrect instance role, agent or DNS issue      | SSM endpoints, agent logs, instance profile         |
| Endpoint works in one AZ but not another | Single-AZ endpoint dependency or AZ impairment                        | Endpoint subnet placement and DNS answers           |
| Endpoint creation fails                  | Invalid service name, unsupported service or AZ, quota reached        | Region, service availability, VPC endpoint quotas   |

### A systematic diagnostic sequence

* Check endpoint state. Use `describe-vpc-endpoints` and ensure the endpoint is `available`.

* Check DNS. Resolve the standard service hostname from the actual workload, not just your laptop.

* Check routing. For gateway endpoints, verify the selected route tables contain the service prefix-list route. For interface endpoints, verify that the workload can route to the endpoint ENI addresses.

* Check security. Confirm HTTPS is allowed in the appropriate directions and that NACLs permit both the request and response traffic.

* Check authorization. If the TLS connection succeeds but the API returns `AccessDenied`, investigate IAM, endpoint policy, resource policy, and other applicable authorization controls.

* Check service dependencies. Confirm that the workload can reach every service it needs, not merely the first API it calls.

Official reference: [Configure and troubleshoot interface endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/interface-endpoints.html?utm_source=chatgpt.com).

### 11\. Endpoint quotas, availability, and cost

Interface endpoints incur charges for each provisioned endpoint in each AZ and for data processed. Gateway endpoints for S3 and DynamoDB have no additional endpoint charge. The exact cost comparison depends on traffic volume, endpoint count, Region, and the alternative egress architecture.

### Architectural trade-offs

| Design                                 | Advantages                                               | Trade-offs                                                                       |
| -------------------------------------- | -------------------------------------------------------- | -------------------------------------------------------------------------------- |
| S3 gateway endpoint                    | No additional endpoint charge; simple same-Region access | Route-table based; not directly usable from on-premises                          |
| Interface endpoint in one AZ           | Lower endpoint hourly cost                               | AZ dependency; clients in other AZs may use cross-AZ paths                       |
| Interface endpoint across multiple AZs | Better resilience and local-AZ endpoint options          | Higher hourly charges                                                            |
| NAT gateway for all AWS API access     | Simple outbound path for many destinations               | NAT charges and dependency; unnecessary for services reachable through endpoints |
| Endpoints plus selective NAT           | Private AWS service access and controlled general egress | More resources and more detailed dependency management                           |

AWS documents a default quota of 50 interface and Gateway Load Balancer endpoints combined per VPC, adjustable, and a default quota of 20 gateway endpoints per Region, also adjustable. Confirm the current quota in your account and Region before designing at scale.

Other considerations:

* IP capacity: Interface endpoint ENIs consume subnet addresses.

* Availability: Deploy critical interface endpoints in at least two AZs when supported and justified.

* Throughput: Check endpoint quotas and documented throughput characteristics for demanding workloads.

* DNS: Centralized or custom DNS designs must correctly resolve the endpoint names.

* Cost: Do not create every possible endpoint by default. Identify actual service dependencies and compare endpoint costs with the NAT traffic they replace.

For the current quota details, consult the official [AWS PrivateLink quotas documentation](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-limits-endpoints.html?utm_source=chatgpt.com).

### 12\. Designing a workload without general-purpose internet egress

A private workload can often operate without a NAT gateway if every required external dependency has an appropriate private access path.

For example, an EC2 application might need:

* S3 for object storage.

* ECR and S3 for container image pulls.

* CloudWatch Logs for application logs.

* Systems Manager for administration.

* KMS for encryption operations.

You would create the corresponding gateway and interface endpoints, configure IAM roles and security groups, and ensure that DNS and service dependencies are correct.

However, consider what happens when the application also needs to download packages from PyPI, call an external SaaS API, or access a public Git repository. Those destinations are not automatically covered by AWS service endpoints. You must provide another approved path, such as controlled egress, a proxy, or an internal artifact mirror.

A good production design starts with an explicit dependency inventory:

| Dependency                  | Required path                                                      | General internet egress needed?     |
| --------------------------- | ------------------------------------------------------------------ | ----------------------------------- |
| S3 in the same Region       | Gateway endpoint                                                   | No                                  |
| DynamoDB in the same Region | Gateway endpoint                                                   | No                                  |
| CloudWatch Logs             | Interface endpoint                                                 | No                                  |
| ECR image layers            | S3 gateway endpoint plus ECR endpoints                             | No                                  |
| Systems Manager             | Required SSM interface endpoints and any additional dependencies   | No, if all requirements are covered |
| Public third-party API      | Approved egress or private connectivity supported by that provider | Depends on the available design     |

The key principle is to design around the application's complete dependency graph, not just its main AWS service.

### 13\. Cleanup and operational safety

When the lab is finished, remove only the resources created specifically for it.

```powershell
pulumi destroy
```

Review the proposed deletions before approving them. The stack should remove the S3 gateway endpoint, CloudWatch Logs interface endpoint, and endpoint security group. It should not delete the VPC, existing subnets, or route tables that were created in earlier modules.

Then verify that the endpoints have been removed:

```powershell
aws ec2 describe-vpc-endpoints `
  --filters "Name=tag:Purpose,Values=vpc-endpoints-lab"
```

This command should return no remaining matching endpoints after cleanup. Check the security group separately if necessary.

If you used existing route tables, verify that other infrastructure still has the intended routing configuration. Do not manually delete shared resources merely because they were involved in the lab.

### 14\. Key takeaways

* Gateway endpoints are the default choice for same-Region S3 and DynamoDB access from a VPC.

* Interface endpoints provide private-IP connectivity to many AWS APIs through AWS PrivateLink.

* Private DNS makes existing applications use endpoint ENIs without changing their standard AWS service hostnames.

* Endpoint policies restrict access through the endpoint but do not replace IAM or resource policies.

* Security groups, routing, DNS, and authorization must all be correct for an API call to succeed.

* Private service access is not the same as universal internet access. NAT can be eliminated for selected paths without eliminating the need for an approved egress design for every other dependency.

### Official AWS references

* [Gateway endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/gateway-endpoints.html?utm_source=chatgpt.com)

* [Interface endpoints](https://docs.aws.amazon.com/vpc/latest/privatelink/interface-endpoints.html?utm_source=chatgpt.com)

* [VPC endpoint policies](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-endpoints-access.html?utm_source=chatgpt.com)

* [AWS services supporting PrivateLink](https://docs.aws.amazon.com/vpc/latest/privatelink/aws-services-privatelink-support.html?utm_source=chatgpt.com)

* [Amazon ECR VPC endpoints](https://docs.aws.amazon.com/AmazonECR/latest/userguide/vpc-endpoints.html?utm_source=chatgpt.com)

* [Systems Manager VPC endpoints](https://docs.aws.amazon.com/us_en/systems-manager/latest/userguide/setup-create-vpc.html?utm_source=chatgpt.com)

* [AWS PrivateLink quotas](https://docs.aws.amazon.com/vpc/latest/privatelink/vpc-limits-endpoints.html?utm_source=chatgpt.com)

That completes Module 7. When you're ready, ask for Module 8 — VPC Peering and Transit Gateway.
