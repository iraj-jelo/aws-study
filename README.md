# AWS Study

A practical, self-paced collection of AWS fundamentals, hands-on examples, and implementation notes. The repository is organized around core AWS services and follows a dependency-first learning path—from accounts and IAM through networking, compute, storage, observability, infrastructure as code, and architecture.

## Learning Topics

| Area | Topics covered |
|---|---|
| [AWS Fundamentals](./learning%20order%20of%20aws%20services.md) | Recommended learning order, study roadmap, and a practical project path |
| [CloudWatch](./CloudWatch/) | Metrics, logs, alarms, monitoring, and troubleshooting |
| [EC2](./EC2/) | Instances, AMIs, storage, scaling, load balancing, and networking |
| [ECS and EKS](./ECS-EKS/) | Container orchestration with Amazon ECS and Amazon EKS |
| [IAM](./IAM/) | Users, groups, roles, policies, ARN, STS, and least-privilege security |
| [Load Balancing](./LB/) | Application and network traffic distribution |
| [Lambda](./Lambda/) | Serverless functions, event-driven architectures, and Python examples |
| [Route 53](./Route53/) | DNS records, routing policies, and domain management |
| [S3](./S3/) | Buckets, objects, permissions, versioning, lifecycle, and storage classes |
| [SNS](./SNS/) | Publish-subscribe messaging and notifications |
| [SQS](./SQS/) | Message queues, decoupling, and asynchronous processing |
| [VPC](./VPC/) | Subnets, routing, gateways, endpoints, and network security |

Each service directory contains an overview README and numbered modules with detailed notes and diagrams.

## Recommended Learning Path

Start with AWS fundamentals and security before provisioning workloads:

1. AWS accounts, Regions, Availability Zones, Console, and CLI
2. IAM users, roles, policies, and least-privilege access
3. VPC, subnets, routing, security groups, and network ACLs
4. EC2, EBS, Elastic Load Balancing, and Auto Scaling
5. S3 and data durability
6. Managed databases and storage options
7. CloudWatch and operational auditing
8. Lambda and container services
9. Pulumi, APIs, automation, and CI/CD
10. Multi-AZ architecture and the AWS Well-Architected Framework

The repository's [learning roadmap](./learning%20order%20of%20aws%20services.md) expands this sequence into 51 study areas.

## Hands-On Project

A good way to use this repository is to build one application throughout the learning journey instead of creating disconnected demos:

- Create an AWS account and IAM roles
- Configure a VPC with public and private subnets
- Deploy an application on EC2 or ECS
- Place it behind a load balancer
- Store application data in RDS or DynamoDB
- Upload files to S3
- Record metrics and logs with CloudWatch
- Define infrastructure with Pulumi
- Apply least-privilege permissions and clean up resources

## Prerequisites

- An AWS account with billing controls and a non-root administrative identity
- AWS CLI v2
- AWS Console access
- Python 3
- Shell access for CLI examples
- A basic understanding of networking, Linux, DNS, and HTTP

## AWS Cost and Safety

The examples may create billable resources. Before running or modifying infrastructure:

- Review AWS service pricing and Free Tier limits
- Set an AWS budget and billing alarms
- Use IAM roles with least-privilege permissions
- Prefer short-lived credentials and MFA
- Record environment names and regions
- Delete test resources after each session

Never commit AWS access keys, session tokens, account credentials, or other secrets.

## Repository Layout

```text
aws-study/
├── CloudWatch/
├── EC2/
├── ECS-EKS/
├── IAM/
├── LB/
├── Lambda/
├── Route53/
├── S3/
├── SNS/
├── SQS/
├── VPC/
└── learning order of aws services.md
```

## Contributing

Contributions are welcome. Useful additions include:

- Correcting outdated AWS behavior or terminology
- Adding practical examples and diagrams
- Improving setup or cleanup instructions
- Adding reusable Python or shell automation
- Linking exercises to the learning roadmap

Open an issue or submit a pull request for changes.

## License

No license has been specified for this repository.
