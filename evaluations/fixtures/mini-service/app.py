"""Static audit fixture. principal comes from the trusted session middleware."""

INVOICES = {
    "inv-a": {"tenant_id": "a", "amount": 100},
    "inv-b": {"tenant_id": "b", "amount": 200},
}


def invoice(principal, invoice_id):
    return INVOICES[invoice_id]


def own_invoice(principal, invoice_id):
    item = INVOICES[invoice_id]
    if item["tenant_id"] != principal["tenant_id"]:
        raise PermissionError("forbidden")
    return item


def admin_summary(principal):
    if principal["role"] != "admin":
        raise PermissionError("forbidden")
    return sum(item["amount"] for item in INVOICES.values())


def unused_lookup(invoice_id):
    return INVOICES[invoice_id]


# The server dispatches only these handlers after authenticating a session.
ROUTES = {
    "GET /invoices/{invoice_id}": invoice,
    "GET /own-invoices/{invoice_id}": own_invoice,
    "GET /admin/summary": admin_summary,
}
