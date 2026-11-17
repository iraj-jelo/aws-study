Worked for 57s

### Phase 4 — Compute

### Module 3 — EC2 IAM Roles and Instance Profiles

Level: Beginner to intermediate · Infrastructure as Code: Pulumi with Python · Focus: secure workload identities and least privilege

In Module 1, you launched an EC2 instance. In Module 2, you attached encrypted EBS storage. Now you'll learn how to give applications running on EC2 permission to access other AWS services without storing long-lived AWS access keys on the instance.

Imagine your FastAPI application needs to read configuration files from Amazon S3, publish logs to CloudWatch, or use Systems Manager for administration. How should it authenticate?

The recommended approach is to give the EC2 instance an IAM role with narrowly scoped permissions. AWS provides temporary credentials to the application through the instance metadata service, and supported AWS SDKs can retrieve and refresh those credentials automatically.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Explain the difference between IAM users, roles, policies, and instance profiles.

* Understand how EC2 assumes an IAM role.

* Read and write role trust policies and permission policies.

* Explain temporary credentials and their automatic refresh.

* Configure and troubleshoot Instance Metadata Service Version 2 (IMDSv2).

* Understand how SSRF vulnerabilities can expose instance credentials.

* Grant scoped access to S3, Systems Manager, and CloudWatch.

* Diagnose `AccessDenied` errors and identify which policy layer is responsible.

* Provision workload identities using Pulumi and Python.

* Deploy an EC2 application that accesses a specific S3 location without embedded AWS credentials.

### 2\. Why EC2 needs a workload identity

Consider an application running on an EC2 instance that needs to read an object from S3.

A common but unsafe approach is to create an IAM user, generate an access key, and put the key in an environment variable or configuration file on the instance.

That creates an unnecessary long-lived secret. If the key leaks through logs, a backup, a container image, or a compromised application, an attacker may be able to use it outside the instance until the key is revoked or otherwise disabled.

A better design is:

EC2 instance

Your application and AWS SDK

Instance Metadata Service

Provides temporary role credentials to authorized local requests

Temporary AWS credentials

Access key, secret key, session token, expiration

Amazon S3

Requests authorized by the role's effective permissions

The application doesn't need to know or store a permanent access key. The AWS SDK can use the instance role automatically, and the temporary credentials are refreshed as necessary.

Core principle: Use an IAM role for an AWS workload running on EC2, rather than distributing long-lived IAM user access keys to the application.

### 3\. IAM roles, trust policies, and instance profiles

Three concepts are essential to understand before writing the infrastructure code.

IAM role

An identity that can be assumed by a trusted principal. A role has permissions defining which AWS actions are allowed or denied when it is assumed.

Trust policy

Defines which principals can assume the role. For an EC2 workload role, the trusted service is normally `ec2.amazonaws.com`, with the action `sts:AssumeRole`.

Instance profile

A container for an IAM role that EC2 can associate with an instance. In the API and infrastructure code, the instance profile connects the role to the EC2 instance.

### 3.1 Trust policy versus permission policy

These two policy types solve different problems.

A trust policy answers:

> Who is allowed to assume this role?

A permission policy answers:

> What is a principal using this role allowed to do?

For example, the EC2 trust relationship can be represented as:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "ec2.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

This does not grant access to S3. It allows the EC2 service to assume the role.

A separate permissions policy can grant read access to a specific S3 bucket or prefix. AWS evaluates the resulting permissions alongside other applicable controls, including explicit denies, permissions boundaries, organization policies, and resource policies.

### 4\. Temporary credentials and the instance metadata service

EC2 exposes a local service called the Instance Metadata Service (IMDS). The service is available from inside the instance, including at the IPv4 link-local address `169.254.169.254`.

When an IAM role is attached to an instance, the metadata service can provide the role's temporary security credentials to authorized local requests.

Those credentials contain:

* An access key ID.

* A secret access key.

* A session token.

* An expiration time.

The AWS SDK uses the credentials to sign requests to AWS APIs. Supported SDKs can refresh the temporary credentials automatically.

### 4.1 IMDSv2

IMDSv2 adds a session-oriented token exchange. A client first requests a token and then includes it in subsequent metadata requests.

Example diagnostic commands on an EC2 instance:

```bash
TOKEN=$(curl -sS -X PUT \
  "http://169.254.169.254/latest/api/token" \
  -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")

curl -sS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  "http://169.254.169.254/latest/meta-data/iam/security-credentials/"
```

If the instance has a role attached, the second command should return its role name. This command does not print the secret credentials.

You can inspect the role credentials' expiration metadata without exposing the actual key material:

```bash
ROLE_NAME=$(curl -sS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  "http://169.254.169.254/latest/meta-data/iam/security-credentials/")

curl -sS \
  -H "X-aws-ec2-metadata-token: $TOKEN" \
  "http://169.254.169.254/latest/meta-data/iam/security-credentials/$ROLE_NAME" \
  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("Expiration"))'
```

Do not print or log the complete credential response, which contains secrets.

### 4.2 Why IMDSv2 matters for SSRF

Server-Side Request Forgery (SSRF) occurs when an attacker can manipulate a server-side application into making requests to unintended destinations.

If a vulnerable application can reach the instance metadata endpoint, an attacker may try to retrieve metadata or role credentials and then use those credentials to call AWS APIs.

IMDSv2 helps mitigate some SSRF techniques because it requires a token obtained through a `PUT` request before metadata can be accessed. However, IMDSv2 is not a complete defense against SSRF. Application-layer request validation, restrictive network controls, and careful credential handling remain necessary.

For EC2 applications, configure the metadata service to require IMDSv2:

```python
metadata_options={
    "http_endpoint": "enabled",
    "http_tokens": "required",
}
```

This configuration will appear in our Pulumi lab.

### 5\. Least privilege for S3, Systems Manager, and CloudWatch

A workload role should receive only the permissions required by its application.

| Workload requirement                            | Example permission scope                                                   |
| ----------------------------------------------- | -------------------------------------------------------------------------- |
| Read an application's S3 objects                | s3:GetObject on a specific object prefix                                   |
| List available objects                          | s3:ListBucket on one bucket, restricted to a prefix where appropriate      |
| Administer the instance through Session Manager | Appropriate Systems Manager managed-instance permissions and configuration |
| Send application logs to CloudWatch             | Required log-stream and log-event permissions for designated log groups    |
| Publish custom metrics                          | cloudwatch:PutMetricData, optionally constrained by supported conditions   |

Avoid giving an application `s3:*`, `AdministratorAccess`, or unrestricted access to every bucket just because the application needs to read one configuration file.

A subtle but important distinction: `s3:ListBucket` applies to the bucket ARN, while `s3:GetObject` applies to object ARNs. A policy that specifies only one of these may not support both operations.

For Systems Manager and CloudWatch, AWS-managed policies can help you get started, but review their scope and prefer appropriately scoped policies for production. The permissions required for Session Manager also depend on how the instance reaches Systems Manager and which features you enable.

### 6\. Hands-on lab — Give an EC2 application scoped S3 access

### Scenario

A small Python application runs on EC2 and reads a configuration object from a dedicated S3 bucket. It must not store AWS access keys in its source code, environment variables, or local credentials file.

Estimated time: 45–75 minutes

You'll use Pulumi with Python to create the bucket, IAM role, trust policy, permissions policy, instance profile, and EC2 instance.

### 6.1 Architecture

Pulumi deployment

Creates resources and uploads a test configuration

IAM role

Trusts EC2

S3 bucket

Stores application config

EC2 instance + instance profile

IMDSv2 → temporary role credentials

Python application using Boto3

Reads only the allowed S3 object

The application doesn't receive a static AWS key. Boto3's default credential provider chain discovers the attached instance role credentials and refreshes them as necessary.

### 6.2 Create the project

```bash
mkdir ec2-iam-role-lab
cd ec2-iam-role-lab

pulumi new aws-python
python -m pip install pulumi pulumi-aws
```

Configure the AWS Region through Pulumi and verify your deployment identity:

```bash
aws sts get-caller-identity
aws configure get region
pulumi config
```

The identity running Pulumi needs permission to create the resources in this lab, including IAM roles and policies, EC2 resources, and S3 resources. Those are deployment permissions; they are separate from the permissions assigned to the application role.

### 6.3 Define the infrastructure with Pulumi

Replace `__main__.py` with the following example. It creates a private S3 bucket, uploads a sample configuration object, creates a narrowly scoped IAM role and instance profile, and launches an EC2 instance configured to read that object.

```python
import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

# Find the default VPC and one of its subnets.
vpc = aws.ec2.get_vpc(default=True)
subnets = aws.ec2.get_subnets(
    filters=[{"name": "vpc-id", "values": [vpc.id]}]
)

if not subnets.ids:
    raise ValueError("No subnet found in the default VPC.")

subnet = aws.ec2.get_subnet(id=subnets.ids[0])

# Private S3 bucket containing application configuration.
bucket = aws.s3.BucketV2(
    "app-config-bucket",
    tags={"Purpose": "ec2-iam-lab"},
)

aws.s3.BucketPublicAccessBlock(
    "app-config-public-access",
    bucket=bucket.id,
    block_public_acls=True,
    ignore_public_acls=True,
    block_public_policy=True,
    restrict_public_buckets=True,
)

aws.s3.BucketServerSideEncryptionConfigurationV2(
    "app-config-encryption",
    bucket=bucket.id,
    rules=[{
        "apply_server_side_encryption_by_default": {
            "sse_algorithm": "AES256",
        }
    }],
)

config_object = aws.s3.BucketObjectv2(
    "app-config-object",
    bucket=bucket.id,
    key="app/config.json",
    content=json.dumps({
        "message": "Read from S3 using an EC2 IAM role",
        "environment": "learning",
    }),
    content_type="application/json",
)

# Trust policy: allow the EC2 service to assume this role.
role = aws.iam.Role(
    "app-ec2-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
    tags={"Purpose": "ec2-iam-lab"},
)

# Permission policy: read only objects under app/* in this bucket.
policy = aws.iam.RolePolicy(
    "app-s3-read-policy",
    role=role.id,
    policy=pulumi.Output.all(
        bucket.arn
    ).apply(lambda values: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "s3:ListBucket",
                "Resource": values[0],
                "Condition": {
                    "StringLike": {
                        "s3:prefix": ["app/*", "app/"]
                    }
                },
            },
            {
                "Effect": "Allow",
                "Action": "s3:GetObject",
                "Resource": values[0] + "/app/*",
            },
        ],
    })),
)

profile = aws.iam.InstanceProfile(
    "app-instance-profile",
    role=role.name,
)

# Restrict HTTP testing to the administrator's IP.
admin_cidr = config.require("adminCidr")

web_sg = aws.ec2.SecurityGroup(
    "app-web-sg",
    description="HTTP access for the EC2 IAM lab",
    vpc_id=vpc.id,
    ingress=[{
        "description": "HTTP from administrator",
        "protocol": "tcp",
        "from_port": 80,
        "to_port": 80,
        "cidr_blocks": [admin_cidr],
    }],
    egress=[{
        "protocol": "-1",
        "from_port": 0,
        "to_port": 0,
        "cidr_blocks": ["0.0.0.0/0"],
    }],
)

ami = (
    "resolve:ssm:/aws/service/ami-amazon-linux-latest/"
    "al2023-ami-kernel-default-x86_64"
)

user_data = f"""#!/bin/bash
set -euxo pipefail

dnf install -y python3 python3-boto3

cat > /opt/s3_app.py <<'PYTHON'
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import boto3

BUCKET = {json.dumps(bucket.bucket)}
KEY = "app/config.json"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        try:
            s3 = boto3.client("s3")
            response = s3.get_object(Bucket=BUCKET, Key=KEY)
            data = json.loads(response["Body"].read())
            body = json.dumps(data, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            # Avoid returning credential or SDK details to clients.
            self.send_error(500, "Unable to read application configuration")

HTTPServer(("0.0.0.0", 80), Handler).serve_forever()
PYTHON

cat > /etc/systemd/system/s3-app.service <<'UNIT'
[Unit]
Description=EC2 S3 IAM Role Demo
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/s3_app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now s3-app.service
"""

server = aws.ec2.Instance(
    "iam-demo-instance",
    ami=ami,
    instance_type="t3.micro",
    subnet_id=subnet.id,
    associate_public_ip_address=True,
    vpc_security_group_ids=[web_sg.id],
    iam_instance_profile=profile.name,
    user_data=user_data,
    user_data_replace_on_change=True,
    metadata_options={
        "http_endpoint": "enabled",
        "http_tokens": "required",
        "http_put_response_hop_limit": 1,
    },
    root_block_device={
        "encrypted": True,
        "volume_size": 8,
        "volume_type": "gp3",
        "delete_on_termination": True,
    },
    tags={"Name": "iam-demo-instance"},
)

pulumi.export("bucket_name", bucket.bucket)
pulumi.export("instance_id", server.id)
pulumi.export("public_ip", server.public_ip)
pulumi.export(
    "application_url",
    pulumi.Output.concat("http://", server.public_ip),
)
pulumi.export("role_arn", role.arn)
```

The example uses Pulumi's AWS provider resources for IAM roles, instance profiles, S3, and EC2.

Configure the allowed HTTP source:

```bash
pulumi config set adminCidr YOUR_PUBLIC_IP/32
```

Replace the placeholder with your public IPv4 address. This lab doesn't need SSH access.

Before deploying, note two practical considerations:

* The selected subnet must have outbound connectivity to download packages and reach S3. A public IP alone doesn't guarantee internet connectivity.

* If the instance fails to bootstrap, inspect EC2 system logs and cloud-init output. The application should not be treated as ready merely because the instance is running.

### 6.4 Preview and deploy

```bash
pulumi preview
pulumi up
```

Review the plan. It should create the bucket, bucket controls, configuration object, IAM role, role policy, instance profile, security group, and instance.

Once deployment completes, retrieve the outputs:

```bash
pulumi stack output bucket_name
pulumi stack output role_arn
pulumi stack output application_url
```

Open the application URL in your browser. If the application has started successfully, it should return JSON similar to:

```json
{
  "message": "Read from S3 using an EC2 IAM role",
  "environment": "learning"
}
```

The important part is that the Python application calls `boto3.client("s3")` without passing any access key or secret. Boto3 uses its credential provider chain to discover the EC2 role credentials.

### 6.5 Important code adjustment: resolve the bucket name safely

Pulumi resource properties such as `bucket.bucket` are asynchronous outputs. They must be resolved through Pulumi's output mechanism before being embedded in EC2 user data.

In the code above, replace the `user_data = f"""...` assignment with an output-dependent construction. Keep the script body the same, but use this pattern:

```python
user_data = pulumi.Output.all(bucket.bucket).apply(
    lambda values: (
        """#!/bin/bash
set -euxo pipefail

dnf install -y python3 python3-boto3

cat > /opt/s3_app.py <<'PYTHON'
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import boto3

BUCKET = __BUCKET__
KEY = "app/config.json"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path != "/":
            self.send_error(404)
            return

        try:
            response = boto3.client("s3").get_object(
                Bucket=BUCKET, Key=KEY
            )
            data = json.loads(response["Body"].read())
            body = json.dumps(data, indent=2).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)
        except Exception:
            self.send_error(
                500, "Unable to read application configuration"
            )

HTTPServer(("0.0.0.0", 80), Handler).serve_forever()
PYTHON

cat > /etc/systemd/system/s3-app.service <<'UNIT'
[Unit]
Description=EC2 S3 IAM Role Demo
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/s3_app.py
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now s3-app.service
"""
    ).replace("__BUCKET__", json.dumps(values[0]))
)
```

This ensures the final user-data script contains the actual bucket name and avoids trying to JSON-encode an unresolved Pulumi output.

For an even narrower policy, the application needs only `s3:GetObject` because it reads a known object key. You can remove the `s3:ListBucket` statement from the role policy entirely. The application doesn't need permission to enumerate objects.

### 7\. Verify that the role works

### 7.1 Confirm the application can read S3

```bash
curl "$(pulumi stack output application_url)"
```

Expected result: the JSON configuration object.

If the request returns an HTTP 500 error, inspect the instance's system logs and the service status. From an authorized administrative session, run:

```bash
sudo systemctl status s3-app.service
sudo journalctl -u s3-app.service --no-pager
sudo tail -n 100 /var/log/cloud-init-output.log
```

The application deliberately returns a generic error rather than exposing detailed AWS SDK errors to an HTTP client.

### 7.2 Verify the role identity

If you administer the instance through an authorized shell, run:

```bash
aws sts get-caller-identity
```

This command requires the AWS CLI to be installed. The returned ARN should identify an assumed role, not an IAM user's long-lived access key.

If you prefer using Python, you can temporarily run this diagnostic script:

```python
import boto3

identity = boto3.client("sts").get_caller_identity()

print("Account:", identity["Account"])
print("ARN:", identity["Arn"])
```

Don't print credential values or expose diagnostic endpoints that return sensitive metadata.

### 7.3 Test least privilege

The application should be able to read:

`s3://YOUR_BUCKET/app/config.json`

It should not automatically have permission to read objects outside the `app/` prefix or access unrelated buckets.

You can verify the effective permission boundary by testing a different object key with a temporary diagnostic script or by reviewing the role policy in IAM. A denied request is an expected result when the role lacks the necessary permission.

Remember that a successful test for one object doesn't prove the role has no other permissions. Review attached managed policies, inline policies, permissions boundaries, and any applicable resource policies.

### 8\. IMDSv2 and SSRF hardening

The lab explicitly requires IMDSv2 and sets the metadata response hop limit to `1`.

These settings help reduce exposure, but they don't eliminate the risk of a compromised application accessing the credentials available to the instance.

Use these additional safeguards:

* Validate URLs and destinations accepted by server-side application features.

* Avoid exposing arbitrary HTTP proxying or URL-fetching functionality.

* Restrict access to metadata from containers and other workloads where applicable.

* Keep application dependencies patched.

* Never log environment dumps, metadata credential responses, or secret key material.

* Give each workload only the permissions it needs.

One important limitation: EC2 instance roles are generally shared by applications running on the same instance. If two applications on one instance have different trust requirements, both may be able to use the same instance role. Separate instances or other workload isolation mechanisms may be necessary.

### 9\. Troubleshooting `AccessDenied`

When AWS returns `AccessDenied`, investigate the request systematically rather than immediately granting broader permissions.

| Check                                       | What to verify                                                                   |
| ------------------------------------------- | -------------------------------------------------------------------------------- |
| Identity                                    | Is the application actually using the intended assumed role?                     |
| Trust policy                                | Does the role trust the EC2 service?                                             |
| Instance profile                            | Is the intended profile attached to the instance?                                |
| Identity policy                             | Does the role allow the exact action on the requested resource?                  |
| Resource policy                             | Does the bucket policy allow the request, and does it contain any explicit deny? |
| Permissions boundary or organization policy | Is another policy limiting the role?                                             |
| KMS                                         | If using SSE-KMS, are the relevant key permissions and key policy configured?    |
| Network                                     | Can the instance reach S3 through its public route, NAT, or VPC endpoint?        |
| Startup                                     | Did the instance bootstrap successfully, and is the SDK installed?               |

A useful distinction:

* `AccessDenied` generally points toward an authorization or policy issue.

* Connection timeouts and DNS failures generally point toward connectivity.

* Missing credentials may indicate that the role isn't attached, the metadata service is inaccessible, or the SDK is using an unexpected credential provider.

For detailed authorization analysis, use IAM policy simulation where applicable, CloudTrail event history, and the AWS SDK's diagnostic information. Don't solve a permission problem by defaulting to `AdministratorAccess`.

### 10\. Credential rotation and operational practice

EC2 role credentials are temporary. AWS manages their delivery and rotation through the instance metadata service, while supported SDKs refresh them automatically.

You should not implement your own static-key rotation system for an EC2 application that can use a role.

Instead:

* Attach the appropriate role to the instance.

* Use a supported AWS SDK and its default credential provider chain.

* Avoid caching credentials manually beyond the SDK's intended behavior.

* Monitor role usage and investigate unexpected API calls.

* Review permissions periodically and remove unnecessary actions.

* If credentials are suspected to be compromised, investigate the affected instance and role, restrict access, and follow your incident response procedure.

For applications that run outside EC2, such as local development or GitHub Actions, use an appropriate identity mechanism for that environment rather than copying the EC2 role's credentials elsewhere.

### 11\. Cleanup

After you've verified the S3 read, destroy the lab:

```bash
pulumi preview --diff
pulumi destroy
```

Review the planned deletions and confirm them. The bucket and uploaded object are managed by Pulumi, so the stack should remove them along with the instance, profile, role, policy, and security group.

If you decide to retain the bucket or its contents, change the resource lifecycle deliberately before destroying the stack. Don't assume a bucket with data can always be deleted automatically.

Also verify that the EC2 instance and IAM resources have been removed in the AWS Console. Review the stack state before deleting any resources manually.

### 12\. Knowledge check

Test your understanding of EC2 workload identities.

1. What is the purpose of an EC2 instance profile?

To define which S3 objects exist

To associate an IAM role with an EC2 instance

To encrypt the root volume

To configure the VPC route table

2. What does the IAM trust policy control?

Which principals can assume a role

Which files are stored in S3

Which instance type is allowed

How long an EBS volume persists

3. Why use an EC2 role instead of storing access keys on the instance?

It removes the need for all IAM policies

It gives every AWS service unrestricted access

It provides temporary credentials without distributing long-lived keys

It disables the metadata service

4. What does requiring IMDSv2 help mitigate?

Every possible SSRF vulnerability

Some techniques used to access metadata through SSRF

All application-layer authorization failures

Every network routing problem

5. Which permission is required to read a known object from S3?

s3:DeleteBucket

s3:GetObject on the relevant object ARN

AdministratorAccess

ec2:DescribeInstances

Check answers

### 13\. Module completion checklist

Your progress

### 0 / 7

Explain IAM roles, trust policies, and instance profiles.

Deploy an EC2 instance with an attached IAM role using Pulumi.

Read an S3 object without embedding AWS access keys.

Verify the application's AWS identity.

Require IMDSv2 and explain its SSRF protections and limitations.

Diagnose a simulated AccessDenied error.

Review least-privilege permissions and clean up the lab.

### Further reading

* AWS IAM roles for EC2 — .

* .

* .

* .

* .

* .

Next: Module 4 — Elastic Load Balancing. You'll learn how to distribute application traffic across EC2 instances, configure health checks, use an Application Load Balancer, and prepare your application for high availability.
