### AWS Load Balancing — Module 4: Health Checks, Resilience, and Traffic Management

Level: Intermediate · Infrastructure as Code: Pulumi Python · Shell: Bash · Platform: AWS

### Module objectives

In this module, you'll learn how AWS load balancers detect unhealthy backends, stop routing traffic to failing targets, and handle deployments and infrastructure failures without unnecessarily interrupting users.

By the end, you'll be able to:

* Configure ALB and NLB target group health checks.

* Interpret target health states and diagnose failed health checks.

* Use slow start, deregistration delay, and connection draining appropriately.

* Understand NLB fail-open behavior and Availability Zone resilience.

* Deploy replacement application instances while maintaining service availability.

* Troubleshoot failures using AWS CLI, application logs, and CloudWatch metrics.

### 1\. Understanding target group health checks

A load balancer needs a reliable way to determine whether a backend can receive traffic. A running EC2 instance or ECS task isn't necessarily a healthy application: its process may be running while its HTTP server, database connection pool, or critical dependency is broken.

AWS Elastic Load Balancing uses target group health checks to periodically evaluate registered targets.

Load balancer

Schedules health checks

Target health-check endpoint

For example: GET /health

Healthy

Eligible for routing

Unhealthy

Normally excluded from routing

### 1.1 Health-check configuration parameters

The main settings for ALB and NLB target groups are:

| Parameter           | Meaning                                                                             |
| ------------------- | ----------------------------------------------------------------------------------- |
| Protocol            | Protocol used to probe the target, such as HTTP, HTTPS, TCP, or TLS where supported |
| Path                | HTTP request path, such as /health                                                  |
| Port                | Port used for the health check; commonly the traffic port                           |
| Interval            | Time between health-check attempts                                                  |
| Timeout             | Maximum time allowed for an individual check                                        |
| Healthy threshold   | Consecutive successes required to move an unhealthy target to healthy               |
| Unhealthy threshold | Consecutive failures required to mark a healthy target unhealthy                    |
| Matcher             | Accepted HTTP status codes for HTTP/HTTPS health checks                             |

The exact available parameters depend on the load balancer, target type, and health-check protocol. For example, TCP health checks do not evaluate HTTP status codes.

Consider an ALB target group with these illustrative settings:

```text
Protocol:             HTTP
Path:                 /health
Port:                 traffic port
Interval:             15 seconds
Timeout:              5 seconds
Healthy threshold:    2
Unhealthy threshold:  3
Matcher:              200
```

If the endpoint repeatedly returns `500`, the target can become unhealthy after the configured failure threshold is reached. Actual transition timing depends on the health-check schedule, response time, and configuration.

Important: The health-check interval is not a guaranteed failover time. Don't assume that a target will be removed exactly `interval × threshold` seconds after a failure.

### 1.2 Choosing the correct health-check protocol

* HTTP/HTTPS: Appropriate for web applications where a specific endpoint can report application readiness.

* TCP: Confirms that a connection can be established, but doesn't prove that the application can process requests correctly.

* TLS: Checks TLS connectivity where supported; it doesn't establish full application correctness.

* HTTPS health checks: Can validate the response returned over HTTPS, but must be configured with the correct target protocol and certificate behavior.

For an HTTP application, prefer a dedicated health endpoint rather than using the homepage. The homepage may perform expensive operations or return redirects that are unsuitable for health checks.

### 2\. Designing application-specific health endpoints

A good health endpoint reflects whether the application is ready to serve its intended traffic.

There are three useful concepts:

* Liveness: Is the process alive, or is it irrecoverably stuck?

* Readiness: Can this instance accept application traffic right now?

* Dependency health: Are critical dependencies, such as a database, available?

These concepts are related but not interchangeable. A load balancer's health check generally needs to answer a routing question: Should requests be sent to this target?

For example, an application might expose:

```text
/health/live
/health/ready
/health
```

A liveness endpoint might return `200` while the process is running. A readiness endpoint might additionally verify that the application has completed startup and can perform its essential work.

Avoid making every health check depend on every external service. If a nonessential downstream service becomes unavailable and every target consequently fails its health checks, the load balancer might remove all backends even though they could still serve most requests.

For ALB HTTP health checks, redirects should generally be avoided: configure the health endpoint to return a direct success response instead of redirecting to a login page or another path.

### Example: FastAPI health endpoints

```python
from fastapi import FastAPI, Response, status

app = FastAPI()
application_ready = False

@app.get("/health/live")
async def liveness():
    return {"status": "alive"}

@app.get("/health/ready")
async def readiness(response: Response):
    if not application_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}

    return {"status": "ready"}
```

The example illustrates the endpoints, but `application_ready` must be updated by your startup and shutdown lifecycle logic in a real application. A production readiness check should reflect actual initialization and essential dependency requirements.

The ALB target group can use `/health/ready` as its health-check path. The endpoint should respond quickly and avoid expensive work.

### 3\. Target health states and reason codes

The AWS CLI reports target health using a state and, when applicable, a reason code. These are essential for distinguishing application failures from configuration problems. Elastic Load Balancing +1

| State       | Meaning                                                                                    | What to investigate                                         |
| ----------- | ------------------------------------------------------------------------------------------ | ----------------------------------------------------------- |
| initial     | Registration or initial health checks are in progress                                      | Wait for checks; verify startup time                        |
| healthy     | Target passed its health checks                                                            | Confirm application-level behavior too                      |
| unhealthy   | Health checks failed or the target is otherwise unhealthy                                  | Endpoint, port, security groups, logs                       |
| draining    | Target is being deregistered                                                               | In-flight requests and shutdown timing                      |
| unused      | Target isn't currently eligible for routing                                                | Listener rules, registration, AZ enablement, instance state |
| unavailable | Health status cannot be determined or health checks are disabled, depending on the service | Health-check configuration and service state                |

NLB target groups can also report `unhealthy.draining` in applicable situations, so don't assume ALB and NLB expose exactly the same state machine. Elastic Load Balancing +1

### Inspect target health with Bash

Set your target group ARN:

```bash
export AWS_REGION="eu-west-2"
export TG_ARN="arn:aws:elasticloadbalancing:eu-west-2:123456789012:targetgroup/example/abcdef1234567890"

aws elbv2 describe-target-health \
  --region "$AWS_REGION" \
  --target-group-arn "$TG_ARN" \
  --query 'TargetHealthDescriptions[].{
    Target:Target.Id,
    Port:Target.Port,
    State:TargetHealth.State,
    Reason:TargetHealth.Reason,
    Description:TargetHealth.Description
  }' \
  --output table
```

The ARN above is a placeholder. Replace it with the actual target group ARN.

To inspect only unhealthy targets:

```bash
aws elbv2 describe-target-health \
  --region "$AWS_REGION" \
  --target-group-arn "$TG_ARN" \
  --query 'TargetHealthDescriptions[?TargetHealth.State==`unhealthy`].{
    Target:Target.Id,
    State:TargetHealth.State,
    Reason:TargetHealth.Reason,
    Description:TargetHealth.Description
  }' \
  --output table
```

Common reason codes include:

* `Target.ResponseCodeMismatch`: the target returned an HTTP status code outside the configured matcher.

* `Target.Timeout`: the target did not respond within the allowed time.

* `Target.FailedHealthChecks`: the health check failed.

* `Target.NotInUse`: the target group isn't configured for active use, or the target's AZ isn't enabled.

* `Target.InvalidState`: the target is in an invalid state, such as a stopped or terminated instance.

The reason code is the starting point for diagnosis, not necessarily the root cause. Elastic Load Balancing +1

### 4\. Slow start, deregistration delay, and connection draining

Health checks determine whether a target is eligible to receive traffic. Lifecycle settings control how traffic is introduced to or removed from a target.

### 4.1 Slow start

ALB target groups support slow start, which gradually increases the traffic share sent to newly healthy targets over a configured period.

For example, suppose an application needs time to warm caches and initialize connection pools. Without slow start, a newly healthy target may receive its normal traffic share immediately.

With slow start, traffic increases gradually instead.

Illustrative traffic ramp-up

New target becomes healthy

0%

During warm-up

Increasing share

Warm-up completed

Normal share

Conceptual illustration, not a guaranteed request percentage at each point in time.

Important considerations:

* ALB slow start duration can be configured from 30 to 900 seconds.

* It applies to newly registered targets as they become healthy, subject to slow-start eligibility rules.

* Existing healthy targets don't automatically enter slow start when the attribute is enabled.

* Slow start cannot be enabled with the `least_outstanding_requests` or `weighted_random` routing algorithms.

Elastic Load Balancing +1

Slow start is useful for applications that need to warm up, but it does not replace readiness checks or application-level autoscaling.

### 4.2 Deregistration delay and connection draining

When a target is deregistered, the load balancer stops sending it new requests and allows in-flight work to finish during the draining period.

The default ALB target group deregistration delay is 300 seconds, and the supported range is 0–3600 seconds for applicable target groups. Elastic Load Balancing +1

Consider a deployment where an ECS task is serving a request that takes 45 seconds to complete. If the task is stopped immediately, the request may fail. With suitable draining and shutdown configuration, the application can finish the request before exiting.

Choose a delay based on:

* Maximum expected request duration.

* Long-running uploads or downloads.

* Persistent connections and streaming.

* Application shutdown behavior.

* Deployment and scale-in timeouts.

A long delay is not automatically safer. It can slow deployments and scale-in operations. For long-lived TCP connections, the right strategy depends on protocol behavior and whether clients can reconnect safely.

### 4.3 Configure target group attributes using Pulumi

The following example creates an ALB target group in an existing VPC. It configures an HTTP health check, slow start, and deregistration delay.

Install the required packages:

```bash
python -m venv .venv
source .venv/bin/activate
pip install pulumi pulumi-aws
```

Create `__main__.py`:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
target_port = config.get_int("targetPort") or 8000

target_group = aws.lb.TargetGroup(
    "app-target-group",
    port=target_port,
    protocol="HTTP",
    target_type="instance",
    vpc_id=vpc_id,
    health_check=aws.lb.TargetGroupHealthCheckArgs(
        enabled=True,
        protocol="HTTP",
        path="/health/ready",
        port="traffic-port",
        matcher="200",
        interval=15,
        timeout=5,
        healthy_threshold=2,
        unhealthy_threshold=3,
    ),
    slow_start=60,
    deregistration_delay=60,
    tags={
        "Name": "app-target-group",
        "ManagedBy": "Pulumi",
    },
)

pulumi.export("targetGroupArn", target_group.arn)
pulumi.export("targetGroupName", target_group.name)
```

Configure the existing VPC and application port:

```bash
pulumi config set vpcId vpc-0123456789abcdef0
pulumi config set targetPort 8000
pulumi up
```

Use a VPC ID from your account. The example assumes an HTTP application on port `8000` with a working `/health/ready` endpoint.

Important: This creates the target group and its attributes, not the complete load-balancing stack. You'll still need compatible registered targets, security group rules, and a listener rule forwarding traffic to this target group. For an instance target group, the registered instances must also be reachable on the configured port.

If you already have a target group and want to change its attributes through the AWS CLI instead:

```bash
aws elbv2 modify-target-group-attributes \
  --region "$AWS_REGION" \
  --target-group-arn "$TG_ARN" \
  --attributes \
    Key=slow_start.duration_seconds,Value=60 \
    Key=deregistration_delay.timeout_seconds,Value=60
```

Avoid applying the example's values blindly to production. A 60-second draining period is appropriate only if it accommodates the application's actual request and shutdown behavior.

### 5\. NLB fail-open behavior and Availability Zone resilience

### 5.1 What happens when all targets are unhealthy?

A common misconception is that an AWS load balancer always stops sending traffic when every backend fails its health checks.

That isn't necessarily true.

For ALB, when a target group contains only unhealthy registered targets, the load balancer can fail open and route requests to those targets anyway. NLB also supports fail-open behavior when its applicable target-health conditions are met. The exact behavior depends on the load balancer, target group, and health configuration. Elastic Load Balancing +1

Why would AWS do this? If health checks are reporting failures because of an incorrect health endpoint, a dependency problem, or an overly strict threshold, an unhealthy target might still be able to serve some requests. Sending traffic to all targets can sometimes be better than refusing all traffic.

However, fail-open is not a guarantee of availability. If every backend is genuinely broken, requests can still fail.

For ALB, target group health settings also support policies that influence DNS failover and routing when healthy target counts fall below configured thresholds. These settings should be evaluated separately from the all-targets-unhealthy fail-open behavior. Elastic Load Balancing +1

### 5.2 Availability Zones and cross-zone load balancing

A load balancer can be deployed across multiple Availability Zones (AZs). The traffic distribution behavior depends on the load balancer type and its cross-zone configuration.

Without cross-zone load balancing

AZ A

Targets in AZ A

AZ B

Targets in AZ B

With cross-zone load balancing enabled

Load balancer nodes can distribute traffic across healthy targets in enabled AZs.

The effective behavior depends on the load balancer type and target group settings.

Key differences:

* ALB: Cross-zone load balancing is enabled at the load balancer level by default.

* NLB: Cross-zone load balancing is disabled by default at the load balancer level, though it can be enabled. Target group attributes can also override inherited behavior.

* GWLB: Cross-zone behavior and appliance traffic symmetry need special consideration because network inspection appliances often depend on flow consistency.

Elastic Load Balancing +2

Cross-zone distribution can help when one AZ has fewer healthy targets than another. It can also increase cross-AZ traffic and data-transfer costs. Without it, zonal traffic distribution and target capacity need careful planning.

For resilient applications:

* Deploy sufficient backend capacity across at least two AZs.

* Ensure each enabled AZ has appropriate routing and healthy targets.

* Avoid relying on a single instance or a single AZ.

* Monitor healthy target counts and application error rates.

* Test AZ failure scenarios rather than assuming that multi-AZ deployment alone guarantees resilience.

### 6\. Application startup, graceful shutdown, and deployment interruptions

Health checks and draining work best when the application lifecycle is designed around them.

### 6.1 A safe application lifecycle

### 1

Start

Initialize the application, configuration, and essential dependencies.

### 2

Become ready

Return success from the readiness endpoint only when traffic can be served.

### 3

Serve traffic

Process requests and remain responsive to health checks.

### 4

Begin shutdown

Stop accepting new work and deregister the target as part of the deployment or scaling process.

### 5

Drain and exit

Allow in-flight requests to complete within the configured deadline, then terminate cleanly.

A critical distinction: marking a target unhealthy is not the same as deliberately deregistering it for a deployment. Health checks control eligibility for new traffic, whereas deregistration initiates the configured draining behavior.

For ECS deployments, the service scheduler and load-balancer integration manage task registration and deregistration. The task's shutdown grace period, container stop timeout, application signal handling, and load-balancer deregistration delay must be compatible. A delay configured on the target group does not by itself guarantee that the container will remain alive long enough to finish every request.

For EC2 Auto Scaling, attach the target group to the Auto Scaling group and configure the appropriate health-check integration and lifecycle behavior. For Kubernetes workloads, coordinate Pod readiness, termination grace periods, endpoint removal, and load-balancer controller behavior.

### 6.2 Example graceful shutdown in FastAPI

FastAPI supports application lifespan handlers. Here's a simplified example of managing readiness during startup and shutdown:

```python
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status

ready = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    global ready

    # Initialize required resources here.
    ready = True

    try:
        yield
    finally:
        # Stop reporting readiness before releasing resources.
        ready = False
        await asyncio.sleep(0)
        # Close database pools and other resources here.

app = FastAPI(lifespan=lifespan)

@app.get("/health/ready")
async def readiness(response: Response):
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready"}

    return {"status": "ready"}
```

This demonstrates lifecycle coordination, not a complete production shutdown implementation. In production, the server must also handle termination signals, stop accepting new work, and enforce a deadline for in-flight requests. The exact sequence depends on the ASGI server and deployment platform.

### 7\. Troubleshooting unhealthy targets and traffic failures

Use a consistent diagnostic sequence instead of changing health-check thresholds at random.

### Step 1: Inspect target health

```bash
aws elbv2 describe-target-health \
  --region "$AWS_REGION" \
  --target-group-arn "$TG_ARN" \
  --output json
```

Identify the state, reason code, target ID, and port.

### Step 2: Check the application locally

On the target, test the health endpoint and application listener:

```bash
curl -i --max-time 5 http://127.0.0.1:8000/health/ready
```

A local success does not prove that the load balancer can reach the application. It does help distinguish an application-level issue from a network-level issue.

### Step 3: Check port binding and processes

On a Linux target:

```bash
ss -lntp
ps aux | grep -E 'uvicorn|gunicorn|python' | grep -v grep
```

If the application listens only on `127.0.0.1`, remote connections from the load balancer won't reach it. For an EC2-hosted service, the application commonly needs to bind to an appropriate interface such as `0.0.0.0` inside its network namespace.

### Step 4: Inspect security groups and networking

Confirm that:

* The target is listening on the expected port.

* The target's security group permits inbound traffic from the load balancer's security group where applicable.

* The load balancer can reach the target through the VPC's routing and network controls.

* Network ACLs allow the required traffic and return traffic.

* The target is registered with the correct target group and an enabled AZ.

For ALB, an incorrect health-check path or an HTTP response outside the configured matcher is another common cause of failure.

### Step 5: Inspect logs and metrics

For an EC2-hosted application using systemd:

```bash
sudo journalctl -u myapp --since "15 minutes ago" --no-pager
```

Replace `myapp` with your actual service name.

For ECS, retrieve task logs through CloudWatch Logs or the configured log driver. Inspect target group and load-balancer CloudWatch metrics, including healthy and unhealthy host counts, HTTP errors, and latency.

### Troubleshooting reference

| Symptom                         | Likely causes                                                       | First action                                                   |
| ------------------------------- | ------------------------------------------------------------------- | -------------------------------------------------------------- |
| Target.Timeout                  | Network restrictions, wrong port, blocked route, slow application   | Test reachability and inspect security groups                  |
| Target.ResponseCodeMismatch     | Wrong path, redirect, authentication, HTTP 5xx                      | Call the endpoint and compare the status code with the matcher |
| Target.FailedHealthChecks       | Connection failure or repeated unsuccessful probes                  | Inspect reason details, listener process, and application logs |
| Target.NotInUse                 | Incorrect listener rule or AZ configuration                         | Inspect listener forwarding and target registration            |
| HTTP 502                        | Target connection reset, invalid response, protocol mismatch        | Correlate ALB access logs with backend logs                    |
| HTTP 503                        | No eligible targets or other service-level conditions               | Check target health and routing configuration                  |
| Requests fail during deployment | Premature termination, insufficient draining, long-running requests | Coordinate deregistration delay and application shutdown       |

The status codes are symptoms, not definitive root causes. For example, a 503 can have causes beyond an empty target group, and a 502 can result from multiple backend communication failures.

### 8\. Hands-on labs

These labs build on the target group and Pulumi concepts introduced above. Use an existing test VPC and backend infrastructure, or adapt your previous module's ALB deployment. All commands use Bash.

### Lab 1 — Configure application-specific health checks

Goal: Create a health check that reflects application readiness.

* Add `/health/ready` to your application.

* Configure the target group's health-check path, timeout, interval, and thresholds using Pulumi.

* Deploy the changes:

```bash
pulumi preview
pulumi up
```

4\. Verify the target health:

```bash
aws elbv2 describe-target-health \
  --region "$AWS_REGION" \
  --target-group-arn "$TG_ARN" \
  --output table
```

5\. Confirm that the target becomes healthy and that the application returns the expected response.

### Lab 2 — Simulate backend failures

Goal: Observe the relationship between application failures and load-balancer health states.

* Confirm that at least two healthy targets are registered.

* Temporarily make one target's health endpoint return HTTP 503.

* Observe the target's health status and reason code.

* Confirm that the other healthy target continues to serve traffic.

* Restore the endpoint and observe recovery.

For an existing test endpoint, you can use a temporary failure flag in your application. Avoid stopping a shared production service or changing production health checks for this exercise.

### Lab 3 — Replace a backend without intentionally interrupting traffic

Goal: Understand target registration, readiness, and traffic shifting.

* Start a replacement backend in the same target group or prepare a new target group.

* Wait for the replacement target to become healthy.

* Verify that the original target is still healthy.

* Deregister the old target after the replacement is ready.

* Observe the old target's draining state and verify application responses.

Use a deployment strategy appropriate to your environment. For ECS, prefer the ECS service deployment mechanism rather than manually manipulating task registrations behind the service scheduler.

### Lab 4 — Test graceful shutdown and connection draining

Goal: Verify that requests can finish during a controlled deployment.

* Create a test endpoint that takes several seconds to complete.

* Start a request and then initiate target deregistration.

* Inspect the target health state:

```bash
aws elbv2 describe-target-health \
  --region "$AWS_REGION" \
  --target-group-arn "$TG_ARN" \
  --query 'TargetHealthDescriptions[].{
    Target:Target.Id,
    State:TargetHealth.State,
    Reason:TargetHealth.Reason
  }' \
  --output table
```

* Verify whether the request completes before the target exits.

* Repeat with a deliberately shorter deregistration delay in a disposable environment and compare the behavior.

Remember that graceful draining depends on the application, protocol, deployment platform, and process termination behavior—not just the target group attribute.

### Lab 5 — Diagnose an unhealthy target

Goal: Follow a repeatable troubleshooting workflow.

Intentionally introduce one problem at a time:

* Incorrect health-check path.

* Incorrect target port.

* Application bound only to loopback.

* Security group rule that blocks the health-check connection.

* Health endpoint that responds too slowly.

For each scenario, inspect the target health reason code, test the endpoint, inspect the relevant configuration, and review application logs. Fix the root cause and confirm recovery.

### 9\. Operational best practices

* Use a lightweight readiness endpoint that responds quickly and accurately.

* Set thresholds based on the application's failure and recovery characteristics.

* Deploy targets across multiple AZs and retain enough healthy capacity to handle failures.

* Coordinate health checks, draining, application shutdown, and deployment timeouts.

* Use slow start for workloads that benefit from gradual traffic ramp-up.

* Monitor healthy target counts and error rates; a healthy target does not guarantee a healthy end-to-end application.

* Test fail-open scenarios and understand the consequences of sending traffic to unhealthy targets.

* Manage infrastructure through Pulumi and validate changes with `pulumi preview` before applying them.

### Official AWS references

* [ALB target group health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/target-group-health-checks.html?utm_source=chatgpt.com)

* [NLB target group health checks](https://docs.aws.amazon.com/elasticloadbalancing/latest/network/target-group-health-checks.html?utm_source=chatgpt.com)

* [ALB target group attributes and slow start](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/edit-target-group-attributes.html?utm_source=chatgpt.com)

* [ALB target groups, draining, and routing](https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-target-groups.html?utm_source=chatgpt.com)

* [Pulumi AWS TargetGroup resource reference](https://www.pulumi.com/registry/packages/aws/api-docs/lb/targetgroup/?utm_source=chatgpt.com)

Module 4 takeaway: Reliable load balancing requires more than distributing requests. Health checks must reflect application readiness, target lifecycle settings must support graceful deployments, and multi-AZ architectures must be designed and tested for real failures.
