### Module 5 — SQS Security, IAM, Encryption, and Networking

Amazon Simple Queue Service (SQS) · Security and access control

### 1\. SQS security architecture and shared responsibility

Amazon SQS is a fully managed messaging service. AWS operates the underlying infrastructure, while you are responsible for configuring who can access your queues, how messages are protected, and how applications authenticate.

SQS security consists of four major areas:

* Identity and access management: Who can send, receive, delete, and manage messages?

* Resource policies: Which AWS accounts and principals can access a queue?

* Encryption: How are messages protected at rest and in transit?

* Network security: How can applications access SQS privately?

### Shared responsibility model

| AWS responsibilities                    | Customer responsibilities        |
| --------------------------------------- | -------------------------------- |
| Physical data center security           | IAM permissions                  |
| Hardware and infrastructure             | Queue access policies            |
| SQS service availability infrastructure | Message encryption configuration |
| Operating the SQS service               | KMS key permissions              |
| Infrastructure maintenance              | Secure application credentials   |
| Underlying network infrastructure       | VPC endpoint policies            |

For example, AWS protects the infrastructure hosting your SQS queue, but it is your responsibility to prevent unauthorized applications from receiving sensitive messages.

### SQS security architecture

![How to set up least privilege access to your encrypted Amazon SQS queue | AWS Security Blog](https://images.openai.com/static-rsc-4/PzCCS4Ss0mLTmAAOLdZ-j2xb1gM9B4m3x7j5IYwvWnLg9YcRPRZ9PCBZbmt1Th7vJdXM9DzzJe6MRoMeCkdqzGWAJzjf7KN1kkfbvN-0OhQVbz3-iERN1y68fyMnUxjPtRUVhXLRl5acgcj_TwrlSK0Xn0Z3tAotNAjWovaRzxKC0uON5swPHEl7I7j42Wh2?purpose=fullsize)

Consider an application architecture:

* A producer application sends messages to SQS.

* IAM determines whether the producer can call `SendMessage`.

* SQS encrypts messages at rest if server-side encryption is enabled.

* A consumer application receives messages.

* IAM determines whether the consumer can call `ReceiveMessage` and `DeleteMessage`.

* HTTPS protects communication between applications and SQS.

The important principle is that authentication, authorization, encryption, and network isolation solve different security problems. You generally need all four.

### 2\. IAM identities and SQS permissions

AWS Identity and Access Management (IAM) controls which identities can perform operations against SQS.

An IAM identity can be:

* IAM user.

* IAM role.

* Federated identity.

* AWS service role.

* Application running with temporary AWS credentials.

In modern AWS application architectures, IAM roles are generally preferred over long-lived IAM user access keys.

### Important SQS API permissions

SQS permissions correspond to API operations.

| IAM permission              | Purpose                    |
| --------------------------- | -------------------------- |
| sqs:CreateQueue             | Create a queue             |
| sqs:DeleteQueue             | Delete a queue             |
| sqs:GetQueueUrl             | Retrieve a queue URL       |
| sqs:GetQueueAttributes      | Read queue configuration   |
| sqs:SetQueueAttributes      | Modify queue configuration |
| sqs:SendMessage             | Send messages              |
| sqs:ReceiveMessage          | Receive messages           |
| sqs:DeleteMessage           | Delete received messages   |
| sqs:ChangeMessageVisibility | Change visibility timeout  |
| sqs:PurgeQueue              | Remove all messages        |
| sqs:ListQueues              | List queues                |

There are also permissions for batch operations, queue tagging, and other management operations.

### Example: Producer IAM policy

Imagine a FastAPI application that only needs to send messages to an SQS queue.

It does not need permission to receive or delete messages.

A least-privilege policy could look like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:SendMessage",
        "sqs:SendMessageBatch"
      ],
      "Resource": "arn:aws:sqs:eu-west-2:123456789012:orders-queue"
    }
  ]
}
```

This policy allows the application to send messages but does not allow it to read messages, delete messages, or modify queue configuration.

### Example: Consumer IAM policy

A consumer application needs different permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "sqs:ReceiveMessage",
        "sqs:DeleteMessage",
        "sqs:ChangeMessageVisibility",
        "sqs:GetQueueAttributes"
      ],
      "Resource": "arn:aws:sqs:eu-west-2:123456789012:orders-queue"
    }
  ]
}
```

The consumer can receive and delete messages but cannot send new messages.

Important: Receiving a message does not automatically delete it. The consumer must explicitly call `DeleteMessage` after successfully processing it.

### IAM roles for AWS applications

Suppose you deploy your FastAPI application to ECS Fargate.

The recommended architecture is:

![A Quick Refresher on ECS Task Role vs Task Execution Role | by Yoshiyuki Watanabe | Medium](https://images.openai.com/static-rsc-4/7bMh8j_mV8LF8bzcgxhSpzNo8jUX-_hFRSq4LQhI-ID_oH1PkgLJAf6Xxua3klDI9mz9IHIWTqROdesOXuKhFXfZOFQFGuMjpPlHUWNCMq1sOqRn8I-02BQFY7F9wVrmF38N4NFuJmhedbitLELKpmntJMwsreDGMarwBLYYFQmq6RePY1mRWKsfcvtFRpRm?purpose=fullsize)

* Create an IAM task role.

* Attach the required SQS permissions.

* Associate the role with the ECS task definition.

* Run the application inside the ECS task.

* Boto3 automatically retrieves temporary credentials through the ECS container credentials provider.

* The application uses those credentials to access SQS.

Example:

```python
import boto3

sqs = boto3.client("sqs", region_name="eu-west-2")

response = sqs.send_message(
    QueueUrl="https://sqs.eu-west-2.amazonaws.com/123456789012/orders-queue",
    MessageBody='{"order_id": 1001}'
)

print(response["MessageId"])
```

Notice that there are no hardcoded access keys.

The SDK obtains credentials from the environment's supported AWS credential provider chain.

The same principle applies to Lambda execution roles and EC2 instance profiles.

### 3\. Identity-based policies and resource-based policies

There are two important policy mechanisms for controlling SQS access.

### Identity-based policies

An identity-based policy is attached to an IAM identity.

For example:

* IAM user.

* IAM role.

* IAM group.

It determines what the identity is allowed to do.

Example:

A role named `OrderProducerRole` has permission to send messages to `orders-queue`.

```json
{
  "Effect": "Allow",
  "Action": "sqs:SendMessage",
  "Resource": "arn:aws:sqs:eu-west-2:123456789012:orders-queue"
}
```

The policy is attached to the IAM role.

### Resource-based policies

A resource-based policy is attached directly to an AWS resource.

For SQS, this is commonly called a queue policy.

It determines which principals can access the queue and what actions they can perform.

For example, you can allow another AWS account to send messages to your queue without giving that account general access to your AWS environment.

### Comparison

| Feature         | Identity-based policy   | Resource-based policy                   |
| --------------- | ----------------------- | --------------------------------------- |
| Attached to     | IAM identity            | SQS queue                               |
| Defines         | What identity can do    | Who can access the queue                |
| Common use      | Application permissions | Cross-account access                    |
| Principal field | Usually not required    | Required for principal-based statements |
| Example         | Producer role           | Queue policy                            |

### How AWS evaluates access

An important concept is that an explicit `Deny` overrides an `Allow`.

Also, permissions boundaries, service control policies (SCPs), and other applicable policy controls can restrict access.

For cross-account access, the principal's account must authorize the operation, and the resource-owning account must allow access through the queue policy. Both sides must permit the operation.

For same-account access, either identity-based or resource-based permissions can authorize an operation, subject to applicable policy restrictions.

### 4\. Queue policies and cross-account access

One of the most useful SQS security features is the ability to allow another AWS account or AWS service to interact with your queue.

Let's consider two AWS accounts:

Account A

Queue owner

`orders-queue`

Account B

External application

`OrderProducerRole`

Cross-account SendMessage access

Account B wants to send messages to a queue owned by Account A.

You need two permissions:

* Account B's IAM identity policy must allow `sqs:SendMessage` on Account A's queue.

* Account A's queue policy must allow Account B's IAM role to send messages.

### Example: Queue resource policy

Attach this policy to `orders-queue` in Account A:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowExternalProducer",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::222222222222:role/OrderProducerRole"
      },
      "Action": [
        "sqs:SendMessage"
      ],
      "Resource": "arn:aws:sqs:eu-west-2:111111111111:orders-queue"
    }
  ]
}
```

Account B's role also needs an identity-based policy granting `sqs:SendMessage` on the same queue ARN.

This is cross-account resource sharing.

### Allowing AWS services to publish messages

You can also allow AWS services to send messages to your queue.

For example, an SNS topic can publish notifications to an SQS queue.

The queue policy could contain:

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
      "Resource": "arn:aws:sqs:eu-west-2:111111111111:orders-queue",
      "Condition": {
        "ArnEquals": {
          "aws:SourceArn": "arn:aws:sns:eu-west-2:111111111111:orders-topic"
        }
      }
    }
  ]
}
```

The `aws:SourceArn` condition ensures that only the specified SNS topic can publish to the queue through this statement.

This also helps protect against the confused deputy problem.

Important: When integrating AWS services with SQS, the queue policy and, when applicable, KMS key policy must authorize the service. Amazon Simple Queue Service +2

### 5\. Least-privilege access control

Least privilege means giving each identity only the permissions it needs to perform its responsibilities.

Imagine an order-processing architecture:

![How to Perform Systemic Threat Modelling — An Example | by Mehran Koushkebaghi | Nationwide Technology | Medium](https://images.openai.com/static-rsc-4/wiYCggHxEIvpJfGEBm5WlXYA0rEzlI_rDmoN7mfpWHERmK4CUvL0M40vR1oPbYy7ur2gUALYPYNwcTklKYrk3WruR1BnytD91IRpJGcfpc-SkV4a01aBiYlBmf0iB9yE8oQuQnt24J1NG89FyFpwAcemKM46EHXojHhEoVO_6zF666pnfXpeNp4HYGcqi8e6?purpose=fullsize)

You have three components:

* Order API: sends messages.

* Payment worker: receives and processes messages.

* Infrastructure administrator: manages queues.

Their permissions should be different.

| Component      | Required permissions                                                       |
| -------------- | -------------------------------------------------------------------------- |
| Order API      | SendMessage, SendMessageBatch                                              |
| Payment worker | ReceiveMessage, DeleteMessage, ChangeMessageVisibility, GetQueueAttributes |
| Administrator  | Queue creation, deletion, configuration, and policy management             |

The Order API should not have `DeleteQueue` or `PurgeQueue`.

The payment worker should not have permission to change the queue's resource policy.

### Additional security conditions

IAM policies can include conditions that restrict access based on request context.

Some useful SQS security conditions include:

| Condition key       | Purpose                                         |
| ------------------- | ----------------------------------------------- |
| aws:SecureTransport | Require HTTPS                                   |
| aws:SourceVpce      | Restrict access to a VPC endpoint               |
| aws:SourceVpc       | Restrict access to a VPC                        |
| aws:SourceArn       | Restrict access to a particular source resource |
| aws:PrincipalOrgID  | Restrict access to an AWS Organization          |

### Enforcing HTTPS

You can enforce encrypted connections through an SQS queue policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "sqs:*",
      "Resource": "arn:aws:sqs:eu-west-2:123456789012:orders-queue",
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

This explicitly denies requests that do not use secure transport.

### Security best practices

* Avoid wildcard permissions where possible.

* Separate producer and consumer roles.

* Use IAM roles instead of permanent access keys.

* Avoid public queue policies.

* Restrict cross-account access to specific principals.

* Use explicit denies for important security boundaries.

* Regularly review permissions and remove unused access.

AWS also supports partial attribute-based access control (ABAC) for SQS, allowing policies to use resource tags in authorization decisions. Amazon Simple Queue Service +1

### 6\. Server-side encryption with SQS-managed keys

Messages can contain sensitive information:

* Customer information.

* Payment processing events.

* Order details.

* Authentication events.

* Internal business data.

SQS supports server-side encryption (SSE) to protect message bodies at rest.

There are two primary options:

* SSE-SQS.

* SSE-KMS.

### How server-side encryption works

![Gestione degli accessi per code crittografate di Amazon SQS con politiche di privilegi minimi - Amazon Simple Queue Service](https://images.openai.com/static-rsc-4/Vw6Z-Ui0jQmAkjyNwl12xpnYVPwsWaLFZj1tYlTDCQ_eqWRCWGceibWO641MqlXbI31j1eSFPwNyJH9hDP1dt89fe6q8UB3pUBKiuPETjESU2vIA_-z43bIhpTpsA5N9pNzplCoAOQ5kDhYczq_2-fLJJeUrfUXHqWGZjto_l_eE50R5o0Ixeyj5SsZP6QdA?purpose=fullsize)

The general process:

* Producer sends a message.

* SQS receives the message.

* SQS encrypts the message body.

* The encrypted message is stored.

* An authorized consumer requests the message.

* SQS decrypts it and returns the plaintext message to the consumer.

The application does not need to implement encryption and decryption itself.

### SSE-SQS

SSE-SQS uses encryption keys managed by Amazon SQS.

Characteristics:

* AWS manages the encryption keys.

* No customer-managed KMS key is required.

* No additional KMS API permissions are required for producers and consumers.

* No additional KMS charges for this encryption option.

* Minimal key-management overhead.

For many ordinary messaging workloads, SSE-SQS is a good default.

Example using AWS CLI:

```bash
aws sqs create-queue \
  --queue-name orders-queue \
  --attributes SqsManagedSseEnabled=true \
  --region eu-west-2
```

### SSE-SQS versus SSE-KMS

| Feature                        | SSE-SQS                   | SSE-KMS                        |
| ------------------------------ | ------------------------- | ------------------------------ |
| Key management                 | SQS                       | AWS KMS                        |
| Customer-managed key           | No                        | Optional                       |
| Custom key policies            | No                        | Yes, for customer-managed keys |
| KMS API permissions            | Not required              | Required                       |
| Key usage auditing through KMS | No customer KMS key usage | Yes                            |
| Additional KMS charges         | No                        | Yes                            |
| Custom key control             | Limited                   | Extensive                      |

SSE-KMS can use either the AWS-managed SQS KMS key or a customer-managed KMS key. The greatest policy and lifecycle control comes with a customer-managed key.

### Important encryption limitation

SQS server-side encryption protects the message body, not every piece of queue or message metadata.

For example, message attributes and queue metadata are not encrypted by SQS SSE.

If sensitive information is placed in message attributes, consider application-level encryption or avoid putting sensitive data there.

Also, HTTPS is required for requests to queues with SSE enabled. Amazon Simple Queue Service +1

### 7\. AWS KMS customer-managed keys

AWS Key Management Service (KMS) allows you to create and manage cryptographic keys.

When you use SSE-KMS with a customer-managed key, you gain more control over encryption.

For example, imagine a financial application that processes payment events.

You might need:

* Centralized key management.

* Key rotation.

* Access restrictions.

* Auditability.

* Controlled key lifecycle.

* Separation of administrative and application permissions.

A customer-managed KMS key provides these capabilities.

### SSE-KMS architecture

![# 🚀 Introduction to AWS SQS (Simple Queue Service) - DEV Community](https://images.openai.com/static-rsc-4/kjL8gF1v-FL4qq8P7EoAQ8wmzhAuMWgadM2B1sW44scqqSUMrK9n0-I2Ea3_zmuCOg3UcrmHa9jFLTL9QXWygZbdJdBCO8yBPxLG2zu9eUrYq5BKQ8-8ZFCFAYjwZ915PllpZKaCRQgaeMAH_hm1ggpvLfL9ltWyHsuKioi2q20LRC_SZHmhysD7qZBH5Yja?purpose=fullsize)

SQS uses envelope encryption.

The simplified process is:

* SQS requests a data key from KMS.

* KMS generates a plaintext data key and an encrypted copy.

* SQS uses the plaintext data key to encrypt message data.

* SQS stores the encrypted message and encrypted data key.

* When an authorized consumer needs the message, SQS uses KMS to decrypt the data key.

* SQS decrypts the message and returns it.

The customer-managed KMS key protects the data keys, rather than directly encrypting every message body.

### Configuring SSE-KMS with AWS CLI

First, create a KMS key:

```bash
aws kms create-key \
  --description "SQS orders queue encryption key" \
  --region eu-west-2
```

Retrieve the key ARN from the response.

Then create the queue:

```bash
aws sqs create-queue \
  --queue-name encrypted-orders-queue \
  --attributes '{
    "KmsMasterKeyId":"arn:aws:kms:eu-west-2:123456789012:key/KEY-ID",
    "KmsDataKeyReusePeriodSeconds":"300"
  }' \
  --region eu-west-2
```

`KmsDataKeyReusePeriodSeconds` controls how long SQS can reuse a data key before requesting a new one.

This setting has implications for both security and KMS request costs.

### Important KMS permissions

For a customer-managed key, producers and consumers need appropriate KMS permissions.

| Principal         | Important KMS permission            |
| ----------------- | ----------------------------------- |
| Producer          | kms:GenerateDataKey and kms:Decrypt |
| Consumer          | kms:Decrypt                         |
| Key administrator | Key administration permissions      |

The exact permissions depend on the integration and the way the key policy is configured.

For example, an application role might have:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "kms:GenerateDataKey",
        "kms:Decrypt"
      ],
      "Resource": "arn:aws:kms:eu-west-2:123456789012:key/KEY-ID"
    }
  ]
}
```

Important: An IAM permission alone might not be sufficient. The KMS key policy must also authorize the relevant principal or delegate authorization to IAM policies.

KMS authorization is a common reason for receiving `AccessDenied` errors when working with encrypted SQS queues. Amazon Simple Queue Service +2

### 8\. VPC endpoints and private SQS access

By default, applications can access SQS through its regional public service endpoint.

However, consider an application running inside a private subnet.

You might not want this application to require:

* A public IP address.

* An Internet Gateway.

* A NAT Gateway.

* Internet connectivity just to communicate with SQS.

AWS provides VPC interface endpoints, powered by AWS PrivateLink, to solve this problem.

### What is an SQS VPC endpoint?

A VPC endpoint provides private connectivity between your VPC and the SQS service.

Instead of routing SQS API traffic through the public internet, your application communicates with SQS through private IP addresses associated with endpoint network interfaces.

![テクニカルインストラクターと学ぶインターフェース型とゲートウェイ型の VPC エンドポイント - builders.flash☆ - 変化を求めるデベロッパーを応援するウェブマガジン | AWS](https://images.openai.com/static-rsc-4/zDCk_bNg2OH0D1LACehl8MY0VRcqbQmkou6IJA8d36c2eerXUqYIRICSIrwHubw4LAfQpQFLq9MB1Z9tilpvXgme6lGLXbd_wWmZZnYtu7jXM51z58D8zjFtNSEbW1M0PmqDLhTS4457eaZqpvlQ_BF_AJgAmA8KR4jMyU8mo2Q1peVhmIh71jlv_eC3z-dW?purpose=fullsize)

### Architecture

Imagine this infrastructure:

* VPC: `10.0.0.0/16`

* Private subnet: `10.0.1.0/24`

* ECS Fargate application.

* SQS orders queue.

* SQS interface VPC endpoint.

The communication flow:

* ECS runs inside the private subnet.

* The application creates a Boto3 SQS client.

* DNS resolves the regional SQS endpoint to private endpoint IP addresses when private DNS is enabled.

* Traffic travels through the VPC endpoint.

* SQS receives the request without requiring an internet gateway or NAT gateway for that SQS connection.

### Creating an SQS VPC endpoint

Using AWS CLI:

```bash
aws ec2 create-vpc-endpoint \
  --vpc-id vpc-0123456789abcdef0 \
  --service-name com.amazonaws.eu-west-2.sqs \
  --vpc-endpoint-type Interface \
  --subnet-ids subnet-11111111 subnet-22222222 \
  --security-group-ids sg-0123456789abcdef0 \
  --private-dns-enabled \
  --region eu-west-2
```

The endpoint uses:

`com.amazonaws.eu-west-2.sqs`

The endpoint security group should allow inbound HTTPS (TCP 443) from the application security group.

### VPC endpoint policies

A VPC endpoint policy controls which principals and SQS resources can be accessed through that endpoint.

For example, you can restrict the endpoint to allow only a particular IAM role to send messages to a particular queue.

Remember that an endpoint policy does not replace IAM policies or SQS queue policies. It is an additional authorization layer.

### Restricting queue access to a VPC endpoint

You can also add a condition to an SQS queue policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyOutsideApprovedVPCEndpoint",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "sqs:*",
      "Resource": "arn:aws:sqs:eu-west-2:123456789012:orders-queue",
      "Condition": {
        "StringNotEquals": {
          "aws:SourceVpce": "vpce-0123456789abcdef0"
        }
      }
    }
  ]
}
```

This denies requests that do not originate through the specified VPC endpoint.

Be careful when applying this policy: it can also block legitimate administrative or service integrations that access the queue through other paths.

Plan and test your access paths before enforcing the restriction.

When should you use VPC endpoints?

* ECS applications in private subnets.

* EC2-based message consumers.

* Private enterprise applications.

* Applications with strict network security requirements.

* Environments where outbound internet access should be minimized.

Amazon Simple Queue Service +2

### 9\. Secrets, credentials, and secure application integration

An application needs AWS credentials to communicate with SQS.

One of the most important security principles is:

Never hardcode AWS access keys inside application source code.

Consider this bad example:

```python
import boto3

sqs = boto3.client(
    "sqs",
    aws_access_key_id="AKIA...",
    aws_secret_access_key="MY_SECRET_KEY"
)
```

This creates several security problems:

* Credentials can leak through Git repositories.

* Developers may accidentally share credentials.

* Keys may remain valid for a long time.

* Credential rotation becomes difficult.

* Multiple environments may share the same credentials.

### Preferred authentication methods

Use the appropriate AWS credential mechanism for your execution environment.

| Environment       | Recommended authentication             |
| ----------------- | -------------------------------------- |
| AWS Lambda        | Lambda execution role                  |
| ECS Fargate       | ECS task role                          |
| EC2               | EC2 instance profile                   |
| EKS               | EKS Pod Identity or IRSA               |
| Local development | AWS CLI profiles / IAM Identity Center |
| GitHub Actions    | OIDC federation with IAM role          |

These approaches provide temporary credentials rather than requiring permanent access keys in application configuration.

### Boto3 credential provider chain

Boto3 automatically searches supported credential providers.

For example:

```python
import boto3

sqs = boto3.client(
    "sqs",
    region_name="eu-west-2"
)
```

You do not need to manually supply credentials when running in an appropriately configured AWS environment.

For local development, you can configure an AWS CLI profile:

```bash
aws configure --profile development
```

Then:

```bash
export AWS_PROFILE=development
export AWS_REGION=eu-west-2
```

Your Python application can use the configured credentials.

### AWS Secrets Manager versus IAM roles

An important distinction:

IAM roles manage AWS authentication. Secrets Manager stores application secrets.

For example, your application might need:

* Database passwords.

* Third-party API tokens.

* External service credentials.

* Application-specific encryption secrets.

These can be stored in AWS Secrets Manager.

Your application receives permission to retrieve only the required secrets.

Example:

```python
import boto3
import json

secrets = boto3.client(
    "secretsmanager",
    region_name="eu-west-2"
)

response = secrets.get_secret_value(
    SecretId="production/database"
)

secret = json.loads(response["SecretString"])

print(secret["username"])
```

Do not confuse application secrets with AWS access credentials.

For SQS access, prefer IAM roles and temporary credentials.

### Secure FastAPI + SQS architecture

Consider a production order-processing system:

![ECS(Fargate)でコンテナアプリケーションを動かすための設定情報の扱い方 - BASEプロダクトチームブログ](https://images.openai.com/static-rsc-4/mEAebQjaioKW_557W9oY8mPuwMROXPU5oXIRFL1Sjaf_jo-DFRvApfnaOQXunTiuZDeSOZt83gQHaGXgIC_QjM43JOQnhMsPqzZghydG9A3WmYDSSWnHltmOpz36h7hkSrBtTrNs7YmbpOXrQuX8ugTVO39wKLsDhvzgXmrTaZYsr_u9T1sGENn0x5z6osXr?purpose=fullsize)

The architecture could look like this:

* FastAPI runs inside ECS Fargate.

* ECS assigns an IAM task role to the application.

* FastAPI sends order events to SQS using Boto3.

* SQS encrypts messages at rest.

* An SQS interface endpoint provides private connectivity.

* A separate ECS consumer processes messages.

* The consumer has its own IAM task role with receive and delete permissions.

* Application-specific secrets are retrieved from Secrets Manager.

* CloudWatch monitors the application and queue.

This architecture separates authentication, authorization, encryption, networking, and application secrets.

### 10\. Infrastructure as Code with Pulumi

Since we are using Pulumi Python throughout our AWS learning path, SQS security should also be managed through infrastructure as code.

For example, a production SQS infrastructure definition should manage:

* Queue configuration.

* Server-side encryption.

* IAM roles and policies.

* Queue resource policies.

* KMS keys and key policies, when needed.

* VPC endpoints.

* Security groups.

* CloudWatch monitoring.

A simplified example of creating an encrypted SQS queue with Pulumi:

```python
import pulumi
import pulumi_aws as aws

queue = aws.sqs.Queue(
    "orders-queue",
    name="orders-queue",
    sqs_managed_sse_enabled=True,
    visibility_timeout_seconds=60,
    message_retention_seconds=345600
)

pulumi.export("queue_url", queue.url)
pulumi.export("queue_arn", queue.arn)
```

This creates a queue with SQS-managed server-side encryption enabled.

For more advanced deployments, you can replace SSE-SQS with SSE-KMS by configuring a customer-managed KMS key and its permissions.

Pulumi is also useful for keeping security configurations consistent across development, staging, and production stacks.

### 11\. Putting everything together: Production security architecture

Let's combine the concepts from this module.

![ECS FargateでVPCエンドポイントを使用する](https://images.openai.com/static-rsc-4/hem6F8VbnoZWVmGZ5LY009QOeAyelu-kdyQKRd9CAVabAo9J8RKaoRv9zL5aA1DRTQ5BMvKclpOb-nbPH441mHJofFOgzNaFzCWUUKUBYZ4DEBr4CEWZEnWQd-cx4KbaU_Of-pPxO3da_QDYDPec8h7UmEsyG8etNjw0MvBQIgboAZ12QraBpg-Vefg6G6-a?purpose=fullsize)

Imagine an order-processing platform with two applications:

Producer

* FastAPI running on ECS Fargate.

* IAM task role with `sqs:SendMessage`.

* Private SQS connectivity.

* No hardcoded AWS credentials.

Consumer

* ECS Fargate worker.

* Separate IAM task role.

* `ReceiveMessage`, `DeleteMessage`, and `ChangeMessageVisibility` permissions.

* Processes messages and acknowledges successful processing.

SQS

* Server-side encryption enabled.

* Customer-managed KMS key if additional key control is required.

* Queue policy restricting unauthorized principals.

* VPC endpoint restrictions where appropriate.

Monitoring and auditing

* CloudWatch metrics and alarms.

* CloudTrail API auditing.

* KMS key usage auditing.

### Security checklist

| Security requirement  | Recommended configuration          |
| --------------------- | ---------------------------------- |
| Authentication        | IAM roles                          |
| Authorization         | Least-privilege IAM policies       |
| Cross-account access  | Queue policies + IAM authorization |
| Encryption at rest    | SSE-SQS or SSE-KMS                 |
| Encryption in transit | HTTPS/TLS                          |
| Key management        | AWS KMS                            |
| Private connectivity  | VPC interface endpoint             |
| Application secrets   | Secrets Manager                    |
| Auditing              | CloudTrail                         |
| Monitoring            | CloudWatch                         |

### 12\. Important concepts to remember

| Concept               | Main takeaway                                               |
| --------------------- | ----------------------------------------------------------- |
| IAM identity policy   | Defines permissions granted to an identity                  |
| SQS queue policy      | Controls access to a particular queue                       |
| Cross-account access  | Requires authorization from both accounts                   |
| Least privilege       | Grant only necessary actions on specific resources          |
| SSE-SQS               | Encryption managed by SQS                                   |
| SSE-KMS               | Encryption integrated with AWS KMS                          |
| KMS key policy        | Controls access to the encryption key                       |
| Envelope encryption   | Uses data keys protected by a KMS key                       |
| VPC endpoint          | Provides private connectivity to SQS                        |
| Secrets Manager       | Stores application secrets, not a replacement for IAM roles |
| Temporary credentials | Avoid long-lived AWS access keys                            |

### Official AWS documentation

These are the most useful references for this module:

* [Amazon SQS Security Best Practices](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-security-best-practices.html?utm_source=chatgpt.com)

* [How Amazon SQS Works with IAM](https://docs.aws.amazon.com/en_en/AWSSimpleQueueService/latest/SQSDeveloperGuide/security_iam_service-with-iam.html?utm_source=chatgpt.com)

* [Encryption at Rest in Amazon SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-server-side-encryption.html?utm_source=chatgpt.com)

* [Amazon SQS Key Management](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-key-management.html?utm_source=chatgpt.com)

* [Least-Privilege Policies for Encrypted SQS Queues](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/sqs-least-privilege-policy.html?utm_source=chatgpt.com)

* [Infrastructure Security in Amazon SQS](https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/infrastructure-security.html?utm_source=chatgpt.com)

Module 5 complete.

The most important architectural lesson is that SQS security is not just about IAM permissions. A production system needs multiple complementary security layers: identity, resource authorization, encryption, network isolation, and secure credential management.

The next module is Module 6 — SQS Monitoring, Scaling, Integrations, and Production Architectures, where we will bring SQS together with Lambda, ECS, SNS, EventBridge, and CloudWatch.
