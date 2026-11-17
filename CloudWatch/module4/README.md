### Module 4 — AWS Config and Configuration Compliance

AWS Operations and Observability · Pulumi · Python

### 1\. Learning objectives

By the end of this module, you will understand how to use AWS Config to maintain visibility into AWS resource configurations, evaluate compliance, investigate configuration changes, and respond to violations.

You will learn how to:

* Record AWS resource configurations and build a resource inventory.

* Examine configuration history and relationships between resources.

* Evaluate resources with AWS-managed and custom Config rules.

* Understand compliance status, remediation, and conformance packs.

* Distinguish AWS configuration drift from Pulumi infrastructure drift.

* Correlate AWS Config findings with CloudTrail events.

* Use Systems Manager Automation for controlled remediation.

* Configure recording scope and retention with cost awareness.

### 2\. AWS Config fundamentals

### 2.1 What is AWS Config?

AWS Config is a service that discovers supported AWS resources, records their configuration states over time, and evaluates those configurations against desired rules.

For example, imagine you operate a fleet of EC2 instances and S3 buckets. You want to answer these questions:

* Which S3 buckets have versioning disabled?

* Which EC2 instances have public IP addresses?

* When was an EC2 instance's security group changed?

* Which resources currently violate your security requirements?

* Did a resource become noncompliant after a recent configuration change?

AWS Config helps answer these questions using configuration records, resource history, and compliance evaluations.

### How AWS Config works

AWS resources

EC2 · S3 · Security Groups · IAM · Other supported resources

Configuration recorder

Records supported resource configuration changes and states

Configuration history

Configuration items, timelines, and resource relationships

Config rules

Evaluate resource configurations against requirements

Operational response

Investigate · Notify · Remediate · Verify

AWS Config is not a replacement for CloudTrail. Config describes resource configuration states and changes; CloudTrail records API activity that can help explain who performed an action and which API was called.

### 2.2 Important AWS Config concepts

| Concept                | Meaning                                                                                                      |
| ---------------------- | ------------------------------------------------------------------------------------------------------------ |
| Configuration recorder | Collects configuration information for selected resource types.                                              |
| Configuration item     | A representation of a resource's configuration at a particular point in time.                                |
| Configuration history  | A timeline of recorded configurations for a resource.                                                        |
| Resource inventory     | A view of supported resources discovered and recorded by Config.                                             |
| Configuration rule     | Evaluates whether resources satisfy a specific requirement.                                                  |
| Compliance result      | Indicates whether a resource or rule is compliant, noncompliant, or in an evaluation state.                  |
| Delivery channel       | Configures the delivery of configuration snapshots and history files to supported destinations, commonly S3. |
| Conformance pack       | Groups Config rules and remediation-related configuration into a reusable compliance package.                |

A configuration item is not necessarily created for every possible change to every AWS service. Recording depends on supported resource types, recorder configuration, and service behavior.

### 3\. Configuration recording and history

### 3.1 Configuration recorders

The configuration recorder is the foundation of AWS Config. Before Config can maintain a useful inventory and configuration history, you must configure a recorder and start it.

Important decisions include:

* Resource coverage: Which resource types should be recorded?

* Recording mode: Whether configuration changes are recorded continuously or periodically, where supported.

* Exclusions: Whether particular resource types should be excluded.

* IAM permissions: Whether the Config service can discover resources and deliver configuration data.

* Region: AWS Config recording is Region-specific, so resources in different Regions need appropriate coverage.

For most operational monitoring, continuous recording is a good starting point. Periodic recording can be useful when its supported resource types and less frequent updates meet your requirements.

### 3.2 Configuration items

A configuration item captures information about a resource's configuration at a particular time. Depending on the resource type, it may include:

* Resource identifiers and type.

* Configuration properties.

* Resource relationships.

* Capture and configuration timestamps.

* Tags and related metadata.

* The recorded configuration state.

Consider an EC2 instance whose security group changes from `sg-aaa` to `sg-bbb`. If the relevant resource types are recorded, AWS Config can help you inspect the configuration before and after the change.

The history is useful for investigation, but it does not guarantee that every possible application-level or network-level event is recorded.

### 3.3 Resource relationships

AWS Config can represent relationships between supported resources, helping you understand dependencies.

For example:

EC2 instance

Security group

VPC

These relationships can help you investigate how a configuration change affects connected resources. The exact relationships available depend on the AWS resource types supported by Config.

### 3.4 Where to inspect history

In the AWS console, open AWS Config in the Region containing your resources. Depending on the console version, look for resource inventory, resource details, configuration timeline, and compliance views.

Using the AWS CLI, you can inspect recorded resources and configuration history.

```bash
# List resources of a specific type.
aws configservice list-discovered-resources \
  --resource-type AWS::EC2::Instance \
  --region eu-west-1

# Retrieve configuration history for a specific resource.
aws configservice get-resource-config-history \
  --resource-type AWS::EC2::Instance \
  --resource-id i-0123456789abcdef0 \
  --region eu-west-1
```

The history request may return paginated results. The resource ID is an example; substitute an actual recorded resource in your account.

### 4\. AWS Config rules and compliance

A configuration recorder collects resource information. Config rules evaluate that information against requirements. Recording alone does not enforce security policies.

### 4.1 AWS-managed rules

AWS provides managed rules for common security, reliability, and operational requirements. You configure a rule and its parameters, and Config evaluates applicable resources.

Examples include:

| Rule                         | Purpose                                                |
| ---------------------------- | ------------------------------------------------------ |
| s3-bucket-versioning-enabled | Checks whether S3 buckets have versioning enabled.     |
| ec2-instance-no-public-ip    | Checks whether EC2 instances have public IP addresses. |
| required-tags                | Checks for required tags on supported resources.       |
| encrypted-volumes            | Checks whether applicable EBS volumes are encrypted.   |

Before deploying a rule, verify its current identifier, supported resource types, parameters, and evaluation behavior in the AWS Config rule catalog. A rule's existence does not mean that it covers every resource or every security requirement.

### 4.2 Custom rules

When a managed rule does not express your requirement, you can develop a custom rule using AWS Lambda or Guard-based policy evaluation, depending on the rule type and supported integration.

For example, your organization might require every production EC2 instance to have:

* An `Environment` tag set to `production`.

* An `Owner` tag.

* A specific approved instance family.

A custom policy can express requirements that are more specific than a single built-in rule.

Custom rules require additional development, testing, permissions, and maintenance. Prefer managed rules when they satisfy the requirement.

### 4.3 Compliance states

AWS Config can report different compliance and evaluation states. Common outcomes include:

* COMPLIANT: The resource satisfies the rule.

* NON_COMPLIANT: The resource violates the rule.

* INSUFFICIENT_DATA: Config does not have enough information to evaluate compliance.

* NOT_APPLICABLE: The rule does not apply to the resource.

Rules may also be undergoing evaluation or have other evaluation-related statuses. A lack of noncompliant findings does not prove that every resource is secure: the recorder may not cover the relevant resource type, and the selected rules may not express all the necessary controls.

### 4.4 Compliance is not the same as enforcement

Suppose you create a rule that detects S3 buckets without versioning.

The rule can identify noncompliant buckets, but it does not automatically enable versioning. Remediation is a separate capability that must be configured deliberately.

A typical operational flow is:

* Record resource configurations.

* Evaluate the configurations against rules.

* Identify a noncompliant resource.

* Notify an operator or invoke a controlled remediation.

* Re-evaluate the resource and confirm the outcome.

### 5\. Configuration drift versus infrastructure drift

These concepts are related, but they answer different questions.

Configuration drift means that a resource's observed configuration no longer meets a desired requirement or baseline.

Infrastructure drift means that the real infrastructure differs from the state or configuration managed by an Infrastructure as Code tool.

| Situation                                                                          | AWS Config                                       | Pulumi                                                                                                             |
| ---------------------------------------------------------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| An S3 bucket has versioning disabled, violating a compliance rule                  | Can report noncompliance                         | May or may not detect a difference from the declared program, depending on the desired state and provider behavior |
| Someone changes an EC2 security group outside Pulumi                               | Can record the configuration change when covered | A subsequent refresh or preview can identify drift relative to the Pulumi program and state                        |
| A resource has a configuration that violates an organizational security baseline   | Can evaluate the applicable rule                 | Pulumi alone does not automatically enforce every organizational compliance policy                                 |
| A resource differs from the Pulumi program but remains compliant with Config rules | May report it as compliant                       | Can identify infrastructure drift                                                                                  |

For example, if Pulumi declares an S3 bucket with versioning enabled but someone disables versioning manually, AWS Config can flag the violation if the relevant rule is active. Pulumi can also detect the divergence from the declared configuration during an appropriate refresh and preview.

These are complementary tools:

* Use AWS Config for ongoing configuration visibility and compliance evaluation.

* Use Pulumi for declarative infrastructure management and reconciliation.

* Use CloudTrail to investigate API activity associated with a change.

### 6\. Compliance remediation and integrations

### 6.1 AWS Config and CloudTrail

When a resource becomes noncompliant, you often need to know what changed and who changed it.

AWS Config helps you identify the resource's configuration history and compliance status. CloudTrail helps you investigate relevant API activity, including the principal, API operation, and event time when those details are available.

A useful investigation sequence is:

* Identify the noncompliant resource and rule.

* Inspect the Config configuration timeline.

* Establish the approximate time of the change.

* Search CloudTrail management or data events, as appropriate.

* Check the event's principal, request parameters, and outcome.

* Determine whether the change was expected, accidental, or unauthorized.

CloudTrail event availability depends on the event category and logging configuration. For example, object-level S3 data events generally require explicit data-event logging configuration.

### 6.2 AWS Config and Systems Manager

AWS Config remediation can integrate with Systems Manager Automation to run a predefined remediation document.

A remediation workflow can:

* Target a specific resource.

* Run a supported Systems Manager Automation document.

* Supply required parameters.

* Apply a correction.

* Re-evaluate the resource's compliance.

Remediation should be carefully scoped. A rule that detects a problem is not, by itself, sufficient justification to make an automatic production change.

Before enabling automatic remediation, establish:

* Which resources are eligible.

* Which parameters are permitted.

* Whether the change is reversible.

* What IAM permissions the automation requires.

* How failures and retries are handled.

* How the remediation is audited and verified.

### 6.3 Conformance packs and organization-wide compliance

A conformance pack groups Config rules and related remediation configuration into a reusable compliance package.

Conformance packs are useful when several controls must be deployed together. They can support standardized baselines across accounts and Regions, including organization-wide deployment patterns.

For larger environments, consider:

* AWS Organizations and delegated administration.

* Centralized compliance reporting.

* Consistent resource recording across accounts and Regions.

* Standardized rule sets for development, staging, and production.

* Exceptions and exclusions with explicit ownership.

* A clear process for updating and rolling out policy changes.

A conformance pack does not remove the need to verify recording coverage, service prerequisites, or the permissions required by each rule.

### 7\. Lab 4 — Detect and Remediate Configuration Drift

### Lab objectives

Build a working AWS Config setup using Pulumi and Python. Record resource configurations, detect a compliance violation, inspect the configuration history, and design a controlled remediation workflow.

Suggested duration: 60–90 minutes

Cost: AWS Config recording and evaluations, S3 storage, and any optional compute resources

### 7.1 Lab architecture

Pulumi — Python

Provision resources and policies

AWS Config recorder

Record supported resource configurations

S3 delivery bucket

Configuration snapshots and history files

Config rules

Evaluate S3 versioning compliance

Investigation and remediation

Config history · CloudTrail · Systems Manager Automation

We will use an S3 bucket as the example resource. The compliance rule will check whether S3 bucket versioning is enabled. We will first deploy the detection infrastructure, then deliberately create a noncompliant configuration, investigate it, and restore compliance.

### 7.2 Prerequisites

Install the Pulumi CLI, Python, and the AWS CLI. Configure AWS credentials for a sandbox account and select the Region for the lab.

Create the project:

```bash
mkdir aws-config-lab
cd aws-config-lab

pulumi new aws-python
```

Install the AWS provider if your project does not already include it:

```bash
uv add pulumi pulumi-aws
```

If your generated project uses a different dependency manager, use that manager consistently instead.

Configure the stack:

```bash
pulumi config set aws:region eu-west-1
```

Replace `eu-west-1` with your chosen Region.

The deploying identity needs permission to create the required IAM, S3, and AWS Config resources. It also needs permission to pass the Config service role. For production deployments, use appropriately scoped permissions rather than unrestricted administrator access.

### 7.3 Provision AWS Config with Pulumi

The following example creates:

* An S3 bucket for AWS Config delivery.

* A service role trusted by AWS Config.

* The AWS-managed `AWS_ConfigRole` policy attachment.

* A bucket policy that permits AWS Config to deliver configuration files.

* A configuration recorder.

* A delivery channel.

* An S3 versioning compliance rule.

Replace the generated `__main__.py` contents with the following:

```python

import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
region = aws.get_region().name
account_id = aws.get_caller_identity().account_id

# Keep the bucket name globally unique.
bucket_name = config.require("configBucketName")

# 1. S3 bucket for AWS Config delivery.
config_bucket = aws.s3.BucketV2(
    "config-delivery-bucket",
    bucket=bucket_name,
    force_destroy=False,
)

# Enforce private access.
public_access_block = aws.s3.BucketPublicAccessBlock(
    "config-bucket-public-access",
    bucket=config_bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

# Encrypt objects at rest.
encryption = aws.s3.BucketServerSideEncryptionConfigurationV2(
    "config-bucket-encryption",
    bucket=config_bucket.id,
    rules=[{
        "apply_server_side_encryption_by_default": {
            "sse_algorithm": "AES256",
        }
    }],
)

# 2. Allow AWS Config to assume its service role.
config_role = aws.iam.Role(
    "config-service-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "config.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

config_role_policy = aws.iam.RolePolicyAttachment(
    "config-managed-policy",
    role=config_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/service-role/AWS_ConfigRole"
    ),
)

# 3. Permit AWS Config to check the bucket ACL and
# write configuration files to the delivery bucket.
bucket_policy = aws.s3.BucketPolicy(
    "config-delivery-policy",
    bucket=config_bucket.id,
    policy=pulumi.Output.all(
        config_bucket.arn,
        config_bucket.bucket,
    ).apply(lambda values: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AWSConfigBucketPermissionsCheck",
                "Effect": "Allow",
                "Principal": {
                    "Service": "config.amazonaws.com"
                },
                "Action": "s3:GetBucketAcl",
                "Resource": values[0],
                "Condition": {
                    "StringEquals": {
                        "AWS:SourceAccount": account_id
                    }
                },
            },
            {
                "Sid": "AWSConfigBucketDelivery",
                "Effect": "Allow",
                "Principal": {
                    "Service": "config.amazonaws.com"
                },
                "Action": "s3:PutObject",
                "Resource": values[0] + "/AWSLogs/"
                    + account_id + "/Config/*",
                "Condition": {
                    "StringEquals": {
                        "s3:x-amz-acl": "bucket-owner-full-control",
                        "AWS:SourceAccount": account_id,
                    }
                },
            },
        ],
    })),
)

# 4. Record all supported resource types in this Region.
recorder = aws.cfg.Recorder(
    "main-config-recorder",
    name="default",
    role_arn=config_role.arn,
    recording_group={
        "all_supported": True,
        "include_global_resource_types": True,
    },
    opts=pulumi.ResourceOptions(
        depends_on=[config_role_policy]
    ),
)

# 5. Configure delivery to S3.
delivery_channel = aws.cfg.DeliveryChannel(
    "main-config-delivery",
    name="default",
    s3_bucket_name=config_bucket.bucket,
    s3_key_prefix="AWSLogs/" + account_id + "/Config",
    opts=pulumi.ResourceOptions(
        depends_on=[
            bucket_policy,
            public_access_block,
            encryption,
            recorder,
        ]
    ),
)

# 6. Start recording after the delivery channel exists.
recorder_status = aws.cfg.RecorderStatus(
    "main-config-recorder-status",
    name=recorder.name,
    is_enabled=True,
    opts=pulumi.ResourceOptions(
        depends_on=[delivery_channel]
    ),
)

# 7. Evaluate S3 bucket versioning compliance.
versioning_rule = aws.cfg.Rule(
    "s3-versioning-compliance",
    name="s3-bucket-versioning-enabled",
    source={
        "owner": "AWS",
        "source_identifier": "S3_BUCKET_VERSIONING_ENABLED",
    },
    opts=pulumi.ResourceOptions(
        depends_on=[recorder_status]
    ),
)

pulumi.export("config_bucket_name", config_bucket.bucket)
pulumi.export("config_recorder_name", recorder.name)
pulumi.export("versioning_rule_name", versioning_rule.name)
pulumi.export("region", region)
```

Important implementation notes

* Use a globally unique S3 bucket name. Set it before deployment:

    ```bash
    pulumi config set configBucketName your-unique-config-bucket-name
    ```

* Check the current Pulumi AWS provider schema and AWS Config documentation if the provider version changes. In particular, recording-group fields and managed rule identifiers must match the installed provider and AWS service requirements.

* The example uses broad resource recording to make the lab easier to understand. In a cost-sensitive or production account, explicitly scope recording to the resource types you need.

* The bucket policy is intentionally restricted to the current account. Cross-account or organization-wide delivery requires a different policy design.

* For a production implementation, also consider S3 lifecycle rules, log retention requirements, and any organization-specific encryption requirements.

### 7.4 Deploy and verify the recorder

Preview the infrastructure:

```bash
pulumi preview
```

Deploy it:

```bash
pulumi up
```

After deployment, verify the recorder and delivery channel:

```bash
aws configservice describe-configuration-recorders \
  --region eu-west-1

aws configservice describe-configuration-recorder-status \
  --region eu-west-1

aws configservice describe-delivery-channels \
  --region eu-west-1
```

The recorder should be enabled, and the delivery channel should reference your S3 bucket.

AWS Config may need time to discover resources, record their configurations, and evaluate the rule. A successful Pulumi deployment does not mean that compliance evaluations have already finished.

### 7.5 Create a test bucket with versioning enabled

Create a separate bucket to act as the application resource under evaluation.

```python
test_bucket = aws.s3.BucketV2(
    "application-test-bucket",
    force_destroy=False,
)

test_versioning = aws.s3.BucketVersioningV2(
    "application-test-versioning",
    bucket=test_bucket.id,
    versioning_configuration={
        "status": "Enabled",
    },
)

pulumi.export("test_bucket_name", test_bucket.bucket)
```

Add this resource to your Pulumi program, deploy it, and retrieve the bucket name from the stack outputs.

The test bucket should initially satisfy the versioning rule. Allow time for AWS Config to discover it and evaluate compliance.

To inspect the results:

```bash
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name s3-bucket-versioning-enabled \
  --region eu-west-1
```

This API returns evaluation details for the rule. If the test bucket does not appear immediately, verify recording status, rule status, Region, and evaluation timing.

### 7.6 Introduce a controlled compliance violation

For this step, deliberately disable versioning on the test bucket using the AWS CLI:

```bash
aws s3api put-bucket-versioning \
  --bucket YOUR_TEST_BUCKET \
  --versioning-configuration Status=Suspended
```

Use only the disposable lab bucket. Do not suspend versioning on a production bucket as part of this exercise.

This change is made outside Pulumi, which gives you an opportunity to compare Config compliance with infrastructure drift.

Wait for AWS Config to record and evaluate the new state, then query the rule again:

```bash
aws configservice get-compliance-details-by-config-rule \
  --config-rule-name s3-bucket-versioning-enabled \
  --region eu-west-1
```

You should eventually see the test bucket reported as noncompliant. Evaluation is asynchronous, so the result may not change immediately.

### 7.7 Inspect the configuration history

Identify the bucket's resource ID and query AWS Config history.

First, list discovered S3 buckets:

```bash
aws configservice list-discovered-resources \
  --resource-type AWS::S3::Bucket \
  --region eu-west-1
```

Then retrieve history for the test bucket:

```bash
aws configservice get-resource-config-history \
  --resource-type AWS::S3::Bucket \
  --resource-id YOUR_TEST_BUCKET \
  --region eu-west-1
```

Review the returned configuration items and timestamps. Compare the recorded states before and after the change.

For a real incident, correlate the approximate change time with CloudTrail events to identify the API operation and principal. Make sure the relevant CloudTrail event category was enabled and retained for the period you are investigating.

### 7.8 Remediate the violation

For this lab, restore compliance explicitly:

```bash
aws s3api put-bucket-versioning \
  --bucket YOUR_TEST_BUCKET \
  --versioning-configuration Status=Enabled
```

Wait for AWS Config to evaluate the updated configuration. Then query compliance again and confirm that the resource returns to a compliant state.

This manual remediation is intentionally simple. In a production environment, you could use a supported AWS Config remediation action backed by Systems Manager Automation, with appropriate permissions, parameters, retry limits, and auditing.

For the S3 versioning use case, ensure the remediation preserves the intended data-protection policy and does not inadvertently modify unrelated bucket settings.

### 7.9 Design a Systems Manager remediation workflow

A production remediation pipeline should separate detection from action:

AWS Config rule

Detect noncompliance

Remediation decision

Validate resource type, scope, and parameters

Systems Manager Automation

Run an approved remediation document

Verification and audit

Re-evaluate compliance and retain execution history

When configuring automatic remediation, verify that the chosen remediation document supports the target resource and parameters. Avoid assuming that every managed Config rule has an appropriate automatic remediation action available.

A safe rollout strategy is to start with notifications and manual approval, test remediation on disposable resources, and enable automatic execution only after validating the failure-handling and rollback strategy.

### 8\. Operational considerations

### 8.1 Recording scope and costs

AWS Config charges can depend on configuration items recorded, rule evaluations, conformance pack usage, and other enabled capabilities. S3 storage and related delivery also contribute to costs.

Control cost by:

* Recording only the resource types required by your operational and compliance goals.

* Reviewing recording frequency and supported recording modes.

* Avoiding unnecessary duplicate rules.

* Applying suitable S3 lifecycle and retention policies.

* Reviewing account and Region coverage regularly.

### 8.2 Troubleshooting checklist

| Symptom                                   | What to investigate                                                                       |
| ----------------------------------------- | ----------------------------------------------------------------------------------------- |
| No resources appear                       | Recorder status, resource coverage, Region, and permissions                               |
| No configuration history                  | Whether the resource type is supported and recording is enabled                           |
| Rule remains in evaluation                | Rule status, evaluation timing, and applicable resource types                             |
| Delivery fails                            | Delivery channel, S3 bucket policy, service role, and Region                              |
| Resource remains noncompliant after a fix | Current resource configuration, rule evaluation timing, and rule parameters               |
| Remediation fails                         | Automation document, execution role, permissions, input parameters, and execution history |

### 9\. Final architecture review

At the end of this lab, you should have a working understanding of how the following pieces fit together:

* Pulumi provisions and manages the infrastructure.

* AWS Config records resource configurations and evaluates compliance.

* Amazon S3 stores delivered configuration history and snapshots.

* CloudTrail helps explain API changes and identify the actor when relevant events are available.

* Systems Manager Automation can execute approved remediation workflows.

* Compliance re-evaluation confirms whether the remediation achieved the intended result.

The key operational principle is that detection, investigation, remediation, and verification are distinct stages. A reliable AWS operations platform connects all four without assuming that a compliance finding automatically fixes the underlying problem.
