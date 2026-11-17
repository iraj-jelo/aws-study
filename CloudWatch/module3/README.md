### Module 3 — AWS CloudTrail and Audit Operations

AWS Operations and Observability · Module 3 of 8

### 1\. Learning objectives

By the end of this module, you will understand how to use AWS CloudTrail to reconstruct API activity, investigate resource changes, and build an auditable detection pipeline using Pulumi.

You will learn to:

* Distinguish management events, data events, and other CloudTrail event categories.

* Identify the IAM user, assumed role, AWS service, or other principal responsible for an API request.

* Configure CloudTrail trails, S3 log storage, and log file integrity validation.

* Send CloudTrail events to CloudWatch Logs for querying and investigation.

* Use Amazon EventBridge to detect important API activity in near real time.

* Investigate unexpected changes by correlating CloudTrail records with alarms and other operational evidence.

* Apply least-privilege IAM policies and protect audit logs against unauthorized modification or deletion.

### 2\. CloudTrail fundamentals

Amazon CloudTrail is an AWS auditing service that records activity in your AWS account. It captures information about API calls and other supported events, helping you answer questions such as:

* Who modified a security group?

* Which role deleted an S3 object?

* When was an IAM policy changed?

* What API request caused a resource configuration to change?

* Did an unexpected principal attempt to access a resource?

CloudTrail is different from CloudWatch. CloudTrail primarily records what happened and who performed an action, while CloudWatch helps you understand how your workload is behaving through metrics, logs, and alarms.

### The audit and detection workflow

AWS API activity

IAM · EC2 · S3 · Lambda · Other services

AWS CloudTrail

Records supported account activity and API events

Amazon S3

Longer-term audit log storage and retention

EventBridge / CloudWatch Logs

Event detection, queries, and investigation

Operational response

Notify · Investigate · Contain · Recover

A critical distinction: CloudTrail is an audit source, not a complete security detection system by itself. You still need event selection, alert rules, suitable permissions, and a response process.

### 3\. CloudTrail event categories

### 3.1 Management events

Management events record control-plane operations that manage AWS resources.

Examples include:

| API operation                 | Typical purpose               |
| ----------------------------- | ----------------------------- |
| RunInstances                  | Launch EC2 instances          |
| AuthorizeSecurityGroupIngress | Modify security group ingress |
| PutBucketPolicy               | Change an S3 bucket policy    |
| CreateRole                    | Create an IAM role            |
| AttachRolePolicy              | Attach a managed IAM policy   |
| DeleteTrail                   | Delete a CloudTrail trail     |

Management events are categorized as:

* Read events: Operations that retrieve information or inspect configuration, such as `DescribeInstances` or `GetRole`.

* Write events: Operations that create, modify, or delete resources, such as `RunInstances`, `PutBucketPolicy`, or `DeleteRole`.

These categories are useful when you want to audit configuration changes without collecting every read operation.

A trail can select read and write management events. The default event selection for a newly created trail typically includes both, but the actual configuration must be checked.

### 3.2 Data events

Data events record supported operations performed on resources or within services. They are often more granular and can generate substantial event volume.

Examples include:

* S3 object operations such as `GetObject`, `PutObject`, and `DeleteObject`.

* Lambda function invocation events such as `Invoke`.

* Other supported resource-level operations, depending on the service.

Unlike management events, data events are not enabled by default in a trail. You explicitly configure which supported resources and event types to record. They may incur additional charges.

For example, recording S3 object-level events can help investigate which principal uploaded or deleted a particular object. It is different from recording the management event that changes the bucket's policy.

### 3.3 Event history versus trails

CloudTrail Event history provides a searchable, regional, 90-day history of management events. It is useful for immediate investigations without first creating a trail.

A trail delivers selected events to destinations such as S3 and, when configured, CloudWatch Logs. Trails can support ongoing retention, centralized audit collection, and more advanced operational workflows.

| Capability                  | Event history                                              | Trail                                                 |
| --------------------------- | ---------------------------------------------------------- | ----------------------------------------------------- |
| Management event history    | Yes, up to 90 days                                         | Yes, according to configured collection and retention |
| S3 log delivery             | No configuration required for Event history itself         | Yes                                                   |
| CloudWatch Logs integration | Not a direct substitute for a configured trail integration | Yes                                                   |
| Data event collection       | Not provided as a general Event history search feature     | Yes, with explicit selectors                          |
| Long-term retention         | Not intended for this purpose                              | Supported through destination configuration           |

For production auditing, use a properly configured trail and a deliberate retention strategy rather than relying solely on Event history.

### 4\. Anatomy of a CloudTrail event

A CloudTrail event is a structured JSON record. Understanding its fields is essential for determining which identity performed an action and whether the request succeeded.

Consider this simplified example of an EC2 security group modification:

```json
{
  "eventSource": "ec2.amazonaws.com",
  "eventName": "AuthorizeSecurityGroupIngress",
  "eventTime": "2026-10-28T10:30:00Z",
  "awsRegion": "eu-west-2",
  "sourceIPAddress": "203.0.113.25",
  "userAgent": "console.amazonaws.com",
  "userIdentity": {
    "type": "AssumedRole",
    "arn": "arn:aws:sts::123456789012:assumed-role/NetworkAdmin/session-01",
    "sessionContext": {
      "sessionIssuer": {
        "arn": "arn:aws:iam::123456789012:role/NetworkAdmin"
      }
    }
  },
  "requestParameters": {
    "groupId": "sg-example123",
    "ipPermissions": {}
  },
  "responseElements": null,
  "errorCode": null
}
```

Illustrative event only; the IP address, account ID, and resource identifiers are examples.

### Fields to inspect during an investigation

| Field                    | What it tells you                                            |
| ------------------------ | ------------------------------------------------------------ |
| eventTime                | When the event occurred                                      |
| eventSource              | Which AWS service received the request                       |
| eventName                | Which API operation was invoked                              |
| userIdentity             | Identity and credentials context associated with the request |
| sourceIPAddress          | Recorded source address                                      |
| userAgent                | Client or software associated with the request               |
| requestParameters        | Parameters supplied with the request, when recorded          |
| responseElements         | Response details, when recorded                              |
| errorCode / errorMessage | Error information for failed requests                        |
| recipientAccountId       | Account that received the event                              |
| requestID                | Request identifier useful for correlation                    |

Important: `userIdentity.type` can be `IAMUser`, `AssumedRole`, `Root`, `AWSService`, or another supported identity type. When the event uses an assumed role, inspect `sessionContext.sessionIssuer` and available session identity information to establish which role was used. If an IAM Identity Center session or federated identity is involved, you may need additional identity-provider or identity-center audit records to map the session back to a human user.

CloudTrail records do not always contain every request parameter or response field. Sensitive values can be omitted, and the presence of a field varies by API operation. AWS CloudTrail +1

### 5\. Creating a secure audit trail

A production-oriented trail usually needs more than the trail resource itself. You must consider the destination bucket, its policy, log delivery permissions, encryption, retention, and monitoring.

### 5.1 Recommended architecture

CloudTrail — multi-Region trail

Management events and selected data events

Amazon S3

Durable audit archive, lifecycle and retention controls

CloudWatch Logs

Centralized search and investigation

EventBridge

Match selected API events and route alerts

Amazon SNS

Email or other supported notification subscribers

For account-wide coverage, a multi-Region trail is generally a sensible default. Global service events and regional service behavior should also be considered when reviewing coverage. CloudTrail supports S3 delivery and optional CloudWatch Logs integration. Amazon Web Services, Inc. +1

### 5.2 Protecting the log destination

Your audit bucket should have:

* S3 Block Public Access enabled.

* Bucket-owner-controlled access and a restrictive bucket policy.

* Encryption at rest, using SSE-S3 or SSE-KMS according to the security requirements.

* Versioning and, where required, S3 Object Lock with an appropriate retention mode.

* Lifecycle policies aligned with the audit retention requirements.

* A policy that allows CloudTrail to validate the bucket and deliver log files, while preventing unrelated principals from writing or deleting them.

* Monitoring for changes to the trail, destination bucket policy, and retention settings.

Enable CloudTrail log file validation to help detect modifications or deletion of delivered log files by validating their digest chain. Validation is a tamper-detection mechanism, not a guarantee that an administrator cannot change the trail configuration or prevent future log delivery.

For higher-assurance environments, separate audit administration from workload administration, and consider centralized logging in a dedicated security account. Amazon Web Services, Inc. +1

### 6\. Integrating CloudTrail with CloudWatch Logs

CloudTrail can deliver events to a CloudWatch Logs log group through a configured IAM role. This enables operational teams to search audit activity alongside application logs.

### 6.1 Log group design

A log group might be named:

```text
/operations/cloudtrail/audit
```

Choose retention deliberately. Audit requirements may call for a different retention period from application debugging logs, and longer retention can increase storage costs.

The CloudTrail delivery role needs permission to create log streams and publish log events to the intended log group. Restrict its permissions to the resources it actually requires.

### 6.2 Example Logs Insights queries

Find security group changes:

```sql
fields @timestamp,
       eventSource,
       eventName,
       userIdentity.arn,
       sourceIPAddress,
       errorCode
| filter eventSource = "ec2.amazonaws.com"
| filter eventName like /SecurityGroup/
| sort @timestamp desc
| limit 50
```

Find IAM policy changes:

```sql
fields @timestamp,
       eventName,
       userIdentity.arn,
       requestParameters,
       errorCode
| filter eventSource = "iam.amazonaws.com"
| filter eventName in [
    "AttachRolePolicy",
    "DetachRolePolicy",
    "PutRolePolicy",
    "DeleteRolePolicy"
  ]
| sort @timestamp desc
| limit 50
```

Investigate failed API calls:

```sql
fields @timestamp,
       eventSource,
       eventName,
       userIdentity.arn,
       errorCode,
       errorMessage
| filter ispresent(errorCode)
| sort @timestamp desc
| limit 100
```

These queries assume that the selected CloudTrail fields are available in the log events and that the events have been delivered to the selected log group.

Operational tip: A failed API request can be security-relevant even when it did not modify a resource. Repeated `AccessDenied` errors, for example, may indicate a misconfigured application, a broken deployment, or an attempted unauthorized operation.

### 7\. Detecting API activity with Amazon EventBridge

EventBridge lets you match incoming events against rules and route matching events to targets such as SNS, Lambda, or SQS. AWS API activity recorded by CloudTrail can be used as an event source for supported event patterns. Amazon EventBridge +1

### Example: Detect security group changes

A rule can match the CloudTrail API event for authorizing ingress:

```json
{
  "source": ["aws.ec2"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["ec2.amazonaws.com"],
    "eventName": [
      "AuthorizeSecurityGroupIngress",
      "RevokeSecurityGroupIngress",
      "AuthorizeSecurityGroupEgress",
      "RevokeSecurityGroupEgress"
    ]
  }
}
```

This pattern identifies selected security group rule changes. It does not automatically determine whether a change is malicious; that requires context, such as the identity, source, approved change window, and requested network permissions.

### Example: Detect changes to IAM roles

```json
{
  "source": ["aws.iam"],
  "detail-type": ["AWS API Call via CloudTrail"],
  "detail": {
    "eventSource": ["iam.amazonaws.com"],
    "eventName": [
      "CreateRole",
      "DeleteRole",
      "AttachRolePolicy",
      "DetachRolePolicy",
      "PutRolePolicy",
      "DeleteRolePolicy"
    ]
  }
}
```

Route matched events to an SNS topic to notify the operations team.

Important distinction: EventBridge event matching and CloudTrail trail delivery are related but not identical. Some CloudTrail management events are available to EventBridge without you configuring an S3 trail. However, you still need an appropriate trail and event selectors for durable S3 delivery, CloudWatch Logs integration, and selected data-event coverage. For example, S3 object-level events require explicit CloudTrail data-event configuration when you use the CloudTrail-based EventBridge pattern. Amazon EventBridge +1

### 8\. Investigating unauthorized changes

When an unexpected change is detected, use a repeatable investigation process rather than immediately assuming malicious activity.

### Incident investigation workflow

* Identify the event

    Record the API name, event time, Region, resource identifiers, and error status.

* Establish the principal

    Inspect `userIdentity`, the role session issuer, available session context, and the source address.

* Inspect the request

    Examine `requestParameters`, resource details, and available response fields to understand what was requested.

* Correlate evidence

    Search nearby CloudTrail events, deployment records, CloudWatch logs, and relevant AWS Health events.

* Contain and recover

    If the change is unauthorized, follow the incident-response process, restrict compromised credentials when appropriate, and restore the approved configuration.

* Preserve evidence

    Retain relevant audit records, document the timeline, and investigate whether logging or security controls were altered.

A common mistake is to interpret the ARN of an assumed role as the name of the human who initiated the operation. Role chaining, federated sessions, and automation can complicate attribution. Correlate the event with the relevant identity-provider, IAM Identity Center, or workload records when necessary.

### 9\. Lab 3 — Build an AWS Audit and Detection Pipeline

Hands-on lab

### Lab architecture

You will deploy a multi-Region CloudTrail trail in a selected home Region, store logs in a dedicated S3 bucket, deliver audit events to CloudWatch Logs, and notify an operator when a security group is modified.

Pulumi deployment

Python + AWS provider

CloudTrail

Management events · Integrity validation · Multi-Region coverage

S3 bucket

Persistent audit archive

CloudWatch Logs

Search and investigation

EventBridge rule → SNS

Detect security group changes and send notifications

### 9.1 Prerequisites

Install and configure:

* Python 3.11 or later.

* Pulumi CLI.

* AWS CLI with credentials for a dedicated learning account.

* The Pulumi AWS provider package.

* Permissions to create CloudTrail, S3, CloudWatch Logs, IAM, EventBridge, and SNS resources.

Configure the AWS provider Region using Pulumi configuration. For this example, use `eu-west-2` (London), or select another supported Region.

```bash
mkdir aws-cloudtrail-lab
cd aws-cloudtrail-lab

pulumi new aws-python
```

Follow the project prompts, then install the Python dependencies specified by the generated project. Use a non-root learning identity with the permissions needed for the lab.

### 9.2 Provision the S3 audit bucket

In `__main__.py`, begin with a dedicated bucket. The following is a focused resource fragment, not the complete trail deployment:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
region = aws.get_region_output().name

account = aws.get_caller_identity_output()

bucket = aws.s3.BucketV2(
    "cloudtrail-audit-bucket",
    force_destroy=False,
)

public_access = aws.s3.BucketPublicAccessBlock(
    "cloudtrail-audit-public-access-block",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

bucket_versioning = aws.s3.BucketVersioningV2(
    "cloudtrail-audit-versioning",
    bucket=bucket.id,
    versioning_configuration={
        "status": "Enabled",
    },
)

pulumi.export("audit_bucket_name", bucket.bucket)
pulumi.export("audit_region", region)
pulumi.export("account_id", account.account_id)
```

This establishes the bucket, public-access protections, and versioning. It does not yet authorize CloudTrail delivery. You will add a bucket policy that permits the CloudTrail service to check the bucket ACL and write objects to the appropriate account-specific log prefix.

For a real audit archive, also decide on encryption, retention, deletion protections, and whether S3 Object Lock is required.

### 9.3 Configure CloudWatch Logs and IAM

Create a log group with a deliberate retention period:

```python
log_group = aws.cloudwatch.LogGroup(
    "cloudtrail-audit-log-group",
    name="/operations/cloudtrail/audit",
    retention_in_days=90,
)
```

Next, create an IAM role for CloudTrail to publish events to CloudWatch Logs. Its trust policy should allow `cloudtrail.amazonaws.com` to assume the role. Attach a policy scoped to the intended log group and its log streams, granting only the required CloudWatch Logs operations.

The CloudTrail trail will reference the resulting role ARN and log group ARN.

### 9.4 Create the trail

The following shows the key Pulumi resource configuration; it depends on the bucket policy and CloudWatch Logs role being created first.

```python
trail = aws.cloudtrail.Trail(
    "operations-audit-trail",
    name="operations-audit-trail",
    s3_bucket_name=bucket.bucket,
    is_multi_region_trail=True,
    include_global_service_events=True,
    enable_log_file_validation=True,
    enable_logging=True,
    cloud_watch_logs_group_arn=log_group.arn.apply(
        lambda arn: f"{arn}:*"
    ),
    cloud_watch_logs_role_arn=cloudtrail_logs_role.arn,
    opts=pulumi.ResourceOptions(
        depends_on=[
            public_access,
            bucket_versioning,
            cloudtrail_bucket_policy,
        ],
    ),
)

pulumi.export("cloudtrail_arn", trail.arn)
```

Here, `cloudtrail_logs_role` and `cloudtrail_bucket_policy` represent the IAM role and S3 bucket policy you define in the preceding steps. The bucket policy must allow CloudTrail delivery; public access should remain blocked.

The trail is multi-Region, so its resource is managed in its home Region while it records supported activity across Regions. Global service events require appropriate configuration. Pulumi Registry +1

For the initial lab, enable management events and verify successful delivery before adding data-event selectors. Add only the S3 or Lambda data events you actually need, since these may incur additional charges.

### 9.5 Create the EventBridge detection rule

Define an event rule for selected EC2 security group changes:

```python
import json

security_group_rule = aws.cloudwatch.EventRule(
    "detect-security-group-changes",
    description="Detect security group ingress and egress modifications",
    event_pattern=json.dumps({
        "source": ["aws.ec2"],
        "detail-type": ["AWS API Call via CloudTrail"],
        "detail": {
            "eventSource": ["ec2.amazonaws.com"],
            "eventName": [
                "AuthorizeSecurityGroupIngress",
                "RevokeSecurityGroupIngress",
                "AuthorizeSecurityGroupEgress",
                "RevokeSecurityGroupEgress",
            ],
        },
    }),
)
```

Create an SNS topic and an email subscription, then add an EventBridge target referencing the topic. Ensure the SNS topic policy allows EventBridge to publish to it.

The email subscription requires confirmation by the recipient. An unconfirmed subscription will not deliver email notifications.

Pulumi's AWS provider documents EventBridge rules and targets as separate resources. Pulumi Registry +1

### 9.6 Deploy and validate

Preview the planned changes and deploy:

```bash
pulumi preview
pulumi up
```

After deployment, complete these checks:

* Confirm that the trail is logging and the S3 bucket is private.

* Confirm the email subscription to SNS.

* Create a disposable security group or use an existing lab-only group.

* Add or revoke a test ingress rule.

* Verify that EventBridge matches the API event and SNS delivers a notification.

* Open CloudTrail Event history and find the corresponding API call.

* Inspect `userIdentity`, `eventTime`, `eventName`, `sourceIPAddress`, and request parameters.

* Confirm that trail logs arrive in S3 and events are available in CloudWatch Logs.

* Verify log file validation and inspect the bucket's retention and access controls.

Event delivery is asynchronous, so allow time for records and notifications to appear. Do not assume that a missing immediate notification proves CloudTrail failed to record the event.

### 9.7 Clean up

When finished, remove the resources created by this lab:

```bash
pulumi destroy
```

Review the preview before confirming. Because the bucket uses `force_destroy=False`, Pulumi will not automatically empty a bucket containing objects. Decide explicitly whether to preserve the audit archive or remove its contents under your account's retention policy.

Also remember that destroying the lab resources does not necessarily remove email messages already delivered, historical records elsewhere, or resources created outside the Pulumi stack.

### 10\. Production considerations

Before adapting the lab to a real environment, address the following:

* Coverage: Use multi-Region trails and appropriate account or organization coverage.

* Event selection: Include both read and write management events where required, and explicitly enable selected data events.

* Least privilege: Separate the deployment role, CloudTrail delivery role, and audit-reader permissions.

* Integrity and retention: Enable log file validation, protect the S3 destination, and establish a documented retention policy.

* Monitoring the monitor: Alert on changes to the trail, logging status, bucket policy, and other audit-critical settings.

* Cost management: Avoid collecting unnecessary high-volume data events, and configure log retention intentionally.

* Incident response: Define how alerts are acknowledged, investigated, escalated, and resolved.

### 11\. Official documentation

* [CloudTrail event types and event records](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html?utm_source=chatgpt.com)

* [Logging management events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-management-events-with-cloudtrail.html?utm_source=chatgpt.com)

* [Logging data events](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/logging-data-events-with-cloudtrail.html?utm_source=chatgpt.com)

* [Analyzing log data with CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html?utm_source=chatgpt.com)

* [Using EventBridge with CloudTrail data events](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-log-s3-data-events.html?utm_source=chatgpt.com)

* [Pulumi AWS CloudTrail Trail resource](https://www.pulumi.com/registry/packages/aws/api-docs/cloudtrail/trail/?utm_source=chatgpt.com)

Module outcome: You can now design an AWS audit pipeline that records relevant activity, retains logs securely, detects selected resource changes, and supports investigations that establish what happened and which identity was involved.
