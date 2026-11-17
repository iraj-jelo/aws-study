### AWS Load Balancing — Module 5: TLS, Security, and Private Networking

AWS · Pulumi Python · Bash · ALB · NLB · ACM · AWS WAF

### Module overview

In this module, you'll learn how to secure traffic entering an AWS load balancer, protect backend services from direct access, and build private application architectures without sacrificing public HTTPS connectivity.

We'll build on the ALB, target groups, listeners, health checks, and VPC concepts from the previous modules. The main hands-on architecture will use a public-facing Application Load Balancer forwarding traffic to a private backend, with TLS termination, security groups, and AWS WAF.

### Learning objectives

By the end of this module, you will be able to:

* Configure HTTPS listeners using AWS Certificate Manager (ACM).

* Understand TLS policies, SNI, certificate selection, and end-to-end encryption.

* Apply least-privilege security groups and appropriate subnet and routing configurations.

* Integrate AWS WAF with an ALB to filter malicious HTTP requests.

* Understand mutual TLS (mTLS) and its supported AWS load-balancer configurations.

* Restrict backend access so applications cannot be reached directly from the internet.

* Validate certificates, TLS negotiation, HTTP behavior, and network restrictions using Bash.

* Provision and manage the infrastructure using Pulumi Python.

### 1\. TLS termination and HTTPS listeners

### 1.1 What happens when a client connects over HTTPS?

TLS provides encryption in transit, server authentication, and protection against undetected modification of traffic. With an ALB, TLS is commonly terminated at the load balancer.

Client

Browser or API client

HTTPS — encrypted TLS connection

Application Load Balancer

ACM certificate · TLS policy · HTTPS listener :443

TLS termination

HTTP or HTTPS to the target

Private backend

EC2, ECS tasks, or IP targets

The client establishes a TLS session with the ALB. The ALB presents its configured server certificate and decrypts the incoming application traffic. It then forwards the request to a healthy target according to the listener rules.

The connection between the ALB and target is a separate connection. It may use HTTP or HTTPS depending on the target group's protocol configuration.

Important distinction: HTTPS from the client to the ALB does not automatically mean HTTPS from the ALB to the backend.

| Connection               | Protocol | Protection                      |
| ------------------------ | -------- | ------------------------------- |
| Client → ALB             | HTTPS    | Encrypted in transit            |
| ALB → backend over HTTP  | HTTP     | No TLS encryption on this hop   |
| ALB → backend over HTTPS | HTTPS    | Separately encrypted in transit |

If your security requirements demand encryption across the entire network path, configure HTTPS to the targets and ensure the backend's certificate and identity-validation requirements are appropriate for the chosen AWS service.

### 1.2 ACM certificates

AWS Certificate Manager manages certificates used by supported AWS services.

There are two common approaches:

* ACM-issued public certificates: Suitable for publicly trusted domain names. Domain ownership must be validated, commonly using DNS validation.

* Imported certificates: Suitable when you already have a certificate issued by another certificate authority. You remain responsible for renewal and reimport where applicable.

For an internet-facing ALB, a public ACM certificate is a common choice. Its DNS name must match the hostname clients use, such as `app.example.com`.

An ACM public certificate must be requested or imported in the AWS Region where the ALB uses it. For an ALB in `eu-west-2`, request or import the certificate in `eu-west-2`.

ACM can automatically renew eligible ACM-issued certificates when renewal requirements are met. Imported certificates do not receive the same automatic renewal service; monitor their expiration and arrange renewal.

### 1.3 TLS policies

An HTTPS listener uses a security policy that controls the supported TLS protocol versions and cryptographic cipher suites.

For example, a policy might permit TLS 1.2 and TLS 1.3, while an older policy could allow legacy protocols or weaker ciphers.

When selecting a policy:

* Prefer a current AWS-recommended policy compatible with your clients and security requirements.

* Avoid obsolete TLS versions unless a documented compatibility requirement forces their use.

* Validate the policy against your application's client population.

* Revisit the policy as AWS introduces newer options and security requirements change.

You can inspect an HTTPS listener's configured policy using the AWS CLI:

```bash
aws elbv2 describe-listeners \
  --load-balancer-arn "$ALB_ARN" \
  --query 'Listeners[].{Port:Port,Protocol:Protocol,SslPolicy:SslPolicy,Certificates:Certificates}'
```

### 1.4 Server Name Indication (SNI)

SNI allows a TLS client to indicate the hostname it wants to reach during the TLS handshake. This enables a single ALB HTTPS listener to serve multiple domain names with different certificates.

For example:

* `api.example.com`

* `shop.example.com`

* `admin.example.com`

A listener can have a default certificate and additional certificates. The ALB selects an appropriate certificate based on the client's SNI hostname and the configured certificates.

SNI is useful for consolidating multiple HTTPS applications behind one ALB. However, SNI is not a substitute for HTTP routing rules: the certificate is selected during the TLS handshake, while host-based routing occurs after the TLS session is established.

### 2\. Security groups, network ACLs, and subnet placement

Security is not just a listener configuration. A correctly configured HTTPS listener can still expose your application if the backend instances accept connections directly from the internet.

### 2.1 Use separate security groups

A production architecture should usually have separate security groups for the load balancer and backend resources.

ALB security group

* Inbound TCP 443 from approved client CIDRs, often `0.0.0.0/0` for a public website.

* Optionally inbound TCP 80 if redirecting HTTP to HTTPS.

* Outbound traffic to backend targets on the application and health-check ports.

Backend security group

* Inbound application traffic only from the ALB security group.

* Health-check traffic allowed on the relevant target port.

* No public inbound rule for the application port.

AWS security groups are stateful: return traffic for an allowed connection is permitted automatically. Network ACLs are stateless, so inbound and outbound rules must account for both directions, including ephemeral ports where needed.

AWS recommends restricting backend instances to traffic from the load balancer's security group rather than permitting traffic from arbitrary sources. Elastic Load Balancing

### 2.2 Public and private subnets

For a conventional internet-facing ALB:

* Place the ALB in subnets in at least two Availability Zones.

* Ensure those public subnets have routes to an internet gateway.

* Place backend instances or ECS tasks in private subnets when they do not need direct public access.

* Allow backend security groups to receive traffic from the ALB security group.

* Configure outbound connectivity separately when private workloads need software downloads, external APIs, or other internet access.

A private backend does not automatically need a NAT gateway to serve requests from the ALB. NAT is primarily relevant when private workloads initiate connections to destinations outside their VPC through a NAT-based path.

### 2.3 Prevent direct-target bypass

Consider an ALB that protects `/api` with HTTPS and AWS WAF. If an EC2 instance has a public IP and its security group permits inbound application traffic from anywhere, an attacker may be able to bypass both the ALB's TLS listener policies and its WAF rules.

The preferred design is:

* Keep application targets private whenever practical.

* Restrict backend inbound rules to the ALB security group.

* Avoid exposing backend application ports through public IPs, public load balancers, or unintended alternate routes.

* Review IPv4 and IPv6 rules independently.

* Validate the effective access path rather than relying on subnet names alone.

### 3\. Network Load Balancer security considerations

ALB and NLB do not have identical security-group behavior.

| Capability          | ALB                             | NLB                                                                                                           |
| ------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| Security groups     | Supported                       | Supported when configured at creation; an NLB created without security groups cannot have them attached later |
| HTTP routing        | Layer 7                         | Not general-purpose HTTP request routing                                                                      |
| TLS listener        | HTTPS                           | TLS                                                                                                           |
| TLS pass-through    | Not its usual termination model | TCP listener can pass encrypted TLS traffic through to targets                                                |
| AWS WAF association | Supported                       | Not directly supported as a WAF-protected resource in the same way as ALB                                     |

For an NLB with security groups, plan the security-group design before creating the load balancer. Also account for client IP preservation and target security-group rules when deciding how to restrict inbound traffic. Elastic Load Balancing +1

A TCP listener on port 443 can preserve encrypted client TLS traffic to the backend, but the target application must then terminate TLS itself. This is different from an NLB TLS listener, which terminates the client TLS connection.

### 4\. AWS WAF integration with ALB

AWS WAF inspects HTTP(S) requests and applies rules to decide whether to allow, block, count, or otherwise handle matching traffic.

Common protections include:

* SQL injection patterns.

* Cross-site scripting (XSS) patterns.

* IP address and geographic restrictions.

* Rate-based rules to mitigate excessive request rates.

* Custom rules based on headers, paths, query parameters, and request characteristics.

* AWS Managed Rules, which provide maintained rule groups for common threats.

A web ACL can be associated with an ALB. When using managed rule groups, start with a monitoring approach such as `Count` where appropriate, examine logs and sampled requests, and then enable blocking after validating the impact on legitimate traffic. Not every false positive can be eliminated through default rules alone.

WAF is not a replacement for application authentication, authorization, input validation, or secure coding. Elastic Load Balancing

### WAF design considerations

* Scope rules to the application and its real traffic patterns.

* Exclude or customize rules carefully when legitimate requests are blocked.

* Use rate limits appropriate to the endpoint; login and public API endpoints may need different thresholds.

* Enable logging and protect log destinations.

* Remember that requests reaching a backend through a separate public endpoint can bypass the ALB-associated web ACL.

### 5\. Mutual TLS (mTLS) and client authentication

Ordinary TLS authenticates the server to the client. Mutual TLS adds client-certificate authentication.

This is useful for service-to-service APIs, partner integrations, and environments in which possession of an approved certificate is part of the client identity.

With ALB, the HTTPS listener supports two mTLS modes:

* Passthrough: The ALB forwards client-certificate information to the backend in HTTP headers. The application must perform the appropriate certificate validation and authorization.

* Verify: The ALB validates client certificates using a configured trust store and rejects certificates that fail the configured validation requirements.

The verify mode requires a trust store containing the appropriate certificate-authority bundle. Certificate revocation and expiration policies must be considered as part of the design. Elastic Load Balancing

mTLS is not the same as simply enabling HTTPS. If an application uses mTLS, plan client certificate issuance, distribution, rotation, revocation, and recovery when a client certificate expires.

### 6\. Pulumi project setup

We'll use Python for the infrastructure definitions and Bash for all shell commands.

The main lab provisions the ALB security boundary and an HTTPS listener. You'll supply an existing VPC, two public subnets, a target group, and an ACM certificate. This keeps the example focused on TLS and security rather than duplicating all the networking work from previous modules.

### 6.1 Create the project

```bash
mkdir aws-lb-security
cd aws-lb-security

pulumi new aws-python
```

Install the AWS provider package if your project does not already include it:

```bash
uv add pulumi pulumi-aws
```

Configure your AWS Region:

```bash
pulumi config set aws:region eu-west-2
```

Use an AWS CLI profile with appropriate permissions, or another supported short-lived credential mechanism. Avoid embedding AWS access keys in source code or Pulumi configuration.

For a public HTTPS certificate, you must also control the domain's DNS or otherwise be able to complete the certificate authority's domain validation. ACM-issued public certificates are not a way to obtain publicly trusted certificates for arbitrary domain names you do not control.

### 6.2 Configure the required inputs

This lab assumes that the VPC, subnets, target group, and ACM certificate already exist. Configure their identifiers:

```bash
pulumi config set vpcId vpc-0123456789abcdef0
pulumi config set publicSubnetA subnet-0123456789abcdef0
pulumi config set publicSubnetB subnet-0abcdef1234567890
pulumi config set targetGroupArn arn:aws:elasticloadbalancing:eu-west-2:123456789012:targetgroup/example/0123456789abcdef
pulumi config set certificateArn arn:aws:acm:eu-west-2:123456789012:certificate/01234567-89ab-cdef-0123-456789abcdef
```

Replace every example identifier with a real resource identifier from your AWS account.

The certificate must be in the same Region as the ALB. The target group must be compatible with the ALB and have its own correctly configured health checks. Elastic Load Balancing +1

### 7\. Lab 1 — Create a secure ALB with Pulumi

Create or replace `__main__.py` with the following code. It creates:

* An internet-facing ALB across two public subnets.

* A dedicated security group that permits HTTP and HTTPS from IPv4 clients.

* An HTTPS listener using your ACM certificate.

* An HTTP listener that redirects requests to HTTPS.

* Outputs for the ALB DNS name and ARN.

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
subnet_a = config.require("publicSubnetA")
subnet_b = config.require("publicSubnetB")
target_group_arn = config.require("targetGroupArn")
certificate_arn = config.require("certificateArn")

# Security boundary for the public-facing ALB.
alb_sg = aws.ec2.SecurityGroup(
    "alb-security-group",
    description="Allow public HTTP and HTTPS traffic to the ALB",
    vpc_id=vpc_id,
    ingress=[
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=80,
            to_port=80,
            cidr_blocks=["0.0.0.0/0"],
            description="HTTP for HTTPS redirection",
        ),
        aws.ec2.SecurityGroupIngressArgs(
            protocol="tcp",
            from_port=443,
            to_port=443,
            cidr_blocks=["0.0.0.0/0"],
            description="Public HTTPS",
        ),
    ],
    egress=[
        aws.ec2.SecurityGroupEgressArgs(
            protocol="-1",
            from_port=0,
            to_port=0,
            cidr_blocks=["0.0.0.0/0"],
            description="Outbound traffic; restrict further if required",
        ),
    ],
    tags={"Name": "alb-security-group"},
)

# Public ALB spanning two Availability Zones.
alb = aws.lb.LoadBalancer(
    "secure-alb",
    load_balancer_type="application",
    internal=False,
    security_groups=[alb_sg.id],
    subnets=[subnet_a, subnet_b],
    enable_deletion_protection=False,
    tags={"Name": "secure-alb"},
)

# HTTPS listener: TLS terminates at the ALB.
https_listener = aws.lb.Listener(
    "https-listener",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn=certificate_arn,
    ssl_policy="ELBSecurityPolicy-TLS13-1-2-2021-06",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="forward",
            target_group_arn=target_group_arn,
        )
    ],
)

# Redirect all HTTP requests to HTTPS.
http_listener = aws.lb.Listener(
    "http-redirect-listener",
    load_balancer_arn=alb.arn,
    port=80,
    protocol="HTTP",
    default_actions=[
        aws.lb.ListenerDefaultActionArgs(
            type="redirect",
            redirect=aws.lb.ListenerDefaultActionRedirectArgs(
                protocol="HTTPS",
                port="443",
                status_code="HTTP_301",
            ),
        )
    ],
)

pulumi.export("albDnsName", alb.dns_name)
pulumi.export("albArn", alb.arn)
pulumi.export("albSecurityGroupId", alb_sg.id)
pulumi.export("httpsListenerArn", https_listener.arn)
pulumi.export("httpListenerArn", http_listener.arn)
```

The example uses a named TLS policy as a starting point; verify the currently recommended policy for your Region and compatibility requirements before production deployment. Elastic Load Balancing +1

### 7.1 Deploy and inspect

Preview the planned infrastructure changes:

```bash
pulumi preview
```

Deploy:

```bash
pulumi up
```

Retrieve the ALB DNS name and security group:

```bash
ALB_DNS=$(pulumi stack output albDnsName)
ALB_SG=$(pulumi stack output albSecurityGroupId)

printf 'ALB DNS: %s\n' "$ALB_DNS"
printf 'ALB security group: %s\n' "$ALB_SG"
```

The ALB will only serve application requests successfully if the target group contains healthy targets and the backend's network access rules allow the ALB to reach them.

### 7.2 Restrict the backend security group

Suppose your backend uses TCP port 8080. The backend security group should permit that port from the ALB security group, rather than from the public internet.

If you own the backend security group, you can add this resource to the same Pulumi project:

```python

backend_sg_id = config.require("backendSecurityGroupId")

backend_ingress = aws.ec2.SecurityGroupRule(
    "backend-from-alb-only",
    type="ingress",
    security_group_id=backend_sg_id,
    protocol="tcp",
    from_port=8080,
    to_port=8080,
    source_security_group_id=alb_sg.id,
    description="Allow application traffic from the ALB only",
)
```

Set the additional configuration value:

```bash
pulumi config set backendSecurityGroupId sg-0123456789abcdef0
```

Adjust the port to match the actual target-group port. If your application and health checks use different ports, account for both. Also remove conflicting broad inbound rules that would still allow direct access.

Important: This rule modifies the backend security group. Review its existing rules and ownership before deploying, particularly if it is shared with other applications or managed by another infrastructure stack.

### 8\. Lab 2 — Verify TLS and HTTP redirection with Bash

These tests require a valid DNS name covered by the certificate. An ALB's generated DNS name generally does not match your custom ACM certificate, so use a domain such as `app.example.com` that you control and have pointed to the ALB.

Set the hostname:

```bash
export APP_HOST="app.example.com"
```

### 8.1 Check HTTP redirection

```bash
curl -sSI "http://${APP_HOST}/"
```

Expected behavior:

* An HTTP redirect response, usually `301`.

* A `Location` header pointing to the HTTPS URL.

If the request times out, inspect the ALB security group, subnet routes, listener status, and DNS configuration.

### 8.2 Check HTTPS

```bash
curl -sSI "https://${APP_HOST}/"
```

This checks TLS negotiation and then displays the HTTP response headers. An application may return a `200`, `301`, `401`, `403`, or another status depending on its behavior.

A successful TLS handshake does not guarantee that the backend application is healthy.

### 8.3 Inspect the presented certificate

```bash
openssl s_client \
  -connect "${APP_HOST}:443" \
  -servername "${APP_HOST}" \
  -verify_hostname "${APP_HOST}" \
  -verify_return_error \
  </dev/null
```

Inspect these parts of the output:

* Certificate subject and issuer.

* Certificate chain verification.

* Negotiated TLS protocol and cipher.

* Whether hostname verification succeeds.

You can inspect the certificate dates and subject separately:

```bash
openssl s_client \
  -connect "${APP_HOST}:443" \
  -servername "${APP_HOST}" \
  </dev/null 2>/dev/null |
openssl x509 -noout -subject -issuer -dates
```

For a more explicit TLS 1.2 compatibility test:

```bash
openssl s_client \
  -connect "${APP_HOST}:443" \
  -servername "${APP_HOST}" \
  -tls1_2 \
  -verify_hostname "${APP_HOST}" \
  -verify_return_error \
  </dev/null
```

A successful TLS 1.2 connection depends on the listener's configured security policy and the client's capabilities.

### 8.4 Inspect listeners and security groups

```bash
aws elbv2 describe-listeners \
  --load-balancer-arn "$(pulumi stack output albArn)" \
  --query 'Listeners[].{Port:Port,Protocol:Protocol,Policy:SslPolicy}'
```

```bash
aws ec2 describe-security-groups \
  --group-ids "$(pulumi stack output albSecurityGroupId)" \
  --query 'SecurityGroups[].{GroupId:GroupId,Ingress:IpPermissions,Egress:IpPermissionsEgress}'
```

Compare the effective rules with your intended security boundary. The ALB security group controls client-to-ALB access; the backend security group controls ALB-to-target access.

### 9\. Lab 3 — Protect the ALB with AWS WAF

In this lab, you'll create a regional WAF web ACL and associate it with the ALB. We'll use AWS Managed Rules for common web exploits and a rate-based rule as an initial layer of protection.

Add the following to `__main__.py` after the ALB resource:

```python

# Regional WAF Web ACL for the ALB.
web_acl = aws.wafv2.WebAcl(
    "application-web-acl",
    name="application-web-acl",
    scope="REGIONAL",
    default_action=aws.wafv2.WebAclDefaultActionArgs(
        allow={}
    ),
    visibility_config=aws.wafv2.WebAclVisibilityConfigArgs(
        cloudwatch_metrics_enabled=True,
        metric_name="applicationWebAcl",
        sampled_requests_enabled=True,
    ),
    rules=[
        aws.wafv2.WebAclRuleArgs(
            name="AWSManagedCommonRules",
            priority=10,
            override_action=aws.wafv2.WebAclRuleOverrideActionArgs(
                none={}
            ),
            statement=aws.wafv2.WebAclRuleStatementArgs(
                managed_rule_group_statement=(
                    aws.wafv2.WebAclRuleStatementManagedRuleGroupStatementArgs(
                        name="AWSManagedRulesCommonRuleSet",
                        vendor_name="AWS",
                    )
                )
            ),
            visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                cloudwatch_metrics_enabled=True,
                metric_name="commonRules",
                sampled_requests_enabled=True,
            ),
        ),
        aws.wafv2.WebAclRuleArgs(
            name="RateLimit",
            priority=20,
            action=aws.wafv2.WebAclRuleActionArgs(
                block={}
            ),
            statement=aws.wafv2.WebAclRuleStatementArgs(
                rate_based_statement=(
                    aws.wafv2.WebAclRuleStatementRateBasedStatementArgs(
                        limit=2000,
                        aggregate_key_type="IP",
                    )
                )
            ),
            visibility_config=aws.wafv2.WebAclRuleVisibilityConfigArgs(
                cloudwatch_metrics_enabled=True,
                metric_name="rateLimit",
                sampled_requests_enabled=True,
            ),
        ),
    ],
)

# Associate the regional Web ACL with the ALB.
waf_association = aws.wafv2.WebAclAssociation(
    "application-waf-association",
    resource_arn=alb.arn,
    web_acl_arn=web_acl.arn,
)

pulumi.export("webAclArn", web_acl.arn)
```

The rate-based rule uses a threshold of 2,000 requests per aggregation window per source IP as an illustrative starting point, not a universal safe production limit. Tune it to actual traffic patterns. Managed rules can also block legitimate requests, so review sampled requests and WAF metrics before enforcing them in production. Pulumi Registry +1

Deploy the updated stack:

```bash
pulumi preview
pulumi up
```

Inspect the web ACL:

```bash
aws wafv2 get-web-acl \
  --name application-web-acl \
  --scope REGIONAL \
  --id "$(pulumi stack output webAclArn | awk -F/ '{print $NF}')" \
  --region eu-west-2
```

If you encounter an identifier mismatch, inspect the full web ACL ARN and use its actual name, ID, and Region. The web ACL ARN is not interchangeable with its ID.

### Test WAF behavior

Send ordinary requests:

```bash
curl -i "https://${APP_HOST}/"
```

Send a request containing a common SQL injection test pattern:

```bash
curl -i \
  --get \
  --data-urlencode "q=' OR 1=1 --" \
  "https://${APP_HOST}/search"
```

The second request may be blocked by the managed rules, but the outcome depends on the request, the configured rules, and any application-specific exclusions. A successful response does not by itself prove that WAF is misconfigured.

You can inspect sampled requests and metrics through the AWS WAF console or CloudWatch. Do not repeatedly generate high volumes of traffic against a production endpoint to test rate limiting.

### 10\. Lab 4 — Private backends and security validation

The goal is to ensure that the ALB is the intended application entry point.

### Architecture

Internet clients

HTTPS

Public ALB

TLS · WAF · listener rules

Private application targets

Backend SG allows application traffic from ALB SG only

Verify the design with these checks:

* The ALB has an HTTPS listener and a valid certificate.

* The public ALB security group permits only the intended listener ports.

* The backend security group permits application traffic from the ALB security group.

* Backend targets do not have unintended public access.

* Health checks reach the correct target port.

* WAF metrics and logs show the expected request behavior.

* CloudTrail records infrastructure changes for audit purposes.

To inspect the registered targets:

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$(pulumi config get targetGroupArn)"
```

To inspect the ALB's scheme, subnet placement, and attached security groups:

```bash
aws elbv2 describe-load-balancers \
  --load-balancer-arns "$(pulumi stack output albArn)" \
  --query 'LoadBalancers[].{Scheme:Scheme,State:State.Code,Subnets:AvailabilityZones[].SubnetId,SecurityGroups:SecurityGroups}'
```

If you have access to a machine outside the VPC, test the public application URL. Separately, test the private backend from an authorized machine inside the VPC. A timeout from an external machine is useful evidence, but verify the security groups, routes, and target addressing to determine why access is denied.

### 11\. Encryption, logging, and security auditing

For production environments, treat the following as part of the security baseline.

| Area                   | Recommended approach                                                             |
| ---------------------- | -------------------------------------------------------------------------------- |
| Client TLS             | HTTPS listener, valid certificate, modern TLS policy                             |
| Backend encryption     | Use HTTPS to targets when end-to-end encryption is required                      |
| Network access         | Separate ALB and backend security groups                                         |
| Web protection         | WAF managed rules, carefully tuned rate limits                                   |
| Certificate lifecycle  | ACM renewal monitoring and expiration alerts for imported certificates           |
| Traffic auditing       | ALB access logs and WAF logging                                                  |
| Configuration auditing | CloudTrail and, where useful, AWS Config                                         |
| Infrastructure changes | Pulumi stack configuration, reviewed previews, controlled deployment permissions |

One important nuance: an ALB encrypting traffic to an HTTPS target does not mean the ALB performs conventional certificate-based authentication of that backend. AWS documents backend encryption support but not backend certificate authentication for ALB. If your design requires independently authenticated backend TLS identities, account for that limitation in the architecture. Amazon Web Services

### 12\. Troubleshooting reference

| Symptom                                     | Likely areas to inspect                                                 |
| ------------------------------------------- | ----------------------------------------------------------------------- |
| Certificate mismatch                        | DNS hostname, certificate SANs, SNI, listener certificate configuration |
| HTTPS handshake failure                     | TLS policy, client compatibility, certificate chain                     |
| HTTP request does not redirect              | Port 80 listener and redirect action                                    |
| ALB returns 503                             | No healthy targets, target registration, health-check configuration     |
| ALB returns 502                             | Backend connection errors, protocol mismatch, application response      |
| ALB returns 403                             | WAF rules, application authorization, listener actions                  |
| Backend connection times out                | Security groups, NACLs, routes, target port                             |
| Direct backend access succeeds unexpectedly | Public IPs, permissive security groups, alternate ingress paths         |
| ACM certificate renewal issue               | Domain validation, DNS records, certificate eligibility                 |

### 13\. Cleanup

Once you've finished testing, remove the lab infrastructure if you no longer need it:

```bash
pulumi destroy
```

Review the preview and confirm that the resources belong to this lab before approving deletion. The existing VPC, backend resources, target group, and ACM certificate were supplied as inputs and are not automatically owned by this stack. Remove them separately only if you created them for the lab and no longer need them.

Module outcome: You now have a reusable pattern for a public HTTPS entry point, restricted private backends, WAF protection, and Bash-based security validation. These techniques carry forward into the ECS/EKS and production load-balancing modules.

### Official references

* [AWS — Create an HTTPS listener](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/create-https-listener.html?utm_source=chatgpt.com)

* [AWS — Infrastructure security in Elastic Load Balancing](https://docs.aws.amazon.com/elasticloadbalancing/latest/userguide/infrastructure-security.html?utm_source=chatgpt.com)

* [AWS — Configure mutual TLS for ALB](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/configuring-mtls-with-elb.html?utm_source=chatgpt.com)

* [Pulumi — WAF Web ACL association](https://www.pulumi.com/registry/packages/aws/api-docs/wafv2/webaclassociation/?utm_source=chatgpt.com)

* [Pulumi — Load balancer listeners](https://www.pulumi.com/registry/packages/aws/api-docs/alb/listener/?utm_source=chatgpt.com)
