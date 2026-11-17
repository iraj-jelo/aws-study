### Module 7 — EKS Workloads, Storage, and Identity

AWS ECS/EKS Course · Module 7 of 9

### Learning objectives

By the end of this module, you will understand how to run stateful workloads on Amazon EKS, provision persistent storage, grant AWS permissions to individual Kubernetes workloads, integrate AWS Secrets Manager, package applications with Helm, and manage EKS add-ons using Pulumi and Python.

The practical lab will build on the EKS cluster, ECR image, and FastAPI deployment from the previous modules. All shell commands and scripts use Bash, not PowerShell.

### 1\. Kubernetes storage fundamentals

Containers are ephemeral: when a container restarts, its writable container filesystem may be lost. Kubernetes persistent storage separates application data from the container lifecycle.

### Core storage resources

StorageClass

Defines how storage is dynamically provisioned, including the provisioner and storage parameters.

PersistentVolumeClaim (PVC)

A workload's request for storage capacity, access modes, and optionally a particular StorageClass.

PersistentVolume (PV)

The Kubernetes resource representing the actual provisioned or statically configured storage.

Pod volume mount

Makes the claimed storage available at a directory inside the application container.

### Storage lifecycle

* A developer creates a PVC.

* Kubernetes uses its StorageClass to request storage from a provisioner.

* The provisioner creates or selects a backing storage resource.

* The PVC binds to a PV.

* A Pod mounts the claim and reads or writes data.

With dynamic provisioning, you generally do not create the PV manually.

### Inspect storage resources

```bash
kubectl get storageclass
kubectl get pv
kubectl get pvc --all-namespaces
kubectl describe storageclass
```

On EKS, a StorageClass is only useful when its corresponding CSI driver and infrastructure permissions are configured correctly.

### 2\. Amazon EBS CSI and Amazon EFS CSI

Amazon EKS integrates with AWS storage through Container Storage Interface (CSI) drivers.

![Kubernetes Storage Playlist - Part 3: Implementing Amazon EBS Storage with Amazon EKS Using Terraform and Kubernetes Manifests - DEV Community](https://images.openai.com/static-rsc-4/Ng6FtHzmYRsPtQ7F1FUQKvMfIC606PI1Jqat_Enqcb0Wa69WLJOKoh5uJDJNdnOPKXWK59WYkqKDeGZuO0NQ4fEqtlZDF1rdywOJPOaj0QfTd7GVm1JApyROzwV5lSBDmH65k14yInVJuZDzkZiTEPxH2WJbVwKkTjQEsuJzv8i94XO5Tp0A0zTRliYNXZSR?purpose=fullsize)

Amazon EBS CSI driver

Provides persistent block storage, commonly for databases and applications requiring a dedicated filesystem.

* Typically suited to one node mounting a volume for read/write access.

* EBS volumes are Availability Zone-specific.

* Supports snapshots and volume expansion when configured appropriately.

* A volume may be remounted on another node in the same AZ, subject to attachment and access constraints.

![AWS - EFS - Develop study](https://images.openai.com/static-rsc-4/_RT8Q0WYVxCALoc-XeqoWAySMS0XMhKMdlU3OBMNUWgULeRiJHxmbBnf0Swe-OUdu0ACNwOgL03NCkcZmIoFKLatK2-MP6KAIn88IZzgGQB-tIDP9RgprSH3eAQh__jsmrK0sUt5hQGTeHjDeiFAtMwh67voPhj4da22KtjcMDvOns5FKYE28Dp_O08inXct?purpose=fullsize)

Amazon EFS CSI driver

Provides shared network file storage that multiple Pods can mount concurrently.

* Supports shared access using `ReadWriteMany`.

* Suitable for shared uploads, content, and application files.

* Can serve clients across multiple Availability Zones in a Region.

* Requires suitable network connectivity, mount targets, and security-group rules.

### EBS versus EFS

| Property            | EBS                                  | EFS                                        |
| ------------------- | ------------------------------------ | ------------------------------------------ |
| Storage type        | Block                                | Shared file                                |
| Typical access      | ReadWriteOnce                        | ReadWriteMany                              |
| Multi-AZ behavior   | Volume is AZ-specific                | Regional filesystem can serve multiple AZs |
| Common workloads    | Databases, single-instance state     | Shared files, uploads, multiple replicas   |
| Cost considerations | Provisioned capacity and volume type | Stored data and throughput-related charges |

`ReadWriteOnce` means read/write mounting from a single node, not necessarily a single Pod. For a typical single-writer EBS workload, use one replica unless the application and storage arrangement explicitly support more.

### Install and manage CSI drivers

Before using a driver, verify that it is installed and has the required permissions.

```bash
kubectl get pods -n kube-system
kubectl get csidriver
kubectl get storageclass
```

The EBS CSI driver is available as an EKS managed add-on. The EFS CSI driver is also available through EKS add-on management; installation and configuration depend on the chosen deployment method and cluster setup.

Important: installing a CSI driver does not automatically give it AWS permissions. EBS provisioning requires suitable IAM permissions, and EFS dynamic provisioning may require an appropriately configured EFS filesystem and access-point permissions.

### 3\. Stateful workloads and availability

Kubernetes separates workload management from storage management. A Deployment is appropriate for many stateless applications, while a StatefulSet provides stable Pod identities and ordered lifecycle operations for workloads that need them.

### Deployment versus StatefulSet

| Feature      | Deployment                                | StatefulSet                         |
| ------------ | ----------------------------------------- | ----------------------------------- |
| Typical use  | Stateless APIs and web apps               | Databases and stateful services     |
| Pod identity | Replaceable                               | Stable ordinal identity             |
| Storage      | Shared or individual claims as configured | Can create a PVC per replica        |
| Scaling      | General-purpose                           | Ordered lifecycle behavior          |
| Example      | FastAPI API                               | PostgreSQL, clustered data services |

A StatefulSet does not automatically make an application highly available. Replication, recovery, consistency, backups, and failover must be designed at the application and storage layers.

### Persistent-volume retention

Inspect a StorageClass's reclaim policy:

```bash
kubectl get storageclass -o yaml
kubectl get pv -o wide
kubectl describe pvc <claim-name>
```

Common reclaim policies are:

* `Delete`: the backing storage may be deleted after the claim and volume lifecycle reaches the relevant deletion stage.

* `Retain`: the backing volume is preserved for manual recovery or cleanup.

For important data, configure retention intentionally, implement backups, and test restoration. A persistent volume is not a backup.

For EBS-backed workloads, Kubernetes volume topology and Pod scheduling must align with the volume's Availability Zone. EFS can simplify multi-AZ shared-file access, but does not replace backup or application-level resilience.

### 4\. Workload identity: Pod Identity and IRSA

Applications running in EKS often need to access AWS APIs, such as S3, Secrets Manager, or DynamoDB. The recommended approach is to give each workload an identity with narrowly scoped IAM permissions rather than embedding long-lived access keys in containers.

Kubernetes Pod

FastAPI or another application

Workload identity

EKS Pod Identity or IAM Roles for Service Accounts (IRSA)

IAM role and policy

Trust policy identifies the permitted workload; the permissions policy defines which AWS operations it can perform.

AWS service

For example, a designated S3 bucket or a specific Secrets Manager secret.

### Option A: EKS Pod Identity

EKS Pod Identity uses the EKS Pod Identity Agent and an association between a Kubernetes service account and an IAM role.

Typical setup:

* Install or verify the EKS Pod Identity Agent add-on.

* Create an IAM role whose trust policy permits the EKS Pod Identity service principal, constrained to the intended cluster and account.

* Attach a least-privilege permissions policy to the role.

* Associate the role with a cluster, namespace, and Kubernetes service account.

* Configure the application to use the AWS SDK's default credential provider chain.

This approach can simplify role trust configuration across clusters. It is available for supported EKS configurations; validate the cluster version, platform requirements, and network connectivity.

### Option B: IAM Roles for Service Accounts (IRSA)

IRSA uses the cluster's OIDC identity provider. An IAM role trust policy restricts assumption of the role to a particular service account subject and the expected audience.

The application receives web-identity credentials through the AWS SDK credential provider chain. IRSA remains a valid choice, especially for existing clusters and environments already standardized on OIDC federation.

### Which should you choose?

| Consideration          | Pod Identity                               | IRSA                                                    |
| ---------------------- | ------------------------------------------ | ------------------------------------------------------- |
| Identity association   | EKS association                            | OIDC trust and service account annotation               |
| Cluster setup          | Pod Identity Agent and supported EKS setup | IAM OIDC provider for the cluster                       |
| Cross-account patterns | Depends on role and service design         | OIDC federation can support cross-account role patterns |
| Existing deployments   | Useful for supported new deployments       | Common in established EKS environments                  |

Security rule: never place AWS access keys in a Docker image, Git repository, Helm values file, or Kubernetes manifest. Use workload identity and narrowly scoped policies.

### 5\. Secure S3 access from a Pod

For the lab, the application will upload and retrieve an object in a dedicated S3 bucket using the AWS SDK for Python (`boto3`).

The IAM policy should grant only the required actions on the target bucket or its objects. For example:

* `s3:ListBucket` on the bucket ARN, if listing is required.

* `s3:GetObject` on the intended object ARN pattern, if reading is required.

* `s3:PutObject` on the intended object ARN pattern, if uploading is required.

Do not grant `s3:*` on `*` just to make a deployment work.

### Application example

```python
import os

import boto3
from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI()

s3 = boto3.client("s3")
bucket = os.environ["S3_BUCKET"]

@app.get("/health")
def health():
    return {"status": "ok"}

@app.put("/objects/{key}")
def put_object(key: str):
    # Production applications should validate keys and authorization.
    s3.put_object(
        Bucket=bucket,
        Key=f"uploads/{key}",
        Body=b"Created by an EKS workload",
    )
    return {"uploaded": True, "key": key}

@app.get("/objects/{key}")
def get_object(key: str):
    result = s3.get_object(
        Bucket=bucket,
        Key=f"uploads/{key}",
    )
    body = result["Body"].read().decode("utf-8")
    return JSONResponse({"key": key, "content": body})
```

The code intentionally uses `boto3.client("s3")` without supplying credentials. The SDK obtains credentials from the configured workload identity mechanism.

For production, validate and authorize object keys, avoid unrestricted access to arbitrary objects, and consider streaming large downloads rather than reading the entire object into memory.

### 6\. AWS Secrets Manager integration

Applications frequently need database passwords, API tokens, and other secrets. Kubernetes Secrets alone are not an encrypted secret-management system unless the cluster's encryption and access controls are properly configured.

Two common integration approaches are:

* AWS Secrets and Configuration Provider (ASCP) with the Secrets Store CSI Driver: mounts supported secrets into Pods as files.

* AWS SDK access: the application retrieves a secret directly from Secrets Manager using its workload identity.

For ASCP, verify the Secrets Store CSI Driver and AWS provider are installed and configured for the cluster. Configure the appropriate IAM access, secret reference, and mount behavior.

For SDK-based access, grant only `secretsmanager:GetSecretValue` on the required secret, plus the appropriate KMS decrypt permission if a customer-managed KMS key requires it.

Avoid printing secret values in logs or passing them as command-line arguments. Also consider rotation behavior: a process that reads a secret only once at startup may need a restart or refresh mechanism to pick up rotated values.

### 7\. Helm charts and reusable application packaging

Helm packages Kubernetes resources into charts. It helps separate reusable deployment templates from environment-specific configuration.

A typical chart structure:

```text
fastapi-chart/
├── Chart.yaml
├── values.yaml
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    └── serviceaccount.yaml
```

Example `values.yaml`:

```yaml
replicaCount: 1

image:
  repository: YOUR_ECR_IMAGE_URI
  tag: "1.0.0"

service:
  port: 8000

serviceAccount:
  create: true
  name: fastapi
  annotations: {}
```

Example installation:

```bash
helm lint ./fastapi-chart

helm upgrade --install fastapi ./fastapi-chart \
  --namespace applications \
  --create-namespace \
  --set image.repository="$ECR_IMAGE_URI" \
  --set image.tag="$IMAGE_TAG"
```

Keep environment-specific settings in version-controlled values files or controlled deployment configuration. Do not put secret values directly in Helm values.

Helm and Pulumi have different responsibilities:

* Pulumi provisions AWS infrastructure and can also manage Kubernetes resources.

* Helm templates and packages Kubernetes applications.

* AWS IAM controls access to AWS APIs.

* Kubernetes RBAC controls access to Kubernetes API resources.

You can manage a Helm release through Pulumi's Kubernetes provider, or deploy it through a separate CI/CD step. Choose one clear owner for each resource to avoid conflicting updates.

### 8\. Resource quotas, limits, and workload isolation

Kubernetes resource controls help prevent one namespace or workload from exhausting cluster resources.

Important mechanisms include:

* `requests.cpu` and `requests.memory`: scheduling and resource-allocation requirements.

* `limits.cpu` and `limits.memory`: upper resource bounds enforced by the container runtime and Kubernetes.

* `ResourceQuota`: caps aggregate resource consumption within a namespace.

* `LimitRange`: defines defaults and minimum or maximum resource values.

* Namespaces and RBAC: separate workload ownership and access.

* NetworkPolicy: controls Pod traffic when a compatible network-policy enforcement mechanism is installed and configured.

Example deployment resources:

```yaml
resources:
  requests:
    cpu: "100m"
    memory: "128Mi"
  limits:
    cpu: "500m"
    memory: "512Mi"
```

For stateful applications, ensure that resource limits, storage requests, and disruption behavior reflect the application's actual needs. CPU limits can throttle workloads, and memory-limit breaches can lead to container termination.

### 9\. EKS managed add-ons and lifecycle management

EKS add-ons provide managed installation and lifecycle integration for selected cluster components.

Common examples include:

* Amazon VPC CNI

* CoreDNS

* kube-proxy

* Amazon EBS CSI driver

* Amazon EKS Pod Identity Agent

EFS CSI and other add-ons can also be managed through supported EKS add-on mechanisms, depending on the component and version.

Inspect installed add-ons:

```bash
aws eks list-addons \
  --cluster-name "$CLUSTER_NAME" \
  --region "$AWS_REGION"

aws eks describe-addon \
  --cluster-name "$CLUSTER_NAME" \
  --addon-name aws-ebs-csi-driver \
  --region "$AWS_REGION"
```

For each add-on, track compatibility with the Kubernetes version, select a supported version, review configuration conflicts, and plan upgrades. A successful control-plane upgrade does not guarantee that every add-on is compatible or healthy.

With Pulumi, manage add-on versions and configuration as code wherever supported. Do not independently install a second copy of a component that is already managed by EKS.

### Lab — Deploy a Stateful, AWS-Integrated Application

### Lab architecture

In this lab, you will deploy FastAPI to your existing EKS cluster, attach persistent EBS storage, grant the application access to S3 using EKS Pod Identity, and package the Kubernetes resources with Helm.

![Amazon EKS add-ons: A curated set of software for managing your Kubernetes clusters - DEV Community](https://images.openai.com/static-rsc-4/1JztiA6qZ11qDowr_4gbK_7yvyS5evlAMjmGufto_oiDVt62O5iIDlLKsM3yD_w-n8jZ9OamKUX0Uq7E8BOvsomtpRCiFZ3-VXgQ2nHuKo2LmBZkiaF9ch1Gs8xpy4nHLCE68REUo-eJo45qZLGYOXIbLCIDguGcoSK8Bd2nL3p9-J5PHb2vv6I8D8ACM0Rv?purpose=fullsize)

Components

* Existing EKS cluster and managed node group from the previous modules.

* Amazon ECR image containing the FastAPI application.

* Amazon EBS CSI driver and a dynamically provisioned persistent volume.

* Amazon S3 bucket for application object storage.

* EKS Pod Identity association and a least-privilege IAM role.

* Helm chart for the Kubernetes application and its service account.

### Lab assumptions

This lab builds on the existing AWS and EKS environment rather than creating another cluster. You will use Bash, AWS CLI, `kubectl`, Helm, Python, and Pulumi.

The commands assume you have already configured AWS CLI credentials, selected the correct region, and deployed the EKS cluster. The EKS nodes need access to the AWS APIs and container image registry they use, either through suitable network access or the appropriate endpoints.

### Lab step 1 — Set environment variables

Run these commands in Bash, substituting your existing cluster name and ECR image URI.

```bash
export AWS_REGION="eu-west-2"
export CLUSTER_NAME="your-existing-eks-cluster"
export ECR_IMAGE_URI="123456789012.dkr.ecr.eu-west-2.amazonaws.com/fastapi"
export IMAGE_TAG="1.0.0"

export NAMESPACE="applications"
export APP_NAME="fastapi"
export SERVICE_ACCOUNT="fastapi"
export S3_BUCKET="your-unique-eks-app-bucket"
```

Confirm your AWS identity and cluster connectivity:

```bash
aws sts get-caller-identity

aws eks update-kubeconfig \
  --name "$CLUSTER_NAME" \
  --region "$AWS_REGION"

kubectl get nodes
kubectl get storageclass
helm version
pulumi version
```

If the cluster uses a non-default EBS StorageClass, identify it before proceeding.

```bash
kubectl get storageclass \
  -o custom-columns=NAME:.metadata.name,PROVISIONER:.provisioner
```

For the EBS portion of this lab, the selected StorageClass must use the EBS CSI driver.

### Lab step 2 — Verify the EBS CSI driver

Check whether the EBS CSI driver is already installed:

```bash
aws eks describe-addon \
  --cluster-name "$CLUSTER_NAME" \
  --addon-name aws-ebs-csi-driver \
  --region "$AWS_REGION"
```

If the add-on is absent, install a version compatible with your EKS cluster. First inspect the available versions:

```bash
aws eks describe-addon-versions \
  --addon-name aws-ebs-csi-driver \
  --kubernetes-version "$(aws eks describe-cluster \
    --name "$CLUSTER_NAME" \
    --region "$AWS_REGION" \
    --query 'cluster.version' \
    --output text)" \
  --region "$AWS_REGION"
```

Select a supported version from the returned results. Before installation, configure the driver's required IAM permissions, preferably through a dedicated IAM role and supported workload identity mechanism.

For a quick diagnostic:

```bash
kubectl get pods -n kube-system
kubectl get csidriver
kubectl get events -A --sort-by=.lastTimestamp
```

Do not proceed until the CSI driver is healthy and the required permissions are configured.

### Lab step 3 — Provision the S3 bucket with Pulumi

Create a separate Pulumi project for the lab's AWS resources.

```bash
mkdir eks-workloads-lab
cd eks-workloads-lab

pulumi new aws-python
```

Configure the stack:

```bash
pulumi config set aws:region "$AWS_REGION"
pulumi config set clusterName "$CLUSTER_NAME"
pulumi config set bucketName "$S3_BUCKET"
```

Replace `__main__.py` with the following example. It creates a private S3 bucket with versioning and public-access blocking.

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

bucket_name = config.require("bucketName")

bucket = aws.s3.BucketV2(
    "app-data",
    bucket=bucket_name,
    force_destroy=False,
    tags={
        "Application": "fastapi",
        "Environment": pulumi.get_stack(),
        "ManagedBy": "Pulumi",
    },
)

aws.s3.BucketVersioningV2(
    "app-data-versioning",
    bucket=bucket.id,
    versioning_configuration={
        "status": "Enabled",
    },
)

aws.s3.BucketPublicAccessBlock(
    "app-data-public-access",
    bucket=bucket.id,
    block_public_acls=True,
    block_public_policy=True,
    ignore_public_acls=True,
    restrict_public_buckets=True,
)

pulumi.export("bucket_name", bucket.bucket)
pulumi.export("bucket_arn", bucket.arn)
```

Install the provider dependency if necessary:

```bash
uv add pulumi pulumi-aws
```

Preview and deploy:

```bash
pulumi preview
pulumi up
```

Retrieve the outputs:

```bash
export S3_BUCKET="$(pulumi stack output bucket_name)"
export S3_BUCKET_ARN="$(pulumi stack output bucket_arn)"
```

The bucket is private, but this alone does not authorize the application to access it. That permission will be granted through workload identity.

### Lab step 4 — Create an IAM role for EKS Pod Identity

Create a dedicated IAM policy for the application. The example permits only object reads and writes under the `uploads/` prefix.

```bash
cat > s3-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "${S3_BUCKET_ARN}/uploads/*"
    }
  ]
}
EOF
```

Create the policy:

```bash
export ACCOUNT_ID="$(aws sts get-caller-identity \
  --query Account --output text)"

export POLICY_ARN="$(aws iam create-policy \
  --policy-name "${APP_NAME}-s3-uploads" \
  --policy-document file://s3-policy.json \
  --query 'Policy.Arn' \
  --output text)"
```

For Pod Identity, create a trust policy that allows the EKS Pod Identity service principal and restricts the role to the intended cluster, namespace, and service account. This example assumes the AWS account and cluster are in the same account.

```bash
cat > trust-policy.json <<EOF
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Service": "pods.eks.amazonaws.com"
      },
      "Action": [
        "sts:AssumeRole",
        "sts:TagSession"
      ],
      "Condition": {
        "StringEquals": {
          "aws:SourceAccount": "${ACCOUNT_ID}"
        },
        "ArnEquals": {
          "aws:SourceArn": "arn:aws:eks:${AWS_REGION}:${ACCOUNT_ID}:cluster/${CLUSTER_NAME}"
        }
      }
    }
  ]
}
EOF
```

Create the role and attach the policy:

```bash
export ROLE_ARN="$(aws iam create-role \
  --role-name "${APP_NAME}-pod-identity-role" \
  --assume-role-policy-document file://trust-policy.json \
  --query 'Role.Arn' \
  --output text)"

aws iam attach-role-policy \
  --role-name "${APP_NAME}-pod-identity-role" \
  --policy-arn "$POLICY_ARN"
```

The role trust policy and permissions policy have different purposes: the first controls who can assume the role, while the second controls which AWS actions the role can perform.

### Verify the Pod Identity Agent

```bash
kubectl get pods -n kube-system | grep -i pod-identity
```

If it is not installed, install the EKS Pod Identity Agent as a managed add-on after verifying version compatibility and the cluster's permissions.

Create the namespace and service account:

```bash
kubectl create namespace "$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -

kubectl create serviceaccount "$SERVICE_ACCOUNT" \
  --namespace "$NAMESPACE" \
  --dry-run=client -o yaml | kubectl apply -f -
```

Associate the service account with the role:

```bash
aws eks create-pod-identity-association \
  --cluster-name "$CLUSTER_NAME" \
  --namespace "$NAMESPACE" \
  --service-account "$SERVICE_ACCOUNT" \
  --role-arn "$ROLE_ARN" \
  --region "$AWS_REGION"
```

Allow for propagation of the association and IAM policy before testing. Pods should be created or restarted after the identity configuration is ready.

### Lab step 5 — Create a persistent volume claim

Create a file called `storage.yaml`:

```yaml

apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: fastapi-data
  namespace: applications
spec:
  accessModes:
    - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 5Gi
```

Apply it:

```bash
kubectl apply -f storage.yaml

kubectl get pvc -n "$NAMESPACE" --watch
```

Use `gp3` only if that StorageClass exists in your cluster. Otherwise, change the value to the name of your configured EBS CSI StorageClass.

The claim should eventually become `Bound` when the provisioner, IAM permissions, node topology, and AWS capacity are all correct.

If it remains `Pending`, inspect the claim:

```bash
kubectl describe pvc fastapi-data -n "$NAMESPACE"
kubectl get events -n "$NAMESPACE" --sort-by=.lastTimestamp
```

### Lab step 6 — Package the application with Helm

Create the chart structure:

```bash
mkdir -p fastapi-chart/templates
```

Create `fastapi-chart/Chart.yaml`:

```yaml

apiVersion: v2
name: fastapi
description: FastAPI application with EKS storage and AWS identity
type: application
version: 0.1.0
appVersion: "1.0.0"
```

Create `fastapi-chart/values.yaml`:

```yaml

replicaCount: 1

image:
  repository: ""
  tag: "1.0.0"
  pullPolicy: IfNotPresent

serviceAccount:
  name: fastapi

s3:
  bucket: ""

persistence:
  enabled: true
  claimName: fastapi-data
  mountPath: /data

service:
  port: 8000

resources:
  requests:
    cpu: 100m
    memory: 128Mi
  limits:
    cpu: 500m
    memory: 512Mi
```

Create `fastapi-chart/templates/deployment.yaml`:

```yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .Release.Name }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .Release.Name }}
  template:
    metadata:
      labels:
        app: {{ .Release.Name }}
    spec:
      serviceAccountName: {{ .Values.serviceAccount.name }}
      containers:
        - name: fastapi
          image: "{{ .Values.image.repository }}:{{ .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          ports:
            - name: http
              containerPort: 8000
          env:
            - name: S3_BUCKET
              value: {{ .Values.s3.bucket | quote }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
          volumeMounts:
            - name: app-data
              mountPath: {{ .Values.persistence.mountPath }}
          readinessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 5
            periodSeconds: 10
          livenessProbe:
            httpGet:
              path: /health
              port: http
            initialDelaySeconds: 15
            periodSeconds: 20
      volumes:
        - name: app-data
          persistentVolumeClaim:
            claimName: {{ .Values.persistence.claimName }}
```

Create `fastapi-chart/templates/service.yaml`:

```yaml

apiVersion: v1
kind: Service
metadata:
  name: {{ .Release.Name }}
spec:
  type: ClusterIP
  selector:
    app: {{ .Release.Name }}
  ports:
    - name: http
      port: {{ .Values.service.port }}
      targetPort: http
```

The chart references the service account created earlier. The Pod Identity association is managed separately by AWS, so Helm does not need to embed AWS credentials or an IAM role's access keys.

Validate the chart:

```bash
helm lint ./fastapi-chart

helm template "$APP_NAME" ./fastapi-chart \
  --namespace "$NAMESPACE" \
  --set image.repository="$ECR_IMAGE_URI" \
  --set image.tag="$IMAGE_TAG" \
  --set s3.bucket="$S3_BUCKET"
```

Install it:

```bash
helm upgrade --install "$APP_NAME" ./fastapi-chart \
  --namespace "$NAMESPACE" \
  --set image.repository="$ECR_IMAGE_URI" \
  --set image.tag="$IMAGE_TAG" \
  --set s3.bucket="$S3_BUCKET"
```

Application requirement: the image must include the S3 endpoints and write its persistent data under `/data` for the storage test. The S3 example in section 5 illustrates the required AWS SDK usage. If your current FastAPI image does not use `/data` or expose `/health`, adapt the chart or application accordingly.

### Lab step 7 — Validate storage and workload identity

Wait for the deployment:

```bash
kubectl rollout status deployment/"$APP_NAME" \
  -n "$NAMESPACE"

kubectl get pods -n "$NAMESPACE"
kubectl get pvc -n "$NAMESPACE"
kubectl get pv
```

Check the application's logs:

```bash
kubectl logs deployment/"$APP_NAME" \
  -n "$NAMESPACE" --tail=100
```

Test the HTTP service locally using port forwarding:

```bash
kubectl port-forward \
  -n "$NAMESPACE" \
  service/"$APP_NAME" 8000:8000
```

In a second Bash terminal:

```bash
curl -i http://localhost:8000/health
```

If you implemented the S3 routes from section 5, test them:

```bash
curl -i -X PUT \
  http://localhost:8000/objects/lab.txt

curl -i \
  http://localhost:8000/objects/lab.txt
```

Check the object using AWS CLI from your own administrative credentials:

```bash
aws s3api head-object \
  --bucket "$S3_BUCKET" \
  --key uploads/lab.txt \
  --region "$AWS_REGION"
```

This final command verifies that an object exists; it does not, by itself, prove the Pod used Pod Identity. To validate the identity path, inspect the association, ensure the application uses the SDK's default credential provider chain, and confirm the Pod can perform the permitted S3 operation without static credentials.

### Lab step 8 — Verify persistent storage

If the application writes a file under `/data`, verify that the file remains after a Pod restart.

```bash
kubectl exec -n "$NAMESPACE" \
  deployment/"$APP_NAME" -- \
  sh -c 'echo persistent-data > /data/test.txt && cat /data/test.txt'
```

Delete the Pod to force Kubernetes to replace it:

```bash
kubectl delete pod \
  -n "$NAMESPACE" \
  -l app="$APP_NAME"
```

Wait for the replacement and inspect the file:

```bash
kubectl rollout status deployment/"$APP_NAME" \
  -n "$NAMESPACE"

kubectl exec -n "$NAMESPACE" \
  deployment/"$APP_NAME" -- \
  cat /data/test.txt
```

The file should remain because the replacement Pod mounts the same PVC. This demonstrates persistence across Pod replacement, not protection against volume deletion, storage failure, or application-level corruption.

### Lab step 9 — Troubleshooting guide

| Symptom                             | What to inspect                                                               |
| ----------------------------------- | ----------------------------------------------------------------------------- |
| PVC stuck in Pending                | StorageClass, CSI controller logs, IAM permissions, events, AZ topology       |
| Pod stuck in ContainerCreating      | Volume attachment, CSI node plugin, image pull, node events                   |
| AccessDenied from S3                | Pod Identity association, role trust, attached policy, object ARN             |
| AWS SDK reports missing credentials | Pod Identity Agent, association propagation, SDK version and credential chain |
| Pod enters CrashLoopBackOff         | Application logs, environment variables, health probes                        |
| Pod cannot access AWS APIs          | DNS, route tables, NAT or VPC endpoints, security groups                      |
| Secret retrieval fails              | Secret ARN, IAM policy, KMS permissions, provider configuration               |
| Add-on installation fails           | EKS version compatibility, IAM permissions, configuration conflicts           |

Useful diagnostic commands:

```bash
kubectl describe pod -n "$NAMESPACE" \
  "$(kubectl get pods -n "$NAMESPACE" \
    -l app="$APP_NAME" \
    -o jsonpath='{.items[0].metadata.name}')"

kubectl get events -n "$NAMESPACE" \
  --sort-by=.lastTimestamp

kubectl get pods -n kube-system
kubectl get csidriver
kubectl get pvc -n "$NAMESPACE"
```

### Lab step 10 — Cleanup and cost management

Delete the Helm release and the lab's Kubernetes resources when you no longer need them:

```bash
helm uninstall "$APP_NAME" -n "$NAMESPACE"

kubectl delete pvc fastapi-data -n "$NAMESPACE"
```

Warning: deleting a PVC can lead to deletion of its backing EBS volume when the reclaim policy is `Delete`. Verify that the data is disposable before running these commands.

After confirming that no resources depend on the lab's S3 bucket, you can remove the Pulumi-managed bucket and its related resources:

```bash
cd eks-workloads-lab
pulumi destroy
```

The bucket has versioning enabled, so it may contain object versions or delete markers. Emptying a versioned bucket requires deleting its object versions and delete markers before it can be deleted. Review the resources before confirming any destructive operation.

Also remove the lab's IAM role and policy, Pod Identity association, and any add-ons that were installed exclusively for the lab. Do not remove shared cluster resources that are still used by other workloads.

### Module 7 — Final reference

By completing the module, you have covered:

* Kubernetes PVs, PVCs, and StorageClasses.

* EBS block storage and EFS shared file storage.

* Stateful workloads, storage topology, and retention.

* EKS Pod Identity and IRSA.

* Least-privilege AWS access from Kubernetes workloads.

* Secrets Manager integration patterns.

* Helm chart structure and deployment configuration.

* Kubernetes requests, limits, and namespace isolation.

* EKS managed add-ons and lifecycle operations.

* Pulumi-based AWS provisioning and Bash-based operational workflows.

The key architectural principle is to keep application data persistent, assign AWS permissions to individual workloads, and manage infrastructure and application deployment declaratively. These practices provide a solid foundation for the production scaling, observability, and security topics in Module 8.
