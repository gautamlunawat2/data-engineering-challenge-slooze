"""
Synthetic dataset generator.

Produces realistic-looking B2B marketplace records that mirror the
schema returned by the live scraper.  Used as a fallback when
IndiaMART blocks requests (very common during automated testing /
CI runs) and as a standalone demo dataset.
"""
from __future__ import annotations

import random
from datetime import datetime


# ── seed data pools ──────────────────────────────────────────────────────────

_CATEGORIES: dict[str, list[str]] = {
    "Industrial Machinery": [
        "CNC Milling Machine", "Hydraulic Press Machine", "Belt Conveyor System",
        "Industrial Air Compressor", "Lathe Machine", "Injection Molding Machine",
        "Pneumatic Drill Press", "Gear Cutting Machine", "Vertical Machining Centre",
        "Industrial Pump", "Vibrating Screen", "Pellet Mill Machine",
        "Welding Robot", "Plasma Cutting Machine", "Industrial Grinder",
        "Heat Treatment Furnace", "Centrifugal Pump", "Industrial Fan",
        "Screw Conveyor", "Jaw Crusher",
    ],
    "Electronics": [
        "Arduino Mega Development Board", "Raspberry Pi 4 Module", "MOSFET Transistor Pack",
        "Industrial PLC Controller", "BLDC Motor Controller", "SMD Capacitor Kit",
        "PCB Prototype Board", "RF Signal Amplifier", "Solar Charge Controller",
        "Temperature Sensor Module", "LCD Display Panel", "Industrial UPS System",
        "Variable Frequency Drive", "Three Phase Inverter", "Energy Meter",
        "IoT Gateway Device", "RFID Reader Module", "Industrial Ethernet Switch",
        "Servo Motor Driver", "Digital Oscilloscope",
    ],
    "Textiles & Apparel": [
        "Organic Cotton Fabric", "Polyester Woven Fabric", "Silk Dupioni Fabric",
        "Jute Hessian Cloth", "Bamboo Terry Towel", "Denim Twill Fabric",
        "Spandex Knit Fabric", "Linen Blend Shirt Fabric", "Printed Voile Fabric",
        "Wool Worsted Suiting", "Viscose Georgette", "Net Embroidered Lace",
        "Reflective Safety Vest", "Non-Woven PP Fabric", "Microfiber Cleaning Cloth",
        "Hand Woven Khadi Cloth", "Industrial Canvas Fabric", "Fire Retardant Fabric",
        "Antibacterial Sports Fabric", "Recycled PET Fabric",
    ],
    "Chemical & Pharma": [
        "Sodium Hydroxide Flakes", "Hydrochloric Acid Industrial", "Isopropyl Alcohol 99%",
        "Activated Carbon Powder", "Titanium Dioxide Pigment", "Potassium Nitrate Fertilizer",
        "Industrial Epoxy Resin", "Sodium Bicarbonate Food Grade", "Citric Acid Monohydrate",
        "Hydrogen Peroxide 35%", "Acetone Solvent", "Polyethylene Glycol",
        "Calcium Carbonate Powder", "Ferric Chloride Solution", "Urea Prilled Fertilizer",
        "Sodium Silicate Solution", "Ammonium Sulphate", "Industrial Salt",
        "Zinc Oxide Powder", "Benzoic Acid",
    ],
    "Agricultural Products": [
        "Basmati Rice Long Grain", "Yellow Corn Maize", "Organic Turmeric Powder",
        "Black Pepper Whole", "Soybean Oil Crude", "Groundnut Kernels Bold",
        "Fresh Pomegranate Arils", "Dried Red Chilli", "Cotton Seed",
        "Sesame Seeds Natural", "Castor Seeds", "Sunflower Seeds",
        "Wheat Flour Maida", "Chickpea (Chana Dal)", "Mango Pulp Alphonso",
        "Banana Powder Spray Dried", "Ginger Dry Slices", "Moringa Leaf Powder",
        "Tamarind Block Seedless", "Onion Dehydrated Flakes",
    ],
}

_LOCATIONS = [
    ("Mumbai",      "Maharashtra"),
    ("Delhi",       "Delhi"),
    ("Ahmedabad",   "Gujarat"),
    ("Ludhiana",    "Punjab"),
    ("Bangalore",   "Karnataka"),
    ("Chennai",     "Tamil Nadu"),
    ("Kolkata",     "West Bengal"),
    ("Hyderabad",   "Telangana"),
    ("Surat",       "Gujarat"),
    ("Coimbatore",  "Tamil Nadu"),
    ("Pune",        "Maharashtra"),
    ("Rajkot",      "Gujarat"),
    ("Faridabad",   "Haryana"),
    ("Jaipur",      "Rajasthan"),
    ("Kanpur",      "Uttar Pradesh"),
    ("Nagpur",      "Maharashtra"),
    ("Indore",      "Madhya Pradesh"),
    ("Vadodara",    "Gujarat"),
    ("Noida",       "Uttar Pradesh"),
    ("Gurgaon",     "Haryana"),
]

_SUPPLIER_PREFIXES = [
    "Shree", "Sri", "Raj", "Anand", "Global", "National", "Premier", "Star",
    "Apex", "Royal", "Indian", "Bharat", "New", "Modern", "Advanced",
]
_SUPPLIER_TYPES = [
    "Enterprises", "Industries", "Corporation", "Pvt Ltd", "Traders",
    "Manufacturers", "Exports", "International", "Solutions", "Works",
]

_PRICE_RANGES: dict[str, tuple[float, float]] = {
    "Industrial Machinery":  (15_000,  5_000_000),
    "Electronics":           (50,      50_000),
    "Textiles & Apparel":    (20,      2_000),
    "Chemical & Pharma":     (5,       50_000),
    "Agricultural Products": (10,      5_000),
}

_UNITS: dict[str, list[str]] = {
    "Industrial Machinery":  ["Piece", "Unit", "Set"],
    "Electronics":           ["Piece", "Pack of 10", "Unit", "Pack of 100"],
    "Textiles & Apparel":    ["Meter", "Kg", "Roll", "Piece"],
    "Chemical & Pharma":     ["Kg", "Litre", "MT", "Drum", "Bag"],
    "Agricultural Products": ["Kg", "MT", "Quintal", "Bag (50 Kg)", "Ton"],
}


# ── generator ────────────────────────────────────────────────────────────────

def _make_supplier() -> str:
    return f"{random.choice(_SUPPLIER_PREFIXES)} {random.choice(_SUPPLIER_TYPES)}"


def _make_record(category: str, product_name: str) -> dict:
    lo, hi = _PRICE_RANGES[category]
    min_p = round(random.uniform(lo, hi * 0.6), 2)
    max_p = round(min_p * random.uniform(1.05, 2.5), 2)
    city, state = random.choice(_LOCATIONS)
    verified = random.random() > 0.35
    rating = round(random.uniform(3.5, 5.0), 1) if random.random() > 0.3 else None
    reviews = random.randint(1, 500) if rating is not None else None
    units = _UNITS[category]

    return {
        "product_name":  product_name,
        "category":      category,
        "min_price_inr": min_p,
        "max_price_inr": max_p,
        "price_unit":    random.choice(units),
        "raw_price":     f"₹{min_p:,.0f} - ₹{max_p:,.0f}/{random.choice(units)}",
        "supplier_name": _make_supplier(),
        "location":      city,
        "state":         state,
        "verified":      verified,
        "rating":        rating,
        "review_count":  reviews,
        "min_order_qty": f"{random.choice([1,5,10,50,100,500])} {random.choice(units)}",
        "description":   f"High-quality {product_name.lower()} sourced directly from manufacturers.",
        "product_url":   None,
        "scraped_at":    datetime.utcnow().isoformat(),
        "data_source":   "synthetic",
    }


def generate_mock_dataset(records_per_product: int = 10) -> list[dict]:
    """
    Returns a list of synthetic product records spanning all categories.
    Each product template is repeated `records_per_product` times with
    different suppliers / prices to simulate a realistic distribution.
    """
    random.seed(42)
    records: list[dict] = []

    for category, products in _CATEGORIES.items():
        for product in products:
            for _ in range(records_per_product):
                records.append(_make_record(category, product))

    random.shuffle(records)
    return records
