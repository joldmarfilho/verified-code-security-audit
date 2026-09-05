--- ISSUE 1 ---

# [Security][High] Invoice read permits cross-tenant access

## Labels

`security`, `severity:high`

## Problem

- **F1 — Invoice read permits cross-tenant access**: The registered GET /invoices/{invoice_id} handler uses the client-controlled identifier directly to read INVOICES and returns the item without comparing its tenant_id with the trusted principal. The neighboring own_invoice handler demonstrates the expected tenant boundary. This is one object-authorization defect, not separate tenant-isolation and IDOR vulnerabilities.

## Exploitability

- **F1**: A tenant-a caller requests GET /invoices/inv-b. ROUTES dispatches to invoice with invoice_id equal to inv-b. invoice ignores principal and returns the tenant-b dictionary item containing tenant_id b and amount 200. This path is established statically; no request or fixture code was executed. (The caller has an authenticated session under the scenario's documented dispatch assumption. The caller supplies an existing invoice identifier belonging to another tenant; inv-b is the concrete fixture target for a tenant-a principal.)

## Evidence

- **F1 — app.py:32**

```text
    "GET /invoices/{invoice_id}": invoice,
```

- **F1 — app.py:9-10**

```text
def invoice(principal, invoice_id):
    return INVOICES[invoice_id]
```

- **F1 — app.py:3-6**

```text
INVOICES = {
    "inv-a": {"tenant_id": "a", "amount": 100},
    "inv-b": {"tenant_id": "b", "amount": 200},
}
```

- **F1 — README.md:3-4**

```text
This Python fixture models authenticated handlers. `principal` is provided by
trusted session middleware; clients control `invoice_id`. All registrations are
```

## Impact

- **F1**: An authenticated user can read another tenant's invoice amount and tenant identifier. The fixture proves unauthorized invoice reads; it does not establish modification, deletion, or exposure of additional production fields.

## Remediation

- **F1**: Apply the same authenticated tenant check used by own_invoice before returning an invoice, preferably through a shared scoped lookup used by both registered invoice handlers. Define a denial response that does not disclose the foreign invoice contents.

## Acceptance criteria

- [ ] Through GET /invoices/{invoice_id}, a tenant-a principal requesting inv-b receives a denial without tenant-b invoice data.
- [ ] Repeat the cross-tenant check in the opposite direction and through GET /own-invoices/{invoice_id}.
- [ ] A tenant-a principal can still read inv-a, and a tenant-b principal can still read inv-b through both invoice routes.
- [ ] Unknown invoice identifiers produce a controlled response with no invoice data; tests use the actual dispatch boundary when its implementation becomes available.

--- END ISSUE 1 ---
