### Module 8 — Production Architecture, Global Traffic, and Capstone

AWS Load Balancing · Pulumi Python · Bash · Production architecture

### 1\. Learning objectives

In this module, we bring together everything covered in the previous seven modules and apply it to production-grade AWS architectures.

By the end of this module, you should be able to:

* Design highly available, multi-AZ load-balancing architectures.

* Understand global traffic distribution using Amazon Route 53 and AWS Global Accelerator.

* Implement DNS-based failover and understand its limitations.

* Design multi-region load-balancing and disaster-recovery strategies.

* Implement blue-green and canary deployments using ALB weighted target groups.

* Integrate load balancing with ECS, EKS, Auto Scaling, CloudFront, and AWS WAF.

* Build reusable Pulumi components for load-balancing infrastructure.

* Manage Pulumi stacks, configuration, secrets, outputs, and environment-specific deployments.

* Develop production operational runbooks and perform failure-recovery exercises.

* Evaluate availability, security, performance, and cost trade-offs.

### 2\. Production load-balancing architecture

Production load balancing involves much more than distributing HTTP requests between servers. You must consider availability zones, regional failures, application deployments, security boundaries, DNS behavior, and operational visibility.

### 2.1 Multi-AZ architecture

A production application should not depend on a single Availability Zone.

A typical architecture includes:

* A public ALB deployed across at least two public subnets in different AZs.

* Private application subnets distributed across multiple AZs.

* ECS tasks or EC2 instances distributed across those AZs.

* Target groups with appropriate health checks.

* Auto Scaling or ECS Service Auto Scaling.

* CloudWatch metrics and alarms.

* Independent NAT gateways per AZ when the architecture requires AZ-independent outbound connectivity.

![Scaling cluster infrastructure in ECS | by Utsav Ojha | Medium](https://images.openai.com/static-rsc-4/Ygophoqn63iNvq0PbFQWZaquYCReoN9_2a-exmNdl1NQVVsDeFHliynttd26Ekhbe51Tz-hhEJbqZITs0j6-keNcJvkTVgmdMbltnh8Ct4p2e3Dul28lOozdJgr0IW28vVLhkwXzQA_iHnOoW8fm7PUSBRGohT2-CzEjETb3I5yv_REmuzn0daP5p8LndsbA?purpose=fullsize)

Important architectural considerations:

* A load balancer is a regional service, but its targets and networking resources still have AZ-level failure dependencies.

* Enable cross-zone load balancing where appropriate, understanding the differences between ALB and NLB behavior.

* Maintain sufficient healthy capacity when one AZ becomes unavailable.

* Configure health checks to detect actual application failures rather than merely confirming that a process is running.

* Avoid making a single database, NAT gateway, or downstream service the failure point of an otherwise highly available architecture.

### 2.2 Capacity planning and failure domains

Consider a service running six ECS tasks across three AZs.

| AZ    | Normal capacity | After one AZ fails |
| ----- | --------------- | ------------------ |
| AZ A  | 2 tasks         | 0                  |
| AZ B  | 2 tasks         | 2                  |
| AZ C  | 2 tasks         | 2                  |
| Total | 6               | 4                  |

The remaining four tasks must be capable of handling the expected production workload.

This is an important distinction: high availability does not automatically mean sufficient capacity after a failure.

Consider:

* Expected peak requests per second.

* CPU and memory utilization.

* Target response times.

* Minimum healthy task count.

* Scaling delays.

* Deployment capacity requirements.

* Downstream database and cache capacity.

### 2.3 Zonal shift and zonal autoshift

AWS provides zonal-shift capabilities through Amazon Application Recovery Controller (ARC).

Understand:

* Zonal shift and how it moves traffic away from an impaired Availability Zone.

* Zonal autoshift and its managed traffic-shifting behavior.

* The difference between removing traffic from an AZ and repairing the underlying infrastructure.

* How load-balancer zonal health and application health affect recovery.

* Operational considerations when manually initiating or cancelling a zonal shift.

Do not assume that every unhealthy application target automatically triggers a regional or zonal traffic shift.

### 3\. Global traffic management with Route 53

Amazon Route 53 provides DNS-based traffic management for applications distributed across multiple endpoints and AWS regions.

### 3.1 Route 53 routing policies

Understand the different routing policies and when to use them.

| Routing policy    | Purpose                                     | Example                          |
| ----------------- | ------------------------------------------- | -------------------------------- |
| Simple            | Basic DNS resolution                        | One application endpoint         |
| Weighted          | Distribute traffic by configured weights    | 90% primary, 10% canary          |
| Latency-based     | Direct users to a low-latency AWS region    | US and European deployments      |
| Failover          | Primary and secondary endpoint selection    | Disaster recovery                |
| Geolocation       | Route based on user location                | Geographic application endpoints |
| Geoproximity      | Route based on geographic distance and bias | Regional traffic distribution    |
| Multivalue answer | Return multiple healthy records             | Multiple application endpoints   |
| IP-based          | Route based on client IP ranges             | Network-specific routing         |

### 3.2 Weighted routing

Weighted routing allows you to distribute DNS responses between multiple endpoints.

For example:

* Primary environment: weight 90.

* Canary environment: weight 10.

![Adding Route 53 Health Checks With an ELB and Route 53 Policies - KodeKloud](https://images.openai.com/static-rsc-4/tIHQjTYxEVcfGSYVqHpPrETDyooYD5Y5S4mw6UyOxZGFKiR-O_t_nsVvKkElHDcwBaffPxwuFEqSjb0dG5BbCyTq-6AiJJwN7Lfw82na-iPUSJ0gmTYpjCatihkWo0qiQa68jPcZabj8MVQGcv2CEIahW_JEYAPR0B9Y-Mpwd5Y75UZx5GzmLaq3dFpR2FAQ?purpose=fullsize)

Example DNS records:

```text
app.example.com
    |
    +-- ALB Primary  (Weight: 90)
    |
    +-- ALB Canary   (Weight: 10)
```

Important considerations:

* Route 53 weights influence DNS responses, not individual HTTP requests.

* DNS caching and TTLs affect how quickly traffic distribution changes.

* Existing client connections are not moved simply because DNS weights change.

* DNS-based weighted routing is not equivalent to ALB weighted target-group forwarding.

### 3.3 Latency-based routing

Latency-based routing directs users toward AWS regions expected to provide lower network latency.

Example:

```text
                    app.example.com
                           |
                       Route 53
                           |
               +-----------+-----------+
               |                       |
          us-east-1                 eu-west-2
               |                       |
             ALB                     ALB
               |                       |
          ECS Service             ECS Service
```

Understand:

* How Route 53 evaluates latency.

* How regional endpoints are configured.

* How health checks can influence DNS responses.

* Why low network latency does not necessarily mean low application response time.

* Why database location and inter-region dependencies matter.

### 3.4 Failover routing and health checks

Route 53 failover routing supports primary and secondary endpoints.

Understand:

* Primary and secondary DNS records.

* Route 53 health checks.

* Calculated health checks.

* Endpoint monitoring and health-check intervals.

* DNS TTL and resolver caching.

* Failover behavior when an endpoint becomes unhealthy.

* Failback behavior after recovery.

Important: DNS failover is not instantaneous. Resolver caching, TTLs, existing connections, and client DNS behavior can delay the effective traffic transition.

Also distinguish between Route 53 health checks and load-balancer target health checks. They monitor different layers and serve different purposes.

### 3.5 Pulumi: Route 53 weighted routing

A simplified Pulumi Python example:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

zone_id = config.require("zoneId")
domain = config.require("domain")

primary_alb_dns = config.require("primaryAlbDns")
primary_alb_zone = config.require("primaryAlbZone")

canary_alb_dns = config.require("canaryAlbDns")
canary_alb_zone = config.require("canaryAlbZone")

primary = aws.route53.Record(
    "primary-record",
    zone_id=zone_id,
    name=domain,
    type="A",
    set_identifier="primary",
    weighted_routing_policies=[{
        "weight": 90,
    }],
    aliases=[{
        "name": primary_alb_dns,
        "zone_id": primary_alb_zone,
        "evaluate_target_health": True,
    }],
)

canary = aws.route53.Record(
    "canary-record",
    zone_id=zone_id,
    name=domain,
    type="A",
    set_identifier="canary",
    weighted_routing_policies=[{
        "weight": 10,
    }],
    aliases=[{
        "name": canary_alb_dns,
        "zone_id": canary_alb_zone,
        "evaluate_target_health": True,
    }],
)

pulumi.export("application_domain", domain)
```

This creates two weighted alias records pointing to separate ALBs.

Notice that `evaluate_target_health` is enabled. This allows Route 53 to consider the health of the alias target when evaluating DNS health, subject to Route 53's alias-health evaluation rules.

For production failover, understand the relationship between alias target health, explicit health checks, and the routing policy.

### 4\. AWS Global Accelerator

Route 53 and AWS Global Accelerator both support global traffic management, but they operate differently.

### 4.1 How Global Accelerator works

AWS Global Accelerator provides static anycast IP addresses that act as fixed entry points for applications.

Traffic enters the AWS network through an AWS edge location and is forwarded over the AWS global network to healthy application endpoints.

Supported standard accelerator endpoints include:

* Application Load Balancers.

* Network Load Balancers.

* EC2 instances.

* Elastic IP addresses.

![](https://images.openai.com/static-rsc-4/imiZH10jhJnlj__1XjcaWrgkXa8NqvB8poxmG6COl5zy9f3YFpQh9LmpsnNQXkbKLi7swYdZ8W8xeKSiO_Bx4_94yYbBbmQBhoTtBw9LBirsm_krK9-0E_Sa2BsNRK1qUHHWfGmcWr0QTK0imHHLGzBqDbP0ZfUVFNkVOAq0y2pebnIS45tB_wymcYyipCDR?purpose=fullsize)

The typical architecture:

```text
             Global Users
                  |
          AWS Global Accelerator
                  |
          Anycast Static IPs
                  |
           Endpoint Groups
             /        \
            /          \
       us-east-1     eu-west-2
           |             |
          ALB           ALB
           |             |
          ECS           ECS
```

### 4.2 Global Accelerator components

| Component       | Responsibility                                                   |
| --------------- | ---------------------------------------------------------------- |
| Accelerator     | Provides static anycast IP addresses                             |
| Listener        | Defines supported ports and protocols                            |
| Endpoint group  | Groups endpoints within an AWS Region                            |
| Endpoint        | ALB, NLB, EC2, or Elastic IP                                     |
| Traffic dial    | Controls the percentage of traffic directed to an endpoint group |
| Endpoint weight | Controls traffic distribution among endpoints                    |

Understand the difference between endpoint weights and traffic dials.

* Endpoint weights influence traffic distribution within an endpoint group.

* Traffic dials control the percentage of traffic directed to a regional endpoint group.

### 4.3 Route 53 versus Global Accelerator

| Feature             | Route 53                            | Global Accelerator                                      |
| ------------------- | ----------------------------------- | ------------------------------------------------------- |
| Primary function    | DNS-based routing                   | Global network traffic routing                          |
| Entry point         | DNS resolution                      | Static anycast IPs                                      |
| Static IP addresses | Not provided by DNS routing itself  | Two static IPv4 addresses for standard accelerators     |
| Traffic routing     | DNS policies                        | Network-level routing                                   |
| Failover            | Health-aware DNS responses          | Endpoint health and traffic routing                     |
| DNS caching impact  | Yes                                 | Not for accelerator endpoint switching                  |
| Regional endpoints  | DNS records                         | Endpoint groups                                         |
| Best use case       | DNS management and flexible routing | Global application entry points and network performance |

When to choose each:

Use Route 53 when you need:

* DNS-based weighted routing.

* Geographic routing.

* Latency-based routing.

* DNS failover.

* Integration with domain management.

Use Global Accelerator when you need:

* Static global IP addresses.

* Consistent application entry points.

* Traffic routing over the AWS global network.

* Faster endpoint switching without waiting for DNS TTL expiration.

* Regional traffic management for TCP and UDP applications.

They can also work together: Route 53 resolves your application domain to Global Accelerator's static IP addresses.

AWS documentation: [How AWS Global Accelerator works](https://docs.aws.amazon.com/global-accelerator/latest/dg/introduction-how-it-works.html?utm_source=chatgpt.com) and [Global Accelerator request routing](https://docs.aws.amazon.com/prescriptive-guidance/latest/dynamodb-global-tables/ga-request-routing.html?utm_source=chatgpt.com).

### 4.4 Pulumi: AWS Global Accelerator

Create a standard accelerator with regional ALB endpoints.

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

primary_alb_arn = config.require("primaryAlbArn")
secondary_alb_arn = config.require("secondaryAlbArn")

accelerator = aws.globalaccelerator.Accelerator(
    "production-accelerator",
    name="production-accelerator",
    enabled=True,
    ip_address_type="IPV4",
)

listener = aws.globalaccelerator.Listener(
    "https-listener",
    accelerator_arn=accelerator.id,
    protocol="TCP",
    client_affinity="NONE",
    port_ranges=[{
        "from_port": 443,
        "to_port": 443,
    }],
)

primary_group = aws.globalaccelerator.EndpointGroup(
    "primary-region",
    listener_arn=listener.id,
    endpoint_group_region="us-east-1",
    traffic_dial_percentage=100,
    endpoint_configurations=[{
        "endpoint_id": primary_alb_arn,
        "weight": 100,
        "client_ip_preservation_enabled": True,
    }],
)

secondary_group = aws.globalaccelerator.EndpointGroup(
    "secondary-region",
    listener_arn=listener.id,
    endpoint_group_region="eu-west-2",
    traffic_dial_percentage=0,
    endpoint_configurations=[{
        "endpoint_id": secondary_alb_arn,
        "weight": 100,
        "client_ip_preservation_enabled": True,
    }],
)

pulumi.export("accelerator_dns", accelerator.dns_name)
pulumi.export("accelerator_ips", accelerator.ip_sets)
```

This is an active-passive starting configuration: the secondary endpoint group has a zero traffic dial. It is not, by itself, a complete failover configuration. You must design and test regional health checks, endpoint health, traffic-dial changes, and recovery behavior.

For production, consider using a controlled failover procedure rather than assuming the traffic dial automatically changes when an entire region fails.

### 5\. Multi-region architecture and disaster recovery

A multi-region architecture extends availability beyond a single AWS region.

It is particularly useful for applications that require regional disaster recovery, geographic distribution, or regional isolation.

### 5.1 Multi-region deployment models

Three common approaches are:

Active-passive

![Designing a Multi-Region Disaster Recovery Architecture on AWS | by Archita | Medium](https://images.openai.com/static-rsc-4/RLp7nERotSrsPhsPxixYqePFtbOUVrbSf_avvk6GlcRYUppZtjNk8cvmyP7J5qhsyVZF59_XfC6p6Uwg9c8HAG6hUKNdEmtR-JF_SXUP6LmyGT1MDJFJUGLZKVAssah68JUkSyjbwzi8HoN6SlcWObo4pa2GPUVyPYh2nCOKjAlwiwGCO70CTBlht9cILlnb?purpose=fullsize)

* One region serves production traffic.

* Another region maintains standby infrastructure.

* Traffic moves to the secondary region when the primary region fails.

* The secondary region must have enough capacity to handle production traffic.

Active-active

* Multiple regions serve production traffic simultaneously.

* Global traffic management distributes requests.

* Each region must be capable of serving application traffic independently.

* Data consistency and synchronization become important design concerns.

Pilot light

* Critical infrastructure and data services remain available in a secondary region.

* Most application capacity is provisioned when recovery is necessary.

* Recovery requires infrastructure deployment and scaling.

* It can reduce standby costs but generally increases recovery time.

### 5.2 RTO and RPO

Two important disaster-recovery metrics:

* RTO (Recovery Time Objective): Maximum acceptable time to restore the application.

* RPO (Recovery Point Objective): Maximum acceptable amount of data loss, expressed as time.

| Strategy           | Relative cost | Recovery time          | Data considerations                      |
| ------------------ | ------------- | ---------------------- | ---------------------------------------- |
| Backup and restore | Low           | Long                   | Restore from backups                     |
| Pilot light        | Low–medium    | Medium–long            | Replicate critical data                  |
| Warm standby       | Medium–high   | Shorter                | Keep a reduced environment running       |
| Active-active      | High          | Potentially very short | Requires careful data consistency design |

These are relative characteristics, not guaranteed AWS recovery times. Actual RTO and RPO depend on the application, database, replication mechanism, automation, and operational procedures.

### 5.3 Regional failover architecture

Consider an application deployed in two regions:

```text
                 Users
                   |
            Route 53 / GA
                   |
           +-------+-------+
           |               |
       us-east-1        eu-west-2
           |               |
          ALB             ALB
           |               |
         ECS             ECS
           |               |
        Database       Database
           |               |
           +-------+-------+
                   |
            Data replication
```

Important design considerations:

* Application configuration must be reproducible in both regions.

* Container images must be available in both regions.

* Secrets and certificates must be available in the recovery region.

* Database replication must meet the application's RPO.

* Network dependencies must be independent of the primary region.

* Health checks must represent actual application availability.

* Failover and failback procedures must be documented and tested.

Do not assume that replicating an ALB configuration automatically replicates the application, its data, or its dependencies.

### 5.4 Disaster-recovery testing

A production recovery strategy should be tested regularly.

Useful failure scenarios include:

* All application targets in one region becoming unhealthy.

* An Availability Zone becoming unavailable.

* An application deployment introducing widespread HTTP 5xx errors.

* A database becoming unavailable.

* A DNS endpoint returning an incorrect response.

* A regional dependency becoming inaccessible.

Use CloudWatch, application logs, and AWS health information to determine whether the failure is in the application, load balancer, DNS, or infrastructure.

### 6\. Blue-green and canary deployments using ALB

Application Load Balancer supports forwarding traffic to multiple target groups using weighted forwarding actions.

This enables gradual application releases without requiring DNS changes.

### 6.1 Blue-green deployment

A blue-green deployment maintains two application environments:

* Blue: currently active production version.

* Green: newly deployed version.

![AWS Elastic Load Balancer Demos](https://images.openai.com/static-rsc-4/Dsz7FYaiLijb7qWLilSu26sGhDJsX9FczDlaKvp52xZEm2KZmWgZ_N2HQUmDj8WEz0t4PJEzG_76YtXQd-8d7ko1ypEAYutJfNsbXuK-v4QdEyZjBzem0U1QMdZtB_dSa_3Yt-892lGpMKNMROPz1Gw-LgmzhALUv8OjDQOB37x-mYTLrloPMi3iTkj2gReP?purpose=fullsize)

Example:

```text
                 ALB
                  |
          Weighted forwarding
                  |
          +-------+-------+
          |               |
       Blue TG          Green TG
       Weight 100       Weight 0
          |               |
       Version 1        Version 2
```

Deployment procedure:

* Deploy the green application.

* Register its targets in a separate target group.

* Wait for green targets to become healthy.

* Send a small amount of traffic to green.

* Monitor latency, errors, and application behavior.

* Gradually increase green traffic.

* Route all traffic to green.

* Keep blue available temporarily for rollback.

* Remove the old environment after the rollback window.

### 6.2 Canary deployment

A canary deployment exposes a new version to a small percentage of traffic.

Example:

| Version   | Weight |
| --------- | ------ |
| Version 1 | 95     |
| Version 2 | 5      |

After validating the new version, increase its weight.

```text
Initial:
  v1 = 100
  v2 = 0

Canary:
  v1 = 95
  v2 = 5

Progressive:
  v1 = 75
  v2 = 25

Final:
  v1 = 0
  v2 = 100
```

### 6.3 Pulumi: ALB weighted forwarding

A simplified listener configuration:

```python
import pulumi_aws as aws

listener = aws.lb.Listener(
    "production-listener",
    load_balancer_arn=alb.arn,
    port=443,
    protocol="HTTPS",
    certificate_arn=certificate.arn,
    ssl_policy="ELBSecurityPolicy-TLS13-1-2-2021-06",
    default_actions=[{
        "type": "forward",
        "forward": {
            "target_groups": [
                {
                    "arn": blue_target_group.arn,
                    "weight": 95,
                },
                {
                    "arn": green_target_group.arn,
                    "weight": 5,
                },
            ],
            "stickiness": {
                "enabled": False,
                "duration": 3600,
            },
        },
    }],
)
```

The example assumes that the ALB, target groups, and ACM certificate have already been created.

Important deployment considerations:

* A target group must have healthy registered targets before receiving production traffic.

* Weighted forwarding does not automatically perform health-based failover to another weighted target group when one target group is unhealthy.

* Target-group stickiness can affect the observed traffic distribution.

* Existing application sessions and database compatibility must be considered during deployment.

* Rollback should include application and database compatibility, not just traffic weights.

AWS reference: [ALB target groups and configuration](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html?utm_source=chatgpt.com).

### 6.4 Bash: Inspect target group health

```bash
aws elbv2 describe-target-health \
  --target-group-arn "$GREEN_TG_ARN" \
  --query 'TargetHealthDescriptions[*].[Target.Id,TargetHealth.State,TargetHealth.Reason]' \
  --output table
```

Inspect listener rules:

```bash
aws elbv2 describe-rules \
  --listener-arn "$LISTENER_ARN" \
  --output table
```

Test the application:

```bash
curl -sS -D - https://app.example.com/health
```

For automated deployments, use CloudWatch alarms and deployment-pipeline conditions to prevent promoting a version that exhibits unacceptable error rates or latency.

### 7\. Integrating load balancing with other AWS services

Production load-balancing architectures usually combine several AWS services.

### 7.1 Application Load Balancer and Auto Scaling

An ALB can distribute traffic across EC2 instances managed by an Auto Scaling group.

Understand:

* Attaching an Auto Scaling group to an ALB target group.

* Automatic target registration and deregistration.

* Scaling policies based on CPU utilization.

* Scaling policies based on ALB request count per target.

* Instance warm-up and health-check grace periods.

* Lifecycle hooks and graceful termination.

* Coordinating scale-in behavior with connection draining.

Example architecture:

```text
             Application Users
                    |
                   ALB
                    |
                Target Group
                    |
              Auto Scaling Group
                 /       \
              EC2         EC2
```

A useful distinction: EC2 Auto Scaling health checks and ALB target health checks are related but not identical. Configure them deliberately according to the failure-recovery behavior you want.

### 7.2 CloudFront and ALB

CloudFront can be placed in front of an ALB to provide a global content-delivery layer.

Understand:

* CloudFront distributions and origins.

* ALB as a custom origin.

* Origin Access Control (OAC) versus origin access mechanisms supported for the origin type.

* HTTPS between CloudFront and ALB.

* Cache policies and origin request policies.

* Dynamic content versus static content caching.

* Cache invalidation.

* AWS WAF integration with CloudFront and ALB.

* Restricting direct access to the ALB origin.

![Block direct access to CloudFront origins with custom headers and AWS WAF - DEV Community](https://images.openai.com/static-rsc-4/dGjQdZ856r5aJOJ9AcwXZCOcNdeKOP4MxsfXOtArRV0t7Bd9udZW_WKrRxU4faA0Mb7PQWtk2J0TpZnXZaBgOcfAu5jRsCOLiek0RQYHeu1rLR2AVmYl4az9CzNrC8gg31oHzSUEd00szXpUf537uHKni4KUGnL44ttoNGQl0mvNv9VYzzcwE3T_XJndi__l?purpose=fullsize)

Important: CloudFront OAC is primarily designed for supported origins such as S3. Do not assume that enabling OAC secures an ALB origin. For an ALB origin, use an appropriate origin-access strategy, such as restricting inbound access and validating a custom origin header, while considering direct-origin bypass risks.

### 7.3 ECS and EKS integration

Review the relationship between load balancers and container orchestration.

| Service         | Typical integration                                  |
| --------------- | ---------------------------------------------------- |
| ECS Fargate     | ALB with IP target groups                            |
| ECS on EC2      | ALB with instance or IP target groups                |
| EKS Ingress     | AWS Load Balancer Controller with ALB                |
| EKS Service     | NLB integration for supported Service configurations |
| EKS Gateway API | Controller-dependent gateway integration             |

Production considerations:

* Keep task and pod health checks consistent with application readiness.

* Configure deregistration delay appropriately.

* Use graceful application shutdown.

* Account for deployment surge capacity.

* Avoid sending traffic to containers that are not ready.

* Monitor target registration during scaling and rolling updates.

### 7.4 AWS WAF and CloudFront

Understand where WAF should be deployed:

* At CloudFront for globally distributed web applications.

* At ALB for regional application protection.

* With separate rule configurations where different protection boundaries are required.

Review:

* AWS Managed Rules.

* Rate-based rules.

* IP reputation rules.

* Custom HTTP header and URI matching.

* Logging and sampled requests.

* False-positive analysis and rule tuning.

### 8\. Production Pulumi architecture and infrastructure management

As the infrastructure grows, individual Pulumi resources should be organized into reusable components.

### 8.1 Organizing Pulumi projects

A production project should separate networking, load balancing, applications, and monitoring.

Example structure:

```text
aws-production/
│
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── Pulumi.staging.yaml
├── Pulumi.production.yaml
│
├── requirements.txt
│
├── __main__.py
│
├── components/
│   ├── __init__.py
│   ├── network.py
│   ├── application_lb.py
│   ├── target_groups.py
│   ├── ecs_service.py
│   └── monitoring.py
│
└── config/
    └── environments.py
```

The objective is to avoid duplicating infrastructure definitions for development, staging, and production.

### 8.2 Pulumi ComponentResource

A component resource groups related resources into a reusable infrastructure abstraction.

For example, an ALB component can manage:

* Application Load Balancer.

* Target groups.

* Listeners.

* Listener rules.

* Security-group association.

* Access logging configuration.

A simplified component:

```python
import pulumi
import pulumi_aws as aws

class ApplicationLoadBalancer(pulumi.ComponentResource):

    def __init__(
        self,
        name,
        subnets,
        security_groups,
        target_port=8000,
        opts=None,
    ):
        super().__init__(
            "custom:loadbalancing:ApplicationLoadBalancer",
            name,
            None,
            opts,
        )

        self.lb = aws.lb.LoadBalancer(
            f"{name}-alb",
            load_balancer_type="application",
            internal=False,
            subnets=subnets,
            security_groups=security_groups,
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.target_group = aws.lb.TargetGroup(
            f"{name}-tg",
            port=target_port,
            protocol="HTTP",
            target_type="ip",
            vpc_id=config.require("vpcId"),
            health_check={
                "enabled": True,
                "path": "/health",
                "protocol": "HTTP",
                "healthy_threshold": 2,
                "unhealthy_threshold": 3,
                "interval": 30,
            },
            opts=pulumi.ResourceOptions(
                parent=self,
            ),
        )

        self.register_outputs({
            "load_balancer_arn": self.lb.arn,
            "load_balancer_dns": self.lb.dns_name,
            "target_group_arn": self.target_group.arn,
        })

config = pulumi.Config()
```

This is a simplified component foundation. A complete implementation should also define listeners, security-group rules, access logs, and any necessary dependencies.

The component should expose useful outputs rather than requiring other modules to understand its internal resource structure.

### 8.3 Pulumi configuration and stacks

Use separate stacks for different environments.

```bash
pulumi stack init dev
pulumi stack init staging
pulumi stack init production
```

Configure environment-specific values:

```bash
pulumi config set aws:region eu-west-2

pulumi config set vpcId vpc-xxxxxxxx

pulumi config set domain app.example.com
```

Store sensitive values as secrets:

```bash
pulumi config set --secret databasePassword 'replace-with-secret'
```

Inspect configuration:

```bash
pulumi config
```

Select an environment:

```bash
pulumi stack select staging
```

Preview infrastructure changes:

```bash
pulumi preview
```

Deploy:

```bash
pulumi up
```

Inspect exported infrastructure outputs:

```bash
pulumi stack output
```

Important production practices:

* Never commit plaintext secrets to Git.

* Use appropriate secret providers and access controls.

* Use separate AWS accounts for stronger production isolation where practical.

* Protect production stacks from accidental destruction.

* Use Pulumi state management and backups appropriately.

* Review infrastructure changes before applying them.

* Avoid embedding environment-specific resource names and identifiers throughout your code.

### 8.4 Pulumi and AWS credentials

Use short-lived AWS credentials whenever practical.

Examples include:

* AWS IAM Identity Center.

* IAM roles.

* GitHub Actions OIDC.

* CI/CD workload identity.

Avoid hardcoding AWS access keys in Pulumi projects or deployment scripts.

### 8.5 Infrastructure deployment workflow

A typical production workflow:

```text
Developer changes
       |
       v
Git commit / Pull request
       |
       v
Pulumi preview
       |
       v
Infrastructure review
       |
       v
Production approval
       |
       v
Pulumi up
       |
       v
Health checks and monitoring
       |
       v
Operational validation
```

### 9\. Operational runbooks, security, and cost governance

A production load-balancing solution must be maintainable.

### 9.1 Operational runbooks

Document procedures for common operational events.

| Incident         | Investigation                                      | Response                                   |
| ---------------- | -------------------------------------------------- | ------------------------------------------ |
| ALB returns 502  | Target health, connection errors, application logs | Repair backend connectivity                |
| ALB returns 503  | Healthy target count, target registration          | Restore healthy capacity                   |
| ALB returns 504  | Backend response time, timeout configuration       | Investigate slow dependencies              |
| TLS errors       | ACM certificate, listener, TLS policy              | Correct certificate/listener configuration |
| Uneven traffic   | Target-group weights, stickiness, target capacity  | Adjust traffic distribution                |
| AZ failure       | AZ health, remaining capacity                      | Shift traffic and scale remaining AZs      |
| Regional failure | Regional health and dependencies                   | Activate recovery region                   |
| Unexpected cost  | LCU/NLCU usage, data transfer, logging             | Identify traffic and configuration drivers |

### 9.2 Security checklist

* Use HTTPS for public application traffic.

* Use appropriate TLS policies.

* Keep application targets in private subnets when possible.

* Restrict backend access to approved load-balancer security groups.

* Enable access logging.

* Enable CloudTrail for configuration auditing.

* Use AWS WAF where appropriate.

* Protect DNS and certificate-management permissions.

* Keep secrets out of source code.

* Apply least-privilege IAM permissions.

* Review direct access to backend targets.

### 9.3 Cost governance

Understand the main load-balancing cost components:

| Service            | Main cost considerations                         |
| ------------------ | ------------------------------------------------ |
| ALB                | ALB hours and LCUs                               |
| NLB                | NLB hours and NLCUs                              |
| GWLB               | Gateway Load Balancer hours and GWLBe processing |
| Route 53           | Hosted zones, DNS queries, health checks         |
| Global Accelerator | Accelerator hours and data transfer              |
| CloudFront         | Requests, data transfer, and optional features   |
| AWS WAF            | Web ACLs, rules, and requests                    |
| CloudWatch         | Metrics, alarms, logs, and ingestion             |

Production cost optimization should consider:

* Removing unused load balancers and target groups.

* Avoiding unnecessary cross-AZ data transfer.

* Selecting the right load-balancer type.

* Monitoring LCU/NLCU consumption.

* Configuring appropriate log retention.

* Avoiding unnecessarily expensive multi-region active-active deployments.

* Reviewing CloudFront caching opportunities.

* Monitoring idle and overprovisioned backend capacity.

### 10\. Hands-on labs

The labs combine the concepts from this module into progressively more production-oriented deployments.

### Lab 1 — Multi-AZ production architecture

Goal: Build a highly available application deployment.

Tasks:

* Reuse the VPC and networking foundation from previous modules.

* Create public and private subnets across at least two AZs.

* Deploy an ALB across the public subnets.

* Deploy ECS Fargate tasks in private subnets.

* Configure an IP-based target group.

* Configure health checks and deregistration delay.

* Configure ECS Service Auto Scaling.

* Configure CloudWatch alarms.

* Test the application through the ALB DNS endpoint.

Validation:

```bash
aws elbv2 describe-load-balancers \
  --query 'LoadBalancers[*].[LoadBalancerName,DNSName,State.Code]' \
  --output table

aws elbv2 describe-target-health \
  --target-group-arn "$TARGET_GROUP_ARN"

aws ecs describe-services \
  --cluster production-cluster \
  --services production-api \
  --query 'services[*].[status,desiredCount,runningCount]' \
  --output table
```

### Lab 2 — Route 53 weighted and failover routing

Goal: Deploy two application endpoints and manage DNS-based traffic distribution.

Tasks:

* Create two ALBs representing separate application environments.

* Create a Route 53 hosted zone or use an existing domain.

* Configure weighted alias records.

* Start with a 90/10 traffic distribution.

* Change the distribution to 50/50.

* Configure health checks where appropriate.

* Create primary and secondary failover records.

* Simulate endpoint failure.

* Observe DNS resolution and failover behavior.

* Investigate TTL and resolver caching effects.

Bash validation:

```bash
dig app.example.com

dig +short app.example.com

watch -n 5 'dig +short app.example.com'
```

Inspect Route 53 records:

```bash
aws route53 list-resource-record-sets \
  --hosted-zone-id "$HOSTED_ZONE_ID"
```

Inspect health checks:

```bash
aws route53 list-health-checks \
  --output table
```

### Lab 3 — AWS Global Accelerator

Goal: Create a global application entry point.

Tasks:

* Deploy an ALB in the primary region.

* Deploy another ALB in a secondary region.

* Create a standard Global Accelerator using Pulumi.

* Configure a TCP listener on port 443.

* Create regional endpoint groups.

* Register both ALBs as endpoints.

* Configure endpoint weights and traffic dials.

* Retrieve the accelerator's static IP addresses.

* Test connectivity using `curl`.

* Simulate an unhealthy regional endpoint and observe endpoint health and traffic behavior.

Validation:

```bash
aws globalaccelerator list-accelerators \
  --query 'Accelerators[*].[Name,DnsName,Enabled]' \
  --output table
```

Inspect listeners:

```bash
aws globalaccelerator list-listeners \
  --accelerator-arn "$ACCELERATOR_ARN"
```

Inspect endpoint groups:

```bash
aws globalaccelerator list-endpoint-groups \
  --listener-arn "$LISTENER_ARN"
```

### Lab 4 — Blue-green deployment with weighted ALB target groups

Goal: Implement controlled application releases.

Tasks:

* Deploy application version 1 to ECS.

* Create a blue target group.

* Deploy application version 2 to a separate ECS service.

* Create a green target group.

* Configure an ALB listener with weighted forwarding.

* Start with 100% blue and 0% green.

* Verify green target health.

* Shift 5% of traffic to green.

* Monitor CloudWatch metrics and application errors.

* Increase green traffic to 25%, 50%, and finally 100%.

* Simulate an application failure and roll back to blue.

Example traffic progression:

```text
Deployment stage 1: 100% Blue / 0% Green
Deployment stage 2:  95% Blue / 5% Green
Deployment stage 3:  75% Blue / 25% Green
Deployment stage 4:  50% Blue / 50% Green
Deployment stage 5:   0% Blue / 100% Green
```

Pay particular attention to target-group stickiness, application session management, and database compatibility.

### Lab 5 — Reusable Pulumi load-balancer components

Goal: Refactor infrastructure into reusable components.

Tasks:

* Create a reusable `ApplicationLoadBalancer` component.

* Create reusable target-group and listener components.

* Expose useful resource outputs.

* Separate development, staging, and production stacks.

* Use Pulumi configuration for environment-specific values.

* Store sensitive configuration as encrypted secrets.

* Deploy each environment independently.

* Validate that changes in one stack do not unintentionally affect another.

* Protect production infrastructure against accidental deletion.

Expected project structure:

```text
load-balancer-platform/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── Pulumi.staging.yaml
├── Pulumi.production.yaml
├── requirements.txt
├── __main__.py
│
├── components/
│   ├── alb.py
│   ├── target_group.py
│   ├── listener.py
│   └── monitoring.py
│
└── config/
    └── environments.py
```

### Lab 6 — Capstone: Production-ready AWS web application

Final project

Goal: Build a production-oriented application architecture using the infrastructure and knowledge acquired throughout the course.

![Building a Containerized and Scalable Web Application on AWS](https://images.openai.com/static-rsc-4/LWiCYAFKa1ZHKxMD8ooxTMXwC1Rs0NxC4WRH9PdMIBgUBzPYlNT1eRGv6OT7JOgqQXBF7ZOWNlDOxmHMmRkyt_DOcBf16MyBXtnH0syaRITPsTE6DLojMZyY51Qf405QuBJ0WP1-NMxv9J59yCmX1cGBgrWKN7nMLBUWsqNpoPKnDsBvV_u5fYvdF7MzyFIH?purpose=fullsize)

Target architecture

```text
                   Internet Users
                         |
                      Route 53
                         |
                  CloudFront (Optional)
                         |
                       AWS WAF
                         |
                Application Load Balancer
                    HTTPS / ACM
                         |
                  Listener Rules
                         |
              +----------+----------+
              |                     |
          Target Group A        Target Group B
              |                     |
          ECS Fargate           ECS Fargate
             AZ-A                  AZ-B
              |                     |
              +----------+----------+
                         |
                  Application Layer
                         |
                  Database Layer

              CloudWatch / CloudTrail
              Access Logs / Alarms
```

Implementation requirements

Phase A — Infrastructure

* Provision a VPC with public and private subnets across at least two AZs.

* Create appropriate route tables and security groups.

* Deploy a public ALB.

* Configure HTTPS using ACM.

* Configure application target groups and listeners.

* Enable ALB access logging.

Phase B — Application deployment

* Containerize a FastAPI application.

* Push the Docker image to Amazon ECR.

* Deploy ECS Fargate services across multiple AZs.

* Configure target registration and health checks.

* Configure ECS Service Auto Scaling.

* Keep application tasks in private subnets.

Phase C — Security

* Configure AWS WAF.

* Restrict direct backend access.

* Use least-privilege IAM roles.

* Configure secrets securely.

* Enable CloudTrail auditing.

Phase D — Traffic management

* Configure Route 53 DNS records.

* Implement host-based or path-based routing.

* Configure weighted target-group forwarding.

* Implement a blue-green deployment.

* Test rollback procedures.

Phase E — Monitoring and reliability

* Create CloudWatch dashboards.

* Configure alarms for unhealthy targets.

* Monitor request count, latency, and HTTP errors.

* Analyze ALB access logs.

* Simulate backend failures.

* Test application recovery after target failures.

* Validate behavior when an AZ loses capacity.

Phase F — Production documentation

Document:

* Architecture and infrastructure dependencies.

* Network and security boundaries.

* Deployment and rollback procedures.

* Failure scenarios and recovery procedures.

* Monitoring and alerting configuration.

* Cost considerations.

* Operational runbooks.

Optional extension — Multi-region deployment

Extend the capstone by deploying a second application environment in another AWS region.

* Deploy a second ALB and ECS service.

* Replicate application images to the secondary ECR repository.

* Configure Route 53 failover or AWS Global Accelerator.

* Establish an appropriate data replication strategy.

* Define RTO and RPO.

* Test regional failover and recovery.

This extension introduces the operational and data-consistency challenges of real multi-region deployments.

### 11\. Cleanup and cost management

Several resources in this module can incur ongoing charges even when they receive no traffic.

Before finishing the labs:

* Delete unused Global Accelerators.

* Remove temporary Route 53 health checks.

* Delete unused ALBs, NLBs, and target groups.

* Remove temporary ECS services and clusters.

* Delete unused NAT gateways and Elastic IP addresses.

* Remove unnecessary CloudWatch log groups and dashboards.

* Remove temporary WAF resources.

* Review Route 53 hosted zones and DNS records.

For Pulumi-managed resources:

```bash
pulumi stack select dev

pulumi preview --diff

pulumi destroy
```

For production stacks, do not run `pulumi destroy` as a routine cleanup operation. Protect persistent resources, particularly databases, DNS zones, certificates, and shared networking infrastructure.

### 12\. Key takeaways

After completing this module, you should understand the complete lifecycle of production load balancing on AWS:

| Area              | Skills acquired                                   |
| ----------------- | ------------------------------------------------- |
| High availability | Multi-AZ architecture and failure-domain planning |
| Global traffic    | Route 53 and Global Accelerator                   |
| Disaster recovery | Multi-region architectures, RTO, and RPO          |
| Deployments       | Blue-green and canary releases                    |
| Containers        | ECS/EKS integration and autoscaling               |
| Security          | TLS, WAF, private networking, IAM                 |
| Infrastructure    | Reusable Pulumi components and stacks             |
| Operations        | CloudWatch, logs, alarms, and runbooks            |
| Optimization      | Performance, capacity, and cost management        |

### Official documentation and further reading

These are useful references for the concepts and implementation details covered in this module.

* [AWS Global Accelerator — How it works](https://docs.aws.amazon.com/global-accelerator/latest/dg/introduction-how-it-works.html?utm_source=chatgpt.com).

* [Route 53 — Complex health-check configurations](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/dns-failover-complex-configs.html?utm_source=chatgpt.com).

* [Route 53 — Weighted routing](https://docs.aws.amazon.com/en_en/Route53/latest/DeveloperGuide/routing-policy-weighted.html?utm_source=chatgpt.com).

* [ALB — Zonal shift](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/start-zonal-shift.html?utm_source=chatgpt.com).

* [ARC — Zonal autoshift](https://docs.aws.amazon.com/r53recovery/latest/dg/arc-zonal-autoshift.how-it-works.about.html?utm_source=chatgpt.com).

* [ALB — Target groups and configuration](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html?utm_source=chatgpt.com).

* [ALB — Target-group stickiness and blue-green deployments](https://docs.aws.amazon.com/prescriptive-guidance/latest/load-balancer-stickiness/target-group-stickiness.html?utm_source=chatgpt.com).

Course completed

You have now covered all eight modules of AWS Load Balancing, progressing from fundamental ELB concepts to production architecture, global traffic management, and disaster recovery.

The final capstone brings together ALB, ECS Fargate, Route 53, ACM, WAF, CloudWatch, and Pulumi into one practical production-oriented architecture.
