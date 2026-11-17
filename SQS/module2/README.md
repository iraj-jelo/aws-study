### Module 2 — Queues, Messages, and Message Lifecycle

AWS SQS · Intermediate · Queue Operations and Message Processing

In Module 1, we explored the architecture of Amazon SQS, messaging concepts, Standard and FIFO queues, and delivery guarantees.

Now we'll move from architecture to implementation.

The goal of this module is to understand how applications create queues, publish messages, retrieve messages, process them, and remove them from SQS.

We'll use AWS CLI (Bash), Python, Boto3, and Pulumi (Python) throughout the module.

### 1\. Creating and configuring SQS queues

An SQS queue is a managed AWS resource that temporarily stores messages until consumers retrieve and process them.

A typical application has two main components:

* Producer: Creates and sends messages to the queue.

* Consumer: Retrieves messages, processes them, and deletes them after successful processing.

![Complete Step-by-Step Guide: Creating AWS SQS Queues with AWS CDK (TypeScript) | by Rohit Chaware | Medium](https://images.openai.com/static-rsc-4/Dc4TXysl8IThk6i6RIZCvdTG2xFQqLvVnp03tHYxsdPmmL4SOS8tQq38WlQCtwp_z8MToanLz_Y1YsMTRMuVL5eiMUvQssgm7Q0h02moanugP-Lk3CePATKW2dyqFSGeQYXehQQJ6HuOYEbR5zeqWO8U1wFsBEvCSFGr9f-4JFL8dYGTQBllRgDOtbtdRfw9?purpose=fullsize)

### 1.1 Queue types

When creating an SQS queue, you choose between two queue types:

| Feature          | Standard      | FIFO                                                              |
| ---------------- | ------------- | ----------------------------------------------------------------- |
| Message ordering | Best-effort   | Strict ordering within a message group                            |
| Delivery         | At-least-once | Exactly-once send deduplication within the deduplication interval |
| Throughput       | Very high     | Depends on FIFO throughput configuration                          |
| Queue name       | Normal name   | Ends with .fifo                                                   |

For example:

* `orders-queue` — Standard queue.

* `orders-queue.fifo` — FIFO queue.

You cannot change an existing Standard queue into a FIFO queue or vice versa. You must create a new queue.

### 1.2 Important queue configuration attributes

When creating an SQS queue, you can configure several attributes.

| Attribute                     | Purpose                                               |
| ----------------------------- | ----------------------------------------------------- |
| VisibilityTimeout             | How long a received message remains invisible         |
| MessageRetentionPeriod        | How long SQS retains messages                         |
| DelaySeconds                  | How long messages remain unavailable after being sent |
| ReceiveMessageWaitTimeSeconds | Default long-polling duration                         |
| MaximumMessageSize            | Maximum permitted message payload size                |
| RedrivePolicy                 | Configures a dead-letter queue                        |
| KmsMasterKeyId                | Configures customer-managed KMS encryption            |

We'll examine these attributes throughout this module and the next modules.

### 1.3 Creating a Standard queue using AWS CLI

First, create a queue:

```bash
aws sqs create-queue \
  --queue-name orders-queue \
  --region eu-west-2
```

Example response:

```json
{
  "QueueUrl": "https://sqs.eu-west-2.amazonaws.com/123456789012/orders-queue"
}
```

The queue URL is important because most SQS operations require it.

You can retrieve the queue URL later:

```bash
aws sqs get-queue-url \
  --queue-name orders-queue \
  --region eu-west-2
```

To inspect queue attributes:

```bash
aws sqs get-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attribute-names All
```

### 1.4 Creating a FIFO queue

FIFO queues require a `.fifo` suffix.

```bash
aws sqs create-queue \
  --queue-name orders-queue.fifo \
  --attributes \
    FifoQueue=true,\
    ContentBasedDeduplication=true \
  --region eu-west-2
```

Here:

* `FifoQueue=true` identifies the queue as FIFO.

* `ContentBasedDeduplication=true` enables content-based deduplication.

Content-based deduplication uses a hash of the message body to identify duplicate messages within the deduplication interval.

FIFO queues also require a `MessageGroupId` when sending messages.

### 1.5 Configuring queue attributes

You can modify supported queue attributes after creation.

For example, configure a 60-second visibility timeout:

```bash
aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes VisibilityTimeout=60
```

Configure a 5-minute delivery delay:

```bash
aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes DelaySeconds=300
```

Configure long polling with a 20-second wait:

```bash
aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes ReceiveMessageWaitTimeSeconds=20
```

Important: Queue attributes have different constraints and update behavior. For example, changing message retention can affect existing messages. Always check the relevant AWS documentation before changing production queues.

### 1.6 Creating an SQS queue with Pulumi (Python)

Since Pulumi is our preferred IaC tool, let's see how to define the same queue programmatically.

Install the AWS provider:

```bash
pip install pulumi pulumi-aws
```

Create `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

orders_queue = aws.sqs.Queue(
    "orders-queue",
    name="orders-queue",
    visibility_timeout_seconds=60,
    message_retention_seconds=345600,
    delay_seconds=0,
    receive_wait_time_seconds=20,
    max_message_size=1048576,
)

pulumi.export("queue_url", orders_queue.url)
pulumi.export("queue_arn", orders_queue.arn)
```

Deploy:

```bash
pulumi stack init development
pulumi config set aws:region eu-west-2

pulumi preview
pulumi up
```

This creates a Standard queue with:

* 60-second visibility timeout.

* Four-day message retention.

* No delivery delay.

* 20-second long polling.

* 1 MiB maximum message size.

Notice that Pulumi manages the infrastructure, while Boto3 will manage the messages.

This separation is important:

* Pulumi: Creates and configures queues.

* Boto3: Sends, receives, processes, and deletes messages.

### 2\. Sending messages using AWS CLI and Python Boto3

Once a queue exists, producers can send messages to it.

Imagine an e-commerce application where customers place orders.

Instead of making the order API directly communicate with every downstream service, it publishes an order event to SQS.

![This is the ONLY resource you need to learn AWS SQS (IN MOST Simple Way) | Sandip Das](https://images.openai.com/static-rsc-4/Yq8BIdw-RwNOQOU9eXB5PhiB8p4DIA0jY4XOO0G-T7WbaHgUQEuzyHO_6HEGLi416VBuk5FuO6U-xqJ3-z8fclA3C5GNdCW3PNEZqflh7PvbxlTbYvL3-g1ttWecOlQMh6seOhC8lpmQRegXEZdqCQrDoODDmEg86YlUFJFSoxeF67fnqZuCrjgUozLKV0Ur?purpose=fullsize)

The producer might send a message containing:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "CUS-2001",
  "amount": 149.99,
  "currency": "USD"
}
```

The consumer can retrieve this message and perform the actual order processing.

### 2.1 Sending a message using AWS CLI

The AWS CLI provides the `send-message` command.

```bash
aws sqs send-message \
  --queue-url "$QUEUE_URL" \
  --message-body '{
    "order_id": "ORD-1001",
    "customer_id": "CUS-2001",
    "amount": 149.99
  }' \
  --region eu-west-2
```

Example response:

```json
{
  "MD5OfMessageBody": "example-md5-hash",
  "MessageId": "abc123-example-message-id"
}
```

Two important values:

* `MessageId`: Identifies the message assigned by SQS.

* `MD5OfMessageBody`: A checksum that can help verify the message body.

The Message ID is not the same as an application-level business identifier such as `order_id`.

### 2.2 Sending a message using Python Boto3

Install Boto3:

```bash
pip install boto3
```

Create `producer.py`:

```python
import json
import boto3

sqs = boto3.client(
    "sqs",
    region_name="eu-west-2"
)

QUEUE_URL = "YOUR_QUEUE_URL"

order = {
    "order_id": "ORD-1001",
    "customer_id": "CUS-2001",
    "amount": 149.99,
    "currency": "USD"
}

response = sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=json.dumps(order)
)

print("Message sent!")
print("Message ID:", response["MessageId"])
```

The important method is:

```python
sqs.send_message()
```

Its main parameters include:

| Parameter               | Description                                      |
| ----------------------- | ------------------------------------------------ |
| QueueUrl                | Destination queue                                |
| MessageBody             | Actual message content                           |
| DelaySeconds            | Delays this message's delivery (Standard queues) |
| MessageAttributes       | Additional structured metadata                   |
| MessageSystemAttributes | Supported system-level attributes                |

Boto3 uses the AWS credential provider chain. In production, prefer IAM roles rather than hardcoding AWS access keys.

### 2.3 Sending messages to a FIFO queue

FIFO queues require two additional identifiers:

* `MessageGroupId`

* `MessageDeduplicationId` (unless content-based deduplication is enabled)

Example:

```python
response = sqs.send_message(
    QueueUrl=FIFO_QUEUE_URL,
    MessageBody=json.dumps(order),
    MessageGroupId="customer-2001",
    MessageDeduplicationId="order-1001"
)
```

Here, all messages belonging to `customer-2001` are assigned to the same message group.

This is useful when orders for a particular customer must be processed in sequence.

The deduplication ID helps SQS identify repeated send requests within its deduplication interval.

We'll explore FIFO processing in detail in Module 3.

### 3\. Receiving and deleting messages

Sending a message is only half of the messaging process.

A consumer must retrieve the message, process it, and explicitly delete it after successful processing.

### 3.1 Receiving messages using AWS CLI

Use:

```bash
aws sqs receive-message \
  --queue-url "$QUEUE_URL" \
  --max-number-of-messages 5 \
  --wait-time-seconds 20 \
  --region eu-west-2
```

Important parameters:

| Parameter                 | Purpose                                             |
| ------------------------- | --------------------------------------------------- |
| --queue-url               | Identifies the queue                                |
| --max-number-of-messages  | Maximum number of messages to retrieve              |
| --wait-time-seconds       | Enables long polling                                |
| --visibility-timeout      | Overrides visibility timeout for retrieved messages |
| --attribute-names         | Requests system attributes                          |
| --message-attribute-names | Requests custom message attributes                  |

SQS returns a response similar to:

```json
{
  "Messages": [
    {
      "MessageId": "abc123",
      "ReceiptHandle": "AQEB-example...",
      "Body": "{\"order_id\":\"ORD-1001\"}"
    }
  ]
}
```

There are two particularly important fields.

MessageId

Identifies the message.

ReceiptHandle

A temporary identifier associated with a particular receive operation.

The receipt handle is required to delete the message or change its visibility timeout.

A common mistake is using `MessageId` when deleting a message. SQS requires the receipt handle instead.

### 3.2 Deleting a message using AWS CLI

After successful processing:

```bash
aws sqs delete-message \
  --queue-url "$QUEUE_URL" \
  --receipt-handle "$RECEIPT_HANDLE" \
  --region eu-west-2
```

The message is then removed from the queue.

Important: Receiving a message does not automatically delete it.

This behavior is fundamental to SQS reliability. If a consumer crashes before deleting a message, SQS can make that message available again after its visibility timeout expires.

### 3.3 Receiving messages using Python Boto3

Create `consumer.py`:

```python
import json
import boto3

sqs = boto3.client(
    "sqs",
    region_name="eu-west-2"
)

QUEUE_URL = "YOUR_QUEUE_URL"

response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=5,
    WaitTimeSeconds=20
)

messages = response.get("Messages", [])

for message in messages:
    try:
        order = json.loads(message["Body"])

        print("Processing order:", order["order_id"])

        # Perform business processing here.

        sqs.delete_message(
            QueueUrl=QUEUE_URL,
            ReceiptHandle=message["ReceiptHandle"]
        )

        print("Message deleted successfully")

    except Exception as error:
        print("Processing failed:", error)
```

This example demonstrates the basic consumer workflow.

However, notice an important detail: if processing fails, the code doesn't delete the message.

Consequently, after the visibility timeout expires, the message becomes available again.

In production, you should also implement proper logging, error classification, idempotency, and retry handling.

### 3.4 The correct processing order

1\. Receive message

Consumer retrieves the message.

2\. Process message

Perform the business operation.

3\. Delete message

Confirm successful processing to SQS.

If processing fails, don't delete the message. It can become available again.

This pattern is called receive-process-delete.

It is the foundation of reliable SQS consumers.

### 4\. Message bodies, attributes, and metadata

An SQS message consists of more than just its body.

Understanding the distinction between message content, custom attributes, and system-generated metadata is important when designing messaging systems.

### 4.1 Message body

The message body contains the actual data that the producer wants to deliver.

For example:

```json
{
  "event_type": "order.created",
  "order_id": "ORD-1001",
  "customer_id": "CUS-2001",
  "total": 149.99
}
```

The body is generally a string, so JSON serialization is a common approach when using Python.

```python
import json

body = json.dumps({
    "event_type": "order.created",
    "order_id": "ORD-1001",
    "total": 149.99
})
```

The consumer deserializes it:

```python
order = json.loads(message["Body"])
```

SQS doesn't understand the business meaning of your JSON structure. It transports the message; your application interprets it.

### 4.2 Message attributes

Message attributes provide additional structured metadata without requiring consumers to parse the message body.

For example, you might want to include:

* Event type.

* Application version.

* Environment.

* Tenant identifier.

* Content format.

Example:

```python
response = sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=json.dumps(order),
    MessageAttributes={
        "event_type": {
            "DataType": "String",
            "StringValue": "order.created"
        },
        "environment": {
            "DataType": "String",
            "StringValue": "production"
        },
        "priority": {
            "DataType": "Number",
            "StringValue": "1"
        }
    }
)
```

Message attributes support several data types:

| Data type | Example     |
| --------- | ----------- |
| String    | production  |
| Number    | 100         |
| Binary    | Binary data |

Number attributes are represented through their string values in the API.

To retrieve custom attributes:

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=5,
    MessageAttributeNames=["All"],
    WaitTimeSeconds=20
)
```

Then:

```python
for message in response.get("Messages", []):
    attributes = message.get("MessageAttributes", {})

    event_type = attributes.get("event_type", {})

    print(event_type.get("StringValue"))
```

### 4.3 System attributes and metadata

SQS also maintains metadata about messages.

Examples include:

| Metadata                         | Meaning                                      |
| -------------------------------- | -------------------------------------------- |
| MessageId                        | SQS-generated message identifier             |
| ReceiptHandle                    | Identifier for the received message instance |
| MD5OfBody                        | Checksum of the message body                 |
| SentTimestamp                    | Time the message was sent                    |
| ApproximateReceiveCount          | Approximate number of times received         |
| ApproximateFirstReceiveTimestamp | Approximate time first received              |
| SenderId                         | Identifier associated with the sender        |

You can request system attributes:

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=5,
    MessageSystemAttributeNames=[
        "All"
    ],
    WaitTimeSeconds=20
)
```

Inspect them:

```python
for message in response.get("Messages", []):
    print("Message ID:", message["MessageId"])

    print(
        "Receive count:",
        message["Attributes"].get("ApproximateReceiveCount")
    )

    print(
        "Sent timestamp:",
        message["Attributes"].get("SentTimestamp")
    )
```

The distinction is:

* Message body: Business data.

* Message attributes: Producer-defined metadata.

* System attributes: SQS-managed metadata.

### 4.4 When should you use message attributes?

Consider a system processing different types of events:

```json
{
  "event_id": "EVT-1001",
  "data": {
    "order_id": "ORD-1001"
  }
}
```

You could put `event_type` inside the JSON body or in a message attribute.

Using an attribute can be useful when consumers need metadata independently of the body.

It also becomes particularly useful with SNS subscription filter policies, which we'll explore in the SNS course.

### 5\. Message size limits and payload considerations

SQS is designed to transport messages, not necessarily large application files.

This distinction matters when designing distributed applications.

### 5.1 Maximum message size

The current SQS maximum message size is:

### 1 MiB

1,048,576 bytes

The minimum message size is 1 byte.

Message attributes contribute to the total message size, so the body alone cannot consume the entire limit if attributes are also present. Amazon Simple Queue Service +1

### 5.2 What if the payload is larger than 1 MiB?

Imagine a document-processing application that needs to process a 50 MB PDF file.

Sending the entire PDF through SQS is not appropriate.

Instead, use an S3-based message reference pattern.

![AWS SQS Overview - KodeKloud](https://images.openai.com/static-rsc-4/_CvLEXdZhY0Ofljmh1Ps_Bf1jBJkciUKB-2pi-erCpHW7BlTDzERRlTtAFcLfqgdcIacJUsckuH6N7AiZdtyEaezT7VtVa_by3oxzTYwynFofGoA0vb4qsBqLa4teZLDe5YN5j19lCw0zt-G0c8WULxHrF4yLEiu4QFs4G9SEWHMZqd1v0wobX6JPP9te6vc?purpose=fullsize)

The architecture works as follows:

* The producer uploads the PDF to S3.

* S3 stores the actual file.

* The producer sends a small SQS message containing the S3 bucket and object key.

* The consumer receives the SQS message.

* The consumer downloads the PDF directly from S3.

* The consumer processes the file.

Example SQS message:

```json
{
  "event_type": "document.uploaded",
  "bucket": "application-documents",
  "object_key": "uploads/document-1001.pdf"
}
```

This architecture separates:

* SQS: Message delivery and coordination.

* S3: Large payload storage.

AWS also provides Extended Client Libraries for Java and Python that use S3 to store large payloads while sending references through SQS. Their documented extended payload support reaches 2 GB. Amazon Simple Queue Service

### 5.3 Important payload design considerations

A good SQS message should generally be:

* Small and self-contained where practical.

* Structured using JSON or another agreed format.

* Versioned when message schemas may evolve.

* Identifiable through a business-level ID.

* Free of unnecessary sensitive information.

For example:

```json
{
  "event_id": "EVT-1001",
  "event_version": "1.0",
  "event_type": "order.created",
  "occurred_at": "2026-11-02T10:00:00Z",
  "data": {
    "order_id": "ORD-1001"
  }
}
```

This envelope pattern makes messages easier to maintain as applications evolve.

### 6\. Short polling and long polling

Polling is the mechanism through which consumers ask SQS whether messages are available.

SQS supports two polling approaches.

### 6.1 Short polling

Short polling returns immediately after checking a subset of SQS servers.

If messages are available on the sampled servers, SQS returns them.

If no messages are found, SQS returns an empty response.

![AWS SQS: Decode the Secret Power Of Short & Long Polling - DEV Community](https://images.openai.com/static-rsc-4/0J9xwr3sMwlTINmktdbLun2RTHXvQGPAvXp9ujIMUBufwFZZ9LEYMXmq9p1_OjpnvK5sMcoNw6RdrB1Nra_-1-Itw2K2nwCgdh8NbC8VVrn1Zpqy87pZ7GHUxgTNLLXcdeyBf6nl6X_VVLauQMHkdaV4fJ28IYXpetRsrmyOFXHwmJBx_vQJ3K8UoAuhZtN0?purpose=fullsize)

Example:

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=0
)
```

Characteristics:

* Returns quickly.

* May return empty responses even when messages exist elsewhere in the distributed system.

* Can produce more API requests.

* Can increase unnecessary polling costs.

### 6.2 Long polling

Long polling allows SQS to wait for messages to become available.

Instead of immediately returning an empty response, SQS waits for up to the configured duration.

![AWS Application Integration Services | AWS Cheat Sheet](https://images.openai.com/static-rsc-4/QzsDo7XNd3uFmAibe8J4s-VHoSl8zRh74mRX_xczsbm09jiNh9eWdcWBVe-JoK1B_r8_usQMAbY2eWOysJTMHc58ExUj0twaElG-es7Q-pPlbu-yOCuc-111JKMXfm0KXSj67N05HboqvBH3YzYdIz7SI29jO1YGdF5V7SrXKj6kR3hgxP2Emk7t4eHUPMp8?purpose=fullsize)

Example:

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)
```

The maximum long-polling duration is 20 seconds.

Long polling:

* Reduces empty responses.

* Reduces unnecessary API requests.

* Reduces false empty responses.

* Can lower costs for consumers.

* Returns available messages without waiting for the full timeout.

Amazon Simple Queue Service +1

### 6.3 Short polling versus long polling

| Characteristic         | Short polling      | Long polling                  |
| ---------------------- | ------------------ | ----------------------------- |
| Wait duration          | 0 seconds          | Up to 20 seconds              |
| Response               | Immediate          | Waits for messages or timeout |
| Empty responses        | More frequent      | Less frequent                 |
| API request frequency  | Potentially higher | Potentially lower             |
| Cost efficiency        | Usually lower      | Usually better                |
| Typical recommendation | Special cases      | Most consumers                |

### 6.4 Queue-level versus request-level polling

You can configure long polling at two levels.

Queue-level configuration:

```bash
aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes ReceiveMessageWaitTimeSeconds=20
```

This establishes the default polling behavior for the queue.

Request-level configuration:

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    WaitTimeSeconds=10
)
```

The request-level value overrides the queue-level default for that receive request.

One important production consideration: your HTTP client read timeout must be longer than the long-polling wait duration. Otherwise, your application might terminate the request before SQS responds. Amazon Simple Queue Service

### 7\. Visibility timeout and message availability

This is one of the most important concepts in SQS.

When a consumer receives a message, SQS doesn't immediately remove it.

Instead, SQS temporarily hides the message from other consumers.

This period is called the visibility timeout.

### 7.1 How visibility timeout works

Suppose:

* An order message is available in SQS.

* Consumer A receives it.

* The visibility timeout is 60 seconds.

SQS makes that message temporarily invisible to other consumers.

![The Essential Guide to Amazon SQS | Baselime Blog](https://images.openai.com/static-rsc-4/wN1A5UMhbrg4revL34-DdsMlYzCzN4jQLTabxSLVZwU-uv80oVnNzPPlqzPOU1RnBU7sROhEGp0xjop-CbpChp2wCiI8P3SsBORnImF8r_VvVBQsOkcouVb6K6n8KqwuLPo8B8UQEy79xW5Wl5q88YV7qyUbJKSSz_BGaYCpYG7k4Yu3kdRBlzQ5LruHWJKs?purpose=fullsize)

During those 60 seconds:

* Consumer A processes the message.

* Consumer B normally cannot retrieve that message.

* The message remains stored in SQS.

If Consumer A successfully processes the order and deletes the message, it is removed.

If Consumer A crashes without deleting it, the message becomes available again after the visibility timeout expires.

### 7.2 Default and maximum values

| Setting                    | Value      |
| -------------------------- | ---------- |
| Default visibility timeout | 30 seconds |
| Minimum                    | 0 seconds  |
| Maximum                    | 12 hours   |

Amazon Simple Queue Service +1

### 7.3 Changing visibility timeout

You can change the visibility timeout for an individual received message.

For example, if processing takes longer than expected:

```python
sqs.change_message_visibility(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle,
    VisibilityTimeout=120
)
```

This gives the consumer another 120 seconds from the change request to finish processing.

You can also make the message immediately available again:

```python
sqs.change_message_visibility(
    QueueUrl=QUEUE_URL,
    ReceiptHandle=receipt_handle,
    VisibilityTimeout=0
)
```

This is useful when a consumer determines it cannot process a message and wants another consumer to try.

### 7.4 Choosing the right visibility timeout

Suppose your application has these processing durations:

| Task                        | Average duration |
| --------------------------- | ---------------- |
| Sending an email            | 2 seconds        |
| Generating a report         | 30 seconds       |
| Processing an image         | 90 seconds       |
| Processing a large document | 5 minutes        |

The visibility timeout should provide sufficient time for processing and deletion.

Setting it too low can cause multiple consumers to process the same message concurrently.

Setting it too high can delay retries when a consumer crashes.

For variable-duration jobs, consumers can periodically extend visibility using `ChangeMessageVisibility`, effectively implementing a heartbeat.

One limitation: the total visibility period from the original receive request cannot exceed 12 hours. Amazon Simple Queue Service +1

Critical distinction: Visibility timeout is not a guarantee of exactly-once processing. Your application must still handle duplicate deliveries.

We'll revisit this in Module 4.

### 8\. Message retention period and delivery delay

These two settings control different aspects of message availability.

* Message retention period: How long SQS keeps a message before automatically deleting it if it hasn't been deleted by a consumer.

* Delivery delay: How long SQS waits before making a newly sent message available to consumers.

### 8.1 Message retention period

By default, SQS retains messages for four days.

You can configure retention between one minute and 14 days.

| Configuration | Duration   |
| ------------- | ---------- |
| Default       | 4 days     |
| Minimum       | 60 seconds |
| Maximum       | 14 days    |

Amazon Simple Queue Service +1

Example:

```bash
aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes MessageRetentionPeriod=604800
```

`604800` seconds equals seven days.

Imagine a consumer application is offline for three days.

If the queue's retention period is four days, messages can remain available for processing when the consumer comes back online.

However, if a message reaches its retention expiration, SQS automatically removes it.

Important: Reducing the retention period can also cause existing messages that are already older than the new limit to expire.

### 8.2 Delivery delay

Delivery delay postpones the availability of a newly sent message.

For example, imagine an e-commerce application that wants to send a reminder 10 minutes after an order is created.

You can configure:

```python
sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody=json.dumps({
        "order_id": "ORD-1001",
        "event_type": "order.reminder"
    }),
    DelaySeconds=600
)
```

The message becomes available after 10 minutes.

The maximum delivery delay is 15 minutes.

There are two ways to configure delivery delay:

Queue-level delay

```bash
aws sqs set-queue-attributes \
  --queue-url "$QUEUE_URL" \
  --attributes DelaySeconds=300
```

This applies a default delay to messages sent to the queue.

Message-level delay

```python
sqs.send_message(
    QueueUrl=QUEUE_URL,
    MessageBody="Process this later",
    DelaySeconds=60
)
```

This delays an individual message.

Note that per-message timers are not supported for FIFO queues. FIFO queues support queue-level delivery delay instead.

### 8.3 Understanding the difference

Consider this timeline:

### Message availability timeline

* Message sent

    10:00 AM — Producer sends a message.

* Delivery delay

    10:00–10:05 AM — Message is not yet available to consumers.

* Message available

    10:05 AM — Consumer can retrieve the message.

* Visibility timeout

    10:05–10:06 AM — Consumer has temporarily hidden the message while processing it.

* Successful deletion

    10:06 AM — Consumer deletes the message.

Retention period is the maximum lifetime of the message in the queue, not the time it spends waiting before becoming available.

### 9\. Batch message operations

SQS supports batch operations, allowing applications to perform multiple message operations through a single API request.

Batch operations are useful for improving application efficiency and reducing API request overhead.

There are three main batch operations:

| Operation          | Purpose                    |
| ------------------ | -------------------------- |
| SendMessageBatch   | Send multiple messages     |
| ReceiveMessage     | Retrieve up to 10 messages |
| DeleteMessageBatch | Delete multiple messages   |

The maximum batch size is 10 messages per request. Amazon Simple Queue Service +1

### 9.1 Sending messages in batches

Instead of sending messages individually:

```python
sqs.send_message(...)
sqs.send_message(...)
sqs.send_message(...)
```

You can use `send_message_batch()`.

Example:

```python
import json
import boto3

sqs = boto3.client("sqs", region_name="eu-west-2")

QUEUE_URL = "YOUR_QUEUE_URL"

entries = [
    {
        "Id": "order-1",
        "MessageBody": json.dumps({
            "order_id": "ORD-1001",
            "amount": 100
        })
    },
    {
        "Id": "order-2",
        "MessageBody": json.dumps({
            "order_id": "ORD-1002",
            "amount": 200
        })
    },
    {
        "Id": "order-3",
        "MessageBody": json.dumps({
            "order_id": "ORD-1003",
            "amount": 300
        })
    }
]

response = sqs.send_message_batch(
    QueueUrl=QUEUE_URL,
    Entries=entries
)

print("Successful:", response.get("Successful", []))
print("Failed:", response.get("Failed", []))
```

Notice that each batch entry has an `Id`.

This ID identifies the entry within that particular batch request. It is not the SQS message ID.

### 9.2 Receiving messages in batches

We have already seen this parameter:

```python
MaxNumberOfMessages=10
```

Example:

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)

messages = response.get("Messages", [])

print("Messages received:", len(messages))
```

SQS can return fewer messages than requested, even when more messages are available.

For example, requesting 10 messages doesn't guarantee that SQS will return exactly 10.

### 9.3 Deleting messages in batches

After processing messages successfully, you can delete them together.

```python
entries = []

for message in messages:
    entries.append({
        "Id": message["MessageId"],
        "ReceiptHandle": message["ReceiptHandle"]
    })

if entries:
    response = sqs.delete_message_batch(
        QueueUrl=QUEUE_URL,
        Entries=entries
    )

    print("Deleted:", response.get("Successful", []))
    print("Failed:", response.get("Failed", []))
```

Notice that batch deletion still requires the receipt handle for each message.

### 9.4 Partial batch failures

This is an important detail.

Batch operations do not necessarily succeed or fail as a whole.

Imagine sending 10 messages:

* 8 messages are successfully sent.

* 2 messages fail.

SQS can return both `Successful` and `Failed` collections.

Your application must inspect the results and retry only failed entries when appropriate.

The same principle applies to batch deletion.

Production consideration: Don't assume that a successful HTTP response means every message in the batch succeeded.

### 10\. Message lifecycle and processing behavior

Now let's combine everything we've learned into one complete message lifecycle.

Understanding this lifecycle is essential for designing reliable distributed applications.

### 10.1 Complete SQS message lifecycle

![AWS SQS Retention Period](https://images.openai.com/static-rsc-4/eSbxQu3xeu-PWdXa_79QJYizQUq_XWVErlfW6GE0HXkZuS0ALZP3X7vbJPZGpGyS9gQmOw7BRUicufB327tWEHTXrZUgrNXxqUe-Y30YtulHj50rVeMVVze22c4SkhMLcyH6WHj92myksVEQdZdz27TB5OLi4dIwi5Sv3eMsdktzwiembmlx-wAqhDNidYuU?purpose=fullsize)

Let's follow an order message through the system.

Step 1 — Producer creates a message

An application receives an order request and creates an event.

```json
{
  "event_type": "order.created",
  "order_id": "ORD-1001"
}
```

Step 2 — Producer sends the message

The producer calls `SendMessage`.

SQS accepts the message and returns a Message ID.

Step 3 — SQS stores the message

The message becomes part of the queue.

If a delivery delay is configured, it remains unavailable until that delay expires.

Step 4 — Consumer polls the queue

The consumer calls `ReceiveMessage`.

With long polling enabled, SQS waits for available messages for up to the configured wait time.

Step 5 — SQS returns the message

SQS returns the message body, Message ID, and ReceiptHandle.

The message becomes temporarily invisible to other consumers.

Step 6 — Consumer processes the message

The consumer performs the business operation.

For example:

* Update the order database.

* Reserve inventory.

* Generate an invoice.

* Send an email.

Step 7 — Consumer deletes the message

After successful processing, the consumer calls `DeleteMessage`.

SQS removes the message.

### 10.2 What happens if the consumer fails?

Consider this situation:

* Consumer A receives an order message.

* Consumer A begins processing.

* Consumer A crashes before deleting the message.

* The visibility timeout expires.

* The message becomes available again.

* Consumer B receives and processes it.

This is how SQS provides message recovery when consumers fail.

However, it introduces an important challenge: duplicate processing.

For example, imagine Consumer A successfully charges a customer's credit card but crashes before deleting the message.

Consumer B might receive the same message and attempt to charge the customer again.

This is why distributed consumers need idempotent processing.

We'll explore idempotency, retries, poison messages, and DLQs in Module 4.

### 10.3 Important identifiers throughout the lifecycle

| Identifier           | Generated by | Purpose                                         |
| -------------------- | ------------ | ----------------------------------------------- |
| MessageId            | SQS          | Identifies the message                          |
| ReceiptHandle        | SQS          | Identifies a specific received message instance |
| Application event ID | Producer     | Identifies the business event                   |
| MessageGroupId       | Producer     | Groups FIFO messages for ordering               |

Remember:

* Use `MessageId` to identify an SQS message.

* Use `ReceiptHandle` to delete or modify a received message.

* Use your own event ID to implement application-level deduplication and idempotency.

### 10.4 Important SQS API operations

Here is a summary of the operations covered in this module.

| API operation           | Purpose                               |
| ----------------------- | ------------------------------------- |
| CreateQueue             | Create a queue                        |
| GetQueueUrl             | Retrieve a queue URL                  |
| GetQueueAttributes      | Inspect queue configuration           |
| SetQueueAttributes      | Modify queue configuration            |
| SendMessage             | Send one message                      |
| SendMessageBatch        | Send multiple messages                |
| ReceiveMessage          | Retrieve messages                     |
| DeleteMessage           | Delete one received message           |
| DeleteMessageBatch      | Delete multiple received messages     |
| ChangeMessageVisibility | Change a message's visibility timeout |

These are the fundamental SQS operations you'll use when building producers and consumers.

### 11\. Putting everything together: A Python SQS producer and consumer

Let's connect the concepts using a small e-commerce example.

We'll build two independent application components:

* `producer.py`: Publishes order messages.

* `consumer.py`: Retrieves and processes orders.

### 11.1 Producer

```python
import json
import uuid
import boto3

sqs = boto3.client("sqs", region_name="eu-west-2")

QUEUE_URL = "YOUR_QUEUE_URL"

def publish_order(order_id: str, amount: float):
    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": "order.created",
        "order_id": order_id,
        "amount": amount
    }

    response = sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(event),
        MessageAttributes={
            "event_type": {
                "DataType": "String",
                "StringValue": "order.created"
            }
        }
    )

    return response["MessageId"]

message_id = publish_order("ORD-1001", 149.99)

print("Published:", message_id)
```

### 11.2 Consumer

```python
import json
import boto3
import time

sqs = boto3.client("sqs", region_name="eu-west-2")

QUEUE_URL = "YOUR_QUEUE_URL"

def process_order(event):
    print("Processing:", event["order_id"])

    # Business logic goes here.
    # For example, update a database.

    print("Order processed successfully")

def consume():
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
            MessageAttributeNames=["All"]
        )

        for message in response.get("Messages", []):
            try:
                event = json.loads(message["Body"])

                process_order(event)

                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"]
                )

            except Exception as error:
                print("Processing failed:", error)

        time.sleep(1)

if __name__ == "__main__":
    consume()
```

This is a basic continuously running consumer.

For a production implementation, you should add:

* Structured logging.

* Database-backed idempotency.

* Graceful shutdown.

* Controlled exception handling.

* Visibility timeout management.

* DLQ configuration.

* Retry and backoff strategies.

* Metrics and health monitoring.

Also, this simple example processes messages sequentially. A production consumer can introduce controlled concurrency, provided that visibility timeouts, FIFO ordering requirements, and downstream capacity are respected.

### 12\. Important concepts to remember

Here is a consolidated reference for the key SQS settings.

| Setting              | Default    | Allowed range     |
| -------------------- | ---------- | ----------------- |
| Visibility timeout   | 30 seconds | 0–12 hours        |
| Message retention    | 4 days     | 1 minute–14 days  |
| Delivery delay       | 0 seconds  | 0–15 minutes      |
| Long polling         | 0 seconds  | 0–20 seconds      |
| Maximum message size | 1 MiB      | 1 KiB–1 MiB       |
| Batch size           | —          | Up to 10 messages |

Amazon Simple Queue Service +3

Some important distinctions:

| Concept            | What it controls                                         |
| ------------------ | -------------------------------------------------------- |
| Visibility timeout | How long a received message stays hidden                 |
| Message retention  | How long SQS stores a message                            |
| Delivery delay     | How long before a new message becomes available          |
| Long polling       | How long SQS waits for messages during a receive request |
| Message attributes | Additional producer-defined metadata                     |
| ReceiptHandle      | The handle used to delete or modify a received message   |

### 13\. Architectural perspective: Where Module 2 fits

![The Basics of AWS SQS, CLI Operations, and Example Code for Producing and Consuming Messages | by ETL, ELT, Data and AI/ML | Medium](https://images.openai.com/static-rsc-4/aD83v1xerWiZBpL-vo8aaYFxQbXWObokTU5SlEoyHqouopqWSns72OecWEQdaWbJ4wm05wqu821FWaYtoP9V6G-vyI40Z2vRUHEJdkD44VekCH40Gyz-CTV26IPG6j2MerDwS4_WtOy-eEpz9pQOvBoimGrDSfAvSTZW_06RkYRyIzwvqWvA6XJw5k5DUe4y?purpose=fullsize)

After this module, you should understand the complete basic messaging workflow:

* Infrastructure is created using Pulumi.

* A producer publishes messages using Boto3.

* SQS stores messages.

* Consumers retrieve messages through polling.

* Visibility timeout protects messages during processing.

* Consumers delete successfully processed messages.

* Failed processing allows messages to become available again.

The next modules will build on this foundation.

### 14\. What comes next?

| Module   | Main focus                                                      |
| -------- | --------------------------------------------------------------- |
| Module 1 | Fundamentals and messaging architecture                         |
| Module 2 | Queues, messages, and message lifecycle                         |
| Module 3 | Standard queues, FIFO queues, ordering, and deduplication       |
| Module 4 | Reliability, retries, and dead-letter queues                    |
| Module 5 | Security, IAM, encryption, and networking                       |
| Module 6 | Monitoring, scaling, integrations, and production architectures |

My recommendation: Pay particular attention to the relationship between visibility timeout, receipt handles, and message deletion. These three concepts form the foundation of reliable SQS consumers. FIFO ordering and deduplication will build on them in Module 3.

### Official AWS documentation

* [Creating Standard SQS queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/creating-sqs-standard-queues.html?utm_source=chatgpt.com)

* [Creating FIFO SQS queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/creating-sqs-fifo-queues.html?utm_source=chatgpt.com)

* [SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html?utm_source=chatgpt.com)

* [SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html?utm_source=chatgpt.com)

* [Short and long polling](https://docs.aws.amazon.com/en_gb/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-short-and-long-polling.html?utm_source=chatgpt.com)
