### Module 1 — Observability Foundations and CloudWatch Metrics

AWS Operations and Observability · Module 1 of 8

### 1\. Learning objectives

By the end of this module, you will understand how to:

* Explain observability and the roles of metrics, logs, traces, and events.

* Understand Amazon CloudWatch namespaces, metrics, dimensions, statistics, and periods.

* Interpret infrastructure and application performance metrics.

* Distinguish standard monitoring, detailed monitoring, and custom metrics.

* Build dashboards and analyze metrics using metric search and metric math.

* Collect operating-system metrics using the CloudWatch agent.

* Provision monitoring infrastructure with Pulumi and Python.

* Build an operational dashboard for CPU, memory, disk usage, and network activity.

### 2\. Observability fundamentals

Observability is the ability to understand the internal state of a system by examining the data it produces. In AWS, observability helps answer questions such as:

* Is the application healthy?

* Why are requests becoming slow?

* Is the server running out of memory or disk space?

* Did a deployment or configuration change cause a failure?

* Is the workload approaching a capacity limit?

Monitoring typically evaluates known conditions, while observability helps investigate unexpected behavior and understand its underlying causes.

### The main telemetry signals

Metrics — What is happening?

Numerical measurements collected over time, such as CPU utilization, request count, latency, and memory usage. Metrics are useful for dashboards, capacity planning, alerting, and trend analysis.

Example: CPU utilization increased from 25% to 92%.

Logs — What happened?

Timestamped records of application and system activity. Logs provide detailed context for errors, authentication failures, application events, and unexpected behavior.

Example: `ERROR: database connection timed out`.

Traces — Where did a request spend its time?

Traces follow a request across application components and distributed services. They help identify slow database calls, overloaded services, and problematic dependencies.

Example: an HTTP request takes 2.4 seconds, including 1.9 seconds waiting for a database query.

Events — What changed or triggered an action?

Events represent discrete occurrences, such as an EC2 instance changing state, an API call modifying a resource, or an AWS Health notification.

Example: an EC2 instance entered the `stopped` state.

Telemetry is the broader term for the data emitted or collected from a system, including metrics, logs, traces, and events.

In AWS, CloudWatch is a central service for metrics, logs, alarms, dashboards, and event-related integrations. AWS X-Ray and OpenTelemetry-compatible instrumentation can provide distributed tracing, while Amazon EventBridge routes events between services.

### A practical troubleshooting example

Suppose a web application becomes slow.

* Metric: CloudWatch shows CPU utilization reaching 95%.

* Log: Application logs show repeated expensive operations.

* Trace: A trace reveals that a database call dominates request latency.

* Event: CloudTrail shows that a configuration change occurred shortly before the incident.

Each signal answers a different question. Combining them provides a stronger explanation than any individual signal alone.

### 3\. Amazon CloudWatch architecture

Amazon CloudWatch collects and exposes monitoring data from AWS resources, applications, and supported external environments.

Data sources

EC2 · EBS · Load balancers · Applications · CloudWatch agent

Amazon CloudWatch

Metrics · Logs · Metric filters · Metric math

Dashboards

Visualize workload health

Alarms

Detect threshold violations

A typical monitoring workflow consists of these stages:

* A resource or agent produces telemetry.

* CloudWatch receives and stores supported monitoring data.

* You select metrics or query logs.

* Dashboards display important measurements.

* Alarms evaluate metric conditions and can trigger actions.

CloudWatch is not a replacement for every AWS operational service. CloudTrail provides API auditing, AWS Config records resource configuration and compliance, and Systems Manager supports fleet operations and remediation. CloudWatch complements these services by making operational signals easier to observe and correlate.

### 4\. CloudWatch metrics: the essential concepts

A CloudWatch metric is a time-ordered collection of measurements identified by its namespace, metric name, and dimensions.

### 4.1 Namespaces

A namespace groups related metrics.

Examples include:

* `AWS/EC2` — EC2 instance metrics.

* `AWS/EBS` — EBS volume metrics.

* `AWS/ApplicationELB` — Application Load Balancer metrics.

* `CWAgent` — metrics commonly published by the CloudWatch agent.

* `MyApplication` — an example of a custom application namespace.

Namespaces help you organize and discover metrics in the CloudWatch console and API.

### 4.2 Metric names

A metric name identifies the measurement being collected.

Common examples:

| Metric            | Meaning                                                    |
| ----------------- | ---------------------------------------------------------- |
| CPUUtilization    | CPU utilization percentage                                 |
| NetworkIn         | Incoming network bytes                                     |
| NetworkOut        | Outgoing network bytes                                     |
| DiskReadBytes     | Bytes read from attached instance storage, where supported |
| mem_used_percent  | Memory utilization published by the CloudWatch agent       |
| disk_used_percent | Disk utilization published by the CloudWatch agent         |

Metric names and their exact availability depend on the namespace, resource type, and publishing configuration.

### 4.3 Dimensions

Dimensions are name-value pairs that identify the resource or series associated with a metric.

For example:

```text
Namespace: AWS/EC2
Metric: CPUUtilization
Dimension:
  InstanceId = i-0123456789abcdef0
```

The instance ID distinguishes the CPU metric for one EC2 instance from the CPU metric for another.

Some metrics have additional dimensions. An Application Load Balancer, for example, can expose metrics associated with a load balancer, target group, or Availability Zone.

Dimensions matter because a metric queried with the wrong dimension set may not appear in the results.

### 4.4 Timestamps, periods, and resolution

Each metric data point has a timestamp and value. CloudWatch presents measurements at a selected period, such as one minute or five minutes.

* Period: The interval over which data points are evaluated or aggregated.

* Resolution: The granularity at which metric data is published and retained.

* Aggregation: The operation used to summarize measurements over a period.

A shorter period can help reveal brief spikes, but it may increase the volume of data points you retrieve and the complexity of your dashboard.

### 4.5 Statistics

Statistics summarize measurements within a period.

| Statistic   | Meaning           | Useful for                                      |
| ----------- | ----------------- | ----------------------------------------------- |
| Average     | Arithmetic mean   | Typical CPU utilization                         |
| Maximum     | Highest value     | Detecting short-lived spikes                    |
| Minimum     | Lowest value      | Finding low points                              |
| Sum         | Total of values   | Request counts or accumulated measurements      |
| SampleCount | Number of samples | Understanding how many observations contributed |

For example, an average CPU utilization of 45% does not mean the instance never exceeded 45%. A `Maximum` of 98% during the same period would reveal a significant spike.

Important: The correct statistic depends on how the metric is published. For a counter such as a request count, `Sum` may be appropriate. For a utilization percentage, `Average` or `Maximum` is often more informative.

### 5\. Important EC2 and infrastructure metrics

EC2 publishes several useful metrics to CloudWatch automatically. However, CPU and network metrics do not provide a complete view of operating-system health. Memory and filesystem utilization generally require an agent or another telemetry publisher.

### 5.1 EC2 metrics

| Metric                               | What it tells you                           | Operational use                            |
| ------------------------------------ | ------------------------------------------- | ------------------------------------------ |
| CPUUtilization                       | Percentage of allocated CPU capacity in use | Detect CPU saturation                      |
| NetworkIn                            | Incoming network bytes                      | Identify changes in inbound traffic        |
| NetworkOut                           | Outgoing network bytes                      | Investigate traffic growth                 |
| NetworkPacketsIn / NetworkPacketsOut | Network packet counts                       | Understand network activity                |
| StatusCheckFailed                    | Whether one or more status checks failed    | Detect instance or infrastructure problems |
| EBSReadOps / EBSWriteOps             | EBS read and write operations               | Investigate storage I/O activity           |

EC2's default metrics do not require installing the CloudWatch agent. Basic EC2 monitoring typically publishes metrics at five-minute intervals; detailed monitoring provides one-minute intervals and can incur additional charges.

The metrics available for an instance also depend on its configuration and the underlying AWS resource.

### 5.2 EBS metrics

Amazon EBS provides metrics that help explain storage performance and throughput.

* `VolumeReadOps` and `VolumeWriteOps` — volume read and write operations.

* `VolumeReadBytes` and `VolumeWriteBytes` — read and write throughput.

* `VolumeQueueLength` — outstanding I/O requests.

* `VolumeThroughputPercentage` — relevant throughput utilization for supported volume types.

* `VolumeIOPSExceededCheck` and `VolumeThroughputExceededCheck` — indicators for supported volume types and configurations.

Use these measurements to investigate whether an application is waiting on storage rather than CPU.

### 5.3 Load balancer metrics

Application Load Balancers publish metrics such as:

* `RequestCount` — requests processed.

* `TargetResponseTime` — time taken for targets to respond.

* `HTTPCode_Target_5XX_Count` — server errors returned by targets.

* `HTTPCode_ELB_5XX_Count` — server errors generated by the load balancer.

* `HealthyHostCount` and `UnHealthyHostCount` — health of registered targets.

A rise in response time alongside a decrease in healthy targets can indicate an application capacity or health problem.

### 5.4 Application metrics

Applications can publish their own metrics using CloudWatch APIs or OpenTelemetry-based instrumentation and integrations.

Useful application-level measurements include:

* Request count and request rate.

* Error rate and failed operations.

* Response latency, including p95 and p99 latency.

* Active jobs and queue depth.

* Database connection pool utilization.

* Business-specific measurements such as completed orders.

A useful monitoring design combines infrastructure and application metrics. High CPU alone does not explain whether users are experiencing failures; request latency and error rate help establish the impact.

### 6\. Standard monitoring, detailed monitoring, and custom metrics

These concepts are related, but they solve different problems.

Standard monitoring

EC2 basic monitoring publishes supported metrics at five-minute intervals. This is a reasonable starting point for low-cost monitoring and general trends.

Detailed monitoring

EC2 detailed monitoring provides supported metrics at one-minute intervals. Use it when faster detection is valuable enough to justify the additional cost.

Custom metrics

Applications and agents publish additional measurements that AWS does not automatically provide, such as memory utilization, business KPIs, or application queue depth.

Do not confuse detailed monitoring with high-resolution custom metrics. Custom metrics can support resolutions finer than one minute when published and queried appropriately, subject to CloudWatch's supported resolutions and pricing.

For this module, we will use standard EC2 metrics plus the CloudWatch agent to publish memory and disk measurements.

### 7\. Dashboards, metric search, and metric math

### 7.1 CloudWatch dashboards

A dashboard is a collection of widgets that present monitoring information in one place.

Typical widgets include:

* Time-series graphs for CPU, memory, and disk usage.

* Single-value displays for current operational indicators.

* Tables for selected metric data.

* Text widgets for operational notes and runbook links.

A useful dashboard answers three questions quickly:

* Is the system healthy?

* What is changing?

* Where should the operator investigate next?

Avoid filling dashboards with every metric available. Prioritize measurements tied to service health, capacity, and user impact.

### 7.2 Finding metrics

In the CloudWatch console, open Metrics and browse by namespace. Select a metric and its dimensions, then choose the time range, period, and statistic.

You can also use the AWS CLI:

```bash
aws cloudwatch list-metrics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization
```

To retrieve measurements for an instance:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/EC2 \
  --metric-name CPUUtilization \
  --dimensions Name=InstanceId,Value=i-0123456789abcdef0 \
  --start-time 2026-10-28T00:00:00Z \
  --end-time 2026-10-28T01:00:00Z \
  --period 300 \
  --statistics Average Maximum
```

Replace the example instance ID and timestamps with values for your environment. The query returns data only when matching metrics exist for the selected interval.

### 7.3 Metric math

Metric math combines one or more metric time series using expressions.

For example, suppose `m1` represents network bytes received and `m2` represents network bytes sent. Their combined byte rate can be calculated as:

\\text{Bytes per second} = \\frac{m_1 + m_2}{300}

This example assumes both values are byte totals over a 300-second period. For metrics already expressed as rates, the calculation would be different.

Metric math can help calculate ratios, error percentages, utilization relationships, and other derived indicators without requiring a separate application to compute them.

### 7.4 Dashboard as code

Pulumi can provision CloudWatch dashboards alongside the resources they monitor. This makes dashboard configuration reproducible and version-controlled.

For example, a dashboard widget can reference an EC2 CPU metric using its instance ID. A second widget can reference `CWAgent` memory metrics for the same instance.

This is particularly valuable when environments are created and destroyed repeatedly, because monitoring resources can be deployed together with the application infrastructure.

### 8\. The CloudWatch agent

The CloudWatch agent runs on supported servers and collects telemetry that is not necessarily available through default AWS resource metrics.

For an EC2 instance, the agent can collect:

* Memory utilization and memory-related measurements.

* Filesystem utilization, including disk usage percentages.

* Disk I/O measurements.

* Operating-system logs.

* Additional supported system measurements.

### Agent architecture

EC2 operating system

CPU · RAM · Filesystems · Logs

CloudWatch agent

Collects and publishes configured telemetry

CloudWatch metrics and logs

CWAgent namespace · Log groups · Dashboards

The agent needs AWS permissions to publish the relevant data. For an EC2 instance, the usual approach is to attach an IAM instance profile with the required permissions rather than embedding access keys in a configuration file.

The agent also needs to be installed, configured, and running. An IAM role by itself does not collect any telemetry.

### Example agent configuration

The following JSON configuration collects memory and filesystem utilization and publishes them under the `CWAgent` namespace.

```json
{
  "agent": {
    "metrics_collection_interval": 60,
    "run_as_user": "root"
  },
  "metrics": {
    "namespace": "CWAgent",
    "append_dimensions": {
      "InstanceId": "${aws:InstanceId}"
    },
    "metrics_collected": {
      "mem": {
        "measurement": [
          "mem_used_percent"
        ],
        "metrics_collection_interval": 60
      },
      "disk": {
        "measurement": [
          "used_percent"
        ],
        "resources": [
          "/"
        ],
        "ignore_file_system_types": [
          "sysfs",
          "devtmpfs",
          "tmpfs",
          "overlay",
          "squashfs"
        ],
        "metrics_collection_interval": 60
      }
    }
  }
}
```

Save this as `amazon-cloudwatch-agent.json`.

The `InstanceId` dimension makes it easier to select metrics for a specific EC2 instance. Filesystem paths and available measurements can differ by operating system, so verify the configured resource paths on the chosen AMI.

Note that the configuration uses a 60-second collection interval. Publishing at this interval can generate additional metric data points and costs compared with less frequent collection.

### Lab 1 — Build an Operational Monitoring Dashboard

Estimated duration: 60–90 minutes · AWS Free Tier eligibility and charges depend on your account and resource usage

### 9\. Lab objectives

In this lab, you will build a monitoring environment using Pulumi and Python. You will provision:

* An EC2 instance running Amazon Linux 2023.

* An IAM role and instance profile for Systems Manager and CloudWatch.

* The CloudWatch agent, configured to publish memory and disk utilization.

* A CloudWatch dashboard displaying CPU, memory, disk, and network activity.

### Architecture

Pulumi (Python)

EC2 · IAM · Instance profile · CloudWatch dashboard

Amazon EC2 — Amazon Linux 2023

CloudWatch agent collects memory and filesystem measurements

Amazon CloudWatch

AWS/EC2 metrics + CWAgent metrics

Operational dashboard

CPU · Memory · Disk · Network

### 10\. Prerequisites

Install and configure the following on your development machine:

* Python 3.11 or later.

* Pulumi CLI.

* AWS CLI with an authorized development identity.

* An AWS account with permission to create EC2, IAM, and CloudWatch resources.

Configure your AWS credentials using an AWS CLI profile or another supported credential provider. Do not hardcode credentials in Pulumi programs.

Check your setup:

```bash
pulumi version
python --version
aws sts get-caller-identity
aws configure get region
```

Choose an AWS Region in which you are authorized to create resources.

### 11\. Create the Pulumi project

Create a project directory and initialize a Python project:

```bash
mkdir aws-observability-lab
cd aws-observability-lab

pulumi new aws-python
```

Follow the prompts and select your target AWS Region.

Create and activate a virtual environment if the generated project does not already have one:

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

On Linux or macOS:

```bash
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install pulumi pulumi-aws
```

The project will contain `Pulumi.yaml`, a stack configuration file such as `Pulumi.dev.yaml`, and `__main__.py`.

### 12\. Configure the AWS stack

Set the Region for the stack:

```bash
pulumi config set aws:region us-east-1
```

Replace `us-east-1` with your chosen Region.

For this lab, we will use one EC2 instance and standard EC2 monitoring to keep the architecture simple. The instance profile provides the permissions required by the CloudWatch agent and Systems Manager.

### 13\. Implement the infrastructure

Replace the contents of `__main__.py` with the following program.

The code creates the instance, role, instance profile, CloudWatch dashboard, and agent configuration. It uses the current Amazon Linux 2023 AMI published in the chosen Region.

```python

import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()
region = aws.get_region_output().name

# Find the latest Amazon Linux 2023 x86_64 AMI.
ami = aws.ec2.get_ami(
    most_recent=True,
    owners=["amazon"],
    filters=[
        {
            "name": "name",
            "values": ["al2023-ami-2023.*-x86_64"],
        },
        {
            "name": "architecture",
            "values": ["x86_64"],
        },
        {
            "name": "state",
            "values": ["available"],
        },
    ],
)

# IAM role for EC2.
role = aws.iam.Role(
    "observability-instance-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

# Permissions for Systems Manager and CloudWatch agent publishing.
aws.iam.RolePolicyAttachment(
    "ssm-managed-instance-policy",
    role=role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "AmazonSSMManagedInstanceCore"
    ),
)

aws.iam.RolePolicyAttachment(
    "cloudwatch-agent-policy",
    role=role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "CloudWatchAgentServerPolicy"
    ),
)

profile = aws.iam.InstanceProfile(
    "observability-instance-profile",
    role=role.name,
)

# Collect memory and root-filesystem utilization.
agent_config = {
    "agent": {
        "metrics_collection_interval": 60,
        "run_as_user": "root",
    },
    "metrics": {
        "namespace": "CWAgent",
        "append_dimensions": {
            "InstanceId": "${aws:InstanceId}",
        },
        "metrics_collected": {
            "mem": {
                "measurement": ["mem_used_percent"],
                "metrics_collection_interval": 60,
            },
            "disk": {
                "measurement": ["used_percent"],
                "resources": ["/"],
                "ignore_file_system_types": [
                    "sysfs",
                    "devtmpfs",
                    "tmpfs",
                    "overlay",
                    "squashfs",
                ],
                "metrics_collection_interval": 60,
            },
        },
    },
}

user_data = f"""#!/bin/bash
set -euxo pipefail

dnf install -y amazon-cloudwatch-agent

cat > /opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json <<'CWCONFIG'
{json.dumps(agent_config)}
CWCONFIG

/opt/aws/amazon-cloudwatch-agent/bin/amazon-cloudwatch-agent-ctl \
  -a fetch-config \
  -m ec2 \
  -c file:/opt/aws/amazon-cloudwatch-agent/etc/amazon-cloudwatch-agent.json \
  -s

systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent
"""

instance = aws.ec2.Instance(
    "observability-ec2",
    ami=ami.id,
    instance_type="t3.micro",
    iam_instance_profile=profile.name,
    user_data=user_data,
    user_data_replace_on_change=True,
    monitoring=False,
    tags={
        "Name": "observability-lab",
        "Environment": "learning",
        "ManagedBy": "Pulumi",
    },
)

# AWS/EC2 metrics are published automatically.
cpu_widget = {
    "type": "metric",
    "x": 0,
    "y": 0,
    "width": 12,
    "height": 6,
    "properties": {
        "title": "CPU Utilization (%)",
        "view": "timeSeries",
        "region": region,
        "period": 300,
        "stat": "Average",
        "metrics": [
            [
                "AWS/EC2",
                "CPUUtilization",
                "InstanceId",
                instance.id,
            ],
        ],
    },
}

network_widget = {
    "type": "metric",
    "x": 12,
    "y": 0,
    "width": 12,
    "height": 6,
    "properties": {
        "title": "Network Traffic (bytes)",
        "view": "timeSeries",
        "region": region,
        "period": 300,
        "stat": "Sum",
        "metrics": [
            [
                "AWS/EC2",
                "NetworkIn",
                "InstanceId",
                instance.id,
            ],
            [
                "AWS/EC2",
                "NetworkOut",
                "InstanceId",
                instance.id,
            ],
        ],
    },
}

# Agent metrics have additional dimensions, such as path,
# device, and fstype for filesystem measurements. Discover
# their exact dimension sets in CloudWatch before adding them.
memory_widget = {
    "type": "metric",
    "x": 0,
    "y": 6,
    "width": 12,
    "height": 6,
    "properties": {
        "title": "Memory Utilization (%)",
        "view": "timeSeries",
        "region": region,
        "period": 60,
        "stat": "Average",
        "metrics": [
            [
                "CWAgent",
                "mem_used_percent",
                "InstanceId",
                instance.id,
            ],
        ],
    },
}

dashboard_body = {
    "widgets": [
        cpu_widget,
        network_widget,
        memory_widget,
    ],
}

dashboard = aws.cloudwatch.Dashboard(
    "observability-dashboard",
    dashboard_name="Observability-Lab",
    dashboard_body=json.dumps(dashboard_body),
)

pulumi.export("instance_id", instance.id)
pulumi.export("dashboard_name", dashboard.dashboard_name)
pulumi.export("region", region)
```

### Important implementation details

* The instance uses an automatically selected Amazon Linux 2023 AMI.

* The IAM role grants the agent permission to publish metrics and enables Systems Manager managed-node functionality.

* The `user_data` script installs and starts the agent during initial instance boot.

* EC2 CPU and network metrics are available independently of the agent.

* The dashboard includes CPU, network, and memory widgets. You will add the disk widget after verifying the filesystem metric dimensions in CloudWatch.

* The instance does not open SSH or HTTP ports. Session Manager access requires the instance to reach the Systems Manager endpoints, either through outbound connectivity or appropriately configured VPC endpoints.

The dashboard uses a 300-second period for the standard EC2 widgets and a 60-second period for memory. A metric might not appear immediately after deployment because the instance must boot and the agent must publish its first measurements.

### 14\. Deploy the stack

Preview the planned changes:

```bash
pulumi preview
```

Review the resources and confirm that the plan is limited to the intended lab infrastructure. Then deploy:

```bash
pulumi up
```

Confirm the update when prompted.

Retrieve the instance ID and dashboard name:

```bash
pulumi stack output instance_id
pulumi stack output dashboard_name
pulumi stack output region
```

The initial deployment may take several minutes. Installing the agent and publishing the first metrics requires additional time after the EC2 instance starts.

### 15\. Verify the monitoring pipeline

### Step 1 — Check the EC2 instance

Open the EC2 console and locate `observability-lab`.

Confirm that the instance is running and its status checks have passed. Verify that it has the intended IAM instance profile.

### Step 2 — Verify the CloudWatch agent

In the Systems Manager console, open Fleet Manager or Managed nodes and look for the instance.

You can also inspect the agent's log on the instance through Session Manager:

```bash
sudo tail -n 100 \
  /opt/aws/amazon-cloudwatch-agent/logs/amazon-cloudwatch-agent.log
```

Check that the agent started successfully and that no configuration or permission errors are being reported.

If the instance does not appear as a managed node, check its SSM Agent status, IAM role, and network connectivity to the Systems Manager endpoints.

### Step 3 — Inspect CloudWatch metrics

Open CloudWatch in the same AWS Region and navigate to Metrics → All metrics.

Look for:

* `AWS/EC2` → `CPUUtilization`

* `AWS/EC2` → `NetworkIn` and `NetworkOut`

* `CWAgent` → `mem_used_percent`

* `CWAgent` → `disk_used_percent`

The exact dimensions for agent metrics depend on the metric and agent configuration. For filesystem metrics, CloudWatch can include `InstanceId`, `path`, `device`, and `fstype`.

If a metric is missing, inspect the dimensions and configuration before assuming the agent failed.

### Step 4 — Open the dashboard

Navigate to CloudWatch → Dashboards → `Observability-Lab`.

You should see CPU utilization, network traffic, and memory utilization after the corresponding metrics have been published.

### Step 5 — Add disk utilization

In CloudWatch Metrics, find the `CWAgent` metric `disk_used_percent` for your instance. Select the root filesystem series, confirm its dimensions, and add it to the dashboard.

Alternatively, extend the `dashboard_body` in `__main__.py` with a widget using the exact dimensions displayed for the selected metric:

```python
disk_widget = {
    "type": "metric",
    "x": 12,
    "y": 6,
    "width": 12,
    "height": 6,
    "properties": {
        "title": "Root Filesystem Utilization (%)",
        "view": "timeSeries",
        "region": region,
        "period": 60,
        "stat": "Average",
        "metrics": [
            [
                "CWAgent",
                "disk_used_percent",
                "InstanceId",
                instance.id,
                "device",
                "/dev/YOUR_DEVICE",
                "fstype",
                "xfs",
                "path",
                "/",
            ],
        ],
    },
}
```

Important: This is a template, not a guaranteed match for every AMI. Replace `YOUR_DEVICE` and `xfs` with the actual `device` and `fstype` values published for your root filesystem. If the metric has a different dimension set, update the widget accordingly. Then include `disk_widget` in `dashboard_body["widgets"]` and run `pulumi up` again.

### 16\. Troubleshooting guide

| Symptom                               | Likely cause                                        | What to check                                                      |
| ------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------ |
| CPU graph is empty                    | Wrong Region, instance ID, or time range            | Verify the AWS/EC2 metric and dimensions                           |
| Memory metric is missing              | Agent did not start or lacks permission             | Agent log, IAM policy, and CWAgent namespace                       |
| Disk metric is missing                | Filesystem configuration or dimensions do not match | Agent configuration and published disk_used_percent dimensions     |
| Instance is not a managed node        | SSM Agent or network connectivity problem           | Instance profile, SSM Agent status, and endpoint access            |
| Dashboard loads but widgets are blank | Metrics have not arrived yet                        | Wait for publication and select a suitable time range              |
| Agent installation failed             | Package repository or network access problem        | Cloud-init output, package availability, and outbound connectivity |

For boot-time failures, inspect the cloud-init logs:

```bash
sudo tail -n 100 /var/log/cloud-init-output.log
```

For additional metric troubleshooting, verify that the CloudWatch agent is running, that the intended configuration was loaded, and that the instance can reach the CloudWatch monitoring endpoint.

### 17\. Operational improvements

Once the basic dashboard works, consider these production-oriented improvements:

* Enable detailed EC2 monitoring only when the additional granularity is needed.

* Add alarms for sustained CPU utilization, status-check failures, and memory or disk thresholds.

* Use SNS to notify operators when alarms change state.

* Add application-level metrics, such as request latency and error rates.

* Apply metric retention, log retention, and cost controls deliberately.

* Separate IAM permissions for infrastructure deployment from those used by the EC2 instance.

* Manage dashboard and alarm definitions in Pulumi alongside the workload.

### 18\. Clean up the lab

When finished, destroy the resources created by the stack:

```bash
pulumi destroy
```

Review the proposed deletions and confirm them. Then, if you no longer need the stack:

```bash
pulumi stack rm
```

Deleting the stack removes its state from Pulumi, so do this only after confirming that its resources have been destroyed and you no longer need the stack.

Check the AWS console afterward to ensure no billable lab resources remain. Also review any resources created manually outside Pulumi.

### Module 1 summary

You have covered the foundations of AWS observability and learned how CloudWatch collects and presents operational measurements. The lab combines infrastructure provisioning with Pulumi, agent-based telemetry collection, and a dashboard for EC2 performance.

The key distinction to remember is that CloudWatch's default EC2 metrics describe infrastructure behavior, while the CloudWatch agent adds operating-system visibility. Combining both gives you a more useful view of workload health and provides a foundation for the alarms and incident-response workflows developed in later modules.
