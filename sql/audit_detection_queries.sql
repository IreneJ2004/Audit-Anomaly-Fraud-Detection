-- =====================================================================
-- AUDIT ANOMALY DETECTION SYSTEM — Core SQL Queries
-- Target: gl_transactions table (SQLite dialect, portable to
--         PostgreSQL/SQL Server with minor date-function changes)
-- =====================================================================


-- ---------------------------------------------------------------------
-- 1. BENFORD'S LAW — Leading Digit Frequency Test
-- Naturally occurring financial figures follow a known, non-uniform
-- distribution of leading digits (digit '1' appears ~30% of the time,
-- '9' only ~4.6%). Large deviations from this expected distribution
-- across an account or vendor can indicate manual/fabricated entries.
-- ---------------------------------------------------------------------
WITH leading_digits AS (
    SELECT
        txn_id,
        account_code,
        amount,
        -- extract the first digit of the amount regardless of magnitude
        CAST(SUBSTR(CAST(CAST(amount AS INTEGER) AS TEXT), 1, 1) AS INTEGER) AS first_digit
    FROM gl_transactions
    WHERE amount >= 1
),
observed AS (
    SELECT
        first_digit,
        COUNT(*) AS observed_count,
        ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM leading_digits), 2) AS observed_pct
    FROM leading_digits
    GROUP BY first_digit
),
benford_expected (first_digit, expected_pct) AS (
    VALUES (1,30.1),(2,17.6),(3,12.5),(4,9.7),(5,7.9),
           (6,6.7),(7,5.8),(8,5.1),(9,4.6)
)
SELECT
    o.first_digit,
    o.observed_count,
    o.observed_pct,
    e.expected_pct,
    ROUND(o.observed_pct - e.expected_pct, 2) AS variance_pct
FROM observed o
JOIN benford_expected e ON o.first_digit = e.first_digit
ORDER BY o.first_digit;
-- Interpretation: digits 7/8/9 significantly over-represented vs. expected
-- flags the "benford_break" transactions we deliberately injected.


-- ---------------------------------------------------------------------
-- 2. DUPLICATE INVOICE DETECTION
-- Same vendor + same amount within a short date window = likely
-- duplicate payment (a classic overpayment / fraud risk).
-- ---------------------------------------------------------------------
WITH ranked AS (
    SELECT
        txn_id, vendor_name, amount, txn_date,
        LAG(txn_date) OVER (
            PARTITION BY vendor_name, amount ORDER BY txn_date
        ) AS prev_date_same_amount
    FROM gl_transactions
)
SELECT
    txn_id, vendor_name, amount, txn_date, prev_date_same_amount,
    JULIANDAY(txn_date) - JULIANDAY(prev_date_same_amount) AS days_between
FROM ranked
WHERE prev_date_same_amount IS NOT NULL
  AND JULIANDAY(txn_date) - JULIANDAY(prev_date_same_amount) <= 7
ORDER BY vendor_name, txn_date;


-- ---------------------------------------------------------------------
-- 3. JUST-UNDER-APPROVAL-THRESHOLD DETECTION ("Structuring")
-- Transactions sitting suspiciously close (within 3%) below a known
-- approval limit (Rs 5,00,000) may indicate deliberate splitting to
-- avoid manager/partner review — a classic structuring red flag.
-- ---------------------------------------------------------------------
SELECT
    txn_id, vendor_name, account_name, amount, txn_date, approved_by,
    ROUND(500000 - amount, 2) AS amount_below_threshold
FROM gl_transactions
WHERE amount BETWEEN 485000 AND 499999.99
ORDER BY amount DESC;


-- ---------------------------------------------------------------------
-- 4. WEEKEND / OFF-CYCLE POSTING DETECTION
-- Transactions posted on Saturday/Sunday are unusual for routine
-- vendor invoices and warrant closer inspection.
-- SQLite: strftime('%w', date) returns 0=Sunday .. 6=Saturday
-- ---------------------------------------------------------------------
SELECT
    txn_id, vendor_name, account_name, amount, txn_date, approved_by,
    CASE strftime('%w', txn_date)
        WHEN '0' THEN 'Sunday'
        WHEN '6' THEN 'Saturday'
    END AS weekend_day
FROM gl_transactions
WHERE strftime('%w', txn_date) IN ('0', '6')
ORDER BY txn_date;


-- ---------------------------------------------------------------------
-- 5. ROUND-NUMBER TRANSACTION DETECTION
-- Genuine invoices rarely land on perfectly round figures; a cluster
-- of exact round amounts (Rs 1,00,000 / 5,00,000 / 10,00,000...) is a
-- classic red flag for estimation or fabrication.
-- ---------------------------------------------------------------------
SELECT
    txn_id, vendor_name, account_name, amount, txn_date
FROM gl_transactions
WHERE amount = ROUND(amount, -4)   -- amount is an exact multiple of 10,000
  AND amount >= 100000
ORDER BY amount DESC;


-- ---------------------------------------------------------------------
-- 6. MONETARY UNIT SAMPLING (MUS) — Audit Sample Selection
-- Selects transactions for audit testing with probability proportional
-- to their dollar value (larger transactions = higher sampling chance),
-- the real technique auditors use instead of pure random sampling.
-- Approach: cumulative amount + systematic interval selection.
-- ---------------------------------------------------------------------
WITH cum AS (
    SELECT
        txn_id, vendor_name, account_name, amount, txn_date,
        SUM(amount) OVER (ORDER BY txn_id) AS running_total,
        SUM(amount) OVER () AS grand_total
    FROM gl_transactions
),
sample_params AS (
    SELECT grand_total / 40 AS sampling_interval   -- targeting ~40 sample items
    FROM cum LIMIT 1
)
SELECT c.txn_id, c.vendor_name, c.account_name, c.amount, c.txn_date
FROM cum c, sample_params p
WHERE CAST(c.running_total / p.sampling_interval AS INTEGER)
    <> CAST((c.running_total - c.amount) / p.sampling_interval AS INTEGER)
ORDER BY c.txn_id;


-- ---------------------------------------------------------------------
-- 7. MATERIALITY-BASED VARIANCE SUMMARY BY ACCOUNT
-- Aggregates spend by account and flags accounts whose total exceeds
-- a materiality threshold (set at 5% of total GL value here).
-- ---------------------------------------------------------------------
WITH account_totals AS (
    SELECT
        account_code, account_name,
        COUNT(*) AS txn_count,
        SUM(amount) AS total_amount
    FROM gl_transactions
    GROUP BY account_code, account_name
),
grand_total AS (
    SELECT SUM(amount) AS total FROM gl_transactions
)
SELECT
    a.account_code, a.account_name, a.txn_count, a.total_amount,
    ROUND(100.0 * a.total_amount / g.total, 2) AS pct_of_total,
    CASE WHEN a.total_amount > 0.05 * g.total THEN 'ABOVE MATERIALITY'
         ELSE 'below materiality' END AS materiality_flag
FROM account_totals a, grand_total g
ORDER BY a.total_amount DESC;
