### Module 1 — SQS Fundamentals and Messaging Architecture

AWS Messaging · Amazon Simple Queue Service · Beginner to Advanced

![Amazon Simple Queue Service (SQS): A Comprehensive Tutorial | DataCamp](https://images.openai.com/static-rsc-4/aU4msFlKOtaH1INcFC51GU3V7_Opq8LrudWfwYa9C0yX36tunP6StNhHcDDaXATmj4zKaFHQcwkSmJBVRYka22lwGABcGDnx8IdJDaWNpbt5NfmxKcyQpamQGdqVA5jFwSuAzDQ_k93fCzfn0av3VcUzjh2DDBjPosbHjiStjkZMwtPI_rxfl4OL_UaGizWM?purpose=fullsize)

### 1\. Introduction to messaging systems

Before understanding Amazon SQS, we need to understand why messaging systems exist and what problems they solve in distributed applications.

Modern applications rarely consist of a single program. They typically contain multiple services responsible for different tasks.

For example, consider an e-commerce application:

* An API receives customer orders.

* An order service validates and stores orders.

* A payment service processes payments.

* An inventory service updates stock.

* An email service sends order confirmations.

* A shipping service arranges delivery.

These services need to communicate with each other.

There are two major approaches to communication:

### 1.1 Synchronous communication

In synchronous communication, one service sends a request to another service and waits for a response.

For example:

```text
Customer
   |
   v
Order API
   |
   | HTTP Request
   v
Payment Service
   |
   | HTTP Response
   v
Order API
   |
   v
Customer
```

Suppose a customer places an order.

The Order API calls the Payment Service and waits until payment processing finishes.

The main characteristics are:

* The caller waits for the response.

* Both services need to be available at the same time.

* Network failures can affect the entire request.

* Slow downstream services increase response latency.

* Services become more tightly coupled.

Synchronous communication is useful when an immediate response is necessary, such as checking account information or validating a payment.

However, it becomes problematic when applications have many independent services.

### 1.2 Asynchronous communication

In asynchronous communication, the sender does not need to wait for the receiver to finish processing a task.

Instead, the sender publishes a message to a messaging system. Another service retrieves and processes that message later.

```text
Customer
   |
   v
Order API
   |
   | Send Message
   v
+------------------+
|    Amazon SQS    |
|                  |
|  Order Message   |
+------------------+
   |
   | Consumer retrieves message
   v
Order Processing Service
   |
   v
Payment / Inventory / Email
```

The Order API can acknowledge the customer's request after successfully submitting the message to the queue.

The processing service can work independently.

Advantages include:

* Reduced coupling between services.

* Better resilience when consumers are temporarily unavailable.

* Ability to absorb traffic spikes.

* Independent scaling of producers and consumers.

* Improved workload distribution.

* Support for background processing.

Important: Asynchronous communication does not mean that messages are processed immediately. It means that sending and processing are independent operations.

### 1.3 Why asynchronous architecture matters

Imagine your e-commerce application normally receives 100 orders per minute.

During a promotional campaign, it receives 10,000 orders per minute.

If every request synchronously invokes payment, inventory, and email services, those services may become overloaded.

With SQS, the application can temporarily store incoming work in a queue.

Consumers process the messages at a rate they can handle.

![REL04-BP02 Menerapkan dependensi yang digabungkan secara longgar - Kerangka Kerja AWS Well-Architected](https://images.openai.com/static-rsc-4/Q0C-SwcMGyX4Ih5YKBavf9t957IvQlkSkXIAA2zZQHg82N9A8j_uzCuhOOAzAUDH-oZOD6QkGvzcMYcFcBQwon3bJ-PNaxMH_CF5Kqf_-z-UAKmKPMIMSqFn1CzPeZgCBp7XZuUK8xn7ShVyOX3xPGUmltF_wYh7HfQlO_nmVJibaP7VXSt9Y52_QyIpLeSq?purpose=fullsize)

This is called buffering.

The queue acts as a buffer between incoming traffic and downstream processing capacity.

For example:

* Producers submit 10,000 messages.

* Consumers process 1,000 messages per minute.

* The queue temporarily stores the remaining messages.

* Consumers continue processing until the backlog decreases.

The queue does not automatically increase consumer capacity. It provides a buffer that allows you to scale consumers independently.

### 2\. Message queues and producer-consumer architecture

A message queue is a communication mechanism that temporarily stores messages until they are retrieved and processed by consumers.

There are three fundamental components.

![A Guide to Async Patterns in API Design](https://images.openai.com/static-rsc-4/au1eAD2iwiUtDaiGlr7_YXCztFjNUFtV_K-Dgo0rQzUov5ZMkxuCoJLIHaaQjpLvd8Xzp1W_9xyhlhFbR6ttJrBgo9uc8WueVxw3qAKX_fhDN0bbRYOMaZ5ISfUeVc3MC6PnQpA0r8L7mbcLCZpyS-CBKJqtIhCQ7bnclRdlp5sWqwpLdP71Mf0tHVeTHIGA?purpose=fullsize)

### 2.1 Producer

A producer is an application or service that creates and sends messages to a queue.

For example:

* An order API sends order information.

* A file-upload service sends file-processing tasks.

* A monitoring service sends notification tasks.

* A payment service sends transaction events.

A producer does not need to know which consumer will process the message.

Its responsibility is to submit the message to the queue.

### 2.2 Queue

The queue stores messages until consumers retrieve them.

It provides an intermediary between producers and consumers.

The queue handles important responsibilities such as:

* Message storage.

* Message availability.

* Message retention.

* Delivery behavior.

* Visibility timeout.

* Message deletion after successful processing.

Amazon SQS manages the underlying queue infrastructure.

You do not need to provision or maintain queue servers.

### 2.3 Consumer

A consumer is an application or service that retrieves messages from a queue and processes them.

Examples include:

* Python workers.

* AWS Lambda functions.

* ECS containers.

* EC2 applications.

* Kubernetes workloads running outside or inside AWS.

A consumer typically performs these operations:

* Retrieves a message.

* Processes the message.

* Confirms successful processing by deleting the message.

The deletion step is particularly important because receiving a message does not automatically remove it from the queue.

We will examine this behavior in Module 2.

### 2.4 Multiple producers and consumers

One of the most useful features of message queues is that multiple producers and consumers can work with the same queue.

![The Basics of AWS SQS, CLI Operations, and Example Code for Producing and Consuming Messages | by ETL, ELT, Data and AI/ML | Medium](https://images.openai.com/static-rsc-4/aD83v1xerWiZBpL-vo8aaYFxQbXWObokTU5SlEoyHqouopqWSns72OecWEQdaWbJ4wm05wqu821FWaYtoP9V6G-vyI40Z2vRUHEJdkD44VekCH40Gyz-CTV26IPG6j2MerDwS4_WtOy-eEpz9pQOvBoimGrDSfAvSTZW_06RkYRyIzwvqWvA6XJw5k5DUe4y?purpose=fullsize)

For example:

* Multiple API instances submit orders.

* Multiple worker instances process orders.

* The queue distributes available messages among consumers.

This architecture supports horizontal scaling.

Instead of making one worker process everything, you can run multiple workers concurrently.

An important distinction: with a shared SQS queue, messages are generally distributed among competing consumers. Each message is intended to be processed by one consumer successfully, although duplicate delivery is possible.

This differs from publish/subscribe messaging, where multiple subscribers can independently receive copies of the same published event. We will explore that distinction when studying SNS.

### 3\. Amazon SQS architecture and core components

![AWS SQS (Simple Queue Service) Logo PNG Vector (SVG) Free Download](https://images.openai.com/static-rsc-4/cy5CkrfhzKr1vydS3bCQVZYjHfpgMNGXHHtLBdPFbb36klAY_ATLROJwulsHnbRG2miqmevvQkpe6MFyVboet-9iAZhxBBGd69sO-fa2v6JE9b85LuuEFeTDbGsI41BLJCGkGvGeRlTpl3sUaWzFlZo9s9eK3lkzb2yFAJQmJn7kwB3N94PEsO_qxDuNuq1k?purpose=fullsize)

Amazon Simple Queue Service (SQS)

Fully managed message queuing service

Amazon SQS is a fully managed AWS service that allows distributed applications and microservices to exchange messages through queues.

AWS manages the underlying infrastructure, including queue availability, storage infrastructure, and service operations.

You interact with SQS through:

* AWS Management Console.

* AWS CLI.

* AWS SDKs, such as Python Boto3.

* AWS APIs.

* Infrastructure as Code tools such as Pulumi.

### 3.1 Basic SQS architecture

![SQS - KodeKloud](https://images.openai.com/static-rsc-4/nQ9JtFs0BbMmRgx4ps8rw92QZvfmhIpg9yoa4KE72CXVHbaGDfl9vbCcKwhOB_xt9OQQ1EhFFOhIhdixuJWSFoqXQS7nsIxuT8pqy0pqUERr7EUzz9Z20l3nDTz_znS42lJIMIt4bCSYGx5g1oEcMFZcvTO10C52_TWwWOmZi1fT-Ehnf3KnTJQFBrD5PoR3?purpose=fullsize)

A typical SQS workflow looks like this:

Step 1 — Create a queue

An application creates an SQS queue.

For example:

`orders-queue`

Step 2 — Send a message

The producer sends a message using the SQS `SendMessage` API operation.

Step 3 — Store the message

SQS stores the message until a consumer retrieves it or the message expires.

Step 4 — Receive the message

The consumer calls `ReceiveMessage` to retrieve available messages.

Step 5 — Process the message

The consumer performs the required business operation.

Step 6 — Delete the message

After successful processing, the consumer calls `DeleteMessage`.

This tells SQS that the message has been successfully handled.

### 3.2 Important SQS components

| Component          | Purpose                                           |
| ------------------ | ------------------------------------------------- |
| Queue              | Stores messages                                   |
| Message            | Contains application data                         |
| Producer           | Sends messages                                    |
| Consumer           | Receives and processes messages                   |
| Queue URL          | Identifies a queue for API operations             |
| Queue ARN          | Globally identifies a queue within AWS            |
| Receipt handle     | Identifies a particular received message delivery |
| Visibility timeout | Temporarily hides a received message              |
| Dead-letter queue  | Stores messages that repeatedly fail processing   |

We will study most of these components in detail in later modules.

### 3.3 SQS is a managed service

With a traditional message broker, you might need to:

* Provision servers.

* Install broker software.

* Configure storage.

* Manage availability.

* Monitor infrastructure.

* Upgrade broker versions.

* Configure replication and failover.

With SQS, AWS manages the underlying infrastructure.

You primarily configure the queues and integrate your applications.

This makes SQS particularly useful for cloud-native applications and distributed systems.

### 4\. Standard queues and FIFO queues

Amazon SQS provides two primary queue types:

* Standard queues.

* FIFO (First-In-First-Out) queues.

Choosing the correct queue type is an important architectural decision because the two types have different ordering, delivery, and throughput characteristics.

### 4.1 Standard queues

High throughput

Standard queues are designed for applications that need high scalability and throughput.

Their main characteristics are:

* Very high, nearly unlimited API throughput.

* At-least-once message delivery.

* Best-effort message ordering.

* Messages can occasionally be delivered more than once.

* Messages can occasionally arrive out of order.

Consider an image-processing application.

Users upload images, and the application sends processing tasks to SQS.

```text
Image Upload API
       |
       v
  SQS Standard Queue
       |
       +----------+
       |          |
       v          v
   Worker 1    Worker 2
       |          |
       v          v
   Image A     Image B
```

It doesn't matter whether Image A or Image B finishes first.

It also doesn't matter if a processing task occasionally gets delivered more than once, provided the application handles duplicate processing safely.

This makes Standard queues appropriate for:

* Background jobs.

* Image and video processing.

* Email processing.

* Log processing.

* High-volume task distribution.

* Independent microservice workloads.

### 4.2 FIFO queues

Strict ordering

FIFO stands for First-In-First-Out.

FIFO queues are designed for applications where message ordering is important.

Their main characteristics are:

* Strict message ordering within each message group.

* Message deduplication support.

* Controlled processing of messages within each group.

* Configurable throughput modes.

Consider an account transaction system.

A customer performs three operations:

* Deposit $100.

* Withdraw $50.

* Deposit $200.

The operations must be processed in the correct order.

![Understanding Message Queues - ByteByteGo Newsletter](https://images.openai.com/static-rsc-4/Y-d8vfJ0IMG1AZ1EVMGbXpV_hXSxZDx5-2EVbiBuvSe17BVtlUpOz7ROREgQcvFA14MGgbkiXjNsvrg4vwVG2MrHKbsM_OFt6IYjIl8SfUtczaArzQEKp4lpUv4QR1MpfEsh3mkIKc67-7NGrYkXAbMWDIGyNiQNWxfhZyLylilSkGfGgiMXNs4NBjKuE-ae?purpose=fullsize)

If the withdrawal is processed before the first deposit, the application might produce an incorrect result.

FIFO queues help preserve the intended sequence.

### 4.3 Message groups in FIFO queues

FIFO queues support message groups.

A message group represents an ordered sequence of related messages.

For example:

```text
FIFO Queue
    |
    +-- Customer A
    |      |
    |      +-- Order 1
    |      +-- Order 2
    |      +-- Order 3
    |
    +-- Customer B
    |      |
    |      +-- Order 1
    |      +-- Order 2
    |
    +-- Customer C
           |
           +-- Order 1
           +-- Order 2
```

SQS preserves ordering within each group.

However, different groups can be processed concurrently.

This is particularly useful when building applications that need both ordering and parallel processing.

For example:

* All transactions belonging to one bank account must be ordered.

* Transactions belonging to different bank accounts can be processed independently.

### 4.4 Standard vs FIFO comparison

| Feature            | Standard                              | FIFO                        |
| ------------------ | ------------------------------------- | --------------------------- |
| Ordering           | Best effort                           | Strict within message group |
| Delivery           | At least once                         | FIFO deduplication support  |
| Duplicate handling | Application must handle duplicates    | Deduplication support       |
| Throughput         | Very high                             | Configurable throughput     |
| Message groups     | Fair Queue functionality is supported | Core feature                |
| Best for           | Independent tasks                     | Ordered operations          |

One important clarification: FIFO's exactly-once processing capability relates to SQS message deduplication and queue behavior. It does not guarantee that an external business operation, such as charging a credit card, executes exactly once. Consumers still need application-level idempotency.

AWS documentation: [SQS queue types](https://docs.aws.amazon.com/en_en/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-queue-types.html?utm_source=chatgpt.com) and [FIFO queues](https://docs.aws.amazon.com/en_en/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fifo-queues.html?utm_source=chatgpt.com).

### 5\. Queue URLs, ARNs, and regional architecture

When working with AWS services, you frequently encounter identifiers such as ARNs, URLs, and resource names.

SQS uses both queue URLs and queue ARNs.

Understanding their differences is important when working with AWS CLI, Boto3, IAM policies, and Pulumi.

### 5.1 Queue URL

Every SQS queue has a queue URL.

A queue URL is used by applications and AWS APIs to interact with the queue.

Example:

```text
https://sqs.eu-west-2.amazonaws.com/123456789012/orders-queue
```

This URL contains:

| Component    | Meaning              |
| ------------ | -------------------- |
| https://sqs  | SQS service endpoint |
| eu-west-2    | AWS Region           |
| 123456789012 | AWS account ID       |
| orders-queue | Queue name           |

The URL is commonly used with operations such as:

* SendMessage

* ReceiveMessage

* DeleteMessage

* GetQueueAttributes

* SetQueueAttributes

For example, using AWS CLI:

```bash
aws sqs send-message \
  --queue-url https://sqs.eu-west-2.amazonaws.com/123456789012/orders-queue \
  --message-body '{"order_id": 1001}'
```

### 5.2 Queue ARN

An ARN (Amazon Resource Name) is a standardized identifier for AWS resources.

Example:

```text
arn:aws:sqs:eu-west-2:123456789012:orders-queue
```

Its structure is:

```text
arn:partition:service:region:account-id:resource
```

For SQS:

| Component    | Meaning        |
| ------------ | -------------- |
| arn          | ARN identifier |
| aws          | AWS partition  |
| sqs          | AWS service    |
| eu-west-2    | Region         |
| 123456789012 | Account ID     |
| orders-queue | Queue name     |

ARNs are commonly used in:

* IAM policies.

* Queue resource policies.

* Cross-account permissions.

* AWS resource references.

* CloudFormation and Pulumi dependencies.

For example, an IAM policy might allow a Lambda execution role to consume messages from a specific queue:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:eu-west-2:123456789012:orders-queue"
    }
  ]
}
```

### 5.3 Queue URL vs ARN

| Queue URL                              | Queue ARN                         |
| -------------------------------------- | --------------------------------- |
| Used for queue API operations          | Used for resource identification  |
| Includes an HTTPS endpoint             | Uses ARN format                   |
| Used by SendMessage and ReceiveMessage | Used in IAM and resource policies |
| Identifies the queue endpoint          | Identifies the AWS resource       |

Remember:

Queue URL = interacting with the queue.

Queue ARN = identifying and authorizing access to the queue.

### 5.4 SQS regional architecture

SQS is a regional AWS service.

When you create a queue, you create it in a specific AWS Region.

For example:

```text
AWS Account
    |
    +---------------------------+
    |                           |
    v                           v
Europe (London)             US East (N. Virginia)
eu-west-2                   us-east-1
    |                           |
    v                           v
orders-queue                orders-queue
```

These are two independent queues.

They do not automatically synchronize messages.

If your application needs to process messages across multiple Regions, you must design an explicit cross-region architecture.

This might involve:

* A producer sending messages to queues in multiple Regions.

* A forwarding application.

* A custom replication mechanism.

* Regional event-driven architectures.

SQS also supports redundant infrastructure across Availability Zones within its Region, helping protect messages against individual infrastructure or Availability Zone failures.

Important distinction: Regional redundancy is not the same as cross-region replication.

### 6\. Push-based vs pull-based messaging

Another important concept in messaging architecture is how consumers receive messages.

There are two common approaches:

* Push-based delivery.

* Pull-based delivery.

### 6.1 Push-based messaging

In push-based messaging, the messaging system actively sends messages to a destination when events occur.

For example, SNS can publish notifications to supported subscribers.

```text
Producer
   |
   v
SNS Topic
   |
   | Push notification
   v
Subscriber
```

The subscriber does not necessarily need to continuously request messages.

This model is useful for notification and event distribution.

### 6.2 Pull-based messaging

SQS primarily follows a pull-based model.

The consumer requests messages from the queue.

```text
Producer
   |
   v
SQS Queue
   |
   ^
   | ReceiveMessage request
   |
Consumer
```

The consumer decides when to retrieve messages.

For example, a Python worker can continuously poll an SQS queue.

```python
import boto3

sqs = boto3.client("sqs", region_name="eu-west-2")

queue_url = "YOUR_QUEUE_URL"

response = sqs.receive_message(
    QueueUrl=queue_url,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)

for message in response.get("Messages", []):
    print(message["Body"])
```

Here:

* `ReceiveMessage` requests messages.

* `MaxNumberOfMessages` controls the maximum number returned in one request.

* `WaitTimeSeconds=20` enables long polling.

### 6.3 Short polling vs long polling

SQS supports two polling approaches.

Short polling

The consumer requests messages and SQS responds without waiting for messages to become available.

This can result in empty responses.

Long polling

The consumer requests messages and SQS waits for messages to become available, up to the configured waiting time.

Long polling can reduce unnecessary API requests and empty responses.

The maximum long-polling wait time is 20 seconds.

![AWS Application Integration Services | AWS Cheat Sheet](https://images.openai.com/static-rsc-4/QzsDo7XNd3uFmAibe8J4s-VHoSl8zRh74mRX_xczsbm09jiNh9eWdcWBVe-JoK1B_r8_usQMAbY2eWOysJTMHc58ExUj0twaElG-es7Q-pPlbu-yOCuc-111JKMXfm0KXSj67N05HboqvBH3YzYdIz7SI29jO1YGdF5V7SrXKj6kR3hgxP2Emk7t4eHUPMp8?purpose=fullsize)

### 6.4 What about Lambda and SQS?

An interesting detail is that Lambda integrates with SQS using an event source mapping.

You configure Lambda to consume messages from an SQS queue.

AWS Lambda polls the queue on your behalf and invokes your function with batches of messages.

```text
Producer
   |
   v
SQS Queue
   |
   v
Lambda Event Source Mapping
   |
   v
Lambda Function
   |
   v
Business Logic
```

Although Lambda is automatically triggered from the application's perspective, the underlying SQS integration still uses polling.

This is an important distinction when comparing SQS and SNS.

### 7\. SQS delivery guarantees and at-least-once delivery

One of the most important concepts in distributed messaging is message delivery guarantees.

When a producer sends a message, what happens if the consumer fails?

Can the message be lost?

Can the message be delivered twice?

Can messages arrive in a different order?

SQS has different delivery characteristics depending on the queue type.

### 7.1 At-least-once delivery

Standard queues provide at-least-once delivery.

This means that SQS is designed to deliver a message one or more times.

A message should not be assumed to arrive exactly once.

Consider this scenario:

```text
Producer
   |
   v
SQS Queue
   |
   v
Consumer
   |
   v
Process Message
   |
   X
Consumer crashes before deleting message
```

The consumer successfully processes the message but crashes before sending the deletion request.

SQS does not know that the business operation completed successfully.

After the visibility timeout expires, the message becomes available again.

Another consumer may receive and process it.

The same business operation could therefore happen twice.

### 7.2 Why duplicate messages happen

Possible causes include:

* Consumer crashes.

* Network interruption.

* Message deletion fails.

* Processing takes longer than the visibility timeout.

* Distributed infrastructure temporarily delivers duplicate copies.

This is why consumers should be designed to handle duplicate messages safely.

### 7.3 Idempotency

Idempotency means that performing the same operation multiple times produces the same final result as performing it once.

For example, consider an order-processing system.

An order has an identifier:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "CUS-2001",
  "amount": 150
}
```

Before processing the order, the consumer checks whether it has already been processed.

Conceptually:

```python
def process_order(order):
    order_id = order["order_id"]

    if order_already_processed(order_id):
        return

    charge_customer(order)
    mark_order_as_processed(order_id)
```

This example illustrates the concept, but the check and business operation must be implemented atomically or with an appropriate idempotency mechanism to avoid race conditions.

Common techniques include:

* Database uniqueness constraints.

* Idempotency keys.

* Transactional writes.

* Conditional updates.

* Deduplication records.

For financial transactions, idempotency is particularly important.

### 7.4 At-least-once vs at-most-once vs exactly-once

| Delivery model | Meaning                                                            |
| -------------- | ------------------------------------------------------------------ |
| At-most-once   | A message is delivered zero or one time; loss is possible          |
| At-least-once  | A message is delivered one or more times; duplicates are possible  |
| Exactly-once   | Processing occurs exactly once under the defined system guarantees |

A crucial architectural lesson:

Exactly-once business processing is difficult in distributed systems.

Even if a messaging service provides deduplication, your application must still account for failures between message delivery and business-operation completion.

AWS reference: [Standard queue delivery guarantees](https://docs.aws.amazon.com/en_gb/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html?utm_source=chatgpt.com) and [SQS visibility timeout](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-visibility-timeout.html?utm_source=chatgpt.com).

### 8\. SQS use cases and architectural patterns

Now let's look at why developers use SQS in real-world applications.

### 8.1 Background job processing

One of the most common SQS use cases is moving expensive operations out of the main application request.

Imagine a FastAPI application that allows users to upload documents.

Without SQS:

```text
User
 |
 v
FastAPI
 |
 +--> Upload document
 |
 +--> Extract text
 |
 +--> Generate thumbnail
 |
 +--> Analyze document
 |
 +--> Store results
 |
 v
Return response
```

The user must wait for all operations to finish.

With SQS:

![Designing a Reliable File Processing Pipeline on AWS for Real-World Applications | by Maryammairaj | SUDO Consultants | Mar, 2026 | Medium](https://images.openai.com/static-rsc-4/XaLyLIJBBeNgTe7DByNcuTCTS4lQ6smCkHbf2YQfFv_a0HmBoiHh6ZH42T2V3ElGvPhz3BTNgP3PI9p0AZvVj3s8BH0dge6YrTnwniRrQshXrOyeWFxwIn4aAST9HtirOuAG37zQBDI6btBIuJPx5o1KIuJaO-ayaPkKOb6yF8IlyVLxTd182O7iAA01RRO9?purpose=fullsize)

```text
User
 |
 v
FastAPI
 |
 +--> Store document in S3
 |
 +--> Send processing message to SQS
 |
 v
Return response

SQS
 |
 +--> Worker 1: Extract text
 |
 +--> Worker 2: Generate thumbnail
 |
 +--> Worker 3: Analyze document
```

The API can return a response without waiting for document processing to finish.

### 8.2 Decoupling microservices

Consider an application with several independent services.

```text
              Order Service
                   |
                   v
                SQS Queue
                   |
          +--------+--------+
          |        |        |
          v        v        v
       Payment  Inventory  Shipping
       Worker    Worker     Worker
```

The Order Service does not need to know how the other services are implemented.

It only needs to send messages.

This reduces direct dependencies between services.

One important architectural distinction: this example distributes work among consumers of one queue. If all three services must independently receive the same event, an SNS-to-multiple-SQS-queues fanout architecture is generally more appropriate.

### 8.3 Traffic buffering

SQS can absorb temporary traffic spikes.

For example:

* An application receives 50,000 requests during a promotional event.

* It places processing tasks into SQS.

* Workers process messages according to available capacity.

* The backlog decreases as processing continues.

This is useful when producers and consumers have different processing speeds.

### 8.4 Distributed task processing

Suppose you need to process one million images.

Instead of using one application instance, you can distribute tasks across multiple workers.

```text
              SQS Queue
                  |
       +----------+----------+
       |          |          |
       v          v          v
    Worker 1   Worker 2   Worker 3
       |          |          |
       v          v          v
    Images     Images     Images
```

You can increase the number of consumers as workload increases.

### 8.5 Combining SQS with other AWS services

Some common architectural patterns include:

Pattern A — S3 → SQS → Lambda

![New pattern submission s3-sqs-lambda · Issue #29 · aws-samples/serverless-patterns · GitHub](https://images.openai.com/static-rsc-4/FN70yZdplahImelnAo9S0SrA4xC7B_tTBKn6jpM5TF-T_XI5gN7QLQpo3EfmZsHu-JyUuK-pXcuDD9sVDY5CuADz0M9PvWsJkxaQ7p8mKsouRcMQ_JmN0Md5-aDmm6TpIFxwqSuc6GgW5g-BSfJFQ5j7fD8G5ysOUJlriOFfdcAQyimVbZtx4AXdrUrPfcj4?purpose=fullsize)

* A file is uploaded to S3.

* S3 sends an event notification to SQS.

* Lambda consumes the message.

* Lambda processes the file.

Pattern B — SNS → SQS → Multiple Consumers

![Mastering AWS SQS + SNS: Scalable, Event-Driven Architectures with Spring Boot ☁️ | by Anderson Kuntz Meurer | Medium](https://images.openai.com/static-rsc-4/7mQfQS7xiag3Zsh8SRnum8GH5f1eXJl1mNJKgElPQsKmPfuz0fZRNPfZs6msw-diMlmGvwSOR386qIWFDCCoxWn1K6BrysdGrGiEkTw-vFXLD9P8oCnPfwmaR6KcAvwJNA803rs0SmyrjUV7TjNbaFc_j8Fy66n3lmPiHtD2kMrSnEx8v1y9HBCROlr3KenV?purpose=fullsize)

* An application publishes an event to SNS.

* SNS distributes copies to multiple SQS queues.

* Independent services consume their respective queues.

Pattern C — API Gateway → Lambda → SQS → ECS

![Process events asynchronously with Amazon API Gateway, Amazon SQS, and AWS Fargate - AWS Prescriptive Guidance](https://images.openai.com/static-rsc-4/diMWalN7NH_3un3uK97azhzniNfcNgitUJZlTrVeevTt2uZWUG-W7MFllnNyf-GILyG7hCiipSRgztLKIFc6flJhuEZfzVlyZAGd-jxzvxNI23ayHUv-_VRcMtPA2CEdSDR2Otr-LHSqWRYwIZdjUTf1ClRL0HtumF8UJcMj6b1jui6eu246GWuR5QK-ptdY?purpose=fullsize)

* API Gateway receives an HTTP request.

* Lambda validates the request.

* Lambda sends a message to SQS.

* ECS workers process the message.

These patterns will become especially important when we study SNS and production architectures later.

### 9\. SQS pricing model, quotas, and service limits

Before deploying SQS in production, you need to understand its pricing and operational limitations.

### 9.1 SQS pricing model

Amazon SQS uses a pay-per-request pricing model.

You generally pay based on:

* Number of API requests.

* Queue type and applicable request pricing.

* Message payload size.

* Additional AWS services used alongside SQS.

* Applicable data transfer charges.

There is no minimum monthly service fee.

AWS currently advertises 1 million SQS requests per month in its Free Tier offering. Always check the applicable offer terms.

Official pricing: [Amazon SQS pricing](https://aws.amazon.com/sqs/pricing/?utm_source=chatgpt.com).

### 9.2 What counts as a request?

Every SQS API action counts as a request.

Common examples:

| API operation           | Purpose                      |
| ----------------------- | ---------------------------- |
| SendMessage             | Send a message               |
| ReceiveMessage          | Retrieve messages            |
| DeleteMessage           | Delete a processed message   |
| ChangeMessageVisibility | Change visibility timeout    |
| GetQueueAttributes      | Retrieve queue configuration |
| CreateQueue             | Create a queue               |

An important detail is that message batching can reduce request costs.

For example:

Without batching:

```text
SendMessage -> 1 request
SendMessage -> 1 request
SendMessage -> 1 request
SendMessage -> 1 request
SendMessage -> 1 request

Total: 5 requests
```

With batching:

```text
SendMessageBatch -> 1 request

5 messages sent together.

Total: 1 request
```

SQS supports up to 10 messages per batch, subject to the batch payload limit.

### 9.3 Message size and payload limits

Some important SQS quotas are:

| Limit                      | Value      |
| -------------------------- | ---------- |
| Maximum message size       | 1 MiB      |
| Maximum messages per batch | 10         |
| Maximum message attributes | 10         |
| Default message retention  | 4 days     |
| Maximum message retention  | 14 days    |
| Maximum visibility timeout | 12 hours   |
| Maximum delay              | 15 minutes |
| Maximum long polling wait  | 20 seconds |

These are useful baseline limits to know.

For larger payloads, you can store the actual data in S3 and send an S3 object reference through SQS.

For example:

```json
{
  "task_id": "TASK-1001",
  "bucket": "document-storage",
  "object_key": "uploads/document.pdf"
}
```

The consumer retrieves the actual file from S3.

This is generally preferable to putting large files directly into messages.

Official reference: [SQS message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html?utm_source=chatgpt.com).

### 9.4 Standard and FIFO throughput

Standard queues support very high, nearly unlimited throughput.

FIFO queues have throughput limits that depend on:

* AWS Region.

* Throughput mode.

* Whether batching is enabled.

* Number and distribution of message groups.

For example, FIFO high-throughput configurations can achieve significantly higher throughput than the default FIFO configuration.

You should not assume that every FIFO queue has the same throughput limit across all Regions.

See [FIFO queue quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-fifo.html?utm_source=chatgpt.com) for the regional details.

### 9.5 In-flight messages

An in-flight message is a message that has been received but has not yet been deleted.

For example:

```text
SQS Queue
    |
    v
Consumer receives message
    |
    v
Message becomes invisible
    |
    v
Consumer processes message
    |
    +--> Delete successfully
    |
    +--> Processing fails
             |
             v
       Visibility timeout expires
             |
             v
       Message becomes available again
```

SQS has in-flight message quotas, so consumers should not receive messages indefinitely without deleting them.

This becomes particularly important in high-throughput applications.

We will study visibility timeout and in-flight message management in Module 2 and Module 4.

### 10\. Key architectural takeaways

Let's summarize the most important concepts from this module.

| Concept                    | What you should understand                       |
| -------------------------- | ------------------------------------------------ |
| Asynchronous communication | Producers don't wait for consumers               |
| Producer                   | Sends messages                                   |
| Queue                      | Temporarily stores messages                      |
| Consumer                   | Retrieves and processes messages                 |
| Standard queue             | High throughput, at-least-once delivery          |
| FIFO queue                 | Strict ordering within message groups            |
| Queue URL                  | Used for queue API operations                    |
| Queue ARN                  | Used for resource identification and permissions |
| Pull-based messaging       | Consumers retrieve messages                      |
| Long polling               | Reduces unnecessary empty receives               |
| Visibility timeout         | Temporarily hides received messages              |
| Idempotency                | Makes duplicate processing safe                  |
| Dead-letter queue          | Isolates repeatedly failing messages             |

### 11\. What comes next?

In Module 2, we'll move from architecture to actual SQS operations.

We'll work with:

* Creating and configuring queues.

* Sending messages with AWS CLI and Python Boto3.

* Receiving and deleting messages.

* Message bodies, attributes, and metadata.

* Short polling and long polling.

* Visibility timeout.

* Message retention and delivery delay.

* Batch operations.

* Managing queues using Pulumi (Python).

We'll also examine how a Python application communicates with SQS and how messages move through their lifecycle.

### Official AWS references

* [Amazon SQS Developer Guide](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/?utm_source=chatgpt.com).

* [Standard queues](https://docs.aws.amazon.com/en_gb/AWSSimpleQueueService/latest/SQSDeveloperGuide/standard-queues.html?utm_source=chatgpt.com).

* [FIFO queues](https://docs.aws.amazon.com/en_en/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-fifo-queues.html?utm_source=chatgpt.com).

* [Message quotas](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/quotas-messages.html?utm_source=chatgpt.com).

* [SQS pricing](https://aws.amazon.com/sqs/pricing/?utm_source=chatgpt.com).

End of Module 1.
