### AWS Operations and Observability — Course Outline

8 modules · Pulumi · Hands-on labs · No exams or quizzes

Course goal: Learn how to operate, monitor, troubleshoot, secure, and control the cost of AWS workloads using AWS-native operational services and Infrastructure as Code with Pulumi.

Prerequisites: Basic AWS knowledge, IAM fundamentals, EC2, VPC, S3, and basic familiarity with Python or TypeScript. Prior Pulumi knowledge is helpful.

### Course curriculum

![](https://images.openai.com/static-rsc-4/Vt6Uafjy6CDDnAYpCyexaGwbue8qkHECf6KCoFTy0E6Tr4TXHmBlMMXvdkoskIFwunD414MRZLUYFPopM-84dzRS7wyxDCPBtymPcY9rKpo_HJ5B-pFUDplJQklHk0HJDG0Fh8MXWB810eBvMq_qeV0f8rBey2d7S_uKzehUSOtJAduVdSO4MGrzPMaXdAU9?purpose=fullsize)

### Module 1 — Observability Foundations and CloudWatch Metrics

Goal: Understand how to monitor workload health and performance.

* Observability fundamentals: metrics, logs, traces, events, and telemetry.

* Amazon CloudWatch architecture, namespaces, dimensions, and statistics.

* EC2, EBS, load balancer, and application metrics.

* Standard versus detailed monitoring and custom metrics.

* CloudWatch dashboards, metric math, and metric search.

* CloudWatch agent for operating-system metrics and logs.

Lab 1 — Build an Operational Monitoring Dashboard

* Provision an EC2 instance and supporting IAM resources using Pulumi.

* Configure the CloudWatch agent and collect system metrics.

* Create a dashboard for CPU, memory, disk usage, and network activity.

![Guided Lab: Introduction to CloudWatch Logs Insights - Tutorials Dojo](https://images.openai.com/static-rsc-4/fxlUyzkJhB3_QpC0O53_qubHczg8FcX8xwDk3U3bx0Wk5BYN7HnvzewOgDbNpPfDz_nB5T2byblUIgStwOoMzbe3vvveqJIOUqoR_Ub5PdJ3BR3xWjw9gBKNCDkG3WAkfimopbY3Dmce_Etz8m9bnPVIwI96ZEh2G_ArCasbWIy_XIqB3feoYKTIwlFA0TmX?purpose=fullsize)

### Module 2 — CloudWatch Logs, Alarms, and Notifications

Goal: Detect failures and investigate application problems.

* CloudWatch Logs groups, streams, retention, and ingestion.

* Application and system log collection.

* CloudWatch Logs Insights query language and troubleshooting.

* Metric filters and custom application metrics.

* CloudWatch alarms, thresholds, evaluation periods, and missing data.

* Composite alarms, anomaly detection, and alarm actions.

* Amazon SNS notifications and operational alerting.

Lab 2 — Detect and Diagnose Application Failures

* Deploy a sample application and configure centralized log collection with Pulumi.

* Create metric filters for errors and failed requests.

* Configure alarms and SNS notifications.

* Investigate application errors using Logs Insights.

![Listening To Events By AWS Services | AWS](https://images.openai.com/static-rsc-4/SnqVvwuZUoYhpVJLhOSXIOZH5Hn00Exaq_iG857dtX_CUUvfubv0v_6MCMQloKX90froSIz53OgUYMJNGBqvejbvrypVgU4DAKssxYZq8VTsvU2_gW0-h-Eq31CvyiXEM_fRiFTRCtkR5xQYyQdFlDEl0vAMvYOzRubB0nw3OBPP-KsYNM_KViNaCAh2XFOp?purpose=fullsize)

### Module 3 — AWS CloudTrail and Audit Operations

Goal: Understand who changed AWS resources, what happened, and when.

* CloudTrail event history and management events.

* Read-only versus write management events.

* Data events for services such as S3 and Lambda.

* CloudTrail trails, S3 log destinations, and log file validation.

* CloudTrail integration with CloudWatch Logs.

* EventBridge rules for detecting important API activity.

* Investigating unauthorized changes and unexpected API calls.

* IAM permissions and secure audit-log retention.

Lab 3 — Build an AWS Audit and Detection Pipeline

* Provision a CloudTrail trail and dedicated S3 log bucket using Pulumi.

* Configure selected event monitoring and CloudWatch Logs integration.

* Detect a resource modification with EventBridge.

* Investigate the associated API event and identify the principal responsible.

![Viewing Compliance History for your AWS Resources with AWS Config - AWS Config](https://images.openai.com/static-rsc-4/uRP8xz9YcfKyPfqt-UVlaXA0mMHa20xe2YmbMTzhjwsYnaqXpXibjhedYtQLeE0uJEIufZLA9-j3DCotBIoG3yJUidJGGGgGwpqWHuuXCeEmPJmXGEJIcjoM8Oll5OMeuAyst7H60judhfYc7lJb_zdZ9k01e-5HuGEr7jBpzfKvHZ_lWtpxR4yjr99U1u37?purpose=fullsize)

### Module 4 — AWS Config and Configuration Compliance

Goal: Track resource configurations and detect compliance drift.

* AWS Config recorders, configuration items, and resource inventory.

* Configuration history and resource relationships.

* Managed and custom AWS Config rules.

* Compliance evaluations and remediation workflows.

* Conformance packs and organization-level configuration management.

* Configuration drift versus infrastructure drift.

* AWS Config integration with CloudTrail and Systems Manager.

* Cost, recording scope, and resource coverage considerations.

Lab 4 — Detect and Remediate Configuration Drift

* Provision AWS Config resources and selected managed rules using Pulumi.

* Detect noncompliant resource configurations.

* Review configuration history and identify the change.

* Design and implement a remediation workflow using Systems Manager where appropriate.

![Ihre Kontoereignisse im AWS Health Dashboard anzeigen - AWS Health](https://images.openai.com/static-rsc-4/iAUSsMeousDsVLGJZhmD5KKCRq2c7RgQiXF511N7fLkO38v5tG-ZzlZVM06I0AY4qodFinASAYdbgZIgabxjD6Ld7i2ER9-F5Vl6OYDd-9xrUisxhMa2iB33FYdOFTtMLym-Mpz2UYEzp3zULc9SLI6SVEaC5DSrJq0c1udJ7_aaOmOq54iabASPa-yaxFtA?purpose=fullsize)

### Module 5 — AWS Health and Incident Awareness

Goal: Recognize AWS service issues and account-specific events that affect workloads.

* AWS Health Dashboard and account-specific events.

* Service health events, scheduled changes, and maintenance notifications.

* AWS Health organizational views and delegated administration.

* EventBridge integration for AWS Health events.

* Planned lifecycle events and affected-resource identification.

* Incident triage, escalation, and operational runbooks.

* Distinguishing AWS infrastructure issues from application failures.

* AWS Health API access and feature availability considerations.

Lab 5 — Create an AWS Health Event Notification Workflow

* Configure EventBridge rules for selected AWS Health event types.

* Route matching events to SNS or another supported notification target.

* Define an incident runbook that identifies affected resources and next steps.

* Test the routing logic with representative events or a controlled simulation.

![AWS Systems manager와 Amazon Inspector로 Amazon EC2 자산 관리 자동화 하기 | AWS 기술 블로그](https://images.openai.com/static-rsc-4/C6T4cdFL0oEae1roT4Y4TIAbl4fMte3ZlpU1K5mpPdZ4nkLU9qWITEr6J8K7Y2AkxjWJbUB1l93IRQTyCcrSLSjotZulJRGm9Z4CRNuE5s0fBKNv1-D2dQR_uuzbmiViomXoHNxWUnKACuOT51-xHwXeTrJltZIsS5zO0fT86d2qMhL3y4wofizXusxMGfju?purpose=fullsize)

### Module 6 — AWS Systems Manager and Fleet Operations

Goal: Operate instances securely without relying on routine SSH or RDP access.

* Systems Manager architecture, SSM Agent, and managed-node prerequisites.

* IAM instance profiles and Systems Manager permissions.

* Session Manager for secure shell access without inbound management ports.

* Run Command and Automation documents.

* Patch Manager and patch compliance.

* State Manager and desired-state enforcement.

* Parameter Store for operational configuration and secrets-related use cases.

* Inventory, Fleet Manager, and maintenance workflows.

* Operational runbooks, least privilege, and audit integration.

Lab 6 — Manage and Troubleshoot an EC2 Fleet

* Provision EC2 instances, IAM roles, and required policies using Pulumi.

* Register instances as Systems Manager managed nodes.

* Run diagnostic commands and collect operational information.

* Execute a controlled automation or patching workflow.

* Review execution history and audit activity.

![Getting Started with AWS Cost Explorer | AWS Cloud Financial Management](https://images.openai.com/static-rsc-4/YtjByZwYsEl3woLUNLcAs4dZ67e5TnxolKESlfvpYe_8c09cw2FFfYQN8jgINnLaA-AKxydg_eXayZ6hcHVm68XTQ8hkGRJNFZI_ejdeatoyO_97rIGpQOKAq6nOQhlvDvwzXlo7rDCENg4a81qX_8jaWIPgRGZTXT_BjxMHnHsOOHfjxrQD4oI13P6h6bea?purpose=fullsize)

### Module 7 — AWS Budgets, Cost Explorer, and Cost Operations

Goal: Monitor spending, investigate cost increases, and establish cost controls.

* AWS Cost Explorer: cost trends, usage patterns, and service-level analysis.

* AWS Budgets for cost, usage, and reservation or commitment monitoring.

* Budget thresholds, forecast alerts, and SNS notifications.

* Cost allocation tags and resource ownership.

* AWS Cost and Usage Reports (CUR) and AWS Data Exports.

* Cost anomalies and unexpected workload growth.

* Cost optimization through CloudWatch retention, instance sizing, and storage lifecycle policies.

* Budget actions, permissions, and safeguards against unintended changes.

Lab 7 — Implement Cost Monitoring and Alerts

* Provision supported budget and notification resources using Pulumi.

* Configure cost thresholds and alert recipients.

* Analyze a sample spending increase using Cost Explorer.

* Apply resource tags and produce a basic cost allocation strategy.

![Hello, CloudWatch!](https://images.openai.com/static-rsc-4/JN3zWmfvVl41My1zxLcTtSASAhvJEjpPiv_mrxasNmwmD1vExG1rcYVzIYGVOVpuxlH4eM3vzax2-0eOKT4s49jf_I_bYqqDnG-f_t5kJN1LkooFaLUCxjYZVZhFr-qYrN_boX2ntRSTFIIa2nByWFduTVnaMi_0bphtFQio0udFBeiC-nP5wylGoRAdKcm8?purpose=fullsize)

### Module 8 — Capstone: Production Operations and Incident Response

Goal: Combine observability, auditing, configuration management, fleet operations, and cost controls into a coherent operational platform.

* Operational architecture and service integration.

* Incident detection, triage, root-cause investigation, and recovery.

* Correlating CloudWatch alarms, logs, CloudTrail events, and AWS Health events.

* Config compliance and Systems Manager remediation.

* Dashboards, alert routing, escalation, and runbook design.

* Reliability indicators, service-level objectives, and alert fatigue.

* Operational IAM boundaries and auditability.

* Pulumi project structure, stacks, configuration, state management, and safe updates.

* Cost controls, cleanup strategy, and production-readiness considerations.

Lab 8 — Operate a Production-Like AWS Workload

* Deploy a small workload and its monitoring infrastructure using Pulumi.

* Create dashboards, alarms, centralized logs, and notifications.

* Configure CloudTrail auditing and selected AWS Config rules.

* Integrate Systems Manager for secure diagnostics and recovery.

* Establish a budget and a documented incident-response workflow.

* Investigate a controlled failure and produce a root-cause report.

### Recommended technical approach

| Area                     | Approach                                        |
| ------------------------ | ----------------------------------------------- |
| Infrastructure as Code   | Pulumi with Python or TypeScript                |
| Compute workload         | Amazon EC2                                      |
| Metrics, logs, alarms    | Amazon CloudWatch                               |
| API auditing             | AWS CloudTrail                                  |
| Configuration compliance | AWS Config                                      |
| Incident awareness       | AWS Health + EventBridge                        |
| Fleet operations         | AWS Systems Manager                             |
| Cost visibility          | AWS Budgets + Cost Explorer                     |
| Notifications            | Amazon SNS                                      |
| Source control           | Git                                             |
| Deployment workflow      | Pulumi preview, update, and stack configuration |

### Course completion outcomes

By the end of the course, you should be able to:

* Build dashboards and alerts that expose application and infrastructure problems.

* Query logs and trace operational changes through CloudTrail.

* Detect configuration drift and compliance violations.

* Manage EC2 instances using Systems Manager and secure operational workflows.

* Respond to AWS Health events and automate event notifications.

* Track AWS spending and configure budget alerts.

* Use Pulumi to provision and maintain repeatable operational infrastructure.

* Troubleshoot an AWS workload systematically, from detection through recovery and root-cause analysis.

Implementation note: Some AWS services have account-, Region-, or feature-specific requirements. In particular, AWS Config recording, CloudTrail data events, detailed CloudWatch metrics, and Systems Manager integrations can incur charges. The labs should use narrowly scoped resources, explicit retention settings, and cleanup procedures to keep costs under control.
