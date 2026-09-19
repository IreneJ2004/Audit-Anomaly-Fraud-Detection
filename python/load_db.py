"""Load the synthetic GL CSV into a SQLite database for SQL analysis."""
import sqlite3
import pandas as pd
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

CSV_PATH = PROJECT_ROOT / "data" / "gl_transactions.csv"
DB_PATH = PROJECT_ROOT / "data" / "audit.db"


df = pd.read_csv(CSV_PATH)

conn = sqlite3.connect(DB_PATH)
# NOTE: true_anomaly_flag is our "answer key" for validating detection later.
# In a real project this column wouldn't exist -- we keep it in a separate
# table so our detection SQL can't "cheat" by referencing it directly.
answer_key = df[["txn_id", "true_anomaly_flag"]].copy()
gl = df.drop(columns=["true_anomaly_flag"]).copy()

gl.to_sql("gl_transactions", conn, if_exists="replace", index=False)
answer_key.to_sql("answer_key", conn, if_exists="replace", index=False)

conn.execute("CREATE INDEX idx_vendor ON gl_transactions(vendor_name);")
conn.execute("CREATE INDEX idx_account ON gl_transactions(account_code);")
conn.execute("CREATE INDEX idx_date ON gl_transactions(txn_date);")
conn.commit()

print("Loaded tables:", conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table';").fetchall())
print("Row count gl_transactions:",
      conn.execute("SELECT COUNT(*) FROM gl_transactions;").fetchone()[0])
conn.close()
