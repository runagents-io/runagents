# RunAgents v1.4.0: Model Budgets, Safer Edits, and Smoother Operations

_May 12, 2026_

RunAgents `v1.4.0` improves the day-to-day operator experience of running governed agents in production.

This release adds stronger controls for model spend, safer edit flows across the console, faster inventory workflows, and smoother handling for deployment and runtime operations.

The biggest improvements in this release are:

- **Model budgets and spend visibility** for production model usage
- **Safer edit workflows** across agents, tools, policies, model providers, and identity providers
- **Faster inventory operations** with shared search, sort, and filter controls across the core console pages
- **Smoother deployment and run handling** for operators working through unfinished drafts, resumed runs, and active workflows

## Who should care

This release is especially relevant if you are:

- running agents in shared environments and need tighter control over model spend
- editing policies, tools, or providers regularly and want safer draft behavior
- managing larger workspaces with many agents, tools, requests, and providers
- using the console as the main operator surface for deployment, debugging, and approvals
- debugging live runs and deployment state in production

## What’s New

### Model budgets and spend visibility

RunAgents now gives teams a clearer way to control and understand model spend in production.

You can now:

- set **monthly budgets per configured model**
- see **model spend** directly in the dashboard
- monitor **Budget Watch** and **Top Model Spend**
- inspect **Model Budget Usage** from observability
- understand budget-related failures more clearly in playground and run detail experiences

This makes model cost control part of normal platform operations instead of a manual follow-up task.

Why this matters:

- premium models can be capped without blocking the rest of a deployment
- teams can separate cost controls by workload
- operators can see which models are healthy, near budget, or already blocked
- budget failures are easier to understand and recover from

### Safer edit flows across the console

This release adds stronger protection against silent draft loss across the main edit surfaces.

RunAgents now makes it clearer when you have unsaved changes while editing:

- agents
- policies
- tools
- identity providers
- model providers

The console now:

- warns when you have unsaved edits
- makes reload and discard behavior explicit
- avoids quietly overwriting in-progress work
- pauses certain auto-refresh behavior while you are actively editing

Why this matters:

- operators can work with more confidence
- draft-based editing feels more predictable
- configuration changes are less likely to be lost during navigation or refresh

### Faster inventory operations

The console now gives operators a more consistent way to navigate and scan workspace resources.

This release adds shared inventory controls across key console pages, including:

- search
- sort
- filtering
- summary cards
- clearer list behavior across the core platform inventory views

These improvements apply across the operational surfaces teams use most often, including:

- agents
- tools
- policies
- requests
- model providers
- identity providers
- catalog and deployment-related views

Why this matters:

- large workspaces are easier to scan
- common operational tasks take fewer clicks
- teams can move between inventory surfaces without relearning controls each time

### Smoother deployment and runtime operations

This release also improves how RunAgents behaves once work is already in progress.

Highlights include:

- cleaner handling of unfinished deployment flows
- better resume behavior for in-progress deployment drafts
- improved run-state continuity for operators following live activity
- runtime reliability fixes that reduce confusing or stale workflow states

In practice, this means operators should see fewer cases where:

- a deployment feels half-finished without a clear next step
- a run appears stuck longer than expected
- resumed workflows lose important context
- operational state is harder to interpret than it should be

## What You Can Do With This Release

### Put model spending under real operational control

If your agents use multiple models, you can now:

1. configure budgets during deploy or later from edit surfaces
2. monitor spend from the dashboard
3. inspect budget pressure in observability
4. understand budget-related failures directly from run and playground experiences

### Make configuration changes with less risk

If you frequently update policies, providers, or agent configs, the new edit protections reduce the chances of losing work while moving around the console.

This is especially helpful for teams that:

- review and tune policies regularly
- iterate on provider configuration
- update deployed agents in-place
- operate across multiple related surfaces in the same session

### Operate larger workspaces more efficiently

If your workspace now includes many agents, tools, providers, or pending requests, the updated inventory controls make the console easier to use as an operational surface rather than just a configuration screen.

## Important notes

- Model budget enforcement uses **estimated spend**, not provider billing exports.
- Estimated spend depends on the **model pricing** configured on the provider.
- Budgets apply **per configured model**, not as a workspace-wide global cap.
- This release improves operational safety and visibility; it does not change the core approval or policy model introduced in the earlier April releases.

## Why this release matters

The core theme of `v1.4.0` is operational maturity.

RunAgents already enforced governance around agent actions. This release improves the day-to-day experience of running that governed system:

- controlling spend
- editing safely
- navigating inventory quickly
- resuming work cleanly
- understanding runtime state with less guesswork

That makes the platform more reliable not just at execution time, but at operator time.

## Learn more

- [Dashboard](../../platform/dashboard.md)
- [Deploying Agents](../../platform/deploying-agents.md)
- [Model Providers](../../platform/model-providers.md)
- [Run Lifecycle](../../operations/runs.md)
- [Policies](../../concepts/policy-model.md)
