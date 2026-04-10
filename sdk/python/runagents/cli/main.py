"""CLI entry point: intercepts ``init`` and ``dev``, delegates rest to Go binary."""

import sys


def main() -> None:
    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        _print_help()
        return

    cmd = args[0]

    if cmd == "init":
        from runagents.cli.init_cmd import run_init
        run_init(args[1:])
    elif cmd == "dev":
        from runagents.cli.dev_cmd import run_dev
        run_dev(args[1:])
    elif cmd == "version" or cmd == "--version":
        from runagents import __version__
        print(f"runagents (Python SDK) {__version__}")
        _delegate_to_go(["version"])
    else:
        _delegate_to_go(args)


def _delegate_to_go(args: list[str]) -> None:
    """Find and exec the Go binary, downloading if needed."""
    import subprocess

    from runagents.cli.binary import ensure_binary

    binary = ensure_binary()
    if binary is None:
        print(
            "Error: Go CLI binary not found.\n"
            "Install it: curl -fsSL https://runagents-releases.s3.amazonaws.com/cli/install.sh | sh",
            file=sys.stderr,
        )
        sys.exit(1)

    result = subprocess.run([str(binary)] + args)
    sys.exit(result.returncode)


def _print_help() -> None:
    print(
        "Usage: runagents <command> [options]\n"
        "\n"
        "Python commands:\n"
        "  init [name]     Scaffold a new agent project\n"
        "  dev             Start local dev server\n"
        "  version         Show version info\n"
        "\n"
        "Platform commands (Go CLI):\n"
        "  deploy          Deploy an agent\n"
        "  agents          Manage agents\n"
        "  catalog         Browse and deploy catalog agents\n"
        "  tools           Manage tools\n"
        "  models          Manage model providers\n"
        "  runs            View agent runs\n"
        "  approvals       Manage access requests\n"
        "  policies        Manage governance policies\n"
        "  approval-connectors  Manage approval routing connectors\n"
        "  identity-providers   Manage workspace identity providers\n"
        "  context         Export assistant/workspace context\n"
        "  analyze         Analyze source code\n"
        "  starter-kit     Seed demo resources\n"
        "  config          View/set configuration\n"
    )


if __name__ == "__main__":
    main()
