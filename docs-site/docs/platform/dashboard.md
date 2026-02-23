# Dashboard

The **Dashboard** is the home screen of the RunAgents Console. It provides an at-a-glance overview of your platform's health, resource counts, active runs, and pending approvals -- everything you need to stay on top of your AI agent fleet.

---

## First Visit: Welcome Hero

When your platform has no resources yet (no agents, tools, or models registered), the Dashboard displays a **welcome hero** card with two options:

- **Deploy Hello World Agent** -- Seeds a starter kit (a built-in echo tool and a playground model provider) and walks you through deploying a sample agent in three clicks. No external API keys or accounts required.
- **I have my own code** -- Takes you directly to the deploy wizard so you can upload your own agent source code.

!!! tip "Get started in under a minute"
    Click **Deploy Hello World Agent** to experience the full deploy flow -- upload, wire, deploy -- with zero configuration. The starter kit provides everything you need.

Once any resource exists on the platform, the welcome hero is replaced by the standard dashboard view.

---

## Summary Cards

The top of the Dashboard shows five summary cards that link to their respective sections:

| Card | What it shows | Links to |
|------|--------------|----------|
| **Tools** | Total number of registered tools | Tools page |
| **Agents** | Running agents / total agents | Agents page |
| **Active Runs** | Number of currently executing runs (plus paused count if any) | Agents page |
| **Identity Providers** | Number of configured identity providers | Identity page |
| **Pending Requests** | Access requests awaiting admin review | Approvals page |

Cards that need attention (pending requests, paused runs) are highlighted with a visual indicator.

---

## Getting Started Checklist

When the platform has some resources but setup is incomplete, the Dashboard displays a **Getting Started** checklist:

1. **Register a Tool** -- create at least one tool for your agents to call
2. **Deploy an Agent** -- deploy your first AI agent
3. **Set up identity provider** *(optional)* -- configure JWT-based authentication for client applications

Each step shows a green checkmark when complete and a **Start** link when pending. The checklist disappears once all required steps are done.

---

## Runs Awaiting Approval

If any active runs are paused because they need admin approval to access a restricted tool, a **Runs Awaiting Approval** section appears. Each row shows:

- The run's current status
- The agent that initiated the run
- The user identity associated with the run
- A **Review** link that navigates to the run detail page

---

## Pending Approvals

When there are pending access requests (agents requesting access to tools with Critical access control), a **Pending Approvals** section shows up to five recent requests. Each row displays:

- The requesting user
- The target tool
- The agent making the request
- A **Review** link to the approval detail

---

## Sidebar Navigation

The Console sidebar is organized into three sections:

| Section | Pages |
|---------|-------|
| **Overview** | Dashboard |
| **Platform** | Agents, Tools, Models, Identity |
| **Governance** | Approvals |

The currently active page is highlighted in the sidebar. All navigation is one click away from any page.

---

## What's Next

| Goal | Where to go |
|------|------------|
| Deploy your first agent | [Deploying Agents](deploying-agents.md) |
| Register an external API | [Registering Tools](registering-tools.md) |
| Configure an LLM provider | [Model Providers](model-providers.md) |
| Set up user authentication | [Identity Providers](identity-providers.md) |
| Review access requests | [Approvals](approvals.md) |
