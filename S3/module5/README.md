### Module 5 — S3 Application Integration and Data Access

Goal: Connect applications to Amazon S3 securely and efficiently using Python, Boto3, temporary credentials, presigned URLs, and event-driven architectures.

Amazon S3 is commonly used as the storage layer behind web applications, APIs, data-processing pipelines, backup systems, and content delivery platforms. The key architectural principle is to let applications access S3 through narrowly scoped permissions while avoiding unnecessary data transfer through application servers.

### 5.1. AWS SDK for Python (Boto3)

Boto3 is the official AWS SDK for Python. It lets Python applications interact with AWS services programmatically, without manually constructing HTTP requests or signing API calls.

The two main S3 interfaces are:

* Client: Provides low-level access to S3 API operations.

* Resource: Provides a higher-level, object-oriented interface where supported.

For most production applications, the Boto3 client is a good default because its operations closely correspond to the S3 API and expose detailed request parameters.

### Common S3 operations

| Operation                | Boto3 method             | Purpose                                          |
| ------------------------ | ------------------------ | ------------------------------------------------ |
| Create a bucket          | create_bucket()          | Create an S3 bucket                              |
| List objects             | list_objects_v2()        | Retrieve objects under a prefix                  |
| Upload a file            | upload_file()            | Upload a local file                              |
| Download a file          | download_file()          | Download an object                               |
| Read an object           | get_object()             | Retrieve object data and metadata                |
| Delete an object         | delete_object()          | Delete an object or create a delete marker       |
| Inspect an object        | head_object()            | Retrieve metadata without downloading the body   |
| Generate a presigned URL | generate_presigned_url() | Grant temporary access to a particular operation |

Application code should generally use Boto3 for object operations, while Pulumi manages the underlying infrastructure, such as buckets, bucket policies, encryption, and event destinations.

### Credential management

Boto3 uses a credential provider chain to discover AWS credentials. Depending on the environment, credentials may come from:

* An AWS CLI profile on a developer's workstation.

* Environment variables.

* An IAM role attached to an Amazon EC2 instance.

* An ECS task role.

* An EKS workload identity mechanism.

* An AWS Lambda execution role.

* AWS IAM Identity Center or another supported credential provider.

For production workloads, prefer temporary credentials supplied by an IAM role or workload identity mechanism.

Avoid embedding access keys in source code, container images, configuration files committed to Git, or frontend JavaScript.

### 5.2. IAM roles and temporary credentials

Applications need permission to perform S3 operations. AWS Identity and Access Management (IAM) determines which actions an identity can perform on which resources.

A typical application separates permissions into two categories:

* Backend permissions: Allow the API to create presigned URLs, inspect objects, or perform administrative operations.

* Client permissions: Allow a browser or mobile application to perform only the operations authorized by a presigned URL.

These permissions should not be confused. A browser uploading through a presigned URL does not need its own AWS credentials.

### Example: Backend IAM permissions

A backend that uploads and downloads objects in a specific bucket might need permissions such as:

* `s3:PutObject` for uploads.

* `s3:GetObject` for downloads.

* `s3:AbortMultipartUpload` for aborting incomplete multipart uploads.

* `s3:ListBucket` only if the application needs to list objects.

The permissions should target the relevant bucket and object ARN patterns, rather than granting unrestricted access to all S3 resources.

For example, `s3:ListBucket` applies to a bucket ARN, whereas `s3:GetObject` and `s3:PutObject` apply to object ARNs.

A further distinction matters when generating presigned URLs: the URL does not grant more permission than the signing identity possesses. The requested operation must be authorized for that identity, and the resulting request must also satisfy applicable bucket policies, encryption requirements, and other access controls.

### Temporary credentials and workload identity

Temporary credentials consist of an access key ID, secret access key, and session token. They expire, reducing the risks associated with long-lived credentials.

For workloads running on AWS, use the appropriate service identity:

| Environment       | Preferred identity mechanism                              |
| ----------------- | --------------------------------------------------------- |
| EC2               | IAM instance profile                                      |
| ECS               | ECS task role                                             |
| Lambda            | Lambda execution role                                     |
| EKS               | EKS Pod Identity or IAM Roles for Service Accounts (IRSA) |
| Local development | AWS CLI profile or IAM Identity Center                    |

Pulumi can provision the relevant IAM roles and policies. The application then obtains credentials through its runtime environment rather than storing them in the codebase.

### 5.3. Direct uploads and presigned URLs

A common web application needs to accept files from a browser. There are two main approaches.

### Approach A — Upload through the backend

Browser

FastAPI backend

Amazon S3

The backend receives the entire file and forwards it to S3.

Advantages: Centralized processing and validation.

Trade-offs: Higher backend bandwidth usage, memory or temporary-disk requirements, and potentially longer request durations.

### Approach B — Upload directly using a presigned URL

Browser

FastAPI backend — requests a presigned URL

Browser uploads directly to S3

The backend authorizes the upload and returns a temporary URL. The browser sends the file directly to S3.

Advantages: Less backend data transfer, better scalability for large files, and reduced application-server load.

Trade-offs: Requires careful URL handling, S3 CORS configuration, and a reliable mechanism for validating uploaded content.

For many file-heavy applications, the second approach is preferable.

### How a presigned URL works

A presigned URL is a time-limited URL containing a cryptographic signature that authorizes a particular S3 request.

It typically specifies:

* The bucket and object key.

* The HTTP operation, such as `PUT` or `GET`.

* The signing identity.

* The expiration time.

* Any signed request parameters or headers.

A presigned URL is a bearer capability: anyone who obtains it may be able to use it until it expires or its underlying authorization becomes invalid.

Treat it like a temporary secret. Avoid logging complete URLs, exposing them to unrelated users, or placing them in publicly accessible analytics events.

### Generating a presigned upload URL with Boto3

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    region_name="us-east-1",
    config=Config(signature_version="s3v4"),
)

def create_upload_url(
    bucket: str,
    object_key: str,
    content_type: str,
) -> str:
    return s3.generate_presigned_url(
        ClientMethod="put_object",
        Params={
            "Bucket": bucket,
            "Key": object_key,
            "ContentType": content_type,
        },
        ExpiresIn=300,
        HttpMethod="PUT",
    )
```

This example generates a URL valid for five minutes, subject to the signing credentials and applicable policies remaining valid.

The client must send the expected `Content-Type` header when making the `PUT` request because it was included in the signed parameters.

The URL's expiration is not an absolute guarantee that it will remain usable for the full five minutes. For example, temporary credentials can expire sooner, and a policy change can invalidate access.

### Presigned downloads

The same mechanism can authorize a temporary download:

```python
download_url = s3.generate_presigned_url(
    ClientMethod="get_object",
    Params={
        "Bucket": "my-private-bucket",
        "Key": "documents/report.pdf",
    },
    ExpiresIn=300,
)
```

This approach allows a private bucket to serve files to authorized users without making the objects publicly readable.

### Important security limitations

A presigned URL does not automatically enforce every business rule an application may require.

For example, checking a filename extension or declared content type in FastAPI does not prove that the uploaded file contains the expected data. Likewise, a simple presigned `PUT` URL does not provide a universal, application-defined maximum upload size.

Depending on the requirements, consider:

* Generating unpredictable object keys on the server.

* Restricting the signing identity to an allowed object prefix.

* Using presigned POST policies when policy-enforced upload constraints are needed.

* Validating file size, file signatures, and actual content after upload.

* Keeping untrusted uploads quarantined until validation succeeds.

* Using short expirations and carefully limiting the URL's distribution.

### 5.4. Multipart uploads and large-file transfers

S3 supports multipart upload, which divides a large object into smaller parts that can be uploaded independently.

Instead of transmitting one large request, the client uploads individual parts and then completes the upload. If a part fails, it can be retried without retransmitting every other part.

The main stages are:

* Initiate a multipart upload.

* Upload individual parts.

* Collect each part's ETag and part number.

* Complete the upload using the required part information.

If the upload is abandoned, the application should abort it to release associated resources.

### Why multipart upload matters

* Parallelism: Multiple parts can be uploaded concurrently.

* Retry efficiency: Failed parts can be uploaded again.

* Large files: Supports large-object transfers within S3's multipart limits.

* Resumability: Applications can preserve upload state and resume unfinished transfers if they retain the necessary part information.

Boto3's `upload_file()` and `upload_fileobj()` support managed transfers and can automatically use multipart upload based on transfer configuration.

For example:

```python
from boto3.s3.transfer import TransferConfig

config = TransferConfig(
    multipart_threshold=16 * 1024 * 1024,
    multipart_chunksize=8 * 1024 * 1024,
    max_concurrency=4,
)

s3.upload_file(
    "large-video.mp4",
    "my-private-bucket",
    "uploads/large-video.mp4",
    Config=config,
)
```

The threshold determines when multipart upload is used, and the chunk size and concurrency affect throughput and resource consumption. These values are illustrative and should be tuned for the workload.

For browser-to-S3 uploads, a backend can orchestrate multipart upload by issuing presigned URLs for individual parts. The browser then transfers each part directly to S3.

Incomplete multipart uploads can incur storage charges. A lifecycle rule using `AbortIncompleteMultipartUpload` can clean up abandoned uploads automatically.

### 5.5. Object metadata, content types, and tagging

S3 objects can carry several kinds of information that influence how applications handle, organize, and process them.

### Object metadata

S3 distinguishes between system-defined metadata and user-defined metadata.

* System-defined metadata: Includes properties such as content length, content type, last-modified time, and ETag.

* User-defined metadata: Custom key-value information supplied by the application, typically using `x-amz-meta-` headers.

* Object tags: A separate set of key-value pairs useful for lifecycle rules, access-control conditions, and cost allocation.

For example, a document might have:

| Property        | Example                        |
| --------------- | ------------------------------ |
| Object key      | uploads/tenant-42/document.pdf |
| Content type    | application/pdf                |
| Custom metadata | source=customer-portal         |
| Object tags     | classification=unreviewed      |

Metadata is useful for describing an object, but it should not be treated as authoritative proof of the object's contents. An untrusted client may be able to supply misleading metadata during upload.

Object tags are particularly useful when storage management depends on business classifications. For example, lifecycle rules can target objects tagged `retention=temporary`.

Changing object metadata or tags requires appropriate permissions and may involve additional API requests. For existing objects, replacing metadata generally requires copying the object with the appropriate metadata directives.

### Content type and browser behavior

The `Content-Type` header describes the media type of the object, such as `image/png` or `application/pdf`. It helps browsers and other clients decide how to handle downloaded content.

Applications should not blindly trust the declared content type. A malicious client can label an executable file as an image. Where file validation matters, inspect the actual content and use an appropriate validation or scanning process.

For potentially dangerous user uploads, consider serving content from a separate origin and using download-oriented response headers where appropriate.

### 5.6. CORS for browser-based uploads

Cross-Origin Resource Sharing (CORS) is a browser security mechanism that determines whether frontend JavaScript from one origin can make certain cross-origin requests and read their responses.

Suppose your application runs at `https://app.example.com` and uploads files to an S3 bucket. The browser may send a preflight `OPTIONS` request to check whether the intended method and headers are permitted.

An S3 CORS configuration defines:

* Allowed origins: Which browser origins may make permitted cross-origin requests.

* Allowed methods: Such as `GET`, `PUT`, and `POST`.

* Allowed headers: Such as `Content-Type` and headers required by the upload protocol.

* Exposed headers: Response headers the browser is allowed to read.

* Max age: How long the browser may cache the preflight result.

A conceptual configuration for a direct-upload frontend might look like this:

```python
cors_configuration = {
    "CORSRules": [
        {
            "AllowedOrigins": [
                "https://app.example.com"
            ],
            "AllowedMethods": [
                "GET",
                "PUT",
                "POST"
            ],
            "AllowedHeaders": [
                "content-type",
                "x-amz-*"
            ],
            "ExposeHeaders": [
                "ETag"
            ],
            "MaxAgeSeconds": 300,
        }
    ]
}
```

This configuration can be supplied to the S3 bucket's CORS configuration through Pulumi or the AWS API.

The allowed origins and headers should match the application's actual needs. Avoid wildcard origins for a production application when a specific origin is appropriate.

CORS is not authorization. A non-browser client can send requests without enforcing browser CORS rules. S3 IAM policies, bucket policies, presigned URL signatures, and application-level checks remain responsible for controlling access.

### 5.7. S3 event notifications and EventBridge

Applications frequently need to respond when an object is created, deleted, or otherwise changed.

S3 can publish event notifications to supported destinations, including:

* Amazon SQS: Queue object events for asynchronous processing.

* Amazon SNS: Fan out notifications to subscribers.

* AWS Lambda: Trigger application code in response to supported events.

* Amazon EventBridge: Route S3 events to supported targets using event rules.

The architecture can look like this:

Amazon S3

Object-created event

Amazon EventBridge

Filter and route matching events

Lambda

Validate or process files

SQS

Queue processing jobs

### Direct notifications versus EventBridge

| Feature                | Direct S3 notifications                    | S3 with EventBridge                                |
| ---------------------- | ------------------------------------------ | -------------------------------------------------- |
| Destinations           | Supported SQS, SNS, and Lambda targets     | A broader set of event targets through EventBridge |
| Filtering              | Event types and key prefixes/suffixes      | Event patterns with additional filtering options   |
| Routing                | Direct delivery to configured destinations | Centralized rules and routing                      |
| Operational complexity | Often simpler for one destination          | Useful for multiple event-driven workflows         |

Direct notifications are a good choice for straightforward integrations. EventBridge becomes more useful when several services need different subsets of events.

S3 event notifications are delivered at least once, and duplicate or out-of-order events can occur. Consumers should therefore be idempotent and should not assume events arrive exactly once or in object-version order.

An object-created event should also not be treated as proof that an upload has passed business validation or security scanning.

### 5.8. Retry behavior, idempotency, and error handling

Distributed applications must account for transient network failures, throttling, interrupted transfers, and ambiguous request outcomes.

Boto3 uses Botocore's retry mechanisms to handle supported transient failures. Retry behavior can be configured through a client configuration or environment variables.

For example:

```python
import boto3
from botocore.config import Config

s3 = boto3.client(
    "s3",
    config=Config(
        retries={
            "mode": "standard",
            "max_attempts": 5,
        }
    ),
)
```

The retry settings should be selected according to the SDK's documented semantics and the application's latency requirements. Retries can increase total request duration, so they should be coordinated with application-level timeouts and retry policies.

### Common errors

| Error or condition    | Typical interpretation                                                             |
| --------------------- | ---------------------------------------------------------------------------------- |
| AccessDenied          | IAM, bucket policy, KMS, or other access restrictions                              |
| NoSuchKey             | Requested object key does not exist or is inaccessible under the expected workflow |
| NoSuchBucket          | Bucket name is incorrect or the bucket is absent                                   |
| SlowDown              | Request rate or service conditions require backoff                                 |
| ExpiredToken          | Temporary credentials have expired                                                 |
| SignatureDoesNotMatch | Request signing, signed headers, region, or credentials do not match               |
| Network timeout       | The request may have failed, or its outcome may be unknown                         |

An important distinction is that a timeout does not necessarily mean an operation failed. An upload might have completed on S3 even if the client never received the response.

### Idempotency

An operation is idempotent when repeating it has the same intended effect as performing it once.

For example, uploading the same bytes to the same unversioned object key can produce the same current object state, but repeating the operation on a versioned bucket can create additional versions. Similarly, triggering downstream processing twice can cause duplicate work.

Useful strategies include:

* Assigning stable application-level identifiers to uploads.

* Recording processing status in a database.

* Using object version IDs where version-specific processing matters.

* Checking existing processing records before repeating side effects.

* Using queue deduplication mechanisms where appropriate.

* Applying bounded exponential backoff with jitter to retryable failures.

For file-processing pipelines, use a durable processing record keyed by an appropriate combination of object identity and version. Do not rely on an S3 ETag as a universal content hash: multipart uploads and certain encryption configurations mean it is not always equivalent to an MD5 digest.

### 5.9. Object key design and safe filenames

An S3 object key identifies an object within a bucket. Although keys often resemble file paths, S3 is fundamentally a flat object namespace. Slashes are characters used to organize key prefixes, not filesystem directory boundaries.

Good key design supports isolation, efficient listing, lifecycle management, and downstream processing.

For a multitenant application, a key structure might look like:

```text
uploads/{tenant_id}/{upload_id}/original
processed/{tenant_id}/{upload_id}/thumbnail.webp
exports/{tenant_id}/{export_id}/report.csv
```

### Design principles

* Generate keys on the server. Avoid using raw client filenames as authoritative object identifiers.

* Separate tenants. Use well-defined tenant prefixes and enforce access boundaries.

* Use stable identifiers. UUIDs or other collision-resistant identifiers can prevent accidental overwrites.

* Separate workflows. Keep raw uploads, processed files, exports, and temporary data in distinguishable prefixes or buckets.

* Plan lifecycle policies. Choose prefixes or tags that make retention rules understandable.

* Avoid path assumptions. Do not assume that S3 key normalization behaves like a local filesystem.

A client-provided filename can still be stored as metadata or in a database for display purposes. It should be handled carefully to avoid path traversal problems, misleading extensions, header injection, and unsafe content rendering.

For multitenant systems, a prefix such as `uploads/tenant-42/` is not itself a security boundary. The application's authorization logic and AWS policies must prevent access to other tenants' objects.

### 5.10. Integrating S3 with FastAPI and Pulumi

These concepts fit together naturally in a Python application architecture.

Frontend

Requests upload authorization

FastAPI backend

Authenticates user, authorizes tenant, generates presigned URL

Private S3 bucket

Receives file directly from frontend

Event-driven processing

Validate, scan, process, and update application state

Pulumi provisions the infrastructure and permissions; FastAPI handles application authorization and workflow logic.

The responsibilities should remain clearly separated:

Pulumi and Python infrastructure code

* Provisions S3 buckets, encryption, CORS, lifecycle policies, and versioning.

* Creates IAM roles and least-privilege policies.

* Configures event routing and required permissions.

* Manages environment-specific configuration.

FastAPI application

* Authenticates the user and verifies tenant-level authorization.

* Generates server-controlled object keys.

* Issues presigned URLs with appropriate expiration and request parameters.

* Records upload state and validates completed uploads.

* Coordinates post-upload processing and error handling.

S3 and downstream services

* Store objects privately.

* Enforce applicable AWS permissions and encryption requirements.

* Emit object events for asynchronous processing.

* Provide durable storage and object-version information for recovery and processing.

For a production implementation, use the S3 `HeadObject` API to inspect completed uploads, but remember that metadata checks alone do not validate file contents. If uploaded files are untrusted, use a quarantine or pending state until content validation and any required malware scanning are complete.

### Key takeaways

* Boto3 provides programmatic S3 access; Pulumi manages the infrastructure.

* IAM roles and temporary credentials are preferable to long-lived application access keys.

* Presigned URLs let clients upload and download objects without receiving AWS credentials.

* Multipart uploads improve the efficiency and resilience of large transfers.

* CORS enables permitted browser requests but does not authorize access.

* Event-driven workflows should tolerate duplicate and out-of-order notifications.

* Idempotency, server-generated object keys, and content validation are essential for reliable applications.

* Private buckets, least privilege, and careful handling of presigned URLs are foundational security practices.

These concepts provide the application-integration foundation for building secure file uploads, document management systems, media platforms, and event-driven data-processing services on AWS S3.
