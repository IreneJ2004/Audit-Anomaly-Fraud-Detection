"""
Rules-Based + ML Hybrid Anomaly Detection
-------------------------------------------
Step 1: Reproduce the rule-based flags from SQL (round number, weekend,
        just-under-threshold, duplicate) directly in pandas so we have a
        single feature table.
Step 2: Engineer features and run an Isolation Forest to catch anomalies
        the fixed rules might miss (multivariate, not just single-rule).
Step 3: Combine both into a final risk score and compare detection
        performance (precision/recall) against the true_anomaly_flag
        answer key we set aside during data generation.
"""

import sqlite3
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_ROOT / "data" / "audit.db"

conn = sqlite3.connect(DB_PATH)
gl = pd.read_sql("SELECT * FROM gl_transactions", conn)
answer_key = pd.read_sql("SELECT * FROM answer_key", conn)
conn.close()

gl["txn_date"] = pd.to_datetime(gl["txn_date"])
gl = gl.sort_values("txn_date").reset_index(drop=True)

# ------------------------------------------------------------------
# RULE-BASED FLAGS (mirrors the SQL logic — kept consistent on purpose)
# ------------------------------------------------------------------
gl["flag_round_number"] = ((gl["amount"] % 10000 == 0) & (gl["amount"] >= 100000)).astype(int)
gl["flag_weekend"] = gl["txn_date"].dt.dayofweek.isin([5, 6]).astype(int)
gl["flag_just_under_threshold"] = gl["amount"].between(485000, 499999.99).astype(int)

# duplicate: same vendor + same amount within 7 days
gl_sorted = gl.sort_values(["vendor_name", "amount", "txn_date"])
gl_sorted["prev_date"] = gl_sorted.groupby(["vendor_name", "amount"])["txn_date"].shift(1)
gl_sorted["days_since_prev"] = (gl_sorted["txn_date"] - gl_sorted["prev_date"]).dt.days
gl_sorted["flag_duplicate"] = (gl_sorted["days_since_prev"] <= 7).fillna(False).astype(int)
gl = gl.merge(gl_sorted[["txn_id", "flag_duplicate"]], on="txn_id", how="left")

gl["rule_flag_count"] = gl[[
    "flag_round_number", "flag_weekend", "flag_just_under_threshold", "flag_duplicate"
]].sum(axis=1)
gl["rules_flagged"] = (gl["rule_flag_count"] >= 1).astype(int)

# ------------------------------------------------------------------
# ML LAYER — Isolation Forest on engineered numeric features
# ------------------------------------------------------------------
vendor_freq = gl["vendor_name"].value_counts()
gl["vendor_txn_frequency"] = gl["vendor_name"].map(vendor_freq)

# Z-score of amount relative to its own account's mean/std -- normalizes
# "how unusual is this amount" per account, rather than globally (Rs 10L
# is normal for Equipment Purchases but very unusual for Office Supplies).
acct_mean = gl.groupby("account_code")["amount"].transform("mean")
acct_std = gl.groupby("account_code")["amount"].transform("std")
gl["account_zscore"] = (gl["amount"] - acct_mean) / acct_std

gl["day_of_week"] = gl["txn_date"].dt.dayofweek
gl["is_month_end"] = (gl["txn_date"].dt.day >= 28).astype(int)

# Log-transform the raw amount: financial amounts are heavily right-skewed
# (a few very large transactions), so without this the Isolation Forest's
# distance-based splits are dominated by scale, drowning out the other
# behavioural features. This is standard practice for monetary features in ML.
gl["log_amount"] = np.log1p(gl["amount"])

# Leading-digit "rarity" score (ties back to Benford's Law): digits that
# should be rare (7/8/9) get a higher rarity weight than common ones (1/2).
gl["leading_digit"] = gl["amount"].astype(int).astype(str).str[0].astype(int)
gl["leading_digit_rarity"] = gl["leading_digit"].map(
    {1: 0.1, 2: 0.2, 3: 0.3, 4: 0.4, 5: 0.5, 6: 0.6, 7: 0.8, 8: 0.9, 9: 1.0}
)

feature_cols = [
    "log_amount", "vendor_txn_frequency", "account_zscore",
    "day_of_week", "is_month_end", "flag_round_number", "flag_weekend",
    "leading_digit_rarity"
]
X = gl[feature_cols].fillna(0)

iso = IsolationForest(
    n_estimators=300, contamination=0.05, random_state=42
)
gl["ml_anomaly_score"] = -iso.fit(X).score_samples(X)  # higher = more anomalous
gl["ml_flagged"] = (iso.predict(X) == -1).astype(int)

# ------------------------------------------------------------------
# COMBINE — Hybrid risk score (rules OR ml, plus a 0-100 risk score)
# ------------------------------------------------------------------
gl["hybrid_flagged"] = ((gl["rules_flagged"] == 1) | (gl["ml_flagged"] == 1)).astype(int)

# Normalize ML score to 0-100 and blend with rule_flag_count for a final score
ml_norm = 100 * (gl["ml_anomaly_score"] - gl["ml_anomaly_score"].min()) / (
    gl["ml_anomaly_score"].max() - gl["ml_anomaly_score"].min()
)
gl["risk_score"] = (0.5 * ml_norm + 0.5 * (gl["rule_flag_count"] / 4 * 100)).round(1)

# ------------------------------------------------------------------
# VALIDATE — compare against the ground-truth answer key
# ------------------------------------------------------------------
eval_df = gl.merge(answer_key, on="txn_id")
eval_df["true_anomaly"] = (eval_df["true_anomaly_flag"] != "none").astype(int)


def precision_recall(pred_col):
    tp = ((eval_df[pred_col] == 1) & (eval_df["true_anomaly"] == 1)).sum()
    fp = ((eval_df[pred_col] == 1) & (eval_df["true_anomaly"] == 0)).sum()
    fn = ((eval_df[pred_col] == 0) & (eval_df["true_anomaly"] == 1)).sum()
    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    flagged = eval_df[pred_col].sum()
    return precision, recall, flagged


print("=" * 60)
print("DETECTION PERFORMANCE vs GROUND TRUTH")
print("=" * 60)
for method, col in [
    ("Rules only", "rules_flagged"),
    ("ML only (Isolation Forest)", "ml_flagged"),
    ("Hybrid (Rules + ML)", "hybrid_flagged"),
]:
    p, r, n = precision_recall(col)
    print(f"{method:32s} | flagged={n:5d} | precision={p:.1%} | recall={r:.1%}")

# ------------------------------------------------------------------
# EXPORT for Power BI / Excel
# ------------------------------------------------------------------
export_cols = [
    "txn_id", "txn_date", "account_code", "account_name", "vendor_name",
    "approved_by", "amount", "flag_round_number", "flag_weekend",
    "flag_just_under_threshold", "flag_duplicate", "rule_flag_count",
    "ml_flagged", "hybrid_flagged", "risk_score"
]
out_path = PROJECT_ROOT / "data" / "gl_transactions_scored.csv"
gl[export_cols].sort_values("risk_score", ascending=False).to_csv(out_path, index=False)
print(f"\nScored dataset exported -> {out_path}")
print(f"\nTop 5 highest-risk transactions:")
print(gl[export_cols].sort_values("risk_score", ascending=False).head(5).to_string(index=False))
