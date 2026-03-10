# LLM NIM Chat Example

Interactive terminal chat with an LLM NIM deployed on self-hosted NVCF.

## Prerequisites

- Python 3.8 or later
- `openai` package: `pip install openai`
- A running LLM NIM function on a self-hosted NVCF cluster (see [Deploying an LLM NIM on Self-Hosted NVCF](https://docs.nvidia.com/cloud-functions/))

## Quick Start

Pass your cluster details as command-line flags:

```bash
python3 llm_chat.py \
    --gateway  a1b2c3d4.us-east-1.elb.amazonaws.com \
    --function-id  <function-uuid> \
    --version-id   <version-uuid> \
    --model        meta/llama-3.1-8b-instruct \
    --api-key      nvapi-...
```

Or set environment variables and run without flags:

```bash
export NVCF_GATEWAY="a1b2c3d4.us-east-1.elb.amazonaws.com"
export NVCF_FUNCTION_ID="<function-uuid>"
export NVCF_FUNCTION_VERSION_ID="<version-uuid>"
export NVCF_MODEL="meta/llama-3.1-8b-instruct"
export NVCF_API_KEY="nvapi-..."
python3 llm_chat.py
```

## Chat Commands

| Command | Description |
|---------|-------------|
| `/help` | Show available commands |
| `/clear` | Clear conversation history (start fresh context window) |
| `/history` | Print the full conversation so far |
| `/stats` | Show cumulative token usage for the session |
| `/system <msg>` | Replace the system prompt mid-session |
| `/exit` | Quit |

## Supported Models

The script works with any LLM NIM that exposes an OpenAI-compatible `/v1/chat/completions`
endpoint. Pass the model name via `--model` to match the `NIM_MODEL_NAME` used when
creating the function.

| Model | GPU | VRAM |
|-------|-----|------|
| `meta/llama-3.1-8b-instruct` | A10G | ~16 GB |
| `mistralai/mistral-7b-instruct-v0.3` | A10G | ~14 GB |
| `microsoft/phi-3-mini-4k-instruct` | A10G | ~8 GB |
| `meta/llama-3.1-70b-instruct` | H100 / L40S | ~140 GB |

## Options

```
--gateway       Envoy Gateway address — ELB hostname or IP (env: NVCF_GATEWAY)
--function-id   NVCF function UUID (env: NVCF_FUNCTION_ID)
--version-id    NVCF function version UUID (env: NVCF_FUNCTION_VERSION_ID)
--model         Model name as passed to NIM_MODEL_NAME (env: NVCF_MODEL)
--api-key       NVCF user API key (nvapi-...); auto-generated via nvcf-cli if omitted
--system        System prompt (overrides built-in default)
--no-stream     Disable streaming — show full reply at once
```
