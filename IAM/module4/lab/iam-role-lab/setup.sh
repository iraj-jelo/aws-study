#!/bin/bash

export PULUMI_CONFIG_PASSPHRASE=123456

export BUCKET_NAME="books"
export TRUSTED_ACCOUNT_ID=000000000000

echo "🔧 Configure pulumi:"
echo "    bucketName=\"${BUCKET_NAME}\""
echo "    trustedAccountId=\"${TRUSTED_ACCOUNT_ID}\""

pulumi config set bucketName $BUCKET_NAME
pulumi config set trustedAccountId $TRUSTED_ACCOUNT_ID

echo "🔧 Configure the localstack profile in aws cli (~/.aws/config)..."
aws configure set aws_access_key_id test --profile localstack
aws configure set aws_secret_access_key test --profile localstack
aws configure set region us-east-1 --profile localstack

# echo "👓 pulumi preview ..."
# pulumi preview

echo "🔨 pulumi up..."
pulumi up

export ROLE_ARN=$(pulumi stack output role.arn)

echo "🔧 Configure the book-reader profile in aws cli (~/.aws/config)..."
aws configure set role_arn  ${ROLE_ARN} --profile book-reader
aws configure set source_profile  localstack --profile book-reader # The `source_profile` tells the CLI which profile to use to obtain the credentials that will request the role session.
aws configure set role_session_name  book-reader-lab --profile book-reader
aws configure set region  us-east-1 --profile book-reader
aws configure set endpoint_url  http://localhost:4566 --profile book-reader

echo "🧪 Test the book-reader profile:"
aws sts get-caller-identity \
    --profile book-reader \
    --endpoint-url http://localhost:4566