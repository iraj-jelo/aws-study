### Module 1 — AWS Lambda Fundamentals and Architecture

The purpose of this module is to build a solid understanding of AWS Lambda before moving into Python development, IAM, networking, scaling, event integrations, and production deployments.

By the end of this module, you should understand how Lambda works internally, how AWS executes your code, how applications invoke functions, and when Lambda is a better choice than traditional compute services such as EC2, ECS, and EKS.

### 1\. Serverless Computing Concepts and Architecture

### 1.1 What is serverless computing?

Serverless computing is a cloud computing model in which the cloud provider manages much of the underlying infrastructure, allowing developers to focus on application code rather than server provisioning and maintenance.

The term serverless does not mean that servers do not exist. Servers are still involved, but their provisioning, maintenance, scaling, and infrastructure management are largely abstracted away from the application developer.

In traditional application hosting, you typically manage:

* Virtual machines or physical servers.

* Operating systems and system updates.

* Runtime installation and configuration.

* Capacity planning.

* Application deployment.

* Scaling and availability.

* Infrastructure monitoring.

With serverless computing, AWS takes responsibility for much of the underlying infrastructure.

For example, instead of provisioning an EC2 instance, installing Python, configuring a web server, and deploying an application, you can upload a Python function to Lambda and configure an event source that invokes it.

AWS manages the compute infrastructure required to execute that function.

### 1.2 Characteristics of serverless architecture

Serverless architectures commonly have the following characteristics:

1\. No server provisioning

You do not need to create or maintain virtual machines to execute your application code.

2\. Automatic scaling

Lambda automatically scales function execution according to incoming invocation demand, subject to concurrency quotas and available capacity.

3\. Pay-per-use pricing

You generally pay for the number of requests and the compute duration consumed by your functions, rather than paying for an application server that remains running continuously.

4\. Event-driven execution

Functions execute in response to events such as HTTP requests, uploaded files, database changes, scheduled events, or messages.

5\. Managed infrastructure

AWS manages the underlying compute infrastructure, operating system maintenance, and execution environment provisioning.

6\. Independent deployment units

Individual Lambda functions can be deployed and scaled independently, making them useful for modular application architectures.

### 1.3 Serverless architecture example

Consider an application that allows users to upload images.

A traditional architecture might look like this:

Traditional application architecture

Users

Load Balancer

EC2 Application Servers

Application runtime, web server, scaling, OS management

Database and Object Storage

A serverless version could look like this:

Serverless image-processing architecture

Users

Amazon API Gateway

HTTP API endpoint

AWS Lambda

Image upload authorization and application logic

Amazon S3

Image storage

S3 Event Notification

AWS Lambda

Image resizing and thumbnail generation

Amazon S3

Processed images

In this architecture:

* A user requests permission to upload an image.

* API Gateway forwards the HTTP request to Lambda.

* Lambda generates an authorized upload response, such as a presigned S3 URL.

* The user uploads the image directly to S3.

* S3 generates an event notification.

* A second Lambda function processes the uploaded image.

* The processed image is stored in S3.

Notice that the application does not need continuously running EC2 instances to process image uploads.

### 1.4 Serverless does not mean completely stateless

Lambda functions are generally designed to be stateless, meaning an invocation should not depend on data stored only in the memory of a previous invocation.

However, AWS may reuse an execution environment across multiple invocations.

This means that global variables and initialized objects can sometimes survive between invocations.

For example, a database connection initialized outside the handler may be reused:

```python
import json

# Initialized when the execution environment starts
database_client = create_database_client()

def lambda_handler(event, context):
    result = database_client.query()

    return {
        "statusCode": 200,
        "body": json.dumps(result)
    }
```

This can improve performance by avoiding repeated initialization.

However, you must never assume that a future invocation will execute in the same environment.

For persistent application state, use external services such as:

* Amazon DynamoDB.

* Amazon RDS.

* Amazon S3.

* Amazon ElastiCache.

The key architectural principle is to keep durable state outside the Lambda execution environment.

### 2\. AWS Lambda Architecture and Core Components

### 2.1 What is AWS Lambda?

AWS Lambda is a serverless compute service that allows you to run application code in response to events without managing the underlying servers.

You provide your code, configure the execution environment, and define how the function should be invoked.

AWS manages the infrastructure required to execute your code.

Lambda supports several programming languages, including Python, Node.js, Java, .NET, Ruby, and Go, along with custom runtimes.

### 2.2 Core Lambda components

A Lambda-based application involves several important components.

| Component              | Responsibility                                                     |
| ---------------------- | ------------------------------------------------------------------ |
| Lambda function        | Contains the application code                                      |
| Handler                | Entry point for function execution                                 |
| Runtime                | Executes the application code                                      |
| Execution environment  | Provides the isolated environment for execution                    |
| Event                  | Contains invocation input                                          |
| Context object         | Provides invocation and function metadata                          |
| Execution role         | Defines AWS permissions for the function                           |
| Invocation mechanism   | Determines how the function is triggered                           |
| Function configuration | Defines memory, timeout, environment variables, and other settings |

Let's examine the most important components.

### 2.3 Lambda function

A Lambda function is the basic deployment and execution unit.

It consists of application code and its associated configuration.

A function has properties such as:

* Function name.

* Runtime.

* Handler.

* Memory allocation.

* Timeout.

* Execution role.

* Environment variables.

* Architecture.

* Deployment package.

For example, a function named `image-processor` might receive an S3 event and generate a thumbnail.

### 2.4 Handler

The handler is the entry point Lambda calls when executing your function.

For Python, a handler commonly has this structure:

```python
def lambda_handler(event, context):
    return {
        "message": "Hello from AWS Lambda!"
    }
```

Here:

* `lambda_handler` is the handler function.

* `event` contains the input data.

* `context` contains invocation metadata.

The handler configuration identifies the Python module and function name.

For example:

```text
app.lambda_handler
```

This means:

* `app` is the Python file named `app.py`.

* `lambda_handler` is the function inside that file.

### 2.5 Runtime

The runtime provides the execution environment required to execute your application code.

For Python, the runtime handles communication between the Lambda service and your Python handler.

It receives invocation information, invokes your handler, and communicates the execution result back to Lambda.

AWS provides managed runtimes, while custom runtimes allow you to implement your own runtime interface.

### 2.6 Execution role

Every Lambda function executes with an IAM execution role.

This role defines which AWS resources the function can access.

For example, a Lambda function that reads objects from S3 needs appropriate S3 permissions.

A simplified IAM policy might contain:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-images-bucket/*"
    }
  ]
}
```

The function assumes its execution role when it executes.

This is different from the permissions used by a developer to deploy the function.

### 2.7 Event and context

The event is the input supplied to a Lambda invocation.

For example, an API Gateway request may contain:

```json
{
  "httpMethod": "GET",
  "path": "/users",
  "queryStringParameters": {
    "status": "active"
  }
}
```

The exact event structure depends on the invoking service.

The context object contains runtime metadata, such as:

* Function name.

* Function version.

* AWS request ID.

* Memory limit.

* Remaining execution time.

* Log group and log stream information.

For example:

```python
def lambda_handler(event, context):

    print("Function:", context.function_name)
    print("Request ID:", context.aws_request_id)
    print("Remaining time:", context.get_remaining_time_in_millis())

    return {
        "statusCode": 200,
        "body": "Success"
    }
```

These values are particularly useful for troubleshooting and observability.

### 3\. Lambda Functions, Execution Environments, and Invocation Models

These three concepts are fundamental to understanding how Lambda works.

### 3.1 What is an execution environment?

An execution environment is an isolated compute environment that AWS Lambda creates to execute your function.

It provides the resources required to run your code, including:

* CPU capacity associated with allocated memory.

* Memory allocation.

* Operating system environment.

* Language runtime.

* Temporary filesystem.

* Environment variables.

* AWS credentials associated with the execution role.

When Lambda receives an invocation, it needs an available execution environment.

If one is available, Lambda can reuse it. Otherwise, Lambda creates a new one.

### 3.2 Execution environment lifecycle

A standard Lambda execution environment has three primary lifecycle phases:

### Lambda execution lifecycle

Phase 1

INIT — Initialization

AWS prepares the execution environment.

* Starts extensions.

* Initializes the runtime.

* Executes static initialization code.

* Loads application dependencies.

Phase 2

INVOKE — Function execution

Lambda invokes your handler.

* Receives the event.

* Executes application logic.

* Calls external services if needed.

* Returns a result or reports an error.

Phase 3

SHUTDOWN — Environment termination

AWS eventually terminates the execution environment.

* Extensions receive shutdown notifications where applicable.

* Runtime resources are cleaned up.

* Temporary environment state is discarded.

Important: Shutdown does not necessarily happen immediately after every invocation.

After an invocation finishes, Lambda can freeze the execution environment and reuse it for another invocation.

AWS eventually terminates environments for infrastructure management and maintenance, so you must never rely on an environment remaining alive.

AWS documents these lifecycle phases and the execution environment reuse behavior in its [execution environment lifecycle documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html?utm_source=chatgpt.com).

### 3.3 Cold starts and warm starts

One of the most important concepts in Lambda architecture is the difference between cold starts and warm starts.

Cold start

A cold start occurs when Lambda needs to initialize a new execution environment before executing your handler.

The process generally involves:

* Preparing the execution environment.

* Starting the runtime.

* Initializing extensions.

* Loading application dependencies.

* Running static initialization code.

* Executing the handler.

This introduces additional latency.

Warm start

A warm start occurs when Lambda reuses an existing execution environment.

The runtime and initialized objects may already be available, so Lambda can execute the handler without repeating the entire initialization process.

Cold start

Initialization required

Create environment → Initialize runtime → Execute handler

Warm start

Environment reused

Reuse environment → Execute handler

Cold starts are particularly important for applications that require very low response latency.

AWS provides two important mechanisms for addressing initialization latency:

* Provisioned Concurrency: Keeps a configured number of execution environments initialized and ready to handle requests.

* Lambda SnapStart: Creates snapshots of initialized execution environments for supported runtimes and configurations, reducing initialization overhead.

These mechanisms will be examined in detail in Module 4.

### 3.4 Execution environment reuse and global variables

Consider this Python example:

```python
import json
import boto3

# Executed during initialization
s3 = boto3.client("s3")

def lambda_handler(event, context):

    bucket = event["bucket"]
    key = event["key"]

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    content = response["Body"].read().decode("utf-8")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "content": content
        })
    }
```

Notice that the S3 client is initialized outside the handler.

This means:

* It is created during environment initialization.

* It can be reused across subsequent invocations in the same environment.

* It does not need to be recreated every time the handler executes.

This is an important optimization technique.

However, do not store user-specific information or sensitive invocation state in global variables because the same environment can serve multiple invocations over time.

### 3.5 Supported runtimes and runtime lifecycle

A runtime is responsible for communicating between the Lambda service and your application code.

For example, the Python runtime:

* Receives invocation information from Lambda.

* Makes the event available to your handler.

* Executes your Python function.

* Collects the result.

* Communicates the result or error back to Lambda.

AWS provides managed runtimes for several programming languages.

| Language | Example runtime identifier |
| -------- | -------------------------- |
| Python   | python3.14                 |
| Node.js  | nodejs24.x                 |
| Java     | java25                     |
| .NET     | dotnet10                   |
| Ruby     | ruby3.4                    |
| Go       | provided.al2023            |

These are examples of runtime identifiers, not a guarantee that every runtime is available in every Region or deployment configuration. Check the current AWS runtime documentation before choosing one.

There are three important runtime concepts.

Managed runtimes

AWS provides and maintains the language runtime.

You select the runtime identifier when creating or configuring your function.

Custom runtimes

You provide the runtime implementation using the Lambda Runtime API.

This is useful when you want to execute languages or runtime versions that are not available as AWS-managed runtimes.

Container image runtimes

You package your application and its runtime dependencies into a container image.

Lambda supports container images stored in Amazon ECR.

One important distinction: container image deployment does not mean that you manage a continuously running container as you would with ECS. Lambda still manages the execution environment and invocation lifecycle.

### 3.6 Runtime lifecycle and deprecation

AWS periodically releases new runtime versions and eventually deprecates older ones.

Runtime deprecation is important because older runtimes may no longer receive security updates or remain eligible for new deployments.

AWS generally provides a runtime deprecation schedule with stages such as:

* Runtime deprecation announcement.

* Deprecation date.

* Blocking creation of new functions using the runtime.

* Blocking updates to existing functions using the runtime.

You should monitor runtime lifecycle announcements and upgrade functions before the relevant deadlines.

Official reference: [AWS Lambda supported runtimes and deprecation policy](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html?utm_source=chatgpt.com).

### 4\. Lambda Execution Model and Function Lifecycle

It is important to distinguish the execution environment lifecycle from the execution model.

The execution environment describes where your code runs.

The execution model describes how Lambda receives an invocation and executes your application code.

### 4.1 How Lambda executes a function

The general execution sequence is:

1

Invocation request

An AWS service, application, or developer invokes the function.

2

Environment selection

Lambda selects an available execution environment or creates a new one.

3

Runtime processing

The runtime receives the event and prepares the handler invocation.

4

Handler execution

Your application code processes the event.

5

Execution result

Lambda returns the result or reports an error to the invoking mechanism.

6

Environment management

Lambda may freeze and reuse the environment or eventually terminate it.

### 4.2 Lambda programming model

The programming model defines how your code interacts with Lambda.

For Python, the handler is the central component.

```python
def lambda_handler(event, context):

    print("Received event:", event)

    name = event.get("name", "Guest")

    return {
        "statusCode": 200,
        "body": f"Hello, {name}!"
    }
```

The function receives two primary arguments:

Event

Contains input data.

Context

Contains information about the current invocation and function environment.

The function returns a value, raises an exception, or communicates through an integration-specific mechanism.

### 4.3 Invocation and execution are not the same thing

A Lambda invocation is a request to execute a function.

An execution is the actual processing of that request inside an execution environment.

For example, suppose an API receives 100 requests.

Lambda may need to create multiple execution environments to process them concurrently.

This means:

* 100 requests can result in 100 invocations.

* Multiple execution environments may be created.

* Each standard execution environment normally handles one invocation at a time.

* Each invocation executes the handler independently.

Lambda Managed Instances have a different concurrency model and are an advanced exception.

This distinction becomes especially important when studying concurrency and scaling in Module 4.

### 5\. Synchronous, Asynchronous, and Polling-Based Invocation

Lambda supports three major invocation patterns.

Understanding these patterns is essential because they determine how events are delivered, how errors are handled, and whether the invoking service waits for the result.

### 5.1 Synchronous invocation

In synchronous invocation, the caller sends a request to Lambda and waits for the function to finish.

The caller receives the function's response or an invocation error.

Synchronous invocation

Client / Application

Request

AWS Lambda

Executes handler

Response

Client / Application

Common examples:

* API Gateway invoking Lambda.

* An application invoking Lambda through the AWS SDK.

* A developer invoking Lambda using the AWS CLI.

Python example using Boto3:

```python
import boto3
import json

client = boto3.client("lambda")

response = client.invoke(
    FunctionName="my-function",
    InvocationType="RequestResponse",
    Payload=json.dumps({
        "name": "John"
    })
)

payload = json.loads(
    response["Payload"].read()
)

print(payload)
```

The important parameter is:

```python
InvocationType="RequestResponse"
```

It tells Lambda to use synchronous invocation.

The caller waits for the response.

### 5.2 Asynchronous invocation

In asynchronous invocation, the caller submits an event to Lambda without waiting for the function to finish processing it.

Lambda accepts the event and places it into an internal queue for processing.

Asynchronous invocation

Event producer

Submit event

Lambda asynchronous event queue

Process event

Lambda function

Processing result / failure destination

Examples include:

* S3 event notifications.

* EventBridge invoking Lambda.

* SNS invoking Lambda.

* Explicit asynchronous invocation through the AWS SDK.

Using Boto3:

```python
response = client.invoke(
    FunctionName="my-function",
    InvocationType="Event",
    Payload=json.dumps({
        "task": "process-image"
    })
)
```

The important parameter is:

```python
InvocationType="Event"
```

The caller receives an acceptance response rather than the function's eventual result.

Important: Acceptance does not mean that the function has successfully processed the event.

Asynchronous invocations have retry behavior and can eventually send failed events to configured destinations or dead-letter queues.

### 5.3 Polling-based invocation

Polling-based invocation is different from direct invocation.

In this model, Lambda uses an event source mapping to poll an external event source for available records.

When records are available, Lambda invokes the function with a batch of events.

Polling-based invocation

Event source

SQS / Kinesis / DynamoDB Streams

Poll for records

Lambda event source mapping

Polls and manages batches

Invoke with batch

Lambda function

Processes records

Examples:

* Amazon SQS.

* Amazon Kinesis Data Streams.

* Amazon DynamoDB Streams.

* Amazon MSK.

* Self-managed Kafka.

The event source mapping is responsible for polling the event source and invoking your function.

For example, with SQS:

* Messages arrive in an SQS queue.

* Lambda polls the queue.

* Lambda retrieves a batch of messages.

* Lambda invokes your function with that batch.

* Successfully processed messages are deleted according to the integration's processing behavior.

* Failed messages may become visible again after the visibility timeout.

This model is especially important for asynchronous application processing.

### 5.4 Comparing the three invocation models

| Characteristic              | Synchronous                 | Asynchronous                  | Polling-based                  |
| --------------------------- | --------------------------- | ----------------------------- | ------------------------------ |
| Caller waits for result     | Yes                         | No                            | No direct caller response      |
| Lambda internal async queue | No                          | Yes                           | No                             |
| Event source mapping        | Usually no                  | No                            | Yes                            |
| Batch processing            | Depends on integration      | Generally event-based         | Common                         |
| Typical integration         | API Gateway                 | S3, SNS, EventBridge          | SQS, Kinesis                   |
| Error handling              | Caller/integration behavior | Lambda retry and destinations | Event source-specific behavior |

One important distinction: polling-based invocation is not simply another name for asynchronous invocation. They have different delivery and retry mechanisms.

AWS documents these models in its [Lambda programming model documentation](https://docs.aws.amazon.com/lambda/latest/dg/concepts-how-lambda-runs-code.html?utm_source=chatgpt.com).

### 6\. Lambda Invocation Types and Execution Flow

In addition to the architectural invocation patterns, Lambda provides three invocation types through its Invoke API.

### 6.1 RequestResponse

This is the synchronous invocation type.

```python
response = client.invoke(
    FunctionName="my-function",
    InvocationType="RequestResponse",
    Payload=b'{"action": "create"}'
)
```

Characteristics:

* Waits for function execution.

* Returns the function response.

* Returns execution errors through the invocation response.

* Suitable for request-response applications.

### 6.2 Event

This is the asynchronous invocation type.

```python
response = client.invoke(
    FunctionName="my-function",
    InvocationType="Event",
    Payload=b'{"action": "process"}'
)
```

Characteristics:

* Accepts the event for asynchronous processing.

* Does not return the eventual handler result.

* Returns an acceptance status.

* Uses Lambda's asynchronous event processing mechanism.

### 6.3 DryRun

DryRun validates whether the caller has permission to invoke the function without actually executing it.

```python
response = client.invoke(
    FunctionName="my-function",
    InvocationType="DryRun"
)
```

This is useful for checking invocation permissions.

### 6.4 Invocation response status codes

| Invocation type | Typical HTTP status |
| --------------- | ------------------- |
| RequestResponse | 200                 |
| Event           | 202                 |
| DryRun          | 204                 |

Remember that a successful HTTP status does not always mean that your function's application logic succeeded.

For synchronous invocation, you should inspect the response payload and the `FunctionError` field when present.

For asynchronous invocation, a `202` means the event was accepted for processing, not that processing completed successfully.

### 7\. Lambda Quotas, Limits, and Regional Availability

AWS Lambda is a managed service, but it has quotas that affect application architecture.

Understanding these limits is important before designing production workloads.

### 7.1 Execution duration

For standard Lambda functions, the maximum execution timeout is:

### 900 seconds

15 minutes per invocation

You can configure the timeout according to your application requirements.

For example:

* API processing: 10–30 seconds.

* Image processing: 60–120 seconds.

* Background processing: Several minutes.

These are illustrative configurations, not AWS recommendations for every workload.

If your application regularly requires more than 15 minutes of continuous execution, consider ECS, AWS Batch, or another compute service.

AWS also offers newer specialized capabilities, including Durable Functions and Lambda Managed Instances, with different execution limits and models. These should not be confused with the standard Lambda function execution limit. AWS Lambda +1

### 7.2 Memory allocation

Lambda memory can be configured from:

### 128 MB – 10,240 MB

Memory allocation also affects the CPU capacity available to your function.

Increasing memory can improve performance for CPU-intensive workloads.

For example, an image-processing function might benefit from a larger memory allocation because it requires additional CPU capacity.

### 7.3 Temporary storage

Lambda provides temporary storage through the `/tmp` directory.

The configurable range is:

* Minimum: 512 MB.

* Maximum: 10,240 MB.

This storage is useful for:

* Downloading files.

* Processing images.

* Temporary application data.

* Caching files within an execution environment.

It is not durable storage. Use S3 or another persistent storage service when data must survive environment termination.

### 7.4 Deployment package limits

Lambda supports different deployment methods.

| Deployment type                       | Important limit                       |
| ------------------------------------- | ------------------------------------- |
| ZIP upload through Lambda API/console | 50 MB compressed                      |
| ZIP deployment package                | 250 MB uncompressed, including layers |
| Container image                       | 10 GB maximum uncompressed image size |

These limits affect how you package dependencies and application code.

For large Python applications, container image deployment may be more appropriate than a ZIP package.

### 7.5 Concurrency limits

Concurrency represents the number of function invocations executing simultaneously.

For example, if 100 requests arrive and Lambda needs 100 execution environments to process them concurrently, the function may require concurrency of 100.

AWS provides account-level concurrency quotas.

The commonly documented default regional account concurrency quota is 1,000, although new accounts may have reduced quotas and AWS can adjust limits.

Important concurrency concepts include:

* Account concurrency.

* Reserved concurrency.

* Provisioned concurrency.

* Function scaling limits.

* Throttling.

These topics are covered in depth in Module 4.

### 7.6 Regional availability

Lambda is available in multiple AWS Regions, but not every feature, runtime, integration, or capability is necessarily available everywhere.

For example, when designing a multi-region application, you must consider:

* Lambda availability in the target Region.

* Runtime availability.

* Regional concurrency quotas.

* Availability of integrated services.

* Cross-region data access.

* Regional pricing differences.

Always verify service availability before deploying production infrastructure.

Official reference: [AWS Lambda quotas and limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html?utm_source=chatgpt.com).

### 8\. Lambda Pricing Model and Cost Fundamentals

One of Lambda's biggest advantages is its pay-per-use pricing model.

Instead of paying for an EC2 instance that remains running continuously, you generally pay for Lambda requests and execution duration.

There are three important pricing concepts.

### 8.1 Request pricing

AWS charges based on the number of requests your Lambda functions receive.

For example:

* 1,000 requests.

* 100,000 requests.

* 1 million requests.

* 100 million requests.

The request count is an important component of Lambda cost.

### 8.2 Compute duration pricing

Lambda also charges based on the duration of function execution and allocated memory.

The fundamental pricing unit is GB-seconds.

The calculation is:

\\text{GB-seconds} =
\\text{Memory in GB} \\times \\text{Execution time in seconds}

For example, suppose a Lambda function has:

* Memory: 512 MB.

* Execution duration: 2 seconds.

* Number of invocations: 100,000.

First, convert memory:

512\\text{ MB}=0.5\\text{ GB}

Compute the GB-seconds per invocation:

0.5 \\times 2=1\\text{ GB-second}

Total compute consumption:

100,000 \\times 1=100,000\\text{ GB-seconds}

This represents the function's compute consumption before applying applicable pricing rates and discounts.

### 8.3 Free tier

AWS Lambda offers a free tier that has traditionally included:

* 1 million requests per month.

* 400,000 GB-seconds of compute per month.

However, eligibility and free-tier conditions can depend on the applicable AWS account and pricing program.

Always check the current pricing page before estimating costs.

### 8.4 Other potential costs

Lambda itself is not necessarily the largest cost in a serverless architecture.

You should also account for:

| Service        | Potential cost                      |
| -------------- | ----------------------------------- |
| API Gateway    | API requests                        |
| Amazon S3      | Storage and requests                |
| DynamoDB       | Reads, writes, and storage          |
| CloudWatch     | Logs, metrics, and ingestion        |
| NAT Gateway    | Hourly usage and data processing    |
| Step Functions | State transitions or workflow usage |
| Data transfer  | Applicable network transfer charges |

A particularly important example is NAT Gateway.

If your Lambda functions run inside a VPC and access the internet through a NAT Gateway, the NAT Gateway can introduce significant costs even when Lambda itself has relatively low usage.

### 8.5 Understanding Lambda cost optimization

Several factors influence Lambda cost:

* Memory allocation.

* Execution duration.

* Invocation frequency.

* Provisioned concurrency.

* Architecture selection.

* Network architecture.

* Logging volume.

* External service consumption.

Increasing memory can sometimes reduce overall cost if the function finishes considerably faster.

For example, a function using 1 GB of memory for 1 second might consume the same GB-seconds as a function using 512 MB for 2 seconds.

Therefore, the cheapest configuration is not necessarily the one with the smallest memory allocation.

### 9\. Comparing Lambda with EC2, ECS Fargate, and EKS

Lambda is not a replacement for every compute workload.

AWS offers several compute services, each designed for different operational and architectural requirements.

![What is AWS EC2? | Amazon Elastic Compute Cloud | ServerWatch](https://images.openai.com/static-rsc-4/HEG9qvmXzCnK6bVBAMEQK1sKYHZl1zVIwuVZXEclIvg7Ejv9Yh65B8SgIl5KV0W9zH594lF8djY5Sltp2WhgFkPiIWdTqRO61XfeYnMYmpL4Ljqbbgbx3-BT-40ni4ENon_NBYA6mfxHyfo3YKqnBldysv1JZ2Tv2Cbd2OLYYShJUSnpyYvRc2ueL_sXdbOG?purpose=fullsize)

Amazon EC2

Virtual machines that provide control over the operating system, installed software, and application runtime.

![Cloud Icons | Amazon Elastic Container Service](https://images.openai.com/static-rsc-4/vokfQfOrJI1LpdAPvgPr8viLfLi5de9oXRWoZpASJ6qBXG85ZzBYotqMKJrtsCUVb2PJSV3DWuVewBCpUVDFEPSEp6Zlt_tzEZ1Qp3Ucnm7PHwUR2DbH7AX0Jw49JxWCR0Mtu5dg0ilIT0QwnlRTm07sejg6J34lRsVWScw8Fa4bXAZdoA-KZhjpx5gd5h9r?purpose=fullsize)

Amazon ECS with Fargate

Managed container orchestration with serverless compute capacity. You manage containerized applications without managing the underlying servers when using Fargate.

![Free High-Quality Amazon EKS Logo for Creative Design](https://images.openai.com/static-rsc-4/SVtsovLA94iILI3LRToWR7ce7dCNJB3tpHjmM1ugK1IBizKzquMBDu3aDx1WZ-6wkpxG8iMiTwGCY2wp99JOuuNpKJsJa36TuEghTWhgD7Jlv8kc-hnKsdajaPs-ir9kKDnYXbjoMmcV9PbfuWyyEJ6NaRP2oS7wZE5WOaEKmaPiDXXHCaRJTg5ZD1munTFa?purpose=fullsize)

Amazon EKS

Managed Kubernetes control plane for running containerized workloads using Kubernetes.

![File:Amazon Lambda architecture logo.svg - Wikimedia Commons](https://images.openai.com/static-rsc-4/RcWQHLNUD9l50iP6YlMINmJt8TYqgZEqRN-8nINgp7zE21gqujKLD4ts65u2HFNyi_QpEyglpBk25Gx4fsJEyZgti-8hgekRtcZrr-73lpfJBhu7rhXILx9AwuuKlIuKa7bnn7zkgOcumIrCQnEBcgzxDbn_4e5w8TrUkaPItqvLvMlMIvJxXQApNN9Vq4uC?purpose=fullsize)

AWS Lambda

Event-driven compute for executing functions without managing application servers.

### 9.1 Comparison table

| Characteristic            | Lambda                              | EC2                       | ECS Fargate                | EKS                   |
| ------------------------- | ----------------------------------- | ------------------------- | -------------------------- | --------------------- |
| Compute model             | Functions                           | Virtual machines          | Containers                 | Kubernetes containers |
| Infrastructure management | AWS-managed                         | Customer-managed          | AWS-managed capacity       | Mixed                 |
| Scaling                   | Automatic                           | Configured                | Configured                 | Kubernetes-based      |
| Execution duration        | Up to 15 min for standard functions | Continuous                | Continuous                 | Continuous            |
| Runtime control           | Limited                             | Full                      | Container-level            | Container-level       |
| Persistent processes      | Not for standard functions          | Yes                       | Yes                        | Yes                   |
| Best suited for           | Event-driven tasks                  | General-purpose workloads | Containerized applications | Kubernetes workloads  |

### 9.2 When should you choose Lambda?

Lambda is particularly suitable when:

* Workloads are event-driven.

* Functions execute relatively quickly.

* Traffic is unpredictable.

* You want automatic scaling.

* You want to minimize infrastructure management.

* You have independent application functions.

* You want a pay-per-use compute model.

Example: A function that processes an image whenever a user uploads it to S3.

### 9.3 When should you choose EC2?

EC2 is more appropriate when:

* You require full operating system control.

* Applications need persistent processes.

* You need specialized system configurations.

* You run workloads that require continuous compute.

* You need specific software or system-level dependencies.

Example: A legacy application requiring custom operating system configuration and a continuously running application server.

### 9.4 When should you choose ECS Fargate?

ECS Fargate is appropriate when:

* You already package applications as Docker containers.

* Applications need to run continuously.

* You need long-running background workers.

* You want container-level control.

* You do not want to manage EC2 instances.

Example: A FastAPI application deployed as a continuously running container behind an Application Load Balancer.

### 9.5 When should you choose EKS?

EKS is appropriate when:

* You need Kubernetes orchestration.

* You operate multiple containerized microservices.

* You need Kubernetes-native deployment patterns.

* You use Kubernetes operators and ecosystem tools.

* You need advanced container orchestration capabilities.

Example: A microservices platform running multiple workloads with Kubernetes, Helm, Argo CD, and service-to-service networking.

### 9.6 A practical architecture decision

Consider an application with three components:

* A FastAPI backend.

* An image-processing worker.

* A scheduled cleanup process.

You could use:

| Component               | Recommended compute            |
| ----------------------- | ------------------------------ |
| FastAPI backend         | ECS Fargate                    |
| Image-processing worker | Lambda                         |
| Scheduled cleanup       | Lambda + EventBridge Scheduler |

This is a hybrid architecture.

You do not have to select one compute service for your entire application.

In fact, choosing different compute services for different workload characteristics is often a better architectural decision.

### 10\. Common AWS Lambda Use Cases

Lambda can support many different application architectures.

Let's examine some of the most common use cases.

### 10.1 API backends

Lambda can execute backend application logic when an HTTP request arrives through API Gateway.

![Build CRUD RESTful Microservices with AWS Lambda, API Gateway, DynamoDB with AWS SDK JS v3 | by Mehmet Ozkaya | AWS Lambda & Serverless — Developer Guide with Hands-on Labs | Medium](https://images.openai.com/static-rsc-4/Or66rsuskTH0YkZIUPc85wMainU_abZcmMUR6mqTuQU93Tp-glf0r_QuKG2mrLCqY5C2qt6jka4EoveQwiUi7M4FyhvgPVJ_2KN0DEoi45Eo7wzCRLoHMjrLFIM2Y3TL6c2uDNAFNB-leYCLI_lYGKVnL3DxSHe3zrPrYwv89qktLh1ByJ02pSaW9Obqy05w?purpose=fullsize)

Typical architecture:

```text
Client
  |
API Gateway
  |
Lambda
  |
DynamoDB
```

Typical use cases:

* REST APIs.

* Backend authentication.

* CRUD operations.

* Microservice endpoints.

* Lightweight application backends.

### 10.2 File processing

Lambda can process files when they are uploaded to S3.

![Building a Serverless Image Processing Pipeline with Terraform | by Kamalesh Govindarajan | Medium](https://images.openai.com/static-rsc-4/690tkxThoKFHgi0Y8d3jUY7LSIeZZ8RjPrCz_ttmAGWt9QdfYxPUrP8f8btZDFC6ZhjgcsCjxguo8rVTeuyjDvJglt2yUN-Hp_LyIGC-Hm3nbfjhZXiVgLhSaiERQmlR3Mccl_kfD-BA7bcaSviyLT4aAafmsBbAin1kMPTZ5lpaynBdhG3Eh_xQl-wHtKYE?purpose=fullsize)

Typical use cases:

* Image resizing.

* Thumbnail generation.

* PDF processing.

* File validation.

* Data transformation.

### 10.3 Message processing

Lambda can consume messages from SQS and SNS.

![Building Scalable Event-Driven Workflows Using AWS SQS and Lambda](https://images.openai.com/static-rsc-4/JiYVYmE6X1hFNHh2GtEuQrowOUKENL-GNxK3_0-XZCgNave_dTVrEv1_4eccZtTqED3Y1wDV7TSbFBo2CvnAcv9uaVDUCh8uNsaoE8bHGURfe2GUSRYuGuGkrscydsphzMVoOxwVs_WMxWigCTjgjyNkZG3nP_9HKG27WBDklNjXw1DPcQJawYlLgD0erQS2?purpose=fullsize)

Typical use cases:

* Background job processing.

* Notification processing.

* Order processing.

* Email workflows.

* Asynchronous application tasks.

### 10.4 Scheduled tasks

Lambda can execute functions on a schedule using EventBridge Scheduler.

![Amazon EventBridge Scheduler to AWS Lambda | Serverless Land](https://images.openai.com/static-rsc-4/q33WCjdt6grD5M7McbMbylDIuoCXPeRjEk4bqHafMliwqxDNaQZY5csv4ghyLK-p85ii57KEgZxlNJvJmjmqG6El-9uWKRN4_GxlsJhZNMkVWcS3mmpEWjJC4v-I_vc2MDDyGUuteyoDj4PxJsp-M0Oak40vXhp5bmgIFMHK5_FpqXdBnm8SogdCTuLSwkaC?purpose=fullsize)

Typical use cases:

* Daily reports.

* Database cleanup.

* Periodic synchronization.

* Scheduled notifications.

* Automated maintenance tasks.

### 10.5 Infrastructure automation

Lambda can execute automation code in response to AWS infrastructure events.

For example:

* Automatically tag newly created resources.

* Detect configuration changes.

* Respond to security events.

* Automate resource cleanup.

* Perform scheduled infrastructure checks.

### 10.6 Data processing

Lambda can process events from streaming and data services.

Examples include:

* DynamoDB Streams.

* Kinesis Data Streams.

* Amazon S3.

* Amazon MSK.

* EventBridge.

It is useful for lightweight transformations, filtering, validation, and event enrichment.

### 11\. Common Lambda Architectural Patterns

Understanding individual use cases is useful, but understanding reusable architectural patterns is even more important.

These patterns help you design applications that are scalable, maintainable, and reliable.

### 11.1 Function-as-a-Service pattern

The basic Lambda pattern is to execute a small, independent function in response to an event.

![Run a Serverless "Hello World!" with AWS Lambda](https://images.openai.com/static-rsc-4/fV4KpliGGVUN6ofiS9jISMy0LdoBdozvNUrkthDSur5HXhH11O7JTBTfOfcePvj2AUT0ZU0e7xdzU2NsIbY6vyZB1Bos6I-V11rIB-d4NoD7yyCatMDkf5h1TnVDCm3zafj4JgWcVtvHLahAllmfYNTEKqrIlKOrxpV56fpLh89wNWG4bvppUmGvw0FyjXkN?purpose=fullsize)

Example:

```text
Event
  |
Lambda Function
  |
Result
```

This is suitable for small application operations and event-driven processing.

### 11.2 Event-driven architecture

In this pattern, application components communicate through events rather than relying exclusively on direct synchronous calls.

![Routing dynamic dispatch patterns - AWS Prescriptive Guidance](https://images.openai.com/static-rsc-4/_QmExSthajuoyaArKr9VVqZ2YyeoaBkxe-P9swk8xnwGI3HkQmC7mRXsRyovKb-Fz1up8mpddnqu-4RhK4EfU2o3ftmjina3xpqNkA7MoN1ry8J_frmfLl1TIh-DNeK_g2X75JW2LboiH-Hv9wRep12ZrmBBL-CU5RTKGdfLLhUI546nr5IGhjQCn_oFSWzg?purpose=fullsize)

Example:

```text
Order Created
      |
  EventBridge
      |
  +---+---+
  |       |
Lambda  Lambda
Payment Inventory
```

The advantage is that application components can operate independently.

### 11.3 Queue-based processing

This pattern uses SQS to decouple event producers from processing consumers.

![How AWS Lambda Communicates with AWS SQS: An Overview of designing scalable web service | by Ahmer Patel | Medium](https://images.openai.com/static-rsc-4/qlDGblxLfiwGUbMM7R9z9BY-NHnY-Vuq0MA-dspAoYxjqb6d5hNIL0HAawg3A8MAk41ToE0GnLhDnxPXjlUOgs_lj6o519RwtnDWc2p-7xTTX5oxaqogSf6fBnTbHv0e5-GW7qIRkExeliM9cV7C6emjgiEq5yn6022yssqZuLUSTEXTiDikIWMDcsTej6pW?purpose=fullsize)

Example:

```text
Application
     |
    SQS
     |
   Lambda
     |
  Database
```

Advantages:

* Decoupling.

* Buffering.

* Independent scaling.

* Retry handling.

* Better traffic management.

### 11.4 Fanout architecture

SNS can distribute one event to multiple independent consumers.

![Amazon SNS vs. Amazon SQS: A simple comparison | Shikisoft Blog](https://images.openai.com/static-rsc-4/xp-eGacF8UCGhvWKmjsU3Otrh0XR1TjWpjAKtZcqjtSSpiUqBdLqDd27_H5KmQd54hJ3volsTvglvIJ29Wyn0IDo8PT2wuY4nz-dFE5TdfIp9eWtXu1Ml-2AqGy6zqaA3T7whPbq-kSTSnnbloeyuODDb12oqOa2cNmwY__I9j38d_VaSlR0C6KAy4kSi4tm?purpose=fullsize)

Example:

```text
           SNS Topic
               |
       +-------+-------+
       |       |       |
      SQS     SQS     SQS
       |       |       |
     Lambda  Lambda  Lambda
     Email   Billing Inventory
```

This is particularly useful for microservices architectures.

### 11.5 Orchestration pattern

For workflows involving multiple steps, Lambda can integrate with AWS Step Functions.

![Serverless Workflow Orchestration – AWS Step Functions – Amazon Web Services](https://images.openai.com/static-rsc-4/m2C63Ak1IMYXqqwpMFj4Fo5SVOVc_fWbr8Bs7tAwNn8R3zfmsN8nvWiC0lni5egMUhMUB4jQS3bWZHrvSsEoICssvpMJb2GPWSaXYpjCoivA_0etlrmIJydV1-SZ0e99xAUkI_9DOgwpAzYP-m-nRMAeP3Am9Nl89-8sseTGqQfeota_yCB8Ait9t9AMey4V?purpose=fullsize)

Example:

```text
Step Functions
      |
      v
Lambda: Validate Order
      |
      v
Lambda: Process Payment
      |
      v
Lambda: Update Inventory
      |
      v
Lambda: Send Notification
```

Step Functions manages workflow execution, state transitions, retries, and error handling.

This is generally preferable to building complex multi-step workflows inside a single Lambda function.

### 11.6 Backend-for-Frontend pattern

Lambda can provide independent backend operations for different client applications.

For example:

```text
       API Gateway
            |
     +------+------+
     |             |
   Lambda         Lambda
   Web API       Mobile API
     |             |
     +------+------+
            |
         Database
```

This allows different client applications to have tailored backend interfaces.

### 12\. Important Architectural Considerations

Before finishing the module, there are several principles worth remembering.

1\. Design functions to be stateless.

Do not rely on in-memory data surviving between invocations.

2\. Make operations idempotent.

The same event might be processed more than once. Your application should avoid unintended duplicate operations.

3\. Avoid excessively large functions.

Separate unrelated application responsibilities into independently maintainable functions.

4\. Understand invocation semantics.

Synchronous, asynchronous, and polling-based invocations have different delivery and failure-handling behaviors.

5\. Account for concurrency.

A sudden increase in incoming events can create many concurrent executions.

6\. Design for failure.

Use appropriate retries, dead-letter queues, failure destinations, and monitoring.

7\. Consider the entire architecture's cost.

Lambda might be inexpensive while supporting services such as NAT Gateway, API Gateway, and CloudWatch contribute significant costs.

8\. Choose compute according to workload characteristics.

Lambda is not automatically better than ECS, EKS, or EC2.

### Module 1 — Final Summary

You have now covered the foundational concepts required to understand AWS Lambda.

| Topic                  | What you should understand                                        |
| ---------------------- | ----------------------------------------------------------------- |
| Serverless             | Infrastructure abstraction and pay-per-use computing              |
| Lambda architecture    | Functions, runtimes, handlers, roles, and events                  |
| Execution environments | Init, Invoke, Shutdown, cold starts, and warm starts              |
| Runtime lifecycle      | Managed runtimes, custom runtimes, and deprecation                |
| Execution model        | How Lambda receives and processes invocations                     |
| Invocation patterns    | Synchronous, asynchronous, and polling-based                      |
| Invocation types       | RequestResponse, Event, and DryRun                                |
| Quotas                 | Execution duration, memory, storage, and concurrency              |
| Pricing                | Requests, GB-seconds, and supporting-service costs                |
| Compute selection      | Lambda vs. EC2 vs. ECS Fargate vs. EKS                            |
| Architecture           | API backends, event processing, queues, fanout, and orchestration |

### Important AWS documentation

For additional technical reference, these official AWS resources are particularly useful:

* [AWS Lambda functions and core concepts](https://docs.aws.amazon.com/lambda/latest/dg/lambda-functions-chapter.html?utm_source=chatgpt.com).

* [Lambda execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html?utm_source=chatgpt.com).

* [Lambda runtimes and runtime deprecation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtimes.html?utm_source=chatgpt.com).

* [Lambda quotas and limits](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html?utm_source=chatgpt.com).

Next: Module 2 — Lambda Functions, Python Development, and Configuration.

In that module, we'll move from understanding Lambda architecture to understanding how to develop actual Python Lambda functions, structure application code, manage dependencies, configure functions, and package applications for deployment.


___

### Module 1 Lab — Deploy Your First AWS Lambda Function with Pulumi

### Lab objectives

In this lab, you'll deploy your first AWS Lambda function using Pulumi and Python.

The goal is to understand how Lambda's fundamental architectural components fit together by creating and managing the infrastructure as code.

You will build a small serverless application that:

* Creates an AWS Lambda execution role.

* Attaches the required IAM permissions.

* Deploys a Python Lambda function.

* Configures the runtime, handler, memory, and timeout.

* Invokes the function using the AWS CLI.

* Examines the execution response and CloudWatch logs.

* Updates the function configuration using Pulumi.

* Destroys the infrastructure when finished.

Architecture

Developer workstation

Python · Pulumi · AWS CLI · Bash

Deploy infrastructure

Pulumi

Creates and manages AWS resources

AWS

IAM Execution Role

AWS Lambda Function

Python 3.14 · 256 MB · 30 seconds

CloudWatch Logs

Function execution logs

### Prerequisites

You should have:

* Python 3.11 or later.

* Pulumi CLI installed.

* Pulumi Python SDK.

* AWS CLI installed.

* AWS credentials configured.

* An AWS account with permissions to create IAM roles and Lambda functions.

Check your installations:

```bash
python --version
pulumi version
aws --version
```

Check AWS authentication:

```bash
aws sts get-caller-identity
```

The command should return your AWS account ID, user or role ARN, and account information.

For this lab, we'll use the `eu-north-1` AWS Region (Stockholm).

### Part 1 — Create the Pulumi project

Create a new project directory:

```bash
mkdir lambda-fundamentals
cd lambda-fundamentals
```

Create a Pulumi Python project:

```bash
pulumi new aws-python
```

Follow the prompts:

| Setting      | Value                   |
| ------------ | ----------------------- |
| Project name | lambda-fundamentals     |
| Description  | AWS Lambda fundamentals |
| Stack name   | dev                     |
| AWS Region   | eu-north-1              |

Pulumi creates a project structure similar to this:

```text
lambda-fundamentals/
├── __main__.py
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
└── .gitignore
```

The important files are:

* `Pulumi.yaml`: Project metadata and runtime configuration.

* `Pulumi.dev.yaml`: Stack-specific configuration.

* `__main__.py`: Infrastructure definition.

* `requirements.txt`: Python dependencies.

### Install dependencies

Open `requirements.txt` and ensure it contains:

```text
pulumi>=3.0.0
pulumi-aws>=7.0.0
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Initialize the Pulumi stack if it hasn't already been created:

```bash
pulumi stack select dev
```

### Part 2 — Create the Lambda application

Create a directory for the Lambda source code:

```bash
mkdir function
```

Create `function/app.py`:

```python

import json
from datetime import datetime, timezone

def lambda_handler(event, context):
    """
    Basic Lambda function demonstrating:
    - Event input
    - Context metadata
    - Runtime execution
    - JSON response
    """

    print("Received event:", json.dumps(event))

    response = {
        "message": "Hello from AWS Lambda!",
        "service": "AWS Lambda",
        "runtime": "Python",
        "event": event,
        "function_name": context.function_name,
        "request_id": context.aws_request_id,
        "remaining_time_ms": context.get_remaining_time_in_millis(),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

    print("Execution completed successfully")

    return {
        "statusCode": 200,
        "body": json.dumps(response)
    }
```

This function demonstrates several important Lambda concepts.

Event input

```python
event
```

Contains the data passed to your function.

Context object

```python
context.function_name
context.aws_request_id
context.get_remaining_time_in_millis()
```

Provides metadata about the current invocation.

Handler

```python
lambda_handler
```

Is the function Lambda executes when an invocation arrives.

Logging

```python
print("Execution completed successfully")
```

Writes output to the Lambda execution logs, which are integrated with CloudWatch Logs.

### Part 3 — Define the AWS infrastructure with Pulumi

Now we'll create the IAM role and Lambda function.

Open `__main__.py` and replace its contents with:

```python

import json
import pulumi
import pulumi_aws as aws

# -------------------------------------------------
# 1. Configuration
# -------------------------------------------------

config = pulumi.Config()

function_name = config.get(
    "functionName"
) or "lambda-fundamentals"

memory_size = config.get_int(
    "memorySize"
) or 256

timeout = config.get_int(
    "timeout"
) or 30

# -------------------------------------------------
# 2. Lambda IAM Execution Role
# -------------------------------------------------

assume_role_policy = json.dumps({
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
})

lambda_role = aws.iam.Role(
    "lambda-execution-role",
    name=f"{function_name}-execution-role",
    assume_role_policy=assume_role_policy,
    description="Execution role for the Lambda fundamentals lab"
)

# -------------------------------------------------
# 3. Attach CloudWatch Logs permissions
# -------------------------------------------------

logs_policy = aws.iam.RolePolicyAttachment(
    "lambda-logs-policy",
    role=lambda_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AWSLambdaBasicExecutionRole"
    )
)

# -------------------------------------------------
# 4. Create CloudWatch Log Group
# -------------------------------------------------

log_group = aws.cloudwatch.LogGroup(
    "lambda-log-group",
    name=f"/aws/lambda/{function_name}",
    retention_in_days=7
)

# -------------------------------------------------
# 5. Deploy Lambda Function
# -------------------------------------------------

lambda_function = aws.lambda_.Function(
    "fundamentals-function",

    name=function_name,

    role=lambda_role.arn,

    runtime="python3.14",

    handler="app.lambda_handler",

    code=pulumi.AssetArchive({
        "app.py": pulumi.FileAsset(
            "./function/app.py"
        )
    }),

    memory_size=memory_size,

    timeout=timeout,

    architectures=["arm64"],

    description="First Lambda function deployed with Pulumi",

    tags={
        "Environment": "dev",
        "Project": "lambda-fundamentals",
        "ManagedBy": "Pulumi"
    },

    opts=pulumi.ResourceOptions(
        depends_on=[
            logs_policy,
            log_group
        ]
    )
)

# -------------------------------------------------
# 6. Export Infrastructure Information
# -------------------------------------------------

pulumi.export(
    "lambda_function_name",
    lambda_function.name
)

pulumi.export(
    "lambda_function_arn",
    lambda_function.arn
)

pulumi.export(
    "lambda_execution_role_arn",
    lambda_role.arn
)

pulumi.export(
    "lambda_log_group",
    log_group.name
)
```

### Understanding the infrastructure definition

Let's examine the resources.

1\. IAM execution role

```python
lambda_role = aws.iam.Role(...)
```

This creates the IAM role that Lambda assumes when executing the function.

The trust policy:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "lambda.amazonaws.com"
  },
  "Action": "sts:AssumeRole"
}
```

Allows the Lambda service to assume this role.

Notice that a trust policy and a permissions policy are different:

* Trust policy: Who can assume the role?

* Permissions policy: What can the role do?

2\. CloudWatch permissions

```python
aws.iam.RolePolicyAttachment(...)
```

Attaches AWS's managed `AWSLambdaBasicExecutionRole` policy.

This grants the permissions necessary for basic CloudWatch Logs operations.

3\. CloudWatch Log Group

```python
aws.cloudwatch.LogGroup(...)
```

Creates the log group explicitly and configures seven-day retention.

This is preferable to allowing Lambda to create an unmanaged log group with indefinite retention.

4\. Lambda function

```python
aws.lambda_.Function(...)
```

This is the main resource.

Let's examine its configuration:

| Property      | Value               | Purpose                    |
| ------------- | ------------------- | -------------------------- |
| name          | lambda-fundamentals | Function name              |
| runtime       | python3.14          | Python runtime             |
| handler       | app.lambda_handler  | Entry point                |
| role          | IAM role ARN        | Execution permissions      |
| memory_size   | 256                 | Memory allocation          |
| timeout       | 30                  | Maximum execution duration |
| architectures | arm64               | CPU architecture           |

We use `pulumi.AssetArchive` and `pulumi.FileAsset` to package `app.py` into the Lambda deployment artifact.

Why ARM64?

Lambda supports both `x86_64` and `arm64` architectures.

ARM64 can provide attractive price-performance characteristics. Python is compatible with both, although native dependencies must be built for the selected architecture.

Our application only uses Python standard-library modules, so there are no additional native dependencies to worry about.

### Part 4 — Configure the Pulumi stack

Instead of hardcoding configuration in your infrastructure definition, we can manage it through Pulumi stack configuration.

Set the function name:

```bash
pulumi config set functionName lambda-fundamentals
```

Set memory:

```bash
pulumi config set memorySize 256
```

Set timeout:

```bash
pulumi config set timeout 30
```

Inspect your configuration:

```bash
pulumi config
```

This demonstrates an important Pulumi concept: the same infrastructure definition can be reused with different configuration values across development, staging, and production stacks.

### Part 5 — Preview and deploy the infrastructure

Before creating anything in AWS, inspect the proposed infrastructure changes:

```bash
pulumi preview
```

You should see resources similar to:

```text
+ aws:iam:Role
+ aws:iam:RolePolicyAttachment
+ aws:cloudwatch:LogGroup
+ aws:lambda:Function
```

The `+` symbol indicates that Pulumi intends to create a resource.

Deploy:

```bash
pulumi up
```

Review the proposed changes and confirm the deployment.

After deployment, Pulumi should display the exported values:

```text
Outputs:

lambda_execution_role_arn: ...
lambda_function_arn: ...
lambda_function_name: lambda-fundamentals
lambda_log_group: /aws/lambda/lambda-fundamentals
```

Your first Lambda function is now deployed.

### Part 6 — Invoke the Lambda function using AWS CLI

Now let's invoke the function directly.

Create an input event:

```bash
cat > event.json <<'EOF'
{
    "name": "AWS Lambda",
    "course": "Serverless Computing",
    "module": 1
}
EOF
```

Invoke the function synchronously:

```bash
aws lambda invoke \
    --function-name lambda-fundamentals \
    --invocation-type RequestResponse \
    --payload fileb://event.json \
    --cli-binary-format raw-in-base64-out \
    response.json
```

The command creates `response.json`, which contains the function's response.

Read it:

```bash
cat response.json
```

You should receive a response similar to:

```json
{
  "statusCode": 200,
  "body": "{\"message\": \"Hello from AWS Lambda!\", ...}"
}
```

The exact timestamp and request ID will differ.

### Understand the invocation response

The AWS CLI returns invocation metadata, including:

* `StatusCode`: HTTP status of the invocation API operation.

* `ExecutedVersion`: Version of the function that executed.

* `FunctionError`: Present when the function reports an execution error.

For synchronous invocation, a `200` status alone does not guarantee that the handler completed successfully. Always inspect `FunctionError` and the response payload.

### Invoke asynchronously

Now try asynchronous invocation:

```bash
aws lambda invoke \
    --function-name lambda-fundamentals \
    --invocation-type Event \
    --payload fileb://event.json \
    --cli-binary-format raw-in-base64-out \
    async-response.json
```

You should receive:

```json
{
    "StatusCode": 202
}
```

This means Lambda accepted the event for asynchronous processing.

It does not mean that the function has completed successfully.

### Invoke using DryRun

You can also validate invocation permissions without executing the function:

```bash
aws lambda invoke \
    --function-name lambda-fundamentals \
    --invocation-type DryRun \
    --payload fileb://event.json \
    --cli-binary-format raw-in-base64-out \
    dryrun-response.json
```

A successful DryRun returns HTTP status `204`.

These three commands demonstrate the three Lambda invocation types covered earlier.

### Part 7 — Inspect Lambda configuration and CloudWatch Logs

Let's inspect the deployed function.

### 7.1 Get function configuration

```bash
aws lambda get-function-configuration \
    --function-name lambda-fundamentals
```

You should find information such as:

```json
{
    "FunctionName": "lambda-fundamentals",
    "Runtime": "python3.14",
    "Handler": "app.lambda_handler",
    "MemorySize": 256,
    "Timeout": 30,
    "Architectures": [
        "arm64"
    ]
}
```

### 7.2 Inspect execution logs

Our function writes messages using Python's `print()` statements.

These messages are sent to CloudWatch Logs.

Retrieve recent logs:

```bash
aws logs tail \
    /aws/lambda/lambda-fundamentals \
    --since 10m \
    --follow
```

You should see output containing:

```text
Received event: ...

Execution completed successfully
```

Lambda also generates system-level execution information, including duration, memory usage, and initialization information when applicable.

### 7.3 Inspect the IAM role

Retrieve the role:

```bash
aws iam get-role \
    --role-name lambda-fundamentals-execution-role
```

List attached policies:

```bash
aws iam list-attached-role-policies \
    --role-name lambda-fundamentals-execution-role
```

You should find:

```text
AWSLambdaBasicExecutionRole
```

This confirms that the function has the permissions required for basic CloudWatch logging.

### Part 8 — Update Lambda configuration using Pulumi

One of the advantages of Infrastructure as Code is that you can change infrastructure configuration without manually editing resources in the AWS Console.

Let's increase the Lambda memory from 256 MB to 512 MB.

Update the stack configuration:

```bash
pulumi config set memorySize 512
```

Preview the changes:

```bash
pulumi preview
```

Apply the update:

```bash
pulumi up
```

Pulumi should detect that the Lambda function configuration needs updating.

Verify the change:

```bash
aws lambda get-function-configuration \
    --function-name lambda-fundamentals \
    --query '{Memory:MemorySize,Timeout:Timeout,Runtime:Runtime}'
```

Expected output:

```json
{
    "Memory": 512,
    "Timeout": 30,
    "Runtime": "python3.14"
}
```

You have now experienced the basic Pulumi infrastructure lifecycle:

```text
Define infrastructure
        |
    pulumi preview
        |
     pulumi up
        |
  Inspect resources
        |
 Update configuration
        |
     pulumi up
        |
  Verify changes
```

This workflow will be used throughout the remaining Lambda modules.

### Part 9 — Destroy the infrastructure

When you finish the lab, remove the resources to avoid unnecessary AWS charges.

Run:

```bash
pulumi destroy
```

Review the proposed deletions and confirm.

Pulumi should remove:

* Lambda function.

* IAM execution role.

* IAM policy attachment.

* CloudWatch log group.

Remove the stack if you no longer need it:

```bash
pulumi stack rm dev
```

The project files remain on your computer, but the deployed infrastructure is removed.

### Final project structure

Your project should now look similar to this:

```text
lambda-fundamentals/
│
├── function/
│   └── app.py
│
├── __main__.py
│
├── Pulumi.yaml
│
├── Pulumi.dev.yaml
│
├── requirements.txt
│
└── .gitignore
```

### Important concepts demonstrated

| AWS Lambda concept       | Where you implemented it    |
| ------------------------ | --------------------------- |
| Lambda function          | aws.lambda_.Function        |
| Python runtime           | python3.14                  |
| Handler                  | app.lambda_handler          |
| Execution environment    | AWS-managed                 |
| Execution role           | aws.iam.Role                |
| Trust policy             | IAM assume-role policy      |
| Permissions policy       | AWSLambdaBasicExecutionRole |
| Memory allocation        | memory_size                 |
| Execution timeout        | timeout                     |
| Architecture             | arm64                       |
| Deployment package       | pulumi.AssetArchive         |
| CloudWatch logging       | aws.cloudwatch.LogGroup     |
| Synchronous invocation   | RequestResponse             |
| Asynchronous invocation  | Event                       |
| Permission validation    | DryRun                      |
| Infrastructure lifecycle | preview, up, destroy        |

### Additional AWS and Pulumi references

* [Pulumi AWS integration documentation](https://www.pulumi.com/docs/integrations/clouds/aws/?utm_source=chatgpt.com).

* [Pulumi AWS Lambda Function resource](https://www.pulumi.com/registry/packages/aws%406.x/api-docs/lambda/function/?utm_source=chatgpt.com).

* [Pulumi AWS IAM Role resource](https://www.pulumi.com/registry/packages/aws/api-docs/iam/role/?utm_source=chatgpt.com).

* [Pulumi Python documentation](https://www.pulumi.com/docs/iac/languages-sdks/python/?utm_source=chatgpt.com).

A note about costs: This is a small deployment, but Lambda invocations, CloudWatch Logs ingestion and storage, and other supporting services can incur charges. The lab uses a seven-day log retention period and does not create an API Gateway, NAT Gateway, or other additional infrastructure.

The main objective is to understand how Pulumi translates Python infrastructure definitions into AWS resources and how those resources participate in Lambda's execution architecture.
