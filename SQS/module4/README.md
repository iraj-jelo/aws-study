### Module 4 — Reliability, Retries, and Dead-Letter Queues (DLQs)

AWS SQS · Reliability Engineering · Message Processing · Failure Recovery

### 1\. Introduction to SQS reliability

Amazon SQS is designed to decouple producers from consumers. However, decoupling introduces an important challenge: what happens when a consumer cannot successfully process a message?

Imagine an e-commerce application:

* A customer places an order.

* The application sends an order message to SQS.

* A consumer receives the message.

* The consumer processes payment and updates the order database.

* The consumer fails because the payment service is temporarily unavailable.

What should happen to the message?

Deleting it would cause data loss. Keeping it invisible forever would prevent other consumers from processing it. Immediately retrying it could overload the failing payment service.

SQS provides several mechanisms to handle these situations:

* Visibility timeout.

* Message redelivery.

* Retry behavior.

* Redrive policies.

* Dead-letter queues.

* DLQ message redrive.

Together, these mechanisms help build reliable asynchronous processing systems.

![How to Use Amazon SQS Dead-Letter Queues to Capture and Replay Failed Messages | by Vishnu Prasad J | Feb, 2026 | Medium](https://images.openai.com/static-rsc-4/yBeVEjvHS_NhrmKmF6e6grGWV1wacPN3ZMPsGT6Blu3sGlvedGLhnAXmjvIhVr-m1L1xhonL1LklNOByHoLbc271uqyZ4NUmOTGxVkR0b6PWjjThozshTNsL9pZ96yPmwJG64Ux6zDmw0SvDcFPJrnesJA8rjCc2ViXKtBTuszxeuA0OHHsZ6aYSyJRYPUJD?purpose=fullsize)

### 2\. Message processing failures and failure scenarios

Before configuring retry mechanisms, understand the different ways message processing can fail.

### 2.1 Consumer crashes

A consumer receives a message but crashes before completing its processing.

Example:

```python
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1
)

message = response["Messages"][0]

process_order(message["Body"])

sqs.delete_message(
    QueueUrl=queue_url,
    ReceiptHandle=message["ReceiptHandle"]
)
```

Suppose `process_order()` crashes.

The execution never reaches `delete_message()`.

The message remains in SQS, but it is temporarily invisible because it has been received.

After its visibility timeout expires, SQS makes it available again.

Another consumer can receive and process it.

### 2.2 Application-level failures

The consumer remains operational, but processing fails.

Examples:

* Invalid message structure.

* Missing required fields.

* Database constraint violations.

* External API failures.

* Payment processing errors.

* Unsupported message versions.

These failures need different handling strategies.

For example:

| Failure                    | Typical strategy            |
| -------------------------- | --------------------------- |
| Temporary database outage  | Retry                       |
| HTTP 503 from external API | Retry with backoff          |
| Invalid JSON               | Isolate in DLQ              |
| Missing required field     | Investigate and isolate     |
| Duplicate order event      | Idempotent processing       |
| Expired credentials        | Fix credentials, then retry |

Not every failure should be retried indefinitely.

### 2.3 Network failures

A consumer may successfully process a message but fail to communicate with SQS when deleting it.

This creates an interesting situation:

* The order is successfully processed.

* The consumer sends `DeleteMessage`.

* The network connection fails.

* SQS does not receive the deletion request.

* The visibility timeout expires.

* The same message is delivered again.

This is one reason SQS applications must support duplicate processing.

### 2.4 Partial processing failures

Consider a consumer that performs three operations:

* Save an order to PostgreSQL.

* Charge a payment.

* Send a confirmation email.

Suppose the first two operations succeed, but the email service fails.

If the entire message is retried, the consumer may accidentally save the order again or charge the customer again.

This is a distributed transaction problem.

A reliable consumer must distinguish between operations that have already succeeded and operations that still need to happen.

This is where idempotency, transactional outbox patterns, and carefully designed workflows become important.

### 3\. Visibility timeout and processing duration relationships

Visibility timeout is one of the most important SQS reliability mechanisms.

When a consumer receives a message, SQS does not immediately remove it from the queue.

Instead, SQS temporarily hides the message from other consumers.

This period is called the visibility timeout.

### 3.1 How visibility timeout works

Consider a queue with a visibility timeout of 30 seconds.

![The Essential Guide to Amazon SQS | Baselime Blog](https://images.openai.com/static-rsc-4/wN1A5UMhbrg4revL34-DdsMlYzCzN4jQLTabxSLVZwU-uv80oVnNzPPlqzPOU1RnBU7sROhEGp0xjop-CbpChp2wCiI8P3SsBORnImF8r_VvVBQsOkcouVb6K6n8KqwuLPo8B8UQEy79xW5Wl5q88YV7qyUbJKSSz_BGaYCpYG7k4Yu3kdRBlzQ5LruHWJKs?purpose=fullsize)

The sequence is:

* Message enters the queue.

* Consumer A receives the message.

* SQS makes the message temporarily invisible.

* Consumer A processes the message.

* Consumer A successfully deletes the message.

* The message is permanently removed from the queue.

If Consumer A fails to delete the message:

* The visibility timeout expires.

* The message becomes visible again.

* Consumer B can receive it.

* Processing starts again.

Important: Visibility timeout does not guarantee exclusive processing.

If processing takes longer than the visibility timeout, another consumer can receive the same message while the original consumer is still working.

### 3.2 Configuring visibility timeout

You can configure visibility timeout when creating a queue.

Using AWS CLI:

```bash
aws sqs create-queue \
  --queue-name orders-queue \
  --attributes VisibilityTimeout=60
```

You can also modify an existing queue:

```bash
aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes VisibilityTimeout=120
```

Using Boto3:

```python
import boto3

sqs = boto3.client("sqs")

sqs.set_queue_attributes(
    QueueUrl=queue_url,
    Attributes={
        "VisibilityTimeout": "120"
    }
)
```

### 3.3 Choosing the correct visibility timeout

The visibility timeout should be longer than the expected processing duration.

For example:

| Processing duration | Suggested timeout |
| ------------------- | ----------------- |
| 2 seconds           | 30 seconds        |
| 10 seconds          | 60 seconds        |
| 30 seconds          | 90 seconds        |
| 2 minutes           | 4 minutes         |
| 5 minutes           | 7 minutes         |

These are illustrative starting points, not universal requirements.

You should consider:

* Normal processing duration.

* Worst-case processing duration.

* External API latency.

* Database response times.

* Network delays.

* Consumer shutdown behavior.

The maximum visibility timeout is 12 hours.

### 3.4 Extending visibility timeout dynamically

Sometimes processing duration is unpredictable.

For example, a consumer downloads a large file, processes it, and uploads the result.

You might initially configure a 60-second visibility timeout but discover that some files take several minutes.

SQS supports `ChangeMessageVisibility`, allowing a consumer to extend the visibility timeout for an individual message.

```python
sqs.change_message_visibility(
    QueueUrl=queue_url,
    ReceiptHandle=receipt_handle,
    VisibilityTimeout=120
)
```

This resets the visibility period to 120 seconds from the time of the request.

You can periodically extend visibility while processing a long-running task.

There are two important limitations:

* The maximum visibility period is 12 hours from the original receive request.

* Extending visibility does not eliminate the possibility of duplicate processing caused by failures or network problems.

### 3.5 Visibility timeout and Lambda

When Lambda consumes messages from SQS through an event source mapping, the relationship between visibility timeout and function timeout becomes particularly important.

AWS recommends configuring the queue visibility timeout to at least six times the Lambda function timeout, plus the maximum batching window when one is configured.

For example:

* Lambda timeout: 30 seconds.

* Maximum batching window: 5 seconds.

* Minimum recommended visibility timeout:

6 \\times 30 + 5 = 185 \\text{ seconds}

This gives Lambda sufficient time for retries and invocation processing.

### 4\. Message redelivery and retry behavior

SQS uses an at-least-once delivery model for Standard queues.

This means a message can be delivered more than once, even when your consumer appears to have processed it successfully.

### 4.1 Understanding message redelivery

Consider this sequence:

```text
Producer
   |
   v
SQS Queue
   |
   v
Consumer A receives message
   |
   v
Processing fails
   |
   v
Visibility timeout expires
   |
   v
Message becomes visible again
   |
   v
Consumer B receives message
   |
   v
Processing succeeds
   |
   v
Delete message
```

The message is not automatically deleted when received.

The consumer must explicitly call `DeleteMessage` after successful processing.

This behavior protects against losing messages when consumers crash.

### 4.2 Receive count

SQS tracks how many times a message has been received using the `ApproximateReceiveCount` message attribute.

You can retrieve it using Boto3:

```python
response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=1,
    AttributeNames=[
        "ApproximateReceiveCount"
    ]
)

for message in response.get("Messages", []):
    receive_count = message["Attributes"][
        "ApproximateReceiveCount"
    ]

    print("Receive count:", receive_count)
```

This is useful for identifying messages that repeatedly fail.

The count is approximate and should not be treated as a precise transactional counter.

### 4.3 SQS does not provide automatic exponential backoff

An important distinction:

SQS automatically makes messages available again after their visibility timeout expires, but it does not provide configurable exponential retry delays for each failed message.

For example, if visibility timeout is 30 seconds, repeated failures can cause repeated deliveries at roughly that interval.

If you need exponential backoff, you can implement it at the application level.

For example:

| Attempt | Retry delay |
| ------- | ----------- |
| 1       | 5 seconds   |
| 2       | 10 seconds  |
| 3       | 20 seconds  |
| 4       | 40 seconds  |

One approach is to change the message visibility timeout after a failed processing attempt:

```python
retry_delay = 60

sqs.change_message_visibility(
    QueueUrl=queue_url,
    ReceiptHandle=receipt_handle,
    VisibilityTimeout=retry_delay
)
```

In production, calculate the delay based on the receive count and apply a maximum delay.

You can also use a separate retry queue architecture for more sophisticated retry scheduling.

### 4.4 Important retry distinction

There are two different retry mechanisms to understand:

SQS message redelivery

* Controlled primarily by visibility timeout.

* Occurs when a message is not deleted.

* Makes the message available again.

Application-level retry

* Implemented by your consumer.

* Can retry a failed API request or database operation.

* Can use exponential backoff and jitter.

* Does not necessarily require receiving the message again.

Avoid combining unlimited application retries with unlimited SQS redelivery. This can create excessive load and delay failure detection.

### 5\. Redrive policies and maximum receive count

A redrive policy tells SQS what to do with messages that repeatedly fail processing.

Instead of allowing a problematic message to circulate indefinitely, SQS can move it to a Dead-Letter Queue.

### 5.1 What is a redrive policy?

A redrive policy defines:

* The destination dead-letter queue.

* The maximum number of receives allowed before a message is moved.

The maximum receive count is configured using `maxReceiveCount`.

For example:

```json
{
  "deadLetterTargetArn": "arn:aws:sqs:eu-west-2:123456789012:orders-dlq",
  "maxReceiveCount": "5"
}
```

This means that after the message has been received repeatedly without successful deletion, SQS can move it to the configured DLQ.

### 5.2 Understanding maxReceiveCount

Suppose:

* Source queue: `orders-queue`

* DLQ: `orders-dlq`

* Visibility timeout: 30 seconds

* Maximum receive count: 5

The processing sequence looks like this:

![SQS - AWS SA Professional](https://images.openai.com/static-rsc-4/jhX9ESB3V-uDx1WNo_bfSVal0nhmBulocpBRQXS_heeHEj7ZBfRqWWoPkEGuwtl7n92-CYtzDWx2nYuPuYC02b-kCHSEZdiIphAXnAFlbFQMbruud3nNRv0PXOHGDktD_iK8R2CoiiK76HfsWad94tbfZiVACuwd2WU8IcYbG-9VeHNUn5ifTbXdTOeFyNeG?purpose=fullsize)

| Receive attempt                | Result                  |
| ------------------------------ | ----------------------- |
| 1                              | Processing fails        |
| 2                              | Processing fails        |
| 3                              | Processing fails        |
| 4                              | Processing fails        |
| 5                              | Processing fails        |
| Subsequent receive eligibility | Message is moved to DLQ |

The important concept is that `maxReceiveCount` is a threshold for failed delivery attempts, not a count of application exceptions.

SQS does not know whether your application encountered an exception. It observes message reception and whether the message was successfully deleted.

### 5.3 Configuring a redrive policy

First, create the DLQ:

```bash
aws sqs create-queue \
  --queue-name orders-dlq
```

Retrieve its ARN:

```bash
aws sqs get-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attribute-names QueueArn
```

Then configure the source queue:

```bash
aws sqs set-queue-attributes \
  --queue-url "$SOURCE_QUEUE_URL" \
  --attributes '{
    "RedrivePolicy": "{\"deadLetterTargetArn\":\"arn:aws:sqs:eu-west-2:123456789012:orders-dlq\",\"maxReceiveCount\":\"5\"}"
  }'
```

### 5.4 Configuring the redrive policy with Boto3

```python
import json
import boto3

sqs = boto3.client("sqs")

dlq_arn = (
    "arn:aws:sqs:eu-west-2:"
    "123456789012:orders-dlq"
)

redrive_policy = {
    "deadLetterTargetArn": dlq_arn,
    "maxReceiveCount": "5"
}

sqs.set_queue_attributes(
    QueueUrl=source_queue_url,
    Attributes={
        "RedrivePolicy": json.dumps(redrive_policy)
    }
)
```

### 5.5 Important considerations

* The source queue and DLQ must be in the same AWS account and Region.

* A Standard queue must use a Standard DLQ.

* A FIFO queue must use a FIFO DLQ.

* A DLQ should have sufficient message retention.

* The maximum receive count should reflect realistic processing behavior.

Retention period consideration:

For Standard queues, the original enqueue timestamp is retained when a message moves to a DLQ. Its expiration is therefore based on the original enqueue time, not the time it entered the DLQ.

For FIFO queues, the enqueue timestamp resets when the message moves to the DLQ.

Consequently, choose DLQ retention carefully. For Standard queues, it is generally sensible to configure a DLQ retention period longer than the source queue's retention period.

### 6\. Dead-Letter Queues (DLQs)

A Dead-Letter Queue is a separate SQS queue that stores messages that could not be successfully processed by their source queue.

Its primary purpose is to isolate problematic messages so they do not continuously interfere with normal processing.

### 6.1 Why do we need DLQs?

Imagine an order-processing application.

A customer submits an order containing:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "CUST-2001",
  "total": 150,
  "currency": "USD"
}
```

However, one message contains an invalid structure:

```json
{
  "order_id": "ORD-1002",
  "customer_id": null,
  "total": "invalid"
}
```

Your consumer cannot process the second message.

Without a DLQ:

* The message keeps returning to the source queue.

* Consumers repeatedly attempt to process it.

* Processing capacity is wasted.

* Other messages can experience additional latency.

With a DLQ:

* The problematic message is isolated.

* Other messages can continue processing.

* Engineers can inspect the failed message.

* The underlying issue can be corrected.

### 6.2 DLQ architecture

![Complete Step-by-Step Guide: Creating AWS SQS Queues with AWS CDK (TypeScript) | by Rohit Chaware | Medium](https://images.openai.com/static-rsc-4/Dc4TXysl8IThk6i6RIZCvdTG2xFQqLvVnp03tHYxsdPmmL4SOS8tQq38WlQCtwp_z8MToanLz_Y1YsMTRMuVL5eiMUvQssgm7Q0h02moanugP-Lk3CePATKW2dyqFSGeQYXehQQJ6HuOYEbR5zeqWO8U1wFsBEvCSFGr9f-4JFL8dYGTQBllRgDOtbtdRfw9?purpose=fullsize)

The architecture consists of:

* Producer sends messages to the source queue.

* Consumer receives messages.

* Successfully processed messages are deleted.

* Repeatedly unsuccessful messages are moved to the DLQ.

* Engineers or automated systems inspect failed messages.

* Corrected messages can be redriven.

### 6.3 Creating a DLQ using Pulumi Python

Since we are using Pulumi for infrastructure management, let's define both queues as infrastructure resources.

```python
import pulumi
import pulumi_aws as aws

dlq = aws.sqs.Queue(
    "orders-dlq",
    name="orders-dlq",
    message_retention_seconds=1209600
)

source_queue = aws.sqs.Queue(
    "orders-queue",
    name="orders-queue",
    visibility_timeout_seconds=60,
    message_retention_seconds=345600,
    redrive_policy=dlq.arn.apply(
        lambda arn: pulumi.Output.json_dumps({
            "deadLetterTargetArn": arn,
            "maxReceiveCount": 5
        })
    )
)

pulumi.export("source_queue_url", source_queue.url)
pulumi.export("dlq_url", dlq.url)
```

Here:

* `orders-queue` is the source queue.

* `orders-dlq` stores failed messages.

* `maxReceiveCount` is set to 5.

* The DLQ retention period is 14 days.

* The source queue retention period is 4 days.

The DLQ ARN is dynamically referenced rather than hardcoded.

### 6.4 Monitoring DLQs

A DLQ should not become a place where messages accumulate unnoticed.

Useful CloudWatch metrics include:

| Metric                                | Purpose                                                |
| ------------------------------------- | ------------------------------------------------------ |
| ApproximateNumberOfMessagesVisible    | Number of messages available for processing            |
| ApproximateNumberOfMessagesNotVisible | Number of messages currently being processed or hidden |
| ApproximateNumberOfMessagesDelayed    | Number of messages waiting due to delivery delay       |
| ApproximateAgeOfOldestMessage         | Age of the oldest message                              |

For a DLQ, a nonzero visible message count can indicate a processing problem that requires investigation.

You can configure CloudWatch alarms to notify your operations team when messages appear in the DLQ.

### 7\. Redrive allow policies

Redrive policies and redrive allow policies sound similar, but they solve different problems.

Redrive policy: Defines where failed messages should go.

Redrive allow policy: Controls which source queues are allowed to use a particular queue as their DLQ.

### 7.1 Why are redrive allow policies useful?

Imagine a large AWS environment with multiple applications:

```text
Application A
    |
    v
Orders Queue ------\
                     \
Application B        \
    |                  v
    v                Shared DLQ
Payments Queue ------/
```

You might not want every queue in your account to use the same DLQ.

Redrive allow policies let you restrict which source queues can designate a queue as their DLQ.

### 7.2 Three redrive allow policy modes

SQS supports three modes:

| Mode     | Meaning                                                                     |
| -------- | --------------------------------------------------------------------------- |
| allowAll | Any eligible source queue can designate this queue as its DLQ               |
| denyAll  | No source queue can designate this queue as its DLQ                         |
| byQueue  | Only explicitly specified source queues can designate this queue as its DLQ |

For example, a restricted policy:

```json
{
  "redrivePermission": "byQueue",
  "sourceQueueArns": [
    "arn:aws:sqs:eu-west-2:123456789012:orders-queue",
    "arn:aws:sqs:eu-west-2:123456789012:payments-queue"
  ]
}
```

This allows only the two specified source queues to use the DLQ.

### 7.3 Configuring a redrive allow policy

Using AWS CLI:

```bash
aws sqs set-queue-attributes \
  --queue-url "$DLQ_URL" \
  --attributes '{
    "RedriveAllowPolicy": "{\"redrivePermission\":\"byQueue\",\"sourceQueueArns\":[\"arn:aws:sqs:eu-west-2:123456789012:orders-queue\"]}"
  }'
```

### 7.4 Important distinction

A redrive allow policy does not control which users or applications can read messages from the DLQ.

That is handled through IAM permissions and queue access policies.

Also, `byQueue` supports a maximum of 10 source queue ARNs. If more source queues need access, consider a different DLQ architecture.

### 8\. Moving messages from DLQs back to source queues

Moving messages from a DLQ back to a source queue is called message redrive.

This is useful after fixing the underlying processing problem.

For example:

* Your consumer cannot process an order because the database is unavailable.

* The message repeatedly fails.

* SQS moves it to the DLQ.

* Your engineering team fixes the database connectivity problem.

* You move the failed message back to the source queue.

* The consumer processes it successfully.

### 8.1 Manual message redrive

You can inspect DLQ messages using the AWS CLI:

```bash
aws sqs receive-message \
  --queue-url "$DLQ_URL" \
  --max-number-of-messages 10 \
  --attribute-names All \
  --message-attribute-names All
```

For investigation, you can inspect message bodies and attributes without immediately deleting them.

You can also use the SQS console to inspect messages.

### 8.2 Native SQS message redrive

AWS provides a native message movement mechanism through the `StartMessageMoveTask` API.

It allows you to move messages from a DLQ back to their source queue or another supported destination queue.

Using AWS CLI:

```bash
aws sqs start-message-move-task \
  --source-arn "$DLQ_ARN"
```

SQS can determine the original source queue from the DLQ's redrive configuration.

You can also explicitly specify a destination:

```bash
aws sqs start-message-move-task \
  --source-arn "$DLQ_ARN" \
  --destination-arn "$SOURCE_QUEUE_ARN" \
  --max-number-of-messages-per-second 50
```

The velocity parameter controls the approximate rate at which messages are moved.

You can inspect the movement task:

```bash
aws sqs list-message-move-tasks \
  --source-arn "$DLQ_ARN"
```

And cancel an active task:

```bash
aws sqs cancel-message-move-task \
  --task-handle "$TASK_HANDLE"
```

### 8.3 Redrive with Boto3

```python
import boto3

sqs = boto3.client("sqs")

response = sqs.start_message_move_task(
    SourceArn=dlq_arn,
    DestinationArn=source_queue_arn,
    MaxNumberOfMessagesPerSecond=50
)

print(response["TaskHandle"])
```

The operation returns a task handle that can be used to monitor the movement task.

### 8.4 Important redrive considerations

Before redriving messages, consider:

* Has the original processing failure been fixed?

* Can the consumer safely process these messages again?

* Could retrying thousands of messages overload the database?

* Should messages be moved gradually?

* Are the original messages still valid?

* Do FIFO ordering requirements need special handling?

FIFO ordering warning: Moving messages to a DLQ can break the original order of messages in a FIFO message group. If strict ordering is essential, consider whether using a DLQ is appropriate for that workflow.

### 8.5 Native redrive versus manual republishing

There are two common approaches:

| Approach            | Description                                                                     |
| ------------------- | ------------------------------------------------------------------------------- |
| Native redrive      | SQS moves messages using its message movement task                              |
| Manual republishing | Application reads messages from the DLQ and sends new messages to another queue |

Native redrive is generally preferable for routine recovery because SQS manages the movement process.

Manual republishing is useful when you need to transform, filter, validate, or enrich messages before retrying them.

### 9\. Poison-pill messages and failure isolation

A poison-pill message is a message that repeatedly causes a consumer to fail.

It is particularly problematic because the same message can repeatedly consume processing resources without producing any useful result.

### 9.1 Understanding poison-pill messages

Imagine a queue containing:

```text
Message 1: Valid order
Message 2: Valid order
Message 3: Invalid order
Message 4: Valid order
Message 5: Valid order
```

Suppose the consumer cannot process Message 3 because its structure is invalid.

The message repeatedly becomes available after the visibility timeout.

Depending on your consumer architecture, it can repeatedly consume resources and delay processing.

Examples of poison-pill messages include:

* Malformed JSON.

* Missing mandatory fields.

* Unsupported message versions.

* Invalid business data.

* Unexpected data types.

* Messages that trigger deterministic application exceptions.

### 9.2 Failure isolation with DLQs

A DLQ isolates messages that repeatedly fail.

```text
                Source Queue
                     |
                     v
                  Consumer
                     |
             +-------+-------+
             |               |
          Success          Failure
             |               |
             v               v
          Delete       Retry delivery
                             |
                      Max receive count
                             |
                             v
                           DLQ
```

This allows healthy messages to continue processing while problematic messages are investigated separately.

### 9.3 Transient failures versus permanent failures

A critical architectural decision is distinguishing between temporary and permanent failures.

| Failure type       | Example                          | Recommended handling             |
| ------------------ | -------------------------------- | -------------------------------- |
| Transient          | Database temporarily unavailable | Retry                            |
| Transient          | HTTP 503                         | Retry with backoff               |
| Permanent          | Invalid JSON                     | Isolate                          |
| Permanent          | Missing mandatory field          | Isolate                          |
| Business rejection | Insufficient account balance     | Apply business-specific handling |
| Unknown            | Unexpected exception             | Log and retry cautiously         |

Do not automatically send every failed message to a DLQ after its first exception.

Temporary infrastructure failures should have an opportunity to recover.

Likewise, do not retry permanently invalid messages indefinitely.

### 9.4 Failure isolation in microservices

Consider an e-commerce architecture:

* Order Service produces order events.

* Payment Service processes payments.

* Inventory Service updates stock.

* Notification Service sends emails.

Each service has its own queue and consumer.

```text
              Order Service
                    |
                    v
                  SNS
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Orders    Payments  Inventory
        Queue      Queue     Queue
          |         |         |
          v         v         v
       Consumer  Consumer  Consumer
          |         |         |
          v         v         v
         DLQ       DLQ       DLQ
```

If the Payment Service fails, its messages can be isolated in its DLQ without necessarily preventing Inventory or Notification processing.

This is an important benefit of asynchronous microservice architectures.

### 10\. Idempotent consumers and duplicate processing

Idempotency is one of the most important concepts in reliable SQS application development.

Remember that SQS Standard queues provide at-least-once delivery.

This means consumers must be prepared to receive duplicate messages.

### 10.1 What is idempotency?

An operation is idempotent if performing it multiple times produces the same final result as performing it once.

Mathematically:

f(f(x)) = f(x)

Consider an operation that sets an order status:

```python
order.status = "PAID"
```

Executing this operation repeatedly produces the same final state.

Now consider a payment operation:

```python
account.balance -= 100
```

Executing it three times subtracts 300 instead of 100.

The second operation is not naturally idempotent.

### 10.2 Why duplicate messages happen

Imagine this sequence:

* Consumer receives a payment message.

* Payment is successfully processed.

* Consumer crashes before deleting the SQS message.

* Visibility timeout expires.

* Another consumer receives the same message.

* Payment is processed again.

Without idempotency, the customer might be charged twice.

This is why successful business processing and successful message deletion must be treated as separate operations.

### 10.3 Using message IDs for deduplication

One common approach is maintaining a database table of processed messages.

For example:

```sql
CREATE TABLE processed_messages (
    message_id VARCHAR(255) PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Before processing a message, check whether its identifier already exists.

A simplified Python example:

```python
def process_message(message):
    message_id = message["MessageId"]

    if is_already_processed(message_id):
        return

    process_order(message["Body"])

    mark_as_processed(message_id)
```

This example illustrates the concept, but it has an important concurrency problem.

Two consumers could simultaneously check the database, both see that the message has not been processed, and both execute the business operation.

You need an atomic mechanism to prevent that race condition.

### 10.4 Atomic idempotency with database transactions

A better approach is to use a unique constraint and a transaction.

Conceptually:

```sql
BEGIN;

INSERT INTO processed_messages (message_id)
VALUES ('message-123')
ON CONFLICT DO NOTHING;

-- Only execute the business operation
-- if this transaction inserted the new record.

COMMIT;
```

The idempotency record and business changes should be committed in the same database transaction whenever possible.

This ensures that:

* A failed transaction does not leave a false processed record.

* Concurrent consumers cannot independently process the same message.

* Duplicate deliveries can be safely ignored.

For payment processing, also use the payment provider's idempotency mechanism where available.

### 10.5 Business-level idempotency keys

Using the SQS message ID is not always sufficient.

A producer might send the same business event twice, resulting in two different SQS message IDs.

For example:

```json
{
  "event_id": "evt-10001",
  "order_id": "ORD-20001",
  "event_type": "payment_requested",
  "amount": 150
}
```

Here, `event_id` is an application-generated identifier.

It remains the same when the producer retries sending the same logical event.

This makes it a stronger business-level idempotency key.

### 10.6 SQS FIFO deduplication versus consumer idempotency

These are related but different concepts.

| FIFO deduplication                                                                       | Consumer idempotency                                                        |
| ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------------- |
| Prevents duplicate messages from being introduced during the FIFO deduplication interval | Prevents duplicate business operations                                      |
| Operates at the queue level                                                              | Operates at the application level                                           |
| Uses deduplication IDs or content-based deduplication                                    | Uses application-level identifiers and persistent state                     |
| Has a five-minute deduplication interval                                                 | Can operate for as long as your application retains its idempotency records |

FIFO deduplication does not eliminate the need for idempotent consumers.

Important: SQS does not provide exactly-once execution of your application's business logic.

A reliable application must implement its own idempotency guarantees.

### 11\. Error handling and resilient consumer architectures

Now let's combine these concepts into a reliable consumer architecture.

### 11.1 A basic resilient consumer

A consumer should generally follow this sequence:

* Receive a message.

* Validate the message.

* Check its idempotency key.

* Process the business operation.

* Commit the business transaction.

* Delete the SQS message.

The deletion should happen only after successful processing.

A simplified Python implementation:

```python
import json
import boto3

sqs = boto3.client("sqs")

def process_order(order):
    # Business logic
    print("Processing:", order["order_id"])

def consume(queue_url):

    response = sqs.receive_message(
        QueueUrl=queue_url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20,
        AttributeNames=[
            "ApproximateReceiveCount"
        ]
    )

    for message in response.get("Messages", []):

        try:
            body = json.loads(message["Body"])

            process_order(body)

            sqs.delete_message(
                QueueUrl=queue_url,
                ReceiptHandle=message["ReceiptHandle"]
            )

        except Exception as error:
            print("Processing failed:", error)

            # Do not delete the message.
            # SQS can make it available again
            # after the visibility timeout.
```

This example demonstrates the basic reliability behavior.

A production consumer would additionally require:

* Structured logging.

* Message validation.

* Idempotency.

* Exception classification.

* Appropriate retry policies.

* Graceful shutdown.

* Metrics and tracing.

* Protection against excessive retry attempts.

### 11.2 Resilient consumer architecture

![Using Amazon SQS dead-letter queues to replay messages | AWS Compute Blog](https://images.openai.com/static-rsc-4/iwWzonFX1M6pjsdROyeNzUknYC6FdLkUvwzQxPtODQta2y0-dPNy6aLgM61wX6qu0pBWw2EypHDHYUieA4oKqn3sHPZxGirkpTQ5NoXGgd0lw-vV5qyivuy4aNjytXHrqtADUMDM7N15fdJ_7wof-bYK9TiEnMrZINOrxoY_syfYmSRd6T-nF4wrL_1aN2YI?purpose=fullsize)

A production architecture typically includes:

| Component           | Responsibility                           |
| ------------------- | ---------------------------------------- |
| SQS source queue    | Stores incoming work                     |
| Consumer            | Processes messages                       |
| Visibility timeout  | Prevents immediate concurrent redelivery |
| Idempotency store   | Prevents duplicate business operations   |
| Redrive policy      | Moves repeatedly unsuccessful messages   |
| DLQ                 | Isolates failed messages                 |
| CloudWatch          | Monitors queue health                    |
| CloudWatch alarms   | Detects abnormal conditions              |
| Logging and tracing | Helps diagnose failures                  |

### 11.3 Consumer concurrency and reliability

Increasing the number of consumers can improve throughput, but it also increases the potential load on downstream services.

For example:

```text
                 SQS Queue
                     |
          +----------+----------+
          |          |          |
          v          v          v
       Worker 1   Worker 2   Worker 3
          |          |          |
          +----------+----------+
                     |
                     v
                 PostgreSQL
```

If PostgreSQL supports only 100 concurrent connections, launching 500 consumers could overload the database.

You should consider:

* Maximum consumer concurrency.

* Database connection limits.

* API rate limits.

* Average processing duration.

* Visibility timeout.

* Queue depth.

* Message age.

For Lambda consumers, configure event source mapping concurrency and batching settings appropriately.

For ECS consumers, use controlled task scaling and application-level concurrency limits.

### 11.4 Handling batches correctly

SQS supports receiving up to 10 messages in one `ReceiveMessage` request.

However, if you process a batch and one message fails, you should avoid unnecessarily retrying every successful message.

For Lambda event source mappings, enable ReportBatchItemFailures to return individual failed message identifiers.

This is called partial batch response.

It is especially important for FIFO queues, where you should stop processing subsequent messages in the same message group after a failure if preserving order is required.

### 11.5 Resilient architecture principles

For production applications, follow these principles:

* Never assume a message is delivered only once.

* Never delete a message before successful processing.

* Configure visibility timeout based on processing duration.

* Use idempotency for business operations.

* Configure a DLQ for repeated failures.

* Monitor DLQ message counts.

* Distinguish transient and permanent errors.

* Avoid uncontrolled retries.

* Scale consumers according to downstream capacity.

* Design recovery procedures before production deployment.

### 12\. Putting everything together: Complete failure and recovery lifecycle

Let's summarize how all the mechanisms work together in a production system.

![AWS SQS Retention Period](https://images.openai.com/static-rsc-4/Jnz6Xh6Sy2HZhRrsQS8tQW4aDgl-Lsts02ET-GmZo_WC41Gs4AqRoxsjjW-o7TfVrzVaiUo_JYHth4HL0zCy0vPyr3e4VjmZxx-1tp_LWEnY1BpszpCvygcbOn5dBqETjKt8hIAOCSOA6rC4aD0qmsaitklZj6MQoq30AVMLzZ4nkB-MWud1vb_8Yz2bG5VN?purpose=fullsize)

Consider an order-processing workflow:

| Step | Event                           | SQS behavior                         |
| ---- | ------------------------------- | ------------------------------------ |
| 1    | Producer sends an order         | Message enters source queue          |
| 2    | Consumer receives it            | Visibility timeout starts            |
| 3    | Consumer processing fails       | Message is not deleted               |
| 4    | Visibility timeout expires      | Message becomes available again      |
| 5    | Consumer retries                | Receive count increases              |
| 6    | Maximum receive count reached   | Message moves to DLQ                 |
| 7    | Engineering team investigates   | Failed message is inspected          |
| 8    | Original problem is fixed       | Message becomes eligible for redrive |
| 9    | Message returns to source queue | Consumer receives it again           |
| 10   | Processing succeeds             | Message is deleted                   |

The idempotency mechanism ensures that retrying an already completed business operation does not cause duplicate transactions.

### 13\. Important concepts to remember

| Concept                | Main responsibility                            |
| ---------------------- | ---------------------------------------------- |
| Visibility timeout     | Temporarily hides received messages            |
| Message redelivery     | Makes unsuccessful messages available again    |
| Receive count          | Tracks message delivery attempts approximately |
| Redrive policy         | Defines DLQ destination and receive threshold  |
| DLQ                    | Isolates repeatedly unsuccessful messages      |
| Redrive allow policy   | Restricts which queues can use a DLQ           |
| Message redrive        | Moves messages out of a DLQ                    |
| Poison-pill message    | Repeatedly causes processing failures          |
| Idempotency            | Prevents duplicate business operations         |
| Partial batch response | Allows individual batch failures to be retried |

### 14\. Important AWS limits and behaviors

| Feature                                     | Limit / behavior       |
| ------------------------------------------- | ---------------------- |
| Maximum visibility timeout                  | 12 hours               |
| Maximum message retention                   | 14 days                |
| Maximum messages per ReceiveMessage request | 10                     |
| Maximum FIFO deduplication interval         | 5 minutes              |
| Maximum source queue ARNs in byQueue        | 10                     |
| Maximum DLQ message movement velocity       | 500 messages/second    |
| Standard queue delivery                     | At-least-once          |
| FIFO ordering                               | Within a message group |

### 15\. How this module connects to the rest of the SQS course

You have now covered the reliability mechanisms that make SQS suitable for production workloads.

The next module builds on these concepts by introducing SQS security and infrastructure access control.

Next: Module 5 — SQS Security, IAM, Encryption, and Networking

We will cover:

* SQS security architecture and shared responsibility.

* IAM identities and SQS permissions.

* Identity-based policies and resource-based policies.

* Queue policies and cross-account access.

* Least-privilege access control.

* Server-side encryption with SQS-managed keys.

* AWS KMS customer-managed keys.

* KMS key policies and encryption permissions.

* VPC endpoints and private SQS access.

* Secrets, credentials, and secure application integration.
