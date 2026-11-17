### Module 6 — Advanced S3 Features and Architecture

Goal: Understand advanced Amazon S3 capabilities and learn how to choose appropriate storage architectures for production workloads, using Pulumi and Python for infrastructure as code.

### 6.1 Cross-Region Replication (CRR) and Same-Region Replication (SRR)

Amazon S3 Replication automatically copies objects from a source bucket to a destination bucket asynchronously. It helps organizations improve disaster recovery, satisfy geographic data requirements, separate production and analytics data, and maintain additional copies of important information.

### Cross-Region Replication (CRR)

CRR replicates objects between buckets in different AWS Regions.

Typical use cases include:

* Disaster recovery in a geographically separate Region.

* Meeting geographic data distribution requirements.

* Reducing latency for users accessing data in another Region.

* Maintaining copies of important datasets away from the primary Region.

### Same-Region Replication (SRR)

SRR replicates objects between buckets in the same Region.

Typical use cases include:

* Separating production and development datasets.

* Maintaining separate copies for analytics or log processing.

* Centralizing data from multiple application buckets.

* Supporting different retention or ownership requirements.

![Secure Amazon S3 Cross-Region Replication with KMS: A Production-Ready Guide | by Dorothycherotich | Medium](https://images.openai.com/static-rsc-4/y3wf7FP9ko1AcTi3vLT79Ev4QdQDW-ehF2rQiQ804g6EyMdu3d-l2kwJhSAoLw-Lx0A6LtLUgAyQ5S7mNQWj5WeeBAyGApn4BD0XoEZyNbGx47YjNQR2c6sSS3VkHuKOXevKWjyb-74lsyyVCVwzXYttkyBnWqURCWoOCzqq0ofEl4bmTYvrqyU9OwCa57xD?purpose=fullsize)

### CRR versus SRR

| Characteristic        | CRR                                              | SRR                                       |
| --------------------- | ------------------------------------------------ | ----------------------------------------- |
| Destination           | Different Region                                 | Same Region                               |
| Disaster recovery     | Supports regional recovery strategies            | Does not protect against regional failure |
| Geographic separation | Yes                                              | No                                        |
| Typical latency       | Depends on cross-Region transfer and replication | Generally avoids cross-Region transfer    |
| Data transfer costs   | Cross-Region transfer charges may apply          | No inter-Region transfer charge           |
| Common use case       | Regional resilience                              | Data separation and regional workflows    |

Both approaches require versioning on the source and destination buckets. Replication is asynchronous, so the destination is not guaranteed to contain every recent change immediately.

Important: Replication is not a complete backup strategy. It can replicate unwanted changes or deletions under certain configurations, and it does not automatically provide independent protection against every form of data loss.

### 6.2 Replication IAM Roles, Permissions, and Configuration

S3 replication requires authorization for S3 to read eligible objects from the source and write replicas to the destination.

### How replication works

The main components are:

* Source bucket: Stores the original objects and defines replication rules.

* Replication configuration: Specifies the destination, eligible objects, and optional filters.

* IAM replication role: Allows S3 to retrieve source object versions and replicate objects.

* Destination bucket: Accepts replicated objects through the required resource permissions.

* Encryption configuration: Defines any additional permissions needed for encrypted objects.

### Important prerequisites

* Enable versioning on both buckets.

* Configure the appropriate IAM role and trust relationship for S3.

* Grant the required source and destination permissions.

* Configure destination bucket policies when needed.

* Provide KMS permissions if replicating objects encrypted with customer-managed KMS keys.

* Consider ownership settings when the destination belongs to another AWS account.

### Replication rules

Replication rules can apply to an entire bucket or to objects selected by prefixes and tags. They can also specify a destination storage class and other supported replication options.

For example, an organization might replicate objects under `critical/` to a disaster recovery bucket while keeping temporary files local.

### Existing objects versus new objects

By default, replication rules apply to eligible objects created after replication is configured. Existing objects generally require S3 Batch Replication to copy them into the destination.

This distinction is important when enabling replication on a bucket that already contains production data.

### 6.3 Replication Time Control and Monitoring

Standard S3 Replication is asynchronous and does not guarantee a fixed replication time. For workloads with stricter replication requirements, Amazon S3 Replication Time Control (RTC) provides a service-level commitment to replicate 99.99% of new objects within 15 minutes.

RTC is an additional paid feature, and its service-level commitment has defined conditions and exclusions.

### Replication metrics

Replication monitoring helps identify delays, failed operations, and backlogs.

Important indicators include:

* Replication latency: How far behind the destination is.

* Pending operations: Objects awaiting replication.

* Failed operations: Replication operations that did not succeed.

* Bytes pending replication: The volume of data waiting to be transferred.

S3 replication metrics and RTC can support CloudWatch monitoring and alarms.

### Designing for recovery objectives

Two common disaster recovery measurements are:

* Recovery Point Objective (RPO): The maximum acceptable amount of data loss measured in time.

* Recovery Time Objective (RTO): The maximum acceptable time to restore service.

Replication can reduce recovery point exposure, but asynchronous replication means the most recent writes may not yet exist in the destination. RTO also depends on application failover, DNS changes, permissions, dependencies, and operational procedures.

### 6.4 S3 Object Lock and Compliance-Oriented Retention

S3 Object Lock helps prevent objects from being deleted or overwritten for a specified retention period. It is commonly used for regulatory records, audit evidence, financial records, and immutable backups.

Object Lock uses a WORM model: write once, read many.

### Retention modes

Governance mode

Authorized principals with the necessary permissions can bypass retention protections. This is appropriate when controlled administrative exceptions are required.

Compliance mode

A protected object version cannot be overwritten or deleted during its retention period, including by the AWS account root user. Retention cannot be shortened in the normal course of operation.

### Default retention and legal holds

Object Lock supports bucket-level default retention settings, as well as retention settings on individual object versions. Legal holds can protect object versions indefinitely until the hold is removed by an authorized principal.

Object Lock requires versioning. Enabling it and selecting compliance settings should be treated as a consequential architectural decision, since protected objects may continue to incur storage charges.

### Object Lock and replication

Object Lock can be relevant to replicated backup architectures. Replication configuration, destination capabilities, permissions, and retention behavior must be evaluated together to ensure the intended protection is actually enforced.

Architectural principle: Immutable storage is most effective when combined with restricted administrative access, separate backup ownership where appropriate, monitoring, and tested recovery procedures.

### 6.5 S3 Access Points and Multi-Region Access Points

As an organization grows, managing access through a single bucket policy can become difficult. S3 access points provide distinct access policies and endpoints for different applications or teams.

### S3 Access Points

An access point is associated with a bucket and can have its own permissions and network access controls.

For example, a shared data bucket could have:

* An analytics access point for read-only access.

* An ingestion access point for writing new records.

* A reporting access point restricted to a particular virtual private cloud.

Access-point policies complement the underlying bucket policy; they do not automatically override the bucket's security restrictions.

### VPC-only access points

An access point can be configured to restrict access to a VPC. This helps private workloads access S3 through supported network paths without exposing the access point to general public network access.

### Multi-Region Access Points

Multi-Region Access Points provide a single global endpoint for accessing datasets replicated across multiple AWS Regions. AWS routes requests to an appropriate underlying bucket based on the configured architecture and routing behavior.

They can simplify application access across Regions, particularly when combined with replication and failover policies.

However, a Multi-Region Access Point does not independently synchronize objects or guarantee that every Region contains the latest data. Replication and consistency requirements still need explicit design.

### 6.6 Static Website Hosting and CloudFront Integration

S3 can host static website content, including HTML, CSS, JavaScript, images, and downloadable assets.

There are two important architectural patterns.

### Pattern A: S3 static website endpoint

S3 website hosting serves static content through a website endpoint. The website endpoint does not support HTTPS directly and commonly requires publicly readable objects.

This pattern is useful for simple demonstrations or intentionally public static content, but it is generally not the preferred approach when private origin access and HTTPS are required.

### Pattern B: Private S3 origin behind CloudFront

![Hosting a Static website on a private Amazon S3 bucket using CloudFront’s OAC - DEV Community](https://images.openai.com/static-rsc-4/_F0f00_Xi9r_zepD7PqEKiMrN0B0ipnxPNam96ekaRBR7YkER35jdv-TQH4auoXVWErMAU3w2PWZ72PYX9zevA7fXhAMvlhKDPvcTC4FL0jr-PwpkLr0MVbyMTU9Mj7XE9NCZBbLUP1F_G-L1JGqizcX4gw74bNIBnNV3qMKyIDedSppEv7GqM68eLkc7yjC?purpose=fullsize)

For production static content, CloudFront can distribute content over HTTPS while the S3 bucket remains private.

The architecture uses:

* Amazon S3: Stores the static files.

* Amazon CloudFront: Caches and distributes content globally.

* Origin Access Control (OAC): Allows CloudFront to access a supported S3 REST API origin without making the bucket public.

* Bucket policy: Grants the intended CloudFront distribution access to the objects.

OAC is the preferred modern approach over the older Origin Access Identity (OAI) for supported S3 origin configurations.

### Caching and invalidation

CloudFront caching reduces repeated requests to S3 and can improve response latency. Cache policies, object cache headers, versioned asset names, and invalidations influence how quickly content updates become visible.

A private CloudFront architecture is particularly suitable for static application frontends, software downloads, and public media assets whose origin should remain inaccessible directly.

### 6.7 S3 Notifications, EventBridge, and Event-Driven Processing

S3 can initiate downstream processing when objects are created, removed, or otherwise trigger supported events.

This allows applications to respond to storage changes without continuously polling a bucket.

### Common integration options

| Integration        | Typical use                                                |
| ------------------ | ---------------------------------------------------------- |
| Amazon SQS         | Buffer work for asynchronous consumers                     |
| AWS Lambda         | Process objects immediately after upload                   |
| Amazon SNS         | Fan out notifications to subscribers                       |
| Amazon EventBridge | Route events using flexible rules and connect AWS services |

Native S3 event notifications support selected destinations, including Lambda, SQS, and SNS. Amazon EventBridge integration provides a broader event-routing model.

### Example architecture

A document processing service might work as follows:

* A client uploads a document to S3.

* S3 emits an object-created event.

* EventBridge routes the event to the appropriate target.

* A processing function extracts metadata or performs validation.

* The result is written to another object key or a separate storage location.

### Reliability considerations

Event-driven systems should account for duplicate notifications, retries, delayed processing, and partial failures. S3 notifications are delivered at least once, and their ordering is not universally guaranteed.

Applications should therefore use idempotent processing, avoid assuming exactly-once delivery, and design clear handling for failed events.

### 6.8 S3 Select Alternatives and Query-Oriented Access Patterns

S3 is primarily an object storage service, not a general-purpose database. Querying large collections of objects efficiently requires an appropriate data format and query architecture.

### Understanding S3 Select

S3 Select historically provided a way to retrieve subsets of data from supported objects using SQL expressions. It supported formats such as CSV, JSON, and Parquet, subject to specific feature limitations.

Important: S3 Select is no longer available to new customers. Existing customers should review current AWS service documentation and consider supported alternatives when designing new architectures.

### Common alternatives

![Creating a Data Lake By Using AWS S3, Glue, and Athena | by Ali Atakan | Medium](https://images.openai.com/static-rsc-4/TOBBU2jYVPRONyfpWoZvBt1a7K0nsMaPcvJxw2h7qiPQXXN2wZHxiZz5t_rj4k39kF9-1yZsTxfnGI7P-TrDeRMOFX3DzUJg0bmXBOHQ-mKoeHaukeITqht8kYZPcEXKwuNx3yKF7nWYV2OQnpvx8idUZjMDTIp0ZdujAB7ZlfRCjAzGZDhpJowK_lZDUGe-?purpose=fullsize)

Amazon Athena

Runs SQL queries against data stored in S3 without requiring a provisioned database server. It is useful for logs, analytics datasets, and data lakes.

![What is Apache Parquet? Columns, Encoding, and Performance](https://images.openai.com/static-rsc-4/tEjHoduyjgoy1B2KdenVZLqJXQfdHpanZJ6T8-HGi-Ph5GdulQ0ZSSGvAUHiCUXtfInMb-vxuLN6YJ_UAthfbaUcoZ6SVf0r0CIv2-fTcxGZEH8c6fNnVb86F55ov14woAtwHBED8BkZ3yDDTSw7zVEHrGGEi1SthfJa9jqYrrQSFBZRmX_1w4MmkSutWxMF?purpose=fullsize)

Columnar formats such as Apache Parquet

Reduce unnecessary data reads for analytical workloads when only selected columns are needed. Compression and partitioning can further reduce query costs.

![DataLakeCatalog | Data solutions framework on AWS](https://images.openai.com/static-rsc-4/urZxH3vOKTOaWd3hW4UntQPTyPa_f8gAgUCInzRfyyL30ziEP7GlHkDfI4p_cqPLKl8RtytKgmLkBXx_1KCnL8SIto8joFGB7hcqnJK5tAqef0HH_7Px7CngYorEHLLWYs23FaBe56CcJBrNz0rONdT0C-0QcL4ywS1RcWTUoluN8LzES2FeXdLgJqQR7ELy?purpose=fullsize)

AWS Glue Data Catalog

Maintains table and schema metadata so analytics services can discover and query structured datasets stored in S3.

### Choosing a query architecture

For large analytical datasets, organize objects into meaningful partitions, use columnar formats when appropriate, and avoid scanning unnecessary data. For frequent low-latency transactional lookups, a database or indexing service may be more appropriate than repeatedly querying raw S3 objects.

### 6.9 Data Lake Fundamentals and Analytics Integration

A data lake is a storage architecture that centralizes structured, semi-structured, and unstructured data for processing and analysis. S3 is frequently used as its storage foundation because it supports large datasets, flexible object formats, and integration with AWS analytics services.

### Common data lake layers

Raw layer

Original files and ingested records retained with minimal transformation.

Processed layer

Validated, cleaned, transformed, and standardized datasets.

Curated layer

Analytics-ready datasets organized for reporting and consumption.

### AWS services commonly used with S3 data lakes

* AWS Glue: Data cataloging and ETL processing.

* Amazon Athena: Serverless SQL analytics.

* Amazon Redshift: Data warehousing and analytics.

* Amazon EMR: Managed big-data processing frameworks.

* AWS Lake Formation: Centralized data lake governance and access management.

* Amazon Kinesis and Amazon Data Firehose: Streaming ingestion into storage and analytics destinations.

### Data lake design considerations

A well-designed data lake requires more than placing files in buckets. Important considerations include schema evolution, partition strategy, file sizes, metadata management, encryption, fine-grained access control, retention, and cost monitoring.

For example, partitioning event data by date can make queries more efficient, while storing huge numbers of tiny files can increase metadata overhead and reduce query efficiency.

### 6.10 Using Pulumi to Model Advanced S3 Architectures

Pulumi allows advanced S3 infrastructure to be defined, reviewed, and managed in Python.

Common resources include:

* `aws.s3.Bucket` for bucket configuration.

* `aws.s3.BucketVersioning` for versioning.

* `aws.s3.BucketReplicationConfig` for replication.

* `aws.s3.BucketLifecycleConfiguration` for lifecycle policies.

* `aws.s3.BucketObjectLockConfiguration` for Object Lock settings.

* `aws.s3.AccessPoint` for access points.

* `aws.cloudfront.Distribution` for CloudFront delivery.

* `aws.s3.BucketNotification` for supported event notifications.

The exact resource properties depend on the Pulumi AWS provider version. Advanced configurations should be checked against the current Pulumi AWS package documentation and AWS service requirements.

### Infrastructure design principles

* Separate production, backup, and analytics responsibilities where appropriate.

* Keep buckets private by default.

* Model IAM permissions explicitly and minimize privileges.

* Treat retention and deletion controls as architectural requirements.

* Monitor replication and event-processing failures.

* Keep environment-specific settings in Pulumi configuration rather than hardcoding secrets.

* Understand which resources can be replaced or destroyed and what data-loss risks that introduces.

### Module 6 Summary

Advanced S3 architecture involves selecting the right combination of replication, access controls, retention, content delivery, event processing, and analytics integration.

The key distinctions to remember are:

* CRR and SRR address different replication and data-separation needs.

* Replication Time Control offers a defined replication-time commitment for eligible workloads, but does not replace disaster recovery planning.

* Object Lock protects object versions against deletion or overwrite according to the configured retention mode.

* Access Points and Multi-Region Access Points simplify access patterns but do not replace underlying security and replication design.

* CloudFront with OAC supports secure content delivery from a private S3 origin.

* EventBridge and S3 notifications enable event-driven processing, which must account for retries and duplicate events.

* Athena, Glue, and columnar formats provide modern approaches to querying S3 data.

* Pulumi makes these architectural decisions reproducible and maintainable as code.
