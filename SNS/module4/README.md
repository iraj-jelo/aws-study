### Module 4 — Message Delivery, Retries, Reliability, and Failure Handling

Amazon SNS · Intermediate to Advanced

This module focuses on one of the most important aspects of Amazon SNS: what happens after a message is published to a topic?

Publishing a message successfully does not necessarily mean that every subscriber has received or processed it successfully.

SNS must distribute messages to different types of endpoints, handle temporary failures, retry unsuccessful deliveries, and provide mechanisms for isolating messages that cannot be delivered.

We'll explore how SNS handles these situations and how to design notification systems that remain reliable even when subscribers become unavailable.

### 1\. SNS Message Delivery Architecture

Let's start with the message delivery lifecycle.

When a publisher sends a message to an SNS topic, SNS takes responsibility for distributing that message to the topic's confirmed subscriptions.

The general delivery flow is:

![Creating an SNS (Simple Notification Service) using the AWS Command Line Interface (CLI) | by Kunalmathur | Medium](https://images.openai.com/static-rsc-4/y-pqHOlZsjrD6NzwybiPdi80_oDQhZCdLPNR8ySECz7IVkEAN4ItoAp3BppI6_zNVDz8Y9xOba38bOafpK7poypnrRkm8FQ4rOl4NOhWqChnU8GwWcDHtqpTK534n48yF3S6Z1K6kf-vnlxWTIuOpPO3jkdEuwxzkORfQrGyGcSKTcq5ULJOVaoRamuaPf7M?purpose=fullsize)

The process consists of several stages:

* Publishing: A producer publishes a message to an SNS topic.

* Acceptance: SNS validates the publishing request and accepts the message.

* Subscription evaluation: SNS identifies the topic's subscriptions and evaluates their filter policies.

* Delivery: SNS attempts to deliver the message to each eligible subscriber.

* Acknowledgment: The subscriber's protocol-specific response determines whether SNS considers the delivery successful.

* Retry or failure handling: If delivery fails, SNS may retry according to the endpoint's delivery policy.

* Dead-letter handling: If supported delivery attempts are exhausted, SNS can send the undeliverable message to a configured dead-letter queue.

An important distinction:

SNS delivery success is not necessarily application processing success.

For example, suppose SNS delivers an order notification to an SQS queue.

SNS considers the delivery successful once SQS accepts the message.

However, the application consuming that SQS message might subsequently fail to process the order.

That second failure belongs to the SQS consumer-processing lifecycle, not SNS's delivery lifecycle.

This distinction becomes especially important when combining SNS, SQS, and Lambda.

### 2\. Delivery Behavior Across Different Subscription Protocols

SNS supports multiple subscription protocols, and each has a different delivery mechanism.

The endpoint's protocol determines how SNS sends messages and what constitutes a successful delivery.

![AWS SQS (Simple Queue Service) Logo PNG Vector (SVG) Free Download](https://images.openai.com/static-rsc-4/cy5CkrfhzKr1vydS3bCQVZYjHfpgMNGXHHtLBdPFbb36klAY_ATLROJwulsHnbRG2miqmevvQkpe6MFyVboet-9iAZhxBBGd69sO-fa2v6JE9b85LuuEFeTDbGsI41BLJCGkGvGeRlTpl3sUaWzFlZo9s9eK3lkzb2yFAJQmJn7kwB3N94PEsO_qxDuNuq1k?purpose=fullsize)

Amazon SQS

SNS sends messages to an SQS queue using AWS service-to-service integration.

Queue accepted message = successful delivery

![File:Amazon Lambda architecture logo.svg - Wikimedia Commons](https://images.openai.com/static-rsc-4/RcWQHLNUD9l50iP6YlMINmJt8TYqgZEqRN-8nINgp7zE21gqujKLD4ts65u2HFNyi_QpEyglpBk25Gx4fsJEyZgti-8hgekRtcZrr-73lpfJBhu7rhXILx9AwuuKlIuKa7bnn7zkgOcumIrCQnEBcgzxDbn_4e5w8TrUkaPItqvLvMlMIvJxXQApNN9Vq4uC?purpose=fullsize)

AWS Lambda

SNS invokes a subscribed Lambda function asynchronously.

Lambda accepts invocation = successful delivery

![MQTT vs Kafka, HTTP, HTTPS, and CoAP UDP: Optimizing IoT Device Communication | by Alejandro Rabadán | Data in Motion | Medium](https://images.openai.com/static-rsc-4/xQHYBDE43dnPi8exM_IWkM0SOef69X8MuZ3mowev57Zjhwt1cSQmvMKY74SAieG6WHF4L9f-VYMYgHR7arAxWfCjUGUfLMLBDqCA-CJ5acY9QQNmm2g4YiqYXdNax_Wat2zVdjLjFrL40KSk5b0MvX9Jt4CPw5U6FwS87_g0QnmYuVdad1AVjFAQGuRFuUJr?purpose=fullsize)

HTTP / HTTPS

SNS sends an HTTP POST request to the subscriber's endpoint.

Successful HTTP response = successful delivery

![Learning AWS Day by Day — Day 51 — Amazon Simple Notification Service(SNS) — Event Destinations - DEV Community](https://images.openai.com/static-rsc-4/BCQF4dywWPfOjz-pe7JSqkRRGO26KZ2cvcyuZUDapWxigPXbC4h434KGNf58MIxhDew6_JF3IYLq3-Z77xlHR_G-K46h8trSWYZeSxGyi6gxeOCB_xwBHCxGIF0tiX08QdwGXsazn8rUPz4EKsevQe9zD5d3rsI9wRhRspHilS8pHz-jWyIY4IfZJFYTud6R?purpose=fullsize)

Email / Email-JSON

SNS sends notification messages through its email delivery infrastructure.

Accepted by email delivery infrastructure

![What is Amazon SNS? - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/AdW1pMfvV6GguKVKs0JIVOV_nq0uZw_wF7j4dw0dlDvXhzSlZ4Yxq9kqpCjZz_R3sFm4ffqiNZG0mD_kj6QZSj7HGVQCo-Xz4eVIc-BiPaz-nw5oLXo_zenQzPA4Gv_aHqIDsYaZMhqZ1nXlc3MonD6cg3zMI2PB8K1MTvsBuzA2cjR-uT-dAKxNFBIjQuH7?purpose=fullsize)

SMS

SNS submits notifications to the SMS delivery infrastructure and downstream carriers.

Delivery depends on downstream networks

Let's examine the most important integrations.

### 2.1 SNS → SQS

When SNS delivers a message to SQS:

* SNS sends the message to the queue.

* SQS validates the request and its permissions.

* If SQS accepts the message, SNS considers delivery successful.

* SQS stores the message until a consumer retrieves it.

If the SQS queue is temporarily unavailable or rejects the request, SNS can retry delivery according to the applicable delivery policy.

Remember:

SNS does not wait for an SQS consumer to process the message.

### 2.2 SNS → Lambda

SNS invokes Lambda asynchronously.

This means there are two separate delivery and processing stages:

* SNS attempts to deliver the notification to Lambda.

* Lambda processes the event asynchronously.

If Lambda accepts the invocation, SNS considers its delivery successful.

If Lambda subsequently fails while executing the function, Lambda's asynchronous invocation mechanism handles the execution retry behavior.

This is a crucial distinction because SNS delivery retries and Lambda execution retries are separate mechanisms.

For example:

```text
Publisher
    |
    v
SNS Topic
    |
    v
Lambda accepts invocation
    |
    v
SNS considers delivery successful
    |
    v
Lambda execution begins
    |
    +---- Success
    |
    +---- Failure
             |
             v
      Lambda retry mechanism
```

A failure after Lambda accepts the event is not automatically an SNS delivery failure.

### 2.3 SNS → HTTP/HTTPS

SNS sends an HTTP POST request containing the notification.

The receiving application must respond appropriately.

For example:

```http
POST /notifications HTTP/1.1
Host: api.example.com
Content-Type: text/plain

{
  "Type": "Notification",
  "Message": "Order created",
  "TopicArn": "arn:aws:sns:..."
}
```

A successful HTTP response indicates that the endpoint accepted the notification.

If the endpoint returns an unsuccessful response, times out, or cannot be reached, SNS may retry according to its delivery policy.

One important operational consideration: your HTTP endpoint should acknowledge a notification only after it has safely accepted the event. Returning success before persisting the event can result in lost application work if the server subsequently crashes.

### 3\. Delivery Policies and Retry Mechanisms

A delivery policy determines how SNS retries failed deliveries.

Not every delivery failure is permanent.

Consider these examples:

| Failure            | Possible explanation                             |
| ------------------ | ------------------------------------------------ |
| HTTP 500           | Application server encountered an internal error |
| HTTP 503           | Service temporarily unavailable                  |
| Timeout            | Endpoint did not respond in time                 |
| Connection failure | Network or server problem                        |
| HTTP 400           | Invalid request or permanent application error   |
| HTTP 403           | Endpoint rejected the request                    |

SNS needs to distinguish between temporary and persistent failures.

A retry mechanism allows SNS to attempt delivery again instead of immediately abandoning the notification.

### 3.1 Retry policy components

SNS delivery policies can define several parameters:

* minDelayTarget: Minimum retry delay.

* maxDelayTarget: Maximum retry delay.

* numRetries: Number of retries in a retry phase.

* numMaxDelayRetries: Number of retries using the maximum delay.

* numMinDelayRetries: Number of retries using the minimum delay.

* numNoDelayRetries: Number of retries without an additional delay.

* backoffFunction: Algorithm used to calculate retry intervals.

These parameters control how SNS distributes retry attempts over time.

### 3.2 Retry policy example

Consider a simplified HTTP delivery policy:

```json
{
  "healthyRetryPolicy": {
    "minDelayTarget": 10,
    "maxDelayTarget": 60,
    "numRetries": 5,
    "numNoDelayRetries": 0,
    "numMinDelayRetries": 2,
    "numMaxDelayRetries": 1,
    "backoffFunction": "exponential"
  }
}
```

This illustrates how a policy can define minimum and maximum retry delays, retry counts, and an exponential backoff strategy.

Important: This is an illustrative policy configuration, not a universal retry schedule. SNS has protocol-specific delivery policy constraints, and AWS applies different delivery behavior depending on the subscription protocol.

For HTTP/S subscriptions, retry policy phases include immediate, pre-backoff, backoff, and post-backoff behavior. The healthy retry policy is distinct from the retry behavior used for other endpoint conditions.

### 3.3 The four retry phases

SNS delivery policies use four phases:

* Immediate retry

    SNS retries immediately, without waiting between attempts.

* Pre-backoff

    SNS retries using a fixed minimum delay.

* Backoff

    SNS gradually increases the delay between attempts according to the configured backoff function.

* Post-backoff

    SNS continues retrying using the maximum configured delay.

For example, a simplified retry sequence might look like this:

| Attempt          | Delay before attempt     |
| ---------------- | ------------------------ |
| Initial delivery | 0 seconds                |
| Retry 1          | 0 seconds                |
| Retry 2          | 1 second                 |
| Retry 3          | 2 seconds                |
| Retry 4          | 4 seconds                |
| Retry 5          | 8 seconds                |
| Retry 6          | 16 seconds               |
| Later attempts   | Up to configured maximum |

This is an illustration of exponential backoff, not an exact SNS-generated schedule. SNS also applies jitter, which introduces variation into retry timing to prevent synchronized retry traffic. Amazon Simple Notification Service +1

### 3.4 Which subscription protocols support custom retry policies?

This is an important AWS distinction.

HTTP/HTTPS subscriptions support custom delivery policies. For other protocols, SNS uses AWS-defined retry policies that you cannot customize in the same way.

| Endpoint    | Delivery retry behavior      |
| ----------- | ---------------------------- |
| HTTP/HTTPS  | Customizable delivery policy |
| SQS         | AWS-managed retry policy     |
| Lambda      | AWS-managed retry policy     |
| Email       | AWS-managed retry policy     |
| SMS         | AWS-managed retry policy     |
| Mobile push | AWS-managed retry policy     |

For AWS-managed SQS and Lambda endpoints, SNS can retry server-side delivery failures up to 100,015 attempts over 23 days. For SMTP, SMS, and mobile push endpoints, the documented policy is 50 attempts over six hours. Amazon Simple Notification Service +1

Don't confuse these numbers with Lambda's own execution retry configuration or SQS message retention.

### 4\. HTTP/HTTPS Endpoint Delivery Retries

HTTP/HTTPS subscriptions deserve special attention because you control the receiving application and can customize the delivery policy.

Imagine an application with this endpoint:

```text
https://api.example.com/sns/notifications
```

SNS sends a POST request whenever a matching message is published.

Now consider what happens if the application is temporarily unavailable.

### 4.1 Retryable HTTP responses

SNS treats the following as retryable HTTP delivery failures:

* HTTP 5xx server errors.

* HTTP 429 Too Many Requests.

* Request timeouts.

* Connection failures and other endpoint connectivity problems.

Other HTTP error responses, such as 400 and 403, are treated as permanent failures and are not retried under the normal HTTP delivery retry policy.

This distinction matters because retrying a permanently invalid request usually doesn't solve anything. Amazon Simple Notification Service +1

### 4.2 Example: Temporary application failure

Suppose your FastAPI application receives an SNS notification:

```python
from fastapi import FastAPI, Request, Response

app = FastAPI()

@app.post("/sns/notifications")
async def receive_notification(request: Request):
    try:
        message = await request.json()

        print("Received SNS message:", message)

        # Persist or enqueue the notification
        # before acknowledging successful receipt.

        return Response(status_code=200)

    except Exception:
        return Response(status_code=500)
```

If the application returns HTTP 500, SNS can retry delivery.

If it returns HTTP 200, SNS considers the notification successfully delivered.

For a production application, you should not simply print the message and acknowledge it. You should validate it, verify the SNS notification signature where appropriate, and persist or enqueue it before returning success.

### 4.3 Idempotency and duplicate notifications

SNS standard topics provide at-least-once delivery behavior. A subscriber can receive duplicate notifications.

For example:

* SNS sends a notification.

* Your application processes it.

* The response is lost because of a network interruption.

* SNS cannot confirm successful delivery.

* SNS retries the notification.

* Your application receives the same notification again.

This creates a potential duplicate-processing problem.

Your application should therefore implement idempotency.

A simple approach is to use the SNS `MessageId` as an identifier:

```python
message_id = message["MessageId"]

if await notification_exists(message_id):
    return Response(status_code=200)

await save_notification(
    message_id=message_id,
    payload=message
)

return Response(status_code=200)
```

The database operation that records the message ID and persists the business event should be atomic, typically using a unique constraint or transaction.

This prevents duplicate deliveries from creating duplicate business operations.

### 5\. Exponential Backoff and Retry Intervals

Exponential backoff is a common distributed-systems technique used to avoid overwhelming an unavailable service.

Instead of retrying continuously, the system increases the waiting time between attempts.

A simplified exponential backoff formula is:

D_n = \\min(D_{\\max}, D_{\\min} \\times 2^{n-1})

Where:

* : Delay before retry number .

* : Initial retry delay.

* : Maximum retry delay.

For example, with a minimum delay of 2 seconds and a maximum delay of 30 seconds:

### Why not retry every second?

Imagine an SNS topic delivering 10,000 notifications per second to an HTTP endpoint.

The endpoint becomes unavailable for 30 seconds.

If SNS retries every failed message continuously, it can generate enormous additional traffic when the endpoint is already struggling.

This creates a retry storm.

Exponential backoff helps reduce pressure on the endpoint and gives it time to recover.

### 5.1 Jitter

AWS SNS also applies jitter to delivery retries.

Jitter introduces randomness into retry intervals.

Without jitter, thousands of failed notifications could all be retried at nearly the same time.

With jitter, retries are distributed over time.

This helps prevent synchronized traffic spikes.

### 5.2 SNS retry policy versus application retry policy

These are two separate mechanisms:

| Mechanism          | Responsibility                                             |
| ------------------ | ---------------------------------------------------------- |
| SNS delivery retry | Redelivers messages that SNS cannot deliver to subscribers |
| Application retry  | Retries operations performed by your own application       |
| SQS retry behavior | Makes unprocessed queue messages available again           |
| Lambda async retry | Handles failed asynchronous Lambda executions              |

Understanding these boundaries is essential when designing distributed applications.

### 6\. Delivery Status and Failure Scenarios

SNS delivery failures can occur at different stages.

Let's classify them.

### 6.1 Publisher-side failures

These occur before SNS successfully accepts a publishing request.

Examples:

* Invalid topic ARN.

* Missing `sns:Publish` permission.

* Invalid message structure.

* Message exceeds the permitted size.

* KMS authorization failure for an encrypted topic.

These are publishing failures, not subscriber delivery failures.

The publisher should inspect the API response and handle the error appropriately.

### 6.2 Subscriber-side failures

These occur after SNS accepts the message but cannot deliver it to a subscriber.

Examples:

* HTTP endpoint unavailable.

* Lambda invocation rejected.

* SQS queue permissions prevent delivery.

* SQS queue no longer exists.

* Email delivery endpoint failure.

* Invalid or inaccessible subscriber endpoint.

SNS applies its protocol-specific delivery behavior.

### 6.3 Client-side versus server-side failures

AWS distinguishes between two important categories.

| Failure type      | Description                                               | Retry behavior                       |
| ----------------- | --------------------------------------------------------- | ------------------------------------ |
| Client-side error | Endpoint configuration, permissions, or resource problems | Generally not retried                |
| Server-side error | Temporary endpoint or service failure                     | Retried according to delivery policy |

A particularly important detail: a permission problem is not necessarily something that retrying can fix. The underlying resource policy or configuration must be corrected.

SNS can discard failed deliveries if no subscription DLQ is configured. Amazon Simple Notification Service +1

### 7\. Dead-Letter Queues (DLQs)

A dead-letter queue is one of the most important reliability mechanisms in AWS messaging.

A DLQ stores messages that cannot be successfully delivered after the applicable retry process.

In SNS, a DLQ is an Amazon SQS queue attached to an SNS subscription.

![Designing durable serverless apps with DLQs for Amazon SNS, Amazon SQS, AWS Lambda | AWS Compute Blog](https://images.openai.com/static-rsc-4/oxHaZVD-0SN1bCa6y1p25xx-e6aSz0sBjO3eXMt-PmSrrVHB9h42iAt3g4z5o8j7o_0WbQGNeDIwmMJ0zCSBnhq-KAdjmCuca7A9s4dqanE74xYSBwIQ2oc-hKDvFyxFzTkXAxJBQpbg2caMOj1MCsKbOLvtwDG9Jmk5yGtI8AbgH7o7hpC3S0aRvyMwsb1J?purpose=fullsize)

Consider this scenario:

* An application publishes an order notification.

* SNS receives the notification.

* SNS attempts to deliver it to an HTTP endpoint.

* The endpoint repeatedly returns HTTP 503.

* SNS retries according to its delivery policy.

* All delivery attempts are exhausted.

* SNS moves the undeliverable message to the subscription's DLQ.

Instead of losing the message, you retain it for investigation and recovery.

### 7.1 Why is the DLQ attached to a subscription rather than a topic?

Remember that a topic can have many subscribers.

For example:

```text
                  SNS Topic
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
        SQS A       Lambda       HTTP API
          |           |           |
          v           v           v
       DLQ A        DLQ B        DLQ C
```

Each subscription has its own delivery lifecycle.

Therefore, each subscription can have its own DLQ.

This makes it possible to identify which subscriber failed to receive a notification.

It also prevents a failure in one subscriber from affecting the others.

### 7.2 SNS DLQ versus SQS DLQ

This distinction is particularly important because both use SQS queues.

| Feature         | SNS subscription DLQ      | SQS consumer DLQ                    |
| --------------- | ------------------------- | ----------------------------------- |
| Purpose         | Failed SNS delivery       | Failed message processing           |
| Attached to     | SNS subscription          | SQS source queue                    |
| Failure example | SNS cannot deliver to SQS | Consumer repeatedly fails           |
| Trigger         | SNS delivery failure      | SQS receive count exceeds threshold |
| Storage         | SQS queue                 | SQS queue                           |

Consider this architecture:

![Message Delivery Failure : Fanout | by Ranjana Jha | Medium](https://images.openai.com/static-rsc-4/fTIcNIY5czWLNROxaP9Ub5GmT1HL1Pb0BMtezptwGWF-4V9_kLwoHziRKEFBgBytcD_FZKAZB7YZb_X1Uylmj4HntUzhLv9F03RcQW_nG7nbJ1uc2Ag0HCnnkfJERxgrUQOS_fgxr8wVYN5AuDIIveuTQdGjk_6KoLghI-1OooqloML-VJQrCNL86IAEqcWz?purpose=fullsize)

There can actually be two different DLQs in one architecture:

* An SNS DLQ captures failures when SNS cannot deliver to the SQS source queue.

* An SQS DLQ captures messages that reach the source queue but repeatedly fail during consumer processing.

These queues solve different problems.

### 7.3 Configuring an SNS DLQ

You first create an ordinary SQS queue.

Then you configure the subscription's `RedrivePolicy` attribute.

Example:

```json
{
  "deadLetterTargetArn": "arn:aws:sqs:eu-west-1:123456789012:sns-delivery-dlq"
}
```

You can configure it using AWS CLI:

```bash
aws sns set-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN" \
  --attribute-name RedrivePolicy \
  --attribute-value file://redrive-policy.json
```

The DLQ must be in the same AWS account and Region as the SNS subscription.

You must also configure the SQS queue policy to allow the SNS service to send messages to the queue. For encrypted queues, the KMS key policy must also grant the required SNS permissions. Amazon Simple Notification Service +1

### 7.4 Processing messages in the DLQ

A DLQ should not simply become a permanent storage location for failed notifications.

You need an operational strategy:

* Monitor the DLQ.

* Investigate failed messages.

* Identify the underlying problem.

* Correct the subscriber configuration or application.

* Redrive or replay messages where appropriate.

* Verify that the recovered messages are processed successfully.

For SNS DLQs, you can use the SQS message redrive capabilities and application-level replay mechanisms.

One important recommendation: use the maximum SQS message retention period of 14 days for a DLQ when your recovery requirements justify it.

Amazon Simple Notification Service +1

### 8\. Message Delivery Status Logging

Retries and DLQs help SNS recover from failures, but you also need visibility into what is happening.

This is where SNS Delivery Status Logging becomes useful.

SNS can publish delivery status information to Amazon CloudWatch Logs.

This information helps you understand:

* Whether a message was successfully delivered.

* Whether delivery failed.

* How many delivery attempts occurred.

* What response the endpoint returned.

* How long delivery took.

* Why a particular delivery failed.

### 8.1 Configuring delivery status logging

SNS uses IAM roles to obtain permission to write delivery status logs to CloudWatch Logs.

For example, when configuring logging for SQS subscriptions, you use these topic attributes:

| Attribute                    | Purpose                                    |
| ---------------------------- | ------------------------------------------ |
| SQSSuccessFeedbackRoleArn    | IAM role for successful delivery logging   |
| SQSFailureFeedbackRoleArn    | IAM role for failed delivery logging       |
| SQSSuccessFeedbackSampleRate | Percentage of successful deliveries to log |

Similar protocol-specific attributes exist for Lambda and HTTP/S.

The IAM role needs permissions such as:

```json
{
  "Effect": "Allow",
  "Action": [
    "logs:CreateLogGroup",
    "logs:CreateLogStream",
    "logs:PutLogEvents"
  ],
  "Resource": "*"
}
```

The role must also trust the SNS service principal.

### 8.2 CloudWatch log groups

SNS uses a naming convention similar to:

```text
sns/<region>/<account-id>/<topic-name>
```

For example:

```text
sns/eu-west-1/123456789012/orders-topic
```

Inside the log group, you can inspect delivery records and identify successful and failed notifications.

### 8.3 Understanding delivery logs

A delivery record contains information such as:

```json
{
  "notification": {
    "messageId": "example-message-id",
    "timestamp": "2026-11-03 10:00:00"
  },
  "delivery": {
    "statusCode": 200,
    "dwellTimeMs": 120,
    "attempts": 1
  },
  "status": "SUCCESS"
}
```

This is an illustrative structure.

The important fields include:

* `messageId`: Identifies the notification.

* `status`: Indicates delivery success or failure.

* `statusCode`: Endpoint response or delivery status code.

* `attempts`: Number of delivery attempts.

* `dwellTimeMs`: Time between publishing and handing the message to the endpoint.

Important: SNS delivery status logging does not support email endpoints. Supported topic endpoint logging includes SQS, Lambda, HTTPS, Firehose, and platform application endpoints. Amazon Simple Notification Service +3

### 8.4 CloudWatch alarms

You can use CloudWatch Logs metric filters to extract useful operational metrics.

For example:

* Failed notification deliveries.

* Delivery latency.

* Number of retry attempts.

* Failure rates over time.

You can then create CloudWatch alarms based on these metrics.

This allows your operations team to detect delivery problems before they become significant application incidents.

### 9\. Handling Unavailable Subscribers and Endpoint Failures

Let's look at several real-world failure scenarios and the appropriate responses.

### Scenario 1: HTTP endpoint temporarily unavailable

Architecture:

```text
Publisher
    |
    v
SNS Topic
    |
    v
HTTP Endpoint
    |
    X
  HTTP 503
```

What happens?

* SNS attempts delivery.

* The endpoint returns HTTP 503.

* SNS identifies a retryable server-side failure.

* SNS retries according to its delivery policy.

* If the endpoint recovers, delivery can succeed.

* If retries are exhausted, SNS sends the notification to the subscription DLQ, if configured.

### Scenario 2: SQS queue rejects delivery

Suppose SNS publishes notifications to an SQS queue, but the queue policy does not permit SNS to send messages.

The problem is an authorization/configuration failure.

You should:

* Inspect the SQS queue policy.

* Verify that the SNS topic ARN is correct.

* Allow the SNS service to call `sqs:SendMessage`.

* Check any applicable KMS key policy.

* Inspect delivery status logs.

* Investigate messages captured in the SNS subscription DLQ.

Simply increasing the retry count does not solve a permissions problem.

### Scenario 3: Lambda function is throttled

Suppose SNS attempts to invoke Lambda, but the function is throttled because its concurrency capacity is exhausted.

SNS treats this as a delivery failure and applies its AWS-managed delivery retry policy.

If Lambda accepts the invocation, however, any subsequent execution failure belongs to Lambda's asynchronous processing mechanism.

These are separate failure boundaries.

### Scenario 4: Subscriber has been deleted

Suppose someone deletes an SQS queue while its SNS subscription still exists.

SNS may retain stale subscription metadata and fail to deliver messages.

This is generally a client-side/configuration failure, not a temporary service outage.

You need to correct or remove the subscription and investigate any failed messages.

### Scenario 5: Subscriber is overloaded

Suppose your HTTP API normally processes 500 notifications per second but suddenly receives 5,000 notifications per second.

The application may start returning HTTP 429 or HTTP 503.

Potential solutions include:

* Configure an appropriate SNS HTTP/S delivery throttle.

* Increase application capacity.

* Introduce an SQS buffer.

* Scale application consumers independently.

* Use retry policies with appropriate backoff.

* Configure a subscription DLQ.

The key idea is to avoid allowing subscriber capacity problems to become system-wide failures.

### 10\. Message Durability and Reliability Considerations

Message durability refers to the ability to preserve messages so that temporary failures do not result in lost business events.

SNS uses several mechanisms to improve message durability:

* Distributed message storage.

* Automatic delivery retries.

* Dead-letter queues.

* Integration with durable destinations such as SQS.

* Monitoring and delivery status logging.

However, SNS does not provide unlimited message retention for every subscription type.

For example, if delivery attempts are exhausted and no DLQ is configured, SNS can discard the undelivered notification.

Amazon Simple Notification Service +1

### 10.1 SNS versus SQS durability

SNS and SQS have different responsibilities.

| Capability               | SNS                                       | SQS                                               |
| ------------------------ | ----------------------------------------- | ------------------------------------------------- |
| Primary purpose          | Message distribution                      | Message storage and consumption                   |
| Communication            | Push-based                                | Pull-based                                        |
| Message retention        | Delivery lifecycle and retries            | Configurable queue retention                      |
| Consumer acknowledgment  | Protocol-specific delivery acknowledgment | Consumer deletes message after processing         |
| Failed delivery handling | Subscription DLQ                          | Queue DLQ                                         |
| Independent consumers    | Multiple subscriptions                    | Multiple consumers, with queue-specific semantics |

This explains why combining SNS and SQS is such a common AWS architecture.

SNS distributes events, while SQS provides a durable buffer for independent consumers.

### 10.2 Important reliability principles

When designing production systems, keep these principles in mind:

1\. Assume duplicate delivery

Use idempotent consumers.

2\. Do not confuse delivery with processing

A successfully delivered notification can still fail later during application processing.

3\. Configure DLQs

Do not allow important notifications to disappear without a recovery mechanism.

4\. Monitor failures

Use CloudWatch metrics, delivery status logs, and alarms.

5\. Design for temporary outages

Use retry mechanisms and appropriate backoff.

6\. Keep subscribers independent

A failure in one subscriber should not prevent other subscribers from receiving the same event.

7\. Plan message recovery

Define how failed messages are inspected, corrected, and replayed.

### 11\. Designing Resilient Notification Systems

Let's put everything together.

Consider an e-commerce application that publishes order events.

Whenever a customer places an order, multiple independent services need to react:

* Inventory service updates stock.

* Payment service processes payment-related events.

* Notification service sends customer notifications.

* Analytics service records order activity.

Instead of directly connecting the order service to every other service, we can use SNS.

### 11.1 Basic architecture

![Startup Ground to Cloud: Launching Fanout Pattern to AWS Cloud - Post | Triglon Technologies | Triglon](https://images.openai.com/static-rsc-4/J2zgZDStw1viozhA_OSD18GuSc3RZj5WAYBbRgNprdJdqmI_mL_9xsZefg83sbj1cTi5KPxQeexFMA7MYl3WhHMvnI08NB2oam7ljT8aKC_OScMp3nT1XKKccFQeWsLDOju9Kljwuln5MAwrrljxBHgtjhB4dRU6ABM4jp9LSc8yYjg1X_Rk3qI5qK1dheXQ?purpose=fullsize)

Architecture:

```text
                 Order Service
                       |
                       v
                   SNS Topic
                       |
          +------------+------------+
          |            |            |
          v            v            v
       SQS Queue    SQS Queue    SQS Queue
       Inventory    Payment      Analytics
          |            |            |
          v            v            v
       Consumer     Consumer     Consumer
```

Each subscriber receives an independent copy of the notification.

If the payment service becomes unavailable, inventory and analytics can continue processing their messages.

### 11.2 Add reliability mechanisms

Now let's improve the architecture.

![Event-driven Architecture with SNS SQS Lambda Example | Darryl R. posted on the topic | LinkedIn](https://images.openai.com/static-rsc-4/7axJUFhvrJ6XE98h6JZDjDhgbg2WcNK3ZMF-c7aAvEJnV3WrDb9whZLb8EnoHqVnog45HIvL11JuLoHCOpshdqfOi9PBu0nh9suoy3cSXESo4dvGQEoP2sf85SyymiP4lS4UESzU5XCgF22on3S3DC1Yww5ramTUYXEHRR_P1iQ1NxEMGtqBs9-Jy3ByilGB?purpose=fullsize)

We introduce:

* SNS delivery retries.

* An SNS subscription DLQ for failed delivery to each SQS endpoint.

* SQS queues for durable buffering.

* SQS consumer DLQs for messages that repeatedly fail processing.

* Lambda consumers.

* CloudWatch monitoring and alarms.

Notice that there are two independent failure-handling mechanisms:

SNS delivery failure:

SNS cannot deliver the notification to the destination SQS queue.

SQS processing failure:

The notification reaches SQS, but the application repeatedly fails to process it.

These should never be treated as the same problem.

### 11.3 Why this architecture is resilient

Consider a temporary payment service outage.

* The order service publishes an event to SNS.

* SNS delivers the notification to the payment SQS queue.

* SQS stores the message.

* The payment consumer is temporarily unavailable.

* The message remains in SQS.

* The consumer recovers and processes the message.

The inventory and analytics consumers are unaffected by the payment service outage.

This is one of the biggest advantages of combining SNS with SQS.

### 12\. Production Best Practices

Here are the most important recommendations when operating SNS in production.

| Area               | Recommendation                                         |
| ------------------ | ------------------------------------------------------ |
| Delivery           | Understand protocol-specific retry behavior            |
| HTTP endpoints     | Customize delivery policies to match endpoint capacity |
| Reliability        | Configure subscription DLQs                            |
| Application design | Implement idempotency                                  |
| SQS integration    | Configure separate consumer DLQs                       |
| Monitoring         | Enable delivery status logging where supported         |
| Security           | Use least-privilege resource policies                  |
| Recovery           | Establish a DLQ inspection and replay process          |
| Scaling            | Avoid overwhelming subscribers                         |
| Architecture       | Keep subscribers independent                           |

One additional consideration: when designing systems that must never lose business-critical events, don't rely on SNS retries alone. Use durable queues, idempotent processing, and an explicit recovery strategy.

### 13\. Important Concepts to Remember

Let's consolidate the most important distinctions from this module.

| Concept                 | Meaning                                                                   |
| ----------------------- | ------------------------------------------------------------------------- |
| Delivery retry          | SNS attempts to deliver an unsuccessful notification again                |
| Delivery policy         | Controls retry behavior                                                   |
| Exponential backoff     | Increases the delay between retries                                       |
| Jitter                  | Randomizes retry timing                                                   |
| Delivery acknowledgment | Indicates that the endpoint accepted the notification                     |
| Delivery status logging | Records delivery outcomes in CloudWatch Logs                              |
| SNS DLQ                 | Stores notifications that SNS cannot deliver to a subscriber              |
| SQS consumer DLQ        | Stores messages that consumers repeatedly fail to process                 |
| Idempotency             | Prevents duplicate deliveries from creating duplicate business operations |
| Message durability      | Preserving messages against temporary failures                            |

### The most important distinction in Module 4

SNS delivery failure

SNS cannot successfully deliver a notification to its subscriber.

SNS subscription DLQ

Application processing failure

The subscriber accepted the notification, but the application subsequently failed to process it.

SQS consumer DLQ or Lambda failure handling

The consumer's own failure-handling mechanism takes responsibility.

If you understand this distinction, you understand one of the most important reliability concepts in AWS event-driven architecture.

### Official AWS documentation

For further technical reference:

* [Amazon SNS message delivery retries](https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html?utm_source=chatgpt.com)

* [Amazon SNS dead-letter queues](https://docs.aws.amazon.com/sns/latest/dg/sns-dead-letter-queues.html?utm_source=chatgpt.com)

* [Amazon SNS message delivery](https://docs.aws.amazon.com/sns/latest/dg/message-delivery.html?utm_source=chatgpt.com)

* [Amazon SNS message delivery status](https://docs.aws.amazon.com/sns/latest/dg/sns-topic-attributes.html?utm_source=chatgpt.com)

* [Configuring delivery status logging](https://docs.aws.amazon.com/sns/latest/dg/topics-attrib.html?utm_source=chatgpt.com)

Module 4 complete. The next module is Module 5 — SNS Security, IAM, Encryption, and Access Control, where we'll explore topic policies, cross-account permissions, KMS encryption, and private SNS access.
