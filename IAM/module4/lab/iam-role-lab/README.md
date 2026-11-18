# IAM Role Lab

### Setup

Run ministack using the `AUTH=true` environment variable to let IAM use authentication when resolving the requests:

```sh
docker run -p 4566:4566 -e AUTH=true --name ministack -v /var/run/docker.sock:/var/run/docker.sock ministackorg/minist
ack
```

Then setup the infrastructure:

```sh
./setup.sh
```

### Quick test

to quickly check the role permissions:

```sh
# Put an object into the books bucket just to test the permissions
aws s3api put-object --bucket books --key "README.md"  --body "./README.md" --profile localstack --endpoint-url http://localhost:4566

# Verify the list-objects permission works for the book-reader profile
aws s3api list-objects --bucket books --profile book-reader --endpoint-url http://localhost:4566

# Verify that the book-reader profile is not allowed to put objects into the books bucket
aws s3api put-object --bucket books --key "README3.md"  --body "./README.md" --profile book-reader --endpoint-url http://localhost:4566
```
