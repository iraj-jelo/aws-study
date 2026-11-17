### Phase 4 — Compute

### Module 10 — Choosing the Right Compute Service

Architecture decisions, operational trade-offs, and production-ready AWS design

In this final module, you'll bring together the compute services covered throughout Phase 4 and learn how to choose the right one for a real application.

We'll use the same FastAPI application across three deployment designs, provision infrastructure with Pulumi and Python, and compare each architecture on reliability, security, operational effort, scalability, and cost.

### Learning objectives

By the end of this module, you should be able to:

* Compare Amazon EC2, Amazon ECS on AWS Fargate, AWS Lambda, and Amazon EKS.

* Explain the trade-off between infrastructure control and operational responsibility.

* Choose compute services based on workload patterns and scaling requirements.

* Design appropriate availability, networking, identity, and security boundaries.

* Estimate costs beyond compute pricing alone.

* Plan migrations from virtual machines to containers or serverless architectures.

* Implement and justify a production-ready deployment using Pulumi.

### 1\. The four compute models

![Elastic Compute Cloud (EC2) - GeeksforGeeks](https://images.openai.com/static-rsc-4/NeUsXNm4kQSDwei7GcWVRJ19nKX2X6oIII3BNfuoZyzxN-szfL1G2XS8uUghKYckd46nyC4GW0L9e0eEQTJ4e-wP_BlBUN6Gk1HYllrFDfWMrx8zu0mqWG_Zmaoau1EDGjhMCfh5rrBHj752SDUzQYwvCX4Arvnzg7wuyr_rsl02pCwEfa8UrX1OSfUmmxvJ?purpose=fullsize)

### A. Amazon EC2 — Virtual machines

You provision virtual servers and manage the operating system, runtime, application, and much of the infrastructure configuration.

Best suited for: Legacy applications, specialized operating-system requirements, persistent processes, and workloads needing detailed infrastructure control.

You manage more; you control more.

![Amazon Elastic Container Service - Overview of Deployment Options on AWS](https://images.openai.com/static-rsc-4/jKCG81lURRpZ0u9xpfKDf6FSElYYSpBClJtsda8RaPhXxWmDC-iWQZtK2_-h6bNoruK1GRUkxPQ04V7ymWVU0aYr2eDbXDu5C2pKUVnE_lfJrGeD2g5kdAm5dhpuFMOFZBfsMRNKjTPm2o_7Ta_g75B7Sjl_7GcKu_dM_pa8A40ser6Fdd5OJcigzH4zU6eL?purpose=fullsize)

### B. Amazon ECS on Fargate — Managed containers

You package the application into a container and define how ECS should run it. Fargate manages the underlying compute infrastructure.

Best suited for: Long-running web APIs, background workers, and containerized services without needing to manage EC2 worker nodes.

You manage containers and services, not the host fleet.

![Agentic workflow patterns - AWS Prescriptive Guidance](https://images.openai.com/static-rsc-4/gzPDOxOCEmWCpsJYG-C3-3jTFLMkLcXaOICF7lBixW495Iox08LC0ehFgTH4BRrL3IxihWO_E4tvjlsJMMw6q3lEY62C1pohaVF9vfvoLoYrUjdYeX2gPMRSaECNO6aLwhBObNwanEduYx3BN8txui4YLZnYzAYqW8sVYoFLLd6Ydodt7wYejihctYiOY9_m?purpose=fullsize)

### C. AWS Lambda — Function-based compute

You deploy functions that execute in response to requests, events, or schedules. AWS manages the underlying servers.

Best suited for: Event processing, lightweight APIs, scheduled tasks, and workloads with variable or intermittent demand.

You manage functions and integrations, not servers.

![Basic Terminologies of Kubernetes and Amazon EKS Cluster | by Sanjal S Eralil | Medium](https://images.openai.com/static-rsc-4/qqbwQAzIgQKbEqzLyrninLhakv-he-CB6DK0qy-VV-IaaKje7SB_C5SVSFFPTox87FFomH1On9cUEjC8cWhIChT3JccywhZjVksYkPWxLgCULEzKtcpQ-LevgwY81woVJ0TCkO26cQGz8xGuMwScS8HDy2uPahjU5Z8afo1Arut5yS3lC5IpnV3USw07qJP3?purpose=fullsize)

### D. Amazon EKS — Managed Kubernetes

You run applications using Kubernetes objects such as Deployments, Services, and Pods. AWS manages the Kubernetes control plane, while you remain responsible for significant parts of cluster and workload operations.

Best suited for: Organizations needing Kubernetes APIs, ecosystem compatibility, advanced orchestration, or established Kubernetes platform practices.

AWS manages the control plane; you still manage substantial platform complexity.

An important distinction: ECS is the container orchestrator; Fargate is a compute option. ECS can also run tasks on EC2. Likewise, EKS can run workloads on managed nodes or use Fargate profiles for supported Pod workloads.

### 2\. Compare the operational trade-offs

| Dimension                   | EC2                          | ECS + Fargate              | Lambda                                | EKS                                   |
| --------------------------- | ---------------------------- | -------------------------- | ------------------------------------- | ------------------------------------- |
| Unit of deployment          | VM/application               | Container/task             | Function                              | Container/Pod                         |
| Host management             | You manage it                | AWS manages hosts          | AWS manages servers                   | Shared responsibility                 |
| Scaling                     | ASG and policies             | ECS service scaling        | Managed concurrency scaling           | Kubernetes autoscaling                |
| Long-running services       | Excellent                    | Excellent                  | Not designed for indefinite processes | Excellent                             |
| Variable, event-driven work | Possible                     | Possible                   | Excellent                             | Possible                              |
| OS-level control            | High                         | Limited                    | Limited                               | Depends on node model                 |
| Operational complexity      | Medium–high                  | Medium                     | Low–medium                            | High                                  |
| Cost model                  | Instance capacity and extras | Task CPU/memory and extras | Requests, duration, and extras        | Cluster compute and platform overhead |

These are general tendencies, not absolute rankings. Actual complexity and cost depend on workload design, traffic, availability requirements, and team experience.

### Operational responsibility

### EC2

Most host control

You manage OS patching, instance configuration, capacity, application deployment, and host-level troubleshooting. Auto Scaling can automate replacement and capacity adjustment, but it doesn't remove host-management responsibilities.

### ECS on Fargate

You manage container images, task definitions, service configuration, IAM, networking, deployments, and observability. AWS manages the underlying hosts.

### Lambda

You manage function code, dependencies, permissions, invocation behavior, concurrency, and integrations. You still need to engineer retries, idempotency, monitoring, and failure handling.

### EKS

AWS manages the control plane, but you must understand Kubernetes access, networking, workload configuration, scheduling, resource requests, upgrades, and observability. The exact workload infrastructure responsibilities depend on the chosen node model.

### 3\. Scaling, availability, and workload characteristics

### How scaling differs

* EC2: An Auto Scaling group adjusts the number of instances based on demand or policies. Application startup and instance initialization affect how quickly new capacity becomes useful.

* ECS on Fargate: ECS service auto scaling adjusts the desired number of tasks. Container startup, image pulls, health checks, and load balancer registration affect scale-out time.

* Lambda: AWS manages execution capacity, with concurrency controls, quotas, and scaling behavior that must fit the workload. Downstream databases and APIs can still become bottlenecks.

* EKS: Kubernetes schedules Pods and can scale workloads and nodes when configured with suitable autoscaling components. Pod scaling and node capacity scaling are separate concerns.

### Availability is an architecture decision

No compute service automatically makes an application highly available.

For a production web API, consider:

* Multiple Availability Zones where supported.

* Health checks and replacement of unhealthy capacity.

* Load balancing and sensible timeout settings.

* Database availability and connection management.

* Graceful deployments and rollback.

* Backups, recovery procedures, and tested failure scenarios.

A single EC2 instance can fail. A multi-AZ ECS service can also fail if its database, permissions, or network dependencies are misconfigured. The same principle applies to Lambda and EKS: reliability depends on the whole system.

### 4\. Security boundaries

All four choices need least-privilege identity, controlled network access, secure deployment artifacts, secrets management, and monitoring.

| Concern                 | EC2                                | ECS on Fargate                      | Lambda                                 | EKS                                                          |
| ----------------------- | ---------------------------------- | ----------------------------------- | -------------------------------------- | ------------------------------------------------------------ |
| Workload identity       | EC2 instance role                  | Task IAM role                       | Execution and function roles           | IAM integration and Kubernetes service accounts              |
| Network boundary        | Subnets and security groups        | Task ENIs, subnets, security groups | Optional VPC attachment                | VPC networking and Kubernetes network controls               |
| Secret handling         | Secrets Manager or Parameter Store | Task secrets integration            | Secrets Manager or Parameter Store     | External secret integrations or controlled secret management |
| Main additional concern | Host hardening                     | Image and task isolation            | Invocation permissions and concurrency | Cluster access and workload isolation                        |

Remember the difference between the Lambda execution role and the Lambda resource-based policy: the execution role grants the function permission to call AWS services, while a resource policy can control which principals or services may invoke it.

For ECS, distinguish the task execution role (used for operations such as pulling images and initializing configured logs or secrets) from the task role (used by application code to access AWS services).

For EKS, Kubernetes permissions and AWS IAM permissions solve related but distinct access-control problems. Both must be designed correctly.

### 5\. Cost trade-offs: compare the whole system

Compute pricing alone is not enough. Include load balancers, networking, logging, storage, observability, and any minimum capacity required for availability.

EC2 cost drivers

* Instance uptime and instance family.

* EBS volumes and snapshots.

* Load balancer and NAT Gateway charges, if used.

* Unused capacity and OS maintenance effort.

Fargate cost drivers

* Requested task vCPU and memory while running.

* Task count, uptime, and deployment overlap.

* Load balancing, image storage, logs, and networking.

* Capacity reserved for availability and traffic spikes.

Lambda cost drivers

* Number of invocations and execution duration.

* Memory allocation and architecture.

* Provisioned concurrency, where configured.

* API Gateway, logs, data transfer, and VPC networking where applicable.

EKS cost drivers

* Kubernetes control-plane charges.

* Worker nodes or Fargate compute.

* Load balancers, storage, networking, and observability.

* Platform engineering and operational overhead.

### Which one is cheapest?

There is no universal winner.

* A continuously busy application may be economical on appropriately sized EC2 instances.

* ECS on Fargate can be attractive when simpler operations justify the per-task cost.

* Lambda can be economical for intermittent workloads, but sustained high utilization and other service charges may change the result.

* EKS can be justified when Kubernetes capabilities and organizational standards deliver sufficient value to offset platform overhead.

Cost exercise: Compare equivalent traffic, CPU and memory requirements, availability targets, and logging for all candidates. Use the AWS Pricing Calculator and actual measurements rather than assuming that serverless always costs less.

### 6\. Three deployment designs for the same FastAPI application

For the lab, the application will expose three endpoints:

* `GET /` — return a basic health response.

* `GET /items` — return a sample list of items.

* `GET /health` — return a health-check response.

The application logic remains the same across all three designs. Only the deployment and execution model changes.

### Design A — EC2 with an Application Load Balancer

Internet

Public ALB

EC2 Auto Scaling group

Private application instances across two Availability Zones

Advantages

* Full OS and runtime control.

* Straightforward for applications that expect a VM.

* Can be economical with predictable, steady utilization.

Disadvantages

* Requires host patching, image management, and capacity planning.

* Instance bootstrap and deployment need careful handling.

* The team owns more of the operational lifecycle.

Pulumi resources: VPC/subnet references, security groups, EC2 launch template, Auto Scaling group, ALB, target group, listener, and IAM roles.

### Design B — ECS on Fargate with an Application Load Balancer

Internet

Public ALB

ECS service on Fargate

Container tasks in private subnets across two Availability Zones

Advantages

* No EC2 worker fleet to patch or resize.

* Repeatable image-based releases and rollbacks.

* Clear separation between application packaging and infrastructure.

Disadvantages

* Requires Docker and ECS concepts.

* Image pulls, task startup, and task networking require configuration.

* Task-level pricing and surrounding AWS services must be included in the cost model.

Pulumi resources: ECR repository, ECS cluster, task definition, task execution role, task role, Fargate service, ALB, target group, listener, security groups, and logging configuration.

### Design C — Lambda behind API Gateway

Internet

API Gateway HTTP API

Lambda function

Managed execution with request-driven scaling

Advantages

* No server or container fleet to manage.

* Natural fit for request-driven execution and variable traffic.

* Integrates well with event-driven AWS services.

Disadvantages

* Runtime, execution duration, and concurrency constraints must be considered.

* Cold starts and downstream connection limits may affect latency.

* Existing ASGI applications may need a compatible adapter and deployment package.

Pulumi resources: Lambda execution role, function and deployment artifact, API Gateway HTTP API, integration, route, stage, invocation permissions, and CloudWatch log configuration.

### Important design detail

A standard FastAPI server is a long-running ASGI application. For the Lambda design, use a compatible adapter such as Mangum or another suitable integration, and ensure the handler is configured correctly. Do not assume that the same `uvicorn` startup command used on EC2 or ECS can be deployed unchanged as a Lambda function.

The three designs should use equivalent application behavior, representative traffic, comparable availability assumptions, and consistent security standards. That makes the comparison meaningful.

### 7\. Implement the comparison with Pulumi and Python

Use three separate Pulumi projects or stacks so each design can be deployed and destroyed independently. Reuse the same application code and, where possible, shared networking components.

### Suggested project layout

```text
compute-comparison/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── ec2/
│   ├── __main__.py
│   └── Pulumi.yaml
├── ecs/
│   ├── __main__.py
│   └── Pulumi.yaml
├── lambda/
│   ├── __main__.py
│   └── Pulumi.yaml
└── README.md
```

### Step 1 — Create the FastAPI application

`app/main.py`

```python
from fastapi import FastAPI

app = FastAPI(title="Compute Comparison API")

@app.get("/")
def root():
    return {"service": "compute-comparison", "status": "ok"}

@app.get("/items")
def list_items():
    return {"items": ["item-1", "item-2", "item-3"]}

@app.get("/health")
def health():
    return {"status": "healthy"}
```

`app/requirements.txt`

```text
fastapi
uvicorn[standard]
```

Run it locally:

```bash
python -m venv .venv
source .venv/bin/activate  # Linux/macOS

pip install -r app/requirements.txt
uvicorn main:app --app-dir app --reload
```

On Windows, activate the environment with `.venv\Scripts\activate` instead.

Test `http://127.0.0.1:8000/health`.

### Step 2 — Set up Pulumi

Install and configure the Pulumi CLI, authenticate to your chosen backend, and configure AWS credentials using your established secure identity workflow.

For each project:

```bash
pulumi new aws-python
python -m pip install -r requirements.txt
pulumi config set aws:region eu-west-3
```

Choose an AWS Region appropriate for your lab and account. The example above uses Paris; substitute another Region if necessary.

### Step 3 — Define each architecture

Use the Pulumi AWS provider resources corresponding to each design. The following is a resource-planning guide, not a complete deployable stack.

### EC2 stack

```python
# Core resource types
aws.ec2.LaunchTemplate(...)
aws.autoscaling.Group(...)
aws.lb.LoadBalancer(...)
aws.lb.TargetGroup(...)
aws.lb.Listener(...)
```

Add instance profiles, scoped security groups, health checks, and a user-data or image-based application deployment strategy.

### ECS Fargate stack

```python
aws.ecr.Repository(...)
aws.ecs.Cluster(...)
aws.iam.Role(...)
aws.ecs.TaskDefinition(...)
aws.ecs.Service(...)
aws.lb.LoadBalancer(...)
```

Also configure the listener, target group, execution-role permissions, task IAM role, container port, health checks, and logs.

### Lambda stack

```python
aws.iam.Role(...)
aws.lambda_.Function(...)
aws.apigatewayv2.Api(...)
aws.apigatewayv2.Integration(...)
aws.apigatewayv2.Route(...)
aws.apigatewayv2.Stage(...)
```

Package a compatible handler, grant API Gateway invocation permission, and configure logging and least-privilege execution permissions.

Pulumi resource names and required arguments depend on the selected provider version and architecture details. Consult the provider documentation when filling out each resource.

### Step 4 — Deploy, test, and destroy

For each stack:

```bash
pulumi preview
pulumi up
pulumi stack output
```

Record the application URL or other relevant outputs. Run the same endpoint tests against each deployment.

After testing:

```bash
pulumi destroy
```

Check the AWS console for resources that might remain outside the stack's managed lifecycle, such as manually created resources, retained logs, snapshots, or resources protected from deletion. Pay special attention to load balancers, NAT Gateways, public IP addresses, and other resources that can incur ongoing charges.

Do not hardcode AWS access keys, passwords, or secret values in source code. Use Pulumi configuration and appropriate secret handling for sensitive inputs.

### 8\. Migration paths: EC2 to containers or serverless

A migration should be driven by a specific business or engineering benefit, not simply by a desire to use a newer service.

Existing application on EC2

Understand dependencies, runtime, state, and deployment

Assess and modernize

Externalize state, configure health checks, automate builds, and manage secrets

Container migration

Package the app in Docker, publish to ECR, then deploy to ECS or EKS.

Serverless migration

Extract suitable request handlers or event-processing workloads into Lambda.

### A sensible migration sequence

* Assess: Identify OS dependencies, local files, background processes, network assumptions, and external integrations.

* Decouple: Move persistent state into suitable managed storage and remove reliance on instance-local state where appropriate.

* Automate: Create repeatable builds, tests, infrastructure definitions, and deployments.

* Containerize where appropriate: Create an image, scan it, and publish it to ECR.

* Deploy in parallel: Test the new architecture without immediately removing the old one.

* Validate: Compare latency, error rates, security, operational burden, and cost.

* Cut over gradually: Use a controlled traffic migration and retain a tested rollback path.

* Decommission: Remove old resources only after the new system is verified.

Not every application needs to migrate. Keeping a stable EC2 workload can be the right decision when the operational and financial benefits of changing are small.

### 9\. Interactive decision exercise

Choose the compute service you would initially recommend for each scenario. Select your answers and check them against the reasoning below.

1. A legacy application requires operating-system packages and a specialized host configuration.

EC2

ECS Fargate

Lambda

EKS

2. A Dockerized FastAPI API runs continuously and needs an ALB, private subnets, and rolling deployments.

EC2

ECS Fargate

Lambda

EKS

3. A function processes occasional object-upload events and performs a short operation.

EC2

ECS Fargate

Lambda

EKS

4. An organization already operates a Kubernetes platform and needs Kubernetes APIs and ecosystem tooling.

EC2

ECS Fargate

Lambda

EKS

Check answers

### 10\. Final lab — Choose and defend a production architecture

Your task is to compare the three FastAPI deployments built in this module and recommend one for a realistic production workload.

### Lab deliverables

0 of 7 complete

Reset

Deploy the same FastAPI endpoints on EC2, ECS Fargate, and Lambda.

Provision the infrastructure with Pulumi and Python.

Test endpoint correctness, health checks, and deployment behavior.

Document identity permissions, network boundaries, and secrets handling.

Compare scaling, availability, operational effort, and estimated monthly cost.

Write an architecture decision record explaining your recommendation.

Destroy test infrastructure and verify cleanup.

### Architecture decision record template

Use this template for your final recommendation.

# Architecture Decision Record: FastAPI Compute Platform

## Context
Describe the application, expected traffic, availability target, latency needs, and team experience.

## Options considered
- Amazon EC2 with an Application Load Balancer and Auto Scaling
- Amazon ECS on Fargate with an Application Load Balancer
- AWS Lambda behind API Gateway

## Decision
State the selected architecture and why it best fits the requirements.

## Security
Describe workload identity, network boundaries, secrets management, and least-privilege access.

## Reliability and scaling
Explain health checks, scaling policies, failure handling, deployment strategy, and recovery.

## Cost
Compare compute, networking, logging, storage, and operational overhead. State assumptions.

## Risks and trade-offs
Explain what the chosen architecture makes easier and what it makes harder.

## Rollback and migration
Describe how to reverse the deployment or move to another compute model if requirements change.

### Module 10 completion criteria

You have completed this module when you can:

* Explain why a workload belongs on EC2, ECS Fargate, Lambda, or EKS.

* Distinguish managed infrastructure from managed application operations.

* Design secure, highly available deployment patterns.

* Compare total cost using consistent assumptions.

* Implement and validate infrastructure with Pulumi.

* Defend your final architecture choice with evidence rather than personal preference.

Phase 4 is complete. The central lesson is that the best compute service is not necessarily the most managed or the most powerful. It is the one that meets the application's requirements with an acceptable balance of reliability, security, cost, and operational complexity.
