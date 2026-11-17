### Module 2 — Amazon ECR and Container Image Delivery

AWS ECS/EKS Course · Module 2 of 9 · Pulumi with Python

### Learning objectives

By the end of this module, you will be able to:

* Explain how Amazon Elastic Container Registry (ECR) stores and distributes container images.

* Create ECR repositories and configure their security and lifecycle policies using Pulumi.

* Build, tag, scan, and push a FastAPI Docker image to ECR.

* Authenticate Docker with AWS using the AWS CLI and understand the IAM permissions required for publishing images.

* Distinguish mutable tags, immutable tags, and image digests.

* Build smaller, more secure, reproducible container images.

* Establish an image-release workflow that can be reused by both Amazon ECS and Amazon EKS.

### 1\. Lab architecture

We will continue with the FastAPI application introduced in Module 1, keeping the same application endpoints and Docker-based workflow.

FastAPI application

app/main.py · requirements.txt · Dockerfile

Docker build and tag

Local Docker image

Versioned image with a unique digest

AWS CLI authentication and Docker push

Amazon ECR

Private repository · image scanning · lifecycle policy

Amazon ECS

Future deployment

Amazon EKS

Future deployment

The key principle is that ECR is independent of the orchestration platform. ECS tasks and EKS nodes can pull the same published image, provided their identities have the necessary permissions and network connectivity.

### 2\. Amazon ECR fundamentals

Amazon ECR is a managed container image registry. It stores Docker-compatible images and OCI artifacts in repositories and integrates with AWS IAM, vulnerability scanning, and image lifecycle management.

The principal concepts are:

| Concept           | Meaning                                                                         |
| ----------------- | ------------------------------------------------------------------------------- |
| Registry          | The account- and Region-specific image registry endpoint.                       |
| Repository        | A named location for storing related images, such as fastapi-api.               |
| Image tag         | A human-readable label, such as 1.0.0 or release-2026-10-28.                    |
| Image digest      | A content-addressed identifier, typically sha256:..., for an image manifest.    |
| Image manifest    | Metadata describing an image's layers, configuration, and platform information. |
| Lifecycle policy  | Rules that expire selected images to control registry retention and storage.    |
| Repository policy | Resource-based permissions controlling who can access the repository.           |

An ECR image URI typically looks like this:

```text
123456789012.dkr.ecr.eu-west-2.amazonaws.com/fastapi-api:1.0.0
```

The components are:

* `123456789012`: AWS account ID.

* `eu-west-2`: AWS Region.

* `fastapi-api`: repository name.

* `1.0.0`: image tag.

The account ID and Region are examples; your lab will obtain the correct values from your AWS environment.

### Tags versus digests

Tags are convenient for people and release pipelines, but their behavior depends on the repository configuration.

* Mutable tag: can be reassigned to another image.

* Immutable tag: cannot be overwritten with a different image while that tag exists.

* Digest: identifies a specific image manifest by its content hash.

For production deployment, an immutable version tag or digest provides a more reliable reference than a tag such as `latest`.

A subtle but important point: a digest identifies a manifest, which may be a multi-platform image index rather than one platform-specific image. It is still a content-addressed reference suitable for reproducible image selection.

### 3\. AWS CLI authentication and IAM permissions

Before creating resources, verify that the tools from Module 1 are available:

```powershell
aws --version
pulumi version
python --version
docker --version
```

Check which AWS identity the CLI is using:

```powershell
aws sts get-caller-identity
aws configure get region
```

The first command returns your AWS account ID and caller identity. The second shows the configured default Region, if one is set.

For this lab, we will use `eu-west-2` as the example Region. Change it if your Module 1 stack uses a different Region.

### How ECR authentication works

ECR uses IAM for authorization and a temporary registry authentication token for Docker login.

* Authenticate the AWS CLI using your configured AWS credentials or IAM Identity Center.

* Request an ECR authorization token using `aws ecr get-login-password`.

* Pass that token to `docker login` using standard input.

* Push the tagged image to the ECR repository.

The token is valid for 12 hours. It does not replace IAM authorization: AWS still checks permissions for the requested ECR operations. Amazon Web Services, Inc.

For a local developer publishing images, typical IAM permissions include:

| Permission                      | Purpose                                    |
| ------------------------------- | ------------------------------------------ |
| ecr:GetAuthorizationToken       | Authenticate Docker with the registry.     |
| ecr:BatchCheckLayerAvailability | Check whether image layers already exist.  |
| ecr:InitiateLayerUpload         | Begin uploading image layers.              |
| ecr:UploadLayerPart             | Upload image layer data.                   |
| ecr:CompleteLayerUpload         | Complete layer uploads.                    |
| ecr:PutImage                    | Publish the image manifest and tags.       |
| ecr:BatchGetImage               | Retrieve image manifests when needed.      |
| ecr:GetDownloadUrlForLayer      | Download image layers when pulling images. |

Creating the repository through Pulumi requires additional control-plane permissions, including `ecr:CreateRepository`, and possibly permissions for managing lifecycle policies and repository configuration.

For production, separate infrastructure-provisioning permissions from image-publishing permissions. A CI/CD publisher generally should not need permission to create or delete repositories.

### 4\. Pulumi project for ECR

We will create a dedicated infrastructure project named `ecr-fastapi`. This keeps the registry's lifecycle separate from the ECS and EKS projects that will consume its images later.

### Project structure

```text
aws-containers/
├── app/
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .dockerignore
└── infrastructure/
    └── ecr-fastapi/
        ├── Pulumi.yaml
        ├── Pulumi.dev.yaml
        ├── __main__.py
        └── requirements.txt
```

Keep the `app/` directory from Module 1. In the following commands, run them from the `infrastructure/ecr-fastapi/` directory when working with Pulumi.

### Initialize the project

```powershell
mkdir ecr-fastapi
cd ecr-fastapi

pulumi new python
```

If you already created the project in Module 1, reuse it rather than initializing it again.

Install the AWS provider:

```powershell
python -m pip install pulumi pulumi-aws
```

Add these dependencies to `requirements.txt`:

```text
pulumi>=3.0.0
pulumi-aws>=7.0.0
```

For a reproducible environment, pin the tested versions in your actual project or lockfile rather than relying indefinitely on open-ended version ranges.

Configure the stack:

```powershell
pulumi config set aws:region eu-west-2
pulumi config set appName fastapi-api
pulumi config set retentionCount 10
```

The `retentionCount` setting will control how many tagged images the lifecycle policy retains.

### Define the ECR repository

Replace `__main__.py` with:

```python
import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

app_name = config.get("appName") or "fastapi-api"
retention_count = config.get_int("retentionCount") or 10

repository = aws.ecr.Repository(
    "fastapi-repository",
    name=app_name,
    image_tag_mutability="IMMUTABLE",
    image_scanning_configuration={
        "scan_on_push": True,
    },
    encryption_configurations=[
        {
            "encryption_type": "AES256",
        }
    ],
    tags={
        "Project": "aws-containers",
        "ManagedBy": "Pulumi",
        "Application": app_name,
    },
)

lifecycle_policy = aws.ecr.LifecyclePolicy(
    "fastapi-lifecycle-policy",
    repository=repository.name,
    policy=pulumi.Output.all(
        retention_count
    ).apply(
        lambda values: json.dumps(
            {
                "rules": [
                    {
                        "rulePriority": 1,
                        "description": (
                            "Retain the newest "
                            f"{values[0]} tagged images"
                        ),
                        "selection": {
                            "tagStatus": "tagged",
                            "tagPatternList": ["*"],
                            "countType": "imageCountMoreThan",
                            "countNumber": values[0],
                        },
                        "action": {
                            "type": "expire",
                        },
                    }
                ]
            }
        )
    ),
)

pulumi.export("repository_name", repository.name)
pulumi.export("repository_url", repository.repository_url)
pulumi.export("repository_arn", repository.arn)
pulumi.export("registry_id", repository.registry_id)
```

This provisions:

* A private ECR repository.

* Immutable image tags.

* Basic image scanning on push, subject to the registry's scanning configuration.

* Encryption at rest using AES-256.

* A lifecycle policy that retains the newest ten tagged images by default.

The lifecycle policy applies to all tagged images in this repository. If you later introduce production, staging, or release tags with different retention requirements, revise the rules to distinguish those classes. Also note that untagged images are not covered by this particular rule. Pulumi Registry +1

The repository resource and lifecycle policy are managed by Pulumi, so subsequent configuration changes can be previewed before they are applied.

### Deploy the repository

```powershell
pulumi preview
pulumi up
```

Review the proposed changes and approve the deployment.

Retrieve the outputs:

```powershell
pulumi stack output repository_name
pulumi stack output repository_url
pulumi stack output registry_id
```

Save the repository URL for the next steps.

### 5\. Build a production-conscious FastAPI image

We will use the existing Module 1 application and preserve its `/` and `/health` endpoints.

A multi-stage Dockerfile separates dependency preparation from the runtime image. This example also uses a non-root user and a slim Python base image.

`app/Dockerfile`:

```dockerfile
FROM python:3.14-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

COPY requirements.txt .

RUN python -m pip wheel \
    --wheel-dir /wheels \
    -r requirements.txt

FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .

RUN python -m pip install \
        --no-cache-dir \
        --no-index \
        --find-links=/wheels \
        -r requirements.txt \
    && rm -rf /wheels \
    && useradd --create-home --uid 10001 appuser

COPY --chown=appuser:appuser main.py .

USER 10001:10001

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s \
    --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`app/requirements.txt`:

```text
fastapi
uvicorn[standard]
```

For a production release, pin and lock dependencies after verifying compatibility. The unpinned requirements above are suitable as a starting point for this learning lab, not as a complete reproducible-build strategy.

Create `app/.dockerignore`:

```text
.git
.venv
__pycache__
*.py[cod]
.env
.pytest_cache
.mypy_cache
```

Do not copy AWS credentials, Pulumi state files, or local secrets into the image.

### Why these choices matter

* Multi-stage build: keeps build-time wheel artifacts out of the final image.

* Slim base image: reduces unnecessary packages and image size.

* Non-root user: limits the privileges available to the application process.

* Health check: allows container tooling to detect an unhealthy process.

* Dependency locking: helps make subsequent builds repeatable.

* No embedded secrets: prevents credentials from leaking into image layers or registries.

A smaller image is not automatically a secure image. Keep the base image updated, review vulnerability findings, and rebuild regularly.

### 6\. Build, tag, and push the image to ECR

Open PowerShell in the project root, `aws-containers/`.

### Step 1 — Set the deployment variables

```powershell
$Region = "eu-west-2"
$RepositoryName = "fastapi-api"
$Version = "1.0.0"

$AccountId = aws sts get-caller-identity `
    --query Account --output text

$Registry = "$AccountId.dkr.ecr.$Region.amazonaws.com"
$RepositoryUri = "$Registry/$RepositoryName"
$ImageUri = "${RepositoryUri}:$Version"
```

These values must match your Pulumi configuration and outputs. If you used a different repository name or Region, update the variables accordingly.

### Step 2 — Authenticate Docker

```powershell
aws ecr get-login-password --region $Region |
    docker login --username AWS --password-stdin $Registry
```

A successful login should return `Login Succeeded`.

### Step 3 — Build the image

```powershell
docker build `
    --pull `
    -t "${RepositoryName}:${Version}" `
    ./app
```

The `--pull` option checks for a newer version of the base image. For strictly reproducible builds, pin the base image by digest rather than relying on a mutable base-image tag.

Run the container locally before publishing:

```powershell
docker run --rm -d `
    --name fastapi-api `
    -p 8000:8000 `
    "${RepositoryName}:${Version}"
```

Test both endpoints:

```powershell
Invoke-RestMethod http://localhost:8000/
Invoke-RestMethod http://localhost:8000/health
```

Stop the test container:

```powershell
docker stop fastapi-api
```

### Step 4 — Tag and push

Tag the image with its complete ECR URI:

```powershell
docker tag "${RepositoryName}:${Version}" $ImageUri
```

Push it:

```powershell
docker push $ImageUri
```

The push uploads the image layers and manifest. Layers already present in ECR can be reused rather than uploaded again.

### Step 5 — Verify the image

```powershell
aws ecr describe-images `
    --repository-name $RepositoryName `
    --region $Region `
    --query "imageDetails[].{Tags:imageTags,Digest:imageDigest,Size:imageSizeInBytes,Status:imageStatus}"
```

The output should include your `1.0.0` tag and its digest.

Retrieve just the digest:

```powershell
$Digest = aws ecr describe-images `
    --repository-name $RepositoryName `
    --region $Region `
    --image-ids imageTag=$Version `
    --query "imageDetails[0].imageDigest" `
    --output text

$Digest
```

You now have two useful references:

```text
Tag:    123456789012.dkr.ecr.eu-west-2.amazonaws.com/fastapi-api:1.0.0

Digest: 123456789012.dkr.ecr.eu-west-2.amazonaws.com/fastapi-api@sha256:...
```

The digest is the more precise reference for deploying the exact published manifest.

### 7\. Image scanning and vulnerability management

ECR offers two principal scanning modes. Amazon ECR

| Feature             | Basic scanning                                     | Enhanced scanning                                                 |
| ------------------- | -------------------------------------------------- | ----------------------------------------------------------------- |
| Main coverage       | Operating-system package vulnerabilities           | Operating-system and programming-language package vulnerabilities |
| Scan behavior       | Manual or scan on push, depending on configuration | Scan on push and/or continuous scanning                           |
| Service integration | Amazon ECR                                         | Amazon Inspector                                                  |
| Best use            | Basic image vulnerability visibility               | Broader and continuously updated vulnerability monitoring         |

Our Pulumi configuration requests basic scan-on-push behavior. The actual behavior depends on the registry's scanning configuration. Enhanced scanning is configured at the registry level and should be enabled separately if required.

### Inspect scan findings

After pushing the image, check its scan status:

```powershell
aws ecr describe-image-scan-findings `
    --repository-name $RepositoryName `
    --image-id imageTag=$Version `
    --region $Region
```

The scan may not finish immediately. If results are not ready, retry after the scan completes. For basic scanning, use `DescribeImageScanFindings` to retrieve findings rather than relying on older image-summary fields. Amazon ECR

When findings are available, investigate:

* Vulnerable operating-system packages.

* Vulnerable Python dependencies.

* Severity and available fixes.

* Whether the affected package is needed by the application.

* Whether a newer base image or dependency version resolves the finding.

A secure image-release pipeline should evaluate findings before promoting an image to production. Scanning detects known vulnerabilities; it does not prove that an image is safe.

### 8\. Image versioning, immutability, and lifecycle policies

The lab repository uses immutable tags. This means a second push using the same existing tag will be rejected rather than silently replacing the published image.

For example, after publishing `1.0.0`, release a new application version as follows:

```powershell
$Version = "1.0.1"
$ImageUri = "${RepositoryUri}:$Version"

docker build -t "${RepositoryName}:${Version}" ./app
docker tag "${RepositoryName}:${Version}" $ImageUri
docker push $ImageUri
```

Use this general strategy:

* `1.0.0`, `1.0.1`: human-readable release versions.

* A Git commit SHA: traceability back to source code.

* An image digest: exact manifest identity.

* `latest`: optional convenience tag, not a dependable production version reference.

Avoid reusing release tags. If a release must be rebuilt, publish a new tag and digest, and retain the relationship between the source revision, build, and published image.

### How lifecycle policies help

ECR lifecycle policies expire images based on rules such as tag patterns, image age, and image count. Our rule retains the newest ten tagged images.

Review the policy before expanding it to production: expiring an image can affect rollback options if the image is no longer available for deployment. Keep sufficient release history and avoid retention rules that unintentionally delete important production images.

### 9\. Repeatable image-release workflows and CI/CD

The workflow you have built can be reused by both ECS and EKS:

### 1

Source

Commit application code and Dockerfile to version control.

### 2

Build

Build the image using a controlled build environment.

### 3

Validate

Run application checks and scan the image for vulnerabilities.

### 4

Publish

Push a uniquely tagged image to ECR using restricted IAM credentials.

### 5

Record

Save the image tag, digest, source revision, and build metadata.

### 6

Deploy

Reference the published image in an ECS task definition or EKS workload.

### CI/CD security principles

* Use short-lived AWS credentials through a supported identity federation mechanism, such as GitHub Actions OIDC, instead of long-lived access keys where practical.

* Give the publishing identity permission to push only to the required repositories.

* Keep infrastructure provisioning permissions separate from application publishing permissions.

* Scan images before promotion and retain build metadata for traceability.

* Deploy by immutable version or digest.

* Rebuild images regularly to incorporate security fixes.

* Use separate repositories or carefully defined permissions and release processes where environment isolation requires them.

For example, a CI pipeline can publish an image tagged with a commit SHA, record the digest, and pass that digest to the ECS deployment or Kubernetes manifest. This avoids rebuilding the application separately for each environment.

### 10\. Lab completion and cleanup

Use this checklist to verify that the lab is complete.

### Lab checklist

0 of 8

Confirmed AWS identity, Region, and required CLI tools.

Provisioned the private ECR repository using Pulumi.

Configured immutable tags, image scanning, and a lifecycle policy.

Built and tested the FastAPI container locally.

Authenticated Docker and pushed version 1.0.0 to ECR.

Verified the image tag and digest in ECR.

Reviewed the image scanning configuration and findings.

Documented the image URI and digest for future ECS/EKS deployments.

### Clean up

Deleting the Pulumi-managed repository will not necessarily succeed while it still contains images. First, inspect the repository and delete its images if you no longer need them:

```powershell
aws ecr list-images `
    --repository-name $RepositoryName `
    --region $Region
```

For a disposable lab repository, delete all images:

```powershell
aws ecr batch-delete-image `
    --repository-name $RepositoryName `
    --region $Region `
    --image-ids (aws ecr list-images `
        --repository-name $RepositoryName `
        --region $Region `
        --query "imageIds[]" `
        --output json | ConvertFrom-Json | ConvertTo-Json -Compress)
```

If PowerShell has trouble passing the image IDs, retrieve them first and pass the resulting JSON array to the AWS CLI. Do not use this command against a shared or production repository.

Then, from the Pulumi project directory:

```powershell
pulumi destroy
```

Review the proposed changes before approving. This deletes the ECR repository and lifecycle policy managed by this stack. Keep the local Docker image if you intend to reuse it; otherwise remove it with `docker image rm`.

### Further reading

* [Amazon ECR documentation](https://docs.aws.amazon.com/AmazonECR/latest/userguide/what-is-ecr.html?utm_source=chatgpt.com) — registry and repository fundamentals.

* [ECR image scanning](https://docs.aws.amazon.com/AmazonECR/latest/userguide/image-scanning.html?utm_source=chatgpt.com) — basic and enhanced scanning.

* [Pulumi AWS ECR Repository](https://www.pulumi.com/registry/packages/aws/api-docs/ecr/repository/?utm_source=chatgpt.com) — repository resource properties.

* [ECR lifecycle policies](https://docs.aws.amazon.com/AmazonECR/latest/userguide/LifecyclePolicies.html?utm_source=chatgpt.com) — image retention and expiration rules.

Next module: Module 3 — Amazon ECS Fundamentals and Fargate Deployments. We will reuse the ECR image created here, define an ECS task definition, configure IAM roles and networking, and deploy the FastAPI service without rebuilding or republishing the application.
