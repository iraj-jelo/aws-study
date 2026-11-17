# Module 7 — Production Operations, Monitoring, and Troubleshooting

## 1. Introduction to S3 Operations

Amazon S3 is designed for high durability and availability, but production workloads still require monitoring, auditing, troubleshooting, recovery planning, and cost management.

Operating S3 effectively means answering five questions:

- Visibility: What is happening to our data and storage?
- Security: Who accessed an object, and why was access denied?
- Reliability: Are uploads, downloads, and replication working correctly?
- Recovery: Can we restore data after accidental deletion or corruption?
- Cost: Which storage, requests, retrievals, and transfers are driving expenditure?

S3 operational capabilities are distributed across several AWS services. Understanding their different purposes is essential to avoiding blind spots.

| Capability                         | Primary AWS service or feature                               |
| ---------------------------------- | ------------------------------------------------------------ |
| Object-level auditing              | AWS CloudTrail data events                                   |
| Operational metrics and alarms     | Amazon CloudWatch                                            |
| Detailed HTTP request records      | S3 server access logging                                     |
| Organization-wide storage analysis | S3 Storage Lens                                              |
| Object-level reporting             | S3 Inventory                                                 |
| Large-scale object processing      | S3 Batch Operations                                          |
| Recovery and historical versions   | S3 Versioning, replication, and backup mechanisms            |
| Cost attribution                   | AWS Cost Explorer, cost allocation tags, and S3 Storage Lens |

## 2. CloudTrail Data Events and Object-Level Auditing

### 2.1 Understanding CloudTrail

AWS CloudTrail records activity in an AWS account, providing an audit trail of actions performed through the AWS Management Console, AWS SDKs, AWS CLI, and other supported interfaces.

CloudTrail distinguishes between two important event categories.

Management events record operations that manage AWS resources, such as creating a bucket, changing a bucket policy, or configuring versioning.

Data events record operations performed on resources, such as uploading, retrieving, or deleting S3 objects.

S3 object-level auditing generally requires enabling the appropriate CloudTrail data-event selectors. These events are not automatically included in the standard management-event history.

### 2.2 Important S3 data events

| Operation            | Example                                                  |
| -------------------- | -------------------------------------------------------- |
| `GetObject`          | A user downloads a confidential document                 |
| `PutObject`          | An application uploads a file                            |
| `DeleteObject`       | An object is deleted                                     |
| `CopyObject`         | An object is copied to another key                       |
| Multipart operations | An application initiates or completes a multipart upload |

The exact event names and coverage depend on the API operation and event configuration.

CloudTrail records can help establish which identity performed an operation, when it occurred, which resource was involved, and what request context was available.

For example, when investigating an unexpected download, an operator can examine the event's identity, bucket and object information, source IP address when recorded, and request outcome.

### 2.3 Configuring data-event collection

CloudTrail event selectors can be configured to record object-level activity for specific buckets or broader sets of S3 resources.

A production configuration should consider:

- Which buckets contain sensitive or regulated data.
- Which object operations must be audited.
- Whether read events, write events, or both are required.
- Where the audit records will be stored.
- How long records must be retained.
- Who is allowed to access or modify the audit trail.

Recording every object operation across a large environment can produce substantial event volume and cost. Targeted selectors are often appropriate when only particular buckets or operations require intensive auditing.

CloudTrail data-event charges depend on the applicable pricing and event configuration. Operational monitoring should therefore include the cost of collecting and retaining audit records.

### 2.4 Protecting audit records

An audit trail is useful only if the records remain trustworthy and accessible.

A production design may use a dedicated logging account or centralized logging bucket, with restricted write permissions, encryption, lifecycle management, and appropriate retention controls.

CloudTrail log file integrity validation can help verify whether delivered log files have been modified or deleted after delivery. It does not prevent every possible administrative attack, so access restrictions and independent retention controls remain important.

CloudTrail is an audit service, not a complete real-time alerting system. Operational alerts can be built using integrations such as EventBridge, CloudWatch, and supported notification services.

## 3. CloudWatch Metrics, Alarms, and Request Monitoring

### 3.1 What CloudWatch provides

Amazon CloudWatch provides metrics, alarms, dashboards, and monitoring integrations for AWS services.

S3 monitoring commonly involves three categories of information:

- Storage metrics: How much data is stored and how many objects exist.
- Request metrics: How clients interact with a bucket.
- Operational events: Whether important changes or failures occur.

S3 publishes several daily storage metrics automatically, while detailed request metrics must generally be enabled for the relevant bucket or filter.

### 3.2 Storage metrics

Common S3 storage metrics include:

- `BucketSizeBytes`
- `NumberOfObjects`

These metrics help operators understand storage growth and object-count trends.

Storage metrics are generally reported daily rather than providing immediate, per-request visibility. They should not be treated as real-time indicators of individual upload or deletion operations.

Storage class and object type distinctions matter when interpreting these metrics. For example, current objects, noncurrent versions, and incomplete multipart uploads can have different cost implications.

### 3.3 Request metrics

S3 request metrics can provide more detailed operational visibility, including:

- `AllRequests`
- `GetRequests`
- `PutRequests`
- `4xxErrors`
- `5xxErrors`
- `FirstByteLatency`
- `TotalRequestLatency`

These metrics are useful for identifying traffic spikes, increased error rates, and latency changes.

Request metrics are typically available at one-minute granularity after configuration, subject to service behavior and metric availability. They are not a replacement for detailed request logs.

Request metrics can incur additional CloudWatch charges, so filters should be chosen carefully.

### 3.4 Designing meaningful alarms

A useful alarm identifies a condition that requires investigation rather than simply reporting that activity occurred.

Examples include:

- A sustained increase in S3 `5xxErrors`.
- An unusual rise in `4xxErrors`.
- Request latency exceeding a workload-specific threshold.
- Storage growth exceeding expected trends.
- Unexpected access or configuration changes detected through audit events.

A high `4xxErrors` count does not automatically mean that S3 is malfunctioning. It may reflect expired presigned URLs, invalid requests, authorization failures, or an application defect.

Likewise, an increase in `5xxErrors` warrants investigation but does not by itself establish the root cause.

### 3.5 Metrics versus logs

| Feature               | Best suited for                    |
| --------------------- | ---------------------------------- |
| CloudWatch metrics    | Trends, rates, latency, and alarms |
| CloudTrail            | Identity and API activity auditing |
| S3 server access logs | Detailed HTTP request analysis     |
| S3 Inventory          | Periodic object-level reporting    |

A reliable monitoring strategy combines these capabilities instead of expecting a single service to answer every operational question.

## 4. S3 Server Access Logging and Its Limitations

S3 server access logging records detailed information about requests made to a bucket. Records can include the requester, request time, operation, object key, HTTP status, error details, and other request attributes.

This information is particularly useful when investigating patterns that are difficult to understand from aggregated metrics.

### 4.1 Typical use cases

Server access logs can help investigate:

- Repeated unauthorized requests.
- Unexpected object downloads.
- Clients repeatedly requesting missing objects.
- Changes in traffic patterns.
- Application behavior that generates excessive requests.
- Request outcomes associated with particular object keys.

### 4.2 Important limitations

Server access logging has several operational considerations.

Delivery is not real-time. Logs are delivered on a best-effort basis, and records can be delayed. They are unsuitable as the sole mechanism for immediate incident detection.

Delivery is not guaranteed to be complete. Logging should not be assumed to provide a perfect, synchronous record of every request.

Log processing requires care. Records must be parsed, filtered, and analyzed before they become useful for complex investigations.

Log storage introduces costs. The destination bucket consumes storage and may incur additional processing charges.

Sensitive information requires protection. Access logs can expose object keys, requester information, and other operational details. Their permissions and retention should be managed accordingly.

### 4.3 Logging bucket architecture

A common production pattern is to keep application data and operational logs separate.

The application bucket holds business objects, while a dedicated logging bucket stores access records. The logging bucket should have appropriately restricted permissions and a lifecycle policy that reflects retention requirements.

Where supported by the chosen logging configuration, avoid circular logging arrangements and carefully review the destination bucket's configuration.

## 5. S3 Storage Lens, Inventory, and Batch Operations

These three capabilities solve different problems and are especially useful when an environment contains many buckets and millions of objects.

### 5.1 S3 Storage Lens

S3 Storage Lens provides visibility into storage usage and activity across buckets and, depending on the configuration, accounts and organizations.

It can help answer questions such as:

- Which buckets consume the most storage?
- How is the distribution across storage classes changing?
- Where are noncurrent object versions accumulating?
- Which storage patterns may indicate inefficient lifecycle policies?
- How is storage usage evolving over time?

Storage Lens includes metrics and dashboards, with advanced capabilities depending on the selected configuration and pricing tier.

It is useful for identifying broad trends, but it is not a substitute for inspecting individual objects when diagnosing a specific failure.

### 5.2 S3 Inventory

S3 Inventory generates scheduled reports about objects and their metadata.

Depending on the configured report, fields can include:

- Bucket and object key.
- Object size and last-modified time.
- Storage class.
- Version information.
- Encryption status.
- Replication status.
- Other supported object attributes.

Inventory is particularly useful when examining large datasets without issuing a separate API request for every object.

It can support storage audits, lifecycle planning, compliance reporting, and identifying objects that do not meet expected configuration requirements.

Inventory is a scheduled reporting mechanism, not a real-time view of bucket contents. Its reports reflect the inventory generation process and may not include the most recent changes.

### 5.3 S3 Batch Operations

S3 Batch Operations performs supported operations across large collections of objects using a job and a manifest.

A manifest identifies the objects to process. It can be based on an inventory report or another supported manifest source.

Depending on the operation, Batch Operations can be used for tasks such as:

- Copying objects.
- Restoring archived objects.
- Replacing object tags.
- Invoking a Lambda function against objects.
- Applying supported retention or legal-hold changes.
- Computing checksums or performing other supported operations.

Batch Operations provides job status and completion reports, making it easier to track success and failure across large-scale tasks.

The exact operations available depend on the job configuration and service support.

### 5.4 Choosing the right capability

| Requirement                                      | Appropriate capability           |
| ------------------------------------------------ | -------------------------------- |
| Understand organization-wide storage trends      | Storage Lens                     |
| Produce a scheduled list of objects and metadata | Inventory                        |
| Perform an operation on many objects             | Batch Operations                 |
| Investigate a specific API request               | CloudTrail or server access logs |
| Detect request-rate and latency changes          | CloudWatch request metrics       |

These services complement one another. Inventory can identify a population of objects, Batch Operations can act on that population, and Storage Lens can help assess the broader impact.

## 6. Diagnosing `AccessDenied`, KMS Failures, and Policy Conflicts

Access problems are among the most common S3 operational issues because permissions can depend on multiple policies and security controls.

### 6.1 The layers of S3 authorization

An S3 request can be affected by several layers:

- IAM identity policies.
- S3 bucket policies.
- S3 access point policies.
- AWS Organizations service control policies (SCPs).
- Permissions boundaries.
- Session policies.
- VPC endpoint policies.
- S3 Block Public Access settings.
- AWS KMS key policies and grants when SSE-KMS is involved.

Not every request is affected by every layer. The relevant controls depend on the identity, resource, network path, and operation.

An explicit deny in an applicable policy generally overrides an allow.

For cross-account access, both the requesting identity's permissions and the resource owner's authorization requirements must be considered.

### 6.2 A systematic troubleshooting process

When a request fails, begin with the exact API operation and error response.

Step 1: Identify the failed operation.

Determine whether the failure involves `GetObject`, `PutObject`, `ListBucket`, `DeleteObject`, or another operation. These operations can require different permissions.

For example, `s3:ListBucket` applies to the bucket resource, whereas `s3:GetObject` applies to an object resource.

Step 2: Identify the caller.

Check which IAM role, user, federated session, or service identity made the request. Applications may use different credentials from those configured in an operator's terminal.

Step 3: Inspect the applicable policies.

Review identity policies, bucket policies, access point policies, organization restrictions, endpoint policies, and any relevant permission boundaries or session policies.

Pay particular attention to resource ARNs, object prefixes, account IDs, condition keys, and explicit denies.

Step 4: Check network and public-access controls.

Verify whether the request uses the expected endpoint and whether a bucket policy restricts access by VPC endpoint, source network, or other conditions.

Step 5: Investigate encryption permissions.

If SSE-KMS is enabled, S3 authorization alone may not be sufficient.

Step 6: Correlate the failure with audit information.

Use CloudTrail records where available and inspect relevant request metrics or access logs. Not every failure will expose the complete policy evaluation, so additional investigation may be necessary.

### 6.3 Common KMS permission failures

With SSE-KMS, access to an object can depend on both S3 permissions and permissions to use the relevant KMS key.

Typical requirements include:

- `kms:Decrypt` for supported read and decryption workflows.
- `kms:GenerateDataKey` for applicable upload operations.
- Additional KMS permissions for certain multipart or administrative workflows.

The exact requirements depend on the API operation, encryption configuration, and workflow.

The KMS key policy must also permit the intended access, directly or through the appropriate IAM authorization arrangement.

A common misconception is that granting `s3:GetObject` automatically grants permission to decrypt an SSE-KMS object. It does not.

### 6.4 Understanding error messages

S3 may return generic authorization errors rather than revealing the exact policy that blocked a request. AWS can provide more detailed authorization context in certain situations, but the availability of that information depends on the request and policy context.

A successful request from the AWS CLI also does not prove that an application has the same permissions. The CLI and application may use different credentials, Regions, endpoints, or encryption settings.

The objective is to establish which authorization layer rejected the request rather than adding broad permissions as a workaround.

## 7. Request Throttling, Retries, and Large-Object Transfer Failures

### 7.1 S3 request scaling

Amazon S3 is designed to support high request rates and automatically scales to accommodate traffic. Nevertheless, clients may encounter temporary errors, network interruptions, service-side errors, or performance problems.

S3 supports high request rates per partitioned prefix, and performance can scale with parallelization. Real-world throughput also depends on object sizes, network capacity, client implementation, concurrency, and workload characteristics.

A prefix should not automatically be treated as a bottleneck simply because it contains many objects.

### 7.2 Retry strategies

Applications should implement retries for appropriate transient failures.

A sound retry strategy commonly includes:

- Exponential backoff.
- Random jitter to avoid synchronized retries.
- Maximum attempt counts or an overall time budget.
- Respect for retryable error types and service responses.
- Idempotency considerations for operations that may be repeated.

AWS SDKs provide retry mechanisms, but application-level workflows still need appropriate timeout and failure-handling policies.

Blindly retrying every error can amplify a problem. For example, repeatedly retrying an authorization failure will not fix an incorrect bucket policy.

### 7.3 Multipart uploads

Multipart upload allows a large object to be uploaded in separate parts. It can improve throughput and allow failed parts to be retried independently.

However, multipart uploads introduce operational considerations:

- Choosing suitable part sizes.
- Controlling upload concurrency and memory usage.
- Retrying failed parts.
- Completing uploads correctly.
- Aborting incomplete uploads.
- Monitoring and cleaning up abandoned uploads.

Incomplete multipart uploads can leave billable parts in storage until they are completed or aborted. Lifecycle rules can be configured to abort incomplete multipart uploads after an appropriate period.

### 7.4 Large downloads and transfers

Large-object transfer problems can result from network instability, timeouts, client memory constraints, incorrect concurrency, or application-level streaming behavior.

Transfer managers in AWS SDKs can simplify multipart handling and retries.

For very large datasets, the appropriate strategy may involve parallel transfers, optimized SDK settings, network improvements, or a managed data-transfer service. The best approach depends on transfer size, frequency, latency requirements, and available network capacity.

## 8. Replication Monitoring and Troubleshooting

S3 replication can copy objects between buckets in the same Region or across Regions. Replication is useful for resilience, regional distribution, and some compliance requirements, but it should not be assumed to provide instantaneous synchronization or a complete backup strategy by itself.

### 8.1 Replication status

S3 exposes replication status for supported object workflows.

Common statuses include:

- `PENDING`: Replication has not completed.
- `COMPLETED`: Replication completed successfully.
- `FAILED`: Replication failed.
- `REPLICA`: The object is a replica.

The exact status behavior depends on the source object, replication configuration, and operation.

### 8.2 Common causes of replication failures

Replication can fail or behave unexpectedly when:

- The required IAM replication role lacks permissions.
- Destination bucket policies do not permit replication.
- KMS permissions or destination encryption settings are incorrect.
- Versioning is disabled or misconfigured.
- The replication rule does not match the object's prefix or tags.
- Object ownership or other destination requirements are not satisfied.
- An object was created before the replication rule existed and is not covered by the applicable existing-object replication workflow.

### 8.3 Monitoring replication health

Replication monitoring should consider more than whether a replication rule exists.

Operators should examine object replication status, replication metrics where configured, and replication events where supported. Replication Time Control can provide defined replication-time objectives and associated monitoring capabilities for supported configurations.

When a failure occurs, first identify the affected object and rule. Then inspect permissions, encryption, versioning, filters, and destination settings.

A successful replication configuration deployment is not proof that every object is replicating correctly.

## 9. Recovery Testing, Deletion Protection, and Backup Strategy

High durability does not eliminate the risk of logical data loss. An authorized application can delete the wrong object, overwrite a file with invalid data, or propagate unwanted changes through a replication workflow.

Recovery requires deliberate design.

### 9.1 S3 Versioning

Versioning preserves multiple versions of an object under the same key.

It can help recover from accidental overwrites and deletions, subject to version retention and permissions.

A normal delete in a versioned bucket commonly creates a delete marker rather than immediately removing all historical versions.

However, versioning alone is not a complete backup solution. An attacker or administrator with sufficient permissions may permanently delete versions or alter relevant configuration.

### 9.2 S3 Object Lock

Object Lock can protect supported object versions from deletion or alteration for a specified retention period or under a legal hold.

Its two retention modes serve different purposes:

- Governance mode: Authorized users with the required permissions can bypass retention controls.
- Compliance mode: Protected object versions cannot be overwritten or deleted before retention expires, including by the account root user.

Object Lock is useful for records that require strong retention guarantees. It must be designed carefully because retention restrictions can prevent legitimate cleanup operations.

### 9.3 Replication versus backup

Replication improves data availability and distribution, but it is not automatically equivalent to an independent backup.

Depending on the design, unwanted changes or deletions may also be reflected at a destination, and shared administrative permissions can undermine both copies.

A stronger recovery strategy considers:

- Versioning and historical object recovery.
- Independent administrative access boundaries.
- Object Lock where required.
- Replication to a separate bucket or account where appropriate.
- Retention and lifecycle policies.
- Tested restoration procedures.
- Recovery time objectives (RTOs) and recovery point objectives (RPOs).

### 9.4 Recovery testing

A recovery plan should be evaluated against realistic failure scenarios, including accidental overwrite, deletion, incorrect lifecycle configuration, and compromised application credentials.

Testing should establish that the required historical data exists, that the recovery identity has the correct permissions, and that restoration can be completed within the required timeframe.

A backup or replica that has never been restored successfully provides weaker assurance than one covered by a tested recovery procedure.

## 10. Cost Allocation, Request Costs, Data Transfer, and Retrieval Charges

S3 costs arise from multiple dimensions. Optimizing only the storage price per gigabyte can lead to unexpected expenditure elsewhere.

### 10.1 Major cost categories

| Cost category       | What drives it                                                                  |
| ------------------- | ------------------------------------------------------------------------------- |
| Storage             | Amount of data stored and selected storage class                                |
| Requests            | API operations such as PUT, GET, LIST, and lifecycle-related requests           |
| Retrieval           | Accessing data in storage classes with retrieval charges                        |
| Data transfer       | Transfer to destinations or services where charges apply                        |
| Replication         | Replication requests, destination storage, and applicable transfer charges      |
| Monitoring          | CloudTrail data events, CloudWatch metrics, and related services                |
| Management features | Applicable Inventory, Storage Lens, Batch Operations, and other feature charges |

Actual prices depend on Region, storage class, usage volume, and the current AWS pricing model.

### 10.2 Storage class economics

Lower-cost archival storage is not automatically the cheapest choice for every workload.

Storage class decisions should account for:

- Expected access frequency.
- Retrieval latency requirements.
- Retrieval and request charges.
- Minimum storage duration.
- Minimum billable object sizes where applicable.
- Early deletion charges.
- Lifecycle transition request costs.

For example, moving frequently accessed objects into an archival class may increase retrieval costs and degrade the application's response time.

### 10.3 Cost allocation tags

Cost allocation tags help attribute eligible AWS charges to applications, teams, environments, or business units.

A consistent tagging strategy might distinguish:

- `Environment`
- `Application`
- `Owner`
- `CostCenter`
- `DataClassification`

User-defined cost allocation tags generally need to be activated for cost reporting. Billing data may take time to reflect newly applied or activated tags, and not every charge is attributable to a resource tag in the same way.

### 10.4 Practical cost optimization principles

S3 cost optimization typically involves several complementary measures:

1. Select storage classes according to actual access patterns.
2. Expire temporary data and obsolete versions when retention permits.
3. Abort incomplete multipart uploads.
4. Use lifecycle rules for eligible archival transitions.
5. Monitor request volume and unnecessary object operations.
6. Review replication and data-transfer requirements.
7. Attribute costs consistently and examine trends.
8. Consider the operational cost of monitoring and compliance controls.

The objective is not simply to minimize storage cost. It is to achieve the required durability, availability, security, and performance at a sustainable total cost.

## 11. Putting the Operational Model Together

A mature S3 operational model combines preventive controls, detection, investigation, and recovery.

Prevent

IAM least privilege, Block Public Access, encryption, versioning, lifecycle rules, and protected logging.

Detect

CloudWatch metrics and alarms, CloudTrail events, replication monitoring, Storage Lens, and Inventory.

Investigate

Correlate API events, request errors, identity policies, KMS permissions, logs, and object replication status.

Recover and improve

Restore historical versions, recover retained data, correct configuration, validate recovery objectives, and review costs.

## 12. Pulumi and Production Operations

Pulumi remains useful for managing the operational configuration of S3 infrastructure alongside its foundational resources.

A well-structured Pulumi project can manage:

- CloudTrail trails and event selectors.
- S3 logging destinations and bucket policies.
- CloudWatch alarms and relevant monitoring resources.
- S3 Inventory configurations.
- Replication roles and policies.
- Lifecycle and versioning settings.
- Encryption and access controls.
- Cost allocation tags and resource naming conventions.

Not every operational capability is best represented as a Pulumi resource alone. Some monitoring, audit, and recovery workflows also involve console investigations, log analysis, SDK calls, and operational procedures.

Infrastructure as code provides repeatability and reviewability, but it does not replace runtime monitoring or recovery testing. Production changes should be reviewed for their effect on existing permissions, retained objects, and data protection settings.

### Module summary

The key to operating S3 in production is understanding the distinct roles of auditing, monitoring, logging, inventory, and recovery mechanisms. CloudTrail explains API activity, CloudWatch identifies operational trends, access logs provide request-level context, Storage Lens and Inventory reveal storage patterns, and versioning, retention, and backup mechanisms support recovery.

Together, these capabilities allow teams to operate S3 with greater visibility, troubleshoot authorization and replication failures systematically, and control both operational risk and cost.