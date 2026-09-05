"""principal is supplied by authenticated server middleware outside this fixture."""


def own_invoice(principal, invoice):
    if invoice["tenant_id"] != principal["tenant_id"]:
        raise PermissionError("forbidden")
    return invoice


def admin_summary(principal):
    if principal["role"] != "admin":
        raise PermissionError("forbidden")
    return {"ok": True}
