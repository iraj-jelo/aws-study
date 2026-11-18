"""An AWS Python Pulumi program"""

import json

import pulumi
import pulumi_aws as aws


# --------------------------------------------------
# 1. S3 Bucket
# --------------------------------------------------

bucket = aws.s3.Bucket(
    "books",
    bucket="study-books",
)

# --------------------------------------------------
# 2. IAM Trust Policy
# --------------------------------------------------

trust_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ec2.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

# --------------------------------------------------
# 3. IAM Permissions Boundary
# --------------------------------------------------

boundary_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
            ],
            "Resource": "arn:aws:s3:::study-books/*",
        }
    ],
}

boundary_policy = aws.iam.Policy(
    "book-reader-boundary",
    name="BookReaderBoundary",
    policy=json.dumps(boundary_document),
)

# --------------------------------------------------
# 4. IAM Role
# --------------------------------------------------

# Attach this boundary when defining the role:
role = aws.iam.Role(
    "book-reader-role",
    name="book-reader-role",
    assume_role_policy=json.dumps(trust_policy_document),
    permissions_boundary=boundary_policy.arn,
)

# --------------------------------------------------
# 5. IAM Permissions Policy
# --------------------------------------------------

book_reader_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ReadBookObjects",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
            ],
            "Resource": "arn:aws:s3:::study-books/*",
        }
    ],
}


book_reader_policy = aws.iam.Policy(
    "book-read-policy",
    name="BookReadPolicy",
    description="Read book objects",
    policy=json.dumps(book_reader_policy_document),
)


# --------------------------------------------------
# 6. Attach IAM Policy to Role
# --------------------------------------------------

policy_attachment = aws.iam.RolePolicyAttachment(
    "book-reader-policy-attachment",
    role=role.name,
    policy_arn=book_reader_policy.arn,
)

# --------------------------------------------------
# 7. S3 Bucket Policy
# --------------------------------------------------

bucket_policy_document = pulumi.Output.all(
    role.arn,
    bucket.arn
).apply(
    lambda args: json.dumps({
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowBookReaderRole",
                "Effect": "Allow",
                "Principal": {
                    "AWS": args[0]
                },
                "Action": ["s3:GetObject"],
                "Resource": f"{args[1]}/covers/*"
            }
        ]
    })
)

bucket_policy = aws.s3.BucketPolicy(
    "study-books-policy",
    bucket=bucket.id,
    policy=bucket_policy_document,
)


# --------------------------------------------------
# 8. Exports
# --------------------------------------------------

pulumi.export('bucket_name', bucket.id)
pulumi.export('role.arn', role.arn)
pulumi.export('book_reader_policy.id', book_reader_policy.id)
pulumi.export('policy_attachment.id', policy_attachment.id)
pulumi.export('bucket_policy.id', bucket_policy.id)
pulumi.export('project', pulumi.get_project())
pulumi.export('stack', pulumi.get_stack())


# aws configure set endpoint_url http://localhost:4566 --profile book-reader
# aws configure set aws_access_key_id test --profile localstack
# aws configure set aws_secret_access_key test --profile localstack
# aws configure set region us-east-1 --profile localstack


# pulumi up
# aws --endpoint-url=http://localhost:4566 s3 ls
# aws s3api list-buckets --endpoint-url=http://localhost:4566
#
# retrieves an S3 bucket policy, not an IAM identity policy
# aws s3api get-bucket-policy --bucket "study-books" --endpoint-url=http://localhost:4566
#
# aws iam list-roles --profile localstack --endpoint-url=http://localhost:4566
# aws iam list-role-policies --role-name book-reader-role-1c8f943 --profile localstack --endpoint-url=http://localhost:4566
# aws iam list-policies --profile localstack --endpoint-url=http://localhost:4566
# aws iam list-attached-role-policies --role-name book-reader-role-1c8f943 --endpoint-url=http://localhost:4566
# aws sts assume-role --role-arn arn:aws:iam::000000000000:role/book-reader-role --role-session-name book-reader-role --profile localstack --endpoint-url=http://localhost:4566