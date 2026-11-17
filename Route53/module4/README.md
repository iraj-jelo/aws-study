### Module 4 — Route 53 Health Checks and DNS Failover

### 1\. Introduction to Route 53 Health Checks

Amazon Route 53 health checks allow DNS routing decisions to depend on the health and availability of application endpoints, AWS resources, or other monitored conditions.

They are particularly important when building highly available applications across multiple Availability Zones or AWS Regions.

### 1.1 What Are Route 53 Health Checks?

A Route 53 health check monitors the availability and responsiveness of a resource.

Depending on its configuration, Route 53 can:

* Monitor an endpoint using HTTP, HTTPS, or TCP.

* Verify that an HTTP response contains a specific string.

* Evaluate the health of multiple endpoints.

* Use CloudWatch alarms to determine resource health.

* Associate health information with DNS records.

* Route users away from unhealthy endpoints when using supported routing configurations.

For example, consider an application deployed in two AWS Regions:

![Creating Disaster Recovery Mechanisms Using Amazon Route 53 | Networking & Content Delivery](https://images.openai.com/static-rsc-4/K9gy_lfmzCuNfiRX865gs83lar0dXDnLrxaJDFU2LW3mg433G1vQKCFVJqCt2r23KfBPPR6n683qCK_uwQjfzz21XIEUIwH7hr7yj2-ArdkjF74-b4gANX2AqIQfcUDrqzIGXOiyI20CayPK60PFHal7wcQQMbtodUZ4wfgqaz-iUDQP822A55uUw3G55RPx?purpose=fullsize)

* Region A hosts the primary application.

* Region B hosts the secondary application.

* Route 53 monitors the primary application's health.

* If the primary application becomes unhealthy, Route 53 can return the secondary application's DNS record instead.

This architecture provides DNS-based failover without requiring clients to know the underlying infrastructure details.

### 1.2 Health Checks Versus Application Monitoring

Route 53 health checks are not a replacement for application monitoring systems.

| Capability                   | Route 53                            | CloudWatch                                   |
| ---------------------------- | ----------------------------------- | -------------------------------------------- |
| Endpoint availability checks | Yes                                 | Through configured monitoring                |
| HTTP/HTTPS checks            | Yes                                 | Through synthetic monitoring                 |
| TCP connectivity checks      | Yes                                 | Through custom monitoring                    |
| Application metrics          | No                                  | Yes                                          |
| CPU and memory monitoring    | No                                  | Yes, with appropriate metric collection      |
| DNS failover integration     | Yes                                 | Indirectly through alarm-based health checks |
| Infrastructure alarms        | Limited to health-check integration | Yes                                          |

The important distinction is that Route 53 health checks determine whether a resource should be considered healthy for DNS routing, while CloudWatch provides broader infrastructure and application observability.

### 1.3 Types of Route 53 Health Checks

Route 53 supports three important health-check categories:

* Endpoint health checks: Monitor a specific endpoint using HTTP, HTTPS, or TCP.

* Calculated health checks: Combine the health status of other health checks.

* CloudWatch alarm health checks: Derive health status from a CloudWatch alarm.

These categories can be combined to build sophisticated health-monitoring and DNS failover architectures.

### 2\. Endpoint Health Checks

Endpoint health checks allow Route 53 to monitor the availability of publicly accessible endpoints.

Route 53 health checkers distributed across multiple AWS locations periodically send requests to the configured endpoint.

### 2.1 Supported Protocols

Route 53 supports the following endpoint monitoring protocols:

| Protocol | Description            | Typical use case                      |
| -------- | ---------------------- | ------------------------------------- |
| HTTP     | Sends HTTP requests    | Public web applications               |
| HTTPS    | Sends HTTPS requests   | TLS-enabled applications              |
| TCP      | Tests TCP connectivity | Database proxies and network services |

For HTTP and HTTPS checks, Route 53 evaluates the response from the endpoint. A successful connection alone does not necessarily mean the application is healthy.

For TCP checks, the health checker verifies that a TCP connection can be established.

### 2.2 Configuring HTTP Health Checks

An HTTP health check periodically sends an HTTP request to an endpoint.

For example:

```text
http://api.example.com/health
```

A typical application health endpoint might return:

```http
HTTP/1.1 200 OK
Content-Type: application/json

{
    "status": "healthy"
}
```

The health check can be configured with:

* The endpoint's IP address or fully qualified domain name.

* The port number.

* The request path.

* The health-check interval.

* The failure threshold.

* Optional response-string matching.

A health endpoint should be lightweight and designed specifically for availability monitoring.

Important: Route 53 endpoint health checks are performed by external health checkers. The monitored endpoint must be reachable from those checkers. A private application endpoint cannot simply be monitored through a normal public endpoint health check.

### 2.3 Configuring HTTPS Health Checks

HTTPS health checks operate similarly to HTTP checks but establish TLS connections.

For example:

```text
https://api.example.com/health
```

The endpoint should have a properly configured TLS certificate and support the expected hostname and connection behavior.

HTTPS monitoring is useful when the application depends on TLS termination, certificate configuration, or HTTPS availability.

### 2.4 Configuring TCP Health Checks

TCP health checks test whether a connection can be established to a particular port.

For example:

```text
api.example.com:443
```

Or:

```text
database-proxy.example.com:5432
```

A successful TCP check confirms that the endpoint accepts connections, but it does not prove that the application can process requests correctly.

For example, a database server might accept TCP connections while being unable to execute queries.

### 2.5 HTTP Response String Matching

HTTP and HTTPS health checks can optionally verify that a specified string appears in the response body.

Consider this response:

```json
{
    "status": "healthy",
    "database": "connected"
}
```

A health check can search for a string such as:

```text
"status": "healthy"
```

This provides an additional validation layer beyond HTTP response status.

However, string matching has limitations:

* It checks for a specific string rather than parsing JSON.

* It does not validate every application dependency automatically.

* It does not replace comprehensive application-level monitoring.

A well-designed health endpoint should report a meaningful application health state.

### 2.6 Health-Check Intervals and Failure Thresholds

Route 53 supports two health-check intervals:

| Interval   | Description                    |
| ---------- | ------------------------------ |
| 10 seconds | Fast health-check interval     |
| 30 seconds | Standard health-check interval |

The fast interval is available through the relevant configuration option and has additional pricing implications.

The failure threshold determines how many consecutive failed checks are required before Route 53 considers an endpoint unhealthy.

For example:

```text
Interval: 30 seconds
Failure threshold: 3
```

Conceptually, repeated failures will eventually cause the health check to become unhealthy.

The actual detection time depends on the health-check interval, distributed health checkers, and evaluation behavior. It should not be treated as an exact guaranteed failover timer.

### 2.7 Distributed Health Checkers

Route 53 uses health checkers distributed across multiple AWS locations.

This provides several advantages:

* Monitoring from different network locations.

* Reduced dependence on a single monitoring location.

* Better detection of regional or network-specific problems.

Health-check status is determined by evaluating the observations from the distributed checkers.

The `RequestInterval` and `FailureThreshold` settings influence the monitoring behavior, while the health-checker's global evaluation determines the final reported status.

### 2.8 Health-Check Regions and Configuration

You can specify which AWS Regions Route 53 health checkers should use.

The available regions include:

* US East (N. Virginia)

* US West (N. California)

* US West (Oregon)

* Europe (Ireland)

* Asia Pacific (Singapore)

* Asia Pacific (Sydney)

* Asia Pacific (Tokyo)

* South America (São Paulo)

By default, Route 53 uses its configured set of health-checking regions. You can customize the regions for endpoint health checks.

This is useful when monitoring applications whose availability differs depending on the geographic location of users.

For example, an application might be accessible from North America but inaccessible from Asia due to network routing problems.

Important distinction: Health-check regions determine where monitoring requests originate. They do not determine where DNS queries are answered.

Reference: [Route 53 health-check configuration](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/health-checks-creating-values.html?utm_source=chatgpt.com).

### 3\. Calculated Health Checks

A calculated health check combines the results of multiple child health checks into a single health status.

Instead of monitoring one endpoint, you can evaluate the availability of an entire application consisting of multiple components.

### 3.1 Why Calculated Health Checks Matter

Consider an application with three backend services:

* API service

* Authentication service

* Payment service

You might want the application to be considered healthy when at least two of these three services are healthy.

A calculated health check makes this possible.

![Route 53 Health Check and Failover - Common Pitfalls and Designs | hidekazu-konishi.com](https://images.openai.com/static-rsc-4/uqaDZ1OOlVS49GH2y_fo9QWEvK-bMnt_X5teyaFfY1wlJKsElRjuRlzrwaXwZPPYPRzGeToAzpNa_ZIw5bxmD7XHXAfl6nmWCefv_fuhTo2wuLtcx9QF5voKm6aZfYhG5tfkHT0lXrZCU4Zbh4INCVzeKs6tx3GFy9xlcNGB7p2EgHXyOzwhxKSZJ3Yz1UU2?purpose=fullsize)

The parent health check evaluates the status of its child health checks.

### 3.2 Health Threshold

A calculated health check uses a health threshold to determine how many child health checks must be healthy.

For example:

```text
Child health checks: 3
Health threshold: 2

API:          Healthy
Authentication: Healthy
Payment:      Unhealthy

Parent:       Healthy
```

If another service becomes unhealthy:

```text
API:          Healthy
Authentication: Unhealthy
Payment:      Unhealthy

Parent:       Unhealthy
```

The parent health check is healthy when the number of healthy child checks meets or exceeds the configured threshold.

### 3.3 Combining Health Checks

Calculated health checks support more advanced configurations:

* AND-like behavior: All required components must be healthy.

* OR-like behavior: At least one component must be healthy.

* Majority-based behavior: A specified number of components must be healthy.

* Inverted health checks: Reverse the health status of a child or parent check.

You can also create nested calculated health checks.

For example:

```text
                 Application Health
                         |
                 Calculated Check
                    /        \
                   /          \
             API Health    Database Health
                 |              |
             Calculated     Endpoint Check
                /   \
               /     \
          API-A     API-B
```

This architecture makes it possible to represent complex application dependencies.

Important limits:

* A calculated health check can reference up to 255 child health checks.

* The configured health threshold determines the required number of healthy children.

* Child health checks must be created before the parent health check.

Reference: [How Route 53 determines health-check status](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html?utm_source=chatgpt.com).

### 3.4 Pulumi: Creating Calculated Health Checks

Pulumi's `aws.route53.HealthCheck` resource supports calculated health checks.

First, create two endpoint health checks:

```python
import pulumi
import pulumi_aws as aws

api_a = aws.route53.HealthCheck(
    "api-a-health",
    fqdn="api-a.example.com",
    port=443,
    type="HTTPS",
    resource_path="/health",
    failure_threshold=3,
    request_interval=30,
)

api_b = aws.route53.HealthCheck(
    "api-b-health",
    fqdn="api-b.example.com",
    port=443,
    type="HTTPS",
    resource_path="/health",
    failure_threshold=3,
    request_interval=30,
)
```

Now create a calculated health check:

```python
application_health = aws.route53.HealthCheck(
    "application-health",
    type="CALCULATED",
    child_healthchecks=[
        api_a.id,
        api_b.id,
    ],
    child_health_threshold=1,
)

pulumi.export("application_health_id", application_health.id)
```

In this configuration:

* Both API endpoints are monitored independently.

* The parent health check evaluates their status.

* At least one API endpoint must remain healthy.

This is useful for applications with redundant backend instances.

### 4\. CloudWatch Alarm-Based Health Checks

Endpoint monitoring is not sufficient for every application.

Some failures cannot be detected by checking whether an HTTP endpoint responds.

For example:

* An application might return HTTP 200 while database queries are failing.

* A server might respond while CPU utilization is critically high.

* An application might be experiencing excessive request latency.

* A critical background processing system might have stopped working.

CloudWatch alarm-based health checks allow Route 53 to use CloudWatch metric data to determine resource health.

### 4.1 Architecture

![Cascading Failures | AWS Architecture Blog](https://images.openai.com/static-rsc-4/b0KzjgEaaFqmT42LhkgoyAPQm0Q7mTpHHWnZHQH1sIe17XQt7K5_vDN16Zu1vod4SslQuxq6uR2rfbgJcGZJtrjQUKJFoWTFKioLHenaq3dg3Iaa1Pkwppfh1pnL6mgZ9uroerwSk9FGVeUWvNPM-mBJwYG4OdA8KAdjII8x_moAuLIwi0CtepNMRczRcQl_?purpose=fullsize)

The architecture works as follows:

* CloudWatch collects application or infrastructure metrics.

* A CloudWatch alarm evaluates those metrics.

* Route 53 monitors the CloudWatch alarm's metric data stream.

* Route 53 determines the health status.

* DNS failover can use the resulting health status.

For example, suppose an application has a CloudWatch alarm:

```text
Metric: ApplicationErrorRate
Threshold: Greater than 10%
Evaluation periods: 3
Period: 60 seconds
```

If the error rate remains above the configured threshold, CloudWatch enters the ALARM state.

Route 53 can use that alarm to consider the associated endpoint unhealthy.

### 4.2 CloudWatch Alarm States

CloudWatch alarms have three primary states:

| State             | Meaning                             | Route 53 interpretation |
| ----------------- | ----------------------------------- | ----------------------- |
| OK                | Metric is within the expected range | Healthy                 |
| ALARM             | Alarm condition is met              | Unhealthy               |
| INSUFFICIENT_DATA | Not enough metric data              | Configurable            |

The insufficient-data behavior can be configured using:

* `Healthy`

* `Unhealthy`

* `LastKnownStatus`

This decision matters because missing monitoring data does not necessarily mean the application is healthy.

### 4.3 Important CloudWatch Integration Detail

Route 53 monitors the CloudWatch metric data stream associated with the alarm rather than simply querying the alarm's current state.

Consequently, calling the CloudWatch `SetAlarmState` API does not force the associated Route 53 health check to change its status.

Also, Route 53 health checks based on CloudWatch alarms require the alarm to be in the same AWS account.

Cross-account CloudWatch alarms are not supported for this integration.

Reference: [CloudWatch alarm health-check behavior](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html?utm_source=chatgpt.com).

### 4.4 Pulumi: Creating a CloudWatch Alarm

Consider an application that publishes an `ApplicationErrorRate` metric.

We can create a CloudWatch alarm:

```python
import pulumi_aws as aws

error_alarm = aws.cloudwatch.MetricAlarm(
    "application-error-alarm",
    comparison_operator="GreaterThanThreshold",
    evaluation_periods=3,
    metric_name="ApplicationErrorRate",
    namespace="MyApplication",
    period=60,
    statistic="Average",
    threshold=10,
    alarm_description="Application error rate is too high",
    treat_missing_data="breaching",
)
```

The metric must actually be published to CloudWatch for this alarm to evaluate meaningful application health.

Now create a Route 53 health check:

```python
application_health = aws.route53.HealthCheck(
    "application-cloudwatch-health",
    type="CLOUDWATCH_METRIC",
    cloudwatch_alarm_name=error_alarm.alarm_name,
    cloudwatch_alarm_region="ap-southeast-1",
    insufficient_data_health_status="Unhealthy",
)
```

This configuration makes the Route 53 health check unhealthy when the alarm indicates an unhealthy application state or when the configured insufficient-data policy applies.

Production consideration: Choose the missing-data behavior carefully. Treating missing data as unhealthy can trigger failover during telemetry interruptions, while treating it as healthy can conceal monitoring failures.

### 5\. Health Checks Associated with DNS Records

Creating a health check does not automatically change DNS responses.

To enable DNS failover, you must associate the health check with the appropriate DNS records.

### 5.1 Health-Checked DNS Records

Consider two application endpoints:

```text
Primary:
primary.example.com

Secondary:
secondary.example.com
```

Each endpoint has its own health check.

The DNS records can reference those health checks.

Conceptually:

```text
example.com
    |
    +---- Primary record
    |        |
    |        +---- Health Check A
    |
    +---- Secondary record
             |
             +---- Health Check B
```

When Route 53 evaluates the DNS request, it considers the health status of the records.

### 5.2 Failover Routing Policy

Route 53 supports a dedicated failover routing policy.

It has two record roles:

* `PRIMARY`: The preferred resource.

* `SECONDARY`: The backup resource.

The primary record is returned while it is considered healthy.

If the primary becomes unhealthy, Route 53 can return the secondary record, provided the secondary is healthy.

### 5.3 Pulumi: Creating a Primary/Secondary Failover Configuration

Let's assume that two ALBs already exist:

```python
primary_alb_dns = "primary-alb-123.ap-southeast-1.elb.amazonaws.com"
secondary_alb_dns = "secondary-alb-456.ap-southeast-2.elb.amazonaws.com"
```

First, create the health checks:

```python
primary_health = aws.route53.HealthCheck(
    "primary-health",
    fqdn=primary_alb_dns,
    port=443,
    type="HTTPS",
    resource_path="/health",
    failure_threshold=3,
    request_interval=30,
)

secondary_health = aws.route53.HealthCheck(
    "secondary-health",
    fqdn=secondary_alb_dns,
    port=443,
    type="HTTPS",
    resource_path="/health",
    failure_threshold=3,
    request_interval=30,
)
```

Next, create the primary DNS record:

```python
primary_record = aws.route53.Record(
    "primary-record",
    zone_id=hosted_zone.id,
    name="app.example.com",
    type="A",
    set_identifier="primary",
    failover_routing_policies=[
        aws.route53.RecordFailoverRoutingPolicyArgs(
            type="PRIMARY",
        )
    ],
    aliases=[
        aws.route53.RecordAliasArgs(
            name=primary_alb_dns,
            zone_id=primary_alb_zone_id,
            evaluate_target_health=True,
        )
    ],
    health_check_id=primary_health.id,
)
```

Then create the secondary record:

```python
secondary_record = aws.route53.Record(
    "secondary-record",
    zone_id=hosted_zone.id,
    name="app.example.com",
    type="A",
    set_identifier="secondary",
    failover_routing_policies=[
        aws.route53.RecordFailoverRoutingPolicyArgs(
            type="SECONDARY",
        )
    ],
    aliases=[
        aws.route53.RecordAliasArgs(
            name=secondary_alb_dns,
            zone_id=secondary_alb_zone_id,
            evaluate_target_health=True,
        )
    ],
    health_check_id=secondary_health.id,
)
```

The example assumes that the hosted zone and ALB hosted-zone IDs have already been obtained.

Notice two important properties:

* `health_check_id` associates the DNS record with its health check.

* `evaluate_target_health` enables Route 53 to evaluate the health of the alias target.

For ALB aliases, target health evaluation is particularly useful because it allows Route 53 to consider the load balancer's target health.

Important: The example uses ALB DNS names as health-check endpoints. In production, ensure that the health-check request reaches the intended application endpoint and that the ALB listener and health endpoint are correctly configured.

Pulumi reference: [Route 53 HealthCheck resource](https://www.pulumi.com/registry/packages/aws/api-docs/route53/healthcheck/?utm_source=chatgpt.com).

### 6\. Active-Active and Active-Passive Architectures

Route 53 health checks can support two common high-availability architectures.

### 6.1 Active-Passive Architecture

In an active-passive architecture, one environment handles normal traffic while another remains available as a backup.

![Designing a multi-region disaster recovery architecture in AWS | Krishnendu Banerjee posted on the topic | LinkedIn](https://images.openai.com/static-rsc-4/uN60WWBlvOryRlg-3fiRr4RxwP6elfskyr1E5H-myqYEeSuz1_LLaN-uxWOTeBfWLerbagPX5f9ACtRLVgp-kVcYWBUJjTotDh74V-AnQXmo8wHzgPV_jjk8qDSWlr0ZVghmCG16QsdI_h1I90OJiYUq05oAoyNTPKLZynhL-A-dz5IMsYETH3Au1J6wR5z5?purpose=fullsize)

Example:

```text
                Route 53
                   |
             Primary Region
                   |
             Application A
                   |
             Health Check
                   |
              If unhealthy
                   |
             Secondary Region
                   |
             Application B
```

Characteristics:

* Primary handles normal traffic.

* Secondary remains available for disaster recovery.

* Route 53 detects primary failures.

* DNS responses change to direct traffic to the secondary.

* Secondary infrastructure must be capable of handling production traffic.

Common use cases:

* Disaster recovery.

* Regional application failures.

* Critical business applications.

* Backup application environments.

### 6.2 Active-Active Architecture

In an active-active architecture, multiple application environments handle production traffic simultaneously.

![](https://images.openai.com/static-rsc-4/twciTC-VSF0DbKHaLPS-m3HHSGBE4q0Qy_GNgQ-2vBd_l6latiY1oW5ynKaKz-WFKXNdOsj02WkscS6wXFETcVfRp0PQ4zXu8lERuKA0PMwENxGP0ceywY7b7cUQXmUxEM6r6Rex3ViCCDx5sKcXpuGmX47FcDOU0qkSIILDCfhWxaJuCn3k1rbqkUpbx0ak?purpose=fullsize)

For example:

```text
                 Route 53
                    |
           +--------+--------+
           |                 |
       Region A           Region B
           |                 |
       Application A     Application B
           |                 |
       Health Check      Health Check
```

Both regions receive traffic while healthy.

If one region becomes unhealthy, Route 53 can stop returning its associated record and direct new DNS resolutions toward the remaining healthy region.

Common use cases:

* Global SaaS applications.

* Multi-region APIs.

* Distributed web applications.

* Applications requiring regional redundancy.

### 6.3 Active-Active Versus Active-Passive

| Characteristic        | Active-Active           | Active-Passive        |
| --------------------- | ----------------------- | --------------------- |
| Normal traffic        | Multiple regions        | Primary region        |
| Backup capacity       | Already serving traffic | Reserved for failover |
| Resource utilization  | Higher                  | Potentially lower     |
| Failover              | Remove unhealthy region | Switch to secondary   |
| Complexity            | Higher                  | Moderate              |
| Common routing policy | Weighted or latency     | Failover              |

### 6.4 Choosing an Architecture

The decision depends on application requirements.

For example:

* A globally distributed API might benefit from active-active deployment with latency-based routing.

* A financial application might use active-passive deployment to maintain a controlled disaster recovery environment.

* A SaaS application might use weighted routing for gradual regional traffic migration.

Remember that DNS failover does not replicate application data. Database replication, session management, and application consistency must be handled separately.

### 7\. DNS Failover Limitations and Recovery Considerations

DNS failover is useful, but it does not provide instantaneous application failover.

Understanding its limitations is essential when designing production architectures.

### 7.1 DNS Caching and TTL

DNS resolvers cache DNS responses according to their TTL values.

Consider:

```text
app.example.com

TTL: 60 seconds

Primary:
192.0.2.10

Secondary:
192.0.2.20
```

A client resolves the DNS name and receives:

```text
192.0.2.10
```

That answer may remain cached until its TTL expires.

Even if Route 53 detects that the primary endpoint is unhealthy, clients with cached DNS responses may continue attempting to connect to the old endpoint.

This is one reason DNS failover cannot guarantee immediate traffic migration.

### 7.2 Health-Check Detection Delay

Failover involves multiple stages:

* Application failure occurs.

* Route 53 health checkers detect the failure.

* Health-check evaluation determines the endpoint is unhealthy.

* Route 53 changes the DNS answer according to the routing policy.

* Recursive DNS resolvers refresh their cached answers.

* Clients establish new connections.

Each stage introduces potential delay.

### 7.3 Existing Connections

DNS failover primarily affects DNS resolution.

It does not automatically:

* Terminate existing TCP connections.

* Migrate active HTTP sessions.

* Move established WebSocket connections.

* Transfer application memory between regions.

* Replicate database transactions.

Applications must implement their own retry, reconnection, session persistence, and data replication mechanisms.

### 7.4 Recovery Behavior

Suppose the primary region becomes healthy again.

Route 53 can begin returning the primary record again, depending on the routing configuration.

However, clients may still have cached secondary DNS responses.

This can result in temporary traffic distribution across both environments.

Therefore, recovery should consider:

* Health-check recovery behavior.

* DNS TTL values.

* Recursive resolver caching.

* Client-side DNS caching.

* Application connection reuse.

* Database synchronization.

### 7.5 What Happens When Both Endpoints Are Unhealthy?

This is an important production scenario.

Route 53 does not create a healthy endpoint when every endpoint fails.

Depending on the routing policy and record configuration, Route 53 can return records that are considered unhealthy when no healthy alternatives are available.

Therefore, a backup environment should be monitored independently, and disaster recovery procedures should include testing the scenario where both regions fail.

### 7.6 Health Checks Are Not End-to-End Availability Guarantees

An endpoint may respond successfully while its application is effectively unusable.

For example:

```text
HTTP endpoint:       Healthy
Database:            Unavailable
Authentication:      Unavailable
Payment processing:  Unavailable
```

A basic HTTP health check may not detect these failures.

A better design uses application-specific health endpoints, calculated health checks, and CloudWatch alarm-based monitoring where appropriate.

Reference: [How Route 53 health checks work](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/welcome-health-checks.html?utm_source=chatgpt.com).

### 8\. Health-Check Monitoring and CloudWatch Integration

Monitoring health checks is important because DNS failover should itself be monitored.

You need to know:

* Whether an endpoint is healthy.

* Whether Route 53 has detected a failure.

* How many health checkers consider an endpoint healthy.

* Whether a failover has occurred.

* Whether the application has recovered.

### 8.1 Route 53 CloudWatch Metrics

Route 53 publishes health-check-related CloudWatch metrics.

Important metrics include:

| Metric                       | Description                                                    |
| ---------------------------- | -------------------------------------------------------------- |
| HealthCheckStatus            | Overall health-check status                                    |
| HealthCheckPercentageHealthy | Percentage of health checkers reporting healthy                |
| HealthCheckPercentageHealthy | Useful for observing disagreement between distributed checkers |

For endpoint health checks, CloudWatch can also expose latency measurements when latency measurement is enabled.

### 8.2 Creating CloudWatch Alarms

You can create an alarm based on the health-check status metric.

For example:

```python
health_alarm = aws.cloudwatch.MetricAlarm(
    "primary-endpoint-unhealthy",
    namespace="AWS/Route53",
    metric_name="HealthCheckStatus",
    dimensions={
        "HealthCheckId": primary_health.id,
    },
    statistic="Minimum",
    period=60,
    evaluation_periods=1,
    threshold=1,
    comparison_operator="LessThanThreshold",
    alarm_description="Primary endpoint is unhealthy",
)
```

The `HealthCheckStatus` metric uses:

* `1` for healthy.

* `0` for unhealthy.

This alarm can be integrated with Amazon SNS for notifications.

For production environments, consider multiple evaluation periods and appropriate missing-data handling to reduce unnecessary alerts.

### 8.3 Monitoring Health Checks Through AWS CLI

List health checks:

```bash
aws route53 list-health-checks
```

Retrieve a specific health check:

```bash
aws route53 get-health-check \
  --health-check-id HEALTH_CHECK_ID
```

Retrieve the current health-check status:

```bash
aws route53 get-health-check-status \
  --health-check-id HEALTH_CHECK_ID
```

Retrieve detailed health-check observations:

```bash
aws route53 get-health-check-observations \
  --health-check-id HEALTH_CHECK_ID
```

Inspect the health-check status through CloudWatch:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Route53 \
  --metric-name HealthCheckStatus \
  --dimensions Name=HealthCheckId,Value=HEALTH_CHECK_ID \
  --start-time "$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" \
  --end-time "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  --period 60 \
  --statistics Minimum Average
```

These commands are useful for troubleshooting health-check behavior without relying exclusively on the AWS Management Console.

### 9\. Hands-on Labs

The following labs progressively build a DNS failover environment.

8 Labs

### Lab 1 — Create HTTP and HTTPS Health Checks

Objective: Understand how Route 53 monitors application endpoints.

Tasks:

* Deploy a simple HTTP application.

* Expose a `/health` endpoint.

* Configure an HTTP health check using Pulumi.

* Configure an HTTPS health check.

* Configure the health-check interval and failure threshold.

* Inspect the health-check status using AWS CLI.

* Compare HTTP and HTTPS health-check behavior.

Example Pulumi implementation:

```python
import pulumi
import pulumi_aws as aws

http_check = aws.route53.HealthCheck(
    "http-check",
    fqdn="api.example.com",
    port=80,
    type="HTTP",
    resource_path="/health",
    failure_threshold=3,
    request_interval=30,
)

https_check = aws.route53.HealthCheck(
    "https-check",
    fqdn="api.example.com",
    port=443,
    type="HTTPS",
    resource_path="/health",
    failure_threshold=3,
    request_interval=30,
)

pulumi.export("http_health_check_id", http_check.id)
pulumi.export("https_health_check_id", https_check.id)
```

### Lab 2 — Configure Health Checks for Application Endpoints

Objective: Understand how endpoint monitoring relates to actual application health.

Tasks:

* Deploy an application behind an ALB.

* Create a dedicated `/health` endpoint.

* Configure an HTTP response validation check.

* Configure a string-matching health check.

* Simulate an application returning an unhealthy response.

* Observe how Route 53 evaluates the endpoint.

* Compare basic HTTP monitoring with application-aware monitoring.

Example:

```python
health_check = aws.route53.HealthCheck(
    "application-string-check",
    fqdn="api.example.com",
    port=443,
    type="HTTPS_STR_MATCH",
    resource_path="/health",
    search_string='"status": "healthy"',
    failure_threshold=3,
    request_interval=30,
)
```

This lab demonstrates why HTTP response validation is useful when an endpoint might return successful HTTP status codes despite application failures.

### Lab 3 — Implement Calculated Health Checks

Objective: Monitor multiple application components through a single health status.

Tasks:

* Deploy two application endpoints.

* Create individual health checks.

* Create a calculated health check.

* Configure a threshold requiring at least one healthy endpoint.

* Simulate individual endpoint failures.

* Observe how the parent health check changes.

* Experiment with different thresholds.

Architecture:

```text
             Application Health
                      |
               Calculated Check
                 /         \
                /           \
           API Server A   API Server B
                |             |
           Health Check  Health Check
```

### Lab 4 — Integrate CloudWatch Alarms with Route 53

Objective: Use application metrics to influence DNS health decisions.

Tasks:

* Publish a custom application metric to CloudWatch.

* Create a CloudWatch metric alarm.

* Configure the alarm's evaluation threshold.

* Create a Route 53 CloudWatch alarm-based health check.

* Configure insufficient-data behavior.

* Observe the Route 53 health-check status.

* Configure an SNS notification for the CloudWatch alarm.

* Investigate the relationship between metric data, alarm state, and DNS health.

Suggested metric:

```text
Namespace: MyApplication
Metric: ApplicationErrorRate
Threshold: 10%
Period: 60 seconds
Evaluation periods: 3
```

### Lab 5 — Build a Primary/Secondary Failover Architecture

Objective: Implement DNS failover between two AWS Regions.

![Ensuring Business Continuity: Route 53 Failover Across On-Premises and AWS](https://images.openai.com/static-rsc-4/OpY62CeVy7-Abr4HxcuW6_D7pRb8l-Rql05J7AVSsLgHS5dZCDsf1EXuBqx5BB7C5e-fXSKCQUibP77gFnQEjAIc8_Kq6Ij086eQisMyeSa62MHbrE0ywJPsGex1SkoNavaOGH2D3McZ3xfRh8_xR_jyL4J2d9hnZcvaMOSehwnSzIef6QiOJw_XeyFHEnEF?purpose=fullsize)

Tasks:

* Deploy an application in two AWS Regions.

* Create an ALB in each Region.

* Create health checks for both application endpoints.

* Create a primary failover DNS record.

* Create a secondary failover DNS record.

* Associate the corresponding health checks.

* Configure DNS TTL values.

* Test normal traffic routing.

* Verify that the secondary environment is selected when the primary becomes unhealthy.

Use Pulumi to manage:

* Regional application infrastructure.

* Route 53 health checks.

* Failover DNS records.

* CloudWatch alarms.

### Lab 6 — Simulate Application Failures and Observe DNS Responses

Objective: Understand how Route 53 responds to application failures.

Tasks:

* Start both application environments.

* Verify that the primary is healthy.

* Query the DNS record using `dig`.

* Stop the primary application.

* Observe health-check status changes.

* Query DNS repeatedly.

* Verify that the secondary record is returned.

* Restore the primary application.

* Observe recovery and DNS behavior.

Useful commands:

```bash
dig app.example.com

dig app.example.com A

dig +noall +answer app.example.com
```

For continuous observation:

```bash
while true; do
    date
    dig +short app.example.com
    sleep 5
done
```

Remember that the DNS resolver used by `dig` might cache previous responses.

For comparison, query an authoritative Route 53 name server directly:

```bash
dig @ns-123.awsdns-45.com app.example.com
```

Replace the example name server with one of the authoritative name servers assigned to your hosted zone.

### Lab 7 — Monitor Health-Check Status Through AWS CLI

Objective: Automate health-check monitoring.

Tasks:

* List all configured health checks.

* Retrieve individual health-check configurations.

* Inspect health-check status.

* Retrieve health-check observations.

* Query CloudWatch metrics.

* Create Bash scripts for health-check inspection.

* Identify unhealthy endpoints.

* Generate a simple operational report.

Example Bash script:

```bash
#!/usr/bin/env bash

set -euo pipefail

HEALTH_CHECK_ID="${1:?Usage: ./check-health.sh HEALTH_CHECK_ID}"

echo "Health Check: ${HEALTH_CHECK_ID}"

aws route53 get-health-check-status \
    --health-check-id "$HEALTH_CHECK_ID" \
    --output json
```

Run it:

```bash
chmod +x check-health.sh

./check-health.sh HEALTH_CHECK_ID
```

### Lab 8 — Investigate DNS Caching and Failover Recovery

Objective: Understand the limitations of DNS-based failover.

Tasks:

* Configure a DNS record with a TTL of 60 seconds.

* Resolve the DNS record from multiple clients.

* Record the returned DNS answers.

* Simulate primary endpoint failure.

* Observe the time required for health-check detection.

* Observe how recursive DNS resolvers handle cached answers.

* Restore the primary endpoint.

* Observe how DNS answers change after recovery.

* Compare authoritative DNS responses with recursive resolver responses.

* Analyze how TTL affects failover and recovery behavior.

Useful commands:

```bash
dig app.example.com

dig @1.1.1.1 app.example.com

dig @8.8.8.8 app.example.com

dig +trace app.example.com
```

The goal is to understand why Route 53 health-check detection time and actual client traffic migration time are different.

### 10\. Module Summary

By completing this module, you should understand how to:

* Configure HTTP, HTTPS, and TCP endpoint health checks.

* Understand distributed health-check evaluation.

* Configure failure thresholds and monitoring intervals.

* Build calculated health checks.

* Integrate CloudWatch alarms with Route 53.

* Associate health checks with DNS records.

* Implement primary/secondary failover.

* Design active-active and active-passive architectures.

* Monitor health checks through CloudWatch and AWS CLI.

* Automate health-check infrastructure using Pulumi.

* Understand DNS caching, failover delays, and recovery behavior.

### Important AWS Documentation

These are useful references while studying the module:

* [How Amazon Route 53 checks the health of your resources](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/welcome-health-checks.html?utm_source=chatgpt.com)

* [How Route 53 determines health-check status](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-determining-health-of-endpoints.html?utm_source=chatgpt.com)

* [Route 53 HealthCheckConfig API reference](https://docs.aws.amazon.com/Route53/latest/APIReference/API_HealthCheckConfig.html?utm_source=chatgpt.com)

* [Monitoring health checks using CloudWatch](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-health-checks.html?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 HealthCheck resource](https://www.pulumi.com/registry/packages/aws/api-docs/route53/healthcheck/?utm_source=chatgpt.com)

Next module: Module 5 — Private Hosted Zones and Hybrid DNS with Route 53 Resolver.
