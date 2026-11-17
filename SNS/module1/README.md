### Module 1 — SNS Fundamentals and Messaging Architecture

Amazon Simple Notification Service (SNS) · Fundamentals and Architecture

### 1\. Messaging Systems and Publish-Subscribe Architecture

Before understanding Amazon SNS, we need to understand messaging systems and why modern applications use them.

### 1.1 What is a messaging system?

A messaging system allows different application components to communicate by exchanging messages rather than directly calling each other.

Consider an e-commerce application.

When a customer places an order, several operations might need to happen:

* Process the payment.

* Update inventory.

* Send an order confirmation email.

* Notify the shipping service.

* Update analytics.

A simple implementation might have the order service directly call every other service.

![Building Event-Driven Applications on AWS - Speaker Deck](https://images.openai.com/static-rsc-4/M7vXvhpcPSMztBf9nxv_oIczC41BQpeMq37avBeo4A8ZyMfMJRSOrPZgJpgr8yVFVVfk_Vb-BSzzrakefRMedLMmmM-ysX7k_U0z38Uhknm-Mq_DTkUU0NJuvp5vA3Oj6yZYGTpUn1zKrKkV5C7KqZGYWTdqQbYIwAx7WvwY8HnatCmRMD5t7bUHh7NWYMDC?purpose=fullsize)

This approach creates several problems:

* Tight coupling: The order service needs to know about every downstream service.

* Availability dependency: If the email service is unavailable, the order workflow might fail.

* Scalability: Adding another consumer requires modifying the order service.

* Maintenance: Changes in downstream services can affect the order service.

* Failure propagation: One service's failure can affect other components.

Messaging systems solve these problems by introducing an intermediary that distributes messages between application components.

Instead of directly communicating, services publish messages to a messaging system, and other services consume them.

![A Guide To Event-Driven Architectural Patterns](https://images.openai.com/static-rsc-4/sZMoyesW4R4TDpCSzxNmNOfJMGlVJ1F51amD7Ssmh8JvWM_P08Fj9s_PEUgt53xh9xxaMFyODEyDv6CnRl6RuZ-VEYk918IFhhdzTVB3ieYSAPjwf2GufDccisYGgUR7Y5El_fa5as0HEA-BKfOlS0i7ZnLA-gUxPKdL60cD5lmU9uWo6zj38sL0ez-P7W9J?purpose=fullsize)

The main benefits are:

* Loose coupling between services.

* Better scalability.

* Independent deployment and development.

* Improved fault isolation.

* Asynchronous processing.

* Easier integration between distributed systems.

### 1.2 What is publish-subscribe (Pub/Sub)?

Publish-subscribe is a messaging pattern in which publishers send messages to a central communication channel, and subscribers receive messages from that channel.

It has three primary concepts:

Publisher: An application or service that generates and publishes messages.

Topic: A logical communication channel that receives published messages.

Subscriber: An application or service that subscribes to a topic and receives its messages.

For example, imagine an order management system:

* The order service publishes an `OrderCreated` event.

* The topic receives the event.

* The inventory service subscribes to the topic.

* The notification service subscribes to the topic.

* The analytics service subscribes to the topic.

All three subscribers receive the same event independently.

![What are Message Queues and When to Use Them?](https://images.openai.com/static-rsc-4/Ag7VjiM9UXJyWw2UBK81ZcLhpUlirQxf3X2D88DXsZBMLSzXl-afoY-MmnrBfe31ggY7P76kPEF59CHHsrrX4imfsywlxY11UPhUbc46dHh3tuECzDc6Pm3t8MldvOcwneai7QwNbbYT5Zi5Hhm39xFQsDqQY4J9iRS3jjVe5kX8peVLAmhWH6qrynNAXu7e?purpose=fullsize)

The important concept is that the publisher does not need to know who the subscribers are.

It only needs to know where to publish the message.

This is called loose coupling.

### 1.3 Pub/Sub versus point-to-point messaging

Two important messaging patterns are point-to-point messaging and publish-subscribe messaging.

| Characteristic       | Point-to-point                      | Publish-subscribe                |
| -------------------- | ----------------------------------- | -------------------------------- |
| Communication        | Producer to queue                   | Publisher to topic               |
| Consumers            | Typically competing consumers       | Multiple independent subscribers |
| Message distribution | One consumer processes each message | Each subscriber receives a copy  |
| Main purpose         | Task distribution                   | Event distribution               |
| AWS service          | SQS                                 | SNS                              |

This distinction is particularly important because SNS and SQS solve different messaging problems.

SQS: A queue distributes work among consumers. Multiple consumers can compete to process messages from the same queue.

SNS: A topic distributes notifications to multiple subscribers. Each subscription represents an independent delivery destination.

For example, if an order event must be processed by three independent services, SNS is a natural choice.

If thousands of order-processing tasks must be distributed among multiple workers, SQS is a natural choice.

And, importantly, SNS and SQS can work together.

### 2\. Synchronous versus Asynchronous Communication

Understanding this distinction is essential for designing event-driven applications.

### 2.1 Synchronous communication

Synchronous communication means the caller sends a request and waits for a response before continuing.

A typical example is an HTTP REST API call.

![Intro to Event-driven architecture](https://images.openai.com/static-rsc-4/n_JOdR3IjjjvhnjrEN_4gRf702o4opYyWcTF0PBmo3-qW2riJRYlohaEZHgJcCNNZ2Dc97vxZ7lMOEoHoO_IavIVVJWeYr1VwHG6-znzEK_oEcdmJKv0APhK-o27Jm7crZrmJ3xE4B4Hih1ZA5HSC1wfZxu-xf18oQF63t5UkYrE12CCa_fhahaZBOpDUbKY?purpose=fullsize)

Consider an application calling a payment service:

* The application sends a payment request.

* The payment service processes the request.

* The payment service returns a response.

* The application continues execution.

The caller is directly dependent on the response.

Common characteristics:

* Request-response communication.

* The caller waits for completion or a response.

* Immediate feedback.

* Stronger runtime dependency between services.

* Timeouts and failures can affect the caller.

### 2.2 Asynchronous communication

Asynchronous communication means the sender does not need to wait for the receiving application to finish processing the message.

For example:

* The order service publishes an `OrderCreated` event.

* SNS accepts the publication.

* SNS distributes the message to subscribers.

* Subscribers process the event independently.

![Event-Driven Architecture | arc42 Quality Model](https://images.openai.com/static-rsc-4/sXLJ7zyQMU_BCvdPLlHILIJvPQJADRLq4TxXvNQpVFi3Nr_5saXdNY-N6rGOG4KBjWIXhzcjuSOjG6SnjM023C52w3g3RrEBw4i29c1IGePhxcsOnQuC6Sjmv9hcTIsrH5alEhJDgtS6VvJDXThJRxYTolI_TmxJjDgIn6fn1xeuBUVJCexT9mE4lLh9nvEU?purpose=fullsize)

The publisher does not need to wait for all subscribers to complete their processing.

Common characteristics:

* Decoupled communication.

* Independent processing.

* Better scalability.

* Better tolerance of temporary downstream failures.

* Processing can happen later.

* More complex failure handling and observability.

### 2.3 Important distinction: asynchronous does not mean guaranteed processing

An asynchronous publishing operation does not automatically guarantee that every subscriber successfully processes the message.

There are different stages:

* The publisher sends a message.

* SNS accepts the message.

* SNS attempts delivery to subscriptions.

* The destination receives the message.

* The destination application processes it successfully.

These are separate events.

For example, SNS might successfully accept a message but encounter repeated delivery failures when trying to reach an HTTP endpoint.

This is why retry policies, delivery monitoring, and dead-letter queues are important.

### 2.4 Synchronous versus asynchronous comparison

| Feature          | Synchronous             | Asynchronous                 |
| ---------------- | ----------------------- | ---------------------------- |
| Caller waits     | Yes                     | Usually no                   |
| Communication    | Request-response        | Message/event-based          |
| Coupling         | Often tighter           | Usually looser               |
| Failure handling | Often immediate         | Often deferred               |
| Scalability      | Depends on request path | Supports independent scaling |
| Example          | HTTP API call           | SNS publication              |

Important: SNS is primarily an asynchronous messaging service, although publishing a message through its API is itself a synchronous API request. The publisher waits for SNS to acknowledge the publication, not for every subscriber to finish processing.

### 3\. Amazon SNS Architecture and Core Components

![What is Amazon SNS? - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/AdW1pMfvV6GguKVKs0JIVOV_nq0uZw_wF7j4dw0dlDvXhzSlZ4Yxq9kqpCjZz_R3sFm4ffqiNZG0mD_kj6QZSj7HGVQCo-Xz4eVIc-BiPaz-nw5oLXo_zenQzPA4Gv_aHqIDsYaZMhqZ1nXlc3MonD6cg3zMI2PB8K1MTvsBuzA2cjR-uT-dAKxNFBIjQuH7?purpose=fullsize)

Amazon Simple Notification Service (SNS)

Fully managed publish-subscribe messaging service provided by AWS.

Amazon SNS is a fully managed messaging service that enables applications to publish messages to topics and distribute them to multiple subscribers.

SNS handles much of the underlying infrastructure, including:

* Topic management.

* Message distribution.

* Subscription management.

* Delivery attempts.

* Retry mechanisms.

* Message filtering.

* Integration with AWS services.

You do not need to operate your own message broker infrastructure.

### 3.1 High-level SNS architecture

The basic architecture looks like this:

![Creating an SNS (Simple Notification Service) using the AWS Command Line Interface (CLI) | by Kunalmathur | Medium](https://images.openai.com/static-rsc-4/y-pqHOlZsjrD6NzwybiPdi80_oDQhZCdLPNR8ySECz7IVkEAN4ItoAp3BppI6_zNVDz8Y9xOba38bOafpK7poypnrRkm8FQ4rOl4NOhWqChnU8GwWcDHtqpTK534n48yF3S6Z1K6kf-vnlxWTIuOpPO3jkdEuwxzkORfQrGyGcSKTcq5ULJOVaoRamuaPf7M?purpose=fullsize)

The main flow is:

* A publisher sends a message to an SNS topic.

* SNS receives and accepts the message.

* SNS identifies the topic's subscriptions.

* SNS applies subscription filtering when configured.

* SNS delivers the message to eligible subscribers.

* Each subscriber independently handles the message.

### 3.2 SNS core components

Let's examine the major components.

1\. Publisher

A publisher is any application or AWS service that sends messages to an SNS topic.

Examples:

* Python applications using Boto3.

* AWS Lambda functions.

* Amazon S3 event notifications.

* Amazon EventBridge rules.

* Backend services.

* AWS CLI commands.

A publisher needs permission to publish to the topic.

2\. Topic

A topic is a logical communication channel.

It acts as the central destination for messages.

For example:

* `orders`

* `payments`

* `user-notifications`

* `system-alerts`

Topics can have multiple subscribers.

3\. Subscription

A subscription connects a topic to a destination.

A topic can have multiple subscriptions, and each subscription defines how messages should be delivered.

For example:

| Topic  | Subscription endpoint        |
| ------ | ---------------------------- |
| Orders | SQS inventory queue          |
| Orders | SQS analytics queue          |
| Orders | Lambda notification function |
| Orders | HTTPS application endpoint   |

Each subscription is independently managed.

4\. Subscriber

A subscriber is the destination that receives messages from SNS.

SNS supports several endpoint types:

| Protocol    | Destination                       |
| ----------- | --------------------------------- |
| SQS         | Amazon SQS queue                  |
| Lambda      | AWS Lambda function               |
| HTTP        | HTTP endpoint                     |
| HTTPS       | Secure HTTP endpoint              |
| Email       | Email address                     |
| Email-JSON  | JSON-formatted email              |
| SMS         | Mobile phone number               |
| Application | Mobile push notification platform |

Some subscription types require endpoint confirmation before activation.

For example, an email subscriber generally needs to confirm its subscription.

5\. Message

A message is the data published to an SNS topic.

It may contain:

* Event information.

* Business data.

* Notification text.

* JSON payloads.

* Message attributes.

An example order event:

```json
{
  "eventType": "OrderCreated",
  "orderId": "ORD-10025",
  "customerId": "CUS-5001",
  "total": 149.99,
  "currency": "USD"
}
```

The topic distributes the message to eligible subscriptions.

6\. Message attributes

Message attributes are additional metadata associated with a published message.

For example:

```json
{
  "eventType": {
    "DataType": "String",
    "StringValue": "OrderCreated"
  },
  "priority": {
    "DataType": "String",
    "StringValue": "High"
  }
}
```

Attributes are particularly useful for message filtering.

We will examine them in detail in Module 3.

### 4\. Topics, Publishers, Subscribers, and Subscriptions

Now let's examine how these components work together in a real application.

### 4.1 Topic-based communication

Imagine an e-commerce application with the following services:

* Order Service

* Inventory Service

* Payment Service

* Notification Service

* Analytics Service

When a customer places an order, the Order Service publishes an event to an SNS topic named `orders`.

![Startup Ground to Cloud: Launching Fanout Pattern to AWS Cloud - Post | Triglon Technologies | Triglon](https://images.openai.com/static-rsc-4/J2zgZDStw1viozhA_OSD18GuSc3RZj5WAYBbRgNprdJdqmI_mL_9xsZefg83sbj1cTi5KPxQeexFMA7MYl3WhHMvnI08NB2oam7ljT8aKC_OScMp3nT1XKKccFQeWsLDOju9Kljwuln5MAwrrljxBHgtjhB4dRU6ABM4jp9LSc8yYjg1X_Rk3qI5qK1dheXQ?purpose=fullsize)

The topic distributes the event to its subscribers.

Each subscriber can perform a different operation:

| Subscriber           | Responsibility                     |
| -------------------- | ---------------------------------- |
| Inventory Service    | Update product inventory           |
| Payment Service      | Process payment-related operations |
| Notification Service | Send order confirmation            |
| Analytics Service    | Record order statistics            |

The Order Service does not need to know how these services are implemented.

It only publishes an event.

### 4.2 One topic, multiple subscriptions

An SNS topic can have multiple subscriptions.

For example:

```text
Topic: orders

Subscriptions:
    ├── SQS: inventory-queue
    ├── SQS: analytics-queue
    ├── Lambda: notification-function
    └── HTTPS: external-system.example.com
```

Each subscription is an independent delivery destination.

This architecture provides several advantages:

* Adding a new subscriber does not require changing the publisher.

* Subscribers can use different technologies.

* Each subscriber can process the same event independently.

* Different services can scale independently.

* Failures in one destination do not necessarily prevent delivery to other destinations.

### 4.3 Topic versus subscription

These concepts are easy to confuse.

| Topic                           | Subscription                      |
| ------------------------------- | --------------------------------- |
| Communication channel           | Connection to a destination       |
| Receives published messages     | Receives eligible messages        |
| Can have multiple subscriptions | Belongs to a topic                |
| Has a topic ARN                 | Has a subscription ARN            |
| Defines the messaging resource  | Defines the delivery relationship |

An important architectural point: SNS does not turn a topic into a queue. A topic distributes messages to subscribers; it does not provide the same persistent, consumer-polling model as SQS.

### 5\. SNS Standard Topics and FIFO Topics

Amazon SNS provides two main topic types:

* Standard topics.

* FIFO (First-In, First-Out) topics.

Choosing the correct type depends on your application's ordering, throughput, and deduplication requirements.

### 5.1 Standard topics

Standard topics are designed for high-throughput, scalable message distribution.

They are suitable when:

* High message throughput is important.

* Strict message ordering is unnecessary.

* Occasional duplicate deliveries can be handled.

* Multiple subscribers need independent notifications.

Example:

A monitoring system publishes application alerts:

```text
Application Alert
       |
       v
   SNS Topic
       |
       ├── Email notification
       ├── Operations Lambda
       ├── SQS monitoring queue
       └── External HTTPS endpoint
```

The notifications do not necessarily need to arrive in exactly the same order in which they were published.

Standard topics are therefore appropriate.

### 5.2 FIFO topics

FIFO topics provide stronger ordering and deduplication capabilities.

They are designed for applications where message sequence matters.

For example, consider a banking application:

```text
AccountCreated
MoneyDeposited
MoneyWithdrawn
AccountClosed
```

Processing these events out of order could cause serious business problems.

FIFO topics provide:

* Message ordering within message groups.

* Message deduplication.

* Ordered delivery to supported FIFO destinations.

* Integration with Amazon SQS FIFO queues.

A FIFO topic uses message group IDs to define ordering boundaries.

Messages within the same message group are delivered in order.

Different message groups can be processed independently.

![Detalhes de ordenação de mensagens do Amazon SNS para tópicos FIFO - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/nT3VHdcw4_W9rbxASARXQo1qxKV4r9RfVWtsIYZUexykmIMSD6QlUcvXLx64qf2gfzvSxj6JBLfVlyYG66UMZD2IH6TbsVmw8MRfUlUtvn_6Zyp1wL4_HJ8yeYS95BkCAkuwyM8Yw_dZGwBsyz-p8zIkZlG6i5xFCksPVhwy7zNczo5bMgPgp-v0_ib8dwg0?purpose=fullsize)

### 5.3 Standard versus FIFO

| Feature         | Standard                             | FIFO                                    |
| --------------- | ------------------------------------ | --------------------------------------- |
| Throughput      | High                                 | Configurable, with FIFO-specific limits |
| Ordering        | Best effort                          | Preserved within message groups         |
| Deduplication   | No FIFO deduplication feature        | Supported                               |
| Message groups  | No                                   | Yes                                     |
| Typical use     | Notifications and event distribution | Ordered business events                 |
| SQS integration | Standard queues                      | FIFO queues                             |

Important: FIFO does not automatically guarantee exactly-once business processing. Deduplication reduces duplicate publishing and delivery within its defined scope, but consumers must still be designed to handle duplicate processing safely.

### 5.4 When should you use each?

Use Standard topics for:

* System notifications.

* Monitoring alerts.

* Email and SMS notifications.

* General event distribution.

* High-throughput fanout architectures.

Use FIFO topics for:

* Financial transaction events.

* Ordered business workflows.

* Inventory operations where event sequence matters.

* Applications that require message deduplication.

### 6\. Topic ARNs and Regional Architecture

AWS resources have unique identifiers called Amazon Resource Names (ARNs).

An SNS topic ARN identifies a specific topic within AWS.

### 6.1 Understanding SNS topic ARNs

An SNS topic ARN follows this structure:

```text
arn:aws:sns:REGION:ACCOUNT_ID:TOPIC_NAME
```

For example:

```text
arn:aws:sns:eu-west-2:123456789012:orders
```

Let's break it down:

| Component    | Meaning              |
| ------------ | -------------------- |
| arn          | Amazon Resource Name |
| aws          | AWS partition        |
| sns          | AWS service          |
| eu-west-2    | AWS Region           |
| 123456789012 | AWS account ID       |
| orders       | Topic name           |

The ARN is important because it is used in:

* IAM policies.

* SNS topic policies.

* AWS CLI commands.

* Boto3 applications.

* Cross-account permissions.

* AWS service integrations.

For example, a publisher's IAM policy might grant permission to publish to a specific topic ARN rather than every SNS topic in the account.

### 6.2 Regional architecture

SNS topics are regional resources.

A topic created in `eu-west-2` belongs to that Region.

A topic created in `us-east-1` is a separate resource.

For example:

```text
AWS Account: 123456789012

eu-west-2
    └── SNS: orders

us-east-1
    └── SNS: orders
```

Although the topics have the same name, they have different ARNs.

This matters when designing multi-region applications.

### 6.3 Regional messaging considerations

Suppose an application operates in London and Virginia.

You might create one SNS topic in each Region:

* London application publishes to the London topic.

* Virginia application publishes to the Virginia topic.

This provides regional isolation and can reduce unnecessary cross-region communication.

However, SNS does not automatically replicate every topic and message to another Region.

For cross-region architectures, you need an explicit replication or forwarding design.

Possible approaches include:

* Publishing to multiple regional topics.

* Using Lambda to forward messages between Regions.

* Using EventBridge cross-region event routing where appropriate.

* Designing application-level event replication.

![Coordinating large messages across accounts and Regions with Amazon SNS and SQS | AWS Architecture Blog](https://images.openai.com/static-rsc-4/hf498ryBqohB72nho7B-jxGwKaW0vXxERoNXjukzdQDQLCJDU09vc2RAcAPBBtCaAXYyuwLAeIYQJYbv1G4p2-RNS6n9DKfS4I5AQUC0MaTJeruCVUWrudoEa5w0fccFFo9jaNHQXfnzv514O4Wxgveypdiy6pRQSbl9z3L6wGAotb_SBpyLL2IORrNUl_b2?purpose=fullsize)

### 6.4 SNS and cross-account communication

SNS also supports communication between AWS accounts.

For example:

```text
Account A
    Order Application
          |
          v
      SNS Topic
          |
          v
Account B
    SQS Queue
```

The topic owner can configure a resource-based topic policy to allow an authorized external account to subscribe or publish, depending on the intended permissions.

This is useful for:

* Multi-account architectures.

* SaaS platforms.

* Centralized event distribution.

* Shared infrastructure.

* Organizational event-driven systems.

### 7\. Push-Based Messaging and Message Delivery

One of the most important differences between SNS and SQS is how messages reach their consumers.

### 7.1 Push-based messaging

SNS primarily uses a push-based delivery model.

When a message is published, SNS attempts to deliver it to the topic's subscribers.

The publisher does not need to contact each subscriber individually.

For example:

```text
Publisher
    |
    v
 SNS Topic
    |
    ├── Push → Lambda
    ├── Push → HTTPS endpoint
    ├── Push → SQS queue
    ├── Push → Email
    └── Push → SMS
```

SNS manages the distribution process.

### 7.2 SNS versus SQS delivery models

This is an important distinction from our previous SQS course.

![Pub-Sub vs Message Queue. When you work with distributed systems… | by chahat arora | Medium](https://images.openai.com/static-rsc-4/_vNkbH1BFFQwJ3LVXfDIMpLg2TwDKpDjbjOQtoCdXLPR9pP1xi_fSjge3K-6beUOzp2dK-_QIYvSoGlYWAjV05Cx51vTSwhfG3F9uqOKLjm-WehlO1I-5X8YtieU9zVlEdUxjgEX7SS2xToZBb-xA72ZwPzKLvlA06-LDJNImRsURJRDfq4tLMlBiufiMD7r?purpose=fullsize)

| Characteristic     | SNS                                 | SQS                      |
| ------------------ | ----------------------------------- | ------------------------ |
| Primary model      | Push                                | Pull                     |
| Main resource      | Topic                               | Queue                    |
| Message delivery   | SNS pushes to subscribers           | Consumers poll queues    |
| Multiple consumers | Independent subscriptions           | Competing consumers      |
| Message storage    | Not a general-purpose durable queue | Persistent queue storage |
| Main purpose       | Event distribution                  | Work distribution        |

A nuance worth understanding: SNS can push directly to Lambda, but Lambda can also integrate with SQS through an event source mapping that polls the queue and invokes the function.

These are different integration models.

### 7.3 Why combine SNS and SQS?

Consider an order-processing application.

If SNS directly invokes multiple Lambda functions, each function receives notifications when messages are published.

But what happens if a consumer needs to process messages at its own pace, or temporarily cannot keep up?

This is where SQS becomes useful.

```text
                  SNS Topic
                      |
          +-----------+-----------+
          |                       |
          v                       v
    SQS Queue A              SQS Queue B
          |                       |
          v                       v
    Lambda A                  Lambda B
```

Now each consumer has its own queue.

Benefits include:

* Independent message buffering.

* Consumer-controlled processing rates.

* Better isolation between services.

* Queue-level visibility and monitoring.

* Independent retry and DLQ configurations.

This pattern is commonly called SNS fanout with SQS buffering.

### 7.4 Push does not mean immediate or simultaneous delivery

SNS attempts delivery to subscribers independently.

You should not assume:

* Every subscriber receives the message at exactly the same time.

* All subscribers finish processing simultaneously.

* A successful publication means every destination has processed the message.

SNS publication and subscriber delivery are separate operations.

This distinction becomes especially important in production systems.

### 8\. SNS Delivery Guarantees and Message Ordering

SNS provides different delivery behavior depending on the topic type and subscription protocol.

### 8.1 At-least-once delivery

For supported delivery protocols, SNS uses retry mechanisms to improve the likelihood of successful delivery.

However, duplicate deliveries can occur.

For example:

```text
Publisher
    |
    v
SNS Topic
    |
    v
Subscriber
    |
    v
Message processed
```

If a delivery is retried because SNS does not receive the expected acknowledgment, the destination may encounter the same message more than once.

This is why consumers should be designed to be idempotent.

### 8.2 What is idempotency?

An operation is idempotent when executing it multiple times produces the same final result as executing it once.

Consider an order-processing service.

A message contains:

```json
{
  "eventId": "evt-1001",
  "orderId": "ORD-5001",
  "eventType": "OrderCreated"
}
```

The consumer can maintain a record of processed event IDs.

Before processing a message:

* Check whether `eventId` has already been processed.

* If yes, ignore the duplicate.

* If no, perform the business operation.

* Record the event ID as processed.

This prevents duplicate business operations.

For example, a customer should not be charged twice because a notification was delivered twice.

In production, the business operation and deduplication record should be handled atomically where possible.

### 8.3 Message ordering

Standard SNS topics do not guarantee strict message ordering.

Imagine publishing:

```text
Message 1: OrderCreated
Message 2: PaymentCompleted
Message 3: OrderShipped
```

A subscriber should not assume that these messages will always arrive in precisely that sequence.

FIFO topics provide ordering guarantees within a message group.

For example:

```text
Message Group: customer-100

1. AccountCreated
2. MoneyDeposited
3. MoneyWithdrawn
```

These messages maintain their ordering within that group.

Different message groups can be processed independently.

### 8.4 Delivery guarantees summary

| Feature                          | Standard SNS            | FIFO SNS                |
| -------------------------------- | ----------------------- | ----------------------- |
| Duplicate handling               | Duplicates possible     | Deduplication supported |
| Strict ordering                  | No                      | Within message groups   |
| Retry mechanisms                 | Yes, protocol-dependent | Yes, protocol-dependent |
| Exactly-once business processing | Not guaranteed          | Not guaranteed          |
| Idempotent consumers             | Recommended             | Still recommended       |

The main lesson is that messaging infrastructure cannot replace correct application-level failure handling.

### 9\. SNS Use Cases and Architectural Patterns

SNS is useful in many distributed application architectures. Let's examine the most important patterns.

### 9.1 Application notifications

An application publishes notifications to an SNS topic, which distributes them to email, SMS, Lambda, or HTTP subscribers.

Example:

```text
E-commerce Application
          |
          v
     SNS Topic
          |
     +----+----+
     |         |
     v         v
   Email      SMS
```

Typical use cases:

* Order confirmations.

* Password-reset notifications.

* Account alerts.

* Payment notifications.

* Operational alerts.

### 9.2 Fanout architecture

Fanout means distributing one published message to multiple independent destinations.

For example, an order event can be delivered to:

* Inventory processing.

* Analytics.

* Customer notifications.

* Shipping workflows.

![Mastering AWS SQS + SNS: Scalable, Event-Driven Architectures with Spring Boot ☁️ | by Anderson Kuntz Meurer | Medium](https://images.openai.com/static-rsc-4/7mQfQS7xiag3Zsh8SRnum8GH5f1eXJl1mNJKgElPQsKmPfuz0fZRNPfZs6msw-diMlmGvwSOR386qIWFDCCoxWn1K6BrysdGrGiEkTw-vFXLD9P8oCnPfwmaR6KcAvwJNA803rs0SmyrjUV7TjNbaFc_j8Fy66n3lmPiHtD2kMrSnEx8v1y9HBCROlr3KenV?purpose=fullsize)

This pattern is especially useful in microservices architectures.

A service can publish an event without knowing how many other services will consume it.

### 9.3 Event-driven microservices

SNS allows microservices to communicate through events rather than direct API calls.

Example:

```text
Order Service
     |
     v
 SNS: order-events
     |
     +------> Inventory Service
     |
     +------> Payment Service
     |
     +------> Notification Service
     |
     +------> Analytics Service
```

This reduces dependencies between services and allows each service to evolve independently.

### 9.4 SNS with SQS for reliable processing

This is one of the most useful AWS messaging patterns.

```text
                  Publisher
                      |
                      v
                  SNS Topic
                      |
             +--------+--------+
             |                 |
             v                 v
        SQS Queue A       SQS Queue B
             |                 |
             v                 v
         Lambda A           Lambda B
```

Each service gets its own queue and controls its own processing rate.

This is useful when consumers:

* Need buffering.

* Have different processing speeds.

* Must tolerate temporary downtime.

* Need independent retry behavior.

* Require separate dead-letter queues.

### 9.5 AWS service notifications

SNS can also distribute notifications generated by other AWS services.

Examples include:

* Amazon S3 event notifications.

* Amazon CloudWatch alarm notifications.

* Amazon RDS event notifications.

* AWS CodeBuild notifications.

* AWS Health event notifications through supported integrations.

For example:

```text
CloudWatch Alarm
       |
       v
   SNS Topic
       |
       +------> Email
       |
       +------> Lambda
       |
       +------> SQS
```

This is particularly useful for centralized operational notifications.

### 9.6 Mobile push notifications

SNS supports mobile push notification delivery through platform applications.

It can integrate with supported push notification services such as:

* Apple Push Notification service (APNs).

* Firebase Cloud Messaging (FCM).

* Amazon Device Messaging where applicable.

A typical architecture:

```text
Mobile Application Backend
          |
          v
       SNS Topic
          |
          v
   Platform Application
          |
          v
      Mobile Devices
```

This allows backend applications to distribute notifications to registered mobile devices.

### 9.7 When should you choose SNS?

| Requirement                                  | Suitable approach   |
| -------------------------------------------- | ------------------- |
| Notify multiple independent services         | SNS                 |
| Distribute the same event to multiple queues | SNS fanout          |
| Distribute tasks among workers               | SQS                 |
| Buffer messages for later processing         | SQS                 |
| Send email or SMS notifications              | SNS                 |
| Process events asynchronously with Lambda    | SNS + Lambda        |
| Independently buffer multiple microservices  | SNS + SQS           |
| Maintain ordered event delivery              | SNS FIFO + SQS FIFO |

### 10\. SNS Pricing Model and Cost Considerations

SNS uses a pay-as-you-go pricing model. You pay based on the messaging operations and delivery mechanisms you use.

Unlike operating your own messaging infrastructure, you do not pay for managing broker servers.

However, SNS costs are not limited to publishing messages. Subscriber delivery and other features can also contribute to the total cost.

### 10.1 Main pricing components

The main cost considerations include:

1\. API requests and message publishing

Publishing messages to topics contributes to SNS usage.

2\. Message delivery

Delivering messages to subscribers can generate additional charges depending on the protocol and destination.

For example:

* SQS delivery.

* Lambda delivery.

* HTTP/HTTPS delivery.

* Email delivery.

* SMS delivery.

3\. SMS notifications

SMS has a different pricing model from ordinary topic messaging.

Costs depend on factors such as:

* Destination country.

* Carrier.

* Message type.

* Message length.

* Sender configuration.

SMS can become a significant cost component for applications sending large notification volumes.

4\. FIFO topics

FIFO topics have their own pricing considerations, including message operations and payload-based request units.

5\. Additional AWS services

SNS integrations can introduce costs in other services.

For example:

* SQS charges for queue requests.

* Lambda charges for function invocations and execution.

* CloudWatch charges for certain monitoring and logging usage.

* KMS can introduce encryption-related charges.

### 10.2 Understanding message size and billing

SNS pricing can depend on the number of requests and message size.

For Standard topics, messages are subject to the SNS message-size limit, and large messages can consume multiple billing request units.

FIFO topics also have message-size and throughput considerations.

Therefore, when designing a messaging system, consider:

* Avoid publishing unnecessarily large payloads.

* Use compact event structures.

* Avoid publishing the same event repeatedly.

* Use message filtering to reduce unnecessary delivery.

* Monitor subscriber delivery volume.

### 10.3 SNS and SQS cost comparison

SNS and SQS have different billing models because they solve different problems.

| Cost consideration  | SNS                                 | SQS                                                   |
| ------------------- | ----------------------------------- | ----------------------------------------------------- |
| Main usage          | Publishing and delivery             | Queue API requests                                    |
| Message publishing  | Charged                             | Charged                                               |
| Message consumption | Delivery-related charges            | Receive/delete requests                               |
| Storage             | Not a general-purpose message queue | Message retention/storage included in service pricing |
| SMS                 | Additional SMS pricing              | Not applicable                                        |
| FIFO                | FIFO-specific pricing               | FIFO-specific pricing                                 |

### 10.4 Cost optimization strategies

For production systems:

* Use message filtering to avoid unnecessary deliveries.

* Avoid publishing large message payloads.

* Prefer batching where supported and appropriate.

* Monitor message publishing and delivery volumes.

* Avoid unnecessary SMS notifications.

* Use CloudWatch metrics to identify unexpected usage.

* Review the costs of downstream services, not only SNS.

* Choose Standard or FIFO based on actual requirements rather than defaulting to FIFO.

### 10.5 Important modern SNS capabilities

A few capabilities are worth keeping in mind as you move beyond the fundamentals:

* Message batching: `PublishBatch` supports publishing up to 10 messages in one API request, helping reduce request overhead. Amazon Simple Notification Service

* Message archiving and replay: SNS FIFO topics support native message archiving and replay, which can help recover or reprocess events. Amazon Simple Notification Service

* Message filtering: Subscribers can filter messages instead of receiving every published event.

* Delivery status logging: You can monitor delivery attempts and failures for supported protocols.

* Cross-region delivery: SNS supports architectures that distribute messages across AWS Regions. Amazon Simple Notification Service +1

For actual cost estimates, always consult the [official SNS pricing page](https://aws.amazon.com/sns/pricing/?utm_source=chatgpt.com). Pricing varies by delivery protocol, Region, message volume, and additional features. AWS +1

### 11\. Important Architectural Considerations

Before finishing this module, let's clarify a few points that will help prevent common design mistakes.

### 11.1 SNS is not a replacement for SQS

SNS and SQS solve complementary problems.

* SNS distributes events.

* SQS buffers messages and distributes work among consumers.

If a subscriber needs independent buffering, configure an SQS subscription.

### 11.2 FIFO topics have endpoint restrictions

SNS FIFO topics support SQS Standard and FIFO queues, but they cannot directly deliver to HTTP/S, email, SMS, or mobile push endpoints.

For ordered processing with Lambda, use an SNS FIFO topic subscribed to an SQS queue, and configure Lambda to consume from that queue. Amazon Simple Notification Service +1

### 11.3 SNS does not guarantee successful business processing

A successful `Publish` API response means SNS accepted the publication. It does not mean every subscriber successfully completed its business operation.

Use retries, DLQs, idempotency, and monitoring to handle failures.

### 11.4 SNS topics do not behave like persistent queues

SNS is primarily a message-distribution service, not a general-purpose queue where consumers can poll and retain messages for later processing.

For durable buffering, use SQS. For SNS FIFO, native archiving and replay are also available.

### 11.5 SNS versus EventBridge

These services overlap in event-driven architectures, but their primary purposes differ.

| Feature             | SNS                          | EventBridge                    |
| ------------------- | ---------------------------- | ------------------------------ |
| Primary model       | Pub/Sub                      | Event routing                  |
| Routing             | Topic subscriptions          | Rules and event patterns       |
| Filtering           | Subscription filter policies | Event pattern matching         |
| Main strength       | Fanout notifications         | Advanced event routing         |
| Typical integration | SNS → SQS                    | EventBridge → multiple targets |

A useful general guideline:

* Use SNS when you want to distribute a message to multiple subscribers.

* Use EventBridge when you need sophisticated event matching and routing across applications and AWS services.

AWS Decision guide +1

### 12\. Module 1 Summary

Let's consolidate the most important concepts.

| Concept          | Key takeaway                                                 |
| ---------------- | ------------------------------------------------------------ |
| Messaging system | Enables communication between distributed components         |
| Pub/Sub          | Publishers send messages to topics; subscribers receive them |
| Publisher        | Produces messages                                            |
| Topic            | Logical messaging channel                                    |
| Subscription     | Connects a topic to a destination                            |
| Subscriber       | Receives published messages                                  |
| Standard topic   | High-throughput, best-effort ordering                        |
| FIFO topic       | Ordered messaging within message groups                      |
| Topic ARN        | Unique identifier for an SNS topic                           |
| Push messaging   | SNS delivers messages to subscribers                         |
| Fanout           | One message distributed to multiple destinations             |
| Idempotency      | Protects applications from duplicate processing              |
| SNS + SQS        | Combines event distribution with independent buffering       |

### The architecture you should remember

![Amazon SNS vs. Amazon SQS: A simple comparison | Shikisoft Blog](https://images.openai.com/static-rsc-4/xp-eGacF8UCGhvWKmjsU3Otrh0XR1TjWpjAKtZcqjtSSpiUqBdLqDd27_H5KmQd54hJ3volsTvglvIJ29Wyn0IDo8PT2wuY4nz-dFE5TdfIp9eWtXu1Ml-2AqGy6zqaA3T7whPbq-kSTSnnbloeyuODDb12oqOa2cNmwY__I9j38d_VaSlR0C6KAy4kSi4tm?purpose=fullsize)

The most important idea behind Amazon SNS is decoupled message distribution.

A publisher generates an event once, SNS distributes it to multiple subscribers, and each subscriber handles its own responsibilities independently.

This is the foundation of scalable event-driven microservices architectures on AWS.

### What's next?

Module 2 — Topics, Subscriptions, Publishing, and Message Management

We'll move from architecture concepts into actual SNS resource management and message publishing:

* Creating SNS topics using AWS CLI and Pulumi.

* Standard and FIFO topic configuration.

* Creating and managing subscriptions.

* Publishing messages using AWS CLI and Python Boto3.

* Message bodies, attributes, and metadata.

* Subscription confirmation.

* Raw message delivery.

* Message lifecycle and delivery behavior.
