### Module 6 — EKS Networking, Ingress, and Application Exposure

AWS ECS/EKS Course · Module 6 of 9 · Hands-on lab with Pulumi, Python, Bash, Kubernetes, and FastAPI

### Learning objectives

By the end of this module, you will be able to:

* Explain how Kubernetes Services expose applications inside and outside an EKS cluster.

* Deploy the AWS Load Balancer Controller and use ALB Ingress resources.

* Expose a FastAPI application over HTTPS using AWS Certificate Manager (ACM).

* Understand public and private EKS API endpoints and private worker-node networking.

* Diagnose VPC CNI IP exhaustion, security-group restrictions, DNS failures, and unhealthy load-balancer targets.

* Apply network restrictions and understand when Kubernetes NetworkPolicy requires a compatible enforcement implementation.

* Provision and manage AWS networking resources with Pulumi instead of Terraform.

### 1\. Kubernetes networking architecture

An EKS application uses several networking layers. Understanding which layer handles each connection makes troubleshooting much easier.

Client / Browser

HTTPS · TCP 443

AWS Application Load Balancer

TLS termination · Host/path routing · AWS security groups

Kubernetes Ingress → Service

Ingress rules select the backend Service; Service selects matching Pods

FastAPI Pod A

Target IP

FastAPI Pod B

Target IP

Typical architecture: the ALB is internet-facing, while application Pods run on private worker nodes and private subnets. The EKS API endpoint is a separate control-plane access path.

There are three distinct traffic paths:

* Control plane: `kubectl` communicates with the Kubernetes API server.

* Application ingress: clients connect to the ALB, which forwards requests to application targets.

* Pod-to-Pod or Pod-to-service traffic: applications communicate over the cluster's networking and DNS.

A successful connection on one path does not guarantee that the other paths work.

### 2\. Kubernetes Services

Pods are replaceable. Their IP addresses can change as Deployments scale or replace them. Kubernetes Services provide stable access to a changing group of Pods.

| Service type     | Purpose                                                                           | Typical use                                                                         |
| ---------------- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- |
| ClusterIP        | Stable internal virtual IP                                                        | Internal APIs, backend services                                                     |
| NodePort         | Exposes a port on cluster nodes                                                   | Specific integration scenarios; underlying mechanism for some load-balancer designs |
| LoadBalancer     | Requests an external or internal load balancer through the configured integration | Direct service exposure                                                             |
| Headless Service | DNS discovery of individual endpoints, using clusterIP: None                      | Stateful applications and endpoint discovery                                        |

For most HTTP applications using an AWS ALB, use a `ClusterIP` Service behind an Ingress resource. The AWS Load Balancer Controller creates and configures the ALB based on the Ingress configuration.

### Example: Deployment and ClusterIP Service

Create a file named `fastapi.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: fastapi
  namespace: default
spec:
  replicas: 2
  selector:
    matchLabels:
      app: fastapi
  template:
    metadata:
      labels:
        app: fastapi
    spec:
      containers:
        - name: fastapi
          image: YOUR_ECR_IMAGE_URI
          ports:
            - name: http
              containerPort: 8000
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: fastapi
  namespace: default
spec:
  type: ClusterIP
  selector:
    app: fastapi
  ports:
    - name: http
      port: 80
      targetPort: http
```

Replace `YOUR_ECR_IMAGE_URI` with the actual image URI from your ECR repository. The application must listen on `0.0.0.0:8000` and implement `/health`.

Apply and inspect the resources:

```bash
kubectl apply -f fastapi.yaml

kubectl get deployments
kubectl get pods -o wide
kubectl get services
kubectl get endpointslices
```

Test the Service without exposing it publicly:

```bash
kubectl port-forward service/fastapi 8080:80
```

In another terminal:

```bash
curl -i http://localhost:8080/health
```

This verifies application and Service behavior independently of the ALB.

### 3\. AWS Load Balancer Controller

The AWS Load Balancer Controller watches Kubernetes resources and provisions AWS load-balancing infrastructure. An Ingress normally results in an ALB, while a `LoadBalancer` Service normally results in an NLB with the current controller's default configuration. Amazon EKS +1

### 3.1 Understand the components

| Component                             | Responsibility                                                          |
| ------------------------------------- | ----------------------------------------------------------------------- |
| AWS Load Balancer Controller          | Watches Kubernetes resources and reconciles AWS load balancers          |
| ALB                                   | Handles HTTP/HTTPS traffic, host rules, path rules, and TLS termination |
| Target group                          | Defines destinations and health-check behavior                          |
| Ingress                               | Declares application routing rules                                      |
| ClusterIP Service                     | Provides a stable Kubernetes backend                                    |
| AWS Load Balancer Controller IAM role | Allows the controller to manage required AWS resources                  |

The controller requires AWS permissions. Prefer a dedicated workload identity using EKS Pod Identity or IRSA rather than broadly granting permissions to every application Pod.

### 3.2 Verify your EKS environment

Run these Bash commands from a terminal with AWS CLI, `kubectl`, and Helm installed:

```bash
export AWS_REGION="eu-west-2"
export CLUSTER_NAME="my-eks-cluster"

aws sts get-caller-identity

aws eks describe-cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --query 'cluster.{Status:status,Version:version,Endpoint:endpoint}' \
  --output table

kubectl get nodes -o wide
kubectl get pods -n kube-system
helm version
```

Change the region and cluster name to match your Module 5 environment.

Check the VPC and subnet configuration:

```bash
aws eks describe-cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --query 'cluster.resourcesVpcConfig.{VpcId:vpcId,Subnets:subnetIds,PublicAccess:endpointPublicAccess,PrivateAccess:endpointPrivateAccess}' \
  --output yaml
```

The EKS API endpoint settings shown here concern access to the Kubernetes control plane. They do not determine whether your application ALB is public or internal.

### 3.3 Install the AWS Load Balancer Controller

First, ensure that the controller's IAM policy and dedicated identity are configured for your cluster. The identity must have the AWS permissions required by the controller, and the correct IAM role must be associated with its Kubernetes ServiceAccount. Follow the current AWS installation guide for your cluster configuration. Amazon EKS +1

Add the Helm repository:

```bash
helm repo add eks https://aws.github.io/eks-charts
helm repo update
```

Set the values that match your environment:

```bash
export VPC_ID="vpc-0123456789abcdef0"
export LBC_ROLE_ARN="arn:aws:iam::123456789012:role/AmazonEKSLoadBalancerControllerRole"
```

The following installation assumes that you have already created the `aws-load-balancer-controller` ServiceAccount and associated it with the role above, for example through IRSA:

```bash
helm upgrade --install aws-load-balancer-controller \
  eks/aws-load-balancer-controller \
  --namespace kube-system \
  --set clusterName="$CLUSTER_NAME" \
  --set region="$AWS_REGION" \
  --set vpcId="$VPC_ID" \
  --set serviceAccount.create=false \
  --set serviceAccount.name=aws-load-balancer-controller \
  --wait
```

The role ARN is included to clarify the expected IAM configuration; Helm does not associate the role with the ServiceAccount through that environment variable. The association must already exist in the ServiceAccount's IAM role annotation or be configured through your chosen identity mechanism.

Verify the controller:

```bash
kubectl get deployment aws-load-balancer-controller \
  -n kube-system

kubectl get pods -n kube-system \
  -l app.kubernetes.io/name=aws-load-balancer-controller

kubectl logs -n kube-system \
  deployment/aws-load-balancer-controller \
  --tail=100
```

If installation fails, inspect the logs and verify IAM permissions, the cluster identity configuration, webhook readiness, and access to the required AWS APIs.

Pulumi note: Keep the EKS cluster, VPC, IAM policy, workload identity, and related AWS infrastructure in Pulumi. Helm can install the controller, and Pulumi's Kubernetes provider can manage Kubernetes resources. Avoid having two independent tools manage the same resource.

### 4\. Ingress and ALB routing

An Ingress lets you define how HTTP requests reach Kubernetes Services. The AWS Load Balancer Controller translates supported Ingress configuration into AWS ALB resources.

Common routing patterns include:

* Host-based routing: `api.example.com` and `admin.example.com`.

* Path-based routing: `/api`, `/admin`, and `/health`.

* HTTPS listeners with certificates issued or imported into ACM.

* Internal ALBs for applications that should not be directly exposed to the internet.

### 4.1 Ingress example

Create `fastapi-ingress.yaml`:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: fastapi
  namespace: default
  annotations:
    alb.ingress.kubernetes.io/scheme: internet-facing
    alb.ingress.kubernetes.io/target-type: ip
    alb.ingress.kubernetes.io/listen-ports: '[{"HTTP":80},{"HTTPS":443}]'
    alb.ingress.kubernetes.io/ssl-redirect: "443"
    alb.ingress.kubernetes.io/healthcheck-path: /health
    alb.ingress.kubernetes.io/success-codes: "200"
spec:
  ingressClassName: alb
  rules:
    - host: api.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: fastapi
                port:
                  number: 80
```

This configuration illustrates the routing design, but it is not yet a complete HTTPS deployment. Before applying it, add the ACM certificate annotation in the next section and replace `api.example.com` with a domain you control.

The `target-type: ip` setting makes the ALB target the Pod IPs directly, which works with the Amazon VPC CNI networking model. The Service still provides a stable Kubernetes abstraction for the application.

With `ssl-redirect` enabled, HTTP requests are redirected to HTTPS. The redirect listener and HTTPS certificate must be configured correctly for this to work.

### 4.2 Understand the Gateway API

Kubernetes Ingress remains a widely used API for HTTP routing. The Gateway API provides a more expressive model that separates infrastructure ownership (`GatewayClass` and `Gateway`) from application routing (`HTTPRoute`).

The AWS Load Balancer Controller also supports Gateway API-based ALB provisioning in supported controller versions. Check the current compatibility and configuration requirements before selecting it for a production cluster. Amazon EKS +1

For this course's lab, we will use Ingress to keep the deployment straightforward.

### 5\. HTTPS with ACM and DNS

You need three things for public HTTPS:

* A domain name you control.

* An ACM certificate in the same AWS Region as the ALB, with the requested hostname covered by the certificate.

* A DNS record that points your hostname to the provisioned ALB.

### 5.1 Request an ACM certificate

If your DNS zone is hosted in Route 53, request a public certificate using DNS validation:

```bash
export DOMAIN="api.example.com"

CERT_ARN=$(aws acm request-certificate \
  --region "$AWS_REGION" \
  --domain-name "$DOMAIN" \
  --validation-method DNS \
  --query CertificateArn \
  --output text)

echo "$CERT_ARN"
```

Inspect the validation record:

```bash
aws acm describe-certificate \
  --region "$AWS_REGION" \
  --certificate-arn "$CERT_ARN" \
  --query 'Certificate.DomainValidationOptions[].ResourceRecord' \
  --output table
```

Create the DNS validation record using the exact name and value returned by ACM. You can create it manually or manage it through Pulumi. Wait until the certificate is issued:

```bash
aws acm describe-certificate \
  --region "$AWS_REGION" \
  --certificate-arn "$CERT_ARN" \
  --query 'Certificate.Status' \
  --output text
```

### 5.2 Add the certificate to the Ingress

Add the following annotation under `metadata.annotations` in `fastapi-ingress.yaml`:

```yaml
alb.ingress.kubernetes.io/certificate-arn: "YOUR_ACM_CERTIFICATE_ARN"
```

Replace the placeholder with the actual certificate ARN. The final annotations should include the certificate ARN, listener ports, redirect configuration, health-check path, target type, and exposure scheme.

Apply the Ingress:

```bash
kubectl apply -f fastapi-ingress.yaml

kubectl get ingress fastapi -w
```

Wait for the address to appear. Then inspect the ALB:

```bash
kubectl describe ingress fastapi

kubectl get ingress fastapi \
  -o jsonpath='{.status.loadBalancer.ingress[*].hostname}'

echo
```

The controller provisions resources asynchronously, so creation can take several minutes.

### 5.3 Create the application DNS record

Once the ALB is ready, create a Route 53 alias record for `api.example.com` pointing to the ALB. Use the ALB's DNS name and canonical hosted-zone ID returned by AWS, rather than guessing either value.

Verify the result:

```bash
dig +short api.example.com
curl -i https://api.example.com/health
```

A successful HTTPS response confirms the end-to-end route. A DNS result alone does not prove that the target is healthy or that the application is responding correctly.

### 6\. Public and private EKS endpoints

EKS networking involves two different concepts that are easy to confuse.

| Configuration            | What it controls                                                                                                    |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------- |
| Public EKS API endpoint  | Whether clients can reach the Kubernetes API through its public endpoint, subject to configured access restrictions |
| Private EKS API endpoint | Whether clients can reach the API through the cluster VPC's private network                                         |
| Internet-facing ALB      | Public client access to an application                                                                              |
| Internal ALB             | Application access through private network connectivity                                                             |
| Private worker nodes     | Nodes without direct public IP-based internet exposure                                                              |

A production-oriented design often uses private worker nodes, a public ALB for intentionally public applications, and restricted EKS API access.

### Inspect endpoint settings

```bash
aws eks describe-cluster \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION" \
  --query 'cluster.resourcesVpcConfig.{Public:endpointPublicAccess,Private:endpointPrivateAccess,PublicCIDRs:publicAccessCidrs}' \
  --output yaml
```

If you disable public endpoint access, your administrative machine must have a supported private network path to the cluster endpoint, such as a VPN, Direct Connect, or a suitably configured management host inside the VPC.

Do not disable public access until you have verified that your administration path works.

### Public versus internal ALB

For a private application, change the Ingress annotation to:

```yaml
alb.ingress.kubernetes.io/scheme: internal
```

An internal ALB is intended for clients with appropriate private network connectivity. DNS resolution, routes, security groups, and access controls must all support that connectivity.

### 7\. Pod networking and Amazon VPC CNI

Amazon EKS commonly uses the Amazon VPC CNI plugin to give Pods VPC IP addresses. This allows Pod traffic to integrate with AWS VPC networking and security controls. Amazon EKS +1

### 7.1 How IP allocation works

The VPC CNI manages network interfaces and available IP addresses for Pods. Depending on instance type, subnet capacity, CNI settings, and prefix delegation, the number of Pods that can run on a node can be constrained by available addresses.

Inspect the cluster's network configuration:

```bash
kubectl get nodes -o wide

kubectl get pods -A -o wide

kubectl get daemonset aws-node -n kube-system

kubectl logs -n kube-system \
  -l k8s-app=aws-node \
  --all-containers=true \
  --tail=100
```

Inspect available IP addresses in a subnet:

```bash
aws ec2 describe-subnets \
  --region "$AWS_REGION" \
  --subnet-ids subnet-0123456789abcdef0 \
  --query 'Subnets[].{Subnet:SubnetId,CIDR:CidrBlock,AvailableIPs:AvailableIpAddressCount}' \
  --output table
```

Replace the example subnet ID with one of your actual cluster subnets.

### 7.2 Common causes of IP exhaustion

* Subnets are too small for the intended node and Pod count.

* The VPC CNI cannot allocate additional IP addresses or prefixes.

* Instance types impose networking or IP allocation limits.

* Other AWS resources consume addresses from the same subnets.

* Pod density exceeds the available networking capacity.

Possible mitigations include using appropriately sized subnets, enabling supported prefix delegation, choosing instance types with sufficient networking capacity, and using custom networking where suitable.

Increasing the Kubernetes Pod limit alone does not create additional IP addresses.

### 8\. Network policies and security groups for Pods

Kubernetes networking is permissive by default in many installations. To restrict traffic, combine Kubernetes-level policies with AWS network controls.

### 8.1 Kubernetes NetworkPolicy

The following policy restricts ingress to FastAPI Pods so that only Pods labeled `role: api-gateway` in the `default` namespace can connect on TCP port 8000.

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: fastapi-ingress
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: fastapi
  policyTypes:
    - Ingress
  ingress:
    - from:
        - podSelector:
            matchLabels:
              role: api-gateway
      ports:
        - protocol: TCP
          port: 8000
```

Apply it only after verifying that the selected enforcement implementation supports your cluster and that the permitted traffic is correct:

```bash
kubectl apply -f network-policy.yaml
kubectl describe networkpolicy fastapi-ingress
```

Important: Creating a NetworkPolicy object does not guarantee enforcement. On EKS, the Amazon VPC CNI supports Kubernetes NetworkPolicy with the appropriate supported version and configuration. Verify the installed add-on and enforcement settings before relying on the policy. Amazon EKS +1

The example policy is intentionally narrow. If you apply it to a real workload, ensure required DNS and other dependencies remain reachable.

### 8.2 Security groups for Pods

Security groups for Pods can apply VPC security-group controls to supported Pod networking configurations. They are useful when a workload needs a distinct network boundary, such as restricting access to a database.

Use the appropriate AWS configuration and verify the supported instance types, CNI settings, and networking behavior before deployment.

Remember the distinction:

* NetworkPolicy: controls supported Pod traffic using Kubernetes policy semantics.

* Security groups: enforce AWS network access rules.

* Network ACLs: enforce subnet-level stateless traffic rules.

* IAM: authorizes AWS API operations; it is not a replacement for network isolation.

### 9\. Kubernetes DNS and network troubleshooting

Kubernetes DNS allows applications to discover Services by name. For example, a Service named `orders` in the `default` namespace is typically accessible as:

```text
orders
orders.default
orders.default.svc.cluster.local
```

The fully qualified name assumes the usual cluster DNS domain. Actual configuration can vary.

Test DNS from a running application Pod:

```bash
kubectl exec deploy/fastapi -- \
  python -c "import socket; print(socket.gethostbyname('kubernetes.default.svc.cluster.local'))"
```

Check CoreDNS:

```bash
kubectl get pods -n kube-system \
  -l k8s-app=kube-dns

kubectl logs -n kube-system \
  -l k8s-app=kube-dns \
  --tail=100
```

### Troubleshooting checklist

| Symptom                      | What to investigate                                                                |
| ---------------------------- | ---------------------------------------------------------------------------------- |
| Ingress has no ALB address   | Controller health, IAM permissions, subnet discovery, and Ingress events           |
| ALB targets are unhealthy    | Health-check path, target port, Pod readiness, routes, and security groups         |
| HTTP works but HTTPS fails   | Certificate ARN, certificate Region, listener configuration, and DNS               |
| Service has no endpoints     | Service selector labels, Pod readiness, and namespace                              |
| Pods cannot resolve Services | CoreDNS health, DNS policies, and network restrictions                             |
| Pods remain Pending          | CPU/memory requests, node capacity, subnet IPs, and scheduling constraints         |
| kubectl cannot connect       | EKS endpoint configuration, client network path, authentication, and authorization |

Useful diagnostic commands:

```bash
kubectl get ingress,svc,endpointslices,pods -o wide

kubectl describe ingress fastapi

kubectl describe service fastapi

kubectl get events \
  --sort-by=.metadata.creationTimestamp

kubectl logs -n kube-system \
  deployment/aws-load-balancer-controller \
  --tail=200
```

For AWS-side diagnostics, inspect target-group health, ALB security groups, subnet routes, and controller-related CloudTrail events where needed.

### 10\. Hands-on lab — Expose FastAPI securely on EKS

### Lab outcome

Deploy a FastAPI application to EKS, expose it through an ALB, configure HTTPS with ACM, and restrict the application to the intended traffic paths.

Infrastructure

Pulumi · EKS · VPC · IAM · ACM · Route 53

Application

FastAPI · ECR · Kubernetes Deployment · Service · Ingress

Security and operations

Private worker nodes · HTTPS · security groups · health checks · diagnostics

### Lab prerequisites

* An operational EKS cluster from Module 5.

* Pulumi CLI, Python, AWS CLI, `kubectl`, and Helm.

* An ECR image containing FastAPI, listening on port `8000`, with a working `/health` endpoint.

* A domain and permission to manage its DNS records.

* An ACM certificate issued in the ALB's Region.

* Permissions to create the required AWS resources and configure Kubernetes.

For this lab, use the cluster and VPC already provisioned in Module 5 wherever possible. This avoids accidentally creating duplicate infrastructure.

### Step 1 — Configure the environment

Use Bash:

```bash
export AWS_REGION="eu-west-2"
export CLUSTER_NAME="my-eks-cluster"
export DOMAIN="api.example.com"

aws sts get-caller-identity

aws eks update-kubeconfig \
  --region "$AWS_REGION" \
  --name "$CLUSTER_NAME"

kubectl get nodes
kubectl cluster-info
```

Confirm that the cluster is healthy before continuing.

### Step 2 — Prepare the Pulumi infrastructure

Organize the infrastructure project so that AWS resources and Kubernetes resources have clear ownership:

```text
eks-networking/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── __main__.py
├── requirements.txt
└── k8s/
    ├── fastapi.yaml
    └── fastapi-ingress.yaml
```

Your Pulumi Python project should manage or reference the following:

* Existing EKS cluster and VPC, without duplicating them.

* ACM certificate and DNS validation, if you want Pulumi to manage them.

* Route 53 application alias record.

* IAM policy and workload identity for the AWS Load Balancer Controller, if not already configured.

* Kubernetes resources through the Pulumi Kubernetes provider, if you choose to manage them through Pulumi rather than `kubectl`.

Example dependencies:

```text
pulumi
pulumi-aws
pulumi-kubernetes
```

Install them in your Python environment and select the appropriate stack:

```bash
python -m venv .venv
source .venv/bin/activate

python -m pip install -r requirements.txt

pulumi stack select dev
pulumi config
```

Configure the AWS provider to use the same Region as your cluster. Use Pulumi configuration or environment variables for environment-specific values. Do not commit credentials or secret values to version control.

Important: Do not create a second EKS cluster in this lab if your existing Module 5 cluster is already the intended target. Reference the existing cluster outputs or its name, VPC ID, subnet IDs, and endpoint configuration.

### Step 3 — Install and verify the controller

Follow Section 3 to install the AWS Load Balancer Controller with its dedicated IAM permissions and Helm chart.

Verify that it is ready:

```bash
kubectl rollout status \
  deployment/aws-load-balancer-controller \
  -n kube-system

kubectl get pods -n kube-system
```

The controller needs to discover suitable subnets for the requested ALB scheme. Ensure the public subnets have the appropriate routing and discovery tags for an internet-facing ALB, and that private subnets are correctly configured for internal resources.

### Step 4 — Deploy the application

Apply the Deployment and ClusterIP Service from Section 2 after replacing the image URI:

```bash
kubectl apply -f k8s/fastapi.yaml

kubectl rollout status deployment/fastapi

kubectl get pods -l app=fastapi
kubectl get endpointslices
```

Test the Service locally:

```bash
kubectl port-forward service/fastapi 8080:80
```

In another terminal:

```bash
curl -i http://localhost:8080/health
```

Do not proceed to the ALB until the application responds correctly.

### Step 5 — Configure Ingress and HTTPS

Complete the Ingress manifest from Section 4 by adding the certificate ARN annotation from Section 5. Confirm that the host matches the certificate's covered domain.

Then apply it:

```bash
kubectl apply -f k8s/fastapi-ingress.yaml

kubectl get ingress fastapi -w
```

Inspect the resulting resources:

```bash
kubectl describe ingress fastapi

kubectl get ingress fastapi \
  -o jsonpath='{.status.loadBalancer.ingress[*].hostname}'

echo
```

Wait for the ALB to be provisioned and its targets to become healthy. The AWS Load Balancer Controller manages the ALB configuration based on the Kubernetes resources and supported annotations. Amazon EKS +1

### Step 6 — Restrict network access

For the public application architecture:

* Keep worker nodes and application Pods in private subnets where appropriate.

* Allow inbound HTTPS on port `443` to the ALB from the intended client CIDRs.

* Restrict backend traffic so that only the appropriate ALB or other authorized paths can reach the application.

* Avoid publicly exposing worker-node management ports.

* Use a supported NetworkPolicy implementation if Pod-level traffic isolation is required.

For a private application, use an internal ALB and ensure clients have the appropriate VPN or VPC connectivity. Do not simply make the ALB public and rely on an application-level login as the only network boundary.

### Step 7 — Verify the complete application path

After creating the DNS alias record:

```bash
dig +short "$DOMAIN"

curl -i "https://${DOMAIN}/health"
```

Inspect ALB target health using the AWS console or CLI. To find the target group associated with the ALB, use the load balancer ARN returned by AWS:

```bash
aws elbv2 describe-target-groups \
  --region "$AWS_REGION" \
  --load-balancer-arn "$ALB_ARN" \
  --query 'TargetGroups[].{Name:TargetGroupName,Arn:TargetGroupArn,Port:Port}' \
  --output table
```

Then inspect target health:

```bash
aws elbv2 describe-target-health \
  --region "$AWS_REGION" \
  --target-group-arn "$TARGET_GROUP_ARN" \
  --output table
```

Set `ALB_ARN` and `TARGET_GROUP_ARN` to the actual returned values. Do not use placeholder values literally.

### Step 8 — Troubleshoot and validate

Use this checklist to confirm that the deployment is functioning correctly.

Lab completion checklist

0 of 9

FastAPI Pods are Ready and the Service has endpoints.

The AWS Load Balancer Controller is running and has the required IAM permissions.

The ALB was provisioned in the expected subnets and has the intended scheme.

The ALB target group reports healthy targets.

The ACM certificate is issued and attached to the HTTPS listener.

DNS resolves the application hostname to the expected ALB.

HTTPS requests succeed and HTTP requests redirect to HTTPS.

Network restrictions prevent unintended direct access to the application.

Pulumi infrastructure changes are reproducible and version-controlled.

### Step 9 — Clean up lab resources

Delete the Kubernetes resources you created:

```bash
kubectl delete -f k8s/fastapi-ingress.yaml
kubectl delete -f k8s/fastapi.yaml
```

Allow time for the ALB and related resources to be removed. Delete any lab-specific DNS records, certificates, and infrastructure only after confirming they are not shared by other workloads.

If Pulumi created the dedicated infrastructure specifically for this lab, review the planned changes before destroying the stack:

```bash
pulumi preview --diff
```

Use `pulumi destroy` only if the stack exclusively owns disposable lab resources. Do not destroy the shared EKS cluster or VPC from Module 5 as part of routine cleanup.

### Module 6 summary

You have covered the full application-exposure path on EKS: Kubernetes Services, Ingress, AWS Load Balancer Controller, ALB routing, ACM certificates, DNS, VPC CNI, network security, and troubleshooting.

The key design principle is to keep the application backend private where possible, expose only the required entry point, and verify each networking layer independently.

For the next module, the natural progression is EKS Workloads, Storage, and Identity, covering persistent storage, workload IAM, EKS Pod Identity, IRSA, Secrets Manager, and Helm.
