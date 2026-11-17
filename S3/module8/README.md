### Module 8 — Capstone: Production-Ready S3 Platform

AWS S3 Course · Final Module · Pulumi with Python

### 1\. Module overview

Goal: Combine the concepts from the previous modules into a practical, secure, observable, and recoverable S3 storage platform.

You will build an infrastructure-as-code project that provisions private S3 buckets, enforces access controls, integrates with an application, monitors object-level activity, and supports recovery from accidental deletion or overwriting.

The project will use Pulumi and Python, AWS IAM, Boto3, CloudTrail, and CloudWatch. It will favor a small, understandable architecture while incorporating production-oriented security and operational practices.

By the end, you will have a version-controlled project that you can deploy, inspect, troubleshoot, and extend.

### 2\. Target architecture

Application / Client

Python application using Boto3

Secure access layer

IAM role · Presigned URLs · HTTPS

Application data bucket

Private · SSE-S3 encryption · Versioning · Lifecycle

Audit trail

CloudTrail data events

Monitoring

CloudWatch metrics and alarms

Audit log bucket

Separate storage and retention

Recovery

Versioning and optional replication

Conceptual architecture. CloudTrail delivery, application data, and optional replication use separate configurations and permissions.

### Design decisions

* Application data: Private S3 bucket with versioning and default encryption.

* Audit logs: Dedicated bucket with restrictive access and appropriate retention controls.

* Access: Use temporary AWS credentials for the application; presigned URLs are used for controlled client uploads and downloads.

* Monitoring: CloudTrail records selected object-level events, while CloudWatch tracks relevant metrics and alarms.

* Recovery: Versioning is the baseline for recovering previous object versions. Cross-Region Replication (CRR) is an optional extension.

* Infrastructure: Pulumi manages the resources, configuration, dependencies, and outputs.

For this capstone, SSE-S3 is the default encryption choice to keep the initial implementation straightforward. SSE-KMS can be added when customer-managed keys, key policies, or compliance requirements justify the additional complexity.

### 3\. Project structure

Create a project named `s3-production-platform` with the following layout:

```text
s3-production-platform/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
├── __main__.py
├── app/
│   ├── storage.py
│   └── requirements.txt
├── docs/
│   ├── architecture.md
│   ├── security-review.md
│   └── runbook.md
└── .gitignore
```

The infrastructure project and application have separate dependencies. This avoids installing Pulumi into the application's runtime environment unnecessarily.

### `Pulumi.yaml`

```yaml
name: s3-production-platform
runtime:
  name: python
description: Production-oriented S3 storage platform
```

### `requirements.txt`

```text
pulumi>=3.0.0,<4.0.0
pulumi-aws>=7.0.0,<8.0.0
```

For a reproducible deployment, resolve and pin the tested versions in your actual project after installation.

### `.gitignore`

```gitignore
.venv/
__pycache__/
*.py[cod]
.env
.terraform/
Pulumi.*.yaml
!Pulumi.dev.yaml
```

The last two patterns above would exclude stack configuration files except `Pulumi.dev.yaml`. Keep that exception only if your development stack configuration contains no secrets. Never commit credentials or plaintext secrets.

### 4\. Provision the infrastructure with Pulumi

The first implementation creates the core storage resources, enforces private access, enables versioning, and defines lifecycle policies. CloudTrail and CloudWatch are added in later sections.

### `__main__.py`

```python

import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

# Use a unique project identifier to avoid bucket-name collisions.
project_name = pulumi.get_project()
stack_name = pulumi.get_stack()

region = aws.get_region_output().name
suffix = config.require("resourceSuffix")

common_tags = {
    "Project": project_name,
    "Environment": stack_name,
    "ManagedBy": "Pulumi",
}

# --------------------------------------------------
# 1. Application data bucket
# --------------------------------------------------

data_bucket = aws.s3.BucketV2(
    "application-data",
    bucket=f"{project_name}-{stack_name}-data-{suffix}",
    tags=common_tags,
)

data_ownership = aws.s3.BucketOwnershipControls(
    "application-data-ownership",
    bucket=data_bucket.id,
    rule=aws.s3.BucketOwnershipControlsRuleArgs(
        object_ownership="BucketOwnerEnforced",
    ),
)

data_public_access = aws.s3.BucketPublicAccessBlock(
    "application-data-public-access",
    bucket=data_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

data_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "application-data-encryption",
    bucket=data_bucket.id,
    rules=[
        aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
            apply_server_side_encryption_by_default=(
                aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                    sse_algorithm="AES256",
                )
            ),
        )
    ],
)

data_versioning = aws.s3.BucketVersioningV2(
    "application-data-versioning",
    bucket=data_bucket.id,
    versioning_configuration=(
        aws.s3.BucketVersioningV2VersioningConfigurationArgs(
            status="Enabled",
        )
    ),
)

data_lifecycle = aws.s3.BucketLifecycleConfigurationV2(
    "application-data-lifecycle",
    bucket=data_bucket.id,
    rules=[
        aws.s3.BucketLifecycleConfigurationV2RuleArgs(
            id="expire-temporary-uploads",
            status="Enabled",
            filter=aws.s3.BucketLifecycleConfigurationV2RuleFilterArgs(
                prefix="temporary/",
            ),
            expiration=(
                aws.s3.BucketLifecycleConfigurationV2RuleExpirationArgs(
                    days=30,
                )
            ),
            noncurrent_version_expiration=(
                aws.s3.BucketLifecycleConfigurationV2RuleNoncurrentVersionExpirationArgs(
                    noncurrent_days=90,
                )
            ),
        )
    ],
)

# --------------------------------------------------
# 2. Dedicated CloudTrail log bucket
# --------------------------------------------------

audit_bucket = aws.s3.BucketV2(
    "audit-logs",
    bucket=f"{project_name}-{stack_name}-audit-{suffix}",
    tags=common_tags,
)

audit_public_access = aws.s3.BucketPublicAccessBlock(
    "audit-logs-public-access",
    bucket=audit_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

audit_ownership = aws.s3.BucketOwnershipControls(
    "audit-logs-ownership",
    bucket=audit_bucket.id,
    rule=aws.s3.BucketOwnershipControlsRuleArgs(
        object_ownership="BucketOwnerEnforced",
    ),
)

audit_encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "audit-logs-encryption",
    bucket=audit_bucket.id,
    rules=[
        aws.s3.BucketServerSideEncryptionConfigurationV2RuleArgs(
            apply_server_side_encryption_by_default=(
                aws.s3.BucketServerSideEncryptionConfigurationV2RuleApplyServerSideEncryptionByDefaultArgs(
                    sse_algorithm="AES256",
                )
            ),
        )
    ],
)

audit_versioning = aws.s3.BucketVersioningV2(
    "audit-logs-versioning",
    bucket=audit_bucket.id,
    versioning_configuration=(
        aws.s3.BucketVersioningV2VersioningConfigurationArgs(
            status="Enabled",
        )
    ),
)

# CloudTrail requires a bucket policy allowing its service
# principal to validate the destination and deliver logs.
trail = aws.cloudtrail.Trail(
    "s3-audit-trail",
    name=f"{project_name}-{stack_name}-audit",
    s3_bucket_name=audit_bucket.id,
    include_global_service_events=True,
    is_multi_region_trail=True,
    enable_log_file_validation=True,
    event_selectors=[
        aws.cloudtrail.TrailEventSelectorArgs(
            read_write_type="All",
            include_management_events=True,
            data_resources=[
                aws.cloudtrail.TrailEventSelectorDataResourceArgs(
                    type="AWS::S3::Object",
                    values=[data_bucket.arn.apply(
                        lambda arn: f"{arn}/"
                    )],
                )
            ],
        )
    ],
    tags=common_tags,
    opts=pulumi.ResourceOptions(depends_on=[
        audit_public_access,
        audit_ownership,
        audit_encryption,
        audit_versioning,
    ]),
)

# CloudTrail delivery policy. Restrict delivery to this trail
# and account, and allow the required ACL-check operation.
audit_policy = aws.s3.BucketPolicy(
    "audit-logs-policy",
    bucket=audit_bucket.id,
    policy=pulumi.Output.all(
        audit_bucket.arn,
        trail.arn,
    ).apply(lambda values: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSCloudTrailAclCheck",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudtrail.amazonaws.com",
                },
                "Action": "s3:GetBucketAcl",
                "Resource": values[0],
                "Condition": {
                    "StringEquals": {
                        "aws:SourceArn": values[1],
                    }
                },
            },
            {
                "Sid": "AWSCloudTrailWrite",
                "Effect": "Allow",
                "Principal": {
                    "Service": "cloudtrail.amazonaws.com",
                },
                "Action": "s3:PutObject",
                "Resource": f"{values[0]}/AWSLogs/{aws.get_caller_identity_output().account_id}/ *".replace("/ *", "/*"),
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control",
                        "aws:SourceArn": values[1],
                    }
                },
            },
        ],
    })),
)

# --------------------------------------------------
# 3. Outputs
# --------------------------------------------------

pulumi.export("region", region)
pulumi.export("data_bucket_name", data_bucket.id)
pulumi.export("data_bucket_arn", data_bucket.arn)
pulumi.export("audit_bucket_name", audit_bucket.id)
pulumi.export("cloudtrail_arn", trail.arn)
```

Important implementation notes

* This is a teaching baseline; verify the exact Pulumi AWS provider schema against the version you pin before deploying. The CloudTrail destination policy and dependency ordering deserve particular attention.

* The CloudTrail log bucket policy must be applied before successful delivery can occur. In a production implementation, establish the destination policy and trail in an explicit dependency-safe order, using a separately constructed policy and the trail ARN as appropriate.

* The `suffix` configuration must make both bucket names globally unique. Use lowercase letters, numbers, and hyphens.

* S3 lifecycle expiration is asynchronous. The 30-day temporary-object rule is a retention policy, not a promise that every object disappears at the exact 30-day mark.

* CloudTrail object-level data events incur additional charges. Scope the selector to the bucket and event types you actually need.

For the cleanest production implementation, use a two-stage deployment for the audit trail: create the audit bucket and its initial service delivery policy first, then create the trail and tighten the policy to its specific trail ARN. This avoids a circular dependency between the policy and the trail.

### 5\. Configure and deploy

### Install the tools

Use a Python virtual environment for the infrastructure project:

```bash
python -m venv .venv
```

Activate it, then install the dependencies:

```bash
python -m pip install -r requirements.txt
pulumi login
aws sts get-caller-identity
```

Configure AWS credentials using an AWS CLI profile, IAM Identity Center, or another supported credential provider. Do not place AWS secret keys in `__main__.py`.

Initialize the stack and configure the unique suffix:

```bash
pulumi stack init dev
pulumi config set aws:region us-east-1
pulumi config set resourceSuffix YOUR-UNIQUE-SUFFIX
```

Replace the example Region and suffix with values appropriate for your environment.

### Preview and deploy

```bash
pulumi preview
pulumi up
```

Read the preview carefully before approving the deployment. Confirm that the planned bucket names, encryption settings, public access blocks, versioning, lifecycle policies, and CloudTrail configuration match the intended design.

After deployment, inspect the outputs:

```bash
pulumi stack output
```

The deployed resource configuration is the source of truth; a successful `pulumi up` alone does not prove that every security or operational requirement has been satisfied.

### 6\. Build the application storage layer

The application should not need unrestricted bucket access. It should use a narrowly scoped IAM role or temporary credentials and generate presigned URLs for clients when direct transfers are appropriate.

### `app/requirements.txt`

```text
boto3>=1.35.0
```

Pin a tested version for production deployments.

### `app/storage.py`

```python

import os
from datetime import timedelta

import boto3
from botocore.exceptions import ClientError

BUCKET_NAME = os.environ["S3_BUCKET_NAME"]

# Use the standard AWS credential provider chain.
# Do not hardcode credentials here.
s3 = boto3.client("s3")

def create_upload_url(
    object_key: str,
    content_type: str,
) -> str:
    """Create a short-lived URL for uploading one object."""

    if not object_key or object_key.startswith("/"):
        raise ValueError("Invalid object key")

    if not object_key.startswith("uploads/"):
        raise ValueError("Uploads must use the uploads/ prefix")

    if content_type not in {
        "image/jpeg",
        "image/png",
        "application/pdf",
    }:
        raise ValueError("Unsupported content type")

    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=int(timedelta(minutes=5).total_seconds()),
        HttpMethod="PUT",
    )

def create_download_url(object_key: str) -> str:
    """Create a short-lived URL for downloading an object."""

    if not object_key or object_key.startswith("/"):
        raise ValueError("Invalid object key")

    if not object_key.startswith("uploads/"):
        raise ValueError("Downloads must use the uploads/ prefix")

    return s3.generate_presigned_url(
        ClientMethod="get_object",
        Params={
            "Bucket": BUCKET_NAME,
            "Key": object_key,
        },
        ExpiresIn=300,
        HttpMethod="GET",
    )

def get_object_metadata(object_key: str) -> dict:
    """Retrieve metadata without downloading the object."""

    try:
        result = s3.head_object(
            Bucket=BUCKET_NAME,
            Key=object_key,
        )
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"404", "NoSuchKey", "NotFound"}:
            raise FileNotFoundError(object_key) from exc
        raise

    return {
        "content_length": result["ContentLength"],
        "content_type": result.get("ContentType"),
        "last_modified": result["LastModified"].isoformat(),
        "version_id": result.get("VersionId"),
    }
```

### How the upload workflow works

* The client authenticates with your application.

* The application authorizes the requested upload and generates a short-lived presigned URL.

* The client uploads directly to S3 using HTTPS.

* The application verifies the uploaded object and records its metadata as needed.

* S3 events or application logic can trigger downstream processing.

The example provides the core signing functions, not a complete production API. In a real service, authenticate callers, generate server-controlled object keys, enforce quotas and upload-size limits, and validate actual file contents. A `Content-Type` header alone does not validate a file. Also remember that a presigned URL is a bearer credential: anyone who obtains it may use it within its permissions and validity period.

### 7\. Add monitoring and operational visibility

Use separate controls for audit records and operational metrics.

| Service                | What it provides                    | Capstone use                                           |
| ---------------------- | ----------------------------------- | ------------------------------------------------------ |
| CloudTrail data events | Object-level API activity           | Investigate uploads, downloads, and deletions          |
| CloudWatch             | Metrics and alarms                  | Track supported request metrics and failures           |
| S3 Inventory           | Scheduled object reports            | Inspect objects, versions, and storage characteristics |
| S3 Storage Lens        | Storage usage and activity insights | Identify trends and cost optimization opportunities    |

### CloudWatch alarm example

For a bucket where request metrics are enabled, an alarm can monitor failed requests. S3 request metrics must first be configured for the relevant bucket or filter.

```python
request_metrics = aws.s3.BucketMetric(
    "application-request-metrics",
    bucket=data_bucket.id,
    name="EntireBucket",
)

errors_alarm = aws.cloudwatch.MetricAlarm(
    "s3-4xx-errors",
    alarm_description="Investigate client and authorization errors",
    namespace="AWS/S3",
    metric_name="4xxErrors",
    statistic="Sum",
    period=300,
    evaluation_periods=2,
    threshold=10,
    comparison_operator="GreaterThanOrEqualToThreshold",
    dimensions={
        "BucketName": data_bucket.id,
        "FilterId": request_metrics.name,
    },
    treat_missing_data="notBreaching",
)
```

This is a starting point, not a universal threshold. Adjust it to your request volume and expected error rate. An alarm without an SNS notification, incident integration, or other response mechanism may detect a problem without notifying anyone.

CloudTrail data events and CloudWatch request metrics are not interchangeable: CloudTrail provides detailed API audit records, while metrics aggregate activity.

### 8\. Recovery and resilience

Versioning protects against many accidental overwrites and deletions, but it is not a complete backup strategy.

### Recovery procedure

* Upload an object, such as `uploads/report.pdf`.

* Upload a changed version under the same key.

* Retrieve the object's version history using the AWS CLI.

* Identify the version that must be restored.

* Copy that version to the current object key, or download and restore it through a controlled recovery workflow.

* Verify the restored content and metadata.

* Record the incident and the recovery steps.

Useful commands:

```bash
aws s3api list-object-versions \
  --bucket YOUR-DATA-BUCKET \
  --prefix uploads/report.pdf
```

Inspect a particular version:

```bash
aws s3api get-object \
  --bucket YOUR-DATA-BUCKET \
  --key uploads/report.pdf \
  --version-id YOUR-VERSION-ID \
  restored-report.pdf
```

If an object was deleted, a delete marker may hide older versions from ordinary listing operations. Recovery requires identifying the previous version and removing or bypassing the delete marker appropriately, subject to permissions and retention settings.

### Optional resilience extension: Cross-Region Replication

For workloads requiring regional resilience, extend the project with:

* A destination bucket in a different AWS Region.

* Versioning enabled on both source and destination buckets.

* A replication IAM role with the necessary source and destination permissions.

* A replication configuration and monitoring.

* A documented recovery procedure that accounts for replication delay and failure.

Replication is not a substitute for every backup strategy: accidental deletions and unwanted changes can propagate to the destination. If you need stronger recovery guarantees, evaluate independent backups, retention controls, and deletion-resistant copies.

### 9\. Security review

Before considering the platform production-ready, review these controls.

| Area             | Expected result                                            |
| ---------------- | ---------------------------------------------------------- |
| Public access    | Block Public Access enabled on all buckets                 |
| Object ownership | Bucket Owner Enforced; ACLs disabled                       |
| Encryption       | Default encryption configured and verified                 |
| Transport        | HTTPS required for data access                             |
| Application IAM  | Only required actions and object prefixes allowed          |
| Presigned URLs   | Short expiration and authorized issuance                   |
| Versioning       | Enabled and recovery tested                                |
| Lifecycle        | Retention rules documented and validated                   |
| Audit logs       | CloudTrail delivery verified; log access restricted        |
| Monitoring       | Alarms have a defined response mechanism                   |
| Infrastructure   | No unexpected changes in Pulumi preview                    |
| Secrets          | No credentials or sensitive configuration committed to Git |

### Important correction to the infrastructure starter code

The initial `__main__.py` illustrates the resource types and intended configuration, but its CloudTrail section should not be deployed unchanged. The trail and bucket policy have a dependency-ordering problem, and the generated policy resource path should be simplified.

For the final implementation, use this sequence:

* Create the audit bucket and its public-access, ownership, and encryption settings.

* Construct the CloudTrail destination policy using the exact expected trail ARN, derived from the account, Region, and trail name.

* Apply the policy before creating the trail, or use a staged deployment to avoid a circular dependency.

* Create the trail with the correct account-specific `AWSLogs/ACCOUNT_ID/` resource path.

* Verify delivery and inspect the resulting log files.

Also add an explicit bucket policy requiring `aws:SecureTransport` for the application data bucket. Test the resulting policy against the complete access design before deployment; a blanket deny can affect legitimate integrations if exceptions are needed.

### 10\. Deployment and verification checklist

Use this as the implementation checklist for the capstone—not as a quiz or exam.

### Implementation progress

### 0/17

Infrastructure

Pulumi project and stack configuration are version-controlled.

All bucket names are unique and the expected Region is configured.

pulumi preview contains no unexplained replacements or deletions.

Security

Public access is blocked and object ownership is enforced.

Encryption and HTTPS requirements are verified.

Application permissions are restricted to required object operations.

No credentials or secrets are committed to source control.

Application

Presigned upload and download workflows work.

Invalid keys and unsupported content types are rejected.

Expired URLs and unauthorized operations are tested.

Operations and recovery

CloudTrail records the intended object-level events.

Audit log delivery is verified and permissions are restricted.

Monitoring thresholds and notification paths are configured.

An overwritten object and a deleted object can be recovered.

Documentation

Architecture and security decisions are documented.

Cost assumptions and failure scenarios are documented.

Cleanup and recovery procedures are documented.

Reset checklist

### 11\. Documentation deliverables

Create the following files in the project.

* `docs/architecture.md` — architecture diagram, components, data flow, and trust boundaries.

* `docs/security-review.md` — IAM permissions, encryption, access restrictions, and security decisions.

* `docs/runbook.md` — deployment, monitoring, troubleshooting, recovery, and cleanup instructions.

Include the following operational information in the runbook:

* How to deploy and update with Pulumi.

* How to identify `AccessDenied` and KMS permission failures.

* How to locate CloudTrail events and CloudWatch alarms.

* How to recover a previous object version.

* How to respond to failed replication, if enabled.

* How to estimate storage, request, monitoring, and data-transfer costs.

### 12\. Cleanup and final deployment review

Use a dedicated development stack for the capstone. Before destroying anything, inspect the planned changes:

```bash
pulumi preview --diff
```

After you have verified that the environment is disposable, run:

```bash
pulumi destroy
```

Review the preview and confirmation prompts carefully. Object versions, retained objects, Object Lock, and other retention controls may prevent complete cleanup. Audit logs may also need to be preserved according to your organization's retention policy.

Do not disable retention controls or delete audit records merely to make cleanup succeed. If the stack contains resources that must be retained, plan their lifecycle explicitly.

### Final result

When you complete this module, you will have a practical S3 platform that demonstrates:

* Reproducible infrastructure using Pulumi and Python.

* Secure object storage and controlled application access.

* Versioning and lifecycle management.

* Application integration using Boto3 and presigned URLs.

* Object-level auditing and operational monitoring.

* A tested recovery process and documented operational procedures.

The central objective is not simply to deploy a few buckets. It is to demonstrate how to design, operate, secure, and recover an S3-based system in a way that can be maintained and extended beyond the learning environment.
