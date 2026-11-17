# What is an ARN in AWS?

ARN stands for Amazon Resource Name. It's a standardized identifier AWS uses to identify a particular resource, such as an S3 bucket, a Lambda function, an IAM role, or a DynamoDB table.

Think of an ARN as a resource's full address in AWS.

For example, on your computer, a file might be identified by:

```
C:\projects\books\cover.jpg
```

In AWS, a resource can be identified by an ARN such as:

```
arn:aws:s3:::study-books/covers/cover.jpg
```

The two identifiers serve a similar purpose: they help specify exactly which resource you're referring to. However, an ARN follows AWS's own structure and isn't a filesystem path.

## 1. Anatomy of an ARN

Let's break down an ARN:

## Example: An S3 object

arn:aws:s3:::study-books/covers/cover.jpg

Partition

aws

AWS partition

Service

s3

Amazon S3

Region

Empty

S3 bucket/object ARNs omit the region

Account ID

Empty

This S3 ARN format omits the account ID

Resource

study-books/covers/cover.jpg

The bucket name followed by the object key.

The general ARN format is:

```
arn:partition:service:region:account-id:resource
```

The components are:

| Component    | Meaning                                                      |
| ------------ | ------------------------------------------------------------ |
| `arn`        | Marks the identifier as an ARN                               |
| `partition`  | The AWS partition, such as `aws` or `aws-us-gov`             |
| `service`    | The AWS service, such as `s3`, `iam`, or `lambda`            |
| `region`     | The AWS Region, when applicable                              |
| `account-id` | The AWS account ID, when applicable                          |
| `resource`   | The resource identifier, whose format depends on the service |

Important: Some components can be empty. Not every ARN contains a Region or account ID, and the resource component can contain additional colons or slashes. Always follow the ARN format documented for the specific AWS service.

## 2. More examples of ARNs

Different AWS services use different ARN formats. Here are some common ones.

S3 bucket

```
arn:aws:s3:::study-books
```

Identifies the bucket named `study-books`.

S3 object

```
arn:aws:s3:::study-books/covers/book.jpg
```

Identifies the object with key `covers/book.jpg` inside the bucket.

IAM role

```
arn:aws:iam::123456789012:role/BookAppRole
```

Identifies the `BookAppRole` role in account `123456789012`. IAM role ARNs don't contain a Region.

Lambda function

```
arn:aws:lambda:us-east-1:123456789012:function:ProcessBooks
```

Identifies the `ProcessBooks` function in `us-east-1` in the specified account.

DynamoDB table

```
arn:aws:dynamodb:us-east-1:123456789012:table/Books
```

Identifies the `Books` table in the specified Region and account.

The account ID and resource names above are illustrative.

## 3. Why are ARNs important in IAM policies?

This is where ARNs become especially useful.

Suppose your FastAPI application needs to read book covers from S3. You don't want to give it permission to access every S3 bucket in your account.

You can specify the exact resources in an IAM policy:

```
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:GetObject",
      "Resource": "arn:aws:s3:::study-books/covers/*"
    }
  ]
}
```

This policy statement allows `s3:GetObject` for objects whose keys begin with `covers/` in the `study-books` bucket, subject to other applicable authorization rules.

For example:

| Object                      | Matches the ARN pattern? |
| --------------------------- | ------------------------ |
| `covers/book1.jpg`          | Yes                      |
| `covers/book2.png`          | Yes                      |
| `documents/book.pdf`        | No                       |
| An object in another bucket | No                       |

The `*` is a wildcard. It matches resource-name characters according to AWS policy pattern-matching rules.

Notice that the policy uses two different concepts:

- `Action` specifies what operation is allowed.
- `Resource` specifies which resource or resources the statement applies to.

You generally need to understand both to write a least-privilege policy.

## 4. What does `*` mean in an ARN?

Wildcards let you match multiple resources without listing each one individually.

Consider these three patterns:

Specific resource

```
arn:aws:s3:::study-books/covers/book1.jpg
```

Matches the specified object.

Multiple objects

```
arn:aws:s3:::study-books/covers/*
```

Matches objects under the `covers/` key prefix.

Broader scope

```
arn:aws:s3:::study-books/*
```

Matches objects under the bucket's key namespace, not the bucket resource itself.

A common beginner mistake is to assume that `*` means absolutely everything in AWS. It doesn't. It matches within the ARN pattern where it appears, and the action still matters.

For example, `s3:GetObject` with `Resource: "*"` does not automatically grant every S3 operation. The statement only applies to the specified action and any other constraints in effect.

Also, S3 object ARNs use the object's key, not a directory structure in the filesystem sense. Prefixes such as `covers/` are part of the key naming scheme.

## 5. How do you find an ARN?

You usually don't need to invent an ARN manually. AWS provides several ways to obtain one.

Using the AWS CLI

For your current identity:

```
aws sts get-caller-identity
```

Example:

```
{
  "UserId": "AIDAEXAMPLE",
  "Account": "123456789012",
  "Arn": "arn:aws:iam::123456789012:user/developer"
}
```

For a Lambda function:

```
aws lambda get-function `
  --function-name ProcessBooks `
  --query "Configuration.FunctionArn" `
  --output text
```

For an S3 bucket, you can construct the standard bucket ARN from its name:

```
arn:aws:s3:::your-bucket-name
```

S3 bucket ARNs do not include an account ID or Region.

Using Pulumi

When you define AWS resources with Pulumi, many resource objects expose an `arn` output. For example:

```
import pulumiimport pulumi_aws as awsbucket = aws.s3.BucketV2("study-books")pulumi.export("bucket_arn", bucket.arn)
```

This example creates an S3 bucket resource and exports its ARN. The AWS provider must be configured with suitable credentials, and deploying the resource requires the appropriate permissions.

For new projects, we'll use current Pulumi AWS provider resource types and avoid introducing legacy resource types when newer alternatives are available.

## 6. ARN vs. URL vs. resource name

These concepts are easy to confuse.

| Identifier    | Example                                              | Purpose                                                                                 |
| ------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------- |
| ARN           | `arn:aws:s3:::study-books`                           | Identifies an AWS resource                                                              |
| Resource name | `study-books`                                        | The bucket's name                                                                       |
| URL           | `https://example-bucket.s3.us-east-1.amazonaws.com/` | A network address used to access a resource, depending on the service and configuration |

An ARN isn't necessarily a URL you can open in a browser. It's primarily an identifier used by AWS APIs, policies, configuration, and other AWS features.

## 7. The key takeaway

Whenever you read an IAM policy, try to interpret it as a sentence:

> Allow this action, on this resource, under these conditions.

For example:

```
{
  "Effect": "Allow",
  "Action": "lambda:InvokeFunction",
  "Resource": "arn:aws:lambda:us-east-1:123456789012:function:ProcessBooks"
}
```

Read it as:

> Allow invoking the Lambda function named `ProcessBooks` in account `123456789012`, in Region `us-east-1`, subject to the rest of AWS's authorization rules.

That's the essential purpose of an ARN: it tells AWS which resource a policy or API request is referring to.

For the authoritative reference, see the AWS documentation on [Amazon Resource Names (ARNs)](https://docs.aws.amazon.com/IAM/latest/UserGuide/reference-arns.html).