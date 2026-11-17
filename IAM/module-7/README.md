# Module 7 — Auditing and Troubleshooting AWS IAM

Level: Intermediate to advanced · Focus: incident investigation, least privilege, and production security

## Module objectives

By the end of this module, you'll be able to investigate failed AWS API calls, determine why a request was denied, identify excessive permissions, and use AWS's native analysis and auditing tools to improve security.

We'll cover the seven requested topics using current AWS practices, practical AWS CLI commands, Python where useful, and Pulumi where infrastructure provisioning is involved. No quizzes.

## 1. The IAM troubleshooting workflow

The most important skill in IAM troubleshooting is to identify the exact principal, action, resource, and request context before changing any policy.

A failed request doesn't automatically mean the identity policy is missing an `Allow`. The request might be blocked by an explicit deny, a permissions boundary, an organization policy, a resource policy, a trust policy, or a service-specific authorization rule.

![alt text](img/d06.png)

1\. Capture the failed API request

Principal · API action · Resource · Region · Timestamp · Error message

2\. Identify the credentials in use

IAM user, assumed role, federated session, or workload identity

3\. Inspect the authorization path

Identity policy · Resource policy · Trust policy · Boundaries · Organization controls

4\. Correlate evidence

CloudTrail · IAM Access Analyzer · Policy Simulator · Service-specific logs

5\. Apply and verify the smallest safe change

Correct the cause, test the intended access, and verify that unintended access remains denied.

The order matters. For example, adding `s3:GetObject` to an identity policy will not fix a request blocked by an explicit deny in an applicable policy.

## 2. IAM Policy Simulator and policy validation

These tools solve related but different problems. Don't treat them as interchangeable.

**IAM Policy Simulator**

Tests whether selected requests are allowed or denied under the policies and context represented in the simulation. Useful for testing policy changes before applying them.

Console: IAM → Policy Simulator · CLI: `aws iam simulate-principal-policy`

**IAM Access Analyzer policy validation**

Reviews policy documents for errors, security warnings, overly broad permissions, and recommendations. It helps answer whether a policy is well-formed and follows AWS security best practices.

CLI: `aws accessanalyzer validate-policy`

AWS recommends validating policies and reviewing the findings before using them to grant access.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS Identity and Access Management

+1



### 2.1 Simulate an identity's permissions

Suppose a role should read objects from `study-books` but must not delete them.

```
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/BookReader \
  --action-names s3:GetObject s3:DeleteObject \
  --resource-arns \
    arn:aws:s3:::study-books/fiction/example.pdf
```

Replace the account ID and role name with your actual values.

The output contains an `EvalDecision` for each tested action. Common results include:

- `allowed` — the simulated request is allowed.
- `implicitDeny` — no applicable permission grants access.
- `explicitDeny` — an applicable explicit Deny blocks access.

The simulator is useful for diagnosis, but it is not a guarantee of the outcome of a live API request. Not all service-specific conditions and authorization mechanisms are fully represented, and simulator support has limitations for resource policies and cross-account scenarios. Always verify critical changes in a controlled real environment.

### 2.2 Validate a policy document

Create `policy.json`:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::study-books/*"
    }
  ]
}
```

Run:

```
aws accessanalyzer validate-policy \
  --policy-document file://policy.json \
  --policy-type IDENTITY_POLICY
```

The response includes findings with fields such as `findingType`, `issueCode`, and `findingDetails`.

Review the findings rather than blindly fixing every warning. For example, an intentionally broad permission might be necessary in a narrowly controlled administrative workflow, but it should be justified and constrained appropriately.

### 2.3 Automate validation in CI/CD

You can run policy validation as part of your pull-request checks. This example assumes AWS CLI credentials have already been configured securely in the CI environment.

```py
import json
import subprocess
from pathlib import Path

policy = json.loads(Path("policy.json").read_text())

result = subprocess.run(
    [
        "aws", "accessanalyzer", "validate-policy",
        "--policy-document", json.dumps(policy),
        "--policy-type", "IDENTITY_POLICY",
        "--output", "json",
    ],
    capture_output=True,
    text=True,
    check=True,
)

response = json.loads(result.stdout)

for finding in response.get("findings", []):
    print(
        finding.get("findingType"),
        finding.get("issueCode"),
        finding.get("findingDetails", ""),
    )

if any(
    finding.get("findingType") == "ERROR"
    for finding in response.get("findings", [])
):
    raise SystemExit("IAM policy validation failed")
```

This example fails the pipeline on validation errors. You can extend it with explicit rules for security warnings, but don't automatically fail on every warning without defining the policy standards your team wants to enforce.

## 3. IAM Access Analyzer

IAM Access Analyzer helps you discover unintended access and validate whether policies meet security expectations.

It has several distinct capabilities, and each serves a different purpose.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS Identity and Access Management

+1


![alt text](img/d06-1.png)

External access analysis

Identifies supported resources that can be accessed by principals outside your zone of trust, such as another AWS account or the public. The analyzer's zone of trust depends on how it is configured.

Policy validation

Checks policy grammar, security issues, and recommended improvements before deployment.

Unused access analysis

Helps identify unused access and resources so you can reduce excessive permissions.

Policy generation

Uses observed CloudTrail activity to produce a policy template for further refinement.

### 3.1 Create an external-access analyzer

For example, you can create a regional analyzer that monitors supported resources in your account.

```
aws accessanalyzer create-analyzer \
  --analyzer-name security-review \
  --type ACCOUNT \
  --region us-east-1
```

Check findings:

```
aws accessanalyzer list-findings \
  --analyzer-arn arn:aws:access-analyzer:us-east-1:123456789012:analyzer/security-review
```

Use your actual analyzer ARN. Findings can be retrieved, reviewed, and investigated using the Access Analyzer console or API.

Important distinctions:

- An external-access finding does not automatically mean a resource has been exploited.
- A resource being publicly accessible does not prove that sensitive data was accessed.
- The absence of findings does not establish that your entire AWS environment is secure.
- Findings are limited to the resource types and analysis capabilities supported by the analyzer.

The objective is to determine whether the access is intended, document the decision, and remediate unintended access.

### 3.2 Review a finding

For a hypothetical S3 bucket, a finding might reveal that a bucket policy allows an external account to read objects.

The investigation should establish:

1. Which policy statement creates the access?
2. Which external principal is able to access the resource?
3. Is the external access part of a legitimate integration?
4. Is access restricted to the required actions and resources?
5. Should the policy be narrowed or removed?

If access is unintended, change the policy and then verify that the legitimate application still works.

## 4. CloudTrail: tracking identity activity

CloudTrail records activity associated with AWS identities and services, including API calls made through the console, AWS CLI, SDKs, and APIs.

The distinction between event types is critical.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS CloudTrail

+1



| Event type              | What it helps investigate                                                                            |
| ----------------------- | ---------------------------------------------------------------------------------------------------- |
| Management events       | IAM changes, role creation, policy attachment, EC2 configuration, and other control-plane operations |
| Data events             | Selected data-plane operations, such as supported S3 object activity, when configured                |
| Network activity events | Selected network-related API activity for supported services                                         |
| Insights events         | Unusual activity patterns for supported event types and configured monitoring                        |

CloudTrail Event history provides the previous 90 days of management events per Region. It is not a complete long-term audit archive and does not show data events. For longer retention, broader queries, or data-event monitoring, configure an appropriate trail or CloudTrail Lake event data store. Data events and advanced analysis features can incur charges.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS CloudTrail

+1



### 4.1 Find failed API calls

Start with Event history in the CloudTrail console, or use the CLI.

```
aws cloudtrail lookup-events \
  --lookup-attributes \
    AttributeKey=EventName,AttributeValue=PutObject \
  --max-results 20 \
  --region us-east-1
```

This searches for events named `PutObject` in the selected Region. It does not automatically mean that the returned events failed.

To inspect a specific event, examine fields such as:

- `eventTime`
- `eventSource`
- `eventName`
- `awsRegion`
- `userIdentity`
- `requestParameters`
- `errorCode`
- `errorMessage`

For example, a failed event might contain:

```
{
  "eventSource": "s3.amazonaws.com",
  "eventName": "PutObject",
  "errorCode": "AccessDenied",
  "userIdentity": {
    "type": "AssumedRole",
    "arn": "arn:aws:sts::123456789012:assumed-role/BookAPI/session-123"
  }
}
```

This hypothetical record tells us the request was made by an assumed role. It does not tell us, by itself, which policy caused the denial.

Important: not every denied request will necessarily be recorded in CloudTrail in the same way. Event availability and error detail depend on the service and event type. For S3 object operations, make sure the relevant data events are configured if you need that activity in your audit trail.

### 4.2 Query CloudTrail from Python

For incident investigations, Boto3 lets you automate event lookups and extract relevant details.

```py
import boto3
from datetime import datetime, timedelta, timezone

cloudtrail = boto3.client("cloudtrail", region_name="us-east-1")

end = datetime.now(timezone.utc)
start = end - timedelta(hours=6)

paginator = cloudtrail.get_paginator("lookup_events")

for page in paginator.paginate(
    LookupAttributes=[
        {
            "AttributeKey": "EventName",
            "AttributeValue": "PutObject",
        }
    ],
    StartTime=start,
    EndTime=end,
):
    for item in page["Events"]:
        event = item.get("CloudTrailEvent", "{}")
        import json
        event = json.loads(event)

        if event.get("errorCode"):
            print({
                "time": event.get("eventTime"),
                "service": event.get("eventSource"),
                "action": event.get("eventName"),
                "error": event.get("errorCode"),
                "message": event.get("errorMessage"),
                "identity": event.get("userIdentity", {}).get("arn"),
            })
```

This example retrieves recent `PutObject` events and prints those containing an error. It searches CloudTrail's lookupable event history, not every possible event type or every S3 data event.

For ongoing security monitoring, use an appropriately configured trail or event data store rather than relying on ad hoc lookups alone.

## 5. Access Advisor and last-accessed information

Access Advisor helps you determine which AWS services an identity has accessed and when. This information is useful when reviewing broad policies and planning least-privilege changes.

It answers a different question from CloudTrail:

- CloudTrail: What activity was recorded?
- Access Advisor: Which services or supported actions have been accessed, and when was access last recorded?

IAM Access Analyzer policy generation can use last-accessed information alongside CloudTrail activity.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS Identity and Access Management

+1



### 5.1 Inspect last-accessed information

Using the AWS CLI:

```
aws iam generate-service-last-accessed-details \
  --arn arn:aws:iam::123456789012:role/BookAPI
```

The command returns a job ID. Use it to retrieve the results:

```
aws iam get-service-last-accessed-details \
  --job-id YOUR_JOB_ID
```

The operation is asynchronous, so the job might initially be in progress. Poll the result until it completes, using a reasonable delay between requests.

You can also use the IAM console's Access Advisor tab for an identity or policy.

### 5.2 What does "never accessed" mean?

It does not automatically mean the permission can safely be removed.

Consider a role that is used only during quarterly disaster-recovery exercises. A 30-day or 90-day review could incorrectly suggest that some of its permissions are unnecessary.

Before removing permissions, consider:

- How long the identity has been observed.
- Seasonal, infrequent, and emergency workloads.
- Whether all relevant accounts and Regions are covered.
- Whether the action is needed for a rarely used operational workflow.
- Whether the application has been tested after narrowing permissions.

Use last-accessed information as evidence, not as an automatic deletion policy.

## 6. Generate a policy from observed activity

IAM Access Analyzer can generate a policy template from an IAM user's or role's CloudTrail activity. This is particularly useful when an existing role has broad permissions and you want to narrow them.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS Identity and Access Management

+1



The workflow is:

1. Enable a suitable CloudTrail trail and ensure the relevant activity is available.
2. Select the IAM role or user and the observation period, up to 90 days for this feature.
3. Generate the policy template.
4. Review the proposed actions, resources, and conditions. Fill in permissions the generated template cannot infer.
5. Test the refined policy in a nonproduction environment.
6. Deploy it gradually and monitor for failures before removing the original broad policy.

### 6.1 Important limitations

Policy generation is not a complete record of everything a workload may ever need.

In particular:

- Infrequent operations may not appear in the observation window.
- The feature does not identify action-level activity for data events such as S3 object operations in generated policies.
- `iam:PassRole` is not included in generated policies.
- Some services provide action-level detail, while others provide only service-level information.
- The generated policy may need resource ARNs, conditions, or additional actions to be completed manually.

AWS explicitly recommends using CloudTrail for auditing and policy generation for refining permissions—not the other way around.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS Identity and Access Management



Production recommendation: generate a candidate policy, review it, and deploy it through a controlled change. Don't automatically replace a working production policy with a generated template.

## 7. Debugging `AccessDenied`, trust-policy errors, and missing permissions

This is the most important practical section of the module.

### 7.1 Start by identifying the active identity

Run:

```
aws sts get-caller-identity
```

Example output:

```
{
  "UserId": "AROAXXXXXXXXXXXXX:book-api",
  "Account": "123456789012",
  "Arn": "arn:aws:sts::123456789012:assumed-role/BookAPI/book-api"
}
```

This confirms the AWS account and identity represented by the credentials being used.

If you expected a different role, stop here and investigate the credential provider chain before modifying any permissions.

For example, a developer may intend to use an SSO profile but accidentally run a command with environment-variable credentials or another CLI profile.

### 7.2 Common error patterns

| Error or symptom                           | What to inspect first                                                           |
| ------------------------------------------ | ------------------------------------------------------------------------------- |
| `no identity-based policy allows...`       | Attached policies, group policies, and action/resource matching                 |
| `explicit deny`                            | The named policy type and its applicable Deny statements                        |
| `no permissions boundary allows...`        | The permissions boundary attached to the user or role                           |
| `no service control policy allows...`      | Applicable organization policies                                                |
| `no resource-based policy allows...`       | The resource policy, where that service uses one                                |
| `not authorized to perform sts:AssumeRole` | Caller permissions, role trust policy, conditions, and organization controls    |
| `not authorized to perform iam:PassRole`   | The caller's permission to pass the specified role to the target service        |
| `ExpiredToken`                             | Credential expiration, refresh behavior, and the active credential source       |
| `InvalidClientTokenId` or signature errors | Credential validity, profile selection, signing configuration, and system clock |

AWS documents these distinct denial cases and recommends checking all applicable policy types rather than changing only the first policy you notice.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS Identity and Access Management

+1



### 7.3 Inspect the role's policies

For an IAM role named `BookAPI`:

```
aws iam list-attached-role-policies \
  --role-name BookAPI
```

Inspect inline policies:

```
aws iam list-role-policies \
  --role-name BookAPI
```

Retrieve a specific inline policy:

```
aws iam get-role-policy \
  --role-name BookAPI \
  --policy-name BookAPIInlinePolicy
```

Inspect the trust policy:

```
aws iam get-role \
  --role-name BookAPI
```

The `AssumeRolePolicyDocument` in the output is the trust policy.

These commands help establish what the role is allowed to do and who is allowed to assume it. You may still need to inspect permissions boundaries, organization policies, resource policies, session policies, and service-specific constraints.

### 7.4 Understand the difference between trust and permissions

A role has two conceptually distinct policy layers.

![alt text](img/d06-2.png)

Trust policy

Answers: Who or what is allowed to assume this role?

Example principal: a specific GitHub Actions OIDC provider, an AWS service, or another trusted AWS role.

STS issues temporary credentials if the assumption request is authorized.

Permissions policy

Answers: What can the resulting role session do?

Example permissions: read specified S3 objects or publish messages to a particular queue.

Adding `s3:GetObject` to a role's permissions policy does not fix a caller that is unable to assume the role in the first place.

Conversely, allowing a GitHub Actions identity to assume a deployment role does not automatically grant that role permission to deploy resources.

### 7.5 Debug `iam:PassRole`

`iam:PassRole` is frequently misunderstood.

It allows a principal to pass an existing IAM role to an AWS service that needs to use that role. It is not itself an API for assuming the role.

For example, a deployment pipeline might have permission to create a Lambda function but fail when it tries to associate an execution role with that function.

A narrowly scoped policy might look like this:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "iam:PassRole",
      "Resource": "arn:aws:iam::123456789012:role/BookApiLambdaExecutionRole",
      "Condition": {
        "StringEquals": {
          "iam:PassedToService": "lambda.amazonaws.com"
        }
      }
    }
  ]
}
```

This limits the role that can be passed and the service to which it can be passed. It does not, by itself, grant permission to create or update Lambda functions.

The execution role also needs its own permissions, and its trust policy must allow the Lambda service to assume it.

## 8. Detect public and unintended cross-account access

A secure IAM review must look beyond identity policies attached to users and roles.

Access can also be granted through resource-based policies, trust relationships, organization-level controls, and service-specific sharing mechanisms.

### 8.1 Review S3 bucket policies

Inspect a bucket policy:

```
aws s3api get-bucket-policy \
  --bucket study-books \
  --query Policy \
  --output text
```

Look for statements containing patterns such as:

```
{
  "Effect": "Allow",
  "Principal": "*",
  "Action": "s3:GetObject",
  "Resource": "arn:aws:s3:::study-books/*"
}
```

This is a warning sign because it grants broad principal scope. Whether the bucket is actually publicly accessible depends on the full authorization context, including applicable S3 Block Public Access settings, policy conditions, and other controls.

Likewise, an external-account principal may be intentional—for example, a partner service or centralized security account.

Do not assume every cross-account grant is a vulnerability. Confirm the intended ownership, business purpose, permitted actions, and resource scope.

### 8.2 Use Access Analyzer to review findings

For supported resources, configure an external-access analyzer and investigate its findings. For an account-wide security review, also inspect resource policies, role trust policies, and relevant organization controls.

When you discover unintended access:

1. Identify the exact statement or trust relationship granting it.
2. Determine whether it has been used, using the available audit evidence.
3. Remove or narrow the grant.
4. Validate the revised policy.
5. Test both legitimate access and the expected denial.
6. Record the remediation and monitor for recurrence.

Remember that finding an exposure and proving historical exploitation are different tasks. Access Analyzer and CloudTrail provide complementary evidence.

## 9. Hands-on lab — Investigate failed API calls and tighten an overprivileged policy

Recommended environment: a dedicated AWS sandbox account · AWS CLI v2 · Python/Boto3 · Pulumi with Python

### Lab scenario

Your hypothetical FastAPI book recommendation application uses an IAM role named `BookAPI`. The role currently has excessive S3 permissions. A recent application deployment also reports `AccessDenied` when reading a book object.

Your task is to establish the cause, narrow the permissions, and verify the result.

### Step 1 — Confirm the identity

```
aws sts get-caller-identity
```

Make sure you're using the intended account and role.

### Step 2 — Investigate the failed request

Search CloudTrail Event history for the relevant API action and timestamp. Inspect the event's identity, resource, Region, and error fields.

If the failure concerns S3 object access, confirm that the appropriate S3 data events were being recorded. Event history alone won't show those object-level events.

### Step 3 — Inspect current permissions

```
aws iam list-attached-role-policies \
  --role-name BookAPI

aws iam list-role-policies \
  --role-name BookAPI

aws iam get-role \
  --role-name BookAPI
```

Review the attached policies, inline policies, trust policy, and permissions boundary if present. Also check relevant resource policies and organization controls.

### Step 4 — Replace broad S3 access with a narrower policy

For an application that only needs to read book objects, a candidate policy could be:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ReadBookObjects",
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::study-books/books/*"
    }
  ]
}
```

This policy grants object reads under the `books/` prefix. It does not grant bucket listing, uploads, or deletions.

If your application needs to list the bucket, add `s3:ListBucket` as a separate permission scoped to the bucket ARN, with an appropriate prefix condition. Don't add it unless the application actually requires it.

### Step 5 — Validate and simulate

Save the policy as `book-reader-policy.json`.

```
aws accessanalyzer validate-policy \
  --policy-document file://book-reader-policy.json \
  --policy-type IDENTITY_POLICY
```

Then test the role's permissions:

```
aws iam simulate-principal-policy \
  --policy-source-arn arn:aws:iam::123456789012:role/BookAPI \
  --action-names s3:GetObject s3:DeleteObject \
  --resource-arns \
    arn:aws:s3:::study-books/books/example.pdf
```

The intended result is that reading the specified object is allowed by the simulated policy set, while deleting it is denied. If the result differs, investigate the role's policies and the simulator's limitations before making changes.

### Step 6 — Manage the policy with Pulumi

For infrastructure that is already managed by Pulumi, you can define a customer-managed IAM policy in Python.

Install the Pulumi AWS provider package in your project's virtual environment:

```
pip install pulumi pulumi-aws
```

Example `__main__.py`:

```py
import json

import pulumi
import pulumi_aws as aws

account = aws.get_caller_identity()

policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadBookObjects",
            "Effect": "Allow",
            "Action": ["s3:GetObject"],
            "Resource": (
                f"arn:aws:s3:::{'study-books'}/books/*"
            ),
        }
    ],
}

book_reader_policy = aws.iam.Policy(
    "book-reader-policy",
    description="Read-only access to book objects",
    policy=json.dumps(policy_document),
)

pulumi.export("policy_arn", book_reader_policy.arn)
pulumi.export("account_id", account.account_id)
```

This creates a managed policy, but does not attach it to the role. That separation is intentional: review the generated policy and your existing role configuration before changing access.

In a real project, manage the role and policy attachment through the same Pulumi stack when feasible. If the role already exists outside Pulumi, import it or manage the attachment deliberately rather than creating a duplicate role.

Review the proposed changes first:

```
pulumi preview
```

After reviewing the plan and confirming that the stack targets the intended sandbox account, apply it:

```
pulumi up
```

The actual deployment requires working AWS credentials and the appropriate IAM permissions. If you attach the new policy to an existing role, remove or narrow the old broad grant only after accounting for all legitimate dependencies.

### Step 7 — Verify the fix

Test the application with its normal credentials:

- Reading an authorized book object should succeed.
- Reading an object outside the permitted prefix should not be allowed by this policy.
- Deleting objects should remain denied.
- Any remaining `AccessDenied` error should be investigated rather than fixed with broad permissions.

Record the result and retain the relevant CloudTrail evidence.

### Lab completion criteria

- The failing identity and request have been identified.
- The denial has been traced to a specific policy or authorization layer, or the remaining uncertainty is documented.
- The revised policy passes validation.
- Unnecessary permissions have been removed without breaking required application behavior.
- The change is managed and reviewable through Pulumi where applicable.

## 10. Production checklist

Before considering an IAM troubleshooting or access-review task complete, use this checklist.

- Confirm the actual caller with `aws sts get-caller-identity`.
- Correlate the failure with CloudTrail evidence where available.
- Check all relevant identity, resource, trust, session, boundary, and organization policies.
- Validate policy documents with IAM Access Analyzer.
- Use the Policy Simulator as supporting evidence, not a substitute for live verification.
- Review last-accessed information with an appropriate observation window.
- Use policy generation as a starting point, not an automatic source of truth.
- Investigate public and cross-account findings and document intended exceptions.
- Deploy changes through reviewed infrastructure-as-code updates.
- Verify both required access and prohibited access after deployment.

## Official documentation

These are the primary references for this module:

- [Troubleshoot IAM AccessDenied errors](https://docs.aws.amazon.com/IAM/latest/UserGuide/troubleshoot_access-denied.html) — denial types and diagnostic procedures.
- [IAM Access Analyzer](https://docs.aws.amazon.com/IAM/latest/UserGuide/what-is-access-analyzer.html) — policy validation, external access analysis, and related capabilities.
- [IAM policy validation](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_policy-validator.html) — policy checks and findings.
- [Generate policies from CloudTrail activity](https://docs.aws.amazon.com/us_en/IAM/latest/UserGuide/access-analyzer-policy-generation.html) — policy generation and its limitations.
- [CloudTrail Event history](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/view-cloudtrail-events.html) — querying and inspecting management events.
- [IAM last-accessed information](https://docs.aws.amazon.com/IAM/latest/UserGuide/access_policies_last-accessed.html) — using access history to support least privilege.

The central lesson of Module 7: investigate first, change permissions deliberately, and verify the outcome. Reliable IAM operations depend on evidence-driven troubleshooting and continuous least-privilege review—not repeatedly attaching broader policies until an error disappears.