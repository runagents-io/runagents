---
title: Self-Hosted Deployment
description: Overview of self-hosted RunAgents deployment options for customers who need to run the platform in their own infrastructure.
---

# Self-Hosted Deployment

RunAgents can run in your own infrastructure for customers who require full data sovereignty, compliance with data residency regulations, or air-gapped environments.

---

## Requirements

| Requirement | Description |
|---|---|
| **Compute environment** | Cloud (AWS, GCP, Azure) or on-premise servers |
| **Container runtime** | Support for running containerized workloads |
| **Network policy support** | Ability to enforce zero-trust mesh networking between services |
| **TLS certificates** | For securing public-facing endpoints (console, API, OAuth callbacks) |
| **DNS** | Custom domain for your RunAgents instance (e.g., `runagents.yourcompany.com`) |
| **Storage** | Persistent storage for token data, run history, and build artifacts |

---

## Deployment Options

### Option 1: Managed by RunAgents (Recommended)

We deploy and manage RunAgents in **your** cloud account. You retain full data sovereignty -- all data stays within your infrastructure. We handle:

- Initial deployment and configuration
- Upgrades and patches
- Monitoring and incident response
- Scaling as your usage grows

!!! tip "Best of both worlds"

    Managed deployment gives you the security of self-hosted with the operational simplicity of a managed service. No infrastructure expertise required on your side.

### Option 2: Self-Managed

Deploy RunAgents using our provided container images and configuration templates. You manage the infrastructure and operations. This option is available for enterprise customers who have specific operational requirements.

!!! info "Enterprise only"

    Self-managed deployment requires an enterprise agreement. Contact us for details.

---

## What Is Included

A complete RunAgents deployment includes the following components:

| Component | Description |
|---|---|
| **Platform Operator** | Manages the lifecycle of agents, tools, model providers, and policies |
| **Security Mesh** | Intercepts all agent-to-tool traffic for identity verification, policy enforcement, and credential injection |
| **LLM Gateway** | Unified endpoint for model inference across providers (OpenAI, Anthropic, AWS Bedrock, local models) |
| **Governance Service** | Manages approvals, runs, OAuth consent flows, and access tokens |
| **Code Ingestion** | Analyzes uploaded agent code to detect tools, LLM usage, secrets, and dependencies |
| **Build Service** | Generates container images from agent source code |
| **Web Console** | Browser-based UI for managing agents, tools, policies, and approvals |

All components are delivered as container images with configuration templates.

---

## Security Architecture

Self-hosted RunAgents maintains the same security properties as the managed platform:

- **Zero-trust networking** -- All agent-to-tool traffic is intercepted and authorized
- **Identity propagation** -- User identity flows end-to-end from client to external tool
- **Policy enforcement** -- Fine-grained access control on every outbound request
- **Credential isolation** -- API keys and OAuth tokens are managed by the platform, never exposed to agent code
- **Audit trail** -- Every run, event, and approval decision is logged

---

## Getting Started

Contact us to begin your self-hosted deployment:

1. **Email [try@runagents.io](mailto:try@runagents.io?subject=Self-Hosted RunAgents)** with "Self-Hosted" in the subject line
2. Include your target infrastructure (cloud provider or on-premise) and any compliance requirements
3. We will schedule an onboarding call and provide:
    - Deployment guide tailored to your infrastructure
    - Container image access via private registry
    - Configuration templates for your environment
    - Dedicated onboarding support

[Request Self-Hosted Deployment](mailto:try@runagents.io?subject=Self-Hosted RunAgents){.cta-button}

---

## Frequently Asked Questions

**How long does deployment take?**
:   Managed deployment typically takes 1-2 business days. Self-managed deployment depends on your infrastructure readiness.

**Can I run RunAgents in an air-gapped environment?**
:   Yes. We provide container images that can be loaded into an air-gapped registry. The platform operates without internet access, though LLM providers that require external API calls will need a network path to their endpoints.

**What cloud providers are supported?**
:   We support AWS, GCP, Azure, and on-premise environments. The platform runs on standard container infrastructure.

**How are upgrades handled?**
:   For managed deployments, we handle upgrades during your maintenance windows. For self-managed deployments, we provide new container images and migration guides with each release.

**What about high availability?**
:   All components support running multiple replicas for high availability. We provide guidance on configuring HA for your specific infrastructure.

---

## Next Steps

- [Architecture](../concepts/architecture.md) -- Understand how RunAgents processes requests
- [Contact & Trial](../contact.md) -- Other ways to get started
