# Function Invocation Reference

Detailed reference for invoking NVCF functions via HTTP and gRPC.

## Prerequisites

- Function must be deployed and in ACTIVE status
- Personal API Key enabled for Cloud Functions (nvapi-xxx format)

## API Key Handling

**Agent Instructions:** You **must** verify the API key is available in the agent's shell **before** attempting any invocation command. Do not attempt invocation and troubleshoot after failure. Never ask users to provide their API key directly or include literal key values in commands or chat.

### Step 1: Check if API key is set

```bash
[ -n "$NGC_API_KEY" ] && echo "NGC_API_KEY is configured" || echo "NGC_API_KEY is not set"
```

**Do NOT use** commands that could leak the key:
- `echo $NGC_API_KEY` - exposes the key
- `printenv NGC_API_KEY` - exposes the key
- `env | grep NGC` - may expose the key

### Step 2: If not set, try loading from NGC CLI config

The NGC CLI stores the API key in `~/.ngc/config`. Attempt to load it automatically:

```bash
NGC_API_KEY=$(grep -E '^[[:space:]]*apikey[[:space:]]*=' ~/.ngc/config 2>/dev/null | head -1 | sed 's/.*=[[:space:]]*//')
[ -n "$NGC_API_KEY" ] && export NGC_API_KEY && echo "NGC_API_KEY loaded from NGC CLI config" || echo "NGC_API_KEY could not be resolved"
```

This avoids requiring the user to do anything extra if they have already run `ngc config set`.

### Step 3: If still not set, help the user resolve it

If neither method works, **stop and help the user** before proceeding. Explain clearly:

1. **Why**: The `NGC_API_KEY` environment variable is required for function invocation via HTTP/curl. It must be available in the agent's shell session, not just in a separate terminal.

2. **How to fix it persistently** (recommended): Add the export to the shell profile so it is available in all new shell sessions, including the agent's:

   ```bash
   # For zsh (default on macOS):
   echo 'export NGC_API_KEY=nvapi-YOUR_KEY_HERE' >> ~/.zshrc

   # For bash:
   echo 'export NGC_API_KEY=nvapi-YOUR_KEY_HERE' >> ~/.bashrc
   ```

   After editing the profile, the user must restart their IDE (or start a new terminal session) for the change to take effect in the agent's shell.

3. **How to fix it for the current session**: If the user wants to proceed immediately without restarting, they can ask the agent to run the export command directly. The agent should run it without displaying the key value back:

   ```bash
   export NGC_API_KEY=nvapi-<key-provided-by-user>
   ```

   Note: This only lasts for the current agent session and will need to be repeated.

4. **Where to get a key**: Personal API Keys can be generated at https://org.ngc.nvidia.com/setup/personal-keys (ensure the "Cloud Functions" scope is enabled).

### Security guidelines

- **Never** ask users to paste their API key into the chat unprompted
- **Never** echo, print, or log the `$NGC_API_KEY` value
- **Never** run commands that output the key (e.g., `echo $NGC_API_KEY`, `printenv`)
- **Always** use `$NGC_API_KEY` variable reference in commands, not literal values
- **Always** check for key existence using only status-based output (configured/not set)
- **Never** include API keys in command output, logs, or chat messages
- If the user provides a key value for the agent to export, run the export command but do not repeat the key value in any message or output

## Invoke URL Format

```
https://<function-id>.invocation.api.nvcf.nvidia.com/<inference-url-path>
```

The `<inference-url-path>` is the path configured when creating the function via `--inference-url`.

## HTTP Invocation

### Basic invocation with curl

```bash
# Assumes NGC_API_KEY is already set in environment
curl --request POST \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/<url-path>" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{"your": "payload"}'
```

### Invocation with query parameters

```bash
curl --request POST \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/echo?name=John" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "Content-Type: application/json" \
  --data '{"message": "hello"}'
```

### HTTP Streaming (Server-Sent Events)

For functions configured with `--function-type STREAMING`:

```bash
curl --request POST \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/<url-path>" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "Accept: text/event-stream" \
  --header "Content-Type: application/json" \
  --data '{"prompt": "Tell me a story"}' \
  --no-buffer
```

### Targeting a specific version

By default, requests route to the deployed version. To target a specific version, add the header:

```bash
curl --request POST \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/<url-path>" \
  --header "Authorization: Bearer $NGC_API_KEY" \
  --header "NVCF-FUNCTION-ASSET-IDS: <version-id>" \
  --header "Content-Type: application/json" \
  --data '{"your": "payload"}'
```

## Python Invocation

### Basic request

```python
import os
import requests

NGC_API_KEY = os.environ.get("NGC_API_KEY")
if not NGC_API_KEY:
    raise EnvironmentError("NGC_API_KEY environment variable is not set")

FUNCTION_ID = "<function-id>"

response = requests.post(
    f"https://{FUNCTION_ID}.invocation.api.nvcf.nvidia.com/echo",
    headers={
        "Authorization": f"Bearer {NGC_API_KEY}",
        "Content-Type": "application/json"
    },
    json={"message": "hello"}
)
print(response.json())
```

### Streaming response

```python
import os
import requests

NGC_API_KEY = os.environ.get("NGC_API_KEY")
if not NGC_API_KEY:
    raise EnvironmentError("NGC_API_KEY environment variable is not set")

FUNCTION_ID = "<function-id>"

response = requests.post(
    f"https://{FUNCTION_ID}.invocation.api.nvcf.nvidia.com/generate",
    headers={
        "Authorization": f"Bearer {NGC_API_KEY}",
        "Content-Type": "application/json",
        "Accept": "text/event-stream"
    },
    json={"prompt": "Tell me a story"},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## gRPC Invocation

For gRPC functions, use host `grpc.nvcf.nvidia.com:443` with metadata:

| Metadata Key | Value | Required |
|--------------|-------|----------|
| `function-id` | Your function ID | Yes |
| `authorization` | `Bearer nvapi-<token>` | Yes |
| `function-version-id` | Specific version ID | No |

### Python gRPC example

```python
import os
import grpc

NGC_API_KEY = os.environ.get("NGC_API_KEY")
if not NGC_API_KEY:
    raise EnvironmentError("NGC_API_KEY environment variable is not set")

channel = grpc.secure_channel(
    'grpc.nvcf.nvidia.com:443',
    grpc.ssl_channel_credentials()
)

metadata = [
    ('function-id', '<function-id>'),
    ('authorization', f'Bearer {NGC_API_KEY}')
]

# Use your generated stub
stub = YourServiceStub(channel)
response = stub.YourMethod(request, metadata=metadata)
```

## OpenAPI Specification Discovery

Many functions expose an OpenAPI specification. Check for an OpenAPI spec when working with an unfamiliar function.

```bash
# Try these endpoints to discover the API spec
curl -s --request GET \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/openapi.json" \
  --header "Authorization: Bearer $NGC_API_KEY"
```

### Common spec paths

| Path | Framework |
|------|-----------|
| `/openapi.json` | FastAPI, vLLM, most Python frameworks |
| `/swagger.json` | Swagger/OpenAPI 2.0 |
| `/docs` | FastAPI interactive docs (HTML) |
| `/redoc` | ReDoc documentation (HTML) |

### Discovering available endpoints

```bash
curl -s --request GET \
  --url "https://<function-id>.invocation.api.nvcf.nvidia.com/openapi.json" \
  --header "Authorization: Bearer $NGC_API_KEY" | jq '.paths | keys'
```

## Response Headers

NVCF includes useful headers in responses:

| Header | Description |
|--------|-------------|
| `NVCF-REQID` | Unique request ID for debugging |
| `NVCF-STATUS` | Request status |
| `NVCF-FUNCTION-ID` | Function that handled the request |
| `NVCF-FUNCTION-VERSION-ID` | Version that handled the request |

## Error Handling

### Common HTTP status codes

| Code | Meaning | Action |
|------|---------|--------|
| 401 | Unauthorized | Check API key format and permissions |
| 403 | Forbidden | Verify function authorization |
| 404 | Not found | Check function ID and inference URL path |
| 429 | Rate limited | Reduce request rate or request exemption |
| 500 | Server error | Check function logs |
| 503 | Service unavailable | Function may be scaling or unhealthy |

### Debugging failed requests

1. Check the `NVCF-REQID` header in the response
2. Query deployment logs with the request ID:

```bash
ngc cf fn deploy log <function-id>:<version-id> \
  --duration 1H
```

## Troubleshooting

### "Function not found" errors

- Verify the function ID is correct
- Check that the function has an active deployment: `ngc cf fn deploy info <function-id>:<version-id>`

### "Unauthorized" errors

- Ensure your API key starts with `nvapi-`
- Verify the key has Cloud Functions permissions enabled
- Check if you're authorized to invoke the function: `ngc cf fn auth info <function-id>:<version-id>`

### Timeout errors

- Check if the function is healthy: `ngc cf fn instance list <function-id>:<version-id>`
- Review instance logs for errors
- Consider increasing deployment replicas for high load
