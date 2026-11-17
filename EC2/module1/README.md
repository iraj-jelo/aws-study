Worked for 1m 2s

### Phase 4 — Compute

### Module 1 — Amazon EC2 and Amazon Machine Images (AMIs)

Level: Beginner to intermediate · Infrastructure as Code: Pulumi with Python · Application: FastAPI

In this module, you'll learn how to run an application on an Amazon EC2 virtual machine, understand how AWS provisions instances, and create repeatable server deployments using Amazon Machine Images (AMIs).

The goal isn't just to launch a server in the AWS Console. You'll learn how to deploy, connect to, secure, troubleshoot, and manage an EC2 instance using the same principles you'll need in production.

### 1\. Learning objectives

By the end of this module, you should be able to:

* Explain EC2 instances, instance types, AMIs, and key pairs.

* Choose an appropriate instance family and size for a workload.

* Understand the relationship between Regions, Availability Zones, subnets, and EC2 instances.

* Explain how instance networking and security groups control connectivity.

* Launch and configure an instance using user data.

* Connect to an instance securely without unnecessarily exposing SSH.

* Provision EC2 infrastructure using Pulumi and Python.

* Understand instance lifecycle operations, pricing, and cleanup.

* Diagnose common instance launch and connectivity failures.

### 2\. How Amazon EC2 works

Amazon EC2 (Elastic Compute Cloud) provides resizable virtual computing capacity in AWS. You can use it to run web applications, APIs, background workers, development environments, and many other workloads.

![Amazon Elastic Compute Cloud | AWS](https://images.openai.com/static-rsc-4/6GPiWPTS8KG0kxa4yXwW6f0UhenU0r0zIadMTdrNg6-L2tgOuPwy_vjXdHiA5u7jEAeFu7U7zak0V_rdFkAHzyvmeZV6kMiZrBQeFB5ub4QODMscHiXcGGoxXewejzGPUnE2ttqwLvPXw5c1PSc98IuDGauwq_rAR4lYxIYQwUGsIk5czB0i2IFVAK9abf6H?purpose=fullsize)

An EC2 instance is created from several configuration choices:

| Component            | Purpose                                                                             |
| -------------------- | ----------------------------------------------------------------------------------- |
| AMI                  | Provides the operating system and initial software image.                           |
| Instance type        | Determines the available CPU, memory, networking, and other capabilities.           |
| VPC and subnet       | Determine the instance's network environment and IP addressing.                     |
| Security group       | Controls permitted inbound and outbound network traffic.                            |
| IAM instance profile | Provides an identity for applications running on the instance; covered in Module 3. |
| EBS volumes          | Provide persistent block storage; covered in Module 2.                              |
| User data            | Runs startup instructions when the instance launches.                               |

Think of an AMI as a starting template, an instance type as the hardware profile, and an EC2 instance as the running virtual machine.

### The provisioning sequence

1\. Select an AMI

Operating system and initial software

2\. Select an instance type

CPU, memory, and network capacity

3\. Configure networking and access

Subnet, security group, and identity

4\. Launch the instance

AWS provisions the virtual machine

5\. Configure and run the application

Bootstrap, validate, monitor, and troubleshoot

### 3\. Understanding EC2 instance types

An instance type defines the resources available to your virtual machine. AWS groups instance types into families designed for different workloads.

| Family                       | Primary use                                | Example workload                            |
| ---------------------------- | ------------------------------------------ | ------------------------------------------- |
| General purpose — t, m       | Balanced compute and memory                | Small APIs, web servers, development        |
| Compute optimized — c        | Higher CPU capacity relative to memory     | CPU-intensive processing                    |
| Memory optimized — r, x      | Larger memory capacity                     | In-memory caches and memory-heavy databases |
| Storage optimized — i, d     | High local storage performance or capacity | Specialized data processing                 |
| Accelerated computing — g, p | GPUs and other accelerators                | Machine learning and graphics               |

Instance families and individual offerings vary by Region and generation. Always check current availability and pricing before choosing one.

### Example: reading an instance type

Consider `t3.micro`.

* `t`: belongs to a burstable general-purpose family.

* `3`: indicates the generation.

* `micro`: indicates the size within that family.

A burstable instance uses CPU credits under the T-series performance model. It can be economical for low-average-CPU workloads, but sustained CPU demand and the selected credit mode can affect performance and cost.

For a small learning application, a currently available, low-cost instance may be sufficient. Check eligibility for AWS Free Tier benefits in your own account; don't assume every instance type or usage pattern is free.

### How to choose an instance

Ask four questions:

* How much memory does the application require?

* Is its workload CPU-intensive or mostly idle?

* How much network throughput does it need?

* What are the cost and availability constraints?

Start small, measure actual utilization, and resize when evidence supports it.

### 4\. Amazon Machine Images (AMIs)

An Amazon Machine Image is a template that contains the information required to launch an EC2 instance, including its operating system and block-device mappings. An AMI can be provided by AWS, shared by another account, published by a third party, or obtained from AWS Marketplace.

### 4.1 Common AMI choices

* Amazon Linux 2023: A good starting point for learning AWS-native server administration.

* Ubuntu Server: Common for Python applications, web servers, and general Linux administration.

* Windows Server: Useful for Windows-based applications and Microsoft workloads.

* Custom AMIs: Images you build with your preferred packages, configuration, and security hardening.

### 4.2 Important AMI properties

An AMI is Region-specific, and compatibility depends on characteristics such as processor architecture, virtualization type, and root-volume configuration. You can copy an AMI to another Region when needed.

When choosing an AMI, verify:

* The publisher or owner is trustworthy.

* The image is compatible with the instance architecture.

* The operating system is supported and receives security updates.

* The image is available in your target Region.

* The image doesn't contain unnecessary software or embedded credentials.

### 4.3 Why avoid hard-coded AMI IDs?

AMI IDs differ across Regions and can change as images are updated. For repeatable deployments, you can resolve an AWS-managed public Systems Manager parameter to find the current Amazon Linux 2023 image.

For example:

```python
ami = "resolve:ssm:/aws/service/ami-amazon-linux-latest/al2023-ami-kernel-default-x86_64"
```

This is a supported approach in the Pulumi AWS provider.

A production deployment should also consider image pinning and controlled upgrades. Automatically resolving the latest image makes updates easier, but it can change what a future deployment launches.

### 5\. Instance lifecycle

EC2 instances have distinct lifecycle states. Understanding them helps you avoid unexpected downtime and costs.

| Action    | What it means                                                                                        |
| --------- | ---------------------------------------------------------------------------------------------------- |
| Launch    | Creates a new instance.                                                                              |
| Reboot    | Restarts the operating system on the instance.                                                       |
| Stop      | Shuts down an EBS-backed instance while retaining the instance and its EBS volumes.                  |
| Start     | Starts a previously stopped instance, subject to capacity and configuration.                         |
| Terminate | Permanently ends the instance; associated resources may also be deleted according to their settings. |

Important distinctions:

* An instance's public IPv4 address can change after a stop and start unless you use an Elastic IP or another addressing arrangement that preserves it.

* EBS volumes typically persist after stopping an instance.

* Terminating an instance may delete its root EBS volume if its delete-on-termination setting is enabled.

* Instance-store data is ephemeral and should not be treated as durable storage.

* Stopping an instance generally stops its instance compute charges, but retained storage and certain associated resources can still incur charges.

For detailed storage behavior, we'll go deeper in Module 2.

### 6\. Secure ways to connect to EC2

There are several ways to administer a Linux instance.

SSH

Uses a key pair or another supported SSH authentication method. Traditional SSH access requires a network path and an appropriately configured security group.

EC2 Instance Connect

Provides supported ways to establish SSH connections, including browser-based access where configured. It still requires the appropriate connectivity and permissions.

AWS Systems Manager Session Manager

Allows interactive administration without opening inbound SSH ports when the instance, IAM permissions, SSM Agent, and required service connectivity are configured.

Course recommendation: Prefer Session Manager for the secure administration lab. In the initial Pulumi exercise below, we'll expose only HTTP for testing and won't open port 22.

### 7\. Hands-on lab — Deploy a web server with Pulumi

### Lab objectives

* Provision an EC2 instance using Pulumi and Python.

* Select an Amazon Linux 2023 AMI dynamically through AWS's public SSM parameter.

* Create a security group that permits HTTP traffic.

* Run a web server automatically using EC2 user data.

* Verify the server through its public endpoint.

* Destroy the infrastructure when finished.

    Estimated time: 30–45 minutes

### 7.1 Prerequisites

Install and configure:

* Python 3.

* The Pulumi CLI.

* The Pulumi AWS provider package.

* AWS CLI v2 with credentials for an account where you are authorized to create EC2 resources.

Official references: and .

Check your AWS identity and configured Region:

```bash
aws sts get-caller-identity
aws configure get region
pulumi version
python --version
```

Use a Region you intend to work in. Check its EC2 pricing and your account's service quotas before deploying.

### 7.2 Create the Pulumi project

```bash
mkdir aws-compute-module-1
cd aws-compute-module-1

pulumi new aws-python
```

Follow the prompts to create the project. If the template asks for a Region, select your intended AWS Region.

Install or verify the Python dependencies through the project's virtual environment:

```bash
python -m pip install pulumi pulumi-aws
```

The AWS credentials configured for the Pulumi deployment must have permission to create and manage the EC2 instance and security group, as well as query the AMI and VPC. Use appropriately scoped credentials rather than permanent root credentials.

### 7.3 Understand the architecture

The lab uses the account's default VPC and its default subnet selection. This keeps the first compute exercise focused on EC2 rather than rebuilding networking from scratch.

Internet client

HTTP request to TCP port 80

Default VPC and subnet

Internet connectivity depends on existing VPC routing

EC2 instance — Amazon Linux 2023

Public IPv4 · Python HTTP server · User data

Security group

Inbound TCP 80 only; no inbound SSH rule

This architecture is appropriate as a learning exercise, not a finished production design. The server is internet-accessible over unencrypted HTTP, and the default VPC may not match your security requirements. Later modules will move toward private application subnets, HTTPS through an ALB, and controlled administration.

### 7.4 Implement the infrastructure

Replace the contents of `__main__.py` with:

```python
import pulumi
import pulumi_aws as aws

# Use the account's default VPC for this introductory lab.
vpc = aws.ec2.get_vpc(default=True)

# Resolve the current Amazon Linux 2023 x86_64 AMI.
ami = (
    "resolve:ssm:/aws/service/ami-amazon-linux-latest/"
    "al2023-ami-kernel-default-x86_64"
)

# Permit HTTP requests to the demo web server.
web_sg = aws.ec2.SecurityGroup(
    "compute-module-1-web-sg",
    description="Allow HTTP for the EC2 learning lab",
    vpc_id=vpc.id,
    ingress=[
        {
            "description": "HTTP",
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
    egress=[
        {
            "description": "Outbound IPv4",
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
    tags={
        "Name": "compute-module-1-web-sg",
        "Purpose": "learning",
    },
)

# EC2 user data runs during initial instance boot.
user_data = """#!/bin/bash
set -euxo pipefail

mkdir -p /opt/compute-demo

cat > /opt/compute-demo/index.html <<'HTML'
<!doctype html>
<html>
  <head><title>EC2 Compute Lab</title></head>
  <body>
    <h1>Hello from Amazon EC2!</h1>
    <p>Provisioned using Pulumi and Python.</p>
  </body>
</html>
HTML

cat > /etc/systemd/system/compute-demo.service <<'UNIT'
[Unit]
Description=EC2 Compute Learning Web Server
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/compute-demo
ExecStart=/usr/bin/python3 -m http.server 80 --bind 0.0.0.0 --directory /opt/compute-demo
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now compute-demo.service
"""

server = aws.ec2.Instance(
    "compute-module-1-web",
    ami=ami,
    instance_type="t3.micro",
    vpc_security_group_ids=[web_sg.id],
    associate_public_ip_address=True,
    user_data=user_data,
    user_data_replace_on_change=True,
    root_block_device={
        "encrypted": True,
        "volume_size": 8,
        "volume_type": "gp3",
        "delete_on_termination": True,
    },
    metadata_options={
        "http_endpoint": "enabled",
        "http_tokens": "required",
    },
    tags={
        "Name": "compute-module-1-web",
        "Purpose": "learning",
    },
)

pulumi.export("instance_id", server.id)
pulumi.export("public_ip", server.public_ip)
pulumi.export("public_dns", server.public_dns)
pulumi.export("website_url", pulumi.Output.concat(
    "http://", server.public_dns
))
```

What this code teaches you:

* `aws.ec2.get_vpc()` looks up existing network infrastructure.

* `aws.ec2.SecurityGroup()` declares the network access policy.

* `aws.ec2.Instance()` declares the virtual machine and its configuration.

* The SSM parameter lets AWS resolve the current Amazon Linux 2023 AMI.

* `user_data` bootstraps the web server on first boot.

* `metadata_options` requires IMDSv2 tokens for instance metadata access.

* `root_block_device` explicitly configures an encrypted, delete-on-termination root volume.

* `pulumi.export()` exposes useful values after deployment.

The code deliberately doesn't configure an SSH key or open port 22. Also, `t3.micro` availability and cost depend on the Region and account; change the instance type if needed.

### 7.5 Preview and deploy

First, inspect the proposed infrastructure changes:

```bash
pulumi preview
```

Review the planned resources before applying them. You should see a security group and an EC2 instance.

Then deploy:

```bash
pulumi up
```

Pulumi will show the proposed changes and ask for confirmation. Approve only after reviewing the plan.

When deployment finishes, inspect the outputs:

```bash
pulumi stack output instance_id
pulumi stack output public_ip
pulumi stack output website_url
```

Open the `website_url` in your browser. You should see:

> Hello from Amazon EC2!

The instance may need additional time to finish bootstrapping after AWS reports that it is running. An EC2 instance in the `running` state does not guarantee that its application is ready.

### 7.6 Verify the application

Test the endpoint from a terminal:

```bash
curl "$(pulumi stack output website_url)"
```

You should receive the HTML page generated by the startup script.

You can also inspect the instance in the EC2 Console and verify:

* Its state is `Running`.

* Its AMI and instance type match your configuration.

* Its security group allows inbound TCP port 80.

* Its root volume is encrypted.

* Its metadata configuration requires IMDSv2.

### 7.7 Troubleshooting

| Symptom                               | What to investigate                                                                           |
| ------------------------------------- | --------------------------------------------------------------------------------------------- |
| Instance fails to launch              | Instance-type availability, quotas, permissions, AMI compatibility, and subnet configuration. |
| Website times out                     | Public IP assignment, internet gateway, route table, security group, and network ACLs.        |
| Connection refused                    | Whether the web server started and is listening on port 80.                                   |
| Incorrect or missing page             | The systemd service status, document directory, and user-data execution.                      |
| AMI resolution fails                  | Region, parameter name, provider configuration, and access to the referenced AMI.             |
| Pulumi reports unexpected replacement | Changes to immutable instance properties or user_data_replace_on_change.                      |

If you later configure Session Manager, useful diagnostic commands on the instance include:

```bash
sudo systemctl status compute-demo.service
sudo journalctl -u compute-demo.service --no-pager
sudo cat /var/log/cloud-init-output.log
```

The final command displays cloud-init output, which is especially useful for diagnosing user-data failures.

### 8\. AMI lifecycle and repeatable deployments

The lab uses a public AWS-managed AMI. In production, you may need a standardized image with a controlled operating system version, approved packages, monitoring agents, and security hardening.

A typical image workflow is:

Base AMI

AWS-managed operating system image

Image build and hardening

Patches, approved software, security settings

Test and validate

Boot, application checks, security checks

Approved AMI

Versioned image used by repeatable deployments

A custom AMI can be created from a configured instance or through an automated image-building pipeline. AMIs can also be copied between Regions and shared with other AWS accounts, subject to permissions and encryption constraints.

For production workloads, consider a tool such as EC2 Image Builder to automate image creation, patching, and validation. Keep application releases and infrastructure configuration versioned, and avoid baking secrets into images.

### 9\. Cost and security review

Before moving on, review these operational principles.

Cost controls

* Choose an instance type appropriate for the workload.

* Stop the instance when you aren't using it, while remembering that retained resources may still incur charges.

* Check the costs of public IPv4 addresses, EBS volumes, snapshots, and data transfer.

* Use AWS Budgets and Cost Explorer to monitor spending.

Security controls

* Do not expose SSH to the entire internet.

* Prefer Session Manager or tightly restricted administrative access.

* Require IMDSv2 where compatible with the workload.

* Encrypt EBS volumes and restrict access to snapshots and AMIs.

* Avoid storing AWS credentials in user data, source code, or AMIs.

* Use a private subnet and an HTTPS-enabled load balancer for a more realistic production architecture.

The lab's HTTP endpoint is intentionally simple. Don't use it to host sensitive data or production traffic.

### 10\. Clean up the lab

When you've finished testing, remove the resources managed by this Pulumi stack:

```bash
pulumi destroy
```

Review the proposed deletions and confirm them. Then verify in the EC2 Console that the instance and security group have been removed.

If you want to keep the Pulumi project for future exercises, leave the project files in place. You can redeploy the stack later with `pulumi up`.

Remember that manually created snapshots, Elastic IPs, or other resources outside the stack may not be deleted automatically.

### 11\. Knowledge check

Try answering these questions before reading the explanations.

1. What is the primary purpose of an AMI?

To assign a public IP address

To provide the template used to launch an instance

To control inbound network traffic

To monitor CPU utilization

2. What happens to a typical EBS-backed instance when it is stopped?

The instance is automatically terminated

All EBS volumes are deleted

The instance is retained and can generally be restarted

Its AMI is deleted

3. Which resource controls permitted inbound HTTP traffic?

AMI

Security group

Instance type

User data

4. Why is an AMI ID often unsuitable as a universal hard-coded value?

AMI IDs are always secret

AMI IDs are specific to a Region and image

AMI IDs determine IAM permissions

AMI IDs change every time an instance reboots

5. What is the purpose of EC2 user data in this lab?

To define IAM users

To replace the VPC route table

To execute startup instructions when the instance launches

To create a custom AMI automatically

Check answers

### 12\. Further reading

Use the official documentation when exploring the concepts in more depth:

* Amazon EC2 AMIs — .

* Pulumi AWS EC2 Instance — .

* AWS Systems Manager Session Manager — .

### Module 1 completion checklist

Your progress

### 0 of 6

Explain the difference between an EC2 instance and an AMI.

Compare the major EC2 instance families.

Deploy the instance using Pulumi and Python.

Verify the HTTP endpoint and inspect startup logs.

Explain the security group and IMDSv2 settings.

Destroy the lab and confirm cleanup.

Next: Module 2 — Amazon EBS and Instance Storage. You'll explore persistent block storage, volume performance, encryption, snapshots, recovery, and how storage behaves when an EC2 instance stops or terminates.
