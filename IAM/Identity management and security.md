You’re right to check the syllabus before moving on. There’s an important distinction here: the previous Module 5 we completed was about IAM roles for AWS workloads, while the topic list you’ve provided is a separate, broader identity management and security module.

Based on our earlier tutorial, some of these topics have already been introduced in Modules 1 and 3, but they have not all been covered in sufficient depth. Rather than repeat the workload-identity material, I’ll attach a supplementary section to Module 5 that fills the gaps in your checklist.

## Module 5 coverage audit

| Required topic                              | Previous coverage                     | What we need to add                                                                         |
| ------------------------------------------- | ------------------------------------- | ------------------------------------------------------------------------------------------- |
| IAM Identity Center and federation          | Introduced, not covered in depth      | Organization setup, permission sets, account assignments, federation workflow               |
| SAML and OIDC                               | Mentioned conceptually                | Protocol differences, authentication flows, appropriate use cases                           |
| MFA                                         | Basic introduction                    | Phishing-resistant MFA, enforcement, recovery, root MFA                                     |
| Root-user protection                        | Basic introduction                    | Root access restrictions, recovery, monitoring, account-specific safeguards                 |
| Access-key lifecycle and credential hygiene | Partial                               | Inventory, rotation/replacement, deactivation, removal, and alternatives to long-lived keys |
| Least privilege and privilege escalation    | Least-privilege principles introduced | Dangerous permissions, policy combinations, privilege-escalation paths, auditing            |
| Delegated administration                    | Permissions boundaries introduced     | AWS Organizations delegation and safely constrained IAM administration                      |
| Developer/operator access lab               | Not completed as a full lab           | Build an access model and audit overly permissive permissions                               |

The supplementary material below covers these gaps. We’ll use Pulumi with Python where infrastructure-as-code helps, the AWS CLI for inspection and auditing, and the AWS Console for identity-provider and MFA workflows that require interactive setup.

# Module 5 attachment — Identity management and security

## 1. IAM Identity Center and federation

### IAM users versus workforce identities

For human access to AWS, the preferred modern pattern is to authenticate people through a workforce identity provider and grant them temporary AWS credentials rather than distributing permanent IAM access keys. AWS IAM Identity Center provides centralized workforce access to multiple AWS accounts.&#x20;


![alt text](img/Identity%20management%20and%20security.png)

Developer / Operator

Signs in with the organization's identity

Identity source + IAM Identity Center

Authentication, groups, MFA, and access assignments

Permission set

Defines what the person can do in an AWS account

AWS account role session

Temporary credentials for the assigned access

### The important concepts

- Identity source: Where workforce identities come from. Depending on your setup, you can use the Identity Center directory or connect an external identity provider or supported directory.
- Group: A collection of people, such as `Developers` or `Operators`.
- Permission set: A reusable definition of AWS permissions and session settings.
- Account assignment: Connects a user or group and a permission set to a particular AWS account.
- Federation: Establishes trusted access between an identity provider and AWS, allowing an authenticated person to access AWS without needing a separate permanent IAM user for every account.

For an AWS Organization, an organization instance of IAM Identity Center is the relevant model for centrally managing account access and permission sets.&#x20;




## 2. SAML versus OpenID Connect (OIDC)

These protocols solve related but different identity problems.

| Feature                  | SAML 2.0                                                | OpenID Connect (OIDC)                                                |
| ------------------------ | ------------------------------------------------------- | -------------------------------------------------------------------- |
| Foundation               | XML-based federation standard                           | Identity layer built on OAuth 2.0                                    |
| Main purpose             | Enterprise single sign-on                               | Modern web, mobile, and federated authentication                     |
| Common identity artifact | SAML assertion                                          | ID token, typically a JWT                                            |
| Common AWS use           | Workforce federation with enterprise identity providers | Web identity federation and supported identity-provider integrations |
| Typical example          | Employees sign in through a corporate SAML provider     | An application or workload uses a trusted OIDC identity              |

A key distinction: OAuth 2.0 is primarily an authorization framework; OIDC adds an authentication layer. An ID token describes authentication, while an access token is generally used to authorize access to a resource. Do not treat these tokens as interchangeable.

For AWS workload federation, a trusted OIDC identity can be exchanged for temporary AWS credentials when the corresponding IAM role trust policy permits it. For workforce single sign-on, IAM Identity Center can integrate with supported external identity providers.

### How federation trust works

A simplified federation flow is:

1. A person or workload authenticates with its identity provider.
2. The identity provider issues a signed assertion or token.
3. AWS validates the token against the configured trust relationship.
4. The trusted principal obtains an AWS role session, subject to the applicable trust and permission policies.

For OIDC-based role assumption, the role's trust policy should restrict the trusted provider and relevant claims, such as the expected audience and subject. Avoid broad trust that accepts tokens from unrelated applications or workloads.

For SAML-based federation, configure the appropriate identity provider and role trust relationship. For workforce access across many AWS accounts, prefer IAM Identity Center over manually maintaining a separate federated role for every person in every account.

## 3. Multi-factor authentication (MFA)

MFA adds an independent authentication factor beyond a password. AWS recommends phishing-resistant methods, such as passkeys and security keys, wherever possible.&#x20;



### Recommended policy for human access

- Require MFA through your workforce identity setup or IAM Identity Center configuration.
- Prefer phishing-resistant authenticators where supported.
- Protect recovery methods as carefully as the primary authentication method.
- Enroll and test recovery options before removing an old authenticator.
- Protect root-user sign-in with MFA separately from ordinary workforce access.
- For IAM users that remain necessary, enable MFA and constrain sensitive operations appropriately.

MFA requirements depend on the authentication path. Enforcing MFA in a workforce identity provider is not the same as automatically requiring MFA for every IAM API request. For role-based access, additional policy conditions may be appropriate, but test them against the actual session type and authentication flow before deployment.

Important: MFA is not a substitute for least privilege. An authenticated user with unnecessarily broad permissions can still cause significant damage.

## 4. Root-user protection

The AWS account root user is different from an IAM administrator. It has exceptional account-level privileges and should be reserved for tasks that require root credentials.

AWS's guidance includes protecting root credentials, enabling MFA, avoiding root access keys, restricting recovery mechanisms, and monitoring root activity.&#x20;


Use this checklist:

- Use a strong, unique root password and restrict access to it.
- Enable root MFA; consider multiple supported MFA devices for resilience.
- Do not create root access keys for ordinary programmatic work.
- Use IAM Identity Center or an appropriately privileged role for routine administration.
- Protect the email account and account-recovery mechanisms associated with root.
- Monitor and alert on root-user activity.
- Keep root access limited to authorized people and necessary tasks.

In AWS Organizations, account management and root-user controls have additional organization-level options. Apply them according to your account structure and required recovery procedures.

## 5. Access-key lifecycle and credential hygiene

Long-term access keys are credentials that can remain valid until they are deactivated or deleted. Temporary role credentials expire automatically and are preferable when available.

AWS recommends temporary credentials where possible and reviewing access-key last-used information before removing long-term credentials.&#x20;


### The lifecycle

1. Avoid creation when possible. Use IAM Identity Center for people and IAM roles or supported federation for workloads.
2. Inventory existing keys. Identify the owner, application, purpose, age, and last-used information.
3. Replace rather than abruptly break production. Move the consumer to a new credential or role, verify it works, then retire the old credential.
4. Deactivate before deletion when practical. This gives you a rollback window if a dependency was missed.
5. Delete obsolete keys. Remove credentials that are no longer needed, and investigate unexpected use.

Never commit credentials to Git, container images, source code, tickets, logs, or ordinary configuration files. Use a supported role or workload-identity mechanism, or a secret-management service when long-term credentials cannot be avoided.

### Audit IAM access keys with the AWS CLI

First, identify the account and caller you are using:

```
aws sts get-caller-identity
```

List IAM users and their access keys:

```
aws iam list-users

aws iam list-access-keys \
  --user-name SOME_IAM_USER
```

Inspect the last-used details of a particular key:

```
aws iam get-access-key-last-used \
  --access-key-id AKIAEXAMPLE
```

These commands are read-only audit operations. Replace the example values with real ones from your own account. The `AKIAEXAMPLE` value is illustrative, not a usable credential.

Do not rotate or delete keys solely because they are old or appear unused in a single snapshot. First establish whether they are used by applications, automation, or recovery procedures. Then migrate, deactivate, test, and remove them in a controlled sequence.

## 6. Least privilege and privilege-escalation risks

Least privilege means granting only the actions, resources, and conditions needed for a person's job. It is not simply about avoiding `Action: "*"`; seemingly narrow IAM permissions can still allow a user to gain more privileges indirectly.

### Dangerous permission patterns to recognize

| Permission or pattern                                                  | Why it deserves scrutiny                                                                 |
| ---------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| `iam:CreatePolicyVersion` and `iam:SetDefaultPolicyVersion`            | May allow a user to change an attached policy's effective permissions                    |
| `iam:AttachUserPolicy` / `iam:AttachRolePolicy`                        | May allow permissions to be added to identities the user controls                        |
| `iam:PutRolePolicy` / `iam:PutUserPolicy`                              | May allow new inline permissions to be installed                                         |
| `iam:CreateAccessKey`                                                  | May create a persistent credential for another IAM user                                  |
| `iam:PassRole` combined with powerful service permissions              | May let a user cause a service to operate with a more privileged role                    |
| Broad `sts:AssumeRole` permissions                                     | May allow access to roles beyond the user's intended responsibilities                    |
| `iam:CreatePolicy`, `iam:CreateRole`, or broad role-trust modification | May create or modify identities and trust relationships that enable privilege escalation |

These are review indicators, not proof of a vulnerability. Whether a permission enables escalation depends on its resource scope, conditions, the target role's permissions and trust policy, and what other actions the principal can perform.

For example, `iam:PassRole` does not itself grant permission to assume a role. But if a developer can pass a highly privileged role to a service and can also configure that service to execute their code or commands, the combination may provide a path to elevated access.

### Safer developer permissions

A developer may need to deploy an application without being allowed to administer all IAM identities.

A safer design is to:

- Scope deployment permissions to the application's resources.
- Restrict `iam:PassRole` to specific, approved execution-role ARNs.
- Use conditions such as `iam:PassedToService` when they correctly fit the deployment workflow.
- Restrict role creation and trust-policy changes.
- Apply a permissions boundary when developers are permitted to create roles.
- Separate production access and sensitive IAM administration from normal development work.
- Review effective permissions, including policies attached indirectly and organization-level guardrails.

Remember the distinctions from Module 3: identity-based policies grant permissions, while permissions boundaries, service control policies (SCPs), and resource control policies (RCPs) limit permissions in their respective scopes. A boundary or organization policy does not grant permissions on its own.&#x20;




## 7. Delegated administration

Delegation allows a team to administer a defined area without receiving unrestricted administrative control over the AWS organization.

There are two related but distinct patterns.

### A. Delegated administration of IAM Identity Center

An organization can register a member account as the delegated administrator for IAM Identity Center. This reduces the need to give workforce administrators access to the AWS Organizations management account. Some management-account operations and permissions remain restricted to the management account.&#x20;

[image](https://www.google.com/s2/favicons?domain=https://docs.aws.amazon.com\&sz=32)

AWS IAM Identity Center



### B. Delegated IAM administration within an account

You might let a platform team create or manage workload roles while preventing those roles from exceeding a defined permission ceiling. A permissions boundary can provide that ceiling.

A simplified design looks like this:

Security administrator

Defines guardrails, approved policies, and sensitive permissions that cannot be delegated.

**Platform / IAM administrator**

Manages approved permission sets, account assignments, and constrained role administration.

**Developer**

Deploys and operates application resources using narrowly scoped permissions.

**Auditor / security operations**

Reviews access findings, policy changes, credentials, and suspicious activity.

Avoid giving delegated administrators permission to modify their own guardrails, change the trust relationships that constrain them, or grant themselves broader access through another identity. Use separate administrative roles, controlled change procedures, and auditing to prevent self-escalation.

For IAM Identity Center specifically, use narrowly scoped policies to delegate permission-set administration and account assignments rather than granting unrestricted control of the service.&#x20;





## 8. Hands-on lab — Developer/operator access model and IAM audit

Goal: design workforce access, separate operational responsibilities, and identify overly permissive IAM policies without changing production permissions.

### Part A — Design the access model

For this lab, assume an AWS Organization with separate development and production accounts. Use IAM Identity Center for workforce access.

| Group               | Account access                        | Intended permissions                                              |
| ------------------- | ------------------------------------- | ----------------------------------------------------------------- |
| `Developers`        | Development                           | Deploy and troubleshoot application resources                     |
| `Operators`         | Development and production            | Operate approved services, inspect logs, respond to incidents     |
| `SecurityAuditors`  | Read-only access to approved accounts | Review IAM configuration, audit findings, and security posture    |
| `IAMAdministrators` | Restricted administrative access      | Manage identity configuration and approved permission assignments |

Use these rules:

1. Assign access to groups where practical instead of maintaining separate assignments for each person.
2. Start with narrowly scoped permission sets.
3. Separate development deployment from production administration.
4. Do not give developers unrestricted IAM administration.
5. Require MFA through the organization's supported authentication configuration.
6. Use separate, controlled administrative access for IAM Identity Center and organization-level changes.

In the AWS Console, open IAM Identity Center → Users and groups, create or select the groups, then configure Permission sets and AWS account assignments. The exact menus can vary with the current console interface. Permission sets are provisioned to the accounts where they are assigned.&#x20;





For an organization-wide setup, Pulumi can manage much of the surrounding IAM infrastructure, but identity-source configuration and initial workforce authentication may require interactive setup. Do not create permanent IAM users merely to simulate workforce SSO.

### Part B — Audit the current IAM configuration

Run these commands from an authorized administrative or audit session. They inspect IAM configuration; they do not change permissions.

1\. Confirm your AWS account and identity

```
aws sts get-caller-identity
```

2\. List IAM users and access keys

```
aws iam list-users
```

For each existing IAM user that warrants review:

```
aws iam list-access-keys --user-name SOME_IAM_USER
```

Then inspect a key's last-used information:

```
aws iam get-access-key-last-used \
  --access-key-id AKIAEXAMPLE
```

3\. Review policies attached to a user

```
aws iam list-attached-user-policies \
  --user-name SOME_IAM_USER
```

Also inspect inline policies:

```
aws iam list-user-policies \
  --user-name SOME_IAM_USER
```

For a role, use the corresponding `list-attached-role-policies` and `list-role-policies` commands. Remember that an identity's effective permissions can come from multiple policy types, not just one attached managed policy.

4\. Inspect a managed policy

Retrieve its default version:

```
aws iam get-policy \
  --policy-arn arn:aws:iam::123456789012:policy/ExamplePolicy
```

Use the returned `DefaultVersionId` to fetch the actual policy document:

```
aws iam get-policy-version \
  --policy-arn arn:aws:iam::123456789012:policy/ExamplePolicy \
  --version-id v1
```

Replace the example account ID, policy ARN, and version with the values returned by your own commands.

### Part C — Validate a suspicious policy

Create a local file named `policy.json` containing a deliberately broad example:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "*",
      "Resource": "*"
    }
  ]
}
```

Validate it with IAM Access Analyzer:

```
aws accessanalyzer validate-policy \
  --policy-document file://policy.json \
  --policy-type IDENTITY_POLICY
```

The result can include errors, security warnings, general warnings, and suggestions. The wildcard policy is intentionally over-permissive for this exercise; do not attach it to an identity.

Now replace it with a narrow example, such as permission to list one application's S3 bucket:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": "s3:ListBucket",
      "Resource": "arn:aws:s3:::example-app-artifacts"
    }
  ]
}
```

Run the validation command again. A successful validation does not prove that a policy is least-privileged or appropriate for your architecture; it is one part of the review process.&#x20;


### Part D — Review unused and externally exposed access

In the IAM Access Analyzer console, examine the available findings for:

- External access: resource policies that expose supported resources outside your intended zone of trust.
- Unused access: unused roles, credentials, and permissions where supported by the analyzer configuration.
- Policy validation: potential problems in new or existing policy documents.

Access Analyzer offers these capabilities, although the available analyzer types, regional setup, and pricing vary. Check the relevant configuration before enabling paid analysis features.&#x20;




### Part E — Remediate safely

For every finding, record the affected identity, permission, resource, business purpose, and proposed change.

Then:

1. Confirm whether the access is required.
2. Check the role trust policy, attached policies, inline policies, permissions boundary, and applicable organization policies.
3. Narrow actions, resources, and conditions where appropriate.
4. Test the new permissions in a non-production environment.
5. Deploy the change through your normal change process.
6. Review CloudTrail and application behavior for unexpected access failures.
7. Remove unused identities and credentials only after confirming they are no longer needed.

IAM Access Analyzer can also generate policy suggestions from CloudTrail activity. These are useful starting points for refining permissions, but they need review because observed activity may not cover every legitimate workflow.&#x20;



## Final status

The supplemental material closes the gaps in your requested syllabus: Identity Center and federation, SAML/OIDC, MFA, root protection, credential lifecycle, privilege-escalation risks, delegated administration, and a practical audit lab.

One distinction to preserve in the course: the original Module 5 remains the module on workload identity (EC2, ECS, EKS, and Lambda roles). This attachment adds the human-identity and security material without discarding that earlier work. We can now proceed to Module 6 without leaving the listed topics uncovered.