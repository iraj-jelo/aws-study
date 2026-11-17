### Module 3 — Message Filtering, FIFO Topics, Ordering, and Deduplication

Amazon SNS · Intermediate to Advanced

In this module, we'll explore two important capabilities of Amazon SNS:

* Message filtering: Control which messages are delivered to which subscribers.

* FIFO messaging: Preserve message ordering and prevent duplicate message publishing within SNS FIFO topics.

These capabilities are particularly important when building event-driven microservices, notification systems, and distributed applications.

We'll use AWS CLI, Bash, Python Boto3, and Pulumi Python where appropriate.

### 1\. SNS Message Filtering Architecture

Imagine you have an e-commerce application that publishes events whenever an order is created.

Different services need to receive different types of events:

* Payment Service needs payment-related events.

* Shipping Service needs orders that have been paid.

* Notification Service needs events related to order confirmation.

* Analytics Service needs all order events.

Without filtering, every subscriber might receive every published message and would need to inspect it, decide whether it is relevant, and discard unwanted messages.

SNS message filtering solves this problem.

Instead of delivering every message to every subscriber, SNS evaluates each subscription's filter policy and delivers only matching messages.

![Amazon SNS message filtering for FIFO topics - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/45pAky-E8RjzDmLG0QZ_cP2ussw8r9p-a3ZOroQAZ_Zjm0sfNe4gOJ3vCLjnRk48pvVRTGSvwkZNYBT39xZNti9NpnjuLyv1pcjM8CnWgXyTi-FdJtq248xLfrgX9bbaWmftZy5QEPQpis8yNBPd67VfCjY3LkQqciyyiIm_nLNkZA35Kv5-FV_BXtmlV6ae?purpose=fullsize)

### How it works

* A publisher sends a message to an SNS topic.

* SNS receives the message.

* SNS evaluates the filter policy associated with each subscription.

* SNS determines whether the message matches each policy.

* Matching subscriptions receive the message.

* Non-matching subscriptions do not receive that message.

Important: Filtering happens at the subscription level, not at the topic level.

A single SNS topic can have many subscribers, each with its own filter policy.

For example:

| Subscriber           | Filter policy             | Receives              |
| -------------------- | ------------------------- | --------------------- |
| Payment Service      | eventType = PAYMENT       | Payment events        |
| Shipping Service     | status = PAID             | Paid orders           |
| Notification Service | eventType = ORDER_CREATED | Order creation events |
| Analytics Service    | No filter                 | All messages          |

This allows multiple services to share one topic without unnecessarily processing unrelated messages.

### 2\. Subscription Filter Policies

A filter policy is a JSON document attached to an SNS subscription.

It defines the conditions that a message must satisfy before SNS delivers it to that subscription.

Consider the following message:

```json
{
  "eventType": "ORDER_CREATED",
  "status": "PAID",
  "region": "EU",
  "amount": 250
}
```

Suppose the Shipping Service only wants paid orders.

Its filter policy could be:

```json
{
  "status": ["PAID"]
}
```

SNS evaluates the message and checks whether its `status` field matches `PAID`.

Because it does, SNS delivers the message to the Shipping Service.

If another message contains:

```json
{
  "eventType": "ORDER_CREATED",
  "status": "PENDING",
  "region": "EU",
  "amount": 250
}
```

The message does not match the filter policy and is not delivered to that subscription.

### Creating a filter policy using AWS CLI

First, retrieve the subscription ARN:

```bash
aws sns list-subscriptions-by-topic \
  --topic-arn "$TOPIC_ARN"
```

Then configure its filter policy:

```bash
aws sns set-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN" \
  --attribute-name FilterPolicy \
  --attribute-value '{"status":["PAID"]}'
```

You can inspect the subscription configuration:

```bash
aws sns get-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN"
```

### Important distinction

Filter policies belong to subscriptions, not topics.

This means two subscriptions on the same topic can have completely different filtering rules.

### 3\. Attribute-Based Message Filtering

SNS supports filtering messages using message attributes.

Message attributes are additional structured metadata attached to a published message.

They are separate from the message body.

For example, an application might publish this message body:

```json
{
  "orderId": "ORD-1001",
  "customerId": "CUS-2001",
  "amount": 250
}
```

Alongside these message attributes:

| Attribute | Type   | Value         |
| --------- | ------ | ------------- |
| eventType | String | ORDER_CREATED |
| region    | String | EU            |
| priority  | String | HIGH          |
| amount    | Number | 250           |

The message body contains the business data, while attributes provide metadata that SNS can use for routing.

### Configuring attribute-based filtering

Suppose the Shipping Service wants only messages with:

* `eventType = ORDER_CREATED`

* `region = EU`

Its filter policy:

```json
{
  "eventType": ["ORDER_CREATED"],
  "region": ["EU"]
}
```

Both conditions must match.

This is important:

* Different attributes in the same filter policy are combined using logical AND.

* Multiple accepted values for the same attribute are combined using logical OR.

For example:

```json
{
  "region": ["EU", "US"],
  "priority": ["HIGH", "URGENT"]
}
```

This means:

```text
(region = EU OR region = US)
AND
(priority = HIGH OR priority = URGENT)
```

### Publishing messages with attributes using Boto3

```python
import boto3
import json

sns = boto3.client("sns", region_name="eu-west-2")

response = sns.publish(
    TopicArn="YOUR_TOPIC_ARN",
    Message=json.dumps({
        "orderId": "ORD-1001",
        "amount": 250
    }),
    MessageAttributes={
        "eventType": {
            "DataType": "String",
            "StringValue": "ORDER_CREATED"
        },
        "region": {
            "DataType": "String",
            "StringValue": "EU"
        },
        "amount": {
            "DataType": "Number",
            "StringValue": "250"
        }
    }
)

print(response["MessageId"])
```

SNS can now evaluate the message attributes against the filter policies of individual subscriptions.

### When should you use message attributes?

Use message attributes when:

* You want to route messages based on metadata.

* You want to avoid parsing the entire message body.

* You have a clearly defined event classification system.

* You want to separate routing metadata from business payload data.

For example, an application can use `eventType`, `region`, `tenantId`, and `priority` as routing attributes.

### 4\. Message-Body-Based Filtering

SNS also supports filtering based on fields inside the JSON message body.

This is useful when routing information is already included in the business payload.

Consider:

```json
{
  "eventType": "ORDER_CREATED",
  "order": {
    "status": "PAID",
    "region": "EU",
    "amount": 250
  }
}
```

Suppose the Shipping Service wants paid orders from the EU.

The filter policy would be:

```json
{
  "order": {
    "status": ["PAID"],
    "region": ["EU"]
  }
}
```

SNS evaluates the nested fields in the JSON message body.

### Enabling message-body filtering

You must configure the subscription's `FilterPolicyScope` as `MessageBody`.

```bash
aws sns set-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN" \
  --attribute-name FilterPolicyScope \
  --attribute-value MessageBody
```

Then configure the filter policy:

```bash
aws sns set-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN" \
  --attribute-name FilterPolicy \
  --attribute-value '{"order":{"status":["PAID"],"region":["EU"]}}'
```

The two available filter policy scopes are:

| Scope             | Description                                |
| ----------------- | ------------------------------------------ |
| MessageAttributes | Evaluates message attributes.              |
| MessageBody       | Evaluates JSON fields in the message body. |

`MessageAttributes` is the default scope.

Important: Message-body filtering requires valid JSON message bodies. A plain-text message cannot satisfy a JSON body filter.

### Attributes versus message body filtering

| Feature            | Attribute filtering            | Body filtering                 |
| ------------------ | ------------------------------ | ------------------------------ |
| Evaluates          | Message attributes             | JSON message body              |
| Routing metadata   | Separate from payload          | Inside payload                 |
| Nested JSON fields | Not applicable in the same way | Supported                      |
| Configuration      | Default scope                  | Explicit MessageBody scope     |
| Best use           | Metadata-based routing         | Business-payload-based routing |

A useful architectural principle is to use attributes for routing metadata and message-body filtering when the routing information naturally belongs in the payload.

### Important filtering behavior

There are several details worth remembering:

* AND across keys: Every key in a filter policy must match.

* OR within a key: At least one value in that key's value list must match.

* Unspecified attributes: SNS ignores message properties that are not included in the filter policy.

* Missing required attributes: If a filter policy requires an attribute that the message doesn't contain, the message does not match.

* Eventual consistency: Changes to filter policies can take up to 15 minutes to become fully effective. Don't assume a policy update takes effect immediately. Amazon Simple Notification Service +1

### 5\. Filter Policy Operators and Matching Rules

SNS supports more than simple exact-value matching. You can build sophisticated routing rules using different operators.

Let's examine the most useful ones.

### 5.1 Exact matching

Matches a specific value.

```json
{
  "eventType": ["ORDER_CREATED"]
}
```

Matches:

```json
{
  "eventType": "ORDER_CREATED"
}
```

String matching is case-sensitive.

### 5.2 Anything-but matching

Matches values other than the specified values.

```json
{
  "status": [
    {
      "anything-but": ["CANCELLED", "REJECTED"]
    }
  ]
}
```

This accepts messages whose status is neither `CANCELLED` nor `REJECTED`.

### 5.3 Prefix matching

Matches strings beginning with a specified prefix.

```json
{
  "eventType": [
    {
      "prefix": "ORDER_"
    }
  ]
}
```

Matches:

* `ORDER_CREATED`

* `ORDER_CANCELLED`

* `ORDER_UPDATED`

Does not match `PAYMENT_COMPLETED`.

### 5.4 Suffix matching

Matches strings ending with a specified suffix.

```json
{
  "eventType": [
    {
      "suffix": "_FAILED"
    }
  ]
}
```

Matches:

* `PAYMENT_FAILED`

* `ORDER_FAILED`

* `DELIVERY_FAILED`

### 5.5 Numeric matching

You can filter messages using numeric comparisons.

For example, suppose a notification service only wants orders worth at least $100.

```json
{
  "amount": [
    {
      "numeric": [">=", 100]
    }
  ]
}
```

Supported comparison operators include:

| Operator | Meaning               |
| -------- | --------------------- |
| =        | Equal                 |
| >        | Greater than          |
| >=       | Greater than or equal |
| <        | Less than             |
| <=       | Less than or equal    |

You can also combine comparisons:

```json
{
  "amount": [
    {
      "numeric": [">=", 100, "<=", 1000]
    }
  ]
}
```

This matches amounts between 100 and 1,000, inclusive.

### 5.6 Exists matching

Checks whether a particular property exists.

```json
{
  "customerId": [
    {
      "exists": true
    }
  ]
}
```

This matches messages containing a non-null, non-empty `customerId` property.

You can also use `exists: false` to match messages where the property is absent.

### 5.7 Case-insensitive matching

SNS supports case-insensitive string matching through `equals-ignore-case`.

```json
{
  "region": [
    {
      "equals-ignore-case": "europe"
    }
  ]
}
```

This can match `EUROPE`, `Europe`, and `europe`.

### 5.8 IP address matching

SNS supports matching IP addresses and CIDR ranges.

```json
{
  "sourceIp": [
    {
      "cidr": "10.0.0.0/16"
    }
  ]
}
```

This matches IP addresses within the specified network range.

### 5.9 Combining operators

You can combine multiple conditions:

```json
{
  "eventType": [
    {
      "prefix": "ORDER_"
    }
  ],
  "amount": [
    {
      "numeric": [">=", 100]
    }
  ],
  "status": [
    {
      "anything-but": "CANCELLED"
    }
  ]
}
```

The message must satisfy all three conditions:

* Event type starts with `ORDER_`.

* Amount is at least 100.

* Status is not `CANCELLED`.

This is particularly useful when building complex event-routing systems.

Amazon Simple Notification Service +2

### 6\. Filter Policy Scope and Configuration

We've already seen that SNS supports two filtering scopes:

* `MessageAttributes`

* `MessageBody`

Let's understand how these settings fit into the subscription configuration.

A subscription has several attributes, including:

| Attribute          | Purpose                                                         |
| ------------------ | --------------------------------------------------------------- |
| FilterPolicy       | Defines filtering conditions                                    |
| FilterPolicyScope  | Defines where SNS evaluates conditions                          |
| RawMessageDelivery | Controls whether SNS metadata is included in delivered messages |
| RedrivePolicy      | Configures a dead-letter queue for delivery failures            |

The important distinction is that filtering and raw message delivery are independent features.

For example, you can filter messages using attributes and still enable raw message delivery to an SQS subscriber.

### Configuring a complete subscription

Using AWS CLI:

```bash
aws sns set-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN" \
  --attribute-name FilterPolicyScope \
  --attribute-value MessageBody
```

Then:

```bash
aws sns set-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN" \
  --attribute-name FilterPolicy \
  --attribute-value '{"eventType":["ORDER_CREATED"]}'
```

To inspect the result:

```bash
aws sns get-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN"
```

### Filter policy limits

Filter policies have service-defined constraints. Some important ones include:

* Maximum five keys for a filter policy, with nested payload policies counting leaf keys.

* Maximum 150 combinations of values/operators.

* Numeric matching supports values between -1 billion and +1 billion, with up to five decimal places.

* Binary message attributes are not evaluated by attribute-based filtering.

These limits matter when designing large event schemas. Amazon Simple Notification Service

### Pulumi configuration

With Pulumi Python, you can define a subscription and its filtering behavior declaratively:

```python
import pulumi
import pulumi_aws as aws

topic = aws.sns.Topic(
    "orders-topic",
    name="orders-topic"
)

queue = aws.sqs.Queue(
    "shipping-queue",
    name="shipping-queue"
)

subscription = aws.sns.TopicSubscription(
    "shipping-subscription",
    topic=topic.arn,
    protocol="sqs",
    endpoint=queue.arn,
    filter_policy='{"status":["PAID"]}',
    filter_policy_scope="MessageAttributes"
)
```

Here:

* Pulumi creates the SNS topic.

* It creates an SQS queue.

* It creates an SNS subscription.

* It attaches a filter policy to the subscription.

For a production implementation, the SQS queue must also have an appropriate resource policy allowing SNS to send messages to it.

### 7\. Filter Policy Evaluation and Subscription Behavior

Let's bring the filtering concepts together with a practical example.

Imagine an e-commerce platform publishing the following events:

```json
{
  "eventType": "ORDER_CREATED",
  "region": "EU",
  "amount": 250,
  "status": "PAID"
}
```

Three subscriptions have different filter policies.

| Subscription       | Filter policy |
| ------------------ | ------------- |
| Shipping           | status = PAID |
| European Analytics | region = EU   |
| High-value Orders  | amount >= 200 |

![Simplifying AWS Message Handling Processes](https://images.openai.com/static-rsc-4/Y2fQNCMrh2zRCp8HF27Bjp44ymKsBNTuseqJvzkdvzHBYfyCHXzsvX6YNefTLLuleHa1ySA77BkbP0NZmtz4bhgF5H9McbDPaw47OfJIcXvy16UwBuIyCNySP-V1XYrUT9bEPOFxBUZMrVSmAQqFhmo6gFernuBDPvUijQO2IYuPhvLn8yvUCLfPn0P-XWDM?purpose=fullsize)

When SNS receives the message:

* Shipping receives it because the order is paid.

* European Analytics receives it because the region is EU.

* High-value Orders receives it because the amount is at least 200.

Now suppose another event arrives:

```json
{
  "eventType": "ORDER_CREATED",
  "region": "US",
  "amount": 50,
  "status": "PENDING"
}
```

None of these three subscriptions receives the message.

However, an additional subscription without a filter policy receives every published message.

Architectural takeaway: Filtering reduces unnecessary message delivery and processing. It does not replace authorization, business validation, or application-level security.

### 8\. Standard Topics versus FIFO Topics

SNS provides two topic types:

* Standard topics

* FIFO topics

Both implement publish-subscribe messaging, but they have different guarantees.

![Creating an SNS (Simple Notification Service) using the AWS Command Line Interface (CLI) | by Kunalmathur | Medium](https://images.openai.com/static-rsc-4/y-pqHOlZsjrD6NzwybiPdi80_oDQhZCdLPNR8ySECz7IVkEAN4ItoAp3BppI6_zNVDz8Y9xOba38bOafpK7poypnrRkm8FQ4rOl4NOhWqChnU8GwWcDHtqpTK534n48yF3S6Z1K6kf-vnlxWTIuOpPO3jkdEuwxzkORfQrGyGcSKTcq5ULJOVaoRamuaPf7M?purpose=fullsize)

Standard topic

High flexibility

Best for high-throughput notifications where strict ordering isn't required.

![Detalhes de ordenação de mensagens do Amazon SNS para tópicos FIFO - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/nT3VHdcw4_W9rbxASARXQo1qxKV4r9RfVWtsIYZUexykmIMSD6QlUcvXLx64qf2gfzvSxj6JBLfVlyYG66UMZD2IH6TbsVmw8MRfUlUtvn_6Zyp1wL4_HJ8yeYS95BkCAkuwyM8Yw_dZGwBsyz-p8zIkZlG6i5xFCksPVhwy7zNczo5bMgPgp-v0_ib8dwg0?purpose=fullsize)

FIFO topic

Ordered delivery

Best for event streams where ordering and deduplication matter.

### Comparison

| Feature          | Standard                 | FIFO                              |
| ---------------- | ------------------------ | --------------------------------- |
| Message ordering | Best effort              | Strict within message group       |
| Deduplication    | No FIFO deduplication    | Supported                         |
| Throughput       | Very high                | High, subject to quotas           |
| Delivery         | At least once            | Depends on delivery configuration |
| Message groups   | No                       | Yes                               |
| Filtering        | Supported                | Supported                         |
| SQS integration  | Standard and FIFO queues | Standard and FIFO queues          |
| HTTP/S delivery  | Supported                | Not supported                     |
| Email/SMS        | Supported                | Not supported                     |

An important distinction: FIFO topics can subscribe to both SQS Standard and SQS FIFO queues, but they cannot directly deliver to HTTP/S, email, SMS, or mobile application endpoints.

Also, subscribing a Standard SQS queue to an SNS FIFO topic does not preserve the strict ordering and deduplication guarantees all the way to the consumer.

Amazon Simple Notification Service +1

### When should you use Standard topics?

Consider a notification system:

* Send order confirmation emails.

* Notify mobile applications.

* Send HTTP notifications to external services.

* Distribute application events to multiple consumers.

The exact order of notifications is usually not critical.

### When should you use FIFO topics?

Consider a banking transaction system:

```text
Account A:
1. Deposit $500
2. Withdraw $100
3. Transfer $200
```

If these operations are processed out of order, the application may calculate an incorrect account balance.

FIFO topics help preserve the intended ordering of related events.

However, FIFO messaging does not automatically make your entire application transactional. Your consumers must still handle failures and maintain correct business state.

### 9\. FIFO Message Ordering and Message Groups

FIFO means First-In, First-Out.

SNS FIFO topics preserve the order in which messages are published within each message group.

The most important concept here is the MessageGroupId.

### What is a message group?

A message group identifies a sequence of related messages that must maintain ordering.

For example, consider an online banking system with three accounts:

| Account   | Message group |
| --------- | ------------- |
| Account A | ACCOUNT-A     |
| Account B | ACCOUNT-B     |
| Account C | ACCOUNT-C     |

Each account has its own independent message sequence.

![Detail pemesanan pesan Amazon SNS untuk topik FIFO - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/M6VGq5GliimuhdX8qej_1Ahn0xGgFwK5h3wamDc9A8k_q7fxhjc0YGLtxAZIrMfJERuYTOoWbBikTfeQl3d7OBkF9pGZ2JwOokhzrSY245wIsbYkZksQNo2dWkt16pSU4p43GoO75fniZwhyQ-s35LgPosROzBzvdi1IzkVVvQlgTjVY-nLS-B3wQhGFXsRI?purpose=fullsize)

Messages within Account A must maintain their original order.

However, Account A and Account B can be processed independently.

For example:

```text
ACCOUNT-A:
  Message 1: Deposit 500
  Message 2: Withdraw 100
  Message 3: Transfer 200

ACCOUNT-B:
  Message 1: Deposit 300
  Message 2: Withdraw 50
```

SNS maintains ordering within each group rather than imposing one global sequence across all groups.

This allows parallel processing while maintaining ordering for related events.

### Publishing to an SNS FIFO topic using Boto3

First, create an SNS FIFO topic:

```python
import boto3

sns = boto3.client("sns", region_name="eu-west-2")

response = sns.create_topic(
    Name="banking-events.fifo",
    Attributes={
        "FifoTopic": "true",
        "ContentBasedDeduplication": "false"
    }
)

topic_arn = response["TopicArn"]

print(topic_arn)
```

Notice the `.fifo` suffix in the topic name.

Now publish a message:

```python
response = sns.publish(
    TopicArn=topic_arn,
    Message='{"accountId":"ACCOUNT-A","amount":500,"type":"DEPOSIT"}',
    MessageGroupId="ACCOUNT-A",
    MessageDeduplicationId="deposit-1001"
)

print(response["MessageId"])
print(response["SequenceNumber"])
```

Two important parameters:

* `MessageGroupId`: Identifies the ordering group.

* `MessageDeduplicationId`: Identifies the message for deduplication.

For another message belonging to the same account, reuse the same group ID but provide a different deduplication ID.

```python
sns.publish(
    TopicArn=topic_arn,
    Message='{"accountId":"ACCOUNT-A","amount":100,"type":"WITHDRAWAL"}',
    MessageGroupId="ACCOUNT-A",
    MessageDeduplicationId="withdrawal-1001"
)
```

This preserves the sequence of events for Account A.

### Sequence numbers

SNS assigns sequence numbers to messages published to FIFO topics.

These numbers are useful for understanding message order.

They are large, non-consecutive numbers and should not be treated as simple counters or used to infer the number of messages published.

Amazon Simple Notification Service +1

### 10\. Message Deduplication Mechanisms

Deduplication prevents SNS FIFO topics from delivering multiple copies of the same published message within a defined time window.

Imagine an application sends an order event:

```json
{
  "orderId": "ORD-1001",
  "eventType": "ORDER_CREATED"
}
```

Because of a network timeout, the publisher doesn't receive the expected response.

It assumes publishing failed and sends the same event again.

Without deduplication, the same order event could be delivered twice.

SNS FIFO provides two deduplication mechanisms:

* Explicit message deduplication IDs.

* Content-based deduplication.

### 10.1 Explicit message deduplication IDs

The publisher assigns a unique identifier to each logical message.

For example:

```python
response = sns.publish(
    TopicArn=topic_arn,
    Message='{"orderId":"ORD-1001","eventType":"ORDER_CREATED"}',
    MessageGroupId="ORDERS",
    MessageDeduplicationId="ORDER-1001-CREATED"
)
```

If the publisher sends another message using the same deduplication ID within the deduplication interval, SNS accepts the publishing request but does not deliver another copy.

The deduplication interval is five minutes.

For example:

| Time  | Deduplication ID   | Result                      |
| ----- | ------------------ | --------------------------- |
| 10:00 | ORDER-1001-CREATED | Delivered                   |
| 10:01 | ORDER-1001-CREATED | Duplicate suppressed        |
| 10:03 | ORDER-1001-CREATED | Duplicate suppressed        |
| 10:06 | ORDER-1001-CREATED | Eligible for delivery again |

The five-minute interval starts with the successful publication of the original message.

An important distinction: SNS deduplication is not a permanent record of processed messages. After the deduplication window expires, the same ID can be accepted again.

### 10.2 Content-based deduplication

Instead of manually generating deduplication IDs, SNS can generate them automatically.

It calculates a SHA-256 hash of the message body and uses that hash as the deduplication ID.

Create a FIFO topic with content-based deduplication enabled:

```python
response = sns.create_topic(
    Name="orders.fifo",
    Attributes={
        "FifoTopic": "true",
        "ContentBasedDeduplication": "true"
    }
)

topic_arn = response["TopicArn"]
```

Now publish without specifying a deduplication ID:

```python
sns.publish(
    TopicArn=topic_arn,
    Message='{"orderId":"ORD-1001","eventType":"ORDER_CREATED"}',
    MessageGroupId="ORDERS"
)
```

If the same message body is published again within five minutes, SNS identifies it as a duplicate.

### Important considerations

* SNS hashes the message body, not its message attributes.

* Different message bodies generate different hashes.

* Identical message bodies generate the same hash.

* An explicitly supplied `MessageDeduplicationId` overrides the generated ID.

* The deduplication interval is five minutes.

Consider these two messages:

Message A:

```json
{
  "orderId": "ORD-1001",
  "region": "EU"
}
```

Message B:

```json
{
  "orderId": "ORD-1001",
  "region": "US"
}
```

They produce different hashes because their bodies differ.

However, if the region is supplied only as a message attribute and the message bodies are identical, content-based deduplication considers them duplicates.

This is an important architectural consideration when designing event schemas.

Amazon Simple Notification Service

### 11\. Deduplication IDs and Deduplication Intervals

Let's examine how deduplication interacts with message groups and throughput.

SNS FIFO supports two deduplication scopes, controlled by the topic attribute `FifoThroughputScope`.

| Scope        | Behavior                                                       |
| ------------ | -------------------------------------------------------------- |
| Topic        | Deduplication applies across the entire topic.                 |
| MessageGroup | Deduplication applies independently within each message group. |

### Example: Topic-level deduplication

Suppose two messages are published:

```text
Message A:
Group ID = ACCOUNT-A
Deduplication ID = TX-100

Message B:
Group ID = ACCOUNT-B
Deduplication ID = TX-100
```

With topic-level deduplication, the second message is treated as a duplicate because its deduplication ID has already been used on the topic.

### Example: Message-group-level deduplication

With `MessageGroup` scope, the same deduplication ID can be used in different message groups without one suppressing the other.

```text
ACCOUNT-A:
  Deduplication ID = TX-100

ACCOUNT-B:
  Deduplication ID = TX-100
```

These messages are independently deduplicated.

This is particularly useful when processing independent customers, accounts, or orders.

Important: When designing identifiers, make them unique within the intended deduplication scope. For example, using a combination of account ID and transaction ID can avoid accidental collisions.

Amazon Simple Notification Service +1

### 12\. FIFO Throughput and Limitations

FIFO topics provide ordering and deduplication, but these capabilities introduce architectural considerations.

### Standard throughput

SNS FIFO topics support two throughput configurations:

* `Topic`: Topic-level deduplication.

* `MessageGroup`: Message-group-level deduplication, which enables high-throughput FIFO mode.

High-throughput mode distributes message groups across SNS partitions.

You don't manage these partitions manually.

SNS manages them automatically based on traffic.

### Configuring high throughput

You can configure this attribute when creating the topic:

```python
response = sns.create_topic(
    Name="orders.fifo",
    Attributes={
        "FifoTopic": "true",
        "ContentBasedDeduplication": "false",
        "FifoThroughputScope": "MessageGroup"
    }
)
```

This enables message-group-level deduplication and high-throughput FIFO behavior.

Once `FifoThroughputScope` is changed to `MessageGroup`, AWS does not allow reverting it to `Topic`.

### Throughput considerations

According to AWS's current service quotas:

| Configuration                  | Throughput                      |
| ------------------------------ | ------------------------------- |
| FIFO topic, Topic scope        | 3,000 messages/second per topic |
| FIFO topic, MessageGroup scope | Up to regional quotas           |
| Maximum per message group      | 300 messages/second             |

The default topic-level limit also considers a 20 MB/second throughput ceiling.

Regional account-level publishing quotas apply as well, so the effective throughput depends on both the topic configuration and regional limits. Amazon Simple Notification Service +1

### Why message group distribution matters

Consider two designs.

Poor distribution

`MessageGroupId = GLOBAL`

All messages belong to one group

Limited parallelism and a potential throughput bottleneck.

Better distribution

`ACCOUNT-A`

`ACCOUNT-B`

`ACCOUNT-C`

Multiple independently ordered groups

More opportunities for parallel processing while preserving ordering within each account.

AWS recommends using many distinct message group IDs to distribute traffic effectively.

### Other FIFO limitations

* FIFO topic names must end with `.fifo`.

* FIFO topics cannot directly deliver to email, SMS, HTTP/S, or mobile application endpoints.

* FIFO ordering is maintained within message groups, not globally across all groups.

* Subscribers must support the appropriate FIFO delivery architecture.

* A single message group can become a throughput bottleneck.

* Cross-region delivery can reduce throughput because maintaining ordering introduces additional latency.

For high-throughput FIFO systems, the subscribed SQS FIFO queues should also use high-throughput FIFO configuration where appropriate. Amazon Simple Notification Service +2

### 13\. SNS FIFO Integration with SQS FIFO Queues

This is one of the most important integrations in the entire SNS and SQS learning track.

SNS is responsible for distributing messages to subscribers.

SQS is responsible for storing messages until consumers retrieve and process them.

Combining SNS FIFO with SQS FIFO gives you:

* Pub/sub message distribution.

* Message ordering within message groups.

* FIFO message deduplication.

* Independent message consumption.

* Decoupling between publishers and consumers.

### Architecture

![Amazon SNS message grouping for FIFO topics - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/qm2ViYnTpYc1ATB4lpbxB87naVC9DA_Zt5jFjEz0lnUmmxcLZOx3VZUQ0ITwaFNWbRkFpXWO8fEmsfmuN4rsjrOzTYcbC2ThF2URkHTxkaakHKTc5oL6R1HowaxxC0HSINKliTtYIlmhYBoTHbHRJDe4iQMSyy7kvDvFqbad2K4oJJ7hdhLBM6HeeqqcIIPO?purpose=fullsize)

Imagine an e-commerce application.

When a customer places an order, the application publishes events to an SNS FIFO topic.

The topic distributes messages to:

* Payment SQS FIFO queue.

* Shipping SQS FIFO queue.

* Inventory SQS FIFO queue.

Each service processes its own copy of the event stream.

### Step 1 — Create an SNS FIFO topic

```python
import boto3

sns = boto3.client("sns", region_name="eu-west-2")

topic = sns.create_topic(
    Name="orders.fifo",
    Attributes={
        "FifoTopic": "true",
        "ContentBasedDeduplication": "false"
    }
)

topic_arn = topic["TopicArn"]
```

### Step 2 — Create SQS FIFO queues

```python
sqs = boto3.client("sqs", region_name="eu-west-2")

queue_names = [
    "payment.fifo",
    "shipping.fifo",
    "inventory.fifo"
]

queues = {}

for name in queue_names:
    response = sqs.create_queue(
        QueueName=name,
        Attributes={
            "FifoQueue": "true",
            "ContentBasedDeduplication": "false"
        }
    )

    queues[name] = response["QueueUrl"]
```

### Step 3 — Obtain queue ARNs

```python
queue_arns = {}

for name, url in queues.items():
    attributes = sqs.get_queue_attributes(
        QueueUrl=url,
        AttributeNames=["QueueArn"]
    )

    queue_arns[name] = attributes["Attributes"]["QueueArn"]
```

### Step 4 — Allow SNS to send messages to SQS

SNS needs permission to deliver messages to each queue.

For example, configure a queue policy:

```python
import json

for name, url in queues.items():

    policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "Service": "sns.amazonaws.com"
                },
                "Action": "sqs:SendMessage",
                "Resource": queue_arns[name],
                "Condition": {
                    "ArnEquals": {
                        "aws:SourceArn": topic_arn
                    }
                }
            }
        ]
    }

    sqs.set_queue_attributes(
        QueueUrl=url,
        Attributes={
            "Policy": json.dumps(policy)
        }
    )
```

This resource policy allows the specified SNS topic to send messages to the queue.

### Step 5 — Subscribe queues to the topic

```python
for name, queue_arn in queue_arns.items():

    sns.subscribe(
        TopicArn=topic_arn,
        Protocol="sqs",
        Endpoint=queue_arn
    )
```

Now all three queues are subscribers to the same SNS FIFO topic.

### Step 6 — Publish an event

```python
response = sns.publish(
    TopicArn=topic_arn,
    Message=json.dumps({
        "orderId": "ORD-1001",
        "eventType": "ORDER_CREATED",
        "amount": 250
    }),
    MessageGroupId="CUSTOMER-1001",
    MessageDeduplicationId="ORD-1001-CREATED"
)

print(response["MessageId"])
```

SNS distributes the message to all three subscribed queues.

### Step 7 — Consumers process their queues

Each service independently receives messages from its own queue.

For example:

```python
response = sqs.receive_message(
    QueueUrl=queues["payment.fifo"],
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)

for message in response.get("Messages", []):

    print(message["Body"])

    sqs.delete_message(
        QueueUrl=queues["payment.fifo"],
        ReceiptHandle=message["ReceiptHandle"]
    )
```

The Payment Service can process messages independently of Shipping and Inventory.

### Important integration details

1\. Use FIFO queues when you need end-to-end ordering.

SNS FIFO can also deliver to Standard SQS queues, but Standard queues do not guarantee strict ordering or deduplication.

2\. Configure filtering carefully.

SNS FIFO supports subscription filtering, but filtering changes the delivery guarantee: filtered subscriptions provide at-most-once delivery rather than the documented exactly-once delivery conditions.

3\. Understand exactly-once limitations.

SNS FIFO and SQS FIFO provide strong deduplication and delivery guarantees under specific conditions. Your consumer must successfully process and delete the message before its visibility timeout expires. Your application should still use idempotent business operations.

4\. Lambda integration.

If you want Lambda to consume messages from an SNS FIFO → SQS FIFO architecture, configure the SQS FIFO queue as the Lambda event source. SNS does not directly invoke Lambda from a FIFO topic.

Amazon Simple Notification Service +2

### 14\. Putting Everything Together: Choosing the Right Architecture

Let's summarize the main concepts.

| Requirement                               | SNS feature                    |
| ----------------------------------------- | ------------------------------ |
| Distribute events to multiple subscribers | SNS topics                     |
| Route only relevant events                | Subscription filter policies   |
| Filter using metadata                     | Attribute-based filtering      |
| Filter using JSON payload fields          | Message-body filtering         |
| Match numeric ranges                      | Numeric operators              |
| Preserve related message ordering         | FIFO topics and message groups |
| Suppress duplicate publications           | Deduplication IDs              |
| Automatically generate deduplication IDs  | Content-based deduplication    |
| Increase FIFO throughput                  | Message-group throughput scope |
| Durable asynchronous consumption          | SNS + SQS                      |

### Final architectural comparison

Scenario A — General notifications

Application

SNS Standard Topic

Email

HTTP/S

Lambda

Use when flexible notification delivery and high throughput matter more than strict ordering.

Scenario B — Ordered business events

Application

SNS FIFO Topic

Payment FIFO

Shipping FIFO

Inventory FIFO

Use when multiple independent consumers need ordered business events.

### Key takeaways

* SNS filtering is subscription-specific. Each subscriber can receive only the messages relevant to it.

* Attribute-based filtering evaluates message metadata, while body-based filtering evaluates JSON payload fields.

* Filter policies support exact matching, numeric comparisons, prefixes, suffixes, and other operators.

* SNS FIFO preserves ordering within message groups.

* Deduplication suppresses repeated messages within a five-minute interval.

* Content-based deduplication uses the message body, not message attributes.

* High-throughput FIFO relies on distributing messages across multiple message groups.

* SNS FIFO + SQS FIFO is a powerful architecture for ordered event distribution and independent processing.

The most important architectural distinction: SNS decides who should receive a message, while SQS decides when a consumer receives and processes that message.

This is the foundation of SNS/SQS-based event-driven microservices.

### Official AWS documentation

For further reference, these are the relevant AWS documentation pages:

* [SNS subscription filter policies](https://docs.aws.amazon.com/sns/latest/dg/sns-subscription-filter-policies.html?utm_source=chatgpt.com).

* [SNS message filtering](https://docs.aws.amazon.com/sns/latest/dg/sns-message-filtering.html?utm_source=chatgpt.com).

* [SNS FIFO message ordering](https://docs.aws.amazon.com/sns/latest/dg/fifo-topic-message-ordering.html?utm_source=chatgpt.com).

* [SNS FIFO message deduplication](https://docs.aws.amazon.com/sns/latest/dg/fifo-message-dedup.html?trk=article-ssr-frontend-pulse_little-text-block&utm_source=chatgpt.com).

* [High-throughput FIFO topics](https://docs.aws.amazon.com/us_en/sns/latest/dg/fifo-high-throughput.html?utm_source=chatgpt.com).

* [SNS service quotas](https://docs.aws.amazon.com/general/latest/gr/sns.html?utm_source=chatgpt.com).
