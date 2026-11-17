### Module 6 — Lambda Invocation, Asynchronous Processing, and Reliability

AWS Lambda · Intermediate to Advanced · Python · Event-driven architectures

### 1\. Introduction

So far, we have explored Lambda functions, Python development, security, networking, scaling, concurrency, and event sources.

Now we need to understand a critical part of serverless architecture: how Lambda receives work, processes events, handles failures, and guarantees reliable application behavior.

In production systems, invoking a Lambda function is not simply a matter of calling a Python handler. Events can be delayed, duplicated, retried, processed out of order, or lost if failure-handling mechanisms are incorrectly configured.

Consider an e-commerce application:

* A customer places an order.

* The application publishes an order event.

* The event is delivered to Lambda.

* Lambda processes the order.

* The application updates its database.

* If processing fails, the event must be retried or sent to a failure-handling destination.

A reliable architecture must account for every step.

In this module, we will explore three fundamental invocation models, retry mechanisms, event processing guarantees, idempotency, dead-letter queues, distributed processing, and workflow orchestration.

### 2\. Synchronous Invocation and Request-Response Behavior

Synchronous invocation is the simplest Lambda invocation model.

The caller invokes a Lambda function and waits for its response.

The execution flow is:

Client / Application

HTTP request or SDK invocation

Invoke

AWS Lambda

Execute Python handler

Return result

Client / Application

Receives response or error

### 2.1 How synchronous invocation works

The caller sends an event to Lambda.

Lambda executes the function and returns the execution result to the caller.

For example, imagine a FastAPI application invoking Lambda to calculate an order's shipping cost.

The Lambda function:

```python
import json

def handler(event, context):
    weight = event["weight"]
    distance = event["distance"]

    shipping_cost = weight * distance * 0.05

    return {
        "statusCode": 200,
        "body": json.dumps({
            "shipping_cost": shipping_cost
        })
    }
```

The caller sends:

```json
{
  "weight": 10,
  "distance": 100
}
```

Lambda returns:

```json
{
  "statusCode": 200,
  "body": "{\"shipping_cost\": 50.0}"
}
```

The caller receives the result and continues its execution.

### 2.2 Lambda synchronous invocation APIs

You can invoke Lambda synchronously using the AWS SDK, AWS CLI, API Gateway, or a Lambda function URL.

Using Boto3:

```python
import boto3
import json

client = boto3.client("lambda")

response = client.invoke(
    FunctionName="shipping-calculator",
    InvocationType="RequestResponse",
    Payload=json.dumps({
        "weight": 10,
        "distance": 100
    })
)

result = json.loads(response["Payload"].read())

print(result)
```

The important parameter is:

```python
InvocationType="RequestResponse"
```

Lambda supports three invocation types:

| Invocation type | Behavior                                                                       |
| --------------- | ------------------------------------------------------------------------------ |
| RequestResponse | Synchronous execution                                                          |
| Event           | Asynchronous invocation                                                        |
| DryRun          | Validates invocation permissions and parameters without executing the function |

### 2.3 Error handling

With synchronous invocation, Lambda returns execution errors to the caller.

For example:

* Invalid input.

* Unhandled Python exceptions.

* Function timeouts.

* Throttling.

* Service-side invocation failures.

The caller is responsible for deciding whether to retry.

This is important: Lambda does not automatically retry a synchronous function invocation just because the handler raised an exception.

Your application should implement appropriate retry policies, exponential backoff, and timeout handling.

### 2.4 When to use synchronous invocation

Typical use cases include:

* REST APIs.

* Authentication and authorization.

* Request validation.

* Real-time calculations.

* Reading or updating application data.

* Backend operations requiring immediate responses.

Important: Synchronous invocation creates a dependency between the caller and the Lambda function. If Lambda is slow or unavailable, the caller may also experience delays or failures.

### 3\. Asynchronous Invocation and Event Queues

Asynchronous invocation works differently.

The caller submits an event to Lambda without waiting for the function to finish processing it.

Lambda accepts the event, places it in an internal event queue, and processes it asynchronously.

Event Producer

Application, S3, or SNS

Lambda Internal Event Queue

Event accepted for asynchronous processing

Lambda Function

Processes the event

Success / Failure Handling

Retry, destination, or dead-letter queue

### 3.1 How asynchronous invocation works

Consider an image-processing application.

A user uploads an image to S3.

Instead of making the upload request wait for image processing, S3 sends an event to Lambda.

Lambda accepts the event and processes the image separately.

The upload operation does not need to wait for image processing to finish.

This architecture improves responsiveness and separates the producer from the consumer.

### 3.2 Configuring asynchronous invocation

Using Boto3:

```python
import boto3
import json

client = boto3.client("lambda")

response = client.invoke(
    FunctionName="image-processor",
    InvocationType="Event",
    Payload=json.dumps({
        "bucket": "images",
        "key": "uploads/photo.jpg"
    })
)

print(response["StatusCode"])
```

A successful asynchronous submission normally returns HTTP status code `202`.

This means Lambda accepted the event for processing. It does not mean the function successfully completed its execution.

### 3.3 Lambda's internal asynchronous queue

Lambda maintains an internal queue for asynchronous invocations.

Important characteristics:

* Events are queued before execution.

* Lambda attempts to process accepted events.

* Failed executions can be retried.

* Events can be delivered more than once.

* Events can expire before successful processing.

* Queue congestion can increase processing latency.

The internal queue is managed by AWS; you do not directly manage its infrastructure.

### 3.4 Asynchronous invocation use cases

* S3 image and document processing.

* Sending emails and notifications.

* Background report generation.

* Processing application events.

* Data transformation.

* Non-blocking application operations.

Important distinction: Lambda asynchronous invocation is not the same as Amazon SQS. With asynchronous Lambda invocation, AWS manages the internal event queue. With SQS, you manage a separate queue service, including its retention, visibility timeout, and message lifecycle.

### 4\. Poll-Based Invocation and Event Source Mappings

The third invocation model is poll-based invocation.

Unlike direct synchronous or asynchronous invocation, Lambda polls an event source for new messages or records.

An event source mapping (ESM) connects a supported event source to a Lambda function.

Examples include:

* Amazon SQS.

* Amazon DynamoDB Streams.

* Amazon Kinesis Data Streams.

* Amazon Managed Streaming for Apache Kafka.

* Self-managed Kafka.

### 4.1 How event source mappings work

Consider an SQS queue receiving orders.

Lambda continuously polls the queue, retrieves available messages, and invokes your function with batches of messages.

Producer

Publishes order messages

Amazon SQS Queue

Stores messages durably

Lambda polls the queue

Lambda Event Source Mapping

Retrieves batches and invokes the function

Lambda Handler

Processes messages

### 4.2 Event source mapping configuration

An event source mapping has several important configuration options:

| Configuration              | Purpose                                                  |
| -------------------------- | -------------------------------------------------------- |
| Batch size                 | Maximum records retrieved per batch                      |
| Maximum batching window    | Time to gather records before invocation                 |
| Enabled                    | Activates or disables the mapping                        |
| Starting position          | Determines where stream processing begins                |
| Parallelization factor     | Controls concurrent processing for supported streams     |
| Maximum concurrency        | Limits concurrent processing for supported event sources |
| Filter criteria            | Filters records before invoking Lambda                   |
| Report batch item failures | Enables partial batch failure reporting                  |

Not every option applies to every event source.

### 4.3 Polling behavior

For SQS, Lambda polls messages and invokes the function with batches.

For DynamoDB Streams and Kinesis, Lambda reads records from stream shards.

The polling and scaling behavior varies according to the event source.

For example:

* SQS scales polling based on queue workload and configured concurrency.

* Kinesis processing is organized around shards.

* DynamoDB Streams processing also uses shard-based ordering.

### 4.4 Important architectural distinction

| Invocation model | Who initiates execution?                         |
| ---------------- | ------------------------------------------------ |
| Synchronous      | Caller directly invokes Lambda                   |
| Asynchronous     | Event producer submits an event                  |
| Poll-based       | Lambda polls the event source and invokes itself |

This distinction is essential when designing serverless architectures.

### 5\. Invocation Retries and Error Handling

Retries are essential for building reliable serverless applications.

A Lambda function can fail for many reasons:

* Temporary database connectivity problems.

* Downstream AWS service throttling.

* Network failures.

* Invalid event data.

* Application exceptions.

* Execution timeouts.

* Insufficient concurrency.

However, retry behavior depends on the invocation model and event source.

### 5.1 Synchronous invocation retries

For synchronous invocation, Lambda returns the error to the caller.

The caller decides whether to retry.

For example:

```python
import time
import boto3

client = boto3.client("lambda")

for attempt in range(3):
    try:
        response = client.invoke(
            FunctionName="order-processor",
            InvocationType="RequestResponse",
            Payload=b'{"order_id": 123}'
        )

        if response.get("FunctionError"):
            raise RuntimeError("Lambda execution failed")

        print(response["Payload"].read())
        break

    except Exception:
        if attempt == 2:
            raise

        time.sleep(2 ** attempt)
```

This example uses exponential backoff:

* First retry: 1 second.

* Second retry: 2 seconds.

* Further retries would increase exponentially.

In production, also consider jitter, maximum retry duration, and which errors are actually retryable.

### 5.2 Asynchronous invocation retries

Asynchronous invocation has Lambda-managed retry behavior.

By default, when a function returns an error:

* Lambda waits approximately one minute.

* Lambda retries the invocation.

* If it fails again, Lambda waits approximately two minutes.

* Lambda performs another retry.

For function execution errors, the default is two additional retries after the initial attempt.

You can configure:

* Maximum retry attempts.

* Maximum event age.

* Failure destinations.

* Dead-letter queues.

The maximum event age can be configured from 60 seconds up to six hours.

### 5.3 Retry behavior comparison

| Invocation model           | Retry responsibility                                |
| -------------------------- | --------------------------------------------------- |
| Synchronous                | Caller                                              |
| Asynchronous               | Lambda-managed                                      |
| SQS event source           | SQS visibility and redelivery                       |
| Kinesis / DynamoDB Streams | Event source mapping and stream processing behavior |

A critical concept is that retries can cause duplicate processing.

For example, Lambda might successfully update a database but fail before the invocation is acknowledged. The event may be delivered again.

This is why retry handling and idempotency must be designed together.

### 6\. Asynchronous Invocation Destinations

Lambda destinations allow you to route the outcome of an asynchronous invocation to another AWS service.

They are useful for building event-driven workflows and failure-handling architectures.

Lambda supports two destination types:

* On-success destination.

* On-failure destination.

### 6.1 On-success destination

When a Lambda function successfully processes an event, Lambda can send an invocation record to a configured destination.

Supported destinations include:

* Amazon SQS.

* Amazon SNS.

* Amazon EventBridge.

* Another Lambda function.

Example:

```text
Order Event
    |
    v
Lambda: Process Order
    |
    v
Successful Execution
    |
    v
SNS Topic: Order Completed
    |
    +----> Email Notification
    |
    +----> Analytics Processor
```

### 6.2 On-failure destination

If an asynchronous invocation fails after its configured retry attempts or expires, Lambda can send an invocation record to a failure destination.

For example:

```text
Order Event
    |
    v
Lambda: Process Order
    |
    v
Execution Failure
    |
    v
Retry Attempts
    |
    v
Failure Destination
    |
    v
SQS: Failed Invocation Records
```

The destination receives an invocation record containing information about the original request and execution result.

### 6.3 Destinations versus dead-letter queues

These two mechanisms are related but different.

| Feature           | Destination                                           | Dead-letter queue        |
| ----------------- | ----------------------------------------------------- | ------------------------ |
| Success handling  | Yes                                                   | No                       |
| Failure handling  | Yes                                                   | Yes                      |
| Receives          | Invocation record                                     | Original event payload   |
| Supported targets | SQS, SNS, EventBridge, Lambda                         | SQS, SNS                 |
| Execution context | Includes invocation metadata and response information | Primarily original event |

For most modern asynchronous workflows, destinations provide richer execution information.

Use a DLQ when retaining the original failed event is the primary requirement.

Important: Destinations and Lambda DLQs discussed here concern asynchronous invocation. An SQS event source mapping has a different failure-handling mechanism, typically involving SQS redrive policies and DLQs.

### 7\. Maximum Event Age and Retry Attempts

Two important asynchronous invocation settings control how long Lambda retains events and how many times it retries failed executions.

### 7.1 Maximum event age

Maximum event age determines how long an event can remain in Lambda's asynchronous processing system before it is discarded or routed through failure handling.

The configurable range is:

* Minimum: 60 seconds.

* Maximum: 21,600 seconds (6 hours).

For example:

```text
MaximumEventAgeInSeconds = 3600
```

This allows an event to remain eligible for processing for up to one hour.

This setting is particularly useful when your application has time-sensitive events.

An old payment authorization request, for example, might no longer be useful after a certain period.

### 7.2 Maximum retry attempts

You can configure the maximum number of retries for function execution errors.

The configurable range is zero to two additional retries.

For example:

```text
MaximumRetryAttempts = 1
```

Lambda makes one retry after the initial failed execution.

### 7.3 Choosing the right configuration

| Application           | Suggested consideration                          |
| --------------------- | ------------------------------------------------ |
| Image processing      | Allow retries for temporary failures             |
| Email notifications   | Use retries and a failure destination            |
| Payment processing    | Use idempotency and carefully controlled retries |
| Time-sensitive events | Set a suitable maximum event age                 |
| Background reports    | Allow a longer processing window                 |

The exact values should depend on business requirements, downstream service capacity, and the consequences of processing late or duplicate events.

### 8\. SQS Visibility Timeout and Lambda Timeout Relationships

This is one of the most important concepts when integrating Lambda with SQS.

### 8.1 What is visibility timeout?

When Lambda retrieves a message from SQS, that message becomes temporarily invisible to other consumers.

This period is called the visibility timeout.

It prevents multiple consumers from processing the same message simultaneously under normal conditions.

For example:

* SQS receives an order message.

* Lambda retrieves the message.

* SQS hides the message for 60 seconds.

* Lambda processes the order.

* Lambda successfully processes the batch.

* The message is deleted from SQS.

If processing fails and the message is not deleted, it becomes visible again after the visibility timeout expires.

SQS Message Available

Lambda Retrieves Message

Visibility timeout begins

Success

Message deleted from SQS

Failure

Message becomes visible again after timeout

### 8.2 Relationship between Lambda timeout and SQS visibility timeout

AWS recommends configuring the SQS visibility timeout to at least six times the Lambda function timeout, plus the maximum batching window.

For example:

* Lambda timeout: 30 seconds.

* Maximum batching window: 5 seconds.

* Recommended minimum visibility timeout: 185 seconds.

Calculation:

(30 \\times 6) + 5 = 185 \\text{ seconds}

Why six times?

Because Lambda may need additional time for retries, throttling, and processing delays.

If visibility timeout is too short, messages can become visible while the original Lambda execution is still processing them.

This can result in duplicate concurrent processing.

### 8.3 Example configuration

```python
lambda_timeout = 30

visibility_timeout = 185
```

The SQS queue and Lambda function must be configured consistently.

### 8.4 SQS redrive policies

SQS supports redrive policies that move repeatedly unsuccessful messages to a dead-letter queue.

The main configuration is:

`maxReceiveCount`

For example:

```json
{
  "maxReceiveCount": 5
}
```

After the message has been received unsuccessfully the configured number of times, SQS moves it to the DLQ.

This allows your application to isolate problematic messages instead of retrying them indefinitely.

### 9\. FIFO Processing and Ordering Considerations

Ordering matters in many business applications.

Consider a banking application:

* Account receives $100.

* Account transfers $40.

* Account withdraws $20.

If these operations are processed in the wrong order, the resulting account balance might be incorrect.

Amazon SQS FIFO queues help preserve message ordering.

### 9.1 Standard versus FIFO queues

| Feature          | Standard queue              | FIFO queue                                                         |
| ---------------- | --------------------------- | ------------------------------------------------------------------ |
| Message ordering | Best-effort                 | Preserved within message groups                                    |
| Delivery         | At least once               | Exactly-once processing capability within its deduplication scope  |
| Throughput       | Very high, nearly unlimited | Higher throughput available with batching and high-throughput FIFO |
| Message groups   | No                          | Yes                                                                |
| Deduplication    | Application-level           | Content-based or explicit deduplication                            |

An important clarification: FIFO deduplication does not guarantee that your business operation executes exactly once. Your application still needs idempotency.

### 9.2 Message group IDs

FIFO queues use `MessageGroupId` to organize messages.

Messages belonging to the same group are processed in order.

For example:

```python
import boto3
import json

sqs = boto3.client("sqs")

sqs.send_message(
    QueueUrl="https://sqs.example.com/orders.fifo",
    MessageBody=json.dumps({
        "order_id": 123,
        "status": "created"
    }),
    MessageGroupId="customer-100",
    MessageDeduplicationId="order-123-created"
)
```

All messages with the same group ID maintain their ordering.

Different message groups can be processed concurrently.

### 9.3 FIFO with Lambda

When Lambda consumes an SQS FIFO queue:

* Message ordering is maintained within a message group.

* Messages from different groups can be processed concurrently.

* A failed message can prevent subsequent messages in its group from progressing.

* Batch failure handling must preserve ordering requirements.

This makes FIFO queues useful for:

* Financial transactions.

* Order state transitions.

* Inventory updates.

* Customer account operations.

* Sequential business workflows.

### 9.4 Important architectural consideration

FIFO queues can reduce concurrency when many messages belong to a single message group.

If all messages use the same group ID, that group becomes a processing bottleneck.

Design message groups around the entities that require ordered processing, such as customer IDs, account IDs, or order IDs.

### 10\. Idempotency and Duplicate Event Prevention

Idempotency is one of the most important concepts in distributed systems.

An operation is idempotent when executing it multiple times produces the same final result as executing it once.

For example:

```text
Set order status to COMPLETED
```

This operation can be repeated without changing the final state.

But:

```text
Subtract $100 from account balance
```

Repeating it twice creates an incorrect result.

### 10.1 Why duplicate events happen

Lambda-based systems can process duplicate events because:

* Asynchronous Lambda invocation can deliver events more than once.

* SQS uses at-least-once delivery.

* A function may complete its business operation but fail before message deletion.

* Network failures can make execution results uncertain.

* Producers may publish the same event more than once.

Therefore, you should never assume that an event will be processed exactly once.

### 10.2 Idempotency keys

A common approach is to assign each event a unique identifier.

For example:

```json
{
  "event_id": "evt-123456",
  "order_id": "order-100",
  "operation": "payment"
}
```

Before processing the event, the Lambda function checks whether the event has already been successfully processed.

A simple conceptual implementation:

```python
def handler(event, context):

    event_id = event["event_id"]

    if already_processed(event_id):
        return {
            "status": "duplicate_ignored"
        }

    process_payment(event)

    mark_as_processed(event_id)

    return {
        "status": "success"
    }
```

The functions `already_processed()` and `mark_as_processed()` represent a persistent idempotency store, not in-memory variables.

### 10.3 Using DynamoDB for idempotency

DynamoDB is a popular choice for storing idempotency records.

Example record:

```json
{
  "event_id": "evt-123456",
  "status": "COMPLETED",
  "expiration": 1793510400
}
```

You can use conditional writes to ensure that only one execution initially claims a given event ID.

For example:

```python
table.put_item(
    Item={
        "event_id": event_id,
        "status": "IN_PROGRESS"
    },
    ConditionExpression="attribute_not_exists(event_id)"
)
```

If the item already exists, the conditional write fails.

A robust implementation must also handle abandoned `IN_PROGRESS` records, concurrent requests, and the atomicity of business updates.

For financial operations, idempotency records and the actual transaction should be coordinated carefully. Merely writing an idempotency record before or after an external payment operation is not enough to eliminate every failure window.

### 10.4 AWS Lambda Powertools

AWS Lambda Powertools for Python provides an idempotency utility that helps implement this pattern.

It supports:

* Idempotency keys.

* Persistent storage.

* Duplicate request detection.

* In-progress execution tracking.

* Expiration of idempotency records.

This is particularly useful for payment processing, order handling, and API requests.

### 11\. Partial Batch Responses and Failure Isolation

When Lambda processes messages in batches, one failed message can affect the entire batch.

Consider an SQS batch containing five messages:

```text
Message 1 → Success
Message 2 → Success
Message 3 → Failure
Message 4 → Success
Message 5 → Success
```

Without partial batch response handling, the entire batch can become eligible for redelivery.

This can result in successful messages being processed again.

### 11.1 What is partial batch response?

Partial batch response allows Lambda to identify only the messages that failed.

Instead of reporting the entire batch as failed, your function returns the identifiers of unsuccessful messages.

The response format is:

```json
{
  "batchItemFailures": [
    {
      "itemIdentifier": "message-id-3"
    }
  ]
}
```

Only the failed messages are returned for retry under the event source's processing rules.

### 11.2 Python example

```python
def handler(event, context):

    failures = []

    for record in event["Records"]:

        try:
            process_message(record)

        except Exception:
            failures.append({
                "itemIdentifier": record["messageId"]
            })

    return {
        "batchItemFailures": failures
    }
```

You must also enable the `ReportBatchItemFailures` response type on the event source mapping.

For SQS, this prevents successfully processed messages from being unnecessarily retried when individual messages fail.

### 11.3 Why it matters

Without partial batch responses:

* Successful messages may be processed repeatedly.

* Queue processing becomes inefficient.

* Downstream systems receive unnecessary requests.

* A single problematic message can slow down an entire batch.

With partial batch responses, failures are isolated and successful processing can continue.

### 11.4 FIFO considerations

For FIFO queues, ordering is more important.

When a message fails, you generally need to stop processing subsequent messages in the same message group and report the failed message and any unprocessed messages appropriately.

This prevents later operations from being applied before an earlier operation has succeeded.

### 12\. Distributed Processing and Fanout Architectures

Distributed processing allows an application to divide work among multiple independent Lambda functions.

Instead of building one large function that handles every operation, you can create multiple specialized consumers.

This improves scalability, separation of responsibilities, and fault isolation.

### 12.1 What is fanout?

Fanout is an architectural pattern in which one event is distributed to multiple independent consumers.

Amazon SNS is commonly used to implement this pattern.

Consider an e-commerce application that publishes an `OrderCreated` event.

Several services need to react:

* Inventory service reserves products.

* Payment service processes payment.

* Notification service sends confirmation.

* Analytics service records the order.

A fanout architecture looks like this:

Order Service

Publishes OrderCreated event

Amazon SNS Topic

Distributes the event

SQS: Inventory

Inventory Lambda

SQS: Payments

Payment Lambda

SQS: Notifications

Notification Lambda

SQS: Analytics

Analytics Lambda

Each consumer has its own queue and can process events independently.

### 12.2 Why use SNS with SQS?

You might wonder why we need both SNS and SQS.

They solve different problems:

SNS: Distribution

* Publishes events to multiple subscribers.

* Supports subscription filtering.

* Provides push-based message delivery.

SQS: Buffering and decoupling

* Stores messages until consumers process them.

* Allows consumers to process at their own pace.

* Supports retries and DLQs.

* Helps isolate consumer failures.

Combining them creates a powerful architecture.

### 12.3 Independent scaling

Suppose your application receives:

* 1,000 orders per minute.

* 1,000 inventory events per minute.

* 200 notification events per minute.

* 50 analytics events per minute.

Each consumer can scale independently according to its queue workload and processing capacity.

The notification service does not need to wait for analytics processing.

### 12.4 Failure isolation

Imagine the notification Lambda function becomes unavailable.

The notification queue retains its messages while the inventory and payment consumers continue processing their own queues.

This is called fault isolation.

It prevents one downstream service from unnecessarily disrupting unrelated services.

### 12.5 Important design considerations

When designing fanout systems, consider:

* Duplicate event delivery.

* Idempotency.

* Message ordering.

* Queue retention.

* Dead-letter queues.

* Consumer concurrency.

* Event schema versioning.

* Monitoring queue depth and message age.

This architecture is especially useful for microservices and event-driven applications.

### 13\. Lambda Integration with AWS Step Functions

AWS Lambda is excellent for executing individual units of application logic.

However, complex business processes often involve multiple steps, conditional decisions, retries, parallel execution, and waiting periods.

Managing all of these directly inside one Lambda function can become difficult.

This is where AWS Step Functions becomes useful.

### 13.1 What is Step Functions?

Step Functions is a workflow orchestration service.

It coordinates multiple AWS services and application operations through state machines.

A state machine defines:

* Which operation executes first.

* Which operation executes next.

* Which conditions determine execution paths.

* Which operations execute in parallel.

* What happens when an operation fails.

* How execution resumes or terminates.

### 13.2 Example: Order processing workflow

Consider a workflow:

* Receive an order.

* Validate the order.

* Process payment.

* Reserve inventory.

* Send confirmation.

* Complete the order.

Start: New Order

Lambda: Validate Order

Lambda: Process Payment

Lambda: Reserve Inventory

Lambda: Send Confirmation

End: Order Completed

Step Functions coordinates the execution of these operations.

Each Lambda function focuses on a specific responsibility.

### 13.3 Amazon States Language (ASL)

Step Functions workflows are defined using Amazon States Language.

ASL is a JSON-based language.

For example:

```json
{
  "Comment": "Order processing workflow",
  "StartAt": "ValidateOrder",
  "States": {
    "ValidateOrder": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:validate-order",
      "Next": "ProcessPayment",
      "Retry": [
        {
          "ErrorEquals": [
            "Lambda.ServiceException",
            "Lambda.TooManyRequestsException"
          ],
          "IntervalSeconds": 2,
          "MaxAttempts": 3,
          "BackoffRate": 2
        }
      ],
      "Catch": [
        {
          "ErrorEquals": ["States.ALL"],
          "Next": "OrderFailed"
        }
      ]
    },
    "ProcessPayment": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:process-payment",
      "End": true
    },
    "OrderFailed": {
      "Type": "Fail"
    }
  }
}
```

This example demonstrates:

* Task states.

* Lambda integration.

* Retry policies.

* Exponential backoff.

* Error handling.

* Failure states.

### 13.4 Important Step Functions states

| State type | Purpose                                 |
| ---------- | --------------------------------------- |
| Task       | Executes work or invokes an AWS service |
| Choice     | Conditional branching                   |
| Parallel   | Executes branches concurrently          |
| Map        | Processes collections of items          |
| Wait       | Introduces a delay                      |
| Pass       | Passes or transforms data               |
| Succeed    | Successfully terminates a workflow      |
| Fail       | Terminates with failure                 |

### 13.5 Standard versus Express workflows

Step Functions offers two primary workflow types.

| Feature           | Standard                                   | Express                                                                  |
| ----------------- | ------------------------------------------ | ------------------------------------------------------------------------ |
| Maximum duration  | Up to 1 year                               | Up to 5 minutes                                                          |
| Execution model   | Exactly-once workflow execution by default | At-least-once or asynchronous at-most-once, depending on invocation mode |
| Execution history | Detailed execution history                 | CloudWatch Logs-based monitoring                                         |
| Typical workloads | Long-running business processes            | High-volume, short-duration workflows                                    |
| Pricing model     | State transitions                          | Executions and duration                                                  |

Exactly-once workflow execution does not mean external side effects are automatically exactly once. Individual task operations still need appropriate idempotency.

### 13.6 When to use Step Functions

Use Step Functions when you need:

* Multi-step business workflows.

* Conditional processing.

* Parallel execution.

* Coordinated retries.

* Long-running workflows.

* Human approval steps.

* Workflow visibility and execution history.

* Integration with multiple AWS services.

One important architectural principle: do not use Lambda merely to wait for another Lambda or to coordinate a long-running process. Step Functions can manage orchestration more efficiently.

### 14\. Durable Execution and Workflow Orchestration Concepts

Durable execution is a broader architectural concept that builds on workflow orchestration.

A normal Lambda invocation executes within a temporary execution environment. When the invocation finishes, its in-memory state is not a durable workflow record.

If an application needs to survive interruptions, it must persist its progress.

### 14.1 Traditional Lambda execution

Imagine a function that performs:

* Validate an order.

* Charge a payment.

* Reserve inventory.

* Send an email.

If the function times out after charging the payment, the remaining operations may never happen.

When the function is retried, it might charge the customer again unless the payment operation is idempotent.

This is a significant reliability problem.

### 14.2 Durable workflow execution

A durable workflow maintains its progress across individual execution steps.

Conceptually:

```text
Workflow Started
      |
      v
Validate Order
      |
      v
Charge Payment
      |
      v
Progress Persisted
      |
      v
Reserve Inventory
      |
      v
Progress Persisted
      |
      v
Send Confirmation
      |
      v
Workflow Completed
```

If an interruption occurs, the orchestration system can resume from an appropriate persisted state rather than restarting the entire business process.

### 14.3 Step Functions as a durable orchestrator

Step Functions provides durable workflow execution through persisted state transitions and execution history.

It can coordinate:

* Lambda invocations.

* SQS and SNS integrations.

* DynamoDB operations.

* ECS tasks.

* Human approval workflows.

* Scheduled waits.

* Parallel tasks.

For example, an insurance claim workflow might wait several days for document approval without keeping a Lambda execution environment running.

### 14.4 Durable Lambda executions

AWS also provides Lambda durable functions, a capability designed for building long-running, stateful workflows using Lambda programming concepts.

The durable execution model introduces concepts such as:

* Persisted execution progress.

* Checkpointing.

* Resuming after interruptions.

* Durable waits.

* Coordinated steps.

* Retryable operations.

This is distinct from ordinary Lambda execution and should not be confused with simply increasing the Lambda timeout.

When selecting a durable execution solution, consider whether you need application-code-centric orchestration or a separately defined state machine.

### 14.5 Choosing an orchestration approach

| Requirement                                            | Suitable approach        |
| ------------------------------------------------------ | ------------------------ |
| Simple independent computation                         | Lambda                   |
| Background message processing                          | SQS + Lambda             |
| Event distribution                                     | SNS + SQS + Lambda       |
| Complex multi-step workflow                            | Step Functions           |
| Long-running workflow with waits                       | Step Functions Standard  |
| Stateful durable execution in Lambda programming model | Lambda durable functions |

The key principle is that compute execution and workflow execution are different responsibilities.

Lambda executes application logic; a durable orchestration mechanism manages the lifecycle and progress of a larger business process.

### 15\. Reliability, Fault Tolerance, and Recovery Strategies

Production Lambda applications must be designed to continue operating when individual components fail.

Reliability is not achieved simply by configuring retries. It requires combining multiple mechanisms.

### 15.1 Fault tolerance

Fault tolerance is the ability of an application to continue operating despite failures in individual components.

For example:

```text
Order Service
     |
     v
   SNS Topic
     |
     +------> SQS Inventory Queue
     |              |
     |              v
     |        Inventory Lambda
     |
     +------> SQS Payment Queue
     |              |
     |              v
     |         Payment Lambda
     |
     +------> SQS Notification Queue
                    |
                    v
              Notification Lambda
```

If the notification service fails, the other consumers can continue operating.

This is an example of fault isolation.

### 15.2 Circuit breaker pattern

A circuit breaker prevents an application from repeatedly calling an unhealthy downstream service.

It generally has three states:

| State     | Behavior                                      |
| --------- | --------------------------------------------- |
| Closed    | Requests are allowed                          |
| Open      | Requests are rejected temporarily             |
| Half-open | A limited number of test requests are allowed |

For example, suppose Lambda invokes an external payment provider.

If the provider repeatedly returns errors, the application can temporarily stop sending requests.

This prevents unnecessary retries and reduces pressure on an already unhealthy dependency.

You can implement circuit breaker logic in your application or use a dedicated library and persistent state mechanism.

### 15.3 Backpressure

Backpressure controls how quickly producers send work into a system relative to the consumers' processing capacity.

Consider an application receiving 10,000 messages per minute while its Lambda consumers can process only 5,000.

Without appropriate controls, queue depth and processing latency increase.

SQS provides buffering, while Lambda concurrency controls help regulate processing.

Useful mechanisms include:

* Reserved concurrency.

* Maximum concurrency on supported SQS event source mappings.

* SQS queue buffering.

* Batch size configuration.

* Producer-side rate limiting.

* Downstream service throttling controls.

### 15.4 Recovery strategies

A reliable Lambda architecture should define what happens after each type of failure.

| Failure                        | Recovery strategy                  |
| ------------------------------ | ---------------------------------- |
| Temporary application failure  | Retry                              |
| Duplicate event                | Idempotency                        |
| Invalid message                | DLQ                                |
| Downstream service unavailable | Backoff and circuit breaker        |
| Queue congestion               | Concurrency management and scaling |
| Partial batch failure          | Partial batch response             |
| Workflow interruption          | Durable orchestration              |
| Regional disruption            | Multi-region recovery architecture |

### 15.5 Disaster recovery

For critical serverless applications, consider:

* Multi-region deployment.

* Replication of DynamoDB data.

* SQS queue and event infrastructure in recovery regions.

* Infrastructure recreation using Pulumi.

* Replicated application artifacts and container images.

* Route 53 or other traffic-management failover.

* Documented recovery procedures.

A multi-region Lambda architecture does not automatically provide disaster recovery. Your queues, databases, secrets, permissions, and event integrations must also be available in the recovery region.

### 15.6 Reliability design principles

For production systems, follow these principles:

* Assume events can be delivered more than once.

* Make event processing idempotent.

* Use retries for transient failures.

* Avoid retrying permanent application errors indefinitely.

* Use DLQs to isolate problematic messages.

* Monitor queue depth and message age.

* Apply concurrency limits to protect downstream services.

* Separate business logic from workflow orchestration.

* Persist important application and workflow state.

* Design recovery procedures before production deployment.

### 16\. Putting Everything Together: Production Architecture

Let's combine the concepts from this module into a realistic architecture.

Imagine building an event-driven order-processing platform.

### Production order processing

FastAPI Application

Receives customer orders

Amazon EventBridge

Publishes OrderCreated event

AWS Step Functions

Coordinates the order workflow

Validate Order

Lambda

Process Payment

Lambda

Amazon SNS

Publishes OrderCompleted event

SQS Inventory Queue

Inventory Lambda

SQS Notification Queue

Notification Lambda

Failure Handling

Retries · DLQs · Idempotency · Recovery

Observability

CloudWatch · X-Ray · CloudTrail

### Architecture walkthrough

* FastAPI receives an order and publishes an event.

* EventBridge routes the event to the appropriate workflow.

* Step Functions coordinates order validation and payment processing.

* SNS distributes the completed-order event.

* Separate SQS queues buffer inventory and notification work.

* Lambda consumers process their respective messages.

* Failed messages are retried and eventually moved to DLQs when configured.

* Idempotency prevents duplicate business operations.

* CloudWatch and X-Ray provide operational visibility.

This architecture combines synchronous APIs, asynchronous events, polling-based invocation, distributed processing, and durable workflow orchestration.

### 17\. Important Concepts to Remember

Here is a consolidated reference for the major concepts covered in this module.

| Concept                 | Main purpose                                        |
| ----------------------- | --------------------------------------------------- |
| Synchronous invocation  | Immediate request-response processing               |
| Asynchronous invocation | Background event processing                         |
| Event source mapping    | Polling an event source                             |
| Retry policy            | Recovering from temporary failures                  |
| Maximum event age       | Limiting asynchronous event lifetime                |
| Destination             | Routing invocation outcomes                         |
| DLQ                     | Isolating failed events or messages                 |
| Visibility timeout      | Preventing immediate SQS message redelivery         |
| FIFO queue              | Preserving message order within message groups      |
| Idempotency             | Preventing duplicate business effects               |
| Partial batch response  | Isolating individual message failures               |
| Fanout                  | Distributing events to multiple consumers           |
| Step Functions          | Orchestrating multi-step workflows                  |
| Durable execution       | Persisting workflow progress                        |
| Backpressure            | Controlling processing load                         |
| Circuit breaker         | Preventing repeated calls to unhealthy dependencies |

### Final architectural comparison

One distinction worth mastering is the difference between the three invocation mechanisms:

|                                | Synchronous    | Asynchronous                      | Poll-based                   |
| ------------------------------ | -------------- | --------------------------------- | ---------------------------- |
| Caller waits for result        | Yes            | No                                | No                           |
| Lambda-managed internal queue  | No             | Yes                               | No                           |
| External queue required        | No             | No                                | Usually                      |
| Automatic event-source polling | No             | No                                | Yes                          |
| Typical integration            | API Gateway    | S3, SNS                           | SQS, Kinesis                 |
| Main reliability concern       | Caller retries | Duplicate events and retry policy | Redelivery and checkpointing |

### What you should take away from Module 6

The most important architectural lessons are:

* Understand the differences between synchronous, asynchronous, and poll-based invocation.

* Never assume Lambda processes an event exactly once.

* Understand how retry behavior differs between invocation types.

* Configure SQS visibility timeout in relation to Lambda execution time.

* Use FIFO queues when ordering is a business requirement.

* Implement idempotency for operations with side effects.

* Use partial batch responses to isolate message failures.

* Combine SNS and SQS for reliable event distribution.

* Use Step Functions instead of building complex workflows inside individual Lambda functions.

* Design for failures, recovery, and observability from the beginning.

The central principle: A production-grade serverless application is not just a collection of Lambda functions. It is a distributed system whose reliability depends on message delivery, retry behavior, state management, failure isolation, and orchestration.

Next, Module 7 will bring these concepts into deployment and infrastructure automation using Pulumi Python, including Lambda versions, aliases, deployment strategies, and CI/CD.
