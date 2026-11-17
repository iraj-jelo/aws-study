Worked for 46s

### Module 6 — SNS Monitoring, Integrations, Scaling, and Production Architectures

Amazon Simple Notification Service (SNS) · Advanced / Production Level

This module brings together everything we've learned about SNS, SQS, and Lambda.

So far, we've covered how to create SNS topics, publish messages, manage subscriptions, filter messages, configure FIFO topics, handle delivery failures, and secure messaging systems.

Now we'll focus on operating SNS in production environments.

The central questions are:

* How do we know whether SNS is delivering messages successfully?

* How do we detect failed notifications?

* How do we integrate SNS with other AWS services?

* How do we distribute events to multiple independent consumers?

* How do we design scalable, reliable event-driven architectures?

* How do we monitor costs and troubleshoot production problems?

### 1\. CloudWatch Metrics and Monitoring

Amazon SNS integrates with Amazon CloudWatch to provide operational metrics.

CloudWatch collects SNS metrics automatically, allowing us to monitor topic activity, message delivery, and potential failures.

### 1.1 SNS CloudWatch metrics

SNS publishes metrics under the following namespace:

```text
AWS/SNS
```

Metrics are generally available at the topic level, with dimensions such as `TopicName`.

Some important metrics include:

| Metric                                             | Description                                                   |
| -------------------------------------------------- | ------------------------------------------------------------- |
| NumberOfMessagesPublished                          | Number of messages published to a topic.                      |
| NumberOfNotificationsDelivered                     | Number of notifications successfully delivered to endpoints.  |
| NumberOfNotificationsFailed                        | Number of notifications that failed delivery.                 |
| NumberOfNotificationsFilteredOut                   | Messages excluded by subscription filter policies.            |
| NumberOfNotificationsFilteredOut-InvalidAttributes | Messages filtered because of invalid message attributes.      |
| PublishSize                                        | Size of published messages.                                   |
| NumberOfMessagesDelivered                          | Messages delivered to subscribed endpoints, where applicable. |

Some metrics are specific to particular protocols or delivery configurations. Also, metric availability and dimensions can differ by SNS topic type and subscription protocol.

An important distinction:

Published messages are not necessarily equal to delivered notifications.

For example, imagine an SNS topic with three subscriptions:

* SQS queue A

* SQS queue B

* Lambda function C

If an application publishes 100 messages and all three subscriptions receive every message:

* Published messages: 100

* Delivered notifications: approximately 300

Each subscription represents a separate delivery.

### 1.2 Monitoring message delivery failures

Suppose an application publishes messages successfully, but an HTTP subscriber is unavailable.

SNS might accept the publication successfully while the subsequent delivery attempts fail.

This means:

* The publishing operation can succeed.

* The subscriber delivery can fail.

* The publisher might not immediately know that delivery failed.

This distinction is essential when designing production notification systems.

You should monitor both publishing activity and downstream delivery.

### 1.3 Monitoring with AWS CLI

You can retrieve SNS metrics using CloudWatch through AWS CLI.

For example:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/SNS \
  --metric-name NumberOfMessagesPublished \
  --dimensions Name=TopicName,Value=orders-topic \
  --start-time 2026-11-03T00:00:00Z \
  --end-time 2026-11-04T00:00:00Z \
  --period 300 \
  --statistics Sum
```

To monitor failed notifications:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/SNS \
  --metric-name NumberOfNotificationsFailed \
  --dimensions Name=TopicName,Value=orders-topic \
  --start-time 2026-11-03T00:00:00Z \
  --end-time 2026-11-04T00:00:00Z \
  --period 300 \
  --statistics Sum
```

These commands retrieve five-minute aggregated statistics over the specified period.

Note that SNS metrics are published to CloudWatch periodically, so they are not instantaneous delivery confirmations.

### 2\. CloudWatch Alarms and Dashboards

Collecting metrics is useful, but production systems also need automated monitoring.

We can create CloudWatch alarms to detect abnormal SNS behavior.

### 2.1 Creating a CloudWatch alarm

Imagine an application that publishes order notifications to an SNS topic.

We want an alarm whenever notification delivery failures occur.

Using AWS CLI:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name sns-delivery-failures \
  --namespace AWS/SNS \
  --metric-name NumberOfNotificationsFailed \
  --dimensions Name=TopicName,Value=orders-topic \
  --statistic Sum \
  --period 300 \
  --evaluation-periods 1 \
  --threshold 0 \
  --comparison-operator GreaterThanThreshold \
  --alarm-actions arn:aws:sns:us-east-1:123456789012:alerts-topic
```

This alarm monitors failed notifications.

If the metric exceeds zero during a five-minute period, CloudWatch transitions the alarm into the ALARM state and publishes a notification to the configured alerts topic.

Notice something interesting:

We are using SNS to monitor SNS!

This is a common AWS architecture. One SNS topic can distribute application events, while another topic distributes operational alerts.

### 2.2 What should we monitor?

A useful production monitoring strategy includes:

| Monitoring objective   | Metric or signal                   |
| ---------------------- | ---------------------------------- |
| Publishing activity    | NumberOfMessagesPublished          |
| Delivery activity      | NumberOfNotificationsDelivered     |
| Delivery failures      | NumberOfNotificationsFailed        |
| Filtering behavior     | NumberOfNotificationsFilteredOut   |
| Message size           | PublishSize                        |
| Application processing | SQS and Lambda metrics             |
| End-to-end failures    | Application-level metrics and logs |

One important point: SNS metrics alone cannot tell you whether a downstream business operation completed successfully.

For example, SNS might successfully deliver a message to SQS, but the Lambda consumer could fail while processing it.

Therefore, monitor the entire messaging pipeline.

### 2.3 CloudWatch dashboards

A CloudWatch dashboard can combine metrics from multiple services.

For an architecture using SNS, SQS, and Lambda, a useful dashboard might contain:

* SNS published messages.

* SNS delivered notifications.

* SNS delivery failures.

* SQS ApproximateNumberOfMessagesVisible.

* SQS ApproximateAgeOfOldestMessage.

* Lambda Invocations.

* Lambda Errors.

* Lambda Duration.

* Lambda Throttles.

This provides a unified view of the event-processing pipeline.

### 3\. CloudTrail Auditing and API Activity

CloudWatch answers questions about system behavior.

CloudTrail answers questions about API activity.

AWS CloudTrail records SNS management operations and API activity.

Examples include:

* CreateTopic

* DeleteTopic

* Subscribe

* Unsubscribe

* SetTopicAttributes

* SetSubscriptionAttributes

* AddPermission

* RemovePermission

* Publish

CloudTrail helps answer questions such as:

* Who created an SNS topic?

* Who modified a topic policy?

* Which identity published a message?

* When was a subscription deleted?

* Which IAM role changed the configuration?

### 3.1 Management events versus data events

An important distinction:

Management events record control-plane operations, such as creating topics and modifying permissions.

SNS publishing activity (`Publish`) can be captured through CloudTrail data events when supported and configured for the relevant resource.

Data events are not generally enabled by default and can incur additional charges.

For example, you may want to audit all publishing activity to a sensitive notification topic.

You can configure a CloudTrail trail or event data store to capture the relevant events.

### 3.2 Example CloudTrail event

A simplified Publish event might contain:

```json
{
  "eventSource": "sns.amazonaws.com",
  "eventName": "Publish",
  "awsRegion": "us-east-1",
  "userIdentity": {
    "type": "AssumedRole"
  },
  "requestParameters": {
    "topicArn": "arn:aws:sns:us-east-1:123456789012:orders-topic"
  }
}
```

This helps security and operations teams understand who performed an operation and which resource was involved.

CloudTrail versus CloudWatch:

| CloudWatch                | CloudTrail                       |
| ------------------------- | -------------------------------- |
| Operational monitoring    | API auditing                     |
| Tracks metrics            | Tracks API activity              |
| Detects delivery failures | Identifies who changed resources |
| Creates metric alarms     | Supports security investigations |

### 4\. SNS Delivery Status Logging

CloudWatch metrics tell us how many notifications succeeded or failed.

However, sometimes we need more detailed information about individual delivery attempts.

For this purpose, SNS provides Delivery Status Logging.

SNS can send delivery status information to CloudWatch Logs for supported subscription protocols.

Supported endpoints include:

* Amazon SQS

* AWS Lambda

* HTTP/HTTPS

* Amazon Data Firehose

* Mobile push platform applications

Email subscriptions do not support SNS delivery status logging. Amazon Simple Notification Service +1

### 4.1 What information does delivery logging provide?

For example, suppose SNS publishes an order notification to an SQS queue.

We can investigate:

* Whether SNS successfully delivered the notification.

* The endpoint response.

* The delivery attempt status.

* The time between publishing and handing off the message to the endpoint.

* The reason for a delivery failure.

This is especially useful when investigating problems that are invisible from the publisher's perspective.

### 4.2 Configuring delivery status logging

SNS uses IAM roles to obtain permission to write delivery logs to CloudWatch Logs.

For example, the logging role needs permissions such as:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

You configure delivery status logging on the SNS topic, selecting the protocols and configuring success sampling.

Failed deliveries are logged, while successful deliveries can be sampled.

The default log group naming convention is:

```text
sns/<region>/<account-id>/<topic-name>
```

For example:

```text
sns/us-east-1/123456789012/orders-topic
```

Amazon Simple Notification Service +1

### 4.3 Why sample successful deliveries?

Imagine an SNS topic delivering 10 million notifications per day.

Logging every successful delivery could generate a considerable amount of log data.

Instead, you might configure:

* Failed deliveries: 100% logging.

* Successful deliveries: 5% sampling.

This gives you visibility into failures without generating unnecessary logs for every successful message.

### 5\. SNS Integration with AWS Lambda

One of the most important SNS integrations is with AWS Lambda.

SNS can invoke a Lambda function whenever a message is published to a subscribed topic.

This creates a push-based, event-driven processing architecture.

### 5.1 Architecture

![Simplify Your Pub/Sub Messaging with Amazon SNS Message Filtering | AWS Compute Blog](https://images.openai.com/static-rsc-4/577Ld5IyJxSgT0uKERXHIxWSgHBjWHvdGqF61ftHCh-U6YyqXdlADkhiRiGAhSR5dM_CxUVRiaRjXO7KBodN9YWp3HK6Jhb9uQAeoeAMev98rjrOvbRUOZBLiRfj4Tlerm5293jfkYqE1A9HsRLm1_P-PVpyhaC-x20UWGvBopZoOzWFO3lfHNmAP2ZIFJ6a?purpose=fullsize)

The sequence is:

* An application publishes a message to SNS.

* SNS identifies the subscribed Lambda function.

* SNS sends the notification to Lambda.

* Lambda receives the message in its event object.

* Lambda executes its handler.

* The function processes the event.

For example, an e-commerce application publishes an order-created event.

A Lambda function subscribed to the topic sends an order confirmation email or updates another application component.

### 5.2 Lambda event structure

When SNS invokes Lambda, the event contains an `Records` array.

A simplified event looks like this:

```json
{
  "Records": [
    {
      "EventSource": "aws:sns",
      "Sns": {
        "MessageId": "example-message-id",
        "TopicArn": "arn:aws:sns:us-east-1:123456789012:orders-topic",
        "Message": "{\"order_id\":\"ORD-1001\",\"amount\":250}"
      }
    }
  ]
}
```

The actual SNS event also contains fields such as timestamps, message attributes, and the subject when provided.

### 5.3 Python Lambda example

```python
import json

def lambda_handler(event, context):

    for record in event["Records"]:

        sns_message = record["Sns"]["Message"]

        order = json.loads(sns_message)

        order_id = order["order_id"]
        amount = order["amount"]

        print(f"Processing order: {order_id}")
        print(f"Amount: {amount}")

    return {
        "statusCode": 200,
        "body": "Orders processed"
    }
```

This function processes every SNS record supplied in the invocation.

### 5.4 Important: SNS-to-Lambda is different from SQS-to-Lambda

We already studied both services, so let's compare their integration models.

SNS → Lambda

![Amazon SNS vs. Amazon SQS: A simple comparison | Shikisoft Blog](https://images.openai.com/static-rsc-4/QIaG1V16eerCPvWUadvwbBSYVUJVPSGfo7UXaS4sGlLmO8lpjcIz0bbhmf_rWxqCPb0GSCd3RBVWpJI1Cij-9H-vE1nwq2lKT4wf3k3B-FHdYkH18-tVPNFRnHJkXcK8bM8265_PL3PA85Eo-CoZxY2JU1CFCSshSbTGYcIJ9H5REdiDsQZR6L9bQIS_Nrr6?purpose=fullsize)

* Push-based invocation.

* SNS delivers notifications directly.

* SNS manages delivery retries.

* Subscription DLQ can capture messages that SNS cannot deliver.

    SQS → Lambda

    ![The Essential Guide to Amazon SQS | Baselime Blog](https://images.openai.com/static-rsc-4/4ryjXbO7OehqPi_J_8_jWRRPQiTjhRjs_AWUIx5N42tC6S3_s4KmWI3zQ7TjxMdLZI46pxqGN0kqXQYOPxWgrPlmvG_wLlRqWyo8pjYD33dwMEUcdX9LPWxa3D0AX7e_K2OMDeMahCib_ldBnf-H11wYsz-kYZFshYR5vYb3lg-P4LwhjAl_3K6CxxbcySv-?purpose=fullsize)

* Lambda event source mapping polls SQS.

* Messages remain in the queue until successfully deleted or otherwise handled.

* Visibility timeout controls message availability.

* Failed processing can result in redelivery and eventually an SQS DLQ.

This distinction is important:

SNS handles notification delivery; SQS provides message storage and consumer-controlled processing.

For workloads requiring buffering, independent consumer scaling, and stronger control over processing, SNS → SQS → Lambda is often preferable.

### 6\. SNS Integration with Amazon SQS

This is arguably the most important SNS integration for distributed systems.

SNS and SQS complement each other.

* SNS distributes messages.

* SQS stores messages until consumers process them.

### 6.1 Basic architecture

![Mastering AWS SQS + SNS: Scalable, Event-Driven Architectures with Spring Boot ☁️ | by Anderson Kuntz Meurer | Medium](https://images.openai.com/static-rsc-4/7mQfQS7xiag3Zsh8SRnum8GH5f1eXJl1mNJKgElPQsKmPfuz0fZRNPfZs6msw-diMlmGvwSOR386qIWFDCCoxWn1K6BrysdGrGiEkTw-vFXLD9P8oCnPfwmaR6KcAvwJNA803rs0SmyrjUV7TjNbaFc_j8Fy66n3lmPiHtD2kMrSnEx8v1y9HBCROlr3KenV?purpose=fullsize)

Imagine an application that receives customer orders.

When an order is created, it publishes an event to an SNS topic.

An SQS queue subscribes to that topic.

SNS delivers a copy of the notification to SQS, where it remains available until a consumer processes it.

### 6.2 Why combine SNS and SQS?

Consider what happens if your consumer application becomes unavailable.

With direct SNS-to-Lambda integration, SNS handles delivery retries, but it does not provide a general-purpose message buffer that your consumer can poll at its own pace.

With SQS:

* SNS publishes the notification to the queue.

* SQS stores the message.

* The consumer can temporarily become unavailable.

* The message remains in the queue.

* The consumer processes it when it becomes available again.

This provides buffering and helps absorb traffic spikes.

### 6.3 Important configuration requirements

To subscribe an SQS queue to an SNS topic, you need:

* An SNS topic.

* An SQS queue.

* An SNS subscription connecting them.

* An SQS queue policy allowing the SNS topic to send messages.

A simplified queue policy looks like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSNSTopic",
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:us-east-1:123456789012:orders-queue",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "arn:aws:sns:us-east-1:123456789012:orders-topic"
        }
      }
    }
  ]
}
```

The `aws:SourceArn` condition restricts the permission to the intended SNS topic.

For production environments, this is an important security control.

### 7\. SNS-to-SQS Fanout Architecture

Now let's expand the previous architecture.

What if multiple independent applications need to receive the same event?

For example, after an order is created:

* The inventory service updates stock.

* The payment service processes payment.

* The shipping service prepares delivery.

* The analytics service records the transaction.

* The notification service sends an email.

We don't want the order service to communicate directly with all these applications.

Instead, we can use SNS fanout.

### 7.1 Architecture

![Startup Ground to Cloud: Launching Fanout Pattern to AWS Cloud - Post | Triglon Technologies | Triglon](https://images.openai.com/static-rsc-4/J2zgZDStw1viozhA_OSD18GuSc3RZj5WAYBbRgNprdJdqmI_mL_9xsZefg83sbj1cTi5KPxQeexFMA7MYl3WhHMvnI08NB2oam7ljT8aKC_OScMp3nT1XKKccFQeWsLDOju9Kljwuln5MAwrrljxBHgtjhB4dRU6ABM4jp9LSc8yYjg1X_Rk3qI5qK1dheXQ?purpose=fullsize)

The architecture:

```text
             Order Service
                   |
                   v
              SNS Topic
                   |
       +-----------+-----------+
       |           |           |
       v           v           v
   SQS Queue    SQS Queue   SQS Queue
   Inventory    Payment     Shipping
       |           |           |
       v           v           v
   Consumer     Consumer    Consumer
   Lambda       Lambda      Lambda
```

We can add as many independent subscribers as our architecture requires, subject to SNS quotas.

### 7.2 Why is fanout powerful?

Consider a traditional architecture:

```text
Order Service
   |
   +----> Inventory Service
   |
   +----> Payment Service
   |
   +----> Shipping Service
   |
   +----> Analytics Service
```

The order service must know about every downstream service.

This creates tight coupling.

With SNS:

```text
Order Service
      |
      v
  SNS Topic
      |
      +----> Inventory Queue
      |
      +----> Payment Queue
      |
      +----> Shipping Queue
      |
      +----> Analytics Queue
```

Now the order service only needs to know about the SNS topic.

New consumers can subscribe without changing the order service.

### 7.3 Independent processing

Each queue has its own:

* Consumer application.

* Processing capacity.

* Visibility timeout.

* Retention period.

* Redrive policy.

* Dead-letter queue.

For example, shipping might process orders slowly, while analytics processes them quickly.

Neither consumer needs to control the processing speed of the other.

### 7.4 Message filtering in fanout

We can combine this architecture with Module 3's subscription filter policies.

For example:

| Subscription               | Filter                   |
| -------------------------- | ------------------------ |
| Inventory queue            | All order-created events |
| Shipping queue             | order_status = PAID      |
| Analytics queue            | All order events         |
| Premium notification queue | customer_tier = PREMIUM  |

SNS evaluates the filter policy separately for each subscription.

This prevents unnecessary message delivery and reduces downstream processing.

AWS identifies fanout as a key SNS application-to-application messaging pattern. Amazon Web Services, Inc. +1

### 8\. SNS Integration with Amazon EventBridge

Amazon EventBridge and SNS are both important components of event-driven architectures, but they solve somewhat different problems.

### 8.1 SNS versus EventBridge

| Feature         | SNS                             | EventBridge                        |
| --------------- | ------------------------------- | ---------------------------------- |
| Main purpose    | Pub/sub messaging               | Event routing                      |
| Distribution    | Topic subscriptions             | Event bus rules                    |
| Filtering       | Subscription filter policies    | Event pattern matching             |
| Routing         | Subscribers                     | Multiple rule targets              |
| Common use      | Fanout notifications            | Routing application and AWS events |
| Schema registry | No equivalent built-in registry | EventBridge schema registry        |

SNS is particularly useful when you want to publish a message and distribute it to multiple subscribers.

EventBridge is particularly useful when you want to match events against rules and route them to different targets.

### 8.2 EventBridge → SNS

A common architecture uses EventBridge as the event router and SNS as a notification distribution service.

![AWS EventBridge: Pricing Guide](https://images.openai.com/static-rsc-4/e3aW7zUZkumE47nkOtKd7uukbWpwmB1eK9Boii6OYmK8x-LW2o2EEPD2N9UNzz5c0W0zD6tAg1qRdRC174iB_yayj2Yart0oUME98N1OXza45_THcIdjfDdIwHgHvakVj-iRyewFCsnMj6MKIpvhp0DMDNG7azfIFHVkbByVZfc8Mx2eVUj8ZNGF5Cb9JfhB?purpose=fullsize)

Example:

An application publishes an event:

```json
{
  "source": "shop.orders",
  "detail-type": "OrderFailed",
  "detail": {
    "order_id": "ORD-1001",
    "reason": "Payment declined"
  }
}
```

EventBridge receives the event and evaluates its rules.

A rule might match:

```json
{
  "source": ["shop.orders"],
  "detail-type": ["OrderFailed"]
}
```

The rule sends matching events to an SNS topic.

SNS then distributes the notification to:

* An operations email subscription.

* An SQS queue.

* A Lambda function.

* An HTTP endpoint.

This separates event routing from notification distribution.

### 8.3 When should we use each?

Use SNS when you need straightforward pub/sub distribution and fanout.

Use EventBridge when you need sophisticated event matching, routing, integration with AWS events, and event-driven workflows.

You can also use both together.

Important: SNS and EventBridge are not interchangeable. EventBridge is not simply an SNS replacement.

### 9\. SNS Integration with Amazon S3 and Other AWS Services

SNS can receive notifications from several AWS services.

One important example is Amazon S3.

### 9.1 S3 → SNS

Imagine an application where customers upload documents to an S3 bucket.

Whenever a new object is created, S3 can publish an event notification to SNS.

![Mastering Amazon S3 Pricing: Cost Optimization Strategies](https://images.openai.com/static-rsc-4/5IvybTxfsDJvoAy7IcQGlIfcpcknr9tstDXayX8uk-36TVf_KaSMiLemWTGVLJvFoCSXnI73L6xv4EWYQ2KhKSACw-ScKQo_NcLbFKV5a_1h6oYjZjG2UL3ddI0ZYhjVU-DZLasG8OiAqgzWAsTzeCvFsfehFpEAYIaLPppz7hUBigfbYrvR_J_tlEtLLIem?purpose=fullsize)

The flow:

* A customer uploads a document.

* S3 detects an object-created event.

* S3 sends an event notification to SNS.

* SNS distributes the notification to subscribers.

* Subscribers process the uploaded object.

For example:

* Lambda generates a thumbnail.

* SQS stores document-processing tasks.

* An HTTP endpoint notifies an external application.

### 9.2 Important S3 configuration requirements

For direct S3-to-SNS notifications:

* The SNS topic must be in the same AWS Region as the S3 bucket.

* The SNS topic policy must allow the S3 service principal to publish.

* The topic policy should restrict access using the source bucket ARN and account.

* The SNS topic must be a supported Standard topic; S3 event notifications do not directly target SNS FIFO topics.

An example topic policy statement:

```json
{
  "Effect": "Allow",
  "Principal": {
    "Service": "s3.amazonaws.com"
  },
  "Action": "sns:Publish",
  "Resource": "arn:aws:sns:us-east-1:123456789012:document-events",
  "Condition": {
    "ArnEquals": {
      "aws:SourceArn": "arn:aws:s3:::my-document-bucket"
    },
    "StringEquals": {
      "aws:SourceAccount": "123456789012"
    }
  }
}
```

### 9.3 Other AWS integrations

SNS can also be used with several other AWS services.

| AWS service                            | Integration                                                        |
| -------------------------------------- | ------------------------------------------------------------------ |
| Amazon S3                              | Object-created and object-deleted notifications                    |
| Amazon CloudWatch                      | Alarm notifications                                                |
| Amazon CloudWatch Events / EventBridge | Event routing to SNS                                               |
| AWS Lambda                             | Direct function invocation                                         |
| Amazon SQS                             | Message distribution and buffering                                 |
| Amazon Data Firehose                   | Streaming delivery                                                 |
| AWS CodePipeline                       | Pipeline notifications through supported integrations              |
| AWS Budgets                            | Budget notifications through supported notification configurations |

A useful design principle is to select the service that produces the event, the service that distributes it, and the service that processes it according to their responsibilities.

### 10\. Multi-Account Messaging Architectures

Larger organizations often use multiple AWS accounts.

For example:

* Development account.

* Staging account.

* Production account.

* Security account.

* Analytics account.

Sometimes applications in different accounts need to receive the same events.

SNS supports cross-account messaging.

### 10.1 Cross-account SNS → SQS

![Coordinating large messages across accounts and Regions with Amazon SNS and SQS | AWS Architecture Blog](https://images.openai.com/static-rsc-4/hf498ryBqohB72nho7B-jxGwKaW0vXxERoNXjukzdQDQLCJDU09vc2RAcAPBBtCaAXYyuwLAeIYQJYbv1G4p2-RNS6n9DKfS4I5AQUC0MaTJeruCVUWrudoEa5w0fccFFo9jaNHQXfnzv514O4Wxgveypdiy6pRQSbl9z3L6wGAotb_SBpyLL2IORrNUl_b2?purpose=fullsize)

Consider:

* Account A owns the SNS topic.

* Account B owns the SQS queue.

Account A publishes an order event.

SNS delivers the message to the SQS queue in Account B.

This requires appropriate permissions on the receiving queue.

The queue policy must authorize the SNS topic to send messages.

The architecture should also use least-privilege permissions and restrict the source ARN.

### 10.2 Cross-account SNS → Lambda

A similar pattern works with Lambda.

Account A owns the SNS topic.

Account B owns the Lambda function.

The Lambda resource-based policy must permit the SNS service to invoke the function.

For example, using AWS CLI:

```bash
aws lambda add-permission \
  --function-name process-orders \
  --statement-id AllowOrdersTopic \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:us-east-1:111111111111:orders-topic
```

The subscription is created in the SNS topic's account and Region.

This pattern allows centralized event distribution while keeping application services in separate accounts.

### 11\. Cross-Region Messaging Architectures

SNS also supports delivery to SQS queues and Lambda functions in different AWS Regions.

For example:

* SNS topic in `us-east-1`.

* SQS queue in `us-west-2`.

* Lambda function in `eu-west-1`.

![🚀 Amazon SNS Boosts Cross-Region Delivery Flexibility! - DEV Community](https://images.openai.com/static-rsc-4/FHqbYHsp0CiK2CkvSlLRRw7Kri_Srya9O3kr2nqMUxEaxrePZrrJeLWK9j-4HkYe9TLNuPgtxeunWpj4n2sFE9vwP09D2pN4yh1OP1H_FX8OqttwzLv_PhoAJcljYouLBX4KNz-gteQDXXsN8rcIzHppJjvj9ivDLvwBU79ShdP0iUseAXutZU3Ia_276Nkv?purpose=fullsize)

This can be useful for:

* Geographically distributed applications.

* Regional processing systems.

* Centralized event distribution.

* Disaster recovery architectures.

Cross-Region delivery requires correct resource policies and subscription configuration. For opt-in Regions, the appropriate regional SNS service principal must be used.

Amazon Simple Notification Service +1

### 11.1 Important architectural consideration

Cross-Region messaging introduces additional concerns:

* Network and data-transfer costs.

* Regional service availability.

* Delivery latency.

* Regional quotas.

* Data residency requirements.

* Independent monitoring across Regions.

Also, cross-Region delivery alone does not provide complete disaster recovery.

For critical applications, you need to consider how events are published, retained, recovered, and processed if an entire Region becomes unavailable.

### 12\. Scaling SNS for High-Throughput Applications

SNS is designed to distribute messages across large numbers of subscribers.

However, designing a scalable system requires more than choosing an SNS topic.

We need to consider:

* Publishing throughput.

* Subscription delivery throughput.

* Consumer processing capacity.

* Message size.

* Service quotas.

* Downstream throttling.

* Regional limitations.

### 12.1 Scaling publishers

Suppose an e-commerce application normally publishes 100 messages per second.

During a seasonal promotion, traffic increases to 10,000 messages per second.

The publishing application must be able to handle this increase.

A good approach includes:

* Reusing SDK clients rather than repeatedly creating them.

* Using appropriate SDK retry behavior.

* Monitoring SNS publishing throttles.

* Distributing workloads across suitable topics when justified.

* Requesting quota increases when necessary.

SNS supports message batching through `PublishBatch` for applicable topic types, allowing multiple messages to be published in one API request.

### 12.2 Scaling subscribers

Consider an SNS topic with four SQS subscriptions.

Each queue has its own consumer group.

![Amazon SNS vs. Amazon SQS: A simple comparison | Shikisoft Blog](https://images.openai.com/static-rsc-4/xp-eGacF8UCGhvWKmjsU3Otrh0XR1TjWpjAKtZcqjtSSpiUqBdLqDd27_H5KmQd54hJ3volsTvglvIJ29Wyn0IDo8PT2wuY4nz-dFE5TdfIp9eWtXu1Ml-2AqGy6zqaA3T7whPbq-kSTSnnbloeyuODDb12oqOa2cNmwY__I9j38d_VaSlR0C6KAy4kSi4tm?purpose=fullsize)

We can scale each consumer independently.

For example:

| Consumer  | Processing requirement | Scaling strategy            |
| --------- | ---------------------- | --------------------------- |
| Inventory | Medium                 | ECS autoscaling             |
| Payments  | High reliability       | Lambda concurrency controls |
| Shipping  | Variable               | ECS or Lambda               |
| Analytics | High throughput        | SQS and Lambda              |

This is one of the strongest advantages of SNS-to-SQS fanout.

Each downstream application can scale according to its own workload.

### 12.3 Monitoring throttling

Imagine SNS delivers messages to a Lambda function, but the function reaches its concurrency limit.

Lambda may throttle incoming invocations.

SNS retries delivery according to its delivery policy.

If the problem continues, SNS can eventually exhaust its delivery attempts.

This is why we need to monitor both SNS delivery failures and Lambda throttling.

The same principle applies to other subscribers: the publishing side may be healthy while the receiving side cannot keep up.

### 13\. Designing Production-Grade Notification Systems

Let's bring the concepts together in a realistic application.

Imagine we are developing a multi-tenant SaaS e-commerce platform.

The platform supports:

* Customer registration.

* Order creation.

* Payment processing.

* Inventory management.

* Shipping.

* Customer notifications.

* Business analytics.

We want to build an event-driven architecture that can grow as new services are introduced.

### 13.1 Production architecture

![Publish/Subscribe Fan-Out Pattern in Serverless Architectures Using SNS, SQS and Lambda | by Mehmet Ozkaya | AWS Lambda & Serverless — Developer Guide with Hands-on Labs | Medium](https://images.openai.com/static-rsc-4/zusw8xnuR8C8Abs7MMetwCaye1flFNx1pFxsqYJcjyldPagFgRXCvMDiTuFftllpBaehnG6Ye_Oi2AJ9f35uxXBuNY8bz2yW8Ungg0YrSM-eFtcVZ3tWHOvcGmvG_jG75al6PiLeI0_jkEqqax4IfuMr9Q838BvxyFSw19s0nwgZAWzHfeVDazdMVuZubOfl?purpose=fullsize)

A simplified event flow:

```text
              FastAPI Application
                      |
                      v
                 SNS Topic
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       SQS Queue   SQS Queue   SQS Queue
       Inventory   Payments    Shipping
          |           |           |
          v           v           v
        Lambda      Lambda       ECS
          |           |           |
          +-----------+-----------+
                      |
                      v
                Business Events
                      |
                      v
                 EventBridge
                      |
              +-------+-------+
              |               |
              v               v
           Analytics       Operations
```

This is a conceptual architecture. In a real application, the exact placement of SNS and EventBridge depends on event ownership, routing requirements, and processing guarantees.

### 13.2 Why this architecture works

Loose coupling

The FastAPI application does not need to know which services consume its events.

Independent scaling

Inventory, payments, and shipping can scale independently.

Buffering

SQS absorbs temporary traffic spikes and consumer outages.

Failure isolation

One consumer's processing problems do not directly prevent other queues from receiving their copies.

Extensibility

New subscribers can be added without redesigning the publisher.

### 13.3 Important production considerations

There are several things we should not overlook.

1\. Idempotency

SNS and SQS standard messaging do not provide exactly-once business processing.

Consumers should be designed to handle duplicate events safely.

For example, a payment consumer should not charge a customer twice because it received the same order event again.

A common approach is to use an event ID and store processed event identifiers in a database.

2\. Event versioning

As applications evolve, event structures change.

Instead of modifying event formats without compatibility considerations, include fields such as:

```json
{
  "event_id": "evt-10001",
  "event_type": "order.created",
  "event_version": 1,
  "timestamp": "2026-11-04T00:00:00Z",
  "data": {
    "order_id": "ORD-1001"
  }
}
```

3\. Observability

Use correlation IDs and event IDs to trace an event across multiple services.

4\. Dead-letter queues

Configure subscription-level SNS DLQs and consumer-side SQS DLQs for their respective failure scenarios.

5\. Backpressure

Do not allow downstream services to receive work faster than they can process it.

Use queue-based buffering and appropriate concurrency limits.

6\. Security

Use separate IAM roles, resource policies, encryption, and least-privilege access.

7\. Message contracts

Define which service owns each event and what its consumers can expect.

### 14\. Implementing SNS Production Infrastructure with Pulumi (Python)

Since we are using Pulumi throughout our AWS courses, let's see how SNS fits into Infrastructure as Code.

We will define:

* An SNS topic.

* An SQS queue.

* A queue policy.

* An SNS subscription.

This creates a basic SNS-to-SQS fanout component.

### 14.1 Project structure

```text
sns-infrastructure/
│
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
└── __main__.py
```

Dependencies:

```bash
uv add pulumi pulumi-aws
```

### 14.2 Creating the SNS topic

```python
import pulumi
import pulumi_aws as aws

topic = aws.sns.Topic(
    "orders-topic",
    name="orders-topic",
    display_name="Order Events"
)
```

This creates an SNS topic.

### 14.3 Creating an SQS queue

```python
queue = aws.sqs.Queue(
    "orders-queue",
    name="orders-queue",
    visibility_timeout_seconds=60,
    message_retention_seconds=86400,
    sqs_managed_sse_enabled=True
)
```

This queue stores messages delivered by SNS.

We have enabled SQS-managed server-side encryption.

### 14.4 Creating the queue policy

SNS needs permission to send messages to our queue.

```python
import json

queue_policy = aws.sqs.QueuePolicy(
    "orders-queue-policy",
    queue_url=queue.id,
    policy=pulumi.Output.all(
        queue.arn,
        topic.arn
    ).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": {
                    "Service": "sns.amazonaws.com"
                },
                "Action": "sqs:SendMessage",
                "Resource": args[0],
                "Condition": {
                    "ArnEquals": {
                        "aws:SourceArn": args[1]
                    }
                }
            }]
        })
    )
)
```

Notice how Pulumi uses `Output` values.

The queue ARN and topic ARN are not necessarily known when the Python program initially runs.

Pulumi resolves these dependencies during deployment.

### 14.5 Creating the SNS subscription

```python
subscription = aws.sns.TopicSubscription(
    "orders-subscription",
    topic=topic.arn,
    protocol="sqs",
    endpoint=queue.arn,
    raw_message_delivery=True
)
```

We enable raw message delivery so that the message body is delivered without the standard SNS notification envelope.

This is useful when consumers expect the original application payload.

### 14.6 Exporting resources

```python
pulumi.export("topic_arn", topic.arn)
pulumi.export("queue_url", queue.id)
pulumi.export("queue_arn", queue.arn)
```

Now we can deploy:

```bash
pulumi stack init dev

pulumi config set aws:region us-east-1

pulumi preview

pulumi up
```

This is a reusable foundation for building more sophisticated SNS infrastructure.

In production, we would extend it with:

* Customer-managed KMS encryption where required.

* SNS subscription DLQs.

* CloudWatch alarms.

* Delivery status logging.

* Multiple queues and subscriptions.

* Cross-account policies where necessary.

* Environment-specific Pulumi configuration.

### 15\. SNS FIFO Topics in Production Architectures

We covered FIFO topics in Module 3, but their production use deserves special attention.

Suppose an application processes financial transactions.

For a particular customer, transactions must be processed in order.

A Standard SNS topic does not guarantee message ordering.

An SNS FIFO topic provides ordering within message groups and supports deduplication.

### Example

```text
Customer A:
Transaction 1
Transaction 2
Transaction 3

Customer B:
Transaction 1
Transaction 2
Transaction 3
```

We can assign:

```text
MessageGroupId = customer-100
MessageGroupId = customer-200
```

This allows independent ordered message groups.

A typical architecture is:

![Detalhes de ordenação de mensagens do Amazon SNS para tópicos FIFO - Amazon Simple Notification Service](https://images.openai.com/static-rsc-4/nT3VHdcw4_W9rbxASARXQo1qxKV4r9RfVWtsIYZUexykmIMSD6QlUcvXLx64qf2gfzvSxj6JBLfVlyYG66UMZD2IH6TbsVmw8MRfUlUtvn_6Zyp1wL4_HJ8yeYS95BkCAkuwyM8Yw_dZGwBsyz-p8zIkZlG6i5xFCksPVhwy7zNczo5bMgPgp-v0_ib8dwg0?purpose=fullsize)

Important limitations:

* SNS FIFO subscriptions are designed for SQS FIFO endpoints.

* FIFO ordering applies within a message group, not globally across all groups.

* FIFO does not eliminate the need for idempotent processing.

* SNS FIFO should be selected when ordering and deduplication requirements justify its additional constraints.

For standard fanout architectures, Standard topics are generally more flexible.

### 16\. SNS Cost Optimization

SNS pricing depends on usage and the delivery protocol.

You should consider several cost components.

### 16.1 Main cost factors

| Cost factor       | Explanation                                                    |
| ----------------- | -------------------------------------------------------------- |
| API requests      | Publishing and management requests                             |
| Message size      | Larger payloads can be billed as multiple request units        |
| Delivery protocol | Different endpoint protocols have different pricing            |
| SMS               | Charged according to destination and messaging characteristics |
| Data transfer     | Applicable data-transfer charges                               |
| CloudWatch Logs   | Delivery logging generates log ingestion and storage costs     |
| CloudTrail        | Additional data-event and storage costs may apply              |

### 16.2 Practical optimization strategies

1\. Use message filtering

Avoid sending irrelevant notifications to subscribers.

2\. Avoid unnecessarily large messages

Keep event payloads small.

For large documents, store the object in S3 and publish a reference containing the bucket, key, and relevant metadata.

3\. Configure successful-delivery sampling

Log every failure but sample successful deliveries where appropriate.

4\. Choose the correct topic type

Do not use FIFO topics unless ordering and deduplication requirements justify them.

5\. Avoid excessive fanout

Each subscription creates another delivery path and potentially additional downstream costs.

6\. Monitor downstream processing

A cheap SNS architecture can still become expensive if it triggers unnecessary Lambda invocations or excessive SQS processing.

For current service quotas and pricing, consult the official documentation rather than relying on fixed values in application code. AWS +1

### 17\. SNS Troubleshooting in Production

Finally, let's examine some common production problems.

| Problem                                         | Possible cause                                     | What to investigate                         |
| ----------------------------------------------- | -------------------------------------------------- | ------------------------------------------- |
| Messages are published but not delivered        | Subscription or endpoint problem                   | Subscription status and delivery logs       |
| SQS receives no messages                        | Missing queue policy                               | sqs:SendMessage permission                  |
| Lambda is not invoked                           | Missing Lambda resource permission                 | lambda:InvokeFunction policy                |
| Some subscribers receive messages, others don't | Filtering or endpoint failures                     | Filter policies and delivery logs           |
| Duplicate processing                            | At-least-once delivery or consumer retry           | Consumer idempotency                        |
| Messages appear out of order                    | Standard topic behavior                            | FIFO topic and message groups               |
| Delivery failures increase                      | Endpoint unavailable or throttled                  | SNS metrics and subscriber health           |
| Messages disappear after delivery attempts      | Retry policy exhausted without successful delivery | Subscription DLQ                            |
| Cross-account delivery fails                    | Incorrect resource policy                          | Principal, source ARN, and account          |
| Cross-Region delivery fails                     | Region or policy configuration                     | Regional subscription and service principal |

### 17.1 Useful troubleshooting commands

List SNS topics:

```bash
aws sns list-topics
```

Inspect a topic:

```bash
aws sns get-topic-attributes \
  --topic-arn "$TOPIC_ARN"
```

List subscriptions:

```bash
aws sns list-subscriptions-by-topic \
  --topic-arn "$TOPIC_ARN"
```

Inspect a subscription:

```bash
aws sns get-subscription-attributes \
  --subscription-arn "$SUBSCRIPTION_ARN"
```

Publish a test message:

```bash
aws sns publish \
  --topic-arn "$TOPIC_ARN" \
  --message '{"event":"test","order_id":"ORD-1001"}'
```

Check the queue for delivered messages:

```bash
aws sqs receive-message \
  --queue-url "$QUEUE_URL" \
  --max-number-of-messages 10
```

Remember that receiving a message from SQS does not automatically delete it. It remains subject to SQS visibility timeout and deletion behavior.

### 17.2 A systematic troubleshooting approach

When an SNS notification is missing, follow this sequence:

* Verify that the publisher successfully called `Publish`.

* Verify that the topic ARN is correct.

* Check that the subscription exists and is confirmed.

* Inspect the subscription filter policy.

* Verify the endpoint's resource policy.

* Inspect SNS delivery status logs.

* Check CloudWatch delivery metrics.

* Inspect the subscription DLQ.

* Investigate downstream processing separately.

This approach helps isolate whether the problem is in publishing, filtering, delivery, or processing.

Amazon Simple Notification Service +1

### 18\. Important Architectural Decisions

Before finishing, let's consolidate some decisions you will encounter when designing real AWS systems.

| Requirement                                   | Recommended approach |
| --------------------------------------------- | -------------------- |
| Distribute events to multiple consumers       | SNS                  |
| Buffer messages for consumers                 | SQS                  |
| Process events using serverless compute       | Lambda               |
| Distribute events with independent processing | SNS → SQS → Lambda   |
| Route events based on complex conditions      | EventBridge          |
| Preserve per-group ordering                   | SNS FIFO → SQS FIFO  |
| Handle subscriber delivery failures           | SNS subscription DLQ |
| Handle consumer processing failures           | SQS DLQ              |
| Monitor operational behavior                  | CloudWatch           |
| Audit API activity                            | CloudTrail           |

One particularly important distinction concerns dead-letter queues:

* SNS subscription DLQ: Captures messages SNS cannot successfully deliver to a subscriber after exhausting its delivery attempts.

* SQS consumer DLQ: Captures messages that a consumer repeatedly fails to process, according to the SQS redrive policy.

These protect different stages of the architecture.

AWS-managed endpoints such as SQS and Lambda have their own SNS delivery retry behavior, which is different from customer-managed HTTP endpoints. Amazon Simple Notification Service +1

### 19\. Final Architecture: Putting Everything Together

![Enhancing multi-account activity monitoring with event-driven architectures | AWS Compute Blog](https://images.openai.com/static-rsc-4/f6Hz1tO3HhKEFLOHFrP0191_RWA5athCaT3Wv0vAsdGhdleVFivOspD1KPpaemtxKEiv-Q_Nl45S23sLGQAjEud1wLMvp1W7ALUIylT_vnQQbzyUVRHngpCnP1Nw78GAfyvnubjghm656UxWHqdZUs_DywyRN9cl0p9DfrCTesbKRy9Qmjm7L-X5mv4WeSIs?purpose=fullsize)

Think of the responsibilities this way:

* SNS: Distributes notifications.

* SQS: Buffers and stores messages.

* Lambda: Executes application logic.

* EventBridge: Routes events according to rules.

* CloudWatch: Monitors operational behavior.

* CloudTrail: Records API activity.

* Pulumi: Defines and manages the infrastructure.

These services complement each other rather than competing with each other.

### Module 6 — Key Takeaways

After completing this module, you should understand:

* How to monitor SNS using CloudWatch metrics, alarms, and dashboards.

* How CloudTrail helps audit SNS API activity.

* How delivery status logging provides detailed delivery information.

* How SNS invokes Lambda functions.

* How SNS and SQS work together.

* How SNS fanout distributes events to independent consumers.

* How SNS integrates with EventBridge and S3.

* How to design cross-account and cross-Region messaging architectures.

* How to scale SNS-based notification systems.

* How to implement SNS infrastructure using Pulumi.

* How to optimize costs and troubleshoot delivery failures.

* How to design production-grade event-driven architectures.

### Official AWS documentation

For further reference:

* [Amazon SNS Developer Guide](https://docs.aws.amazon.com/sns/latest/dg/welcome.html?utm_source=chatgpt.com)

* [Monitoring SNS with CloudWatch](https://docs.aws.amazon.com/sns/latest/dg/sns-monitoring-using-cloudwatch.html?utm_source=chatgpt.com)

* [SNS Message Delivery Status](https://docs.aws.amazon.com/sns/latest/dg/sns-topic-attributes.html?utm_source=chatgpt.com)

* [SNS Message Delivery Retries](https://docs.aws.amazon.com/sns/latest/dg/sns-message-delivery-retries.html?utm_source=chatgpt.com)

* [SNS to SQS Integration](https://docs.aws.amazon.com/sns/latest/dg/sns-sqs-as-subscriber.html?utm_source=chatgpt.com)

* [Cross-Region SNS Delivery](https://docs.aws.amazon.com/sns/latest/dg/sns-cross-region-delivery.html?utm_source=chatgpt.com)

SNS course completed

You have now completed all six modules of the Amazon SNS course.

You have covered the three major AWS event-driven building blocks:

* Lambda — event-driven compute.

* SQS — asynchronous message queuing.

* SNS — pub/sub messaging and fanout.

The natural next step is to study how these three services work together in production-grade serverless and microservices architectures.
