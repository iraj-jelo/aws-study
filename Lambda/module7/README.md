### Module 7 — Lambda Deployment, Versioning, and CI/CD with Pulumi

This module focuses on taking Lambda functions from development to production. You'll learn how to package and deploy Python applications, manage immutable versions, promote releases between environments, implement gradual deployments, and automate infrastructure and application delivery using Pulumi Python and GitHub Actions.

The central idea is to separate application releases from infrastructure management and make deployments repeatable, controlled, and reversible.

### 1\. Lambda deployment strategies

AWS Lambda supports several ways to package and deploy functions. The appropriate approach depends on application complexity, dependencies, deployment size, and operational requirements.

### 1.1 ZIP deployment packages

A ZIP deployment package contains:

* Python handler files.

* Application modules.

* Third-party dependencies.

* Supporting configuration files.

Example structure:

```text
lambda-project/
├── src/
│   ├── handler.py
│   ├── services.py
│   └── database.py
├── requirements.txt
└── deployment.zip
```

A simple handler:

```python
import json

def handler(event, context):
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Hello from Lambda"
        })
    }
```

You can package the function using Bash:

```bash
mkdir -p package

uv pip install \
    --target package \
    -r requirements.txt

cp -r src/* package/

cd package
zip -r ../deployment.zip .
cd ..
```

For production, ensure dependencies are built for the Lambda runtime's operating system and architecture. Native Python dependencies may not work if packaged from an incompatible local environment.

### 1.2 Container image deployment

Lambda also supports container images stored in Amazon ECR.

This approach is useful when:

* Your application has many dependencies.

* You need OS-level libraries.

* You want reproducible container-based packaging.

* You already use Docker-based build pipelines.

Example Dockerfile:

```dockerfile
FROM public.ecr.aws/lambda/python:3.14

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ${LAMBDA_TASK_ROOT}/

CMD ["handler.handler"]
```

Build and publish:

```bash
docker build -t lambda-api .

docker tag lambda-api:latest \
    ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/lambda-api:latest

docker push \
    ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/lambda-api:latest
```

The ECR repository must exist and the Docker client must be authenticated before pushing.

Important: Lambda container images have a maximum uncompressed image size of 10 GB. ZIP deployment packages have a 250 MB uncompressed limit, including layers.

### 1.3 ZIP vs. container images

| Characteristic            | ZIP                   | Container image      |
| ------------------------- | --------------------- | -------------------- |
| Packaging                 | ZIP archive           | OCI image            |
| Registry                  | Direct upload / S3    | Amazon ECR           |
| Maximum uncompressed size | 250 MB                | 10 GB                |
| OS customization          | Limited               | Greater control      |
| Build tooling             | ZIP and Python tools  | Docker               |
| Best suited for           | Most Python functions | Complex dependencies |

For this course, ZIP deployment is the default. Container images are an important alternative when the application needs them.

### 2\. AWS CLI and Bash-based function management

AWS CLI allows you to deploy, configure, inspect, and manage Lambda functions without using the AWS Console.

It is especially useful for understanding the underlying Lambda APIs that Pulumi automates.

### 2.1 Create a Lambda function

Assuming you have already created an execution role:

```bash
aws lambda create-function \
    --function-name orders-api \
    --runtime python3.14 \
    --handler handler.handler \
    --role arn:aws:iam::ACCOUNT_ID:role/lambda-role \
    --zip-file fileb://deployment.zip \
    --timeout 30 \
    --memory-size 512
```

### 2.2 Update function code

```bash
aws lambda update-function-code \
    --function-name orders-api \
    --zip-file fileb://deployment.zip
```

### 2.3 Update function configuration

```bash
aws lambda update-function-configuration \
    --function-name orders-api \
    --timeout 60 \
    --memory-size 1024
```

### 2.4 Inspect function configuration

```bash
aws lambda get-function-configuration \
    --function-name orders-api
```

### 2.5 Invoke the function

```bash
aws lambda invoke \
    --function-name orders-api \
    --payload '{"order_id": 123}' \
    --cli-binary-format raw-in-base64-out \
    response.json

cat response.json
```

### 2.6 Wait for updates to finish

Lambda configuration and code updates are not always immediately available.

Use:

```bash
aws lambda wait function-updated \
    --function-name orders-api
```

This is important in automated deployment scripts. Otherwise, subsequent operations may encounter update conflicts.

### 3\. Deployment packages and container image deployments

Let's look at the deployment lifecycle in more detail.

![Container Image Support in AWS Lambda Deep Dive - DEV Community](https://images.openai.com/static-rsc-4/scQPuzb3FMPmiaHAja5C5JqjMHhN9lXAdb9ojOPvwiJvVUmLuu_poHsGAPkVsPvFuufy0KYV97p0hlPdIdb1O2wpLxjR8c2IHkbcIFvMq5Q-1MUgpSA0ORrxvwmLjVbk7okGG6qZy7spxeEOHfyL8TSdaiicZSGVtp6NMQ7wwVhdc6Lel5Q0akr2B3ySO4oy?purpose=fullsize)

### 3.1 ZIP deployment lifecycle

The typical workflow is:

* Develop the Python application.

* Install production dependencies.

* Package the application.

* Upload the ZIP archive.

* Update the Lambda function.

* Wait for the update to complete.

* Test the deployed function.

* Publish a version.

The deployment artifact should be treated as a release artifact.

For example:

```text
artifacts/
├── orders-api-1.0.0.zip
├── orders-api-1.1.0.zip
└── orders-api-1.2.0.zip
```

Avoid relying on an unchanging filename or mutable artifact when you need reliable release traceability.

### 3.2 Container image lifecycle

For container deployments:

* Build the Docker image.

* Tag the image with a release identifier.

* Push the image to ECR.

* Update Lambda to use the new image.

* Publish a Lambda version.

* Test and promote the release.

For example:

```bash
docker build -t orders-api:1.2.0 .

docker tag orders-api:1.2.0 \
    ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/orders-api:1.2.0
```

One important distinction: Lambda resolves an image tag to an image digest when the function code is updated. Publishing a new image under an existing tag does not automatically update an existing Lambda function.

Use unique release tags and track the image digest.

### 4\. Lambda function versions and immutable deployments

One of Lambda's most important deployment capabilities is function versioning.

A Lambda function has two major forms:

* `$LATEST`: The mutable development version.

* Published versions: Immutable snapshots of function code and version-specific configuration.

### 4.1 Understanding function versions

Suppose you deploy your first application:

```text
orders-api
    |
    └── $LATEST
```

After testing, publish a version:

```text
orders-api
    |
    ├── $LATEST
    └── Version 1
```

Later, you deploy updated code:

```text
orders-api
    |
    ├── $LATEST (new code)
    └── Version 1 (old code)
```

Publish another version:

```text
orders-api
    |
    ├── $LATEST
    ├── Version 1
    └── Version 2
```

Version 1 remains unchanged even when `$LATEST` is updated.

### 4.2 Publish a version using AWS CLI

```bash
aws lambda publish-version \
    --function-name orders-api \
    --description "Release 1.2.0"
```

You can inspect versions:

```bash
aws lambda list-versions-by-function \
    --function-name orders-api
```

### 4.3 Why immutable versions matter

Published versions provide:

* Reproducible releases.

* Stable deployment targets.

* Controlled traffic shifting.

* Easier rollback.

* Release history.

* Better separation between development and production.

Important: A published version captures version-specific function code and configuration, but it does not snapshot every external dependency. IAM policies, event source mappings, API Gateway resources, and external databases can change independently.

This distinction matters when designing reliable production rollbacks.

### 5\. Lambda aliases and environment promotion

An alias is a named pointer to a published Lambda version.

Instead of invoking a specific version directly, applications can invoke an alias.

Common aliases include:

* `dev`

* `staging`

* `production`

![AWS Lambda Versions & Aliases — The Blueprint for Safe, Zero-Downtime Deployments | by Content Tech | Medium](https://images.openai.com/static-rsc-4/NczMr9Tgwb6BYi7C290Zboe2yS3CuMyG-SbXdu_rGa-Pxyi9Cs8mx3i1k2afMZMIePjjxZBbvdsINAVpComqrjlYo4-es2jEy2FirVyy-Bjpi2Y-SOx7NLZaC6W0Z1TLWF1s_UbsbcgLpi95PHCsOnOS_h7R0X5WraaC5hLihDnqgkMvjS7FBaLkYj6T5u8P?purpose=fullsize)

For example:

```text
orders-api
    |
    ├── Version 1
    ├── Version 2
    └── Version 3

Aliases:
    |
    ├── staging    → Version 3
    └── production → Version 2
```

### 5.1 Create an alias

```bash
aws lambda create-alias \
    --function-name orders-api \
    --name production \
    --function-version 2 \
    --description "Production release"
```

### 5.2 Update an alias

```bash
aws lambda update-alias \
    --function-name orders-api \
    --name production \
    --function-version 3
```

The application can continue invoking:

```text
arn:aws:lambda:REGION:ACCOUNT_ID:function:orders-api:production
```

You can promote a new release by changing the alias rather than modifying every application integration.

### 5.3 Environment promotion

A typical promotion strategy:

```text
Development
    |
    v
Publish Version 3
    |
    v
Staging → Version 3
    |
    v
Integration validation
    |
    v
Production → Version 3
```

Aliases are particularly useful when multiple environments need to use the same Lambda function but different published versions.

However, aliases do not automatically create isolated environments. Separate AWS accounts or independently managed stacks are often preferable for production-grade environment isolation.

### 6\. Weighted alias routing and gradual deployments

Lambda aliases support weighted routing, allowing traffic to be distributed between two published versions.

This is useful when you want to introduce a new release gradually rather than immediately sending all production traffic to it.

### 6.1 Weighted routing

Suppose you have:

* Version 2: Current production release.

* Version 3: New release.

You can configure the production alias to send:

* 90% of traffic to Version 2.

* 10% of traffic to Version 3.

![Building well-architected serverless applications: Approaching application lifecycle management – part 2 | AWS Compute Blog](https://images.openai.com/static-rsc-4/gNROtTyxCqV8pXA6t26Z4BYcHFG8zReRElLQLJNlVCb_Oe7EOris49B7h5_Vh-L8BMBg3RJpj6RO_pMHMWTruicWlyNfZm8ynDmaMxxy8F_Bee-WWVMzsyfL1kXrSGPNTS8cv8Nv9u4n5EmZRQn_bqnYthgBb1qj3RS7BhDFzvrzKzrgg7Ct_7NdIKnuifrB?purpose=fullsize)

The AWS CLI configuration looks like this:

```bash
aws lambda update-alias \
    --function-name orders-api \
    --name production \
    --function-version 2 \
    --routing-config '{"AdditionalVersionWeights":{"3":0.1}}'
```

This means that Version 2 receives the remaining 90%, while Version 3 receives 10%.

After monitoring the new release, you can increase its traffic:

```bash
aws lambda update-alias \
    --function-name orders-api \
    --name production \
    --function-version 2 \
    --routing-config '{"AdditionalVersionWeights":{"3":0.5}}'
```

Now the distribution is 50/50.

Finally, promote Version 3:

```bash
aws lambda update-alias \
    --function-name orders-api \
    --name production \
    --function-version 3 \
    --routing-config '{}'
```

### 6.2 Canary deployment

A canary deployment gradually introduces a new release to a small percentage of traffic.

Example:

| Stage   | Version 2 | Version 3 |
| ------- | --------- | --------- |
| Initial | 100%      | 0%        |
| Stage 1 | 90%       | 10%       |
| Stage 2 | 50%       | 50%       |
| Final   | 0%        | 100%      |

At each stage, monitor:

* Invocation errors.

* Execution duration.

* Throttles.

* Application-specific failures.

* Downstream service errors.

If the new version behaves incorrectly, restore the previous alias configuration.

### 6.3 CodeDeploy for Lambda deployments

AWS CodeDeploy supports automated Lambda deployments with predefined traffic-shifting strategies.

Common strategies include:

| Strategy                    | Behavior                                              |
| --------------------------- | ----------------------------------------------------- |
| Canary10Percent5Minutes     | Sends 10% initially, then the rest after five minutes |
| Canary10Percent10Minutes    | Sends 10% initially, then the rest after ten minutes  |
| Linear10PercentEvery1Minute | Moves 10% of traffic every minute                     |
| AllAtOnce                   | Moves all traffic immediately                         |

CodeDeploy can integrate with CloudWatch alarms and deployment hooks.

For example, a pre-traffic validation hook can invoke a Lambda function to validate the new release before traffic shifting proceeds.

A CloudWatch alarm can trigger automatic rollback when deployment metrics indicate failure.

Important: Weighted routing is probabilistic, not a strict guarantee for every request. It is designed for traffic distribution, not deterministic routing or session affinity.

### 7\. Blue/green and canary deployment strategies

These are two important production deployment patterns.

### 7.1 Blue/green deployment

Blue/green deployment maintains two application versions:

* Blue: Current production release.

* Green: New release.

![Fine-tuning blue/green deployments on application load balancer | AWS DevOps & Developer Productivity Blog](https://images.openai.com/static-rsc-4/Xp6xlwCDrzTXgTQ1eu77_heixXp-2ZNqIEIb_x3Uv5SIELBKW6In_KKbxHiR1HSw3_Jf-hiIrAER87yAc2lTHB-pI1tPJr82HN25RLU-K7NHfdg9JJv1zQMQpmdONjfprlmjimVuSDICFGKqOCCeet6Mn4NNdNbNoMkEc9tUdgp60x7ybLy9DUudKPGnGaX_?purpose=fullsize)

The process:

* Blue serves production traffic.

* Deploy Green as a new published Lambda version.

* Validate Green independently.

* Switch the production alias to Green.

* Monitor application behavior.

* Roll back to Blue if necessary.

For example:

```text
Before deployment:

production → Version 2 (Blue)

After deployment:

production → Version 3 (Green)
```

Rollback:

```bash
aws lambda update-alias \
    --function-name orders-api \
    --name production \
    --function-version 2
```

The major benefit is that the previous release remains available.

### 7.2 Canary vs. blue/green

| Characteristic    | Canary                   | Blue/green                      |
| ----------------- | ------------------------ | ------------------------------- |
| Traffic migration | Gradual                  | Usually immediate               |
| Risk management   | Progressive exposure     | Independent validation          |
| Monitoring        | At each stage            | Before and after switch         |
| Rollback          | Restore previous routing | Switch back to previous version |
| Typical use       | Frequent releases        | Major releases                  |

Both approaches are useful, and they can be combined.

### 7.3 Database compatibility considerations

One common deployment mistake is assuming that rolling back Lambda code automatically rolls back database changes.

For example:

* Version 2 expects database column `customer_name`.

* Version 3 expects a new column `full_name`.

* Version 3 performs a database migration.

* You roll back the Lambda alias to Version 2.

Version 2 may now fail if the migration removed or changed `customer_name`.

Use backward-compatible database migrations:

* Add new fields without immediately removing old ones.

* Deploy code that supports both schemas.

* Migrate existing data.

* Switch application behavior.

* Remove old fields only after old application versions are no longer needed.

This is particularly important for serverless microservices.

### 8\. Lambda function URLs and their use cases

A Lambda Function URL provides an HTTPS endpoint directly associated with a Lambda function.

You don't need to configure API Gateway to expose a basic HTTP endpoint.

![Let AWS Lambda Handle Your Event-Driven Hassles — Invocation Models of AWS Lambda | by Devindie Samaranayake | Medium](https://images.openai.com/static-rsc-4/vd5l-kbkv2G_fdAw0-XJyRQ7Wr3oXuQf7jxNUL9r03NSofTicOA7c4zVF3u-FQiv5qxG6i9pcaAhrcP2jahoZ7Emfp42IYjNzkF7TC_LNgmR5xbnDyK2ZL4qM4qJtFkglNeaCsvaYdoSqsJiJb5vQOsKtGPe0h9_Vj6TkeeMfxZVVMnkGXE5Ly-yjNcbpk_6?purpose=fullsize)

### 8.1 Function URL architecture

```text
Client
  |
  | HTTPS Request
  v
Lambda Function URL
  |
  v
Lambda Function
  |
  v
Application Logic
```

Function URLs support two authentication modes:

| Mode    | Description                                                 |
| ------- | ----------------------------------------------------------- |
| AWS_IAM | Requests must be authorized using AWS IAM authentication    |
| NONE    | No AWS IAM authentication is required at the endpoint level |

`NONE` does not mean that your application has no security responsibilities. You must implement appropriate authentication and authorization if the endpoint is publicly accessible.

### 8.2 Create a Function URL

```bash
aws lambda create-function-url-config \
    --function-name orders-api \
    --auth-type AWS_IAM \
    --cors '{
      "AllowOrigins": ["https://example.com"],
      "AllowMethods": ["GET", "POST"],
      "AllowHeaders": ["content-type"]
    }'
```

Inspect it:

```bash
aws lambda get-function-url-config \
    --function-name orders-api
```

### 8.3 Function URL vs. API Gateway

| Feature                   | Function URL                                 | API Gateway                    |
| ------------------------- | -------------------------------------------- | ------------------------------ |
| HTTP endpoint             | Yes                                          | Yes                            |
| Direct Lambda integration | Yes                                          | Yes                            |
| API management features   | Limited                                      | Extensive                      |
| Authentication            | IAM or application-level                     | Multiple authorization options |
| Request throttling        | No API Gateway-style configurable throttling | Supported                      |
| API keys and usage plans  | No                                           | Supported                      |
| Request validation        | Application-level                            | Supported                      |
| Custom API routing        | Application-level                            | Supported                      |

Use Function URLs for simple HTTP integrations, internal tools, lightweight webhooks, and straightforward endpoints.

Use API Gateway when you need API management, sophisticated authorization, throttling, request validation, API stages, or advanced routing.

### 9\. API Gateway integration and deployment considerations

API Gateway is commonly used as the HTTP entry point for Lambda-based applications.

![API Development Series Part 7: AWS API Gateway & Lambda - Wasil Zafar](https://images.openai.com/static-rsc-4/vL5j0D7a1AjQZR_v9JxW6Zu9Kdwbxbo4aHHBUDWq-pEZ92lKR5n2ghSnL_oHSO033YZTa83LlNX53N2-uKcN3HA2u1an-R-uDb1O6sI-7csOYp-B_Oq6uBiCTpcWCLCI0DoJQNLihj4Y3syD0ztPICbAyaDUjgw3m2aMnxXOTxM0VwoDhuVCW3eB0C_AXAL-?purpose=fullsize)

The request flow:

```text
Client
  |
  v
API Gateway
  |
  | Lambda Invocation
  v
Lambda Function
  |
  v
Business Logic
  |
  v
Response
  |
  v
API Gateway
  |
  v
Client
```

### 9.1 Lambda proxy integration

With proxy integration, API Gateway forwards the request information to Lambda.

The event may contain:

```json
{
  "httpMethod": "POST",
  "path": "/orders",
  "headers": {
    "content-type": "application/json"
  },
  "body": "{\"product_id\": 123}",
  "isBase64Encoded": false
}
```

Lambda processes the event and returns an HTTP-compatible response:

```python
import json

def handler(event, context):
    body = json.loads(event.get("body") or "{}")

    return {
        "statusCode": 201,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps({
            "message": "Order created",
            "product_id": body.get("product_id")
        })
    }
```

### 9.2 Permissions

API Gateway needs permission to invoke Lambda.

For example:

```bash
aws lambda add-permission \
    --function-name orders-api:production \
    --statement-id apigateway-invoke \
    --action lambda:InvokeFunction \
    --principal apigateway.amazonaws.com \
    --source-arn "arn:aws:execute-api:REGION:ACCOUNT_ID:API_ID/*/*/*"
```

Notice that the permission references the production alias.

This is useful because the API Gateway integration can invoke the alias without needing to be changed for every application release.

### 9.3 Deployment considerations

For production applications, consider:

* API Gateway stages and stage variables.

* Lambda aliases as deployment targets.

* API authorization and authentication.

* Request validation.

* Throttling and quotas.

* CORS configuration.

* Access logging.

* CloudWatch monitoring.

* API versioning and backward compatibility.

* API Gateway timeout constraints.

* Lambda timeout and memory configuration.

A useful architecture is to deploy API Gateway once and connect it to a stable Lambda alias. New application releases then require only alias promotion.

### 10\. Infrastructure as Code with Pulumi Python

Now we move to one of the most important parts of this module: managing Lambda deployments using Pulumi.

Pulumi allows you to define AWS infrastructure using Python instead of manually creating resources through the Console or CLI.

For Lambda deployments, Pulumi can manage:

* IAM roles and policies.

* Lambda functions.

* Deployment artifacts.

* Lambda versions.

* Aliases.

* Function URLs.

* Permissions.

* Event source mappings.

* API Gateway resources.

* CloudWatch resources.

### 10.1 Pulumi project structure

A practical project structure:

```text
orders-lambda/
├── app/
│   ├── handler.py
│   ├── services.py
│   └── requirements.txt
│
├── infrastructure/
│   ├── __main__.py
│   ├── Pulumi.yaml
│   ├── Pulumi.dev.yaml
│   └── Pulumi.prod.yaml
│
└── README.md
```

The application and infrastructure are separated.

This makes it easier to maintain application code independently of infrastructure definitions.

### 10.2 Create a Pulumi project

```bash
cd infrastructure

pulumi new aws-python
```

The project uses the AWS provider and Python runtime.

A simplified `Pulumi.yaml`:

```yaml
name: orders-lambda
runtime:
  name: python
description: AWS Lambda deployment with Pulumi
```

### 10.3 Pulumi stacks

Stacks allow you to manage separate environments.

```bash
pulumi stack init dev
pulumi stack init staging
pulumi stack init prod
```

Select an environment:

```bash
pulumi stack select dev
```

Inspect the current stack:

```bash
pulumi stack
```

The same infrastructure definition can be reused across environments with different configuration values.

### 10.4 Pulumi configuration

Set configuration:

```bash
pulumi config set aws:region eu-west-2

pulumi config set environment dev

pulumi config set memorySize 512
```

Retrieve configuration in Python:

```python
import pulumi

config = pulumi.Config()

environment = config.require("environment")
memory_size = config.get_int("memorySize") or 512
```

For secrets:

```bash
pulumi config set dbPassword --secret
```

Read the secret:

```python
db_password = config.require_secret("dbPassword")
```

Pulumi encrypts secret configuration in its state and configuration storage according to the configured secrets provider.

Avoid printing secret values in logs or exposing them through ordinary outputs.

### 11\. Managing Lambda functions, IAM roles, and permissions with Pulumi

Let's look at a representative Pulumi implementation.

First, define an IAM execution role.

```python
import json
import pulumi
import pulumi_aws as aws

role = aws.iam.Role(
    "orders-lambda-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }]
    })
)
```

Attach the basic execution policy:

```python
policy = aws.iam.RolePolicyAttachment(
    "lambda-basic-execution",
    role=role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "service-role/AWSLambdaBasicExecutionRole"
    )
)
```

This allows Lambda to write logs to CloudWatch Logs.

### 11.1 Deploy the Lambda function

```python
function = aws.lambda_.Function(
    "orders-api",
    runtime="python3.14",
    handler="handler.handler",
    role=role.arn,

    code=pulumi.FileArchive("../app"),

    timeout=30,
    memory_size=512,

    environment=aws.lambda_.FunctionEnvironmentArgs(
        variables={
            "ENVIRONMENT": environment,
            "LOG_LEVEL": "INFO"
        }
    ),

    opts=pulumi.ResourceOptions(
        depends_on=[policy]
    )
)
```

This example assumes that `../app` contains a correctly packaged Lambda application with all required dependencies.

For production, I recommend generating a ZIP artifact in the build pipeline and deploying that immutable artifact rather than packaging an uncontrolled development directory.

### 11.2 Publish an immutable version

```python
version = aws.lambda_.Version(
    "orders-api-version",
    function_name=function.name,
    description="Production release",
    opts=pulumi.ResourceOptions(
        replace_on_changes=["code_sha256"]
    )
)
```

In production, ensure that the deployment process updates the function code hash or artifact identity so that a new version is published when the application changes.

### 11.3 Create a production alias

```python
production = aws.lambda_.Alias(
    "orders-api-production",
    name="production",
    function_name=function.name,
    function_version=version.version
)
```

Now the alias points to the published version.

### 11.4 Export deployment information

```python
pulumi.export("function_name", function.name)

pulumi.export("function_arn", function.arn)

pulumi.export("production_alias_arn", production.arn)
```

You can retrieve outputs using:

```bash
pulumi stack output
```

This is a simplified deployment example. A production implementation should also manage artifact hashing, runtime compatibility, release metadata, IAM permissions, and deployment dependencies explicitly.

### 12\. Managing environment variables and Lambda layers with Pulumi

Lambda environment variables are useful for application configuration.

For example:

```python
environment=aws.lambda_.FunctionEnvironmentArgs(
    variables={
        "APP_ENV": "production",
        "LOG_LEVEL": "INFO",
        "DATABASE_HOST": "database.internal"
    }
)
```

For sensitive information, use Secrets Manager or Parameter Store rather than ordinary environment variables.

### 12.1 Lambda Layers

Layers allow you to package dependencies separately from your function code.

Example structure:

```text
layer/
└── python/
    ├── requests/
    └── urllib3/
```

Create a ZIP archive:

```bash
cd layer

zip -r ../dependencies-layer.zip python/

cd ..
```

Create the layer using Pulumi:

```python
layer = aws.lambda_.LayerVersion(
    "orders-dependencies",
    layer_name="orders-dependencies",
    code=pulumi.FileArchive("../dependencies-layer.zip"),
    compatible_runtimes=["python3.14"]
)
```

Attach it to the Lambda function:

```python
function = aws.lambda_.Function(
    "orders-api",
    runtime="python3.14",
    handler="handler.handler",
    role=role.arn,
    code=pulumi.FileArchive("../deployment.zip"),
    layers=[layer.arn]
)
```

Layers are useful when multiple functions share the same dependencies.

However, they introduce version management considerations. Updating a layer does not automatically update existing functions to use the new layer version.

### 12.2 Managing event source mappings

Pulumi can also manage connections between Lambda and polling-based event sources such as SQS.

For example:

```python
mapping = aws.lambda_.EventSourceMapping(
    "orders-queue-mapping",
    event_source_arn=queue.arn,
    function_name=production.arn,
    batch_size=10,
    enabled=True
)
```

This connects the SQS queue to the production Lambda alias.

For production, also consider:

* Visibility timeout.

* Batch window.

* Maximum concurrency.

* Partial batch failure reporting.

* Dead-letter queue configuration.

* Queue retention and retry policies.

### 13\. Pulumi state management, imports, previews, and updates

Pulumi maintains a state file that tracks the infrastructure resources managed by your project.

For Lambda deployments, the state tracks resources such as:

* Lambda functions.

* IAM roles and policies.

* Lambda versions.

* Lambda aliases.

* Event source mappings.

* Function URLs.

* API Gateway integrations.

### 13.1 Preview infrastructure changes

Before deploying:

```bash
pulumi preview
```

This displays the resources Pulumi intends to create, update, replace, or delete.

For example:

```text
+ aws:lambda:function:Function orders-api
+ aws:iam:role:Role orders-lambda-role
+ aws:lambda:alias:Alias orders-api-production
```

The symbols indicate the planned operations.

### 13.2 Deploy infrastructure

```bash
pulumi up
```

Pulumi calculates the differences between the desired infrastructure and its recorded state, then applies the changes.

### 13.3 Refresh state

If someone changes an AWS resource outside Pulumi, the recorded state might become outdated.

Use:

```bash
pulumi refresh
```

This reconciles Pulumi's state with the actual infrastructure.

### 13.4 Import existing Lambda resources

Suppose you already have a Lambda function created manually.

You can import it into Pulumi instead of recreating it.

For example:

```bash
pulumi import \
    aws:lambda/function:Function \
    orders-api \
    orders-api
```

The general syntax is:

```bash
pulumi import RESOURCE_TYPE RESOURCE_NAME AWS_RESOURCE_ID
```

After importing, define the corresponding resource in your Python program so Pulumi can manage it going forward.

### 13.5 State management best practices

For production environments:

* Use a reliable remote state backend.

* Enable state encryption.

* Restrict access to deployment credentials.

* Separate development and production stacks.

* Review previews before production updates.

* Avoid manually modifying Pulumi state.

* Keep infrastructure definitions in Git.

* Use secrets for sensitive configuration.

One important distinction: Pulumi state tracks infrastructure; it is not a backup of your Lambda application code or a complete release history.

Keep deployment artifacts and release metadata in a separate, durable storage location.

### 14\. CI/CD automation using GitHub Actions

Continuous Integration and Continuous Deployment automate the process of building, testing, packaging, and deploying Lambda applications.

A typical deployment architecture looks like this:

![🚀 \[GitHub Actions Series #14\] Deploy to AWS Lambda with GitHub Actions + OIDC | by Bharat Puri | Medium](https://images.openai.com/static-rsc-4/_mk5cEIMUypsAeVKjQ5UgTt9_TFttdjZA6-SsfrYkVrkJT85mMtDgVh0KOO6RBmr3zc7WM1FQKn_sHur0VYSDgSJSU8v_uFihby2-bUQGDela_EKrC-E8WQFOWYlg6O9Thn3XVjYIMgbuxzOfrmZfJtx1jqMP1WzKJccSU3PzmC3M2zaE51eRE08tLt8adLG?purpose=fullsize)

```text
Developer
    |
    v
GitHub Repository
    |
    v
GitHub Actions
    |
    +---- Build Python application
    |
    +---- Install dependencies
    |
    +---- Package Lambda
    |
    +---- Authenticate with AWS
    |
    +---- Pulumi Preview
    |
    +---- Pulumi Up
    |
    v
AWS Lambda
    |
    v
Publish Version
    |
    v
Update Production Alias
```

### 14.1 GitHub Actions workflow

A workflow can be triggered when changes are pushed to the main branch.

Example:

```yaml
name: Deploy Lambda

on:
  push:
    branches:
      - main

permissions:
  id-token: write
  contents: read

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Install Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.14"

      - name: Install uv
        uses: astral-sh/setup-uv@v6

      - name: Install dependencies
        run: |
          cd infrastructure
          uv sync --locked

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
          aws-region: eu-west-2

      - name: Install Pulumi CLI
        uses: pulumi/actions@v6

      - name: Deploy infrastructure
        uses: pulumi/actions@v6
        with:
          command: up
          stack-name: organization/orders-lambda/prod
          work-dir: infrastructure
        env:
          PULUMI_ACCESS_TOKEN: ${{ secrets.PULUMI_ACCESS_TOKEN }}
```

This is a deployment-oriented example. In a production pipeline, pin third-party actions to reviewed commit SHAs, add dependency caching, and separate validation and deployment stages.

Also, the application packaging process must be connected to the infrastructure definition so that Pulumi deploys the newly built artifact.

### 14.2 GitHub Actions authentication with AWS OIDC

Notice that the workflow uses:

```yaml
role-to-assume: ${{ secrets.AWS_ROLE_ARN }}
```

This is an important security feature.

Instead of storing long-lived AWS access keys in GitHub, you can use OpenID Connect (OIDC).

The architecture:

```text
GitHub Actions
      |
      | OIDC token
      v
AWS IAM OIDC Provider
      |
      v
STS AssumeRoleWithWebIdentity
      |
      v
Temporary AWS Credentials
      |
      v
AWS Lambda / Pulumi
```

The IAM role should restrict trust to the intended GitHub organization, repository, and branch or GitHub environment.

This provides temporary credentials without requiring permanent AWS access keys.

### 14.3 Separate CI and CD responsibilities

A mature pipeline usually has two logical stages.

Continuous Integration:

* Validate Python code.

* Install dependencies.

* Build deployment artifacts.

* Check packaging compatibility.

* Run static analysis.

* Validate Pulumi infrastructure definitions.

* Generate deployment previews.

Continuous Deployment:

* Authenticate with AWS.

* Select the correct Pulumi stack.

* Deploy infrastructure and application changes.

* Publish Lambda versions.

* Promote aliases.

* Monitor deployment health.

This separation helps prevent unvalidated application code from reaching production.

### 15\. Deployment rollback and release management

A production deployment strategy must include a reliable rollback mechanism.

There are several ways to roll back Lambda releases.

### 15.1 Alias rollback

This is one of the simplest approaches.

Suppose:

```text
Version 5 → Current production
Version 6 → New release
```

After deployment, Version 6 produces unexpected errors.

Restore the previous version:

```bash
aws lambda update-alias \
    --function-name orders-api \
    --name production \
    --function-version 5
```

Because the API Gateway integration invokes the alias, the API does not need to be reconfigured.

### 15.2 CodeDeploy automatic rollback

CodeDeploy can automatically roll back a Lambda deployment when configured CloudWatch alarms indicate a failure.

For example:

```text
Deploy Version 6
       |
       v
Send 10% traffic to Version 6
       |
       v
Monitor CloudWatch alarms
       |
       +---- Healthy ----> Continue deployment
       |
       +---- Unhealthy --> Automatic rollback
```

This is especially useful for canary deployments.

### 15.3 Pulumi rollback considerations

Pulumi can help restore infrastructure configuration, but it is important to understand the difference between infrastructure rollback and application release rollback.

For example:

* Pulumi can restore an alias to an earlier version.

* Pulumi can restore previous IAM policies.

* Pulumi can restore earlier event source mapping configuration.

* Pulumi can recreate or update infrastructure resources.

However, `pulumi cancel`, `pulumi refresh`, and `pulumi destroy` are not deployment rollback mechanisms.

For Lambda application releases, version and alias management is usually the cleaner rollback strategy.

### 15.4 Release management

A good release process should identify each deployment clearly.

Example:

```text
orders-api/
├── v1.0.0
├── v1.1.0
├── v1.2.0
└── v2.0.0
```

For each release, maintain:

* Application version.

* Git commit SHA.

* Deployment artifact checksum.

* Lambda published version.

* Deployment timestamp.

* Pulumi stack.

* Deployment outcome.

* Rollback target.

This provides traceability when troubleshooting production issues.

### 16\. Production deployment architecture

Let's bring the concepts together into a realistic production architecture.

Imagine you're building an order-processing API using FastAPI-style application logic deployed as Lambda functions.

![](https://images.openai.com/static-rsc-4/NyuEwNbUgI2eg-_aEpfrEpwVUBHMrjUFVzGbKlZDERZZ92MedAZ-S_wDXSv8XUqeEpb1GUw5EoJ_eq0iLWxmthlbV7pwtBm8gg2ktFDE_9P-DhW7puKV7wVJtrhq-RSFWypIdftiLdusG-IT44mHDe4TpYdZ7PBxcB6Rhb4IuTIz7MJ7ZxkGoeC9ciP2kibz?purpose=fullsize)

The architecture contains:

| Component       | Responsibility                             |
| --------------- | ------------------------------------------ |
| GitHub          | Application and infrastructure source code |
| GitHub Actions  | Automated build and deployment             |
| Pulumi          | Infrastructure provisioning                |
| IAM OIDC        | Secure CI/CD authentication                |
| API Gateway     | HTTP API entry point                       |
| Lambda          | Application execution                      |
| Lambda versions | Immutable application releases             |
| Lambda aliases  | Environment and traffic management         |
| CodeDeploy      | Gradual traffic shifting                   |
| CloudWatch      | Monitoring and alarms                      |
| ECR / S3        | Deployment artifact storage                |

### 16.1 Recommended release workflow

The complete release process looks like this:

* Developer pushes application changes to GitHub.

* GitHub Actions checks out the repository.

* Python dependencies are installed.

* The application is packaged.

* The deployment artifact is generated and identified by its checksum.

* GitHub Actions authenticates with AWS using OIDC.

* Pulumi previews infrastructure changes.

* Pulumi deploys the new Lambda code and infrastructure.

* A new immutable Lambda version is published.

* The staging alias is updated.

* The application is validated.

* CodeDeploy gradually shifts production traffic.

* CloudWatch monitors application health.

* The deployment is completed or automatically rolled back.

This is a practical foundation for production-grade serverless delivery.

### 17\. Important deployment best practices

There are several principles worth following when deploying Lambda applications at scale.

### Application deployment

* Prefer immutable deployment artifacts.

* Use unique artifact identifiers.

* Separate application code from infrastructure code.

* Keep dependencies minimal.

* Use ZIP packages for ordinary Python functions.

* Use container images when custom OS dependencies or larger packages justify them.

### Version management

* Publish versions for production releases.

* Use aliases instead of invoking `$LATEST`.

* Maintain release metadata.

* Avoid deleting versions still used by production.

* Use gradual traffic shifting for risky deployments.

### Infrastructure management

* Use Pulumi for repeatable infrastructure deployment.

* Separate stacks for different environments.

* Keep secrets encrypted.

* Use remote state management.

* Review infrastructure previews.

* Avoid unnecessary infrastructure replacement.

### CI/CD security

* Prefer GitHub OIDC over permanent AWS access keys.

* Apply least-privilege IAM permissions.

* Protect production deployment environments.

* Pin GitHub Actions dependencies.

* Keep deployment credentials out of application code.

### Reliability

* Configure CloudWatch alarms.

* Monitor error rates and latency.

* Use automatic rollback where appropriate.

* Maintain backward-compatible database migrations.

* Test the deployed version before production promotion.

### 18\. Key concepts and how they fit together

Here is how the major technologies in this module relate to one another.

| Technology       | What it solves                                        |
| ---------------- | ----------------------------------------------------- |
| ZIP deployment   | Packages Python application code                      |
| Container images | Packages applications with their runtime dependencies |
| AWS CLI          | Direct Lambda management and automation               |
| Lambda versions  | Immutable application releases                        |
| Lambda aliases   | Stable references to application versions             |
| Weighted routing | Gradual traffic distribution                          |
| CodeDeploy       | Automated canary and linear deployments               |
| Function URLs    | Direct HTTPS access to Lambda                         |
| API Gateway      | Managed API exposure and traffic management           |
| Pulumi           | Infrastructure as Code                                |
| Pulumi stacks    | Environment separation                                |
| Pulumi state     | Infrastructure tracking                               |
| GitHub Actions   | Automated CI/CD                                       |
| AWS OIDC         | Temporary CI/CD authentication                        |
| CloudWatch       | Monitoring and deployment alarms                      |

### Final architectural picture

### Lambda production delivery lifecycle

1\. Source code

Python application + Pulumi infrastructure

2\. GitHub Actions

Build · Package · Validate · Authenticate

3\. Pulumi deployment

IAM · Lambda · Versions · Permissions · Integrations

4\. Lambda published version

Immutable application release

5\. Alias promotion and CodeDeploy

Staging → Canary → Production

6\. Production monitoring

CloudWatch · Alarms · Rollback · Release tracking

The most important takeaway: Pulumi manages your infrastructure, GitHub Actions automates your delivery pipeline, Lambda versions preserve application releases, aliases control which release receives traffic, and CodeDeploy can automate gradual deployment and rollback.

Together, these technologies provide a strong foundation for managing Lambda applications throughout their production lifecycle.
