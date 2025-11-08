PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS clients (
  client_id        INTEGER PRIMARY KEY,         -- from CSV
  company_name     TEXT    NOT NULL,
  industry         TEXT,
  region           TEXT,
  annual_revenue   REAL,
  owner_name       TEXT,                        -- account owner
  lifecycle_stage  TEXT,                        -- e.g., Lead, Customer, Evangelist
  deal_stage       TEXT,                        -- e.g., Prospecting, Closed Won/Lost
  lifetime_value   REAL,
  created_at       TEXT                         -- ISO date string
);

CREATE TABLE IF NOT EXISTS contacts (
  contact_id   INTEGER PRIMARY KEY,
  client_id    INTEGER    NOT NULL,
  full_name    TEXT,
  title        TEXT,
  email        TEXT,
  phone        TEXT,
  linkedin     TEXT,
  is_primary   INTEGER DEFAULT 0,               -- 0/1
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS metrics (
  client_id            INTEGER NOT NULL,
  month                TEXT    NOT NULL,        -- YYYY-MM-01 (ISO month start)
  spend                REAL,
  satisfaction_score   REAL,
  churn_risk           REAL,
  open_tickets         INTEGER,
  renewal_due          INTEGER DEFAULT 0,       -- 0/1
  PRIMARY KEY (client_id, month),
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS interactions (
  interaction_id INTEGER PRIMARY KEY,
  client_id      INTEGER NOT NULL,
  timestamp      TEXT    NOT NULL,              -- ISO datetime
  channel        TEXT,                          -- Email/Call/Meeting
  owner_name     TEXT,
  notes          TEXT,
  sentiment      TEXT,                          -- negative/neutral/positive
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS tickets (
  ticket_id             INTEGER PRIMARY KEY,
  client_id             INTEGER NOT NULL,
  category              TEXT,                   -- Billing/Technical/Delivery/Account
  status                TEXT,                   -- Open/Pending/Resolved
  opened_at             TEXT,                   -- ISO datetime
  resolved_at           TEXT,                   -- ISO datetime or NULL
  resolution_time_days  INTEGER,                -- nullable
  priority              TEXT,                   -- Low/Medium/High
  FOREIGN KEY (client_id) REFERENCES clients(client_id) ON DELETE CASCADE
);

-- Helpful indexes for common lookups
CREATE INDEX IF NOT EXISTS ix_contacts_client            ON contacts(client_id);
CREATE INDEX IF NOT EXISTS ix_metrics_client_month       ON metrics(client_id, month);
CREATE INDEX IF NOT EXISTS ix_interactions_client_time   ON interactions(client_id, timestamp);
CREATE INDEX IF NOT EXISTS ix_tickets_client_status      ON tickets(client_id, status);
