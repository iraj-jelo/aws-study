### Module 3 — Route 53 Routing Policies

### 1\. Introduction to Route 53 Routing Policies

Amazon Route 53 routing policies determine how DNS queries are answered when multiple DNS records exist for the same domain name.

Unlike traditional load balancers, Route 53 makes routing decisions at the DNS resolution level. It returns DNS responses based on configured policies, health checks, geographic information, latency measurements, or the IP address of the DNS resolver.

For example, suppose an application runs in three AWS regions:

* US East (N. Virginia): `us-east-1`

* Europe (Frankfurt): `eu-central-1`

* Asia Pacific (Singapore): `ap-southeast-1`

Route 53 can direct users toward different regional endpoints depending on the selected routing policy.

![AWS Route 53 and Routing Policies | by Crishantha Nanayakkara | Medium](https://images.openai.com/static-rsc-4/ot5GojQ4UgtEkAkTI5nCtrqmMBILyaImvN9TfslArStIdomnGk-UuVpCKRh5ayNwQbna8ySPcYCZFtzGG6aviToChXkVpXpqdBAetAt3dUeKJTA1PdzAP7_gWavJegTh_N17dXvRPY0Em7qvW0uOcc4-yqfQPY9OMrDhdsj2JLE4sMHcQx51oSCw_fat-BN2?purpose=fullsize)

### 1.1 Routing policies versus DNS records

A DNS record defines information associated with a DNS name, while a routing policy determines how Route 53 selects an answer.

For example:

| Record | Purpose                                       |
| ------ | --------------------------------------------- |
| A      | Maps a hostname to an IPv4 address            |
| AAAA   | Maps a hostname to an IPv6 address            |
| CNAME  | Maps one hostname to another                  |
| Alias  | Routes a hostname to a supported AWS resource |
| TXT    | Stores text information                       |

A routing policy can be associated with records such as A, AAAA, and other supported record types.

### 1.2 Routing policies available in Route 53

Route 53 provides the following major routing policies:

* Simple routing

* Weighted routing

* Latency-based routing

* Failover routing

* Geolocation routing

* Geoproximity routing

* IP-based routing

* Multivalue answer routing

Each policy addresses a different traffic-management requirement.

### 2\. Simple Routing Policy

Simple routing is the default routing policy in Route 53.

It allows you to configure one DNS record for a particular combination of domain name and record type.

For example:

```text
app.example.com
    |
    v
203.0.113.10
```

When a DNS resolver queries `app.example.com`, Route 53 returns the configured DNS answer.

### 2.1 Multiple values in a simple record

Simple routing also supports multiple values in a single record.

For example:

```text
app.example.com

A:
  203.0.113.10
  203.0.113.20
  203.0.113.30
```

Route 53 can return multiple values in the DNS response.

However, simple routing does not provide controlled traffic distribution between endpoints.

### 2.2 Limitations

* No percentage-based traffic distribution.

* No latency-aware endpoint selection.

* No geographic routing.

* No primary/secondary failover configuration.

* No routing decisions based on client IP CIDR collections.

* Multiple returned IP addresses do not guarantee that clients distribute requests evenly.

Simple routing is appropriate when an application has a single endpoint or when sophisticated DNS traffic management is unnecessary.

### 2.3 Pulumi implementation

We can create a simple A record using Pulumi Python.

```python
import pulumi
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

record = aws.route53.Record(
    "app-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=300,
    records=["203.0.113.10"],
)

pulumi.export("record_name", record.name)
```

The example assumes that the public hosted zone already exists.

For production deployments, you would normally use an ALB Alias record rather than hardcoding an application endpoint IP.

### 3\. Weighted Routing Policy

Weighted routing allows you to distribute DNS responses across multiple resources according to configured weights.

This is particularly useful for:

* Blue-green deployments.

* Canary releases.

* Gradual application migrations.

* Traffic distribution across multiple regions.

* Testing a new application version.

### 3.1 How weighted routing works

Suppose you have two application endpoints:

| Endpoint      | Weight |
| ------------- | ------ |
| Application A | 80     |
| Application B | 20     |

The total weight is 100.

Route 53 distributes eligible DNS responses according to the relative weights.

![AWS Route 53 | AWS Pro Architect Prep](https://images.openai.com/static-rsc-4/Uo6i3dKGTrEZSBP0d5Ifik5acrIqOi2qVUSjm8a-3ohgWpKZfeHwLDhqaW4jeRftYtmmQH0nGCdkFVV37qqAI1ENb-8QiHrm5p1oBumMHPUNfvORmomnv8F5wr1z2M69TQoHEmLHRKqRAu1UwYcN0OuGUmy1sPO_c1UwgkgmCXd6kLiAx2H3-T-_oHYvjg4x?purpose=fullsize)

The approximate distribution is:

* 80% of DNS responses point toward Application A.

* 20% of DNS responses point toward Application B.

Important: Weighted routing does not guarantee that exactly 80% of HTTP requests reach Application A. DNS caching, resolver behavior, client caching, and connection reuse influence actual application traffic.

### 3.2 Weighted routing configuration

Each weighted record requires:

* A record name.

* A record type.

* A routing policy.

* A weight.

* A unique set identifier (`set_identifier`).

Example:

```python
import pulumi
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

app_a = aws.route53.Record(
    "app-a",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.10"],
    weighted_routing_policies=[
        {
            "weight": 80
        }
    ],
    set_identifier="application-a",
)

app_b = aws.route53.Record(
    "app-b",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.20"],
    weighted_routing_policies=[
        {
            "weight": 20
        }
    ],
    set_identifier="application-b",
)
```

These records share the same name and type but have different identifiers.

### 3.3 Weighted routing and health checks

Weighted records can be associated with Route 53 health checks.

When a weighted record is unhealthy, Route 53 excludes it from eligible responses, subject to the routing policy's health-evaluation behavior.

There is also a special consideration when all weighted records are unhealthy: Route 53 can return answers from the unhealthy records rather than guarantee an empty response.

### 4\. Latency-Based Routing

Latency-based routing directs users toward the AWS region that Route 53 determines will provide the lowest network latency.

This is useful for globally distributed applications.

Suppose your application runs in three regions:

| AWS Region     | Endpoint             |
| -------------- | -------------------- |
| us-east-1      | US application       |
| eu-central-1   | European application |
| ap-southeast-1 | Asian application    |

A user querying from Europe may receive the Frankfurt endpoint, while a user querying from Asia may receive the Singapore endpoint.

![\[aws\] Route53 (7) - Routing Policy - Latency Based | renine94](https://images.openai.com/static-rsc-4/siZ83ywukeUfMlkixifm8kvNf3_phxxNJTsY0pFRBHbCEyrCbOJItkT8Tap-qxMO2ET44MYV7neaCMeXPj3sb9iLH2q0B3VmQRSeSf95v8fhNHtbNp0P-BXKIO0wvy9fwfGLoCcyn_r5jcjU63b-kw65Cgeo9CXI9zwO6q7wzReczaNsu_zJoTD-cMIo8sBG?purpose=fullsize)

### 4.1 How latency-based routing works

Route 53 maintains latency measurements between different geographic areas and AWS regions.

When a DNS query arrives:

* Route 53 identifies the source location of the DNS query.

* It evaluates available regional records.

* It determines which AWS region has the lowest measured latency.

* It returns the corresponding DNS answer.

The important distinction is that Route 53 uses AWS-maintained latency measurements, not real-time measurements of the application response time.

### 4.2 Pulumi configuration

Latency-based records require the AWS region associated with each endpoint.

```python
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

us_record = aws.route53.Record(
    "us-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.10"],
    latency_routing_policies=[
        {
            "region": "us-east-1"
        }
    ],
    set_identifier="us-east",
)

eu_record = aws.route53.Record(
    "eu-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.20"],
    latency_routing_policies=[
        {
            "region": "eu-central-1"
        }
    ],
    set_identifier="eu-central",
)
```

In a real deployment, the records would normally point to regional ALBs through Alias records.

### 4.3 Important considerations

* Latency-based routing does not guarantee geographic proximity.

* The nearest AWS region is not necessarily the lowest-latency region.

* DNS caching can delay changes in routing decisions.

* Resolver location can differ from the actual end-user location.

* Health checks can be used to exclude unhealthy endpoints.

Latency-based routing is especially useful for multi-region SaaS platforms, APIs, and globally distributed web applications.

### 5\. Failover Routing Policy

Failover routing provides primary/secondary DNS routing.

It is commonly used for disaster recovery and high-availability architectures.

Suppose your primary application runs in N. Virginia and your backup application runs in Frankfurt.

![Creating Disaster Recovery Mechanisms Using Amazon Route 53 | Networking & Content Delivery](https://images.openai.com/static-rsc-4/K9gy_lfmzCuNfiRX865gs83lar0dXDnLrxaJDFU2LW3mg433G1vQKCFVJqCt2r23KfBPPR6n683qCK_uwQjfzz21XIEUIwH7hr7yj2-ArdkjF74-b4gANX2AqIQfcUDrqzIGXOiyI20CayPK60PFHal7wcQQMbtodUZ4wfgqaz-iUDQP822A55uUw3G55RPx?purpose=fullsize)

### 5.1 Primary and secondary records

The primary record receives DNS responses while its associated health evaluation considers it healthy.

If the primary endpoint becomes unhealthy, Route 53 can return the secondary endpoint.

| Record    | Role              | Health  |
| --------- | ----------------- | ------- |
| Primary   | Main application  | Healthy |
| Secondary | Disaster recovery | Healthy |

If the primary becomes unhealthy, the secondary becomes the preferred answer.

### 5.2 Pulumi implementation

A failover record uses:

* `failover_routing_policies`

* `set_identifier`

* An associated health check for the primary endpoint.

Example:

```python
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

primary_health = aws.route53.HealthCheck(
    "primary-health",
    fqdn="primary.example.com",
    port=443,
    type="HTTPS",
    resource_path="/health",
    request_interval=30,
    failure_threshold=3,
)

primary = aws.route53.Record(
    "primary",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.10"],
    health_check_id=primary_health.id,
    failover_routing_policies=[
        {
            "type": "PRIMARY"
        }
    ],
    set_identifier="primary",
)

secondary = aws.route53.Record(
    "secondary",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.20"],
    failover_routing_policies=[
        {
            "type": "SECONDARY"
        }
    ],
    set_identifier="secondary",
)
```

### 5.3 Failover considerations

Failover routing does not automatically replicate application data.

You must separately implement:

* Database replication.

* Application deployment in the backup region.

* Storage replication.

* Disaster recovery procedures.

* Application consistency and recovery mechanisms.

DNS failover changes where new DNS resolutions are directed. Existing client connections are not automatically transferred.

### 6\. Geolocation Routing Policy

Geolocation routing directs DNS queries according to the geographic location of the requester.

Unlike latency-based routing, which tries to optimize network latency, geolocation routing lets you explicitly define which geographic regions should receive which DNS responses.

### 6.1 Geographic routing configuration

Route 53 supports geographic matching at several levels:

* Continent.

* Country.

* US state (for supported US geographic subdivisions).

For example:

| Geographic location | Destination           |
| ------------------- | --------------------- |
| North America       | US application        |
| Europe              | European application  |
| Asia                | Singapore application |
| Default             | US application        |

![Multi-Region advertising workloads - Video Streaming Advertising Lens](https://images.openai.com/static-rsc-4/dKDAOmbdUgoT5L_0kODTXOD6LbehWEH33LGSiu34-9U0Kmuk8o9wCZuxA5pTPmQ_NWBZU-vRwlpmDefHVR1pSzE8Xjk88mD_0zWG2KWB1yssBTnL4tM4A8DLKELosICyC28TthMRFhOiQwqb_d70niN3SBVJvVMu1zlLnzxSFCzyDRQB_k85pqZ113Zw8fHk?purpose=fullsize)

### 6.2 Geolocation routing behavior

Route 53 evaluates geographic records according to their specificity.

For example, if you configure:

* A continent-level record for Europe.

* A country-level record for Germany.

A query identified as originating in Germany matches the more specific country-level record.

Default records are important.

Not every IP address can be mapped to a geographic location. You should configure a default record to handle requests that do not match your geographic records.

Without a default record, Route 53 can return no answer for unmatched queries.

### 6.3 Pulumi implementation

The following example routes European and Asian requests to different endpoints.

```python
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

europe = aws.route53.Record(
    "europe-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.10"],
    geolocation_routing_policies=[
        {
            "continent": "EU"
        }
    ],
    set_identifier="europe",
)

asia = aws.route53.Record(
    "asia-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.20"],
    geolocation_routing_policies=[
        {
            "continent": "AS"
        }
    ],
    set_identifier="asia",
)

default = aws.route53.Record(
    "default-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.30"],
    geolocation_routing_policies=[
        {}
    ],
    set_identifier="default",
)
```

The empty geographic policy represents the default location.

### 6.4 Geolocation use cases

* Regional content distribution.

* Geographic restrictions.

* Regional application endpoints.

* Country-specific application experiences.

* Compliance-oriented traffic segmentation.

Remember that geolocation routing is based on IP-derived geographic information. It is not an authentication or access-control mechanism.

### 7\. Geoproximity Routing Policy

Geoproximity routing directs DNS queries according to the geographic location of AWS resources and users.

It also allows you to influence traffic distribution using a configurable parameter called bias.

This makes geoproximity routing useful when you want more control over geographic traffic distribution than latency-based routing provides.

### 7.1 How geoproximity routing works

Route 53 considers:

* The geographic location of the user.

* The geographic location of the AWS resource.

* The configured bias value.

For AWS resources, you specify the AWS region.

For non-AWS resources, you can specify geographic coordinates.

![Geoproximity routing - Amazon Route 53](https://images.openai.com/static-rsc-4/GY1LvyUZzliVlnDKXwNv4SXKU4UnwOBljc13_Guo7Y0s0FoyuNQ17ytbjhkK33r9n1KEnk8CjrXBrTR-Yi35h-wwugC0AGtTv3UUf6qfCEhh3eO9SRjv8JdNt780eLr9Rsp0Fl35hqGdsYh4ru42WHPXkcPx8X9Yp_3PXVRPMUjWgHcEv8j2BnDcQ_ucWbO6?purpose=fullsize)

### 7.2 Understanding traffic bias

The bias parameter adjusts the geographic area from which a resource receives queries.

The supported range is:

* `-99`: Shrinks the geographic coverage area.

* `0`: Uses the default geographic coverage.

* `+99`: Expands the geographic coverage area.

For example, suppose you have two application deployments:

| Resource      | Region       | Bias |
| ------------- | ------------ | ---- |
| Application A | us-east-1    | +30  |
| Application B | eu-central-1 | 0    |

Increasing the bias for Application A expands its effective geographic coverage, potentially directing more queries toward it.

The bias is not a percentage. A bias of `+30` does not mean 30% more traffic.

### 7.3 Pulumi implementation

```python
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

us_record = aws.route53.Record(
    "us-geoproximity",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.10"],
    geoproximity_routing_policy={
        "aws_region": "us-east-1",
        "bias": 30,
    },
    set_identifier="us-geoproximity",
)

eu_record = aws.route53.Record(
    "eu-geoproximity",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.20"],
    geoproximity_routing_policy={
        "aws_region": "eu-central-1",
        "bias": 0,
    },
    set_identifier="eu-geoproximity",
)
```

### 7.4 When to use geoproximity routing

Consider geoproximity routing when:

* You operate application infrastructure in multiple geographic locations.

* You want to shift traffic toward a particular region.

* You need geographic control over traffic distribution.

* You want to adjust regional traffic distribution without changing application endpoints.

Geoproximity routing requires Route 53 Traffic Flow support for configuring the bias feature through the console's visual policy editor; the underlying geoproximity routing policy can also be managed through the Route 53 API and Pulumi.

### 8\. IP-Based Routing Policy

IP-based routing allows you to select DNS responses based on the IP address range of the DNS requester.

This is especially useful when you have information about your users' networks, ISPs, or enterprise customers.

For example:

* ISP A users → US application.

* ISP B users → European application.

* Corporate network users → Dedicated application endpoint.

### 8.1 CIDR collections

IP-based routing uses CIDR collections.

A CIDR collection contains named geographic or network locations, each associated with one or more CIDR blocks.

Example:

| Location name | CIDR            |
| ------------- | --------------- |
| isp-a         | 198.51.100.0/24 |
| isp-b         | 203.0.113.0/24  |
| corporate     | 192.0.2.0/24    |

You associate these locations with DNS records.

When a query arrives, Route 53 evaluates the requester IP against the configured CIDR blocks and selects the matching record.

![Adding Route 53 Health Checks With an ELB and Route 53 Policies - KodeKloud](https://images.openai.com/static-rsc-4/1o4XC9ugkDgZGTtSMw-ojRaEF80-o-7t_z6fPxbqlQkiV7H1h4qNbYIbDXr9sWbaj5G9iE1wtLfVsOBAG2bU4J2LtkPJT2pJjSM1AtIz9NHnYYVlCbDPQi7mj0GJBwa4lBj5DDqpFwxsbkVKIvbug_fd0DZReLbadJV0-jfxJPVG_ZmvGm0InlzAZDgOwqL1?purpose=fullsize)

### 8.2 Pulumi implementation

First, create a CIDR collection:

```python
import pulumi_aws as aws

cidr_collection = aws.route53.CidrCollection(
    "client-networks",
    name="client-networks",
)
```

Next, create locations inside the collection:

```python
isp_a = aws.route53.CidrLocation(
    "isp-a-location",
    collection_id=cidr_collection.id,
    name="isp-a",
    cidrs=["198.51.100.0/24"],
)

isp_b = aws.route53.CidrLocation(
    "isp-b-location",
    collection_id=cidr_collection.id,
    name="isp-b",
    cidrs=["203.0.113.0/24"],
)
```

Now create records using the CIDR locations:

```python
zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

record_a = aws.route53.Record(
    "isp-a-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.10"],
    cidr_routing_policy={
        "collection_id": cidr_collection.id,
        "location_name": "isp-a",
    },
    set_identifier="isp-a",
)

record_b = aws.route53.Record(
    "isp-b-record",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.20"],
    cidr_routing_policy={
        "collection_id": cidr_collection.id,
        "location_name": "isp-b",
    },
    set_identifier="isp-b",
)
```

You can also configure a default CIDR location to handle requests that do not match any configured CIDR block.

### 8.3 Important considerations

* CIDR ranges must represent the IP addresses Route 53 uses to identify DNS requesters.

* Resolver behavior and DNS proxying can affect the observed requester address.

* CIDR collections must be maintained as network allocations change.

* More-specific CIDR ranges take precedence over less-specific matching ranges.

* IP-based routing is not a firewall and does not restrict direct network access.

### 9\. Multivalue Answer Routing Policy

Multivalue answer routing allows Route 53 to return multiple DNS records in response to a query.

It can associate health checks with individual records and return only healthy endpoints when healthy records are available.

This provides basic DNS-level load distribution and improves availability.

### 9.1 How multivalue routing works

Suppose you have four application servers:

| Server   | IP address   | Health    |
| -------- | ------------ | --------- |
| Server A | 203.0.113.10 | Healthy   |
| Server B | 203.0.113.20 | Healthy   |
| Server C | 203.0.113.30 | Unhealthy |
| Server D | 203.0.113.40 | Healthy   |

Route 53 can return up to eight healthy records in response to a DNS query.

In this example, Server C is excluded.

![Adding Route 53 Health Checks With an ELB and Route 53 Policies - KodeKloud](https://images.openai.com/static-rsc-4/Ajq_UZQfPr07VYlEFmGBirLwkQWGSp6fb_21mbvCJn6o3ILUXXC_mGMf_BC3c8hKh87oeJa9BMpoPniEuTyG6IcpZrJLkoGjAp8xBjlpgQAnI5TRB3cZ57dw6De80k0JsdIbZTocEyiCPTPdOXLhXliBx5N2boFD-D11telG0giDVD58lrqw975F5DWSDIJq?purpose=fullsize)

### 9.2 Characteristics

* Supports up to eight returned healthy records.

* Can associate individual health checks with records.

* Returns different combinations of records to different DNS resolvers.

* Supports public and private hosted zones.

* Provides basic DNS-level load distribution.

If all records are unhealthy, Route 53 can still return up to eight unhealthy records.

### 9.3 Pulumi implementation

```python
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

health_a = aws.route53.HealthCheck(
    "server-a-health",
    fqdn="server-a.example.com",
    port=443,
    type="HTTPS",
    resource_path="/health",
)

health_b = aws.route53.HealthCheck(
    "server-b-health",
    fqdn="server-b.example.com",
    port=443,
    type="HTTPS",
    resource_path="/health",
)

server_a = aws.route53.Record(
    "server-a",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.10"],
    health_check_id=health_a.id,
    multivalue_answer_routing_policy=True,
    set_identifier="server-a",
)

server_b = aws.route53.Record(
    "server-b",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    ttl=60,
    records=["203.0.113.20"],
    health_check_id=health_b.id,
    multivalue_answer_routing_policy=True,
    set_identifier="server-b",
)
```

### 9.4 Multivalue routing versus load balancing

Multivalue answer routing is not a replacement for ALB or NLB.

It does not provide:

* Application-layer request distribution.

* Connection-level load balancing.

* Session persistence.

* Sophisticated target selection.

* Per-request health evaluation.

It is most appropriate for relatively simple DNS-level distribution across multiple endpoints.

### 10\. Routing Policies Versus Load Balancing

An important architectural distinction is that Route 53 performs DNS-level routing, while load balancers distribute application traffic.

### 10.1 DNS routing versus application load balancing

| Feature                       | Route 53          | ALB                    | NLB                    |
| ----------------------------- | ----------------- | ---------------------- | ---------------------- |
| DNS-based routing             | Yes               | No (uses DNS endpoint) | No (uses DNS endpoint) |
| Geographic routing            | Yes               | No                     | No                     |
| Latency-based routing         | Yes               | No                     | No                     |
| Weighted traffic distribution | Yes               | No                     | No                     |
| HTTP/HTTPS routing            | No                | Yes                    | No                     |
| TCP/UDP load balancing        | No                | No                     | Yes                    |
| Application health checks     | DNS health checks | Target health checks   | Target health checks   |
| Connection management         | No                | Yes                    | Yes                    |

### 10.2 Combining Route 53 with ALB

A common production architecture uses Route 53 to select a regional ALB, while the ALB distributes traffic among application targets.

![Amazon Route 53: The Invisible System That Decides Where the Internet Goes | by Yaswanth Reddy Arumulla | Mar, 2026 | Medium](https://images.openai.com/static-rsc-4/X8Wioisd_yVK1HpsLwo6EZd1_PYvsAXrHxA1-M6aOfW-GTkbng1rz01gn1BkKPrarqoZ4-LNBXNFZ2eIa4TNEoGZEzdYNPVZIC5uch-f0j5xCc2NuX0-x-J5MO16UyeHD_CaLRIouEeT0ZCVxNg6PvTS_StlWoQBomd6GjhSspK991UsiiiTE_hdGAksWvrZ?purpose=fullsize)

For example:

```text
                  Users
                    |
                    v
             Route 53 DNS
                    |
          Latency-based routing
              /           \
             /             \
            v               v
       US East ALB       EU ALB
            |               |
        Target Group     Target Group
         /      \         /      \
       ECS     ECS      ECS      ECS
```

This architecture provides two levels of traffic management:

* Route 53 selects the appropriate regional application endpoint.

* The regional load balancer distributes requests among healthy application targets.

This is generally preferable to exposing individual application server IP addresses through DNS.

### 11\. Routing Policy Combinations and Record Configuration

Route 53 supports several routing policies, but an individual DNS record cannot combine arbitrary routing policies.

For example, you cannot attach both weighted and latency-based routing policies to the same record.

Each routing policy has its own configuration requirements.

### 11.1 Policy configuration comparison

| Policy       | Main configuration               | Health checks                          |
| ------------ | -------------------------------- | -------------------------------------- |
| Simple       | Record values                    | Optional                               |
| Weighted     | Weight + identifier              | Optional                               |
| Latency      | AWS region + identifier          | Optional                               |
| Failover     | Primary/secondary + identifier   | Required for primary health evaluation |
| Geolocation  | Geographic location + identifier | Optional                               |
| Geoproximity | Resource location + bias         | Optional                               |
| IP-based     | CIDR collection + location       | Optional                               |
| Multivalue   | Identifier + multivalue flag     | Optional                               |

### 11.2 Combining policies architecturally

Although individual records cannot combine arbitrary policies, you can build multi-level architectures using separate DNS names.

For example:

```text
app.example.com
       |
       v
Geolocation routing
       |
       +------------------+
       |                  |
       v                  v
us.example.com       eu.example.com
       |                  |
       v                  v
Weighted routing     Failover routing
       |                  |
   +---+---+          +---+---+
   |       |          |       |
  ALB A   ALB B      ALB A   ALB B
```

This gives you flexibility to use different routing strategies at different levels.

However, additional DNS indirection introduces more complexity and can increase the number of DNS lookups.

### 11.3 Alias records with routing policies

Route 53 supports Alias records with several routing policies, including:

* Weighted.

* Latency.

* Failover.

* Geolocation.

* Geoproximity.

This is particularly useful when pointing DNS records to AWS resources such as ALBs.

For example, weighted Alias records can distribute DNS responses between two regional ALBs without hardcoding their IP addresses.

### 12\. DNS Caching and Its Impact on Routing

DNS caching is one of the most important considerations when implementing Route 53 routing policies.

A routing policy determines which DNS answer Route 53 returns, but it does not control how long clients and DNS resolvers continue using that answer.

### 12.1 Understanding TTL

TTL (Time to Live) specifies how long a DNS answer can be cached.

For example:

```text
app.example.com

A 300 203.0.113.10
```

The TTL is 300 seconds, meaning a compliant resolver can cache the answer for five minutes.

### 12.2 Why TTL matters for routing

Consider a weighted routing configuration:

```text
Application A: 90%
Application B: 10%
```

Suppose you change it to:

```text
Application A: 50%
Application B: 50%
```

Route 53 starts answering new eligible DNS queries using the updated weights.

However, resolvers that already cached previous answers can continue returning those answers until their caches expire.

Consequently, actual application traffic may not immediately reflect the new distribution.

![DNS Propagation: Why DNS Changes Take Time & How to Fix It](https://images.openai.com/static-rsc-4/05FkDZz2MHje2HJxRlVydYWEpqhS_JuHjCixjenqLxYl5XMBo5wPsHQGJscLXV4PCeLrtt0fYipp87eQ8XqPhxHoLPlfo59tlTZy4-j-1GmxjmiuHOPNqXvC-Nl89cQAN1a2OOM4IgaAG8Nbtr_5NSiFVy5EdcsFH2G7KdoGyUUJiAvx9NCUpgPIcbBMM9KF?purpose=fullsize)

### 12.3 Factors affecting DNS routing behavior

* DNS record TTL.

* Recursive resolver caching.

* Client operating system DNS caching.

* Browser DNS caching.

* DNS forwarding and proxy infrastructure.

* Application connection reuse.

* EDNS Client Subnet support and resolver behavior.

* Existing TCP and HTTP connections.

### 12.4 TTL recommendations

| Scenario                        | Example TTL     |
| ------------------------------- | --------------- |
| Frequently changing DNS records | 60 seconds      |
| Blue-green deployment           | 60–120 seconds  |
| Regional failover               | 60 seconds      |
| Stable production endpoints     | 300–900 seconds |
| Rarely changing records         | 3600 seconds    |

These are starting points, not universal recommendations.

Lower TTLs can improve DNS change responsiveness, but they can also increase DNS query volume.

Important: TTL does not guarantee failover within the same number of seconds. Health-check detection, DNS resolver caching, client behavior, and application connections all affect recovery time.

### 13\. Choosing the Right Routing Policy

Selecting a routing policy depends on your application's architecture and traffic-management requirements.

| Requirement                                          | Recommended policy |
| ---------------------------------------------------- | ------------------ |
| Single application endpoint                          | Simple             |
| Gradual traffic shifting                             | Weighted           |
| Global application with multiple AWS regions         | Latency-based      |
| Disaster recovery                                    | Failover           |
| Country-specific traffic distribution                | Geolocation        |
| Geographic traffic optimization with adjustable bias | Geoproximity       |
| Routing based on known client networks               | IP-based           |
| Returning multiple healthy server addresses          | Multivalue answer  |

### 13.1 Practical architecture examples

Scenario A — Blue-green deployment

You have two application versions running behind separate ALBs.

Use weighted routing to gradually move traffic from the old version to the new version.

Scenario B — Global SaaS platform

Your application runs in three AWS regions.

Use latency-based routing to direct users toward the region with the best measured network latency.

Scenario C — Disaster recovery

Your primary application runs in one region, with a backup deployment in another.

Use failover routing with health checks.

Scenario D — Regional content delivery

You want European users to reach European application infrastructure and Asian users to reach Asian infrastructure.

Use geolocation routing.

Scenario E — ISP optimization

You know which IP ranges belong to specific ISPs and want to optimize their traffic paths.

Use IP-based routing with CIDR collections.

Scenario F — Geographic traffic balancing

You want to expand or shrink the geographic coverage of specific application regions.

Use geoproximity routing with bias.

### Hands-on Labs

The labs below use Pulumi Python, AWS CLI v2, and Bash. They assume you already have a public hosted zone and a working Pulumi AWS project.

### Lab 1 — Configure Simple Routing for a Web Application

Objective: Create a basic DNS record pointing to a web application endpoint.

### Step 1: Configure the Pulumi project

```bash
mkdir route53-simple
cd route53-simple

pulumi new aws-python
```

Configure your AWS region:

```bash
pulumi config set aws:region us-east-1
```

### Step 2: Create the DNS record

Use the simple routing implementation from Section 2.

Configure your existing domain:

```bash
pulumi config set domain example.com
```

For a reusable project, retrieve the domain from configuration:

```python
config = pulumi.Config()

domain = config.require("domain")

zone = aws.route53.get_zone(
    name=domain,
    private_zone=False
)
```

### Step 3: Deploy

```bash
pulumi preview
pulumi up
```

### Step 4: Verify DNS resolution

```bash
dig app.example.com

dig app.example.com A

dig +short app.example.com
```

Inspect the authoritative name servers:

```bash
dig NS example.com
```

Expected result: The hostname resolves to the configured application endpoint.

### Lab 2 — Implement Weighted Routing Between Two ALBs

Objective: Distribute DNS responses between two Application Load Balancers.

![Adding Route 53 Health Checks With an ELB and Route 53 Policies - KodeKloud](https://images.openai.com/static-rsc-4/tIHQjTYxEVcfGSYVqHpPrETDyooYD5Y5S4mw6UyOxZGFKiR-O_t_nsVvKkElHDcwBaffPxwuFEqSjb0dG5BbCyTq-6AiJJwN7Lfw82na-iPUSJ0gmTYpjCatihkWo0qiQa68jPcZabj8MVQGcv2CEIahW_JEYAPR0B9Y-Mpwd5Y75UZx5GzmLaq3dFpR2FAQ?purpose=fullsize)

### Step 1: Prepare the infrastructure

Deploy two ALBs in the same or different AWS regions.

For this lab, assume you already have:

```text
ALB A: app-a.example.com
ALB B: app-b.example.com
```

Retrieve their DNS names and hosted-zone IDs:

```bash
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[*].[DNSName,CanonicalHostedZoneId]' \
  --output table
```

### Step 2: Create weighted Alias records

Use the `aliases` property instead of hardcoded IP addresses.

```python
record_a = aws.route53.Record(
    "weighted-alb-a",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    aliases=[
        {
            "name": alb_a_dns,
            "zone_id": alb_a_zone_id,
            "evaluate_target_health": True,
        }
    ],
    weighted_routing_policies=[
        {
            "weight": 80
        }
    ],
    set_identifier="alb-a",
)

record_b = aws.route53.Record(
    "weighted-alb-b",
    zone_id=zone.zone_id,
    name="app.example.com",
    type="A",
    aliases=[
        {
            "name": alb_b_dns,
            "zone_id": alb_b_zone_id,
            "evaluate_target_health": True,
        }
    ],
    weighted_routing_policies=[
        {
            "weight": 20
        }
    ],
    set_identifier="alb-b",
)
```

The example assumes `alb_a_dns`, `alb_a_zone_id`, `alb_b_dns`, and `alb_b_zone_id` are obtained from the ALB resources or stack outputs.

### Step 3: Deploy and inspect

```bash
pulumi preview
pulumi up
```

Query DNS repeatedly:

```bash
for i in {1..20}; do
    dig +short app.example.com
    sleep 1
done
```

Remember that resolver caching can make repeated queries return the same result.

Expected result: Route 53 returns DNS answers according to the configured weights, subject to resolver caching and health evaluation.

### Lab 3 — Perform Gradual Traffic Shifting Using Weighted Records

Objective: Implement a controlled blue-green deployment.

Assume:

* Blue environment: Existing application.

* Green environment: New application.

Start with:

| Environment | Weight |
| ----------- | ------ |
| Blue        | 100    |
| Green       | 0      |

Gradually change the distribution:

Traffic shifting strategy

Initial

100% / 0%

Blue / Green

Canary

90% / 10%

Blue / Green

Expansion

75% / 25%

Blue / Green

Halfway

50% / 50%

Blue / Green

Final

0% / 100%

Blue / Green

### Step 1: Configure Pulumi

Create two weighted records with configurable weights:

```python
config = pulumi.Config()

blue_weight = config.get_int("blueWeight") or 100
green_weight = config.get_int("greenWeight") or 0
```

Use these values in the two weighted routing policies.

### Step 2: Deploy initial configuration

```bash
pulumi config set blueWeight 100
pulumi config set greenWeight 0

pulumi up
```

### Step 3: Shift traffic

```bash
pulumi config set blueWeight 90
pulumi config set greenWeight 10

pulumi up
```

Continue with:

```bash
pulumi config set blueWeight 75
pulumi config set greenWeight 25

pulumi up
```

Then:

```bash
pulumi config set blueWeight 50
pulumi config set greenWeight 50

pulumi up
```

Finally:

```bash
pulumi config set blueWeight 0
pulumi config set greenWeight 100

pulumi up
```

### Step 4: Observe the application

Monitor:

* ALB request counts.

* HTTP error rates.

* Application latency.

* Target group health.

* CloudWatch application metrics.

Expected result: You can progressively shift DNS responses from the blue environment to the green environment.

### Lab 4 — Configure Latency-Based Routing Across AWS Regions

Objective: Route users toward regional application endpoints based on AWS latency measurements.

### Step 1: Prepare regional infrastructure

Deploy two application environments:

```text
us-east-1
  └── ALB: us-app.example.com

eu-central-1
  └── ALB: eu-app.example.com
```

### Step 2: Create latency-based Alias records

```python
us_record = aws.route53.Record(
    "us-latency-record",
    zone_id=zone.zone_id,
    name="global.example.com",
    type="A",
    aliases=[{
        "name": us_alb_dns,
        "zone_id": us_alb_zone_id,
        "evaluate_target_health": True,
    }],
    latency_routing_policies=[{
        "region": "us-east-1"
    }],
    set_identifier="us-east",
)

eu_record = aws.route53.Record(
    "eu-latency-record",
    zone_id=zone.zone_id,
    name="global.example.com",
    type="A",
    aliases=[{
        "name": eu_alb_dns,
        "zone_id": eu_alb_zone_id,
        "evaluate_target_health": True,
    }],
    latency_routing_policies=[{
        "region": "eu-central-1"
    }],
    set_identifier="eu-central",
)
```

### Step 3: Deploy and verify

```bash
pulumi up

dig global.example.com
dig global.example.com A
```

Repeat DNS queries from different geographic locations.

You can use EC2 instances in different AWS regions as DNS test clients.

Expected result: Route 53 selects the regional endpoint according to its latency measurements.

### Lab 5 — Implement Primary/Secondary Failover Routing

Objective: Build a basic disaster recovery DNS architecture.

### Step 1: Prepare two application endpoints

```text
Primary:
  us-east-1
  primary.example.com

Secondary:
  eu-central-1
  secondary.example.com
```

### Step 2: Create a health check

```python
health = aws.route53.HealthCheck(
    "primary-health",
    fqdn="primary.example.com",
    port=443,
    type="HTTPS",
    resource_path="/health",
    request_interval=30,
    failure_threshold=3,
)
```

### Step 3: Configure primary and secondary records

Use the failover implementation from Section 5, preferably with Alias records pointing to the regional ALBs.

### Step 4: Simulate failure

Stop the primary application's health endpoint or configure it to return an unsuccessful response.

Inspect the health check:

```bash
aws route53 get-health-check-status \
  --health-check-id YOUR_HEALTH_CHECK_ID
```

Inspect DNS:

```bash
dig app.example.com
```

Expected result: Once the primary health check is evaluated as unhealthy, Route 53 directs eligible DNS queries toward the secondary endpoint.

Restore the primary application and observe recovery behavior.

### Lab 6 — Configure Geolocation Routing

Objective: Route users from different continents toward different application endpoints.

### Step 1: Prepare three endpoints

```text
North America → US application
Europe        → EU application
Asia          → Singapore application
```

### Step 2: Create geolocation records

Use the implementation from Section 6.

Configure:

```python
geolocation_routing_policies=[
    {"continent": "NA"}
]
```

For Europe:

```python
geolocation_routing_policies=[
    {"continent": "EU"}
]
```

For Asia:

```python
geolocation_routing_policies=[
    {"continent": "AS"}
]
```

Create a default record as well.

### Step 3: Test geographic responses

From test machines in different geographic locations:

```bash
dig app.example.com
```

Use EC2 instances in different regions or external DNS testing locations.

Expected result: Route 53 returns the endpoint associated with the geographic location it identifies for the DNS requester.

### Lab 7 — Experiment with Geoproximity Routing and Traffic Bias

Objective: Configure geographic routing and observe how bias influences endpoint selection.

### Step 1: Prepare regional endpoints

Use:

* US East.

* Europe (Frankfurt).

* Asia Pacific (Singapore).

### Step 2: Configure geoproximity records

Use the Pulumi implementation from Section 7.

Start with:

```python
"bias": 0
```

Deploy the infrastructure.

### Step 3: Adjust bias

For example:

```python
"bias": 30
```

Then experiment with:

```python
"bias": -30
```

### Step 4: Observe routing behavior

Test DNS resolution from multiple geographic locations.

Compare the responses before and after changing the bias.

Expected result: You observe how changing the bias modifies the geographic coverage of each endpoint.

### Lab 8 — Implement IP-Based Routing Using CIDR Collections

Objective: Direct DNS requests based on predefined client IP ranges.

### Step 1: Create a CIDR collection

Use the `CidrCollection` and `CidrLocation` resources from Section 8.

Configure example networks:

```python
cidrs=["198.51.100.0/24"]
```

```python
cidrs=["203.0.113.0/24"]
```

These are documentation-only IP ranges. Replace them with actual network ranges under your control for a real deployment.

### Step 2: Create routing records

Create one record per CIDR location, referencing the same collection.

Add a default CIDR location for unmatched requests.

### Step 3: Test routing

You can inspect the configured collection:

```bash
aws route53 list-cidr-collections
```

Inspect its locations:

```bash
aws route53 list-cidr-locations \
  --collection-id YOUR_COLLECTION_ID
```

To test actual IP-based routing, send DNS queries through resolvers whose source IP addresses fall within your configured CIDR ranges.

Expected result: Requests identified with different configured CIDR locations receive their corresponding DNS answers.

### Lab 9 — Compare DNS Responses Across Routing Policies Using `dig`

Objective: Understand how different routing policies influence DNS responses.

Create separate test hostnames:

| Hostname              | Routing policy |
| --------------------- | -------------- |
| simple.example.com    | Simple         |
| weighted.example.com  | Weighted       |
| latency.example.com   | Latency        |
| failover.example.com  | Failover       |
| geo.example.com       | Geolocation    |
| proximity.example.com | Geoproximity   |
| ip.example.com        | IP-based       |
| multi.example.com     | Multivalue     |

### Step 1: Inspect DNS answers

```bash
dig simple.example.com A

dig weighted.example.com A

dig latency.example.com A

dig failover.example.com A
```

### Step 2: Inspect response details

```bash
dig weighted.example.com A +noall +answer

dig weighted.example.com A +stats

dig weighted.example.com A +trace
```

### Step 3: Query different DNS resolvers

```bash
dig @1.1.1.1 weighted.example.com A

dig @8.8.8.8 weighted.example.com A
```

Different resolvers may return different answers, but caching can affect the observed results.

### Step 4: Compare TTL values

```bash
dig weighted.example.com A +noall +answer
```

Observe the TTL values and how they change as cached answers age.

### Step 5: Build a Bash diagnostic script

```bash
#!/usr/bin/env bash

set -euo pipefail

HOSTNAMES=(
    simple.example.com
    weighted.example.com
    latency.example.com
    failover.example.com
    geo.example.com
    proximity.example.com
    ip.example.com
    multi.example.com
)

for hostname in "${HOSTNAMES[@]}"; do
    echo "=================================="
    echo "Hostname: $hostname"
    echo "=================================="

    dig "$hostname" A +noall +answer

    echo
done
```

Run it:

```bash
chmod +x dns-check.sh

./dns-check.sh
```

Expected result: You can inspect and compare DNS answers, TTLs, and routing behavior across all eight routing policies.

### 14\. Important Operational Considerations

Before using Route 53 routing policies in production, keep these points in mind:

* DNS routing is not request routing. Route 53 selects DNS answers, not individual HTTP requests.

* TTL affects traffic transitions. Cached DNS responses can delay the effect of routing changes.

* Health checks have detection delays. DNS failover is not instantaneous.

* Resolver location matters. The DNS resolver's location can differ from the end user's location.

* Weighted routing is approximate. Configured weights do not guarantee exact application request percentages.

* Geolocation is not access control. Use appropriate security controls for geographic restrictions.

* Failover requires application readiness. DNS switching alone does not provide disaster recovery.

* Monitor actual application traffic. Use ALB metrics and application telemetry to validate routing behavior.

### 15\. Official Documentation and References

These resources are particularly useful when implementing the module's Pulumi projects:

* [Choosing a Route 53 Routing Policy](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy.html?icmpid=docs_console_unmapped&utm_source=chatgpt.com) — AWS documentation covering routing policy selection.

* [Geolocation Routing](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-geo.html?utm_source=chatgpt.com) — Geographic routing configuration and default records.

* [IP-Based Routing](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-ipbased.html?utm_source=chatgpt.com) — CIDR collections and IP-based routing.

* [Multivalue Answer Routing](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/routing-policy-multivalue.html?utm_source=chatgpt.com) — Health checks and multiple DNS answers.

* [Pulumi AWS Route 53 Record](https://www.pulumi.com/registry/packages/aws/api-docs/route53/record/?utm_source=chatgpt.com) — Pulumi resource properties and Python configuration.

### Module 3 — Completion Summary

By the end of this module, you should understand:

* How all eight Route 53 routing policies work.

* How to implement routing policies using Pulumi Python.

* How to distribute traffic across multiple ALBs.

* How to build multi-region DNS architectures.

* How to implement DNS-based disaster recovery.

* How to control geographic and network-based routing.

* How DNS caching affects routing behavior.

* How to troubleshoot DNS responses using `dig` and Bash.

Next module: Module 4 — Route 53 Health Checks and DNS Failover.
