### Module 2 — Lambda Functions, Python Development, and Configuration

This module focuses on developing AWS Lambda functions using Python, understanding how Lambda executes application code, managing dependencies, configuring runtime resources, and packaging applications for deployment.

By the end of this module, you should understand how to build Lambda functions that are maintainable, configurable, reusable, and ready for deployment.

We will use Python for application development, `uv` for dependency management where appropriate, and AWS CLI with Bash for deployment-related examples.

### 1\. Lambda Function Structure and Programming Model

An AWS Lambda function is a unit of code that AWS executes in response to an event or an invocation request.

Unlike a traditional application that continuously runs and waits for requests, Lambda executes your function when it is invoked.

A Lambda function generally consists of:

* Function code.

* Runtime.

* Handler.

* Execution role.

* Configuration.

* Event input.

* Execution environment.

### Basic Lambda architecture

![Run a Serverless "Hello World!" with AWS Lambda](https://images.openai.com/static-rsc-4/fV4KpliGGVUN6ofiS9jISMy0LdoBdozvNUrkthDSur5HXhH11O7JTBTfOfcePvj2AUT0ZU0e7xdzU2NsIbY6vyZB1Bos6I-V11rIB-d4NoD7yyCatMDkf5h1TnVDCm3zafj4JgWcVtvHLahAllmfYNTEKqrIlKOrxpV56fpLh89wNWG4bvppUmGvw0FyjXkN?purpose=fullsize)

Consider a simple Python Lambda function:

```python
def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from AWS Lambda!"
    }
```

There are two important parameters:

* `event`: Contains the input data provided to the function.

* `context`: Provides information about the current invocation and execution environment.

The function returns a Python dictionary.

Lambda's integration determines how that return value is interpreted. For example, API Gateway can interpret the dictionary as an HTTP response when using its Lambda proxy integration.

### Lambda programming model

The programming model describes how your application code interacts with the Lambda runtime.

The typical execution sequence is:

* AWS receives an invocation.

* Lambda prepares an execution environment if one is needed.

* The runtime initializes your application.

* Lambda invokes your handler.

* Your handler processes the event.

* Your handler returns a result or raises an exception.

* Lambda handles the invocation outcome.

An important concept is that Lambda execution environments can be reused across multiple invocations.

This means you should distinguish between:

* Initialization code: Runs when the execution environment is initialized.

* Invocation code: Runs each time the handler is invoked.

For example:

```python
import json

# Initialization phase
SERVICE_NAME = "orders-service"

def lambda_handler(event, context):
    # Invocation phase
    return {
        "service": SERVICE_NAME,
        "event": event
    }
```

The module-level variable is initialized once per execution environment, rather than once per invocation.

However, you should never assume that Lambda will reuse an environment. AWS can create new environments or terminate existing ones at any time.

### 2\. Python Handlers and Event Objects

### What is a handler?

The handler is the entry point that Lambda calls when your function is invoked.

For Python, the handler is defined using the following format:

```text
module_name.function_name
```

For example:

```text
app.lambda_handler
```

This tells Lambda to:

* Load the Python module named `app`.

* Execute the function named `lambda_handler`.

A corresponding file might look like this:

```text
project/
├── app.py
└── requirements.txt
```

The `app.py` file:

```python
def lambda_handler(event, context):
    return {
        "message": "Request processed successfully"
    }
```

### Understanding the event object

The event object contains the data associated with an invocation.

Its structure depends on the service invoking Lambda.

For example, an API Gateway event may contain:

```python
{
    "httpMethod": "POST",
    "path": "/orders",
    "body": "{\"product_id\": 100}"
}
```

An S3 event may contain:

```python
{
    "Records": [
        {
            "eventSource": "aws:s3",
            "eventName": "ObjectCreated:Put",
            "s3": {
                "bucket": {
                    "name": "my-upload-bucket"
                },
                "object": {
                    "key": "documents/report.pdf"
                }
            }
        }
    ]
}
```

An SQS event may contain:

```python
{
    "Records": [
        {
            "messageId": "message-123",
            "body": "{\"order_id\": 100}"
        }
    ]
}
```

Notice that these event structures are different.

Your handler must understand the schema of the event source.

### Processing event data

A simple handler that processes an SQS message:

```python
import json

def lambda_handler(event, context):
    for record in event.get("Records", []):
        message = json.loads(record["body"])

        order_id = message["order_id"]

        print(f"Processing order: {order_id}")

    return {
        "statusCode": 200,
        "processed": len(event.get("Records", []))
    }
```

This example demonstrates how a Lambda function can process multiple messages in a single invocation.

For production applications, you should also consider malformed messages, duplicate delivery, and partial batch failures.

### 3\. Context Object and Execution Metadata

The `context` object provides runtime information about the current Lambda invocation.

It is supplied automatically by the Lambda runtime. You do not need to construct it yourself.

Important context attributes include:

| Attribute                              | Description                          |
| -------------------------------------- | ------------------------------------ |
| context.function_name                  | Name of the Lambda function          |
| context.function_version               | Version being executed               |
| context.invoked_function_arn           | ARN used for invocation              |
| context.memory_limit_in_mb             | Configured memory allocation         |
| context.aws_request_id                 | Unique identifier for the invocation |
| context.log_group_name                 | Associated CloudWatch log group      |
| context.log_stream_name                | Current CloudWatch log stream        |
| context.get_remaining_time_in_millis() | Remaining execution time             |

### Example

```python
def lambda_handler(event, context):
    remaining_time = context.get_remaining_time_in_millis()

    return {
        "function": context.function_name,
        "request_id": context.aws_request_id,
        "memory": context.memory_limit_in_mb,
        "remaining_time_ms": remaining_time
    }
```

### Why is the context object important?

Consider a function that processes large files.

You configure its timeout to 60 seconds.

The function starts processing a file, but after 45 seconds, only 15 seconds remain.

You can use:

```python
remaining = context.get_remaining_time_in_millis()
```

Your application can use this information to decide whether to:

* Continue processing.

* Save its current progress.

* Stop starting additional operations.

* Return a controlled error.

This is particularly useful for long-running workloads and batch processing.

Another important use is request correlation. The `aws_request_id` helps you associate application logs with a specific Lambda invocation.

### 4\. Request-Response Processing

Lambda uses a request-response programming model in which an invocation provides input to a function and the function produces an output.

The actual request-response behavior depends on the invocation type and integration.

### Basic request-response flow

![Effective error handling strategies for Lambda invocation models - DEV Community](https://images.openai.com/static-rsc-4/_a2YMufCX-WEWjXq2_H_PLgCi3r3VnG_G7lmZ6VnHi39OlmCDvhyxi0dRS21XBnStYjGmj3MT8EuCK9oP7kMj7gmkkTr05BH59rnVfsS73MgnsqkuqgVTqEpYcnVYjOV-MpVZIGvAYhBzPvY7iq8rx4cYhUz8JvjYuxhKSMC2U_GvALVILPAbtDvEWHKmk0_?purpose=fullsize)

For example, an API Gateway endpoint might invoke a Lambda function:

```text
Client
  |
  v
API Gateway
  |
  v
Lambda Function
  |
  v
Response
  |
  v
API Gateway
  |
  v
Client
```

Consider a function that processes an HTTP request:

```python
import json

def lambda_handler(event, context):
    body = json.loads(event.get("body") or "{}")

    username = body.get("username")

    if not username:
        return {
            "statusCode": 400,
            "headers": {
                "Content-Type": "application/json"
            },
            "body": json.dumps({
                "error": "username is required"
            })
        }

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": f"Welcome, {username}"
        })
    }
```

There are several important concepts here.

Input processing: Lambda receives an event containing the request information.

Application processing: Python processes the request and performs the required operations.

Response generation: The function returns a response object.

Integration processing: API Gateway interprets the returned object and sends an HTTP response to the client.

An important distinction: Lambda itself does not automatically understand HTTP status codes. The integration determines how the returned value is interpreted.

### Request-response limitations

Synchronous Lambda invocations have a maximum execution duration of 15 minutes.

However, HTTP integrations may have shorter integration-specific timeout limits.

You should also consider:

* Payload size limits.

* Network latency.

* Client connection timeouts.

* API Gateway integration timeouts.

* Error propagation.

* Retry behavior.

For applications that need to process requests asynchronously, returning an immediate acknowledgement and processing the workload separately is often a better architecture.

### 5\. Environment Variables and Configuration Management

Environment variables allow you to configure Lambda functions without hardcoding configuration values in your application.

For example, imagine that your Lambda function communicates with a database.

You might need:

* Database hostname.

* Database port.

* Database name.

* Application environment.

* External API endpoint.

Instead of hardcoding these values, you can provide them through Lambda environment variables.

### Configuring environment variables

Example:

```text
DATABASE_HOST=db.example.internal
DATABASE_PORT=5432
DATABASE_NAME=orders
APP_ENV=production
```

In Python, you can retrieve them using the `os` module:

```python
import os

DATABASE_HOST = os.environ["DATABASE_HOST"]
DATABASE_PORT = int(os.environ.get("DATABASE_PORT", "5432"))
DATABASE_NAME = os.environ["DATABASE_NAME"]

def lambda_handler(event, context):
    return {
        "database_host": DATABASE_HOST,
        "database_port": DATABASE_PORT,
        "database_name": DATABASE_NAME
    }
```

### Configuration management strategies

There are several ways to manage application configuration in AWS.

| Service or mechanism                | Purpose                                 |
| ----------------------------------- | --------------------------------------- |
| Lambda environment variables        | Function-specific configuration         |
| AWS Systems Manager Parameter Store | Centralized configuration storage       |
| AWS Secrets Manager                 | Secret and credential management        |
| AWS KMS                             | Encryption key management               |
| Pulumi configuration                | Infrastructure deployment configuration |

### Environment variables versus Secrets Manager

Environment variables are useful for relatively small configuration values.

However, sensitive information such as database passwords and API credentials should be managed carefully.

For sensitive values, Secrets Manager is generally preferable.

A Lambda function can retrieve a secret using Boto3:

```python
import boto3
import json

client = boto3.client("secretsmanager")

def get_database_credentials():
    response = client.get_secret_value(
        SecretId="production/database"
    )

    return json.loads(response["SecretString"])
```

For performance, avoid retrieving the same secret on every invocation unnecessarily. You can cache it within the execution environment while accounting for secret rotation and cache expiration.

### Important security considerations

* Encrypt environment variables at rest.

* Restrict access through IAM policies.

* Avoid logging secrets.

* Avoid embedding credentials in deployment packages.

* Use Secrets Manager for sensitive application credentials.

* Apply least-privilege permissions.

### 6\. Function Memory, Timeout, and Ephemeral Storage

Every Lambda function has configurable execution resources.

Three particularly important settings are:

* Memory.

* Timeout.

* Ephemeral storage.

### 6.1 Memory allocation

Lambda memory determines the amount of memory available to the function.

The configurable range is:

* Minimum: 128 MB.

* Maximum: 10,240 MB.

Memory allocation also influences the CPU resources available to your function.

Higher memory allocations provide more CPU capacity, which can improve execution performance.

For example:

| Memory    | Potential workload             |
| --------- | ------------------------------ |
| 128 MB    | Lightweight operations         |
| 512 MB    | Small API processing           |
| 1,024 MB  | Moderate application workloads |
| 3,008 MB  | CPU-intensive processing       |
| 10,240 MB | Memory-intensive workloads     |

These are illustrative workload categories, not fixed requirements.

### 6.2 Timeout configuration

Timeout determines the maximum execution duration of a Lambda invocation.

The maximum configurable timeout is 900 seconds (15 minutes).

For example:

```text
Timeout: 30 seconds
```

If the function does not finish within that period, Lambda terminates the invocation.

Timeout configuration should reflect the actual processing requirements.

A function that handles a simple HTTP request might need only a few seconds, whereas a function that processes large files may require significantly more time.

### 6.3 Ephemeral storage

Lambda provides temporary storage through the `/tmp` directory.

This storage is useful when your function needs to:

* Download files.

* Extract ZIP archives.

* Process images.

* Generate temporary reports.

* Store intermediate processing results.

The configurable ephemeral storage range is:

* Minimum: 512 MB.

* Maximum: 10,240 MB.

Example:

```python
import os

def lambda_handler(event, context):
    temp_directory = "/tmp"

    file_path = os.path.join(
        temp_directory,
        "report.txt"
    )

    with open(file_path, "w") as file:
        file.write("Lambda temporary file")

    return {
        "file_path": file_path
    }
```

Remember that `/tmp` is not permanent storage.

Execution environments may be reused, so temporary files can remain between invocations, but you must not depend on their persistence.

For durable storage, use services such as Amazon S3 or Amazon EFS.

![How to modify the timeouts in Lambda and SQS](https://images.openai.com/static-rsc-4/Yhap8YYm722a1ZbsBlzvs1UMReamHnkkRACcr4uO6EsXhrKFx3FyrdRiir_cvBHN9NKHy46gO8GIoC5K3wBDUdrcl2FvkW0PU5yJpYaps8c__7fgvaOheBmBjCLYX8YKuhtLd1TVylRc-GfoQ6zSK3rV-EGGEDIi56lXtEhvlECkBAASuzA3zYMM6aU3pG9a?purpose=fullsize)

### 7\. Lambda Deployment Packages and ZIP Archives

Lambda needs access to your application code and its dependencies before it can execute your function.

One common deployment method is a ZIP deployment package.

A ZIP deployment package contains:

* Python source files.

* Required dependencies.

* Supporting application files.

* Other resources needed by the function.

### Example project structure

```text
lambda-project/
│
├── app.py
├── requirements.txt
└── utils.py
```

Your handler could be:

```python
# app.py

from utils import format_message

def lambda_handler(event, context):
    return {
        "message": format_message("Hello Lambda")
    }
```

And:

```python
# utils.py

def format_message(message):
    return message.upper()
```

### Creating a ZIP package

For a simple function without external dependencies:

```bash
mkdir -p package

cp app.py utils.py package/

cd package

zip -r ../lambda-function.zip .

cd ..
```

The resulting archive contains the application files.

### Deploying using AWS CLI

You can create a Lambda function with the AWS CLI:

```bash
aws lambda create-function \
  --function-name orders-processor \
  --runtime python3.13 \
  --handler app.lambda_handler \
  --role arn:aws:iam::123456789012:role/lambda-execution-role \
  --zip-file fileb://lambda-function.zip
```

This is an illustrative command; the runtime must be supported in the target AWS Region when you deploy.

To update the function code:

```bash
aws lambda update-function-code \
  --function-name orders-processor \
  --zip-file fileb://lambda-function.zip
```

### Important packaging considerations

Python dependencies must be available inside the deployment package or through another supported mechanism, such as Lambda Layers.

Also consider:

* Operating system compatibility.

* CPU architecture compatibility.

* Python runtime compatibility.

* Native libraries and compiled extensions.

* Deployment package size limits.

For Python packages containing native extensions, building on a compatible Linux environment is important because a package compiled for Windows generally cannot be used directly in a Linux Lambda execution environment.

### 8\. Python Dependencies and Package Management

Real-world Lambda applications rarely depend only on the Python standard library.

You might need:

* Boto3 for AWS service interactions.

* Pydantic for data validation.

* SQLAlchemy for database operations.

* Requests or HTTPX for HTTP communication.

* Pillow for image processing.

These dependencies must be packaged correctly.

### Managing dependencies with uv

For local Python development, `uv` provides fast dependency management.

A project might look like:

```text
orders-lambda/
├── pyproject.toml
├── uv.lock
├── app.py
└── requirements.txt
```

You can add dependencies:

```bash
uv add pydantic httpx
```

For deployment packaging, create a compatible requirements file:

```bash
uv export \
  --format requirements.txt \
  --no-dev \
  --no-emit-project \
  -o requirements.txt
```

Then install the dependencies into the deployment directory.

```bash
mkdir -p package

uv pip install \
  --target package \
  -r requirements.txt

cp app.py package/

cd package

zip -r ../lambda-function.zip .

cd ..
```

For dependencies containing native extensions, perform the installation in a compatible Linux environment with the correct Python version and architecture.

### Dependency management considerations

You should understand:

* Dependency pinning.

* Lock files.

* Transitive dependencies.

* Development versus production dependencies.

* Platform-specific packages.

* Package size optimization.

* Dependency vulnerability management.

An important detail: AWS provides Boto3 in its Python Lambda runtimes, but if your application relies on a specific SDK version, packaging and managing that version yourself can provide more predictable dependency behavior.

### 9\. Lambda Layers and Dependency Reuse

Lambda Layers provide a mechanism for sharing dependencies and other files across multiple Lambda functions.

Imagine that you have ten Lambda functions, all using the same Python libraries.

Without Layers, you might package the same dependencies into all ten functions.

With Layers, you can centralize shared dependencies.

![AWS Lambda Layers: Code Reusability | by Harry Kay | Medium](https://images.openai.com/static-rsc-4/Yxo3VTLtX5ORtRfv0Qlq5JMHUfB8JHPUD6MM08IaliX8XId34pD2sreUtOvVVN-vCqY5GQ-UIQs1DuJhBxAlsztyXXKNT2sdBzuRuIklEgBehvLS8YVsncUNd6QJs1RZ5wyISqJ5pZzcEgD04TCREDkJ3fPkdmvh_VUsFqi6IuB5QyHKf8BwKIO_Rk5OQQxB?purpose=fullsize)

### Python Layer structure

For Python, the directory structure is important.

For example:

```text
python/
└── lib/
    └── python3.13/
        └── site-packages/
            ├── pydantic/
            └── httpx/
```

The `python` directory must be at the root of the Layer ZIP archive.

### Creating a Layer

```bash
mkdir -p layer/python

uv pip install \
  --target layer/python \
  pydantic httpx

cd layer

zip -r ../python-dependencies.zip .

cd ..
```

You can publish the Layer using AWS CLI:

```bash
aws lambda publish-layer-version \
  --layer-name python-dependencies \
  --zip-file fileb://python-dependencies.zip \
  --compatible-runtimes python3.13
```

This example assumes that the selected runtime is supported.

### Attaching a Layer

Once published, you can attach the Layer to a Lambda function.

```bash
aws lambda update-function-configuration \
  --function-name orders-processor \
  --layers arn:aws:lambda:REGION:ACCOUNT_ID:layer:python-dependencies:1
```

### Layer characteristics

* Layers are versioned.

* A function can use multiple Layers.

* Layers can be shared across functions.

* Layers can be shared across AWS accounts through permissions.

* Layers must be compatible with the function's runtime and architecture.

Lambda supports up to five attached Layers per function.

### When should you use Layers?

Layers are useful when:

* Multiple functions share dependencies.

* You want to separate application code from shared libraries.

* You want to maintain common utilities.

* You need to distribute extensions or shared runtime resources.

However, Layers are not always necessary. For a small application, including dependencies directly in the deployment package may be simpler.

### 10\. Custom Runtimes and Runtime API Fundamentals

AWS provides managed runtimes for popular programming languages, including Python, Node.js, Java, .NET, and Ruby.

A managed runtime handles the communication between Lambda and your application code.

However, sometimes you need to use a programming language or runtime environment that AWS does not provide directly.

This is where custom runtimes become useful.

### What is a custom runtime?

A custom runtime allows you to bring your own runtime implementation.

For example, you might want to execute:

* Go applications using a custom runtime.

* Rust applications.

* Applications written in less common programming languages.

* Specialized language environments.

A custom runtime is responsible for communicating with the Lambda Runtime API.

### Lambda Runtime API

The Runtime API allows a runtime to retrieve invocation events and return execution results.

The general execution flow is:

![How to run stateful AWS Lambda functions in any language using custom runtimes - DEV Community](https://images.openai.com/static-rsc-4/xINxESxbhjpKM1oMu76L1cGLp9WaX6AtCpJxDWYnPvAZk5Fw1wmlCS-uqTzQbrXh9pSCT7TY_OWcL_GCfLObJiW1QquCqRDDubLJn6i4M67aTn_3RSJ-a9hJe8G5PbVZDJzx7CnCn4akFqG-DzW24woDKLspjf_8IunlXXQYO8k5IWmFfDuTD2rz_I5rnSEo?purpose=fullsize)

The runtime communicates with the following endpoints:

| Runtime API endpoint                     | Purpose                         |
| ---------------------------------------- | ------------------------------- |
| /runtime/invocation/next                 | Retrieves the next invocation   |
| /runtime/invocation/{requestId}/response | Submits a successful result     |
| /runtime/invocation/{requestId}/error    | Reports an invocation error     |
| /runtime/init/error                      | Reports an initialization error |

The runtime repeatedly retrieves events, executes application code, and returns results.

### Bootstrap file

A custom runtime typically uses an executable file named:

```text
bootstrap
```

This file starts the runtime implementation.

For example, a simplified conceptual bootstrap script:

```bash
#!/bin/bash

exec /var/task/my-runtime
```

The runtime executable is responsible for implementing the Runtime API communication.

### Custom runtime versus managed runtime

| Feature              | Managed runtime    | Custom runtime      |
| -------------------- | ------------------ | ------------------- |
| Runtime management   | AWS                | You                 |
| Runtime updates      | AWS-managed        | Your responsibility |
| Language flexibility | Supported runtimes | Broad flexibility   |
| Complexity           | Lower              | Higher              |
| Maintenance          | Less               | More                |

Custom runtimes are particularly useful when you need complete control over the execution environment.

### 11\. Container Image-Based Lambda Functions

ZIP deployment packages are not the only way to deploy Lambda functions.

AWS also supports deploying Lambda functions as container images.

This is particularly useful when your application has complex dependencies or requires a specific operating system environment.

### Container image architecture

![Using container image support for AWS Lambda with AWS SAM | AWS Compute Blog](https://images.openai.com/static-rsc-4/T3FjrRNr-rOvO4FJQtniJBmYJsLNGoyQ-Hy5CfABsXL-xn6Rul8P9xT2DIRMNH9BpGnOuYUP_ZnRpjWn39AoPImPVZYeqTZibRmF4O-kftC3wc4S0a7SNm1HARErLupMn1e_c6OD9bUQ6nODuA7YiN6BNqgUMuIEYArxchJapXpcXyr9XbwJV960VtY2P8aE?purpose=fullsize)

The deployment process generally looks like this:

* Build a container image.

* Tag the image.

* Push the image to Amazon ECR.

* Create a Lambda function using the image URI.

* Lambda retrieves and executes the image.

### Example Dockerfile

For a Python application:

```dockerfile
FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt ${LAMBDA_TASK_ROOT}

RUN pip install \
    -r requirements.txt \
    --target ${LAMBDA_TASK_ROOT}

COPY app.py ${LAMBDA_TASK_ROOT}

CMD ["app.lambda_handler"]
```

This uses an AWS Lambda Python base image.

The `CMD` instruction identifies the handler.

### Application code

```python
def lambda_handler(event, context):
    return {
        "message": "Hello from Lambda container!"
    }
```

### Building the image

```bash
docker build -t orders-lambda .
```

### Pushing to Amazon ECR

After creating an ECR repository:

```bash
aws ecr get-login-password --region eu-north-1 \
  | docker login \
      --username AWS \
      --password-stdin ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com
```

Tag the image:

```bash
docker tag orders-lambda:latest \
  ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/orders-lambda:latest
```

Push it:

```bash
docker push \
  ACCOUNT_ID.dkr.ecr.eu-north-1.amazonaws.com/orders-lambda:latest
```

You can then create a Lambda function using the image URI.

### ZIP versus container image

| Characteristic        | ZIP deployment              | Container image                              |
| --------------------- | --------------------------- | -------------------------------------------- |
| Packaging             | ZIP archive                 | OCI container image                          |
| Maximum package size  | 250 MB uncompressed         | 10 GB image                                  |
| Dependency management | Package or Layers           | Container image                              |
| Base environment      | Lambda runtime environment  | Customizable Lambda-compatible image         |
| Local development     | Straightforward             | Docker-based                                 |
| Best suited for       | Most conventional functions | Complex dependencies and custom environments |

One important distinction: Lambda container images must follow Lambda's runtime requirements. You cannot simply deploy an arbitrary Docker container that expects to run as a continuously running web server.

Container images also require Amazon ECR as their image repository.

### 12\. Lambda Extensions and Execution Environment Integration

Lambda Extensions allow you to integrate additional capabilities into the Lambda execution environment.

They are particularly useful for monitoring, observability, security, and configuration management.

Imagine that your application needs to send logs to an external monitoring platform.

Instead of implementing the entire monitoring integration inside your application, you can use a Lambda Extension.

### Extension architecture

![AWS Builder Center](https://images.openai.com/static-rsc-4/ekCh8ri9t0Ao2FNBgZAxofxvU0oKfhHjf8O83ouMTx8o5ZWsbiqdeUSuFtuIGabMLBSnxlgLI0ZqwzwyYJzX2x1Q6nqJDdu08pwQpYwGQ_w0zlI0bqfe4K58HYF3Mcb7mr0OLgs1bFyJm10xli7L5LBijMNETFTZu_kHlVD5s6bJm4gwrAesTlHuu_I4o-OL?purpose=fullsize)

There are two main extension categories.

Internal extensions

These run within the language runtime process.

For example, an extension can be implemented as part of a Python application.

External extensions

These run as separate processes inside the Lambda execution environment.

They can interact with the Lambda Extensions API.

### Extension lifecycle

An extension participates in different execution environment lifecycle events.

Important lifecycle events include:

* `INIT`: Initialization phase.

* `INVOKE`: Invocation phase.

* `SHUTDOWN`: Execution environment shutdown.

External extensions register themselves with the Extensions API and receive lifecycle notifications.

### Extensions use cases

| Use case      | Description                                   |
| ------------- | --------------------------------------------- |
| Monitoring    | Collect application and runtime metrics       |
| Logging       | Forward logs to external platforms            |
| Security      | Perform security-related monitoring           |
| Configuration | Retrieve or provide configuration             |
| Observability | Integrate with tracing and monitoring systems |

Examples of technologies that provide Lambda extensions include AWS Lambda Extensions and third-party observability agents.

### Extensions versus Layers

These two features are related but serve different purposes.

* Lambda Layers distribute code, libraries, and supporting files.

* Lambda Extensions provide additional functionality that integrates with the Lambda execution environment.

A Layer can package an extension, but the Layer itself is not an extension.

### 13\. Logging and Structured Application Output

Logging is essential for understanding what happens inside Lambda functions.

AWS Lambda integrates with Amazon CloudWatch Logs.

When a function executes, its standard output and standard error streams can be collected and delivered to the function's CloudWatch log group.

### Basic logging with Python

Python provides the built-in `logging` module.

```python
import logging

logger = logging.getLogger()

logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    logger.info("Lambda function started")

    logger.info(
        "Processing request %s",
        context.aws_request_id
    )

    logger.warning("Example warning")

    return {
        "statusCode": 200,
        "message": "Completed"
    }
```

The output can be inspected through CloudWatch Logs.

### Log levels

| Level    | Purpose                               |
| -------- | ------------------------------------- |
| DEBUG    | Detailed diagnostic information       |
| INFO     | Normal application events             |
| WARNING  | Unexpected but recoverable conditions |
| ERROR    | Application errors                    |
| CRITICAL | Severe application failures           |

### Structured logging

In production applications, structured logging is preferable to unstructured text.

Instead of:

```text
Order 123 processed successfully
```

You can produce JSON:

```json
{
  "level": "INFO",
  "event": "order_processed",
  "order_id": 123,
  "request_id": "abc-123",
  "status": "success"
}
```

Structured logging makes it easier to search, filter, aggregate, and analyze application logs.

For example, you can use CloudWatch Logs Insights to search for failed orders or specific request IDs.

### Python structured logging example

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    log_entry = {
        "event": "order_processed",
        "request_id": context.aws_request_id,
        "order_id": event.get("order_id"),
        "status": "success"
    }

    logger.info(json.dumps(log_entry))

    return {
        "statusCode": 200
    }
```

### Lambda logging configuration

Lambda provides configurable logging options, including:

* Log format.

* Log level.

* Application log level.

* System log level.

* CloudWatch Logs destination.

Python Lambda runtimes also support structured JSON logging through their managed logging capabilities.

### Important logging practices

* Include request identifiers.

* Use consistent log formats.

* Avoid logging sensitive information.

* Use appropriate log levels.

* Avoid excessive logging.

* Configure appropriate log retention periods.

* Use CloudWatch Logs Insights for analysis.

### 14\. Initialization and Execution Phases

Understanding the Lambda execution lifecycle is essential for building efficient applications.

Lambda does not necessarily create a completely new execution environment for every invocation.

Instead, AWS can reuse an existing execution environment.

The lifecycle has three important phases:

* Initialization.

* Invocation.

* Shutdown.

![Building Extensions for AWS Lambda | AWS Compute Blog](https://images.openai.com/static-rsc-4/cir0vwWBm-FN0tm-a-x5L8kC1cd7d5g7GxMlFMSWVJs3RZJg-25laZVuE0Zsp-R9p8CAQRwpi8rdABfvriL8rNkYsgNtxLDMcfrCtb8joEQlT6pg_VUZ2MJb2ibpp7WYfpu4eMRfFbExF5ACoqrSBM_CYWY5wDrRKHBmlunJjM7irZeZ1LvhbPWZ4_ANLdZd?purpose=fullsize)

### 14.1 Initialization phase

During initialization, Lambda prepares the execution environment.

This includes:

* Starting the runtime.

* Loading application code.

* Importing Python modules.

* Executing global initialization code.

* Initializing extensions.

Consider:

```python
import boto3

# Initialization phase
s3 = boto3.client("s3")

BUCKET_NAME = "my-application-bucket"

def lambda_handler(event, context):
    # Invocation phase
    response = s3.list_objects_v2(
        Bucket=BUCKET_NAME
    )

    return {
        "object_count": len(
            response.get("Contents", [])
        )
    }
```

The S3 client is created during initialization rather than on every invocation.

This can improve performance because the execution environment can reuse the client.

### 14.2 Invocation phase

During the invocation phase, Lambda executes your handler.

For example:

```python
def lambda_handler(event, context):
    order_id = event["order_id"]

    return {
        "order_id": order_id,
        "status": "processed"
    }
```

This handler can be executed multiple times if Lambda reuses the same execution environment.

However, each invocation receives its own event and context objects.

### 14.3 Shutdown phase

The shutdown phase occurs when Lambda terminates an execution environment.

This may happen because of:

* Environment expiration.

* Scaling decisions.

* Runtime failures.

* Function updates.

* Infrastructure lifecycle events.

External extensions can receive a shutdown notification.

You should not depend on application cleanup code always executing during shutdown. Lambda may terminate an environment without allowing arbitrary application-level cleanup to complete.

### Cold starts and warm invocations

These concepts are closely related to the execution lifecycle.

Cold start: Lambda needs to prepare a new execution environment before executing the handler.

Warm invocation: Lambda reuses an existing initialized execution environment.

A simplified comparison:

| Operation                    | Cold start    | Warm invocation |
| ---------------------------- | ------------- | --------------- |
| Create execution environment | Yes           | No              |
| Initialize runtime           | Yes           | No              |
| Import application modules   | Yes           | No              |
| Execute handler              | Yes           | Yes             |
| Reuse initialized clients    | Not initially | Potentially     |

Cold starts can affect application latency.

They are especially relevant for functions that respond directly to user requests.

### Best practices for initialization

* Initialize reusable SDK clients outside the handler.

* Avoid expensive initialization operations where possible.

* Avoid unnecessary imports.

* Reuse database connections carefully.

* Keep initialization code lightweight.

* Do not store invocation-specific state in global variables.

* Never assume an execution environment will persist indefinitely.

### Module 2 — Key Takeaways

You should now understand the main building blocks of Python-based Lambda development.

| Concept               | What you should understand                                |
| --------------------- | --------------------------------------------------------- |
| Handler               | Entry point for Lambda execution                          |
| Event                 | Input data supplied during invocation                     |
| Context               | Invocation and execution metadata                         |
| Environment variables | Function configuration                                    |
| Memory                | Available memory and associated CPU resources             |
| Timeout               | Maximum execution duration                                |
| Ephemeral storage     | Temporary filesystem storage                              |
| ZIP package           | Code and dependency deployment                            |
| Dependencies          | Python libraries required by the application              |
| Layers                | Reusable libraries and supporting resources               |
| Custom runtime        | Bringing your own runtime implementation                  |
| Container image       | Deploying Lambda through an OCI image                     |
| Extensions            | Integrating additional execution environment capabilities |
| Logging               | Capturing application execution information               |
| Lifecycle             | Initialization, invocation, and shutdown                  |

### How Module 2 connects to the next modules

The concepts introduced here become the foundation for the remaining Lambda course.

* Module 3: You will learn how to secure Lambda functions using IAM, KMS, Secrets Manager, and VPC networking.

* Module 4: You will learn how Lambda scales, manages concurrency, handles cold starts, and optimizes performance.

* Module 5: You will connect Lambda to services such as S3, SQS, SNS, DynamoDB, and EventBridge.

The most important architectural principle from this module is that Lambda functions should be designed as independently deployable, stateless application components, while reusable initialization resources and external services provide the supporting infrastructure.


---

### Module 2 Lab — Building and Deploying Python Lambda Functions with Pulumi

### 1\. Lab objectives

In this lab, you will build a Python-based AWS Lambda application, package its dependencies, configure its execution environment, and deploy it using Pulumi.

You will create a reusable deployment structure that demonstrates the main concepts covered in Module 2.

By the end, you will have:

* A Python Lambda function with a proper handler.

* A configurable Lambda execution environment.

* Environment variables managed through Pulumi.

* A Lambda execution role with appropriate IAM permissions.

* A Python dependency packaged with the application.

* A Lambda Layer containing shared dependencies.

* CloudWatch Logs integration.

* Configurable memory, timeout, and ephemeral storage.

* A deployed function that you can invoke using AWS CLI.

* A Pulumi-managed infrastructure deployment.

### 2\. Lab architecture

![AWS Lambda 関数に適切に AWS IAM のポリシーを設定しよう！ - builders.flash☆ - 変化を求めるデベロッパーを応援するウェブマガジン | AWS](https://images.openai.com/static-rsc-4/4XU5-phAfjOO6CeBrV3a36UBROCpLnatvlBLwrXyzUp99PJj_JUPMdqyMywtfGkQUR-sRKPnclSR5F0iD179Lzo5hxxTysWWoL_bUvYvJmgpGqXHcjS5IkYMGlgGPsZ_xwEJCyxFyBKGcnQz0cNBlJex70bQ6kOFF53si5yhGRIAiv0ztx2djOHXchh8mGTv?purpose=fullsize)

The architecture will contain:

| Resource        | Purpose                               |
| --------------- | ------------------------------------- |
| AWS Lambda      | Executes the Python application       |
| IAM Role        | Defines Lambda execution permissions  |
| IAM Policy      | Grants access to CloudWatch Logs      |
| Lambda Layer    | Provides reusable Python dependencies |
| CloudWatch Logs | Stores application logs               |
| Pulumi          | Provisions and manages AWS resources  |

We will use a ZIP deployment package rather than a container image because the objective is to understand Python packaging and Lambda Layers.

### 3\. Prerequisites

Install or prepare the following:

* Python 3.13 or another Python version supported by your selected Lambda runtime.

* Pulumi CLI.

* AWS CLI.

* Docker (for compatible Linux dependency packaging).

* `uv` Python package manager.

* An AWS account and configured AWS credentials.

Check the installations:

```bash
python --version
uv --version
pulumi version
aws --version
docker --version
```

Configure AWS credentials:

```bash
aws configure
```

Verify your AWS identity:

```bash
aws sts get-caller-identity
```

For this lab, we will use `eu-north-1` as the AWS Region.

### 4\. Create the project structure

Create a project directory:

```bash
mkdir lambda-module-2
cd lambda-module-2
```

Create the following structure:

```text
lambda-module-2/
│
├── app/
│   ├── app.py
│   └── requirements.txt
│
├── layer/
│   └── requirements.txt
│
├── infra/
│   ├── __main__.py
│   ├── Pulumi.yaml
│   └── Pulumi.dev.yaml
│
└── scripts/
    └── invoke.sh
```

We will separate application code from infrastructure code.

* `app/` contains the Lambda application.

* `layer/` contains dependencies shared through a Lambda Layer.

* `infra/` contains Pulumi infrastructure definitions.

* `scripts/` contains deployment and invocation scripts.

This separation is useful when applications become larger and multiple Lambda functions share infrastructure components.

### 5\. Develop the Python Lambda application

We will build a small application that receives an order event, validates it using Pydantic, and returns a structured response.

### 5.1 Define application dependencies

Create `app/requirements.txt`:

```text
pydantic>=2,<3
```

Pydantic will be installed in a Lambda Layer rather than directly in the application ZIP.

This allows us to demonstrate dependency reuse.

### 5.2 Create the Lambda handler

Create `app/app.py`:

```python
import json
import logging
import os
from pydantic import BaseModel, Field, ValidationError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Order(BaseModel):
    order_id: int
    customer: str = Field(min_length=2)
    amount: float = Field(gt=0)

# Initialization phase
APP_ENV = os.environ.get("APP_ENV", "development")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "orders-service")

def lambda_handler(event, context):

    logger.info(
        json.dumps({
            "event": "lambda_invoked",
            "service": SERVICE_NAME,
            "environment": APP_ENV,
            "request_id": context.aws_request_id
        })
    )

    try:
        order = Order.model_validate(event)

        result = {
            "order_id": order.order_id,
            "customer": order.customer,
            "amount": order.amount,
            "status": "processed"
        }

        logger.info(
            json.dumps({
                "event": "order_processed",
                "order_id": order.order_id
            })
        )

        return {
            "statusCode": 200,
            "body": json.dumps(result)
        }

    except ValidationError as exc:

        logger.warning(
            json.dumps({
                "event": "validation_failed",
                "errors": exc.errors()
            })
        )

        return {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Invalid order",
                "details": exc.errors()
            })
        }
```

There are several important concepts in this implementation.

Initialization phase:

```python
APP_ENV = os.environ.get("APP_ENV", "development")
SERVICE_NAME = os.environ.get("SERVICE_NAME", "orders-service")
```

These values are loaded when the execution environment initializes.

Handler:

```python
def lambda_handler(event, context):
```

This is the entry point configured in Lambda.

Event processing:

```python
order = Order.model_validate(event)
```

Pydantic validates the incoming event.

Context usage:

```python
context.aws_request_id
```

We use the invocation request ID for log correlation.

Structured logging:

The application generates JSON log entries that can be searched through CloudWatch Logs Insights.

### 6\. Build the Lambda Layer

Now we will package Pydantic as a reusable Lambda Layer.

Create `layer/requirements.txt`:

```text
-r ../app/requirements.txt
```

We need to install the dependencies in a Linux-compatible environment.

Because Pydantic uses native components, we will use Docker to ensure that the packages are compatible with the Lambda Linux runtime.

From the project root, execute:

```bash
mkdir -p build/layer/python
```

Install dependencies:

```bash
docker run --rm \
  --platform linux/amd64 \
  -v "$PWD:/work" \
  -w /work \
  python:3.13-slim \
  bash -c "
    pip install \
      --no-cache-dir \
      --only-binary=:all: \
      --target build/layer/python \
      -r layer/requirements.txt
  "
```

This command:

* Starts a Linux Python container.

* Mounts your project directory.

* Installs Pydantic and its dependencies.

* Places the installed packages in the Layer directory.

The resulting structure should resemble:

```text
build/
└── layer/
    └── python/
        ├── pydantic/
        ├── pydantic_core/
        ├── annotated_types/
        └── ...
```

### Package the Layer

```bash
cd build/layer

zip -r ../python-layer.zip python

cd ../..
```

The resulting archive is:

```text
build/python-layer.zip
```

Remember that `python/` must be at the root of the ZIP archive.

### 7\. Package the Lambda application

We will package the application separately from the Layer.

From the project root:

```bash
mkdir -p build/function
```

Copy the application:

```bash
cp app/app.py build/function/
```

Create the deployment ZIP:

```bash
cd build/function

zip -r ../lambda-function.zip .

cd ../..
```

Your final build directory should contain:

```text
build/
├── lambda-function.zip
└── python-layer.zip
```

The application ZIP contains `app.py`, while the Layer ZIP contains Pydantic and its dependencies.

This separation makes it possible for multiple Lambda functions to share the same Layer.

### 8\. Configure Pulumi

We will now create the infrastructure using Pulumi Python.

Navigate to the infrastructure directory:

```bash
cd infra
```

Create a virtual environment and initialize Pulumi:

```bash
uv init --bare
uv add pulumi pulumi-aws
```

Create a Pulumi project:

`infra/Pulumi.yaml`

```yaml
name: lambda-module-2
runtime:
  name: python
  options:
    virtualenv: .venv
description: Python Lambda deployment with Pulumi
```

Configure the development stack:

```bash
pulumi stack init dev
```

Set the AWS Region:

```bash
pulumi config set aws:region eu-north-1
```

Set application configuration:

```bash
pulumi config set appEnv development
pulumi config set serviceName orders-service
pulumi config set memorySize 512
pulumi config set timeout 30
pulumi config set ephemeralStorage 1024
```

Your `Pulumi.dev.yaml` will contain the corresponding stack configuration.

We are using Pulumi configuration instead of hardcoding infrastructure settings in the application.

### 9\. Create AWS infrastructure with Pulumi

Create `infra/__main__.py`.

This file will provision:

* IAM execution role.

* CloudWatch Logs permissions.

* CloudWatch Log Group.

* Lambda Layer.

* Lambda Function.

* Function configuration.

### 9.1 Import dependencies

```python
import os
import pulumi
import pulumi_aws as aws
```

### 9.2 Read Pulumi configuration

```python
config = pulumi.Config()

app_env = config.get("appEnv") or "development"
service_name = config.get("serviceName") or "orders-service"

memory_size = config.get_int("memorySize") or 512
timeout = config.get_int("timeout") or 30
ephemeral_storage = config.get_int("ephemeralStorage") or 1024
```

### 9.3 Define deployment package paths

```python
function_zip = os.path.abspath(
    "../build/lambda-function.zip"
)

layer_zip = os.path.abspath(
    "../build/python-layer.zip"
)
```

These paths point to the ZIP files created earlier.

### 9.4 Create the IAM execution role

Lambda needs an execution role to access AWS services.

```python
assume_role_policy = aws.iam.get_policy_document(
    statements=[
        aws.iam.GetPolicyDocumentStatementArgs(
            effect="Allow",
            principals=[
                aws.iam.GetPolicyDocumentStatementPrincipalArgs(
                    type="Service",
                    identifiers=["lambda.amazonaws.com"]
                )
            ],
            actions=["sts:AssumeRole"]
        )
    ]
)

lambda_role = aws.iam.Role(
    "lambda-execution-role",
    assume_role_policy=assume_role_policy.json
)
```

This trust policy allows the Lambda service to assume the role.

### 9.5 Create a CloudWatch Log Group

```python
log_group = aws.cloudwatch.LogGroup(
    "lambda-log-group",
    name=f"/aws/lambda/{service_name}",
    retention_in_days=7
)
```

We explicitly create the log group so that we can manage its retention through Pulumi.

### 9.6 Grant logging permissions

```python
logging_policy = aws.iam.RolePolicy(
    "lambda-logging-policy",
    role=lambda_role.id,
    policy=pulumi.Output.all(
        log_group.arn
    ).apply(
        lambda values: __import__("json").dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogStream",
                        "logs:PutLogEvents"
                    ],
                    "Resource": f"{values[0]}:*"
                }
            ]
        })
    )
)
```

This policy allows the function to create log streams and publish log events within its designated log group.

Unlike attaching a broad logging policy, this example scopes permissions to the application's log group.

### 9.7 Create a Lambda Layer

```python
python_layer = aws.lambda_.LayerVersion(
    "python-dependencies",
    layer_name="orders-python-dependencies",
    code=pulumi.FileArchive(layer_zip),
    compatible_runtimes=["python3.13"],
    description="Shared Pydantic dependencies"
)
```

This publishes the Python dependency package as a Lambda Layer.

### 9.8 Create the Lambda function

```python
lambda_function = aws.lambda_.Function(
    "orders-lambda",
    name=service_name,
    role=lambda_role.arn,

    runtime="python3.13",
    handler="app.lambda_handler",

    code=pulumi.FileArchive(function_zip),

    layers=[python_layer.arn],

    memory_size=memory_size,
    timeout=timeout,

    ephemeral_storage=aws.lambda_.FunctionEphemeralStorageArgs(
        size=ephemeral_storage
    ),

    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "APP_ENV": app_env,
            "SERVICE_NAME": service_name
        }
    ),

    opts=pulumi.ResourceOptions(
        depends_on=[
            logging_policy,
            log_group
        ]
    )
)
```

The important configuration values are:

| Setting           | Value                 |
| ----------------- | --------------------- |
| Runtime           | Python 3.13           |
| Handler           | app.lambda_handler    |
| Memory            | 512 MB                |
| Timeout           | 30 seconds            |
| Ephemeral storage | 1,024 MB              |
| Layer             | Pydantic dependencies |
| Environment       | development           |

### 9.9 Export deployment information

Add this to the end of `__main__.py`:

```python
pulumi.export("lambda_name", lambda_function.name)

pulumi.export("lambda_arn", lambda_function.arn)

pulumi.export("lambda_runtime", lambda_function.runtime)

pulumi.export("lambda_layer_arn", python_layer.arn)

pulumi.export("log_group_name", log_group.name)
```

These outputs make it easier to retrieve deployment information.

### 10\. Deploy the infrastructure

Make sure you are inside the `infra/` directory.

First, inspect the planned infrastructure changes:

```bash
pulumi preview
```

Pulumi should identify the resources it needs to create:

* IAM Role.

* IAM Role Policy.

* CloudWatch Log Group.

* Lambda Layer.

* Lambda Function.

Deploy:

```bash
pulumi up
```

Review the preview and confirm the deployment.

After successful deployment, inspect the outputs:

```bash
pulumi stack output
```

Retrieve the function name:

```bash
pulumi stack output lambda_name
```

Retrieve its ARN:

```bash
pulumi stack output lambda_arn
```

At this point, your Lambda function and its Layer should be deployed.

### 11\. Invoke the Lambda function

Now we will invoke the function directly using AWS CLI.

Return to the project root:

```bash
cd ..
```

Create a test event:

```bash
cat > event.json <<'EOF'
{
  "order_id": 1001,
  "customer": "John",
  "amount": 250.50
}
EOF
```

Retrieve the Lambda function name:

```bash
FUNCTION_NAME=$(cd infra && pulumi stack output lambda_name)
```

Invoke the function:

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload fileb://event.json \
  --cli-binary-format raw-in-base64-out \
  response.json
```

Inspect the response:

```bash
cat response.json
```

Expected application response:

```json
{
  "statusCode": 200,
  "body": "{\"order_id\": 1001, \"customer\": \"John\", \"amount\": 250.5, \"status\": \"processed\"}"
}
```

The exact formatting may vary.

### Test invalid input

Create another event:

```bash
cat > invalid-event.json <<'EOF'
{
  "order_id": 1002,
  "customer": "A",
  "amount": -10
}
EOF
```

Invoke the function again:

```bash
aws lambda invoke \
  --function-name "$FUNCTION_NAME" \
  --payload fileb://invalid-event.json \
  --cli-binary-format raw-in-base64-out \
  error-response.json
```

Inspect the result:

```bash
cat error-response.json
```

You should receive a validation error with HTTP-style status code `400`.

Notice that this is a successful Lambda invocation from the Lambda service's perspective: your handler caught the validation error and returned a normal response. It is not a Lambda invocation failure.

This distinction is important when designing error handling.

### 12\. Inspect CloudWatch Logs

Our function uses structured logging.

Let's inspect its logs.

Retrieve the log group:

```bash
LOG_GROUP=$(cd infra && pulumi stack output log_group_name)
```

Retrieve recent log streams:

```bash
aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime \
  --descending
```

Retrieve log events:

```bash
aws logs tail "$LOG_GROUP" --since 10m
```

You should find entries similar to:

```json
{
  "event": "lambda_invoked",
  "service": "orders-service",
  "environment": "development",
  "request_id": "..."
}
```

And:

```json
{
  "event": "order_processed",
  "order_id": 1001
}
```

This demonstrates the relationship between Python application logging and CloudWatch Logs.

### 13\. Experiment with Lambda configuration

One advantage of Pulumi is that infrastructure configuration is separate from application code.

Let's change some Lambda settings.

From the `infra/` directory:

```bash
pulumi config set memorySize 1024
pulumi config set timeout 60
pulumi config set ephemeralStorage 2048
pulumi config set appEnv production
```

Preview the changes:

```bash
pulumi preview
```

Apply them:

```bash
pulumi up
```

You have now changed:

| Configuration           | Before      | After      |
| ----------------------- | ----------- | ---------- |
| Memory                  | 512 MB      | 1,024 MB   |
| Timeout                 | 30 seconds  | 60 seconds |
| Ephemeral storage       | 1,024 MB    | 2,048 MB   |
| Application environment | development | production |

Notice that the Python application code did not need to change.

The Lambda function reads the new environment variable when its execution environment initializes.

### Inspect the deployed configuration

```bash
aws lambda get-function-configuration \
  --function-name orders-service
```

You can inspect the memory, timeout, runtime, environment variables, and Layer configuration.

### 14\. Update the application and redeploy

Let's make a small application change.

Modify the handler to include the application environment in its response:

```python
return {
    "statusCode": 200,
    "body": json.dumps({
        "order_id": order.order_id,
        "customer": order.customer,
        "amount": order.amount,
        "status": "processed",
        "environment": APP_ENV,
        "service": SERVICE_NAME
    })
}
```

Rebuild the application package:

```bash
rm -rf build/function
mkdir -p build/function

cp app/app.py build/function/

cd build/function
zip -r ../lambda-function.zip .
cd ../..
```

Deploy the updated package:

```bash
cd infra
pulumi preview
pulumi up
```

Pulumi detects the changed deployment archive and updates the Lambda function.

This illustrates an important infrastructure automation concept: application artifacts and infrastructure configuration can be managed through the same deployment workflow.

### 15\. Optional: Deploy the same application using a container image

You can also package the application as a Lambda container image.

Create `Dockerfile` in the project root:

```dockerfile
FROM public.ecr.aws/lambda/python:3.13

COPY app/requirements.txt ${LAMBDA_TASK_ROOT}/

RUN pip install \
    -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY app/app.py ${LAMBDA_TASK_ROOT}/

CMD ["app.lambda_handler"]
```

Build the image:

```bash
docker build -t orders-lambda .
```

For this alternative, the dependencies are installed directly into the image, so you do not need the separate Pydantic Layer.

The image must be pushed to ECR before deployment. You can then use Pulumi's `aws.lambda_.Function` with `package_type="Image"` and `image_uri` instead of the ZIP package and handler configuration.

This provides an alternative deployment approach for applications with more complex dependencies.

### 16\. Troubleshooting guide

| Problem                   | Possible cause                      | Solution                                             |
| ------------------------- | ----------------------------------- | ---------------------------------------------------- |
| Runtime.ImportModuleError | Incorrect handler or missing module | Verify app.py and handler configuration              |
| No module named pydantic  | Layer incorrectly packaged          | Verify python/ is at ZIP root                        |
| Unable to import module   | Incompatible native dependency      | Rebuild dependencies in compatible Linux environment |
| AccessDeniedException     | Missing IAM permissions             | Inspect the execution role                           |
| Task timed out            | Insufficient timeout                | Adjust timeout or optimize processing                |
| No CloudWatch logs        | Missing logging permissions         | Inspect IAM policy and log group                     |
| Invalid runtime           | Runtime unavailable or retired      | Select a currently supported runtime                 |
| Layer incompatible        | Runtime or architecture mismatch    | Rebuild and publish a compatible Layer               |

### 17\. Clean up AWS resources

To avoid unnecessary AWS charges, destroy the infrastructure after completing the lab.

From `infra/`:

```bash
pulumi destroy
```

Confirm the operation.

Then remove the Pulumi stack if you no longer need it:

```bash
pulumi stack rm dev
```

This removes the stack's state from Pulumi; the preceding destroy command is what removes the provisioned AWS resources.

### Final lab architecture and skills acquired

### What you built

Python application

Handler · Pydantic · Environment variables · Structured logging

Lambda ZIP

Application package

Lambda Layer

Shared dependencies

AWS Lambda

Execution role · Memory · Timeout · Ephemeral storage

Amazon CloudWatch Logs

Application logs and execution information

Infrastructure management

Pulumi Python

### Technologies covered

| Technology    | Practical application       |
| ------------- | --------------------------- |
| Python        | Lambda application          |
| Pydantic      | Input validation            |
| uv            | Dependency management       |
| Docker        | Linux-compatible packaging  |
| ZIP           | Lambda deployment package   |
| Lambda Layers | Shared dependencies         |
| IAM           | Execution permissions       |
| CloudWatch    | Application logging         |
| AWS CLI       | Invocation and inspection   |
| Pulumi        | Infrastructure provisioning |

Important scope note: The main lab implements ZIP packaging, Python dependencies, Layers, configuration, execution metadata, and logging. Custom runtimes, Extensions, and container-image deployment are introduced through the additional sections; they are alternative deployment and integration approaches rather than all being deployed simultaneously.

The next module, Module 3 — Lambda Security, IAM, and VPC Networking, will build on this infrastructure and introduce secure access to AWS services, private resources, secrets, and network connectivity.
