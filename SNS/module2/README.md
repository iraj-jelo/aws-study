### Module 2 — Topics, Subscriptions, Publishing, and Message Management

Amazon SNS · Core Operations and Message Management

In Module 1, we learned that Amazon SNS is a managed publish-subscribe messaging service. It allows publishers to send messages to a topic, which distributes those messages to its subscribers.

In this module, we'll move from architecture to actual SNS operations. We'll learn how to create topics, configure subscriptions, publish messages, manage message attributes, and understand how SNS delivers messages to different endpoints.

We'll use three main interfaces throughout this module:

* AWS CLI: Managing SNS resources using Bash.

* Python Boto3: Interacting with SNS programmatically.

* Pulumi (Python): Defining and managing SNS infrastructure as code.

### 1\. Creating and Configuring SNS Topics

### 1.1 What is an SNS topic?

An SNS topic is a logical communication channel that publishers use to send messages to subscribers.

Think of a topic as a distribution point.

For example, imagine an e-commerce application that needs to notify different services whenever a customer places an order.

The application publishes an event:

```json
{
  "event_type": "OrderCreated",
  "order_id": "ORD-1001",
  "customer_id": "CUST-501",
  "total": 149.99
}
```

Instead of communicating directly with every service, the application publishes the event to an SNS topic.

![Creating an SNS (Simple Notification Service) using the AWS Command Line Interface (CLI) | by Kunalmathur | Medium](https://images.openai.com/static-rsc-4/y-pqHOlZsjrD6NzwybiPdi80_oDQhZCdLPNR8ySECz7IVkEAN4ItoAp3BppI6_zNVDz8Y9xOba38bOafpK7poypnrRkm8FQ4rOl4NOhWqChnU8GwWcDHtqpTK534n48yF3S6Z1K6kf-vnlxWTIuOpPO3jkdEuwxzkORfQrGyGcSKTcq5ULJOVaoRamuaPf7M?purpose=fullsize)

The topic distributes the message to its subscriptions.

For example:

* An SQS queue receives the order event for inventory processing.

* Another SQS queue receives it for payment processing.

* A Lambda function receives it for sending an email notification.

* An HTTPS endpoint receives it for updating an external system.

The publisher doesn't need to know how these subscribers work or where they are located.

This is one of the main benefits of SNS: loose coupling between application components.

### 1.2 Creating an SNS topic using AWS CLI

Let's create a Standard topic.

```bash
aws sns create-topic \
    --name order-events \
    --region eu-west-1
```

Example response:

```json
{
    "TopicArn": "arn:aws:sns:eu-west-1:123456789012:order-events"
}
```

The Topic ARN uniquely identifies the topic.

Its structure is:

```text
arn:aws:sns:region:account-id:topic-name
```

Let's save it in a Bash variable:

```bash
TOPIC_ARN="arn:aws:sns:eu-west-1:123456789012:order-events"
```

You can retrieve topic attributes using:

```bash
aws sns get-topic-attributes \
    --topic-arn "$TOPIC_ARN"
```

The response includes configuration information such as:

* Topic ARN.

* Display name.

* Subscription count.

* Owner account.

* FIFO configuration.

* Encryption configuration.

* Access policy.

### 1.3 Standard and FIFO topic creation

SNS supports two main topic types.

Standard topic:

```bash
aws sns create-topic \
    --name order-events
```

FIFO topic:

```bash
aws sns create-topic \
    --name order-events.fifo \
    --attributes FifoTopic=true
```

FIFO topic names must end with `.fifo`.

A FIFO topic provides ordering and deduplication capabilities and is designed to work with FIFO SQS queues.

We'll examine FIFO topics in detail in Module 3.

### 1.4 Configuring topic attributes

SNS topics have configurable attributes that control their behavior.

For example, you can configure a display name:

```bash
aws sns set-topic-attributes \
    --topic-arn "$TOPIC_ARN" \
    --attribute-name DisplayName \
    --attribute-value "Order Events"
```

You can also configure server-side encryption using AWS KMS:

```bash
aws sns set-topic-attributes \
    --topic-arn "$TOPIC_ARN" \
    --attribute-name KmsMasterKeyId \
    --attribute-value alias/aws/sns
```

This enables encryption at rest using the AWS-managed SNS KMS key.

We'll explore encryption and permissions in Module 5.

### 1.5 Managing topics with Pulumi

For infrastructure that needs to be reproducible, Pulumi is preferable to manually creating resources through the CLI.

Example using Pulumi Python:

```python
import pulumi
import pulumi_aws as aws

order_topic = aws.sns.Topic(
    "order-events",
    name="order-events",
    display_name="Order Events",
)

pulumi.export("topic_arn", order_topic.arn)
```

Pulumi manages the topic as infrastructure.

You can use:

```bash
pulumi preview
pulumi up
```

Pulumi also tracks the resource in its state, allowing you to manage configuration changes over time.

Important distinction: AWS CLI is useful for direct operations and troubleshooting, whereas Pulumi provides declarative infrastructure management.

### 2\. Managing Topics Using AWS CLI and Bash

Once a topic exists, you'll frequently need to inspect, modify, list, and delete topics.

### 2.1 Listing topics

```bash
aws sns list-topics \
    --region eu-west-1
```

This returns the topics available in your AWS account and selected region.

To retrieve only the topic ARNs using the AWS CLI query language:

```bash
aws sns list-topics \
    --query 'Topics[*].TopicArn' \
    --output table
```

### 2.2 Updating topic configuration

You can modify supported topic attributes without recreating the topic.

For example:

```bash
aws sns set-topic-attributes \
    --topic-arn "$TOPIC_ARN" \
    --attribute-name DisplayName \
    --attribute-value "E-Commerce Order Notifications"
```

You can inspect an individual attribute:

```bash
aws sns get-topic-attributes \
    --topic-arn "$TOPIC_ARN" \
    --query 'Attributes.DisplayName' \
    --output text
```

### 2.3 Deleting a topic

```bash
aws sns delete-topic \
    --topic-arn "$TOPIC_ARN"
```

Deleting a topic removes the topic and its subscriptions.

Therefore, topic deletion should be treated as a destructive infrastructure operation.

### 3\. Creating and Managing Subscriptions

### 3.1 What is an SNS subscription?

A subscription connects an SNS topic to an endpoint.

The topic represents the communication channel, while the subscription defines where messages should be delivered.

For example:

![Blogs | Mastering AWS SNS: Cloud-Based Messaging Made Simple](https://images.openai.com/static-rsc-4/X6Cz4sJLRCQVFYM4y4I_dUiOH06BaMjP_04UaLSogSAXYUgr2e1_g74cstLEUi3cNLiQ-hiQ2xcKllyUK4N-QxiCnqUMWShpFWUBc_5jzZdcyGA0MjvQ7j1fnXlem8ePCP7dTFJ832MHgBZYdfTS6DldTl1-3NqdNdJPo05bmU_kYlw3DGAd757Rec45pZZn?purpose=fullsize)

An SNS topic can have multiple subscriptions.

Each subscription has:

* A topic ARN.

* A protocol.

* An endpoint.

* A subscription ARN.

* Optional subscription attributes.

* A confirmation status, where applicable.

Let's examine a practical example.

Suppose we have an `order-events` topic with three subscribers:

| Protocol | Endpoint              | Purpose                        |
| -------- | --------------------- | ------------------------------ |
| SQS      | Inventory queue       | Update inventory               |
| Lambda   | Notification function | Send customer notifications    |
| HTTPS    | External API          | Notify an external application |

The publisher sends one message to the topic. SNS distributes it to the configured subscriptions.

### 3.2 Creating an SQS subscription

First, assume we have an existing SQS queue.

Retrieve its ARN:

```bash
QUEUE_URL=$(aws sqs get-queue-url \
    --queue-name inventory-queue \
    --query QueueUrl \
    --output text)

QUEUE_ARN=$(aws sqs get-queue-attributes \
    --queue-url "$QUEUE_URL" \
    --attribute-names QueueArn \
    --query 'Attributes.QueueArn' \
    --output text)
```

Create the SNS subscription:

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol sqs \
    --notification-endpoint "$QUEUE_ARN"
```

The result is a subscription ARN.

Important: An SNS topic policy and an SQS queue policy have different responsibilities.

The queue must allow the SNS service to call `sqs:SendMessage`.

A simplified queue policy looks like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
      "Action": "sqs:SendMessage",
      "Resource": "QUEUE_ARN",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "TOPIC_ARN"
        }
      }
    }
  ]
}
```

Replace `QUEUE_ARN` and `TOPIC_ARN` with their actual values.

This policy allows messages from the specified SNS topic rather than allowing arbitrary SNS topics to send messages to the queue.

### 3.3 Creating a Lambda subscription

Assume you already have a Lambda function named `order-notification`.

Retrieve its ARN:

```bash
FUNCTION_ARN=$(aws lambda get-function \
    --function-name order-notification \
    --query 'Configuration.FunctionArn' \
    --output text)
```

Allow SNS to invoke the function:

```bash
aws lambda add-permission \
    --function-name order-notification \
    --statement-id AllowSNSInvoke \
    --action lambda:InvokeFunction \
    --principal sns.amazonaws.com \
    --source-arn "$TOPIC_ARN"
```

Create the subscription:

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol lambda \
    --notification-endpoint "$FUNCTION_ARN"
```

Now, when SNS publishes a message to the topic, it can invoke the Lambda function.

The Lambda function receives an SNS event containing the message and associated metadata.

### 3.4 Listing subscriptions

List all subscriptions in your account:

```bash
aws sns list-subscriptions
```

List subscriptions for a specific topic:

```bash
aws sns list-subscriptions-by-topic \
    --topic-arn "$TOPIC_ARN"
```

### 3.5 Unsubscribing

To remove a subscription:

```bash
aws sns unsubscribe \
    --subscription-arn "$SUBSCRIPTION_ARN"
```

This removes the relationship between the topic and the endpoint.

It does not delete the topic or the endpoint itself.

### 4\. Subscription Protocols and Endpoint Types

SNS supports several subscription protocols. The protocol determines how SNS delivers messages to the endpoint.

Understanding these protocols is important because different endpoint types have different delivery mechanisms, configuration requirements, and limitations.

### 4.1 HTTP and HTTPS

SNS can deliver messages to web applications through HTTP or HTTPS endpoints.

For example:

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol https \
    --notification-endpoint https://api.example.com/sns/events
```

When a message is published, SNS sends an HTTP POST request to the endpoint.

The request contains a JSON notification envelope.

An example:

```json
{
  "Type": "Notification",
  "MessageId": "abc-123",
  "TopicArn": "arn:aws:sns:eu-west-1:123456789012:order-events",
  "Subject": "New Order",
  "Message": "{\"order_id\":\"ORD-1001\"}",
  "Timestamp": "2026-11-03T12:00:00.000Z",
  "SignatureVersion": "1",
  "Signature": "...",
  "SigningCertURL": "...",
  "UnsubscribeURL": "..."
}
```

The endpoint should:

* Receive the HTTP POST request.

* Validate the SNS message signature.

* Process the message.

* Return a successful HTTP response.

SNS uses the response to determine whether delivery succeeded.

HTTPS is generally preferable because it protects message data in transit.

### 4.2 Email

SNS can send notifications to email addresses.

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol email \
    --notification-endpoint user@example.com
```

The recipient receives a subscription confirmation email.

After confirmation, SNS can send notifications to that address.

Email is useful for:

* System alerts.

* Infrastructure notifications.

* Operational warnings.

* Application notifications.

It is not intended to replace a full email delivery platform.

### 4.3 Email-JSON

The `email-json` protocol delivers notifications using a JSON-formatted email representation.

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol email-json \
    --notification-endpoint user@example.com
```

Unlike ordinary email delivery, the message content is structured as JSON.

This is useful when email-processing systems need structured notification data.

### 4.4 SMS

SNS supports SMS delivery to mobile phone numbers.

```bash
aws sns publish \
    --topic-arn "$TOPIC_ARN" \
    --message "Your order has been shipped."
```

For direct SMS delivery, you can specify a phone number instead of a topic ARN:

```bash
aws sns publish \
    --phone-number "+33612345678" \
    --message "Your order has been shipped."
```

SNS SMS is useful for:

* One-time passwords.

* Delivery notifications.

* Critical alerts.

* Customer notifications.

SMS delivery has additional considerations, including country restrictions, origination identities, spending limits, and per-message pricing.

Also, SMS is not a normal topic subscription protocol with the same confirmation process as email. Direct SMS publishing is a separate delivery path.

### 4.5 SQS

SQS is particularly important when integrating SNS with asynchronous processing systems.

The architecture is:

![Mastering AWS SQS + SNS: Scalable, Event-Driven Architectures with Spring Boot ☁️ | by Anderson Kuntz Meurer | Medium](https://images.openai.com/static-rsc-4/7mQfQS7xiag3Zsh8SRnum8GH5f1eXJl1mNJKgElPQsKmPfuz0fZRNPfZs6msw-diMlmGvwSOR386qIWFDCCoxWn1K6BrysdGrGiEkTw-vFXLD9P8oCnPfwmaR6KcAvwJNA803rs0SmyrjUV7TjNbaFc_j8Fy66n3lmPiHtD2kMrSnEx8v1y9HBCROlr3KenV?purpose=fullsize)

SNS pushes messages into the SQS queue.

The SQS consumer then pulls and processes them independently.

This provides several advantages:

* Buffering during traffic spikes.

* Independent consumer scaling.

* Message retention.

* Retry handling through queue visibility behavior.

* Dead-letter queue support at the queue level.

Unlike direct Lambda delivery, SNS-to-SQS delivery does not require the application to process messages immediately.

### 4.6 Lambda

SNS can directly invoke Lambda functions.

The architecture:

![Simplify Your Pub/Sub Messaging with Amazon SNS Message Filtering | AWS Compute Blog](https://images.openai.com/static-rsc-4/577Ld5IyJxSgT0uKERXHIxWSgHBjWHvdGqF61ftHCh-U6YyqXdlADkhiRiGAhSR5dM_CxUVRiaRjXO7KBodN9YWp3HK6Jhb9uQAeoeAMev98rjrOvbRUOZBLiRfj4Tlerm5293jfkYqE1A9HsRLm1_P-PVpyhaC-x20UWGvBopZoOzWFO3lfHNmAP2ZIFJ6a?purpose=fullsize)

This is useful when a published event should immediately trigger application logic.

For example:

* A customer places an order.

* SNS receives an `OrderCreated` event.

* SNS invokes a Lambda function.

* Lambda sends a notification.

Remember that SNS-to-Lambda invocation and Lambda's own asynchronous event processing have different retry and failure-handling behavior. We'll revisit this in Module 4.

### 4.7 Platform applications

SNS also supports mobile push notifications through platform applications.

A platform application connects SNS to a push notification service such as:

* Apple Push Notification service (APNs).

* Firebase Cloud Messaging (FCM).

* Other supported mobile push services.

The general architecture is:

![AWS Certified Solutions Architect Professional](https://images.openai.com/static-rsc-4/FeFhSd5l3jhY7ASD56QYCB70Az2UwNUH0FN5JkZ0ms5BYpIWOZzl0oeQbscytyv0CbPlzL7Tt-W-fYwsHJEOSmo5FFSXeXXA76pCU2IqTOxlQHdRRYn-WsB_-wcOGCUqmflKy-RVnqMUuyddu6ioWtS7sIqaIe2cml55q8Ehk8Ndz4QYjb3VyLUB42N2iliA?purpose=fullsize)

The application registers a mobile device with its platform push provider and obtains a device token.

SNS uses that token to create a platform endpoint.

The platform endpoint becomes the subscription target for the topic.

For example, a mobile shopping application can receive notifications about order status updates.

### 5\. Publishing Messages Using AWS CLI and Python Boto3

Now let's examine how publishers send messages to SNS topics.

### 5.1 Publishing with AWS CLI

The basic command is:

```bash
aws sns publish \
    --topic-arn "$TOPIC_ARN" \
    --message "A new order has been created."
```

Example response:

```json
{
    "MessageId": "12345678-1234-1234-1234-123456789012"
}
```

The `MessageId` identifies the published message.

It does not mean that every subscriber has successfully processed the message.

SNS accepting a publish request and subscribers successfully processing the resulting notification are separate events.

### 5.2 Publishing JSON messages

Applications often publish structured JSON messages.

For example:

```json
{
  "event_type": "OrderCreated",
  "order_id": "ORD-1001",
  "customer_id": "CUST-501",
  "total": 149.99,
  "currency": "EUR"
}
```

You can publish it using:

```bash
aws sns publish \
    --topic-arn "$TOPIC_ARN" \
    --message '{
      "event_type": "OrderCreated",
      "order_id": "ORD-1001",
      "customer_id": "CUST-501",
      "total": 149.99,
      "currency": "EUR"
    }'
```

The message body is a string, even when its contents represent JSON.

SNS doesn't automatically interpret arbitrary JSON as a domain event schema. Your subscribers are responsible for understanding and validating the payload.

### 5.3 Publishing with Python Boto3

Let's use the SNS client.

```python
import boto3
import json

sns = boto3.client(
    "sns",
    region_name="eu-west-1"
)

topic_arn = (
    "arn:aws:sns:eu-west-1:"
    "123456789012:order-events"
)

message = {
    "event_type": "OrderCreated",
    "order_id": "ORD-1001",
    "customer_id": "CUST-501",
    "total": 149.99,
    "currency": "EUR"
}

response = sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps(message)
)

print("Message ID:", response["MessageId"])
```

The important operation is:

```python
sns.publish()
```

It sends a message to the topic.

Boto3 returns the message ID when SNS successfully accepts the publish request.

It does not wait for all subscribers to complete their processing.

### 5.4 Publishing with a subject

For protocols that support it, SNS messages can have a subject.

```python
response = sns.publish(
    TopicArn=topic_arn,
    Subject="New Order Created",
    Message="Order ORD-1001 has been created."
)
```

The subject is commonly useful for email notifications.

It is separate from the message body and has a maximum length of 100 characters.

### 6\. Message Bodies, Attributes, and Metadata

SNS messages contain more than just a message body. Publishers can attach additional information that helps subscribers understand, categorize, and process notifications.

Let's distinguish the main components.

### 6.1 Message body

The message body contains the actual application data.

For example:

```json
{
  "event_type": "OrderCreated",
  "order_id": "ORD-1001",
  "customer_id": "CUST-501",
  "total": 149.99
}
```

This is the information that subscribers ultimately need.

SNS transports the message but generally doesn't interpret the business meaning of its contents.

### 6.2 Message attributes

Message attributes are additional structured metadata attached to a message.

For example, consider an order event:

Message body:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "CUST-501",
  "total": 149.99
}
```

Message attributes:

```text
event_type = OrderCreated
environment = production
priority = high
```

The difference is important:

* The message body contains the actual business event.

* Message attributes provide additional information about that event.

Attributes can be used by subscription filter policies to determine which subscribers receive a message. We'll explore filtering in Module 3.

### 6.3 Supported message attribute data types

SNS supports three principal message attribute data types:

| Data type | Purpose        | Example                |
| --------- | -------------- | ---------------------- |
| String    | Text values    | production             |
| Number    | Numeric values | 100                    |
| Binary    | Binary data    | Encoded binary payload |

SNS also supports `String.Array`, a string-array subtype.

For example:

```text
event_type = OrderCreated
priority = 5
tags = ["orders", "payments"]
```

### 6.4 Publishing message attributes using Boto3

```python
import boto3
import json

sns = boto3.client("sns", region_name="eu-west-1")

message = {
    "order_id": "ORD-1001",
    "customer_id": "CUST-501",
    "total": 149.99
}

response = sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps(message),
    MessageAttributes={
        "event_type": {
            "DataType": "String",
            "StringValue": "OrderCreated"
        },
        "environment": {
            "DataType": "String",
            "StringValue": "production"
        },
        "priority": {
            "DataType": "Number",
            "StringValue": "5"
        }
    }
)

print(response["MessageId"])
```

Notice that numeric attribute values are passed as strings through `StringValue`, while their declared data type is `Number`.

### 6.5 Publishing attributes using AWS CLI

You can also use the CLI:

```bash
aws sns publish \
    --topic-arn "$TOPIC_ARN" \
    --message "New order created" \
    --message-attributes '{
      "event_type": {
        "DataType": "String",
        "StringValue": "OrderCreated"
      },
      "priority": {
        "DataType": "Number",
        "StringValue": "5"
      }
    }'
```

Important: Message attributes are not the same as subscription attributes.

| Message attributes                | Subscription attributes                   |
| --------------------------------- | ----------------------------------------- |
| Attached to individual messages   | Attached to subscriptions                 |
| Published by the publisher        | Configured on the subscription            |
| Can be used for message filtering | Configure delivery behavior and filtering |
| Vary between messages             | Persist as subscription configuration     |

### 7\. Subject Fields and Message Structure

SNS provides two important concepts for organizing notification content: the subject and the message structure.

### 7.1 Subject field

The subject is an optional short text field associated with a notification.

For example:

```python
sns.publish(
    TopicArn=topic_arn,
    Subject="Payment Successful",
    Message="Payment for order ORD-1001 was completed."
)
```

The subject is particularly useful for email notifications because it becomes the email subject line.

Important characteristics:

* Maximum length: 100 characters.

* Optional.

* Not a replacement for the message body.

* Not supported by every delivery protocol in the same way.

For example, an SQS subscriber should not depend on the subject being included in its message body.

### 7.2 Message structure

SNS normally sends a notification envelope to subscribers.

For example, an HTTP subscriber receives a JSON structure containing:

```json
{
  "Type": "Notification",
  "MessageId": "abc-123",
  "TopicArn": "...",
  "Subject": "Payment Successful",
  "Message": "Payment completed.",
  "Timestamp": "...",
  "Signature": "..."
}
```

This is the default notification structure.

However, SNS also supports protocol-specific message formatting through the `MessageStructure` parameter.

### 7.3 Protocol-specific messages

Suppose you want to send different content to different subscriber types.

You can use a JSON message structure:

```json
{
  "default": "Your order has been processed.",
  "email": "Your order ORD-1001 has been processed successfully.",
  "sqs": "{\"event\":\"OrderCreated\",\"order_id\":\"ORD-1001\"}"
}
```

Publish it using Boto3:

```python
import json

messages = {
    "default": "Your order has been processed.",
    "email": (
        "Your order ORD-1001 has "
        "been processed successfully."
    ),
    "sqs": json.dumps({
        "event": "OrderCreated",
        "order_id": "ORD-1001"
    })
}

response = sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps(messages),
    MessageStructure="json"
)
```

SNS selects the appropriate message based on the subscriber's protocol.

The `default` key is required.

Supported protocol-specific keys include `email`, `email-json`, `http`, `https`, `sqs`, `lambda`, and `application`.

This is useful when different subscribers need different representations of the same event.

Architectural recommendation: For event-driven microservices, keeping a consistent JSON event schema across subscribers is usually easier to maintain than creating many protocol-specific message representations.

### 8\. Message Size Limits and Payload Considerations

SNS has message size limits that affect application architecture.

### 8.1 Maximum message size

The maximum SNS message size is:

256 KB

This is the general message-size limit for SNS, including message attributes.

The size is measured in bytes, not characters.

For example:

```json
{
  "event": "OrderCreated",
  "order_id": "ORD-1001"
}
```

This is a small message and is comfortably within the limit.

However, consider an application that tries to publish an entire document, image, or large API response.

Large payloads can exceed the SNS message limit.

### 8.2 Large payload architectural pattern

Instead of publishing large data directly, store it in object storage and publish a reference.

For example:

![How to send large SQS/SNS messages with Node.js | by Marian Zagoruiko | Aspecto | Medium](https://images.openai.com/static-rsc-4/zr0bMlKEgtytLKZLAnH6BFL1qc4vEIscY3zAA1IHs0apH9Jui08kCxviCCn72ttEs93qi4Y34uIA6LTWQd8SJC_o-G3afMDS0dk1BnbXoNYDiLM7kUY0tFKophnvhBJujEjmgXHOm6XQwOdaL0BGslMnQGK7qbHHy6JnfWeAnDSZ7W0BC4jCDqgt72ES3OiU?purpose=fullsize)

The workflow:

* The application uploads a large file to Amazon S3.

* S3 stores the file.

* The application publishes an SNS notification.

* The notification contains the S3 bucket and object key.

* Subscribers retrieve the file from S3 when necessary.

Example message:

```json
{
  "event_type": "DocumentUploaded",
  "bucket": "application-documents",
  "object_key": "orders/ORD-1001/invoice.pdf"
}
```

This pattern is commonly called the claim-check pattern.

It provides several benefits:

* Smaller notification messages.

* Reduced messaging overhead.

* Better handling of large files.

* Independent storage and processing.

* Easier message distribution.

The subscriber must have appropriate S3 permissions to retrieve the referenced object.

### 8.3 SMS size considerations

SMS has different constraints from ordinary SNS messages.

SMS messages are billed according to the number of message segments, and segment size depends on the encoding used.

For example:

* GSM-7 encoding generally supports 160 characters in a single SMS segment.

* Unicode encoding, such as messages containing many non-GSM characters, generally supports 70 characters per segment.

Long messages may be split into multiple segments, increasing costs.

### 8.4 Practical payload recommendations

For production applications:

* Keep messages small and focused.

* Use JSON for structured business events.

* Include stable identifiers such as `order_id`.

* Avoid embedding large files.

* Use S3 for large payloads.

* Define versioned event schemas.

* Avoid publishing sensitive information unnecessarily.

* Make subscribers tolerant of additional optional fields.

### 9\. Raw Message Delivery

Raw message delivery changes the format SNS uses when delivering messages to certain subscribers.

By default, SNS wraps messages inside a notification envelope.

Let's compare both approaches.

### 9.1 Default message delivery

Suppose the publisher sends:

```json
{
  "order_id": "ORD-1001",
  "event": "OrderCreated"
}
```

An SQS subscriber normally receives an SNS notification envelope.

The SQS message body contains something similar to:

```json
{
  "Type": "Notification",
  "MessageId": "abc-123",
  "TopicArn": "...",
  "Message": "{\"order_id\":\"ORD-1001\",\"event\":\"OrderCreated\"}",
  "Timestamp": "..."
}
```

The actual application payload is inside the `Message` field.

Consequently, the consumer must extract the inner message before processing it.

### 9.2 Raw message delivery enabled

With raw message delivery enabled, SNS removes its notification envelope for supported endpoints.

For an SQS subscriber, the queue receives the original message body directly:

```json
{
  "order_id": "ORD-1001",
  "event": "OrderCreated"
}
```

This simplifies consumer implementation because it doesn't need to unwrap the SNS notification.

### 9.3 Enabling raw message delivery

You can enable it when creating a subscription:

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol sqs \
    --notification-endpoint "$QUEUE_ARN" \
    --attributes '{"RawMessageDelivery":"true"}'
```

Or update an existing subscription:

```bash
aws sns set-subscription-attributes \
    --subscription-arn "$SUBSCRIPTION_ARN" \
    --attribute-name RawMessageDelivery \
    --attribute-value true
```

You can inspect the configuration:

```bash
aws sns get-subscription-attributes \
    --subscription-arn "$SUBSCRIPTION_ARN"
```

### 9.4 Important raw delivery considerations

Raw delivery is supported for SQS and HTTP/S subscriptions.

For SQS, SNS message attributes can also be passed through, subject to the raw-delivery limit of 10 message attributes.

For HTTP/S, raw delivery removes the JSON notification envelope.

However, raw delivery also removes useful SNS metadata from the message body, such as the SNS message ID and topic ARN.

This creates an architectural trade-off:

| Default delivery               | Raw delivery                        |
| ------------------------------ | ----------------------------------- |
| SNS notification envelope      | Original message body               |
| Includes SNS metadata          | Removes envelope metadata           |
| Consumer must unwrap message   | Consumer processes original payload |
| Useful for SNS-aware consumers | Useful for simple message consumers |

My recommendation: Use raw delivery when the subscriber only needs the application payload. Use default delivery when the consumer benefits from SNS notification metadata.

### 10\. Subscription Confirmation and Endpoint Management

Some SNS subscriptions require endpoint confirmation before SNS starts delivering notifications.

This is particularly important for email and HTTP/S subscriptions.

### 10.1 Why confirmation is necessary

Imagine someone creates a subscription to:

```text
user@example.com
```

Without confirmation, another person could subscribe someone else's email address without their permission.

SNS uses a confirmation mechanism to verify that the endpoint owner agrees to receive notifications.

### 10.2 Email subscription confirmation

When an email subscription is created:

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol email \
    --notification-endpoint user@example.com
```

SNS sends a confirmation email.

The recipient must open the email and click the confirmation link.

Before confirmation, the subscription is pending.

After confirmation, the subscription becomes active.

### 10.3 HTTP/S subscription confirmation

HTTP/S subscriptions use a different mechanism.

When SNS creates the subscription, it sends an HTTP POST request to the endpoint containing a `SubscriptionConfirmation` message.

Example:

```json
{
  "Type": "SubscriptionConfirmation",
  "MessageId": "abc-123",
  "Token": "...",
  "TopicArn": "...",
  "Message": "You have chosen to subscribe...",
  "SubscribeURL": "https://sns..."
}
```

The endpoint must confirm the subscription.

It can do so by visiting the supplied `SubscribeURL` or by calling the SNS `ConfirmSubscription` API with the appropriate topic ARN and token.

For security, the endpoint should validate the SNS signature and expected topic before trusting or following confirmation information.

### 10.4 Confirming a subscription using Boto3

```python
import boto3

sns = boto3.client("sns", region_name="eu-west-1")

response = sns.confirm_subscription(
    TopicArn=topic_arn,
    Token=confirmation_token
)

print(response["SubscriptionArn"])
```

The confirmation token is obtained from the confirmation notification.

### 10.5 Pending confirmation versus confirmed subscriptions

You can inspect subscriptions:

```bash
aws sns list-subscriptions-by-topic \
    --topic-arn "$TOPIC_ARN"
```

A subscription that requires confirmation may have:

```text
PendingConfirmation
```

After successful confirmation, SNS returns a subscription ARN.

Some subscription types, such as SQS and Lambda, are normally confirmed automatically during subscription creation when the required permissions are available.

### 10.6 Managing endpoints

For HTTP/S subscriptions, endpoint management includes:

* Ensuring the endpoint is publicly reachable by SNS.

* Handling confirmation requests.

* Processing notification POST requests.

* Returning appropriate HTTP status codes.

* Validating SNS signatures.

* Handling duplicate notifications safely.

* Monitoring endpoint availability.

For mobile push, SNS platform endpoints have additional lifecycle management requirements, particularly when device tokens become invalid or change.

### 11\. Publishing Messages to Multiple Subscribers

One of the most important features of SNS is its ability to distribute a single published message to multiple subscribers.

This is called fanout messaging.

### 11.1 Understanding SNS fanout

Imagine an e-commerce application with the following services:

* Inventory service.

* Payment service.

* Notification service.

* Analytics service.

When a customer places an order, the application publishes an `OrderCreated` event.

Instead of sending four separate requests, the application publishes one message to SNS.

![Startup Ground to Cloud: Launching Fanout Pattern to AWS Cloud - Post | Triglon Technologies | Triglon](https://images.openai.com/static-rsc-4/J2zgZDStw1viozhA_OSD18GuSc3RZj5WAYBbRgNprdJdqmI_mL_9xsZefg83sbj1cTi5KPxQeexFMA7MYl3WhHMvnI08NB2oam7ljT8aKC_OScMp3nT1XKKccFQeWsLDOju9Kljwuln5MAwrrljxBHgtjhB4dRU6ABM4jp9LSc8yYjg1X_Rk3qI5qK1dheXQ?purpose=fullsize)

SNS distributes the notification to all four subscriptions.

Each service can process the event independently.

For example:

| Subscriber          | Responsibility          |
| ------------------- | ----------------------- |
| Inventory SQS       | Reserve products        |
| Payment SQS         | Process payment         |
| Notification Lambda | Notify customer         |
| Analytics SQS       | Record order statistics |

This architecture provides several important benefits.

Loose coupling: The publisher doesn't need to know about individual subscribers.

Independent processing: Each subscriber can process the event according to its own requirements.

Scalability: Subscribers can scale independently.

Extensibility: New subscribers can be added without modifying the publisher.

### 11.2 Adding multiple subscriptions

You can create several subscriptions for the same topic:

```bash
aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol sqs \
    --notification-endpoint "$INVENTORY_QUEUE_ARN"

aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol sqs \
    --notification-endpoint "$PAYMENT_QUEUE_ARN"

aws sns subscribe \
    --topic-arn "$TOPIC_ARN" \
    --protocol lambda \
    --notification-endpoint "$NOTIFICATION_FUNCTION_ARN"
```

Now all three endpoints receive notifications published to the topic.

Remember that each endpoint must have the appropriate permissions.

### 11.3 Publishing a single message to all subscribers

The publisher doesn't need to publish separate messages for each subscriber.

```python
response = sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({
        "event_type": "OrderCreated",
        "order_id": "ORD-1001",
        "customer_id": "CUST-501",
        "total": 149.99
    })
)

print(response["MessageId"])
```

SNS distributes this message to the topic's subscriptions.

### 11.4 SNS fanout versus direct communication

Consider two architectural approaches.

Direct communication

![Microservices Communication: Synchronous and Asynchronous Explained with Beautiful Diagrams | by Ramesh Fadatare | Javarevisited | Medium](https://images.openai.com/static-rsc-4/gaa2ZveUN6wEHlMJmWHPoTxyejnkOzfVBxZf25PCxni7EIYrqGn-WVTXE1z_R0Rd4dGV7CbHxXniJgB_v12070JGOGZEEbh618839xK1uCs-OeNneNF-97-tv4pIkdVG-40_kdfvBTJADpw5BRODisg-mWSnU5NpjZV5kZxp2HxbZIAp0LynMiD4CE8LQ_uf?purpose=fullsize)

The publisher must know about multiple services and communicate with each one individually.

SNS fanout

![Asynchronous Communication Between Microservices — 02: AWS - SNS + SQS | by Syed Fawzul Azim | Medium](https://images.openai.com/static-rsc-4/CEPiH-B9Ibe78n8GuMGa_tYGUwSj3-oyzQeygnJjXWvdrvj-woE4p4jNmKTjgB8IkZ5hr_XTg7HySXkN0Fk4iO4vbJHggXe_oDKSAvg4Tp_jDG96iVF5pIqyD33tugk0rDXtBY91pkYzB0uYYw5MERfREDNHfh8mcutbwZZX96ra-YJLK31AnPT3d8sqJGmY?purpose=fullsize)

The publisher communicates with one topic, while SNS distributes notifications to subscribers.

SNS is particularly useful when multiple independent services need to react to the same business event.

### 12\. SNS Message Publishing and Delivery Lifecycle

Let's put everything together and understand what happens from the moment an application publishes a message until subscribers receive it.

### 12.1 Message lifecycle

The general lifecycle consists of these stages:

* Publisher creates a message

    An application prepares a message containing the event payload and optional message attributes.

* Publisher sends the message to SNS

    The application calls the SNS `Publish` API using the topic ARN.

* SNS accepts the request

    SNS validates the request and returns a message ID if publishing succeeds.

* SNS processes subscriptions

    SNS identifies the subscriptions associated with the topic and evaluates applicable filtering policies.

* SNS delivers notifications

    SNS attempts delivery to eligible subscribers using their configured protocols.

* Subscribers receive messages

    SQS receives messages, Lambda is invoked, and HTTP endpoints receive POST requests, for example.

* Subscribers process messages

    Each subscriber independently performs its application-specific processing.

### 12.2 Publishing success versus delivery success

This is a particularly important distinction.

Suppose an application publishes a message:

```python
response = sns.publish(
    TopicArn=topic_arn,
    Message="Order ORD-1001 created."
)
```

SNS returns:

```json
{
    "MessageId": "abc-123"
}
```

This means SNS accepted the publishing request.

It does not guarantee that:

* Every subscriber received the message.

* Every Lambda invocation succeeded.

* Every SQS consumer processed the message.

* Every external HTTP endpoint completed its work.

Publishing and subscriber processing are separate stages.

This distinction is essential when designing reliable distributed applications.

### 12.3 Different subscribers have different delivery behavior

| Subscriber  | Delivery behavior                                            |
| ----------- | ------------------------------------------------------------ |
| SQS         | SNS pushes a message into the queue                          |
| Lambda      | SNS invokes the function                                     |
| HTTP/S      | SNS sends an HTTP POST request                               |
| Email       | SNS sends an email                                           |
| SMS         | SNS delivers a text message                                  |
| Mobile push | SNS forwards notifications through the platform push service |

Each protocol has different delivery and failure-handling characteristics.

For example, when SNS delivers to SQS, the message becomes available in the queue. The consumer retrieves it later.

When SNS invokes Lambda, the function is triggered without the publisher waiting for its execution to finish.

### 12.4 Message identifiers

SNS provides a message ID for every successfully accepted publish request.

This identifier is useful for:

* Logging.

* Troubleshooting.

* Correlating publish operations.

* Investigating delivery problems.

However, don't confuse the SNS message ID with an application-level event ID.

For production systems, include your own event identifier:

```json
{
  "event_id": "evt-2026-1001",
  "event_type": "OrderCreated",
  "order_id": "ORD-1001",
  "timestamp": "2026-11-03T12:00:00Z"
}
```

This helps subscribers recognize duplicate business events and implement idempotent processing.

### 12.5 Duplicate delivery considerations

SNS Standard topics provide at-least-once delivery for supported delivery paths, meaning subscribers should be prepared for occasional duplicate notifications.

For example:

* SNS delivers an order notification.

* A consumer processes the notification.

* The consumer experiences a failure before recording successful completion.

* The notification may be delivered again.

Therefore, subscribers should implement idempotent processing.

A consumer should be able to receive the same business event more than once without accidentally charging a customer twice or reserving inventory twice.

We'll explore SNS delivery retries and failure handling in Module 4.

### 13\. Putting the Concepts Together: A Complete E-Commerce Example

Let's combine the concepts from this module into one architecture.

![Ejemplo de caso de uso de temas FIFO de Amazon SNS - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/PpWfCBDq_iHurq-CGr3sINqalW-Sw2mVl7rPaP7CMQSnJ0EtdTlR0O_5xc7aphRNGqlfycoMLTw18WamWx0wlId0W_xA_Q6OZxKaoB7p0ZA1QkUYzw3EYV49HD6TScCl5Q2iRIBQrzKFgLwSRXpm7OSrqLu_jwbJBE16teijjMzgS2zbdoaYE7AK9zd6UfIi?purpose=fullsize)

Imagine an application that publishes order events.

The architecture contains:

* An application acting as the SNS publisher.

* An SNS topic named `order-events`.

* An inventory SQS queue.

* A payment SQS queue.

* A notification Lambda function.

* An analytics SQS queue.

The application publishes:

```json
{
  "event_id": "evt-1001",
  "event_type": "OrderCreated",
  "order_id": "ORD-1001",
  "customer_id": "CUST-501",
  "total": 149.99,
  "currency": "EUR"
}
```

SNS distributes the event to all eligible subscriptions.

Each service handles its own responsibility:

* Inventory processes product reservations.

* Payment processes the transaction.

* Notification sends a customer notification.

* Analytics records the event.

The publisher doesn't need to know how any of these services work.

This architecture combines:

* SNS publish-subscribe messaging.

* Multiple subscriptions.

* Message publishing.

* JSON payloads.

* Message attributes.

* Fanout distribution.

* SQS asynchronous processing.

* Lambda event-driven execution.

### 14\. Module 2 — Important Concepts to Remember

| Concept                   | Key takeaway                                           |
| ------------------------- | ------------------------------------------------------ |
| Topic                     | Logical communication channel                          |
| Subscription              | Connection between a topic and an endpoint             |
| Publisher                 | Application that sends messages                        |
| Endpoint                  | Destination that receives notifications                |
| Topic ARN                 | Unique identifier of an SNS topic                      |
| Message body              | Actual application payload                             |
| Message attributes        | Additional structured message metadata                 |
| Subject                   | Optional notification subject                          |
| Message structure         | Default or protocol-specific content                   |
| Raw delivery              | Delivers the original payload without the SNS envelope |
| Subscription confirmation | Verifies endpoint ownership or consent                 |
| Fanout                    | Distributes one message to multiple subscribers        |
| Message ID                | Identifies a successfully accepted publish request     |

### What comes next?

In Module 3, we'll examine one of SNS's most useful capabilities: message filtering and FIFO messaging.

We'll cover:

* Subscription filter policies.

* Attribute-based filtering.

* Message-body-based filtering.

* Filter policy operators.

* Standard versus FIFO topics.

* Message groups and ordering.

* Deduplication mechanisms.

* Content-based deduplication.

* SNS FIFO and SQS FIFO integration.

These concepts will help you build more selective messaging architectures where subscribers receive only the events relevant to their responsibilities.
