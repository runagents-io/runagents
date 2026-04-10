# Installation

The RunAgents CLI lets you manage your agents, tools, model providers, runs, and approvals from the terminal.

## Python (pip) — Recommended

If you use Python, `pip install runagents` is the easiest way. It installs the CLI, the Python SDK, and the agent runtime in one command.

```bash
pip install runagents
```

The `runagents` command is available immediately. The Python SDK (Client, Agent, `@tool`, local dev) is documented at [Python SDK →](../sdk/index.md)

---

## One-line install (macOS / Linux)

Binary-only install — no Python required.

```bash
curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
```

Override the install directory:

```bash
INSTALL_DIR=~/.local/bin curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh
```

## npm

Current version: **1.3.0**

```bash
npm install -g @runagents/cli
```

Or run without installing:

```bash
npx @runagents/cli version
```

## Download Binary

Pre-built binaries for every platform — no dependencies required.

=== "macOS (Apple Silicon)"

    ```bash
    curl -sL https://runagents-releases.s3.amazonaws.com/cli/latest/runagents_darwin_arm64.tar.gz | tar xz
    sudo mv runagents /usr/local/bin/
    ```

=== "macOS (Intel)"

    ```bash
    curl -sL https://runagents-releases.s3.amazonaws.com/cli/latest/runagents_darwin_amd64.tar.gz | tar xz
    sudo mv runagents /usr/local/bin/
    ```

=== "Linux (x86_64)"

    ```bash
    curl -sL https://runagents-releases.s3.amazonaws.com/cli/latest/runagents_linux_amd64.tar.gz | tar xz
    sudo mv runagents /usr/local/bin/
    ```

=== "Linux (ARM64)"

    ```bash
    curl -sL https://runagents-releases.s3.amazonaws.com/cli/latest/runagents_linux_arm64.tar.gz | tar xz
    sudo mv runagents /usr/local/bin/
    ```

=== "Windows"

    Download [`runagents_windows_amd64.zip`](https://runagents-releases.s3.amazonaws.com/cli/latest/runagents_windows_amd64.zip),
    extract `runagents.exe`, and place it somewhere on your `PATH`.

=== "Debian / Ubuntu (.deb)"

    ```bash
    curl -sLO https://runagents-releases.s3.amazonaws.com/cli/latest/runagents_latest_linux_amd64.deb
    sudo dpkg -i runagents_latest_linux_amd64.deb
    ```

=== "RHEL / Fedora (.rpm)"

    ```bash
    curl -sLO https://runagents-releases.s3.amazonaws.com/cli/latest/runagents_latest_linux_amd64.rpm
    sudo rpm -i runagents_latest_linux_amd64.rpm
    ```

---

## Verify Installation

```bash
runagents version
```

```
runagents version 1.3.0
```

---

## Configuration

Configure the CLI with your API endpoint and key:

```bash
runagents config set endpoint https://api.runagents.io
runagents config set api-key YOUR_API_KEY
runagents config set namespace default
runagents config set assistant-mode external
```

Set `assistant-mode` to `runagents` only if you want built-in `runagents copilot` commands.

Get your API key from the RunAgents console under **Settings**.

Verify your configuration:

```bash
runagents config get
```

```
Endpoint: https://api.runagents.io
API Key:  sk-****...****1234
```

Configuration is stored in `~/.runagents/config.json`.

## Environment Variables

| Variable | Description |
|----------|-------------|
| `RUNAGENTS_ENDPOINT` | API endpoint URL |
| `RUNAGENTS_API_KEY` | API key for authentication |
| `RUNAGENTS_NAMESPACE` | Workspace namespace header used by API requests |
| `RUNAGENTS_ASSISTANT_MODE` | Assistant mode override: `external`, `runagents`, or `off` |

## Shell Completion

=== "Bash"

    ```bash
    runagents completion bash > /etc/bash_completion.d/runagents
    ```

=== "Zsh"

    ```bash
    runagents completion zsh > "${fpath[1]}/_runagents"
    ```

=== "Fish"

    ```bash
    runagents completion fish > ~/.config/fish/completions/runagents.fish
    ```

=== "PowerShell"

    ```powershell
    runagents completion powershell | Out-String | Invoke-Expression
    ```

---

!!! tip "Need an API key?"
    [Sign up for free](https://try.runagents.io) and we'll get you set up within 24 hours.
