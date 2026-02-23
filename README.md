# RunAgents

**Deploy AI agents that act securely.** RunAgents is a platform for deploying and orchestrating AI agents with secure, policy-driven access to external tools and services.

- **Identity Propagation** — user identity flows from client → agent → tool
- **Policy-Driven Access** — fine-grained allow/deny rules, auto-binding, capability enforcement
- **Just-In-Time Approvals** — high-risk tool access pauses for admin sign-off with TTL expiry
- **LLM Gateway** — unified OpenAI-compatible endpoint for all model providers

## Documentation

**[docs.runagents.io](https://docs.runagents.io)**

## Install the CLI

```bash
# macOS / Linux
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh

# npm
npm install -g @runagents/cli

# Homebrew
brew tap runagents-io/tap && brew install runagents
```

## Quick Start

```bash
# Configure
runagents config set endpoint https://api.runagents.io
runagents config set api-key YOUR_API_KEY

# Seed starter resources
runagents starter-kit

# Deploy an agent
runagents deploy --name my-agent --file agent.py --tool echo-tool --model openai/gpt-4o-mini

# Check runs
runagents runs list
```

## Get Access

Email **[try@runagents.io](mailto:try@runagents.io)** to request a free trial.

## License

Apache 2.0
