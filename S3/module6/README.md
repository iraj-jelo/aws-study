### Module 6 — Advanced S3 Features and Architecture

AWS S3 Course · Intermediate to Advanced · Pulumi with Python

### Learning objectives

By the end of this module, you will understand how to design advanced Amazon S3 architectures for resilience, data protection, content delivery, and event-driven processing. You will also learn how to implement these architectures using Pulumi rather than Terraform.

You will learn to:

* Design cross-region and same-region replication strategies.

* Configure replication permissions, versioning, monitoring, and lifecycle policies.

* Protect critical data using S3 Object Lock.

* Control access to large or shared datasets using S3 access points.

* Deliver private S3 content through Amazon CloudFront.

* Build event-driven workflows around object creation and deletion.

* Choose appropriate alternatives to S3 Select for querying object data.

* Understand how S3 integrates with AWS analytics and data lake services.

### 6.1 — S3 Replication: CRR and SRR

Amazon S3 replication automatically copies eligible objects from a source bucket to a destination bucket.

![Secure Amazon S3 Cross-Region Replication with KMS: A Production-Ready Guide | by Dorothycherotich | Medium](https://images.openai.com/static-rsc-4/y3wf7FP9ko1AcTi3vLT79Ev4QdQDW-ehF2rQiQ804g6EyMdu3d-l2kwJhSAoLw-Lx0A6LtLUgAyQ5S7mNQWj5WeeBAyGApn4BD0XoEZyNbGx47YjNQR2c6sSS3VkHuKOXevKWjyb-74lsyyVCVwzXYttkyBnWqURCWoOCzqq0ofEl4bmTYvrqyU9OwCa57xD?purpose=fullsize)

Cross-Region Replication (CRR)

Replicates objects between buckets in different AWS Regions. Useful for geographic resilience, regional data access, disaster recovery, and data residency architectures.

![S3 Replication Between Buckets at Inez Bennett blog](https://images.openai.com/static-rsc-4/2zWmJiuIDNasH0LiTFg6VQQVVxQDE3R067QcsPhI6rVWYEDYEFibepYcy6VfveRabSAoP1aHEjb_HFjoFgF0StrHtbvm_4gfw2VzJo8Z_ddR-zOdo5wf3cXAM7sFtDPwQ_bkwy-JmQ-g2HNCKqfeXJ34AD_I2qfk8vt7K9vPVFV-q-IQ4qJv1oVzZkPlJzGT?purpose=fullsize)

Same-Region Replication (SRR)

Replicates objects between buckets in the same Region. Useful for separating production and analytics datasets, centralizing data, or maintaining independent copies for organizational workflows.

### How replication works

Replication relies on several components:

* Source bucket: Holds the original objects and replication configuration.

* Destination bucket: Receives replicas and must have compatible permissions and configuration.

* Versioning: Must be enabled on both source and destination buckets.

* IAM replication role: Allows S3 to read source object versions and replicate objects to the destination.

* Replication rules: Define which objects are replicated, optionally based on prefixes or tags.

Replication is asynchronous. An upload can succeed in the source bucket before its replica is available in the destination.

Important behaviors to understand:

* By default, replication rules primarily apply to eligible new objects after replication is configured. Existing objects require S3 Batch Replication or another supported approach.

* Objects encrypted with SSE-KMS require additional configuration and KMS permissions.

* Delete markers and permanent version deletions have different replication behavior. Configure delete-marker replication deliberately.

* Replication does not automatically copy every bucket-level setting, such as lifecycle rules, bucket policies, or notification configurations.

* Replication is not a complete backup strategy by itself: deletions, compromised permissions, and replicated unwanted changes can affect recovery.

### Replication Time Control and monitoring

For workloads that require predictable replication timing, S3 offers Replication Time Control (RTC). AWS states that RTC replicates 99.99% of new objects within 15 minutes, backed by a service-level agreement. It also provides replication metrics and threshold notifications. Amazon Simple Storage Service +1

Monitor:

* Bytes pending replication.

* Operations pending replication.

* Replication latency.

* Failed replication operations.

* Object-level replication status.

Without RTC, replication is still asynchronous, but you should not assume that every object will arrive within a fixed time.

### 6.2 — S3 Object Lock and immutable storage

S3 Object Lock helps prevent objects from being deleted or overwritten for a specified retention period. It is useful for regulatory records, audit evidence, backups, and ransomware-resistant data retention.

There are three main mechanisms:

| Mechanism       | Purpose                                                                                                                                        |
| --------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| Governance mode | Authorized users with specific permissions can bypass retention restrictions.                                                                  |
| Compliance mode | Protected object versions cannot be deleted or have their retention shortened during the retention period, including by the account root user. |
| Legal hold      | Keeps an object version protected until the legal hold is removed, independently of a fixed retention date.                                    |

Object Lock works with versioning and applies to individual object versions. It does not automatically prevent every change to bucket configuration or prevent an attacker from disrupting access.

### Example architecture

Application or backup process

Versioned S3 bucket

Default retention · Object Lock · Restricted deletion

Retention and recovery policy

### Important design considerations

* Enable Object Lock on the bucket as part of its initial configuration where appropriate.

* Choose retention periods carefully: compliance-mode retention is intentionally difficult to reverse.

* Configure lifecycle rules with retention constraints in mind.

* For replication of locked objects, the destination must also have Object Lock enabled, and the replication role needs additional retention and legal-hold permissions. Amazon Simple Storage Service

* Test with disposable data before applying retention to real business records.

### 6.3 — S3 Access Points and Multi-Region Access Points

### S3 Access Points

An access point gives an application, team, or workload a dedicated endpoint and access policy for a bucket. It can simplify access control when many consumers use the same dataset.

For example, a shared bucket might hold several teams' data:

* Analytics team: read access to analytics data.

* Ingestion service: write access to an ingestion prefix.

* Reporting service: read access to published reports.

Access points help separate these access policies without needing every consumer to use the same bucket policy.

### Multi-Region Access Points (MRAPs)

A Multi-Region Access Point provides a global endpoint for accessing datasets stored in multiple S3 buckets across AWS Regions. Depending on the configuration, it can route requests to an appropriate bucket and support failover between Regions.

MRAPs are useful when applications need a common access endpoint without hardcoding regional bucket names.

Keep in mind that a global endpoint is not the same as automatic multi-region data consistency. You still need to design replication, conflict handling, permissions, and failover behavior. Two-way replication can introduce conflicts when different clients modify the same logical object in different Regions.

### 6.4 — Static content delivery with CloudFront and OAC

A common production architecture is to store static assets in a private S3 bucket and deliver them through Amazon CloudFront.

Users

HTTPS requests

Amazon CloudFront

Edge caching · TLS · Cache policies

Private S3 origin

Origin Access Control · Bucket policy

### Why use Origin Access Control (OAC)?

OAC lets CloudFront access an S3 bucket while keeping the bucket private to direct public requests. AWS recommends OAC over the older Origin Access Identity approach because OAC supports additional capabilities, including SSE-KMS-encrypted S3 origins. Amazon CloudFront

Key concepts:

* Origin: The S3 bucket from which CloudFront retrieves content.

* OAC: Controls authenticated requests from CloudFront to S3.

* Bucket policy: Grants the intended CloudFront distribution permission to retrieve objects.

* Cache policy: Controls which requests CloudFront caches and for how long.

* Cache invalidation: Removes selected cached content when necessary.

* TLS: Secures traffic between clients and CloudFront.

A regular S3 REST endpoint is appropriate for an OAC-protected origin. An S3 static website endpoint is different: it behaves as a website endpoint and must be configured as a custom origin, so it does not support OAC in the same way.

For most production static content, prefer a private bucket with CloudFront and OAC over making the S3 bucket public.

### 6.5 — S3 notifications and event-driven processing

S3 can publish events when objects are created, deleted, restored, or otherwise changed through supported operations.

Common destinations include:

* Amazon SQS: Buffer work for asynchronous consumers.

* Amazon SNS: Fan out notifications to multiple subscribers.

* AWS Lambda: Process objects automatically.

* Amazon EventBridge: Route events to supported targets using rules and filters.

Example: an uploaded image triggers a processing function that generates thumbnails and stores them under a separate prefix.

S3: `incoming/`

Object created

EventBridge or S3 notification

Lambda / SQS consumer

Validate and process the object

S3: `processed/`

Store output separately

### Design rules for event-driven S3 applications

* Design consumers to be idempotent: the same event may be delivered more than once.

* Avoid writing processed outputs to the same prefix that triggers the consumer, unless recursion is explicitly controlled.

* Use SQS when you need buffering, controlled concurrency, or a dead-letter queue.

* Expect asynchronous processing and handle failures and retries.

* Choose S3 notifications for straightforward event routing and EventBridge when you need richer filtering and integration with multiple AWS services.

### 6.6 — S3 Select alternatives and query-oriented access

Amazon S3 Select allowed SQL-like filtering of individual objects, but it is no longer available to new customers. Existing customers can continue using it. New architectures should consider other query services. Amazon Simple Storage Service

| Requirement                                       | Suitable option                                             |
| ------------------------------------------------- | ----------------------------------------------------------- |
| Query CSV, JSON, or Parquet files in S3 using SQL | Amazon Athena                                               |
| Run large-scale analytics with managed Spark      | AWS Glue                                                    |
| Build data lake catalogs and ETL pipelines        | AWS Glue Data Catalog and Glue jobs                         |
| Query structured data in a data warehouse         | Amazon Redshift, including supported external-data patterns |
| Process individual objects as they arrive         | Lambda or container-based consumers                         |

### Data lake architecture basics

A data lake typically separates data into logical zones:

* Raw: Original uploaded data, preserved for traceability.

* Processed: Validated, transformed, or standardized data.

* Curated: Data prepared for analytics and business consumption.

S3 provides the storage layer, while services such as Glue and Athena provide cataloging, transformation, and querying.

For analytical workloads, columnar formats such as Parquet can reduce the amount of data scanned. Partitioning by useful dimensions—such as date or region—can also reduce query costs when designed appropriately.

### Lab 6 — Build a resilient, cross-region S3 architecture with Pulumi

For this lab, we will implement Cross-Region Replication (CRR) using Python and Pulumi. This is the main hands-on exercise for the module; CloudFront and Object Lock can be explored as separate extensions.

### Architecture

Region A — Source

S3 bucket with versioning enabled

S3 Replication

IAM role · Replication rule · Optional RTC

Region B — Destination

Separate S3 bucket with versioning enabled

### Step 1 — Create the Pulumi project

Install the AWS provider package in your Python environment:

```bash
mkdir s3-replication
cd s3-replication

pulumi new aws-python
```

Install or update the provider package if required:

```bash
uv add pulumi pulumi-aws
```

Configure your AWS profile and the source Region:

```bash
aws configure --profile s3-lab

pulumi config set aws:region eu-west-2
```

This example uses London (`eu-west-2`) as the source and Ireland (`eu-west-1`) as the destination. Choose Regions permitted for your account and workload.

### Step 2 — Define the buckets and replication role

The following is the core of `__main__.py`. It creates two versioned buckets and an IAM role for S3 replication.

```python
import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

source_region = config.get("sourceRegion") or "eu-west-2"
destination_region = config.get("destinationRegion") or "eu-west-1"

source_provider = aws.Provider(
    "source-provider",
    region=source_region,
)

destination_provider = aws.Provider(
    "destination-provider",
    region=destination_region,
)

source = aws.s3.BucketV2(
    "replication-source",
    opts=pulumi.ResourceOptions(provider=source_provider),
)

destination = aws.s3.BucketV2(
    "replication-destination",
    opts=pulumi.ResourceOptions(provider=destination_provider),
)

source_versioning = aws.s3.BucketVersioningV2(
    "source-versioning",
    bucket=source.id,
    versioning_configuration={
        "status": "Enabled",
    },
    opts=pulumi.ResourceOptions(provider=source_provider),
)

destination_versioning = aws.s3.BucketVersioningV2(
    "destination-versioning",
    bucket=destination.id,
    versioning_configuration={
        "status": "Enabled",
    },
    opts=pulumi.ResourceOptions(provider=destination_provider),
)

replication_role = aws.iam.Role(
    "s3-replication-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "s3.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

replication_policy = aws.iam.RolePolicy(
    "s3-replication-policy",
    role=replication_role.id,
    policy=pulumi.Output.all(
        source.arn,
        destination.arn,
    ).apply(lambda arns: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetReplicationConfiguration",
                    "s3:ListBucket",
                ],
                "Resource": arns[0],
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:GetObjectVersionForReplication",
                    "s3:GetObjectVersionAcl",
                    "s3:GetObjectVersionTagging",
                ],
                "Resource": f"{arns[0]}/*",
            },
            {
                "Effect": "Allow",
                "Action": [
                    "s3:ReplicateObject",
                    "s3:ReplicateDelete",
                    "s3:ReplicateTags",
                ],
                "Resource": f"{arns[1]}/*",
            },
        ],
    })),
)

pulumi.export("source_bucket", source.id)
pulumi.export("destination_bucket", destination.id)
pulumi.export("replication_role_arn", replication_role.arn)
```

The role policy grants S3 permission to read source versions and create replicas at the destination. For a production deployment, review the exact required permissions against your replication features, encryption configuration, and account boundaries.

### Step 3 — Add the replication configuration

Append this after the role policy:

```python
replication = aws.s3.BucketReplicationConfig(
    "source-replication-config",
    bucket=source.id,
    role=replication_role.arn,
    rules=[
        aws.s3.BucketReplicationConfigRuleArgs(
            id="replicate-all-objects",
            status="Enabled",
            filter=aws.s3.BucketReplicationConfigRuleFilterArgs(
                prefix="",
            ),
            delete_marker_replication=(
                aws.s3.BucketReplicationConfigRuleDeleteMarkerReplicationArgs(
                    status="Disabled",
                )
            ),
            destination=(
                aws.s3.BucketReplicationConfigRuleDestinationArgs(
                    bucket=destination.arn,
                    storage_class="STANDARD",
                )
            ),
        ),
    ],
    opts=pulumi.ResourceOptions(
        provider=source_provider,
        depends_on=[
            source_versioning,
            destination_versioning,
            replication_policy,
        ],
    ),
)

pulumi.export("replication_rule_id", replication.id)
```

This creates a basic replication rule. It intentionally leaves delete-marker replication disabled so you can examine deletion behavior without automatically mirroring ordinary delete markers. Adjust this setting if your recovery or synchronization requirements differ.

For the exact resource schema and supported options, see the Pulumi documentation for [S3 BucketReplicationConfig](https://www.pulumi.com/registry/packages/aws/api-docs/s3/bucketreplicationconfig/?utm_source=chatgpt.com).

### Step 4 — Deploy and verify

Preview the changes before deploying:

```bash
pulumi config set sourceRegion eu-west-2
pulumi config set destinationRegion eu-west-1

pulumi preview
pulumi up
```

Upload a test object to the source bucket:

```bash
echo "S3 replication test" > replication-test.txt

aws s3 cp replication-test.txt \
  "s3://$(pulumi stack output source_bucket)/replication-test.txt" \
  --profile s3-lab
```

Check the destination after allowing time for asynchronous replication:

```bash
aws s3api head-object \
  --bucket "$(pulumi stack output destination_bucket)" \
  --key replication-test.txt \
  --profile s3-lab \
  --region eu-west-1
```

You can also inspect the source object's replication status:

```bash
aws s3api head-object \
  --bucket "$(pulumi stack output source_bucket)" \
  --key replication-test.txt \
  --query ReplicationStatus \
  --profile s3-lab \
  --region eu-west-2
```

For an eligible replicated object, the source status should eventually indicate `COMPLETED`. A missing or pending status immediately after upload does not necessarily mean replication is broken.

If replication fails, inspect the source bucket's replication configuration, IAM permissions, destination bucket policy, versioning status, and any KMS permissions.

### Step 5 — Extend the architecture

Once basic replication works, explore these improvements:

* Add lifecycle rules independently to both buckets.

* Enable replication metrics and configure alarms.

* Evaluate S3 Replication Time Control if your recovery requirements justify its additional cost.

* Test object versioning and delete-marker behavior.

* Use S3 Batch Replication to copy eligible objects that existed before the replication rule was created.

* Explore Object Lock in a separate test environment.

* Alternatively, deploy a private S3 bucket behind CloudFront using OAC.

For production replication, review the official [S3 replication documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication.html?utm_source=chatgpt.com) and [replication monitoring guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/replication-metrics.html?utm_source=chatgpt.com).

### Lab deliverable and completion criteria

By the end of this lab, you should have:

* A source and destination bucket in separate Regions.

* Versioning enabled on both buckets.

* An IAM role with the required replication permissions.

* A Pulumi-managed replication rule.

* A successfully replicated test object.

* A short architecture document covering recovery, deletion behavior, monitoring, and regional trade-offs.

Cost and cleanup: Two buckets, replication requests, replicated storage, and cross-region transfer can incur charges. After testing, remove the lab resources when they are no longer needed. Ensure that buckets are empty and that no retention controls prevent deletion before running `pulumi destroy`.
