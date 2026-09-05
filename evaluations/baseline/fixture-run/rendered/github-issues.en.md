--- ISSUE 1 ---

# [Security][High] Authenticated invoice lookup discloses another tenant's invoice

## Labels

`security`, `severity:high`

## Problem

- **VCSA-001 — Authenticated invoice lookup discloses another tenant's invoice**: GET /invoices/{invoice_id} calls invoice, which returns the selected dictionary entry without consulting the trusted principal or comparing tenant_id. The stored entries belong to different tenants, and the adjacent own_invoice handler demonstrates the intended tenant boundary. Authentication alone does not enforce that boundary.

## Exploitability

- **VCSA-001**: Under the documented dispatch model, a session with principal tenant_id a requests GET /invoices/inv-b. ROUTES selects invoice; invoice evaluates INVOICES["inv-b"] and returns the tenant b record, including amount 200. This is a static source trace, not an executed request or proof of runtime behavior. (The documented server dispatches the registered route after authenticating a session; this is assumed because its implementation is unavailable. The caller is authenticated as one tenant and controls invoice_id. A record for another tenant exists and the caller knows or guesses its identifier; inv-b is present in the fixture.)

## Evidence

- **VCSA-001 — app.py:3-6**

```text
INVOICES = {
    "inv-a": {"tenant_id": "a", "amount": 100},
    "inv-b": {"tenant_id": "b", "amount": 200},
}
```

- **VCSA-001 — app.py:9-10**

```text
def invoice(principal, invoice_id):
    return INVOICES[invoice_id]
```

- **VCSA-001 — app.py:30-33**

```text
# The server dispatches only these handlers after authenticating a session.
ROUTES = {
    "GET /invoices/{invoice_id}": invoice,
    "GET /own-invoices/{invoice_id}": own_invoice,
```

## Impact

- **VCSA-001**: Cross-tenant confidentiality loss of invoice records available in INVOICES. The fixture supports unauthorized reads, not modification, account takeover, or unauthenticated access. High severity reflects the tenant-isolation failure; real-world sensitivity and scale are not supplied.

## Remediation

- **VCSA-001**: Route invoice reads through the existing own_invoice tenant check, or add an equivalent tenant_id comparison before returning any record. Apply this policy to every registered invoice lookup. Ensure missing and forbidden records produce controlled responses without invoice data.

## Acceptance criteria

- [ ] An authenticated tenant a request for inv-b through GET /invoices/{invoice_id} is rejected without returning the record.
- [ ] A tenant b request for inv-a is likewise rejected.
- [ ] Same-tenant reads remain successful on both registered invoice endpoints.
- [ ] Regression checks exercise the actual route dispatch and cannot bypass the shared tenant authorization check.
- [ ] Missing invoice identifiers produce a controlled response without sensitive error details.

--- END ISSUE 1 ---
