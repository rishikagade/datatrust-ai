from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path


SEED = 20260528
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "sample_datasets"


FIRST_NAMES = ["Alex", "Jordan", "Taylor", "Morgan", "Casey", "Riley", "Avery", "Quinn", "Jamie", "Reese"]
LAST_NAMES = ["Chen", "Patel", "Johnson", "Smith", "Garcia", "Brown", "Kim", "Davis", "Miller", "Wilson"]
REGIONS = ["North", "South", "East", "West", "Central"]
DEPARTMENTS = [
    ("FIN", "Finance"),
    ("HR", "Human Resources"),
    ("ENG", "Engineering"),
    ("MKT", "Marketing"),
]


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def generate_customers() -> None:
    random.seed(SEED + 1)
    columns = ["customer_id", "first_name", "last_name", "email", "country", "age", "annual_revenue", "account_status"]
    total_rows = 5000
    base_count = total_rows - 847
    rows: list[dict[str, object]] = []

    duplicate_positions = set(random.sample(range(base_count), 1247))
    duplicate_ids = [f"C{100000 + i}" for i in range(420)]

    us_variants = [
        ("United States", 0.63),
        ("US", 0.10),
        ("USA", 0.08),
        ("U.S.", 0.05),
        ("united states", 0.04),
        ("United states", 0.03),
        ("UNITED STATES", 0.02),
        ("U.S.A.", 0.02),
        ("us", 0.01),
        ("America", 0.01),
        ("USA.", 0.01),
        ("United States of America", 0.01),
    ]
    other_countries = ["Canada", "Mexico", "United Kingdom", "Germany", "Australia"]

    for i in range(base_count):
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        customer_id = random.choice(duplicate_ids) if i in duplicate_positions else f"C{200000 + i}"
        country = random.choices([v for v, _ in us_variants], [w for _, w in us_variants], k=1)[0]
        if random.random() > 0.60:
            country = random.choice(other_countries)
        rows.append(
            {
                "customer_id": customer_id,
                "first_name": first,
                "last_name": last,
                "email": f"{first.lower()}.{last.lower()}{i}@example.com",
                "country": country,
                "age": random.randint(18, 82),
                "annual_revenue": random.randint(18_000, 480_000),
                "account_status": random.choice(["Active", "Inactive", "Prospect"]),
            }
        )

    for idx in random.sample(range(base_count), round(total_rows * 0.34)):
        rows[idx]["email"] = ""
    for idx in random.sample(range(base_count), 14):
        rows[idx]["age"] = random.randint(125, 145)
    for idx in random.sample(range(base_count), 203):
        rows[idx]["annual_revenue"] = random.choice(["$45,000", "$125,500", "N/A"])

    rows.extend(dict(rows[idx]) for idx in random.sample(range(base_count), 847))
    random.shuffle(rows)
    write_csv(OUT_DIR / "customer_master.csv", rows, columns)


def fmt_mixed_date(value: date, bucket: float) -> str:
    if bucket < 0.40:
        return value.strftime("%Y-%m-%d")
    if bucket < 0.75:
        return value.strftime("%m/%d/%Y")
    return value.strftime("%d/%m/%Y")


def generate_sales() -> None:
    random.seed(SEED + 2)
    columns = ["transaction_id", "order_date", "ship_date", "order_total", "product_category", "discount_pct", "region"]
    total_rows = 15000
    duplicate_count = round(total_rows * 0.023)
    base_count = total_rows - duplicate_count
    start = date(2025, 1, 1)
    rows: list[dict[str, object]] = []

    for i in range(base_count):
        order_date = start + timedelta(days=random.randint(0, 450))
        ship_date = order_date + timedelta(days=random.randint(1, 10))
        bucket = random.random()
        category = random.choice(["Electronics", "Furniture", "Office Supplies", "Software", "Services"])
        if category == "Electronics":
            category = random.choice(["Electronics", "Electronics ", " electronics", "ELECTRONICS", "electronics"])
        rows.append(
            {
                "transaction_id": f"TX{1000000 + i}",
                "order_date": fmt_mixed_date(order_date, bucket),
                "ship_date": ship_date.strftime("%Y-%m-%d"),
                "order_total": round(random.uniform(12, 2800), 2),
                "product_category": category,
                "discount_pct": random.choice([0, 5, 10, 15, 20, 25]),
                "region": random.choice(REGIONS),
            }
        )

    for idx in random.sample(range(base_count), 47):
        parsed = start + timedelta(days=random.randint(100, 420))
        rows[idx]["order_date"] = parsed.strftime("%Y-%m-%d")
        rows[idx]["ship_date"] = (parsed - timedelta(days=random.randint(1, 12))).strftime("%Y-%m-%d")
    for idx in random.sample(range(base_count), 89):
        rows[idx]["order_total"] = -round(random.uniform(5, 600), 2)
    for idx in random.sample(range(base_count), 12):
        rows[idx]["discount_pct"] = random.randint(101, 250)

    rows.extend(dict(rows[idx]) for idx in random.sample(range(base_count), duplicate_count))
    random.shuffle(rows)
    write_csv(OUT_DIR / "sales_transactions.csv", rows, columns)


def generate_hr() -> None:
    random.seed(SEED + 3)
    columns = ["employee_id", "hire_date", "termination_date", "status", "salary", "department", "job_title"]
    total_rows = 1200
    rows: list[dict[str, object]] = []
    duplicate_ids = ["E1007", "E1033", "E1099"]

    for i in range(total_rows):
        active = random.random() < 0.70
        hire = date(2016, 1, 1) + timedelta(days=random.randint(0, 3100))
        term = "" if active else (hire + timedelta(days=random.randint(45, 1800))).strftime("%Y-%m-%d")
        code, full = random.choice(DEPARTMENTS)
        rows.append(
            {
                "employee_id": f"E{1000 + i}",
                "hire_date": hire.strftime("%Y-%m-%d"),
                "termination_date": term,
                "status": random.choice(["Active", "active", "ACTIVE"]) if active else random.choice(["Terminated", "terminated", "Term"]),
                "salary": random.randint(52_000, 162_000),
                "department": random.choice([code, full]),
                "job_title": random.choice(["Analyst", "Manager", "Engineer", "Coordinator", "Director"]),
            }
        )

    for dup_id, idx in zip(duplicate_ids, random.sample(range(200, total_rows), 3)):
        rows[idx]["employee_id"] = dup_id
    median_salary = 104_000
    for idx in random.sample(range(total_rows), 18):
        rows[idx]["salary"] = median_salary * 10
    for idx in random.sample([i for i, row in enumerate(rows) if row["termination_date"]], 23):
        term = date.fromisoformat(str(rows[idx]["termination_date"]))
        rows[idx]["hire_date"] = (term + timedelta(days=random.randint(1, 90))).strftime("%Y-%m-%d")

    write_csv(OUT_DIR / "hr_employees.csv", rows, columns)


def main() -> None:
    generate_customers()
    generate_sales()
    generate_hr()


if __name__ == "__main__":
    main()
