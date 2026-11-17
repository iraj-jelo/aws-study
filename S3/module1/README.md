### Module 1 — Amazon S3 Fundamentals

AWS S3 Course · Module 1 of 8 · Beginner level · Estimated time: 2–3 hours

### Learning objectives

By the end of this module, you will be able to:

* Explain object storage and how it differs from block and file storage.

* Understand S3 buckets, objects, keys, prefixes, and metadata.

* Explain bucket naming, AWS Regions, and S3's global namespace.

* Understand S3's consistency guarantees and basic object operations.

* Use the AWS Console and CLI to manage objects.

* Provision an S3 bucket using Pulumi with Python.

* Upload, download, list, inspect, and delete objects from the command line.

### 1\. What is Amazon S3?

Amazon Simple Storage Service (S3) is an AWS object storage service designed to store and retrieve data at scale. It is commonly used for application files, backups, logs, media assets, data lakes, and data exchange between services.

Unlike a traditional hard drive, S3 does not expose a disk with sectors and a filesystem that you mount by default. Instead, you interact with objects inside buckets using APIs, SDKs, the AWS Console, or command-line tools.

![What Is Amazon S3? Your Guide to Scalable Cloud Storage | DataCamp](https://images.openai.com/static-rsc-4/sr8zyiIdq6OFhDfikHD-ZA_RLuiEfJUy12sypSK8QfDZtr_F-lwLJt4hWPyRsKzLvnyYaUR6Wz59kp9SlKEdkhefJTPKuOydX4BHIGKEpD8PGZ-ZM7EMAODLj478ZSqmix05Z3m2QyPy9hlfaExBEXfhEbDZcZuy0G1eLk2BE1SDi9jkimIqH-uH2QUn9DMv?purpose=fullsize)

![AWS Storage - Part 4: Amazon S3 - DEV Community](https://images.openai.com/static-rsc-4/JOxgrHP9XH7Kkta7CuMvHsaufdv6fMfXc-yoFS2FsW1ABN64o6SXvLcUUio3d8CTn0gNazbP3f8BdWcd55sAYwA1JRv3uvAha_b5PTZkKxjjSpwbcJ_c9mvmTfSrzqjXJcpHaMn6VF3fWyZuEkqXGoFg-TkP00fDle4s1NGrT8DZNF5D86xGUM0rRu73eHR7?purpose=fullsize)

![Designing an S3 object storage system | Iván Ovejero](https://images.openai.com/static-rsc-4/4iP7BZhj8ZcS7G8bfNYxZPG4hBO2hNtRCn48ffbV_hcd2Qby88kzhmQziYIiB3rFdseAbOJdHgdTTeMo8xoQAgvu3sH4JgCQUJhXFTwMJTBnxKs7lwu8OwP8UUqKNNY2VF1pl8n7UaoyV9awx4hUhevPrIBYy77cEpqZCvH_Z9tu89XcvoFodELEP3RlaAyf?purpose=fullsize)

### 1.1 Object storage versus block and file storage

![Amazon S3 Deep Dive (part 3-object) - DEV Community](https://images.openai.com/static-rsc-4/rB4KPu3n5llOfryMZEvMsPQIs6vwOi1Uyj8sxlCocGBn5Re7iFP0Sizuc1EXCO3CCUjW6mhuSboFNdDih6k3-pCioUEWRpogpePm1vpgZ2jE8ReAaRfLhhvv1KXKfkZZnbgkGIlNzWtK-Z8CxI5Qyok_XBJv82n4ToGm-W11Xh1rQvgGnKJ1VLsocQOe2V0J?purpose=fullsize)

Object storage — Amazon S3

Stores data as objects identified by keys, with associated metadata. Access typically happens through HTTP APIs.

Examples: images, backups, logs, documents, data lake files.

![What Is File And Block Storage at Ida Wheeler blog](https://images.openai.com/static-rsc-4/KqUad1xDypt2FCg6N05Y4ajVwugvbQS4jbKZNxPo_CEqvdoBpob57vs8vD-ojyarR-GZaCGUan3nxxyPMvu2k3KkR8ihzkgndC-4kd6CIzzDLN-rZZWNtpO_p5aIUracuTNytg7Sk5Q1ORcZhG5bAGNRRFE_003REHvFIwDN6NcBx0XYWxLPARZ9f14TYmoT?purpose=fullsize)

Block storage — Amazon EBS

Provides block devices that an operating system can format with a filesystem or use for database storage.

Examples: EC2 boot volumes, database disks, low-latency random reads and writes.

![Repository - Free computer icons](https://images.openai.com/static-rsc-4/7eHCttXDWsVi3QYQItlUck-mV7mqf18VnTMqB9ooLcXipPy_UKnK0EFoJyUC6ip2nvxCRGsZd5opU28oM4E5PNqvmkX9X7hehjr5O1v4dvGhvO6Pv_9bnws3Elx5em9Miuc4kswTdbhbPFjoJQ1H-r9YfQayQpI2zdlehG6eGMZz3Q2hmP9uZF8oqoVbJ0Jx?purpose=fullsize)

File storage — Amazon EFS

Provides a shared filesystem with directories, files, and familiar filesystem operations.

Examples: shared application files, Linux workloads, shared home directories.

The key architectural distinction is how applications access and modify data:

| Characteristic              | S3                          | EBS                     | EFS                      |
| --------------------------- | --------------------------- | ----------------------- | ------------------------ |
| Storage model               | Objects                     | Blocks                  | Files and directories    |
| Typical access              | API / HTTP                  | Attached block device   | Mounted filesystem       |
| Common use                  | Backups, assets, data lakes | EC2 disks, databases    | Shared application files |
| Native filesystem interface | No                          | Usually added by the OS | Yes                      |

Important: S3 is not a drop-in replacement for a filesystem or a database disk. Applications that need filesystem semantics or frequent in-place random writes may need another storage service.

### 1.2 How S3 organizes data

The fundamental hierarchy is simple:

AWS account

Bucket: `training-assets-example`

Object: `images/cat.jpg`

Data + metadata + object key

Object: `reports/2026/january.csv`

A different object with its own key

An object consists of the data being stored, a key that identifies it within its bucket, and system-defined or user-defined metadata. Depending on the configuration, it may also have tags, checksums, encryption settings, and a version ID.

An object key is the complete name of an object within a bucket. For example:

`reports/2026/january.csv`

A prefix is the beginning of a key, such as `reports/2026/`. Prefixes help group objects and filter listings.

S3 is a flat object namespace: the `/` character is part of the key. The Console presents prefixes like folders, but those folders do not generally need to exist as separate resources.

For example, these are two independent object keys:

```text
photos/cat.jpg
photos/dog.jpg
```

The `photos/` prefix does not require a physical directory.

### 1.3 Buckets, names, and Regions

A bucket is a container for objects and a major boundary for configuration, access policies, and many storage settings.

* Bucket names must satisfy S3 naming rules.

* General purpose bucket names are unique within the applicable AWS partition's global namespace.

* A bucket is created in a specific AWS Region.

* The bucket's Region influences request routing, latency, data residency, and some costs.

* Bucket names are visible in URLs, so avoid placing sensitive information in them.

For example, `training-assets-example-12345` might be a bucket name, while `images/cat.jpg` is an object key inside it.

For this course, Pulumi will create the bucket and expose its name as a stack output. We will use that output rather than hardcoding the name in CLI commands.

### 1.4 S3 consistency and object operations

Amazon S3 provides strong read-after-write consistency for successful object PUTs, DELETEs, and related read operations. After a successful write, subsequent reads and listings reflect the change.

Basic operations include:

| Operation     | Purpose                                                          |
| ------------- | ---------------------------------------------------------------- |
| PutObject     | Upload or create an object                                       |
| GetObject     | Retrieve object data                                             |
| HeadObject    | Retrieve object metadata without downloading the data            |
| ListObjectsV2 | List objects using a prefix or delimiter                         |
| DeleteObject  | Delete an object or create a delete marker in a versioned bucket |

Strong consistency does not mean every multi-object workflow is transactional. For example, uploading several related objects does not make the entire group an atomic operation.

Also distinguish between deleting an object in an unversioned bucket and deleting one in a versioned bucket: versioning changes what a delete operation does and how data can be recovered.

### 2\. Lab 1 — Create and explore an S3 bucket

Hands-on lab

Tools: AWS CLI, Pulumi CLI, Python, AWS account

### Lab architecture

You will create one S3 bucket using Pulumi, then manage test objects with the AWS CLI.

Pulumi + Python

Create and manage the bucket

Amazon S3 bucket

Stores objects under unique keys

AWS CLI

Upload · List · Inspect · Download · Delete

### Step 1 — Verify your environment

Check that the required tools are installed:

```bash
aws --version
pulumi version
python --version
```

Configure AWS credentials using your preferred supported method. For a local lab, a named AWS CLI profile is convenient:

```bash
aws configure --profile s3-lab
```

Use credentials with sufficient permissions to create and manage the lab bucket. Avoid using the AWS account root user.

Verify that authentication works:

```bash
aws sts get-caller-identity --profile s3-lab
```

This returns the AWS account ID, principal ARN, and user ID associated with your current credentials.

Choose a Region for the lab, such as `eu-west-3` (Paris). Confirm that it is appropriate for your account and workload.

### Step 2 — Create a Pulumi project

Create a new project using Python:

```bash
mkdir aws-s3-module-01
cd aws-s3-module-01

pulumi new aws-python
```

Follow the prompts to configure the project and stack. If the template prompts for a Region, enter `eu-west-3` or your chosen Region.

The template creates files including:

```text
aws-s3-module-01/
├── __main__.py
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
└── venv/
```

Exact generated files can vary by Pulumi template version.

Set the AWS profile in your shell before deploying.

Linux or macOS:

```bash
export AWS_PROFILE=s3-lab
```

PowerShell:

```powershell
$env:AWS_PROFILE = "s3-lab"
```

For subsequent commands, keep using the same profile and Region.

### Step 3 — Write the S3 infrastructure code

Replace the contents of `__main__.py` with the following:

```python

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

# Supply a globally unique, lowercase bucket name
# through Pulumi stack configuration.
bucket_name = config.require("bucketName")

bucket = aws.s3.BucketV2(
    "s3-fundamentals-bucket",
    bucket=bucket_name,
    tags={
        "Project": "aws-s3-course",
        "Module": "01",
        "ManagedBy": "Pulumi",
    },
)

pulumi.export("bucket_name", bucket.bucket)
pulumi.export("bucket_arn", bucket.arn)
pulumi.export("bucket_region", bucket.region)
```

What the code does:

* `pulumi.Config()` reads configuration for the current stack.

* `config.require("bucketName")` requires a bucket name to be provided.

* `aws.s3.BucketV2` declares the S3 bucket resource.

* The `tags` dictionary adds searchable metadata to the AWS resource.

* `pulumi.export()` publishes values you can retrieve from the stack.

Notice that the resource's logical name, `s3-fundamentals-bucket`, is not necessarily the actual S3 bucket name. The latter comes from configuration.

### Step 4 — Configure a unique bucket name

S3 bucket names must be globally unique within the applicable AWS partition. Choose a lowercase name that is unlikely to be taken, using a suffix you control.

For example:

```bash
pulumi config set bucketName s3-fundamentals-lab-<your-unique-suffix>
```

Replace the placeholder with a real suffix; do not include the angle brackets.

If the bucket name is already taken, choose a different one. The name is public-facing and should not contain confidential data.

### Step 5 — Preview and deploy

First, preview the infrastructure changes:

```bash
pulumi preview
```

Review the proposed changes. You should see a new S3 bucket being created.

Deploy it:

```bash
pulumi up
```

Review the preview shown by Pulumi and confirm the update when prompted.

After a successful deployment, inspect the outputs:

```bash
pulumi stack output bucket_name
pulumi stack output bucket_arn
pulumi stack output bucket_region
```

Save the bucket name in a shell variable for the remaining exercises.

Linux or macOS:

```bash
BUCKET=$(pulumi stack output bucket_name)
```

PowerShell:

```powershell
$BUCKET = pulumi stack output bucket_name
```

You have now created an AWS resource through infrastructure as code rather than through a manual Console workflow.

### 3\. Explore the bucket using the AWS CLI

### Step 6 — Verify the bucket and its Region

Check that the bucket exists:

```bash
aws s3api head-bucket \
  --bucket "$BUCKET"
```

This example uses Bash syntax. In PowerShell, use `$BUCKET` as set above; for commands with multiline continuations, replace `\` with PowerShell's backtick or enter the command on one line.

Inspect the bucket's Region:

```bash
aws s3api get-bucket-location \
  --bucket "$BUCKET"
```

The Region response can represent `us-east-1` as `null`, which is a legacy API convention. For other Regions, you should see a Region identifier.

You can also confirm the Region configured for the bucket in the AWS Console by opening S3 and selecting the bucket.

### Step 7 — Create some sample objects

Create a small local directory structure:

```text
sample-data/
├── hello.txt
├── images/
│   └── photo.txt
└── reports/
    └── january.csv
```

Create the files using Bash:

```bash
mkdir -p sample-data/images sample-data/reports

echo "Hello from Amazon S3!" > sample-data/hello.txt
echo "Sample image placeholder" > sample-data/images/photo.txt
echo "month,total" > sample-data/reports/january.csv
echo "January,120" >> sample-data/reports/january.csv
```

The file named `photo.txt` is intentionally a text placeholder, not an actual image.

Upload the files individually:

```bash
aws s3 cp sample-data/hello.txt "s3://$BUCKET/hello.txt"

aws s3 cp sample-data/images/photo.txt "s3://$BUCKET/images/photo.txt"

aws s3 cp sample-data/reports/january.csv "s3://$BUCKET/reports/january.csv"
```

The resulting object keys are:

```text
hello.txt
images/photo.txt
reports/january.csv
```

Important distinction: The local directory structure is not being mounted in S3. The CLI uploads file contents as objects whose keys happen to contain `/` characters.

### Step 8 — List objects and prefixes

List all objects:

```bash
aws s3 ls "s3://$BUCKET/" --recursive
```

Example output:

```text
2026-10-21 12:00:00        22 hello.txt
2026-10-21 12:00:01        26 images/photo.txt
2026-10-21 12:00:02        33 reports/january.csv
```

The timestamps and sizes above are illustrative.

Now list only the objects under the `images/` prefix:

```bash
aws s3api list-objects-v2 \
  --bucket "$BUCKET" \
  --prefix "images/"
```

Try listing with a delimiter:

```bash
aws s3api list-objects-v2 \
  --bucket "$BUCKET" \
  --delimiter "/"
```

The delimiter groups keys into common prefixes. This is how tools can present a folder-like view even though S3 stores a flat namespace.

### Step 9 — Inspect object metadata

Inspect the object without downloading its content:

```bash
aws s3api head-object \
  --bucket "$BUCKET" \
  --key "hello.txt"
```

Look for fields such as:

* `ContentLength`: size of the object in bytes.

* `ContentType`: media type, if set.

* `LastModified`: last modification time.

* `ETag`: an entity tag whose meaning depends on the upload method and encryption configuration.

* `ServerSideEncryption`: server-side encryption information, when returned.

* `Metadata`: user-defined metadata, if present.

Try explicitly setting a content type when uploading:

```bash
aws s3 cp sample-data/hello.txt "s3://$BUCKET/hello.txt" \
  --content-type "text/plain"
```

Run `head-object` again and observe the content type.

You can also add user-defined metadata:

```bash
aws s3api put-object \
  --bucket "$BUCKET" \
  --key "metadata-demo.txt" \
  --body sample-data/hello.txt \
  --content-type "text/plain" \
  --metadata "course=aws-s3,module=01"
```

Inspect it:

```bash
aws s3api head-object \
  --bucket "$BUCKET" \
  --key "metadata-demo.txt"
```

User-defined metadata is returned under `Metadata`, with keys typically represented in lowercase. Metadata is associated with the object and is not a general-purpose searchable database.

### Step 10 — Download and compare

Download the original object:

```bash
aws s3 cp "s3://$BUCKET/hello.txt" downloaded-hello.txt
```

Compare the downloaded file to the original:

```bash
diff sample-data/hello.txt downloaded-hello.txt
```

If the files match, `diff` produces no output and exits successfully.

On Windows, you can compare files with PowerShell:

```powershell
Compare-Object `
  (Get-Content sample-data/hello.txt) `
  (Get-Content downloaded-hello.txt)
```

You have now completed a round trip: local file → S3 object → local file.

### Step 11 — Understand deletion

Delete a single object:

```bash
aws s3 rm "s3://$BUCKET/metadata-demo.txt"
```

Verify that the object no longer appears in a listing:

```bash
aws s3 ls "s3://$BUCKET/" --recursive
```

Delete is a useful operation to understand early, but it deserves special care in production. In a versioned bucket, a normal delete usually creates a delete marker rather than permanently removing all object versions.

For this initial lab, the bucket has no explicit versioning resource enabled by the Pulumi code, so the basic delete behavior is straightforward.

### 4\. Explore the AWS Console

Open the Amazon S3 console: [AWS S3 Console](https://console.aws.amazon.com/s3/?utm_source=chatgpt.com).

Complete these exercises:

* Locate your bucket and verify its Region.

* Open the bucket and inspect the uploaded objects.

* Open the `images/` prefix and compare the Console's folder-like view with the object keys.

* Select `hello.txt` and inspect its properties and metadata.

* Upload a small test file through the Console and verify that it appears in the CLI listing.

* Delete the test file through the Console and verify the result with the CLI.

The Console and CLI operate on the same underlying S3 resources. Changes made through either interface are reflected in the other.

### 5\. Lab exercises and knowledge check

Use this checklist to confirm that you've completed the module.

Lab completion

0 of 8

Provision a bucket with Pulumi

Confirm the resource appears in pulumi stack output.

Retrieve bucket name, ARN, and Region

Verify all three stack outputs.

Upload at least three objects

Include two different prefixes.

List objects using the CLI

Try recursive listing and prefix filtering.

Inspect metadata

Use head-object and identify the object's size and content type.

Download and compare an object

Confirm the downloaded file matches the original.

Delete an object

Verify its removal using list-objects-v2.

Explore the AWS Console

Inspect the same bucket and objects in the UI.

### Knowledge check

1. What uniquely identifies an object within a bucket?

Its local file path

Its object key

Its content type

2. Is \`reports/2026/january.csv\` necessarily stored inside a physical S3 directory?

Yes, every slash creates a directory

No, the slash is part of the object key

Only when using the AWS Console

3. What does strong consistency mean after a successful object upload?

Every related multi-object operation is atomic

Subsequent reads and listings reflect the successful write

The object is automatically replicated to every Region

4. Which command retrieves object metadata without downloading the object body?

aws s3 ls

aws s3api head-object

aws s3 rm

Reset quiz

### 6\. Troubleshooting guide

| Problem                            | What to check                                                                     |
| ---------------------------------- | --------------------------------------------------------------------------------- |
| Bucket name already exists         | Choose a different globally unique name.                                          |
| AccessDenied                       | Verify your AWS identity, IAM permissions, and any applicable bucket policies.    |
| Wrong Region                       | Check the bucket Region and AWS provider configuration.                           |
| Object not found                   | Check the exact bucket name and case-sensitive object key.                        |
| Pulumi wants to replace a resource | Review pulumi preview carefully before approving changes.                         |
| Bucket deletion fails              | Empty the bucket, including versions and delete markers if versioning is enabled. |

### 7\. Clean up the lab

First remove the objects created during the exercises. For Bash:

```bash
aws s3 rm "s3://$BUCKET/" --recursive
```

This deletes the objects under that bucket, so make sure it contains only lab data.

Then destroy the Pulumi-managed infrastructure:

```bash
pulumi destroy
```

Review the proposed deletion and confirm it. Verify in the AWS Console that the bucket has been removed.

If the bucket is versioned or has retention controls, additional cleanup steps may be necessary. Do not disable retention controls or permanently delete protected data merely to force cleanup.

### Module 1 completion criteria

You have completed this module when you can explain the difference between object, block, and file storage; describe how S3 keys and prefixes work; use the AWS CLI to manage objects; and deploy and inspect a bucket using Pulumi.

Coming next: Module 2 — Managing S3 Infrastructure with Pulumi. You'll build reusable bucket configuration, work with Pulumi stacks and outputs, and learn how to manage infrastructure changes safely across environments.

5
