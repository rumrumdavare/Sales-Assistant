from pathlib import Path
import sqlite3
import sys
import pandas as pd

DB_PATH = Path("local.db")
RAW_DIR = Path("data/raw")

# Load order respects FKs: parent tables first
TABLE_FILES = [
    ("clients",      RAW_DIR / "clients.csv"),
    ("contacts",     RAW_DIR / "contacts.csv"),
    ("metrics",      RAW_DIR / "metrics.csv"),
    ("interactions", RAW_DIR / "interactions.csv"),
    ("tickets",      RAW_DIR / "tickets.csv"),
]

# Optional dtype nudges (keeps inserts tidy; ignores if column missing)
DTYPES = {
    "clients":      {"client_id": "int64", "annual_revenue": "float64", "lifetime_value": "float64"},
    "contacts":     {"contact_id": "int64", "client_id": "int64", "is_primary": "int64"},
    "metrics":      {"client_id": "int64", "spend": "float64", "satisfaction_score": "float64",
                     "churn_risk": "float64", "open_tickets": "int64", "renewal_due": "int64"},
    "interactions": {"interaction_id": "int64", "client_id": "int64"},
    "tickets":      {"ticket_id": "int64", "client_id": "int64", "resolution_time_days": "float64"},
}

def ensure_paths():
    if not DB_PATH.exists():
        sys.exit("DB not found. Run scripts\\init_db.py first.")
    missing = [(t, p) for t, p in TABLE_FILES if not p.exists()]
    if missing:
        lines = "\n".join(f" - {t}: {p}" for t, p in missing)
        sys.exit(f"Missing CSVs in data/raw:\n{lines}")

def truncate_tables(conn: sqlite3.Connection):
    """Optional: clear existing rows for idempotent seeding."""
    # Order matters due to FKs
    for tbl in ("tickets", "interactions", "metrics", "contacts", "clients"):
        conn.execute(f"DELETE FROM {tbl};")

def load_table(conn: sqlite3.Connection, table: str, csv_path: Path):
    df = pd.read_csv(csv_path)
    # Apply gentle dtype conversions (ignore if column missing)
    for col, typ in DTYPES.get(table, {}).items():
        if col in df.columns:
            df[col] = df[col].astype(typ, errors="ignore")
    df.to_sql(table, conn, if_exists="append", index=False)
    return len(df)

def main():
    ensure_paths()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("PRAGMA foreign_keys=ON;")
        # Make seeding repeatable: clear tables before inserting
        truncate_tables(conn)

        print("[seed] Loading tables from data/raw ...")
        total = 0
        for table, path in TABLE_FILES:
            n = load_table(conn, table, path)
            total += n
            print(f"  → {table:<13} +{n:,} rows")
        print(f"[seed] Done. Inserted {total:,} rows total into {DB_PATH.resolve()}")

        # Quick counts summary
        print("[seed] Row counts:")
        for table, _ in TABLE_FILES:
            (cnt,) = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            print(f"  - {table:<13} {cnt:,}")

if __name__ == "__main__":
    main()
