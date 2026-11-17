### AWS Lambda — Complete Course Outline

8 modules · Beginner to Advanced · Production-focused · Pulumi-first infrastructure automation

This course is designed to take you from Lambda fundamentals to designing, deploying, securing, and operating production-grade serverless applications on AWS.

The course emphasizes practical architecture, Python development, AWS integrations, infrastructure as code with Pulumi (Python), and automation using AWS CLI and Bash.

### Module 1 — AWS Lambda Fundamentals and Architecture

* Serverless computing concepts and architecture.

* AWS Lambda architecture and core components.

* Lambda functions, execution environments, and invocation models.

* Supported runtimes and runtime lifecycle.

* Lambda execution model and function lifecycle.

* Event-driven computing fundamentals.

* Synchronous, asynchronous, and polling-based invocation.

* Lambda invocation types and execution flow.

* Lambda quotas, limits, and regional availability.

* Lambda pricing model and cost fundamentals.

* Comparing Lambda with EC2, ECS Fargate, and EKS.

* Common Lambda use cases and architectural patterns.

### Module 2 — Lambda Functions, Python Development, and Configuration

* Lambda function structure and programming model.

* Python handlers and event objects.

* Context object and execution metadata.

* Request-response processing.

* Environment variables and configuration management.

* Function memory, timeout, and ephemeral storage.

* Lambda deployment packages and ZIP archives.

* Python dependencies and package management.

* Lambda Layers and dependency reuse.

* Custom runtimes and runtime API fundamentals.

* Container image-based Lambda functions.

* Lambda extensions and execution environment integration.

* Logging and structured application output.

* Initialization and execution phases.

### Module 3 — Lambda Security, IAM, and VPC Networking

* Lambda security architecture and shared responsibility.

* Lambda execution roles and IAM policies.

* Resource-based policies and function permissions.

* Least-privilege access and permission boundaries.

* Lambda access to S3, DynamoDB, SQS, SNS, and other AWS services.

* AWS KMS integration and environment variable encryption.

* Secrets Manager and Systems Manager Parameter Store integration.

* VPC networking fundamentals for Lambda.

* Lambda VPC configuration and subnet selection.

* Security groups and network access.

* Accessing private resources inside a VPC.

* NAT gateways and internet connectivity.

* VPC endpoints and private AWS service access.

* Lambda networking considerations and connection management.

### Module 4 — Lambda Scaling, Concurrency, Performance, and Optimization

* Lambda scaling architecture.

* Execution environment reuse.

* Concurrent executions and concurrency fundamentals.

* Account-level and function-level concurrency limits.

* Reserved concurrency and its use cases.

* Provisioned concurrency and initialization optimization.

* Cold starts and warm execution environments.

* SnapStart and supported runtime considerations.

* Memory allocation and CPU performance.

* Timeout configuration and execution optimization.

* Ephemeral storage optimization.

* Connection reuse and database connection management.

* Lambda performance tuning.

* Cost optimization and concurrency management.

* Throttling, backpressure, and scaling behavior.

### Module 5 — Lambda Event Sources, Triggers, and Event-Driven Integrations

* Lambda event source architecture.

* Direct service integrations and event notifications.

* S3 event notifications and object processing.

* DynamoDB Streams integration.

* Kinesis Data Streams integration.

* Amazon SQS event source mappings.

* Amazon SNS integration.

* Amazon EventBridge rules and event buses.

* API Gateway and Lambda integration.

* Application Load Balancer and Lambda targets.

* Event filtering and event source mapping configuration.

* Batch processing and partial batch failure handling.

* Event-driven processing patterns.

* Event ordering, duplicate events, and idempotency.

* EventBridge Scheduler and scheduled Lambda execution.

### Module 6 — Lambda Invocation, Asynchronous Processing, and Reliability

* Synchronous invocation and request-response behavior.

* Asynchronous invocation and event queues.

* Poll-based invocation and event source mappings.

* Invocation retries and error handling.

* Asynchronous invocation destinations.

* Dead-letter queues and failure destinations.

* Maximum event age and retry attempts.

* SQS visibility timeout and Lambda timeout relationships.

* FIFO processing and ordering considerations.

* Idempotency and duplicate event prevention.

* Partial batch responses and failure isolation.

* Distributed processing and fanout architectures.

* Lambda integration with Step Functions.

* Durable execution and workflow orchestration concepts.

* Reliability, fault tolerance, and recovery strategies.

### Module 7 — Lambda Deployment, Versioning, and CI/CD with Pulumi

* Lambda deployment strategies.

* AWS CLI and Bash-based function management.

* Deployment packages and container image deployments.

* Function versions and immutable deployments.

* Aliases and environment promotion.

* Weighted alias routing and gradual deployments.

* Blue/green and canary deployment strategies.

* Lambda function URLs and their use cases.

* API Gateway integration and deployment considerations.

* Infrastructure as Code with Pulumi Python.

* Pulumi projects, stacks, configuration, and secrets.

* Managing Lambda functions, IAM roles, and permissions with Pulumi.

* Managing environment variables and Lambda layers.

* Managing event source mappings and integrations.

* Pulumi state management, imports, previews, and updates.

* CI/CD automation using GitHub Actions.

* Deployment rollback and release management.

### Module 8 — Lambda Monitoring, Troubleshooting, and Production Architectures

* CloudWatch Logs and Lambda logging.

* CloudWatch metrics and monitoring.

* Lambda metrics: invocations, errors, duration, throttles, and concurrency.

* CloudWatch alarms and dashboards.

* AWS X-Ray distributed tracing.

* Lambda Insights and performance monitoring.

* CloudTrail auditing and API activity.

* Troubleshooting invocation failures and permission errors.

* Diagnosing cold starts, throttling, and timeouts.

* Monitoring asynchronous processing failures.

* Observability for event-driven applications.

* Cost monitoring and optimization.

* Multi-account Lambda deployment considerations.

* Multi-region serverless architectures.

* Lambda integration with API Gateway, SQS, SNS, EventBridge, and Step Functions.

* Production architecture patterns and operational best practices.

### Course progression

| Module | Main focus                                 | Level        |
| ------ | ------------------------------------------ | ------------ |
| 1      | Fundamentals and architecture              | Beginner     |
| 2      | Python development and configuration       | Beginner     |
| 3      | Security and networking                    | Intermediate |
| 4      | Scaling and performance                    | Intermediate |
| 5      | Event sources and integrations             | Intermediate |
| 6      | Reliability and asynchronous processing    | Advanced     |
| 7      | Deployment and Pulumi automation           | Advanced     |
| 8      | Observability and production architectures | Advanced     |

### Recommended technology stack

Throughout the course, I recommend using:

| Area                     | Technology         |
| ------------------------ | ------------------ |
| Programming              | Python             |
| Infrastructure as Code   | Pulumi (Python)    |
| Command-line automation  | AWS CLI + Bash     |
| Application dependencies | uv                 |
| Container packaging      | Docker             |
| CI/CD                    | GitHub Actions     |
| Monitoring               | CloudWatch + X-Ray |
| API integration          | API Gateway        |
| Messaging                | SQS + SNS          |
| Event routing            | EventBridge        |
| Workflow orchestration   | Step Functions     |

My recommendation: Keep this as an eight-module course. Lambda deserves more depth than SQS or SNS because it is both a compute service and a central integration point for many AWS services. The final goal should be to understand not just how to write Lambda functions, but how to operate reliable, secure, scalable serverless applications in production.
