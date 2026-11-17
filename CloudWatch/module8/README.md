### Module 8 — Capstone: Production Operations and Incident Response

AWS Operations and Observability · Pulumi · Python

### 1\. Module overview

The goal of this module is to bring together the operational services covered throughout the course and build a production-like AWS environment that can detect failures, collect evidence, notify operators, support recovery, and control costs.

You will work with a small application hosted on Amazon EC2 and integrate it with CloudWatch, CloudTrail, AWS Config, Systems Manager, EventBridge, SNS, and AWS Budgets.

By the end, you will have a reusable operational architecture, a Pulumi project for provisioning its infrastructure, and an incident report documenting a simulated production failure.

### Learning objectives

* Design an operational architecture with clear responsibilities for each AWS service.

* Detect application and infrastructure failures using CloudWatch.

* Correlate logs, metrics, API activity, and AWS Health events during an incident.

* Diagnose configuration drift and remediate selected problems with Systems Manager.

* Define meaningful reliability indicators and service-level objectives.

* Implement least-privilege IAM permissions and auditable operational procedures.

* Organize Pulumi stacks, configuration, secrets, state, previews, and updates safely.

* Apply cost controls and clean up resources after the capstone.

### 2\. Production operations architecture

![A multi-dimensional approach helps you proactively prepare for failures, Part 3: Operations and process resiliency | AWS Architecture Blog](https://images.openai.com/static-rsc-4/Dv_qrK5-VCeIK4lozGPYC0eaGuWHU6JdmNZJ50lGjWF-36z56D8Mr78dl7TABzotusYp6Vducxu4YOpGKcTfuf_cEVioHZruIZ1XqmGWPrbt5VQih3cMngoa6cM5D875iIML-Jk_0hsimS7_RyCCFRSY_qLmAJod4_Vxj8Y3dE8fmzYGP-bkKjtCmYiu56m0?purpose=fullsize)

The workload is an HTTP application running on EC2. CloudWatch monitors its performance and collects logs, while other AWS services provide evidence and operational controls.

Application workload

EC2 · HTTP health endpoint · Application and system logs

CloudWatch

Metrics, logs, dashboards, alarms

CloudTrail + Config

API audit history and configuration compliance

Systems Manager

Secure diagnostics and controlled recovery

AWS Health

AWS service and account events

Event routing and response

EventBridge · SNS · Operator runbooks

### Service responsibilities

| Service         | Responsibility                                                         |
| --------------- | ---------------------------------------------------------------------- |
| CloudWatch      | Detect performance degradation, collect logs, and trigger alarms.      |
| CloudTrail      | Establish which identity performed an API operation and when.          |
| AWS Config      | Evaluate resource configuration against compliance rules.              |
| Systems Manager | Diagnose managed instances and perform controlled operational actions. |
| AWS Health      | Identify relevant AWS service issues and account-specific events.      |
| EventBridge     | Route supported events to appropriate targets.                         |
| SNS             | Deliver notifications to configured subscribers.                       |
| AWS Budgets     | Notify operators when spending or usage thresholds are reached.        |
| Pulumi          | Provision and maintain the operational infrastructure as code.         |

Important distinction: These services do not automatically share every type of event. CloudWatch alarms, CloudTrail events, Config compliance changes, and AWS Health events have different event formats and delivery mechanisms. Integration requires explicit rules, permissions, and targets.

### 3\. Incident response workflow

A reliable operational process follows a consistent sequence. The objective is not merely to restart a failed application, but to preserve evidence, identify the cause, restore service safely, and prevent recurrence.

### 1

Detect

CloudWatch alarm, application error, or relevant AWS Health event.

### 2

Triage

Determine severity, customer impact, affected resources, and incident scope.

### 3

Investigate

Correlate application logs, metrics, CloudTrail API events, and Config history.

### 4

Mitigate

Use an approved Systems Manager procedure or another controlled recovery action.

### 5

Verify

Confirm the health endpoint works and the relevant metrics return to acceptable levels.

### 6

Learn

Document the timeline, root cause, corrective actions, and follow-up owners.

AWS supports routing selected service events through EventBridge, and CloudTrail can provide the API-level evidence needed to investigate operational actions. These are complementary mechanisms, not substitutes for one another. AWS Systems Manager +2

### Incident severity and response

| Severity | Example                                         | Response                                                   |
| -------- | ----------------------------------------------- | ---------------------------------------------------------- |
| SEV-1    | Workload unavailable with major customer impact | Immediate response, rapid mitigation, frequent updates     |
| SEV-2    | Significant degradation or repeated failures    | Prioritized investigation and controlled recovery          |
| SEV-3    | Isolated error with limited impact              | Diagnose and resolve through normal operational procedures |
| SEV-4    | Non-urgent configuration or monitoring issue    | Schedule corrective work and track it to completion        |

These are example severity levels for the course, not official AWS classifications. A real organization should define its own impact criteria and escalation policies.

### 4\. Reliability indicators and service-level objectives

Observability becomes more useful when monitoring measures the outcomes users care about, rather than collecting metrics without a clear purpose.

### Example service indicators

| Indicator      | Measurement                                          | Example objective  |
| -------------- | ---------------------------------------------------- | ------------------ |
| Availability   | Successful health checks / total valid health checks | 99.9% over 30 days |
| Latency        | HTTP response time at the 95th percentile            | p95 below 300 ms   |
| Error rate     | Failed requests / total requests                     | Below 1%           |
| Detection time | Time from incident onset to alert                    | Under 2 minutes    |
| Recovery time  | Time from incident onset to service recovery         | Under 15 minutes   |

These values are illustrative targets, not guarantees. A single EC2 instance cannot provide the same availability characteristics as a properly designed multi-AZ architecture.

### SLI, SLO, and SLA

* SLI (Service-Level Indicator): The actual measurement, such as successful requests divided by total requests.

* SLO (Service-Level Objective): The target for an indicator, such as 99.9% availability.

* SLA (Service-Level Agreement): A formal commitment, potentially including remedies when agreed targets are missed.

For an availability SLO of 99.9%, the theoretical error budget over a 30-day period is approximately 43.2 minutes of unavailability, assuming continuous service and a time-based availability definition.

### Reducing alert fatigue

Configure alarms around actionable symptoms:

* Alert on sustained failures rather than every transient spike.

* Use evaluation periods and appropriate treatment of missing data.

* Separate warning-level degradation from critical service outages.

* Include resource identifiers, alarm names, timestamps, and runbook references in notifications.

* Avoid creating multiple independent alerts for the same underlying failure unless each provides distinct diagnostic value.

For example, a CPU spike alone might not justify a critical alert. A sustained CPU spike combined with elevated latency and an increased error rate provides stronger evidence of a user-facing problem.

### 5\. Pulumi project structure and safe operations

Use the standard Pulumi AWS provider with Python for this capstone. Pulumi allows infrastructure to be expressed in application-language code, with reusable resources, stack-specific configuration, and managed deployment state. Pulumi Docs +1

A maintainable project can be organized as follows:

```text
aws-operations-capstone/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
├── __main__.py
├── config.py
├── iam.py
├── workload.py
├── monitoring.py
├── audit.py
├── compliance.py
├── operations.py
├── notifications.py
├── costs.py
└── runbooks/
    ├── application-unavailable.md
    ├── high-error-rate.md
    └── configuration-drift.md
```

The files have distinct responsibilities:

* `config.py`: Read stack configuration and validate required values.

* `iam.py`: Define narrowly scoped instance and service roles.

* `workload.py`: Provision the EC2 instance, networking, and application configuration.

* `monitoring.py`: Create log groups, alarms, and dashboards.

* `audit.py`: Configure CloudTrail and its log destination.

* `compliance.py`: Configure AWS Config recording and selected rules.

* `operations.py`: Set up Systems Manager permissions and operational resources.

* `notifications.py`: Create SNS topics, subscriptions, and supported EventBridge rules.

* `costs.py`: Define budget resources and alert thresholds where supported.

### Pulumi lifecycle

Use a deliberate deployment process rather than applying every change immediately.

```bash
# Create the project using the Python AWS template
pulumi new aws-python

# Select the stack used for development
pulumi stack select dev

# Preview planned infrastructure changes
pulumi preview

# Deploy the reviewed changes
pulumi up

# Inspect stack outputs
pulumi stack output

# Preview resource removal before cleanup
pulumi destroy --preview
```

The final command's preview flag is not supported uniformly across all Pulumi CLI versions and command variants. For cleanup, use the installed CLI's documented preview or confirmation workflow; `pulumi destroy` normally provides a confirmation step.

### Configuration and state management

Keep environment-specific values in stack configuration rather than scattering them through source files.

Example configuration:

```bash
pulumi config set aws:region eu-west-2
pulumi config set instanceType t3.micro
pulumi config set logRetentionDays 7
```

These values are examples for a development stack; select the Region, instance type, and retention period appropriate to your account.

For sensitive configuration, use encrypted Pulumi configuration:

```bash
pulumi config set --secret appToken
```

The command prompts for a value. Avoid committing plaintext secrets, AWS credentials, or sensitive stack configuration to source control.

Safe operations should include:

* Review `pulumi preview` before each significant update.

* Use separate stacks for development and production.

* Keep the state backend durable and access-controlled.

* Restrict who can change production infrastructure.

* Review resource replacements and deletions carefully.

* Use temporary AWS credentials where practical.

* Tag resources with an owner, environment, and project identifier.

* Verify that the deployed infrastructure matches the intended configuration.

### 6\. Lab 8 — Operate a Production-Like AWS Workload

Estimated duration: 4–6 hours

IaC: Pulumi with Python

Environment: One AWS Region, a development stack

### Lab architecture

For cost-conscious learning, use one EC2 instance and a small set of operational services. Use the default VPC if suitable, or an existing development VPC. Do not build a multi-AZ production topology merely to complete this lab.

EC2 application

HTTP health endpoint and controlled failure switch

CloudWatch

Logs, metrics, alarms, dashboard

CloudTrail + Config

Audit history and compliance

Systems Manager

Secure diagnostics and recovery

Budgets

Spending notifications

SNS notifications and incident runbook

### Step 1 — Create the Pulumi foundation

Initialize a Python project and install the AWS provider:

```bash
pulumi new aws-python
python -m pip install pulumi pulumi-aws
pulumi stack init dev
pulumi config set aws:region eu-west-2
```

Use a virtual environment and pin compatible dependency versions in `requirements.txt` for repeatable deployments.

Configure the AWS CLI or another supported credential provider with permissions for the lab. Prefer short-lived credentials over long-lived access keys.

Start by defining the foundational resources:

* EC2 instance and security group.

* IAM instance profile with the permissions needed by Systems Manager and CloudWatch.

* CloudWatch log groups with explicit retention.

* SNS topic for operational alerts.

* Resource tags for cost attribution and cleanup.

Keep ingress restricted. If you use a public HTTP endpoint for demonstration, restrict access to your own IP where practical. Systems Manager should be the preferred administrative path, not unrestricted SSH.

### Step 2 — Deploy and monitor the application

Deploy a simple HTTP service with a `/health` endpoint and structured logs. Make the application able to simulate an unhealthy response through an explicit development-only switch.

Create CloudWatch resources with Pulumi:

* A dashboard showing EC2 CPU utilization, application request errors, and health-check results.

* A log group for application output.

* A log group for relevant system logs.

* An alarm for sustained application failures.

* An alarm for excessive CPU utilization.

* SNS alarm actions.

For a basic HTTP application, publish a custom CloudWatch metric for successful and failed health checks or use a suitable load-balancer health metric if your architecture includes a load balancer.

Example alarm configuration in Python:

```python
import pulumi_aws as aws

application_alarm = aws.cloudwatch.MetricAlarm(
    "application-error-alarm",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=2,
    metric_name="FailedHealthChecks",
    namespace="OperationsCapstone",
    period=60,
    statistic="Sum",
    threshold=0,
    alarm_description="Application health checks are failing",
    treat_missing_data="notBreaching",
    alarm_actions=[alert_topic_arn],
)
```

Here, `alert_topic_arn` must refer to an SNS topic created earlier in your Pulumi program.

The metric `OperationsCapstone/FailedHealthChecks` is a custom metric that your application or monitoring component must publish. The alarm will not detect failures until the metric exists and matching datapoints arrive. The example also uses a simplified missing-data policy; choose one appropriate to your application's telemetry guarantees.

### Step 3 — Configure CloudTrail and AWS Config

Use Pulumi to configure a CloudTrail trail with a dedicated S3 destination, appropriate bucket policies, and log-file validation.

For the development stack:

* Enable management-event auditing.

* Choose whether multi-Region coverage is appropriate for the account.

* Configure data events only for resources where the additional visibility is necessary.

* Restrict access to the audit destination.

* Configure retention and lifecycle policies consistent with your lab requirements.

Then configure AWS Config recording and one or two relevant managed rules. Select rules that match the resources you actually deploy, and confirm the rule's required recording scope.

Use Config history to identify a configuration change and CloudTrail to investigate the API operation associated with that change. Config notifications require a properly configured recorder and delivery channel when using its SNS notification mechanism. AWS Config +1

### Step 4 — Integrate Systems Manager

Make the EC2 instance a Systems Manager managed node:

* Attach an instance profile with appropriate Systems Manager permissions.

* Confirm that the SSM Agent is installed and running.

* Verify connectivity to the required Systems Manager endpoints.

* Confirm the instance appears as a managed node.

* Use Session Manager or Run Command to collect diagnostic information.

Create a narrowly scoped diagnostic procedure that collects:

* Application process status.

* Recent application logs.

* Disk usage and memory information.

* Service health endpoint results.

* Relevant timestamps.

Use an approved Systems Manager document or a controlled script for remediation. Avoid automatically rebooting instances or making broad configuration changes in response to every alarm.

Systems Manager supports monitoring and event integration, including routing selected execution status changes through EventBridge. AWS Systems Manager +1

### Step 5 — Configure notification routing and cost controls

Create an EventBridge rule for a supported event, such as a Systems Manager command execution status change or a relevant CloudTrail API operation.

Route the event to SNS with the required permissions. Configure the message to include the event type, resource identifier, status, and instructions for locating the runbook.

Create an AWS Budget with an illustrative monthly threshold, such as $10, and configure an actual-cost notification. Adjust the amount to your own account's expected usage.

Remember that budgets are not instantaneous hard spending caps. AWS Budgets data and alerts can be delayed, and forecast notifications require sufficient historical usage. AWS Cost Management +1

### Step 6 — Simulate and investigate a failure

Use a controlled application failure, such as making the health endpoint return HTTP 500 or causing the application process to stop. Do not simulate an AWS-wide outage or modify production resources.

Follow this incident sequence:

* Observe the CloudWatch alarm transition.

* Open the relevant log stream and identify the failure.

* Record the alarm timestamp and the first observed failed request.

* Review CloudTrail for relevant API changes around that time.

* Inspect AWS Config compliance and resource history if a configuration issue is suspected.

* Use Systems Manager to diagnose the instance and apply a controlled recovery action.

* Verify application health and confirm that the alarm returns to a healthy state.

* Record the root cause and preventive actions.

If the failure is purely application-level, CloudTrail may show no relevant configuration change. That is a valid finding: not every incident has an infrastructure-level cause.

### 7\. Incident report template

Use this template for the final deliverable.

# Incident Report — AWS Operations Capstone

## 1. Incident summary
- Incident ID:
- Date and time:
- Severity:
- Affected service:
- Customer impact:

## 2. Detection
- First observed symptom:
- Detection mechanism:
- Alarm name:
- Time to detection:

## 3. Timeline
| Timestamp | Event |
|---|---|
| | Failure begins |
| | Alert received |
| | Investigation begins |
| | Mitigation applied |
| | Service restored |

## 4. Evidence
- CloudWatch metrics:
- Relevant log entries:
- CloudTrail events:
- AWS Config findings:
- Systems Manager diagnostic output:
- AWS Health findings, if relevant:

## 5. Root cause
Describe the underlying technical cause and explain how the evidence supports the conclusion.

## 6. Recovery
- Action taken:
- Verification performed:
- Recovery time:
- Outstanding risks:

## 7. Corrective actions
| Action | Priority | Owner | Target date |
|---|---|---|---|
| | | | |

## 8. Lessons learned
- What detected the problem effectively?
- What delayed diagnosis or recovery?
- Which alerts or runbooks need improvement?
- How can recurrence be prevented?

### 8\. Production-readiness review

Before considering the capstone complete, review the following:

### Readiness checklist

0 / 15 complete

Infrastructure

Pulumi resources are reproducible from a clean stack.

Changes have been reviewed with pulumi preview.

Resources have consistent ownership and environment tags.

Observability

Application logs are available and have a retention policy.

Alarms use appropriate thresholds and evaluation periods.

Notifications reach a confirmed recipient.

Security and auditing

IAM policies follow least privilege.

CloudTrail logs are protected from unauthorized modification.

Systems Manager access is restricted and auditable.

Incident response

The controlled failure was detected.

Evidence supports the root-cause conclusion.

Recovery was verified and documented.

Cost and cleanup

A budget notification is configured.

Potentially chargeable resources and retention settings were reviewed.

Temporary resources are removed when no longer needed.

Reset checklistCopy checklist

### 9\. Cost, cleanup, and limitations

A development environment can still incur charges for EC2, CloudWatch log ingestion and retention, CloudTrail data events, AWS Config recording and rule evaluations, S3 storage, and other enabled features.

Before deployment, verify pricing for the selected Region and account. Budget alerts help provide visibility but should not be treated as an immediate stop mechanism.

After completing the incident investigation:

* Preserve the incident report and any required audit evidence.

* Review which resources are safe to delete.

* Run the appropriate Pulumi destroy preview or review workflow.

* Remove lab resources that are no longer needed.

* Retain audit records only as long as required by the lab's retention policy.

* Verify that no unintended infrastructure remains.

Capstone outcome: You have designed and deployed a small operational platform with infrastructure managed through Pulumi, observability through CloudWatch, auditing through CloudTrail, compliance monitoring through AWS Config, secure diagnostics through Systems Manager, and cost notifications through AWS Budgets. You have also followed a complete incident lifecycle from detection to verified recovery and documented root cause.

### Official references

* Pulumi AWS provider — [Provider documentation](https://www.pulumi.com/docs/iac/guides/clouds/aws/providers/?utm_source=chatgpt.com).

* Amazon EventBridge — [EventBridge user guide](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html?utm_source=chatgpt.com).

* AWS Systems Manager — [Systems Manager user guide](https://docs.aws.amazon.com/systems-manager/latest/userguide/what-is-systems-manager.html?utm_source=chatgpt.com).

* AWS Budgets — [Budget and cost management documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html?utm_source=chatgpt.com).
