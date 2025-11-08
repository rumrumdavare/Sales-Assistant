from pathlib import Path
import sqlite3
import sys

DB_PATH = Path("local.db")
SCHEMA_PATH = Path("db/schema.sql")

def main():
    print(f"[init-db] schema path: {SCHEMA_PATH.resolve()}")
    if not SCHEMA_PATH.exists():
        print("[init-db] ERROR: schema file missing at db/schema.sql", file=sys.stderr)
        sys.exit(1)
    try:
        DB_PATH.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(DB_PATH) as conn, open(SCHEMA_PATH, "r", encoding="utf-8") as f:
            conn.execute("PRAGMA foreign_keys=ON;")
            conn.executescript(f.read())
        print(f"[init-db] SUCCESS: created/updated DB at {DB_PATH.resolve()}")
    except Exception as e:
        print(f"[init-db] ERROR: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
