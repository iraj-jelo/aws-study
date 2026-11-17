### Module 2 — Managing S3 Infrastructure with Pulumi

### 2.1 Introduction to Infrastructure as Code

Infrastructure as Code (IaC) is the practice of defining, provisioning, and managing infrastructure through code rather than creating resources manually in a cloud console.

For Amazon S3, IaC allows you to define buckets, encryption settings, versioning, access controls, lifecycle policies, and other configurations in a repeatable and version-controlled way.

Without IaC, an engineer might manually create a development bucket and then repeat the same steps for production. Over time, these environments can diverge: one bucket might have encryption enabled, another might lack versioning, and a third might accidentally allow public access.

With IaC, the desired configuration is defined once and applied consistently.

### Why use IaC for S3?

* Consistency: Apply the same security and configuration standards across environments.

* Repeatability: Recreate infrastructure reliably when needed.

* Version control: Track infrastructure changes alongside application code.

* Reviewability: Inspect proposed changes before applying them.

* Automation: Integrate infrastructure deployment into CI/CD pipelines.

* Governance: Make infrastructure configuration easier to audit and maintain.

### 2.2 Understanding Pulumi

![Pulumi Logo PNG Vector (SVG) Free Download](https://images.openai.com/static-rsc-4/AmMHN4y85QKxhHeN2npC_DidEJaLbNZF084iBdQ_J0fK2EtZaq6wzMCGvjC8N_2QjJmtCPhAjHYYSaZ-8j_CHSUZd3WYcUUJcpRKIoafKDAYvvAguhwUerpzZ7ad5kE11tcf1juwqBxkczsDu7oHM0PRogVITZgzE8TleA6bKEpno9-uuwBxA864_QRhweRS?purpose=fullsize)

Pulumi

Pulumi is an infrastructure-as-code platform that lets you define cloud resources using general-purpose programming languages, including Python, TypeScript, Go, C#, and Java.

In this course, Python is the primary language for defining AWS infrastructure.

Pulumi programs use AWS provider libraries to describe resources such as S3 buckets. Pulumi then compares the program's desired state with the state it tracks and determines which resources need to be created, updated, replaced, or deleted.

For example, an S3 bucket can be represented as a Python resource:

```python
import pulumi
import pulumi_aws as aws

bucket = aws.s3.BucketV2(
    "application-data",
    tags={
        "Environment": "dev",
        "ManagedBy": "Pulumi",
    },
)

pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
```

This program defines an S3 bucket and exports its name and ARN.

Notice that the program does not directly call an AWS API to create the bucket. Instead, it declares the desired resource, and Pulumi's engine and AWS provider handle the infrastructure operations.

The example uses `BucketV2`, a resource for managing an S3 general-purpose bucket. Modern S3 configurations can also use separate resources for versioning, encryption, public access blocking, and other settings, making those configurations more explicit.

### 2.3 Pulumi Projects, Stacks, and Configuration

Pulumi organizes infrastructure code around three important concepts: projects, stacks, and configuration.

Project

A collection of related infrastructure code. An S3 infrastructure project might define buckets, encryption, lifecycle policies, and access controls.

Stack

An independent instance of a project. A project might have `dev`, `staging`, and `prod` stacks, each with its own resources and tracked state.

Configuration

Environment-specific values supplied to the program, such as the AWS Region, retention period, bucket naming prefix, and whether versioning is enabled.

### 2.3.1 Project structure

A typical Pulumi Python project might look like this:

```text
s3-infrastructure/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── Pulumi.prod.yaml
├── requirements.txt
├── __main__.py
└── components/
    └── s3_bucket.py
```

The files serve different purposes:

* `Pulumi.yaml` defines the project name, runtime, and optional project metadata.

* `Pulumi.dev.yaml` stores configuration specific to the development stack.

* `Pulumi.prod.yaml` stores configuration specific to production.

* `requirements.txt` specifies Python dependencies.

* `__main__.py` is the main Pulumi program.

* `components/s3_bucket.py` contains reusable infrastructure definitions.

The configuration files are stack-specific. Sensitive values should be encrypted using Pulumi's secret configuration mechanism rather than stored as ordinary plaintext configuration.

### 2.3.2 Stack isolation

Stacks provide a logical boundary between environments. Each stack maintains its own resource state and configuration.

For example:

| Property            | Development                        | Production                      |
| ------------------- | ---------------------------------- | ------------------------------- |
| Stack               | dev                                | prod                            |
| Purpose             | Testing and development            | Business workloads              |
| Versioning          | May be enabled according to policy | Commonly enabled                |
| Retention           | Shorter, where appropriate         | Based on retention requirements |
| Access              | Developer and test roles           | Restricted workload roles       |
| Deployment approval | Often lightweight                  | Usually controlled              |

Separate stacks do not automatically guarantee security isolation. Stronger isolation may require separate AWS accounts, IAM permissions, policies, and deployment credentials.

### 2.3.3 Stack configuration in Python

Pulumi's `Config` object provides access to stack configuration.

```python
import pulumi

config = pulumi.Config()

environment = config.require("environment")
bucket_prefix = config.require("bucketPrefix")
versioning_enabled = config.get_bool("versioningEnabled") or False

pulumi.export("environment", environment)
pulumi.export("versioning_enabled", versioning_enabled)
```

The distinction between `require` and `get` is important:

* `require()` expects a value to exist and raises an error if it does not.

* `get()` returns `None` if a value is absent.

* `get_bool()` reads a Boolean configuration value.

* `get_int()` reads an integer configuration value.

* `require_secret()` retrieves a required secret value.

For a Boolean setting where `False` is a meaningful value, prefer an explicit default:

```python
versioning_enabled = config.get_bool("versioningEnabled")

if versioning_enabled is None:
    versioning_enabled = False
```

This makes the default behavior unambiguous.

### 2.4 AWS Provider Configuration and Credentials

Pulumi uses an AWS provider to communicate with AWS APIs. The provider determines how infrastructure operations are performed, including the target Region and credential source.

### 2.4.1 Configuring the AWS provider

An explicit provider configuration makes the intended Region visible in the infrastructure code.

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

region = config.require("awsRegion")

aws_provider = aws.Provider(
    "aws-provider",
    region=region,
)
```

Resources can then use this provider explicitly:

```python
bucket = aws.s3.BucketV2(
    "application-data",
    opts=pulumi.ResourceOptions(
        provider=aws_provider,
    ),
)
```

Explicit provider selection becomes especially useful when a program deploys resources to multiple AWS Regions or accounts.

For a small single-Region project, Pulumi can also use the default AWS provider, configured through the standard AWS and Pulumi configuration mechanisms.

### 2.4.2 Credential management

Pulumi does not eliminate the need for AWS authentication. It uses AWS credentials available through supported provider mechanisms.

Common options include:

* AWS CLI profiles.

* Environment variables.

* IAM roles attached to EC2 instances.

* IAM roles assumed through AWS STS.

* Federated credentials in CI/CD systems.

* IAM Identity Center-based authentication workflows.

For local development, a named AWS profile is often appropriate. In production automation, temporary credentials obtained through role assumption or workload identity are generally preferable to long-lived access keys.

Avoid hardcoding access keys in Python files or committing them to version control.

### 2.4.3 AWS permissions

The identity running Pulumi needs permission to create, read, update, and sometimes delete the resources defined by the program.

For S3 infrastructure, permissions may include operations associated with:

* Creating and deleting buckets.

* Reading bucket configuration.

* Managing versioning and encryption settings.

* Managing bucket policies and public access settings.

* Managing lifecycle rules.

* Reading account or Region information.

The precise permissions depend on the resources being managed. Features involving AWS KMS, replication, CloudTrail, or cross-account access introduce additional permission requirements.

A deployment identity should receive only the permissions required for its intended infrastructure responsibilities.

### 2.5 S3 Resources, Dependencies, and Outputs

Pulumi represents AWS resources as objects in a dependency graph.

The engine uses this graph to determine the correct order for resource creation, updates, and deletion.

### 2.5.1 Resource definitions

An S3 bucket is only one part of a complete storage configuration. Other settings are often represented by dedicated resources.

For example, versioning can be configured independently:

```python
bucket = aws.s3.BucketV2(
    "application-data",
)

versioning = aws.s3.BucketVersioningV2(
    "application-data-versioning",
    bucket=bucket.id,
    versioning_configuration={
        "status": "Enabled",
    },
)
```

The versioning resource depends on the bucket's ID. Pulumi recognizes that dependency and creates the bucket before configuring its versioning.

Explicit references between resources are preferable to manually hardcoding resource identifiers because they communicate dependencies directly to Pulumi.

### 2.5.2 Outputs and asynchronous values

Pulumi resource properties are frequently represented as `Output` values rather than ordinary Python strings.

For example:

```python
pulumi.export("bucket_name", bucket.id)
pulumi.export("bucket_arn", bucket.arn)
```

The bucket's actual name and ARN become available as Pulumi resolves the resource.

Outputs can also be transformed using `apply()` or combined with `pulumi.Output.all()` when derived values are needed.

This is different from conventional Python code: resource values might not be known until deployment, so they should not be treated as ordinary strings during program execution.

### 2.5.3 Resource options

`pulumi.ResourceOptions` controls how Pulumi manages a resource.

Important options include:

* `provider`: Selects the provider responsible for the resource.

* `depends_on`: Declares an explicit dependency.

* `protect`: Prevents accidental deletion through Pulumi.

* `parent`: Establishes a parent-child relationship.

* `aliases`: Helps Pulumi recognize a resource after certain naming or structural changes.

* `ignore_changes`: Tells Pulumi to ignore specified properties during updates.

These options influence lifecycle management and should be applied deliberately. For example, `protect=True` can help safeguard a production bucket, but it does not replace backups, retention policies, or AWS-level access controls.

### 2.6 Reusable S3 Components

As infrastructure grows, defining every bucket independently creates unnecessary duplication.

Pulumi supports reusable components that encapsulate resource creation and expose a stable interface to the rest of the program.

A reusable S3 component might accept:

* A logical component name.

* Environment and naming information.

* Versioning requirements.

* Encryption settings.

* Public access restrictions.

* Tags.

* Optional lifecycle configuration.

The component then creates the appropriate AWS resources.

A simplified component can look like this:

```python
import pulumi
import pulumi_aws as aws

class S3BucketComponent(pulumi.ComponentResource):
    def __init__(
        self,
        name: str,
        environment: str,
        opts: pulumi.ResourceOptions | None = None,
    ):
        super().__init__(
            "example:storage:S3BucketComponent",
            name,
            None,
            opts,
        )

        self.bucket = aws.s3.BucketV2(
            f"{name}-bucket",
            tags={
                "Environment": environment,
                "ManagedBy": "Pulumi",
            },
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.public_access_block = aws.s3.BucketPublicAccessBlock(
            f"{name}-public-access-block",
            bucket=self.bucket.id,
            block_public_acls=True,
            block_public_policy=True,
            ignore_public_acls=True,
            restrict_public_buckets=True,
            opts=pulumi.ResourceOptions(parent=self),
        )

        self.bucket_name = self.bucket.id
        self.bucket_arn = self.bucket.arn

        self.register_outputs({
            "bucket_name": self.bucket_name,
            "bucket_arn": self.bucket_arn,
        })
```

This component illustrates encapsulation and resource relationships. It is not, by itself, a complete production bucket standard: encryption, versioning, lifecycle management, policy requirements, and deletion safeguards should be added according to the workload's requirements.

The component also establishes a parent-child relationship, making the resources easier to understand in Pulumi's resource hierarchy.

### 2.6.1 Why components matter

Components are useful when an organization needs consistent storage patterns across many applications.

For example, an organization might establish a standard that all application buckets must:

* Block public access.

* Use approved encryption settings.

* Include environment and ownership tags.

* Enable versioning for important data.

* Apply approved lifecycle policies.

* Follow naming and retention conventions.

Instead of implementing these rules separately in every project, teams can reuse a shared component.

A reusable component reduces duplication, but it does not automatically guarantee compliance. Teams must also manage component versions, review changes, and apply appropriate AWS-level governance.

### 2.7 Naming Conventions and Environment-Specific Infrastructure

S3 bucket names belong to a shared namespace within an AWS partition. A bucket name must satisfy S3's naming rules and must be available when the bucket is created.

This makes naming strategy particularly important for infrastructure that is deployed repeatedly across environments.

A naming convention might include:

* Organization or application identifier.

* Environment.

* Data purpose.

* A unique suffix where required.

For example:

```text
acme-dev-application-data-a1b2c3
acme-prod-application-data-d4e5f6
```

These are illustrative names, not guaranteed to be available.

Avoid including sensitive information in bucket names because names may appear in URLs, logs, policies, and operational tooling.

### Environment-specific configuration

A single Pulumi program can support different configurations for development and production.

For example, the development stack might use:

```yaml
config:
  s3-course:environment: dev
  s3-course:awsRegion: eu-west-3
  s3-course:bucketPrefix: acme-dev
  s3-course:versioningEnabled: false
```

Production could use a different configuration:

```yaml
config:
  s3-course:environment: prod
  s3-course:awsRegion: eu-west-3
  s3-course:bucketPrefix: acme-prod
  s3-course:versioningEnabled: true
```

The project name determines the configuration namespace; `s3-course` here is an example.

The production setting is illustrative, not a recommendation to disable versioning in development universally. The appropriate settings depend on testing needs, recovery requirements, and cost considerations.

Configuration controls behavior, while the program defines how those settings map to actual AWS resources.

### 2.8 Previewing, Updating, Importing, and Destroying Infrastructure

Pulumi provides commands for managing infrastructure throughout its lifecycle.

`pulumi preview`

Calculates and displays the changes Pulumi expects to make without applying them. Reviewing the preview helps identify unexpected replacements or deletions.

`pulumi up`

Executes the planned changes and brings the managed infrastructure toward the desired state declared in the program.

`pulumi import`

Imports an existing cloud resource into Pulumi's management state. The program must subsequently represent the imported resource correctly to manage it safely.

`pulumi destroy`

Deletes resources managed by the selected stack, subject to protection settings and provider behavior. This is potentially destructive, especially for storage infrastructure.

### 2.8.1 Understanding previews and replacements

Not all infrastructure changes can be applied in place.

Some S3 properties can be updated without replacing the bucket. Other changes may require resource replacement, depending on the AWS provider's schema and the specific resource.

Replacement deserves particular attention for S3 because deleting and recreating a bucket can affect applications, data retention, bucket names, policies, and integrations.

Before applying a replacement, determine whether the bucket contains objects or versions, whether retention controls prevent deletion, and whether dependent systems rely on the existing bucket identity.

A preview is an important planning tool, but it does not eliminate all deployment risk. Review the planned changes alongside the resource's actual configuration and operational requirements.

### 2.8.2 Importing existing buckets

Organizations often have buckets that were originally created manually or managed outside Pulumi.

Importing an existing bucket can bring it under infrastructure-as-code management without creating a new bucket.

The general process involves identifying the existing resource, importing it into the appropriate stack, and ensuring that the Pulumi program describes its intended configuration.

After import, configuration drift can become visible during previews. Existing settings should be reviewed carefully before applying changes, particularly when they involve encryption, public access, policies, lifecycle behavior, or versioning.

Importing a bucket does not automatically import every associated S3 configuration as a separate managed resource. Additional resources may need to be imported or defined independently.

### 2.9 Pulumi State and Drift Management

Pulumi state records the resources managed by a stack and the information needed to compare deployed infrastructure with the desired configuration.

State is central to reliable infrastructure management.

### What state contains

Depending on the resource and configuration, Pulumi state can contain:

* Resource identifiers.

* Resource types and relationships.

* Recorded resource properties.

* Dependency information.

* Provider-related information needed for subsequent operations.

State should be treated as operationally sensitive. Access to it must be controlled, and secret values should use the platform's supported secret-protection mechanisms.

### State backends

Pulumi supports managed and self-managed state backends. The appropriate choice depends on collaboration requirements, access controls, auditability, availability, and operational responsibilities.

For a team, the backend should be selected deliberately rather than relying on individual developers' isolated local state.

### Configuration drift

Drift occurs when the actual AWS configuration differs from the configuration expected by Pulumi. For example, someone might manually disable bucket versioning or change a bucket policy in the AWS console.

Pulumi previews and refresh-related workflows help identify and reconcile differences between tracked state and actual resources. The appropriate response depends on whether the manual change is intentional or accidental.

For production S3, preventing unmanaged changes through IAM controls and deployment processes is often preferable to repeatedly correcting drift afterward.

### 2.10 Managing Existing Resources and Avoiding Unintended Replacements

Infrastructure code evolves. Resource names change, components are refactored, and configurations are adjusted. These changes can affect how Pulumi identifies resources.

### Resource identity

Pulumi uses resource identity and state information to associate program declarations with managed resources. Changing a logical resource name or restructuring a component can cause Pulumi to interpret a resource as new unless it can associate the old and new declarations.

Aliases can help preserve resource identity during supported refactoring operations.

### Protection and lifecycle controls

For critical S3 buckets, consider combining:

* Pulumi resource protection.

* AWS IAM restrictions on bucket deletion.

* Versioning and appropriate retention settings.

* Backup or replication strategies.

* Reviewed deployment previews.

* Explicit data-retention and recovery procedures.

These controls serve different purposes. Pulumi protection helps prevent accidental deletion through Pulumi, while AWS permissions govern which API operations an identity may perform. Neither guarantees that stored data can always be recovered.

### A critical distinction: infrastructure versus data

An S3 bucket is an infrastructure resource, but the objects it contains are application data.

Deleting or replacing infrastructure can have consequences beyond the resource itself. A production deployment process should therefore evaluate both infrastructure lifecycle and data lifecycle.

For example, deleting a bucket resource may fail if it is not empty. Even when deletion is technically possible, deleting object versions or retained data can be irreversible from the perspective of the application.

A safe infrastructure workflow treats data preservation as a first-class requirement.

### 2.11 Putting the Concepts Together

The main ideas in this module form a coherent infrastructure-management model:

Pulumi Python Program

Resources, components, and desired configuration

Pulumi Engine and State

Resource graph, dependencies, change planning, and tracked state

AWS Provider and AWS APIs

Authentication, resource operations, and actual AWS infrastructure

The Python program describes the intended infrastructure. Pulumi's engine uses that declaration and its state to determine required changes. The AWS provider performs the corresponding operations against AWS.

This separation is what makes Pulumi more than a scripting tool: it provides a resource model, dependency management, state tracking, and a repeatable deployment workflow.

### 2.12 Summary

In this module, we covered the main concepts required to manage S3 infrastructure with Pulumi:

* Infrastructure as Code and the role of Pulumi.

* Projects, stacks, and configuration.

* AWS provider configuration and credential management.

* S3 resource declarations, dependencies, outputs, and resource options.

* Reusable components and environment-specific settings.

* Naming conventions and configuration management.

* Previewing, updating, importing, and destroying infrastructure.

* Pulumi state, drift, and resource identity.

* Protection against unintended replacements and data loss.

These concepts provide the foundation for building S3 infrastructure that is repeatable, maintainable, and suitable for production environments. They also prepare you to define more advanced S3 configurations, including encryption, access policies, versioning, lifecycle management, and replication, as reusable infrastructure components.
