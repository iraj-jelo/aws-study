### Module 4 — Storage Classes, Versioning, and Lifecycle Management

AWS S3 with Pulumi and Python · Intermediate

### Learning objectives

Amazon S3 provides multiple storage classes, versioning, lifecycle automation, and retention controls to help organizations balance storage cost, availability, durability, and recovery requirements.

In this module, you'll learn how these features work, how they interact, and how to manage them declaratively with Pulumi. The central idea is that storing data cheaply is only one part of cost optimization; access frequency, retrieval latency, retention requirements, and recovery behavior matter just as much.

### 1\. Understanding S3 storage classes

S3 storage classes determine how objects are stored, what availability characteristics they provide, and how storage and retrieval are billed. You choose a storage class when uploading an object or transition an existing object through a lifecycle policy.

![\[Re2021\] Amazon S3의 신규 스토리지 클래스(Glacier Instant Retrieval)가 출시되었습니다 - GS네오텍(WiseN) 블로그 | GS네오텍(WiseN) 블로그](https://images.openai.com/static-rsc-4/XUXoPGm2TNPoSTd5yOL3WdWMFXL0F72BuKdL75dLuyQFMmC-1x0hpxdw-2j8uf_mkp6zpT6zE5NaNEiAvb8IlxBavLq9xAZrmMGxBPMccEBfPAz9GE3EFDgk5ZKzlXwfIJ02ntCkY84LnctimmJtQxW_y5PZOqMtZprE4UUUPFXGOiVCiU8Fh5fLz2tFUW87?purpose=fullsize)

S3 Standard

Frequent access

Designed for frequently accessed data that needs low-latency access. It stores data redundantly across multiple Availability Zones and is suitable for application assets, active datasets, and frequently read files.

![How Canva saves over $3 million annually in Amazon S3 costs | AWS Storage Blog](https://images.openai.com/static-rsc-4/_E2lrz665cz3g6AW38dJwtOqfmxKFvjbAxMfH9XTaeaZrfMnKMnyE12VyvxeGTx_DGZm1HKp1YeGjgKWo75H1Kn3Meac-QfVx273ExV3cZPtkb_AER1Z2TzCV8VVFhbeC0AqUdvjUDq-NJIOCZcf8e9lfZg0-GonYRCa1nOv5noWnv71K-0B6fcbIcGvst1P?purpose=fullsize)

S3 Intelligent-Tiering

Changing access patterns

Automatically moves eligible objects between access tiers as their access patterns change. It is useful when access frequency is unpredictable. Monitoring and automation charges apply, and certain optional archive tiers have additional retrieval considerations.

![Optimizing your AWS Infrastructure for Sustainability, Part II: Storage | AWS Architecture Blog](https://images.openai.com/static-rsc-4/n9uvhHWTw5M36iF7_7S73J6nTAdVv1I1ONahpzi-LExs_ugpd8gfISQDZ4buiMYnLmhvq-NLCl0RmzGOorq58fcdfuzeAuRlzMaOSI34YSTF5mvZj1PDFO53x3jwb6vPvsKoFbnuXOhe9nq5VJ8AJfXkGd1erh0f1VSw9FXwK-q6aNNpmzjS9XQJJM-Mc2Yr?purpose=fullsize)

S3 Standard-IA

Infrequent access

For data that is accessed infrequently but must remain quickly accessible when requested. It offers lower storage pricing than Standard, with retrieval charges and a minimum billable storage duration.

![Medium](https://images.openai.com/static-rsc-4/o62Fdotqqwl3XLOsOLhgPM2G5ur--5O5wnFUPS02DkC0gQpBBMHWylZz0NqJR5U2LEiYoDPs2jmWbEvrOh5bWpF8ch6MA_hsR0Q9a9M8az-BQoxcJLp1WzXGgwgVGHIrUNDxJXCucUUNcHkq-g-sLh27DM8uVB62DLKA0PAtZoJNFftNxt6d7A69AY9nNnD4?purpose=fullsize)

S3 One Zone-IA

For infrequently accessed, recreatable or separately recoverable data that does not require multi-AZ storage resilience. Data is stored in one Availability Zone, making this a poor choice for irreplaceable primary copies.

![Let’s Architect! Modern data architectures | AWS Architecture Blog](https://images.openai.com/static-rsc-4/K3DagzKGZXW-B1ZKNoFIbjec0_jrOtPepw51aDTSTFNDm1iGwr9lfogRJQdt3gUmCusf_rGUH95nLtZLkS-tQBdbD-ekxAusG70__XZeka1wJ-jHGPsd7uEhbpHoxikQNC07Wv55ZLQJvrRVyEs9lFBof5AkUmi8VmXHo_cBcrjuS9wICLpRnEkTAguppbL4?purpose=fullsize)

S3 Glacier Instant Retrieval

For long-lived archival data that is rarely accessed but still requires millisecond retrieval access. It is useful for archives that occasionally need to be read immediately, though retrieval costs and minimum storage duration must be considered.

![AWS の S3 Glacier を改めて整理してみる | 大阪のAWSパートナー | ターン・アンド・フロンティア](https://images.openai.com/static-rsc-4/1cOAE3frseLB_W4MOimiLGgO_4XXHMC4gFfdSypS7Y3sawKpfET_6o1OUgjZBBJ0jcNAOqYRJWjkETGrruK9nKkfrrYgvw-Bei2XduB-JNhwkCcbSe3VQM2OVWK0d06WU0EhuNlqaxUOofBybeqqN83Spej8_moJ30Fs0ztZ-4W4yECF1yr6qqFDJ-lX2Mvj?purpose=fullsize)

S3 Glacier Flexible Retrieval

For archive data where retrieval can take minutes to hours, depending on the retrieval option. It supports several retrieval modes and is appropriate for backups and historical data that do not require immediate access.

![How to reduce AWS S3 costs with lifecycle policies and intelligent-tiering - Hykell](https://images.openai.com/static-rsc-4/lrxxNq7cW0RMrKt6EulL6SBxaiF3k4Cqwj45gCPbuQqfW-fOpz0GwE7G2iuhTvMiXBcDCEelQlETg4SKwznbe5KC_mLN5-vL644KcYbrxLhL-QNwHPbYzVK32Si15lT_AqJ0h9o1P6XBrnTjV6RXosWTYVbZN1FFik33ZNnk2teX-paEulIrRDw-GwNphor9?purpose=fullsize)

S3 Glacier Deep Archive

Intended for data retained for years and rarely retrieved, such as regulatory archives or long-term records. Retrieval typically takes many hours, so it is unsuitable for data that must be restored immediately.

### Comparing the main storage classes

| Storage class              | Access pattern      | Retrieval behavior                                            | Minimum storage duration                           |
| -------------------------- | ------------------- | ------------------------------------------------------------- | -------------------------------------------------- |
| S3 Standard                | Frequent            | Immediate                                                     | None                                               |
| Intelligent-Tiering        | Unknown or changing | Immediate for frequent, infrequent, and archive-instant tiers | No minimum duration charge for the automatic tiers |
| Standard-IA                | Infrequent          | Immediate                                                     | 30 days                                            |
| One Zone-IA                | Infrequent          | Immediate                                                     | 30 days                                            |
| Glacier Instant Retrieval  | Rare                | Milliseconds                                                  | 90 days                                            |
| Glacier Flexible Retrieval | Rare                | Minutes to hours                                              | 90 days                                            |
| Glacier Deep Archive       | Extremely rare      | Typically 12–48 hours, depending on retrieval option          | 180 days                                           |

These minimum durations affect billing, not a requirement to physically retain an object. Deleting or transitioning an object before the minimum duration expires can result in a remaining-duration charge. Intelligent-Tiering has separate considerations for optional archive tiers and small objects.

### 2\. Understanding storage costs and access patterns

Choosing a storage class requires evaluating more than its price per gigabyte. The total cost can include:

* Storage capacity per month.

* Requests, including uploads, copies, and lifecycle transitions.

* Data retrieval charges.

* Minimum billable object sizes.

* Minimum storage duration charges.

* Restore requests and temporary restored copies for archive classes.

* Data transfer and replication.

* Monitoring charges for Intelligent-Tiering.

For example, Standard-IA may be cheaper for a large object that is read occasionally, but it can be less economical for many small objects that are frequently retrieved. Intelligent-Tiering can help when access patterns are uncertain, but its per-object monitoring charges should be considered.

AWS documents the current storage class characteristics and cost considerations in its [S3 storage class guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/storage-class-intro.html?utm_source=chatgpt.com). Amazon Simple Storage Service

### Practical storage selection

| Data type                                          | Typical choice             | Reason                                        |
| -------------------------------------------------- | -------------------------- | --------------------------------------------- |
| Active application uploads                         | Standard                   | Frequent, low-latency access                  |
| Data with unpredictable access                     | Intelligent-Tiering        | Automatic tiering                             |
| Older reports read occasionally                    | Standard-IA                | Immediate access with lower storage cost      |
| Re-creatable intermediate data                     | One Zone-IA                | Lower storage cost with reduced AZ resilience |
| Rarely accessed archives requiring immediate reads | Glacier Instant Retrieval  | Millisecond retrieval                         |
| Historical backups with flexible recovery times    | Glacier Flexible Retrieval | Lower-cost archive storage                    |
| Long-term compliance archives                      | Glacier Deep Archive       | Very infrequent access                        |

These are starting points, not universal rules. Real workloads should be evaluated using object size, access frequency, retention periods, and recovery objectives.

### 3\. S3 Versioning

S3 Versioning preserves multiple versions of an object in the same bucket. When versioning is enabled, writing another object with the same key creates a new version rather than simply replacing the existing version.

For example, consider an object named `reports/annual.pdf`.

`reports/annual.pdf`

Current version · Version C

Current

Previous version B

An earlier copy retained by S3

Previous version A

An even older copy retained by S3

Every stored version consumes storage and can incur its own storage and request charges. Versioning therefore improves recovery but can also increase costs if old versions accumulate indefinitely.

### How versioning works

S3 versioning has three important states:

* Unversioned: The bucket does not maintain an object version history.

* Enabled: New writes create versioned objects, and overwrites preserve previous versions.

* Suspended: New writes no longer create ordinary new unique version IDs, but existing versions remain. Writes can create or replace the special `null` version.

Once versioning has been enabled, disabling it is not supported in the same way as suspending it. Existing versions are not automatically removed when versioning is suspended.

### Delete markers

Deleting an object from a version-enabled bucket normally creates a delete marker. The marker becomes the current version, making the object appear deleted to ordinary reads, while previous versions remain stored.

Current state: Delete marker

A normal GET request typically behaves as if the key does not exist.

Previous object version

The original content is still available when accessed by its version ID.

Deleting the delete marker by its version ID can make the previous version current again. Permanently deleting a particular object version requires specifying its version ID and having the appropriate permissions.

Important distinction: Versioning protects against many accidental overwrites and deletions, but it is not a complete backup strategy. A principal with sufficient permissions can permanently delete versions, and versioning does not by itself protect against every security or account-level failure.

See [How S3 Versioning works](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html?utm_source=chatgpt.com). Amazon Simple Storage Service

### 4\. S3 Lifecycle Management

S3 Lifecycle automates what happens to objects as they age. Instead of requiring an application to move or delete data, you define rules that S3 evaluates and applies.

A lifecycle rule consists of:

* Status: Whether the rule is enabled.

* Filter: Which objects are affected.

* Transitions: When eligible objects move to another storage class.

* Expiration: When eligible objects expire.

* Noncurrent version actions: How older versions are transitioned or expired.

Rules can target an entire bucket, a key prefix, object tags, or combinations of supported filter conditions.

### Example lifecycle policy

Consider a bucket storing application reports:

Days 0–30: S3 Standard

New reports are frequently accessed.

After 30 days: S3 Standard-IA

Older reports are accessed less frequently but remain immediately available.

After 120 days: S3 Glacier Flexible Retrieval

Historical reports move into archival storage when slower recovery is acceptable.

After the retention period: Expiration

Objects are scheduled for expiration according to the policy and any applicable retention requirements.

This timeline is illustrative. The transition schedule must account for minimum storage durations, object sizes, and lifecycle transition restrictions. For example, Glacier Flexible Retrieval has a 90-day minimum storage duration, so a transition to Deep Archive should not be scheduled in a way that causes an unintended early-transition charge. Amazon Simple Storage Service +1

### Expiration in versioned buckets

Lifecycle expiration behaves differently depending on versioning:

* In an unversioned bucket, expiration permanently removes the object.

* In a version-enabled bucket, expiration generally creates a delete marker for the current version.

* Noncurrent versions require separate lifecycle management if they should eventually be permanently removed.

* Expired delete markers can also be removed through an appropriate lifecycle configuration when no other versions remain.

Lifecycle processing is asynchronous. An object may remain visible for a period after it becomes eligible for expiration, and lifecycle rules should not be treated as an exact-time deletion mechanism.

### 5\. Noncurrent versions and storage cost control

Versioning can result in large amounts of historical data. Lifecycle rules can transition noncurrent versions to cheaper storage classes and expire them after a defined retention period.

For example, a policy might keep recent versions readily available while moving older versions into archive storage and eventually deleting them.

The key distinction is between two clocks:

* Current-version age: Time since the current object version was created.

* Noncurrent-version age: Time since that version stopped being current.

Noncurrent version actions use the second clock. This matters when an object is overwritten repeatedly: its older versions may be eligible for archival or expiration based on when each became noncurrent, rather than when the original object key was first created.

A retention policy must also account for delete markers. Removing old versions does not necessarily remove a current delete marker, and removing a delete marker does not necessarily delete all historical content.

AWS describes these behaviors in its [Lifecycle management guide](https://docs.aws.amazon.com/AmazonS3/latest/userguide/object-lifecycle-mgmt.html?utm_source=chatgpt.com). Amazon Simple Storage Service +1

### 6\. Object tags and tag-based lifecycle policies

S3 object tags are key-value pairs associated with individual object versions. They allow storage policies to reflect the purpose or ownership of data rather than relying solely on the object's path.

Examples include:

| Tag         | Example value | Possible purpose                      |
| ----------- | ------------- | ------------------------------------- |
| DataClass   | temporary     | Short-lived processing data           |
| DataClass   | archive       | Long-term retention                   |
| Environment | production    | Environment-specific management       |
| Owner       | analytics     | Ownership and cost allocation         |
| Retention   | 90-days       | Classification for a retention policy |

A lifecycle rule can select objects using tags. For example, objects tagged `DataClass=temporary` can be expired after a defined number of days, while objects tagged `DataClass=archive` can be transitioned to archival storage.

Tags are not inherently security controls. They are metadata that can drive policies and reporting. If an application or user can change a tag, that change may affect lifecycle eligibility. Permissions for modifying tags should therefore be designed carefully.

### Design considerations

* Use consistent, documented tag names and values.

* Avoid overlapping lifecycle rules that apply conflicting actions.

* Apply tags at upload time or through controlled automation.

* Consider how tag changes affect existing objects and versions.

* Remember that lifecycle filters and actions have service-specific constraints.

### 7\. S3 Object Lock, retention modes, and legal holds

Versioning helps recover data, but it does not inherently prevent authorized users from permanently deleting object versions. S3 Object Lock adds write-once-read-many (WORM) retention controls to protect object versions against deletion or alteration during a defined retention period.

Object Lock is useful for regulated records, immutable backups, and other data that must remain protected from modification or deletion.

### Retention modes

Governance mode

Authorized principals with the appropriate permissions can bypass retention protection. This supports controlled exceptions while preventing ordinary deletion.

Compliance mode

A protected object version cannot be overwritten or deleted before its retention period expires, including by the account root user. Retention cannot be shortened during that period.

Legal hold

A legal hold protects an object version without a predefined expiration date. It remains in effect until an authorized principal removes it. A legal hold can coexist with a retention period.

Object Lock requires versioning. It must be designed deliberately because retention settings can make cleanup impossible until the applicable protection expires. Compliance requirements should determine the retention mode and duration, not convenience.

### 8\. Replication prerequisites and versioning dependencies

S3 replication automatically copies eligible objects from a source bucket to a destination bucket, within the same Region (SRR) or across Regions (CRR).

Replication can support disaster recovery, compliance, data locality, and the separation of operational and backup copies.

Important prerequisites and considerations include:

* Source and destination buckets must have versioning enabled.

* The replication configuration needs an appropriate IAM role.

* Destination bucket policies and encryption permissions must permit replication.

* SSE-KMS encrypted objects require appropriate KMS permissions and configuration.

* Existing objects generally require S3 Batch Replication to replicate objects already present when the replication rule was created.

* Replication is asynchronous; it should not be treated as an instantaneous copy.

* Delete-marker replication behavior depends on the replication configuration and supported features.

* Replication does not automatically replace a retention strategy or protect against every destructive action.

A particularly important distinction is that replication can copy mistakes as well as good data. If an application overwrites an object or deletes data, replication alone is not a substitute for versioning, retention controls, or a carefully designed recovery strategy.

### 9\. Managing versioning and lifecycle policies with Pulumi

Pulumi lets you define S3 versioning and lifecycle configuration as code. The AWS provider exposes resources for both features, so changes can be reviewed, version-controlled, and deployed consistently across environments.

### Versioning configuration

A typical Pulumi Python resource enables versioning on a bucket:

```python
import pulumi_aws as aws

bucket = aws.s3.Bucket(
    "archive-bucket",
    force_destroy=False,
)

versioning = aws.s3.BucketVersioning(
    "archive-bucket-versioning",
    bucket=bucket.id,
    versioning_configuration={
        "status": "Enabled",
    },
)
```

The bucket's versioning state is managed separately from the bucket itself. This makes it easier to understand dependencies and control changes to versioning. The `force_destroy=False` setting also helps prevent Pulumi from automatically emptying a bucket during destruction.

AWS recommends allowing time for versioning configuration to propagate before issuing writes to a newly version-enabled bucket. Pulumi Registry

### Lifecycle configuration

The following example illustrates a lifecycle policy for objects tagged `DataClass=temporary`, plus management of noncurrent versions:

```python
lifecycle = aws.s3.BucketLifecycleConfigurationV2(
    "archive-bucket-lifecycle",
    bucket=bucket.id,
    rules=[
        {
            "id": "temporary-data-expiration",
            "status": "Enabled",
            "filter": {
                "tag": {
                    "key": "DataClass",
                    "value": "temporary",
                },
            },
            "expiration": {
                "days": 30,
            },
            "noncurrent_version_expiration": {
                "noncurrent_days": 90,
            },
        },
    ],
    opts=pulumi.ResourceOptions(
        depends_on=[versioning],
    ),
)
```

This example assumes `pulumi` is imported and the bucket is configured with appropriate security settings. The lifecycle resource manages the bucket's lifecycle configuration, which should generally be defined in one place rather than split across multiple competing resources. Pulumi Registry +1

The example's retention periods are illustrative, not universal recommendations. In a versioned bucket, expiration of the current object and expiration of noncurrent versions are separate operations. Temporary data should be tagged appropriately before the lifecycle policy is expected to affect it.

For additional details, consult the [Pulumi S3 lifecycle configuration reference](https://www.pulumi.com/registry/packages/aws/api-docs/s3/bucketlifecycleconfigurationv2/?utm_source=chatgpt.com).

### 10\. Common design mistakes

Several mistakes can undermine otherwise reasonable S3 retention and cost policies:

* Archiving too early: Minimum storage durations and transition charges can eliminate expected savings.

* Ignoring small objects: Minimum billable object sizes affect some infrequent-access classes.

* Keeping every version forever: Versioning without noncurrent-version management can cause storage costs to grow continuously.

* Assuming expiration is immediate: Lifecycle processing is asynchronous.

* Confusing delete markers with permanent deletion: A delete marker can hide an object while its content remains stored.

* Using tags without controlling tag changes: Changing an object's tags can affect lifecycle eligibility.

* Assuming replication is backup: Replication does not automatically protect against every accidental deletion or malicious action.

* Ignoring Object Lock during cleanup: Retention controls can prevent permanent deletion even when infrastructure teardown is requested.

* Defining lifecycle configuration in multiple places: Competing resource declarations can overwrite each other's intended configuration.

### Module summary

The essential concepts to retain are:

* Storage classes should reflect access frequency, retrieval requirements, resilience, and retention duration.

* Versioning preserves previous object versions and supports recovery from accidental overwrites or ordinary deletions.

* Lifecycle policies automate transitions, expiration, and noncurrent-version management.

* Object tags allow policies to target data by purpose, ownership, or classification.

* Object Lock provides stronger retention protection for immutable records.

* Replication improves geographic or operational resilience but does not replace a recovery strategy.

* Pulumi makes these configurations reproducible, reviewable, and maintainable as part of infrastructure as code.

The overarching principle is to design storage lifecycle policies around the data's actual business requirements. Cost optimization should never silently undermine required retention, recovery time, or durability.
