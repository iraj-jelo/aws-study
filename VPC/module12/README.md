### Module 12 — VPC Observability and Troubleshooting

This module focuses on how to diagnose real AWS networking failures systematically: determine where packets are being lost, distinguish routing problems from security filtering, and use AWS observability tools to gather evidence rather than guessing.

We’ll use Pulumi with Python for infrastructure examples and the AWS CLI v2 for investigation. No quizzes, and no unnecessary legacy workflows.

### 1\. Learning objectives

By the end of this module, you should be able to:

* Use VPC Flow Logs to investigate accepted and rejected traffic.

* Interpret CloudWatch metrics and logs without confusing them with packet-level evidence.

* Use VPC Reachability Analyzer to identify potential connectivity blockers.

* Use Network Access Analyzer to evaluate network exposure against security requirements.

* Inspect routes, security groups, network ACLs, DNS resolution, and packet paths.

* Recognize MTU, fragmentation, intermittent connectivity, and asymmetric-routing problems.

* Separate network failures from IAM authorization, application failures, and DNS issues.

* Follow a repeatable troubleshooting procedure using AWS CLI commands.

### 2\. Concepts and architecture

### 2.1 Observability is not the same as packet capture

AWS networking observability combines several sources of evidence. Each answers a different question.

| Tool                                 | Primary question                                                                                               |
| ------------------------------------ | -------------------------------------------------------------------------------------------------------------- |
| VPC Flow Logs                        | What traffic metadata was observed at a supported network interface or other supported scope?                  |
| CloudWatch metrics                   | How much traffic, how many errors, or how many connection-related events occurred?                             |
| CloudWatch Logs                      | What events or flow records were recorded?                                                                     |
| Reachability Analyzer                | Can the modeled network path connect these source and destination resources, and what configuration blocks it? |
| Network Access Analyzer              | Does the modeled network configuration permit paths that violate defined network-access requirements?          |
| Route tables and security group APIs | What routing and filtering configuration is currently defined?                                                 |
| Route 53 Resolver query logging      | What DNS queries and responses were observed?                                                                  |
| VPC Traffic Mirroring                | What selected packets can be copied to a monitoring appliance for deeper analysis?                             |
| Network Manager                      | How can supported AWS and hybrid network resources, topology, and health be monitored centrally?               |

These tools are complementary, not interchangeable. In particular, Reachability Analyzer and Network Access Analyzer perform configuration-based analysis; they do not prove that a real application is healthy or that every packet successfully traverses the path.

### 2.2 The packet path: a systematic model

Suppose a client connects to an application running on an EC2 instance in a private subnet.

Client

DNS lookup and TCP connection

Name resolution and destination selection

Network path

Routes · gateways · peering · Transit Gateway, if applicable

Security filtering

Destination ENI and security group

Network ACLs and stateful security-group rules

Host and application processing

Application

Listening socket · TLS · application response

This is a diagnostic model, not a claim that every AWS architecture processes traffic in precisely this sequence. The actual path depends on the source, destination, protocol, gateways, and network architecture.

For a TCP connection, investigate both directions:

* Does the client send a SYN packet toward the destination?

* Can the SYN reach the destination?

* Does the destination send a SYN-ACK response?

* Can the response return to the client?

* Does the TCP handshake complete?

* Does the application respond successfully after the connection is established?

A working forward path does not guarantee a working return path.

Important: Security groups are stateful, but network ACLs are stateless. Routing must support the return path, and applicable network ACL rules must allow the relevant traffic in both directions.

### 3\. VPC Flow Logs

### 3.1 What Flow Logs record

VPC Flow Logs collect metadata about IP traffic associated with supported network resources. You can enable them at VPC, subnet, or network-interface scope and publish records to CloudWatch Logs, Amazon S3, or Amazon Data Firehose, depending on the chosen configuration.

A default flow record contains fields such as:

* Source and destination IP addresses.

* Source and destination ports.

* IP protocol number.

* Number of packets and bytes.

* Start and end timestamps.

* `ACCEPT` or `REJECT` action.

* Logging status.

A flow is identified using a five-tuple: source IP, destination IP, source port, destination port, and protocol, scoped to a network interface and aggregation interval. Records summarize traffic; they are not a packet-by-packet transcript.

Example:

```text
2 123456789012 eni-0123456789abcdef0
10.0.2.15 10.0.3.25 49152 8080 6 12 840
1729400000 1729400060 ACCEPT OK
```

This is a line-wrapped illustration of a version-2 record, not a real observation. Its key fields mean:

| Field                 | Meaning                                                 |
| --------------------- | ------------------------------------------------------- |
| eni-0123456789abcdef0 | Network interface                                       |
| 10.0.2.15             | Source IP                                               |
| 10.0.3.25             | Destination IP                                          |
| 49152                 | Source port                                             |
| 8080                  | Destination port                                        |
| 6                     | TCP protocol                                            |
| 12                    | Packet count                                            |
| 840                   | Byte count                                              |
| ACCEPT                | Traffic was accepted by the applicable network controls |
| OK                    | Logging completed normally for that record              |

The protocol number `6` means TCP; `17` means UDP; and `1` means ICMP for IPv4. IPv6 uses a different protocol-number context for ICMPv6 (`58`).

### 3.2 Understand `ACCEPT`, `REJECT`, and logging status

`ACCEPT`

The recorded traffic was accepted by the applicable network controls. This does not guarantee that the destination application received the data or returned a successful response.

`REJECT`

Traffic was rejected. Security-group or network ACL rules may be responsible, but a rejected record can also arise from packets arriving after a connection has closed. Inspect the tuple, direction, and surrounding records before concluding why it happened.

`NODATA` / `SKIPDATA`

`NODATA` means no traffic was recorded for the interface during the aggregation interval. `SKIPDATA` means some records were skipped. Neither should be interpreted as proof that the entire network is healthy.

AWS documents these record statuses and their meanings in the [Flow Logs record reference](https://docs.aws.amazon.com/vpc/latest/userguide/flow-log-records.html?utm_source=chatgpt.com).

### 3.3 Important limitations

Flow Logs are extremely useful, but they have boundaries.

* They are not packet captures. You cannot reconstruct TCP sequence numbers, HTTP request bodies, or every individual packet from ordinary flow records.

* They are aggregated and delivered asynchronously. They are not a real-time packet debugger.

* Some traffic is not captured. AWS documents exclusions, including traffic generated by instances when they contact the Amazon-provided DNS server. Check the current limitations before interpreting missing records.

* Records can be skipped. Investigate `SKIPDATA` rather than assuming no traffic occurred.

* A flow can be accepted without a successful application response. The application may not be listening, may crash, or may reject the request at a higher layer.

* The destination address fields can be misleading in some translated or multi-address scenarios. Consider custom fields such as `pkt-srcaddr` and `pkt-dstaddr` when original packet addresses matter.

* Enabling Flow Logs does not recover past traffic. You need a logging configuration that was active when the relevant traffic occurred.

For the full list, consult the [official Flow Logs limitations](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-limitations.html?utm_source=chatgpt.com).

### 3.4 Enable Flow Logs using AWS CLI

First, identify your account, region, and VPC:

```bash
aws sts get-caller-identity

aws configure get region

aws ec2 describe-vpcs \
  --query 'Vpcs[].{VpcId:VpcId,CIDR:CidrBlock,State:State}' \
  --output table
```

Set the VPC ID and create a CloudWatch log group. Replace the example ID with your own.

```bash
export VPC_ID=vpc-0123456789abcdef0
export LOG_GROUP=/aws/vpc/flow-logs
```

On PowerShell, use:

```powershell
$VpcId = "vpc-0123456789abcdef0"
$LogGroup = "/aws/vpc/flow-logs"
```

Create the log group if it doesn't exist:

```bash
aws logs create-log-group \
  --log-group-name "$LOG_GROUP"
```

If the group already exists, AWS returns an error; you can safely continue after confirming it exists.

Now enable Flow Logs. This example assumes you have already created a suitable IAM role for VPC Flow Logs and have its ARN.

```bash
aws ec2 create-flow-logs \
  --resource-type VPC \
  --resource-ids "$VPC_ID" \
  --traffic-type ALL \
  --log-destination-type cloud-watch-logs \
  --log-group-name "$LOG_GROUP" \
  --deliver-logs-permission-arn \
    arn:aws:iam::123456789012:role/VPCFlowLogsRole
```

The role ARN is a placeholder. The role must have the trust relationship and permissions required by the Flow Logs delivery service. The caller creating the Flow Log also needs the relevant EC2 and IAM permissions.

Verify the configuration:

```bash
aws ec2 describe-flow-logs \
  --filter "Name=resource-id,Values=$VPC_ID" \
  --output table
```

Check the delivery status and, after traffic occurs, inspect the log group:

```bash
aws logs describe-log-streams \
  --log-group-name "$LOG_GROUP" \
  --order-by LastEventTime \
  --descending
```

You may need to wait for the first records to arrive. An empty log group immediately after enabling Flow Logs does not necessarily indicate a configuration failure.

AWS setup reference: [Publish Flow Logs to CloudWatch Logs](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs-cwl-create-flow-log.html?utm_source=chatgpt.com).

### 3.5 Query Flow Logs with CloudWatch Logs Insights

Once records exist, Logs Insights can help isolate suspicious traffic. For the default format, a useful starting query is:

```sql
fields @timestamp, @message
| filter @message like /REJECT/
| sort @timestamp desc
| limit 100
```

This filters for records containing `REJECT`. It is a quick first pass; for structured analysis, parse the record fields or configure a custom format with named fields.

For example, if the log format includes `srcaddr`, `dstaddr`, `dstport`, `protocol`, and `action`:

```sql
fields @timestamp, srcaddr, dstaddr, dstport,
       protocol, action
| filter action = "REJECT"
| stats count(*) as records
  by srcaddr, dstaddr, dstport, protocol
| sort records desc
| limit 50
```

The second query assumes those fields are available as structured fields in your log events. If your logs are stored as space-delimited text, parse the fields first or use the field names supported by your configured log format.

For production, use a consistent record format and include enough information to investigate original packet addresses, traffic direction, and the relevant interface.

### 4\. CloudWatch metrics and logging

Flow Logs answer, “What traffic metadata was recorded?” CloudWatch metrics answer a different question: “How is this resource behaving over time?”

Useful metrics depend on the network service being investigated.

| Resource                  | Useful metrics or signals                                                                                   | What to investigate                                                        |
| ------------------------- | ----------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------- |
| NAT Gateway               | ErrorPortAllocation, PacketsDropCount, BytesInFromSource, BytesOutToDestination and related traffic metrics | Connection allocation pressure, dropped packets, unexpected traffic volume |
| Transit Gateway           | Bytes, packets, and applicable packet-drop metrics                                                          | Traffic changes, attachment-level issues, dropped traffic                  |
| Network Load Balancer     | HealthyHostCount, UnHealthyHostCount, TCP_Target_Reset_Count, TCP_ELB_Reset_Count                           | Unhealthy targets, resets, connection failures                             |
| Application Load Balancer | HealthyHostCount, UnHealthyHostCount, TargetConnectionErrorCount, HTTPCode_Target_5XX_Count                 | Target reachability, backend connection errors, application errors         |
| EC2                       | NetworkIn, NetworkOut, NetworkPacketsIn, NetworkPacketsOut                                                  | Traffic volume and broad changes in network activity                       |

Metric names, dimensions, and availability vary by service and configuration. Verify the relevant CloudWatch namespace and current metric documentation before building alarms.

A few useful diagnostic distinctions:

* A sudden drop in traffic volume might indicate a routing, application, or client-side problem.

* An increase in unhealthy load-balancer targets can be a symptom of application failure or network connectivity failure.

* A NAT Gateway drop or port-allocation metric can point toward egress pressure rather than an inbound security-group issue.

* EC2 network-byte metrics do not tell you which security-group rule blocked a connection.

CloudWatch metrics are aggregated measurements. Combine them with Flow Logs, resource configuration, and application logs to identify the cause.

### 5\. Reachability Analyzer

### 5.1 What it does

VPC Reachability Analyzer is a configuration-analysis tool that determines whether a modeled network path exists between a specified source and destination. It can identify blocking configuration in supported components, including route tables, security groups, network ACLs, and load balancers.

It does not send test packets across the network. Instead, it analyzes the configured network path and provides hop-by-hop details or an explanation of why the modeled path is not reachable.

Use it when you need to answer questions such as:

* Can this EC2 instance reach a database on TCP port 5432?

* Can a network path reach an instance from an internet gateway?

* Which route or security-group configuration blocks the expected connection?

* Does a route-table change preserve the intended connectivity?

### 5.2 Run an analysis with AWS CLI

Suppose your application instance should connect to a database instance on TCP port 5432.

First, identify the relevant instances and network interfaces:

```bash
aws ec2 describe-instances \
  --filters \
    "Name=instance-state-name,Values=running" \
  --query \
    'Reservations[].Instances[].{
       Instance:InstanceId,
       PrivateIP:PrivateIpAddress,
       Vpc:VpcId,
       Subnet:SubnetId,
       ENIs:NetworkInterfaces[].NetworkInterfaceId
    }' \
  --output json
```

Choose the source and destination resources. Reachability Analyzer paths are created using supported AWS resource identifiers, commonly ENI IDs for an instance-to-instance analysis.

Set the values:

```bash
export SOURCE_ENI=eni-0123456789abcdef0
export DEST_ENI=eni-0abcdef1234567890
```

Create the path:

```bash
aws ec2 create-network-insights-path \
  --source "$SOURCE_ENI" \
  --destination "$DEST_ENI" \
  --protocol TCP \
  --destination-port 5432
```

Record the returned `NetworkInsightsPathId`, then start the analysis:

```bash
aws ec2 start-network-insights-analysis \
  --network-insights-path-id nip-REPLACE_ME
```

Record the returned `NetworkInsightsAnalysisId`. Retrieve its result:

```bash
aws ec2 describe-network-insights-analyses \
  --network-insights-analysis-ids nia-REPLACE_ME \
  --output json
```

Inspect these result fields:

* `Status` — whether the analysis completed successfully.

* `NetworkPathFound` — whether a modeled path was found.

* `Explanations` — reasons a path could not be established.

* `ForwardPathComponents` — the modeled forward path when available.

* `ReturnPathComponents` — return-path details when available.

A completed analysis with `NetworkPathFound: false` is a useful diagnostic result, not an AWS service error. It means the modeled path is blocked or unavailable under the analyzed configuration.

Official walkthrough: [Reachability Analyzer using the AWS CLI](https://docs.aws.amazon.com/vpc/latest/reachability/getting-started-cli.html?utm_source=chatgpt.com).

### 5.3 What Reachability Analyzer cannot prove

A reachable result does not establish that:

* The database process is listening on port 5432.

* PostgreSQL credentials are valid.

* DNS resolves to the intended address.

* A firewall inside the operating system permits the connection.

* A transient network event will not cause packet loss.

* An application response will be generated successfully.

Think of Reachability Analyzer as a way to validate the modeled network configuration, not as a substitute for a live connection test.

### 6\. Network Access Analyzer

Reachability Analyzer investigates a particular path. Network Access Analyzer is more suited to identifying unintended access paths across your AWS network.

For example, imagine that your production database should not be reachable from an internet gateway. You can define a network access scope that matches paths from an internet gateway to network interfaces, then exclude explicitly approved public-facing resources if necessary.

Security requirement

No unintended internet-to-database paths

Network Access Scope

MatchPaths: internet gateway → network interface

ExcludePaths: approved public ingress resources, where appropriate

Analysis findings

Review potential paths that match the scope and investigate any unexpected exposure

Network Access Analyzer is based on automated reasoning over supported network configurations. Its findings are potential paths that match the specified scope; they are not observations of live traffic. It also has limitations around supported resources, protocols, cross-account and cross-Region paths, and certain intermediate resources. In particular, its network path analysis is limited to IPv4 TCP and UDP, and its findings are unidirectional.

### 6.1 Inspect and run Network Access Analyzer

Start by listing existing scopes:

```bash
aws ec2 describe-network-insights-access-scopes \
  --output table
```

Create a scope using a match condition, for example:

```bash
aws ec2 create-network-insights-access-scope \
  --match-paths \
  'Source={ResourceStatement={ResourceTypes=["AWS::EC2::InternetGateway"]}} Destination={ResourceStatement={ResourceTypes=["AWS::EC2::NetworkInterface"]}}'
```

The returned scope ID is needed for the next step. Analyze it:

```bash
aws ec2 start-network-insights-access-scope-analysis \
  --network-insights-access-scope-id nas-REPLACE_ME
```

Use the returned analysis ID to inspect the result:

```bash
aws ec2 describe-network-insights-access-scope-analyses \
  --network-insights-access-scope-analysis-ids nasa-REPLACE_ME
```

Review the resulting findings and inspect the involved resources. This example is an intentionally broad starting scope; a production security assessment should narrow its match and exclusion conditions to the actual requirements. Exact CLI input syntax and supported resource statements should be checked against the current [Network Access Analyzer CLI guide](https://docs.aws.amazon.com/vpc/latest/network-access-analyzer/getting-started-cli.html?utm_source=chatgpt.com).

### 7\. AWS Network Manager and network visualization

AWS Network Manager provides centralized visibility into supported AWS and hybrid networks. Its capabilities include network topology visualization, monitoring dashboards, and event tracking for managed network resources.

This is especially useful when your architecture includes multiple Transit Gateways, remote sites, customer gateways, and connections that are difficult to understand from individual VPC consoles.

For example, if a remote office cannot reach a VPC, you might need to investigate several layers:

* The on-premises site and device.

* The VPN or Direct Connect connection.

* The Transit Gateway attachment and routing.

* The destination VPC route table.

* The target subnet and security controls.

Network Manager can help you visualize supported network topology and monitor applicable resources. It does not automatically explain every application-level failure or capture arbitrary packets. Its exact capabilities depend on the resources and network features being managed.

Useful CLI discovery commands include:

```bash
aws ec2 describe-transit-gateways

aws ec2 describe-transit-gateway-attachments

aws ec2 describe-transit-gateway-route-tables
```

These commands inspect the underlying Transit Gateway resources and complement the visual overview.

### 8\. Route analysis and security-group analysis

When a connection fails, do not inspect only the destination security group. Examine the complete path.

### 8.1 Inspect the destination instance

```bash
aws ec2 describe-instances \
  --instance-ids i-REPLACE_ME \
  --query \
    'Reservations[].Instances[].{
       Instance:InstanceId,
       PrivateIP:PrivateIpAddress,
       PublicIP:PublicIpAddress,
       Vpc:VpcId,
       Subnet:SubnetId,
       SecurityGroups:SecurityGroups
    }' \
  --output json
```

Find its network interfaces:

```bash
aws ec2 describe-network-interfaces \
  --filters \
    "Name=attachment.instance-id,Values=i-REPLACE_ME" \
  --query \
    'NetworkInterfaces[].{
       ENI:NetworkInterfaceId,
       PrivateIP:PrivateIpAddress,
       Subnet:SubnetId,
       Groups:Groups
    }' \
  --output json
```

Inspect the security groups:

```bash
aws ec2 describe-security-groups \
  --group-ids sg-REPLACE_ME \
  --output json
```

Remember that an instance may have multiple interfaces and security groups. The effective rules are the combination of rules associated with the relevant interface, not just whichever group you happened to inspect first.

### 8.2 Inspect the subnet route table

```bash
aws ec2 describe-route-tables \
  --filters \
    "Name=association.subnet-id,Values=subnet-REPLACE_ME" \
  --output json
```

If this does not return an explicitly associated route table, inspect the VPC's main route table as well:

```bash
aws ec2 describe-route-tables \
  --filters \
    "Name=vpc-id,Values=vpc-REPLACE_ME" \
  --output json
```

Inspect each route's destination CIDR, target, and state. Look for:

* A missing route to the destination network.

* A more-specific route overriding a default route.

* A route in `blackhole` state.

* A route pointing to the wrong peering connection, Transit Gateway, NAT Gateway, or gateway.

* Missing return routes in a connected VPC or on-premises network.

AWS routing uses longest-prefix matching when multiple applicable routes exist. A more-specific route can therefore take precedence over a default route.

### 8.3 Inspect network ACLs

```bash
aws ec2 describe-network-acls \
  --filters \
    "Name=association.subnet-id,Values=subnet-REPLACE_ME" \
  --output json
```

Check the inbound and outbound rules for the source and destination CIDRs, protocol, and ports. Remember that network ACLs are stateless and evaluate rules by rule number; the first matching rule determines the outcome.

A common mistake is allowing TCP port 443 inbound but forgetting the return traffic requirements in a stateless ACL. Ephemeral source ports may be required for response traffic, depending on the connection and path.

### 8.4 Use a packet-path checklist

For a TCP connection from an application subnet to a database subnet, verify:

* The destination IP is correct.

* The source subnet has a valid route to the destination.

* Intermediate gateways or network appliances have the necessary routes.

* The destination subnet has a valid return route.

* The destination security group allows inbound TCP on the database port from the intended source.

* The source security group permits the required outbound traffic.

* Applicable network ACLs allow both request and response traffic.

* The database is listening and the host-level firewall allows the connection.

This sequence helps distinguish network configuration failures from problems inside the destination instance.

### 9\. DNS diagnostics

DNS failures often look like network failures. An application may be healthy, its security groups may be correct, and its subnet routes may be valid, but the client may be connecting to the wrong IP address—or may be unable to resolve the hostname at all.

### 9.1 Diagnose from the workload first

On Linux, run:

```bash
# Resolve the hostname
getent ahosts api.internal.example.com

# Inspect DNS responses
dig api.internal.example.com A
dig api.internal.example.com AAAA

# Test TCP connectivity independently of the application client
nc -vz api.internal.example.com 443

# Test the application endpoint
curl -v --connect-timeout 5 \
  https://api.internal.example.com/
```

These commands answer different questions:

* `getent` checks name resolution using the system's configured name-service mechanisms.

* `dig` shows DNS records and response details.

* `nc` tests whether a TCP connection can be established.

* `curl` tests the HTTP/TLS path and exposes more application-protocol details.

On Windows, use:

```powershell
Resolve-DnsName api.internal.example.com
Test-NetConnection api.internal.example.com -Port 443
curl.exe -v --connect-timeout 5 https://api.internal.example.com/
```

### 9.2 Inspect Route 53 Resolver query logs

VPC Resolver query logging can record DNS queries originating from selected VPCs, including the requested name, record type, response code, and response data. It can also cover queries handled through supported inbound and outbound Resolver endpoints.

Useful response codes include:

* `NOERROR` — the DNS operation succeeded; inspect the returned records to verify the address is correct.

* `NXDOMAIN` — the queried name does not exist according to the responding DNS server.

* `SERVFAIL` — the resolver failed to complete the query.

Query logs do not necessarily record every lookup: resolver caching means repeated requests may be answered without a new logged query.

If the DNS result is wrong, check:

* The record in the public or private hosted zone.

* The hosted zone's VPC associations.

* The VPC DNS attributes.

* Resolver rules and forwarding endpoints.

* Record TTL and cached responses.

* Whether the client is using the expected DNS server.

For split-horizon DNS, the same hostname may legitimately resolve to different IP addresses inside and outside the VPC.

Reference: [Route 53 Resolver query logging](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs.html?utm_source=chatgpt.com).

### 10\. Traffic Mirroring

VPC Traffic Mirroring copies selected network traffic from supported network interfaces and sends it to a monitoring appliance. The copied traffic can be inspected with tools such as Wireshark or `tcpdump` on the receiving appliance.

Unlike Flow Logs, which summarize flows, Traffic Mirroring can preserve packet-level information useful for diagnosing protocol behavior.

Application EC2 instance

Source network interface

Traffic Mirror filter and session

Selected traffic is copied and encapsulated

Monitoring appliance

Packet analysis and inspection

Traffic Mirroring is useful when you need to investigate:

* TCP retransmissions and resets.

* Unexpected protocol exchanges.

* TLS handshake behavior.

* Application timeouts where flow metadata is insufficient.

* Differences between requests and responses at the packet level.

However, it has important constraints. For example, it is not supported for IPv6-only subnets; certain traffic types are excluded; and mirrored traffic can be dropped when bandwidth or packet-rate limits are exceeded. Flow Logs do not capture the original mirrored source traffic as ordinary application flows.

Production consideration: Packet captures may contain credentials, personal information, or other sensitive data. Restrict access, minimize capture scope, and set appropriate retention and deletion policies.

### 11\. Diagnosing intermittent connectivity and MTU problems

### 11.1 Symptoms and likely causes

| Symptom                                   | Possible causes                                                                       | Best starting point                                    |
| ----------------------------------------- | ------------------------------------------------------------------------------------- | ------------------------------------------------------ |
| Connection always times out               | Missing route, blocked security group, network ACL, unavailable destination           | Reachability Analyzer, route tables, Flow Logs         |
| Connection is refused immediately         | No listener, host firewall rejection, application not running                         | ss -lntp, application logs                             |
| Small requests work; large transfers hang | MTU mismatch, blocked ICMP, Path MTU Discovery failure                                | MTU tests, packet capture, network ACL review          |
| Some clients work, others fail            | DNS differences, routing asymmetry, source-specific security rules                    | DNS diagnostics, source IP and route comparison        |
| Outbound connections fail intermittently  | NAT Gateway port pressure, upstream timeouts, transient service or application issues | NAT metrics, Flow Logs, application logs               |
| DNS works for some names but not others   | Resolver rules, private hosted zones, DNS firewall policies, caching                  | dig, Resolver query logs, DNS configuration            |
| TCP connects but HTTP returns 5xx         | Application failure, unhealthy backend, upstream dependency                           | Load-balancer metrics, target health, application logs |

Treat these as hypotheses, not conclusions. Confirm each using evidence.

### 11.2 MTU and Path MTU Discovery

The maximum transmission unit (MTU) is the largest IP packet that can traverse a link without exceeding that link's packet-size limit.

EC2 instances support standard 1500-byte frames, and current-generation instance types support jumbo frames up to 9001 bytes. Whether jumbo frames are appropriate depends on the entire network path.

A classic MTU problem looks like this:

* DNS resolution succeeds.

* A TCP connection may establish.

* Small requests work.

* Large responses or file transfers stall.

* Retransmissions occur, and the application eventually times out.

The underlying issue may be that larger packets cannot traverse one link, while the sender does not successfully learn to send smaller packets.

For IPv4, Path MTU Discovery may depend on an ICMP “fragmentation needed” message. For IPv6, the relevant signal is ICMPv6 “Packet Too Big.” If these messages are blocked, packet-size problems can be difficult to diagnose.

Check the interface MTU on Linux:

```bash
ip link show eth0
```

Check path MTU where supported:

```bash
tracepath api.internal.example.com
```

You can also test with `ping` where ICMP is permitted:

```bash
# Linux: IPv4, 1472 bytes of ICMP payload + 28 bytes of headers = 1500
ping -M do -s 1472 <destination-ip>
```

This command is Linux-specific. A failed ping alone does not prove an MTU problem: ICMP may be filtered, the destination may not respond, or the path may have another issue. Try smaller payloads and compare behavior only where the relevant protocol is permitted.

AWS reference: [Path MTU Discovery and network ACLs](https://docs.aws.amazon.com/vpc/latest/userguide/path_mtu_discovery.html?utm_source=chatgpt.com).

### 11.3 Intermittent NAT Gateway problems

For private IPv4 workloads that use a NAT Gateway, inspect metrics such as:

* `ErrorPortAllocation` — failed source-port allocations.

* `PacketsDropCount` — dropped packets.

* `ConnectionAttemptCount` and `ConnectionEstablishedCount` — useful signals when connections fail to establish.

AWS notes that port allocation errors can indicate too many concurrent connections through a NAT Gateway. Investigate connection patterns and consider additional private IPv4 addresses or a suitable egress design when justified.

Retrieve NAT Gateway metrics through CloudWatch:

```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/NATGateway \
  --metric-name ErrorPortAllocation \
  --dimensions \
    Name=NatGatewayId,Value=nat-REPLACE_ME \
  --start-time 2026-10-20T00:00:00Z \
  --end-time 2026-10-20T02:00:00Z \
  --period 300 \
  --statistics Sum
```

The timestamps are illustrative and must be adjusted to the incident window. CloudWatch metric availability and dimensions depend on the resource and Region.

### 12\. Separate network failures from IAM and application failures

A reliable investigation tests each layer independently.

Network layer

Can the client reach the target IP and port? Check routes, security groups, network ACLs, Flow Logs, and Reachability Analyzer.

DNS layer

Does the hostname resolve to the expected IP? Check `dig`, `Resolve-DnsName`, private hosted zones, and Resolver logs.

Application layer

Is the process listening? Check application logs, service health, TLS configuration, HTTP status codes, and target health.

IAM and authorization layer

Can the caller authenticate and perform the requested AWS API action? Check the identity, IAM policies, resource policies, and service-specific authorization.

For example, if an application returns `AccessDenied` while calling S3, a healthy VPC route to S3 does not resolve the authorization problem. The request may have reached AWS successfully but been denied by IAM or an S3 bucket policy.

Conversely, if a private EC2 instance cannot connect to an AWS API because the required endpoint or egress route is missing, IAM changes will not restore connectivity.

To inspect the current AWS identity:

```bash
aws sts get-caller-identity
```

To inspect an instance's attached IAM profile:

```bash
aws ec2 describe-instances \
  --instance-ids i-REPLACE_ME \
  --query \
    'Reservations[].Instances[].IamInstanceProfile' \
  --output json
```

Use application-specific logs and AWS service error messages to determine whether a request was rejected for network reasons, identity authorization, resource authorization, or application logic.

### 13\. Hands-on lab: Investigate realistic connectivity failures

We'll use a small application-to-database architecture. You can use an existing AWS test environment, or create an isolated environment with Pulumi. The exercises focus on investigation, not on building a large network.

### Lab architecture

Application EC2 instance

Private subnet · TCP client

Database EC2 instance

Private subnet · TCP 5432

Both instances should be in a supported, routable path within the test VPC.

Prerequisites:

* AWS CLI v2 configured for the correct account and Region.

* Permission to inspect EC2 networking and create or run network analyses.

* An existing test VPC with two instances, or an environment you can provision.

* A database listener on TCP port 5432 if you want to test a real connection.

* VPC Flow Logs enabled before generating the traffic you intend to investigate.

Cost and safety: Reachability Analyzer analyses are billable. Flow Logs incur log-delivery and storage costs. EC2 instances, public IPv4 addresses, NAT Gateways, and other infrastructure can also incur charges. Use an isolated test environment and clean up resources after the lab.

### Scenario A — A security group blocks the database connection

Symptoms: The application resolves the database address, but TCP connections to port 5432 time out.

Step 1: Test from the application instance:

```bash
nc -vz -w 5 <database-private-ip> 5432
```

Step 2: Inspect the destination security group and verify that its inbound rules permit TCP port 5432 from the application's security group or intended source.

Step 3: Check the Flow Logs for the source and destination IPs, destination port 5432, and `REJECT` action.

Step 4: Run Reachability Analyzer using the application and database network interfaces, with TCP port 5432 as the destination port.

Step 5: If the analysis identifies a security-group rule mismatch, correct the specific rule and rerun the analysis.

Expected outcome: The analyzer identifies the modeled blocker, and the path becomes reachable after the intended security rule is applied. A live connection should then be tested separately.

### Scenario B — A route is missing

Symptoms: Two VPCs are intended to communicate through VPC peering or Transit Gateway, but connections fail.

Step 1: Inspect the source and destination subnet route tables.

Step 2: Verify that the source route points to the correct connection or gateway for the destination CIDR.

Step 3: Verify the return route in the destination VPC.

Step 4: Inspect the relevant peering connection or Transit Gateway attachment and routes.

Step 5: Run Reachability Analyzer for the intended path where the resource types and path are supported.

Expected outcome: You identify the missing or incorrect route and restore the intended path without adding an overly broad route.

### Scenario C — DNS resolves to the wrong destination

Symptoms: A service hostname resolves successfully, but connections reach the wrong backend or fail only in one VPC.

Step 1: Run:

```bash
dig api.internal.example.com A
dig api.internal.example.com AAAA
```

Step 2: Compare the returned addresses with the expected private IPs or load-balancer addresses.

Step 3: Inspect the relevant private hosted zone, VPC association, and Resolver rules.

Step 4: Review Resolver query logs if enabled, accounting for cached responses.

Step 5: Test the correct IP directly to separate DNS behavior from TCP connectivity.

Expected outcome: You identify a DNS record, association, forwarding, or caching issue rather than changing unrelated security-group rules.

### Scenario D — Connections fail during large transfers

Symptoms: Small HTTP responses work, but large downloads stall or TLS connections intermittently time out.

Step 1: Check interface MTUs on both endpoints.

Step 2: Test the path MTU using suitable operating-system tools.

Step 3: Review network ACL rules that may block Path MTU Discovery messages.

Step 4: If necessary, capture packets using an appropriate packet-capture method or Traffic Mirroring on a supported source.

Step 5: Compare retransmissions and packet sizes, and verify that the end-to-end path supports the selected MTU.

Expected outcome: You determine whether packet-size constraints or blocked ICMP messages explain the failure, instead of treating every timeout as a routing issue.

### Scenario E — An AWS API request returns `AccessDenied`

Symptoms: The application can establish network connections, but its call to an AWS service fails with an authorization error.

Step 1: Verify the active identity with `aws sts get-caller-identity` in the same execution context.

Step 2: Inspect the instance role, workload identity, or other credential source used by the application.

Step 3: Review identity policies, resource policies, endpoint policies where applicable, and service-specific authorization requirements.

Step 4: Use the relevant AWS authorization diagnostics and service logs.

Expected outcome: You distinguish authorization failure from network failure and avoid unnecessary changes to routes or security groups.

### 14\. Pulumi: Enable Flow Logs for a VPC

For repeatable infrastructure, Flow Logs should be managed alongside the VPC. The following is a focused Pulumi Python resource example that assumes the VPC, CloudWatch log group, and Flow Logs delivery role already exist.

Install the provider:

```bash
python -m pip install pulumi pulumi-aws
```

Add the following to your Pulumi program:

```python
import pulumi
import pulumi_aws as aws

config = pulumi.Config()

vpc_id = config.require("vpcId")
log_group_name = config.require("flowLogGroupName")
flow_log_role_arn = config.require("flowLogRoleArn")

flow_log = aws.ec2.FlowLog(
    "vpc-flow-logs",
    resource_id=vpc_id,
    resource_type="VPC",
    traffic_type="ALL",
    log_destination_type="cloud-watch-logs",
    log_destination=log_group_name,
    iam_role_arn=flow_log_role_arn,
    tags={
        "Purpose": "VPC troubleshooting",
        "ManagedBy": "Pulumi",
    },
)

pulumi.export("flowLogId", flow_log.id)
```

Configure the existing resources:

```bash
pulumi config set vpcId vpc-REPLACE_ME
pulumi config set flowLogGroupName /aws/vpc/flow-logs
pulumi config set flowLogRoleArn \
  arn:aws:iam::123456789012:role/VPCFlowLogsRole
```

Then preview and deploy:

```bash
pulumi preview
pulumi up
```

Verify the resulting Flow Log:

```bash
aws ec2 describe-flow-logs \
  --filter "Name=resource-id,Values=vpc-REPLACE_ME"
```

The CloudWatch log destination must be configured with the appropriate permissions. The role must trust the Flow Logs delivery service and have the necessary CloudWatch Logs permissions; the Pulumi deployment identity must also be authorized to pass the role.

This example deliberately reuses existing logging resources rather than silently creating IAM roles or changing permissions. For a complete reusable component, manage the log group, retention policy, delivery role, and Flow Log together, with appropriate protection and cleanup behavior.

### 15\. Production troubleshooting runbook

Use the following order during a real incident.

* Establish the exact failure. Record source, destination, protocol, port, timestamp, error message, and whether the issue affects all clients or only some.

* Validate DNS. Confirm that the hostname resolves to the expected destination and address family.

* Test the connection. Check TCP establishment separately from TLS and application responses.

* Inspect the network configuration. Verify routes, security groups, network ACLs, gateway attachments, and return paths.

* Gather traffic evidence. Query Flow Logs and relevant CloudWatch metrics for the incident window.

* Analyze modeled reachability. Use Reachability Analyzer to identify supported configuration blockers. Use Network Access Analyzer for broader exposure reviews.

* Investigate packet behavior if needed. Consider MTU tests or Traffic Mirroring when flow metadata is insufficient.

* Separate higher-layer failures. Review application health, operating-system firewalls, TLS errors, IAM authorization, and service-specific logs.

* Validate and document the fix. Re-test the original failure, confirm expected connectivity, record the root cause, and add monitoring or configuration safeguards where appropriate.

### 16\. Security, cost, and operational considerations

* Enable Flow Logs at the narrowest useful scope, or use VPC-level logging when centralized visibility justifies the volume.

* Set CloudWatch log retention intentionally; indefinite retention can create avoidable storage costs.

* Restrict access to network telemetry because IP addresses and traffic patterns can be sensitive.

* Use least-privilege IAM roles for logging, analysis, and remediation.

* Treat Reachability Analyzer and Network Access Analyzer as configuration-analysis tools, not live traffic monitors.

* Run security exposure analyses periodically and after significant routing or security-group changes.

* Use Traffic Mirroring selectively, accounting for packet sensitivity, bandwidth, packet-rate limits, and monitoring infrastructure costs.

* Make route and security changes narrowly scoped; do not resolve a specific connectivity issue by opening broad CIDRs or ports unnecessarily.

* For production networks, document known-good routes, approved paths, expected DNS responses, and service dependencies so that deviations are easier to identify.

### 17\. Official AWS references

![Cloud Notes: AWS VPC](https://images.openai.com/static-rsc-4/0E_LEIYUit48bYC9S6lBXhlL_IpWRGiGE9UTiWFSqgKOcmlr0GDNIw6R75aZT5i7NBZGXgzaZomzSYCPcZWk6FLHbEyNioGoM_77K4Q9ZBbUNfGrXw47SAUV-agFG0flcZZK0cbNO7cjpDy52TGDhiHTlqBGx-4NmHygBGSO8FVdLyjE7sKIX25jQe7NGULL?purpose=fullsize)

VPC Flow Logs

Record formats, limitations, destinations, and troubleshooting.

[AWS documentation](https://docs.aws.amazon.com/vpc/latest/userguide/flow-logs.html?utm_source=chatgpt.com)

![Getting started with Reachability Analyzer - Amazon Virtual Private Cloud](https://images.openai.com/static-rsc-4/B3OncnstrwAH0VQqADNsr7-y6KRrzM_aeSmlz_aaVCgj7NDmsE0A8HpPy-ljVq752OG4IaaHR8Ru8l1r_45y9c5LWdgv4c1XD5Riw3zySv7dnt1zxHazSqljAHqIV_krQrmuDb7R_w4vCJF4Pu2tXS9xTM46Ww6r0fgY_WTmvtAYeSRl52V7hHKih9dY-rzL?purpose=fullsize)

Reachability Analyzer

Path creation, analysis, explanation codes, and CLI usage.

[AWS documentation](https://docs.aws.amazon.com/vpc/latest/reachability/what-is-reachability-analyzer.html?utm_source=chatgpt.com)

![New – Amazon VPC Network Access Analyzer | AWS News Blog](https://images.openai.com/static-rsc-4/6ymxwB5O5ykJyP0euakOygnREf0zpdyNkWXCPx2uudz_dL77ZiWzrhfJbz5-YSu6G-0HyaH1Ppe0zkSl8g8s1eW43z0SGbODZzTfVcRoDF0UbQTE-ZWWgjpNbta-yKTejepn3FAe8GYiRIPSBLLI6dv9o9y12P7IutZTEI8ydnXG4G9J_iHUDXI7Bhb7Pp0t?purpose=fullsize)

Network Access Analyzer

Network access scopes, findings, and analysis constraints.

[AWS documentation](https://docs.aws.amazon.com/vpc/latest/network-access-analyzer/?utm_source=chatgpt.com)

![How to automatically parse Route 53 Resolver query logs | Networking & Content Delivery](https://images.openai.com/static-rsc-4/n_XLX3RqL5ttCv-ZMygWZWaNFhojLyWPi4Is_lb_kwUBkw-ikK_KmFOFvxmQ7hpSBqQPlWjH_bQK7CA0u0ixMxAzbaPVOA0Ijiu2djARKW7rDAM4IRhc3qM2Qr_wigkCSFhARE-HY5KTUKMLQ5AYhpN7fQ0fkzicY8UUO29tL6ZvDhIoFUQOFLuwkEV6_ZW_?purpose=fullsize)

DNS diagnostics

Resolver query logging and DNS response details.

[AWS documentation](https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/resolver-query-logs.html?utm_source=chatgpt.com)

![Traffic Mirroring example configuration scenarios - Amazon Virtual Private Cloud](https://images.openai.com/static-rsc-4/GtVAfKf159ahH_rvymJcYDbvXaFOBeqt2Eivhuw4ukDAXPsX4essS2RJ17fEd6Kz0zONyKJjA9SrKJFolYEI7SLLXvYXv3Hm9wYktJkHh7l5Fjq4FCWy2E-zV5GzIGVYGMhf-JvXlYZ8zdV2S4c8mEQJcGYAhTh1AgCJO2X9uNWaKUtZBrmUKabJIuQvmxIy?purpose=fullsize)

Traffic Mirroring

Packet inspection architecture, session configuration, and limitations.

[AWS documentation](https://docs.aws.amazon.com/vpc/latest/mirroring/?utm_source=chatgpt.com)

That completes Module 12. The central operational principle is to combine configuration analysis, traffic telemetry, live connection tests, and application evidence. No single AWS networking tool can prove that every layer of a service is functioning correctly.
