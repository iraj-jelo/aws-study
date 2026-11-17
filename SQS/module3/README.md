Worked for 35s

### Module 3 — Standard Queues, FIFO Queues, Ordering, and Deduplication

Amazon SQS · Intermediate to Advanced

In this module, we'll explore one of the most important architectural decisions when working with Amazon SQS: choosing between Standard and FIFO queues.

Both queue types allow applications to communicate asynchronously, but they differ significantly in message ordering, delivery behavior, deduplication, throughput, and processing guarantees.

By the end of this module, you should understand how to design queue-based systems when message order matters, how to process messages concurrently, and how to prevent duplicate business operations.

### 1\. Standard Queue Architecture and Throughput

A Standard queue is the default SQS queue type. It is designed for high throughput, horizontal scalability, and distributed message processing.

Its architecture allows multiple producers and consumers to interact with the same queue independently.

![AWS SQS Overview - KodeKloud](https://images.openai.com/static-rsc-4/LKK8Gyj1OkXLowBoNvGWvI9MbvJKCd32x4-bwU-P_al9kEWakl1w-OlS8ZDEvUZQKF5aFqbzWnqrnQQcJnzBQVGr3F88Nceyr6eSVKTq_inqI-W2mJpJoq1KglbDyIx6deeMB3Ckb0ohPtxCCzg9W-zntRxDNQge6s5VbFG9X99Aj7ufwZALDGG-WS34Y5C1?purpose=fullsize)

### How Standard queues work

Consider an e-commerce application that processes customer orders.

The application has three components:

* Order API: receives customer orders.

* SQS: stores order-processing messages.

* Order workers: process orders asynchronously.

The architecture looks like this:

```text
              Order API
                  |
                  | SendMessage
                  v
          +---------------+
          |  SQS Standard |
          |     Queue     |
          +---------------+
             |    |    |
             v    v    v
           Worker Worker Worker
             1    2    3
```

Each worker independently receives messages from the queue.

For example:

```text
Producer:
  Order-101
  Order-102
  Order-103
  Order-104

Queue:
  [101] [102] [103] [104]

Consumers:
  Worker-1 -> Order-101
  Worker-2 -> Order-102
  Worker-3 -> Order-103
```

This allows multiple messages to be processed simultaneously.

### Standard queue characteristics

1\. At-least-once delivery

SQS Standard queues provide at-least-once delivery.

A message can occasionally be delivered more than once.

For example:

```text
Order-101 -> Worker-1
Order-101 -> Worker-2
```

This might happen if a message is received but its deletion is not successfully completed, or because of distributed delivery behavior.

Your application must therefore tolerate duplicate messages.

2\. Best-effort ordering

Standard queues generally preserve message order, but they do not guarantee that messages will be received in the same order they were sent.

For example:

```text
Sent:
  Message-A
  Message-B
  Message-C

Received:
  Message-B
  Message-A
  Message-C
```

This is acceptable for many workloads, such as independent image-processing jobs or background email delivery.

3\. High throughput

Standard queues support a very high number of API requests per second and automatically scale to handle large workloads.

Unlike FIFO queues, Standard queues do not impose FIFO message-group ordering constraints.

4\. Horizontal scalability

You can increase the number of consumers to process more messages concurrently.

For example:

```text
             SQS Standard
                  |
       +----------+----------+
       |          |          |
    Worker-1   Worker-2   Worker-3
       |          |          |
       v          v          v
    Process    Process    Process
```

This is particularly useful when workloads have variable processing demands.

### When to use Standard queues

Common examples include:

* Sending notification emails.

* Processing uploaded images.

* Background report generation.

* Processing independent data records.

* Distributed task processing.

* Asynchronous API workloads.

The important principle is that Standard queues prioritize scalability and throughput over strict ordering.

### 2\. FIFO Queue Architecture and Ordering Guarantees

FIFO stands for First-In, First-Out.

FIFO queues are designed for applications where message ordering and deduplication are important.

Unlike Standard queues, FIFO queues provide strict ordering within each message group.

![The Essential Guide to Amazon SQS | Baselime Blog](https://images.openai.com/static-rsc-4/wN_h_YquFuiCYehKZR7BF8DePUDHUzOlj4MTgIFSKprriAWdDCPi6TTBNGAMMcCzzRtLEGp7hWx7rZ14PFpKffaPC03UHzBoqkchlOCDpny6kzTdEdiKSGehupcNfsc3foysqyc_KGtUkwzZn_m0jTbrfMOBtPhbwVv_xFEkxb9qxVtTWSOPGZ4wlAEZOYzj?purpose=fullsize)

### How FIFO queues work

Imagine a banking application that processes account transactions.

A customer performs these operations:

* Deposit $500.

* Withdraw $100.

* Transfer $200.

These operations should be processed in the same order.

If the withdrawal is processed before the deposit, the application might produce an incorrect result.

A FIFO queue helps preserve the intended order.

```text
Producer:

Transaction-1
Transaction-2
Transaction-3
       |
       v
+------------------+
|    SQS FIFO      |
|                  |
| Transaction-1    |
| Transaction-2    |
| Transaction-3    |
+------------------+
       |
       v
    Consumer
       |
       v
 Process in order
```

### FIFO delivery characteristics

FIFO queues provide two important guarantees:

1\. Exactly-once processing within the SQS deduplication window

SQS FIFO uses deduplication to prevent duplicate messages from being introduced into the queue during the deduplication interval.

However, this does not mean your business application is guaranteed to execute an operation exactly once. We'll examine this distinction later.

2\. Strict message ordering within a message group

Messages belonging to the same message group are processed in their intended order.

For example:

```text
Message Group: Customer-100

Order-1
Order-2
Order-3
```

SQS preserves the ordering of these messages.

An important distinction: FIFO ordering is not necessarily global across all messages in a queue. It is guaranteed within each message group.

### FIFO queue naming

FIFO queues must have names ending in `.fifo`.

For example:

```text
orders.fifo
payments.fifo
transactions.fifo
```

When creating a FIFO queue, you must configure the FIFO queue attribute.

With AWS CLI:

```bash
aws sqs create-queue \
  --queue-name orders.fifo \
  --attributes FifoQueue=true
```

FIFO queues also support the `ContentBasedDeduplication` attribute, which we'll discuss shortly.

### 3\. Message Ordering and Message Groups

Message groups are one of the most important concepts in FIFO queue architecture.

They allow SQS to preserve ordering for related messages while processing unrelated messages concurrently.

### What is a MessageGroupId?

A `MessageGroupId` identifies a group of related messages.

SQS guarantees that messages within the same group are processed in order.

Consider an e-commerce application processing orders from multiple customers.

```text
Customer-A:
  Order-1
  Order-2
  Order-3

Customer-B:
  Order-4
  Order-5

Customer-C:
  Order-6
  Order-7
```

You can assign each customer a separate message group:

| Message | MessageGroupId |
| ------- | -------------- |
| Order-1 | customer-A     |
| Order-2 | customer-A     |
| Order-3 | customer-A     |
| Order-4 | customer-B     |
| Order-5 | customer-B     |
| Order-6 | customer-C     |
| Order-7 | customer-C     |

SQS preserves the order within each group.

![Solving Complex Ordering Challenges with Amazon SQS FIFO Queues | AWS Compute Blog](https://images.openai.com/static-rsc-4/lUmhhZEkI_E7ovBgzaFM6d-SJQLGyCngKlKRXiRhwGXWT6gtz_eiocqYv4ueSB5rimft_zIxkwRmZJ7nxMc9OttASK9oQaq6Ekf3IBn4_MRGz6TnsYRIGl5MDTBhsK6z57mPmJRU6j_P-EhjUonWEsVVTnIQ_2_IDPZogIWbzeWvVTg-eW9Z3DPBCEQYWR2x?purpose=fullsize)

### How parallel processing works

Suppose three consumers are polling the same FIFO queue.

```text
                 FIFO Queue
                      |
          +-----------+-----------+
          |           |           |
       Group A      Group B     Group C
          |           |           |
          v           v           v
       Worker 1    Worker 2    Worker 3
```

Each consumer can process a different message group concurrently.

However, messages belonging to the same group must maintain their ordering.

For example:

```text
Customer-A:
  Order-1 -> Order-2 -> Order-3

Customer-B:
  Order-4 -> Order-5

Customer-C:
  Order-6 -> Order-7
```

SQS can process the three groups concurrently, while preserving the order within each group.

This gives you a balance between ordering and parallelism.

### Important: Message group IDs affect scalability

Consider two different designs.

Design A: One message group

```text
MessageGroupId = "orders"

Order-1
Order-2
Order-3
Order-4
Order-5
```

All messages belong to the same group.

This limits concurrent processing because SQS must preserve the ordering of that group.

Design B: Multiple message groups

```text
MessageGroupId = "customer-A"
MessageGroupId = "customer-B"
MessageGroupId = "customer-C"
```

Now unrelated customer workloads can be processed concurrently.

This is generally a better architecture for high-throughput FIFO workloads.

The key principle:

More independent message groups can provide more opportunities for parallel processing.

However, creating many groups does not automatically guarantee a particular throughput. Consumer capacity, message availability, polling, and FIFO throughput limits also matter.

### 4\. Message Deduplication Mechanisms

Deduplication prevents the same logical message from being added to a FIFO queue multiple times within a defined time window.

This is particularly important when producers experience network failures or uncertain API responses.

### Why do we need deduplication?

Imagine your application sends an order message:

```text
Producer -> SQS: Order-1001
```

SQS successfully receives the message, but the response never reaches the producer because of a network failure.

The producer cannot determine whether SQS accepted the message.

It retries:

```text
Producer -> SQS: Order-1001
Producer -> SQS: Order-1001 (retry)
```

Without deduplication, the queue could contain two copies of the same logical operation.

FIFO queues solve this problem using message deduplication.

There are two mechanisms:

* Explicit message deduplication IDs.

* Content-based deduplication.

### 4.1 Explicit MessageDeduplicationId

When sending a message to a FIFO queue, you can provide a `MessageDeduplicationId`.

For example:

```text
Message body:
{
    "order_id": "1001",
    "customer_id": "500"
}

MessageDeduplicationId:
order-1001
```

If the producer sends another message using the same deduplication ID within the deduplication interval, SQS recognizes it as a duplicate.

```text
SendMessage:
  MessageDeduplicationId = order-1001

Retry:
  MessageDeduplicationId = order-1001

Result:
  Only one message is introduced into the queue.
```

The deduplication ID is independent of the message body. You can use the same ID even if the message bodies differ.

This is useful when you want to control what constitutes a duplicate.

For example:

```python
import boto3
import json

sqs = boto3.client("sqs", region_name="eu-west-2")

queue_url = "https://sqs.eu-west-2.amazonaws.com/123456789012/orders.fifo"

response = sqs.send_message(
    QueueUrl=queue_url,
    MessageBody=json.dumps({
        "order_id": "1001",
        "customer_id": "500",
        "amount": 250
    }),
    MessageGroupId="customer-500",
    MessageDeduplicationId="order-1001"
)

print(response["MessageId"])
```

Important parameters:

| Parameter              | Purpose                               |
| ---------------------- | ------------------------------------- |
| QueueUrl               | Identifies the FIFO queue.            |
| MessageBody            | Contains the message payload.         |
| MessageGroupId         | Identifies the ordered message group. |
| MessageDeduplicationId | Identifies duplicate submissions.     |

### 4.2 Content-Based Deduplication

Instead of generating deduplication IDs yourself, you can enable content-based deduplication on a FIFO queue.

SQS automatically generates a deduplication ID using a SHA-256 hash of the message body.

For example:

```json
{
  "order_id": "1001",
  "customer_id": "500",
  "amount": 250
}
```

SQS calculates a hash of the message body.

If another message with the same body is submitted within the deduplication interval, SQS recognizes it as a duplicate.

![Amazon SQS と処理の重複 後編 ~ FIFO キューの特徴  - builders.flash☆ - 変化を求めるデベロッパーを応援するウェブマガジン | AWS](https://images.openai.com/static-rsc-4/mtU1l1Fns-cR-pidEeWvzPwSWbjM8E7Sw0Oems8VdKmLpKW6zcsjT-WooqHsEyxOpDtqFXHXF0SYDvMXzloFu9HO1u4jhsJxAnX1TEBwXnt8NK2nyEA7-0GDug_RsinCl6mn8qCXjzT-pK98GQMgeCa4uXiXA9C4pyIXXaVl3vLo4a1l4u13olhIgGqs9qM4?purpose=fullsize)

You can enable this feature using AWS CLI:

```bash
aws sqs create-queue \
  --queue-name orders.fifo \
  --attributes '{
    "FifoQueue": "true",
    "ContentBasedDeduplication": "true"
  }'
```

With content-based deduplication enabled, you can omit `MessageDeduplicationId` when sending messages.

Important details:

* SQS hashes the message body, not message attributes.

* Identical bodies produce the same content-based deduplication ID.

* Different message bodies generally produce different IDs.

* You can still explicitly provide a deduplication ID, overriding the generated one.

For example, consider these two messages:

```json
{
  "order_id": "1001",
  "amount": 250
}
```

```json
{
  "order_id": "1001",
  "amount": 300
}
```

Their bodies differ, so their content-based deduplication IDs differ.

This means content-based deduplication is not a replacement for business-level idempotency.

### 4.3 Deduplication Interval

Amazon SQS FIFO uses a 5-minute deduplication interval.

Consider this timeline:

```text
12:00:00  Send order-1001
12:01:00  Retry order-1001
12:02:00  Retry order-1001
12:04:00  Retry order-1001
12:05:30  Send order-1001 again
```

The first four submissions fall within the initial five-minute deduplication window.

The later submission is outside that window and can be accepted as a new message.

An important detail: SQS continues tracking a deduplication ID even after the original message has been received and deleted, for the duration of the deduplication interval.

Therefore, the five-minute interval is not based on how long the message remains in the queue.

Amazon Simple Queue Service +1

### 5\. FIFO Throughput Modes and High-Throughput FIFO

FIFO queues provide ordering and deduplication, but traditionally have had lower throughput limits than Standard queues.

AWS provides High Throughput FIFO to increase throughput while maintaining FIFO ordering within message groups.

### 5.1 Normal FIFO throughput

In normal FIFO mode, the default documented throughput is:

| Operation      | Throughput          |
| -------------- | ------------------- |
| SendMessage    | 300 requests/second |
| ReceiveMessage | 300 requests/second |
| DeleteMessage  | 300 requests/second |

With batching, each API request can contain up to 10 messages.

Therefore:

300 \\times 10 = 3,000

You can process up to 3,000 messages per second per API action under these documented limits.

### 5.2 High Throughput FIFO

High Throughput FIFO allows substantially higher throughput.

It uses two important configuration settings:

| Setting             | High-throughput configuration |
| ------------------- | ----------------------------- |
| DeduplicationScope  | messageGroup                  |
| FifoThroughputLimit | perMessageGroupId             |

These settings allow deduplication and throughput management at the message-group level.

![High throughput for FIFO queues in Amazon SQS - Amazon Simple Queue Service](https://images.openai.com/static-rsc-4/_0v2pdPi4oTPeDIhCC-Jm6dV3pIJJg8ybQdC5GdoZ-jKkXcoVxv9Bit3ojHfJpsaEckYzZS6h9K4IJuY6eSmB4acXulUEcU0lJBUzFdrfeTXWbNVo6eDDdKnlDttSTkuWTc8gdwFZEDt9Z43yRBwv10udNRDVR6nPXwzHUfWHkn8n5H77D459oPTgHW2mYhW?purpose=fullsize)

For example:

```text
                  FIFO Queue
                       |
        +--------------+--------------+
        |              |              |
     Group A         Group B        Group C
        |              |              |
        v              v              v
     Worker 1       Worker 2       Worker 3
```

Messages belonging to different groups can be processed concurrently.

High-throughput mode is particularly useful when you have:

* Large numbers of independent customers.

* High-volume order processing.

* Event-processing systems.

* Multiple independent workflows.

* Large-scale transaction pipelines.

### 5.3 Regional throughput limits

High-throughput FIFO quotas vary by AWS Region.

For example, AWS currently documents the following maximum batched message throughput for selected Regions:

| Region                   | Maximum messages/second |
| ------------------------ | ----------------------- |
| US East (N. Virginia)    | 700,000                 |
| Europe (Ireland)         | 700,000                 |
| Europe (Frankfurt)       | 190,000                 |
| Europe (London)          | 45,000                  |
| Asia Pacific (Singapore) | 90,000                  |

These are regional quotas, not guaranteed application throughput. Actual throughput depends on API usage, batching, message-group distribution, and consumer capacity.

Amazon Simple Queue Service +1

### 5.4 Configuring High Throughput FIFO with Pulumi

Since we are using Pulumi Python in this course, here's how to create a high-throughput FIFO queue.

```python
import pulumi
import pulumi_aws as aws

orders_queue = aws.sqs.Queue(
    "orders-queue",
    name="orders.fifo",
    fifo_queue=True,
    content_based_deduplication=False,

    deduplication_scope="messageGroup",
    fifo_throughput_limit="perMessageGroupId",

    visibility_timeout_seconds=60,
    message_retention_seconds=345600,
)

pulumi.export("queue_url", orders_queue.url)
pulumi.export("queue_arn", orders_queue.arn)
```

The two important properties are:

```python
deduplication_scope="messageGroup"
fifo_throughput_limit="perMessageGroupId"
```

Together, these configure the required settings for High Throughput FIFO.

The example also explicitly disables content-based deduplication because we are assuming that producers will supply their own deduplication IDs.

### 6\. Exactly-Once Processing Limitations and Application-Level Idempotency

This is one of the most important concepts in the entire SQS course.

You should understand the difference between:

* Message deduplication.

* Message delivery.

* Business-operation execution.

They are not the same thing.

### 6.1 What exactly-once means in FIFO queues

AWS describes FIFO queues as supporting exactly-once processing.

However, the important guarantee is that SQS prevents duplicate messages from being introduced through repeated sends with the same deduplication ID during the five-minute deduplication interval.

It does not guarantee that your application will execute its business logic exactly once under every possible failure scenario.

Consider this example:

```text
1. Consumer receives Order-1001.

2. Consumer processes the order.

3. Database successfully stores the order.

4. Consumer crashes before deleting the SQS message.

5. Visibility timeout expires.

6. SQS makes the message available again.

7. Another consumer receives Order-1001.
```

Now the same business operation could be executed twice.

![Dissecting SQS FIFO Queues — Does Ordered and Exactly Once Messaging Really Exist? | Kevin Sookocheff](https://images.openai.com/static-rsc-4/H3QiStg1rwEHC37hrNmbkf6ORYjDqyCq610qDgVqTMZhO4PS14Icnv61PEUXwIQ84Jn-Ig2QQmMeLL0pKdkTKP1-arIQq4dI9gRpfaGudUQCNTVWZ9wQ8vBe-sTQ8rBHqVBw8_o5vTuGIFL02y_6ALG5D55n84RnVsGPqiv9u-fsnm3ONGy0GPL4_lEkN_mG?purpose=fullsize)

This is why application-level idempotency is necessary.

### 6.2 What is idempotency?

An operation is idempotent when executing it multiple times produces the same final result as executing it once.

For example:

Non-idempotent operation:

```python
account.balance += 100
```

If executed twice, the account receives $200 instead of $100.

Idempotent approach:

Use a unique transaction ID to ensure that the same transaction is not applied twice.

```text
Transaction ID: TX-1001

First execution:
  Transaction does not exist.
  Apply transaction.
  Record TX-1001.

Second execution:
  TX-1001 already exists.
  Skip transaction.
```

### 6.3 Implementing idempotency with PostgreSQL

Suppose we have a FastAPI application consuming SQS messages.

We can maintain a table of processed transactions.

```sql
CREATE TABLE processed_messages (
    message_id VARCHAR(100) PRIMARY KEY,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

When a consumer receives a message:

* Begin a database transaction.

* Attempt to insert the message ID.

* If the ID already exists, skip the business operation.

* Otherwise, execute the business operation.

* Commit the database transaction.

* Delete the message from SQS.

Python example:

```python
def process_message(conn, message):
    message_id = message["MessageId"]

    with conn.transaction():
        result = conn.execute(
            """
            INSERT INTO processed_messages (message_id)
            VALUES (%s)
            ON CONFLICT DO NOTHING
            RETURNING message_id
            """,
            (message_id,)
        )

        if result.fetchone() is None:
            print("Message already processed")
            return

        # Execute business operation here.
        print("Processing message...")
```

This example illustrates the pattern, but there is an important improvement: use a stable business event ID in the message body as the idempotency key rather than relying exclusively on the SQS `MessageId`.

Why?

Because a producer can send the same logical business event twice and receive two different SQS message IDs.

For example:

```json
{
  "event_id": "order-payment-1001",
  "order_id": "1001",
  "event_type": "payment_completed",
  "amount": 250
}
```

Your database can use `event_id` as the unique key.

### 6.4 The importance of atomicity

The database transaction is essential.

You should not:

* Record the message as processed.

* Commit.

* Execute the business operation separately.

If the application crashes between steps 2 and 3, the message could be permanently skipped.

Instead, the idempotency record and business operation should be committed atomically within the same database transaction whenever possible.

If your business operation involves an external system, such as a payment gateway, you may also need that system's idempotency mechanism or an outbox/inbox architecture.

Key takeaway: FIFO deduplication protects the queue from duplicate submissions within its deduplication window. Application-level idempotency protects your business operations from duplicate execution.

Amazon Simple Queue Service +1

### 7\. Choosing Between Standard and FIFO Queues

Now let's put everything together and understand when to choose each queue type.

The decision should be based on your application's requirements rather than simply choosing the more advanced queue.

### 7.1 Side-by-side comparison

| Feature              | Standard              | FIFO                                             |
| -------------------- | --------------------- | ------------------------------------------------ |
| Message ordering     | Best effort           | Strict within group                              |
| Delivery guarantee   | At least once         | Exactly-once send deduplication within 5 minutes |
| Duplicate messages   | Possible              | Duplicate sends suppressed within window         |
| Throughput           | Nearly unlimited      | Limited by FIFO quotas                           |
| Message groups       | Fair queues supported | Ordering and concurrency                         |
| Parallel processing  | High                  | Across message groups                            |
| Deduplication        | Application-level     | Built-in + application-level                     |
| Queue naming         | Any valid name        | Must end in .fifo                                |
| Per-message delay    | Supported             | Not supported                                    |
| High-throughput mode | Not needed            | Supported                                        |

One interesting detail: Standard queues also support `MessageGroupId` for fair queues. This is different from FIFO message groups. In Standard queues, messages from the same group can still be processed concurrently; the feature helps maintain fair message dwell times across tenants. Amazon Simple Queue Service +1

### 7.2 When should you use Standard queues?

Choose Standard queues when:

* Message ordering is not important.

* You need very high throughput.

* Messages represent independent tasks.

* Your application already supports idempotent processing.

* You want maximum flexibility for distributed consumers.

Example: Image processing.

```text
User uploads 1,000 images
          |
          v
     SQS Standard
          |
    +-----+-----+
    |     |     |
    v     v     v
 Worker Worker Worker
    1     2     3
```

Each image can be processed independently.

There is no reason to wait for image 1 to finish before processing image 2.

### 7.3 When should you use FIFO queues?

Choose FIFO queues when:

* Message order is important.

* Events represent sequential business operations.

* You need built-in producer-side deduplication.

* Multiple events belong to the same logical entity.

* You need controlled parallelism through message groups.

Example: Banking transactions.

```text
Customer-100
     |
     v
  FIFO Queue
     |
     +-- Deposit $500
     |
     +-- Withdraw $100
     |
     +-- Transfer $200
     |
     v
 Process in order
```

The account operations must respect their intended sequence.

### 7.4 Real-world architectural examples

| Application                  | Recommended queue | Reason                                           |
| ---------------------------- | ----------------- | ------------------------------------------------ |
| Image processing             | Standard          | Independent tasks                                |
| Email notifications          | Standard          | Ordering usually unnecessary                     |
| Video transcoding            | Standard          | High parallelism                                 |
| Banking transactions         | FIFO              | Ordered operations                               |
| Inventory updates            | FIFO              | Prevent conflicting updates                      |
| Customer order events        | FIFO              | Preserve per-customer order                      |
| Background report generation | Standard          | Independent workloads                            |
| Payment processing           | FIFO or Standard  | Depends on ordering and idempotency requirements |

A payment system does not automatically require FIFO. If payment events are independent, Standard may be sufficient with strong idempotency. If operations for the same account must be sequential, FIFO with appropriate message groups is a better fit.

### 7.5 Can you convert a Standard queue into a FIFO queue?

No. You cannot change an existing Standard queue into a FIFO queue simply by changing an attribute.

You must create a new FIFO queue and migrate your application and message-processing workflow.

There are also configuration differences to consider:

* FIFO queues require `MessageGroupId`.

* FIFO queues use deduplication IDs or content-based deduplication.

* FIFO queues support queue-level delay, not per-message delay.

* Consumer processing must respect message-group ordering.

Amazon Simple Queue Service +1

### 8\. Practical Architecture: E-Commerce Order Processing

Let's finish by combining the concepts into a realistic architecture.

Imagine you're developing an e-commerce platform with FastAPI, PostgreSQL, and background workers.

The application needs to process customer orders.

Requirements:

* Orders from the same customer must be processed in order.

* Different customers should be processed concurrently.

* Duplicate order submissions must not create duplicate business operations.

* Multiple workers should be able to process messages.

* Failed messages should not block the entire system indefinitely.

### Architecture

![Using Amazon SQS in a Multi-Tenant SaaS Solution | AWS Partner Network (APN) Blog](https://images.openai.com/static-rsc-4/rsu2zj2ohHoxkwANB7YYcvIqPAJZRPuLtvBRl-0YpGovSf-0wLnuj1UFTpmVWoVxb8k4c4nxb2ogxf4GNzGVKu62IMConlwcmNIUGCSoJ42UeVFb7OUgG_ZTIdXx5_0De8iLnIvh3YiC62SY3jQAlDpPbxPQYKFnoH26l4j3lCSTvgYQULICHgcPdBHQS7YT?purpose=fullsize)

```text
                 FastAPI
                    |
                    | SendMessage
                    v
             SQS FIFO Queue
                    |
        +-----------+-----------+
        |           |           |
     Group A     Group B     Group C
        |           |           |
        v           v           v
     Worker 1    Worker 2    Worker 3
        |           |           |
        +-----------+-----------+
                    |
                    v
               PostgreSQL
                    |
                    v
             Order Processing
```

### Producer implementation

```python
import boto3
import json

sqs = boto3.client("sqs", region_name="eu-west-2")

QUEUE_URL = "YOUR_FIFO_QUEUE_URL"

def publish_order(order):
    return sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(order),
        MessageGroupId=f"customer-{order['customer_id']}",
        MessageDeduplicationId=f"order-{order['order_id']}"
    )

publish_order({
    "order_id": "1001",
    "customer_id": "500",
    "amount": 250
})
```

Here:

* `MessageGroupId` preserves the order of messages for a customer.

* `MessageDeduplicationId` prevents duplicate submissions within the deduplication window.

* Different customers can be processed concurrently.

### Consumer architecture

Multiple workers poll the same queue.

Each worker:

* Receives available messages.

* Processes messages in the correct group order.

* Uses PostgreSQL to enforce business-level idempotency.

* Deletes successfully processed messages using their receipt handles.

* Leaves failed messages undeleted so they can be retried.

Remember that FIFO queues can return multiple messages from the same group in a single receive batch. Your consumer must process those messages sequentially, not concurrently. Messages from different groups can be processed in parallel.

This architecture combines:

* FIFO ordering.

* Message groups.

* Producer-side deduplication.

* Application-level idempotency.

* Horizontal consumer scaling.

It is a good foundation for production event-driven applications.

### 9\. Important Concepts to Remember

Here is a condensed reference of the most important concepts from this module.

| Concept                     | What you should remember                                               |
| --------------------------- | ---------------------------------------------------------------------- |
| Standard queue              | High throughput, best-effort ordering                                  |
| FIFO queue                  | Strict ordering within message groups                                  |
| MessageGroupId              | Defines an ordered processing group                                    |
| MessageDeduplicationId      | Identifies duplicate message submissions                               |
| Content-based deduplication | Generates an ID using SHA-256 of the message body                      |
| Deduplication interval      | 5 minutes                                                              |
| High Throughput FIFO        | Higher throughput using message-group-level settings                   |
| Idempotency                 | Prevents duplicate business effects                                    |
| Parallel processing         | FIFO supports concurrency across independent groups                    |
| Exactly-once limitation     | Queue deduplication does not guarantee exactly-once business execution |

### The three most important distinctions

1\. Ordering

Standard: Best effort.

FIFO: Strict ordering within each message group.

2\. Deduplication

Standard: Your application must handle duplicates.

FIFO: SQS suppresses duplicate sends within the five-minute deduplication interval.

3\. Processing guarantees

Standard: At-least-once delivery.

FIFO: Exactly-once send deduplication, but application-level idempotency is still necessary.

### Official AWS documentation

These are useful references for deeper technical details:

* [Amazon SQS queue types](https://docs.aws.amazon.com/en_gb/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-queue-types.html?utm_source=chatgpt.com)

* [Amazon SQS FIFO queues](https://docs.aws.amazon.com/en_en/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fifo-queues.html?utm_source=chatgpt.com)

* [FIFO queue delivery logic](https://docs.aws.amazon.com/en_en/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-understanding-logic.html?utm_source=chatgpt.com)

* [Exactly-once processing](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/FIFO-queues-exactly-once-processing.html?utm_source=chatgpt.com)

* [Enabling high throughput for FIFO queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/enable-high-throughput-fifo.html?utm_source=chatgpt.com)

* [Message deduplication and grouping best practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/best-practices-message-deduplication.html?utm_source=chatgpt.com)

Module 3 complete.

The central idea of this module is that Standard queues optimize for throughput, while FIFO queues provide ordered processing and producer-side deduplication. Understanding message groups and application-level idempotency is essential for designing reliable distributed systems.

Next, we'll move to Module 4 — Reliability, Retries, and Dead-Letter Queues, where we'll explore how SQS handles failed messages, repeated delivery, poison-pill messages, and resilient consumer architectures.
