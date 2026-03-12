# Deal Desk Demo Agent (LangGraph)

Open-source framework: `langgraph`

## What this agent does

- Uses `crm_update_opportunity` for low-risk CRM updates.
- Uses `erp_issue_credit_note` for high-risk credit/refund actions.
- Requires complete ERP details before issuing credit notes.

## Expected tool endpoints

- `TOOL_URL_CRM_UPDATE_OPPORTUNITY` -> `POST /crm/opportunity/update`
- `TOOL_URL_ERP_ISSUE_CREDIT_NOTE` -> `POST /erp/credit-note/issue`

## Deploy

```bash
runagents deploy \
  --files agent.py,requirements.txt \
  --name deal-desk-agent
```

## Suggested demo prompts

1. `Update opportunity OPP-1042 to negotiation, amount 120000, next step send final quote.`
2. `Issue a credit note for invoice INV-9007 customer CUST-22 amount 2500 because SLA breach.`
