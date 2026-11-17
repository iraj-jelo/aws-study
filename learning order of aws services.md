I'd learn AWS services in dependency order, not alphabetically. First understand the platform and security, then networking, compute, storage, databases, and finally deployment and architecture.

# AWS Fundamentals — Recommended Learning Order

Roadmap from beginner to practical cloud engineering

[AWS Management Console: Features and Benefits](https://images.openai.com/static-rsc-4/N0KzRgot0JqQnA3NyPTb38lF73SWPNSWjrwdkrL_3EHAnGq2viVlPIj0uk70HhcyTwSamrWAl7XgBG6LKz6ur0n0ryHsQaCcDUz6uMIsXNV2cuR6BbDFfBG7wpj8RA88R2wbNKBiHsrsCRtjaXZYUdP6d5FCHSR8XLk9qmDVcnI?purpose=inline)

### Phase 1 — AWS Platform Basics

Understand where everything lives.

1. AWS global infrastructure: Regions and Availability Zones
2. AWS accounts and account boundaries
3. AWS Organizations — introductory concepts
4. AWS Management Console
5. AWS CLI v2 and CloudShell
6. AWS pricing, billing, and Free Tier eligibility

[How IAM works - AWS Identity and Access Management](https://images.openai.com/static-rsc-4/nggNFZiu2R-6kjoUg5NdkOBzNc9MTMIeErQvfKJik7uXtN6cGUbZ9upnPzLN-I8GSbxB8_iC9KNIWIizkpdHe0ZwGqW-_t56yDAZ8WwmUX3Ml5WoGP3FdUHE2Q68QUOrM_rav4goa4PPFfcU4knWC-cjPlGxPER4wLQouMQsGFs?purpose=inline)

### Phase 2 — Identity and Security

Learn this before provisioning resources.

7\. IAM users, groups, roles, and policies 8. IAM policy evaluation and least privilege 9. AWS STS and temporary credentials 10. IAM Identity Center and human access 11. AWS KMS and encryption fundamentals 12. Secrets Manager and Systems Manager Parameter Store

[If AWS Networking Confuses You — This Guide Is Your Missing Map | by Muhammad Shahbaj | Medium](https://images.openai.com/static-rsc-4/yuF0NBA9405e4do5FU7fAW3dvBFHDQ69ZK3P0FaDT_mD886EmJVuvT1Tvi4b4HWen_ipZ1Lba_1bybEvkmxft6WtVGvXE5FG-TKhqPwpAxmz1givpPPALHOYzzII9uVJ0fHCok7uqmHPxhpQ524MnLq0Wb4p_96dlKYM5s9QiKA?purpose=inline)

### Phase 3 — Networking

Build the network before deploying applications.

13\. Amazon VPC, CIDRs, and subnets 14. Route tables and Internet Gateway 15. Security groups and network ACLs 16. NAT Gateway and outbound connectivity 17. Route 53 and DNS 18. VPC endpoints and private service access

[Elastic Compute Cloud (EC2) - GeeksforGeeks](https://images.openai.com/static-rsc-4/H0-rOLtvjiqzJmNUhguH6YM60CusWrhfy1ZO9TMB4rZEmISh5DuKgLYwMFd-VpGI5Ebz-p-7913hE9Y-hW9C9UzhA9j0SbF6_Tn8IKcTr5Pinq_SDg70G3LdS5QWAdJ2eXUNMsO0FMG_RTSdmCny1OEPZMqmKOhnUetdCsRqXGs?purpose=inline)

### Phase 4 — Compute

Learn how applications run.

19\. Amazon EC2 and Amazon Machine Images 20. Amazon EBS and instance storage 21. EC2 IAM roles and instance profiles 22. Elastic Load Balancing 23. EC2 Auto Scaling 24. AWS Lambda 25. Amazon ECR and Amazon ECS 26. Amazon EKS overview

[How to Create an S3 Bucket in AWS Using Terraform · Mike Vu](https://images.openai.com/static-rsc-4/jZqDUzzQUb10BhmSmtsIq4JkYLqCJFNxVTICjssDZoJFY4UTiPDOR9kbdllzsXxTG9DfBsjEngZcm9zdtQS33Fp8F25T6nuDKr_LqN-p5UG54-qjVyCmOEEZXPRy91IGtmB0XIYNQdbMe0xpjXRAqfw6KklmYkIlFYMYf7ZEo_8?purpose=inline)

### Phase 5 — Storage and Databases

Understand persistence, backups, and data access.

27\. Amazon S3 28. S3 versioning and lifecycle policies 29. Amazon RDS and PostgreSQL 30. Amazon Aurora overview 31. Amazon DynamoDB 32. Amazon EFS and Amazon FSx overview 33. Backup, recovery, and retention

[How to build Web Application Dashboards in AWS CloudWatch | Si Novi](https://images.openai.com/static-rsc-4/xbprTUD3Imyx_d8fEIDKf1XNT2DdMHYspSKIaYtg8x8B3KHmr6oQg6iLWCzlGAOHBxd0Jv-W3CTJcl2XNS1vJ8_EYdHrmbQhKMrZ4xxlVYETa6TfFDPsMUA5298w0SEqHY-K-HMKCrS0BE0KmrJ1iwqDkjRA7Qgv7HQYqikhsCU?purpose=inline)

### Phase 6 — Operations and Observability

Operate and troubleshoot workloads.

34\. Amazon CloudWatch metrics, logs, and alarms 35. AWS CloudTrail 36. AWS Config 37. AWS Health 38. AWS Systems Manager 39. AWS Budgets and Cost Explorer

[Mastering AWS Infrastructure as Code with Pulumi and Python - Part 1 / Blogs / Perficient](https://images.openai.com/static-rsc-4/rEDmWIcNtjN3_H9Bq87E7aqkxUsoC0nbPyHrfvfoisVlpvP8wkxkA0DwuFgQysEl0d9ceHJrE01Mkv1bJDhN-ZwBiPrE45ZerVyfwmJeBsOxcfV_nIDifq1OVh0FeXq9C_I4l8z3cVMy18XrjAFFLayRVR6vrXR6ZEIJLlmLyOs?purpose=inline)

### Phase 7 — Infrastructure as Code and Automation

Make infrastructure reproducible.

40\. Pulumi fundamentals with Python 41. AWS provider, resources, stacks, and configuration 42. Reusable networking and application components 43. Python Boto3 and AWS API automation 44. GitHub Actions with OIDC federation 45. CI/CD, previews, deployment verification, and cleanup

[Designing a Three-Tier Architecture Design | by Babatunde Oyedeji | Medium](https://images.openai.com/static-rsc-4/nmt-lcuHv8azwAhvEnxrnx39uutpbU5UsEt4RSH1SbMiUBtBwkxq5tGbFE0nUI35-wD0zWy9YjlTguXL36N2br0lJ0nFilHfqiQEeBoP64cCBIvHED0J3IYXF5CqHbma-a-M92Vv56-oQLk6z_lS-tz0zfJrTYagCge36hlgFfQ?purpose=inline)

### Phase 8 — Integration and Architecture

Combine the services into working systems.

46\. Amazon SQS, SNS, and EventBridge 47. AWS Well-Architected Framework 48. Multi-AZ and high-availability design 49. Multi-account architecture 50. Security, reliability, and cost optimization 51. Production-style application capstone

## The first 15 services and concepts to prioritize

If you want to get started quickly, concentrate on these before exploring the wider AWS catalog.

| Order | Service or concept       | Why it comes here                               |
| ----- | ------------------------ | ----------------------------------------------- |
| 1     | AWS accounts and Regions | Establish the environment                       |
| 2     | IAM                      | Control access to everything else               |
| 3     | AWS CLI                  | Inspect and operate resources                   |
| 4     | VPC                      | Establish network boundaries                    |
| 5     | Subnets and route tables | Control traffic paths                           |
| 6     | Security groups          | Control network access                          |
| 7     | EC2                      | Run a virtual server                            |
| 8     | EBS                      | Attach persistent block storage                 |
| 9     | S3                       | Store application objects and files             |
| 10    | RDS                      | Run a managed relational database               |
| 11    | Elastic Load Balancing   | Distribute application traffic                  |
| 12    | EC2 Auto Scaling         | Maintain and scale compute capacity             |
| 13    | CloudWatch               | Monitor application and infrastructure behavior |
| 14    | CloudTrail               | Audit AWS API activity                          |
| 15    | Pulumi                   | Provision and manage infrastructure as code     |

## A practical learning project

Use one project throughout the roadmap instead of creating unrelated toy examples.

## Deploy a FastAPI application on AWS

Build incrementally as you learn each service.

```

AWS Account
├── IAM
│   └── Developer and workload roles
├── VPC
│   ├── Public subnets
│   │   └── Application Load Balancer
│   └── Private subnets
│       ├── FastAPI on EC2 or ECS
│       └── RDS PostgreSQL
├── S3
│   └── Uploaded files
├── CloudWatch
│   └── Logs, metrics, and alarms
└── Pulumi
    └── Infrastructure lifecycle
  
```

Learn to deploy the application, restrict access, inspect logs, troubleshoot networking, and tear down resources safely. Later, replace or extend the compute layer with containers and add CI/CD.

Recommended order for your studies: AWS Fundamentals → AWS IAM → AWS VPC → AWS Compute and Storage → AWS Observability → Pulumi and CI/CD → Advanced AWS Architecture.

One important distinction: you don't need to master every service before building something useful. Learn each service when it becomes necessary for your project, and go deeper into specialized services only when your architecture requires them.