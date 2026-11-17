### Module 7 — Production Operations, Monitoring, and Troubleshooting

Goal: Operate Amazon S3 reliably, diagnose access problems, monitor storage activity, and control operational costs.

Production S3 operations involve more than keeping buckets available. You need visibility into who accesses objects, why requests fail, how data is protected, whether replication is working, and how storage costs evolve over time.

This module covers the operational tools and troubleshooting techniques used to manage S3 in production, including how to represent relevant infrastructure with Pulumi and Python.

### 1\. CloudTrail and S3 Object-Level Auditing

Amazon S3 integrates with AWS CloudTrail to record activity involving S3 resources.

CloudTrail helps answer questions such as:

* Who accessed or modified an object?

* When was an object deleted?

* Which identity attempted a failed API operation?

* Which role or application made a request?

* What API operation was performed, and what was its outcome?

### Management events vs. data events

| Event type        | Examples                                           | Default behavior                                                                         |
| ----------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Management events | CreateBucket, PutBucketPolicy, PutBucketVersioning | Logged by a trail by default for management event categories unless configured otherwise |
| Data events       | GetObject, PutObject, DeleteObject                 | Not logged by default; must be explicitly configured                                     |
| Insights events   | Unusual API activity patterns                      | Requires CloudTrail Insights configuration and applicable event support                  |

Object-level auditing requires particular attention because S3 data events can generate substantial volumes of logs.

For example, a bucket serving millions of downloads could generate a large number of `GetObject` events. Logging every request may be justified for sensitive data, but unnecessary for some high-volume, low-risk workloads.

Operational recommendation: Enable data events selectively for the buckets, prefixes, or access patterns that need auditing. Account for CloudTrail charges and log retention.

### 2\. CloudWatch Metrics, Alarms, and Request Monitoring

Amazon CloudWatch provides metrics that help you understand S3 storage consumption, request activity, and replication health.

### Storage metrics vs. request metrics

| Metric category      | What it tells you                                     | Typical use                   |
| -------------------- | ----------------------------------------------------- | ----------------------------- |
| Storage metrics      | Bucket size and object count                          | Detect storage growth         |
| Request metrics      | GET, PUT, total requests, errors, and latency         | Diagnose application problems |
| Replication metrics  | Replication failures, pending operations, and latency | Monitor replication health    |
| Storage Lens metrics | Organization-wide usage and activity trends           | Identify inefficiencies       |

S3 storage metrics are generally reported daily. Request metrics can provide one-minute monitoring when enabled, but delivery is best-effort and is not a complete accounting of every request. Amazon Simple Storage Service +1

### Important request metrics

* `AllRequests` — total HTTP requests covered by the metric configuration.

* `GetRequests` — object GET requests.

* `PutRequests` — object PUT requests.

* `4xxErrors` — client-side errors, including authorization failures.

* `5xxErrors` — server-side errors.

* `FirstByteLatency` — time until the first response byte.

* `TotalRequestLatency` — total request processing time measured by S3.

### CloudWatch alarms

Alarms can notify operators when a metric crosses a threshold. Common examples include:

* A sustained increase in 5xx errors.

* Unexpected growth in 4xx errors.

* Replication failures above an acceptable threshold.

* Storage usage exceeding a planned budget threshold.

* Abnormally high request volume.

An important distinction: S3 storage metrics and CloudWatch alarms are not a replacement for AWS billing alerts. Use AWS Budgets and cost monitoring separately for financial controls.

Pulumi integration: Pulumi can manage S3 request-metric configurations, CloudWatch alarms, SNS notification topics, and dashboards. Keep thresholds configurable so that development and production environments can use different values.

### 3\. S3 Server Access Logging and Its Limitations

S3 server access logging records detailed request information about a source bucket and delivers log files to a designated destination bucket.

Typical log information includes:

* Request time and requester information.

* Operation and object key.

* Request status and HTTP response code.

* Bytes sent and request processing time.

* Error details and other request attributes.

### Server access logs vs. CloudTrail

| Feature                  | CloudTrail                                                | S3 server access logging                                                                                       |
| ------------------------ | --------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Primary purpose          | Auditing API activity                                     | Detailed request analysis                                                                                      |
| Object-level operations  | Yes, with data events enabled                             | Yes, for logged requests                                                                                       |
| Delivery                 | Trail or event destinations                               | Destination S3 bucket                                                                                          |
| Delivery characteristics | Generally delivered within minutes, but not instantaneous | Best-effort; delivery can be delayed                                                                           |
| Cost considerations      | Data-event charges may apply                              | No additional charge for enabling server access logging, but destination storage and processing can cost money |

Server access logging is best-effort, and its records are not guaranteed to capture every request. It should not be treated as a complete, real-time security audit trail. Amazon Simple Storage Service +1

Operational recommendations:

* Use a dedicated destination bucket for logs.

* Restrict access to log files and protect them from accidental deletion.

* Apply suitable lifecycle policies to manage retention and storage costs.

* Avoid logging configurations that create circular dependencies or unnecessary complexity.

* Prefer CloudTrail for attributable API audit events and use server access logs when their request-level details serve a specific operational need.

### 4\. S3 Storage Lens, Inventory, and Batch Operations

These three features solve different operational problems: understanding usage, reporting on objects, and applying changes at scale.

### S3 Storage Lens

Amazon S3 Storage Lens provides organization-wide visibility into storage usage and activity.

It helps answer questions such as:

* Which accounts and buckets consume the most storage?

* How much data is stored in each storage class?

* Are large numbers of incomplete multipart uploads accumulating?

* Where might versioning or lifecycle policies be creating avoidable costs?

* Which storage patterns warrant further investigation?

Storage Lens offers free metrics and additional advanced metrics and recommendations at extra cost. Advanced metrics can also be published to CloudWatch for dashboards and alarms. Amazon Simple Storage Service

### S3 Inventory

S3 Inventory produces scheduled reports about objects in a bucket. Reports can include object keys, sizes, storage classes, encryption status, version IDs, and other configured attributes.

Inventory is useful for:

* Auditing encryption coverage.

* Finding objects in unexpected storage classes.

* Reviewing object versions and delete markers.

* Identifying data that may require lifecycle policy changes.

* Analyzing large buckets without repeatedly listing every object through the API.

Inventory is a scheduled report, not a real-time view of bucket contents.

### S3 Batch Operations

S3 Batch Operations applies an operation to a large number of objects using a manifest.

Typical uses include:

* Copying objects in bulk.

* Replacing object tags.

* Invoking a Lambda function on selected objects.

* Restoring archived objects.

* Applying certain object-level operations across large datasets.

Batch Operations can generate completion reports to help identify successful and failed tasks. Permissions, manifest configuration, supported operations, and request costs must be considered before launching a job.

How they fit together: Storage Lens helps identify a problem, Inventory helps identify the affected objects, and Batch Operations can help apply a large-scale change.

### 5\. Diagnosing `AccessDenied`, KMS Failures, and Policy Conflicts

Access failures are among the most common S3 operational problems. A request can fail even when an IAM policy appears to allow it because several authorization layers may apply simultaneously.

### Understand the authorization layers

Request identity

IAM user, role, or federated session

Authorization evaluation

Identity policies · Bucket/access-point policies · SCPs · Permissions boundaries · Session policies · Explicit denies

Additional access conditions

VPC endpoint policies · Resource conditions · KMS permissions for encrypted objects

Request allowed or denied

The exact evaluation depends on the account relationship and request path. Cross-account access generally requires authorization from both the caller's side and the resource-owning side. Explicit denies and applicable organizational restrictions can override otherwise permissive policies.

### Common causes of `AccessDenied`

| Symptom                                      | Potential cause                                                               |
| -------------------------------------------- | ----------------------------------------------------------------------------- |
| ListBucket fails                             | Missing s3:ListBucket permission on the bucket ARN                            |
| GetObject fails                              | Missing s3:GetObject permission on the object ARN                             |
| Upload fails                                 | Missing s3:PutObject, required tagging permissions, or encryption permissions |
| Upload succeeds but download fails           | Missing read permission or KMS decrypt permission                             |
| Access works locally but fails in production | Different IAM role, session policy, network path, or endpoint policy          |
| Access fails after a policy change           | Explicit deny, condition mismatch, or resource ARN mismatch                   |

A crucial detail is the distinction between bucket and object ARNs:

* Bucket-level permissions usually target `arn:aws:s3:::bucket-name`.

* Object-level permissions usually target `arn:aws:s3:::bucket-name/*`.

Granting `s3:GetObject` on the bucket ARN does not grant access to its objects.

### Troubleshooting SSE-KMS failures

When an object uses SSE-KMS, S3 access authorization and KMS authorization are separate concerns.

For example, downloading a KMS-encrypted object may require `s3:GetObject` plus appropriate `kms:Decrypt` authorization. Uploading with a customer-managed KMS key can require `kms:GenerateDataKey`, along with any other permissions required by the specific operation.

Investigate:

* Which IAM identity actually made the request.

* Whether the S3 operation is authorized.

* Whether the bucket and object policies allow the request.

* Whether the KMS key policy and IAM permissions allow the required cryptographic operation.

* Whether organizational policies, endpoint policies, or request conditions introduce a denial.

Useful tools include CloudTrail, IAM policy simulation, IAM Access Analyzer, and the relevant S3 and KMS configuration.

Pulumi consideration: A correctly declared policy in Pulumi does not guarantee that an application's runtime identity has every required permission. Infrastructure deployment identity and application runtime identity should be evaluated separately.

### 6\. Request Throttling, Retries, and Large-Object Transfer Failures

S3 supports high request rates and automatically scales to accommodate workloads. Nevertheless, applications must handle transient errors, concurrency, and transfer failures appropriately.

### Request throttling and retries

A client may encounter errors such as `503 Slow Down` during certain traffic patterns or periods of rapid request growth.

Recommended practices include:

* Use an AWS SDK with appropriate retry behavior.

* Apply exponential backoff with jitter where suitable.

* Avoid uncontrolled retry loops.

* Monitor error rates and request latency.

* Distribute request traffic across object keys when designing high-throughput workloads.

* Use bounded concurrency to avoid overwhelming application resources.

Retries should be limited and should respect the idempotency characteristics of the operation. Repeating a read is usually straightforward; repeating a multipart upload or a business operation may require more careful state management.

### Large-object transfers

For large files, multipart upload allows an object to be uploaded as separate parts and assembled when the upload completes.

Important operational considerations include:

* Selecting a suitable multipart threshold and part size.

* Choosing an appropriate level of concurrency.

* Retrying failed parts rather than unnecessarily restarting entire transfers.

* Aborting abandoned multipart uploads.

* Monitoring incomplete multipart storage.

* Validating checksums and the final object.

* Using lifecycle rules to abort incomplete multipart uploads after a suitable period.

Multipart uploads improve transfer resilience, but incomplete uploads can continue to consume storage until their parts are removed.

For Python applications, Boto3's transfer utilities can manage multipart transfers and concurrency. Their configuration should reflect file sizes, network conditions, memory limits, and workload characteristics.

### 7\. Replication Status and Failed Replication Troubleshooting

S3 replication copies eligible objects from a source bucket to a destination bucket according to configured rules.

Replication may be used for regional resilience, account separation, compliance, or distributing data closer to consumers.

### Common replication problems

* Source bucket versioning is not enabled.

* The replication role lacks required permissions.

* The destination bucket policy does not authorize replication.

* KMS permissions are missing for encrypted objects.

* An object does not match the configured replication rule.

* An existing object was created before replication was configured.

* Object ownership or destination encryption settings create additional requirements.

### Replication monitoring

Review:

* Replication status on source objects.

* Failed replication operation counts.

* Pending operations and replication latency.

* Replication rule filters and destination configuration.

* CloudTrail events and IAM permissions associated with replication.

S3 Replication Time Control is an additional option for workloads that need a predictable replication time objective under its service terms. It should not be confused with a general guarantee that all replication completes immediately.

Operational principle: Replication is not a complete backup strategy by itself. Deletes and other changes can be replicated depending on the rule configuration, and replicated data may share the same logical failure or compromise. Combine replication with versioning, appropriate retention, restricted deletion permissions, and recovery testing.

### 8\. Recovery Testing, Deletion Protection, and Backup Strategy

Reliable S3 operations require a recovery plan for accidental deletion, unwanted overwrites, compromised credentials, and regional failures.

### Versioning and recovery

S3 Versioning preserves multiple versions of an object. When an object is overwritten, S3 can retain the previous version. A normal delete in a versioned bucket typically creates a delete marker rather than permanently deleting all versions.

Recovery requires understanding how to identify previous versions, remove a delete marker where appropriate, and restore the desired object version.

Versioning alone is not a complete backup: sufficiently privileged identities can permanently delete versions, and it does not independently protect against every form of account compromise or destructive action.

### Protection mechanisms

| Mechanism                | Purpose                                                      | Important limitation                                           |
| ------------------------ | ------------------------------------------------------------ | -------------------------------------------------------------- |
| S3 Versioning            | Recover previous object versions                             | Does not prevent permanent deletion of versions                |
| S3 Object Lock           | Protect objects from deletion or alteration during retention | Requires careful retention configuration                       |
| Cross-Region Replication | Maintain copies in another Region                            | Changes or deletions may propagate depending on configuration  |
| Separate-account backups | Reduce shared-account security risks                         | Still requires independent permissions and recovery procedures |
| IAM restrictions         | Limit destructive actions                                    | Highly privileged identities may still change policies         |

Object Lock supports governance and compliance retention modes. Governance mode allows specially authorized users to bypass retention; compliance mode provides stronger protection during the retention period. Legal holds can also protect objects independently of a fixed retention period.

### Recovery planning

A production recovery strategy should define:

* Which data must be recoverable.

* Acceptable recovery point and recovery time objectives (RPO and RTO).

* How object versions or backup copies are restored.

* Who is authorized to perform recovery.

* How recovery integrity is verified.

* How the recovery procedure is tested periodically.

Use Pulumi to manage appropriate versioning, retention, replication, and access-control configurations. Be especially careful when changing or destroying resources that contain retained or legally protected data.

### 9\. Cost Allocation, Request Costs, and Data Transfer

S3 cost management requires visibility into both stored data and the operations performed against it.

### Main cost drivers

* Storage: Amount of data stored in each storage class.

* Requests: GET, PUT, LIST, lifecycle, and other billable operations.

* Retrieval: Charges for retrieving data from certain storage classes.

* Data transfer: Charges that may apply when data moves between Regions or out to other destinations.

* Management and analytics: Features such as Inventory, advanced Storage Lens metrics, and Batch Operations.

* Monitoring and auditing: CloudWatch metrics and alarms, CloudTrail data events, and log storage or processing.

* Incomplete multipart uploads: Stored parts that remain until completed or aborted.

Exact charges depend on Region, storage class, operation type, volume, and current AWS pricing.

### Cost allocation and visibility

Use consistent resource tags to identify application, environment, team, and cost center. Configure AWS cost allocation tags in billing, then use Cost Explorer and AWS Budgets to track spending and investigate changes.

S3 Storage Lens and Inventory provide additional operational context for identifying storage inefficiencies.

### Cost optimization principles

* Choose storage classes based on actual access patterns, retention, and retrieval requirements.

* Configure lifecycle transitions and expiration carefully.

* Remove incomplete multipart uploads when they are no longer needed.

* Review noncurrent object versions and delete markers.

* Avoid collecting high-volume audit events without a clear purpose.

* Monitor replication, retrieval, and data transfer costs.

* Apply retention and deletion rules only after considering recovery and compliance requirements.

### 10\. Pulumi and Python for Operational Infrastructure

Pulumi lets you manage much of the S3 operational configuration alongside the bucket itself. Keeping related settings in code makes changes reviewable and repeatable.

Common resources include:

| Operational capability | Pulumi resource                       |
| ---------------------- | ------------------------------------- |
| S3 bucket              | aws.s3.BucketV2                       |
| Bucket versioning      | aws.s3.BucketVersioningV2             |
| Lifecycle rules        | aws.s3.BucketLifecycleConfigurationV2 |
| Server access logging  | aws.s3.BucketLoggingV2                |
| Request metrics        | aws.s3.BucketMetric                   |
| CloudTrail trail       | aws.cloudtrail.Trail                  |
| CloudWatch alarm       | aws.cloudwatch.MetricAlarm            |
| CloudWatch dashboard   | aws.cloudwatch.Dashboard              |
| SNS notifications      | aws.sns.Topic                         |

Exact resource availability and properties depend on the Pulumi AWS provider version. CloudTrail data-event selectors, Inventory configurations, Storage Lens configurations, and replication metrics may require additional resources and supporting IAM policies.

Keep these operational principles in mind:

* Separate deployment permissions from runtime application permissions.

* Store configuration in Pulumi stack configuration rather than hardcoding environment-specific values.

* Protect sensitive configuration with Pulumi secrets.

* Review `pulumi preview` before applying policy, lifecycle, retention, or deletion-related changes.

* Avoid destructive replacements of production resources.

* Use AWS-native monitoring and billing services together rather than relying on a single dashboard.

### Module 7 summary

By the end of this module, you should understand how to operate S3 using audit events, metrics, logging, inventory, troubleshooting tools, and recovery mechanisms.

The central idea is that production S3 management combines observability, security, recoverability, and cost control. CloudTrail explains API activity; CloudWatch helps identify operational changes; Storage Lens and Inventory provide usage visibility; and a deliberate recovery strategy protects against data loss.

For further reference, consult the official AWS documentation:

* [CloudTrail events for Amazon S3](https://docs.aws.amazon.com/AmazonS3/latest/userguide/cloudtrail-logging-s3-info.html?utm_source=chatgpt.com)

* [S3 metrics and CloudWatch monitoring](https://docs.aws.amazon.com/AmazonS3/latest/userguide/metrics-dimensions.html?utm_source=chatgpt.com)

* [Amazon S3 Storage Lens](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage_lens.html?utm_source=chatgpt.com)

* [Amazon S3 Inventory](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-inventory.html?utm_source=chatgpt.com)

* [S3 Object Lock and retention](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lock.html?utm_source=chatgpt.com)

* [Pulumi AWS provider reference](https://www.pulumi.com/registry/packages/aws/?utm_source=chatgpt.com)
