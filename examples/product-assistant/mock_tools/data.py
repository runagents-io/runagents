"""
mock_tools/data.py — Fake product and inventory data for local testing.

Replace this with calls to your real database or API in production.
"""

# ---------------------------------------------------------------------------
# Product catalog
# Each product has: id, name, description, sku, base_price, category
# ---------------------------------------------------------------------------

PRODUCTS = {
    "PRD-001": {
        "id": "PRD-001",
        "name": "Wireless Noise-Cancelling Headphones",
        "description": "Over-ear Bluetooth 5.3 headphones with 40-hour battery and ANC",
        "sku": "PRD-001",
        "base_price": 149.99,
        "currency": "USD",
        "category": "Audio",
        "specs": {
            "battery_hours": 40,
            "bluetooth": "5.3",
            "weight_grams": 250,
            "colors": ["Midnight Black", "Pearl White", "Navy Blue"],
        },
    },
    "PRD-002": {
        "id": "PRD-002",
        "name": "Mechanical Keyboard — TKL",
        "description": "Tenkeyless mechanical keyboard with hot-swap switches and RGB backlight",
        "sku": "PRD-002",
        "base_price": 89.99,
        "currency": "USD",
        "category": "Peripherals",
        "specs": {
            "layout": "TKL (87-key)",
            "switches": ["Red (Linear)", "Brown (Tactile)", "Blue (Clicky)"],
            "backlight": "Per-key RGB",
            "connectivity": ["USB-C", "Bluetooth 5.0"],
        },
    },
    "PRD-003": {
        "id": "PRD-003",
        "name": "USB-C Docking Station — 12-in-1",
        "description": "12-in-1 hub: 4K HDMI, 100W PD, 4x USB-A, SD card, ethernet",
        "sku": "PRD-003",
        "base_price": 59.99,
        "currency": "USD",
        "category": "Accessories",
        "specs": {
            "ports": 12,
            "max_power_delivery_w": 100,
            "display_output": "4K@60Hz",
            "ethernet": "Gigabit",
        },
    },
    "PRD-004": {
        "id": "PRD-004",
        "name": "Ergonomic Mouse — Silent Click",
        "description": "Vertical ergonomic mouse, silent buttons, 6-button programmable",
        "sku": "PRD-004",
        "base_price": 39.99,
        "currency": "USD",
        "category": "Peripherals",
        "specs": {
            "dpi_range": "400-3200",
            "buttons": 6,
            "connectivity": ["USB receiver", "Bluetooth"],
            "battery_months": 18,
        },
    },
    "PRD-005": {
        "id": "PRD-005",
        "name": "27-inch Monitor — 4K IPS",
        "description": "4K IPS monitor, 99% sRGB, USB-C 90W, height-adjustable stand",
        "sku": "PRD-005",
        "base_price": 449.99,
        "currency": "USD",
        "category": "Displays",
        "specs": {
            "resolution": "3840x2160",
            "panel": "IPS",
            "refresh_rate_hz": 60,
            "usb_c_power_delivery_w": 90,
            "color_coverage": "99% sRGB",
        },
    },
}

# ---------------------------------------------------------------------------
# Inventory
# Each entry: sku, quantity_available, warehouse, restock_date (if low)
# ---------------------------------------------------------------------------

INVENTORY = {
    "PRD-001": {
        "sku": "PRD-001",
        "quantity_available": 47,
        "warehouse": "US-WEST-1",
        "status": "in_stock",
        "restock_date": None,
    },
    "PRD-002": {
        "sku": "PRD-002",
        "quantity_available": 3,
        "warehouse": "US-EAST-1",
        "status": "low_stock",
        "restock_date": "2026-03-18",
        "note": "Only 3 units remaining — restock arriving March 18",
    },
    "PRD-003": {
        "sku": "PRD-003",
        "quantity_available": 120,
        "warehouse": "US-WEST-1",
        "status": "in_stock",
        "restock_date": None,
    },
    "PRD-004": {
        "sku": "PRD-004",
        "quantity_available": 0,
        "warehouse": "US-EAST-1",
        "status": "out_of_stock",
        "restock_date": "2026-03-25",
        "note": "Currently out of stock — restock expected March 25",
    },
    "PRD-005": {
        "sku": "PRD-005",
        "quantity_available": 12,
        "warehouse": "US-WEST-1",
        "status": "in_stock",
        "restock_date": None,
    },
}

# ---------------------------------------------------------------------------
# Pricing logic
# Volume discounts and promotional codes
# ---------------------------------------------------------------------------

# Volume discount tiers: (min_quantity, discount_percent)
VOLUME_TIERS = [
    (100, 20),   # 100+ units → 20% off
    (50,  15),   # 50+ units  → 15% off
    (20,  10),   # 20+ units  → 10% off
    (10,   5),   # 10+ units  →  5% off
    (1,    0),   # base price
]

# Promotional codes: code → discount_percent
PROMO_CODES = {
    "SAVE10":  10,
    "SAVE20":  20,
    "NEWCUST": 15,
    "BULK50":  50,   # only for testing
}


def apply_discount(product: dict, quantity: int, promo_code: str = "") -> dict:
    """Calculate the final price for a quantity with volume discount + promo code."""
    base_price = product["base_price"]

    # Find volume discount
    volume_discount_pct = 0
    for min_qty, pct in VOLUME_TIERS:
        if quantity >= min_qty:
            volume_discount_pct = pct
            break

    # Find promo discount
    promo_discount_pct = 0
    promo_valid = False
    if promo_code:
        promo_discount_pct = PROMO_CODES.get(promo_code.upper(), 0)
        promo_valid = promo_code.upper() in PROMO_CODES

    # Discounts stack additively (capped at 60%)
    total_discount_pct = min(volume_discount_pct + promo_discount_pct, 60)
    unit_price = round(base_price * (1 - total_discount_pct / 100), 2)
    total_price = round(unit_price * quantity, 2)

    result = {
        "sku": product["sku"],
        "product_name": product["name"],
        "quantity": quantity,
        "base_price_per_unit": base_price,
        "currency": product.get("currency", "USD"),
        "discounts_applied": [],
        "unit_price": unit_price,
        "total_price": total_price,
        "savings": round((base_price - unit_price) * quantity, 2),
    }

    if volume_discount_pct:
        result["discounts_applied"].append(
            {"type": "volume", "percent": volume_discount_pct,
             "label": f"{volume_discount_pct}% volume discount ({quantity}+ units)"}
        )
    if promo_code:
        if promo_valid:
            result["discounts_applied"].append(
                {"type": "promo", "code": promo_code.upper(),
                 "percent": promo_discount_pct,
                 "label": f"{promo_discount_pct}% promo discount ({promo_code.upper()})"}
            )
        else:
            result["promo_warning"] = f"Promo code '{promo_code}' is invalid or expired"

    return result
