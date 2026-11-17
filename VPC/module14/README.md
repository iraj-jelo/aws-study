### Module 14 — VPC for Containers and Kubernetes

AWS Networking Course · Advanced Architecture · Pulumi with Python

This module focuses on how Amazon VPC networking works when applications run inside containers, especially Amazon ECS and Amazon EKS. We'll examine how IP addresses are assigned to pods, how packets move through the network, how to avoid IP exhaustion, and how to troubleshoot connectivity failures in production.

The main emphasis is Amazon EKS with the Amazon VPC CNI, including a hands-on lab that designs a Kubernetes network and diagnoses a broken connection.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Design VPC subnets for ECS and EKS clusters across multiple Availability Zones.

* Explain how Kubernetes pods obtain VPC addresses through the Amazon VPC CNI.

* Compare pod networking, ECS networking modes, and alternative EKS networking approaches.

* Calculate subnet capacity and understand prefix delegation.

* Configure private EKS API access, load balancers, and controlled egress.

* Distinguish VPC security groups from Kubernetes NetworkPolicy enforcement.

* Troubleshoot pod-to-pod, pod-to-Service, and pod-to-AWS-service connectivity.

* Provision the foundational VPC architecture with Pulumi Python and validate it using AWS CLI and Kubernetes tools.

### 2\. The architecture: containers inside a VPC

Start with the central idea: a container is not automatically a separate network endpoint in the VPC. Its networking depends on the container platform and networking mode.

On EKS, Kubernetes schedules pods onto worker nodes. The Amazon VPC CNI plugin normally assigns VPC-routable private IPv4 addresses to pod network interfaces or their supported secondary-IP arrangements. Consequently, pods can communicate with other VPC resources using ordinary VPC routing and applicable security controls.

![CNI Amazon VPC - Amazon EKS](https://images.openai.com/static-rsc-4/oJ3heiyq_acYH0Kd_GVGDiacmxASLt2UIpnWA9o-AE16EYIneIxQ2v61USU1AXJr-RhprBlnKZwz4tda244iF6OhZE9uZUPxsKpytauzGX1Swexno_Fhmjblc4N2t6ywQctjftwCWfjc6bWB_fB82UZj_E-lhlcUhRP16rPBCkTQj4T_ztVGeiXaiGN8f6ez?purpose=fullsize)

A typical production architecture looks like this:

Internet clients

HTTPS requests

Internet-facing Application Load Balancer

Public subnets · TLS · listener rules

Amazon EKS VPC · 10.40.0.0/16

AZ-a: private subnet

Worker node

Pod IPs

10.40.16.0/20

AZ-b: private subnet

Worker node

Pod IPs

10.40.32.0/20

Private routing, security groups, pod network policy, and cluster service networking

Private AWS service access

VPC endpoints, or controlled NAT egress where required

This is a conceptual design, not a complete deployment. Actual subnet sizes, route tables, node placement, load-balancer targets, and security rules depend on the selected cluster configuration.

### The main networking layers

| Layer                    | Responsibility                                                        |
| ------------------------ | --------------------------------------------------------------------- |
| VPC and subnet           | Address allocation and network boundaries                             |
| Route table              | Determines the next hop for a destination                             |
| ENI and pod IP           | Provides network attachment and addressing                            |
| Security group           | Stateful filtering at supported network interfaces                    |
| Network ACL              | Stateless subnet-level filtering                                      |
| Kubernetes Service       | Stable virtual endpoint for a group of pods                           |
| Kubernetes NetworkPolicy | Pod traffic restrictions when supported by the network implementation |
| Load balancer            | Exposes or distributes traffic to application targets                 |

A connection can fail at any one of these layers. Correct Kubernetes YAML alone does not guarantee network connectivity.

### 3\. ECS networking versus EKS networking

Although both services run containers, their networking abstractions are different.

### Amazon ECS

ECS offers several networking modes, depending on whether tasks run on EC2 instances or Fargate.

| Mode   | Addressing and isolation                                       | Practical considerations                                                     |
| ------ | -------------------------------------------------------------- | ---------------------------------------------------------------------------- |
| awsvpc | Each task gets an ENI-backed network attachment and private IP | Preferred for task-level security groups and straightforward VPC networking  |
| bridge | Containers use a host-local Docker bridge network              | Port mapping and host-level networking complicate traffic analysis           |
| host   | Container shares the host network                              | Port conflicts and weaker network isolation; generally avoid for new designs |

`awsvpc` is the mode used by ECS Fargate tasks and is generally the best default for new ECS services requiring clear network isolation.

### Amazon EKS

EKS introduces additional concepts:

* Node: the EC2 instance or other supported compute environment running workloads.

* Pod: the smallest Kubernetes deployable unit; containers within a pod share its network namespace and IP.

* CNI: the Container Network Interface, which connects pods to the network.

* Service: a stable virtual IP and DNS name that directs traffic to eligible pod endpoints.

* Ingress or Gateway: an application entry point that can integrate with AWS load-balancing infrastructure.

The important distinction is that a Kubernetes Service IP is not normally an individual VPC ENI address. The Amazon VPC CNI allocates pod addresses; Kubernetes service networking handles traffic to ClusterIP Services.

### 4\. Amazon VPC CNI: how pod IP addresses work

The Amazon VPC CNI plugin, commonly deployed as the `aws-node` DaemonSet, allocates and configures pod networking on supported EKS worker nodes. It interacts with EC2 networking APIs and maintains local networking configuration.

### 4.1 Standard IPv4 networking

Suppose a worker node has the following configuration:

* Node primary IP: `10.40.16.25`

* Additional IPv4 addresses available through its network interfaces.

* Pod IPs: `10.40.16.101`, `10.40.16.102`, and so on.

Conceptually:

EC2 worker node

Primary ENI · 10.40.16.25

VPC CNI manages pod networking

Pod A

10.40.16.101

Pod B

10.40.16.102

Pod C

10.40.16.103

The diagram is illustrative. The precise allocation depends on the CNI configuration, node type, subnet, and whether prefix delegation or custom networking is enabled.

In the normal VPC CNI model, pod addresses are allocated from VPC address space, making pods directly addressable through VPC routing. This differs from a typical overlay network, where pod addresses might exist only inside an encapsulated virtual network.

### 4.2 What happens when a pod sends a packet?

Consider Pod A sending an HTTPS request to a private API at `10.40.50.20:443`.

Pod A: `10.40.16.101`

Pod and node networking configuration

Route selection and applicable network security rules

Destination: `10.40.50.20:443`

To diagnose a failure, work through these questions in order:

* Does the pod have an IP address and a valid route?

* Does the destination IP resolve correctly, if a DNS name was used?

* Is the destination reachable through the relevant VPC routes?

* Do security groups, network ACLs, and any applicable network policies permit the connection?

* Is the destination listening on port 443?

* Does the return path work, including any NAT or stateful filtering behavior?

This layered approach is more reliable than immediately changing security groups or restarting pods.

### 5\. Pod networking alternatives

The standard VPC CNI is not the only available EKS networking arrangement. Choose based on address capacity, isolation requirements, IP-family needs, and operational constraints.

| Approach                 | Main benefit                                                  | Main trade-off                                                             |
| ------------------------ | ------------------------------------------------------------- | -------------------------------------------------------------------------- |
| Standard VPC CNI         | Native VPC pod addresses                                      | Consumes subnet IPv4 addresses                                             |
| Prefix delegation        | More efficient allocation of IPv4 addresses to eligible nodes | Requires suitable contiguous address capacity and compatible configuration |
| Custom networking        | Separates node and pod address allocation                     | Adds subnet and routing complexity                                         |
| IPv6 pod networking      | Large address space for supported cluster designs             | Requires IPv6-aware connectivity and service integration                   |
| Alternate CNI or overlay | Can suit particular routing or portability requirements       | May change security, routing, and observability behavior                   |

Not every alternative supports every EKS compute type or feature. Confirm the specific EKS version, CNI version, and supported configuration before choosing one. AWS documents these modes and their constraints in the [VPC CNI networking guide](https://docs.aws.amazon.com/eks/latest/userguide/pod-networking-use-cases.html?utm_source=chatgpt.com).

### Prefix delegation

Prefix delegation is especially important when many pods share a relatively small node fleet.

Instead of allocating every pod address individually, the VPC CNI can allocate a prefix of addresses to an eligible network interface. The CNI then assigns pod IPs from that prefix.

For IPv4, a `/28` contains 16 addresses. However, a `/28` prefix does not mean every node can always run exactly 16 additional pods. Capacity depends on the interface limits, primary addresses, other prefixes or secondary addresses, available subnet space, and kubelet pod limits.

Useful configuration and operational references:

* [Assign more IP addresses to Amazon EKS nodes with prefixes](https://docs.aws.amazon.com/eks/latest/userguide/cni-increase-ip-addresses.html?utm_source=chatgpt.com)

* [Amazon EKS VPC and subnet best practices](https://docs.aws.amazon.com/eks/latest/best-practices/subnets.html?utm_source=chatgpt.com)

Prefix delegation is not a substitute for subnet planning. A subnet can still run out of available addresses or lack suitably aligned contiguous prefixes.

### 6\. Subnet sizing and IP exhaustion

IP exhaustion is one of the most common infrastructure design problems in EKS. A cluster may have enough CPU and memory to schedule more pods while lacking enough network addresses to create them.

### 6.1 Calculate subnet capacity

AWS reserves five IPv4 addresses in every subnet. Therefore, for a conventional IPv4 subnet:

\\text{Usable IPv4 addresses}=2^{(32-p)}-5

Here, is the CIDR prefix length.

| Subnet CIDR | Total IPv4 addresses | AWS-usable addresses before other allocations |
| ----------- | -------------------- | --------------------------------------------- |
| /24         | 256                  | 251                                           |
| /22         | 1,024                | 1,019                                         |
| /20         | 4,096                | 4,091                                         |
| /19         | 8,192                | 8,187                                         |

These figures are subnet-level upper bounds, not the number of pods you can safely schedule. Nodes, load balancers, interface endpoints, other ENIs, and warm IP allocations also consume addresses.

### 6.2 Estimate the workload requirement

Suppose an EKS cluster needs:

* 6 worker nodes across two Availability Zones.

* 30 application pods per node.

* 10 system and infrastructure pods per node.

* Additional room for autoscaling and rolling deployments.

The initial pod demand is:

6 \\times (30+10)=240 \\text{ pod IPs}

That does not mean 240 addresses is a sufficient subnet allocation. You must also account for node primary addresses, CNI allocation behavior, infrastructure ENIs, scaling headroom, and subnet fragmentation.

For example, a rolling deployment may temporarily run old and new replicas simultaneously. A cluster that barely accommodates its steady-state replicas can fail during an otherwise routine release.

### 6.3 Understand prefix fragmentation

A subnet may have many free IPv4 addresses but still fail to allocate a `/28` prefix because the free addresses are scattered rather than contiguous.

AWS recommends considering dedicated workload subnets and subnet CIDR reservations to preserve suitable prefix space for prefix delegation. Prefix allocation also requires compatible instance networking capabilities.

Useful commands:

```bash
aws ec2 describe-subnets \
  --subnet-ids subnet-0123456789abcdef0 \
  --query 'Subnets[].{CIDR:CidrBlock,Available:AvailableIpAddressCount}'
```

```bash
kubectl get nodes -o wide
kubectl get pods -A -o wide
kubectl describe node <node-name>
kubectl describe pod <pod-name> -n <namespace>
```

Inspect the CNI configuration and logs:

```bash
kubectl get daemonset aws-node -n kube-system
kubectl get pods -n kube-system -l k8s-app=aws-node -o wide
kubectl logs -n kube-system daemonset/aws-node --all-containers
```

Look for IP assignment errors, failed ENI operations, and subnet capacity problems.

### 7\. EKS API endpoint access

The Kubernetes API endpoint is the control-plane endpoint used by `kubectl`, cluster nodes, and Kubernetes controllers. It is separate from your application's public ingress.

EKS supports three endpoint access configurations.

Public only

API requests use the public endpoint. Control access using public access CIDRs, IAM authentication, and Kubernetes authorization.

Public and private

Clients can use the public endpoint when permitted; requests from within the VPC can use the private endpoint.

Private only

The API endpoint is reachable from the VPC or an appropriately connected network. Administrative access requires a suitable private path.

For production, private access is a strong default. Public access can be disabled if administrators have a reliable private management path, such as VPN, Direct Connect, or a controlled management environment.

Check the existing configuration:

```bash
aws eks describe-cluster \
  --name production \
  --query 'cluster.resourcesVpcConfig.{
    Public:endpointPublicAccess,
    Private:endpointPrivateAccess,
    PublicCIDRs:publicAccessCidrs,
    Subnets:subnetIds
  }'
```

To enable both public and private access while restricting public access:

```bash
aws eks update-cluster-config \
  --name production \
  --resources-vpc-config \
  'endpointPublicAccess=true,endpointPrivateAccess=true,publicAccessCidrs=["203.0.113.10/32"]'
```

Replace the example CIDR with your actual approved administrator egress address. This is a configuration change to a real cluster, not a read-only command.

Remember that three separate authorization and connectivity concerns exist:

* Network access to the API endpoint.

* AWS IAM authentication.

* Kubernetes RBAC authorization.

Passing one does not automatically pass the others.

### 8\. Load balancers and the AWS Load Balancer Controller

The AWS Load Balancer Controller watches Kubernetes resources and provisions AWS load balancers accordingly. It supports Application Load Balancers (ALBs) for Ingress resources, and Network Load Balancers (NLBs) for Service resources of type `LoadBalancer`; supported Gateway API configurations are also available in current controller releases.

### 8.1 Instance targets versus IP targets

Instance target mode

ALB or NLB

EC2 node and NodePort

Kubernetes Service → Pod

IP target mode

ALB or NLB

Pod IP directly

With IP targets, the load balancer can send traffic directly to pod IP addresses. This is required for certain compute configurations, including Fargate pods and EKS Hybrid Nodes for the documented ALB use case. Instance mode instead routes traffic through worker nodes.

An example Ingress annotation for an ALB using IP targets:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: app
  namespace: production
  annotations:
    alb.ingress.kubernetes.io/scheme: internal
    alb.ingress.kubernetes.io/target-type: ip
spec:
  ingressClassName: alb
  rules:
    - host: app.internal.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: app
                port:
                  number: 80
```

This is a networking example, not a complete deployment. It assumes the AWS Load Balancer Controller is installed and authorized, an appropriate internal DNS setup exists, and the VPC contains correctly selected private subnets.

Common failures

* Subnet role tags are missing or identify the wrong subnets.

* Security groups do not allow traffic from the load balancer to the targets.

* The application listens on a different port from the target group configuration.

* The pod is not Ready, or its Service selector matches no pods.

* The health-check path returns an error.

* The load balancer is placed in the wrong subnet class.

For automatic subnet discovery, AWS recommends explicitly tagging public subnets with `kubernetes.io/role/elb=1` and private subnets with `kubernetes.io/role/internal-elb=1`.

### 9\. Security groups for pods

By default, the security groups attached to a node's network interfaces play a major role in controlling network traffic. In supported EKS configurations, you can instead associate specific security groups with selected pods using Security Groups for Pods.

This is useful when a workload needs narrowly scoped access to a database, an internal service, or a legacy resource that is already protected by security-group rules.

The feature uses branch network interfaces and requires compatible networking, IAM permissions, and EC2 instance types. It is not supported on Windows nodes or EKS Auto Mode, so verify current compatibility before designing around it.

Example policy object:

```yaml
apiVersion: vpcresources.k8s.aws/v1beta1
kind: SecurityGroupPolicy
metadata:
  name: payments-network-policy
  namespace: production
spec:
  podSelector:
    matchLabels:
      app: payments
  securityGroups:
    groupIds:
      - sg-0123456789abcdef0
```

The example assumes the necessary AWS VPC resource definitions and controller support are available. The security group ID is a placeholder.

### Security groups are not Kubernetes NetworkPolicy

These controls solve different problems.

| Control                   | Primary purpose                                                                           |
| ------------------------- | ----------------------------------------------------------------------------------------- |
| VPC security groups       | Stateful filtering associated with supported AWS network interfaces                       |
| Kubernetes NetworkPolicy  | Pod-level ingress and egress restrictions enforced by a compatible network implementation |
| Network ACLs              | Stateless filtering at the subnet boundary                                                |
| IAM and workload identity | Authorization to call AWS APIs and other AWS services                                     |

The Amazon VPC CNI supports Kubernetes NetworkPolicy enforcement in documented configurations. For the built-in VPC CNI implementation, confirm the required add-on version and configuration, and account for supported compute types and policy semantics.

For a default-deny application namespace, you might start with:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: production
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
```

This policy denies ingress and egress for selected pods once enforcement is active. You must add explicit allow policies for required application communication, DNS, health checks, and AWS endpoints. Do not apply it blindly to a running production cluster: depending on the enforcement mode, essential communication can stop immediately or new pods can start under default-deny enforcement.

### 10\. Private access to AWS APIs and cluster egress

A private EKS cluster is not necessarily a cluster with no internet access. These are separate design choices:

* Private Kubernetes API endpoint: restricts access to the cluster's Kubernetes control-plane API.

* Private worker subnets: keep worker nodes off direct internet routes.

* Private AWS service endpoints: let workloads reach supported AWS APIs without using a general-purpose NAT path.

* Controlled internet egress: permits necessary external access through NAT gateways, a firewall, or another approved egress architecture.

### Example: a workload reads an object from S3

A pod using an IAM role through EKS Pod Identity or IRSA needs both network connectivity and authorization to access S3.

Application pod

Workload IAM credentials

S3 gateway VPC endpoint

Route-table entry for S3 traffic

Amazon S3

IAM and bucket policy authorization

A gateway endpoint is generally a useful option for private IPv4 S3 access. It does not replace IAM permissions, bucket policies, DNS, or appropriate route-table associations.

For a private cluster that needs to pull images from Amazon ECR, use the required ECR API and registry interface endpoints plus the S3 endpoint used to download image layers. Other requirements depend on which AWS services the cluster and workloads use.

Common private endpoints include:

| Service                    | Endpoint type                                        |
| -------------------------- | ---------------------------------------------------- |
| Amazon S3                  | Gateway endpoint                                     |
| Amazon ECR API             | Interface endpoint                                   |
| Amazon ECR registry        | Interface endpoint                                   |
| AWS STS                    | Interface endpoint when private STS calls are needed |
| Amazon CloudWatch Logs     | Interface endpoint                                   |
| EKS Auth API               | Interface endpoint when required by EKS Pod Identity |
| Elastic Load Balancing API | Interface endpoint for private controller access     |

Not every private cluster requires every endpoint. Build the list from actual image-pulling, identity, management, logging, and application requirements.

### Workload identity is part of networking design

Use EKS Pod Identity or IAM Roles for Service Accounts (IRSA) instead of distributing long-lived AWS access keys inside pods.

If using IRSA without internet egress, the workload must reach the regional STS endpoint through an appropriate private endpoint. SDK configuration matters: requests to the global `sts.amazonaws.com` endpoint may not use the regional VPC endpoint. EKS Pod Identity instead uses the EKS Auth API.

### 11\. Designing VPCs for multiple clusters and tenants

There is no universally correct layout, but a sound starting point is to isolate workloads by environment and reserve address space for growth.

Consider a SaaS platform with development, staging, and production clusters.

Shared network services

Central DNS · logging · controlled egress

Development

10.40.0.0/16

Independent cluster and workload subnets

Staging

10.41.0.0/16

Independent cluster and workload subnets

Production

10.42.0.0/16

Independent cluster and workload subnets

Illustrative address plan: these CIDRs must be checked against your existing VPCs, on-premises networks, and planned connectivity.

Three useful patterns:

* Separate VPCs: strong environment isolation and independent routing; requires connectivity design for shared services.

* Multiple clusters in one VPC: simpler shared routing and fewer VPCs, but subnet allocation, cluster-specific load-balancer selection, and security boundaries require careful planning.

* One cluster with tenant namespaces: lower infrastructure overhead, but namespaces alone are not a strong security boundary. Combine them with appropriate RBAC, network policies, IAM identity separation, and resource controls.

For strict regulatory or hostile multi-tenant workloads, consider separate clusters or accounts when namespace-level controls are insufficient.

### 12\. Hands-on lab — design an EKS network and diagnose a pod connectivity issue

We'll build the VPC foundation with Pulumi Python and then use Kubernetes manifests to reproduce a connectivity failure.

The lab is divided into two parts:

* Provision and inspect a multi-AZ VPC network.

* Deploy a sample application and diagnose a broken connection using `kubectl`.

Cost warning: this lab's Pulumi VPC foundation creates billable AWS resources only when you deploy it, but creating a real EKS cluster additionally incurs costs for the EKS control plane and any EC2 nodes, NAT gateways, interface endpoints, load balancers, and data transfer. The Kubernetes troubleshooting exercise can also be performed against an existing cluster you control. Local Kubernetes cannot reproduce every AWS-specific VPC CNI behavior.

### Part A — Build the VPC foundation with Pulumi

We'll use:

* VPC: `10.40.0.0/16`

* Two Availability Zones

* Two public subnets for ingress infrastructure

* Two private subnets for Kubernetes workers

* One internet gateway

* NAT gateways omitted from this initial example to avoid automatic NAT gateway charges

This is a foundational VPC project, not a complete EKS deployment. Private workers would need appropriate NAT or VPC endpoint access for their required services.

### Project structure

```text
eks-network-lab/
├── Pulumi.yaml
├── requirements.txt
└── __main__.py
```

`Pulumi.yaml`

```yaml
name: eks-network-lab
runtime:
  name: python
description: Multi-AZ VPC foundation for an EKS network lab
```

`requirements.txt`

```text
pulumi>=3.0.0,<4.0.0
pulumi-aws>=7.0.0,<8.0.0
```

These are compatible major-version constraints, not a guarantee that the newest provider release has been pinned. For repeatable deployments, resolve and commit exact tested versions in your project's dependency lock files.

`__main__.py`

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()
vpc_cidr = config.get("vpcCidr") or "10.40.0.0/16"

vpc = aws.ec2.Vpc(
    "eks-lab-vpc",
    cidr_block=vpc_cidr,
    enable_dns_support=True,
    enable_dns_hostnames=True,
    tags={"Name": "eks-lab-vpc"},
)

azs = aws.get_availability_zones(
    state="available",
    filters=[{
        "name": "opt-in-status",
        "values": ["opt-in-not-required", "opted-in"],
    }],
)

public_cidrs = ["10.40.0.0/24", "10.40.1.0/24"]
private_cidrs = ["10.40.16.0/20", "10.40.32.0/20"]

public_subnets = []
private_subnets = []

for i in range(2):
    public = aws.ec2.Subnet(
        f"public-{i}",
        vpc_id=vpc.id,
        cidr_block=public_cidrs[i],
        availability_zone=azs.names[i],
        map_public_ip_on_launch=True,
        tags={
            "Name": f"eks-lab-public-{i}",
            "kubernetes.io/role/elb": "1",
        },
    )
    public_subnets.append(public)

    private = aws.ec2.Subnet(
        f"private-{i}",
        vpc_id=vpc.id,
        cidr_block=private_cidrs[i],
        availability_zone=azs.names[i],
        tags={
            "Name": f"eks-lab-private-{i}",
            "kubernetes.io/role/internal-elb": "1",
        },
    )
    private_subnets.append(private)

igw = aws.ec2.InternetGateway(
    "eks-lab-igw",
    vpc_id=vpc.id,
    tags={"Name": "eks-lab-igw"},
)

public_rt = aws.ec2.RouteTable(
    "eks-lab-public-rt",
    vpc_id=vpc.id,
    routes=[{
        "cidr_block": "0.0.0.0/0",
        "gateway_id": igw.id,
    }],
    tags={"Name": "eks-lab-public-rt"},
)

for i, subnet in enumerate(public_subnets):
    aws.ec2.RouteTableAssociation(
        f"public-association-{i}",
        subnet_id=subnet.id,
        route_table_id=public_rt.id,
    )

# Private subnets intentionally have no internet default route.
# Add controlled egress or appropriate VPC endpoints before
# using these subnets for real EKS nodes.

pulumi.export("vpc_id", vpc.id)
pulumi.export("public_subnet_ids", [
    subnet.id for subnet in public_subnets
])
pulumi.export("private_subnet_ids", [
    subnet.id for subnet in private_subnets
])
pulumi.export("availability_zones", azs.names[:2])
```

Address-planning note: the VPC includes the two public `/24` subnets and private `/20` subnets shown above. Ensure the Availability Zones returned by the provider are appropriate for your region and that the CIDRs don't overlap existing resources.

### Deploy and inspect

Install Pulumi, Python, and AWS CLI v2. Configure an AWS profile with permissions appropriate for creating and inspecting these resources.

```bash
python -m venv .venv
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
pip install -r requirements.txt

pulumi stack init dev
pulumi config set aws:region eu-west-3
pulumi config set vpcCidr 10.40.0.0/16

pulumi preview
pulumi up
```

Review the preview carefully before approving the update.

Inspect the outputs and the deployed VPC:

```powershell
pulumi stack output
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=eks-lab-vpc"
aws ec2 describe-subnets --filters "Name=vpc-id,Values=<vpc-id>"
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=<vpc-id>"
```

Replace `<vpc-id>` with the actual ID returned by Pulumi.

The expected result is one VPC, four subnets in two Availability Zones, an internet gateway, a public route table, and public subnet associations. The private subnets have no internet default route.

Before adding EKS, design how the nodes will reach the Kubernetes API, container registry, identity endpoints, logging services, and any other dependencies. For a private cluster with limited internet access, use the [official private-cluster requirements](https://docs.aws.amazon.com/eks/latest/userguide/private-clusters.html?utm_source=chatgpt.com).

### Part B — Deploy an application and reproduce a connectivity failure

Use an existing test EKS cluster with working `kubectl` access. The following manifests create an application pod and a client pod in a dedicated namespace.

Create `lab.yaml`:

```yaml
apiVersion: v1
kind: Namespace
metadata:
  name: network-lab
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
  namespace: network-lab
spec:
  replicas: 2
  selector:
    matchLabels:
      app: web
  template:
    metadata:
      labels:
        app: web
    spec:
      containers:
        - name: web
          image: nginx:stable
          ports:
            - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: web
  namespace: network-lab
spec:
  selector:
    app: web
  ports:
    - port: 80
      targetPort: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: client
  namespace: network-lab
spec:
  replicas: 1
  selector:
    matchLabels:
      app: client
  template:
    metadata:
      labels:
        app: client
    spec:
      containers:
        - name: client
          image: curlimages/curl:latest
          command: ["/bin/sh", "-c", "sleep 36000"]
```

Apply the manifest:

```bash
kubectl apply -f lab.yaml
kubectl rollout status deployment/web -n network-lab
kubectl rollout status deployment/client -n network-lab
kubectl get pods -n network-lab -o wide
kubectl get svc,endpointslices -n network-lab
```

Expected outcome: two web pods, one client pod, a ClusterIP Service, and ready Service endpoints.

Test the connection:

```bash
kubectl exec -n network-lab deployment/client -- \
  curl -sv --connect-timeout 3 http://web
```

You should receive an HTTP response from NGINX.

### Part C — Introduce a deliberate fault

Now apply a NetworkPolicy that selects the web pods and denies all ingress traffic to them.

Create `deny-web.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-web-ingress
  namespace: network-lab
spec:
  podSelector:
    matchLabels:
      app: web
  policyTypes:
    - Ingress
```

Apply it:

```bash
kubectl apply -f deny-web.yaml
```

This policy blocks ingress to the selected pods when a compatible NetworkPolicy implementation is enforcing it. If your cluster has no compatible enforcement configured, the policy object can exist without producing the expected network restriction.

Repeat the test:

```bash
kubectl exec -n network-lab deployment/client -- \
  curl -sv --connect-timeout 3 http://web
```

In an enforcing cluster, the request should fail or time out.

### Part D — Diagnose and fix the failure

Use this workflow rather than guessing.

1\. Check DNS and Service endpoints

```bash
kubectl get svc web -n network-lab
kubectl get endpointslices -n network-lab
kubectl exec -n network-lab deployment/client -- \
  curl -sv --connect-timeout 3 http://web
```

If DNS fails, investigate CoreDNS and the pod's DNS configuration. If endpoints are empty, inspect the Service selector and pod readiness.

2\. Inspect NetworkPolicies

```bash
kubectl get networkpolicy -n network-lab
kubectl describe networkpolicy deny-web-ingress \
  -n network-lab
```

The policy selects pods labelled `app=web` and defines ingress isolation without allowing any ingress sources.

3\. Check the AWS networking layer if necessary

```bash
kubectl get nodes -o wide
kubectl get pods -n kube-system -l k8s-app=aws-node
kubectl logs -n kube-system daemonset/aws-node \
  --all-containers --tail=100
```

If the failure remains after removing the policy, inspect CNI health, available subnet addresses, VPC routes, security groups, and relevant network ACLs.

4\. Restore connectivity

Delete the deliberately restrictive policy:

```bash
kubectl delete networkpolicy deny-web-ingress \
  -n network-lab
```

Retest the client request. If the connection succeeds again, the policy was the cause of the fault.

For production incidents, remember that Kubernetes NetworkPolicy enforcement, security groups, routing, and application health are distinct layers. AWS also provides dedicated guidance for [troubleshooting VPC CNI NetworkPolicies](https://docs.aws.amazon.com/eks/latest/userguide/network-policies-troubleshooting.html?utm_source=chatgpt.com).

### 13\. Troubleshooting reference

| Symptom                                 | Likely causes                                                         | First checks                                                 |
| --------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------------ |
| Pod stuck in Pending                    | Insufficient CPU/memory, pod limit, IP allocation failure             | kubectl describe pod; node events                            |
| FailedCreatePodSandBox                  | CNI failure, ENI/IP exhaustion, node networking problem               | Pod events; aws-node logs                                    |
| Pod cannot reach another pod            | NetworkPolicy, routing, security group, wrong IP                      | Pod IPs, policies, CNI logs                                  |
| Service DNS fails                       | CoreDNS, DNS egress restriction, bad service name                     | kubectl get svc; DNS test                                    |
| Service resolves but connection fails   | Empty endpoints, policy, wrong target port, application not listening | EndpointSlices; pod readiness; logs                          |
| Load balancer is unhealthy              | Wrong health check, missing SG rules, bad target registration         | Target health; controller logs                               |
| Pod cannot call an AWS API              | IAM authorization, endpoint or DNS issue, blocked egress              | Workload identity, endpoint configuration, application error |
| Pods cannot be scheduled during scaling | Subnet exhaustion, prefix fragmentation, instance limits              | Available subnet IPs; CNI configuration                      |

### 14\. Security, availability, and cost recommendations

* Use private worker subnets for production workloads where practical.

* Reserve IP capacity deliberately. Model peak replicas, rolling updates, autoscaling, and infrastructure ENIs—not just steady-state pod counts.

* Consider prefix delegation for eligible IPv4 workloads with high pod density, and plan contiguous prefix space in advance.

* Restrict EKS API access to approved management paths and maintain a tested administrative access method.

* Use workload identity instead of static AWS credentials in containers.

* Combine network policies and security groups appropriately. Neither replaces IAM authorization.

* Use private endpoints selectively. They can reduce internet dependence, but interface endpoints incur ongoing charges and are not available for every AWS service.

* Deploy across multiple Availability Zones and account for subnet capacity and load-balancer requirements in each zone.

* Monitor address utilization and CNI errors before they become scheduling incidents.

* Treat multi-tenant boundaries explicitly. Namespace separation without appropriate authorization and network enforcement is not sufficient for strong isolation.

### Cleanup

Remove the Kubernetes test resources:

```bash
kubectl delete namespace network-lab
```

If you deployed the Pulumi VPC and no longer need it, inspect the planned deletion:

```powershell
pulumi preview --diff
pulumi destroy
```

Review the proposed deletions before approving. Only destroy the stack if you own its resources and no other workloads depend on them. If you created an EKS cluster, node groups, endpoints, or load balancers separately, remove those resources according to their dependencies and verify that no billable resources remain.

### 15\. Official AWS documentation

[Amazon EKS networking](https://docs.aws.amazon.com/eks/latest/userguide/network-reqs.html?utm_source=chatgpt.com)

VPC requirements, subnet sizing, pod IPs, and load-balancer subnet selection.

[VPC CNI networking modes](https://docs.aws.amazon.com/eks/latest/userguide/pod-networking-use-cases.html?utm_source=chatgpt.com)

Prefix delegation, custom networking, IPv6, and other pod networking features.

[EKS API endpoint access](https://docs.aws.amazon.com/eks/latest/userguide/cluster-endpoint.html?utm_source=chatgpt.com)

Public and private API endpoint behavior and access restrictions.

[AWS Load Balancer Controller](https://docs.aws.amazon.com/eks/latest/userguide/aws-load-balancer-controller.html?utm_source=chatgpt.com)

Ingress, Service, Gateway integration, and AWS load-balancer provisioning.

[Kubernetes NetworkPolicy on EKS](https://docs.aws.amazon.com/eks/latest/userguide/cni-network-policy.html?utm_source=chatgpt.com)

Pod traffic segmentation, supported configurations, and enforcement limitations.

[Amazon ECS networking security](https://docs.aws.amazon.com/AmazonECS/latest/developerguide/security-network.html?utm_source=chatgpt.com)

ECS network modes, task-level addressing, and security-group considerations.

Module 14 complete. The key architectural lesson is that container networking is a combination of VPC addressing and routing, platform networking, workload-level security, and application-level service discovery. When troubleshooting, identify which layer owns the failure before changing infrastructure.
