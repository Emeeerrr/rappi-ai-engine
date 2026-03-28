"""
Fallback Data Generator - Realistic dummy competitive data for demo purposes.

Generates deterministic (seed=42) data for 3 platforms x 30 addresses with
realistic Mexican peso pricing, platform-specific characteristics, and
zone-type-based variation.
"""

import random
from datetime import datetime

from app.scraping.addresses import ADDRESSES, REFERENCE_PRODUCTS

# Platform-specific pricing profiles (base prices in MXN)
_PLATFORM_PROFILES = {
    "rappi": {
        "product_multiplier": 1.0,   # baseline prices
        "delivery_fee_range": (19, 49),
        "service_fee_pct_range": (0.05, 0.15),
        "delivery_time_range": (25, 50),
        "promo_chance": 0.45,  # most promotions
        "promotions": [
            "Envio gratis en tu primer pedido",
            "2x1 en McFlurry",
            "15% descuento con RappiPrime",
            "Cashback 10% en Rappi creditos",
            "$50 de descuento en pedidos +$200",
            "Combo familiar con 20% off",
        ],
    },
    "ubereats": {
        "product_multiplier": 1.06,  # slightly higher product prices
        "delivery_fee_range": (15, 45),
        "service_fee_pct_range": (0.05, 0.12),
        "delivery_time_range": (20, 45),
        "promo_chance": 0.30,
        "promotions": [
            "Envio gratis con Uber One",
            "$70 off en tu primera orden",
            "2x1 en bebidas seleccionadas",
            "30% off maximo $80",
        ],
    },
    "didi": {
        "product_multiplier": 0.98,  # slightly lower to compete
        "delivery_fee_range": (12, 39),  # cheapest delivery (penetration strategy)
        "service_fee_pct_range": (0.03, 0.10),
        "delivery_time_range": (25, 55),
        "promo_chance": 0.35,
        "promotions": [
            "Envio GRATIS sin minimo",
            "50% descuento hasta $100",
            "Descuento de bienvenida $80",
            "Cupon DiDi: COMIDAMX",
        ],
    },
}

# Base product prices in MXN
_BASE_PRICES = {
    "Big Mac": 99,
    "Combo Mediano McDonalds": 169,
    "McNuggets 10 piezas": 119,
    "Coca-Cola 500ml": 28,
    "Agua Natural 1L": 19,
}

# Zone-type modifiers
_ZONE_MODIFIERS = {
    "premium": {"delivery_fee_mult": 0.75, "time_mult": 0.80, "availability": 0.98},
    "middle": {"delivery_fee_mult": 1.00, "time_mult": 1.00, "availability": 0.93},
    "popular": {"delivery_fee_mult": 1.25, "time_mult": 1.15, "availability": 0.82},
}


def generate_fallback_data(addresses: list[dict] | None = None) -> list[dict]:
    """Generate realistic competitive data for all platforms and addresses.

    Args:
        addresses: List of address dicts. Defaults to ADDRESSES.

    Returns:
        List of result dicts (one per platform per address).
    """
    random.seed(42)
    addresses = addresses or ADDRESSES
    results = []
    timestamp = datetime.now().isoformat()

    for addr in addresses:
        zone_mod = _ZONE_MODIFIERS[addr["zone_type"]]

        for platform, profile in _PLATFORM_PROFILES.items():
            products = []
            total_product_price = 0

            for prod in REFERENCE_PRODUCTS:
                base = _BASE_PRICES[prod["name"]]
                # Apply platform multiplier + random variance (-5% to +8%)
                price = base * profile["product_multiplier"] * random.uniform(0.95, 1.08)
                price = round(price, 2)

                # Some products unavailable in popular zones
                available = random.random() < zone_mod["availability"]
                # Retail items less available on some platforms
                if prod.get("category") == "retail" and platform == "didi":
                    available = random.random() < 0.70

                products.append({
                    "name": prod["name"],
                    "price": price if available else None,
                    "available": available,
                })

                if prod["name"] == "Big Mac" and available:
                    total_product_price = price

            # Delivery fee with zone modifier
            fee_lo, fee_hi = profile["delivery_fee_range"]
            delivery_fee = round(
                random.uniform(fee_lo, fee_hi) * zone_mod["delivery_fee_mult"], 2,
            )

            # Service fee as percentage of products total
            svc_lo, svc_hi = profile["service_fee_pct_range"]
            service_fee_pct = random.uniform(svc_lo, svc_hi)
            avg_product = sum(p["price"] for p in products if p["price"]) / max(1, sum(1 for p in products if p["price"]))
            service_fee = round(avg_product * service_fee_pct, 2)

            # Delivery time with zone modifier
            t_lo, t_hi = profile["delivery_time_range"]
            delivery_time = int(random.uniform(t_lo, t_hi) * zone_mod["time_mult"])

            # Total price for Big Mac combo (product + delivery + service)
            total_big_mac = None
            if total_product_price > 0:
                total_big_mac = round(total_product_price + delivery_fee + service_fee, 2)

            # Promotions
            promos = []
            if random.random() < profile["promo_chance"]:
                n_promos = random.randint(1, 2)
                promos = random.sample(profile["promotions"], min(n_promos, len(profile["promotions"])))

            # Determine scrape status
            all_available = all(p["available"] for p in products)
            status = "success" if all_available else "partial"

            results.append({
                "platform": platform,
                "address_id": addr["id"],
                "address_label": addr["label"],
                "city": addr["city"],
                "zone_type": addr["zone_type"],
                "timestamp": timestamp,
                "restaurant": "McDonalds",
                "products": products,
                "delivery_fee": delivery_fee,
                "service_fee": service_fee,
                "estimated_delivery_time": f"{delivery_time}-{delivery_time + random.randint(5, 15)} min",
                "promotions": promos,
                "total_price_big_mac_combo": total_big_mac,
                "screenshot_path": None,
                "scrape_status": status,
                "error": None,
            })

    return results
