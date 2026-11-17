### Module 7 — Route 53 Traffic Management and Advanced Architectures

### 1\. Introduction to Route 53 Traffic Management

So far, we've covered DNS records, routing policies, health checks, private hosted zones, and DNS security.

Now we'll bring these concepts together to design production-grade DNS architectures.

The central idea is that Route 53 can make intelligent DNS-based traffic decisions based on the location, latency, health, and weight of your application endpoints.

Imagine you operate an application in three AWS regions:

* `us-east-1` — North Virginia

* `eu-west-1` — Ireland

* `ap-southeast-1` — Singapore

Your users are distributed globally.

You want:

* US users to reach the US region.

* European users to reach the European region.

* Asian users to reach the Singapore region.

* Traffic to automatically move away from unhealthy regions.

* New application versions to receive traffic gradually.

* A backup region to become active when the primary region fails.

Route 53 can implement these behaviors using DNS routing policies.

![Amazon Route 53: The Invisible System That Decides Where the Internet Goes | by Yaswanth Reddy Arumulla | Mar, 2026 | Medium](https://images.openai.com/static-rsc-4/LyLdwSYGdYX19hWtzVKTO1iPBVTRDCmVwNFHQKJh1wasUtZ1J1P7EIsne9KvnxbV65xspSJk7o3kqJ5s3NP2RC_SiGTPS4IZGmc7iyHiKvOoxnQfz10Mhhsi8B4LUzCf0laS4jaSfjok00922GwFvaOjbKGNA1nssm_rA1COQZVectqk6uoysgkmZdWggFJy?purpose=fullsize)

### 1.1 DNS-based traffic management

Traditional DNS simply resolves a domain name into an IP address or another DNS target.

For example:

```text
api.example.com
       |
       v
   DNS lookup
       |
       v
203.0.113.10
```

Route 53 adds decision-making capabilities.

Instead of always returning the same endpoint, it evaluates routing policies and associated information before returning an answer.

For example:

```text
                 api.example.com
                        |
                        v
                  Amazon Route 53
                        |
             +----------+----------+
             |          |          |
             v          v          v
          US-East     EU-West    Singapore
             |          |          |
             v          v          v
            ALB        ALB        ALB
             |          |          |
             v          v          v
          App-US     App-EU     App-Asia
```

The DNS response depends on the routing configuration.

One important distinction:

Route 53 does not proxy application traffic.

It returns DNS answers. After DNS resolution, the client connects directly to the selected endpoint.

This has several consequences:

* Route 53 doesn't inspect HTTP requests.

* Route 53 doesn't distribute individual requests across servers.

* Route 53 doesn't maintain application sessions.

* DNS caching can delay the effect of routing changes.

* The client or its recursive resolver may continue using a cached DNS answer.

This is why Route 53 traffic management and application load balancing solve different problems.

| Route 53                                | Application Load Balancer                       |
| --------------------------------------- | ----------------------------------------------- |
| Operates at DNS resolution time         | Operates at HTTP/HTTPS request time             |
| Selects DNS endpoints                   | Selects application targets                     |
| Can route across regions                | Primarily distributes traffic within its region |
| Influenced by DNS caching               | Evaluates incoming requests                     |
| Supports geographic and latency routing | Supports path-, host-, and header-based routing |

### 1.2 Routing policy versus Traffic Flow

Route 53 offers two related approaches to traffic management:

* Standard DNS routing policies.

* Route 53 Traffic Flow.

Standard routing policies are configured directly on DNS records.

Traffic Flow provides a visual policy-management system that allows you to build more complex routing configurations.

We'll examine both approaches in this module.

### 2\. Route 53 Traffic Flow

### 2.1 What is Traffic Flow?

is a Route 53 feature for creating and managing sophisticated DNS traffic-routing configurations.

Instead of manually configuring multiple DNS records and their relationships, you can define a traffic policy that describes how DNS queries should be routed.

For example, consider this requirement:

* Route users to the region with the lowest latency.

* Use weighted routing to distribute traffic between two application versions.

* If the selected region becomes unhealthy, route users to another region.

Implementing this with individual records requires careful configuration.

Traffic Flow lets you express the routing logic as a policy tree.

### 2.2 Traffic Flow policy architecture

A Traffic Flow policy consists of routing rules and endpoint definitions.

A simplified policy might look like this:

![Multi-region Traffic Engineering](https://images.openai.com/static-rsc-4/0xIjPEzx1h_Yg_KrNyLuIsZSx4nWocZ6gs8sHwm8vcAUg-QBHydXLgwRsJE_r3iYC_MR_xQISgJganb8yyj8QZf5q_GSCeKmF662dG4rI-8NmVTLcbCVfwpRSpFY9_xZ-T2TD6SJodr-yV7xkitJhJlQU4CTOxom-L-AsOPl_x-R5r2Nel2udZM13RbQFRDp?purpose=fullsize)

```text
                 DNS Query
                     |
                     v
              Latency Routing
                     |
          +----------+----------+
          |                     |
          v                     v
       US Region             EU Region
          |                     |
          v                     v
     Weighted Routing      Weighted Routing
       /       \              /       \
      v         v            v         v
   Version A Version B    Version A Version B
```

The policy can combine different routing strategies.

For example:

* Latency routing chooses a region.

* Weighted routing distributes traffic between application versions.

* Failover routing provides a backup endpoint.

### 2.3 Traffic Flow components

The main components are:

Traffic policy

Defines the complete DNS routing logic.

Policy version

A saved version of a traffic policy. You can create new versions while retaining earlier versions.

Endpoint

Represents a destination for traffic, such as an ALB, CloudFront distribution, or another DNS endpoint.

Policy record

A DNS record created by applying a traffic policy to a specific DNS name and hosted zone.

### 2.4 Traffic Flow policy versions

Traffic Flow supports versioning.

Suppose your application initially uses:

```text
Policy Version 1

US: 100%
EU: 0%
```

You then introduce a European deployment:

```text
Policy Version 2

US: 70%
EU: 30%
```

Later, you change the policy:

```text
Policy Version 3

US: 50%
EU: 50%
```

You can retain previous policy versions for reference and create new policy records from newer versions.

Important distinction:

Traffic policy versioning is not the same as Pulumi state versioning or Git version control.

Traffic Flow versions describe DNS traffic-routing configurations.

Pulumi manages the infrastructure resources and their desired configuration.

Git manages your source code and configuration history.

### 2.5 Traffic Flow pricing consideration

Traffic Flow is a separately priced Route 53 capability.

Creating and maintaining traffic policies and policy records can incur additional charges.

For simple routing requirements, standard Route 53 records are often sufficient.

Use Traffic Flow when the complexity of your routing policy justifies its additional management capabilities and cost.

### 3\. DNS-Based Traffic Management Across Multiple AWS Regions

Multi-region DNS management is one of the most important Route 53 use cases.

A multi-region architecture deploys application infrastructure in multiple AWS regions to improve availability, reduce latency, and support disaster recovery.

### 3.1 Why multiple regions?

Consider a SaaS application hosted exclusively in `us-east-1`.

If the region experiences a significant outage, your application may become unavailable globally.

A multi-region deployment reduces this dependency.

For example:

![Configuring Route53 for Automatic Failover - Cori Amer - Senior Technical Communicator](https://images.openai.com/static-rsc-4/2qeZcUPiXvnPwX0ADpgYAK4jXoIGo_nSN85OWmIeeaZU0TvMQhLcwQyWLQ7SZfsCwThUhtIbabNVXmVm4pR7GtL-6DUVoYS7dgkoFnVeGoUMu_qIfI-cclfD5NhM-0miEkWuIo6EphbZqtlCK6w5rWtFVolifcERV_s-9XK5OJiPbxS4guZ9he9iOBTYnshy?purpose=fullsize)

```text
                 api.example.com
                        |
                        v
                   Route 53
                        |
           +------------+------------+
           |            |            |
           v            v            v
        US-East       EU-West     AP-Southeast
           |            |            |
           v            v            v
          ALB          ALB          ALB
           |            |            |
           v            v            v
         ECS          ECS          ECS
```

Each region has its own application infrastructure.

Route 53 determines which regional endpoint should be returned to DNS clients.

### 3.2 Latency-based routing

Latency-based routing attempts to direct users to the AWS region that provides the lowest network latency.

For example:

| User location | Selected region |
| ------------- | --------------- |
| New York      | US-East         |
| London        | EU-West         |
| Singapore     | AP-Southeast    |

Route 53 uses AWS-maintained latency information to make these decisions.

It does not simply choose the geographically closest region.

Network latency depends on several factors, including:

* Network topology.

* Internet routing.

* ISP connectivity.

* Regional network performance.

Important: Latency-based routing does not measure the current latency of your application for every DNS query. It uses AWS's latency data and the available routing configuration.

### 3.3 Regional endpoint configuration

Each region needs an endpoint.

For an ALB-based application, the endpoints might be:

```text
us-east-1:
app-us.example.com

eu-west-1:
app-eu.example.com

ap-southeast-1:
app-asia.example.com
```

You can configure latency-based records for a shared DNS name:

```text
api.example.com
```

Each record has:

* The same DNS name.

* The same record type.

* A different AWS region.

* A region-specific endpoint.

* A unique set identifier.

Conceptually:

```text
api.example.com
    |
    +-- us-east-1 --> ALB-US
    |
    +-- eu-west-1 --> ALB-EU
    |
    +-- ap-southeast-1 --> ALB-ASIA
```

This allows Route 53 to select a regional endpoint according to its latency-routing logic.

### 3.4 Health checks and regional availability

Latency routing alone does not guarantee application availability.

Suppose the Singapore region experiences an application failure.

If you have not configured health-based routing behavior, Route 53 might continue returning its endpoint.

You can associate health checks with routing records.

Conceptually:

```text
             Route 53
                 |
       +---------+---------+
       |         |         |
       v         v         v
      US        EU       Singapore
       |         |         |
       v         v         v
     Healthy   Healthy   Unhealthy
       |         |         |
       +---------+---------+
                 |
                 v
          Available regions
```

For latency-based routing, unhealthy records can be excluded from eligible answers when the appropriate health-check configuration is used.

However, health checks must accurately represent application availability. A healthy ALB does not necessarily mean every application dependency is healthy.

### 4\. Combining Latency, Weighted, Geolocation, and Failover Routing

One of Route 53's most powerful capabilities is combining routing strategies to implement sophisticated traffic-management architectures.

Let's examine how these policies can work together.

### 4.1 Combining latency and weighted routing

Suppose you operate two regions:

* US-East

* EU-West

Each region has two application versions:

* Version A: stable production release.

* Version B: new release.

You want users to reach the lowest-latency region, but you also want to distribute traffic between application versions.

The architecture looks like this:

![Como as verificações de integridade funcionam com as configurações complexas do Amazon Route 53 - Amazon Route 53](https://images.openai.com/static-rsc-4/k0bSgbDU3HoYKFFW8wlvmlpfprzf4GkdTtmK5Vz9N7n7l9woMsK-T_hPHQE3kuSf5uX0fAQ98NM-ZkOno37PVyypaz_8F2Xq_go1v7X9noFffeg_A-9bj7dwogegggjmysg-I17tcv1nj7FvZFWQOS4RgYwjkKSBISgiTlnP9N8x7kb9-5_AN76LaD2V6SQn?purpose=fullsize)

Conceptually:

```text
                  Route 53
                      |
                      v
               Latency Routing
                 /        \
                v          v
             US-East     EU-West
                |          |
                v          v
             Weighted   Weighted
              Routing    Routing
              /   \      /   \
             v     v    v     v
           A 90% B 10% A 90% B 10%
```

The desired distribution is:

| Region  | Version A | Version B |
| ------- | --------- | --------- |
| US-East | 90%       | 10%       |
| EU-West | 90%       | 10%       |

This architecture is useful for gradual releases.

For example, you can initially send 5% of eligible DNS responses to Version B, monitor the deployment, and gradually increase its weight.

Important implementation detail: Standard Route 53 DNS records do not allow arbitrary nesting of routing policies. You cannot simply create a latency record whose child is another weighted record.

For complex combinations, use Route 53 Traffic Flow, which supports policy trees.

Also, DNS weights are not exact HTTP request percentages. DNS caching, recursive resolvers, client behavior, and query distribution affect actual traffic.

### 4.2 Combining geolocation and failover

Suppose you want:

* North American users to use US-East.

* European users to use EU-West.

* Asian users to use Singapore.

* Users to fall back to a backup endpoint if their regional endpoint becomes unhealthy.

A Traffic Flow policy can represent this logic:

```text
                  DNS Query
                      |
                      v
                Geolocation
                      |
          +-----------+-----------+
          |           |           |
          v           v           v
       America      Europe       Asia
          |           |           |
          v           v           v
       Failover    Failover     Failover
        /   \       /   \       /   \
       v     v     v     v     v     v
     Primary Backup Primary Backup Primary Backup
```

This is particularly useful for applications with geographic requirements.

One consideration: geolocation routing is based on the location information available to Route 53, not necessarily the physical location of the end user. Recursive DNS resolvers can influence the location information unless EDNS Client Subnet information is available.

### 4.3 Routing policy selection

| Requirement                           | Recommended policy |
| ------------------------------------- | ------------------ |
| Return one endpoint                   | Simple             |
| Distribute traffic by weights         | Weighted           |
| Choose a low-latency AWS region       | Latency            |
| Route based on geographic location    | Geolocation        |
| Route based on network proximity      | Geoproximity       |
| Provide primary/secondary DNS answers | Failover           |
| Return multiple healthy endpoints     | Multivalue answer  |
| Route based on client IP ranges       | IP-based           |

For complex combinations, consider Traffic Flow.

### 4.4 DNS routing is not application-level routing

Consider this configuration:

```text
api.example.com
       |
       v
    Route 53
       |
       v
     ALB-US
       |
       v
   Application
```

Route 53 chooses the ALB.

Once the client connects to the ALB, Route 53 no longer controls the individual HTTP requests.

If you need to route requests based on:

* HTTP paths.

* Host headers.

* Cookies.

* HTTP headers.

* Application-level information.

Use an application load balancer or another application-layer routing component.

This distinction becomes particularly important when designing blue-green deployments.

### 5\. Multi-Region Application Architectures

A multi-region architecture deploys application components in multiple geographical AWS regions.

The goal is to improve availability, performance, and disaster recovery.

There are two fundamental deployment models.

### 5.1 Active-active architecture

In an active-active architecture, multiple regions serve application traffic simultaneously.

![Building an Active-Active Multi-Region SaaS Architecture on AWS ECS & Fargate | by Lakindu Gunasekara | Medium](https://images.openai.com/static-rsc-4/vhpKJlhRfLCUKsdKOnsqld8HTrh2KCJSLdRM_mxTfU8Ys9HO7gyBfOSE-oQEMyMlNmXVUBWoNmVOSMkfnnsDUwG2qcZrxMJ-vJlA2hbzrxOcIW7wIZXazjvi2a4eOIUWHT2SuLXTlM0Odpw4vnj29jwf_G_jaOoZUqdWZx-9k2ZmpA6dgM7I1tOzvY8L4ePF?purpose=fullsize)

```text
                   Route 53
                       |
              +--------+--------+
              |                 |
              v                 v
           US-East            EU-West
              |                 |
              v                 v
             ALB               ALB
              |                 |
              v                 v
             ECS               ECS
              |                 |
              +--------+--------+
                       |
                  Data Layer
```

Both regions actively serve users.

Advantages:

* Better geographic distribution.

* Reduced latency for global users.

* Better utilization of regional infrastructure.

* Continued service availability when one region fails, assuming the surviving region has sufficient capacity.

Challenges:

* Cross-region data consistency.

* Database replication.

* Conflict resolution.

* Session management.

* Duplicate processing of asynchronous events.

* More complicated deployment and operational procedures.

For example, imagine a user updates their profile through the US region.

If the same user immediately accesses the application through Europe, the European region must have access to the updated data.

This requires an appropriate data architecture.

Possible AWS technologies include:

* Amazon DynamoDB Global Tables.

* Amazon Aurora Global Database.

* Amazon S3 Cross-Region Replication.

* Application-level replication mechanisms.

Not every application needs synchronous cross-region writes. Some can tolerate eventual consistency.

### 5.2 Active-passive architecture

In an active-passive architecture, one region handles normal production traffic while another region remains available as a standby.

![Creating Disaster Recovery Mechanisms Using Amazon Route 53 | Networking & Content Delivery](https://images.openai.com/static-rsc-4/K9gy_lfmzCuNfiRX865gs83lar0dXDnLrxaJDFU2LW3mg433G1vQKCFVJqCt2r23KfBPPR6n683qCK_uwQjfzz21XIEUIwH7hr7yj2-ArdkjF74-b4gANX2AqIQfcUDrqzIGXOiyI20CayPK60PFHal7wcQQMbtodUZ4wfgqaz-iUDQP822A55uUw3G55RPx?purpose=fullsize)

```text
                  Route 53
                      |
                      v
                 Health Check
                      |
             +--------+--------+
             |                 |
             v                 v
          Primary            Secondary
          US-East            EU-West
             |                 |
             v                 v
            ALB               ALB
             |                 |
             v                 v
        Application        Standby App
```

Normally:

```text
api.example.com --> US-East
```

If the primary region becomes unhealthy:

```text
api.example.com --> EU-West
```

The secondary region becomes the destination for new DNS resolutions.

Advantages:

* Simpler application deployment.

* Potentially lower operating costs.

* Easier operational control.

* Useful for disaster recovery.

Challenges:

* Failover delay.

* Standby capacity.

* Data replication lag.

* Database promotion or recovery.

* DNS caching.

* Failback procedures.

### 5.3 Active-active versus active-passive

| Characteristic          | Active-active                          | Active-passive                |
| ----------------------- | -------------------------------------- | ----------------------------- |
| Regions serving traffic | Multiple                               | Normally one                  |
| Resource utilization    | Higher                                 | Potentially lower             |
| Complexity              | Higher                                 | Usually lower                 |
| Failover                | Traffic shifts away from failed region | Standby takes over            |
| Data synchronization    | Often more complicated                 | Depends on replication design |
| Typical use             | Global applications                    | Disaster recovery             |

### 5.4 Disaster recovery strategies

AWS commonly discusses four disaster recovery strategies:

* Backup and restore.

* Pilot light.

* Warm standby.

* Multi-site active-active.

Route 53 can participate in the DNS traffic-management part of these architectures.

However, DNS failover alone does not implement disaster recovery.

A complete solution also needs:

* Application infrastructure recovery.

* Database recovery.

* Data replication.

* Secrets and configuration availability.

* Network connectivity.

* Operational procedures.

### 5.5 RTO and RPO

Two important disaster recovery concepts:

RTO — Recovery Time Objective

The maximum acceptable time required to restore the application.

RPO — Recovery Point Objective

The maximum acceptable amount of data loss measured in time.

Example:

```text
RTO = 15 minutes
RPO = 5 minutes
```

This means:

* The application should recover within 15 minutes.

* The recovered application should lose no more than approximately 5 minutes of data.

Route 53 can help redirect traffic, but it cannot guarantee these objectives by itself.

### 5.6 DNS failover limitations

Suppose Route 53 detects that the primary region is unhealthy and begins returning the secondary endpoint.

Some users may still reach the primary region because:

* Their recursive resolver cached the old DNS answer.

* Their operating system cached the answer.

* Their application maintains an existing connection.

* Their client does not perform another DNS lookup immediately.

Therefore:

A DNS failover event does not instantly terminate existing connections or redirect every active client.

This is an important production consideration.

### 6\. Integration with ALB, NLB, CloudFront, API Gateway, and S3

Route 53 can integrate with several AWS services through Alias records.

An Alias record is an AWS-specific DNS record capability that allows you to point a DNS name to supported AWS resources.

Unlike a conventional CNAME, Alias records can be used at the zone apex.

For example:

```text
example.com
```

You cannot create a conventional CNAME at the zone apex, but you can create an Alias A record pointing to a supported AWS resource.

### 6.1 Route 53 and Application Load Balancer

![aws-route53-alb - AWS Solutions Constructs](https://images.openai.com/static-rsc-4/5xrrYuT8qTREh0Z6Z--Ti10Ydor5sLPxmgsxReOIVh1ZeCA2QjT_frc_RNyGIgMWnuJZjC-csgxXu9eNYGCqDftNwra2fQ-tCH0uoMkCXPBFtofeTWvdE6VuGDm0OnYkaMWtfHJzIrjklparTHjBs-FBxrq-Itq9wt7cSPEHZxOf3x0KY4kyy-_gtCNp9G4-?purpose=fullsize)

An ALB is commonly used as the entry point for regional web applications.

Example:

```text
api.example.com
       |
       v
    Route 53
       |
       v
      ALB
       |
       v
   Target Group
       |
       v
   ECS / EC2
```

You can create an Alias A record pointing to an ALB.

Example Pulumi configuration:

```python
import pulumi
import pulumi_aws as aws

zone = aws.route53.get_zone(
    name="example.com",
    private_zone=False
)

alb = aws.lb.get_load_balancer(
    name="production-alb"
)

record = aws.route53.Record(
    "api-record",
    zone_id=zone.zone_id,
    name="api.example.com",
    type="A",
    aliases=[{
        "name": alb.dns_name,
        "zone_id": alb.zone_id,
        "evaluate_target_health": True,
    }]
)
```

Here:

* `zone_id` identifies the hosted zone.

* `name` is the DNS name.

* `type` is A.

* `aliases` contains the ALB DNS target.

* `evaluate_target_health` enables Route 53 to consider the target's health when supported by the routing configuration.

Notice that we don't need to hardcode the ALB's DNS name.

Pulumi retrieves the existing ALB information and uses its attributes.

Important: `evaluate_target_health` is not a substitute for an application-specific health check. It evaluates AWS target health according to Route 53's supported behavior.

### 6.2 Route 53 and Network Load Balancer

NLB is commonly used for:

* TCP applications.

* TLS termination.

* UDP services.

* High-performance network workloads.

* Applications requiring static IP addresses or zonal networking features.

A Route 53 Alias record can point to an NLB.

Example:

```text
service.example.com
         |
         v
      Route 53
         |
         v
         NLB
         |
         v
   Application Targets
```

You can also use NLB endpoints as part of multi-region routing configurations.

### 6.3 Route 53 and CloudFront

CloudFront is a global content delivery network.

It distributes content through geographically distributed edge locations.

A typical architecture:

![AWS CloudFront: Delivering Content at the Speed of Light](https://images.openai.com/static-rsc-4/u8bypmZFIeKTmK7Q5efEaUd788Dcx8SEV1ikWwzVmqJD0KYF0Me5HAeuS2MPCjnHWdhFxk92S8XlQx2zXBZIPmVzRVsx_8k_rKxwFKhwHZMy6YS9N8NQNwqWT75Xpk3bGLc9Jzot4Wy_Ajw_z3wSiTN6SUJ2g0gGdI7rRkPhPPk2JjIoYnn1kKIcD5jCh8k1?purpose=fullsize)

```text
             example.com
                  |
                  v
               Route 53
                  |
                  v
               CloudFront
                  |
             +----+----+
             |         |
             v         v
           S3       ALB Origin
          Static    Dynamic
          Content   Content
```

Route 53 resolves the application domain to CloudFront.

For example:

```text
example.com
    |
    v
CloudFront distribution
    |
    +----> S3 origin
    |
    +----> ALB origin
```

For a custom domain, you generally configure:

* A CloudFront distribution.

* An alternate domain name (CNAME) on the distribution.

* An appropriate TLS certificate in AWS Certificate Manager in `us-east-1`.

* An Alias A record in Route 53.

* Optionally, an Alias AAAA record for IPv6.

Important: CloudFront is already a global service. You generally don't need to create separate CloudFront distributions for every application region simply to achieve global content delivery.

### 6.4 Route 53 and API Gateway

API Gateway provides managed API endpoints.

You can configure a custom domain such as:

```text
api.example.com
```

Instead of exposing the default API Gateway hostname, clients use your domain.

The configuration typically involves:

* An API Gateway custom domain.

* A TLS certificate.

* API mapping to a stage.

* A Route 53 Alias record.

Example:

```text
api.example.com
       |
       v
    Route 53
       |
       v
   API Gateway
       |
       v
   API Stage
       |
       v
   Backend Service
```

API Gateway custom domains have different endpoint types, including Regional and edge-optimized configurations.

For a Regional API Gateway custom domain, the DNS record points to its Regional domain target.

### 6.5 Route 53 and S3

Route 53 can also point a domain to an S3 website endpoint.

For example:

```text
www.example.com
       |
       v
    Route 53
       |
       v
  S3 Website Endpoint
       |
       v
   Static Website
```

This is useful for simple static website hosting.

However, S3 website endpoints have limitations:

* They do not provide HTTPS directly.

* They are not equivalent to S3 REST endpoints.

* They do not provide the same access-control behavior as private S3 origins.

For production static websites, a common architecture is:

```text
example.com
     |
     v
Route 53
     |
     v
CloudFront
     |
     v
Private S3 Bucket
```

CloudFront can use Origin Access Control (OAC) to access a private S3 bucket securely.

### 7\. Multi-Account DNS Architecture

In real-world AWS environments, applications are often distributed across multiple AWS accounts.

For example, an organization might have:

| AWS account     | Responsibility                     |
| --------------- | ---------------------------------- |
| Shared Services | Centralized DNS management         |
| Development     | Development applications           |
| Staging         | Staging applications               |
| Production      | Production applications            |
| Security        | Security monitoring and governance |

You generally don't want every account independently managing the organization's entire DNS namespace.

Instead, you can implement centralized DNS management.

### 7.1 Why centralized DNS management?

Consider this organization:

```text
                AWS Organization
                       |
             +---------+---------+
             |                   |
             v                   v
       Shared Services       Workloads
             |                   |
             v          +--------+--------+
       Central DNS      |        |        |
                      Dev     Staging   Production
```

The Shared Services account manages centralized DNS infrastructure.

Workload accounts deploy their applications and manage their own application resources.

This provides several advantages:

* Centralized DNS governance.

* Consistent DNS naming conventions.

* Reduced configuration duplication.

* Better security boundaries.

* Easier management of multiple environments.

### 7.2 Public hosted zones across accounts

Suppose your organization owns:

```text
example.com
```

The DNS namespace is managed by the Shared Services account.

You want separate accounts to manage their own subdomains:

```text
dev.example.com
staging.example.com
prod.example.com
```

One approach is DNS delegation.

![Multi-account DNS with AWS CDK](https://images.openai.com/static-rsc-4/TytTN-IS7oax3APN2ARbu7VUOlSMiLHIVWNjSiTGCjUJp1RR3xCn9LN3GTTaRoPGkoQwHz35fqvpg8QuyXIMy_5VD_0hjq5v8xSENbVU2NsMEfLwzYpdKBnbSQKFJ2Llsjn3GxUwVJ1o6gXJRmTU1CkLywshR1fNHmmPoq7ldxDEUD57oNuGoqjyYBsSzoY5?purpose=fullsize)

The architecture:

```text
          Shared Services Account
                    |
                    v
             example.com
                    |
          +---------+---------+
          |         |         |
          v         v         v
         dev     staging     prod
          |         |         |
          v         v         v
      Dev Account Stage Account Prod Account
      Hosted Zone Hosted Zone  Hosted Zone
```

The parent hosted zone contains NS records delegating the subdomains to their respective child hosted zones.

For example:

```text
dev.example.com
```

The parent zone has an NS record containing the authoritative name servers assigned to the child zone.

The child account manages its own DNS records.

This is standard DNS delegation and works across AWS accounts.

### 7.3 Cross-account hosted-zone management with Pulumi

You can manage resources in different AWS accounts using separate Pulumi providers.

For example:

```python
import pulumi
import pulumi_aws as aws

dns_provider = aws.Provider(
    "dns-provider",
    region="us-east-1",
    profile="shared-services"
)

prod_provider = aws.Provider(
    "prod-provider",
    region="us-east-1",
    profile="production"
)
```

Create a production hosted zone:

```python
prod_zone = aws.route53.Zone(
    "prod-zone",
    name="prod.example.com",
    opts=pulumi.ResourceOptions(
        provider=prod_provider
    )
)
```

Now delegate the production subdomain from the central account:

```python
parent_zone_id = "Z123456789EXAMPLE"

delegation = aws.route53.Record(
    "prod-delegation",
    zone_id=parent_zone_id,
    name="prod.example.com",
    type="NS",
    ttl=300,
    records=prod_zone.name_servers,
    opts=pulumi.ResourceOptions(
        provider=dns_provider
    )
)
```

This demonstrates an important Pulumi concept:

A single Pulumi program can manage resources across multiple AWS accounts using different providers.

The account credentials should be configured securely.

For production, prefer IAM roles and short-lived credentials over long-lived access keys.

Also, don't hardcode the parent hosted-zone ID in reusable infrastructure. It can be supplied through Pulumi configuration.

### 7.4 Cross-account private hosted zones

Private hosted zones introduce an additional consideration.

A private hosted zone is associated with VPCs rather than being publicly delegated through DNS name servers.

Suppose:

* Account A owns the private hosted zone.

* Account B owns an application VPC.

You want Account B's VPC to resolve records from Account A's private hosted zone.

The traditional cross-account association workflow is:

Step 1 — Account A authorizes the association

```bash
aws route53 create-vpc-association-authorization \
  --hosted-zone-id Z123456789EXAMPLE \
  --vpc VPCRegion=us-east-1,VPCId=vpc-0123456789abcdef0
```

Step 2 — Account B associates its VPC

```bash
aws route53 associate-vpc-with-hosted-zone \
  --hosted-zone-id Z123456789EXAMPLE \
  --vpc VPCRegion=us-east-1,VPCId=vpc-0123456789abcdef0
```

Step 3 — Account A removes the authorization

After the association is established, the authorization can be deleted.

```bash
aws route53 delete-vpc-association-authorization \
  --hosted-zone-id Z123456789EXAMPLE \
  --vpc VPCRegion=us-east-1,VPCId=vpc-0123456789abcdef0
```

The VPC and hosted zone must satisfy the service's association requirements.

### 7.5 Route 53 Profiles

Another important feature for multi-account DNS management is Route 53 Profiles.

Profiles allow you to centrally manage and share DNS configurations across multiple VPCs and accounts.

A profile can include supported DNS configurations such as:

* Private hosted zone associations.

* Resolver forwarding rules.

* DNS Firewall rule groups.

You can share profiles across accounts using AWS Resource Access Manager (AWS RAM).

For example:

![Streamlining multi-VPC DNS management with Amazon Route 53 Profiles and interface VPC endpoint integration | Networking & Content Delivery](https://images.openai.com/static-rsc-4/OSiq1n0UfSdQ0RAXM_uZpNz3PlhK3JlmMvKH8xN9C9Bm9CwEAktvNo82Im7XC7a6bHHpaszunQE5jFoYvkj5Wh7aRWu30DAEEYhen3ZCZfUT6A0gSmAKu5hZJiFX2YgxKK3n4PKQFXJKgEFsDhsDx_9ue1VV0a9joJ2mUkiL7qHQPnCOgHdBSlwHmL6eLiqo?purpose=fullsize)

```text
             Shared Services Account
                       |
                       v
                Route 53 Profile
                       |
                       v
                 AWS RAM Share
                       |
             +---------+---------+
             |         |         |
             v         v         v
           Dev       Staging   Production
           VPC         VPC       VPC
```

This reduces the operational overhead of manually configuring DNS settings in every VPC.

When to use which approach:

| Requirement                                | Approach                                  |
| ------------------------------------------ | ----------------------------------------- |
| Delegate public subdomains                 | NS record delegation                      |
| Share private hosted zones across accounts | Cross-account VPC association or Profiles |
| Share Resolver rules                       | AWS RAM or Profiles                       |
| Centrally distribute DNS security policies | Route 53 Profiles and DNS Firewall        |
| Manage all DNS infrastructure as code      | Pulumi                                    |

### 8\. Route 53 ARC and DNS Failover Considerations

Amazon Route 53 Application Recovery Controller (ARC) provides capabilities for managing application recovery and availability.

It is particularly useful for applications deployed across multiple AWS Availability Zones and Regions.

ARC is not simply another Route 53 routing policy.

It provides operational controls and recovery mechanisms that help you manage application availability during failures.

### 8.1 Route 53 ARC components

Important ARC capabilities include:

* Routing controls.

* Readiness checks.

* Zonal shift.

* Zonal autoshift.

We'll focus on routing controls because they are especially relevant to DNS failover.

### 8.2 Routing controls

Routing controls are switches that you can use to enable or disable traffic to particular application replicas.

For example:

```text
              Route 53
                  |
          +-------+-------+
          |               |
          v               v
       Primary         Secondary
       US-East          EU-West
          |               |
          v               v
       Routing          Routing
       Control          Control
        ON               OFF
          |               |
          v               v
       Active           Standby
```

During normal operation:

```text
US-East: ON
EU-West: OFF
```

During a disaster recovery event:

```text
US-East: OFF
EU-West: ON
```

ARC routing controls are backed by highly available control infrastructure.

They can be integrated with Route 53 DNS records through health-check mechanisms.

This allows an operator or an automation system to change application traffic routing without manually modifying every DNS record.

### 8.3 Routing control safety rules

One important problem in disaster recovery is accidentally disabling every application replica.

Imagine you have two regions:

```text
US-East: ON
EU-West: OFF
```

An operator accidentally turns off US-East without enabling EU-West.

The application becomes unavailable.

ARC supports safety rules that can prevent certain dangerous combinations of routing-control states.

For example, a safety rule can enforce that at least one routing control remains enabled.

This is particularly important for applications with strict availability requirements.

### 8.4 Readiness checks

Readiness checks help evaluate whether application replicas are prepared to take over traffic.

They can inspect supported AWS resources and configurations, including aspects of:

* Resource configuration.

* Service quotas.

* Capacity-related readiness.

* Recovery configuration.

The objective is to detect recovery problems before an actual disaster occurs.

For example, you might discover that the standby region has insufficient capacity or missing resources.

This is much better than discovering the problem during a regional outage.

### 8.5 Zonal shift and zonal autoshift

ARC also supports Availability Zone-level recovery.

Zonal shift allows you to move traffic away from an impaired Availability Zone for supported AWS resources.

Zonal autoshift can automatically shift traffic away from an Availability Zone when AWS determines that there is an issue affecting that zone.

These capabilities are different from multi-region Route 53 DNS failover.

They operate at the Availability Zone recovery level and are supported only for eligible resources.

### 8.6 Route 53 failover versus ARC

| Feature             | Route 53 health-based failover     | ARC routing controls                                                  |
| ------------------- | ---------------------------------- | --------------------------------------------------------------------- |
| Main purpose        | DNS health-based routing           | Controlled application recovery                                       |
| Decision mechanism  | Health checks and DNS routing      | Operator or automation-controlled switches                            |
| Application health  | Health-check configuration         | Routing control state; readiness checks provide additional assessment |
| Safety rules        | Not equivalent to ARC safety rules | Supported                                                             |
| Recovery automation | Health-based DNS behavior          | Explicit operational control and automation                           |

### 8.7 Important DNS failover considerations

When designing production DNS failover, consider the following:

1\. DNS TTL

A low TTL can help reduce caching duration, but it does not guarantee immediate failover.

2\. Recursive resolver caching

Some recursive DNS resolvers may cache records longer than the configured TTL.

3\. Existing connections

DNS changes do not automatically terminate established TCP connections.

4\. Health-check accuracy

A health check should measure meaningful application availability, not merely whether a server responds.

5\. Database readiness

The backup region must have usable application data.

6\. Failback

Returning traffic to the original region requires a controlled recovery process.

7\. Capacity

The surviving region must have enough capacity to handle the additional workload.

8\. Testing

Disaster recovery must be tested periodically, not just documented.

### 9\. Centralized DNS Management Patterns

Let's bring the multi-account concepts together.

A large AWS organization might use the following architecture:

![Migrating your multi-account DNS environment to Amazon Route 53 Profiles | Networking & Content Delivery](https://images.openai.com/static-rsc-4/KA0zEzpoZWuO1JvbjYx-B9dd-R_SiOZtAS9Be2BuO5kkUHdjp8kGJ2j1sK0guvPrTKHA5rpqPLrx7jXFZAjCh1Jph6Jq2CawnIZmUIl-eZ_woXTWSx0JSrGOumQ7TcjUHwBCeuZcjU5_V_VMcb-UVh651xZZCZhejoDcz1kn0jBNR2YGJGqdy-kOqPY-p8M8?purpose=fullsize)

```text
                    AWS Organization
                           |
                           v
                  Shared Services Account
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
        Public DNS    Private DNS    DNS Firewall
             |             |             |
             +-------------+-------------+
                           |
                           v
                    Route 53 Profiles
                           |
                           v
                       AWS RAM
                           |
             +-------------+-------------+
             |             |             |
             v             v             v
          Dev Account  Staging Account  Prod Account
             |             |             |
             v             v             v
          Dev VPC      Staging VPC     Prod VPC
```

A centralized DNS architecture commonly has these responsibilities:

| Component                   | Responsibility                         |
| --------------------------- | -------------------------------------- |
| Shared Services             | Central DNS ownership                  |
| Route 53 public hosted zone | Public domain resolution               |
| Private hosted zones        | Internal service discovery             |
| Route 53 Resolver           | DNS forwarding and hybrid connectivity |
| Route 53 Profiles           | Reusable DNS configuration             |
| AWS RAM                     | Cross-account resource sharing         |
| DNS Firewall                | DNS query filtering                    |
| CloudWatch                  | Monitoring and logging                 |
| Pulumi                      | Infrastructure automation              |

The main design principle is to separate DNS governance from application deployment.

Application teams should be able to deploy their own services without requiring unrestricted permissions to modify the organization's root DNS namespace.

For example:

```text
Shared Services:
example.com

Production:
api.prod.example.com
web.prod.example.com

Staging:
api.staging.example.com
web.staging.example.com
```

This creates clear ownership boundaries.

### 10\. Pulumi Architecture for Multi-Region DNS

Now let's look at how we can organize this infrastructure as code.

A common mistake is putting every DNS record, hosted zone, ALB, and application resource into one enormous Pulumi program.

Instead, we can separate infrastructure into reusable components and stacks.

### 10.1 Recommended project structure

```text
route53-platform/
│
├── Pulumi.yaml
├── requirements.txt
│
├── components/
│   ├── hosted_zone.py
│   ├── dns_record.py
│   ├── latency_routing.py
│   └── health_check.py
│
├── stacks/
│   ├── shared_dns/
│   │   └── __main__.py
│   │
│   ├── us_east/
│   │   └── __main__.py
│   │
│   ├── eu_west/
│   │   └── __main__.py
│   │
│   └── ap_southeast/
│       └── __main__.py
│
└── scripts/
    ├── deploy.sh
    ├── destroy.sh
    └── dns_check.sh
```

Each stack has a specific responsibility.

| Stack        | Responsibility                    |
| ------------ | --------------------------------- |
| shared-dns   | Hosted zones and centralized DNS  |
| us-east      | US regional infrastructure        |
| eu-west      | European regional infrastructure  |
| ap-southeast | Singapore regional infrastructure |

### 10.2 Configure Pulumi stacks

You can create the stacks using Bash:

```bash
pulumi stack init shared-dns
pulumi stack init us-east
pulumi stack init eu-west
pulumi stack init ap-southeast
```

Configure the AWS region for each stack:

```bash
pulumi config set aws:region us-east-1 \
  --stack us-east

pulumi config set aws:region eu-west-1 \
  --stack eu-west

pulumi config set aws:region ap-southeast-1 \
  --stack ap-southeast
```

The shared DNS stack can use a designated region for Route 53 resource management:

```bash
pulumi config set aws:region us-east-1 \
  --stack shared-dns
```

Remember that public Route 53 hosted zones are global resources, even though the AWS provider requires a region configuration.

### 10.3 Export regional ALB information

Each regional application stack can export its ALB DNS information.

For example:

```python
pulumi.export("alb_dns_name", alb.dns_name)
pulumi.export("alb_zone_id", alb.zone_id)
```

The shared DNS stack can consume these outputs through `StackReference`.

```python
us_stack = pulumi.StackReference(
    "organization/route53-platform/us-east"
)

eu_stack = pulumi.StackReference(
    "organization/route53-platform/eu-west"
)

us_dns = us_stack.require_output("alb_dns_name")
us_zone_id = us_stack.require_output("alb_zone_id")

eu_dns = eu_stack.require_output("alb_dns_name")
eu_zone_id = eu_stack.require_output("alb_zone_id")
```

This allows the DNS stack to reference regional infrastructure without duplicating its configuration.

The same technique works across projects and, with appropriate permissions and state-backend configuration, across accounts.

### 10.4 Create latency-based records

The shared DNS stack can create latency-based records:

```python
us_record = aws.route53.Record(
    "api-us",
    zone_id=hosted_zone.zone_id,
    name="api.example.com",
    type="A",
    set_identifier="us-east-1",
    latency_routing_policy={
        "region": "us-east-1"
    },
    aliases=[{
        "name": us_dns,
        "zone_id": us_zone_id,
        "evaluate_target_health": True
    }]
)

eu_record = aws.route53.Record(
    "api-eu",
    zone_id=hosted_zone.zone_id,
    name="api.example.com",
    type="A",
    set_identifier="eu-west-1",
    latency_routing_policy={
        "region": "eu-west-1"
    },
    aliases=[{
        "name": eu_dns,
        "zone_id": eu_zone_id,
        "evaluate_target_health": True
    }]
)
```

These records share the same DNS name but have different regions and set identifiers.

You can add the Singapore record in exactly the same way.

This is a practical example of how Pulumi can manage a multi-region DNS architecture.

Note: This example demonstrates latency routing with ALB Alias targets. For a complex combination of latency, weighted, and failover policy trees, use Traffic Flow or an appropriately designed set of standard routing records. Do not assume that standard routing records support arbitrary nested policy composition.

### 11\. Hands-on Labs

We'll now translate the concepts into practical AWS architectures.

The labs use Pulumi (Python), AWS CLI, and Bash.

### Lab 1 — Design a Multi-Region Application DNS Architecture

Architecture lab

Objective: Design a global DNS architecture for an application deployed in three AWS regions.

Architecture:

```text
                api.example.com
                       |
                       v
                  Route 53
                       |
          +------------+------------+
          |            |            |
          v            v            v
       US-East       EU-West     Singapore
          |            |            |
          v            v            v
         ALB          ALB          ALB
          |            |            |
          v            v            v
         ECS          ECS          ECS
```

Tasks:

* Define the regional application architecture.

* Identify the DNS endpoints.

* Choose an appropriate routing policy.

* Define health-check requirements.

* Design regional failure scenarios.

* Determine how traffic should behave during a regional outage.

* Organize the infrastructure into Pulumi stacks.

### Lab 2 — Route Traffic Between Regional ALBs

Pulumi lab

Objective: Configure Route 53 to direct traffic to ALBs deployed in different AWS regions.

Tasks:

* Create an ALB in `us-east-1`.

* Create another ALB in `eu-west-1`.

* Export ALB DNS names and hosted-zone IDs.

* Reference regional outputs using Pulumi `StackReference`.

* Create a Route 53 public hosted zone.

* Create Alias records pointing to both ALBs.

* Configure latency-based routing.

* Verify DNS responses using `dig`.

* Test regional endpoint health.

Useful commands:

```bash
dig api.example.com

dig api.example.com +short

dig api.example.com +trace
```

### Lab 3 — Combine Weighted and Latency-Based Routing

Advanced Traffic Flow lab

Objective: Implement a regional traffic-management policy with gradual application releases.

Architecture:

```text
                 Route 53
                     |
                     v
              Latency Routing
                /        \
               v          v
            US-East     EU-West
               |          |
               v          v
            Weighted   Weighted
             Routing    Routing
              /  \       /  \
             v    v     v    v
            V1   V2    V1   V2
```

Tasks:

* Deploy two application versions in each region.

* Create regional endpoints.

* Define a Traffic Flow policy.

* Configure latency-based regional selection.

* Configure weighted distribution between versions.

* Create a policy record.

* Change the traffic weights.

* Create another policy version.

* Observe the effect of DNS caching on traffic distribution.

The objective is to understand the difference between policy configuration and actual application request distribution.

### Lab 4 — Build a Multi-Region Active-Active Architecture

Architecture + Pulumi lab

Objective: Build an application that serves traffic from multiple AWS regions simultaneously.

Tasks:

* Deploy the application in two AWS regions.

* Deploy regional ALBs.

* Configure regional DNS endpoints.

* Implement latency-based routing.

* Configure health checks.

* Design a cross-region data strategy.

* Implement application session management.

* Simulate the failure of one region.

* Verify that the surviving region can handle additional traffic.

Consider using DynamoDB Global Tables or another suitable cross-region data solution.

### Lab 5 — Implement a Multi-Region Active-Passive Architecture

Disaster recovery lab

Objective: Configure a primary and standby region with automated DNS failover.

Architecture:

```text
                Route 53
                    |
                    v
              Failover Policy
                /        \
               v          v
           Primary     Secondary
           US-East      EU-West
               |          |
               v          v
              ALB        ALB
               |          |
               v          v
           Application  Standby
```

Tasks:

* Deploy the primary application in US-East.

* Deploy a standby application in EU-West.

* Configure regional health checks.

* Create primary and secondary failover records.

* Configure appropriate TTL values.

* Simulate primary-region failure.

* Observe DNS failover behavior.

* Verify secondary-region application availability.

* Design a controlled failback procedure.

### Lab 6 — Configure DNS Records for CloudFront Distributions

Integration lab

Objective: Configure Route 53 to expose a CloudFront distribution through a custom domain.

Architecture:

```text
             www.example.com
                    |
                    v
                 Route 53
                    |
                    v
                CloudFront
                    |
              +-----+-----+
              |           |
              v           v
             S3           ALB
           Static       Dynamic
           Content      Content
```

Tasks:

* Create an S3 bucket for static content.

* Configure CloudFront with the S3 origin.

* Configure Origin Access Control.

* Request or configure an ACM certificate in `us-east-1`.

* Add the custom domain to CloudFront.

* Create Route 53 Alias A and AAAA records.

* Test HTTPS connectivity.

* Verify CloudFront distribution behavior.

### Lab 7 — Delegate Subdomains Across AWS Accounts

Multi-account lab

Objective: Implement centralized DNS management across multiple AWS accounts.

Tasks:

* Create a parent public hosted zone in the Shared Services account.

* Create separate AWS profiles for Shared Services and Production.

* Create a child hosted zone in the Production account.

* Export the child hosted zone name servers.

* Create NS delegation records in the parent zone.

* Configure application records in the child zone.

* Verify DNS delegation.

* Organize cross-account resources using Pulumi providers.

* Review IAM permissions and access boundaries.

Expected namespace:

```text
example.com
    |
    +-- dev.example.com
    |
    +-- staging.example.com
    |
    +-- prod.example.com
```

### Lab 8 — Automate DNS Infrastructure Across Multiple Pulumi Stacks

Production automation lab

Objective: Build reusable DNS infrastructure that can be deployed and managed independently across regions and accounts.

Tasks:

* Create separate Pulumi stacks for each region.

* Create a centralized DNS stack.

* Export regional ALB information.

* Consume outputs through `StackReference`.

* Create reusable DNS components.

* Configure Pulumi providers for different AWS accounts.

* Implement stack configuration and secret management.

* Automate deployment using Bash.

* Preview infrastructure changes before deployment.

* Implement safe infrastructure updates and cleanup.

Example Bash deployment script:

```bash
#!/usr/bin/env bash

set -euo pipefail

stacks=(
  "us-east"
  "eu-west"
  "ap-southeast"
  "shared-dns"
)

for stack in "${stacks[@]}"; do
    echo "Deploying stack: ${stack}"

    pulumi preview --stack "${stack}"

    pulumi up --yes --stack "${stack}"
done

echo "Deployment completed."
```

For production deployments, use explicit dependency ordering and ensure regional infrastructure is ready before deploying DNS records that reference it.

### 12\. Important Production Design Considerations

Before finishing this module, let's summarize several design decisions that matter when building real-world Route 53 architectures.

| Concern                       | Recommended consideration                  |
| ----------------------------- | ------------------------------------------ |
| Global availability           | Multi-region deployment                    |
| Regional performance          | Latency-based routing                      |
| Gradual releases              | Weighted routing                           |
| Geographic requirements       | Geolocation routing                        |
| Disaster recovery             | Failover routing + recovery infrastructure |
| Application availability      | Meaningful health checks                   |
| Multi-account DNS             | Centralized management and delegation      |
| Private DNS                   | Private hosted zones and Resolver          |
| DNS security                  | DNS Firewall and DNSSEC                    |
| Infrastructure automation     | Pulumi components and stacks               |
| Operational recovery          | Route 53 ARC where appropriate             |
| Traffic distribution accuracy | Understand DNS caching limitations         |

### Common architectural mistakes

* Assuming DNS failover is instantaneous.

* Treating latency routing as real-time application latency measurement.

* Assuming DNS weights represent exact HTTP request percentages.

* Using health checks that only verify whether a server responds.

* Forgetting database replication when implementing multi-region applications.

* Assuming Route 53 can distribute individual HTTP requests.

* Allowing application accounts unrestricted access to the organization's root hosted zone.

* Treating Traffic Flow versioning as Pulumi state versioning.

* Assuming ARC routing controls automatically detect every application failure.

* Ignoring the cost of multiple hosted zones, health checks, Traffic Flow policies, and Resolver endpoints.

### 13\. Module 7 Summary

Let's review what we've covered.

| Topic                      | Key takeaway                                               |
| -------------------------- | ---------------------------------------------------------- |
| Traffic Flow               | Visual management of complex DNS routing policies          |
| Policy versioning          | Maintain versions of traffic-routing configurations        |
| Multi-region DNS           | Route users to regional application endpoints              |
| Latency + weighted routing | Combine regional selection and gradual releases            |
| Active-active              | Multiple regions serve production traffic                  |
| Active-passive             | One region serves traffic while another is standby         |
| ALB/NLB integration        | Route DNS names to regional load balancers                 |
| CloudFront integration     | Provide global content delivery through custom domains     |
| API Gateway integration    | Expose APIs through custom DNS names                       |
| S3 integration             | Configure DNS for static websites                          |
| Multi-account DNS          | Separate DNS governance from application ownership         |
| Route 53 Profiles          | Share DNS configurations across accounts and VPCs          |
| Route 53 ARC               | Support controlled application recovery and zonal recovery |

### The architecture you should understand after this module

![レイテンシベースルーティングを使用して Amazon CloudFront で マルチリージョンのアクティブ – アクティブなアーキテクチャを実現する | Amazon Web Services ブログ](https://images.openai.com/static-rsc-4/9AjShMVWamFd2P6i6Pu8YHDvFtmwFyX1yaAKcOZKNXWiPKdNZzEv95a_rfjD066jPxjh0hRVp1Cw0Mtju0cRjjQRIFgpWXl6KfEY6wM24AepFoFIukKpLTw9qUtlMS72V5KSlsTGbzdpFJvwCNkD6BpmDImcpf65EJEv2GnNRorZrE_EYYJyBYVM8aet0rX9?purpose=fullsize)

The major architectural idea is:

Route 53 provides the DNS traffic-management layer, while regional application infrastructure, databases, load balancers, and recovery mechanisms provide the actual application availability.

Combining these capabilities allows you to build global, resilient, multi-account AWS architectures.

Next module: Module 8 — DNS Monitoring, Logging, Troubleshooting, and Cost Optimization.

We'll focus on Route 53 query logging, Resolver query logging, CloudWatch Logs Insights, CloudTrail, DNS troubleshooting, monitoring, and cost optimization.
