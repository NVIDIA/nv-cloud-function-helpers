#!/usr/bin/env python3
"""
Interactive terminal chat with an LLM NIM deployed on self-hosted NVCF.

The script connects to any NIM that exposes an OpenAI-compatible
/v1/chat/completions endpoint via NVCF's self-hosted invocation service.

────────────────────────────────────────────────────────────────────────────
QUICK START

Pass your cluster details as command-line flags:

    python3 llm_chat.py \\
        --gateway  a1b2c3d4.us-east-1.elb.amazonaws.com \\
        --function-id  <function-uuid> \\
        --version-id   <version-uuid> \\
        --model        meta/llama-3.1-8b-instruct \\
        --api-key      nvapi-...

Or set environment variables and run without flags:

    export NVCF_GATEWAY="a1b2c3d4.us-east-1.elb.amazonaws.com"
    export NVCF_FUNCTION_ID="<function-uuid>"
    export NVCF_FUNCTION_VERSION_ID="<version-uuid>"
    export NVCF_MODEL="meta/llama-3.1-8b-instruct"
    export NVCF_API_KEY="nvapi-..."
    python3 llm_chat.py

────────────────────────────────────────────────────────────────────────────
HOW IT CONNECTS

Self-hosted NVCF uses a single load balancer address with Host-header routing.
The script connects to:

    http://<GATEWAY>/v1/chat/completions

with these HTTP headers on every request:

    Host:                invocation.<GATEWAY>   ← routes to the invocation service
    Function-Id:         <function-uuid>        ← identifies which function to call
    Function-Version-Id: <version-uuid>         ← identifies which version
    Authorization:       Bearer <api-key>

This is different from public NVCF, where invocation URLs are function-specific
(https://<function-id>.invocation.api.nvcf.nvidia.com/...).

────────────────────────────────────────────────────────────────────────────
CHOOSING A DIFFERENT MODEL

To use a different NIM, change --model to match the model name passed to
NIM_MODEL_NAME when the function was created. Common examples:

    meta/llama-3.1-8b-instruct       (A10G, ~16 GB VRAM)
    mistralai/mistral-7b-instruct-v0.3  (A10G, ~14 GB VRAM)
    microsoft/phi-3-mini-4k-instruct    (A10G, ~8 GB VRAM)
    meta/llama-3.1-70b-instruct      (H100 / L40S, ~140 GB VRAM)

────────────────────────────────────────────────────────────────────────────
COMMANDS DURING CHAT

    /help       Show this list
    /clear      Clear conversation history (fresh context window)
    /history    Print the full conversation so far
    /stats      Show token usage for the session
    /system     Replace the system prompt mid-session
    /exit       Quit  (also Ctrl-C or Ctrl-D)
────────────────────────────────────────────────────────────────────────────
"""

import argparse
import os
import sys
import textwrap

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai package not found. Run: pip install openai")


# ── ANSI colours (disabled automatically when not writing to a terminal) ───────

def _c(code):
    return code if sys.stdout.isatty() else ""

RESET   = _c("\033[0m")
BOLD    = _c("\033[1m")
DIM     = _c("\033[2m")
CYAN    = _c("\033[36m")
GREEN   = _c("\033[32m")
YELLOW  = _c("\033[33m")
BLUE    = _c("\033[34m")
RED     = _c("\033[31m")


# ── Default system prompt ───────────────────────────────────────────────────────
# Override at runtime with --system "your prompt here" or /system during chat.

DEFAULT_SYSTEM = """\
You are a precise, reliable AI assistant.

ACCURACY RULES:
- If you are not certain of a fact, say so explicitly ("I'm not certain, but...").
  Never present uncertain information as fact.
- For factual or technical questions, give accurate and specific answers.
- For math or logic, show your reasoning step by step.
- When you don't know something, say so — do not guess or make up details.

STYLE:
- Be direct and concise. Avoid filler phrases like "Certainly!" or "Great question!".
- Use plain language. Only use bullet points or headers when they genuinely aid clarity.
- Match the depth of your answer to the complexity of the question.\
"""


# ── Helpers ─────────────────────────────────────────────────────────────────────

def banner(gateway: str, function_id: str, model: str):
    gw_short = gateway if len(gateway) <= 50 else gateway[:47] + "..."
    print(f"""
{BOLD}{CYAN}╔══════════════════════════════════════════════════════════════╗
║  NVCF LLM NIM Chat                                            ║
║  Gateway  : {gw_short:<49}║
║  Function : {function_id:<49}║
║  Model    : {model:<49}║
╚══════════════════════════════════════════════════════════════╝{RESET}
{DIM}Type your message and press Enter. Commands start with /{RESET}
{DIM}/help for a list of commands   |   Ctrl-C or /exit to quit{RESET}
""")


def help_text():
    print(f"""
{BOLD}Available commands:{RESET}
  {CYAN}/help{RESET}            Show this message
  {CYAN}/clear{RESET}           Clear conversation history (fresh context window)
  {CYAN}/history{RESET}         Print the full conversation so far
  {CYAN}/stats{RESET}           Show cumulative token usage this session
  {CYAN}/system <msg>{RESET}    Replace the system prompt (also clears history)
  {CYAN}/exit{RESET}            Quit
""")


def resolve_api_key(cli_key: str | None) -> str:
    """Return API key from: CLI flag > env var > nvcf-cli auto-generate."""
    if cli_key:
        return cli_key
    env = os.environ.get("NVCF_API_KEY")
    if env and env.startswith("nvapi-"):
        return env
    # Fall back to auto-generating via nvcf-cli if it is on the PATH
    import subprocess, shutil
    cli = shutil.which("nvcf-cli") or "./nvcf-cli"
    try:
        result = subprocess.run(
            [cli, "api-key", "generate"],
            capture_output=True, text=True, timeout=15,
            cwd=os.path.dirname(os.path.abspath(__file__)),
        )
        for line in result.stdout.splitlines():
            if "API Key:" in line:
                key = line.split(":", 1)[1].strip()
                print(f"{DIM}[auto-generated API key via nvcf-cli, expires ~24h]{RESET}\n")
                return key
    except Exception:
        pass
    sys.exit(
        f"{RED}No API key found.{RESET}\n"
        "Provide one via --api-key, the NVCF_API_KEY environment variable,\n"
        "or run: ./nvcf-cli api-key generate"
    )


# ── Chat session ─────────────────────────────────────────────────────────────────

class ChatSession:
    def __init__(self, client: OpenAI, model: str, system_prompt: str, stream: bool):
        self.client  = client
        self.model   = model
        self.stream  = stream
        self.history = []          # list of {"role": ..., "content": ...}
        self.system  = system_prompt
        self.total_prompt_tokens     = 0
        self.total_completion_tokens = 0
        self.turn_count = 0

    def _messages(self):
        return [{"role": "system", "content": self.system}] + self.history

    def _send(self, user_input: str):
        self.history.append({"role": "user", "content": user_input})
        self.turn_count += 1
        print(f"\n{BOLD}{GREEN}Assistant ▸{RESET} ", end="", flush=True)
        reply = self._send_streaming() if self.stream else self._send_blocking()
        print()  # newline after response
        self.history.append({"role": "assistant", "content": reply})

    def _send_streaming(self) -> str:
        collected = []
        with self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(),
            max_tokens=1024,
            temperature=0.7,
            stream=True,
        ) as stream:
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta:
                    print(delta, end="", flush=True)
                    collected.append(delta)
        return "".join(collected)

    def _send_blocking(self) -> str:
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=self._messages(),
            max_tokens=1024,
            temperature=0.7,
        )
        content = resp.choices[0].message.content
        width = min(
            os.get_terminal_size().columns if sys.stdout.isatty() else 80, 100
        )
        for para in content.split("\n"):
            if para.strip():
                print(textwrap.fill(para, width=width))
            else:
                print()
        self.total_prompt_tokens     += resp.usage.prompt_tokens
        self.total_completion_tokens += resp.usage.completion_tokens
        return content

    def print_history(self):
        print()
        for msg in self.history:
            if msg["role"] == "user":
                label = f"{BOLD}{BLUE}You{RESET}"
            else:
                label = f"{BOLD}{GREEN}Assistant{RESET}"
            print(f"{label}: {msg['content']}\n")

    def print_stats(self):
        total = self.total_prompt_tokens + self.total_completion_tokens
        print(f"""
{BOLD}Session stats:{RESET}
  Turns              : {self.turn_count}
  Prompt tokens      : {self.total_prompt_tokens}
  Completion tokens  : {self.total_completion_tokens}
  Total tokens       : {total}
  Messages in context: {len(self.history)} (+ system prompt)
""")

    def set_system(self, new_system: str):
        self.system  = new_system
        self.history = []
        print(f"{DIM}System prompt updated. Conversation history cleared.{RESET}\n")

    def clear(self):
        self.history = []
        print(f"{DIM}Conversation history cleared.{RESET}\n")

    def run(self):
        while True:
            try:
                user_input = input(f"{BOLD}{BLUE}You ▸{RESET} ").strip()
            except (EOFError, KeyboardInterrupt):
                print(f"\n{DIM}Bye!{RESET}")
                break

            if not user_input:
                continue

            if user_input.startswith("/"):
                cmd  = user_input.split(None, 1)
                verb = cmd[0].lower()
                if verb in ("/exit", "/quit", "/q"):
                    print(f"{DIM}Bye!{RESET}")
                    break
                elif verb == "/help":
                    help_text()
                elif verb == "/clear":
                    self.clear()
                elif verb == "/history":
                    self.print_history()
                elif verb == "/stats":
                    self.print_stats()
                elif verb == "/system":
                    if len(cmd) < 2 or not cmd[1].strip():
                        print(f"{YELLOW}Usage: /system <new system prompt>{RESET}\n")
                    else:
                        self.set_system(cmd[1].strip())
                else:
                    print(f"{YELLOW}Unknown command '{verb}'. Type /help for options.{RESET}\n")
                continue

            try:
                self._send(user_input)
            except KeyboardInterrupt:
                print(f"\n{DIM}(interrupted){RESET}")
            except Exception as e:
                print(f"\n{RED}Error: {e}{RESET}\n")
                print(
                    f"{DIM}If you see a connection error, check that your gateway "
                    f"address, function ID, and API key are correct.{RESET}\n"
                )


# ── Entry point ──────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Interactive chat with an LLM NIM on self-hosted NVCF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--gateway",
        default=os.environ.get("NVCF_GATEWAY"),
        help="Envoy Gateway address — ELB hostname or IP (env: NVCF_GATEWAY)",
    )
    parser.add_argument(
        "--function-id",
        default=os.environ.get("NVCF_FUNCTION_ID"),
        help="NVCF function UUID (env: NVCF_FUNCTION_ID)",
    )
    parser.add_argument(
        "--version-id",
        default=os.environ.get("NVCF_FUNCTION_VERSION_ID"),
        help="NVCF function version UUID (env: NVCF_FUNCTION_VERSION_ID)",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("NVCF_MODEL", "meta/llama-3.1-8b-instruct"),
        help="Model name as passed to NIM_MODEL_NAME (env: NVCF_MODEL)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="NVCF user API key (nvapi-...); auto-generated via nvcf-cli if omitted (env: NVCF_API_KEY)",
    )
    parser.add_argument(
        "--system",
        default=DEFAULT_SYSTEM,
        help="System prompt",
    )
    parser.add_argument(
        "--no-stream",
        action="store_true",
        help="Disable streaming — show full reply at once",
    )
    args = parser.parse_args()

    # Validate required arguments
    missing = [name for name, val in [
        ("--gateway",     args.gateway),
        ("--function-id", args.function_id),
        ("--version-id",  args.version_id),
    ] if not val]
    if missing:
        parser.error(
            f"Missing required arguments: {', '.join(missing)}\n"
            "Pass them as flags or set the corresponding environment variables.\n"
            "Run with --help for details."
        )

    api_key = resolve_api_key(args.api_key)

    # Build the OpenAI client pointed at the self-hosted NVCF invocation service.
    #
    # Key points:
    #   - base_url is the raw gateway address — this resolves in DNS.
    #     Do NOT use http://invocation.<gateway>/v1 — that subdomain has no DNS record.
    #   - The Host header routes the request to the invocation service via Envoy.
    #   - Function-Id and Function-Version-Id tell the invocation service which
    #     deployed function instance to dispatch to.
    client = OpenAI(
        base_url=f"http://{args.gateway}/v1",
        api_key=api_key,
        default_headers={
            "Host":                f"invocation.{args.gateway}",
            "Function-Id":         args.function_id,
            "Function-Version-Id": args.version_id,
        },
        timeout=120,
    )

    banner(args.gateway, args.function_id, args.model)

    if args.system != DEFAULT_SYSTEM:
        print(f"{DIM}System: {args.system}{RESET}\n")

    session = ChatSession(
        client=client,
        model=args.model,
        system_prompt=args.system,
        stream=not args.no_stream,
    )
    session.run()


if __name__ == "__main__":
    main()
