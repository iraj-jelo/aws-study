### Module 7 — AWS Budgets, Cost Explorer, and Cost Operations

AWS Operations and Observability · Pulumi · Python examples

### Module objectives

The goal of this module is to learn how to monitor AWS spending, identify unexpected cost increases, allocate costs to teams and workloads, and establish safeguards against budget overruns.

By the end of this module, you should understand how AWS billing data is collected, how to analyze spending patterns, and how to automate cost notifications and selected cost-control actions.

### 1\. Understanding AWS cost management

AWS cost management involves three related activities:

* Cost visibility: Understand what you're spending money on.

* Cost governance: Set budgets, assign ownership, and notify responsible people when spending exceeds thresholds.

* Cost optimization: Reduce unnecessary spending without compromising reliability, security, or performance.

These activities use different AWS services.

| Service                                             | Primary responsibility                                           |
| --------------------------------------------------- | ---------------------------------------------------------------- |
| AWS Cost Explorer                                   | Analyze historical and forecast costs and usage.                 |
| AWS Budgets                                         | Define spending or usage limits and configure alerts.            |
| AWS Cost Anomaly Detection                          | Identify unusual spending patterns.                              |
| AWS Cost and Usage Reports (CUR) / AWS Data Exports | Access detailed billing and usage records.                       |
| AWS Billing and Cost Management                     | Centralize billing, cost-management settings, and reports.       |
| Amazon SNS                                          | Deliver budget and operational notifications.                    |
| AWS IAM                                             | Control who can view costs and modify cost-management resources. |

These services complement one another. Cost Explorer helps investigate spending, Budgets evaluates configured thresholds, and Cost Anomaly Detection identifies unusual patterns that might not cross a predefined budget threshold.

### 2\. AWS Cost Explorer

AWS Cost Explorer provides interactive reports for understanding historical AWS spending and examining usage patterns. It also supports cost forecasting based on historical trends.

### 2.1 Cost dimensions and metrics

Cost Explorer allows you to group and filter spending using dimensions such as:

* Service: EC2, S3, CloudWatch, and other AWS services.

* Region: Identify geographic differences in spending.

* Usage type: Investigate charges associated with specific types of resource usage.

* Linked account: Compare spending across AWS accounts in an organization.

* Tag: Attribute eligible costs to an application, team, environment, or project.

* Purchase option: Examine on-demand and applicable commitment-based usage.

* Charge type: Distinguish usage charges, credits, refunds, and other billing adjustments where available.

Common metrics include unblended cost, amortized cost, usage quantity, and forecasted cost. The right metric depends on the question being investigated.

For example, unblended cost can help examine charges as recorded, while amortized cost allocates eligible upfront and recurring commitment costs across the relevant usage periods.

### 2.2 Investigating a spending increase

Imagine an application team's monthly AWS spending increases from $400 to $650.

### Illustrative monthly cost comparison

Previous month

### $400

Current month

### $650

Increase

### 62.5%

Illustrative figures, not live AWS billing data.

A useful investigation sequence is:

* Compare the two periods using the same cost metric and billing scope.

* Group costs by service to find which services contributed most to the increase.

* Filter the largest contributor by Region, usage type, linked account, and applicable cost allocation tags.

* Compare resource usage and deployment changes during the affected period.

* Review CloudTrail events and CloudWatch metrics to investigate possible causes.

* Identify an appropriate corrective action and verify its effect in subsequent billing data.

A cost increase is a symptom, not proof of waste. Increased traffic, data processing, backup activity, or a planned deployment may explain the difference.

### 3\. AWS Budgets

AWS Budgets lets you define spending targets and receive notifications when actual or forecast costs cross configured thresholds. It also supports usage and commitment-related budgets. Pulumi Registry +1

### 3.1 Budget types

| Budget type                                | What it monitors                                  | Example                                    |
| ------------------------------------------ | ------------------------------------------------- | ------------------------------------------ |
| Cost                                       | Spending in a chosen period                       | Monthly cost below $500                    |
| Usage                                      | Consumption of a measurable resource or service   | Track eligible usage against a target      |
| Reserved Instance utilization              | Use of purchased Reserved Instance capacity       | Alert when utilization falls below target  |
| Savings Plans utilization                  | Use of purchased Savings Plans commitments        | Identify underused commitments             |
| Reserved Instance / Savings Plans coverage | How much eligible usage is covered by commitments | Identify opportunities to improve coverage |

Exact dimensions and available metrics depend on the budget type.

### 3.2 Actual versus forecast thresholds

Suppose a monthly budget is $500.

### Example alert policy

Warning — 80% actual cost

### $400

Notify the responsible team when actual spending exceeds 80% of the budget.

Early warning — 100% forecasted cost

### $500 projected

Notify the team when the forecast indicates the budget may be fully consumed.

Illustrative thresholds. Budget notifications are not a real-time spending limit or a guarantee that charges will stop.

Actual and forecasted notifications answer different questions:

* Actual: Have we already spent more than the configured percentage of our budget?

* Forecasted: Does the current forecast indicate that spending will exceed the configured threshold?

Forecasts are estimates, and alerts can arrive after the underlying usage has occurred. Use them as an operational signal, not as a hard spending cap. Pulumi Registry +1

### 3.3 Notification delivery

Budget notifications can be sent directly to email subscribers or to an Amazon SNS topic. SNS can then fan out notifications to supported subscribers and downstream workflows. AWS CloudFormation +1

A typical design is:

AWS Budgets

Evaluates actual and forecast spending

Amazon SNS

Distributes the alert

Email

Automated workflow

Use email for straightforward alerts. Use an automated workflow only when you have a well-defined response, appropriate permissions, logging, and safeguards.

### 4\. Provisioning a budget with Pulumi

We will use the Pulumi AWS provider with Python. The following example creates a monthly cost budget of $500 and two email alerts.

### 4.1 Create the project

```bash
mkdir aws-cost-operations
cd aws-cost-operations

pulumi new aws-python
```

Configure your AWS credentials using your existing approved AWS authentication method, and select the target account and Region. Billing data and cost-management resources have account-level considerations, so verify that your deployment identity has the necessary permissions.

Install or update the provider dependency as appropriate for the generated project:

```bash
uv add pulumi pulumi-aws
```

### 4.2 Configure the budget

In `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

alert_email = config.require("alertEmail")
monthly_budget = config.get_float("monthlyBudget") or 500.0

cost_budget = aws.budgets.Budget(
    "monthly-operations-budget",
    name="monthly-operations-budget",
    budget_type="COST",
    limit_amount=str(monthly_budget),
    limit_unit="USD",
    time_unit="MONTHLY",
    notifications=[
        aws.budgets.BudgetNotificationArgs(
            comparison_operator="GREATER_THAN",
            notification_type="ACTUAL",
            threshold=80,
            threshold_type="PERCENTAGE",
            subscriber_email_addresses=[alert_email],
        ),
        aws.budgets.BudgetNotificationArgs(
            comparison_operator="GREATER_THAN",
            notification_type="FORECASTED",
            threshold=100,
            threshold_type="PERCENTAGE",
            subscriber_email_addresses=[alert_email],
        ),
    ],
    tags={
        "Project": "aws-operations",
        "Environment": "learning",
        "ManagedBy": "Pulumi",
    },
)

pulumi.export("budget_name", cost_budget.name)
pulumi.export("monthly_budget_usd", str(monthly_budget))
```

This uses the Pulumi AWS provider's `aws.budgets.Budget` resource and its notification configuration. Pulumi Registry +1

Configure the stack:

```bash
pulumi config set alertEmail your-address@example.com
pulumi config set monthlyBudget 500
```

Replace the example email with an address you control. Cost-management notifications may contain billing information, so use an appropriate recipient.

Preview and deploy:

```bash
pulumi preview
pulumi up
```

Review the preview before confirming the update. After deployment, check the budget in the AWS Billing and Cost Management console and complete any email subscription confirmation required by the notification mechanism.

To remove the resources created by this project when you are finished:

```bash
pulumi destroy
```

Important: Creating a budget does not activate cost allocation tags, create a detailed billing export, or impose a spending cap. Those are separate configuration tasks.

### 5\. Cost allocation tags and resource ownership

Tags help answer an important operational question: Which team or workload is responsible for a particular cost?

### 5.1 Define a consistent tagging strategy

Use a small set of standardized keys across resources.

| Tag key     | Example value       | Purpose                             |
| ----------- | ------------------- | ----------------------------------- |
| Project     | book-recommendation | Identify the application            |
| Environment | development         | Separate development and production |
| Team        | platform            | Identify the responsible team       |
| CostCenter  | engineering-001     | Attribute costs to a cost center    |
| ManagedBy   | Pulumi              | Identify infrastructure management  |

Example Pulumi resource tagging:

```python
import pulumi_aws as aws

instance = aws.ec2.Instance(
    "application-server",
    instance_type="t3.micro",
    ami="ami-REPLACE_WITH_VALID_AMI_ID",
    tags={
        "Project": "book-recommendation",
        "Environment": "development",
        "Team": "platform",
        "CostCenter": "engineering-001",
        "ManagedBy": "Pulumi",
    },
)
```

The AMI value is a placeholder; replace it with a valid image ID for the selected Region before deploying. This example assumes that the associated network configuration and permissions are handled separately.

### 5.2 Activate cost allocation tags

Applying tags to resources does not automatically make every tag available in billing reports.

* Apply standardized tags to supported resources.

* Open the AWS Billing and Cost Management console.

* Navigate to Cost Allocation Tags.

* Activate the relevant user-defined tags.

* Allow time for activation and billing data to become available.

* Use the activated tags in Cost Explorer and supported cost-management reports.

AWS also supports account-level cost allocation tags through AWS Organizations, which can help allocate costs that cannot be tagged at the individual resource level. AWS Billing +1

### 5.3 Cost allocation strategy

A practical strategy combines multiple levels of ownership:

* Use separate AWS accounts for major environments or business units when appropriate.

* Apply resource tags to identify applications, teams, and environments.

* Use account tags to allocate account-level costs where supported.

* Use Cost Explorer to analyze costs by available dimensions.

* Define budgets for the overall account and important workloads.

Remember that not every AWS charge can be attributed perfectly to a resource tag. Shared networking, support, data transfer, and other shared costs may require a documented allocation policy.

### 6\. Cost and Usage Reports and AWS Data Exports

Cost Explorer is convenient for interactive analysis. For detailed billing analytics, AWS Data Exports provides a way to deliver recurring cost and usage data for downstream processing.

AWS recommends Cost and Usage Report 2.0 (CUR 2.0) for detailed cost and usage data. Exports can be stored in Amazon S3 and analyzed using tools such as Athena and QuickSight. AWS Data Exports +1

A typical architecture looks like this:

AWS billing and usage data

AWS Data Exports — CUR 2.0

Amazon S3

Durable billing data storage

Amazon Athena

SQL analysis

Amazon QuickSight

Dashboards

### When should you use CUR 2.0?

Use detailed exports when you need to:

* Investigate charges at a more granular level than a standard Cost Explorer report.

* Build recurring reports for teams or business units.

* Query historical billing records with SQL.

* Combine billing information with internal application or ownership data.

* Produce custom dashboards or financial reports.

For this module, start with Cost Explorer and Budgets. Introduce CUR 2.0 when the analysis requires detailed records or repeatable reporting pipelines.

### 7\. Cost Anomaly Detection and optimization

### 7.1 AWS Cost Anomaly Detection

Cost Anomaly Detection identifies spending patterns that differ from expected behavior. This complements budgets because an unusual increase may occur even when total spending remains below the monthly budget.

For example:

* An unexpected increase in S3 requests.

* A sudden rise in data transfer charges.

* An EC2 workload consuming substantially more resources.

* An unplanned increase in log ingestion.

When an anomaly is detected, examine the affected service, cost impact, and time period. Then correlate the finding with deployments, CloudTrail activity, and CloudWatch telemetry.

### 7.2 Practical cost optimization

| Area                     | Investigation                                   | Potential improvement                                    |
| ------------------------ | ----------------------------------------------- | -------------------------------------------------------- |
| EC2                      | CPU, memory, and utilization patterns           | Right-size instances or schedule nonproduction workloads |
| CloudWatch Logs          | Ingestion volume and retention                  | Reduce unnecessary logs and configure suitable retention |
| S3                       | Storage class, age, and access patterns         | Apply lifecycle policies where appropriate               |
| Data transfer            | Transfer volume and network paths               | Reduce unnecessary cross-Region or external transfers    |
| Commitment spending      | Reserved Instance and Savings Plans utilization | Evaluate commitments against stable demand               |
| Development environments | Idle resources outside working hours            | Schedule shutdowns where safe                            |

Do not optimize based on price alone. Validate application performance, availability requirements, recovery objectives, and operational overhead before making changes.

### 8\. Budget actions, IAM, and safeguards

AWS Budgets can support selected actions when thresholds are crossed. Depending on the configuration, actions can apply IAM policies, use service control policies (SCPs), or target supported resources through an appropriate workflow.

However, a budget is not a universal hard spending limit. It does not automatically stop every resource when the budget is exceeded.

A safe operating model is:

* Start with notifications only.

* Review alert accuracy and tune thresholds.

* Identify which resources are safe to change automatically.

* Apply least-privilege permissions.

* Test automation in a development account.

* Require approval or provide rollback mechanisms for disruptive changes.

* Audit all actions and periodically review the policy.

Avoid automatically stopping production resources merely because a budget threshold was crossed. A sudden cost increase may be caused by legitimate demand, and indiscriminate shutdowns can create an outage.

### Lab 7 — Implement Cost Monitoring and Alerts

Infrastructure as Code: Pulumi with Python

### Lab architecture

Pulumi project

Budget and notification configuration

AWS Budgets

Threshold evaluation

Resource tags

Cost ownership

Email alerts and cost reports

Investigate and respond to cost changes

### Lab objectives

By the end of the lab, you will have:

* Created a monthly cost budget using Pulumi.

* Configured actual and forecast thresholds.

* Deployed and verified email notifications.

* Applied a consistent tagging strategy to a sample workload.

* Investigated a spending increase using Cost Explorer.

### Step 1 — Prepare the environment

Verify that your AWS identity has the required permissions for AWS Budgets and any resources you intend to tag. Cost Explorer and billing features may also require account-level setup and billing permissions.

Configure your Pulumi project using the code in Section 4. Begin with a budget of $500 and a warning threshold of 80%.

### Step 2 — Preview and deploy

```bash
pulumi preview
pulumi up
```

Inspect the proposed changes before deployment. Confirm that the budget and both notifications appear in the AWS console.

### Step 3 — Configure and verify cost allocation

Apply the tags from Section 5 to your sample workload. Activate the relevant cost allocation tags in Billing and Cost Management.

Allow for billing-data and tag-activation delays. Do not expect a newly deployed resource to appear immediately in every cost report.

### Step 4 — Investigate a spending increase

Open Cost Explorer and compare two suitable historical periods. Group by service and investigate the largest changes. Use resource tags, where available, to identify ownership.

If you are working in a new or low-usage account, you may not have enough historical data to produce a meaningful comparison. In that case, use a supplied sample cost report or examine a representative historical dataset rather than creating unnecessary AWS usage just to generate charges.

### Step 5 — Review the operational safeguards

Confirm that the budget sends notifications rather than applying disruptive automatic actions. Document who receives each alert and how the team should respond.

When finished, remove lab resources you no longer need:

```bash
pulumi destroy
```

Deleting a budget does not delete unrelated workload resources, and deleting lab resources does not erase charges already incurred.

### Key takeaways

* Cost Explorer explains historical spending and helps investigate cost drivers.

* AWS Budgets monitors configured spending or usage thresholds.

* Cost Anomaly Detection helps identify unusual spending patterns.

* Cost allocation tags improve visibility into application and team ownership.

* CUR 2.0 through AWS Data Exports supports detailed, repeatable billing analytics.

* Pulumi makes cost-monitoring infrastructure reproducible and maintainable.

Official references for further reading:

* [Pulumi AWS Budgets resource](https://www.pulumi.com/registry/packages/aws/api-docs/budgets/budget/?utm_source=chatgpt.com)

* [AWS Cost Explorer documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/ce-what-is.html?utm_source=chatgpt.com)

* [Managing costs with AWS Budgets](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html?utm_source=chatgpt.com)

* [AWS Data Exports and CUR 2.0](https://docs.aws.amazon.com/cur/latest/userguide/what-is-data-exports.html?utm_source=chatgpt.com)
