"""
Import UK IT consulting prospects from Sales Navigator CSV export into Voss CRM.

Usage:
    cd backend && python -m scripts.import_prospects
"""

import csv
import os
import re
import sys

# Ensure the backend package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.sheet_service import companies_sheet, contacts_sheet

CSV_PATH = os.path.expanduser(
    "~/Development/signalstrata/analysis/prospects/uk_it_consulting_prospects.csv"
)


def parse_leader(raw: str) -> dict | None:
    """Parse 'Peeyoosh Pandey (CEO)' → {first_name, last_name, role}."""
    raw = raw.strip()
    if not raw:
        return None

    role = ""
    match = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", raw)
    if match:
        name_part = match.group(1).strip()
        role = match.group(2).strip()
    else:
        name_part = raw

    parts = name_part.split()
    if not parts:
        return None

    first_name = parts[0]
    last_name = " ".join(parts[1:]) if len(parts) > 1 else ""

    return {"first_name": first_name, "last_name": last_name, "role": role}


def build_company_notes(row: dict) -> str:
    """Build a structured notes block from CSV fields."""
    lines = []
    for label, key in [
        ("Location", "location"),
        ("Revenue", "revenue"),
        ("Description", "description"),
        ("Services", "services"),
        ("Sales Nav Signal", "sales_nav_signal"),
        ("Sales Nav Activity", "sales_nav_activity"),
    ]:
        val = row.get(key, "").strip()
        if val:
            lines.append(f"{label}: {val}")
    return "\n".join(lines)


def main():
    if not os.path.exists(CSV_PATH):
        print(f"CSV not found: {CSV_PATH}")
        sys.exit(1)

    # Read CSV
    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    print(f"Read {len(rows)} rows from CSV")

    # Fetch existing company names for dedup
    existing = companies_sheet.get_all()
    existing_names = {c["name"].strip().lower() for c in existing}
    print(f"Found {len(existing_names)} existing companies in CRM")

    # Prepare batches
    company_data_list = []
    contact_data_list = []
    skipped = 0

    for row in rows:
        company_name = row["name"].strip()
        if company_name.lower() in existing_names:
            skipped += 1
            continue

        # Build company record
        company = {
            "name": company_name,
            "industry": row.get("industry", "").strip(),
            "website": row.get("website", "").strip(),
            "size": row.get("employees_linkedin", "").strip(),
            "notes": build_company_notes(row),
        }
        company_data_list.append(company)

        # Parse leaders for this company (stored temporarily, linked after bulk create)
        leaders = []
        ceo = parse_leader(row.get("ceo", ""))
        if ceo:
            leaders.append(ceo)

        other_leaders_raw = row.get("other_leaders", "").strip()
        if other_leaders_raw:
            for chunk in other_leaders_raw.split("),"):
                chunk = chunk.strip()
                if chunk and not chunk.endswith(")"):
                    chunk += ")"
                leader = parse_leader(chunk)
                if leader:
                    leaders.append(leader)

        # Store leaders with company index so we can link after bulk create
        for leader in leaders:
            contact_data_list.append({
                "_company_index": len(company_data_list) - 1,
                **leader,
            })

    print(f"Skipped {skipped} duplicate companies")
    print(f"Preparing to create {len(company_data_list)} companies and {len(contact_data_list)} contacts")

    if not company_data_list:
        print("Nothing to import.")
        return

    # Bulk create companies
    print("Creating companies...")
    created_companies = companies_sheet.bulk_create(company_data_list)
    print(f"  Created {len(created_companies)} companies")

    # Build contact records with company_id links
    contact_records = []
    for c in contact_data_list:
        company_idx = c.pop("_company_index")
        company_id = created_companies[company_idx]["id"]
        contact_records.append({
            "company_id": company_id,
            "first_name": c["first_name"],
            "last_name": c["last_name"],
            "role": c["role"],
            "source": "linkedin",
            "segment": "consulting",
            "engagement_stage": "new",
            "inbound_channel": "cold_outbound",
            "tags": "uk_it_consulting_prospects",
            "status": "active",
        })

    # Bulk create contacts
    print("Creating contacts...")
    created_contacts = contacts_sheet.bulk_create(contact_records)
    print(f"  Created {len(created_contacts)} contacts")

    print(f"\nDone! Summary:")
    print(f"  Companies created: {len(created_companies)}")
    print(f"  Contacts created:  {len(created_contacts)}")
    print(f"  Companies skipped: {skipped}")


if __name__ == "__main__":
    main()
