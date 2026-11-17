### Module 5 — SNS Security, IAM, Encryption, and Access Control

Amazon SNS security is built around controlling who can publish messages, who can manage topics, who can subscribe to topics, and who can receive messages.

When designing production SNS architectures, security must cover several layers:

* Identity and authentication.

* Authorization and access policies.

* Cross-account access.

* Encryption at rest and in transit.

* Private network connectivity.

* Protection of sensitive message data.

We'll explore each layer using AWS IAM, SNS, KMS, AWS CLI, Bash, and Python Boto3, with Pulumi (Python) for infrastructure management.

### 1\. SNS Security Architecture and Shared Responsibility

Amazon SNS is a fully managed messaging service. AWS operates the underlying infrastructure, but you are responsible for configuring access controls and protecting your application data.

### 1.1 Security architecture

Consider an application that publishes messages to an SNS topic, which distributes them to SQS queues and Lambda functions.

![Chiffrement des messages publiés sur Amazon SNS avec AWS KMS | Le Blog Amazon Web Services](https://images.openai.com/static-rsc-4/osl2XVMi9_o6tIYSGlqJ1iDeqxhvwOEb9VRscAbl1dXPjdkXDMAzhdYGrdBw6Rv5LGN5cwKHYH82_5uOuSzLqsoSVttDISolbgS1_HjDCKf4owDdgyrLTEOkn9nMUP3jRQdfVqbBqIlKJXC2mRTJUqeXoRdpLXLcGIByJZxD9USYmC40ieuxUSXEAq7LtzuY?purpose=fullsize)

There are several security boundaries:

| Security boundary  | Responsibility                           |
| ------------------ | ---------------------------------------- |
| Publisher identity | Who is allowed to publish?               |
| SNS topic          | Who can access and manage the topic?     |
| Subscription       | Who can create or manage subscriptions?  |
| Subscriber         | Who can receive and process messages?    |
| KMS                | Who can encrypt and decrypt messages?    |
| Network            | How does traffic reach SNS securely?     |
| Application        | How is sensitive message data protected? |

### 1.2 AWS shared responsibility model

AWS is responsible for security OF the cloud:

* Physical data centers.

* Physical servers and storage.

* Networking infrastructure.

* Hypervisors and virtualization.

* SNS service infrastructure.

* Managed service availability and infrastructure maintenance.

You are responsible for security IN the cloud:

* IAM policies and permissions.

* SNS topic policies.

* Subscription permissions.

* KMS keys and key policies.

* Encryption configuration.

* Network access configuration.

* Sensitive information in messages.

* Monitoring and auditing.

For example, AWS protects the infrastructure hosting SNS, but AWS does not automatically know whether your application should allow every IAM user to publish to a particular topic.

### 2\. IAM Identities and SNS Permissions

IAM (Identity and Access Management) controls which AWS identities can perform operations against SNS.

An IAM identity can be:

* IAM user.

* IAM role.

* Federated identity.

* AWS service role.

In production architectures, IAM roles are generally preferred over long-lived IAM user access keys.

### 2.1 Important SNS IAM actions

SNS provides different API actions for different operations.

| IAM action                   | Purpose                    |
| ---------------------------- | -------------------------- |
| sns:CreateTopic              | Create a topic             |
| sns:DeleteTopic              | Delete a topic             |
| sns:GetTopicAttributes       | Read topic configuration   |
| sns:SetTopicAttributes       | Modify topic configuration |
| sns:Publish                  | Publish messages           |
| sns:Subscribe                | Create subscriptions       |
| sns:Unsubscribe              | Remove subscriptions       |
| sns:ListSubscriptionsByTopic | List subscriptions         |
| sns:ListTopics               | List topics                |
| sns:ConfirmSubscription      | Confirm a subscription     |

Notice that publishing messages and managing topics are separate permissions.

An application that only publishes messages should not automatically receive permission to delete topics or modify subscriptions.

### 2.2 Identity-based policies

An identity-based policy is attached to an IAM user, group, or role.

For example, suppose an application runs inside an ECS task and needs permission to publish messages to one SNS topic.

Its IAM role could have the following policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sns:Publish"
      ],
      "Resource": "arn:aws:sns:eu-west-1:123456789012:orders-topic"
    }
  ]
}
```

This policy allows the application to publish messages to the specified topic.

It does not allow:

* Creating SNS topics.

* Deleting SNS topics.

* Changing topic policies.

* Managing subscriptions.

* Publishing to unrelated topics.

This is an example of least-privilege access.

### 2.3 AWS CLI: Inspecting SNS permissions

You can inspect a topic's attributes:

```bash
aws sns get-topic-attributes \
  --topic-arn arn:aws:sns:eu-west-1:123456789012:orders-topic
```

You can also inspect the permissions attached to an IAM role:

```bash
aws iam list-attached-role-policies \
  --role-name orders-publisher-role
```

To inspect inline policies:

```bash
aws iam list-role-policies \
  --role-name orders-publisher-role
```

Important distinction: IAM identity policies authorize an identity to perform operations, while SNS topic policies can authorize external identities and services to access a topic.

### 3\. Identity-Based Policies and Resource-Based Policies

SNS uses two important authorization mechanisms.

### 3.1 Identity-based policies

These policies are attached to IAM identities.

Example:

An ECS task assumes an IAM role with permission to publish to `orders-topic`.

The authorization relationship is:

ECS Task

Runs the application

IAM Task Role

Identity-based policy: sns:Publish

SNS Topic

orders-topic

### 3.2 Resource-based policies

A resource-based policy is attached directly to a resource.

SNS supports resource-based policies through topic policies.

For example, you can attach a policy to an SNS topic allowing another AWS account to publish messages.

The policy is attached to the topic, not the external IAM role.

### 3.3 Comparing the two approaches

| Feature              | Identity-based policy                         | Resource-based policy             |
| -------------------- | --------------------------------------------- | --------------------------------- |
| Attached to          | IAM identity                                  | SNS topic                         |
| Controls             | What identity can do                          | Who can access the topic          |
| Cross-account access | Requires corresponding resource authorization | Can authorize external principals |
| Common use           | Application publishing                        | Cross-account and service access  |

Important: An identity policy granting access does not automatically override an explicit deny, permissions boundary, SCP, or other applicable authorization restriction. Cross-account access also requires the appropriate authorization on both sides.

### 4\. SNS Topic Policies

An SNS topic policy is a resource-based JSON policy attached directly to an SNS topic.

It determines which AWS principals can perform operations against that topic.

Topic policies are especially important for:

* Cross-account publishing.

* Allowing AWS services to publish notifications.

* Controlling subscription creation.

* Restricting access to specific IAM roles.

* Preventing unauthorized publishing.

### 4.1 Example: Allowing a specific IAM role to publish

Suppose you have:

* AWS account: `123456789012`

* SNS topic: `orders-topic`

* IAM role: `orders-publisher-role`

You want that role to publish messages to the topic.

A topic policy could look like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowOrdersPublisher",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/orders-publisher-role"
      },
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:eu-west-1:123456789012:orders-topic"
    }
  ]
}
```

The important elements are:

| Element   | Meaning                        |
| --------- | ------------------------------ |
| Effect    | Allow or Deny                  |
| Principal | Identity receiving permission  |
| Action    | SNS operation being authorized |
| Resource  | SNS topic ARN                  |
| Sid       | Optional statement identifier  |

### 4.2 Applying the policy using AWS CLI

Save the policy as `topic-policy.json`.

Then:

```bash
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:eu-west-1:123456789012:orders-topic \
  --attribute-name Policy \
  --attribute-value file://topic-policy.json
```

Inspect the policy:

```bash
aws sns get-topic-attributes \
  --topic-arn arn:aws:sns:eu-west-1:123456789012:orders-topic
```

### 4.3 Restricting publishing to a specific AWS account

You can also authorize an entire AWS account:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowExternalAccount",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222233334444:root"
      },
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:eu-west-1:123456789012:orders-topic"
    }
  ]
}
```

Here, `root` represents the AWS account principal, not exclusively the root user.

The external account can then delegate the permission to its IAM roles or users through its own identity policies.

Security recommendation: Prefer specific role principals over broad account-level access when the intended publisher is known.

### 5\. Publisher and Subscriber Permissions

SNS has two distinct sides:

* Publishers send messages to topics.

* Subscribers receive messages through subscriptions.

These operations require different permissions.

### 5.1 Publisher permissions

A publisher typically needs:

```json
{
  "Effect": "Allow",
  "Action": "sns:Publish",
  "Resource": "arn:aws:sns:eu-west-1:123456789012:orders-topic"
}
```

For example, a FastAPI application running in ECS might publish an order notification:

```python
import boto3
import json

sns = boto3.client("sns", region_name="eu-west-1")

response = sns.publish(
    TopicArn="arn:aws:sns:eu-west-1:123456789012:orders-topic",
    Subject="New Order",
    Message=json.dumps({
        "order_id": "ORD-1001",
        "status": "created"
    })
)

print(response["MessageId"])
```

Boto3 automatically obtains temporary credentials from the ECS task role when configured correctly.

You should not hardcode AWS access keys inside the application.

### 5.2 Subscriber permissions

Subscriber permissions depend on the subscription protocol.

| Subscription protocol | Important security consideration                     |
| --------------------- | ---------------------------------------------------- |
| SQS                   | Queue policy must authorize SNS to send messages     |
| Lambda                | Lambda resource policy must authorize SNS invocation |
| HTTPS                 | Endpoint must confirm the subscription               |
| Email                 | Recipient must confirm subscription                  |
| SMS                   | Phone-number and account-level messaging controls    |
| Platform application  | Platform credentials and application configuration   |

This is an important architectural distinction:

Allowing SNS to publish to a topic does not automatically allow SNS to deliver messages to every destination.

Each subscriber has its own authorization requirements.

### 5.3 SNS → SQS permissions

Suppose SNS publishes messages to an SQS queue.

The SQS queue needs a resource-based policy allowing the SNS service to send messages.

Example queue policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSNSToSendMessages",
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
      "Action": "sqs:SendMessage",
      "Resource": "arn:aws:sqs:eu-west-1:123456789012:orders-queue",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "arn:aws:sns:eu-west-1:123456789012:orders-topic"
        }
      }
    }
  ]
}
```

The condition restricts delivery to the intended SNS topic.

This is preferable to allowing every SNS topic to send messages to the queue.

### 5.4 SNS → Lambda permissions

Lambda requires permission to be invoked by SNS.

You can create that permission using:

```bash
aws lambda add-permission \
  --function-name process-order \
  --statement-id AllowSNSInvocation \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:eu-west-1:123456789012:orders-topic
```

This adds a resource-based permission to the Lambda function.

The distinction is:

* The SNS topic policy controls who can publish to SNS.

* The Lambda resource policy controls whether SNS can invoke Lambda.

### 6\. Cross-Account Topic Access

Cross-account access allows one AWS account to publish messages to or subscribe to a topic owned by another account.

This is useful in:

* Multi-account AWS organizations.

* Microservice architectures.

* Centralized notification systems.

* Shared event distribution platforms.

* SaaS applications serving multiple AWS accounts.

### 6.1 Example architecture

Imagine two AWS accounts:

Account A — Application Account

Account ID: 111122223333

Orders application

Assumes an IAM role and publishes messages.

Cross-account sns:Publish

Account B — Messaging Account

Account ID: 444455556666

SNS orders-topic

Receives messages and distributes them to subscribers.

### 6.2 Configuring cross-account publishing

There are two important authorization steps.

Step 1 — Account B authorizes Account A in the SNS topic policy.

For example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowAccountAPublishing",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::111122223333:root"
      },
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:eu-west-1:444455556666:orders-topic"
    }
  ]
}
```

Step 2 — Account A authorizes its application role.

Attach this identity-based policy to the application role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "sns:Publish",
      "Resource": "arn:aws:sns:eu-west-1:444455556666:orders-topic"
    }
  ]
}
```

Now the application role has identity-based permission, and the destination topic trusts its AWS account.

### 6.3 Cross-account security considerations

* Avoid using wildcard principals unless there is a clear reason.

* Use specific IAM roles whenever possible.

* Restrict actions to the minimum required.

* Consider AWS Organizations conditions when appropriate.

* Monitor cross-account activity through CloudTrail.

* Configure KMS permissions separately when the topic uses a customer-managed key.

An important detail: cross-account subscription management and message delivery involve additional permissions beyond cross-account publishing.

### 7\. AWS Service Principals and Service-to-Service Permissions

AWS services frequently communicate with SNS.

Examples include:

* S3 publishing object-created notifications.

* CloudWatch publishing alarm notifications.

* EventBridge publishing events.

* CodePipeline publishing deployment notifications.

These services can be authorized using AWS service principals.

### 7.1 What is a service principal?

A service principal identifies an AWS service in an IAM policy.

For example:

```json
"Principal": {
  "Service": "s3.amazonaws.com"
}
```

This identifies Amazon S3 as the principal.

It does not identify a particular bucket or AWS account by itself.

### 7.2 Example: Allowing S3 to publish to SNS

Suppose an S3 bucket should publish object-created notifications to an SNS topic.

The SNS topic policy can contain:

```json
{
  "Sid": "AllowS3BucketNotifications",
  "Effect": "Allow",
  "Principal": {
    "Service": "s3.amazonaws.com"
  },
  "Action": "sns:Publish",
  "Resource": "arn:aws:sns:eu-west-1:123456789012:storage-events",
  "Condition": {
    "ArnEquals": {
      "aws:SourceArn": "arn:aws:s3:::my-application-bucket"
    },
    "StringEquals": {
      "aws:SourceAccount": "123456789012"
    }
  }
}
```

The conditions restrict the publishing permission to a particular bucket and account.

Without these conditions, an overly broad service-principal policy can create a confused-deputy security risk.

### 7.3 Service-to-service authorization pattern

A typical authorization model looks like this:

| Publisher         | Principal                | Permission  |
| ----------------- | ------------------------ | ----------- |
| ECS application   | IAM role                 | sns:Publish |
| S3                | s3.amazonaws.com         | sns:Publish |
| CloudWatch alarms | cloudwatch.amazonaws.com | sns:Publish |
| EventBridge       | events.amazonaws.com     | sns:Publish |

The exact service principal and supported condition keys should be verified for the integration being configured.

### 8\. Least-Privilege Access Control

Least privilege means granting an identity only the permissions it needs to perform its specific job.

This is one of the most important principles in AWS security.

Consider a notification system with three components:

* An ECS application publishes order events.

* An SNS topic distributes those events.

* An administrator manages the SNS infrastructure.

These components should not share the same permissions.

### 8.1 Separate IAM roles

| IAM role              | Required permissions                       |
| --------------------- | ------------------------------------------ |
| orders-publisher-role | sns:Publish                                |
| sns-admin-role        | Create, delete, and configure topics       |
| sns-subscription-role | Manage subscriptions                       |
| monitoring-role       | Read SNS attributes and CloudWatch metrics |

For example, the publisher role should not have:

```json
{
  "Effect": "Allow",
  "Action": "sns:*",
  "Resource": "*"
}
```

This policy grants unnecessarily broad permissions.

Instead, grant only:

```json
{
  "Effect": "Allow",
  "Action": "sns:Publish",
  "Resource": "arn:aws:sns:eu-west-1:123456789012:orders-topic"
}
```

### 8.2 Restricting subscriptions by protocol

SNS provides condition keys that can restrict subscription requests.

For example, you might want to allow subscriptions only through HTTPS.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowHTTPSSubscriptions",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::123456789012:role/sns-subscription-role"
      },
      "Action": "sns:Subscribe",
      "Resource": "arn:aws:sns:eu-west-1:123456789012:orders-topic",
      "Condition": {
        "StringEquals": {
          "sns:Protocol": "https"
        }
      }
    }
  ]
}
```

You can also restrict subscriptions to specific endpoints using the `sns:Endpoint` condition key.

This helps prevent someone from subscribing an unauthorized endpoint to receive sensitive notifications.

### 8.3 Preventing public topic access

Avoid policies such as:

```json
{
  "Effect": "Allow",
  "Principal": "*",
  "Action": "sns:Publish",
  "Resource": "*"
}
```

This can expose your topic to unauthorized publishers.

For sensitive systems, explicitly define the trusted principals and topic ARNs.

### 8.4 Additional least-privilege practices

* Use IAM roles instead of long-lived access keys.

* Enable MFA for privileged human identities.

* Use permissions boundaries where appropriate.

* Apply AWS Organizations SCPs to enforce organizational restrictions.

* Restrict subscription protocols and endpoints.

* Require HTTPS.

* Audit changes to topic policies.

* Regularly review unused permissions.

One additional SNS-specific consideration: `ConfirmSubscription` and `Unsubscribe` have unauthenticated API behavior in certain circumstances. IAM policies alone do not provide the same protection for these operations as they do for ordinary authenticated SNS API calls. Configure authenticated unsubscribe where appropriate.

### 9\. Server-Side Encryption with AWS KMS

SNS supports Server-Side Encryption (SSE) using AWS Key Management Service (KMS).

SSE protects message contents stored within SNS topics.

Without SNS SSE, you should not assume that your application-level encryption requirements are satisfied merely because SNS is a managed AWS service.

### 9.1 What is AWS KMS?

AWS Key Management Service (KMS) is a managed service for creating, controlling, and auditing cryptographic keys.

KMS helps you:

* Create encryption keys.

* Control key access.

* Rotate eligible keys.

* Define key policies.

* Audit cryptographic operations.

* Integrate encryption with AWS services.

### 9.2 How SNS encryption works

![Encrypting messages published to Amazon SNS with AWS KMS | AWS Compute Blog](https://images.openai.com/static-rsc-4/-HdMuEBNRSSVNHz_Q3faTHZ0rJ8_7ZqyU-MFKUNTK8RQ_9DY5rcWfuHuKG3P9k146s5Zu17EmCVuYEPS8qKuUZV7CQb92NlLRgesM4AjND43C4jiKeFKC0nebn0sPgt7-ZUhhA-BEeLSxVptJKq0XHe7HPLWVv_hwLWrBYs9XY1sU9_AvX4cSzipI71mjMQK?purpose=fullsize)

The general process is:

* A publisher sends a message to an SNS topic.

* SNS obtains a data encryption key through KMS.

* SNS uses the data key to encrypt the message body.

* SNS stores the encrypted message.

* When delivering the message, SNS decrypts it internally.

* SNS sends the message to the subscriber.

This is based on envelope encryption.

There are two important keys:

| Key                       | Purpose                              |
| ------------------------- | ------------------------------------ |
| KMS key                   | Protects the data encryption key     |
| Data encryption key (DEK) | Encrypts the actual message contents |

SNS manages this process transparently.

Subscribers do not normally need to decrypt the SNS message themselves just because the topic uses SSE.

### 9.3 What does SNS actually encrypt?

An important distinction is that SNS SSE does not encrypt every field associated with a message.

| Data               | Encrypted by SNS SSE? |
| ------------------ | --------------------- |
| Message body       | Yes                   |
| Message subject    | No                    |
| Message attributes | No                    |
| Message ID         | No                    |
| Timestamp          | No                    |
| Topic name         | No                    |
| Topic metadata     | No                    |

Therefore, do not place confidential information in message attributes, subjects, or topic names expecting SNS SSE to protect it.

Also, messages already stored before SSE is enabled are not retroactively encrypted.

### 9.4 Enabling SNS encryption using AWS CLI

You can enable encryption when creating a topic.

First, create the topic:

```bash
aws sns create-topic \
  --name encrypted-orders-topic
```

Then configure its KMS key:

```bash
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:eu-west-1:123456789012:encrypted-orders-topic \
  --attribute-name KmsMasterKeyId \
  --attribute-value alias/aws/sns
```

Here:

```text
alias/aws/sns
```

is the AWS-managed KMS key alias for SNS.

You can inspect the configuration:

```bash
aws sns get-topic-attributes \
  --topic-arn arn:aws:sns:eu-west-1:123456789012:encrypted-orders-topic
```

Look for:

```json
{
  "KmsMasterKeyId": "alias/aws/sns"
}
```

### 9.5 Enabling encryption using Python Boto3

You can also create an encrypted topic directly using Boto3:

```python
import boto3

sns = boto3.client("sns", region_name="eu-west-1")

response = sns.create_topic(
    Name="encrypted-orders-topic",
    Attributes={
        "KmsMasterKeyId": "alias/aws/sns"
    }
)

print(response["TopicArn"])
```

This creates a topic with SNS server-side encryption enabled.

### 10\. AWS-Managed Keys and Customer-Managed Keys

SNS supports two important KMS key options.

### 10.1 AWS-managed KMS key

AWS manages the key lifecycle and key policy.

For SNS, the key alias is:

```text
alias/aws/sns
```

Characteristics:

* AWS creates and manages the key.

* Minimal key-management configuration.

* No need to maintain your own key policy.

* Limited customization of key access.

* Not suitable for every cross-account encryption requirement.

This is generally a convenient choice when you need SNS encryption without extensive key-management customization.

### 10.2 Customer-managed KMS key

A customer-managed key is created and controlled within your AWS account.

You control:

* Key policies.

* IAM permissions.

* Key administrators.

* Key usage permissions.

* Rotation configuration.

* Key deletion scheduling.

* Audit and access management.

For example, you might create a key named:

```text
alias/orders-sns-encryption
```

You can then configure SNS to use it:

```bash
aws sns set-topic-attributes \
  --topic-arn arn:aws:sns:eu-west-1:123456789012:orders-topic \
  --attribute-name KmsMasterKeyId \
  --attribute-value alias/orders-sns-encryption
```

### 10.3 Comparison

| Feature                       | AWS-managed key | Customer-managed key      |
| ----------------------------- | --------------- | ------------------------- |
| Key creation                  | AWS             | You                       |
| Key policy customization      | Limited         | Yes                       |
| Key lifecycle management      | AWS             | You control configuration |
| IAM integration               | Yes             | Yes                       |
| Detailed access control       | Limited         | Extensive                 |
| Custom rotation configuration | No              | Yes                       |
| Additional KMS management     | Minimal         | Required                  |

### 10.4 Which should you choose?

For a simple notification system, an AWS-managed SNS key is often sufficient.

For production systems involving multiple AWS accounts, compliance requirements, or detailed key-access controls, a customer-managed key is often preferable.

Remember that customer-managed keys introduce additional operational responsibilities and KMS charges.

### 11\. KMS Key Policies and Encryption Permissions

This is one of the most important and commonly misunderstood parts of SNS security.

Having permission to publish to an SNS topic does not automatically mean that the publisher has all the KMS permissions required for an encrypted topic.

There are two separate authorization systems:

* SNS authorization.

* KMS authorization.

### 11.1 Example permission requirements

Suppose an ECS application publishes messages to an encrypted SNS topic.

The ECS task role may need:

| Permission           | Purpose                                 |
| -------------------- | --------------------------------------- |
| sns:Publish          | Publish to the SNS topic                |
| kms:GenerateDataKey* | Obtain data encryption keys             |
| kms:Decrypt          | Support the SNS encryption key workflow |

The exact KMS permissions depend on the publishing principal, key policy, and integration.

### 11.2 Example customer-managed KMS key policy

A key policy can authorize SNS to use the key on behalf of a specific topic.

For example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowSNSUseOfKey",
      "Effect": "Allow",
      "Principal": {
        "Service": "sns.amazonaws.com"
      },
      "Action": [
        "kms:GenerateDataKey*",
        "kms:Decrypt"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:EncryptionContext:aws:sns:topicArn": "arn:aws:sns:eu-west-1:123456789012:orders-topic"
        }
      }
    }
  ]
}
```

This is an illustrative service-access statement, not necessarily a complete production key policy. You must also preserve appropriate key-administration and account-access permissions.

### 11.3 Why is `kms:Decrypt` needed?

SNS uses envelope encryption and reuses data encryption keys for a limited period.

The KMS permissions are not simply a direct mapping of application publishing and message consumption.

SNS performs the encryption and decryption operations internally, while KMS authorizes the relevant cryptographic operations.

### 11.4 Common KMS permission mistakes

| Mistake                                        | Consequence                    |
| ---------------------------------------------- | ------------------------------ |
| Missing KMS key policy permissions             | SNS cannot use the key         |
| Missing publisher KMS permissions              | Publishing may fail            |
| Wrong key ARN or Region                        | Encryption configuration fails |
| Incorrect encryption context                   | Key authorization fails        |
| Using an unsupported asymmetric key            | SNS cannot use the key         |
| Missing permissions for AWS service publishers | Service integration may fail   |

Important: SNS supports symmetric KMS encryption keys, not asymmetric keys.

### 11.5 SNS → encrypted SQS considerations

Consider an architecture where both SNS and SQS use customer-managed KMS keys.

![How to set up least privilege access to your encrypted Amazon SQS queue | AWS Security Blog](https://images.openai.com/static-rsc-4/PzCCS4Ss0mLTmAAOLdZ-j2xb1gM9B4m3x7j5IYwvWnLg9YcRPRZ9PCBZbmt1Th7vJdXM9DzzJe6MRoMeCkdqzGWAJzjf7KN1kkfbvN-0OhQVbz3-iERN1y68fyMnUxjPtRUVhXLRl5acgcj_TwrlSK0Xn0Z3tAotNAjWovaRzxKC0uON5swPHEl7I7j42Wh2?purpose=fullsize)

You must configure both encryption systems correctly:

* SNS needs permission to use its topic encryption key.

* SNS needs permission to send messages to the SQS queue.

* The SQS queue's KMS key policy must allow SNS to use the required KMS operations, including `kms:GenerateDataKey` and `kms:Decrypt`.

* The queue's consumer must have the necessary permissions to consume and decrypt the queue's messages.

A frequent production problem is configuring the SNS topic correctly but forgetting the KMS permissions on the encrypted SQS queue.

### 12\. VPC Endpoints and Private SNS Access

By default, applications communicate with SNS through AWS service endpoints.

If an application runs inside a private subnet, it can access SNS through a NAT Gateway or another supported network path.

However, you can also use an Interface VPC Endpoint (AWS PrivateLink) to access SNS privately.

### 12.1 What is an Interface VPC Endpoint?

An interface endpoint creates private network interfaces (ENIs) inside your VPC.

These interfaces provide private connectivity between your VPC and supported AWS services.

For SNS, this means your application can publish messages without sending API traffic through the public internet.

![Leverage VPC endpoints - Serverless Applications Lens](https://images.openai.com/static-rsc-4/w0HQx5Fe6wtt1r2jPiEP1YPZToVW5TWOIaniq-OlbRoW-iE-u0JqlF-bozQeT_z9gllgStGfHHes6_6UJB_oDV4Cb0We2OWFRdx-V9mDi9rpTEwk1Lhx1-CXR7oITdolO0GZogNlBGvLvQv32XK-Jt-3KCCndvCVDBS8tATPo144mQSW-O0u01jpc5HBivaA?purpose=fullsize)

### 12.2 Without a VPC endpoint

Consider this architecture:

```text
Private Subnet
     |
     v
ECS Application
     |
     v
NAT Gateway
     |
     v
Internet Gateway
     |
     v
SNS Public Endpoint
```

The application needs an outbound network path to reach SNS.

### 12.3 With a VPC endpoint

The architecture becomes:

```text
Private Subnet
     |
     v
ECS Application
     |
     v
SNS Interface Endpoint
     |
     v
Amazon SNS
```

The application communicates with SNS through private connectivity.

You do not need:

* An Internet Gateway for this SNS connection.

* A NAT Gateway for this SNS connection.

* Public IP addresses for the application.

Other application dependencies may still require internet or NAT connectivity.

### 12.4 Creating an SNS VPC endpoint using AWS CLI

First, identify your VPC and subnet IDs.

Then create an interface endpoint:

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --vpc-endpoint-type Interface \
  --service-name com.amazonaws.eu-west-1.sns \
  --subnet-ids subnet-11111111 subnet-22222222 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled
```

The important parameters are:

| Parameter             | Purpose                           |
| --------------------- | --------------------------------- |
| --vpc-id              | Target VPC                        |
| --vpc-endpoint-type   | Interface endpoint                |
| --service-name        | SNS regional service              |
| --subnet-ids          | Subnets containing endpoint ENIs  |
| --security-group-ids  | Controls traffic to endpoint ENIs |
| --private-dns-enabled | Enables private DNS resolution    |

### 12.5 VPC endpoint policies

You can attach an additional policy to the VPC endpoint.

For example, you can allow only a particular IAM role to publish to a specific SNS topic through that endpoint.

This adds another authorization layer.

Remember that a VPC endpoint policy does not replace IAM policies or SNS topic policies.

### 12.6 Important networking limitation

There is an important distinction between accessing SNS privately and delivering SNS notifications privately.

A VPC endpoint allows applications inside your VPC to access SNS.

It does not make SNS capable of delivering notifications to arbitrary private IP addresses inside your VPC.

For example:

* ECS application → SNS through VPC endpoint: supported.

* SNS → private IP address in your VPC as an HTTPS subscription: not supported through the VPC endpoint.

For private subscriber architectures, using SNS → SQS or SNS → Lambda is often more appropriate.

### 13\. HTTPS Delivery and Endpoint Security

SNS supports several subscription protocols, including HTTP and HTTPS.

However, for production systems, HTTPS should be preferred.

### 13.1 HTTP versus HTTPS

| Feature                                 | HTTP    | HTTPS                         |
| --------------------------------------- | ------- | ----------------------------- |
| Transport encryption                    | No      | Yes                           |
| Data confidentiality in transit         | No      | Yes                           |
| Protection against network interception | Limited | Yes, when properly configured |
| Production recommendation               | Avoid   | Preferred                     |

Consider an application subscribing to an SNS topic:

```text
SNS Topic
    |
    v
HTTPS Endpoint
    |
    v
FastAPI Application
```

When SNS sends a notification, HTTPS protects the communication channel using TLS.

### 13.2 Enforcing HTTPS for publishers

You can enforce secure transport using the global IAM condition key:

```json
"aws:SecureTransport"
```

For example, add an explicit Deny statement to your SNS topic policy:

```json
{
  "Sid": "DenyInsecureTransport",
  "Effect": "Deny",
  "Principal": "*",
  "Action": "sns:Publish",
  "Resource": "arn:aws:sns:eu-west-1:123456789012:orders-topic",
  "Condition": {
    "Bool": {
      "aws:SecureTransport": "false"
    }
  }
}
```

This prevents publishing requests that do not use secure transport.

For topics with SSE enabled, SNS requires HTTPS and AWS Signature Version 4 for requests.

### 13.3 Securing HTTPS subscription endpoints

Suppose you have a FastAPI application:

```python
from fastapi import FastAPI, Request

app = FastAPI()

@app.post("/sns/notifications")
async def sns_notification(request: Request):
    message = await request.json()

    return {
        "status": "received"
    }
```

This is only a basic receiving endpoint. A production SNS subscriber should implement additional security controls.

Important protections include:

1\. HTTPS and valid TLS certificates

Use a valid certificate and a trusted domain name.

Avoid subscribing directly to raw IP addresses.

2\. SNS message signature verification

SNS notifications contain signature-related information.

Your application should verify the SNS signature using AWS's documented verification process before trusting the notification.

This protects against forged notifications.

3\. Subscription confirmation

SNS sends a subscription confirmation message when a new HTTPS subscription is created.

Your application must handle this confirmation correctly.

4\. Replay and duplicate protection

Do not assume that a notification is received only once.

Use message IDs, idempotency keys, or application-level deduplication to avoid duplicate processing.

5\. Input validation

Validate the message structure and reject unexpected or malformed payloads.

6\. Authentication and authorization

Do not rely solely on an obscure endpoint URL.

Use signature verification and appropriate application-level access controls.

### 13.4 Authenticated unsubscribe

SNS supports subscription confirmation options that require authenticated unsubscribe requests.

For subscriptions where unauthenticated unsubscribe is unnecessary, set:

```text
AuthenticateOnUnsubscribe = true
```

This helps prevent unauthorized parties from removing subscriptions.

### 14\. Protecting Sensitive Message Data

Encryption is important, but encryption alone does not solve every data-security problem.

Imagine an e-commerce application publishing this message:

```json
{
  "customer_id": "CUST-1001",
  "customer_email": "customer@example.com",
  "credit_card_number": "4111111111111111",
  "order_id": "ORD-2001",
  "total": 250.00
}
```

Even if SNS SSE is enabled, the message is delivered to authorized subscribers in decrypted form.

Therefore, every subscriber that receives the message becomes part of your data-security boundary.

### 14.1 Minimize sensitive information

Instead of publishing complete customer information, publish only what downstream services need.

For example:

```json
{
  "customer_id": "CUST-1001",
  "order_id": "ORD-2001",
  "event_type": "order.created",
  "total": 250.00
}
```

If a subscriber needs additional customer information, it can retrieve it from an authorized application service.

This reduces the amount of sensitive information distributed across your architecture.

### 14.2 Separate sensitive data from event notifications

A useful architectural pattern is to distribute references rather than confidential data.

Customer Database / Secure Storage

Contains sensitive customer information

SNS Topic

Distributes customer ID and event reference

Service A

Retrieves authorized data

Service B

Retrieves authorized data

This architecture allows SNS to distribute events without distributing confidential customer records to every subscriber.

### 14.3 SNS Message Data Protection

An additional feature worth understanding is SNS Message Data Protection.

This feature allows you to define data protection policies that inspect message content for sensitive information.

For example, you can configure policies to identify sensitive data such as:

* Credit card numbers.

* Social Security numbers.

* Email addresses.

* Other supported personally identifiable information (PII).

Depending on the configured policy, SNS can audit or block messages containing specified sensitive data.

This is different from SSE:

| Feature                      | Purpose                                         |
| ---------------------------- | ----------------------------------------------- |
| SNS SSE                      | Encrypts message bodies at rest                 |
| HTTPS                        | Encrypts data in transit                        |
| IAM                          | Controls who can access SNS                     |
| Topic policies               | Control access to topics                        |
| Message Data Protection      | Inspects and controls sensitive message content |
| Application-level encryption | Protects selected data before publishing        |

For example, an organization could use Message Data Protection to detect accidental publication of payment information.

This is particularly useful when multiple applications publish messages to a shared SNS topic.

### 14.4 Logging and sensitive data

Be careful about where messages are logged.

Sensitive data can unintentionally appear in:

* Application logs.

* CloudWatch Logs.

* Debugging output.

* Error messages.

* Tracing systems.

* Monitoring dashboards.

Avoid logging complete message bodies when they contain confidential information.

Instead, log identifiers and event metadata.

For example:

```python
logger.info(
    "Order event published",
    extra={
        "order_id": order_id,
        "message_id": response["MessageId"]
    }
)
```

This provides useful operational visibility without unnecessarily exposing customer information.

### 15\. Putting Everything Together: Production Security Architecture

Let's combine the security concepts into one production-style architecture.

Imagine an e-commerce application running on ECS Fargate.

It publishes order events to an encrypted SNS topic. SNS distributes messages to an SQS queue and a Lambda function.

![Gestione degli accessi per code crittografate di Amazon SQS con politiche di privilegi minimi - Amazon Simple Queue Service](https://images.openai.com/static-rsc-4/Vw6Z-Ui0jQmAkjyNwl12xpnYVPwsWaLFZj1tYlTDCQ_eqWRCWGceibWO641MqlXbI31j1eSFPwNyJH9hDP1dt89fe6q8UB3pUBKiuPETjESU2vIA_-z43bIhpTpsA5N9pNzplCoAOQ5kDhYczq_2-fLJJeUrfUXHqWGZjto_l_eE50R5o0Ixeyj5SsZP6QdA?purpose=fullsize)

### Security configuration

| Component       | Security configuration                            |
| --------------- | ------------------------------------------------- |
| ECS application | IAM task role with sns:Publish                    |
| SNS topic       | Private, restrictive topic policy                 |
| SNS encryption  | Customer-managed KMS key                          |
| KMS             | Explicit key policy and restricted usage          |
| SQS             | Queue policy allowing only the intended SNS topic |
| SQS encryption  | Customer-managed KMS key                          |
| Lambda          | Resource policy allowing SNS invocation           |
| VPC             | Interface endpoint for private SNS API access     |
| Communication   | HTTPS and TLS                                     |
| Monitoring      | CloudTrail and CloudWatch                         |
| Application     | Minimal message payloads and input validation     |

### Security flow

* ECS obtains temporary AWS credentials through its task role.

* ECS publishes an order event using HTTPS.

* IAM verifies the publisher's SNS permissions.

* SNS uses KMS to encrypt the message body at rest.

* SNS evaluates its subscription configuration.

* SNS delivers the message to authorized subscribers.

* SQS and Lambda enforce their own resource-level permissions.

* CloudTrail records relevant API activity.

* CloudWatch provides operational monitoring.

The important lesson is that SNS security is not controlled by a single policy. It requires coordination between IAM, SNS, KMS, subscriber permissions, networking, and application-level security.

### 16\. Important Security Concepts to Remember

Here is a consolidated reference for the entire module.

| Concept                 | Main responsibility                            |
| ----------------------- | ---------------------------------------------- |
| IAM identity policy     | Authorizes IAM identities                      |
| SNS topic policy        | Controls access to SNS topics                  |
| Cross-account access    | Enables authorized access between AWS accounts |
| Service principal       | Identifies AWS services in resource policies   |
| Least privilege         | Minimizes unnecessary permissions              |
| AWS KMS                 | Manages encryption keys                        |
| SNS SSE                 | Encrypts message bodies at rest                |
| KMS key policy          | Controls cryptographic key usage               |
| VPC endpoint            | Provides private SNS API connectivity          |
| HTTPS                   | Encrypts network communication                 |
| Signature verification  | Validates SNS HTTP/S notifications             |
| Message Data Protection | Detects and controls sensitive message content |

### Common production mistakes

* Giving an application `sns:*` instead of `sns:Publish`.

* Allowing public access through wildcard topic policies.

* Forgetting SQS queue policies when integrating SNS with SQS.

* Forgetting Lambda resource permissions.

* Enabling SNS encryption without configuring KMS permissions.

* Assuming SNS SSE encrypts message attributes and subjects.

* Assuming VPC endpoints allow SNS to deliver to private IP addresses.

* Using HTTP for production notification endpoints.

* Trusting incoming SNS HTTP notifications without signature verification.

* Publishing confidential information unnecessarily.

### 17\. Official AWS Documentation

These are useful references for going deeper into the topics covered.

* [Amazon SNS Security Best Practices](https://docs.aws.amazon.com/sns/latest/dg/sns-security-best-practices.html?utm_source=chatgpt.com)

* [Using Identity-Based Policies with Amazon SNS](https://docs.aws.amazon.com/sns/latest/dg/sns-using-identity-based-policies.html?utm_source=chatgpt.com)

* [SNS Server-Side Encryption](https://docs.aws.amazon.com/sns/latest/dg/sns-server-side-encryption.html?utm_source=chatgpt.com)

* [Managing SNS Encryption Keys and Costs](https://docs.aws.amazon.com/sns/latest/dg/sns-key-management.html?utm_source=chatgpt.com)

* [Securing SNS Traffic with VPC Endpoints](https://docs.aws.amazon.com/sns/latest/dg/sns-internetwork-traffic-privacy.html?utm_source=chatgpt.com)

* [Amazon SNS Security and Data Protection](https://docs.aws.amazon.com/sns/latest/dg/security.html?utm_source=chatgpt.com)

### Module 5 — Final Takeaways

After completing this module, you should understand:

* How IAM controls SNS operations.

* How identity-based and resource-based policies work together.

* How to configure SNS topic policies.

* How to authorize publishers and subscribers.

* How to implement cross-account publishing.

* How AWS service principals enable service-to-service communication.

* How to implement least-privilege access.

* How SNS integrates with KMS.

* Differences between AWS-managed and customer-managed keys.

* How KMS key policies affect SNS encryption.

* How to access SNS privately through VPC endpoints.

* How to secure HTTPS subscriptions.

* How to protect sensitive information in SNS messages.

My recommendation: Pay particular attention to sections 5, 6, 7, and 11. Understanding the interaction between SNS topic policies, SQS queue policies, Lambda resource policies, and KMS key policies is essential when building secure event-driven architectures.

Next, we'll move to Module 6 — SNS Monitoring, Integrations, Scaling, and Production Architectures, where we'll connect SNS with the Lambda and SQS concepts we've already studied.
