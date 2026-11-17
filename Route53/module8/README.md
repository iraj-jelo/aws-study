### Module 8 — DNS Monitoring, Logging, Troubleshooting, and Cost Optimization

### 1\. Introduction

DNS is one of the most important components of an AWS infrastructure. Applications depend on DNS to discover services, connect to load balancers, communicate across VPCs, and reach external resources.

However, DNS problems are not always obvious.

For example:

* An application cannot connect to an ALB because DNS returns an outdated IP address.

* A private DNS record resolves in one VPC but not another.

* A Route 53 Resolver endpoint stops forwarding DNS queries.

* A health check reports an unhealthy endpoint, causing DNS failover.

* A DNS configuration change accidentally removes an important record.

* DNS queries increase unexpectedly, resulting in higher costs.

To operate Route 53 reliably, you need three capabilities:

* Observability: Understand what DNS queries are happening and how DNS infrastructure behaves.

* Troubleshooting: Identify why DNS resolution fails or produces unexpected results.

* Cost optimization: Understand which Route 53 features generate costs and how to manage them efficiently.

This module focuses on these three capabilities.

### Part 1 — DNS Monitoring and Logging

### 2\. Route 53 Query Logging

Route 53 provides DNS query logging capabilities that allow you to inspect DNS queries made against your DNS infrastructure.

Query logs help answer questions such as:

* Which domain names are clients requesting?

* Which clients are generating the most DNS queries?

* Are clients requesting nonexistent domains?

* Are applications repeatedly querying the same records?

* Are DNS requests coming from unexpected locations?

* Are DNS resolution patterns changing after a deployment?

There are two important logging mechanisms:

| Logging mechanism                         | What it monitors                             |
| ----------------------------------------- | -------------------------------------------- |
| Route 53 public hosted zone query logging | DNS queries received by a public hosted zone |
| Route 53 Resolver query logging           | DNS queries handled by the Route 53 Resolver |

These mechanisms serve different purposes.

### 2.1 Public Hosted Zone Query Logging

Route 53 public hosted zones support query logging through Amazon CloudWatch Logs.

When enabled, Route 53 sends information about DNS queries received by the hosted zone to a CloudWatch Logs log group.

For example, suppose you own:

```text
example.com
```

And configure these records:

```text
api.example.com
www.example.com
mail.example.com
```

Clients around the world send DNS queries for these names.

With query logging enabled, you can investigate requests received by your hosted zone.

A simplified query log might contain:

```json
{
  "query_timestamp": "2026-11-01T10:15:30Z",
  "query_name": "api.example.com",
  "query_type": "A",
  "response_code": "NOERROR",
  "protocol": "UDP",
  "edge_location": "Example-Edge",
  "source": "203.0.113.10"
}
```

The fields above are illustrative; actual Route 53 query log records have a defined AWS schema.

Important information includes:

* Query timestamp.

* Requested domain name.

* DNS record type.

* DNS response code.

* Transport protocol.

* DNS response information.

* Source and edge-location information where provided.

Important: Public hosted zone query logging is not a complete record of every DNS lookup performed by every client.

For example, a client might receive a cached answer from its recursive resolver without generating a new query to your authoritative hosted zone.

This distinction becomes important when investigating query volume.

### 2.2 Enabling Public Hosted Zone Query Logging

The general configuration process is:

* Create a CloudWatch Logs log group.

* Configure the required Route 53 logging permissions.

* Create a query logging configuration.

* Associate it with the public hosted zone.

* Generate DNS queries.

* Inspect the resulting log events.

Using AWS CLI:

```bash
aws logs create-log-group \
  --log-group-name /aws/route53/public-dns
```

Create the query logging configuration:

```bash
aws route53 create-query-logging-config \
  --hosted-zone-id Z123456789EXAMPLE \
  --cloud-watch-logs-log-group-arn \
  arn:aws:logs:us-east-1:123456789012:log-group:/aws/route53/public-dns
```

The hosted zone ID and log group ARN are examples.

You must also configure the appropriate CloudWatch Logs resource permissions so Route 53 can publish the logs. The exact requirements and supported resource configuration should be checked against the current AWS documentation.

### 2.3 Pulumi Configuration

You can manage query logging as infrastructure using Pulumi.

For example, using Python:

```python
import pulumi
import pulumi_aws as aws

zone = aws.route53.Zone(
    "public-zone",
    name="example.com"
)

log_group = aws.cloudwatch.LogGroup(
    "route53-query-logs",
    name="/aws/route53/public-dns",
    retention_in_days=30
)

query_logging = aws.route53.QueryLoggingConfig(
    "public-zone-query-logging",
    zone_id=zone.zone_id,
    cloudwatch_log_group_arn=log_group.arn
)
```

This illustrates the resource relationship. In a deployable project, you must also configure the required CloudWatch Logs resource policy and ensure the log group is in a supported Region for the hosted zone's query logging configuration.

Notice that Route 53 hosted zones are global resources, but their CloudWatch Logs destinations are regional resources.

### 3\. DNS Query Logging for Private Hosted Zones

Public hosted zone logging and private DNS logging are not interchangeable.

For private DNS, the primary mechanism is Route 53 Resolver query logging.

Consider an AWS environment with three VPCs:

* Production VPC

* Development VPC

* Shared Services VPC

You create a private hosted zone:

```text
internal.example.com
```

And configure records:

```text
api.internal.example.com
database.internal.example.com
redis.internal.example.com
```

Applications inside associated VPCs can resolve these names.

But how do you know which VPC is requesting which domain?

This is where Resolver query logging becomes useful.

### 4\. Route 53 Resolver Query Logging

Route 53 Resolver query logging captures DNS queries handled by the Resolver in your VPCs.

It provides visibility into DNS resolution activity for workloads using VPC DNS resolution.

You can associate a query logging configuration with:

* One VPC.

* Multiple VPCs.

* VPCs across supported AWS accounts through centralized architectures.

A simplified architecture:

![Route 53 Resolver の DNS クエリログを設定する - サーバーワークスエンジニアブログ](https://images.openai.com/static-rsc-4/7zzN8mn_IMTJoy4IyDuAiQ6t2xP2qW5LjjGVXzuFs3UwoykqHaYmuwxC5ysWAunR2WV589UMZPG4XInZ1FyPSm0O1SkL-3zti7lqoRgOqtDm1f7u6s9ZtyRpqsZpM32SXHsb7ytKBJqlZPZQzEr6OxBSZNqwtSUquRXoLeIpYQ3mREl_YIlJ7jz3y3DKVyb6?purpose=fullsize)

The architecture works as follows:

* An EC2 instance sends a DNS query.

* The query reaches the VPC Route 53 Resolver.

* Resolver processes the query.

* Resolver query logging captures the DNS activity.

* Log events are delivered to the configured destination.

### 4.1 Supported Log Destinations

Route 53 Resolver query logging supports three important destinations:

| Destination          | Typical purpose                          |
| -------------------- | ---------------------------------------- |
| CloudWatch Logs      | Real-time investigation and analysis     |
| Amazon S3            | Long-term storage and archival           |
| Amazon Data Firehose | Streaming and centralized log processing |

This gives you flexibility when designing your logging architecture.

For example:

* CloudWatch Logs for operational troubleshooting.

* S3 for long-term retention.

* Firehose for forwarding logs into centralized analytics platforms.

### 4.2 Creating a Resolver Query Logging Configuration

Using AWS CLI:

```bash
aws route53resolver create-resolver-query-log-config \
  --name production-dns-logs \
  --destination-arn \
  arn:aws:logs:us-east-1:123456789012:log-group:/aws/route53/resolver
```

The returned configuration ID can then be associated with a VPC:

```bash
aws route53resolver associate-resolver-query-log-config \
  --resolver-query-log-config-id rqlc-123456789 \
  --resource-id vpc-123456789
```

The destination must have the appropriate resource permissions.

### 4.3 What Information Can You Investigate?

Resolver query logs can help you investigate:

* Query names.

* Query types.

* Query timestamps.

* Source IP addresses.

* VPC IDs.

* DNS response codes.

* Resolver endpoint information where applicable.

* DNS transport and response details.

This is particularly valuable when troubleshooting private hosted zones and hybrid DNS.

Important distinction: Resolver query logging records queries handled by the VPC Resolver. It does not automatically capture every DNS packet exchanged directly between arbitrary DNS servers or every lookup satisfied by an application-level cache.

### 5\. Integration with CloudWatch Logs

CloudWatch Logs is one of the primary destinations for Route 53 DNS logs.

It provides a centralized location for storing and analyzing DNS activity.

Its main capabilities include:

* Log groups and log streams.

* Log retention policies.

* Search and filtering.

* CloudWatch Logs Insights.

* Metric filters.

* Subscription filters.

* Integration with CloudWatch alarms and dashboards.

### 5.1 Log Groups and Log Streams

A log group represents a collection of related logs.

For example:

```text
/aws/route53/public-dns
/aws/route53/resolver
/aws/route53/health-checks
```

Log streams organize events within a log group.

A common organizational strategy is to separate DNS logs by environment or purpose.

For example:

```text
/aws/route53/production
/aws/route53/development
/aws/route53/hybrid-dns
```

### 5.2 Log Retention

CloudWatch Logs charges for log ingestion and storage.

You should avoid retaining every DNS event indefinitely unless you have a specific operational, security, or compliance requirement.

For example:

```python
log_group = aws.cloudwatch.LogGroup(
    "dns-logs",
    retention_in_days=30
)
```

You could use shorter retention for development environments and longer retention for production environments.

For long-term archival, S3 is often more economical.

### 6\. Analyzing DNS Queries with CloudWatch Logs Insights

CloudWatch Logs Insights allows you to query DNS logs using a specialized query language.

It is especially useful when DNS traffic increases unexpectedly or when an application experiences DNS resolution problems.

### 6.1 Find the Most Frequently Queried Domains

A query might look like:

```sql
fields query_name
| stats count(*) as total_queries by query_name
| sort total_queries desc
| limit 20
```

This identifies the most frequently queried domain names.

You might discover that one application continuously queries:

```text
database.internal.example.com
```

This could indicate excessive DNS lookup activity or inefficient application-level caching.

### 6.2 Find DNS Errors

For example:

```sql
fields query_name, response_code
| filter response_code != "NOERROR"
| stats count(*) as errors by response_code, query_name
| sort errors desc
```

This helps identify unsuccessful DNS responses.

Common response codes include:

| Response code | Meaning                                 |
| ------------- | --------------------------------------- |
| NOERROR       | Successful DNS response                 |
| NXDOMAIN      | Requested domain name does not exist    |
| SERVFAIL      | DNS server could not complete the query |
| REFUSED       | Query was refused                       |

Be careful when interpreting these results: `NOERROR` does not necessarily mean that the requested record type exists. An empty answer can still be a successful DNS response, commonly called NODATA.

### 6.3 Find DNS Queries from a Specific VPC

For Resolver query logs:

```sql
fields query_name, srcaddr, vpc_id
| filter vpc_id = "vpc-123456789"
| stats count(*) as total_queries by query_name
| sort total_queries desc
```

This can help identify DNS-heavy workloads in a particular VPC.

### 6.4 Investigate NXDOMAIN Spikes

```sql
fields @timestamp, query_name, response_code
| filter response_code = "NXDOMAIN"
| stats count(*) as failures by bin(5m)
```

This produces a time-based view of unsuccessful DNS requests.

A sudden spike could indicate:

* A deployment with an incorrect hostname.

* A missing DNS record.

* A configuration error.

* A compromised workload generating unusual DNS requests.

* An application using an outdated service name.

### 7\. Integration with Amazon S3 and Centralized Log Storage

CloudWatch Logs is convenient for immediate troubleshooting, but it is not always the best destination for long-term DNS log storage.

For large AWS environments, you may want to centralize DNS logs from multiple accounts and VPCs.

Amazon S3 provides durable object storage for this purpose.

### 7.1 CloudWatch Logs to S3

A common architecture is:

![Stream AWS CloudWatch log groups to Amazon S3 | by Venkatesh Muthusami | Medium](https://images.openai.com/static-rsc-4/VxJNHsYPouaeOEorApbBqJnufkLhEeTwX61aFITuYUA1zo4urfLg5I2L-phYKPpOgdFK2H_MC0C0Bmq67HwfrzkSpptnBGQJgMdTb573Ny6mWv3E6iugp9VcCR2NITanSpw44n5hFSX4qfi-VxDza1jfrJ8JmRXLQbHdQ14UcKLTzv2-vQvfAi68oHhLva3W?purpose=fullsize)

The workflow:

* Route 53 generates DNS query logs.

* CloudWatch Logs receives the events.

* A subscription filter forwards matching events to Amazon Data Firehose.

* Firehose delivers the events to an S3 bucket.

* Analytics services can query the stored logs.

You can also use S3 as a direct destination for Route 53 Resolver query logging, avoiding CloudWatch Logs when direct archival is your primary requirement.

### 7.2 Organizing DNS Logs in S3

For a multi-account architecture, organize log objects by account, Region, environment, and date.

For example:

```text
s3://central-dns-logs/
    account-id/
        region/
            environment/
                year/
                    month/
                        day/
                            dns-logs.json.gz
```

This organization makes it easier to retrieve logs for a particular account or time period.

### 7.3 Querying DNS Logs with Athena

Amazon Athena allows you to query structured DNS logs stored in S3 using SQL.

For example:

```sql
SELECT
    query_name,
    COUNT(*) AS total_queries
FROM dns_logs
WHERE year = '2026'
  AND month = '11'
GROUP BY query_name
ORDER BY total_queries DESC
LIMIT 20;
```

You can use this approach to investigate historical DNS behavior without keeping all logs in CloudWatch Logs.

### 7.4 Choosing a Storage Strategy

| Requirement                       | Recommended destination |
| --------------------------------- | ----------------------- |
| Immediate troubleshooting         | CloudWatch Logs         |
| Historical DNS analytics          | S3 + Athena             |
| Streaming log processing          | Data Firehose           |
| Centralized multi-account storage | S3                      |
| Operational dashboards            | CloudWatch              |

For production systems, you can combine these services rather than choosing only one.

### 8\. CloudTrail Management Events and Route 53 API Auditing

DNS query logs tell you what DNS requests occurred.

But they don't necessarily tell you who changed the DNS configuration.

For that, you need AWS CloudTrail.

CloudTrail records API activity in your AWS account.

For Route 53, this includes management operations such as:

* Creating hosted zones.

* Deleting hosted zones.

* Creating DNS records.

* Updating DNS records.

* Deleting DNS records.

* Creating health checks.

* Modifying traffic policies.

* Changing Resolver configurations.

### 8.1 Understanding the Difference Between CloudTrail and DNS Query Logs

Consider this situation:

An application suddenly stops resolving:

```text
api.example.com
```

You need to determine what happened.

There are two separate questions:

* What DNS queries were made, and what responses did clients receive?

* Did someone change or delete the DNS record?

The first question is investigated using DNS query logs.

The second is investigated using CloudTrail.

| Feature                                     | DNS query logging          | CloudTrail |
| ------------------------------------------- | -------------------------- | ---------- |
| Records DNS requests                        | Yes                        | No         |
| Records DNS responses                       | Yes, according to log type | No         |
| Records API operations                      | No                         | Yes        |
| Identifies API caller                       | Not its primary purpose    | Yes        |
| Helps investigate DNS configuration changes | Indirectly                 | Yes        |

### 8.2 Example: Investigating a DNS Record Deletion

Suppose someone deletes:

```text
api.example.com
```

You can search CloudTrail Event History for the Route 53 API operation:

```text
ChangeResourceRecordSets
```

An illustrative event structure:

```json
{
  "eventSource": "route53.amazonaws.com",
  "eventName": "ChangeResourceRecordSets",
  "awsRegion": "us-east-1",
  "userIdentity": {
    "type": "IAMUser"
  },
  "requestParameters": {
    "hostedZoneId": "Z123456789EXAMPLE"
  }
}
```

The actual event contains additional information, including the request details and identity information when available.

You can investigate:

* Who performed the operation.

* When the operation occurred.

* Which AWS identity was used.

* Which hosted zone was affected.

* What changes were requested.

### 8.3 CloudTrail Event History

You can use AWS CLI to look for Route 53 changes:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes \
  AttributeKey=EventName,AttributeValue=ChangeResourceRecordSets
```

For production environments, create a CloudTrail trail and send events to a dedicated S3 bucket.

You can then use Athena to analyze historical API activity.

Important: Route 53 DNS query activity and Route 53 API activity are different categories. CloudTrail management events are not a replacement for DNS query logging.

Also, distinguish management events from Route 53 Resolver DNS Firewall and Resolver data-plane activity. Not every DNS query or firewall evaluation is a CloudTrail management event.

### Part 2 — CloudWatch Monitoring and Health Checks

### 9\. Route 53 Metrics and CloudWatch Monitoring

CloudWatch provides monitoring capabilities for several Route 53 features.

However, Route 53 does not expose every DNS operation as a native CloudWatch metric.

You need to understand which metrics are available and which must be derived from logs.

Important monitoring areas include:

* Health checks.

* DNS query activity.

* Resolver endpoints.

* Resolver query logging.

* DNS Firewall.

* Operational errors and service limits.

### 9.1 Route 53 Health Check Metrics

Route 53 health checks publish metrics to CloudWatch.

One particularly important metric is:

```text
HealthCheckStatus
```

It indicates whether the monitored endpoint is healthy.

Conceptually:

| Metric value | Meaning   |
| ------------ | --------- |
| 1            | Healthy   |
| 0            | Unhealthy |

Suppose you monitor:

```text
api.example.com
```

If the endpoint becomes unavailable, Route 53 can detect the failure and update its health status.

CloudWatch can use this metric to trigger an alarm.

### 9.2 Monitoring Health Check Status

Using AWS CLI:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/Route53 \
  --metric-name HealthCheckStatus \
  --dimensions Name=HealthCheckId,Value=abc123 \
  --start-time 2026-11-01T00:00:00Z \
  --end-time 2026-11-01T01:00:00Z \
  --period 60 \
  --statistics Minimum
```

This is an illustrative command; use an appropriate time range and period for the actual metric configuration.

### 9.3 CloudWatch Alarms for Health Checks

You can create an alarm that detects an unhealthy endpoint.

For example:

```python
alarm = aws.cloudwatch.MetricAlarm(
    "api-health-alarm",
    comparison_operator="LessThanThreshold",
    evaluation_periods=2,
    metric_name="HealthCheckStatus",
    namespace="AWS/Route53",
    period=60,
    statistic="Minimum",
    threshold=1,
    dimensions={
        "HealthCheckId": health_check.id
    },
    alarm_description="API endpoint is unhealthy"
)
```

This example uses Pulumi's AWS provider.

In a real production setup, configure an SNS notification action or another incident-management integration.

### 9.4 Important Monitoring Distinction

A Route 53 health check and an application health check are not necessarily equivalent.

For example:

```text
GET /health
```

might return HTTP 200 even though the application cannot access its database.

A better health-check endpoint might validate:

* Application availability.

* Database connectivity.

* Critical dependencies.

* Required internal services.

However, be careful not to make health checks unnecessarily dependent on every optional service. Otherwise, a minor dependency failure might cause an entire region to be removed from DNS routing.

### 10\. Monitoring Resolver Endpoints

Route 53 Resolver endpoints allow DNS queries to move between AWS and external DNS infrastructure.

For example:

```text
On-premises DNS
       |
       v
Inbound Resolver Endpoint
       |
       v
AWS VPC DNS
```

And in the opposite direction:

```text
AWS VPC
   |
   v
Outbound Resolver Endpoint
   |
   v
On-premises DNS
```

Resolver endpoints depend on network connectivity and endpoint capacity.

When troubleshooting them, investigate:

* Endpoint status.

* Endpoint IP addresses.

* Associated security groups.

* Subnet availability.

* Network ACLs.

* Route tables.

* TCP and UDP port 53 connectivity.

* On-premises firewall rules.

* Resolver forwarding rules.

You should also monitor the available Resolver endpoint CloudWatch metrics.

Some useful metrics include:

* `InboundQueryVolume`

* `OutboundQueryVolume`

* `InboundEndpointHealthyENICount`

* `OutboundEndpointHealthyENICount`

* `InboundQueryAggregateVolume`

* `OutboundQueryAggregateVolume`

These metrics help identify DNS traffic patterns and endpoint health.

For example, if an inbound endpoint has fewer healthy network interfaces than expected, investigate its underlying network interfaces and subnet configuration.

Important: Resolver endpoint metrics are different from DNS query logs. Metrics summarize activity; logs provide individual query details.

### 11\. Creating CloudWatch Dashboards

A dashboard provides a centralized view of DNS infrastructure.

For a production environment, you could create a dashboard with the following sections:

![Conceitos básicos dos painéis automáticos do CloudWatch - Amazon CloudWatch](https://images.openai.com/static-rsc-4/H6svyQfcuCJG5AAPtNjG5AmZKILlR6-bx3g-_7c7T5T3L3jtMgyrrTGswAPdzvcEgFTdgopYSkBVkURelSNMqA7PjCmTjgCnrQwuzviFJFMd6r83BwyUiJI2oyrWXiEzsudMAe0gZQFFdEdOUxESP5eIBkCPDsHOcPHkm84QwxVGN0hV3xyOY-FaG2cqELYH?purpose=fullsize)

| Dashboard section  | Information                            |
| ------------------ | -------------------------------------- |
| Health checks      | Healthy/unhealthy endpoints            |
| Resolver endpoints | Inbound/outbound query volume          |
| DNS errors         | NXDOMAIN and SERVFAIL counts from logs |
| Query activity     | Most frequently queried domains        |
| DNS Firewall       | Blocked and allowed queries            |
| Operational events | Recent DNS configuration changes       |
| Cost               | Route 53 estimated monthly spending    |

CloudWatch dashboards can display native CloudWatch metrics and metrics generated from log data.

For example, you can create a metric filter that counts DNS errors and use that metric in a dashboard.

This gives you a unified operational view of your DNS infrastructure.

### Part 3 — DNS Troubleshooting

### 12\. DNS Troubleshooting Methodology

DNS troubleshooting should follow a systematic process.

Randomly changing DNS records can make the problem worse.

A useful approach is to investigate DNS from the client toward the authoritative DNS infrastructure.

DNS troubleshooting workflow

1\. Client configuration

Is the client using the expected DNS resolver?

2\. DNS resolver

Can the recursive resolver process the query?

3\. DNS delegation

Does the DNS hierarchy point to the correct authoritative servers?

4\. Authoritative DNS

Does Route 53 contain the expected record?

5\. DNS response

Is the returned answer correct and usable by the application?

Let's explore the most common problems.

### 13\. Common DNS Resolution Failures

### 13.1 NXDOMAIN

NXDOMAIN means the requested domain name does not exist.

For example:

```bash
dig api.example.com
```

The response might contain:

```text
status: NXDOMAIN
```

Possible causes:

* The DNS record was never created.

* The record was deleted.

* The domain name contains a typo.

* The parent domain delegation is incorrect.

* A private hosted zone is not associated with the VPC.

* A negative DNS response is still cached.

Start by checking the authoritative DNS server:

```bash
dig @ns-123.awsdns-45.com api.example.com A
```

If the authoritative server also returns NXDOMAIN, investigate the hosted zone and record configuration.

If the authoritative server returns a valid answer but your normal resolver returns NXDOMAIN, investigate caching and delegation.

### 13.2 SERVFAIL

SERVFAIL means the DNS server could not successfully complete the query.

Possible causes include:

* DNSSEC validation failures.

* Authoritative server problems.

* DNS forwarding failures.

* Incorrect Resolver configuration.

* Connectivity problems between DNS servers.

Useful commands:

```bash
dig api.example.com
```

```bash
dig +trace api.example.com
```

```bash
dig +dnssec api.example.com
```

If DNSSEC is involved, inspect the DS records and DNSSEC signing configuration.

### 13.3 REFUSED

REFUSED indicates that a DNS server refused to process the query.

Possible causes include:

* DNS server access policies.

* DNS Firewall rules.

* Resolver configuration.

* Incorrect query routing.

* Restrictions on recursive queries.

Check the relevant DNS server or Resolver configuration.

### 13.4 Timeout

A timeout means the client did not receive a response within the expected period.

Possible causes:

* Security group restrictions.

* Network ACL restrictions.

* Missing routes.

* Incorrect Resolver endpoint configuration.

* Firewall restrictions.

* DNS server unavailability.

Remember that DNS commonly uses UDP port 53, but TCP port 53 is also required in certain situations.

Do not investigate only UDP connectivity.

### 14\. Debugging DNS Delegation

Delegation is one of the most common sources of DNS problems.

Suppose you have:

```text
example.com
```

And you create:

```text
dev.example.com
```

You create a separate hosted zone for the subdomain.

However, simply creating the subdomain hosted zone does not make it publicly resolvable through the parent domain.

You must delegate the subdomain.

The parent zone needs NS records pointing to the authoritative name servers of the child hosted zone.

Conceptually:

Parent hosted zone

`example.com`

NS delegation

Child hosted zone

`dev.example.com`

Application records

`api.dev.example.com`

To inspect delegation:

```bash
dig NS example.com
```

```bash
dig NS dev.example.com
```

To trace the resolution process:

```bash
dig +trace api.dev.example.com
```

Check that:

* The parent zone contains the correct NS delegation.

* The child hosted zone has the expected NS records.

* The registrar points to the correct name servers for the parent domain.

* No stale or conflicting delegation exists.

Important: Changing the NS records in a child hosted zone is not the same as updating delegation in the parent zone.

Both sides must be configured correctly.

### 15\. Debugging TTL and DNS Caching

TTL stands for Time To Live.

It specifies how long a DNS response can be cached by a DNS resolver.

For example:

```text
api.example.com
Type: A
Value: 203.0.113.10
TTL: 300
```

A resolver can cache the answer for approximately 300 seconds.

Suppose you change the IP address:

```text
203.0.113.10
```

to:

```text
203.0.113.20
```

Some clients may continue using the old answer until their cached entry expires.

This is why a DNS change may not be immediately visible everywhere.

### 15.1 Inspecting TTL

Use:

```bash
dig api.example.com
```

Look at the answer section:

```text
api.example.com.  300  IN  A  203.0.113.10
```

The number `300` represents the remaining TTL returned by the resolver.

You can also query a specific DNS server:

```bash
dig @8.8.8.8 api.example.com
```

Or:

```bash
dig @1.1.1.1 api.example.com
```

This helps compare the answers returned by different recursive resolvers.

### 15.2 TTL Trade-offs

| TTL           | Advantages                   | Disadvantages                            |
| ------------- | ---------------------------- | ---------------------------------------- |
| 30 seconds    | Faster DNS change visibility | More DNS queries                         |
| 60 seconds    | Relatively fast updates      | Higher query volume                      |
| 300 seconds   | Balanced configuration       | Some delay during changes                |
| 3600 seconds  | Better caching efficiency    | Slower change visibility                 |
| 86400 seconds | Long-lived caching           | Slow recovery from incorrect DNS answers |

These are illustrative choices, not universal recommendations.

### 15.3 Negative Caching

DNS resolvers can also cache negative responses.

For example, a client requests:

```text
new-api.example.com
```

The name does not exist, so the resolver receives NXDOMAIN.

Even after you create the record, some resolvers may continue returning the cached negative response.

The negative caching duration is influenced by the zone's SOA configuration and resolver behavior.

Inspect the SOA record:

```bash
dig example.com SOA
```

Important: Reducing a record's TTL after a DNS change does not immediately invalidate answers that were already cached with the previous TTL.

For planned migrations, reduce TTL sufficiently in advance.

### 16\. Troubleshooting Private DNS and Resolver Endpoints

Private DNS failures require additional investigation because DNS resolution depends on VPC configuration and network connectivity.

Consider:

```text
Production VPC
10.0.0.0/16

Private hosted zone:
internal.example.com

Record:
database.internal.example.com
```

An EC2 instance should resolve:

```text
database.internal.example.com
```

But the lookup fails.

Investigate the following.

### 16.1 VPC DNS Attributes

Check:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-123456789 \
  --attribute enableDnsSupport
```

And:

```bash
aws ec2 describe-vpc-attribute \
  --vpc-id vpc-123456789 \
  --attribute enableDnsHostnames
```

For normal VPC DNS resolution, `enableDnsSupport` must be enabled.

`enableDnsHostnames` is important for features that rely on DNS hostnames, including certain AWS resource hostname behaviors.

### 16.2 Private Hosted Zone Association

Check the hosted zone:

```bash
aws route53 get-hosted-zone \
  --id Z123456789EXAMPLE
```

Inspect its associated VPCs.

The VPC where the workload runs must have the appropriate association with the private hosted zone, directly or through a supported association arrangement.

### 16.3 Resolver Endpoint Troubleshooting

For inbound and outbound endpoints, inspect:

* Endpoint status.

* Endpoint network interfaces.

* Security group inbound and outbound rules.

* Subnet availability.

* Route tables.

* Network ACLs.

* DNS forwarding rules.

* On-premises connectivity.

For DNS traffic, ensure UDP and TCP port 53 are allowed wherever required.

### 16.4 Testing Private DNS

From an EC2 instance inside the VPC:

```bash
dig database.internal.example.com
```

Query the VPC Resolver explicitly:

```bash
dig @169.254.169.253 \
  database.internal.example.com
```

The address `169.254.169.253` is the Amazon-provided VPC DNS server address.

If the private record resolves inside one VPC but not another, compare:

* Private hosted zone associations.

* VPC DNS attributes.

* Resolver forwarding rules.

* DNS Firewall policies.

* Network configuration.

### 17\. DNS Propagation Versus DNS Caching

These two concepts are frequently confused.

When you update a Route 53 record, the change is generally propagated across Route 53's authoritative DNS infrastructure quickly.

However, recursive DNS resolvers may still hold previously cached responses.

Therefore:

Authoritative DNS propagation is not the same thing as recursive DNS cache expiration.

Consider this example:

| Time  | Event                               |
| ----- | ----------------------------------- |
| 10:00 | DNS record points to IP A           |
| 10:01 | A resolver caches IP A with TTL 300 |
| 10:02 | You change the record to IP B       |
| 10:03 | Authoritative DNS returns IP B      |
| 10:04 | Some clients still receive IP A     |
| 10:06 | Previously cached answer expires    |

The delay experienced by clients is caused by caching, not necessarily by Route 53 failing to propagate the update.

There are additional caching layers to consider:

* Browser DNS caches.

* Operating system DNS caches.

* Local recursive resolvers.

* ISP DNS resolvers.

* Application-level DNS caches.

* Intermediate forwarding DNS servers.

A good troubleshooting strategy is to compare:

```bash
dig +trace api.example.com
```

with:

```bash
dig @8.8.8.8 api.example.com
```

The first helps inspect the authoritative resolution chain; the second tests a specific recursive resolver.

### Part 4 — Route 53 Cost Optimization

### 18\. Route 53 Pricing Fundamentals

Route 53 pricing is based on the features and resources you use.

It is important to understand that Route 53 is not simply a DNS service with one monthly subscription fee.

Different capabilities have different billing models.

The main cost categories include:

* Hosted zones.

* DNS queries.

* Health checks.

* Resolver endpoints.

* Resolver DNS queries and related capabilities.

* Traffic Flow policies.

* DNS Firewall and other optional features.

Let's examine the important categories.

### 18.1 Hosted Zone Pricing

A hosted zone represents a DNS namespace.

For example:

```text
example.com
internal.example.com
dev.example.com
```

Each separately created hosted zone can incur a monthly charge.

Creating additional hosted zones unnecessarily can increase your costs.

For example, consider this architecture:

```text
example.com
    |
    +-- api.example.com
    +-- www.example.com
    +-- mail.example.com
    +-- dev.example.com
```

You do not necessarily need a separate hosted zone for every subdomain.

You can manage multiple subdomains as records inside the parent hosted zone.

Create separate hosted zones when delegation, administrative separation, or other architectural requirements justify them.

### 18.2 DNS Query Pricing

Route 53 charges for DNS queries according to the applicable query category and pricing rules.

Different query types and features can have different pricing treatments.

For example:

* Standard DNS queries.

* Alias queries.

* Routing-policy queries.

* Geolocation and latency-based routing.

* Health-check-related DNS behavior.

You should understand the difference between the number of DNS queries and the number of records.

A hosted zone containing 100 records does not automatically generate 100 queries.

Query volume depends on actual DNS traffic.

### 18.3 Health Check Pricing

Route 53 health checks can generate additional costs.

The cost depends on the health-check configuration and applicable pricing category.

For example, consider:

```text
Production API
    |
    +-- HTTP Health Check
    |
    +-- HTTPS Health Check
    |
    +-- Calculated Health Check
```

Creating multiple health checks for the same endpoint without a clear monitoring requirement can unnecessarily increase costs.

You should design health checks around actual availability requirements.

### 18.4 Resolver Endpoint Pricing

Route 53 Resolver endpoints introduce a different cost model.

Inbound and outbound endpoints use network interfaces in your VPC subnets.

Their costs generally involve:

* Endpoint availability charges.

* DNS query processing charges.

The endpoint's network interface architecture and query volume influence the overall cost.

For example:

```text
Production VPC
    |
    +-- Inbound Endpoint
    |      +-- ENI in AZ-A
    |      +-- ENI in AZ-B
    |
    +-- Outbound Endpoint
           +-- ENI in AZ-A
           +-- ENI in AZ-B
```

A highly available hybrid DNS architecture requires multiple endpoint IP addresses across Availability Zones.

That improves resilience but increases infrastructure costs.

You should not remove redundancy merely to reduce costs in a production environment.

### 18.5 Example Cost Model

Consider a hypothetical environment:

| Resource                    | Quantity |
| --------------------------- | -------- |
| Public hosted zones         | 2        |
| Private hosted zones        | 3        |
| Health checks               | 4        |
| Resolver inbound endpoints  | 1        |
| Resolver outbound endpoints | 1        |
| Resolver endpoint IPs       | 4        |

Your monthly cost estimation should account for each applicable pricing category.

A useful approach is to maintain a cost inventory:

```text
Route 53
    |
    +-- Hosted zone charges
    |
    +-- Public DNS query charges
    |
    +-- Health check charges
    |
    +-- Resolver endpoint charges
    |
    +-- Resolver query charges
    |
    +-- Optional feature charges
```

Do not assume every query or resource is billed identically. Consult the current AWS pricing page before estimating actual spending.

### 19\. Query Volume Optimization and TTL Trade-offs

One of the simplest ways to influence DNS query volume is to configure appropriate TTL values.

Consider an application that repeatedly requests:

```text
api.example.com
```

If the record has a TTL of 30 seconds, recursive resolvers generally need to refresh their cached answer more frequently than if the TTL is 3600 seconds.

This can increase authoritative DNS query volume.

However, higher TTL values also mean that changes can take longer to become visible to clients.

### 19.1 Choosing TTL Based on Application Requirements

| Application                           | Possible TTL strategy                    |
| ------------------------------------- | ---------------------------------------- |
| Stable production API                 | 300–3600 seconds                         |
| Frequently changing deployment target | 30–300 seconds                           |
| Static infrastructure endpoint        | 3600 seconds or higher                   |
| Planned DNS migration                 | Temporarily lower TTL                    |
| Highly dynamic service discovery      | Evaluate a dedicated discovery mechanism |

These are starting points, not mandatory values.

### 19.2 Avoid Unnecessary DNS Lookups

Consider an application that resolves the same database hostname repeatedly.

Poor application behavior:

```python
def process_request():
    database_ip = resolve_dns(
        "database.internal.example.com"
    )

    return connect(database_ip)
```

If this happens for every request, DNS activity can become unnecessarily high.

A better approach is to reuse established database connections and use appropriate DNS caching behavior.

However, application caching must respect DNS TTL and account for endpoint changes.

Do not cache an IP address indefinitely simply to reduce DNS traffic.

### 19.3 Use Alias Records Where Appropriate

Route 53 Alias records are useful when pointing DNS names to supported AWS resources.

For example:

```text
example.com
    |
    +-- ALB
```

Alias records have special Route 53 pricing treatment, and queries to qualifying AWS resources can be free under the applicable pricing rules.

Always verify the current pricing conditions for the target resource and query type.

### 19.4 Remove Unnecessary Resources

Regularly inspect:

* Unused hosted zones.

* Unused health checks.

* Unused Resolver endpoints.

* Obsolete Resolver forwarding rules.

* Unnecessary Traffic Flow policies.

* Excessively duplicated DNS configurations.

Remember that deleting a resource can affect production DNS resolution. Validate dependencies before removing anything.

### 20\. Operational Monitoring and Alerting Strategies

A production DNS architecture needs proactive monitoring rather than waiting for application failures.

A good monitoring strategy should detect:

* Unhealthy endpoints.

* Sudden DNS error increases.

* Unexpected query-volume changes.

* Resolver endpoint degradation.

* DNS Firewall blocking spikes.

* Unexpected DNS configuration changes.

* Unusual spending patterns.

### 20.1 Recommended Alerts

| Alert                         | Detection mechanism           | Example response                                |
| ----------------------------- | ----------------------------- | ----------------------------------------------- |
| Endpoint unhealthy            | CloudWatch alarm              | Investigate application availability            |
| Resolver endpoint degradation | Resolver metrics              | Inspect endpoint ENIs and networking            |
| NXDOMAIN spike                | Logs Insights / metric filter | Check DNS records and application configuration |
| SERVFAIL increase             | DNS query logs                | Investigate DNSSEC and forwarding               |
| DNS Firewall blocking spike   | Resolver logs and metrics     | Investigate suspicious queries                  |
| Unexpected DNS changes        | CloudTrail                    | Review API caller and change request            |
| Cost increase                 | AWS Budgets / Cost Explorer   | Investigate resource and query growth           |

### 20.2 Operational Runbook

For production environments, document what to do when an alert fires.

For example:

Alert: Production API DNS health check is unhealthy.

* Inspect the Route 53 health-check status.

* Check application availability directly.

* Inspect ALB target health.

* Check CloudWatch application logs.

* Verify the current DNS response.

* Investigate whether DNS failover occurred.

* Check CloudTrail for recent DNS configuration changes.

* Restore service and verify DNS recovery.

This prevents engineers from immediately changing DNS records without identifying the underlying failure.

### Part 5 — Hands-on Labs

The following labs build a monitoring and troubleshooting environment using Pulumi, AWS CLI, Bash, and Python where appropriate.

### Lab 1 — Enable Route 53 Query Logging

Pulumi + Python

Objective: Enable public hosted zone query logging.

Architecture:

```text
Client
  |
  v
Public DNS
  |
  v
Route 53 Hosted Zone
  |
  v
CloudWatch Logs
```

Tasks:

* Create a public hosted zone using Pulumi.

* Create a CloudWatch Logs log group.

* Configure the required CloudWatch Logs resource policy.

* Create a Route 53 query logging configuration.

* Associate the configuration with the hosted zone.

* Generate DNS queries.

* Inspect the resulting log events.

Expected result:

You should be able to identify DNS queries reaching your public hosted zone.

### Lab 2 — Configure Resolver Query Logging

Pulumi + AWS CLI

Objective: Monitor private DNS resolution inside a VPC.

Architecture:

```text
EC2 Instance
     |
     v
VPC Resolver
     |
     +----> Private Hosted Zone
     |
     +----> Resolver Query Logs
                 |
                 v
           CloudWatch Logs
```

Tasks:

* Create a VPC using Pulumi.

* Enable VPC DNS support.

* Create a private hosted zone.

* Associate the hosted zone with the VPC.

* Create private DNS records.

* Create a Resolver query logging configuration.

* Associate the configuration with the VPC.

* Generate DNS queries from an EC2 instance.

* Inspect the query logs.

Expected result:

You should be able to identify which VPC workloads are requesting private DNS records.

### Lab 3 — Analyze DNS Queries Using CloudWatch Logs Insights

Objective: Analyze DNS activity and identify unusual patterns.

Tasks:

* Open the CloudWatch Logs console.

* Select the Route 53 query log group.

* Run queries to identify frequently requested domains.

* Identify NXDOMAIN responses.

* Find DNS requests originating from a particular VPC.

* Group DNS errors by five-minute intervals.

* Compare query patterns before and after generating application traffic.

Expected result:

You should be able to identify DNS query patterns and investigate common resolution problems.

### Lab 4 — Track Route 53 Changes Through CloudTrail

Objective: Audit DNS infrastructure modifications.

Tasks:

* Enable a CloudTrail trail.

* Configure delivery to an S3 bucket.

* Create and modify Route 53 DNS records.

* Delete a test DNS record.

* Find the corresponding API events.

* Identify the IAM identity responsible for each change.

* Inspect the event request parameters.

* Investigate an unexpected DNS configuration change.

Useful AWS CLI command:

```bash
aws cloudtrail lookup-events \
  --lookup-attributes \
  AttributeKey=EventSource,AttributeValue=route53.amazonaws.com
```

Expected result:

You should be able to reconstruct who changed DNS infrastructure and when.

### Lab 5 — Create CloudWatch Dashboards and Alarms

Objective: Build centralized DNS monitoring.

Tasks:

* Identify available Route 53 health-check metrics.

* Create a CloudWatch dashboard.

* Add health-check status metrics.

* Add Resolver endpoint metrics.

* Create a metric filter for DNS errors.

* Create an alarm for repeated unhealthy health-check status.

* Configure SNS notifications.

* Simulate an application failure and observe the alarm.

Expected result:

You should have a dashboard that provides operational visibility into your DNS infrastructure.

### Lab 6 — Troubleshoot Common DNS Resolution Failures

Objective: Diagnose DNS failures systematically.

Intentionally introduce the following problems:

* Delete a DNS record.

* Configure an incorrect record value.

* Introduce incorrect subdomain delegation.

* Associate a private hosted zone with the wrong VPC.

* Configure an incorrect Resolver forwarding rule.

* Introduce a DNS Firewall blocking rule.

For each problem:

* Generate a DNS request.

* Inspect the response.

* Identify the failure category.

* Inspect authoritative DNS.

* Review relevant logs.

* Correct the configuration.

* Verify successful resolution.

Useful commands:

```bash
dig api.example.com
```

```bash
dig +trace api.example.com
```

```bash
dig +short api.example.com
```

```bash
dig NS example.com
```

Expected result:

You should be able to distinguish DNS record errors, delegation problems, private DNS issues, and Resolver failures.

### Lab 7 — Investigate DNS Latency and Caching Behavior

Objective: Understand DNS TTL and recursive resolver caching.

Tasks:

* Create a DNS record with a TTL of 60 seconds.

* Query the record using `dig`.

* Repeat the query against the same recursive resolver.

* Observe the remaining TTL.

* Modify the authoritative DNS record.

* Compare answers from multiple recursive resolvers.

* Investigate the effect of negative caching.

* Compare DNS response behavior using different TTL values.

Useful command:

```bash
watch -n 5 'dig api.example.com'
```

Expected result:

You should understand why different clients can temporarily receive different DNS answers after a record change.

### Lab 8 — Analyze Route 53 Usage and Estimate Monthly Costs

Objective: Understand Route 53 resource consumption and pricing.

Tasks:

* Inventory all hosted zones.

* Inventory health checks.

* Inspect Resolver endpoints and endpoint IPs.

* Review DNS query volumes.

* Inspect CloudWatch log ingestion and retention.

* Review applicable Route 53 pricing categories.

* Estimate monthly spending.

* Identify unnecessary or oversized resources.

* Prepare a cost optimization report.

Useful commands:

```bash
aws route53 list-hosted-zones
```

```bash
aws route53 list-health-checks
```

```bash
aws route53resolver list-resolver-endpoints
```

For historical spending, use AWS Cost Explorer or the AWS Cost and Usage Report.

Expected result:

You should be able to estimate Route 53 costs and identify opportunities to reduce unnecessary spending.

### Lab 9 — Build Bash Scripts for DNS Diagnostics and Operational Monitoring

Bash automation

Objective: Create reusable DNS troubleshooting scripts.

You will build three small operational tools.

Script A — DNS Record Diagnostics

The script should:

* Accept a domain name as an argument.

* Query A, AAAA, CNAME, and NS records.

* Display the DNS response status.

* Display TTL values.

* Report resolution failures.

Example usage:

```bash
./dns-check.sh api.example.com
```

Script B — DNS Server Comparison

The script should:

* Accept a domain name.

* Query multiple recursive DNS servers.

* Compare returned IP addresses.

* Display response times.

* Identify inconsistent responses.

Example:

```bash
./dns-compare.sh api.example.com
```

Script C — DNS Operational Monitoring

The script should:

* Check multiple application DNS names.

* Verify that expected records resolve.

* Record timestamps.

* Log failures.

* Return a nonzero exit status when a critical DNS check fails.

Example:

```bash
./dns-monitor.sh
```

A simplified implementation of Script C:

```bash
#!/usr/bin/env bash

set -u

DOMAINS=(
    "api.example.com"
    "www.example.com"
    "database.internal.example.com"
)

FAILED=0

for domain in "${DOMAINS[@]}"; do

    timestamp=$(date -Is)

    if result=$(dig +time=3 +tries=1 \
        +short "$domain" 2>/dev/null) \
        && [[ -n "$result" ]]; then

        printf '[%s] OK: %s -> %s\n' \
            "$timestamp" "$domain" "$result"

    else

        printf '[%s] FAILED: %s\n' \
            "$timestamp" "$domain"

        FAILED=1

    fi

done

exit "$FAILED"
```

This is a basic DNS existence check. For production monitoring, extend it to validate expected IP addresses or record types, distinguish NXDOMAIN from timeouts, and use an explicit DNS resolver where appropriate.

Expected result:

You should have reusable Bash scripts for DNS diagnostics that can be integrated into CI/CD pipelines, cron jobs, or operational monitoring systems.

### 21\. Key Takeaways

By completing this module, you should understand the following:

| Area               | What you should understand                          |
| ------------------ | --------------------------------------------------- |
| Query logging      | How to capture public and private DNS activity      |
| Resolver logging   | How to monitor DNS queries inside VPCs              |
| CloudWatch Logs    | How to store, search, and analyze DNS logs          |
| S3 and Athena      | How to centralize and analyze historical DNS data   |
| CloudTrail         | How to audit DNS infrastructure changes             |
| CloudWatch metrics | How to monitor health checks and Resolver endpoints |
| Troubleshooting    | How to diagnose DNS failures systematically         |
| Delegation         | How parent and child hosted zones work together     |
| TTL                | How DNS caching affects record changes              |
| Private DNS        | How to troubleshoot VPC DNS and Resolver endpoints  |
| Pricing            | How Route 53 resources and queries affect spending  |
| Bash automation    | How to build reusable DNS diagnostic tools          |

### 22\. Important AWS Documentation

These are useful references for studying this module and keeping your implementation aligned with AWS capabilities.

* [Public hosted zone query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/query-logs.html?utm_source=chatgpt.com)

* [Route 53 Resolver query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs.html?utm_source=chatgpt.com)

* [CloudWatch Logs Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AnalyzingLogData.html?utm_source=chatgpt.com)

* [AWS CloudTrail documentation](https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-user-guide.html?utm_source=chatgpt.com)

* [Monitoring Route 53 health checks](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/monitoring-health-checks.html?utm_source=chatgpt.com)

* [Amazon Route 53 pricing](https://aws.amazon.com/route53/pricing/?utm_source=chatgpt.com)

* [Pulumi AWS Route 53 resources](https://www.pulumi.com/registry/packages/aws/api-docs/route53/?utm_source=chatgpt.com)

### 23\. How This Module Fits into the Course

* Module 1 — DNS Fundamentals and Route 53 Architecture

    Completed

* Module 2 — Hosted Zones, DNS Records, and Domain Management

    Completed

* Module 3 — Route 53 Routing Policies

    Completed

* Module 4 — Route 53 Health Checks and DNS Failover

    Completed

* Module 5 — Private Hosted Zones and Hybrid DNS

    Completed

* Module 6 — DNS Firewall and DNS Security

    Completed

* Module 7 — Traffic Management and Advanced Architectures

    Completed

* Module 8 — Monitoring, Logging, Troubleshooting, and Cost Optimization

    Current module

* Module 9 — Production Route 53 Automation and Capstone Project

    Next

The most important lesson from Module 8: A production DNS architecture is not complete simply because DNS records resolve correctly. You must also be able to observe DNS behavior, investigate failures, audit configuration changes, monitor availability, and control operational costs.
