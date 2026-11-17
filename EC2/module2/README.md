Worked for 1m 3s

### Phase 4 — Compute

### Module 2 — Amazon EBS and Instance Storage

Level: Beginner to intermediate · Infrastructure as Code: Pulumi with Python · Practical focus: persistence, encryption, snapshots, and recovery

In Module 1, you launched an EC2 instance and configured it to serve a web page. Now you'll learn how to store application data independently of the instance's operating system and recover that data when something goes wrong.

The central question for this module is:

If your EC2 instance is terminated, replaced, or fails, what happens to the data your application has written?

The answer depends on where that data lives and how you've configured the storage.

### 1\. Learning objectives

By the end of this module, you'll be able to:

* Explain the difference between Amazon EBS, instance store, and object storage such as Amazon S3.

* Select suitable EBS volume types and sizes.

* Understand IOPS, throughput, latency, and volume performance.

* Configure encrypted EBS volumes.

* Distinguish root volumes from additional data volumes.

* Attach and detach EBS volumes safely.

* Create Linux filesystems, mount volumes, and configure persistent mounts.

* Create EBS snapshots and restore volumes from them.

* Understand how EBS snapshots relate to AMIs.

* Provision storage resources using Pulumi and Python.

* Test data persistence and recovery through a practical lab.

### 2\. The three storage models to understand

![Básicos, pero valiosos - EBS Volume  Vs Instance Store  en AWS](https://images.openai.com/static-rsc-4/_ViJDC6keeaTbakGleYYB6WRk2xECTmTZJziFNMahfnLjuu_RBDt-FBidrJlIZFr9TjqXEtMvXYvJFIxlckXpduc41DaMSWZNJ7s_JHpduhR5xh_ZYOZ49tYomg6mdHINcvAVBVLEPgUn0dyFsi2cIewUaUoWVr8YcNVMCp6JheKtuTsLpZtszjNJGw1yoL2?purpose=fullsize)

### Amazon EBS

Persistent block storage

EBS provides block devices that can be attached to EC2 instances. It is appropriate for filesystems, application data, and workloads that need persistent storage beyond the life of a particular virtual machine.

![EBS vs. instance store: How your storage choice impacts downtime | by RepoBaby | Mar, 2026 | Medium](https://images.openai.com/static-rsc-4/yZ4VZOSX_VR5X0F51vS4180bARRQQZ-F9GroHw5skHLvzEsnzwsdU_pEoSChwB2115MoDpJLNWlx8lTYcVfNngW7CAvwu3kFhDzxzHQ9Uz-x7Fs2PVQ1_Cvg0JNwpk0bY6J3WC-wYjFiMqGyrgXFTJw12-Tn0nmQFTsfLYqfU1NhFnbbJvGmc-0Iv1orFKPZ?purpose=fullsize)

### EC2 instance store

Temporary local storage

Instance store provides storage physically associated with the host running an instance. It can offer high performance, but its data is not designed to survive instance termination or underlying host failure.

![What Is Amazon S3? Your Guide to Scalable Cloud Storage | DataCamp](https://images.openai.com/static-rsc-4/sr8zyiIdq6OFhDfikHD-ZA_RLuiEfJUy12sypSK8QfDZtr_F-lwLJt4hWPyRsKzLvnyYaUR6Wz59kp9SlKEdkhefJTPKuOydX4BHIGKEpD8PGZ-ZM7EMAODLj478ZSqmix05Z3m2QyPy9hlfaExBEXfhEbDZcZuy0G1eLk2BE1SDi9jkimIqH-uH2QUn9DMv?purpose=fullsize)

### Amazon S3

Object storage

S3 stores objects in buckets rather than presenting a conventional attached block device. It is useful for uploaded files, backups, static assets, and datasets shared across applications.

A useful rule of thumb:

* Use EBS when an application needs an attached block device and filesystem.

* Use instance store for suitable temporary data that can be recreated.

* Use S3 for objects that need to be accessed through an object-storage API.

These services complement one another rather than being interchangeable.

### 3\. How EBS fits into an EC2 architecture

EC2 instance

Operating system and application

Root EBS volume

OS, packages, configuration

Data EBS volume

Application files and persistent data

EBS snapshots

Point-in-time recovery and volume restoration

The root volume typically contains the operating system. A separate data volume lets you keep application data apart from the OS.

This separation is useful when replacing an instance, upgrading the operating system, or restoring application data. However, a separate EBS volume is not automatically a backup: accidental deletion, application-level corruption, or compromised credentials can still affect data. Snapshots and tested recovery procedures are important.

### 4\. EBS volume types, sizing, and performance

EBS volumes are not all designed for the same workload. Choosing a volume type means balancing performance, capacity, durability, and cost.

| Volume type | Best suited for                                 | Key consideration                                                                 |
| ----------- | ----------------------------------------------- | --------------------------------------------------------------------------------- |
| gp3         | General-purpose SSD workloads                   | Independent configuration of capacity, IOPS, and throughput within service limits |
| gp2         | General-purpose SSD workloads                   | Performance scales with volume size and includes burst behavior                   |
| io2         | I/O-intensive, performance-sensitive workloads  | Provisioned IOPS and high durability options                                      |
| io1         | Legacy or specific provisioned-IOPS workloads   | Compare with current io2 offerings before choosing                                |
| st1         | Large, sequential throughput workloads          | HDD-backed; not supported as a root volume                                        |
| sc1         | Infrequently accessed, throughput-oriented data | Lower-cost HDD option; not supported as a root volume                             |

AWS describes SSD-backed volumes as suitable for random and sequential I/O, while `st1` and `sc1` are optimized for large, sequential operations.

For this course, use `gp3` for the practical lab. It is a good default for learning persistent application storage without introducing unnecessary performance tuning.

### 4.1 Understand the performance metrics

### IOPS

Input/output operations per second. This describes how many read and write operations a volume can support. It's especially relevant to workloads with many small, random operations.

### Throughput

The volume of data transferred per second, commonly measured in MiB/s. This matters for workloads moving large amounts of data.

### Latency

The time required for an I/O operation to complete. Lower latency can be important for interactive applications and databases.

A volume's performance also depends on the EC2 instance's EBS bandwidth limits, workload patterns, and operating system configuration. Provisioning a high-performance volume does not guarantee that the entire application will achieve that performance.

### 4.2 Capacity is different from performance

Suppose an application needs 20 GiB of storage. Increasing its volume size to 100 GiB gives it more capacity, but it does not automatically mean that every performance metric increases proportionally. For `gp3`, you can configure supported IOPS and throughput independently of capacity, within the volume's limits.

For production workloads, use actual measurements to guide sizing rather than simply choosing the largest available configuration.

### 5\. Root volumes versus data volumes

An EC2 instance can have a root EBS volume and additional data volumes.

| Property                   | Root volume                                  | Data volume                                  |
| -------------------------- | -------------------------------------------- | -------------------------------------------- |
| Typical purpose            | OS and boot files                            | Application data, files, or databases        |
| Created at launch          | Usually, from the AMI's block-device mapping | Can be created at launch or attached later   |
| Persistence on termination | Often deleted by default                     | Depends on its delete-on-termination setting |
| Can be backed up           | Yes                                          | Yes                                          |
| Can be restored separately | Yes, using appropriate recovery procedures   | Yes                                          |

The deletion behavior is determined by each volume's configuration, not just by whether it is called a root or data volume. Verify the `DeleteOnTermination` setting before terminating an instance.

Production principle: Keep replaceable operating-system components separate from important application data when the workload benefits from that separation. This makes instance replacement and recovery easier to manage.

### 6\. EBS encryption

EBS encryption protects data at rest and supports encryption of data moving between EC2 and EBS on supported instance types. It also applies to snapshots created from encrypted volumes.

Encryption is integrated with AWS KMS. AWS-managed EBS encryption keys are available, and customer-managed keys can be used when you need more control over permissions, auditing, and key lifecycle.

Important considerations:

* You can enable encryption by default for new EBS volumes in an account and Region.

* A volume created from an encrypted snapshot is encrypted.

* Snapshots of encrypted volumes remain encrypted.

* Sharing or copying encrypted snapshots can require additional KMS permissions and deliberate key configuration.

* Encryption does not replace filesystem permissions, IAM controls, backups, or recovery testing.

AWS documents these rules in its .

For the lab, we'll explicitly set `encrypted=True` on the data volume. That makes the intention visible in the infrastructure code, even if the account already encrypts volumes by default.

### 7\. EBS snapshots and recovery

An EBS snapshot is a point-in-time backup of a volume. Snapshots are stored and managed by AWS and can be used to create new volumes.

EBS data volume

Filesystem and application data

Create snapshot

Point-in-time block-level backup

Restore

Create a replacement volume

Attach

Mount on an EC2 instance

Snapshots are incremental: after the first snapshot, AWS can store only the blocks that have changed since the previous snapshot, while maintaining the ability to restore the volume's point-in-time contents.

Remember these distinctions:

* A snapshot is not the same thing as a running volume.

* A snapshot can be used to create a new volume.

* A restored volume must be attached and mounted before its filesystem contents are accessed.

* A snapshot is generally crash-consistent unless the application and filesystem are prepared for a stronger consistency guarantee.

* Databases and other stateful applications may require application-aware backup procedures.

* Restoring a volume does not automatically validate that the application can recover successfully.

### 7.1 How AMIs use EBS snapshots

An EBS-backed AMI includes references to snapshots for its EBS-backed block devices. When you launch an instance from that AMI, AWS creates the corresponding EBS volumes.

A custom AMI is useful when you need to preserve a bootable system image. An EBS snapshot is useful when you need to preserve and restore a volume. They solve related but different recovery problems.

### 8\. Hands-on lab — Attach, format, snapshot, and restore an EBS volume

### Lab scenario

You'll deploy an EC2 instance with a separate encrypted EBS data volume, write a file to it, create a snapshot, and restore the data to a new volume.

Estimated time: 45–75 minutes

Cost note: EC2 compute, EBS capacity, snapshots, and data transfer may incur charges. Use a small volume and clean up resources when finished.

### 8.1 Lab architecture

We'll create a dedicated stack instead of depending on resources from Module 1. That keeps the exercise reproducible and makes cleanup easier.

* One EC2 instance running Amazon Linux 2023.

* One encrypted `gp3` data volume.

* A separate root volume.

* A security group for HTTP testing, with no inbound SSH rule.

* A snapshot and a restored volume created during the exercise.

The instance uses a public endpoint only for the simple web demonstration. The data volume will be separate from the root volume, and the web application will store its data on the mounted filesystem.

### 8.2 Create the Pulumi project

Create a new project for this lab:

```bash
mkdir aws-ebs-module-2
cd aws-ebs-module-2

pulumi new aws-python
python -m pip install pulumi pulumi-aws
```

Configure the AWS Region and choose a stack name such as `dev`. Use the same Region for the instance, volume, and snapshot.

For this exercise, the instance will use a configurable SSH key and a security group restricted to your public IP address. If you prefer not to use SSH, you can adapt the instance to use Systems Manager Session Manager, provided the required instance role, agent, and connectivity are configured.

### 8.3 Provision the instance and encrypted volume

Replace `__main__.py` with the following code. This creates the EC2 instance and EBS volume in the same Availability Zone, then attaches the volume to the instance.

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

# Required: existing EC2 key pair name and your public IPv4 CIDR.
key_name = config.require("keyName")
admin_cidr = config.require("adminCidr")

# Use the default VPC for this introductory lab.
vpc = aws.ec2.get_vpc(default=True)
subnets = aws.ec2.get_subnets(
    filters=[
        {
            "name": "vpc-id",
            "values": [vpc.id],
        }
    ]
)

if not subnets.ids:
    raise ValueError("No subnets found in the default VPC.")

# Use the first available subnet for this lab.
subnet = aws.ec2.get_subnet(id=subnets.ids[0])

ami = (
    "resolve:ssm:/aws/service/ami-amazon-linux-latest/"
    "al2023-ami-kernel-default-x86_64"
)

web_sg = aws.ec2.SecurityGroup(
    "ebs-lab-sg",
    description="Restricted SSH and HTTP for the EBS lab",
    vpc_id=vpc.id,
    ingress=[
        {
            "description": "SSH from administrator IP",
            "protocol": "tcp",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": [admin_cidr],
        },
        {
            "description": "HTTP for the lab",
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        }
    ],
    tags={"Purpose": "learning"},
)

server = aws.ec2.Instance(
    "ebs-lab-instance",
    ami=ami,
    instance_type="t3.micro",
    subnet_id=subnet.id,
    associate_public_ip_address=True,
    key_name=key_name,
    vpc_security_group_ids=[web_sg.id],
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
    tags={"Name": "ebs-lab-instance"},
)

data_volume = aws.ebs.Volume(
    "application-data",
    availability_zone=server.availability_zone,
    size=8,
    type="gp3",
    encrypted=True,
    tags={
        "Name": "ebs-lab-data",
        "Purpose": "learning",
    },
)

attachment = aws.ec2.VolumeAttachment(
    "application-data-attachment",
    device_name="/dev/sdf",
    volume_id=data_volume.id,
    instance_id=server.id,
)

pulumi.export("instance_id", server.id)
pulumi.export("public_ip", server.public_ip)
pulumi.export("data_volume_id", data_volume.id)
pulumi.export("availability_zone", server.availability_zone)
pulumi.export("ssh_command", pulumi.Output.concat(
    "ssh -i <path-to-private-key> ec2-user@",
    server.public_ip,
))
```

Set the two required configuration values:

```bash
pulumi config set keyName YOUR_EXISTING_EC2_KEY_PAIR
pulumi config set adminCidr YOUR_PUBLIC_IP/32
```

Replace `YOUR_PUBLIC_IP` with your current public IPv4 address. Don't use `0.0.0.0/0` for SSH access.

Preview and deploy:

```bash
pulumi preview
pulumi up
```

Review the changes and confirm the deployment.

Why use the instance's Availability Zone for the volume? Standard EBS volumes must be attached to instances in the same Availability Zone. The Pulumi dependency on `server.availability_zone` ensures the volume is created in the correct zone.

### 8.4 Find the actual Linux block device

The attachment's requested device name is `/dev/sdf`, but on many modern Nitro-based EC2 instances, Linux exposes EBS volumes as NVMe devices such as `/dev/nvme1n1`. The requested name and the device name visible inside Linux may differ.

Connect using the SSH command from the stack output, supplying your actual private-key path. Then run:

```bash
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS
```

Example output might resemble:

```text
NAME          SIZE FSTYPE MOUNTPOINTS
nvme0n1         8G
└─nvme0n1p1     8G xfs    /
nvme1n1         8G
```

Your device names may differ. Identify the new, unformatted 8 GiB device by comparing its size and mount points with the root disk. Never format the root device or a disk that already contains data.

You can inspect filesystem signatures before proceeding:

```bash
sudo blkid
sudo file -s /dev/nvme1n1
```

Replace `/dev/nvme1n1` in the commands below with the actual unformatted data device you identified.

### 8.5 Format and mount the data volume

For this lab, we'll use the XFS filesystem. Formatting a disk destroys existing filesystem data, so only run these commands after confirming that the selected device is the new, empty EBS volume.

Create the filesystem:

```bash
sudo mkfs.xfs /dev/nvme1n1
```

Create a mount point and mount the filesystem:

```bash
sudo mkdir -p /data
sudo mount /dev/nvme1n1 /data
```

Verify that the filesystem is mounted:

```bash
df -hT /data
lsblk -f
```

You should see the XFS filesystem mounted at `/data`.

### 8.6 Persist data across reboots

Create an application data file:

```bash
echo "Persistent EBS data created in Module 2" \
  | sudo tee /data/important.txt

cat /data/important.txt
```

Now configure the filesystem to mount automatically after reboot.

First, obtain the filesystem UUID:

```bash
sudo blkid /dev/nvme1n1
```

The output includes a UUID. Copy that value and add an entry to `/etc/fstab`:

```text
UUID=YOUR-FILESYSTEM-UUID /data xfs defaults,nofail 0 2
```

Replace the placeholder with the actual UUID. Use `sudoedit /etc/fstab` or another safe editor to add the line.

Test the configuration before rebooting:

```bash
sudo mount -a
findmnt /data
```

If these commands succeed, the filesystem should mount automatically on reboot. Using a UUID avoids depending on a device name that can change.

Important distinction: Mounting the filesystem makes it accessible at `/data`. The UUID identifies the filesystem, not the EBS volume itself. If you restore a snapshot into a second volume while the original is still attached, both volumes can contain the same filesystem UUID. Don't mount both filesystems using the same UUID-based configuration without addressing that duplication.

### 9\. Create an EBS snapshot

Before creating the snapshot, verify that the file exists:

```bash
cat /data/important.txt
```

For this small lab, you can create a snapshot using the AWS CLI after the data has been written. For an application with ongoing writes, quiesce the application or use an application-consistent backup procedure first.

Retrieve the volume ID from Pulumi:

```bash
pulumi stack output data_volume_id
```

Set it in your shell:

```bash
VOLUME_ID=$(pulumi stack output data_volume_id)
```

Create a snapshot:

```bash
SNAPSHOT_ID=$(aws ec2 create-snapshot \
  --volume-id "$VOLUME_ID" \
  --description "Module 2 EBS recovery lab" \
  --query SnapshotId \
  --output text)

echo "$SNAPSHOT_ID"
```

Wait until the snapshot is complete:

```bash
aws ec2 wait snapshot-completed \
  --snapshot-ids "$SNAPSHOT_ID"
```

Verify the snapshot:

```bash
aws ec2 describe-snapshots \
  --snapshot-ids "$SNAPSHOT_ID" \
  --query 'Snapshots[0].{State:State,VolumeId:VolumeId,Encrypted:Encrypted,Size:VolumeSize}'
```

The snapshot should reach the `completed` state. Because the source volume is encrypted, its snapshot is encrypted as well.

Save the snapshot ID somewhere safe for the restore exercise.

### 10\. Restore a new volume from the snapshot

We'll create a second volume from the snapshot, attach it to the same instance, and verify that the original file is present. The original volume remains intact during this test.

### 10.1 Create the restored volume with Pulumi

Add a configuration value containing the snapshot ID:

```bash
pulumi config set restoreSnapshotId YOUR_SNAPSHOT_ID
```

Add the following to `__main__.py`, after the existing volume and attachment resources:

```python
restore_snapshot_id = config.require("restoreSnapshotId")

restored_volume = aws.ebs.Volume(
    "restored-application-data",
    availability_zone=server.availability_zone,
    snapshot_id=restore_snapshot_id,
    type="gp3",
    encrypted=True,
    tags={
        "Name": "ebs-lab-restored-data",
        "Purpose": "recovery-test",
    },
)

restored_attachment = aws.ec2.VolumeAttachment(
    "restored-data-attachment",
    device_name="/dev/sdg",
    volume_id=restored_volume.id,
    instance_id=server.id,
)

pulumi.export("restored_volume_id", restored_volume.id)
```

The restored volume is created in the same Availability Zone as the instance. Its size is derived from the snapshot unless you explicitly request a larger size. If the source snapshot is encrypted, AWS preserves encryption for the restored volume; KMS permissions and configuration must permit the operation.

Preview the changes:

```bash
pulumi preview
pulumi up
```

Confirm that Pulumi plans to create the restored volume and its attachment without unexpectedly replacing your original instance or data volume.

### 10.2 Identify and mount the restored filesystem

On the EC2 instance, inspect the devices again:

```bash
lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS
```

Identify the new disk by comparing the device list before and after the attachment. On a Nitro-based instance, it may appear as another NVMe device, but don't assume a particular device name.

Create a separate mount point:

```bash
sudo mkdir -p /mnt/restore
```

The restored disk already contains the original filesystem. Do not run `mkfs` on it. Mount the existing filesystem using the verified device path:

```bash
sudo mount -o ro /dev/nvme2n1 /mnt/restore
```

Replace `/dev/nvme2n1` with the actual restored device. Read-only mounting helps prevent accidental modification of the recovered data.

Verify the recovered file:

```bash
cat /mnt/restore/important.txt
```

Expected output:

```text
Persistent EBS data created in Module 2
```

You've now verified that a snapshot can be used to create a new volume containing the data that existed at the snapshot point in time.

### 11\. Resizing an EBS volume and its filesystem

EBS volume capacity can be increased, but expanding the AWS volume is only one part of the process. The partition and filesystem may also need to be extended.

1\. Increase EBS volume size

For example, 8 GiB → 16 GiB

2\. Verify the operating system sees the new capacity

Use lsblk and filesystem tools

3\. Expand the partition or filesystem if required

The procedure depends on the disk layout and filesystem

AWS supports modifying EBS volume size, type, and performance for supported configurations. Filesystem expansion is a separate operating-system operation.

For example, if your XFS filesystem is directly on an unpartitioned device, the filesystem can be grown with:

```bash
sudo xfs_growfs /data
```

Run this only after increasing the underlying volume and verifying that the additional capacity is available to the filesystem. If the filesystem is on a partition, you must expand the partition first.

For ext4, the corresponding filesystem command is typically `resize2fs`, with the appropriate device and partition preparation.

Never assume that increasing the EBS volume size automatically expands the mounted filesystem.

### 12\. Common EBS troubleshooting scenarios

| Problem                                  | Investigation                                                                                  |
| ---------------------------------------- | ---------------------------------------------------------------------------------------------- |
| Volume won't attach                      | Confirm the instance and volume are in the same Availability Zone and the volume is available. |
| Device name isn't /dev/sdf               | Inspect lsblk; Nitro instances commonly expose EBS volumes as NVMe devices.                    |
| Filesystem isn't mounted after reboot    | Check /etc/fstab, the UUID, and journalctl for mount errors.                                   |
| mount reports an unknown filesystem      | Verify the actual device and filesystem type; don't format a volume containing data.           |
| Restored data is missing                 | Confirm the snapshot ID, completion state, restored device, and mount point.                   |
| Volume is encrypted but can't be created | Check KMS permissions and the encryption key configuration.                                    |
| Application reports slow storage         | Examine IOPS, throughput, queue length, latency, and EC2 EBS bandwidth limits.                 |
| Disk space remains full after resizing   | Check whether the partition and filesystem have also been expanded.                            |

A useful habit is to inspect the entire storage path: AWS volume configuration, device visibility, partition layout, filesystem, mount configuration, and application behavior.

### 13\. Cleanup and recovery hygiene

Before destroying the stack, unmount the restored and original filesystems:

```bash
sudo umount /mnt/restore
sudo umount /data
```

Remove the corresponding `/etc/fstab` entry for `/data` if you added one. Then return to your local terminal and review the planned deletions:

```bash
pulumi preview --diff
pulumi destroy
```

The snapshot created through the AWS CLI is not managed by Pulumi, so it may remain after the stack is destroyed. Check its ID:

```bash
aws ec2 describe-snapshots \
  --snapshot-ids "$SNAPSHOT_ID" \
  --query 'Snapshots[0].State' \
  --output text
```

If you no longer need the snapshot, delete it deliberately:

```bash
aws ec2 delete-snapshot --snapshot-id "$SNAPSHOT_ID"
```

Only do this after confirming that you don't need it for recovery or future exercises. Also verify that no retained EBS volumes remain, since they can continue to incur charges.

### 14\. Knowledge check

1. Which EBS type is a sensible default for this general-purpose learning lab?

gp3

sc1

st1

2. What must match for a standard EBS volume attachment?

The instance and volume must have the same AMI

The instance and volume must be in the same Availability Zone

The instance and volume must have identical security groups

3. What should you do before mounting a volume restored from a snapshot?

Format it with mkfs

Delete its filesystem UUID

Identify the device and mount its existing filesystem

4. Does increasing EBS capacity always expand the filesystem automatically?

Yes, always

No, the filesystem or partition may need to be expanded

Only for encrypted volumes

5. What happens to instance-store data when an instance is stopped?

It is preserved like EBS data

It is erased

It is automatically copied into an EBS snapshot

Check answers

### 15\. Module completion checklist

Hands-on progress

### 0 / 8

Explain EBS, instance store, and S3 differences.

Choose an appropriate EBS volume type.

Provision an encrypted gp3 volume with Pulumi.

Format and mount the data volume safely.

Write data and configure persistent mounting.

Create a snapshot and restore a second volume.

Verify recovered data and understand resize procedures.

Clean up resources and review remaining snapshots.

### Further reading

* Amazon EBS — .

* .

* .

* .

* .

Next: Module 3 — EC2 IAM Roles and Instance Profiles. You'll learn how applications running on EC2 can access AWS services securely using temporary credentials instead of embedded access keys.
