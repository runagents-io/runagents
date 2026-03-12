# Policy YAML For LangChain Enterprise Example

This folder shows policy-first access control for `hr-assistant` using current RunAgents policy semantics.

---

## Files

- `employee-directory-binding.yaml`
  - Creates a policy with `permission: allow` for read access to employee directory API.
  - Binds that policy to ServiceAccount `hr-assistant`.

- `compensation-binding.yaml`
  - Creates a policy with `permission: approval_required` for compensation write operations.
  - Adds `spec.approvals` approver group rules (`hr-admins`).
  - Binds that policy to ServiceAccount `hr-assistant`.

---

## Apply

```bash
kubectl apply -f policy/employee-directory-binding.yaml
kubectl apply -f policy/compensation-binding.yaml
```

---

## Runtime Behavior

- Employee directory calls matching `GET` rules are allowed immediately.
- Compensation write calls matching `approval_required` rules return `403 APPROVAL_REQUIRED` and create approval requests.
- After approval, RunAgents creates a temporary allow grant and resumes blocked run actions.

---

## Notes

- Authorization decisions follow precedence: `deny` > `approval_required` > `allow` > default deny.
- Tool-level `requireApproval` is deprecated for runtime authorization.
- Ensure tool base URLs in your tool registrations match the resource patterns in these policies.
