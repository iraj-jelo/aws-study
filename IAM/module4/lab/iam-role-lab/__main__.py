"""An AWS Python Pulumi program"""

import json

import pulumi
import pulumi_aws as aws


config = pulumi.Config()

bucket_name = config.require("bucketName")
trusted_account_id = config.require("trustedAccountId")

# --------------------------------------------------
# 1. S3 Bucket
# --------------------------------------------------

bucket = aws.s3.Bucket(
    "books",
    bucket=bucket_name,
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
                "AWS": f"arn:aws:iam::{trusted_account_id}:root"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}

# --------------------------------------------------
# 3. IAM Permissions Boundary
# --------------------------------------------------

# boundary_document = {
#     "Version": "2012-10-17",
#     "Statement": [
#         {
#             "Effect": "Allow",
#             "Action": [
#                 "s3:ListBucket",
#             ],
#             "Resource": f"arn:aws:s3:::{bucket_name}"
#         },
#         {
#             "Effect": "Allow",
#             "Action": [
#                 "s3:GetObject",
#             ],
#             "Resource": f"arn:aws:s3:::{bucket_name}/*",
#         }
#     ],
# }

# boundary_policy = aws.iam.Policy(
#     "book-reader-boundary",
#     name="BookReaderBoundary",
#     policy=json.dumps(boundary_document),
# )

# --------------------------------------------------
# 4. IAM Role
# --------------------------------------------------

# Attach this boundary when defining the role:
role = aws.iam.Role(
    "book-reader-role",
    name="BookReaderRole",
    description="Read-only access to one S3 bucket for the IAM lab",
    assume_role_policy=json.dumps(trust_policy_document),
    max_session_duration=3600,
    tags={
        "purpose": "IAM-training",
        "Access": "ReadOnly",
    },
    # permissions_boundary=boundary_policy.arn,
)

# --------------------------------------------------
# 5. IAM Permissions Policy
# --------------------------------------------------

book_reader_policy_document = {
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "ListOnlyBookBucket",
            "Effect": "Allow",
            "Action": [
                "s3:ListBucket",
            ],
            "Resource": f"arn:aws:s3:::{bucket_name}"
        },
        {
            "Sid": "ReadBookObjects",
            "Effect": "Allow",
            "Action": [
                "s3:GetObject",
            ],
            "Resource": f"arn:aws:s3:::{bucket_name}/*",
        }
    ],
}


book_reader_policy = aws.iam.Policy(
    "book-reader-policy",
    name="BookReadPolicy",
    description="List Book bucket and read its objects",
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

# bucket_policy_document = pulumi.Output.all(
#     role.arn,
#     bucket.arn
# ).apply(
#     lambda args: json.dumps({
#         "Version": "2012-10-17",
#         "Statement": [
#             {
#                 "Sid": "AllowBookReaderRoleListBucket",
#                 "Effect": "Allow",
#                 "Principal": {
#                     "AWS": args[0]
#                 },
#                 "Action": ["s3:ListBucket"],
#                 "Resource": f"{args[1]}"
#             },
#             {
#                 "Sid": "AllowBookReaderRoleReadObjects",
#                 "Effect": "Allow",
#                 "Principal": {
#                     "AWS": args[0]
#                 },
#                 "Action": ["s3:GetObject"],
#                 "Resource": f"{args[1]}/*"
#             }
#         ]
#     })
# )

# bucket_policy = aws.s3.BucketPolicy(
#     "book-reader-readonly-policy",
#     bucket=bucket.id,
#     policy=bucket_policy_document,
# )


# --------------------------------------------------
# 8. Exports
# --------------------------------------------------

pulumi.export('bucket_name', bucket.id)
pulumi.export('role.arn', role.arn)
pulumi.export('book_reader_policy.arn', book_reader_policy.arn)
pulumi.export('book_reader_policy.id', book_reader_policy.id)
pulumi.export('policy_attachment.id', policy_attachment.id)
# pulumi.export('bucket_policy.id', bucket_policy.id)
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