# Agent Catalog

The RunAgents **Agent Catalog** is the fastest way to move from platform setup to a real production workflow.

Catalog agents are maintained blueprints that package together:

- agent code
- expected tools
- model defaults
- deployment structure
- a recommended operational pattern

Use the catalog when you want to start from a known-good template instead of building every agent from scratch.

---

## Why the catalog matters

Hello World is still the best path for learning the platform quickly.

The catalog is the better path when you want to:

- deploy a real workflow sooner
- reuse a supported reference pattern
- onboard a team to a concrete agent example
- validate policy, approval, and OAuth behavior against a practical use case

---

## What a catalog agent gives you

A catalog entry typically includes:

- source code ready to deploy
- a clear tool contract
- recommended model configuration
- environment or credential expectations
- deployment instructions
- operational notes for policy, approval, and consent

This makes catalog agents a strong bridge between a demo and a production deployment.

---

## Recommended first catalog example: Google Workspace assistant

The Google Workspace assistant is a strong example of what the catalog is for.

It brings together:

- delegated-user OAuth
- policy-controlled external tool access
- governed writes such as calendar event creation
- operator approvals and user consent
- conversational usage across workspace surfaces

That makes it a much more realistic first production-style workflow than a simple echo demo.

---

## When to use Hello World vs. the catalog

| Path | Best for |
|------|----------|
| **Hello World** | learning the deploy flow in minutes with no external dependencies |
| **Agent Catalog** | standing up a practical workflow with real tools, policy, approval, and OAuth |

Both paths are valuable. They solve different onboarding goals.

---

## Deploying from the catalog

The exact deploy command depends on the catalog agent, but the overall pattern is straightforward:

1. choose the catalog agent that matches your workflow
2. review the required tools and model defaults
3. register or configure the required tools
4. deploy the catalog agent
5. validate policy, approval, and consent behavior end to end

For example, the Google Workspace assistant can be deployed from the catalog and used as the starting point for a governed Google workflow.

---

## Recommended docs path

If you are new to RunAgents:

1. start with [Quickstart](../getting-started/quickstart.md) if you want the fastest possible first deploy
2. continue to [Deploying Agents](deploying-agents.md) for the full deployment model
3. use the catalog when you want a production-shaped starting point such as the Google Workspace assistant
