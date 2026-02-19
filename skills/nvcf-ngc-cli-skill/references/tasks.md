# NGC Cloud Function Task Reference

Detailed reference for managing batch tasks via NGC CLI.

Tasks are batch jobs that run to completion on GPU resources. Unlike functions (which handle requests), tasks run a container/helm chart once and terminate.

## Creating Tasks

### Basic container task

```bash
ngc cf task create \
  --name <task-name> \
  --container-image <org>/[<team>/]<image>:<tag> \
  --gpu-specification <gpu>:<instance_type>[:<backend>][:<cluster_1,cluster_2>]
```

### Full options

```bash
ngc cf task create \
  --name <task-name> \
  --container-image <image> \
  --gpu-specification <spec> \
  [--description "<description>"] \
  [--container-args "<args>"] \
  [--container-environment-variable <key:value>] \
  [--secret <name:value>] \
  [--model <model>] \
  [--resource <resource>] \
  [--tag <tag>] \
  [--max-runtime-duration <nD><nH><nM><nS>] \
  [--max-queued-duration <nD><nH><nM><nS>] \
  [--termination-grace-period-duration <nD><nH><nM><nS>] \
  [--result-handling-strategy UPLOAD|NONE] \
  [--result-location <path>] \
  [--configuration-file <values.yaml>] \
  [--configuration <json>] \
  [--set <key=value>]
```

### GPU specification format

```
<gpu>:<instance_type>[:<backend>][:<cluster_1,cluster_2>]
```

Examples:
- `L40:gl40_1.br20_2xlarge` - L40 GPU with specific instance type
- `A100:ga100_1.br20_4xlarge:GFN` - A100 on GFN backend
- `T10:g6.full:GFN` - T10 on GFN
- `L40:gl40_1.br20_2xlarge::cluster-us-west,cluster-us-east` - Specific clusters

### Duration format

Durations use ISO 8601 format: `[nD][nH][nM][nS]`
- `1H` - 1 hour
- `30M` - 30 minutes
- `1H30M` - 1 hour 30 minutes
- `1D12H` - 1 day 12 hours

### Helm chart task

```bash
ngc cf task create \
  --name <task-name> \
  --helm-chart <org>/[<team>/]<chart>:<tag> \
  --gpu-specification <spec> \
  [--configuration-file <values.yaml>] \
  [--set <key=value>]
```

## Listing and Viewing Tasks

```bash
# List all tasks
ngc cf task list

# Get task details
ngc cf task info <task-id>
```

## Task Status Values

| Status | Description |
|--------|-------------|
| `QUEUED` | Waiting for resources |
| `RUNNING` | Currently executing |
| `COMPLETED` | Finished successfully |
| `CANCELED` | Manually canceled |
| `ERRORED` | Failed with error |
| `EXCEEDED_MAX_RUNTIME_DURATION` | Timed out |

## Monitoring Tasks

### View task events

```bash
ngc cf task events <task-id>
```

Shows status transitions and error messages.

Example output:
```
+--------------------------------------+--------------------------+------------------------------------------+
| Event Id                             | Created At               | Message                                  |
+--------------------------------------+--------------------------+------------------------------------------+
| 21027187-9426-4b26-b907-c5432943ff7f | 2024-10-19T10:13:46.213Z | Changing status from 'QUEUED' to         |
|                                      |                          | 'ERRORED' with error 'Capacity not       |
|                                      |                          | available at this time'                  |
+--------------------------------------+--------------------------+------------------------------------------+
```

### View task logs

```bash
ngc cf task logs <task-id>
```

### View task results

```bash
ngc cf task results <task-id>
```

## Instance Management

```bash
# List task instances
ngc cf task instance list <task-id>

# Get instance logs
ngc cf task instance logs <task-id> \
  --instance-id <instance-id> \
  [--pod-name <pod>] \
  [--container-name <container>]

# Execute command in running task
ngc cf task instance execute <task-id> \
  --instance-id <instance-id> \
  --pod-name <pod> \
  --container-name <container> \
  --command "<command>"
```

## Managing Tasks

### Cancel a running task

```bash
ngc cf task cancel <task-id>
```

### Delete a task

```bash
ngc cf task delete <task-id>
```

### Update task secrets

```bash
ngc cf task update-secret <task-id> \
  --secret <name:value>
```

## Telemetry

Configure custom telemetry endpoints for task monitoring:

```bash
ngc cf task create \
  --name <task-name> \
  --container-image <image> \
  --gpu-specification <spec> \
  --metrics-telemetry-id <uuid> \
  --logs-telemetry-id <uuid> \
  --traces-telemetry-id <uuid>
```

## Common Patterns

### Get task ID from list

```bash
ngc cf task list --format_type json | jq -r '.[] | select(.name=="my-task") | .id'
```

### Wait for task completion

```bash
while true; do
  STATUS=$(ngc cf task info <task-id> --format_type json | jq -r '.status')
  echo "Status: $STATUS"
  if [[ "$STATUS" == "COMPLETED" || "$STATUS" == "ERRORED" || "$STATUS" == "CANCELED" ]]; then
    break
  fi
  sleep 30
done
```

### List tasks as JSON

```bash
ngc cf task list --format_type json
```

### Check if task is running

```bash
ngc cf task info <task-id> --format_type json | jq -r '.status'
```
