### Module 5 — AWS Health and Incident Awareness

AWS Operations and Observability · Module 5 of 8

### 1\. Learning objectives

By the end of this module, you should understand how to:

* Identify AWS service disruptions, account-specific events, scheduled maintenance, and planned lifecycle changes.

* Distinguish AWS infrastructure incidents from application-level failures.

* Understand AWS Health Dashboard, organizational views, and delegated administration.

* Route AWS Health events through Amazon EventBridge to Amazon SNS and other supported targets.

* Identify affected resources and prioritize incidents by operational impact.

* Use AWS Health API capabilities where available.

* Design incident-response runbooks that guide investigation, escalation, mitigation, and recovery.

* Provision the notification infrastructure with Pulumi rather than Terraform.

### 2\. AWS Health fundamentals

AWS Health provides information about AWS service availability, operational issues, scheduled changes, and events that may affect your account or resources.

A key distinction is that AWS Health is not a replacement for application monitoring. CloudWatch tells you how your workload is behaving; AWS Health provides information about relevant issues and changes within AWS.

### Where AWS Health fits into observability

AWS Health

Reports AWS service issues, account-specific events, scheduled changes, and affected resources.

Amazon CloudWatch

Detects workload symptoms through metrics, logs, alarms, and dashboards.

Amazon EventBridge

Matches events against rules and routes them to notification, automation, or incident-management targets.

For example, suppose an application running on EC2 begins returning HTTP 5xx errors. CloudWatch might trigger an alarm because the error rate has increased. AWS Health may separately report an EC2 availability issue affecting the Availability Zone in which the instance runs.

Correlating these signals helps an operator determine whether the application has a local defect, an infrastructure dependency is degraded, or both problems are occurring together.

### 3\. AWS Health Dashboard and event categories

### 3.1 AWS Health Dashboard

The AWS Health Dashboard presents information relevant to your AWS environment. The exact events visible depend on the event type, affected account and Region, and your AWS support and service entitlements.

The main categories to understand are:

| Event category          | What it tells you                                     | Operational response                                                       |
| ----------------------- | ----------------------------------------------------- | -------------------------------------------------------------------------- |
| Service health          | AWS service disruption or degradation                 | Check affected services and Regions; assess workload impact                |
| Account-specific events | Issues or changes relevant to your account            | Identify affected resources and take account-specific action               |
| Scheduled changes       | Planned maintenance or service changes                | Review deadlines, prepare mitigations, and schedule work                   |
| Lifecycle events        | Upcoming changes that may require action on resources | Identify affected resources and plan upgrades, migrations, or replacements |

AWS Health event information may include an event type, status, start and end times, affected entities, and recommended actions. Available fields vary by event.

### 3.2 Public service health versus account-specific events

Do not assume that a public service status page provides all the information needed for incident response.

* Public service health information describes broader AWS service availability.

* Account-specific AWS Health events provide information about issues or changes relevant to your account and can identify affected resources.

For production operations, account-specific events are particularly valuable because they help connect AWS-reported conditions to actual infrastructure.

### 3.3 Event lifecycle and prioritization

An AWS Health event can change as an incident develops. For example, an event may be open, updated with additional information, and later closed.

An incident workflow should therefore account for event updates rather than treating every incoming message as an entirely new incident.

Prioritize events according to:

* The resources and services affected.

* The business criticality of those resources.

* Whether the event is active or scheduled.

* The potential for an outage, data loss, or security impact.

* The required response deadline and available mitigation options.

AWS Health event severity and your internal incident priority are not necessarily the same thing. Your organization should map AWS event information to its own incident-management policy.

### 4\. EventBridge integration for AWS Health

Amazon EventBridge is the main building block for an event-driven AWS Health notification workflow.

AWS Health sends events directly to EventBridge. A rule evaluates each event against an event pattern and invokes the configured target when the pattern matches. AWS documents durable delivery with at-least-once delivery attempts, so consumers should tolerate duplicate notifications. AWS Health +1

### 4.1 Event flow

AWS Health

Service issues · Scheduled changes · Account events

Amazon EventBridge rule

Match event source, type, category, service, and scope

Amazon SNS

Email and notifications

Automation

Lambda, SQS, or supported targets

Incident response

Triage · Identify affected resources · Mitigate · Recover

### 4.2 Understand the event schema

An AWS Health event delivered to EventBridge commonly includes these fields:

| Field                    | Purpose                                                                         |
| ------------------------ | ------------------------------------------------------------------------------- |
| source                   | Identifies the producer as aws.health                                           |
| detail-type              | Identifies the event as AWS Health Event                                        |
| detail.service           | Identifies the affected AWS service                                             |
| detail.eventTypeCode     | Identifies the specific event type                                              |
| detail.eventTypeCategory | Indicates an issue, scheduled change, or another event category                 |
| detail.eventScopeCode    | Distinguishes ACCOUNT_SPECIFIC from PUBLIC events                               |
| detail.eventRegion       | Identifies the affected Region                                                  |
| detail.affectedAccount   | Identifies the affected account                                                 |
| detail.affectedEntities  | May identify affected resources and their statuses                              |
| detail.actionability     | May indicate whether action is required, potentially required, or informational |

The schema varies by event, and some events have no affected-resource list. Also, the top-level EventBridge `region` is the delivery Region, not necessarily the Region affected by the event. AWS Health +1

### 4.3 Example event pattern

This rule matches account-specific AWS Health events that are issues or scheduled changes:

```json
{
  "source": ["aws.health"],
  "detail-type": ["AWS Health Event"],
  "detail": {
    "eventScopeCode": ["ACCOUNT_SPECIFIC"],
    "eventTypeCategory": [
      "issue",
      "scheduledChange"
    ]
  }
}
```

This is a useful starting point, but it intentionally matches a broad set of events. In a production environment, you may create separate rules for high-priority incidents, scheduled maintenance, and informational updates.

Important: Use the exact source value `aws.health`, not a wildcard such as `aws.health*`. AWS also recommends appropriate backup-region rules for public Health events and deduplication across backup deliveries. AWS Health +1

### 5\. Organizational views and delegated administration

In a multi-account AWS environment, a centralized operational team needs visibility into Health events across the organization.

AWS Health organizational view aggregates events from member accounts. An organization can designate an authorized delegated administrator for supported organizational Health workflows, reducing the need to manage all notifications independently in every account. AWS Health +1

A typical architecture is:

* Member accounts produce account-specific Health events.

* AWS Organizations and AWS Health organizational view provide centralized visibility.

* A management or delegated administrator account receives supported organizational events.

* EventBridge rules route relevant events to the correct operational teams.

* Incident tooling associates events with affected accounts, services, and resources.

Do not assume that a normal EventBridge rule in one account automatically receives every event from all member accounts. Organizational aggregation must be configured separately, and feature availability and permissions must be checked.

### 6\. Incident triage and operational runbooks

A notification is only useful if it tells the operator what to do next.

### 6.1 A repeatable incident-response workflow

* Detect

    Receive an AWS Health event or a CloudWatch alarm.

* Classify

    Identify the affected service, event category, scope, actionability, and timeline.

* Correlate

    Compare the event with application metrics, logs, deployment history, and related CloudTrail activity.

* Determine impact

    Map affected resources to workloads and business services. Verify whether the workload is actually degraded.

* Mitigate

    Follow approved procedures, such as shifting traffic, using healthy capacity, or preparing for scheduled maintenance.

* Recover and verify

    Confirm service recovery using application-level indicators and CloudWatch alarms.

* Document

    Record the timeline, actions, root cause where known, and preventive improvements.

### 6.2 Example operational runbook

### Runbook: AWS reports an EC2 maintenance event

Trigger

An account-specific AWS Health event indicates scheduled EC2 maintenance or an instance lifecycle action.

Investigate

Identify the instance, affected Region, maintenance window, workload owner, and whether the instance is replaceable.

Mitigate

Validate redundancy and health checks. If supported by the workload design, shift traffic or replace capacity using the approved procedure.

Verify

Confirm the service is healthy, alarms have cleared, and the scheduled action has been handled.

Close

Document the response and update operational records. Do not close an incident merely because the AWS Health event itself is closed.

### 6.3 Distinguishing infrastructure incidents from application failures

| Signal                                                     | Possible interpretation                               | Next step                                                           |
| ---------------------------------------------------------- | ----------------------------------------------------- | ------------------------------------------------------------------- |
| AWS Health event plus rising application errors            | An AWS event may be affecting the workload            | Correlate service, Region, resources, and timestamps                |
| No Health event, but CPU and latency increase              | Application saturation or another workload issue      | Inspect metrics, logs, dependencies, and recent changes             |
| Health event exists, but application metrics remain normal | Potential impact without current workload degradation | Assess exposure and prepare mitigation                              |
| Several unrelated services fail simultaneously             | Shared dependency or broader infrastructure issue     | Investigate network paths, DNS, identity, and regional dependencies |

An AWS Health event is evidence to investigate, not automatic proof of root cause. Likewise, the absence of a Health event does not prove that AWS infrastructure is healthy in every respect.

### 7\. AWS Health API and feature availability

The AWS Health API supports programmatic access to Health events, including workflows that retrieve events, affected entities, and organizational information.

As documented by AWS, API access requires an eligible support plan. The current documentation lists Business, Enterprise On-Ramp, and Enterprise Support; verify the applicable plan and feature entitlements before building an API-dependent workflow. AWS Health

For this module, prioritize EventBridge integration first. It is sufficient for many notification workflows and avoids making direct API polling a prerequisite.

Use the API when you need to retrieve event history, enumerate affected entities, build custom reporting, or integrate Health information with an incident-management system.

### 8\. Lab 5 — Create an AWS Health Event Notification Workflow

Estimated duration: 60–90 minutes

Python · Pulumi · AWS EventBridge · SNS

### Lab objectives

Build an event-driven notification system that detects selected AWS Health events, sends notifications to an operator, and provides a repeatable incident-response procedure.

### Architecture

AWS Health

Account-specific events

EventBridge rule

Match issues and scheduled changes

SNS topic

Publish matching event notifications

Email subscriber

Review event and execute runbook

### Step 1 — Prepare the environment

Install the Pulumi CLI, Python, and the Pulumi AWS provider. Configure an AWS profile with permissions to provision SNS, EventBridge, and the associated IAM permissions and policies.

Create a project:

```bash
mkdir aws-health-alerts
cd aws-health-alerts

pulumi new aws-python
```

Choose an AWS Region supported by the services used in the lab. AWS Health EventBridge monitoring is Region-sensitive, so the selected Region must be configured deliberately.

### Step 2 — Define the infrastructure with Pulumi

Install the Python dependencies in the project environment:

```bash
uv add pulumi pulumi-aws
```

Replace the contents of `__main__.py` with the following example.

```python

import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
notification_email = config.require("notificationEmail")

# SNS notification destination.
topic = aws.sns.Topic(
    "aws-health-alerts",
    display_name="AWS Health Alerts",
)

subscription = aws.sns.TopicSubscription(
    "aws-health-email-subscription",
    topic=topic.arn,
    protocol="email",
    endpoint=notification_email,
)

# Permit EventBridge to publish to this SNS topic.
topic_policy = aws.sns.TopicPolicy(
    "aws-health-topic-policy",
    arn=topic.arn,
    policy=pulumi.Output.json_dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "AllowEventBridgePublish",
            "Effect": "Allow",
            "Principal": {
                "Service": "events.amazonaws.com"
            },
            "Action": "sns:Publish",
            "Resource": topic.arn,
        }],
    }),
)

# Match account-specific incidents and scheduled changes.
event_pattern = {
    "source": ["aws.health"],
    "detail-type": ["AWS Health Event"],
    "detail": {
        "eventScopeCode": ["ACCOUNT_SPECIFIC"],
        "eventTypeCategory": [
            "issue",
            "scheduledChange",
        ],
    },
}

rule = aws.cloudwatch.EventRule(
    "aws-health-event-rule",
    description="Notify operators about AWS Health events",
    event_pattern=json.dumps(event_pattern),
)

target = aws.cloudwatch.EventTarget(
    "aws-health-sns-target",
    rule=rule.name,
    arn=topic.arn,
    opts=pulumi.ResourceOptions(
        depends_on=[topic_policy, subscription]
    ),
)

pulumi.export("snsTopicArn", topic.arn)
pulumi.export("eventRuleName", rule.name)
pulumi.export("notificationEmail", subscription.endpoint)
```

Configure the email address and deploy:

```bash
pulumi config set notificationEmail ops@example.com

pulumi preview
pulumi up
```

Replace `ops@example.com` with an email address you control.

Important implementation notes:

* Confirm the SNS subscription using the email AWS sends. Creating the subscription alone does not complete email delivery setup.

* This example matches account-specific issues and scheduled changes. It does not include public service health events.

* The SNS topic policy grants the EventBridge service permission to publish to this topic. In a production deployment, apply the appropriate least-privilege conditions and validate the policy against your organization's security requirements.

* This example creates a single-Region notification workflow. Multi-Region coverage and organization-wide event aggregation require additional configuration.

### Step 3 — Validate the EventBridge rule

In the AWS Console, open Amazon EventBridge and inspect the rule created by Pulumi.

Confirm that:

* The event source is `aws.health`.

* The event detail type is `AWS Health Event`.

* The event pattern filters for the expected categories and scope.

* The SNS topic is configured as the target.

* The target can be invoked and the SNS subscription is confirmed.

You can use EventBridge's event-pattern testing functionality with a representative AWS Health event payload to check whether the pattern matches. You can also inspect the event schema and sample payloads in the [official AWS Health EventBridge schema reference](https://docs.aws.amazon.com/health/latest/ug/aws-health-events-eventbridge-schema.html?utm_source=chatgpt.com).

Testing limitation: A fabricated sample event can validate your pattern, but it does not prove that AWS Health will deliver a real event to the rule. Do not assume that a synthetic event submitted through EventBridge reproduces an authentic AWS Health event.

AWS notes that public health events can take up to an hour to begin flowing after a rule is created. AWS Health

### Step 4 — Test the notification destination separately

To test email delivery without waiting for an actual AWS Health event, publish a controlled test message directly to the SNS topic:

```bash
aws sns publish \
  --topic-arn YOUR_SNS_TOPIC_ARN \
  --subject "AWS Health workflow test" \
  --message "Test notification: review the AWS Health incident runbook."
```

This validates the SNS notification destination, not the EventBridge-to-SNS rule or the AWS Health event source.

For end-to-end verification, wait for a suitable genuine AWS Health event, or use a representative event-pattern test alongside the independent SNS test. Record which components were verified.

### Step 5 — Write the incident runbook

Create `runbook.md` with an operational procedure such as the following:

# AWS Health Incident Runbook

## Trigger
An AWS Health notification is received for an account-specific issue or scheduled change.

## 1. Identify the event
- Record the event type, status, affected service, and affected Region.
- Identify the affected account and resources, if provided.
- Review the event description, timeline, and recommended AWS actions.

## 2. Assess impact
- Identify the application or business service that depends on the affected resources.
- Check CloudWatch alarms, application logs, and service health indicators.
- Determine whether the event is causing an active incident or requires preventive action.

## 3. Respond
- Escalate according to the incident severity and ownership policy.
- For scheduled changes, plan and validate mitigation before the event window.
- For active incidents, follow approved recovery procedures.
- Do not execute destructive remediation solely because an AWS Health event was received.

## 4. Verify recovery
- Confirm that the affected workload is healthy.
- Review relevant CloudWatch alarms and application-level indicators.
- Confirm that any required maintenance or mitigation has been completed.

## 5. Document
- Record the timeline, impact, actions, and outcome.
- Identify follow-up work and preventive improvements.
- Close the internal incident only after the recovery criteria are satisfied.

### Step 6 — Deploy safely and clean up

Inspect the deployed resources and confirm that the rule, SNS topic, topic policy, target, and subscription are present.

When finished, remove the lab infrastructure:

```bash
pulumi destroy
```

The SNS subscription confirmation email and the deployment's AWS resources should be accounted for during cleanup. Confirm that no lab resources remain unexpectedly.

### 9\. Production considerations

Before adapting this workflow to production, account for the following:

* Duplicate events: AWS Health delivery is at least once, so downstream processing should be idempotent.

* Regional coverage: Create and validate the required rules in the Regions relevant to the workload; account for AWS's documented backup-Region behavior.

* Organization-wide events: Configure AWS Health organizational view and delegated administration when centralized multi-account visibility is needed.

* Security: Restrict who can modify rules, targets, SNS subscriptions, and notification policies.

* Observability: Monitor EventBridge rule matches and target delivery failures. Configure retries and a dead-letter queue where appropriate for supported targets.

* Cost and cleanup: Remove unnecessary resources and review service-specific charges after the lab.

* API access: Check AWS Support eligibility before building a workflow that directly calls the AWS Health API.

### 10\. Key takeaways

AWS Health helps operators anticipate and respond to AWS service issues and account-specific changes. EventBridge turns Health events into actionable workflows, SNS provides a straightforward notification destination, and runbooks help operators translate notifications into consistent incident response.

The essential operational principle is to correlate AWS Health events with workload telemetry before deciding on a response. This reduces unnecessary remediation while improving readiness for genuine infrastructure incidents and scheduled changes.

### Official references

* [Monitoring AWS Health events with EventBridge](https://docs.aws.amazon.com/health/latest/ug/cloudwatch-events-health.html?utm_source=chatgpt.com)

* [AWS Health EventBridge event schema](https://docs.aws.amazon.com/health/latest/ug/aws-health-events-eventbridge-schema.html?utm_source=chatgpt.com)

* [Public and account-specific AWS Health events](https://docs.aws.amazon.com/health/latest/ug/about-public-events.html?utm_source=chatgpt.com)

* [AWS Health API reference](https://docs.aws.amazon.com/health/latest/APIReference/Welcome.html?utm_source=chatgpt.com)

* [Pulumi AWS provider reference](https://www.pulumi.com/registry/packages/aws/?utm_source=chatgpt.com)
