Module 1 — IAM Fundamentals
Beginner
- What IAM is and how it fits into AWS
- Authentication vs. authorization
- AWS account root user, IAM users, groups, roles, and policies
- Principals, resources, actions, and permissions
- AWS account IDs, ARNs, and IAM terminology
- Console access vs. programmatic access
  Lab: Explore IAM, inspect identities, and create your first read-only policy.




Module 2 — IAM Policies Deep Dive
Core skills
- JSON policy structure: Version, Statement, Effect, Action, Resource, Condition
- Allow vs. Deny and implicit denial
- AWS-managed, customer-managed, and inline policies
- Wildcards and ARN matching
- Action-specific resource permissions
- Condition operators, request context keys, and policy variables
- Tag-based access control (ABAC) vs. role-based access control (RBAC)
  Lab: Build policies that allow access to selected S3 objects while denying sensitive operations.




Module 3 — Policy Evaluation and Authorization
Critical concepts
- How AWS evaluates an API request
- Identity-based vs. resource-based policies
- Explicit Deny precedence
- Permissions boundaries
- Session policies
- Service control policies (SCPs) and resource control policies (RCPs)
- Same-account vs. cross-account access
- Why a policy that contains Allow can still result in AccessDenied
  Lab: Solve policy-evaluation puzzles and trace the cause of authorization failures.




Module 4 — IAM Roles, STS, and Temporary Credentials
- Trust policies vs. permission policies
- AssumeRole and AWS Security Token Service (STS)
- Temporary access key, secret key, and session token
- Role chaining and session duration
- External IDs and the confused deputy problem
- Cross-account role assumption
- Instance profiles and workload identity
  Lab: Assume a role with the AWS CLI and access a resource using temporary credentials.




Module 5 — Identity Management and Security
- IAM Identity Center and federation
- SAML and OpenID Connect (OIDC)
- Multi-factor authentication (MFA)
- Root-user protection
- Access-key lifecycle and credential hygiene
- Least privilege and privilege escalation risks
- Delegated administration
  Lab: Configure a developer/operator access model and audit overly permissive permissions.




Module 6 — IAM for Developers and DevOps
- AWS CLI profiles and credential provider chains
- IAM with Python and Boto3
- IAM roles for EC2, Lambda, and other workloads
- GitHub Actions OIDC federation
- IAM permissions for CI/CD pipelines
- EKS workload identity and IRSA/EKS Pod Identity
- Terraform execution identities and deployment roles
  Lab: Let a CI pipeline deploy a service without storing permanent AWS access keys in repository secrets.




Module 7 — Auditing and Troubleshooting
- IAM Policy Simulator and policy validation
- IAM Access Analyzer
- CloudTrail and tracking identity activity
- Access Advisor and last-accessed information
- IAM policy generation from observed activity
- Debugging AccessDenied, trust-policy errors, and missing permissions
- Detecting public and unintended cross-account access
  Lab: Investigate failed API calls and tighten an overprivileged policy.




Module 8 — Advanced IAM Architecture
- Multi-account AWS Organizations design
- Permission guardrails and delegated administration
- Cross-account resource sharing
- ABAC at scale
- Workload identity for containers and Kubernetes
- IAM Roles Anywhere for supported external workloads
- Access Analyzer findings and automated remediation
- Production security reviews and design trade-offs