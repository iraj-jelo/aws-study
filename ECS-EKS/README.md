### AWS ECS and EKS — Course Outline

Course title: Container Orchestration and Deployment on AWS: ECS and EKS

Structure: 9 modules

Infrastructure as Code: Pulumi (Python)

Application stack: Docker, FastAPI, Amazon ECR, Amazon ECS, Amazon EKS, AWS IAM, VPC, CloudWatch, and AWS Load Balancing

### Course objectives

By the end of this course, you will understand how to package, deploy, scale, secure, monitor, and troubleshoot containerized applications on AWS using both Amazon ECS and Amazon EKS. You will learn when to choose AWS-managed container orchestration versus Kubernetes and how to provision infrastructure reproducibly with Pulumi.

### Module 1 — Container Orchestration Fundamentals and AWS Architecture

* Container orchestration concepts: scheduling, desired state, service discovery, scaling, and self-healing.

* Docker images, containers, registries, and container networking.

* Amazon ECS architecture: clusters, services, tasks, task definitions, and capacity providers.

* Amazon EKS architecture: Kubernetes control plane, worker nodes, pods, deployments, and services.

* AWS Fargate versus EC2-backed container compute.

* ECS versus EKS: operational complexity, flexibility, portability, and cost.

* AWS account structure, IAM permissions, VPCs, subnets, and security groups for containers.

* Introduction to Pulumi projects, stacks, configuration, secrets, state, and resource dependencies.

Lab: Prepare the container deployment environment

* Build a small FastAPI application and package it with Docker.

* Run the application locally and configure health-check endpoints.

* Create a Pulumi Python project and configure an AWS stack.

* Establish a reusable project structure for provisioning container infrastructure.

### Module 2 — Amazon ECR and Container Image Delivery

* Amazon Elastic Container Registry (ECR) repositories, image tags, and image digests.

* Creating and managing ECR repositories with Pulumi.

* Building, tagging, and pushing Docker images to ECR.

* AWS CLI authentication and IAM permissions for image publishing.

* Image scanning, vulnerability findings, and image lifecycle policies.

* Immutable tags, versioning strategies, and reproducible deployments.

* Multi-stage Docker builds, non-root containers, and minimal base images.

* CI/CD integration concepts for building and publishing images.

Lab: Build and publish a FastAPI image

* Provision an ECR repository using Pulumi.

* Build and push the FastAPI application image to ECR.

* Configure image scanning and lifecycle policies.

* Establish a repeatable image-release workflow that can be used by ECS and EKS.

### Module 3 — Amazon ECS Fundamentals and Fargate Deployments

* ECS clusters, task definitions, tasks, and services in depth.

* Container definitions, CPU and memory allocation, environment variables, and secrets.

* ECS task execution roles versus ECS task roles.

* Fargate tasks and serverless container capacity.

* ECS service desired count, deployment configuration, and task replacement.

* Public and private subnet placement, security groups, and outbound connectivity.

* CloudWatch Logs integration and container health checks.

* ECS service discovery and internal application communication.

Lab: Deploy FastAPI on ECS Fargate with Pulumi

* Provision an ECS cluster, task definition, IAM roles, and Fargate service.

* Deploy the FastAPI image from ECR.

* Configure networking, logging, health checks, and environment settings.

* Update the application image and observe ECS rolling deployments.

### Module 4 — Production ECS: Load Balancing, Scaling, and Operations

* Application Load Balancer (ALB), target groups, listener rules, and health checks.

* Deploying private ECS tasks behind a public-facing load balancer.

* ECS service auto scaling using CPU, memory, and request-related metrics.

* ECS capacity providers, Fargate capacity, and Fargate Spot considerations.

* Rolling deployments, deployment circuit breakers, and rollback behavior.

* Secrets Manager and Systems Manager Parameter Store integration.

* ECS Exec, task inspection, and troubleshooting failed deployments.

* CloudWatch metrics, alarms, logs, and operational cost controls.

Lab: Build a production-style ECS service

* Use Pulumi to deploy FastAPI into private subnets behind an ALB.

* Configure service auto scaling and deployment health checks.

* Integrate application logs, CloudWatch alarms, and secure configuration.

* Investigate unhealthy targets, failed tasks, and incorrect IAM permissions.

### Module 5 — Kubernetes Fundamentals and Amazon EKS Architecture

* Kubernetes architecture: API server, scheduler, controller manager, and etcd.

* EKS control plane, managed node groups, and Fargate profiles.

* Kubernetes resources: Pods, Deployments, ReplicaSets, Services, and Namespaces.

* ConfigMaps, Secrets, labels, selectors, and annotations.

* Kubernetes desired state, reconciliation, scheduling, and self-healing.

* Cluster access using `kubectl`, kubeconfig, and AWS CLI.

* EKS IAM authentication and Kubernetes authorization with access entries and RBAC.

* EKS networking fundamentals and the Amazon VPC CNI.

* Kubernetes resource requests, limits, and container health probes.

Lab: Provision an EKS cluster with Pulumi

* Create an EKS cluster and managed node group using Pulumi's AWS and Kubernetes ecosystem.

* Configure IAM permissions and cluster access.

* Deploy a FastAPI application using Kubernetes Deployments and Services.

* Inspect pods, events, node placement, resource usage, and application logs.

### Module 6 — EKS Networking, Ingress, and Application Exposure

* Kubernetes ClusterIP, NodePort, and LoadBalancer Services.

* AWS Load Balancer Controller and ALB-based application routing.

* Ingress resources and the Gateway API concept.

* Public and private cluster endpoints and control-plane access.

* Pod networking, subnet IP capacity, and VPC CNI considerations.

* Network policies and supported enforcement mechanisms.

* Internal service discovery through Kubernetes DNS.

* TLS certificates, HTTPS termination, and AWS Certificate Manager integration.

* Private application access, security groups for pods, and network troubleshooting.

Lab: Expose FastAPI securely on EKS

* Deploy FastAPI behind an ALB using Kubernetes ingress resources.

* Configure DNS and HTTPS with AWS-managed certificates.

* Restrict access to the application and keep workloads in private subnets where appropriate.

* Troubleshoot service selectors, ingress configuration, target health, and connectivity issues.

### Module 7 — EKS Workloads, Storage, and Identity

* Kubernetes persistent volumes, PersistentVolumeClaims, and StorageClasses.

* Amazon EBS CSI driver for block storage and Amazon EFS CSI driver for shared file storage.

* Stateful workloads, storage lifecycle, and availability considerations.

* Workload identity with EKS Pod Identity and IAM Roles for Service Accounts (IRSA).

* Secure access to Amazon S3 and other AWS services from pods.

* Secrets management and integration with AWS Secrets Manager.

* Helm charts and reusable Kubernetes application packaging.

* Kubernetes resource quotas, limits, and workload isolation.

* EKS managed add-ons and cluster add-on lifecycle management.

Lab: Deploy a stateful, AWS-integrated application

* Provision EKS workload resources and storage-related infrastructure with Pulumi.

* Deploy a workload that uses persistent storage.

* Configure pod-level IAM permissions for access to an AWS service.

* Package application configuration using Helm and validate identity and storage behavior.

### Module 8 — Production EKS: Scaling, Security, and Observability

* Horizontal Pod Autoscaler (HPA) and workload scaling.

* Cluster capacity management with managed node groups and Karpenter.

* Cluster Autoscaler versus Karpenter and their operational trade-offs.

* Pod disruption budgets, topology spread constraints, and high availability.

* Rolling updates, readiness and liveness probes, and safe application rollbacks.

* EKS control-plane logs, CloudWatch Container Insights, and Kubernetes events.

* Prometheus-compatible metrics and Grafana-based observability concepts.

* Kubernetes RBAC, IAM integration, Pod Security Standards, and network isolation.

* ECR image security, vulnerability management, and workload hardening.

* Troubleshooting pending pods, crash loops, DNS failures, IP exhaustion, and resource pressure.

Lab: Operate and scale an EKS application

* Configure HPA and appropriate workload resource requests and limits.

* Deploy an application across multiple worker nodes and availability zones.

* Configure monitoring, logs, and alarms.

* Simulate application failures and capacity pressure, then diagnose and recover.

* Review security boundaries and improve workload resilience.

### Module 9 — Capstone: ECS and EKS Production Deployment Strategy

* Reference architectures for deploying containerized applications on ECS and EKS.

* Selecting ECS Fargate, ECS on EC2, EKS managed nodes, or EKS Fargate.

* Multi-environment infrastructure using Pulumi stacks and reusable components.

* Infrastructure state management, configuration, secrets, and deployment dependencies.

* CI/CD architecture for building images, deploying workloads, and managing releases.

* Blue/green and canary deployment concepts and their implementation options.

* IAM least privilege, private networking, image security, and secret management.

* Observability, incident response, backup and recovery, and cost optimization.

* Comparing operational overhead, extensibility, portability, and total cost of ownership.

* Production-readiness considerations for teams operating ECS and EKS.

Lab: Build and compare two deployment architectures

* Use Pulumi to provision an ECS Fargate deployment and an EKS-based deployment for the same FastAPI application.

* Store and distribute application images through ECR.

* Implement HTTPS access, health checks, logs, and basic scaling.

* Configure environment-specific stacks and repeatable deployment workflows.

* Compare deployment behavior, operational complexity, scaling, security boundaries, and estimated costs.

* Document a recommendation explaining which architecture best fits different application and team requirements.

### Recommended learning sequence

Foundation and ECS

Modules 1–4

Learn container fundamentals, ECR, Fargate, networking, load balancing, and ECS operations.

Kubernetes and EKS

Modules 5–8

Progress through Kubernetes, EKS networking, identity, storage, scaling, and production operations.

Production architecture

Module 9

Apply Pulumi to both platforms and compare their operational trade-offs.

Suggested prerequisites: Basic AWS IAM, VPC, networking, Docker, Python, and command-line skills. Familiarity with Pulumi is helpful but can be developed throughout the course.

Infrastructure approach: Use Pulumi with Python for AWS resources and, where appropriate, Kubernetes resources. Keep application manifests and infrastructure code version-controlled. For local preparation, Docker and a local Kubernetes distribution can help with early learning, but AWS-specific EKS behavior and managed-service integrations ultimately require access to an AWS environment.
