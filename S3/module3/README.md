### Module 3 — S3 Security and Access Control

AWS S3 · Pulumi with Python · Security architecture and access management

### Module overview

Amazon S3 security is built around controlling who can access data, which operations they can perform, under what conditions access is permitted, and how data is protected at rest and in transit.

A secure S3 architecture combines AWS Identity and Access Management (IAM), S3 bucket policies, S3 Block Public Access, encryption, network controls, and resource ownership settings. These mechanisms complement one another; no single setting provides complete protection.

Using Pulumi, these controls can be defined as code, reviewed before deployment, consistently applied across environments, and tracked alongside application infrastructure.

### 3.1 — IAM identities, policies, and least privilege

AWS IAM controls access to AWS services through identities, permissions, and policy evaluation.

### IAM identities

IAM users

IAM users represent persistent identities in an AWS account. They can have long-term credentials, although workloads generally benefit from temporary credentials through IAM roles instead.

IAM roles

Roles provide temporary credentials to trusted principals, such as EC2 instances, Lambda functions, applications running in containers, and users accessing another AWS account.

IAM policies

Policies define allowed or denied actions on specific resources, optionally subject to conditions. They can be attached to identities or, in resource-based form, directly to S3 buckets and other supported resources.

### Understanding S3 permissions

S3 permissions are expressed as actions, resources, and conditions. Common actions include:

| Action                 | Purpose                                                               |
| ---------------------- | --------------------------------------------------------------------- |
| s3:ListBucket          | Lists objects in a bucket                                             |
| s3:GetObject           | Reads an object                                                       |
| s3:PutObject           | Uploads an object or creates a new object version                     |
| s3:DeleteObject        | Deletes an object or creates a delete marker, depending on versioning |
| s3:GetObjectVersion    | Reads a specific object version                                       |
| s3:DeleteObjectVersion | Permanently deletes a specified version                               |

Bucket-level and object-level permissions use different resource ARNs.

For example, `s3:ListBucket` typically applies to:

```text
arn:aws:s3:::company-private-data
```

Whereas `s3:GetObject` applies to object resources:

```text
arn:aws:s3:::company-private-data/*
```

Confusing these resource types is a common reason for unexpected `AccessDenied` errors.

### The principle of least privilege

Least privilege means granting only the permissions necessary for a principal to perform its intended function.

A read-only application might need `s3:GetObject` for a particular prefix but not `s3:PutObject`, `s3:DeleteObject`, or permissions to change the bucket policy.

A well-designed policy should:

* Limit actions to the minimum required set.

* Scope resources to the necessary bucket and object prefixes.

* Use conditions when additional restrictions are appropriate.

* Avoid broad permissions such as `s3:*` unless there is a specific administrative need.

* Separate application permissions from infrastructure-management permissions.

The identity that runs Pulumi also needs AWS permissions to create and configure resources. Those deployment permissions should be separate from the runtime permissions granted to applications that use the resulting bucket.

### 3.2 — Identity-based policies versus bucket policies

S3 supports both identity-based and resource-based permissions. Understanding the difference is fundamental to designing access boundaries.

Identity-based policy

Attached to an IAM user, group, or role. It describes what that identity can do, such as read objects from a specific bucket.

Question answered: What is this identity allowed to do?

Bucket policy

Attached to an S3 bucket. It defines which principals may access the bucket and its objects, and can impose additional restrictions on requests.

Question answered: Who can access this bucket, and under what conditions?

### How policy evaluation works

AWS authorization depends on the identity making the request, the resource involved, the applicable policies, and the request context.

The important general rules are:

* An applicable explicit `Deny` overrides an `Allow`.

* An `Allow` must exist through the relevant authorization mechanisms for the request to succeed.

* The absence of an applicable `Allow` normally means access is denied.

* Service control policies (SCPs), permissions boundaries, session policies, and other applicable controls can further restrict permissions.

* Cross-account access generally requires authorization from both the requesting account's side and the resource-owning account's side.

A bucket policy does not automatically grant permissions to every principal mentioned in a broader IAM policy, and an identity policy does not override an explicit denial in a bucket policy.

### Example: Allowing an application role to read objects

The following policy grants an application role permission to retrieve objects from a designated bucket. It is an identity-based policy fragment, so it would be attached to the appropriate IAM role.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::company-private-data/*"
    }
  ]
}
```

This policy does not grant permission to list the bucket. If the application must discover object keys, it may also need `s3:ListBucket` on the bucket ARN.

Policy design should reflect application behavior rather than granting broad permissions preemptively.

### Explicit-deny guardrails

A bucket policy can enforce a restriction that applies even when a principal has a broader identity-based `Allow`.

For example, an explicit denial can prevent requests over insecure transport. Similar guardrails can restrict access to approved networks, encryption requirements, or other supported request conditions.

Care is necessary when writing `Deny` statements: a condition that matches legitimate administrative or recovery requests can lock out intended users. Policies should be evaluated against the actual principals and access paths that the architecture requires.

### 3.3 — S3 Block Public Access

S3 Block Public Access provides account-level and bucket-level controls designed to prevent public exposure.

It consists of four independent settings:

| Setting               | Purpose                                                                             |
| --------------------- | ----------------------------------------------------------------------------------- |
| BlockPublicAcls       | Rejects attempts to apply new public ACLs                                           |
| IgnorePublicAcls      | Prevents public ACL grants from taking effect                                       |
| BlockPublicPolicy     | Rejects bucket policies that S3 identifies as public                                |
| RestrictPublicBuckets | Restricts access to buckets with public policies, subject to AWS-defined exceptions |

These settings protect different authorization mechanisms. They are not interchangeable.

For most private application buckets, enabling all four at the bucket level is an appropriate baseline. An organization can also establish account-level controls to provide a stronger default across its storage resources.

### What Block Public Access does not do

Block Public Access is not a replacement for IAM or careful policy design.

It does not automatically remove every unnecessary permission from an otherwise private bucket policy. Nor does it prevent every possible form of unintended access through an authorized role, a compromised credential, a presigned URL, or a separate data-sharing mechanism.

A presigned URL, for example, allows a holder to use a signed request within its permitted scope and validity period. It should be treated as a temporary bearer credential.

Recommended default: Keep buckets private, enable all four Block Public Access settings, and grant external access only through a deliberately designed authorization mechanism.

### 3.4 — Object Ownership and ACLs

S3 supports access control lists (ACLs) as a legacy mechanism for assigning certain permissions to buckets and objects. Modern architectures generally prefer IAM and resource policies.

### Bucket Owner Enforced

The recommended default for most new workloads is Bucket Owner Enforced Object Ownership.

With this setting:

* ACLs are disabled for the bucket.

* The bucket owner owns the objects.

* Access is managed through IAM and bucket policies.

* Upload requests that attempt to set unsupported ACLs may fail.

This simplifies access management, especially when multiple applications or accounts upload data into a shared storage location.

Some older integrations still expect ACL-based behavior. Those integrations need to be assessed before changing ownership settings. If ACLs are disabled, clients should avoid sending ACL headers unless the particular supported request behavior permits them.

Object Ownership is particularly important for cross-account uploads, where ownership and the ability to manage uploaded objects can otherwise become complicated.

### 3.5 — Server-side encryption

Encryption at rest protects stored object data against certain forms of unauthorized access to underlying storage. S3 supports multiple server-side encryption approaches, each with different operational and key-management characteristics.

![python - boto encryption key with amazon s3 - Stack Overflow](https://images.openai.com/static-rsc-4/5-Qowi-RmTKzjmTFeyZy2Pr6j_3ZLSu4CXmEINt1S4zESEdmohFuVX-G4klZ4PGZzWTsmnMmh4Byx9_BbRyYhywXKKnJby5OXiDQL8QVVaY9-Dr8arLgxIXRAySm4WBjJqP_evIUegkmTZ_NIjWk7cVn7kCcySsPTbafnTwgnf3crZQZ4Ew32T8Gp4eODhpa?purpose=fullsize)

SSE-S3 — S3-managed encryption

Amazon S3 automatically encrypts objects at rest using keys managed by S3. This is the default encryption behavior for new S3 uploads. It minimizes key-management overhead and is suitable for many general-purpose storage workloads.

![QA Learning Platform](https://images.openai.com/static-rsc-4/kyQM84kd9Be6zYo3tPwKyUYjjlxCeWYafWoqZGfMBwKL7odqHvN9e06KlYJ-txYXFUsaYgyck79fDvpR5FxFVqHYgMk-NhJptLKNDVncZXiFmUNkRyiJ-xmIgCOPvhDPjoRtkvctkF8bBa8_YABZQahs5xVboIBHrUnwlBHnlIWBreqf6YQyRFRY8n_37lpr?purpose=fullsize)

SSE-KMS — AWS KMS encryption

S3 uses AWS Key Management Service (KMS) to protect data encryption keys. Depending on the key choice, organizations gain additional control over key policies, grants, auditing, and lifecycle management. Customer-managed keys support more granular administrative control but add cost and operational responsibilities.

![Amazon S3 dual-layer server-side encryption with AWS KMS (DSSE-KMS)](https://images.openai.com/static-rsc-4/vHZ5GVMd7DHChl5lEL15r8dmWt8sVqAg9CcJPFLyhi7e8UMvx7PowiIp3v1NNtTcQeWrEUBk8spLf7Q16QSWQAUqqAZ5Tsmxe8sTy2yDksqxBMShihb3NpNsP2xX30MW3CKiqC5k2bo1re4Oja0T7lRgTwBduviXsvNw9ksOwg1TkWZFypFE4k1Ho4onV0P9?purpose=fullsize)

DSSE-KMS — Dual-layer server-side encryption

Provides two independent layers of server-side encryption using AWS KMS-related key management mechanisms. It is designed for workloads requiring the additional protection of dual-layer encryption, subject to service and feature compatibility requirements.

### Comparing the encryption options

| Characteristic                             | SSE-S3 | SSE-KMS               | DSSE-KMS                                      |
| ------------------------------------------ | ------ | --------------------- | --------------------------------------------- |
| Encryption at rest                         | Yes    | Yes                   | Yes, dual layer                               |
| Customer-managed key policy control        | No     | Available             | Available through supported KMS configuration |
| KMS permissions required for object access | No     | Yes, where applicable | Yes                                           |
| Additional KMS request costs               | No     | Generally applicable  | Generally applicable                          |
| Operational complexity                     | Low    | Moderate              | Higher                                        |

SSE-S3 is sufficient for many workloads. SSE-KMS becomes valuable when key-management controls, auditability, or separation of duties are requirements. DSSE-KMS should be selected when its additional protection addresses a specific requirement rather than simply because it offers another encryption option.

S3 also supports client-side encryption, where an application encrypts data before sending it to S3. This shifts more responsibility for encryption, key custody, and recovery to the application.

### Encryption in transit

Encryption at rest does not protect data while it travels between clients and AWS endpoints. HTTPS using TLS protects requests and responses in transit.

A bucket policy can deny requests where the AWS condition key `aws:SecureTransport` is `false`. This is a useful defense-in-depth measure, but clients should already be configured to use HTTPS.

### 3.6 — AWS KMS key policies and encryption permissions

AWS Key Management Service controls access to encryption keys. When a bucket uses SSE-KMS, successful S3 access can depend on permissions in both S3 and KMS.

### How KMS authorization works

For a typical SSE-KMS workflow:

* Uploading an object generally requires `kms:GenerateDataKey` on the relevant KMS key.

* Downloading an object generally requires `kms:Decrypt`.

* Multipart uploads using SSE-KMS may require additional key permissions, including `kms:Decrypt`, depending on the operation.

* The KMS key policy must permit the relevant access, directly or through a supported delegation mechanism.

Having `s3:GetObject` does not necessarily mean a principal can decrypt the object. Conversely, KMS permissions alone do not grant permission to retrieve the object from S3.

### AWS-managed versus customer-managed KMS keys

The `aws/s3` AWS-managed KMS key is convenient when standard KMS-backed encryption is required without managing a dedicated key policy.

Customer-managed KMS keys provide more control over key policies, grants, administrative separation, and lifecycle. They also require additional care: disabling or deleting a key can make encrypted data inaccessible.

For cross-account access to SSE-KMS objects, customer-managed keys are generally required when the external account must be authorized to use the key. The S3 permissions, key policy or grants, and relevant IAM permissions must all align.

### KMS considerations in Pulumi

Pulumi can manage KMS keys, aliases, policies, and S3 bucket encryption settings as infrastructure resources. Key policies should be deliberately designed to preserve administrative access and avoid circular dependencies between the key, its policy, and other resources.

A production design should also consider:

* Key rotation and key administration.

* Separation between key administrators and data readers.

* CloudTrail auditing of relevant KMS activity.

* Regional requirements and replication compatibility.

* Recovery implications before scheduling key deletion.

### 3.7 — VPC endpoints and network-based restrictions

S3 is a regional AWS service, but applications running in private VPC subnets can access it without requiring a public IP address for every workload.

A VPC endpoint provides a private network path to supported AWS services.

### Gateway endpoints versus interface endpoints

| Feature        | Gateway endpoint                                    | Interface endpoint                                                |
| -------------- | --------------------------------------------------- | ----------------------------------------------------------------- |
| Implementation | Route-table target                                  | Private network interfaces                                        |
| Typical S3 use | Common choice for VPC workloads                     | Useful for supported connectivity patterns requiring PrivateLink  |
| Pricing model  | No additional endpoint charge for gateway endpoints | Endpoint and data-processing charges may apply                    |
| Routing        | Uses route tables                                   | Uses endpoint network interfaces and applicable DNS configuration |

Gateway endpoints for S3 are commonly used by EC2 instances, ECS tasks, and other workloads inside a VPC. They can reduce reliance on NAT gateways for S3 access and provide a basis for network-related access restrictions.

### Restricting access through endpoint conditions

A bucket policy can use the `aws:SourceVpce` condition key to restrict requests to a particular VPC endpoint.

This is powerful but requires caution. A blanket denial of requests not coming through a specified endpoint can also block legitimate access through the AWS console, administrative tooling, other VPCs, or recovery processes.

A sound architecture identifies all intended access paths before enforcing network restrictions. Administrative access and cross-account integrations should be considered explicitly.

### 3.8 — S3 access points

S3 access points provide named endpoints with individual policies for accessing data in a shared bucket.

They are useful when multiple teams or applications need different access boundaries to the same underlying data.

For example, an analytics team might require read-only access to a dataset, while an ingestion service needs write access to a designated prefix. Access points can simplify the policy structure by giving each workload a separate access endpoint and policy.

Important characteristics include:

* Each access point has its own policy and network-origin configuration.

* Access points refer to an underlying S3 bucket rather than storing separate objects.

* Access point policies work alongside the bucket's authorization controls.

* Access points do not automatically override bucket policies or other applicable restrictions.

* VPC-only access points can help establish network-based access boundaries.

Access points are especially valuable when one large bucket serves many applications and policy complexity becomes difficult to maintain.

### 3.9 — Cross-account S3 access

Cross-account access allows a principal in one AWS account to use a bucket owned by another account, subject to the relevant permissions.

A typical architecture separates the storage account from the application account. This can reduce the impact of compromised application credentials and centralize data governance.

The main elements are:

* Trust and identity: The application assumes an appropriately authorized IAM role.

* Identity permissions: The role's policies allow the required S3 operations.

* Bucket policy: The bucket owner authorizes the external principal where required.

* Encryption permissions: If SSE-KMS uses a customer-managed key, the relevant KMS authorization must also be configured.

* Ownership: Bucket Owner Enforced simplifies object ownership by making the bucket owner the owner of uploaded objects.

Cross-account policies should identify the intended account or role instead of granting access to a broad set of principals.

For large multi-account environments, AWS Organizations, SCPs, and centralized security controls can complement individual bucket policies.

### 3.10 — Implementing S3 security with Pulumi and Python

Pulumi allows security controls to be declared alongside the S3 resources they protect. The infrastructure code becomes a reviewable description of the intended security posture.

The primary resource types commonly used in a secure S3 design include:

| Pulumi AWS resource                              | Purpose                                          |
| ------------------------------------------------ | ------------------------------------------------ |
| aws.s3.BucketV2                                  | Defines the S3 bucket                            |
| aws.s3.BucketPublicAccessBlock                   | Configures the four Block Public Access settings |
| aws.s3.BucketOwnershipControls                   | Configures Object Ownership                      |
| aws.s3.BucketServerSideEncryptionConfigurationV2 | Defines default server-side encryption           |
| aws.s3.BucketPolicy                              | Applies bucket-level authorization rules         |
| aws.iam.Role                                     | Defines a workload or application role           |
| aws.iam.RolePolicy                               | Defines inline permissions for a role            |
| aws.kms.Key                                      | Defines a customer-managed KMS key when required |

Resource names and arguments depend on the version of the Pulumi AWS provider being used, so implementation should follow the documentation for the installed provider version.

### Configuration and separation of environments

Security configuration should not be hard-coded in ways that accidentally make development and production environments identical when their requirements differ.

Pulumi stacks can represent different environments, with configuration controlling settings such as:

* Environment-specific bucket naming.

* Whether customer-managed KMS encryption is required.

* Which application role is permitted access.

* Which VPC endpoint is authorized.

* Whether replication or additional logging is enabled.

Credentials should come from supported AWS credential providers, such as IAM roles, AWS IAM Identity Center, or locally configured profiles. Long-lived secrets should not be embedded in source code.

### Managing changes safely

Security-related infrastructure changes deserve careful review because an apparently small policy change can expose data or interrupt an application.

`pulumi preview` helps identify proposed infrastructure changes before deployment. It does not prove that every security requirement is satisfied, so policy review and validation remain necessary.

Particular attention should be given to:

* Unexpected resource replacement.

* Bucket policies containing overly broad principals.

* Changes that disable encryption or public-access protections.

* KMS key deletion or policy modifications.

* Dependencies between buckets, policies, IAM roles, and encryption keys.

### 3.11 — A layered S3 security architecture

The most reliable approach is defense in depth: multiple independent controls reduce the likelihood that a single misconfiguration exposes data.

Identity and authentication

IAM roles · Temporary credentials · Least privilege

Authorization and exposure controls

IAM policies · Bucket policies · Block Public Access

Data protection

TLS · SSE-S3 or SSE-KMS · Ownership controls

Network and organizational controls

VPC endpoints · Endpoint conditions · AWS Organizations

Auditing and governance

CloudTrail · Security monitoring · Infrastructure as code

These layers address different threats. Encryption does not replace authorization, a private bucket does not eliminate the risk of compromised credentials, and network restrictions do not guarantee that an authorized application handles data safely.

### Module summary

A secure S3 design should begin with private-by-default access, IAM least privilege, all four Block Public Access settings, Bucket Owner Enforced Object Ownership, and encryption at rest and in transit.

More advanced requirements can introduce customer-managed KMS keys, VPC endpoint restrictions, access points, and cross-account policies. Each additional control should serve a clear security or operational requirement and be managed consistently through Pulumi.

The central principle is that S3 security is an authorization and governance system, not merely a bucket configuration. Effective protection depends on the interaction between identity, resource policies, encryption, network access, and operational controls.
