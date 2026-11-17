### Module 4 — Lambda Scaling, Concurrency, Performance, and Optimization

### 1\. Lambda Scaling Architecture

One of the most important characteristics of AWS Lambda is its ability to scale automatically based on incoming workloads.

Unlike traditional application servers, where you provision EC2 instances or containers and manage their capacity, Lambda automatically creates additional execution environments when more concurrent executions are required.

### 1.1 How Lambda scales

Consider a Python Lambda function that processes incoming HTTP requests through API Gateway.

Initially, one request arrives:

* Lambda receives the invocation.

* AWS selects or creates an execution environment.

* The function executes.

* The execution environment becomes available for reuse.

Now imagine 100 requests arrive simultaneously.

Lambda can create multiple execution environments to process those requests concurrently.

![Comprender el escalado de la función de Lambda - AWS Lambda](https://images.openai.com/static-rsc-4/NN-UTxd6xyINFeoPizgHb2FwUmCTkmmr3eMOsSkyu8ale1yAZS-dWZtwvpHPTO_fgOUlr-AldI_q-ogX2rT2A4eT_NNly1xloKZR55BS8amZHzxYTKjBtH4x85XX57A1BIcjHwJTR5F1aqFrbDDuIOPZEyDXC68-Vkl9aRbEghpdVfN7q4YgdrmWAlrUMhQG?purpose=fullsize)

Each execution environment generally handles one invocation at a time. Therefore, concurrent requests require multiple execution environments.

For example:

| Incoming requests | Required environments (illustrative) |
| ----------------- | ------------------------------------ |
| 1                 | 1                                    |
| 10                | 10                                   |
| 100               | 100                                  |
| 500               | 500                                  |

These numbers assume all requests overlap in execution time and that no existing capacity is available.

### 1.2 Lambda scaling behavior

Lambda scales differently depending on the invocation source.

For example:

* Synchronous invocations: Lambda scales to handle incoming requests, subject to concurrency limits and scaling rates.

* Asynchronous invocations: Lambda uses an internal queue to manage events and dispatch executions.

* SQS event source mappings: Lambda polls SQS and scales the number of concurrent function invocations based on queue workload and configured limits.

* Kinesis and DynamoDB Streams: Scaling is influenced by stream shards, partitioning, and event source mapping configuration.

An important distinction is that Lambda's scaling behavior is not identical across all event sources.

### 1.3 Lambda scaling limits

Lambda does not scale infinitely.

Scaling is controlled by:

* Regional account concurrency quotas.

* Function-level concurrency configuration.

* Event source mapping limits.

* Downstream service capacity.

* AWS scaling rates and service quotas.

For example, even if Lambda can create hundreds of execution environments, your RDS database might only support 50 simultaneous connections.

This is why application architecture must consider both Lambda capacity and downstream dependencies.

### 2\. Execution Environment Reuse

Lambda execution environments are temporary environments in which your function code runs.

An execution environment contains:

* Your application code.

* The selected runtime.

* Initialized libraries and dependencies.

* Environment variables.

* Runtime configuration.

* Memory and ephemeral storage allocations.

### 2.1 The execution lifecycle

A simplified Lambda lifecycle has three important phases:

1\. Init phase

Lambda initializes the execution environment.

This can include:

* Starting the runtime.

* Loading your Python application.

* Importing dependencies.

* Initializing global variables.

* Creating reusable clients and connections.

2\. Invoke phase

Lambda executes your handler in response to an event.

3\. Shutdown phase

Lambda eventually terminates the execution environment when it is no longer needed.

![8 best practices for optimizing Lambda functions — Cloudash Blog](https://images.openai.com/static-rsc-4/NhKX553r33Fcf-xA1_xEO0P_3lmKoD2w3sTVWKiE-yhL7ay-tXqKtNJXmu-ZtcM3R1isAxYXGNIuRwlzt9TBhNWrOvAujVFZdMuWzw6fFB7H0cfhvcIyo-NibT1YnWIdAHjchi36A_TdV-Zp0RgtgotXA4PB-urbKpQaF72sFR-zo2BeH73KUnrftEFRQ84a?purpose=fullsize)

### 2.2 Reusing execution environments

One important optimization is to initialize reusable resources outside the handler.

Consider this Python example:

```python
import json
import boto3

# Initialized during the execution environment initialization
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

Here, the S3 client is initialized outside the handler.

If Lambda reuses the execution environment, subsequent invocations can reuse the same client.

Compare that with:

```python
import boto3

def lambda_handler(event, context):
    # A new client is created for every invocation
    s3 = boto3.client("s3")

    return s3.list_buckets()
```

The second approach introduces unnecessary initialization overhead.

### 2.3 What should you reuse?

Good candidates include:

* Boto3 clients and resources.

* Database connection pools, when appropriate.

* HTTP connection pools.

* Compiled regular expressions.

* Static configuration.

* Expensive application initialization.

However, execution environment reuse is not guaranteed.

Lambda can terminate an environment at any time. Your application must never depend on local memory or temporary files being preserved across invocations.

Also, avoid storing user-specific or sensitive request data in global variables because a reused environment might serve another request.

### 3\. Concurrent Executions and Concurrency Fundamentals

Concurrency describes how many Lambda function invocations are executing simultaneously.

It is one of the most important concepts for understanding Lambda scaling and cost.

### 3.1 What is concurrency?

Suppose a Lambda function receives 100 requests.

Each request takes 2 seconds to complete.

If all 100 requests arrive at approximately the same time, Lambda may need 100 concurrent executions.

Concurrency is calculated using:

\\text{Concurrency} =
\\text{Requests per second} \\times
\\text{Average duration (seconds)}

For example:

* Incoming requests: 50 per second.

* Average execution duration: 2 seconds.

50 \\times 2 = 100100 concurrent executions

This formula is known as Little's Law in this context.

### 3.2 Understanding concurrency through examples

| Requests/second | Average duration | Concurrency |
| --------------- | ---------------- | ----------- |
| 10              | 1 second         | 10          |
| 50              | 2 seconds        | 100         |
| 100             | 3 seconds        | 300         |
| 200             | 5 seconds        | 1,000       |

Notice something important: concurrency increases when either request volume or execution duration increases.

This means improving application performance can reduce concurrency requirements.

### 3.3 Why concurrency matters

Concurrency affects:

* Lambda scaling.

* Request processing capacity.

* Throttling.

* Database connections.

* Downstream API limits.

* Application latency.

* Infrastructure costs.

For example, suppose you operate a FastAPI backend using Lambda and RDS.

If 500 Lambda environments each create a database connection, your database could become overloaded.

You must design concurrency limits around the capacity of dependent services.

### 4\. Account-Level and Function-Level Concurrency Limits

AWS Lambda provides concurrency quotas to control how many executions can run simultaneously.

There are two important concepts:

* Regional account concurrency.

* Function-level concurrency allocation.

### 4.1 Account-level concurrency

Lambda has a regional concurrency quota shared by functions in your AWS account.

For example, imagine your regional account concurrency quota is 1,000.

You have three functions:

| Function      | Concurrent executions |
| ------------- | --------------------- |
| Orders API    | 400                   |
| Payments API  | 300                   |
| Notifications | 200                   |
| Total         | 900                   |

You have 100 concurrent executions of available capacity remaining.

If additional functions need capacity, they compete for the remaining shared concurrency.

The default quota is commonly 1,000 per Region, but actual quotas can vary and may be increased.

### 4.2 Function-level concurrency

You can configure concurrency for individual functions using:

* Reserved concurrency.

* Provisioned concurrency.

These solve different problems, which we will explore shortly.

### 4.3 Unreserved concurrency

Unreserved concurrency represents the account's available shared concurrency pool after reserved concurrency allocations.

For example:

* Account quota: 1,000.

* Function A reserved concurrency: 200.

* Function B reserved concurrency: 300.

The remaining unreserved concurrency is:

1000 - 200 - 300 = 500

Other functions can use this shared pool.

One important operational consideration: reserving concurrency reduces the capacity available to other functions, even when the reserved function is idle.

### 5\. Reserved Concurrency and Its Use Cases

Reserved concurrency guarantees a concurrency allocation for a particular Lambda function and establishes its maximum concurrency.

It has two purposes:

* Reserve capacity for a function.

* Limit the maximum number of simultaneous executions.

### 5.1 Example

Imagine an application with three functions:

* Payments.

* Orders.

* Notifications.

You want to protect the payment system from being starved by notification processing.

You configure:

| Function      | Reserved concurrency |
| ------------- | -------------------- |
| Payments      | 200                  |
| Orders        | 300                  |
| Notifications | 100                  |

The payment function has an allocation of 200 concurrent executions.

It can scale up to that limit without competing with unreserved functions for those executions.

However, if 250 simultaneous requests arrive, approximately 50 cannot execute immediately and may be throttled.

Reserved concurrency does not guarantee that all 200 execution slots are constantly running. It guarantees an allocation and imposes a maximum.

### 5.2 When should you use reserved concurrency?

Useful scenarios include:

* Protecting critical business functions.

* Preventing one function from consuming all available concurrency.

* Limiting database connections.

* Protecting external APIs from excessive requests.

* Controlling background processing workloads.

### 5.3 Setting reserved concurrency with AWS CLI

```bash
aws lambda put-function-concurrency \
    --function-name payments-function \
    --reserved-concurrent-executions 200
```

To remove the reservation:

```bash
aws lambda delete-function-concurrency \
    --function-name payments-function
```

### 5.4 Important distinction

Reserved concurrency is not the same as provisioned concurrency.

Reserved concurrency controls capacity allocation and maximum execution concurrency.

Provisioned concurrency prepares execution environments in advance to reduce initialization latency.

### 6\. Provisioned Concurrency and Initialization Optimization

Provisioned concurrency allows you to prepare Lambda execution environments before incoming requests arrive.

This is particularly useful for latency-sensitive applications.

### 6.1 The problem with on-demand initialization

Imagine a customer opens an e-commerce application.

The API invokes a Lambda function that:

* Starts a Python runtime.

* Imports FastAPI-related libraries.

* Initializes application dependencies.

* Creates service clients.

* Executes the request.

The first invocation might experience additional initialization latency.

This is commonly associated with a cold start.

### 6.2 How provisioned concurrency works

With provisioned concurrency, AWS initializes a configured number of execution environments in advance.

![How Smartsheet reduced latency and optimized costs in their serverless architecture | AWS Architecture Blog](https://images.openai.com/static-rsc-4/BsycUCBrsVLchUe4nncgv7VucLbpPjuHPHrtdh4eOfW23fmbJSIZ2Tb2jWA2KczzGz4HHmp6qBMkZiWXrlD9qfci6zZ-rL9xKx7QOQM5Zb_DfXwvyYEF1EBladA4HBUoZT6k4GITTExp4rlVRGS-beRPt_im4oNUmd5om1FvE9x75Wc0_RB0Oae33qLMpthp?purpose=fullsize)

For example, configure 20 provisioned environments.

When traffic arrives, Lambda can route requests to these already initialized environments.

This significantly reduces initialization-related latency for requests served by provisioned capacity.

### 6.3 Configure provisioned concurrency

Provisioned concurrency is configured against a published function version or an alias, not directly against the mutable `$LATEST` version.

First, publish a version:

```bash
aws lambda publish-version \
    --function-name payments-function
```

Then configure an alias:

```bash
aws lambda create-alias \
    --function-name payments-function \
    --name production \
    --function-version 3
```

Configure provisioned concurrency:

```bash
aws lambda put-provisioned-concurrency-config \
    --function-name payments-function \
    --qualifier production \
    --provisioned-concurrent-executions 20
```

Check its status:

```bash
aws lambda get-provisioned-concurrency-config \
    --function-name payments-function \
    --qualifier production
```

Provisioned concurrency has additional costs, even when the provisioned environments are not processing requests.

### 6.4 Reserved vs. provisioned concurrency

| Feature                      | Reserved concurrency           | Provisioned concurrency       |
| ---------------------------- | ------------------------------ | ----------------------------- |
| Reserves capacity            | Yes                            | Uses allocated capacity       |
| Limits maximum concurrency   | Yes                            | No, not by itself             |
| Pre-initializes environments | No                             | Yes                           |
| Reduces cold starts          | No                             | Yes, for provisioned capacity |
| Additional capacity cost     | No separate reservation charge | Yes                           |
| Typical use case             | Protecting downstream systems  | Low-latency applications      |

A function can use both reserved and provisioned concurrency, provided the configurations are compatible.

### 7\. Cold Starts and Warm Execution Environments

Cold starts are one of the most discussed performance characteristics of serverless applications.

### 7.1 What is a cold start?

A cold start occurs when Lambda needs to initialize a new execution environment before executing your function.

For example, a Python function might require:

* Creating a new execution environment.

* Starting the Python runtime.

* Loading application code.

* Importing dependencies.

* Initializing application components.

All this initialization adds latency before your handler starts processing the event.

### 7.2 Cold start vs. warm invocation

![AWS Lambda Cold Starts vs Warm Starts — What Really Happens Behind the Scenes | by Content Tech | Medium](https://images.openai.com/static-rsc-4/L1obeKGA3DaAivlKSMlPn6UAqMr-dEY7XrHBPgANmE53HeCsxCmbSQBTIDelrLZ_afq1UV8hqoVk3NSVIhoFCzKKpso0RKeVGNIuPx33xLOm6K3V84O-M5CGiWo-K0hZYpO9_9pzCrbSwVIFGYJN44YDeS9aMTrUrXmdndImiDSw77ZDACmwZXk8bqTPCek_?purpose=fullsize)

Cold start

New environment, runtime initialization, dependency loading, then handler execution.

![Understanding Cold and Warm Starts in AWS Lambda | Abdullah jiroudi posted on the topic | LinkedIn](https://images.openai.com/static-rsc-4/n7aJpE9FmRmQWw6wMESW3xAupOyK46hbUrDLaQPnLv_Xc58iZkJoakunyYuy-7DKa_IPQMUFCNR48E9Sp1LsiIq4j7kHqq0PEEKG7fAwnMXC7GMXW-ObVjNd4rZkKJNqC4E0lpJxScCAxloVVzdsmZqTEe3gioj2K4MzCWGpumXN9y2Q0i69AC2n_JZ6uw--?purpose=fullsize)

Warm invocation

Existing environment is reused, so initialization is generally skipped.

Consider this example:

```python
import time

print("Initializing application...")

time.sleep(2)

def lambda_handler(event, context):
    return {
        "statusCode": 200,
        "body": "Hello from Lambda"
    }
```

The two-second initialization happens when the execution environment initializes, not on every invocation.

If Lambda reuses that environment, subsequent invocations avoid repeating the initialization.

### 7.3 Factors affecting cold starts

* Runtime selection.

* Deployment package size.

* Number of dependencies.

* Initialization code complexity.

* Memory allocation.

* VPC networking configuration.

* External service initialization.

* Container image size.

### 7.4 Cold start optimization techniques

You can reduce initialization latency by:

* Reducing unnecessary dependencies.

* Moving reusable initialization outside the handler.

* Using lightweight libraries.

* Avoiding expensive operations during initialization.

* Optimizing container images and deployment packages.

* Using provisioned concurrency when predictable low latency is required.

* Considering SnapStart where supported.

One important point: a warm environment is not permanent. Lambda controls its lifecycle, and you should never assume an invocation will always be warm.

### 8\. Lambda SnapStart and Supported Runtime Considerations

Lambda SnapStart is an optimization that reduces cold-start latency by creating a snapshot of an initialized execution environment.

Instead of initializing every new environment from scratch, Lambda can restore environments from a previously created snapshot.

### 8.1 How SnapStart works

The process is approximately:

* You enable SnapStart for a function.

* You publish a function version.

* Lambda initializes the function.

* Lambda creates and caches a snapshot.

* New execution environments can be restored from that snapshot.

![Aws Lambda Function Execution History at Ebony Butters blog](https://images.openai.com/static-rsc-4/AL88kY94aQGCDHwc-yJqbtte2tbw6k873F6aNNXVO4q3_BfM6QgPl_3J6Id47e0f-lwmBZkhQau9sRTC-yuEY8K9ejxB-hPEQuObP0WZTFeKTI-PFOvdJsJqcvUecbKQ9QOtsvDRZTtwdMJGtnZU5uhD3_nXuWGuvFbBJd0MHEbHPm3rWB6jE1nqDx39xeY3?purpose=fullsize)

### 8.2 Supported runtimes

According to AWS documentation, SnapStart supports:

| Runtime                  | Support |
| ------------------------ | ------- |
| Java 11 and later        | Yes     |
| Python 3.12 and later    | Yes     |
| .NET 8 and later         | Yes     |
| Node.js managed runtimes | No      |
| Ruby managed runtimes    | No      |
| OS-only runtimes         | No      |

SnapStart also has deployment and configuration limitations:

* It requires published function versions.

* It cannot be combined with provisioned concurrency on the same function.

* It does not support EFS.

* It does not support ephemeral storage greater than 512 MB.

AWS also supports SnapStart with corresponding Lambda base images for supported runtimes. Check the current runtime and deployment-specific requirements before enabling it. AWS Lambda +1

### 8.3 SnapStart and Python

Since this course uses Python, SnapStart is particularly relevant.

For example, a Python 3.12+ function can benefit from SnapStart when it has expensive initialization operations.

However, you must consider initialization state carefully.

Avoid assuming that values generated during initialization remain unique after restoring a snapshot.

Potentially problematic examples include:

* Random identifiers.

* Timestamps.

* Temporary credentials.

* Open network connections.

* Unique session identifiers.

Use appropriate runtime hooks and reinitialize resources that must be unique after restoration.

### 8.4 SnapStart vs. provisioned concurrency

| Characteristic                   | SnapStart            | Provisioned concurrency       |
| -------------------------------- | -------------------- | ----------------------------- |
| Initialization optimization      | Snapshot and restore | Pre-initialized environments  |
| Reduces cold starts              | Yes                  | Yes, for provisioned capacity |
| Additional capacity provisioning | No                   | Yes                           |
| Supported runtimes               | Selected runtimes    | Broad runtime support         |
| Can be used together             | No                   | No                            |

Practical recommendation: For Python Lambda applications, evaluate SnapStart first when using a supported runtime. Use provisioned concurrency when you need more predictable latency and are willing to pay for pre-initialized capacity.

### 9\. Memory Allocation and CPU Performance

Lambda memory configuration affects more than memory consumption.

It also influences the CPU resources allocated to your function.

### 9.1 Memory and CPU relationship

Lambda allows you to configure memory between 128 MB and 10,240 MB.

As memory allocation increases, Lambda provides proportionally more CPU resources.

This means increasing memory can make CPU-intensive applications execute significantly faster.

For example:

| Memory    | Relative CPU capacity               |
| --------- | ----------------------------------- |
| 128 MB    | Lowest                              |
| 512 MB    | Higher                              |
| 1,024 MB  | Higher                              |
| 1,769 MB  | Approximately one vCPU equivalent   |
| 3,538 MB  | Approximately two vCPU equivalents  |
| 7,076 MB  | Approximately four vCPU equivalents |
| 10,240 MB | Approximately six vCPU equivalents  |

These CPU figures are approximate; actual CPU allocation and performance depend on the execution environment.

### 9.2 Example: Image processing

Imagine a Lambda function that processes uploaded images.

At 512 MB:

* Image processing takes 8 seconds.

* CPU resources are relatively limited.

At 2,048 MB:

* Processing might take 3 seconds.

* More CPU resources are available.

Although the function uses more memory, its shorter execution time might make the overall cost comparable or even lower.

### 9.3 Memory tuning

You should benchmark different memory configurations instead of automatically choosing the smallest possible allocation.

A useful tool is the AWS Lambda Power Tuning project, which helps compare performance and cost at different memory settings.

Useful metrics include:

* Duration.

* Memory usage.

* Billed duration.

* Cost per invocation.

* CPU-bound processing time.

Official reference: [AWS Lambda Power Tuning](https://github.com/alexcasalboni/aws-lambda-power-tuning?utm_source=chatgpt.com).

### 10\. Timeout Configuration and Execution Optimization

Every Lambda function has a maximum execution duration.

The timeout determines how long Lambda allows an invocation to run before terminating it.

### 10.1 Lambda timeout

The configurable timeout range is:

* Minimum: 1 second.

* Maximum: 900 seconds (15 minutes).

For example:

```bash
aws lambda update-function-configuration \
    --function-name image-processor \
    --timeout 60
```

This configures a 60-second timeout.

### 10.2 Choosing the correct timeout

Consider different application workloads:

| Workload                | Example timeout |
| ----------------------- | --------------- |
| Simple API request      | 5–10 seconds    |
| Database operation      | 10–30 seconds   |
| Image processing        | 30–120 seconds  |
| Document processing     | 60–300 seconds  |
| Long-running batch task | 300–900 seconds |

These are starting points, not AWS recommendations or universal limits.

### 10.3 Why timeout configuration matters

Suppose your Lambda function calls an external API.

The API occasionally takes 40 seconds to respond.

If your Lambda timeout is 10 seconds, the invocation will fail before the external API responds.

You should configure:

* Connection timeout.

* Read timeout.

* Lambda timeout.

* Retry behavior.

* Maximum execution duration.

For example:

```python
import boto3
from botocore.config import Config

config = Config(
    connect_timeout=3,
    read_timeout=10,
    retries={
        "max_attempts": 2,
        "mode": "standard"
    }
)

s3 = boto3.client("s3", config=config)

def lambda_handler(event, context):
    response = s3.list_buckets()

    return {
        "bucket_count": len(response["Buckets"])
    }
```

### 10.4 Execution optimization

Other important techniques include:

* Avoiding unnecessary network calls.

* Reducing serialization and deserialization overhead.

* Processing batches instead of individual records when appropriate.

* Using efficient data structures.

* Avoiding unnecessary dependency imports.

* Optimizing database queries.

* Using asynchronous I/O where it improves workload efficiency.

* Moving long-running workflows to Step Functions or other suitable compute services.

Remember that Lambda's 15-minute execution limit makes it unsuitable for some long-running workloads.

### 11\. Ephemeral Storage Optimization

Lambda provides temporary local storage through the `/tmp` directory.

This storage is useful when your function needs to download, process, or temporarily store files.

### 11.1 Understanding Lambda ephemeral storage

By default, Lambda provides 512 MB of ephemeral storage.

You can configure it between:

* Minimum: 512 MB.

* Maximum: 10,240 MB (10 GB).

The storage is available during the execution environment's lifecycle.

For example, imagine a Lambda function that processes uploaded PDF documents.

Its workflow might look like this:

* Receive an S3 event.

* Download the PDF from S3.

* Store the PDF in `/tmp`.

* Extract text from the document.

* Generate a processed document.

* Upload the result to S3.

* Return the processing result.

### 11.2 Python example

```python
import boto3
import os

s3 = boto3.client("s3")

def lambda_handler(event, context):

    bucket = event["bucket"]
    key = event["key"]

    local_path = f"/tmp/{os.path.basename(key)}"

    s3.download_file(
        bucket,
        key,
        local_path
    )

    file_size = os.path.getsize(local_path)

    return {
        "file": key,
        "size": file_size
    }
```

### 11.3 Configuring ephemeral storage

Using AWS CLI:

```bash
aws lambda update-function-configuration \
    --function-name document-processor \
    --ephemeral-storage '{"Size": 2048}'
```

This allocates 2 GB of temporary storage.

### 11.4 Important considerations

* `/tmp` is not permanent storage.

* Different execution environments have separate temporary storage.

* Data might remain available when an environment is reused, but you must not rely on it.

* Clean up temporary files when appropriate.

* Avoid writing sensitive information to temporary storage unnecessarily.

* Use S3 or another persistent storage service for durable data.

When should you increase ephemeral storage?

* Large image processing.

* PDF and document conversion.

* Machine learning inference.

* Temporary file extraction.

* Video processing.

* Large data transformations.

### 12\. Connection Reuse and Database Connection Management

One of the biggest challenges when scaling Lambda applications is managing connections to databases and external services.

Remember that Lambda can create many execution environments simultaneously.

If each environment creates a new database connection, your database can become overloaded.

### 12.1 The connection explosion problem

Imagine your application uses:

* Lambda.

* Amazon RDS PostgreSQL.

* API Gateway.

Your Lambda function scales to 500 concurrent executions.

Each execution environment establishes one database connection.

Your database could receive 500 simultaneous connections.

![RDS Proxy. wfv svvsvs | by Michael Chidiogo Okoli | Medium](https://images.openai.com/static-rsc-4/Ubrb3xDH6dwxrkb2UNNV48O3bsIYw_hkNOU-CNv95it0VzMIZK6OzTrs4B4xCqcN_AIF1lHTiT9Z2ScOGnRr9KFgadrxCt47tqGdjm9CV36uJbor9meaPtFG-Ywx4qH1vQNTPmB5C0WAbrPwhTpkn8ZL8SSPFcRrThKtz1VdAOS8kGFVxH9prAtagbqlqkUs?purpose=fullsize)

This can cause:

* Database connection exhaustion.

* Increased connection establishment latency.

* Database CPU and memory pressure.

* Failed requests.

* Connection timeout errors.

### 12.2 Reuse database connections

For Python applications, initialize database clients or connection pools outside the handler where appropriate.

For example:

```python
import psycopg

connection = psycopg.connect(
    "host=db.example.com "
    "dbname=app "
    "user=appuser "
    "password=secret"
)

def lambda_handler(event, context):

    with connection.cursor() as cursor:
        cursor.execute("SELECT NOW()")
        result = cursor.fetchone()

    return {
        "database_time": str(result[0])
    }
```

This illustrates connection reuse, but production applications need additional safeguards:

* Detect broken connections.

* Reconnect when necessary.

* Use appropriate connection timeouts.

* Avoid concurrent use of a connection that is not thread-safe.

* Avoid retaining stale connections indefinitely.

Never hardcode database credentials. Use Secrets Manager or another secure configuration mechanism.

### 12.3 Amazon RDS Proxy

![AWS RDS new features circa Dec'2019](https://images.openai.com/static-rsc-4/ZTl7ybkFtDdMUFE7IlI0KGmQwE2PDYvtCsjnf93tUzyjV6nhF6E0pc5lUOf389SuALYYsyDRCpf6Vgj71uKQIn0wALt6JTOH4DLEhOQ5qHcagPc43NtK5pcxxOuIe1o9c6OU6hVgNM2r8yR9B8iK2MRLW10fXJqdb_dpA5p45Zsgzbr4h1TF6Er8_Td8A_Kb?purpose=fullsize)

Amazon RDS Proxy helps manage database connections from applications that scale dynamically.

Instead of allowing every Lambda execution environment to establish an independent database connection to RDS, applications connect through RDS Proxy.

RDS Proxy can:

* Pool database connections.

* Reuse established connections.

* Reduce database connection overhead.

* Help manage connection spikes.

* Improve database availability during certain failover scenarios.

Example architecture:

```text
API Gateway
     |
     v
Lambda Functions
     |
     v
Amazon RDS Proxy
     |
     v
Amazon RDS PostgreSQL
```

### 12.4 HTTP connection reuse

Connection reuse is also important when calling external APIs.

For example:

```python
import requests

session = requests.Session()

def lambda_handler(event, context):

    response = session.get(
        "https://api.example.com/products",
        timeout=10
    )

    return {
        "statusCode": response.status_code
    }
```

The session can reuse HTTP connections within the same execution environment.

This reduces repeated TCP and TLS connection establishment overhead.

Important: Connection reuse is an optimization, not a guarantee that connections remain valid. Your application must handle connection failures and reconnections.

### 13\. Lambda Performance Tuning

Performance tuning involves improving execution speed, reducing latency, controlling resource consumption, and optimizing costs.

A well-designed Lambda function should not simply execute successfully. It should execute efficiently under realistic workloads.

### 13.1 Important performance metrics

| Metric               | Meaning                                         |
| -------------------- | ----------------------------------------------- |
| Duration             | Time spent executing a function                 |
| Init Duration        | Initialization time associated with cold starts |
| ConcurrentExecutions | Number of simultaneous executions               |
| Throttles            | Requests rejected due to concurrency limits     |
| Errors               | Failed function executions                      |
| Max Memory Used      | Maximum memory consumed during execution        |
| IteratorAge          | Processing delay for stream-based event sources |

### 13.2 Performance optimization strategies

1\. Optimize initialization

Avoid unnecessary dependency imports and expensive startup operations.

2\. Optimize memory

Benchmark different memory allocations to find the best performance-to-cost ratio.

3\. Optimize network communication

Reuse connections, minimize unnecessary API requests, and choose appropriate VPC networking configurations.

4\. Optimize database access

Use connection pooling, RDS Proxy where appropriate, and efficient SQL queries.

5\. Optimize application code

Use efficient algorithms, avoid unnecessary serialization, and reduce redundant computations.

6\. Optimize deployment packages

Remove unused dependencies and avoid excessively large deployment artifacts.

7\. Optimize concurrency

Configure reserved and provisioned concurrency based on actual application requirements.

### 13.3 Use Lambda Power Tuning

A useful approach is to benchmark your function at different memory allocations.

For example:

| Memory   | Execution duration |
| -------- | ------------------ |
| 512 MB   | 4.8 seconds        |
| 1,024 MB | 2.7 seconds        |
| 2,048 MB | 1.5 seconds        |
| 3,008 MB | 1.1 seconds        |

These are illustrative numbers.

You should compare the actual execution cost at each memory allocation rather than automatically selecting the fastest configuration.

### 13.4 Load testing

Performance should be evaluated under realistic traffic.

Useful tools include:

* AWS Distributed Load Testing.

* Locust.

* k6.

* AWS Lambda Power Tuning.

For an API Gateway and Lambda application, measure:

* Requests per second.

* Average latency.

* P95 and P99 latency.

* Error rate.

* Concurrent executions.

* Throttling.

* Database connections.

* Cost per request.

### 14\. Cost Optimization and Concurrency Management

Lambda pricing is primarily based on the number of requests and the compute resources consumed.

Memory allocation and execution duration are particularly important because they influence compute cost.

### 14.1 Lambda pricing components

The main pricing components include:

* Request charges.

* Duration charges.

* Provisioned concurrency charges, when used.

* Additional charges for features such as SnapStart caching and restoration.

* Other associated AWS services, such as CloudWatch Logs, API Gateway, and NAT Gateway.

Pricing varies by architecture, Region, and applicable free-tier or pricing-plan benefits.

Official reference: [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/?utm_source=chatgpt.com).

### 14.2 Memory and duration affect cost

Consider two configurations:

| Configuration | Memory   | Duration  |
| ------------- | -------- | --------- |
| A             | 512 MB   | 4 seconds |
| B             | 2,048 MB | 1 second  |

Both use approximately the same amount of memory-time per invocation:

512 \\times 4 = 20482048 \\times 1 = 2048

This simplified comparison illustrates why allocating more memory can sometimes improve performance without increasing compute cost substantially.

Actual billing also depends on architecture, duration billing increments, and pricing rules.

### 14.3 Cost optimization techniques

* Reduce unnecessary function execution.

* Optimize memory allocation.

* Reduce execution duration.

* Avoid unnecessary provisioned concurrency.

* Use appropriate invocation patterns.

* Batch events when appropriate.

* Reduce excessive logging.

* Avoid unnecessary network traffic.

* Use Graviton-based Lambda architectures when compatible.

* Monitor requests and duration across functions.

### 14.4 Monitor Lambda costs

Useful AWS tools include:

* AWS Cost Explorer.

* AWS Budgets.

* Cost and Usage Reports.

* CloudWatch metrics.

* Lambda Insights.

You should monitor both Lambda costs and downstream infrastructure costs.

For example, a Lambda function might be inexpensive, but excessive NAT Gateway data processing or database resources could make the overall architecture expensive.

### 15\. Throttling, Backpressure, and Scaling Behavior

Throttling happens when Lambda cannot accept additional invocations because a concurrency or scaling limit has been reached.

It is essential to understand throttling because it affects application reliability.

### 15.1 What causes throttling?

Common causes include:

* Account concurrency exhaustion.

* Reserved concurrency limits.

* Function scaling-rate limits.

* Requests-per-second limits.

* Provisioned concurrency exhaustion combined with unavailable on-demand capacity.

* Downstream service protection mechanisms.

### 15.2 Example

Suppose your Lambda function has reserved concurrency of 100.

Now imagine 150 requests arrive simultaneously.

| Requests     | Result                               |
| ------------ | ------------------------------------ |
| First 100    | Can execute                          |
| Remaining 50 | Throttled if capacity is unavailable |

The throttled requests do not simply disappear in every invocation model. Their subsequent behavior depends on the invocation source.

For example:

| Invocation source                  | Throttling behavior                                                                                          |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| API Gateway synchronous invocation | Client may receive an HTTP 429 response                                                                      |
| Direct synchronous invocation      | Caller receives a throttling exception                                                                       |
| Asynchronous invocation            | Lambda retries according to asynchronous invocation behavior and event age settings                          |
| SQS event source mapping           | Messages remain in the queue and are retried after visibility timeout, subject to polling and retry behavior |
| Kinesis/DynamoDB Streams           | Processing is delayed, and iterator age can increase                                                         |

This distinction is extremely important when designing event-driven applications.

### 15.3 Understanding backpressure

Backpressure is a mechanism that prevents a system from overwhelming downstream components.

Imagine this architecture:

```text
API Gateway
     |
     v
Lambda
     |
     v
Amazon SQS
     |
     v
Worker Lambda
     |
     v
RDS PostgreSQL
```

Suppose the database can safely handle only 50 concurrent connections.

Instead of allowing Lambda to create hundreds of simultaneous database operations, you can control worker concurrency.

For example:

* Configure worker Lambda reserved concurrency to 40.

* Use SQS to buffer incoming jobs.

* Allow the worker to process messages at a controlled rate.

* Monitor queue depth and message age.

![Introducing maximum concurrency of AWS Lambda functions when using Amazon SQS as an event source | AWS Compute Blog](https://images.openai.com/static-rsc-4/nmYBXkEmXXqpcyLzf6NwaFApSTkEzR6FdRDpitaxMQVzuz4k7BL0X2-4UKedidnqvU6PbX_1yndRygXMciTtp88ysDTmj0SD36WNOEXRyiUuApcDIabpOw4i29wjAZLDpFb-lad_64ibVQuQiwM8bCO0paEY5RtES0M-YoxGj1lPeKtY0Kc_OPcNd3PqnFDF?purpose=fullsize)

This creates a buffer between incoming workloads and downstream processing.

### 15.4 Lambda scaling rate

Lambda also has a scaling-rate limit separate from its total concurrency quota.

According to current AWS documentation, for each function in a Region, the on-demand concurrency scaling rate is up to 1,000 additional execution environments every 10 seconds. This is a scaling-rate limit, not a guarantee that every workload immediately receives that capacity. AWS Lambda +1

For sudden traffic spikes, you should consider:

* Provisioned concurrency.

* SQS buffering.

* Reserved concurrency.

* Client-side retry strategies.

* Exponential backoff with jitter.

* Downstream service capacity.

* Load shedding where appropriate.

### 15.5 Retry strategies and exponential backoff

A common retry strategy is exponential backoff.

For example:

| Attempt | Waiting time |
| ------- | ------------ |
| 1       | 1 second     |
| 2       | 2 seconds    |
| 3       | 4 seconds    |
| 4       | 8 seconds    |

Add random jitter to prevent many clients from retrying simultaneously.

Be careful not to retry non-idempotent operations blindly. For example, retrying a payment request without an idempotency mechanism could result in duplicate charges.

### 16\. Putting Everything Together: Production Scaling Architecture

Let's combine the concepts into a realistic serverless architecture.

Imagine you're building an e-commerce application with the following requirements:

* Customers submit orders through an API.

* Orders are processed asynchronously.

* Payment operations must be reliable.

* Database connections must remain controlled.

* The application must scale during traffic spikes.

* Critical API operations should have low latency.

![Guidance for Designing Resilient Applications with Amazon Aurora and Amazon RDS Proxy](https://images.openai.com/static-rsc-4/XXFTDBiraW6L44wZNnXe3ogJLt0S09FV_EuhAbwgADzpou8iuj2pimEM5la7mFKLvrgde7PE1OCc7AzUa4a1woGbhfYPh4pAniiA5Svg56LnQSE42HymvKK_v20doHc8Z_0Z-IHrsrd19VrKcMecOyF8Kdku52Pq3X9IPYKOpkBN_hK1FORUkmrlHdH9wk0N?purpose=fullsize)

### Architecture components

| Component      | Responsibility                  |
| -------------- | ------------------------------- |
| API Gateway    | Receives customer requests      |
| Lambda API     | Validates and accepts orders    |
| SQS            | Buffers order-processing jobs   |
| Worker Lambda  | Processes orders asynchronously |
| RDS Proxy      | Manages database connections    |
| RDS PostgreSQL | Stores order information        |
| SNS            | Publishes order notifications   |
| CloudWatch     | Monitors performance and errors |

### Recommended scaling configuration

For this architecture:

* Use reserved concurrency to protect critical functions.

* Use provisioned concurrency for latency-sensitive API functions if necessary.

* Configure worker concurrency according to database capacity.

* Use SQS to absorb traffic spikes.

* Reuse SDK clients and database connections.

* Optimize Lambda memory based on benchmarking.

* Monitor queue depth, concurrency, throttling, and execution duration.

* Configure retries and dead-letter queues for failed processing.

### Infrastructure automation with Pulumi

This architecture can eventually be deployed using Pulumi Python.

You would manage:

* Lambda functions and configurations.

* Execution roles and IAM policies.

* Reserved and provisioned concurrency.

* SQS queues and event source mappings.

* SNS topics and subscriptions.

* RDS Proxy and database networking.

* CloudWatch alarms and dashboards.

### Module 4 — Key Concepts to Remember

| Concept                 | Main takeaway                                                             |
| ----------------------- | ------------------------------------------------------------------------- |
| Automatic scaling       | Lambda creates execution environments as demand increases.                |
| Environment reuse       | Reuse initialized clients and resources.                                  |
| Concurrency             | Number of simultaneously executing invocations.                           |
| Reserved concurrency    | Reserves capacity and limits maximum concurrency.                         |
| Provisioned concurrency | Pre-initializes execution environments.                                   |
| Cold starts             | Additional initialization latency.                                        |
| SnapStart               | Restores initialized environments from snapshots.                         |
| Memory allocation       | Controls memory and influences CPU resources.                             |
| Timeout                 | Maximum execution duration, up to 15 minutes.                             |
| Ephemeral storage       | Temporary /tmp storage, up to 10 GB.                                      |
| Connection reuse        | Reduces repeated connection establishment.                                |
| Performance tuning      | Optimize memory, duration, dependencies, and networking.                  |
| Cost optimization       | Balance execution time, memory, and concurrency.                          |
| Throttling              | Occurs when available invocation capacity or scaling limits are exceeded. |
| Backpressure            | Protects downstream services from excessive workloads.                    |

### Recommended AWS documentation

For deeper technical reference, these are particularly useful:

* [Understanding Lambda concurrency](https://docs.aws.amazon.com/lambda/latest/dg/lambda-concurrency.html?utm_source=chatgpt.com).

* [Lambda execution environment lifecycle](https://docs.aws.amazon.com/lambda/latest/dg/lambda-runtime-environment.html?utm_source=chatgpt.com).

* [Provisioned concurrency](https://docs.aws.amazon.com/lambda/latest/dg/provisioned-concurrency.html?utm_source=chatgpt.com).

* [Lambda SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html?utm_source=chatgpt.com).

* [Configuring ephemeral storage](https://docs.aws.amazon.com/lambda/latest/dg/configuration-ephemeral-storage.html?utm_source=chatgpt.com).

The most important architectural lesson: Lambda's automatic scaling does not mean your entire application scales automatically. Your databases, APIs, queues, and other dependencies must be able to handle the workload. Designing concurrency limits, buffering, connection management, and backpressure is what turns a simple Lambda application into a reliable production system.

Next, Module 5 will build on these concepts by exploring Lambda event sources, triggers, and integrations with S3, SQS, SNS, DynamoDB Streams, EventBridge, and API Gateway.
