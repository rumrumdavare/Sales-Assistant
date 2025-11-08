"""
Generate synthetic CRM-style data for the AI Sales Assistant project.
Creates:
  data/raw/clients.csv
  data/raw/contacts.csv
  data/raw/metrics.csv
  data/raw/interactions.csv
  data/raw/tickets.csv
  data/meeting_notes/*.txt
"""

from __future__ import annotations
import os
import random
from datetime import date, datetime
from datetime import timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

# ----------------------------
# Config
# ----------------------------
SEED = 42
N_CLIENTS = 10
MONTHS = 6  # trailing months
NOTES_PER_CLIENT = (2, 3)  # inclusive range
INTERACTIONS_PER_CLIENT = (8, 14)
CONTACTS_PER_CLIENT = (1, 3)
TICKETS_PER_CLIENT = (0, 4)

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
NOTES_DIR = DATA_DIR / "meeting_notes"

REGIONS = ["EMEA", "AMER", "APAC"]
INDUSTRIES = ["SaaS", "E-commerce", "Manufacturing", "FinTech", "Healthcare"]
CHANNELS = ["Email", "Call", "Meeting"]
TICKET_CATS = ["Billing", "Technical", "Delivery", "Account"]
DEAL_STAGES = ["Prospecting", "Qualified", "Proposal/Quote", "Negotiation", "Closed Won", "Closed Lost"]

random.seed(SEED)
np.random.seed(SEED)
fake = Faker()
Faker.seed(SEED)

# ----------------------------
# Helpers
# ----------------------------
def daterange_months(end: date, months_back: int) -> list[date]:
    """List of month-start dates going back `months_back` months from end."""
    out = []
    y, m = end.year, end.month
    for _ in range(months_back):
        out.append(date(y, m, 1))
        # decrement month
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return list(sorted(out))

def sample_company_name() -> str:
    base = fake.company()
    # Make names a bit more “B2B”
    suffix = random.choice(["Ltd", "Inc", "GmbH", "SRL", "SpA", "PLC"])
    return f"{base} {suffix}"

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def ensure_dirs():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    NOTES_DIR.mkdir(parents=True, exist_ok=True)

# ----------------------------
# 1) Clients & Contacts
# ----------------------------
def make_clients(n_clients: int) -> pd.DataFrame:
    rows = []
    for i in range(1, n_clients + 1):
        company = sample_company_name()
        rows.append({
            "client_id": i,
            "company_name": company,
            "industry": random.choice(INDUSTRIES),
            "region": random.choice(REGIONS),
            "annual_revenue": round(np.random.lognormal(mean=14, sigma=0.6)),  # ~ €1.2M–€20M-ish
            "owner_name": fake.name(),
            "lifecycle_stage": random.choice(["Lead", "Customer", "Evangelist"]),
            "deal_stage": random.choice(DEAL_STAGES),
            "lifetime_value": round(np.random.lognormal(mean=11.5, sigma=0.6), 2),
            "created_at": fake.date_between(start_date="-3y", end_date="-3m"),
        })
    return pd.DataFrame(rows)

def make_contacts(clients: pd.DataFrame) -> pd.DataFrame:
    rows = []
    contact_id = 1
    for _, c in clients.iterrows():
        for _ in range(random.randint(*CONTACTS_PER_CLIENT)):
            rows.append({
                "contact_id": contact_id,
                "client_id": c["client_id"],
                "full_name": fake.name(),
                "title": random.choice(["Head of Procurement", "CTO", "COO", "VP Operations", "IT Manager"]),
                "email": fake.unique.email(),
                "phone": fake.phone_number(),
                "linkedin": f"https://www.linkedin.com/in/{fake.user_name()}",
                "is_primary": False
            })
            contact_id += 1

    # Mark first per client as primary
    df = pd.DataFrame(rows)
    df.sort_values(["client_id", "contact_id"], inplace=True)
    df.loc[df.groupby("client_id").head(1).index, "is_primary"] = True
    return df

# ----------------------------
# 2) Monthly Metrics
# ----------------------------
def make_metrics(clients: pd.DataFrame, months: int) -> pd.DataFrame:
    month_starts = daterange_months(date.today(), months)
    rows = []
    for _, c in clients.iterrows():
        base_spend = np.random.uniform(8000, 60000)
        satisfaction = np.random.uniform(60, 90)  # 0–100
        churn_risk = np.random.uniform(5, 25)     # 0–100

        for m in month_starts:
            spend = base_spend * np.random.uniform(0.8, 1.2)
            # Update over time a tiny bit
            satisfaction = clamp(satisfaction + np.random.normal(0, 2), 20, 100)
            churn_risk  = clamp(churn_risk + np.random.normal(0, 1.5), 0, 100)
            open_tickets = int(max(0, np.random.poisson(1.2)))
            rows.append({
                "client_id": c["client_id"],
                "month": m.isoformat(),
                "spend": round(spend, 2),
                "satisfaction_score": round(satisfaction, 1),
                "churn_risk": round(churn_risk, 1),
                "open_tickets": open_tickets,
                "renewal_due": random.choice([0, 0, 0, 1])  # sparse
            })
    return pd.DataFrame(rows)

# ----------------------------
# 3) Interactions (emails/calls/meetings)
# ----------------------------
LOREM_SNIPPETS = [
    "Discussed delivery delays; client asked for clearer ETA.",
    "Positive feedback on onboarding; interested in analytics add-on.",
    "Requested pricing for premium support.",
    "Escalated bug impacted batch processing last week.",
    "Renewal call scheduled; want case studies for healthcare sector.",
    "Asked for integration with SAP; timeline concerns remain.",
    "Happy with performance improvements since last sprint.",
    "Considering downsizing license seats next quarter.",
]

def random_datetime_in_last_n_days(n=180):
    days_ago = random.randint(0, n)
    dt = datetime.now() - timedelta(days=days_ago, hours=random.randint(0,23), minutes=random.randint(0,59))
    return dt.replace(second=0, microsecond=0)

def make_interactions(clients: pd.DataFrame) -> pd.DataFrame:
    rows = []
    iid = 1
    for _, c in clients.iterrows():
        n_int = random.randint(*INTERACTIONS_PER_CLIENT)
        for _ in range(n_int):
            rows.append({
                "interaction_id": iid,
                "client_id": c["client_id"],
                "timestamp": random_datetime_in_last_n_days().isoformat(),
                "channel": random.choice(CHANNELS),
                "owner_name": c["owner_name"],
                "notes": random.choice(LOREM_SNIPPETS),
                "sentiment": random.choice(["negative", "neutral", "positive"])
            })
            iid += 1
    return pd.DataFrame(rows)

# ----------------------------
# 4) Tickets
# ----------------------------
def make_tickets(clients: pd.DataFrame) -> pd.DataFrame:
    rows = []
    tid = 1
    for _, c in clients.iterrows():
        for _ in range(random.randint(*TICKETS_PER_CLIENT)):
            opened = random_datetime_in_last_n_days(200)
            resolved = opened + timedelta(days=random.randint(0, 21))
            status = random.choice(["Open", "Pending", "Resolved"])
            if status != "Resolved":
                resolved = None
            rows.append({
                "ticket_id": tid,
                "client_id": c["client_id"],
                "category": random.choice(TICKET_CATS),
                "status": status,
                "opened_at": opened.isoformat(),
                "resolved_at": resolved.isoformat() if resolved else None,
                "resolution_time_days": (resolved - opened).days if resolved else None,
                "priority": random.choice(["Low", "Medium", "High"])
            })
            tid += 1
    return pd.DataFrame(rows)

# ----------------------------
# 5) Meeting notes (RAG corpus)
# ----------------------------
NOTE_TEMPLATES = [
    "Met with {contact} ({title}) to review Q{qtr} goals. Main concern: {concern}. Interested in {interest}. Next step: {next_step}.",
    "Call recap: Discussed {concern}. Client sentiment {sent}. Considering {interest}. Need follow-up on {next_step}.",
    "Quarterly review: Performance {perf}. Budget {budget}. Risk {risk}. Action: {next_step}.",
]

def synth_note_text(company: str) -> str:
    contact = fake.name()
    title = random.choice(["CTO", "COO", "IT Manager", "Head of Procurement", "Ops Director"])
    concern = random.choice(["deployment delays", "data accuracy", "integration with ERP", "support responsiveness"])
    interest = random.choice(["analytics add-on", "premium support", "volume discount", "multi-year deal"])
    next_step = random.choice(["send case studies", "schedule demo", "share revised quote", "draft SoW"])
    sent = random.choice(["neutral", "positive", "mixed", "negative"])
    perf = random.choice(["improving", "stable", "declining"])
    budget = random.choice(["tight", "flexible", "under review"])
    risk = random.choice(["low", "moderate", "elevated"])

    tpl = random.choice(NOTE_TEMPLATES)
    qtr = (datetime.now().month - 1) // 3 + 1
    return tpl.format(
        contact=contact, title=title, qtr=qtr,
        concern=concern, interest=interest, next_step=next_step,
        sent=sent, perf=perf, budget=budget, risk=risk
    ) + f"\n\nCompany: {company}\nDate: {fake.date_between(start_date='-6M', end_date='today')}"

def write_notes_for_clients(clients: pd.DataFrame):
    for _, c in clients.iterrows():
        n_notes = random.randint(*NOTES_PER_CLIENT)
        company_slug = c['company_name'].lower().replace(" ", "_").replace(".", "")
        for i in range(1, n_notes + 1):
            text = synth_note_text(c["company_name"])
            path = NOTES_DIR / f"{company_slug}_{i}.txt"
            path.write_text(text, encoding="utf-8")

# ----------------------------
# Main
# ----------------------------
def main():
    ensure_dirs()

    clients = make_clients(N_CLIENTS)
    contacts = make_contacts(clients)
    metrics = make_metrics(clients, MONTHS)
    interactions = make_interactions(clients)
    tickets = make_tickets(clients)

    clients.to_csv(RAW_DIR / "clients.csv", index=False)
    contacts.to_csv(RAW_DIR / "contacts.csv", index=False)
    metrics.to_csv(RAW_DIR / "metrics.csv", index=False)
    interactions.to_csv(RAW_DIR / "interactions.csv", index=False)
    tickets.to_csv(RAW_DIR / "tickets.csv", index=False)

    write_notes_for_clients(clients)

    print("✅ Synthetic data generated:")
    for p in [
        RAW_DIR / "clients.csv",
        RAW_DIR / "contacts.csv",
        RAW_DIR / "metrics.csv",
        RAW_DIR / "interactions.csv",
        RAW_DIR / "tickets.csv",
    ]:
        print(" -", p.as_posix())
    print("🗒️ Notes in:", NOTES_DIR.as_posix())

if __name__ == "__main__":
    main()
