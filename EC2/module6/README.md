### Module 6 — AWS Lambda

Phase 4: Compute · Serverless computing and event-driven execution

In this module, you'll learn how to run Python code on AWS without managing servers, configure event-driven workloads, secure functions with IAM, and deploy a working HTTP endpoint using Pulumi with Python.

We'll use a small FastAPI-style application function as our practical example, building on the AWS and networking concepts from the earlier modules.

### Learning objectives

By the end of this module, you should be able to:

* Explain Lambda's execution model and when serverless is appropriate.

* Create functions, configure runtimes and handlers, and package dependencies.

* Configure memory, timeouts, concurrency, and execution behavior.

* Understand synchronous and asynchronous invocation.

* Configure event sources, retries, destinations, and dead-letter queues.

* Secure Lambda with execution roles and understand VPC networking.

* Diagnose cold starts, inspect CloudWatch logs, and optimize costs.

* Provision and deploy a Lambda function and HTTP endpoint with Pulumi.

### 1\. What is AWS Lambda?

AWS Lambda is a serverless compute service that runs your code in response to requests or events. AWS manages the underlying servers, operating system maintenance, and much of the infrastructure scaling.

Client or event source

HTTP request, S3 event, queue message, or schedule

AWS Lambda

Invokes your function in a managed execution environment

Other AWS services

S3, DynamoDB, SQS, or another API

For example, imagine an application that generates a thumbnail whenever a user uploads an image. Instead of keeping an EC2 server running and waiting for uploads, you can configure an S3 event to invoke a Lambda function only when an object is created.

Lambda is particularly useful for:

* HTTP APIs and lightweight backend operations.

* Processing uploaded files.

* Scheduled maintenance jobs.

* Queue and event processing.

* Automation and integration between AWS services.

Lambda isn't automatically the best option for every workload. Long-running processes, specialized operating-system requirements, predictable high-throughput workloads, and applications requiring extensive runtime control may be better suited to EC2 or containers.

### 2\. Functions, runtimes, handlers, and packages

A Lambda function is the unit of code AWS invokes. Its configuration identifies the runtime, entry point, permissions, and execution settings.

### Runtime

The runtime provides the language environment in which your function executes. For this module, we'll use a supported Python runtime compatible with your installed Pulumi AWS provider and AWS Lambda's current runtime availability.

### Handler

The handler is the function Lambda calls when an invocation arrives.

For a Python file named `app.py` containing a function named `handler`, the handler setting is:

`app.handler`

This means:

* `app` — the Python module, usually `app.py`.

* `handler` — the callable inside that module.

A minimal function looks like this:

```python

import json

def handler(event, context):
    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Hello from AWS Lambda!",
            "request_id": context.aws_request_id
        })
    }
```

The `event` argument contains invocation data. Its structure depends on the trigger: an HTTP request, S3 notification, queue message, or another event source.

The `context` argument provides invocation metadata, including the request ID and remaining execution time.

Notice that the function returns a response object, but it doesn't start a web server or listen on a TCP port. The invoking service determines how the response is interpreted.

### Deployment packages

Lambda needs your code and any required dependencies. Depending on the application, you can deploy:

* A ZIP archive containing Python source and dependencies.

* A container image stored in Amazon ECR.

For this module's first lab, a ZIP package is sufficient. Container-image deployments are useful when dependencies or packaging requirements make a ZIP less convenient.

### 3\. Execution settings and scaling

Lambda automatically creates and reuses execution environments as needed. Each environment can handle invocations according to Lambda's execution model, and additional environments may be created to handle concurrent requests.

Important settings include:

| Setting                 | What it controls                                                                |
| ----------------------- | ------------------------------------------------------------------------------- |
| Memory                  | Memory allocated to the function; CPU allocation also increases with memory.    |
| Timeout                 | Maximum duration allowed for a single invocation.                               |
| Concurrency             | Number of invocations executing simultaneously.                                 |
| Ephemeral storage       | Temporary /tmp storage available to the function.                               |
| Environment variables   | Configuration values made available to your code.                               |
| Reserved concurrency    | Capacity reserved for a function and a limit on its concurrent executions.      |
| Provisioned concurrency | Execution environments initialized in advance to reduce initialization latency. |

### Example: memory and timeout

Suppose a function processes uploaded images. Increasing its memory can provide more CPU resources and reduce processing time. However, more memory also changes the price per unit of execution time.

The best configuration depends on the workload, not simply on choosing the smallest possible value.

A sensible tuning process is:

* Establish a baseline with representative requests.

* Measure duration, memory use, errors, and concurrency.

* Test alternative memory settings.

* Review latency and cost together.

* Configure a timeout that allows legitimate work without letting stuck invocations run indefinitely.

Important: Lambda has a maximum execution duration of 15 minutes per invocation. Work that exceeds that limit needs a different execution model or must be divided into smaller tasks.

### 4\. Synchronous versus asynchronous invocation

Lambda supports different invocation patterns, and they affect how results and failures are handled.

### Synchronous invocation

Client

Lambda

Response

The caller waits for the invocation result. Common for API requests and direct SDK calls.

### Asynchronous invocation

Event source

Event queue

Lambda

The initial caller doesn't wait for the function's final result. Lambda manages delivery and retries for eligible asynchronous invocations.

A third important pattern is poll-based event source mapping. Lambda polls supported event sources such as SQS and invokes your function with batches of records. Retry and checkpoint behavior depends on the event source.

### Failure handling

* Asynchronous invocations can be retried after function errors, subject to the configured retry policy.

* An asynchronous invocation destination can capture invocation outcomes and route them to another service.

* A dead-letter queue can retain failed asynchronous events for later investigation.

* SQS event source mappings use queue visibility timeouts, redelivery, and redrive policies; these differ from Lambda's asynchronous retry mechanism.

Design handlers to tolerate duplicate processing. Retries and redelivery mean you should not assume every event will be processed exactly once.

For example, if a payment event is processed twice, your application should use an idempotency mechanism to prevent duplicate charges.

### 5\. IAM execution roles and VPC networking

Every Lambda function should have an execution role that grants only the permissions it needs.

### How Lambda permissions work

Execution role

Defines what the running function can do, such as writing logs or reading specific S3 objects.

Resource-based policy

Can authorize a service or account to invoke the function, where required.

VPC configuration

Controls network connectivity when the function needs access to private resources such as an RDS database.

### Lambda in a VPC

A Lambda function doesn't need to be attached to your VPC simply because it accesses AWS services. Many services can be accessed through their APIs without placing the function in a VPC.

Configure VPC access when the function needs to reach private resources, such as:

* An RDS database in private subnets.

* An internal service reachable through your VPC.

* A private endpoint or other VPC-connected resource.

When configuring VPC access, understand these distinctions:

* Private subnet: Doesn't inherently provide internet access.

* NAT Gateway: Can provide outbound internet connectivity, with associated costs.

* VPC endpoint: Can provide private connectivity to supported AWS services.

* Security groups: Control network traffic to and from relevant network interfaces and resources.

A VPC-connected Lambda function does not automatically receive internet access just because it is configured with public subnet IDs. Its routing and networking must be designed correctly.

### 6\. Cold starts, observability, and cost

### Cold starts

A cold start occurs when Lambda needs to initialize a new execution environment. Initialization may include starting the runtime, loading dependencies, and executing initialization code.

To reduce unnecessary initialization latency:

* Keep deployment packages and dependencies reasonably small.

* Avoid expensive initialization when it can be deferred.

* Reuse clients and connections carefully across warm invocations.

* Consider provisioned concurrency for workloads with strict latency requirements.

Warm environments may be reused, but you must not depend on that reuse for application correctness or persistent state.

### CloudWatch observability

Lambda integrates with Amazon CloudWatch.

| Signal                | What to investigate                                |
| --------------------- | -------------------------------------------------- |
| Invocations           | How often the function runs                        |
| Duration              | How long executions take                           |
| Errors                | Failed invocations                                 |
| Throttles             | Invocations rejected because of concurrency limits |
| ConcurrentExecutions  | Simultaneous execution demand                      |
| Init Duration in logs | Initialization overhead when reported              |

By default, your function needs appropriate CloudWatch Logs permissions to create log streams and publish log events. The common starting point is the AWS-managed `AWSLambdaBasicExecutionRole` policy.

### Cost optimization

Lambda pricing generally depends on requests and execution duration, with memory affecting the compute charge. Additional charges may apply for features such as provisioned concurrency, networking resources, and API Gateway.

For cost-conscious labs:

* Use modest memory and timeout values appropriate for the function.

* Avoid unnecessary NAT Gateways for simple public HTTP-triggered functions.

* Set budgets or billing alerts.

* Delete lab infrastructure when finished.

* Remember that destroying a Lambda function does not necessarily remove every related resource if it was created separately.

### 7\. Hands-on lab: Deploy Lambda with Pulumi

Goal: Create a Python Lambda function, expose it through an API Gateway HTTP API, invoke it over HTTP, and inspect its CloudWatch logs.

We'll use Amazon API Gateway rather than a Lambda Function URL so that you can also learn the common API Gateway integration pattern.

### Architecture

HTTP client

curl or browser

API Gateway HTTP API

GET / → Lambda proxy integration

AWS Lambda

Python handler + execution role

Amazon CloudWatch Logs

Execution output and debugging

### Step 1 — Check your prerequisites

You should have:

* An AWS account and a configured AWS CLI profile.

* Python and a working Pulumi CLI installation.

* AWS credentials that allow you to create the required IAM, Lambda, and API Gateway resources.

* A designated AWS Region for the lab.

IAM role creation and passing the role to Lambda require suitable IAM permissions. If your account uses an organizational permission boundary or service control policy, that may also restrict deployment.

Verify your setup:

```bash
aws sts get-caller-identity
pulumi version
python --version
```

### Step 2 — Create a Pulumi Python project

```bash
mkdir lambda-http-lab
cd lambda-http-lab

pulumi new aws-python
```

Follow the prompts to select a project name, stack, and AWS Region.

Install the additional dependencies:

```bash
pip install pulumi-aws pulumi-archive
```

If the generated project already includes `pulumi-aws`, you don't need to install it twice.

### Step 3 — Implement the Lambda function

Create `app.py`:

```python

import json

def handler(event, context):
    response = {
        "message": "Hello from AWS Lambda!",
        "request_id": context.aws_request_id,
        "method": event.get("requestContext", {})
                      .get("http", {})
                      .get("method", "unknown"),
        "path": event.get("rawPath", "/"),
    }

    print(json.dumps({
        "level": "INFO",
        "message": "Request processed",
        "request_id": context.aws_request_id,
    }))

    return {
        "statusCode": 200,
        "headers": {
            "content-type": "application/json"
        },
        "body": json.dumps(response),
    }
```

This function accepts an API Gateway HTTP API payload, logs a structured message, and returns JSON.

The `request_id` helps correlate an HTTP request with the corresponding Lambda execution log.

### Step 4 — Define the infrastructure using Pulumi

Replace the contents of `__main__.py` with the following:

```python

import pulumi
import pulumi_aws as aws

# 1. Create the Lambda execution role.
assume_role_policy = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            effect="Allow",
            principals=[
                aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Service",
                    identifiers=["lambda.amazonaws.com"],
                )
            ],
            actions=["sts:AssumeRole"],
        )
    ]
)

role = aws.iam.Role(
    "lambda-execution-role",
    assume_role_policy=assume_role_policy.json,
)

# 2. Allow Lambda to publish logs to CloudWatch.
logging_policy = aws.iam.RolePolicyAttachment(
    "lambda-basic-logging",
    role=role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AWSLambdaBasicExecutionRole"
    ),
)

# 3. Create the Lambda function.
function = aws.lambda_.Function(
    "hello-lambda",
    runtime="python3.12",
    handler="app.handler",
    role=role.arn,
    code=pulumi.AssetArchive({
        "app.py": pulumi.FileAsset("app.py"),
    }),
    memory_size=256,
    timeout=10,
    opts=pulumi.ResourceOptions(
        depends_on=[logging_policy],
    ),
)

# 4. Create an API Gateway HTTP API.
api = aws.apigatewayv2.Api(
    "lambda-http-api",
    protocol_type="HTTP",
)

integration = aws.apigatewayv2.Integration(
    "lambda-integration",
    api_id=api.id,
    integration_type="AWS_PROXY",
    integration_method="POST",
    integration_uri=function.invoke_arn,
    payload_format_version="2.0",
)

route = aws.apigatewayv2.Route(
    "get-root",
    api_id=api.id,
    route_key="GET /",
    target=pulumi.Output.concat(
        "integrations/",
        integration.id,
    ),
)

stage = aws.apigatewayv2.Stage(
    "default-stage",
    api_id=api.id,
    name="$default",
    auto_deploy=True,
)

# 5. Allow API Gateway to invoke this function.
invoke_permission = aws.lambda_.Permission(
    "allow-api-gateway",
    action="lambda:InvokeFunction",
    function=function.name,
    principal="apigateway.amazonaws.com",
    source_arn=pulumi.Output.concat(
        api.execution_arn,
        "/*/*",
    ),
)

# Export useful values.
pulumi.export("function_name", function.name)
pulumi.export("api_url", api.api_endpoint)
pulumi.export("log_group", pulumi.Output.concat(
    "/aws/lambda/",
    function.name,
))
```

What the infrastructure code creates:

* An IAM role trusted by the Lambda service.

* An attached policy for basic CloudWatch logging.

* A Lambda function packaged from `app.py`.

* An HTTP API with a `GET /` route and proxy integration.

* A default API stage with automatic deployment.

* Permission for API Gateway to invoke the function.

* Stack outputs for the API endpoint, function name, and log group.

The `GET /` route is the only route created in this lab. The API is intentionally public and unauthenticated, so don't use it to expose sensitive operations or data.

### Step 5 — Preview and deploy

First preview the changes:

```bash
pulumi preview
```

Review the planned resources. If they look correct, deploy:

```bash
pulumi up
```

Approve the update when prompted.

Pulumi should display outputs including `api_url`, `function_name`, and `log_group`.

### Step 6 — Invoke the HTTP endpoint

Get the endpoint URL:

```bash
pulumi stack output api_url
```

Invoke it:

```bash
curl "$(pulumi stack output api_url)/"
```

You should receive a JSON response resembling:

```json
{
  "message": "Hello from AWS Lambda!",
  "request_id": "example-request-id",
  "method": "GET",
  "path": "/"
}
```

The request ID shown here will differ on every invocation. The example above illustrates the response structure, not a real execution result.

If the request fails, check the API route, Lambda integration, invocation permission, and CloudWatch logs.

### Step 7 — Inspect CloudWatch logs

Use the function's log group output:

```bash
aws logs tail "$(pulumi stack output log_group)" \
  --since 10m \
  --follow
```

Keep this command running in one terminal and invoke the endpoint from another.

You should see the structured `Request processed` message and Lambda's runtime log records.

The first request may take longer because the execution environment needs initialization. Subsequent requests may reuse a warm environment, although this isn't guaranteed.

### Step 8 — Explore failure scenarios

Once the basic lab works, experiment with these scenarios one at a time.

### Practical exercises

0 of 5

1. Change the memory allocation

Increase memory_size from 256 to 512 MB, deploy again, and compare execution duration and billed duration.

2. Introduce a controlled error

Temporarily raise an exception in the handler, deploy, invoke the endpoint, and inspect the error logs and HTTP response.

3. Explore timeout behavior

Temporarily set a very short timeout and add a sleep in the handler. Observe the timeout error in CloudWatch.

4. Inspect permissions

Review the execution role and its attached logging policy. Identify which permissions would be needed to read a specific S3 bucket.

5. Compare cold and warm invocations

Send several requests and compare observed latency. Remember that repeated requests alone do not guarantee a controlled cold-start experiment.

### 8\. Cleanup

When you're finished, remove the lab resources:

```bash
pulumi destroy
```

Review and approve the deletion. Then verify that the stack no longer has its deployed resources.

```bash
pulumi stack
pulumi stack output
```

Depending on the CLI version and stack state, outputs may no longer be available after destruction. You can remove the local stack when you no longer need its state:

```bash
pulumi stack rm
```

Only remove the stack after verifying that its infrastructure has been destroyed and that you no longer need the stack's state. The AWS account, CLI profile, and Pulumi project files are not deleted by `pulumi destroy`.

### 9\. Knowledge check

Try answering these without looking back at the lesson.

1. What does the Lambda handler setting \`app.handler\` identify?

An AWS IAM role

A Python module and callable

A CloudWatch log group

An API Gateway stage

2. Which setting increases Lambda's available CPU allocation as it increases?

Timeout

Environment variable count

Memory allocation

API Gateway route count

3. What is the purpose of a Lambda execution role?

To define permissions the function can exercise

To choose the HTTP route

To store the deployment ZIP

To configure DNS records

4. Does placing Lambda in a public subnet automatically give it internet access?

Yes, always

Only when memory is at least 512 MB

No; routing and connectivity must be configured

Only when the handler returns HTTP 200

5. What is a good reason to use an idempotent event handler?

To eliminate all cold starts

To prevent duplicate side effects when events are retried

To avoid creating an execution role

To make every function run for 15 minutes

Check answers

### Module 6 completion checklist

* Explain Lambda's runtime, handler, package, and execution environment.

* Distinguish synchronous, asynchronous, and event-source-mapping invocation.

* Explain IAM execution roles and Lambda VPC connectivity.

* Understand retries, idempotency, cold starts, and CloudWatch metrics.

* Deploy and invoke the Lambda HTTP API using Pulumi.

* Inspect execution logs and destroy the lab resources safely.

Once you've completed this module, the next step in the Compute course is Module 7 — Amazon ECR and ECS Fundamentals, where you'll package the same kind of Python application as a container and run it on AWS.
