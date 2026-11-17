### Module 1 — Container Orchestration Fundamentals and AWS Architecture

Course: AWS ECS and EKS · Module 1 of 9

### 1\. Introduction to container orchestration

Container orchestration is the automated management of containers across one or more machines. It handles deploying applications, deciding where containers run, replacing failed workloads, scaling capacity, and connecting services.

Running a single container with Docker is straightforward. Operating dozens or hundreds of containers introduces additional problems:

* Which machine should run each container?

* What happens when a container or machine fails?

* How do applications discover one another?

* How do you release a new version without causing downtime?

* How do you allocate CPU and memory efficiently?

* How do you control network access and permissions?

Container orchestration systems address these problems by maintaining a desired application state and continually working to achieve it.

### 1.1 Essential orchestration concepts

![Container Orchestrator | Cloud Adoption Patterns](https://images.openai.com/static-rsc-4/eOKPx83wBMvIiXX6Z7O-9Z2cowcJVuwa7ZwUL-cZwwAxd2BiS4p26jokJFiB5-bU0h_ZpGHMk35rTqJNENuvVLqAD6UIFZIy9mQ0OXuyQlqYilR3UdcsUIe2odFfsaCtdk_jk1F29qqU3Yrg1AD6vUFw83_zSr09advfpndH3Z9nfA8FMR6F37jEsks8vi4V?purpose=fullsize)

Scheduling

The orchestrator chooses where workloads run based on available CPU and memory, placement constraints, availability requirements, and other scheduling rules.

![FlytePropeller Architecture - Flyte](https://images.openai.com/static-rsc-4/ULMKcVq8e68NV9qUcpp-QTeayHOWA_UA45twq1gNR_Zt0Ww8V4W0nOxxH40nQH1Pd2Z7Rtxp_sNwVK0EMDSAHieNA_5sk17IEBGzKGv1N9l99rtUHEoogRZSvHdA4YuTwBbtgkQD3UnY5jH-gPyjXERfkn8Zk9ODdb7zPn6fMQ6tX3ZJIl-i0c7yzlSYmNts?purpose=fullsize)

Desired state and reconciliation

You declare the intended configuration, such as three application replicas. The orchestrator compares the actual state with the desired state and attempts to correct differences.

![amazon ec2 - AWS ECS Private and Public Services - Stack Overflow](https://images.openai.com/static-rsc-4/XsjN-cYNXx2K02KQ4og5Qv_a9N6KFguL-kqtq_NViRFBoYxWof7eS7oquhyGl87JVPNcoOM0HaR_NlLLRnHIBHvvGUsj10cGpUj92gqBHW4osufmO-f6i9XmqyyV8AsjopdcL5RFJbgCnnKVU2UR9LFQjhVIdBm4SdF-oAcgONwHqA4DJxHAwf-t-jWCZXyq?purpose=fullsize)

Service discovery

Applications need a reliable way to find other services without depending on changing container IP addresses. Service discovery provides stable names or endpoints.

![Lesson 41: Cluster Autoscaling - Dynamic Node Provisioning at Scale](https://images.openai.com/static-rsc-4/hn2L3u1stEumL8b29Zq5rnt3Qa35jxrxGyndoeEWNw6YZPu3owcokt42ZGN3aEK8Y2YaBqjFaHGbJocag4Gq8__PwhRJjW-iCFKGkDT_9fMpBtjS4LRoyrrXYhJuP9aDoiITCqIipoP4c6WZx5sYUBK6VvkyWrsy5SLCe4UsaenJGiF02k48mS95hs-oI8Y8?purpose=fullsize)

Scaling

The orchestrator can increase or decrease the number of running application instances based on configured replica counts, CPU utilization, memory, requests, or other signals.

![Understanding Kubernetes for Data Engineers (Without the Confusing Jargon) | by Satyam Sahu | T3CH | Medium](https://images.openai.com/static-rsc-4/8v2_tagDoBcNAitHiOjylhnMKjxPztk5omTaa7s0rwPHaNOONqLyCp39pAZTao6WS0dSjGYXI5AL2jz6eENLeq1A0ei_q3ybIXxvmxkDI_d_6gFz9QYLI3oypeLwCErhLk9DhFxbbDwZTgzvZQnglck3XQDSOm2_FbOphr71MDtVGLUv8T0Co-p8IJhIve0C?purpose=fullsize)

Self-healing

When a container crashes or a workload becomes unhealthy, the orchestrator can replace or restart it. Recovery from a failed machine may require rescheduling workloads onto another machine with sufficient capacity.

These capabilities are related but distinct. Restarting a failed container does not necessarily recover its data, and creating more replicas does not automatically guarantee that traffic reaches healthy replicas.

### 1.2 The reconciliation model

A common orchestration workflow looks like this:

1\. Declare desired state

Example: run three replicas of API version 1.2

2\. Schedule workloads

Choose eligible compute capacity and placement

3\. Run and monitor containers

Evaluate health and actual state

4\. Reconcile differences

Replace failed workloads or adjust capacity

For example, if three replicas are desired but only two remain healthy, the orchestrator attempts to restore the required state. Whether it succeeds depends on available compute capacity, image availability, permissions, networking, and other dependencies.

This principle appears in both ECS and EKS, although they implement it through different APIs and control mechanisms.

### 2\. Docker images, containers, and networking

### 2.1 Images versus containers

A Docker image is a packaged, versioned filesystem and application configuration. A container is a running instance of that image with its own process environment and runtime configuration.

| Concept   | Purpose                                                            |
| --------- | ------------------------------------------------------------------ |
| Image     | Packages application code, dependencies, and runtime configuration |
| Container | Runs an image as an isolated process                               |
| Registry  | Stores and distributes container images                            |
| Volume    | Provides storage that can outlive a container                      |
| Network   | Enables communication between containers and other endpoints       |

Images are generally treated as immutable deployment artifacts. Instead of modifying a running container to release a new application version, you build and publish a new image and deploy it.

### 2.2 Image lifecycle

Source code

FastAPI application and dependencies

Docker build

Create an image from a Dockerfile

Container registry

Store the versioned image in Amazon ECR

Container runtime

ECS or EKS pulls and runs the image

Amazon Elastic Container Registry (ECR) is AWS's managed container registry. Both ECS and EKS can use private ECR repositories, subject to the correct IAM permissions and network access.

A container image tag such as `fastapi-api:1.0.0` is a convenient version label. Tags can be moved to different image contents unless repository policies prevent it. Image digests identify specific image contents more reliably.

### 2.3 Container networking

Containers need network connectivity for several purposes:

* Receiving requests from users or upstream services.

* Calling databases, APIs, and other dependencies.

* Downloading images and retrieving configuration.

* Sending logs and metrics to monitoring services.

The important distinction is between container networking and application exposure. A process listening on a container port is not necessarily reachable from the internet.

For example, a FastAPI process might listen on port `8000`. In a local Docker environment, you can publish that port with `-p 8000:8000`. In AWS, you typically configure the task or pod network, security groups, and service or load-balancing resources to provide the intended connectivity.

Do not assume that every container needs a public IP. Production applications commonly run in private subnets and receive external traffic through a load balancer.

### 3\. Amazon ECS architecture

Amazon Elastic Container Service (ECS) is an AWS-native container orchestration service. It provides its own orchestration API and integrates directly with AWS networking, IAM, load balancing, logging, and compute services. You do not need to operate a Kubernetes control plane to use ECS. Amazon Web Services, Inc. +1

### 3.1 Core ECS components

ECS cluster

Logical grouping for services, tasks, and compute capacity

ECS service

Maintains the desired number of long-running tasks

Task 1

FastAPI container

Task 2

FastAPI container

Each task is launched from a task definition revision.

Compute capacity

AWS Fargate, EC2-backed capacity, or other supported ECS capacity options

The main ECS concepts are:

* Cluster: A logical grouping for container workloads and their compute capacity.

* Task definition: A versioned blueprint describing containers, images, CPU, memory, ports, environment variables, logging, and IAM roles.

* Task: A running instance of a task definition. A task can contain one or more closely related containers.

* Service: Maintains a desired number of tasks and coordinates their replacement and deployment.

* Capacity provider: Connects workload placement to a compute-capacity strategy, such as Fargate or an EC2 Auto Scaling group.

These concepts are documented in the official Amazon ECS documentation. Amazon Elastic Container Service +1

### 3.2 Task definitions and tasks

Imagine that you need to run a FastAPI application with the following settings:

| Property           | Example         |
| ------------------ | --------------- |
| Container image    | my-api:1.0.0    |
| Container port     | 8000            |
| CPU                | 256 CPU units   |
| Memory             | 512 MiB         |
| Logging            | CloudWatch Logs |
| Desired task count | 2               |

The task definition describes the application container and its runtime settings. The ECS service requests two running tasks.

If one task fails, ECS can replace it to restore the desired count, provided the required image, permissions, and compute resources are available.

A task definition is not the same as a task: the former describes what to run; the latter is an execution of that description.

### 3.3 ECS service discovery

When one ECS service needs to call another, you should avoid hard-coding the destination task's IP address. Task addresses can change during replacement and scaling.

ECS offers service communication options such as AWS Cloud Map integration and ECS Service Connect. These mechanisms help applications communicate through service names and managed networking. Amazon Web Services, Inc. +1

For example, an `orders-api` service might call an internal `catalog-api` service by its configured service name rather than by an individual task IP.

### 4\. Amazon EKS architecture

Amazon Elastic Kubernetes Service (EKS) is AWS's managed Kubernetes service. Kubernetes supplies the orchestration model, API, and workload resources, while AWS manages the EKS control plane. Your application workloads can run on supported compute options such as EC2 nodes or Fargate. Amazon EKS +1

### 4.1 Control plane and data plane

EKS control plane — managed by AWS

Kubernetes API server, scheduler, controllers, and cluster state storage

Worker compute — runs application workloads

Worker node A

Pod: FastAPI

Pod: Worker

Worker node B

Pod: FastAPI

Pod: Worker

The control plane processes Kubernetes API requests and coordinates the cluster. Worker compute runs the application containers. In a typical EKS managed-node deployment, AWS manages the control plane while you remain responsible for important aspects of worker configuration, workloads, access, and operations.

### 4.2 Core Kubernetes resources

| Resource   | Purpose                                                                              |
| ---------- | ------------------------------------------------------------------------------------ |
| Pod        | Smallest deployable Kubernetes unit; contains one or more containers                 |
| Deployment | Manages replicated, usually stateless application workloads and updates              |
| ReplicaSet | Maintains a specified number of matching pod replicas                                |
| Service    | Provides a stable endpoint for a group of pods                                       |
| Namespace  | Organizes resources within a cluster                                                 |
| ConfigMap  | Stores non-sensitive application configuration                                       |
| Secret     | Holds sensitive configuration, subject to appropriate protection and access controls |

A key difference from ECS is that Kubernetes exposes a general-purpose API with many resource types and extensibility mechanisms. ECS expresses its native orchestration model through clusters, task definitions, tasks, and services.

### 4.3 Example: running three API replicas

In EKS, you would commonly declare a Deployment with three replicas. Kubernetes schedules the pods and continually reconciles the actual state against the declared state.

A Kubernetes Service then gives clients a stable way to reach the matching pods.

Conceptually:

* Deployment: “Maintain three API pods.”

* Pods: “Run the actual application containers.”

* Service: “Provide a stable endpoint to reach the API pods.”

In ECS, the comparable high-level configuration is a service with a desired count of three tasks.

The concepts are similar, but their resource models and configuration APIs are different. ECS is not Kubernetes under another name, and EKS is not simply an alternative interface to ECS.

### 5\. AWS Fargate versus EC2-backed compute

Orchestration and compute are separate decisions. ECS and EKS determine how workloads are scheduled and managed; the compute layer determines where and how their containers run.

![AWS ECS and Fargate: Understanding the Differences | by Anuj Shashimal | Medium](https://images.openai.com/static-rsc-4/zWHUK8yYyvLn3S9nLjJRzToHxp1cgoU8IwY0AdT_Zj5OBo2CcOFUJUZOj514b549T4BnxQEQwG1YnF7M-L6tXR93abEJXNPX_kqmzJArYsLYyZgB3BkMc-SLVlUSyOpo1N4aAYA2IX3m-WdMKFSMHIGKloLd7aNREymkqIcoKbdeHcZou7WJQaEdZ3dq-EjE?purpose=fullsize)

AWS Fargate

You specify task or pod requirements without managing the underlying worker instances. AWS manages the underlying compute infrastructure.

Useful when you want to reduce server administration and have workload requirements compatible with Fargate.

![Everything about AWS ECS(with hands-on) | by anubhav jhalani | Medium](https://images.openai.com/static-rsc-4/iBM5byF-BCbBDNvlBZnKaBnkx1wuhjoIgBy_di4aIN5piOau8Ies-c2oJKqE8w9axLg-57dtR46B29ODkpGYGW2V6WXK3ktGi1UdIB5s0hce8nqgIc3nVZsDC-Qg-k15z9FcrBR-bqIhub5OT5XPJbnBLaFDbjUURiJqaCE-nqbIQTkD9HDNa3UZJc72lqWg?purpose=fullsize)

EC2-backed containers

Containers run on EC2 instances that provide the compute capacity. You gain more control over instance types, capacity, and host configuration, while taking on additional operational responsibilities.

Useful when you need more control over compute, specialized instance choices, or workload economics that favor managed fleets of instances.

ECS supports Fargate and EC2-backed capacity. EKS supports Fargate for eligible pods as well as EC2-based worker nodes and other managed compute options. The exact constraints and supported configurations differ between the services. Amazon Elastic Container Service +2

| Consideration        | Fargate                                                        | EC2-backed compute                                              |
| -------------------- | -------------------------------------------------------------- | --------------------------------------------------------------- |
| Host management      | AWS manages underlying hosts                                   | Host fleet configuration and lifecycle require management       |
| Capacity control     | Defined through task or pod resource requirements              | More control over instance selection and capacity               |
| Billing model        | Based on provisioned workload resources and applicable charges | Instance-based costs, whether or not capacity is fully utilized |
| Operational effort   | Generally lower                                                | Generally higher                                                |
| Workload flexibility | Subject to Fargate's supported features and limits             | Greater control over the host environment                       |

Neither option is universally cheaper. Actual cost depends on workload utilization, CPU and memory requirements, architecture, region, networking, logging, storage, and scaling behavior.

### 6\. ECS versus EKS: choosing the right service

Choose ECS when AWS-native simplicity is a priority.

ECS is a strong fit for applications that need container scheduling, service scaling, load balancing, IAM integration, and AWS operations without adopting the full Kubernetes API ecosystem.

Choose EKS when Kubernetes capabilities are a priority.

EKS is a strong fit when you need Kubernetes APIs, its ecosystem of controllers and tools, standardized Kubernetes deployment workflows, or compatibility with existing Kubernetes workloads.

| Decision factor              | ECS                                                  | EKS                                                                     |
| ---------------------------- | ---------------------------------------------------- | ----------------------------------------------------------------------- |
| Orchestration API            | AWS-native ECS API                                   | Kubernetes API                                                          |
| Learning curve               | Generally lower                                      | Generally higher                                                        |
| Kubernetes compatibility     | No native Kubernetes API                             | Yes                                                                     |
| Operational responsibilities | ECS service and workload configuration               | Kubernetes resources, access, add-ons, and cluster operations           |
| Portability                  | AWS-specific orchestration model                     | Greater compatibility with Kubernetes environments                      |
| Cost considerations          | Compute, networking, logging, and other AWS services | Same categories plus applicable EKS and Kubernetes infrastructure costs |

EKS does not automatically make an application more scalable or reliable than ECS. Both can support production-grade systems. The right choice depends on required features, engineering experience, operational capacity, and total cost.

### 7\. AWS accounts, IAM, and networking for containers

Before deploying either service, understand the AWS boundaries that govern access and connectivity.

### 7.1 AWS account and Region

An AWS account provides an administrative and resource boundary. A Region contains separate regional resources, and many services use Availability Zones within a Region to improve resilience.

For example, an application may run in a single account and Region initially, then use separate accounts for development and production as its requirements grow.

### 7.2 IAM permissions and roles

Container workloads commonly involve several different identities:

* Deployment identity: The developer or CI/CD system that creates and updates AWS resources.

* Execution identity: Permissions needed by the platform to pull images, publish logs, or initialize a workload.

* Application identity: Permissions that application code itself needs to access AWS services.

For ECS, distinguish the task execution role from the task role. For EKS, distinguish the identities used for cluster access from the workload identity assigned to an individual application.

For example, an API that reads objects from S3 should receive narrowly scoped application permissions instead of inheriting broad permissions from the developer's account.

### 7.3 VPC, subnets, and security groups

VPC

Private network address space

Public subnet

Often contains an internet-facing load balancer, with suitable routing and security controls.

Private subnet

Often contains application tasks or worker nodes without direct public IP exposure.

Security groups control permitted network traffic at supported resource interfaces. Route tables, gateways, endpoints, and other network resources determine connectivity.

A secure baseline commonly places application workloads in private subnets, permits only the required inbound traffic, and gives workloads the outbound access they need to retrieve images, call dependencies, and publish telemetry.

Private subnets do not automatically have internet access. Depending on the architecture, outbound connectivity may use NAT gateways, VPC endpoints, or other appropriate network paths.

For EKS, also consider pod networking and the address capacity of the subnets. For ECS, consider the networking mode and task network interfaces. These details become important in later modules.

### 8\. Introduction to Pulumi for AWS infrastructure

Pulumi is an infrastructure-as-code (IaC) platform that lets you define cloud resources using general-purpose programming languages. In this course, we use Python with Pulumi, rather than Terraform, to provision AWS infrastructure.

Pulumi will eventually manage ECR repositories, ECS clusters and services, EKS clusters, networking, IAM roles, and related resources. Pulumi SDK Python API reference +1

### 8.1 Projects, stacks, configuration, and state

| Concept       | Meaning                                                                                            |
| ------------- | -------------------------------------------------------------------------------------------------- |
| Project       | A collection of infrastructure code and project configuration, identified by Pulumi.yaml.          |
| Stack         | An independently managed instance of a project, commonly used for dev, staging, or prod.           |
| Configuration | Inputs such as AWS Region, environment name, and resource sizing.                                  |
| Secrets       | Sensitive configuration values that Pulumi encrypts using the stack's configured secrets provider. |
| State         | Metadata Pulumi uses to track managed resources and determine required changes.                    |
| Dependencies  | Relationships between resources that determine the order in which operations can occur.            |

Pulumi stores stack state in a configured backend, such as Pulumi Cloud, an S3 backend, or a local backend. Choose a backend appropriate to your collaboration, recovery, and security requirements. Pulumi Docs +3

### 8.2 Typical project structure

As the course progresses, we will expand a project into reusable infrastructure components.

```text
aws-containers/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── Dockerfile
├── infrastructure/
│   ├── Pulumi.yaml
│   ├── requirements.txt
│   ├── __main__.py
│   └── components/
│       ├── ecr.py
│       ├── ecs.py
│       └── eks.py
└── README.md
```

The ECS and EKS component files are planned structure, not resources we will provision in this first module.

### 8.3 How Pulumi manages resources

A typical infrastructure workflow is:

Python infrastructure program

Declare resources and their dependencies

Preview

Inspect proposed creates, updates, and deletes

Apply

Pulumi invokes provider operations and updates stack state

Important commands include:

```bash
pulumi new python
pulumi stack init dev
pulumi config set aws:region eu-west-2
pulumi preview
pulumi up
pulumi stack output
```

`pulumi up` applies the proposed changes after the required confirmation or approval flow. For this module, we will create a stack but will not deploy AWS resources yet.

### Lab — Prepare the container deployment environment

Objective: Create a working FastAPI container, verify its health endpoint, and prepare a Pulumi Python project for future AWS deployments.

### Lab architecture

FastAPI source code

Docker image

Build and run locally

Local HTTP endpoints

Application response and health checks

Pulumi Python project

AWS Region, dev stack, and infrastructure code foundation

### 9.1 Prerequisites

Install or prepare the following on your development machine:

* Python 3.12 or later.

* Docker Desktop or another working Docker Engine.

* Git.

* Pulumi CLI.

* AWS CLI v2.

* An AWS account and an appropriate authentication method for future AWS provisioning.

Verify the installations:

```bash
python --version
docker --version
docker info
git --version
pulumi version
aws --version
```

For this first lab, Docker must be working. AWS authentication will be needed when we start provisioning resources in later modules, but creating the Pulumi stack itself does not require deploying to AWS.

### 9.2 Create the FastAPI application

Create a directory called `aws-containers`, then create this structure:

```text
aws-containers/
└── app/
    ├── main.py
    ├── requirements.txt
    └── Dockerfile
```

`app/main.py`

```python
from fastapi import FastAPI

app = FastAPI(title="AWS Containers Demo")

@app.get("/")
async def root():
    return {
        "application": "aws-containers-demo",
        "message": "Hello from FastAPI",
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

The root endpoint returns application information. The `/health` endpoint provides a simple response that a local health check can use.

In production, a health endpoint should reflect the application's actual readiness and dependencies where appropriate. A process returning HTTP 200 does not necessarily prove that every downstream dependency is healthy.

`app/requirements.txt`

```text
fastapi
uvicorn[standard]
```

For a production build, pin dependencies to tested versions and use a lockfile so that builds are reproducible. We will refine the image-building workflow as the course progresses.

### 9.3 Write the Dockerfile

`app/Dockerfile`

```dockerfile
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

This uses a slim Python base image, runs the application as a non-root user, and starts Uvicorn on port `8000`.

`EXPOSE 8000` documents the intended container port; it does not publish the port to your host automatically. The `-p` option in the next command does that.

### 9.4 Build and run the container

From the `aws-containers` directory, build the image:

```bash
docker build -t fastapi-api:1.0.0 ./app
```

Start a container:

```bash
docker run --rm \
  --name fastapi-api \
  -p 8000:8000 \
  fastapi-api:1.0.0
```

Keep that terminal running. Open another terminal and call the endpoints.

Root endpoint:

```bash
curl http://localhost:8000/
```

Expected response:

```json
{
  "application": "aws-containers-demo",
  "message": "Hello from FastAPI"
}
```

Health endpoint:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{
  "status": "healthy"
}
```

On Windows PowerShell, you can also open `http://localhost:8000/health` in your browser or use `curl.exe` to avoid PowerShell's `curl` alias.

### 9.5 Add a Docker health check

Add the following to the Dockerfile before the `CMD` instruction:

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s \
    --start-period=5s --retries=3 \
    CMD ["python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"]
```

Rebuild the image:

```bash
docker build -t fastapi-api:1.0.0 ./app
```

Run the container again and inspect its health status:

```bash
docker run -d --rm \
  --name fastapi-api \
  -p 8000:8000 \
  fastapi-api:1.0.0

docker inspect --format='{{.State.Health.Status}}' fastapi-api
```

The health status may initially be `starting`; inspect it again after a few seconds.

This is a Docker-level health check. ECS and Kubernetes have their own health-check mechanisms, which we will configure separately when deploying the application to those platforms.

To stop the detached container:

```bash
docker stop fastapi-api
```

### 9.6 Create the Pulumi Python project

From the `aws-containers` directory, create a separate infrastructure directory:

```bash
mkdir infrastructure
cd infrastructure

pulumi new python
```

Follow the CLI prompts to create the project and its initial stack. If the CLI asks you to select a stack, use `dev`.

Install the AWS provider:

```bash
uv add pulumi pulumi-aws
```

If you are not using `uv` for this project, install the dependencies in the Python environment configured for Pulumi instead:

```bash
python -m pip install pulumi pulumi-aws
```

Keep the Pulumi runtime and provider dependencies in the project's dependency manifest. Do not install packages into an unrelated Python environment.

A typical project contains:

```text
infrastructure/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── __main__.py
└── requirements.txt
```

The exact generated files depend on the template and dependency manager you choose.

### 9.7 Configure the AWS Region and inspect the stack

Choose the AWS Region you plan to use for the course. For example, `eu-west-2` is London:

```bash
pulumi config set aws:region eu-west-2
pulumi stack
pulumi config
```

This configures the Region; it does not create AWS infrastructure.

If your Pulumi project uses `uv`, keep the Python runtime configured to use the appropriate project environment and ensure the installed dependencies are available to the Pulumi program.

Now open `__main__.py` and replace the generated program with a simple informational program:

```python
import pulumi

config = pulumi.Config()

environment = pulumi.get_stack()
region = config.require("aws:region")

pulumi.export("environment", environment)
pulumi.export("region", region)
pulumi.export("course", "AWS ECS and EKS")
```

Run:

```bash
pulumi preview
pulumi up
pulumi stack output
```

Because this program only exports values and declares no cloud resources, it should not provision AWS infrastructure. Pulumi will still create or update the stack's state and outputs.

For real deployments, remember to inspect previews before applying changes.

### 9.8 Understand the stack configuration

A stack-specific configuration file is named `Pulumi.dev.yaml`. It contains settings for the `dev` stack.

Pulumi may encrypt secrets in this file using the configured secrets provider. For example, if a later module requires a sensitive application credential, configure it using:

```bash
pulumi config set --secret app-password
```

The CLI will prompt for the value. Retrieve it in Python using `config.require_secret("app-password")` rather than treating it as an ordinary string. Pulumi Docs +1

Do not place AWS access keys in source code, Dockerfiles, container images, or ordinary configuration values. Prefer appropriate AWS credential providers and short-lived credentials.

### Lab completion checklist

### Lab progress

0 of 7

FastAPI application starts successfully in Docker

Root and health endpoints return the expected responses

Docker health status becomes healthy

Pulumi Python project and dev stack exist

AWS Region is stored in Pulumi configuration

Pulumi preview runs without creating AWS resources

Pulumi stack outputs show the environment and Region

### 10\. Key takeaways

* Container orchestration automates scheduling, desired-state reconciliation, service discovery, scaling, and recovery.

* ECS uses clusters, task definitions, tasks, and services. EKS uses Kubernetes resources such as pods, Deployments, and Services.

* Fargate reduces host-management responsibilities; EC2-backed compute offers greater control over the worker environment.

* AWS networking and IAM determine where workloads can run, how they communicate, and which AWS resources they can access.

* Pulumi uses Python to define infrastructure, stacks to separate environments, and state to track managed resources.

* The lab establishes a reproducible FastAPI container and Pulumi foundation without incurring costs from creating ECS or EKS infrastructure.

### Further reading

* Amazon ECS documentation — [Official guide](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/Welcome.html?utm_source=chatgpt.com).

* Amazon EKS documentation — [Official guide](https://docs.aws.amazon.com/eks/latest/userguide/what-is-eks.html?utm_source=chatgpt.com).

* Pulumi — [Infrastructure-as-code documentation](https://www.pulumi.com/docs/iac/?utm_source=chatgpt.com).

* FastAPI — [Official documentation](https://fastapi.tiangolo.com/?utm_source=chatgpt.com).
