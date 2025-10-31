from datetime import datetime

ORDERS = {
    "A123": {"status": "Delivered", "delivered_at": "2025-10-20", "amount": 79.99},
    "B456": {"status": "In Transit", "eta": "2025-11-02", "amount": 129.49},
}

def check_order_status(order_id: str):
    data = ORDERS.get(order_id)
    if not data:
        return {"found": False}
    return {"found": True, "order_id": order_id, **data}

def process_refund(order_id: str, reason: str, amount: float | None = None):
    amt = amount if amount is not None else ORDERS.get(order_id, {}).get("amount", 0.0)
    return {
        "ok": True,
        "order_id": order_id,
        "amount": round(amt, 2),
        "created_at": datetime.utcnow().isoformat() + "Z",
        "reference": f"RF-{order_id}-{int(datetime.utcnow().timestamp())}",
        "reason": reason,
    }

def create_return_label(order_id: str, reason: str):
    return {
        "ok": True,
        "order_id": order_id,
        "carrier": "UPS",
        "label_url": f"https://example.com/labels/{order_id}.pdf",
        "expires": (datetime.utcnow().date()).isoformat(),
        "reason": reason,
    }
