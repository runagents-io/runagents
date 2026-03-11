"""
deploy.py — One-shot deploy: register tools, deploy agent, print invoke URL.

Usage:
    python deploy.py

After deploying, apply policy YAML to enable Restricted tools:
    kubectl apply -f policy/employee-directory-binding.yaml
    kubectl apply -f policy/compensation-binding.yaml

Or use the runagents CLI / console to create PolicyBindings.
"""

import subprocess
import sys
import time

from runagents import Client
from runagents.config import load_config

AGENT_NAME = "hr-assistant"
NAMESPACE  = "default"

# Tool definitions — replace base_url with your real API endpoints.
# For local testing with mock_tools/server.py, use http://localhost:9090
# (but that won't work for a cloud deployment — tools need reachable URLs).
TOOLS = [
    {
        "name":        "hr-knowledge-base",
        "base_url":    "https://hr-api.your-company.com",   # ← replace
        "description": "HR policy and procedures knowledge base. GET /articles/search",
        "auth_type":   "None",
        "port":        443,
        "scheme":      "HTTPS",
    },
    {
        "name":        "employee-directory",
        "base_url":    "https://hr-api.your-company.com",   # ← replace
        "description": "Employee directory. GET /employees/{id}",
        "auth_type":   "APIKey",    # platform injects API key from a K8s Secret
        "port":        443,
        "scheme":      "HTTPS",
    },
    {
        "name":        "compensation-api",
        "base_url":    "https://hr-api.your-company.com",   # ← replace
        "description": "Compensation management. POST /compensation/{id}",
        "auth_type":   "OAuth2",    # platform injects per-user OAuth2 token
        "port":        443,
        "scheme":      "HTTPS",
    },
]

SYSTEM_PROMPT = (
    "You are an HR assistant. Help HR analysts look up policies (search_knowledge_base), "
    "find employee information (get_employee), and process compensation changes "
    "(update_compensation — requires admin approval). Always verify employee ID before "
    "making changes. Compensation changes are audited with the requester's identity."
)

LLM_CONFIGS = [{"provider": "openai", "model": "gpt-4o-mini", "role": "default"}]


def main():
    cfg = load_config()
    print(f"Deploying to: {cfg.endpoint}")
    print()

    client = Client()

    # --- 1. Register tools ---
    print("Registering tools...")
    for t in TOOLS:
        try:
            client.tools.create(**t)
            print(f"  {t['name']}: registered ✓")
        except Exception as e:
            if "already exists" in str(e).lower() or "conflict" in str(e).lower():
                print(f"  {t['name']}: already exists")
            else:
                print(f"  {t['name']}: {e}", file=sys.stderr)
                sys.exit(1)

    print()

    # --- 2. Deploy agent ---
    source_files = {}
    for fname in ["agent.py", "tools.py"]:
        try:
            source_files[fname] = open(fname).read()
        except FileNotFoundError:
            print(f"Error: {fname} not found. Run from langchain-enterprise/ directory.", file=sys.stderr)
            sys.exit(1)

    print(f"Deploying '{AGENT_NAME}'...")
    try:
        client.agents.deploy(
            name=AGENT_NAME,
            source_files=source_files,
            system_prompt=SYSTEM_PROMPT,
            required_tools=[t["name"] for t in TOOLS],
            llm_configs=LLM_CONFIGS,
            requirements=(open("requirements.txt").read() if open("requirements.txt") else ""),
            entry_point="agent.py",
        )
        print("  Deploy accepted ✓")
    except Exception as e:
        print(f"  Deploy failed: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 3. Wait for Running ---
    print("\nWaiting for agent to be Running", end="", flush=True)
    deadline = time.time() + 120
    ns = cfg.namespace or NAMESPACE
    while time.time() < deadline:
        try:
            info = client.agents.get(ns, AGENT_NAME)
            if info.status == "Running":
                print(" ✓")
                break
            elif info.status == "Failed":
                print(f"\nFailed. Check console for build logs.")
                sys.exit(1)
        except Exception:
            pass
        print(".", end="", flush=True)
        time.sleep(5)
    else:
        print("\nTimeout. Check console.")
        sys.exit(1)

    # --- 4. Print next steps ---
    endpoint   = cfg.endpoint.rstrip("/")
    invoke_url = f"{endpoint}/api/agents/{ns}/{AGENT_NAME}/invoke"

    print()
    print("=" * 60)
    print(f"Agent deployed: {AGENT_NAME}")
    print()
    print("Next: apply PolicyBindings to enable Restricted tools:")
    print("  kubectl apply -f policy/employee-directory-binding.yaml")
    print("  kubectl apply -f policy/compensation-binding.yaml")
    print()
    print("Test (knowledge base — works immediately, Open access):")
    print(f'  curl -X POST {invoke_url} \\')
    print(f'    -H "Authorization: Bearer {cfg.api_key or "YOUR_KEY"}" \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"message": "What is the maternity leave policy?"}}\' ')
    print()
    print("Test (compensation — will trigger approval after binding applied):")
    print(f'  curl -X POST {invoke_url} \\')
    print(f'    -H "Authorization: Bearer {cfg.api_key or "YOUR_KEY"}" \\')
    print(f'    -H "Content-Type: application/json" \\')
    print(f'    -d \'{{"message": "Update salary for EMP-042 to $95000"}}\' ')
    print()
    print("Monitor approvals:")
    print("  runagents approvals list")
    print("  runagents approvals approve <action-id>")
    print("=" * 60)


if __name__ == "__main__":
    main()
