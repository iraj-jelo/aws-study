### Module 6 — SQS Monitoring, Scaling, Integrations, and Production Architectures

Amazon Simple Queue Service · Advanced · Production Engineering

This final module brings together everything learned in the SQS course. The goal is to understand how to operate SQS in production environments, monitor message-processing systems, scale consumers, integrate SQS with other AWS services, and manage infrastructure using Pulumi.

We'll move beyond individual queues and look at complete event-driven architectures involving Lambda, ECS, SNS, EventBridge, CloudWatch, and SQS.

### 1\. CloudWatch Metrics and Monitoring

Amazon SQS integrates with Amazon CloudWatch to provide operational metrics about queues and their messages.

CloudWatch collects metrics automatically for SQS queues. You can use these metrics to understand:

* How many messages are waiting to be processed.

* How many messages are currently being processed.

* How quickly consumers process messages.

* Whether messages are accumulating.

* Whether consumers are keeping up with producers.

* Whether messages are approaching expiration.

SQS publishes metrics in the `AWS/SQS` namespace.

### Important SQS CloudWatch metrics

| Metric                                | Description                                           |
| ------------------------------------- | ----------------------------------------------------- |
| ApproximateNumberOfMessagesVisible    | Messages available to be received.                    |
| ApproximateNumberOfMessagesNotVisible | Messages currently in flight.                         |
| ApproximateNumberOfMessagesDelayed    | Messages waiting for their delivery delay to expire.  |
| ApproximateAgeOfOldestMessage         | Approximate age of the oldest message in the queue.   |
| NumberOfMessagesSent                  | Number of messages sent to the queue.                 |
| NumberOfMessagesReceived              | Number of messages received by consumers.             |
| NumberOfMessagesDeleted               | Number of messages deleted after processing.          |
| NumberOfEmptyReceives                 | Number of receive requests that returned no messages. |
| SentMessageSize                       | Message sizes sent to the queue.                      |

Most SQS queue-depth metrics are approximate because SQS is a distributed service.

Important distinction: Receiving a message does not mean it has been successfully processed. A message is removed permanently only after a successful deletion.

For example:

Suppose an order-processing queue has:

* 5,000 visible messages.

* 200 messages in flight.

* 50 delayed messages.

* An oldest-message age of 180 seconds.

This tells us that consumers have a substantial backlog. However, we need additional information to determine whether the problem is insufficient consumer capacity, slow processing, or a failure in the consumer application.

### CloudWatch metric dimensions

SQS metrics are associated with dimensions such as:

* `QueueName`

* AWS Region

* Account

You can use these dimensions to monitor individual queues and compare different environments.

### Metric collection considerations

SQS provides metrics automatically, but there are some important details:

* Many queue metrics are approximate.

* Metrics are generally published at one-minute intervals, but some metrics have different reporting characteristics.

* CloudWatch metrics are not a replacement for application-level monitoring.

* Metrics alone cannot tell you why a particular message failed.

For more detailed visibility, combine SQS metrics with application logs, tracing, and CloudTrail.

### 2\. Queue Depth, Message Age, and Processing Throughput

Monitoring a queue requires understanding three important concepts:

* Queue depth.

* Message age.

* Processing throughput.

These metrics help you determine whether your messaging system is healthy.

### 2.1 Queue depth

Queue depth represents the number of messages waiting to be processed.

The most important metric is:

```text
ApproximateNumberOfMessagesVisible
```

Consider this architecture:

Producers

Applications sending orders

SQS Queue

### 5,000

Visible messages

Consumers

Processing orders

If producers send 100 messages per second but consumers process only 60 messages per second, the queue grows by approximately 40 messages per second.

The backlog will continue growing until:

* Consumer capacity increases.

* Producer traffic decreases.

* Processing becomes more efficient.

* Messages are otherwise removed or expire.

### 2.2 Message age

The metric:

```text
ApproximateAgeOfOldestMessage
```

indicates how long the oldest message has been waiting in the queue.

This is often more useful than queue depth alone.

For example:

| Queue         | Visible messages | Oldest message age |
| ------------- | ---------------- | ------------------ |
| Orders        | 10,000           | 5 seconds          |
| Payments      | 100              | 600 seconds        |
| Notifications | 2,000            | 30 seconds         |

The Payments queue has fewer messages than the Orders queue, but its oldest message is much older.

This could indicate that payment processing is stalled or that the consumers are processing messages too slowly.

Message age also requires careful interpretation. In Standard queues, repeatedly received messages can affect which message is reported as the oldest. DLQ behavior and message expiration can also affect the metric.

### 2.3 Processing throughput

Throughput measures how many messages your system processes over a period.

For example:

```text
Messages processed per second = 500
Messages produced per second  = 400
```

The system processes messages faster than producers create them, so the backlog should generally decrease.

A simplified throughput calculation is:

Throughput = \\frac{ProcessedMessages}{Time}

For example:

Throughput = \\frac{30,000}{60} = 500

The processing rate is 500 messages per second.

You can use CloudWatch's `NumberOfMessagesDeleted` as an approximate indicator of successful processing, provided your application deletes messages only after successful processing.

It is not a perfect measure of business-level success. Application-level metrics should track successful orders, payments, or other business operations separately.

### 2.4 Understanding the relationship between metrics

Consider three situations:

| Situation  | Queue depth          | Message age        | Interpretation           |
| ---------- | -------------------- | ------------------ | ------------------------ |
| Healthy    | Stable or decreasing | Low                | Consumers keep up        |
| Overloaded | Increasing           | Increasing         | Insufficient capacity    |
| Stalled    | High                 | Increasing rapidly | Consumers may be failing |

A production monitoring system should consider multiple metrics together rather than alerting only on queue depth.

### 3\. CloudWatch Alarms and Dashboards

CloudWatch alarms allow you to detect operational problems automatically.

Instead of manually checking queue metrics, you can configure alarms that notify your team when certain conditions occur.

### 3.1 Creating a CloudWatch alarm

Suppose you want to detect when an SQS queue has more than 1,000 visible messages for several consecutive minutes.

You can create an alarm using:

* Namespace: `AWS/SQS`

* Metric: `ApproximateNumberOfMessagesVisible`

* Dimension: `QueueName`

* Threshold: 1,000

* Comparison: Greater than

* Evaluation period: 5 minutes

* Datapoints to alarm: 3 out of 5

This helps prevent temporary spikes from triggering unnecessary notifications.

### 3.2 Important production alarms

| Metric               | Example alarm condition         |
| -------------------- | ------------------------------- |
| Visible messages     | Above 1,000                     |
| Oldest message age   | Above 300 seconds               |
| In-flight messages   | Approaching processing capacity |
| DLQ visible messages | Greater than 0                  |
| Empty receives       | Unexpectedly high               |
| Processing errors    | Application-defined threshold   |

These are illustrative thresholds, not universal defaults. Actual values depend on your application's latency requirements, throughput, and workload.

### 3.3 CloudWatch alarm architecture

Amazon SQS

Queue metrics

Amazon CloudWatch

Metrics and alarm evaluation

CloudWatch Dashboard

Visual monitoring

SNS Notification

Operational alerts

CloudWatch dashboards can display:

* Queue depth.

* Oldest message age.

* Messages sent and deleted.

* In-flight messages.

* DLQ message counts.

* Lambda errors and duration.

* Consumer application metrics.

This gives you a centralized view of the entire messaging system.

### 4\. CloudTrail Auditing and API Activity

CloudWatch tells us how SQS is performing. AWS CloudTrail tells us what actions were performed against AWS resources and who performed them.

CloudTrail records API activity, including operations such as:

* `CreateQueue`

* `DeleteQueue`

* `SetQueueAttributes`

* `SendMessage`

* `ReceiveMessage`

* `DeleteMessage`

* `PurgeQueue`

* `AddPermission`

* `RemovePermission`

### 4.1 Management events versus data events

This distinction is important.

| Event type        | Examples                                     | Default behavior                          |
| ----------------- | -------------------------------------------- | ----------------------------------------- |
| Management events | CreateQueue, DeleteQueue, SetQueueAttributes | Logged by CloudTrail event history        |
| Data events       | SendMessage, ReceiveMessage, DeleteMessage   | Require explicit data-event configuration |

Management events help you understand changes to your infrastructure.

Data events help you investigate message-level API activity.

For example, imagine someone accidentally changes the permissions of a production queue.

You can investigate:

* Who performed the API operation?

* When did it happen?

* Which queue was affected?

* Which IAM identity made the request?

* What request parameters were supplied?

For message-level auditing, you can enable SQS data events in a CloudTrail trail or event data store.

Important: Data events can generate substantial volumes of records and additional charges. Enable them selectively for queues where the auditing requirements justify the cost.

### 4.2 CloudTrail and CloudWatch have different responsibilities

| CloudWatch                       | CloudTrail                              |
| -------------------------------- | --------------------------------------- |
| Monitors queue health            | Audits AWS API activity                 |
| Tracks queue metrics             | Records API calls                       |
| Creates operational alarms       | Supports security investigations        |
| Helps detect backlogs            | Helps investigate configuration changes |
| Monitors application performance | Helps establish who performed an action |

In production, you generally need both.

### 5\. Scaling Consumers and Managing Processing Capacity

One of the most important responsibilities when operating SQS is managing consumer capacity.

SQS separates producers from consumers, which means each side can scale independently.

For example, an e-commerce application might have:

* An order API producing messages.

* An SQS queue storing orders.

* Multiple workers processing orders.

When traffic increases, you can increase the number of consumers without changing the producer application.

### 5.1 Horizontal scaling

Horizontal scaling means increasing or decreasing the number of consumer instances.

Consider the following example:

Order Producers

SQS Queue

Increasing message backlog

Worker 1

Consumer

Worker 2

Consumer

Worker 3

Consumer

Suppose each worker can process 20 messages per second.

| Workers | Approximate capacity |
| ------- | -------------------- |
| 1       | 20 messages/sec      |
| 5       | 100 messages/sec     |
| 10      | 200 messages/sec     |
| 20      | 400 messages/sec     |

These numbers assume similar processing times and sufficient downstream capacity.

More consumers do not always mean more throughput. Your database, external APIs, connection pools, or other dependencies may become bottlenecks.

### 5.2 Scaling based on queue depth

A common approach is to scale consumers according to the number of visible messages.

For example:

* Below 100 messages: 2 workers.

* Between 100 and 1,000 messages: 5 workers.

* Above 1,000 messages: 10 workers.

In production, you should also consider message age and processing latency.

A queue with 10,000 messages that can be processed in a few seconds may be less concerning than a queue with 100 messages that have been waiting for 20 minutes.

### 5.3 Scaling based on backlog per worker

A more useful metric for container-based consumers is backlog per worker.

BacklogPerWorker = \\frac{VisibleMessages}{RunningWorkers}

For example:

\\frac{10,000}{10}=1,000

Each worker has approximately 1,000 messages of backlog to process.

You can use this metric to create a target-tracking scaling policy.

### 5.4 Other scaling considerations

When increasing consumer capacity, consider:

* Maximum database connections.

* CPU and memory consumption.

* API rate limits.

* Message processing duration.

* Visibility timeout.

* Maximum in-flight messages.

* FIFO message group concurrency.

* Downstream service capacity.

Important: SQS is designed to absorb bursts, but it does not eliminate the need to manage downstream capacity.

### 6\. Lambda Event Source Mappings and SQS Integration

One of the most popular SQS integrations is AWS Lambda.

Lambda can automatically poll an SQS queue and invoke your function when messages become available.

This is different from a traditional HTTP-triggered Lambda function.

With SQS, Lambda uses an event source mapping.

### 6.1 How the integration works

Producer Application

Sends messages using SendMessage

Amazon SQS

Stores messages

Lambda Event Source Mapping

Polls the queue and retrieves batches

AWS Lambda Function

Processes messages

Successful messages deleted from SQS

Failed messages become available for retry after visibility timeout

Lambda manages the polling process. You do not need to implement an SQS polling loop inside your function.

### 6.2 Event source mapping configuration

An event source mapping has several important configuration options.

| Configuration                  | Purpose                                                 |
| ------------------------------ | ------------------------------------------------------- |
| batchSize                      | Maximum number of messages retrieved per batch          |
| maximumBatchingWindowInSeconds | Maximum time to collect messages before invoking Lambda |
| enabled                        | Enables or disables the mapping                         |
| maximumConcurrency             | Limits concurrent Lambda invocations for the mapping    |
| functionResponseTypes          | Enables partial batch failure reporting                 |
| scalingConfig                  | Controls maximum concurrency for supported mappings     |

For SQS event source mappings:

* Standard queues support batch sizes up to 10,000.

* FIFO queues support batch sizes up to 10.

* A batching window can be configured to collect messages before invocation.

Actual concurrency and throughput depend on queue type, function configuration, account quotas, and downstream capacity.

### 6.3 Python Lambda example

Suppose an SQS message contains an order:

```json
{
  "order_id": "ORD-1001",
  "customer_id": "CUS-501",
  "amount": 150.00
}
```

The Lambda function receives a batch of messages in the event.

```python
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    for record in event["Records"]:
        body = json.loads(record["body"])

        order_id = body["order_id"]

        logger.info(
            "Processing order %s",
            order_id
        )

        process_order(body)

    return {"statusCode": 200}

def process_order(order):
    logger.info(
        "Order processed: %s",
        order["order_id"]
    )
```

When all records are processed successfully, Lambda's SQS integration deletes the corresponding messages.

However, if the invocation fails, messages can become available again after the visibility timeout.

This means your processing logic must be idempotent.

### 6.4 Partial batch failure handling

Suppose Lambda receives 10 messages:

* 8 succeed.

* 2 fail.

Without partial batch response handling, the entire batch can be retried.

You can enable `ReportBatchItemFailures` to report only the failed messages.

Example:

```python
import json
import logging

logger = logging.getLogger()

def lambda_handler(event, context):
    failures = []

    for record in event["Records"]:
        try:
            body = json.loads(record["body"])
            process_order(body)

        except Exception:
            logger.exception("Message processing failed")

            failures.append({
                "itemIdentifier": record["messageId"]
            })

    return {
        "batchItemFailures": failures
    }

def process_order(order):
    logger.info(
        "Processing order %s",
        order["order_id"]
    )
```

This reduces unnecessary reprocessing of successful messages.

For FIFO queues, failure handling requires additional care to preserve ordering within message groups.

### 6.5 Important operational considerations

When integrating Lambda with SQS:

* Configure visibility timeout appropriately. AWS recommends setting it to at least six times the Lambda function timeout, plus the maximum batching window, to allow for retries and throttling.

* Configure a DLQ or appropriate failure-isolation strategy.

* Implement idempotent processing.

* Monitor Lambda concurrency and throttling.

* Set batch size according to processing requirements.

* Protect downstream systems from excessive concurrency.

A particularly important distinction: Lambda polling is managed by the event source mapping, not by SQS pushing messages directly to Lambda.

### 7\. ECS and Container-Based Consumers

Lambda is excellent for event-driven workloads, but it is not always the best choice.

Some applications require:

* Long-running processes.

* Custom dependencies.

* Persistent connections.

* Specialized runtimes.

* More control over CPU and memory.

* Complex message-processing pipelines.

For these workloads, you can deploy consumers using Amazon ECS.

### 7.1 ECS consumer architecture

Consider a FastAPI-based application that processes background jobs.

You might have:

* FastAPI API running in ECS.

* SQS queue receiving background jobs.

* ECS worker containers polling SQS.

* PostgreSQL database storing results.

FastAPI Application

Receives HTTP requests

Amazon SQS

Stores background jobs

ECS Worker 1

ECS Worker 2

PostgreSQL Database

Stores processing results

### 7.2 Python SQS consumer

A simple worker can use Boto3 to poll messages.

```python
import json
import boto3
import time

sqs = boto3.client("sqs", region_name="eu-west-2")

QUEUE_URL = "YOUR_QUEUE_URL"

def process_message(body):
    order = json.loads(body)

    print(
        f"Processing order: {order['order_id']}"
    )

def run_worker():
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=10,
            WaitTimeSeconds=20,
            VisibilityTimeout=120
        )

        messages = response.get("Messages", [])

        for message in messages:
            try:
                process_message(message["Body"])

                sqs.delete_message(
                    QueueUrl=QUEUE_URL,
                    ReceiptHandle=message["ReceiptHandle"]
                )

            except Exception as exc:
                print(f"Processing failed: {exc}")

if __name__ == "__main__":
    run_worker()
```

This example demonstrates long polling and deletion after successful processing. A production implementation should also include structured logging, controlled backoff, graceful shutdown, and a strategy for extending visibility timeout when processing takes longer.

### 7.3 ECS scaling

You can scale ECS services based on SQS queue metrics.

For example:

* Minimum tasks: 2.

* Maximum tasks: 20.

* Target backlog per worker: 100 messages.

ECS Service Auto Scaling can use CloudWatch metrics and target tracking or step scaling.

For backlog-per-task scaling, you may need a custom CloudWatch metric or an appropriate metric-math approach.

The desired behavior is:

* Queue backlog increases → increase ECS tasks.

* Queue backlog decreases → reduce ECS tasks.

* Queue becomes empty → maintain minimum capacity or scale down according to your requirements.

### 7.4 ECS versus Lambda consumers

| Feature                    | Lambda                       | ECS                                        |
| -------------------------- | ---------------------------- | ------------------------------------------ |
| Execution model            | Event-driven                 | Long-running containers or scheduled tasks |
| Infrastructure management  | Highly managed               | Container infrastructure                   |
| Scaling                    | Event source mapping         | ECS Service Auto Scaling                   |
| Runtime control            | Managed runtime or container | Full container control                     |
| Long-running workloads     | Limited by function timeout  | Suitable                                   |
| Operational responsibility | Lower                        | Higher                                     |
| Best use case              | Short event processing       | Complex background workers                 |

For a FastAPI application with substantial background-processing requirements, ECS workers can be a natural choice.

### 8\. SNS-to-SQS Fanout Architectures

One of the most useful production patterns is combining Amazon SNS with SQS.

SNS provides publish/subscribe messaging, while SQS provides durable message queues for independent consumers.

This combination is called the SNS-to-SQS fanout pattern.

### 8.1 Why combine SNS and SQS?

Imagine an e-commerce application that publishes an event whenever a customer places an order.

Several independent services need to process that event:

* Inventory service.

* Payment service.

* Notification service.

* Analytics service.

One approach is to send the event separately to each service.

However, this creates tight coupling between the producer and consumers.

Instead, publish the event once to an SNS topic and subscribe multiple SQS queues.

Order Service

SNS Topic: order-events

Inventory SQS

Payment SQS

Notification SQS

Inventory Worker

Payment Worker

Notification Worker

Each consumer receives its own copy of the event.

This provides several advantages:

* Independent processing.

* Independent scaling.

* Independent retry behavior.

* Failure isolation.

* Different processing speeds.

* Reduced coupling between services.

For example, if the notification service is unavailable, inventory and payment processing can continue independently.

### 8.2 SNS subscription filtering

Not every consumer needs every event.

SNS supports subscription filter policies that allow you to route messages based on message attributes or message-body properties, depending on the subscription configuration.

Suppose an SNS topic receives:

```json
{
  "event_type": "order_created",
  "order_id": "ORD-1001",
  "region": "uk"
}
```

You could configure a subscription filter so that only certain events reach a particular SQS queue.

For example:

* UK orders → UK fulfillment queue.

* US orders → US fulfillment queue.

* Payment events → payment queue.

* Order cancellation events → cancellation queue.

This reduces unnecessary processing.

### 8.3 Important SNS-to-SQS configuration

To connect SNS and SQS correctly, you need:

* An SNS topic.

* One or more SQS queues.

* SNS subscriptions targeting those queues.

* SQS queue policies allowing the SNS topic to send messages.

* Appropriate IAM permissions for publishers and administrators.

A queue policy should restrict access to the intended SNS topic, commonly using the `aws:SourceArn` condition.

Example policy structure:

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
          "aws:SourceArn": "SNS_TOPIC_ARN"
        }
      }
    }
  ]
}
```

In a real deployment, replace the placeholders with the actual ARNs.

### 8.4 SNS versus SQS responsibilities

| SNS                             | SQS                                  |
| ------------------------------- | ------------------------------------ |
| Publishes events                | Stores messages                      |
| Distributes messages            | Makes messages available for polling |
| Supports subscriptions          | Supports independent consumers       |
| Supports subscription filtering | Supports visibility timeout          |
| Push-oriented delivery          | Pull-oriented consumption            |
| Fanout architecture             | Work distribution and buffering      |

Remember: SNS does not replace SQS. They solve complementary messaging problems.

### 9\. SQS Integration with EventBridge and Other AWS Services

SQS integrates with many AWS services. Understanding these integrations helps you build systems without tightly coupling applications.

### 9.1 EventBridge to SQS

Amazon EventBridge allows applications and AWS services to publish events to an event bus.

EventBridge rules inspect events and route matching events to configured targets, including SQS queues.

For example:

An EC2 instance changes state.

EventBridge receives the event, matches a rule, and sends the event to an SQS queue.

A worker can then process that event asynchronously.

AWS Service / Application

Produces an event

EventBridge Event Bus

Receives events

EventBridge Rule

Filters and routes events

SQS Queue

Worker / Lambda

EventBridge provides routing and event filtering. SQS provides buffering and independent message consumption.

EventBridge can also be configured with retry policies and a dead-letter queue for failed target delivery. This is separate from the SQS consumer's own retry and DLQ behavior.

### 9.2 Other important integrations

| AWS service        | Integration                                                         |
| ------------------ | ------------------------------------------------------------------- |
| AWS Lambda         | Polls SQS through event source mappings                             |
| Amazon SNS         | Publishes messages to SQS subscriptions                             |
| Amazon EventBridge | Routes events to SQS targets                                        |
| Amazon S3          | Can publish object-created notifications to SQS                     |
| Amazon ECS         | Runs container-based SQS consumers                                  |
| AWS Step Functions | Can consume messages through integrations and orchestrate workflows |
| AWS KMS            | Encrypts SQS messages                                               |
| Amazon CloudWatch  | Monitors queues and triggers alarms                                 |
| AWS CloudTrail     | Audits SQS API activity                                             |

### S3-to-SQS example

Suppose users upload documents to an S3 bucket.

You want to process each document asynchronously.

The architecture could be:

* A user uploads a document.

* S3 generates an object-created notification.

* S3 sends the notification to an SQS queue.

* A Lambda function or ECS worker receives the notification.

* The worker downloads and processes the document.

* The worker stores the result.

This is particularly useful for image processing, document conversion, data ingestion, and file validation.

Important: S3 notifications can be delivered more than once and are not guaranteed to arrive in the same order as the events occurred. Consumers should be idempotent.

### 10\. High-Availability and Multi-Consumer Architectures

Production messaging systems should be designed to remain operational even when individual application components fail.

SQS is a regional managed service designed for high availability. You do not manage its underlying queue servers or replicate queue data manually across Availability Zones.

However, your application architecture still needs careful design.

### 10.1 Multiple consumers

A queue can have multiple independent consumers.

For example:

* ECS worker 1.

* ECS worker 2.

* ECS worker 3.

* Lambda consumer.

These consumers can compete for messages from the same queue.

When one consumer receives a message, that message becomes invisible to other consumers during its visibility timeout.

This enables parallel processing.

However, competing consumers must be designed carefully:

* Standard queues can deliver messages more than once.

* FIFO queues provide ordering within message groups.

* Multiple consumers can process different FIFO message groups concurrently.

* Consumers must delete messages after successful processing.

* Visibility timeouts must accommodate processing duration.

### 10.2 Multi-AZ application architecture

A typical highly available application architecture might look like this:

Application Producers

Amazon SQS

Regional managed queue

Availability Zone A

ECS Worker 1

ECS Worker 2

Availability Zone B

ECS Worker 3

ECS Worker 4

Shared Application Database

Configured for appropriate high availability

If an Availability Zone becomes unavailable, workers in another Availability Zone can continue processing messages, assuming the remaining infrastructure and dependencies have sufficient capacity.

### 10.3 Multi-Region considerations

Multi-Region architectures require additional planning.

SQS queues are regional resources. A queue in London is not automatically replicated to a queue in another AWS Region.

If you need multi-Region resilience, you must design the replication or failover mechanism yourself.

Possible approaches include:

* Publishing events to multiple regional queues.

* Using EventBridge cross-Region event bus delivery.

* Maintaining regional producer and consumer deployments.

* Using application-level event replication.

* Designing idempotent processing across regions.

Be careful with active-active processing: the same business event might reach multiple regions, so duplicate protection becomes especially important.

### Regional failure planning

A production design should answer:

* How do producers behave if a Region becomes unavailable?

* Where will new messages be stored?

* How will existing messages be recovered?

* How will duplicate processing be prevented?

* How will the system switch back after recovery?

SQS provides regional queue durability and availability, but cross-Region disaster recovery remains an architectural responsibility.

### 11\. Cost Optimization and Production Troubleshooting

Running SQS in production requires controlling costs and identifying problems before they affect application users.

### 11.1 Understanding SQS pricing

SQS pricing is primarily based on the number of requests and certain additional features.

A request can include:

* `SendMessage`

* `ReceiveMessage`

* `DeleteMessage`

* `ChangeMessageVisibility`

* Queue-management API operations.

Batch operations can reduce request costs because one API request can process multiple messages.

For example:

| Operation          | Individual approach | Batch approach                        |
| ------------------ | ------------------- | ------------------------------------- |
| Send 10 messages   | 10 requests         | 1 request                             |
| Delete 10 messages | 10 requests         | 1 request                             |
| Receive messages   | Multiple requests   | Up to 10 messages per receive request |

The maximum number of messages in a standard SQS batch operation is generally 10.

There are also additional pricing considerations:

* FIFO queue pricing.

* Payload size and 64 KB billing chunks.

* Extended client libraries for large payloads.

* KMS requests for customer-managed encryption keys.

* CloudWatch metrics and dashboards.

* CloudTrail data events.

* Cross-Region data transfer.

Always consult the current AWS pricing page for your Region and queue type.

### 11.2 Cost optimization strategies

1\. Use long polling

Long polling reduces unnecessary empty receive requests.

```python
response = sqs.receive_message(
    QueueUrl=QUEUE_URL,
    MaxNumberOfMessages=10,
    WaitTimeSeconds=20
)
```

2\. Use batch operations

Send, receive, and delete messages in batches whenever practical.

3\. Avoid unnecessary polling

A worker that continuously polls an empty queue can generate unnecessary API requests.

4\. Select the appropriate queue type

Use Standard queues unless ordering or FIFO deduplication requirements justify FIFO queues.

5\. Optimize message payloads

Avoid sending large documents or binary data through SQS. Store the actual files in S3 and send references through SQS.

For example:

```json
{
  "event_type": "document_uploaded",
  "bucket": "company-documents",
  "key": "uploads/document-1001.pdf"
}
```

6\. Monitor KMS usage

Customer-managed KMS keys provide additional control, but encryption and decryption operations can generate additional costs.

7\. Configure retention appropriately

Do not retain messages longer than your business requirements demand.

### 11.3 Production troubleshooting

Here are common SQS production problems and their possible causes.

| Problem                      | Possible cause                                       | Investigation                            |
| ---------------------------- | ---------------------------------------------------- | ---------------------------------------- |
| Queue backlog increases      | Insufficient consumer capacity                       | Check queue depth and worker count       |
| Messages repeatedly reappear | Processing failures or visibility timeout expiration | Inspect application logs                 |
| Messages are not processed   | Consumer permissions or polling failure              | Check IAM and application logs           |
| Lambda throttling            | Insufficient concurrency                             | Inspect Lambda metrics                   |
| DLQ receives messages        | Repeated processing failures                         | Inspect DLQ and source consumer          |
| FIFO throughput is low       | Too few active message groups                        | Inspect MessageGroupId distribution      |
| Unexpected API costs         | Excessive polling                                    | Check EmptyReceives and request patterns |
| KMS access denied            | Incorrect key policy or IAM permissions              | Inspect KMS and CloudTrail events        |

### Troubleshooting scenario: Growing queue backlog

Imagine your order-processing queue normally processes 500 messages per second.

Suddenly, it drops to 100 messages per second while producers continue sending 400 messages per second.

The backlog increases by approximately 300 messages per second.

A systematic investigation would look like this:

Step 1 — Check SQS metrics

Inspect:

* `ApproximateNumberOfMessagesVisible`

* `ApproximateAgeOfOldestMessage`

* `ApproximateNumberOfMessagesNotVisible`

Step 2 — Check consumer health

For ECS, inspect:

* Running task count.

* CPU utilization.

* Memory utilization.

* Container restarts.

* Application logs.

For Lambda, inspect:

* Errors.

* Duration.

* Throttles.

* Concurrent executions.

* Iterator or event-source-related processing metrics where applicable.

Step 3 — Check downstream dependencies

The queue might not be the problem.

Your database could be overloaded, an external API might be rate-limiting requests, or your connection pool might be exhausted.

Step 4 — Check visibility timeout

If processing takes longer than the visibility timeout, messages can become visible again while the original consumer is still working.

This can lead to duplicate processing and additional load.

Step 5 — Check DLQ activity

Determine whether messages are repeatedly failing and being moved to the DLQ.

Step 6 — Apply corrective actions

Depending on the cause:

* Increase consumer capacity.

* Fix application errors.

* Increase visibility timeout where appropriate.

* Optimize database queries.

* Reduce downstream request concurrency.

* Correct IAM or KMS permissions.

* Reprocess DLQ messages after fixing the underlying issue.

The key lesson is that increasing consumer count is not always the right solution. First identify the actual bottleneck.

### 12\. Infrastructure Management and Production Deployments with Pulumi

The final part of this course brings SQS infrastructure management into Infrastructure as Code.

We'll use Pulumi with Python to define and deploy production SQS resources.

This approach allows you to manage queues, policies, encryption, subscriptions, alarms, and other infrastructure through version-controlled code.

### 12.1 What should Pulumi manage?

A production SQS deployment might contain:

| Resource             | Purpose                             |
| -------------------- | ----------------------------------- |
| SQS Standard queue   | Main application queue              |
| SQS DLQ              | Failed-message isolation            |
| Queue redrive policy | Controls automatic failure handling |
| Queue encryption     | Protects message contents           |
| IAM policies         | Controls application access         |
| Queue policies       | Controls resource-level access      |
| SNS topic            | Publishes application events        |
| SNS subscriptions    | Connects SNS to SQS                 |
| CloudWatch alarms    | Detects operational problems        |
| CloudWatch dashboard | Displays queue health               |

### 12.2 Pulumi project structure

A simple project might look like:

```text
sqs-infrastructure/
│
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── Pulumi.prod.yaml
│
├── __main__.py
├── requirements.txt
│
└── components/
    └── queues.py
```

You can use separate Pulumi stacks for development, staging, and production.

For example:

```bash
pulumi stack init dev
pulumi stack init staging
pulumi stack init prod
```

### 12.3 Creating an SQS queue with Pulumi

Let's create a production-style Standard queue and its DLQ.

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

environment = pulumi.get_stack()

dlq = aws.sqs.Queue(
    "orders-dlq",
    name=f"orders-dlq-{environment}",
    message_retention_seconds=1209600,
    sqs_managed_sse_enabled=True,
)

queue = aws.sqs.Queue(
    "orders-queue",
    name=f"orders-{environment}",
    visibility_timeout_seconds=180,
    message_retention_seconds=345600,
    receive_wait_time_seconds=20,
    sqs_managed_sse_enabled=True,
    redrive_policy=pulumi.Output.json_dumps({
        "deadLetterTargetArn": dlq.arn,
        "maxReceiveCount": 5,
    }),
)

pulumi.export("queue_url", queue.url)
pulumi.export("queue_arn", queue.arn)
pulumi.export("dlq_url", dlq.url)
```

A few important details:

* The DLQ retains messages for up to 14 days.

* The source queue retains messages for four days.

* Consumers have a 180-second visibility timeout.

* Long polling is enabled with a 20-second wait.

* Server-side encryption uses SQS-managed encryption keys.

* Messages are moved to the DLQ after reaching the configured receive threshold.

The redrive policy determines when messages are moved to the DLQ. It does not automatically make failed messages successful or reprocess them.

### 12.4 Adding a CloudWatch alarm

Now let's monitor the queue backlog.

```python
alarm = aws.cloudwatch.MetricAlarm(
    "orders-queue-backlog",
    name=f"orders-backlog-{environment}",
    namespace="AWS/SQS",
    metric_name="ApproximateNumberOfMessagesVisible",
    dimensions={
        "QueueName": queue.name,
    },
    statistic="Average",
    period=60,
    evaluation_periods=5,
    datapoints_to_alarm=3,
    threshold=1000,
    comparison_operator="GreaterThanThreshold",
    treat_missing_data="notBreaching",
)
```

This alarm detects when the average visible-message count exceeds 1,000 for at least three of five one-minute evaluation periods.

For production, you would generally add another alarm for message age and one for DLQ activity.

### 12.5 Deploying the infrastructure

Use Pulumi's normal deployment workflow:

```bash
pulumi preview
pulumi up
```

To inspect the deployed resources:

```bash
pulumi stack output
```

To remove the infrastructure when it is no longer required:

```bash
pulumi destroy
```

For production deployments, use CI/CD, reviewed changes, protected stack configuration, and appropriate deployment permissions.

Important: Protect production queues and DLQs against accidental deletion. Queue deletion can permanently remove messages, and recreating a queue with the same name does not restore its previous contents.

### 13\. Putting Everything Together: Production E-Commerce Architecture

Let's finish the SQS course by combining the concepts from all six modules.

Imagine we are building an e-commerce platform with the following requirements:

* Customers place orders through a FastAPI application.

* Orders must be processed asynchronously.

* Inventory and payment operations must be independent.

* Notifications should be delivered asynchronously.

* Failed messages must be isolated.

* Consumers should scale automatically.

* The infrastructure should be managed with Pulumi.

* The system should provide operational monitoring.

### Complete architecture

![Decoupling at Scale: My Deep Dive into AWS Event-Driven Architecture (API Gateway, EventBridge, SQS) - DEV Community](https://images.openai.com/static-rsc-4/c_Fjxl1gdH6Jw-ARtMcAtXy22Xs0HmjWDb4JwbPD6OZcGd-q2PHaq5ak_62rFia_8TMabgksaw_B2RaGoW7lS6xk7cs7bg2KxnlfuDYIb1r_COjL8BgKl0BhjF8cjc4ZfZLfUMw7V1Jg973UXbmjem-CXM6MTZPfK8Wox9lH7jBL1jH_7euwodHvv2e5hGyw?purpose=fullsize)

The architecture can be organized as follows:

| Component        | Responsibility                      |
| ---------------- | ----------------------------------- |
| FastAPI on ECS   | Accepts customer orders             |
| SNS topic        | Publishes order events              |
| Inventory SQS    | Buffers inventory operations        |
| Payment SQS      | Buffers payment operations          |
| Notification SQS | Buffers notification operations     |
| ECS workers      | Process inventory and payment jobs  |
| Lambda           | Processes notification jobs         |
| DLQs             | Isolate repeatedly failing messages |
| CloudWatch       | Monitors queues and consumers       |
| CloudTrail       | Audits API activity                 |
| Pulumi           | Manages AWS infrastructure          |

### Order-processing flow

* A customer places an order.

* FastAPI validates the request and persists the order.

* The application publishes an `order_created` event to SNS.

* SNS distributes the event to the subscribed SQS queues.

* Inventory and payment workers independently retrieve their messages.

* Lambda retrieves notification messages.

* Each consumer processes its messages and deletes successful messages.

* Failed messages are retried and eventually moved to their DLQs according to their redrive policies.

* CloudWatch monitors processing health and queue backlogs.

* Pulumi manages the underlying infrastructure.

### Important production design consideration

SNS fanout does not guarantee that inventory, payment, and notification operations happen in a particular order.

If the business requires coordinated order processing, you need an additional orchestration or state-management mechanism.

For example, a payment operation should not necessarily execute before the order has passed the required validation and inventory checks.

You can use Step Functions, application-level state transitions, or another orchestration approach to manage these dependencies.

### Final Module Summary

By completing this module, you should understand how to operate SQS as part of a production-grade event-driven system.

| Topic             | Main concepts                                       |
| ----------------- | --------------------------------------------------- |
| CloudWatch        | Metrics, monitoring, alarms, dashboards             |
| Queue metrics     | Depth, age, throughput                              |
| CloudTrail        | Management and data events                          |
| Scaling           | Horizontal scaling, backlog-based scaling           |
| Lambda            | Event source mappings, batch processing             |
| ECS               | Container-based consumers and autoscaling           |
| SNS               | Fanout, subscriptions, filtering                    |
| EventBridge       | Event routing and asynchronous delivery             |
| High availability | Multi-consumer and multi-AZ architectures           |
| Cost optimization | Long polling, batching, payload optimization        |
| Troubleshooting   | Backlogs, retries, throttling, permissions          |
| Pulumi            | Infrastructure management and production deployment |

### SQS course completed

6 of 6 modules completed

You have now covered the complete SQS learning path, from basic queue architecture to production integrations and infrastructure management.

The most important architectural concepts to carry forward:

* SQS decouples producers and consumers.

* Standard queues provide at-least-once delivery, so consumers must handle duplicates.

* FIFO queues provide ordering within message groups, not universal global ordering across all groups.

* Visibility timeout, retries, and DLQs are fundamental to reliability.

* Lambda and ECS provide different approaches to consumer processing.

* SNS and SQS together enable scalable event fanout.

* CloudWatch and CloudTrail serve complementary operational and auditing purposes.

* Pulumi allows you to manage messaging infrastructure consistently across environments.

Next step: We can move on to the Amazon SNS course, using the same six-module structure and Pulumi-first approach, building on the SQS concepts you've just learned.
