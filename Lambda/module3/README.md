### Module 3 — Lambda Security, IAM, and VPC Networking

AWS Lambda · Intermediate · Security and Networking

This module focuses on how AWS Lambda securely accesses AWS services, external resources, and private infrastructure inside a VPC.

One of the most important concepts to understand is that Lambda has two different permission directions:

* Execution role: Determines what the Lambda function is allowed to access.

* Resource-based policy: Determines who or what is allowed to invoke the Lambda function.

You will also learn how Lambda connects to private databases, accesses secrets, communicates with AWS services without public internet access, and manages network connectivity.

### 1\. Lambda Security Architecture and Shared Responsibility

### 1.1 Understanding Lambda security

AWS Lambda is a managed compute service. AWS manages the underlying infrastructure, while you manage the security configuration of your functions and their integrations.

Lambda security can be divided into several layers:

| Security layer          | Responsibility                                                              |
| ----------------------- | --------------------------------------------------------------------------- |
| Infrastructure security | AWS manages physical infrastructure and underlying hosts.                   |
| Execution environment   | AWS manages the Lambda execution environment and isolation.                 |
| Identity and access     | You configure IAM roles and policies.                                       |
| Application security    | You secure Python code, dependencies, and input validation.                 |
| Data protection         | You configure encryption and access to sensitive data.                      |
| Network security        | You configure VPC connectivity, subnets, and security groups when required. |
| Monitoring              | You configure logging, auditing, and security monitoring.                   |

### 1.2 Shared responsibility model

Consider a Lambda function that processes customer orders.

AWS is responsible for:

* Physical data center security.

* Host operating system maintenance.

* Infrastructure patching.

* Runtime execution environment infrastructure.

* Isolation between execution environments.

You are responsible for:

* Writing secure application code.

* Configuring execution permissions.

* Protecting database credentials.

* Controlling access to S3 buckets.

* Configuring network access.

* Managing dependencies and vulnerabilities.

* Monitoring suspicious application activity.

Important: Managed serverless infrastructure does not mean that your application is automatically secure. Incorrect IAM permissions, exposed secrets, and insecure application code can still create serious vulnerabilities.

### 1.3 Lambda execution environment isolation

Lambda executes functions inside managed execution environments.

Each environment provides:

* An isolated runtime environment.

* Memory allocated to the function.

* Temporary local storage.

* Runtime and application dependencies.

* Network connectivity according to the function's configuration.

Execution environments can be reused across multiple invocations.

This has an important security implication: global variables and initialized objects can remain available between invocations within the same environment.

For example:

```python
# Global scope
customer_data = {}

def lambda_handler(event, context):
    customer_id = event["customer_id"]

    customer_data[customer_id] = {
        "processed": True
    }

    return {"statusCode": 200}
```

You should avoid storing sensitive, user-specific information in global mutable variables because execution environments can be reused.

A safer approach is to keep request-specific information inside the handler or its invocation-specific functions.

### 2\. Lambda Execution Roles and IAM Policies

### 2.1 What is a Lambda execution role?

A Lambda execution role is an IAM role that Lambda assumes when executing your function.

It determines which AWS resources the function can access.

For example, suppose you develop a Lambda function that:

* Receives an S3 object event.

* Downloads the uploaded file.

* Processes the file.

* Stores the result in another S3 bucket.

The function needs permission to read from the source bucket and write to the destination bucket.

Instead of embedding AWS access keys inside your Python code, you attach an IAM execution role to the function.

The execution flow looks like this:

AWS Lambda Function

Python application

Assumes execution role

IAM Execution Role

Trust policy + permission policies

Temporary AWS credentials

Amazon S3

Read objects

DynamoDB

Write records

Lambda automatically obtains temporary credentials through its execution role. The AWS SDK can use these credentials without you manually managing access keys.

### 2.2 Trust policy

An IAM role has a trust policy that defines which principal is allowed to assume it.

For Lambda, the trusted service principal is:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "lambda.amazonaws.com"
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

This allows the Lambda service to assume the role.

Notice that the trust policy does not grant access to S3, DynamoDB, or other AWS services. It only establishes who can assume the role.

### 2.3 Permission policies

Permission policies define what the assumed role can do.

For example, a Lambda function that reads objects from one S3 bucket might use:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::my-source-bucket/*"
    }
  ]
}
```

This policy allows reading objects from the specified bucket.

It does not allow:

* Uploading objects.

* Deleting objects.

* Accessing unrelated buckets.

* Modifying bucket configurations.

This is an example of least-privilege access.

### 2.4 Basic execution permissions

A typical Lambda execution role requires CloudWatch logging permissions.

AWS provides the managed policy:

`AWSLambdaBasicExecutionRole`

It allows the function to create log streams and publish logs to CloudWatch Logs.

You should understand the difference between:

* `AWSLambdaBasicExecutionRole`: Basic logging.

* `AWSLambdaVPCAccessExecutionRole`: Permissions needed for Lambda's VPC network interface operations.

* Custom IAM policies: Permissions for application-specific resources.

These managed policies are convenient starting points, but production roles should still be reviewed for unnecessary permissions.

### 3\. Resource-Based Policies and Function Permissions

Execution roles control what Lambda can access. Resource-based policies control who can invoke Lambda.

This distinction is fundamental.

### 3.1 Understanding resource-based policies

Suppose you have a Lambda function named:

`order-processor`

You want Amazon S3 to invoke this function whenever a new object is uploaded.

The S3 service needs permission to invoke the Lambda function.

You grant this through a resource-based policy attached to the Lambda function.

A simplified policy statement looks like this:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "s3.amazonaws.com"
      },
      "Action": "lambda:InvokeFunction",
      "Resource": "*",
      "Condition": {
        "ArnLike": {
          "AWS:SourceArn": "arn:aws:s3:::my-upload-bucket"
        }
      }
    }
  ]
}
```

The source ARN condition restricts invocation to the specified bucket.

In production, use the function's actual ARN and apply an appropriate source account condition where supported.

### 3.2 Execution policy versus resource policy

| Feature        | Execution role        | Resource-based policy         |
| -------------- | --------------------- | ----------------------------- |
| Attached to    | IAM role              | Lambda function               |
| Controls       | Outbound access       | Inbound invocation            |
| Example        | Lambda reads S3       | S3 invokes Lambda             |
| Main identity  | Lambda execution role | Invoking service or principal |
| Typical action | s3:GetObject          | lambda:InvokeFunction         |

### 3.3 Common Lambda invocation permissions

Different services use different integration mechanisms.

Examples:

* S3 event notifications: Lambda resource-based permission.

* SNS subscriptions: Lambda resource-based permission.

* EventBridge rules: Lambda resource-based permission.

* API Gateway: Lambda resource-based permission or an applicable authorization arrangement.

* SQS event source mappings: The Lambda execution role needs permissions to consume messages from the queue.

This last example is particularly important: SQS event source mappings use Lambda-managed polling, so the execution role needs queue consumption permissions.

For example:

```json
{
  "Effect": "Allow",
  "Action": [
    "sqs:ReceiveMessage",
    "sqs:DeleteMessage",
    "sqs:GetQueueAttributes"
  ],
  "Resource": "arn:aws:sqs:eu-west-1:123456789012:orders"
}
```

### 4\. Least-Privilege Access and Permission Boundaries

### 4.1 Principle of least privilege

Least privilege means granting only the permissions necessary to perform a specific task.

Consider three Lambda functions:

| Function               | Required permissions                                  |
| ---------------------- | ----------------------------------------------------- |
| Image processor        | Read from source S3 bucket, write to processed bucket |
| Order processor        | Read/write specific DynamoDB tables                   |
| Notification processor | Publish to a specific SNS topic                       |

A poor architecture would assign all three functions the same powerful IAM role.

A better architecture gives each function its own execution role.

This reduces the potential impact if one function is compromised.

### 4.2 IAM permission boundaries

A permission boundary establishes the maximum permissions that an IAM principal can receive through identity-based policies.

For example:

* An execution role has an identity policy allowing S3, DynamoDB, and SNS access.

* Its permission boundary allows only S3 and DynamoDB access.

The effective permissions cannot exceed the boundary.

A simplified conceptual model:

\\text{Effective permissions}
=
\\text{Identity permissions}
\\cap
\\text{Permission boundary}

This is useful in larger AWS environments where teams can create roles but must remain within centrally defined security limits.

Important: Permission boundaries are not standalone permission grants. They limit permissions rather than granting them.

You should also understand how SCPs, explicit denies, session policies, and resource policies affect effective access.

### 5\. Lambda Access to AWS Services

Lambda frequently interacts with other AWS services.

The AWS SDK for Python, known as Boto3, provides a convenient interface for these integrations.

### 5.1 Accessing Amazon S3

Consider a Lambda function that downloads an object from S3.

```python
import boto3

s3 = boto3.client("s3")

def lambda_handler(event, context):
    bucket = event["bucket"]
    key = event["key"]

    response = s3.get_object(
        Bucket=bucket,
        Key=key
    )

    content = response["Body"].read()

    return {
        "statusCode": 200,
        "size": len(content)
    }
```

The execution role needs:

```text
s3:GetObject
```

on the appropriate bucket objects.

For encrypted objects, it may also need `kms:Decrypt` permissions on the relevant KMS key, subject to the key policy.

### 5.2 Accessing DynamoDB

Lambda can interact with DynamoDB using Boto3.

```python
import boto3

dynamodb = boto3.resource("dynamodb")

table = dynamodb.Table("Orders")

def lambda_handler(event, context):
    table.put_item(
        Item={
            "order_id": event["order_id"],
            "status": "processed"
        }
    )

    return {
        "statusCode": 200
    }
```

The execution role needs an appropriate permission such as:

```text
dynamodb:PutItem
```

The permissions should be scoped to the required table.

### 5.3 Accessing SQS

A Lambda function can interact with SQS in two different ways:

* It can call SQS APIs directly using Boto3.

* It can be configured with an SQS event source mapping.

For direct API calls:

```python
import boto3
import json

sqs = boto3.client("sqs")

def lambda_handler(event, context):
    sqs.send_message(
        QueueUrl="https://sqs.eu-west-1.amazonaws.com/123456789012/orders",
        MessageBody=json.dumps(event)
    )

    return {"statusCode": 200}
```

The execution role requires:

```text
sqs:SendMessage
```

For an SQS event source mapping, the role needs the relevant message consumption permissions instead.

### 5.4 Accessing SNS

Lambda can publish notifications to SNS topics.

```python
import boto3

sns = boto3.client("sns")

def lambda_handler(event, context):
    sns.publish(
        TopicArn="arn:aws:sns:eu-west-1:123456789012:orders",
        Message="Order processed successfully"
    )

    return {"statusCode": 200}
```

The execution role needs:

```text
sns:Publish
```

on the relevant topic.

### 5.5 Understanding the integration pattern

Lambda Function

Python + Boto3

S3

GetObject / PutObject

DynamoDB

GetItem / PutItem

SQS

SendMessage / ReceiveMessage

SNS

Publish

Each integration requires the appropriate IAM permissions.

A key distinction: Lambda does not necessarily need to run inside a VPC to access AWS services. Many AWS services have public service endpoints that Lambda can access through the AWS-managed networking environment.

VPC configuration becomes important when your function needs access to private resources or when you want to control network paths.

### 6\. AWS KMS Integration and Environment Variable Encryption

### 6.1 Understanding AWS KMS

AWS Key Management Service (KMS) is a managed service that allows you to create, manage, and control cryptographic keys.

Lambda often needs to handle sensitive information, such as:

* Database credentials.

* API tokens.

* Third-party service credentials.

* Encryption keys.

* Application configuration containing confidential information.

KMS helps protect this information through encryption and access control.

### 6.2 Lambda environment variable encryption

Lambda supports environment variables for application configuration.

For example:

```text
DB_HOST=database.internal
DB_USERNAME=app_user
DB_PASSWORD=secret_password
API_KEY=your_api_key
```

Environment variables are encrypted at rest by default using AWS-managed encryption.

You can also configure a customer-managed KMS key instead of relying on the default AWS-managed key.

This provides additional control over:

* Key policies.

* Key administrators.

* Key usage permissions.

* Key rotation.

* Auditing through CloudTrail.

### 6.3 AWS-managed keys versus customer-managed keys

| Feature             | AWS-managed key                   | Customer-managed key                            |
| ------------------- | --------------------------------- | ----------------------------------------------- |
| Key management      | AWS                               | You control configuration                       |
| Key policies        | Limited customization             | Full policy control                             |
| Rotation            | AWS-managed                       | Configurable                                    |
| CloudTrail auditing | Available for relevant operations | More granular key-use auditing                  |
| Cost                | No separate KMS key charge        | KMS charges apply                               |
| Typical usage       | General encryption                | Sensitive workloads and compliance requirements |

### 6.4 How Lambda uses KMS

Suppose you configure a Lambda function with a customer-managed KMS key.

The architecture looks like this:

Lambda Configuration

Environment variables

Encryption using KMS

Customer-managed KMS key

Encrypted configuration stored

Lambda Execution Environment

Application receives configuration values

Lambda supports two relevant encryption approaches:

Standard encryption

Lambda encrypts environment variables at rest and makes them available to the function at runtime.

Encryption helpers

You can use Lambda's encryption helpers to encrypt sensitive environment variable values in the console and explicitly decrypt them in your application using KMS.

This can provide an additional security boundary, especially when access to the function configuration and access to plaintext secrets need to be separated.

### 6.5 KMS permissions

Depending on the encryption configuration, the relevant IAM principal needs permissions such as:

* `kms:Decrypt`

* `kms:Encrypt`

* `kms:GenerateDataKey`

* `kms:CreateGrant`

Do not automatically grant every KMS permission. The required actions depend on the operation and integration.

Also remember that KMS authorization involves both IAM policies and the KMS key policy.

Security recommendation: Environment variables are useful for non-sensitive configuration, but do not treat them as a full secrets-management solution. For database passwords, API tokens, and frequently rotated credentials, use Secrets Manager or Parameter Store.

### 7\. Secrets Manager and Systems Manager Parameter Store Integration

Lambda applications frequently need sensitive configuration values.

AWS provides two important services for this purpose:

* AWS Secrets Manager.

* AWS Systems Manager Parameter Store.

Both can store configuration centrally and allow Lambda functions to retrieve values securely.

### 7.1 AWS Secrets Manager

Secrets Manager is designed specifically for storing, managing, retrieving, and rotating secrets.

Common examples include:

* Database usernames and passwords.

* API credentials.

* OAuth client secrets.

* Third-party application credentials.

* Service authentication tokens.

For example, imagine a Lambda function that connects to an RDS PostgreSQL database.

Instead of placing the database password inside the Lambda environment variables, store the credentials in Secrets Manager.

The application retrieves them when needed.

### Architecture

Lambda Function

Python application

GetSecretValue API

AWS Secrets Manager

Encrypted database credentials

Retrieve credentials

Amazon RDS PostgreSQL

Database authentication

### 7.2 Retrieving secrets with Python

Boto3 provides a Secrets Manager client.

```python
import boto3
import json

secrets = boto3.client("secretsmanager")

def get_database_credentials():
    response = secrets.get_secret_value(
        SecretId="production/database"
    )

    return json.loads(response["SecretString"])

def lambda_handler(event, context):
    credentials = get_database_credentials()

    username = credentials["username"]
    password = credentials["password"]

    return {
        "statusCode": 200,
        "message": "Credentials retrieved"
    }
```

The Lambda execution role needs:

```text
secretsmanager:GetSecretValue
```

on the specific secret.

If the secret uses a customer-managed KMS key, the function also needs appropriate KMS decryption authorization.

### 7.3 Secret rotation

One of the most valuable Secrets Manager features is automatic secret rotation.

For example:

* A database password is initially stored in Secrets Manager.

* A rotation schedule is configured.

* Secrets Manager initiates a rotation workflow.

* The database credential is changed.

* The new credential is stored in Secrets Manager.

* Lambda retrieves the updated credential.

This reduces the need for manually managing long-lived credentials.

However, your application must handle rotation correctly. Cached credentials can become stale, and existing database connections may need to be recreated.

### 7.4 Systems Manager Parameter Store

Parameter Store is a centralized configuration management service.

It supports several parameter types:

| Type         | Description                    |
| ------------ | ------------------------------ |
| String       | Regular text configuration     |
| StringList   | Comma-separated string values  |
| SecureString | Encrypted configuration values |

Example parameters:

```text
/application/production/database-host
/application/production/database-port
/application/production/log-level
/application/production/api-key
```

SecureString parameters use KMS encryption.

### Retrieving parameters with Python

```python
import boto3

ssm = boto3.client("ssm")

def get_api_key():
    response = ssm.get_parameter(
        Name="/application/production/api-key",
        WithDecryption=True
    )

    return response["Parameter"]["Value"]

def lambda_handler(event, context):
    api_key = get_api_key()

    return {
        "statusCode": 200,
        "message": "Configuration retrieved"
    }
```

The execution role needs:

```text
ssm:GetParameter
```

For SecureString parameters encrypted with a customer-managed key, it also needs appropriate `kms:Decrypt` permission.

### 7.5 Secrets Manager versus Parameter Store

| Feature                        | Secrets Manager             | Parameter Store                                                                 |
| ------------------------------ | --------------------------- | ------------------------------------------------------------------------------- |
| Main purpose                   | Secrets management          | Configuration management                                                        |
| Secret rotation                | Built-in rotation workflows | Requires custom automation                                                      |
| Secure storage                 | Yes                         | Yes, using SecureString                                                         |
| Hierarchical naming            | Yes                         | Yes                                                                             |
| Versioning                     | Yes                         | Yes                                                                             |
| Database credential management | Strong integration          | Possible, but less specialized                                                  |
| Configuration storage          | Yes                         | Particularly suitable                                                           |
| Cost model                     | Generally higher            | Standard parameters have no additional charge; advanced features may cost extra |

### Which should you use?

* Use Secrets Manager for database credentials, API secrets, and credentials requiring rotation.

* Use Parameter Store for application settings, feature configuration, environment-specific values, and simpler encrypted parameters.

For production applications, you should also consider caching retrieved values to reduce API calls and latency. Make sure the cache duration is compatible with your secret rotation requirements.

### 8\. VPC Networking Fundamentals for Lambda

### 8.1 What is a VPC?

A Virtual Private Cloud (VPC) is an isolated virtual network in AWS.

It allows you to define:

* IP address ranges.

* Subnets.

* Route tables.

* Internet gateways.

* NAT gateways.

* Security groups.

* Network ACLs.

* VPC endpoints.

Suppose you deploy a production application with:

* Lambda functions.

* An RDS PostgreSQL database.

* An ElastiCache Redis cluster.

* Private application resources.

You might want your Lambda functions to communicate with these resources without exposing them to the public internet.

This is where VPC integration becomes important.

### 8.2 Why connect Lambda to a VPC?

By default, Lambda functions execute in an AWS-managed network environment.

They can communicate with publicly accessible AWS service endpoints and internet destinations without requiring you to attach them to your VPC.

However, they cannot directly access private resources in your VPC unless you configure VPC connectivity.

Typical reasons for VPC integration include:

* Connecting to private RDS databases.

* Accessing private EC2 instances.

* Communicating with ElastiCache.

* Accessing internal application services.

* Connecting to private network resources.

* Using private AWS service endpoints.

### 8.3 VPC architecture

Consider this architecture:

![aws lambda - freeCodeCamp.org](https://images.openai.com/static-rsc-4/xG1PH1GWdBgCeYGuQS7KrpVaT9S5BO0yH279hRB3kSFzBiZNQWRRMGesAo9QkT1_m4PB5dL3v9aE-eiS0HjnLF0jnOTiYNurVhNINEH2jpvZVunWBYqfBTryuIbDVy8qyKIvQ994zMu5EK-X8Xk7lcsIxcQGVaqUeLKB-tKgLIf5d9Xd0-excvYZlC0Joaop?purpose=fullsize)

Your Lambda function is associated with selected subnets and security groups.

It can then communicate with resources reachable through the VPC network.

For example:

```text
Lambda Function
      |
      v
VPC Networking
      |
      +---- Private RDS PostgreSQL
      |
      +---- ElastiCache Redis
      |
      +---- Internal EC2 Application
      |
      +---- VPC Endpoints
```

An important distinction: placing Lambda inside a VPC does not mean that Lambda becomes a traditional EC2 instance. AWS continues to manage its execution environment.

### 9\. Lambda VPC Configuration and Subnet Selection

### 9.1 Configuring VPC access

When configuring VPC connectivity, you specify:

* The VPC.

* One or more subnets.

* One or more security groups.

Lambda uses these settings to establish network connectivity through managed network interfaces.

For example:

```text
VPC: production-vpc

Subnets:
  - private-subnet-a
  - private-subnet-b

Security Groups:
  - lambda-security-group
```

You should generally select private subnets across multiple Availability Zones for production workloads.

This provides network-level placement flexibility and helps support highly available architectures.

### 9.2 Lambda Hyperplane ENIs

One important technical detail is how Lambda establishes network connectivity.

Lambda uses Hyperplane Elastic Network Interfaces (ENIs) to connect execution environments to your VPC.

Unlike a traditional EC2 deployment where each instance has its own network interface, Lambda can share Hyperplane ENIs across functions using the same subnet and security group combination.

This provides efficient networking at scale.

The important concepts are:

* Lambda manages the network interfaces.

* You select the subnets and security groups.

* Lambda establishes connectivity through Hyperplane ENIs.

* AWS handles the underlying networking infrastructure.

### 9.3 Subnet selection

You should understand the difference between public and private subnets.

| Feature                          | Public subnet                                   | Private subnet                                  |
| -------------------------------- | ----------------------------------------------- | ----------------------------------------------- |
| Direct route to Internet Gateway | Yes                                             | No                                              |
| Public internet access           | Requires suitable public addressing and routing | Usually through NAT or another controlled path  |
| Typical resources                | Internet-facing ALB, NAT Gateway                | Lambda connectivity, RDS, internal applications |
| Direct public inbound access     | Depends on resource configuration               | Not directly through an Internet Gateway        |

Important: Attaching Lambda to a public subnet does not automatically give it internet access or a public IP address.

This is a common misconception.

For Lambda, public internet egress generally requires a NAT Gateway or another suitable network egress architecture.

### 10\. Security Groups and Network Access

### 10.1 What is a security group?

A security group is a stateful virtual firewall associated with network interfaces and supported AWS resources.

It controls inbound and outbound network traffic.

For Lambda VPC connectivity, the security group determines which network connections the function can establish and which responses are allowed.

Consider a Lambda function connecting to an RDS PostgreSQL database.

The database listens on TCP port 5432.

You could configure the security groups as follows:

Lambda security group

\- Outbound TCP 5432 to the database security group.

RDS security group

\- Inbound TCP 5432 from the Lambda security group.

Lambda Security Group

Outbound TCP 5432

TCP 5432

RDS Security Group

Inbound from Lambda security group

RDS PostgreSQL

Private database

The database does not need to be publicly accessible.

### 10.2 Security group references

Instead of allowing traffic from an entire CIDR range, you can reference another security group.

For example:

```text
Inbound rule:

Protocol: TCP
Port: 5432
Source: sg-lambda
```

This means the database accepts PostgreSQL connections from network interfaces associated with the specified Lambda security group.

This is generally more maintainable than allowing a broad IP range.

### 10.3 Network ACLs

Network ACLs operate at the subnet level.

Unlike security groups, network ACLs are stateless.

This means you must consider both inbound and outbound traffic rules.

| Feature         | Security group                                          | Network ACL                  |
| --------------- | ------------------------------------------------------- | ---------------------------- |
| Scope           | Network interface                                       | Subnet                       |
| Stateful        | Yes                                                     | No                           |
| Rule evaluation | Allow rules                                             | Ordered allow and deny rules |
| Return traffic  | Automatically permitted when related to allowed traffic | Must be explicitly allowed   |
| Common use      | Resource-level firewall                                 | Subnet-level traffic control |

For most Lambda-to-RDS configurations, security groups are the primary network access control mechanism.

### 11\. Accessing Private Resources Inside a VPC

### 11.1 Lambda and Amazon RDS

One of the most common Lambda networking patterns is connecting to a relational database.

For example:

```text
API Gateway
     |
     v
Lambda Function
     |
     v
Private VPC Network
     |
     v
Amazon RDS PostgreSQL
```

The database remains private, and Lambda accesses it through the VPC.

You need to configure:

* Lambda VPC attachment.

* Private subnet selection.

* Lambda security group.

* RDS security group.

* Database credentials.

* Database connectivity.

### 11.2 Database connection management

Lambda is designed to scale horizontally.

Imagine that 500 requests arrive simultaneously.

Lambda might create many concurrent execution environments, and each environment could establish its own database connection.

This can overwhelm a database with a limited connection capacity.

For this reason, consider using:

Amazon RDS Proxy.

RDS Proxy pools and shares database connections, helping Lambda applications manage database connection pressure.

Architecture:

```text
API Gateway
     |
     v
Lambda Functions
     |
     v
RDS Proxy
     |
     v
RDS PostgreSQL
```

RDS Proxy is especially useful for serverless workloads with unpredictable concurrency.

### 11.3 Other private resources

Lambda can also communicate with:

* Private EC2 instances.

* ElastiCache Redis.

* Internal application servers.

* Private APIs.

* Other services reachable through VPC routing.

The required connectivity depends on routing, security groups, network ACLs, DNS resolution, and the destination's listening configuration.

### 12\. NAT Gateways and Internet Connectivity

### 12.1 Why does Lambda need a NAT Gateway?

Suppose your Lambda function is attached to private subnets.

It needs to communicate with an external payment provider:

```text
https://api.payment-provider.com
```

The external service is accessible through the public internet.

However, your Lambda function is inside private subnets without a direct internet route.

A NAT Gateway allows resources in private subnets to initiate outbound internet connections without exposing them to unsolicited inbound internet connections.

### 12.2 NAT Gateway architecture

![AWS Lambda VPC Internet Access via NAT Gateway (Terraform)](https://images.openai.com/static-rsc-4/9uu8OsbDJJcbqh6aWM93Zmie2RkMkb_mWxKeccT7Z2tOo1tkA2Sex6ljvQkmCVUmBGOWrcojijota9rCjn3gqAKx_2pw5ZvgxAqyA27M7Oz9oxx5xE4HFFjV44DmAcA93K90KSa5v5QOVky_PPZ_SgBi_pyd4XI7Ni261wM2opnVDBlxfUgqgxgRv0wRYUhb?purpose=fullsize)

The traffic flow is:

* Lambda initiates an outbound connection.

* Traffic reaches the NAT Gateway through the private subnet route table.

* NAT Gateway forwards the traffic through the Internet Gateway.

* The external service receives the request.

* The response returns through the NAT Gateway.

A typical route table configuration:

Private subnet route table

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         nat-gateway
```

Public subnet route table

```text
Destination       Target
10.0.0.0/16       local
0.0.0.0/0         internet-gateway
```

### 12.3 NAT Gateway considerations

NAT Gateways introduce additional costs and architectural considerations.

You should understand:

* Hourly charges.

* Data processing charges.

* Availability Zone placement.

* Cross-AZ traffic costs.

* Elastic IP allocation.

* Route table configuration.

* Redundancy and failure scenarios.

For production architectures, deploying a NAT Gateway per Availability Zone can improve availability and avoid unnecessary cross-AZ traffic.

### 12.4 NAT Gateway versus Internet Gateway

| Feature                     | Internet Gateway                                  | NAT Gateway                                    |
| --------------------------- | ------------------------------------------------- | ---------------------------------------------- |
| Main purpose                | Internet connectivity for public resources        | Outbound internet access for private resources |
| Public IP requirements      | Public addressing for IPv4 internet communication | Uses its Elastic IP for IPv4 translation       |
| Private resource protection | Does not provide NAT isolation                    | Prevents unsolicited inbound connections       |
| Typical location            | Attached to VPC                                   | Deployed in a public subnet                    |

Remember that NAT Gateway is not a firewall replacement. Security groups, network ACLs, and appropriate egress controls remain important.

### 13\. VPC Endpoints and Private AWS Service Access

### 13.1 What is a VPC endpoint?

A VPC endpoint allows resources inside a VPC to communicate with supported AWS services without requiring a public internet connection.

For example, suppose a Lambda function runs inside a private subnet and needs to download files from S3.

Without a VPC endpoint, you might route traffic through a NAT Gateway.

With an S3 Gateway Endpoint, the Lambda function can access S3 through the AWS network without requiring NAT for that traffic.

This can reduce networking costs and improve security.

### 13.2 Types of VPC endpoints

There are two important endpoint categories to understand.

1\. Gateway endpoints

Gateway endpoints support:

* Amazon S3.

* Amazon DynamoDB.

They are configured through route tables.

2\. Interface endpoints

Interface endpoints use AWS PrivateLink and create private network interfaces in your subnets.

They support many AWS services, including:

* Secrets Manager.

* Systems Manager.

* KMS.

* SQS.

* SNS.

* CloudWatch Logs.

* ECR API and ECR Docker Registry.

The exact available services depend on the AWS Region.

### 13.3 Gateway versus interface endpoints

| Feature            | Gateway endpoint              | Interface endpoint                 |
| ------------------ | ----------------------------- | ---------------------------------- |
| Technology         | Route table integration       | AWS PrivateLink                    |
| Uses ENIs          | No                            | Yes                                |
| Security groups    | No endpoint security group    | Yes                                |
| Supported services | S3, DynamoDB                  | Many AWS services                  |
| Pricing            | No additional endpoint charge | Hourly and data processing charges |
| Configuration      | Route tables                  | Subnets, security groups, DNS      |

### 13.4 Lambda accessing S3 privately

Consider this architecture:

![AWS Lambda in VPC to access S3](https://images.openai.com/static-rsc-4/FWe4F0wpdvY2pdE0CeWWcgFnnBLymv__v3l_15yu_ZGQPJ5XEQ9Q7Z-gNfanzRzCuVBBNkw5XoZNkP34sq5D4SwBo3_8By_smCjxcSYWHnIOV38lO_pujeeRD-Oyry22N1kSzZtdy32hbyVEyAgW7FeUbeeO_WkgXkiWMsbenHYrthqMnQ1yPXfVwPok3FOl?purpose=fullsize)

The flow is:

* Lambda executes inside a private subnet.

* It requests an S3 object.

* The subnet route table directs S3 traffic through the Gateway Endpoint.

* The request reaches S3 through AWS networking.

* S3 returns the object.

No NAT Gateway is required for this S3 traffic.

You still need the appropriate IAM permissions and S3 bucket policies.

### 13.5 Accessing Secrets Manager privately

Suppose Lambda needs to retrieve a database password from Secrets Manager.

You can create an Interface VPC Endpoint for Secrets Manager.

The architecture becomes:

```text
Lambda Function
      |
      v
Private Subnet
      |
      v
Secrets Manager Interface Endpoint
      |
      v
AWS Secrets Manager
```

The endpoint security group must allow the appropriate HTTPS traffic, typically TCP 443, from the Lambda security group.

You also need:

* Appropriate IAM permissions.

* A suitable endpoint policy, if configured.

* Correct DNS configuration.

* KMS permissions when using a customer-managed key.

### 13.6 When should you use NAT versus VPC endpoints?

| Requirement                      | Recommended approach                              |
| -------------------------------- | ------------------------------------------------- |
| Access S3 privately              | S3 Gateway Endpoint                               |
| Access DynamoDB privately        | DynamoDB Gateway Endpoint                         |
| Access Secrets Manager privately | Interface Endpoint                                |
| Access SQS privately             | Interface Endpoint                                |
| Access SNS privately             | Interface Endpoint                                |
| Access public third-party APIs   | NAT Gateway or another controlled egress solution |
| Access private RDS               | VPC connectivity                                  |

Production recommendation: For private Lambda workloads, consider using VPC endpoints for frequently accessed AWS services and NAT only when actual internet connectivity is required.

This can substantially reduce unnecessary NAT Gateway traffic.

### 14\. Lambda Networking Considerations and Connection Management

This section brings together the most important networking concepts for production Lambda applications.

### 14.1 Lambda execution environment reuse

Lambda can reuse execution environments between invocations.

This means you can initialize reusable clients outside the handler.

For example:

```python
import boto3

s3 = boto3.client("s3")
dynamodb = boto3.resource("dynamodb")

def lambda_handler(event, context):
    # Reuse initialized clients
    response = s3.list_objects_v2(
        Bucket="my-bucket"
    )

    return {
        "object_count": len(response.get("Contents", []))
    }
```

This avoids unnecessarily creating new SDK clients for every invocation.

It is particularly useful when your Lambda function communicates with multiple AWS services.

However, you should not assume that execution environments are permanent. Lambda can terminate them at any time.

### 14.2 Database connection reuse

Opening a new database connection for every invocation can introduce unnecessary latency and resource consumption.

A common approach is to initialize a database connection outside the handler and reuse it when appropriate.

Conceptually:

```python
import psycopg

connection = None

def get_connection():
    global connection

    if connection is None or connection.closed:
        connection = psycopg.connect(
            host="database.internal",
            dbname="application",
            user="app_user",
            password="retrieved-secret"
        )

    return connection

def lambda_handler(event, context):
    conn = get_connection()

    with conn.cursor() as cursor:
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

    return {
        "result": result[0]
    }
```

This is a simplified example. Production implementations should also handle stale connections, connection failures, timeouts, and credential rotation.

For workloads with high concurrency, RDS Proxy is often a better solution than relying entirely on per-environment connection reuse.

### 14.3 DNS resolution

Lambda functions frequently use DNS to communicate with:

* RDS endpoints.

* ElastiCache endpoints.

* Private APIs.

* External services.

* AWS service endpoints.

For VPC-based Lambda functions, DNS configuration is important.

Two VPC attributes are particularly relevant:

* `enableDnsSupport`: Enables DNS resolution in the VPC.

* `enableDnsHostnames`: Enables DNS hostnames for resources that support them.

You should also understand Route 53 Resolver, private hosted zones, and DNS resolution for interface VPC endpoints.

### 14.4 IPv4 and IPv6 networking

Lambda supports IPv4 and dual-stack networking configurations for VPC-connected functions, subject to subnet and service requirements.

Important concepts include:

* IPv4 CIDR ranges.

* IPv6 CIDR ranges.

* Dual-stack subnets.

* Internet Gateway routing.

* Egress-only Internet Gateway.

* Security group IPv6 rules.

For IPv6-only or dual-stack networking designs, verify the specific Lambda configuration and supported destination connectivity requirements before deployment.

### 14.5 Lambda networking performance

VPC networking introduces additional architectural considerations.

You should understand:

* Hyperplane ENI reuse.

* Subnet IP address capacity.

* Availability Zone selection.

* DNS resolution latency.

* Connection pooling.

* NAT Gateway throughput and availability.

* VPC endpoint costs.

* Cross-AZ traffic.

* Database connection limits.

A common mistake is to focus exclusively on Lambda concurrency while ignoring the capacity of downstream services.

For example, increasing Lambda concurrency from 50 to 500 can overload an RDS database even if Lambda itself scales successfully.

### 14.6 Common networking problems

| Problem                                | Possible cause                                             |
| -------------------------------------- | ---------------------------------------------------------- |
| Lambda cannot connect to RDS           | Incorrect security group rules                             |
| Lambda cannot access the internet      | Missing NAT Gateway or route                               |
| Lambda cannot access S3                | Missing IAM permission or incorrect endpoint configuration |
| Secrets Manager request times out      | Missing endpoint, NAT route, or incorrect DNS              |
| Database connections fail under load   | Connection exhaustion                                      |
| Lambda cannot resolve private hostname | DNS configuration problem                                  |
| Lambda experiences connection timeouts | Routing, firewall, or destination availability issue       |
| VPC configuration fails                | Insufficient ENI permissions or subnet IP capacity         |

### 15\. Putting Everything Together: Production Security Architecture

Let's consider a realistic application.

You are developing a FastAPI-based application that uses Lambda for asynchronous document processing.

The application has:

* API Gateway for HTTP requests.

* Lambda for processing.

* S3 for document storage.

* SQS for asynchronous jobs.

* RDS PostgreSQL for application data.

* Secrets Manager for database credentials.

* KMS for encryption.

* CloudWatch for monitoring.

A possible architecture:

![今日は、LambdaとSecrets ManagerとVPCエンドポイントの日。 - 今日はなにの日。](https://images.openai.com/static-rsc-4/17fRJu7FVb3r3vA9yM0YxsbCogA3BQkiccb8IgnG4_SM52a5nDMjcn4CNIimxiL6yLEh3fsj9cnK9PXuYptJq39ao5qjZ1GHkvsHFOJ5YIKIyh_U85pzxXDTJZMV9sxs_r9j-cZt3dmM72ighhmS31DaEOsEM_WkNMUlRCreVsBvXvRVdIxvayg85B6LE4bg?purpose=fullsize)

### Security design

| Component       | Security configuration                                |
| --------------- | ----------------------------------------------------- |
| API Gateway     | Authentication and request authorization              |
| Lambda          | Dedicated execution role                              |
| S3              | Private bucket and least-privilege object permissions |
| SQS             | Queue policies and restricted access                  |
| RDS             | Private subnets and restrictive security groups       |
| Secrets Manager | Encrypted credentials and controlled retrieval        |
| KMS             | Customer-managed encryption key where appropriate     |
| VPC             | Private subnets and controlled routing                |
| VPC Endpoints   | Private AWS service connectivity                      |
| CloudWatch      | Application logging and monitoring                    |

### Important design decisions

* Give each Lambda function its own execution role when its permissions differ.

* Avoid hardcoding credentials in Python source code.

* Use Secrets Manager for database credentials.

* Keep databases in private subnets.

* Restrict database access to the Lambda security group.

* Use VPC endpoints for private AWS service connectivity where appropriate.

* Use NAT only when external internet access is necessary.

* Consider RDS Proxy for high-concurrency database workloads.

* Enable appropriate logging and auditing.

* Regularly review IAM policies and KMS permissions.

### 16\. Important Concepts to Remember

Here is a summary of the most important distinctions from this module.

| Concept               | What you should remember                     |
| --------------------- | -------------------------------------------- |
| Execution role        | Defines what Lambda can access               |
| Resource-based policy | Defines who can invoke Lambda                |
| Trust policy          | Defines who can assume an IAM role           |
| Least privilege       | Grants only required permissions             |
| Permission boundary   | Limits maximum IAM permissions               |
| KMS                   | Manages encryption keys                      |
| Secrets Manager       | Stores and rotates sensitive credentials     |
| Parameter Store       | Centralizes application configuration        |
| VPC                   | Provides an isolated AWS network             |
| Hyperplane ENI        | Provides managed Lambda VPC connectivity     |
| Security group        | Stateful network firewall                    |
| Network ACL           | Stateless subnet-level firewall              |
| NAT Gateway           | Provides outbound IPv4 internet connectivity |
| Gateway endpoint      | Private routing to S3 and DynamoDB           |
| Interface endpoint    | Private connectivity through AWS PrivateLink |
| RDS Proxy             | Helps manage database connection pooling     |

### Recommended knowledge progression

* Identity and permissions

    Understand execution roles, trust policies, resource policies, and least privilege.

* Encryption and secrets

    Understand KMS, Secrets Manager, and Parameter Store.

* VPC fundamentals

    Understand VPCs, subnets, route tables, and security groups.

* Private connectivity

    Understand Lambda-to-RDS communication, NAT Gateways, and VPC endpoints.

* Production networking

    Understand Hyperplane ENIs, connection pooling, DNS, and scaling implications.

The central takeaway: Lambda security is not just about IAM permissions. You must understand identity, encryption, secrets management, network isolation, and connectivity together. A secure Lambda architecture combines all five.

For the next module, we will build on this foundation and explore Lambda Scaling, Concurrency, Performance, and Optimization, including cold starts, reserved concurrency, provisioned concurrency, SnapStart, and cost optimization.
