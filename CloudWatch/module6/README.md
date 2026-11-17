### Module 6 — AWS Systems Manager and Fleet Operations

AWS Operations and Observability · Module 6 of 8

### 1\. Learning objectives

By the end of this module, you will understand how to manage EC2 instances centrally using AWS Systems Manager (SSM), securely access servers without opening SSH or RDP ports, execute operational commands, automate maintenance, and investigate fleet-level problems.

You will learn how to:

* Explain the Systems Manager architecture and managed-node registration process.

* Configure IAM instance profiles and least-privilege permissions.

* Use Session Manager for secure interactive access.

* Execute commands remotely using Run Command.

* Automate operational procedures with Automation runbooks.

* Manage patching, compliance, and desired system state.

* Store configuration and sensitive values using Parameter Store appropriately.

* Collect inventory and manage fleets using Fleet Manager.

* Audit operational actions through CloudTrail and Systems Manager execution history.

* Provision the infrastructure with Pulumi and Python.

### 2\. Systems Manager architecture

AWS Systems Manager is a collection of AWS capabilities for operating and managing resources across AWS, hybrid environments, and supported on-premises servers. It helps centralize access, configuration, automation, patching, inventory, and operational troubleshooting.

![AWS Systems Manager (SSM) | @abiydv](https://images.openai.com/static-rsc-4/0VKlh3T9pGFOccxqK4cH8-vrb0YVSL4av_752q4AjL2s7jO5fAO4KRIxVwI8KFjmLMR767eM5C4h92C-5YgO-MpcngZeT0oMUabTE5fiJ3HGEFKyFGGFeWdqHIjapc3USyrm4hVmIBSooldsKh8kNrtRv7uG2Wc36IFuF_ZYT47HPe7-MwgQM9ua_AiRpT3P?purpose=fullsize)

The basic architecture consists of four components.

1\. Managed nodes

EC2 instances, supported hybrid servers, or other supported managed machines. The SSM Agent runs on each node and communicates with Systems Manager.

2\. IAM permissions

An EC2 instance profile supplies the instance with temporary AWS credentials. The permissions allow the agent to register and communicate with Systems Manager.

3\. Systems Manager service

AWS receives management requests and coordinates capabilities such as Session Manager, Run Command, Inventory, Patch Manager, and Automation.

4\. Operational visibility

Systems Manager provides execution and compliance information, while CloudTrail records supported API activity. CloudWatch and Amazon S3 can be used for additional logs and monitoring.

### How the management flow works

* An EC2 instance starts with a suitable IAM instance profile.

* The SSM Agent obtains temporary credentials from the instance's IAM role.

* The agent communicates with the Systems Manager endpoints over HTTPS.

* The instance becomes available as a managed node when registration and connectivity prerequisites are satisfied.

* An authorized operator starts a session, executes a command, or launches an automation.

* Execution status and output become available through the relevant Systems Manager interface and configured logging destinations.

The agent typically initiates outbound connections, so inbound SSH port 22 and RDP port 3389 are not required for Session Manager. You still need suitable network connectivity, service permissions, and operator authorization.

### 3\. Managed-node prerequisites

An instance does not automatically become manageable just because it is running in EC2. Several conditions must be satisfied.

| Requirement                | Purpose                                                                         |
| -------------------------- | ------------------------------------------------------------------------------- |
| SSM Agent                  | Runs on the node and handles Systems Manager communication.                     |
| IAM instance profile       | Provides the node with AWS credentials and permissions.                         |
| Network connectivity       | Allows HTTPS communication with required AWS endpoints.                         |
| Supported operating system | Must be supported by the relevant Systems Manager capability and agent version. |
| Operator IAM permissions   | Allows authorized users to start sessions, send commands, or run automations.   |
| Service configuration      | Logging, encryption, and optional features must be configured as required.      |

### IAM instance profiles

For EC2 instances, the standard starting point is an IAM role with the AWS-managed policy `AmazonSSMManagedInstanceCore`, attached through an instance profile.

This policy supplies common permissions needed by the SSM Agent to communicate with Systems Manager. Additional permissions may be required for specific operations, such as reading parameters, uploading logs to S3, or publishing application metrics.

Do not confuse these two permission boundaries:

* Instance role: What the managed machine itself can do.

* Operator role: What the person or automation initiating the management operation can do.

A node might be correctly registered while an operator still lacks permission to open a session. Conversely, an operator might be authorized while the node is unavailable because its agent or network is misconfigured.

### Network connectivity

For instances in a public subnet, outbound connectivity can use an appropriate internet gateway and public addressing, subject to routing and security configuration.

For instances in private subnets, common options include:

* A NAT gateway or another suitable outbound path.

* VPC interface endpoints for the required Systems Manager services, typically including `ssm` and `ssmmessages`; some configurations or Regions may also require `ec2messages`.

Use the endpoint requirements for your Region and current agent configuration rather than assuming every environment needs exactly the same endpoint set. Interface endpoints also require appropriate security-group rules and DNS configuration.

Private connectivity is especially useful when servers should not have general internet access.

### 4\. Session Manager: secure interactive access

Session Manager provides interactive shell access to Linux and Windows managed nodes through the AWS console or CLI, without requiring SSH keys, bastion hosts, or inbound management ports. AWS Systems Manager +1

### Traditional access versus Session Manager

| Traditional SSH/RDP                                     | Session Manager                                             |
| ------------------------------------------------------- | ----------------------------------------------------------- |
| Requires SSH keys or other remote-access credentials    | Uses IAM authorization                                      |
| Usually requires inbound management access              | Uses agent-initiated communication                          |
| Often needs a bastion host for private instances        | Can access supported private instances without a bastion    |
| Access auditing requires additional configuration       | Integrates with CloudTrail and configurable session logging |
| Credentials and network access need separate management | Access can be controlled centrally through IAM              |

Session Manager is not a reason to grant unrestricted administrative access. Operators should have narrowly scoped permissions, and session logging should be configured according to operational and compliance requirements.

### Starting a session

First, configure the AWS CLI and the Session Manager plugin on your workstation if using the CLI.

```bash
aws sts get-caller-identity

aws ssm describe-instance-information \
  --query 'InstanceInformationList[*].[InstanceId,PingStatus,PlatformName]' \
  --output table
```

The first command verifies the caller identity. The second lists Systems Manager managed-node information available to your current account and Region.

Start an interactive session:

```bash
aws ssm start-session \
  --target i-0123456789abcdef0
```

Replace the example instance ID with a real managed-node ID.

Inside a Linux session, useful diagnostics include:

```bash
hostname
uptime
df -h
free -m
ps aux --sort=-%cpu | head
```

On Windows, a PowerShell session can use commands such as:

```powershell
hostname
Get-Service
Get-Volume
Get-Process | Sort-Object CPU -Descending |
    Select-Object -First 10
```

These commands provide a quick picture of system identity, uptime, disk capacity, memory, services, and processes.

### Session logging and auditing

Session Manager can send session data to CloudWatch Logs or Amazon S3 when the relevant preferences and permissions are configured. Encryption options include AWS KMS for supported logging configurations. Validate the logging behavior for the selected session type and configuration; not every access record automatically contains a complete transcript.

CloudTrail records supported API actions, such as session initiation, but an API event is not the same thing as a full record of everything typed inside the shell. AWS Systems Manager +1

### 5\. Run Command: execute operations remotely

Run Command executes commands or predefined Systems Manager documents on one or more managed nodes without requiring an interactive session.

Typical use cases include:

* Collecting disk, memory, process, and service information.

* Restarting a service after verifying its health.

* Deploying configuration files or installing approved software.

* Running security and compliance checks.

* Executing the same diagnostic across an entire fleet.

### Example: run a Linux diagnostic

```bash
aws ssm send-command \
  --document-name "AWS-RunShellScript" \
  --targets "Key=tag:Environment,Values=dev" \
  --parameters 'commands=["hostname","uptime","df -h"]' \
  --comment "Collect basic system diagnostics"
```

This command targets managed nodes tagged `Environment=dev`. It will not run successfully unless the target instances are registered, online, and authorized for the operation.

Retrieve the command ID from the response, then inspect the result:

```bash
aws ssm list-command-invocations \
  --command-id COMMAND_ID \
  --details
```

Replace `COMMAND_ID` with the actual ID returned by `send-command`.

For a Windows fleet, a compatible document such as `AWS-RunPowerShellScript` can execute PowerShell commands.

### Operational considerations

* Prefer tags over manually maintaining long instance ID lists.

* Set appropriate concurrency and error thresholds for large fleets.

* Inspect command output and exit status instead of assuming success.

* Avoid placing credentials or secrets directly in command parameters.

* Test potentially disruptive commands on a small group first.

Run Command is especially useful for repeatable operational work across many servers. AWS Systems Manager +1

### 6\. Automation: operational runbooks

Systems Manager Automation executes defined workflows using Systems Manager documents. A runbook can combine several steps, use outputs from earlier steps, and include branching or error handling where supported.

Examples include:

* Stop an instance before a controlled maintenance operation.

* Verify an instance's configuration.

* Create a backup before making a change.

* Restart a service and verify recovery.

* Notify an operations team if a step fails.

A simplified operational sequence might be:

1\. Identify targets

Select instances using tags or explicit resource IDs

2\. Validate prerequisites

Check status, permissions, and operational conditions

3\. Execute controlled change

Run an approved action or maintenance step

4\. Verify and report

Check results, record execution status, and notify operators

Automation runbooks may invoke other AWS services, so the permissions of the initiating operator and the execution role must be considered separately. Avoid using broad administrative permissions merely to make a runbook work.

### 7\. Patch Manager and patch compliance

Patch Manager helps automate operating-system patching and report patch compliance for supported managed nodes. It supports scanning for missing patches and installing applicable patches. For organization-wide patch policies, AWS recommends the Quick Setup patch-policy approach. AWS Systems Manager +1

### The patch-management lifecycle

* Define a patch baseline. Specify which patches are approved under the chosen rules.

* Scan nodes. Compare installed patches with the applicable baseline.

* Review compliance. Identify missing patches and noncompliant machines.

* Plan installation. Select the maintenance window and target scope.

* Install and validate. Apply updates and check service health.

* Review results. Examine command status and the latest compliance report.

A patch scan is not the same as patch installation. Compliance results are based on the latest successful relevant operation, so check their timestamps before concluding that a node is currently compliant.

### Maintenance windows

Maintenance windows allow supported operational tasks to run during scheduled periods. This is important when updates could restart services or temporarily disrupt workloads.

For production environments, plan around:

* Application redundancy and load-balancer health.

* Backup and recovery requirements.

* Maintenance-window duration.

* Installation concurrency and failure thresholds.

* Post-patch verification and rollback or recovery procedures.

Patch Manager does not replace application-level compatibility testing, and it does not perform major operating-system version upgrades. AWS Systems Manager +1

### 8\. State Manager: maintain a desired state

State Manager uses associations to apply and maintain a defined configuration on managed nodes.

For example, you might want all development instances to have:

* A required diagnostic package installed.

* A particular configuration file present.

* A monitoring agent configured.

* A recurring inventory collection schedule.

An association connects a Systems Manager document with target nodes and execution settings. Depending on the document and configuration, it can run on a schedule or when an association is applied.

The key distinction is:

* Run Command: Execute an operation when requested.

* State Manager: Maintain a desired configuration through associations.

* Automation: Orchestrate a multi-step operational workflow.

* Patch Manager: Manage patch scanning, installation, and compliance.

These capabilities overlap in some workflows but solve different operational problems. AWS Systems Manager +1

### 9\. Parameter Store: configuration and sensitive values

AWS Systems Manager Parameter Store provides centralized storage for configuration values and parameters. Parameters can be plain strings, string lists, or encrypted `SecureString` values.

Examples include:

* Application environment names.

* API endpoint URLs.

* Feature flags.

* Database connection configuration.

* Sensitive values that need encryption at rest.

Example commands:

```bash
aws ssm put-parameter \
  --name "/demo/dev/app/log-level" \
  --type String \
  --value "INFO"
```

Retrieve the parameter:

```bash
aws ssm get-parameter \
  --name "/demo/dev/app/log-level"
```

For an encrypted parameter:

```bash
aws ssm get-parameter \
  --name "/demo/dev/app/api-token" \
  --with-decryption
```

The encrypted example assumes the parameter already exists and that the caller has the necessary permissions.

For sensitive values, use `SecureString`, restrict read access, and apply suitable KMS permissions. Avoid passing secrets through shell history, source control, or unprotected deployment configuration.

Parameter Store can be useful for many operational parameters, but it is not a universal replacement for AWS Secrets Manager. Secrets requiring managed rotation or other specialized lifecycle features may be better suited to Secrets Manager.

### 10\. Inventory, Fleet Manager, and maintenance workflows

Systems Manager Inventory collects metadata about managed nodes, such as supported operating-system details, installed applications, and other inventory information.

Fleet Manager provides a centralized interface for viewing and managing managed nodes. Maintenance Windows help schedule supported operational tasks, including selected patching and Run Command operations.

These capabilities help answer practical questions:

* Which instances are running a particular operating system?

* Which nodes have a required application installed?

* Which machines are missing updates?

* Which nodes have stopped reporting to Systems Manager?

* Which instances should be included in a maintenance operation?

For larger fleets, use consistent resource tags and clear naming conventions. Tags such as `Environment`, `Application`, `Owner`, and `MaintenanceGroup` make targeting and reporting easier.

### 11\. Pulumi foundations for the lab

The lab will provision two EC2 instances with a shared Systems Manager instance role. To keep the example focused, it uses an existing VPC and subnet rather than rebuilding the networking layer from scratch.

The example uses Python and Pulumi's AWS provider. The official Pulumi documentation describes the relevant IAM instance-profile and EC2 resources. Pulumi Tutorials +2

### Project structure

```text
systems-manager-lab/
├── Pulumi.yaml
├── Pulumi.dev.yaml
├── requirements.txt
└── __main__.py
```

Create the project:

```bash
mkdir systems-manager-lab
cd systems-manager-lab

pulumi new aws-python
```

Use the interactive prompts to create a Python project, or initialize the project using your preferred existing template.

Install the dependencies:

```bash
uv add pulumi pulumi-aws
```

If you use a standard Python virtual environment instead of `uv`, install the same packages through your environment's package manager.

Configure the AWS Region and stack:

```bash
pulumi stack init dev
pulumi config set aws:region us-east-1
aws sts get-caller-identity
```

The example uses `us-east-1`; select another supported Region if needed.

You will also need the IDs of an existing VPC, subnet, and a suitable AMI. For a straightforward first deployment, choose an Amazon Linux AMI supported by Systems Manager, a subnet with suitable outbound connectivity, and an instance type available in your account.

### 12\. Lab 6 — Manage and Troubleshoot an EC2 Fleet

### Lab objectives

* Provision two EC2 instances using Pulumi.

* Attach an IAM instance profile with Systems Manager core permissions.

* Register both instances as managed nodes.

* Run remote diagnostic commands.

* Start a Session Manager session.

* Perform a controlled patch-compliance scan.

* Review execution history and CloudTrail activity.

### Lab architecture

Operator workstation

AWS CLI · Session Manager plugin · Pulumi CLI

AWS Systems Manager

Session Manager · Run Command · Patch Manager

Existing VPC and subnet

EC2 A

SSM Agent

EC2 B

SSM Agent

Outbound HTTPS connectivity · IAM instance profile · No inbound SSH rule required

### Step 1 — Configure Pulumi inputs

Store the network IDs in stack configuration rather than hardcoding them in the program.

```bash
pulumi config set vpcId vpc-0123456789abcdef0
pulumi config set subnetId subnet-0123456789abcdef0
pulumi config set amiId ami-0123456789abcdef0
```

Replace all three sample IDs with real values from your selected Region.

Create `Pulumi.yaml` if you need a minimal project definition:

```yaml
name: systems-manager-lab
runtime:
  name: python
description: EC2 fleet managed with AWS Systems Manager
```

Create `requirements.txt`:

```text
pulumi
pulumi-aws
```

### Step 2 — Define the IAM role and EC2 fleet

Place the following in `__main__.py`.

```python
import json

import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
subnet_id = config.require("subnetId")
ami_id = config.require("amiId")

# Permit EC2 to assume this role.
ssm_role = aws.iam.Role(
    "fleet-ssm-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Principal": {"Service": "ec2.amazonaws.com"},
            "Action": "sts:AssumeRole",
        }],
    }),
)

# Standard Systems Manager core permissions.
ssm_policy = aws.iam.RolePolicyAttachment(
    "fleet-ssm-core-policy",
    role=ssm_role.name,
    policy_arn=(
        "arn:aws:iam::aws:policy/"
        "AmazonSSMManagedInstanceCore"
    ),
)

instance_profile = aws.iam.InstanceProfile(
    "fleet-ssm-profile",
    role=ssm_role.name,
)

# No inbound SSH rule is created.
# Instances need outbound connectivity to the required
# Systems Manager endpoints.
security_group = aws.ec2.SecurityGroup(
    "fleet-ssm-sg",
    vpc_id=vpc_id,
    description="Outbound-only security group for SSM lab",
    ingress=[],
    egress=[{
        "protocol": "tcp",
        "from_port": 443,
        "to_port": 443,
        "cidr_blocks": ["0.0.0.0/0"],
        "description": "HTTPS egress",
    }],
    tags={"Purpose": "systems-manager-lab"},
)

instances = []

for index in range(2):
    instance = aws.ec2.Instance(
        f"fleet-node-{index + 1}",
        ami=ami_id,
        instance_type="t3.micro",
        subnet_id=subnet_id,
        vpc_security_group_ids=[security_group.id],
        iam_instance_profile=instance_profile.name,
        associate_public_ip_address=False,
        metadata_options={
            "http_tokens": "required",
            "http_endpoint": "enabled",
        },
        root_block_device={
            "encrypted": True,
            "volume_size": 8,
            "volume_type": "gp3",
        },
        tags={
            "Name": f"fleet-node-{index + 1}",
            "Environment": "dev",
            "Application": "ssm-lab",
            "ManagedBy": "Pulumi",
        },
        opts=pulumi.ResourceOptions(
            depends_on=[ssm_policy],
        ),
    )

    instances.append(instance)

pulumi.export(
    "instanceIds",
    [instance.id for instance in instances],
)

pulumi.export("securityGroupId", security_group.id)
pulumi.export("instanceProfileName", instance_profile.name)
```

Important design details:

* The role is attached to both instances through an instance profile.

* IMDSv2 is required to protect instance metadata access.

* Root EBS volumes are encrypted.

* There is no inbound SSH or RDP rule.

* HTTPS egress is allowed, but unrestricted outbound access is broader than a production least-privilege design. For production, consider restricting egress to appropriate VPC endpoints and other explicitly required destinations.

Networking requirement: This configuration does not create a NAT gateway or VPC endpoints. Because public IP assignment is disabled, the selected subnet must already provide a working private path to the required Systems Manager endpoints. A private subnet without that path will not register successfully.

The Amazon Linux AMI must also include a compatible SSM Agent, or you must install and start the agent through an appropriate image-building or bootstrap process.

### Step 3 — Preview and deploy

Preview the infrastructure changes:

```bash
pulumi preview
```

Review the planned IAM, security-group, and EC2 resources. Then deploy:

```bash
pulumi up
```

Confirm the changes when prompted.

Retrieve the resulting instance IDs:

```bash
pulumi stack output instanceIds
```

The instances may take a few minutes to appear as online managed nodes. Provisioning success does not guarantee Systems Manager registration; registration depends on the agent, permissions, network connectivity, and supported configuration.

### Step 4 — Verify managed-node registration

Check the registered instances in the selected Region:

```bash
aws ssm describe-instance-information \
  --filters "Key=tag:Environment,Values=dev" \
  --query 'InstanceInformationList[*].{
    Instance:InstanceId,
    Ping:PingStatus,
    Platform:PlatformName,
    Agent:AgentVersion
  }' \
  --output table
```

If your CLI query does not return the expected nodes, first verify the EC2 instance IDs and Region. The Systems Manager API's inventory filters may not expose EC2 resource tags in every query context; you can instead query EC2 by tag and check each instance's registration directly.

For an individual node:

```bash
aws ssm describe-instance-information \
  --filters "Key=InstanceIds,Values=YOUR_INSTANCE_ID" \
  --output table
```

Expected result: each successfully registered instance should report `Online` for its ping status.

If an instance is missing or offline, investigate:

* Is the SSM Agent installed and running?

* Is the correct instance profile attached?

* Does the role have the required Systems Manager permissions?

* Can the instance resolve and reach the required endpoints over HTTPS?

* Are VPC endpoint security groups, DNS, and routing configured correctly?

* Is the CLI operating in the correct AWS account and Region?

### Step 5 — Run fleet-wide diagnostics

Execute a diagnostic command against both instances using their shared tag:

```bash
aws ssm send-command \
  --targets "Key=tag:Application,Values=ssm-lab" \
  --document-name "AWS-RunShellScript" \
  --parameters 'commands=["hostname","uptime","df -h","free -m"]' \
  --comment "Module 6 fleet diagnostics" \
  --query 'Command.CommandId' \
  --output text
```

Copy the returned command ID and retrieve the execution details:

```bash
aws ssm list-command-invocations \
  --command-id YOUR_COMMAND_ID \
  --details \
  --output table
```

Inspect the output and status for each instance. If a command fails, distinguish between a delivery failure, a script execution failure, and a command that succeeds but reports an unhealthy system.

### Step 6 — Open a Session Manager session

Select one instance ID from the Pulumi output:

```bash
aws ssm start-session \
  --target YOUR_INSTANCE_ID
```

Inside the shell, inspect its operating state:

```bash
hostname
uptime
df -h
systemctl --failed
```

Exit the session when finished:

```bash
exit
```

The instance does not need an inbound SSH rule for this workflow. Session Manager access still requires the operator's appropriate IAM permissions and a functioning managed-node connection.

### Step 7 — Run a controlled patch-compliance scan

Before installing updates, begin with a scan to understand the current state of the nodes.

```bash
aws ssm send-command \
  --targets "Key=tag:Application,Values=ssm-lab" \
  --document-name "AWS-RunPatchBaseline" \
  --parameters '{"Operation":["Scan"]}' \
  --comment "Module 6 patch compliance scan" \
  --query 'Command.CommandId' \
  --output text
```

Inspect the command's results as in Step 5, then review patch compliance in Systems Manager.

Do not automatically install every available patch just to complete the lab. Review the applicable baseline, operating-system support, and expected impact first. If you choose to test installation, use a disposable instance and the appropriate maintenance controls. Patch operations can change system state and may require service restarts. AWS Systems Manager +1

### Step 8 — Review execution history and audit activity

Review the following operational evidence:

| Evidence                  | Where to inspect it                          | What it tells you                                                         |
| ------------------------- | -------------------------------------------- | ------------------------------------------------------------------------- |
| Command status and output | Systems Manager Run Command                  | Whether commands reached and ran on the target nodes                      |
| Session activity          | Systems Manager session history              | Which sessions were started and their recorded status                     |
| Session transcript        | Configured CloudWatch Logs or S3 destination | Detailed session activity, if transcript logging is enabled and supported |
| API activity              | CloudTrail event history                     | Who invoked supported AWS API operations and when                         |
| Patch compliance          | Systems Manager Patch Manager                | Missing patches and the latest recorded compliance state                  |

For CloudTrail, search for relevant Systems Manager API events and correlate their timestamps with your diagnostic commands and sessions. CloudTrail API records and shell transcripts serve different purposes, so use both when the logging configuration supports them.

### 13\. Troubleshooting reference

| Symptom                                 | Likely cause                                                          | First action                                            |
| --------------------------------------- | --------------------------------------------------------------------- | ------------------------------------------------------- |
| Instance is absent from Systems Manager | Agent, role, or connectivity issue                                    | Check agent status, profile, and endpoint access        |
| Instance remains offline                | Agent cannot communicate reliably                                     | Check outbound HTTPS, DNS, and VPC endpoints            |
| AccessDeniedException                   | Missing operator or instance-role permission                          | Identify the denied action and relevant principal       |
| Session fails to start                  | Node connectivity or Session Manager permissions                      | Verify online status and ssm:StartSession authorization |
| Run Command has no output               | Command still running, failed delivery, or output configuration issue | Inspect invocation status and detailed results          |
| Patch scan fails                        | Unsupported OS, repository connectivity, or missing permissions       | Review command output and patch prerequisites           |
| Session transcript is missing           | Logging preferences or destination permissions                        | Verify Session Manager logging configuration            |

### 14\. Cleanup and cost control

Once you have finished the lab, remove the resources you created:

```bash
pulumi destroy
```

Review the proposed deletion before confirming. This removes the Pulumi-managed instances, IAM resources, and security group; it does not delete the pre-existing VPC or subnet.

Also review any independently created CloudWatch log groups, S3 log destinations, interface endpoints, or other supporting resources. Resources not managed by this Pulumi project will not be removed by its destroy operation.

### Further reading

* AWS Systems Manager — [Official documentation](https://docs.aws.amazon.com/systems-manager/latest/userguide/what-is-systems-manager.html?utm_source=chatgpt.com)

* [Session Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/session-manager.html?utm_source=chatgpt.com)

* [Run Command](https://docs.aws.amazon.com/systems-manager/latest/userguide/run-command.html?utm_source=chatgpt.com)

* [Patch Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/patch-manager.html?utm_source=chatgpt.com)

* [State Manager](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-state.html?utm_source=chatgpt.com)

* [Pulumi IAM InstanceProfile resource](https://www.pulumi.com/registry/packages/aws/api-docs/iam/instanceprofile/?utm_source=chatgpt.com)

Module 6 takeaway: Systems Manager turns server administration into a centrally controlled operational workflow. Pulumi makes the underlying infrastructure repeatable, while IAM, managed-node connectivity, execution history, and audit logging provide the foundation for secure fleet operations.
