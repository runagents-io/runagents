# Policy YAML — How RunAgents Access Control Works

RunAgents access control is built on three Kubernetes CRDs:
**Tool**, **Policy**, and **PolicyBinding**.

---

## The Model

```
Agent (ServiceAccount) ──bound by──> PolicyBinding ──references──> Policy
                                                                      │
                                                                      └──> Tool (resource URN)
```

### Tool CRD
Defines an external API — base URL, auth type, topology. Can declare
`accessMode: Open | Restricted` and capabilities (operation allow-lists).

### Policy CRD
A named set of allow/deny rules over resource URN patterns.
Example resource: `"tool:compensation-api"`.

### PolicyBinding CRD
Links a set of subjects (ServiceAccounts, users, groups) to a Policy.
The binding is where `requireApproval` lives — it controls whether the
first call triggers a JIT access request.

---

## What the Operator Auto-Creates (Open Tools)

For any tool with `accessMode: Open`, the **agent operator controller**
automatically creates a Policy + PolicyBinding when the Agent CRD is
reconciled. You don't need to apply anything.

```yaml
# Auto-generated for hr-knowledge-base (Open)
apiVersion: platform.ai/v1alpha1
kind: Policy
metadata:
  name: hr-assistant-hr-knowledge-base   # {agent}-{tool}
  namespace: agent-system
spec:
  rules:
    - resources: ["tool:hr-knowledge-base"]
      verbs: ["call"]
      effect: Allow
---
apiVersion: platform.ai/v1alpha1
kind: PolicyBinding
metadata:
  name: hr-assistant-hr-knowledge-base
  namespace: agent-system
spec:
  subjects:
    - kind: ServiceAccount
      name: hr-assistant        # agent's ServiceAccount
      namespace: default
  policyRef:
    name: hr-assistant-hr-knowledge-base
  requireApproval: false        # no approval needed — just call it
  ttl: ""                       # permanent (no expiry)
```

The owner reference on these resources points to the Agent CRD, so they
are deleted automatically when the agent is deleted.

---

## What You Apply (Restricted Tools)

For `accessMode: Restricted`, no auto-binding is created.
You apply the binding explicitly to grant access.

### employee-directory — Restricted, no approval

```yaml
# policy/employee-directory-binding.yaml
```

Apply with:
```bash
kubectl apply -f policy/employee-directory-binding.yaml
```

Once applied, the agent can call employee-directory freely.

### compensation-api — Restricted, requireApproval: true

```yaml
# policy/compensation-binding.yaml
```

Apply with:
```bash
kubectl apply -f policy/compensation-binding.yaml
```

After applying, the first call to compensation-api:
1. Ext-authz sees the PolicyBinding with `requireApproval: true`
2. Calls governance `POST /governance/requests` to create an AccessRequest
3. Returns 403 `{"code": "APPROVAL_REQUIRED", "action_id": "act-xxx", "run_id": "run-xxx"}`
4. The agent's run pauses (PAUSED_APPROVAL)
5. Admin approves → ResumeWorker resumes the run

### Durable Resume — Survives Agent Failure

Immediately after the 403 APPROVAL_REQUIRED is raised, the runtime
saves the full conversation checkpoint to governance **before** returning
control to your code:

```
403 APPROVAL_REQUIRED received by runtime
  ↓
runtime POST /runs/{run_id}/checkpoint  ← stored in governance, not in pod
  ↓
ApprovalRequired raised to agent code
  ↓
agent returns "pending approval" response
  ↓ ... time passes, pod may crash, restart, or be redeployed ...
  ↓
admin approves via runagents approvals approve <action_id>
  ↓
ResumeWorker fetches checkpoint from governance  ← no dependency on agent pod state
  ↓
ResumeWorker calls POST /resume/<action_id> on the agent pod
  ↓
runtime restores: messages + pending tool calls
  ↓
tool calls re-executed, LLM loop continues, run completes
```

**The checkpoint contains:**
- Full LLM message history (every user message, assistant message, tool result)
- All pending tool calls that were blocked (blocked call + any subsequent calls
  from the same LLM response that hadn't been attempted yet)
- Tool definitions and routes from the original request

**Your agent code is not involved in checkpointing or resume.** The
runtime handles it entirely. This means your agent can be restarted,
redeployed, or replaced between approval and resume — it will still
complete correctly.

---

## The ext-authz Decision Flow

Every outbound tool call from the agent pod passes through Envoy →
ext-authz service. Here is exactly what happens:

```
Agent pod makes HTTP request to tool
  │
  ▼ Istio sidecar captures the request
  │
  ▼ Envoy sends CheckRequest to ext-authz (port 9001)
  │
  ├─ ext-authz identifies Tool CRD by matching destination hostname
  │
  ├─ ext-authz extracts agent identity from XFCC header (SPIFFE URI → ServiceAccount)
  │
  ├─ ext-authz lists PolicyBindings for this agent's ServiceAccount
  │    │
  │    ├─ No matching binding → 403 {"code": "PERMISSION_DENIED"}
  │    │
  │    └─ Binding found, requireApproval: false → proceed to token injection
  │         └─ Binding found, requireApproval: true → create AccessRequest
  │                                                    → 403 APPROVAL_REQUIRED
  │
  ├─ [if capabilities declared] ext-authz checks request method + path
  │    └─ no matching capability → 403 {"code": "OPERATION_NOT_PERMITTED"}
  │
  └─ ext-authz calls governance /internal/token/retrieve
       └─ injects Authorization: Bearer <token> + X-End-User-ID
         └─ forwards request to tool
```

---

## AccessRequest Lifecycle

```
Pending ──(admin approves)──> Approved ──(ResumeWorker executes)──> Executed
        ──(admin rejects)───> Rejected
        ──(TTL expires)─────> Expired
```

When a PolicyBinding has `ttl: "1h"`, the created PolicyBinding for the
approved action expires after 1 hour. Subsequent calls require a new
approval.

---

## Checking Active Bindings

```bash
# List all PolicyBindings in agent-system
kubectl get policybindings -n agent-system

# See what policies an agent has
kubectl get policybindings -n agent-system -l runagents.ai/agent=hr-assistant

# List pending AccessRequests
runagents approvals list

# See approved history
kubectl get accessrequests -n agent-system
```
