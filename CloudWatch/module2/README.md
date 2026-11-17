### Module 2 — CloudWatch Logs, Alarms, and Notifications

AWS Operations and Observability · Module 2 of 8

### Module goal

Learn how to centralize application and system logs, detect failures with CloudWatch metrics and alarms, and notify operators when workloads become unhealthy. You will also learn to investigate incidents using CloudWatch Logs Insights and deploy the monitoring infrastructure with Pulumi instead of Terraform.

By the end of this module, you should understand how to move from an application error to an actionable alert, identify the underlying cause, and verify that the problem has been resolved.

### 1\. Understanding CloudWatch Logs

Amazon CloudWatch Logs is AWS's managed log collection and analysis service. Applications, operating systems, AWS services, and custom workloads can send log events to CloudWatch so operators can search, analyze, retain, and monitor them centrally.

### 1.1 Log groups, streams, and events

Log group

A collection of logs for an application, service, or component

Log stream A

One source of log events

Log stream B

Another source of log events

Log events

Timestamped records containing messages, structured fields, and diagnostic information.

```text
2026-10-28T10:15:21Z INFO  request_id=abc123 status=200 path=/health
2026-10-28T10:15:22Z ERROR request_id=abc124 status=500 path=/orders
2026-10-28T10:15:23Z WARN  database_connection_pool_nearly_full
```

The three fundamental concepts are:

* Log group: Defines a logical collection of log data and its retention and monitoring configuration.

* Log stream: Contains log events from a particular source, such as an EC2 instance, container, or application process.

* Log event: A timestamp and a message, potentially containing structured JSON data.

A log group might be named `/applications/orders-api/production`, while its streams represent different application instances.

### 1.2 Naming and organizing log groups

A consistent naming convention makes it easier to locate logs and apply retention policies.

Examples:

| Workload          | Log group                              |
| ----------------- | -------------------------------------- |
| Application       | /applications/orders-api/production    |
| Operating system  | /infrastructure/ec2/production         |
| Background worker | /applications/orders-worker/production |
| Lambda function   | /aws/lambda/orders-processor           |

For Lambda functions, AWS commonly creates the `/aws/lambda/` log group when the function first writes logs, provided the execution role has the necessary permissions. You can also create the log group explicitly using infrastructure as code.

Avoid creating separate log groups for every individual request. Use streams and structured fields to distinguish sources and requests.

### 1.3 Retention, ingestion, and storage

CloudWatch Logs separates log ingestion from log retention.

* Ingestion: Sending log events into CloudWatch Logs.

* Retention: How long events remain available before automatic expiration.

* Storage: Charges associated with retaining log data, according to the applicable pricing model.

* Queries: Logs Insights queries can incur additional charges based on the amount of data scanned, depending on the query and pricing model.

Log groups commonly retain events indefinitely unless a retention policy is configured. Production log groups should have an intentional retention period that reflects operational needs, compliance requirements, and budget.

For example, a development log group might retain logs for seven days, while production logs might be retained for 30 or 90 days. These are examples, not universal requirements.

Deleting a log group removes its retained log data, so retention changes and deletion should be handled carefully.

### 2\. Collecting application and system logs

CloudWatch Logs is most useful when applications and infrastructure consistently send useful diagnostic information to it.

### 2.1 Application logging

Applications should emit logs that help operators answer four questions:

* What happened?

* When did it happen?

* Which request or component was involved?

* Why did it happen?

For a Python application, structured JSON logs are often easier to analyze than unstructured text.

```python
import json
import logging
import sys
from datetime import datetime, timezone

logger = logging.getLogger("orders-api")
logger.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)

def log_request(request_id: str, status_code: int) -> None:
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": "ERROR" if status_code >= 500 else "INFO",
        "event": "http_request",
        "request_id": request_id,
        "status_code": status_code,
    }

    logger.log(
        logging.ERROR if status_code >= 500 else logging.INFO,
        json.dumps(event),
    )
```

This example writes one JSON object per log line to standard output. The CloudWatch agent or another supported log collector can forward those lines to CloudWatch Logs.

A real application should also record useful fields such as the HTTP method, route template, latency, and exception type when appropriate.

Important logging practices

* Use consistent severity levels: `DEBUG`, `INFO`, `WARNING`, `ERROR`, and `CRITICAL`.

* Include request or correlation IDs to connect related events.

* Avoid logging passwords, access tokens, session cookies, or sensitive personal information.

* Prefer structured fields over complex messages that are difficult to parse.

* Avoid logging complete request bodies by default.

* Include stack traces for unexpected exceptions, while ensuring sensitive information is excluded.

### 2.2 Collecting EC2 operating-system logs

For EC2 workloads, the CloudWatch agent can collect both operating-system metrics and log files.

A typical architecture looks like this:

EC2 instance

Application logs · System logs · Agent configuration

Amazon CloudWatch agent

Reads configured files and forwards log events

CloudWatch Logs

Centralized log groups, retention, search, and analysis

On a Linux EC2 instance, useful log sources include:

* `/var/log/messages` on some distributions.

* `/var/log/syslog` on Ubuntu and some Debian-based systems.

* `/var/log/nginx/access.log` and `/var/log/nginx/error.log` for Nginx.

* Application-specific log files.

The exact paths depend on the operating system and application configuration.

The agent needs permission to publish logs and metrics. A common approach is an EC2 instance profile with the AWS-managed `CloudWatchAgentServerPolicy`, adjusted to a narrower custom policy when appropriate.

The agent configuration can be stored in Systems Manager Parameter Store, allowing consistent configuration across multiple instances.

### 2.3 CloudWatch agent configuration

Here is a simplified Linux configuration that collects application and system logs:

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/nginx/access.log",
            "log_group_name": "/applications/nginx/production",
            "log_stream_name": "{instance_id}/access",
            "retention_in_days": 30
          },
          {
            "file_path": "/var/log/nginx/error.log",
            "log_group_name": "/applications/nginx/production",
            "log_stream_name": "{instance_id}/error",
            "retention_in_days": 30
          }
        ]
      }
    }
  }
}
```

This is an illustrative configuration fragment; it must be saved as the agent's configuration file and applied using the appropriate agent control command. The log files must exist and be readable by the agent.

For example, after installing and configuring the agent, a typical Linux command to start it with a local configuration file is:

```bash
sudo /opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s
```

On supported distributions, the agent may be installed using AWS Systems Manager, a package manager, or an image-building process.

### 2.4 Log collection troubleshooting

If logs are not appearing in CloudWatch, investigate the pipeline in order:

* Confirm the application is actually writing to the configured file or standard output.

* Check the file path, permissions, and log rotation configuration.

* Confirm the CloudWatch agent is running and its configuration is valid.

* Verify the instance has the correct IAM permissions.

* Check network access to the CloudWatch Logs endpoint, including required VPC endpoints or outbound connectivity.

* Inspect the agent's own log file for errors.

This order helps distinguish an application problem from an agent, permissions, or connectivity problem.

### 3\. CloudWatch Logs Insights

CloudWatch Logs Insights is a query engine for exploring and analyzing log events. Instead of manually searching large files, operators can filter, parse, aggregate, and sort records using a purpose-built query language.

### 3.1 Basic query structure

A query usually follows this pattern:

```text
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 20
```

The commands mean:

* `fields`: Select fields to display.

* `filter`: Keep matching events.

* `sort`: Order the results.

* `limit`: Restrict the number of returned records.

The built-in fields `@timestamp` and `@message` are available for typical log events. JSON logs can expose additional fields automatically.

### 3.2 Query examples

Example A — Find application errors

```text
fields @timestamp, @message
| filter @message like /ERROR/
| sort @timestamp desc
| limit 50
```

Useful when investigating a recent failure or looking for recurring errors.

Example B — Find HTTP 500 responses in JSON logs

```text
fields @timestamp, request_id, status_code, path
| filter status_code >= 500
| sort @timestamp desc
| limit 100
```

Assumes the log events contain the corresponding structured JSON fields.

Example C — Count errors by status code

```text
fields status_code
| filter status_code >= 400
| stats count(*) as requests by status_code
| sort requests desc
```

Helps identify whether client errors, server errors, or both are increasing.

Example D — Find the busiest five-minute intervals

```text
fields @timestamp, status_code
| filter status_code >= 500
| stats count(*) as errors by bin(5m)
| sort bin(5m) desc
```

Useful for correlating a spike in errors with deployments or infrastructure changes.

Example E — Calculate error rates from request logs

```text
fields status_code
| stats
    count(*) as total_requests,
    sum(strcontains(@message, "ERROR")) as error_messages
```

This last example counts messages containing the literal word ERROR, not necessarily failed HTTP requests. For a reliable HTTP error rate, use structured status codes and conditional aggregation appropriate to the logged schema.

For structured request logs, an aggregation can use `filter` and `stats` or conditional expressions to derive error counts. Always confirm that the fields exist and that the query matches the actual log format.

### 3.3 Query performance and operational use

Logs Insights queries can scan substantial amounts of data. To control query costs and improve response times:

* Select the narrowest useful time range.

* Select only relevant log groups.

* Filter early in the query.

* Use structured JSON fields where practical.

* Avoid repeatedly scanning long retention windows for routine monitoring.

Logs Insights is primarily for investigation and analysis. For continuously evaluating a known condition and triggering an alarm, metric filters or application-published metrics are generally more suitable.

### 4\. Metric filters and custom application metrics

A log event is detailed evidence of what happened. A metric is a numerical time series that can be aggregated, visualized, and evaluated by alarms.

Metric filters bridge the two.

### 4.1 How metric filters work

Suppose an application writes these messages:

```text
INFO request completed status=200
ERROR request failed status=500
ERROR request failed status=503
```

A metric filter can match error records and publish a numerical metric to CloudWatch.

Application log events

Text or structured JSON

Metric filter

Matches configured patterns

CloudWatch custom metric

For example, application error count

CloudWatch alarm

Evaluates thresholds over time

For a simple text log, the filter pattern might be:

```text
ERROR
```

For structured JSON logs, a filter pattern can match a field:

```text
{ $.status_code >= 500 }
```

A metric filter needs a metric transformation that specifies a namespace, metric name, and numerical value. A matched event can contribute `1` to an error counter.

Metric filters process incoming log events; they do not retroactively generate metric data for all previously ingested logs. For historical investigation, query the logs directly with Logs Insights.

### 4.2 Choosing metric dimensions

Dimensions add context to metrics, such as environment, service, or application component.

Useful examples:

* `Environment=production`

* `Service=orders-api`

Avoid using unique request IDs, customer IDs, or other unbounded values as metric dimensions. This creates high metric cardinality, increases cost, and makes monitoring harder to manage.

If a metric filter is counting every matched error, a sum statistic can represent the number of matched events over the evaluation period. For rate-based monitoring, the numerator and denominator must be defined consistently.

### 4.3 Publishing custom metrics directly

Applications can publish metrics directly using the CloudWatch API or AWS SDK. This is useful when an application can calculate a meaningful value more reliably than a log filter can.

For example, a Python application using Boto3 could publish a metric like this:

```python
import boto3

cloudwatch = boto3.client("cloudwatch")

cloudwatch.put_metric_data(
    Namespace="OrdersAPI",
    MetricData=[
        {
            "MetricName": "FailedRequests",
            "Dimensions": [
                {"Name": "Environment", "Value": "production"}
            ],
            "Value": 1,
            "Unit": "Count",
        }
    ],
)
```

This code publishes a single metric data point. It assumes AWS credentials and permissions are configured correctly, and the calling application should handle errors, batching, and retry behavior in production.

Use metric filters when logs already contain the signal you need. Publish custom metrics directly when the application owns a more meaningful measurement, such as queue depth, business-operation failures, or processing duration.

### 5\. CloudWatch alarms

CloudWatch alarms continuously evaluate metric data against a configured condition. They can transition between states and trigger actions when a workload requires attention.

### 5.1 Alarm states

OK The metric satisfies the configured condition. The workload is within the alarm's defined threshold.

ALARM The evaluated metric breaches the configured threshold for enough periods to meet the alarm's evaluation requirements.

INSUFFICIENT_DATA There is not enough usable metric data to determine whether the alarm condition is satisfied, or the alarm is initializing.

An alarm state is not necessarily a direct statement about application health. For example, a CPU alarm can be in the `OK` state while the application is returning HTTP 500 responses. Good monitoring combines infrastructure and application signals.

### 5.2 Thresholds and evaluation periods

Consider a hypothetical alarm with these settings:

| Setting             | Value                      |
| ------------------- | -------------------------- |
| Metric              | FailedRequests             |
| Statistic           | Sum                        |
| Period              | 60 seconds                 |
| Threshold           | Greater than or equal to 5 |
| Evaluation periods  | 3                          |
| Datapoints to alarm | 2                          |

With these settings, the alarm transitions to `ALARM` when at least two of the most recent three evaluation periods breach the threshold.

The threshold is evaluated against the metric statistic for each period. It does not simply mean that five errors occurred in total across the entire three-minute window.

CloudWatch calls this M-out-of-N evaluation: M datapoints must breach the threshold among N evaluation periods.

### 5.3 Missing data

Missing metric data needs an explicit operational interpretation.

CloudWatch supports four missing-data treatments:

* `missing`: Missing datapoints remain missing and may lead to `INSUFFICIENT_DATA`.

* `notBreaching`: Treat missing datapoints as not breaching the threshold.

* `breaching`: Treat missing datapoints as breaching the threshold.

* `ignore`: Retain the current alarm state when data is missing.

The right choice depends on the workload.

For example, if an application publishes metrics only when errors occur, missing data might mean no errors. But if a heartbeat metric should arrive every minute, missing data could mean the application or monitoring pipeline has stopped working.

Do not automatically treat missing data as healthy. For critical services, monitor telemetry availability separately when possible.

### 5.4 Composite alarms

A composite alarm combines the states of other CloudWatch alarms using logical expressions.

For example:

```text
ALARM(HighCPU)
AND
ALARM(HighErrorRate)
```

This composite alarm activates only when both component alarms are in the `ALARM` state.

Composite alarms can reduce notification noise by requiring multiple signals before sending an incident notification. They do not replace the underlying metric alarms; they combine their states.

### 5.5 Anomaly detection

CloudWatch anomaly detection models expected metric behavior and creates a band representing normal variation. An alarm can evaluate whether a metric moves outside that expected band.

This is useful when a fixed threshold is inappropriate—for example, request traffic that varies significantly throughout the day.

Anomaly detection requires sufficient representative metric history and is not a guarantee that every unusual event will be detected. Critical workloads may still need fixed safety thresholds.

### 5.6 Alarm actions

Common alarm actions include:

* Publishing to an SNS topic.

* Triggering supported EC2 actions, such as stopping or recovering an instance.

* Invoking supported Auto Scaling actions.

* Driving other operational workflows through supported integrations.

Choose actions carefully. Notifications are generally safer as an initial step than automatic remediation that could interrupt a production workload.

### 6\. Amazon SNS and operational notifications

Amazon Simple Notification Service (SNS) distributes messages from publishers to subscribers.

CloudWatch alarms can publish notifications to an SNS topic when the alarm transitions into a configured state.

### 6.1 Notification architecture

CloudWatch alarm

Detects an error-rate threshold breach

Amazon SNS topic

Distributes the alarm notification

Email

SMS\*

Other targets

\*SMS availability and cost depend on the destination and configuration. Other targets may require subscriptions or integrations.

### 6.2 SNS topic and subscription concepts

* Topic: The logical destination for published messages.

* Publisher: CloudWatch alarm or another service publishing a message.

* Subscription: A destination registered to receive messages, such as an email address, HTTPS endpoint, or supported AWS service.

* Confirmation: Some subscription types require the recipient to confirm the subscription before delivery begins.

For email notifications, the recipient generally needs to confirm the subscription. Creating a topic and subscription in Pulumi does not guarantee that notifications are delivered until confirmation and permissions are in place.

### 6.3 Notification design

Production monitoring should distinguish between urgent incidents and informational events.

For example:

| Severity      | Example                                     | Response                                 |
| ------------- | ------------------------------------------- | ---------------------------------------- |
| Critical      | Sustained server errors affecting customers | Immediate incident notification          |
| Warning       | CPU usage approaching a limit               | Investigate if persistent                |
| Informational | Deployment completed                        | Record or send to an operational channel |

Avoid creating an alert for every individual error. Instead, use thresholds, evaluation periods, composite alarms, and appropriate routing to reduce alert fatigue.

SNS is a notification mechanism, not a complete incident-management system. Escalation policies, ownership, on-call rotations, and incident tracking may require additional tooling.

### 7\. Lab 2 — Detect and Diagnose Application Failures

Hands-on lab

### Lab objective

Build a small AWS monitoring pipeline with Pulumi, send application logs to CloudWatch Logs, convert matching errors into a metric, trigger an alarm, and receive an SNS notification.

### 7.1 Target architecture

Sample Python application on EC2

Produces HTTP request and error logs

CloudWatch Logs

Application log group and retained log events

Metric filter → CloudWatch metric

Counts matching HTTP 5xx responses

CloudWatch alarm → SNS topic

Detects sustained failures and sends email

You will also use Logs Insights to investigate the failed requests.

### 7.2 Prerequisites

* An AWS account with permission to create EC2 instances, IAM roles, CloudWatch resources, and SNS resources.

* AWS CLI configured with credentials for a lab account.

* Python and Pulumi installed.

* An SSH key pair if you choose to connect to the instance through SSH; Session Manager is another option when configured.

* A verified email address accessible for SNS subscription confirmation.

The lab creates billable resources. Use a dedicated lab environment, restrict permissions, avoid opening SSH to the entire internet, and remove resources after testing.

### 7.3 Project structure

Create a Pulumi Python project:

```text
cloudwatch-lab/
├── __main__.py
├── Pulumi.yaml
├── Pulumi.dev.yaml
└── requirements.txt
```

Initialize the project and install the AWS provider:

```bash
mkdir cloudwatch-lab
cd cloudwatch-lab

pulumi new aws-python
```

Follow the prompts to configure the project. The AWS region should be one where the required services are available.

The generated project normally includes a Python virtual environment. Activate it, then install or confirm the provider dependency:

```bash
python -m pip install pulumi pulumi-aws
```

For reproducible environments, pin provider versions in your project dependencies and keep them updated deliberately.

### 7.4 Configure the sample application

The sample application will emit one JSON event per request. It uses a small HTTP server to demonstrate the monitoring pipeline without requiring a full application framework.

Create `app.py`:

```python
import json
import logging
import os
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("lab-app")

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status = 500 if self.path == "/fail" else 200

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR" if status >= 500 else "INFO",
            "event": "http_request",
            "path": self.path,
            "status_code": status,
        }

        logger.info(json.dumps(event))

        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(
            json.dumps({"status_code": status}).encode()
        )

    def log_message(self, format_string, *args):
        pass

port = int(os.environ.get("PORT", "8080"))
HTTPServer(("0.0.0.0", port), Handler).serve_forever()
```

The `/fail` endpoint deliberately generates HTTP 500 responses for monitoring. This is a controlled test failure, not a real application error.

For this lab, the application will write logs to a file so that the CloudWatch agent can collect them. A production service may instead use another supported collection method.

### 7.5 Provision the AWS resources using Pulumi

The following example defines the core monitoring infrastructure. It creates an IAM role for EC2, a log group, a metric filter, an SNS topic and email subscription, and a CloudWatch alarm.

It assumes that an EC2 instance will be provisioned with a suitable Linux AMI and configured to run the application and CloudWatch agent. The next section explains the instance bootstrap requirements.

Create or extend `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

notification_email = config.require("notificationEmail")

# Centralized application logging.
log_group = aws.cloudwatch.LogGroup(
    "application-logs",
    name="/applications/orders-api/lab",
    retention_in_days=7,
)

# Instance role for CloudWatch agent log delivery.
instance_role = aws.iam.Role(
    "application-instance-role",
    assume_role_policy="""{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ec2.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }""",
)

aws.iam.RolePolicyAttachment(
    "cloudwatch-agent-policy",
    role=instance_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "CloudWatchAgentServerPolicy"
    ),
)

instance_profile = aws.iam.InstanceProfile(
    "application-instance-profile",
    role=instance_role.name,
)

# Count JSON log events where status_code >= 500.
error_filter = aws.cloudwatch.LogMetricFilter(
    "http-server-errors",
    log_group_name=log_group.name,
    pattern='{ $.status_code >= 500 }',
    metric_transformation={
        "name": "Http5xxCount",
        "namespace": "Lab/OrdersAPI",
        "value": "1",
        "unit": "Count",
    },
)

# Email notification destination.
topic = aws.sns.Topic("operations-alerts")

subscription = aws.sns.TopicSubscription(
    "operations-email",
    topic=topic.arn,
    protocol="email",
    endpoint=notification_email,
)

# Alarm when at least five errors are recorded in a period.
alarm = aws.cloudwatch.MetricAlarm(
    "http-5xx-alarm",
    alarm_description="Application HTTP 5xx error count is high",
    namespace="Lab/OrdersAPI",
    metric_name="Http5xxCount",
    statistic="Sum",
    period=60,
    evaluation_periods=1,
    datapoints_to_alarm=1,
    threshold=5,
    comparison_operator="GreaterThanOrEqualToThreshold",
    treat_missing_data="notBreaching",
    alarm_actions=[topic.arn],
)

pulumi.export("log_group_name", log_group.name)
pulumi.export("sns_topic_arn", topic.arn)
pulumi.export("alarm_name", alarm.name)
pulumi.export("instance_profile_name", instance_profile.name)
pulumi.export("metric_filter_name", error_filter.name)
```

Configure the email address:

```bash
pulumi config set notificationEmail your-address@example.com
```

Then preview and deploy:

```bash
pulumi preview
pulumi up
```

Review the proposed changes before approving the deployment.

What this infrastructure establishes

* A log group with seven-day retention.

* An EC2 instance profile with the AWS-managed CloudWatch agent policy.

* A metric filter that converts matching HTTP 5xx log events into metric datapoints.

* An SNS topic and email subscription.

* An alarm that triggers when the sum reaches five or more within a 60-second period.

The instance role and profile are prerequisites for EC2 log collection; this snippet does not itself create the EC2 instance or install the application. The metric filter starts counting newly ingested matching events, so historical logs do not automatically populate the metric.

### 7.6 Configure EC2 log collection

Provision an EC2 instance using a supported Linux AMI. Attach the instance profile created above and ensure the instance can reach CloudWatch Logs.

Install the CloudWatch agent and configure it to collect the application log file. A configuration might look like this:

```json
{
  "logs": {
    "logs_collected": {
      "files": {
        "collect_list": [
          {
            "file_path": "/var/log/orders-api/app.log",
            "log_group_name": "/applications/orders-api/lab",
            "log_stream_name": "{instance_id}",
            "retention_in_days": 7
          }
        ]
      }
    }
  }
}
```

Run the application with its output directed to the configured log file. For example, the Python process can be started with shell output redirection:

```bash
sudo mkdir -p /var/log/orders-api
sudo touch /var/log/orders-api/app.log

sudo python3 app.py >> /var/log/orders-api/app.log 2>&1
```

For a persistent service, configure a systemd unit or another process supervisor rather than leaving the application attached to an interactive terminal.

Start or restart the CloudWatch agent with the configuration file. Verify the agent status and inspect its own logs if the log stream does not appear.

In a production deployment, use a proper service account, secure file permissions, log rotation, and a repeatable bootstrap mechanism. Do not rely on manual setup for every new instance.

### 7.7 Generate test traffic

Once the application is running, send successful and failing requests from a machine that can reach the instance on port 8080.

```bash
curl -i http://INSTANCE_ADDRESS:8080/
curl -i http://INSTANCE_ADDRESS:8080/fail
```

Repeat the failing request at least five times within a single 60-second period to test the configured alarm. Replace `INSTANCE_ADDRESS` with the actual reachable address or hostname.

Do not open the application port broadly to the public internet merely to run the lab. Use a restricted security group, a private test environment, or an appropriate secure access method.

### 7.8 Confirm the SNS subscription

When the subscription is created, AWS sends a confirmation email to the configured recipient.

Open the message and confirm the subscription. Until that step is complete, email notifications may not be delivered.

Then inspect the CloudWatch alarm and verify that it transitions to `ALARM` after sufficient matching requests have been ingested and the metric has been evaluated.

Allow for log ingestion and metric evaluation delays. A successful `pulumi up` does not guarantee that the application is already emitting logs or that the alarm has received datapoints.

### 7.9 Investigate the errors using Logs Insights

Open the CloudWatch console and navigate to Logs → Logs Insights. Select `/applications/orders-api/lab` and choose a time range covering the test requests.

Run this query to find failed requests:

```text
fields @timestamp, @message, status_code, path
| filter status_code >= 500
| sort @timestamp desc
| limit 50
```

Then run an aggregation to identify the number of failures by path:

```text
fields path, status_code
| filter status_code >= 500
| stats count(*) as failures by path
| sort failures desc
```

To inspect the overall distribution of HTTP status codes:

```text
fields status_code
| stats count(*) as requests by status_code
| sort requests desc
```

If the query returns no results, verify the following:

* The application is generating the expected JSON logs.

* The agent is reading the correct log file.

* Events are arriving in the intended log group.

* The selected time range includes the test traffic.

* The query fields match the actual JSON structure.

### 7.10 Validate the complete monitoring pipeline

Use this checklist to verify the lab's behavior.

### Lab verification

0 of 9

The application responds successfully to normal requests.

The /fail endpoint produces HTTP 500 responses.

Application log events appear in the CloudWatch log group.

Logs Insights can find failed requests and aggregate results.

The metric filter matches newly ingested HTTP 5xx events.

The CloudWatch metric records the expected error count.

The alarm enters ALARM after its threshold is breached.

The SNS email subscription is confirmed and notifications arrive.

The alarm returns to OK after the error metric falls below its threshold and the evaluation window updates.

One detail matters for the final step: because the alarm uses a one-minute period and a single evaluation period, it will return to `OK` only after a subsequent evaluation no longer meets the threshold. If there is no new metric data, the configured missing-data treatment is `notBreaching`, which can also affect the transition.

### 7.11 Common failures and troubleshooting

| Symptom                                 | Likely cause                               | What to investigate                                 |
| --------------------------------------- | ------------------------------------------ | --------------------------------------------------- |
| No log stream appears                   | Agent not running or file not readable     | Agent status, configuration, file path, permissions |
| AccessDenied in agent logs              | Missing IAM permission                     | Instance profile and effective role policies        |
| Logs arrive but metric stays empty      | Filter pattern does not match              | JSON structure and filter pattern                   |
| Metric exists but alarm remains OK      | Threshold not reached                      | Period, statistic, datapoints, error count          |
| Alarm enters ALARM but no email arrives | Subscription unconfirmed or delivery issue | SNS subscription status and delivery diagnostics    |
| Logs Insights finds no errors           | Wrong time range or field names            | Actual event format and selected log group          |
| Query is unexpectedly expensive         | Too much data scanned                      | Narrow the time range and selected log groups       |

### 7.12 Clean up the lab

After verifying the monitoring workflow, remove the resources you created:

```bash
pulumi destroy
```

Review the proposed deletions and approve them. Also verify that the EC2 instance, any separately created networking resources, and any manually installed software are no longer needed.

Pulumi only manages resources represented in its stack; manually created resources may require separate cleanup. Check the AWS console for leftover resources and confirm that ongoing charges have stopped where applicable.

### Module summary

You have now covered the core workflow for application monitoring and incident investigation:

* CloudWatch Logs centralizes application and system logs.

* Logs Insights helps operators search and analyze events.

* Metric filters turn matching log events into numerical metrics.

* CloudWatch alarms detect threshold breaches and changes in workload health.

* SNS distributes notifications to operators and supported destinations.

* Pulumi makes the monitoring infrastructure repeatable and version-controlled.

The key operational principle is to connect logs, metrics, alarms, and notifications without treating them as interchangeable. Logs explain individual events, metrics reveal trends, alarms identify conditions that require attention, and notifications bring those conditions to the people responsible for resolving them.
