# Audit Anomaly & Fraud Detection System

## Project Overview

This project builds an end-to-end audit analytics workflow for identifying anomalous and high-risk General Ledger (GL) transactions.

The core idea is to combine traditional audit detection rules with statistical and machine-learning techniques to produce a practical, transaction-level risk score — the kind of screening tool an audit analyst would actually use to decide where to look first.

The analysis runs on a synthetic FY 2024–25 Indian GL dataset of 15,250 transactions, built to reflect realistic corporate expense activity. Five known anomaly patterns were deliberately embedded into the data so detection performance could be measured, not just eyeballed:

* Round-number transactions
* Transactions just below the approval threshold
* Weekend postings
* Duplicate invoice patterns
* Benford's Law deviations

The workflow:

**SQL → Audit Rules → Machine Learning → Hybrid Risk Scoring → Materiality Analysis → Power BI**

Rather than treating machine learning as a standalone fraud detector, the project layers it on top of rule-based audit tests. Rules give explainable, defensible flags; the ML layer catches multivariate patterns the rules miss on their own.

The final output is a scored transaction dataset feeding an interactive Power BI dashboard, used to prioritize transactions for further review.

#### Business Objective \& Audit Context

The goal is to support the audit review process by surfacing GL transactions that show characteristics commonly associated with higher audit risk, and to answer four practical questions:

1. Which transactions look unusual or potentially suspicious?
2. Which vendors, accounts, and periods have a higher concentration of flagged activity?
3. Which transactions should be prioritized for investigation first?
4. How well do rule-based audit tests hold up when complemented with ML-based anomaly detection?

This is built as a screening and prioritization tool, not a fraud verdict engine — a flagged transaction means "worth a closer look," not "confirmed fraud." (See [Limitations \& Audit Considerations](#limitations--audit-considerations) for the full caveats on interpreting these results.)

#### Dataset \& Data Generation

#### Dataset Summary

|Attribute|Details|
|-|-|
|Financial Year|FY 2024–25|
|Total Transactions|15,250|
|Normal Transactions|14,000|
|Anomaly-labelled Transactions|1,250|
|Accounts|10|
|Vendors|25|
|Employees / Approvers|60|
|Approval Threshold|₹5,00,000|

The dataset is generated programmatically in Python, giving a controlled environment for testing audit detection techniques. Using synthetic data allows the detection methodology to be tested in a controlled environment while keeping the project independent of confidential financial information.

Every injected anomaly is retained in a separate ground-truth `answer\_key` table (kept apart from the detection logic itself), which lets the detection methods be scored on actual precision and recall rather than just visual inspection.

#### Embedded Anomaly Patterns

|Anomaly Type|Purpose|
|-|-|
|Round-number transactions|Identify unusually rounded transaction amounts|
|Just-under-threshold transactions|Identify transactions clustered immediately below the approval threshold|
|Weekend postings|Identify transactions posted on Saturdays or Sundays|
|Duplicate invoice patterns|Identify repeated vendor and amount combinations within a short period|
|Benford's Law deviations|Identify unusual first-digit distributions|

## Technology Stack

* **Python** — Synthetic data generation, feature engineering, anomaly detection and evaluation
* **Pandas / NumPy** — Data preparation and numerical analysis
* **Scikit-learn** — Isolation Forest anomaly detection
* **SQLite** — Transaction storage and audit-oriented SQL analysis
* **SQL** — Rule-based audit tests and transaction investigation
* **Excel** — Materiality calculation and audit prioritization
* **Power BI** — Interactive audit dashboard and investigation queue

## Analytical Workflow

```text
Synthetic GL Data Generation
            ↓
       SQLite Database
            ↓
      SQL Audit Tests
            ↓
   Python Feature Engineering
            ↓
     Isolation Forest ML
            ↓
      Hybrid Detection
            ↓
       Risk Scoring
            ↓
   Excel Materiality Analysis
            ↓
      Power BI Dashboard
```

## Detection Methodology

The detection framework uses two complementary approaches — rule-based audit detection and ML-based anomaly detection — combined into a hybrid layer and a single transaction-level risk score.

##### 1\. Rule-Based Audit Detection

|Detection Rule|Description|
|-|-|
|Round Number|Flags high-value transactions with unusually rounded amounts|
|Just Under Threshold|Flags transactions between ₹4,85,000 and ₹4,99,999.99|
|Weekend Posting|Flags transactions posted on Saturdays or Sundays|
|Duplicate Invoice|Identifies repeated vendor and amount combinations occurring within a short period|

These rules are directly interpretable — an auditor can look at a flag and immediately understand why it fired.



##### 2\. Machine Learning Detection

An **Isolation Forest** model handles unsupervised anomaly detection, using transaction-level features:

* Log-transformed transaction amount
* Vendor transaction frequency
* Account-level z-score (how unusual an amount is *relative to its own account*, not globally)
* Day of week
* Month-end indicator
* Rule-based flags
* Leading-digit rarity (a Benford's Law-informed feature)

The model isolates observations that behave differently from the broader population, without ever being told which transactions are actually anomalous.



##### 3\. Hybrid Detection

```text
Rule Flags + ML Flag
       ↓
   Hybrid Flag
```


##### 4\. Risk Scoring

Each transaction gets a risk score combining:

* The ML anomaly score (normalized to 0–100)
* The number of rule-based indicators triggered

**Risk Score = 50% ML Anomaly Score + 50% Rule-Based Score**

A higher score means a transaction has more anomaly indicators stacking up within this framework — it's a prioritization signal, not a fraud probability.


### SQL Audit Tests

Seven SQL queries run against the SQLite transaction database:

1. **Benford's Law Analysis** — compares observed first-digit distribution against the expected Benford distribution
2. **Duplicate Invoice Detection** — repeated vendor + amount combinations within a short window, using `LAG()`
3. **Approval Threshold Analysis** — transactions sitting just below the ₹5,00,000 approval limit
4. **Weekend Posting Analysis** — transactions posted on Saturdays and Sundays
5. **Round-Number Analysis** — high-value transactions with suspiciously round amounts
6. **Monetary Unit Sampling (MUS)** — selects an audit sample with probability proportional to transaction value, the same technique auditors use for real sample selection
7. **Materiality-Based Analysis** — compares account-level totals against the materiality threshold

#### Python Anomaly Detection \& Evaluation

##### Isolation Forest Configuration

* **Number of estimators:** 300
* **Contamination:** 5%
* **Random state:** 42



##### Detection Performance

Because the synthetic dataset carries known anomaly labels, detection results can be scored against ground truth:

|Detection Approach|Transactions Flagged|Precision|Recall|
|-|-:|-:|-:|
|Rules Only|767|83.7%|51.4%|
|Isolation Forest Only|763|62.6%|38.2%|
|Hybrid (Rules + ML)|969|70.6%|54.7%|

Rules alone are precise but conservative — they only catch what they're explicitly looking for. The ML layer trades some precision for the ability to catch anomalies that don't match any predefined rule. The hybrid approach improves recall by over 3 percentage points versus rules alone while keeping precision at a reasonable level.

These numbers reflect performance against synthetic ground truth on a controlled dataset — not a claim about real-world fraud-detection accuracy.



### Materiality Analysis

The materiality calculator (built in Excel, formula-driven) uses the total GL transaction value for FY 2024–25 and defined project assumptions to establish thresholds of financial significance.


##### Materiality Framework

|Measure|Assumption / Result|
|-|-:|
|Total GL Transaction Value|₹74,71,59,231.80|
|Overall Materiality|5%|
|Performance Materiality|75% of Overall Materiality|
|Individually Significant Threshold|50% of Overall Materiality|
|Approval Sub-Threshold|₹4,85,000|

Resulting thresholds:

* **Overall Materiality:** ₹3,73,57,961.59
* **Performance Materiality:** ₹2,80,18,471.19
* **Individually Significant Threshold:** ₹1,86,78,980.80

Materiality doesn't determine whether a specific transaction is anomalous — it adds a financial-significance lens on top of the anomaly scores, so review effort goes where the money actually matters. The workbook recalculates automatically if the underlying assumptions or transaction totals change.



## Power BI Dashboard

The dashboard is built around an audit-review workflow:

**Population Overview → Detection Patterns → Financial Exposure → Time Trends → Investigation Queue**

It includes:

* **Total Transactions** — overall transaction population
* **Hybrid Flagged Transactions** — transactions caught by the combined detection framework
* **Flagged Transaction Value** — total ₹ value of hybrid-flagged transactions
* **Anomalies by Detection Method** — rule-based vs. ML detection breakdown
* **Flagged Transaction Value by Account** — which accounts carry the most flagged exposure
* **Monthly Flagged Transaction Value** — flagged value trend across the financial year
* **High-Risk Transactions — Investigation Queue** — transactions with a risk score ≥ 60, ranked for review



## Key Results

* **15,250** synthetic GL transactions processed end-to-end
* **969** transactions flagged by the hybrid detection framework
* **₹39.68 crore** in transaction value tied to hybrid-flagged transactions
* **7** transactions with risk scores ≥ 60 surfaced in the investigation queue
* **40** transactions selected through Monetary Unit Sampling
* Full SQL audit-test suite covering duplicates, approval thresholds, weekend postings, round numbers, Benford's Law, MUS, and materiality
* Detection framework validated against synthetic ground-truth labels using precision and recall
* A consolidated Power BI dashboard tying together population, detection method, financial exposure, time trends, and the investigation queue



## Project Structure

```text
Project\_1\_Audit\_Anomaly\_Fraud/
│
├── README.md
│
├── data/
│   ├── gl\_transactions.csv
│   ├── gl\_transactions\_scored.csv
│   └── audit.db
│
├── python/
│   ├── generate\_data.py
│   ├── load\_db.py
│   └── detect\_anomalies.py
│
├── sql/
│   └── audit\_detection\_queries.sql
│
├── excel/
│   └── materiality\_calculator.xlsx
│
├── powerbi/
│   └── Audit\_Anomaly\_Fraud\_Dashboard.pbix
│
└── outputs/
```

#### Limitations \& Audit Considerations

This is an analytical screening and prioritization framework, not a fraud-detection verdict. A few things worth keeping in mind when interpreting the results:

* The dataset is **synthetic** — the results demonstrate the methodology, not findings from a real organization.
* Anomaly patterns were intentionally embedded during generation, which allows controlled evaluation but doesn't capture the full complexity of real-world fraud.
* Rule-based tests can produce false positives, since an unusual transaction isn't necessarily an inappropriate one.
* Isolation Forest is unsupervised — it flags statistical outliers, not confirmed fraud.
* Benford's Law results should be read carefully, since first-digit distributions can shift depending on the nature of the underlying population.
* Materiality thresholds here are analytical assumptions built to demonstrate the workflow, not an actual audit firm's materiality determination.
* Any flagged transaction needs further investigation and supporting evidence before any conclusion about error, control weakness, or fraud can be drawn.

Anomaly detection here is a tool for **risk identification and investigation prioritization** — it supports professional audit judgement, it doesn't replace it.



## How to Run

##### Prerequisites

* Python 3.10+
* Power BI Desktop (Windows) — to open the `.pbix` dashboard
* Excel — to open the materiality calculator
* A SQL client that can open a SQLite `.db` file (e.g., DB Browser for SQLite), to run the queries in `sql/audit\_detection\_queries.sql`

##### Setup

From the project root, create a virtual environment and install dependencies:

```cmd
python -m venv .venv
.venv\\Scripts\\activate
python -m pip install pandas numpy scikit-learn openpyxl
```

##### Run the pipeline

**1. Generate the synthetic dataset**

```cmd
python python\\generate\_data.py
```

**2. Load the dataset into SQLite**

```cmd
python python\\load\_db.py
```

**3. Run the SQL audit tests**
Open `data/audit.db` in a SQL client (e.g., DB Browser for SQLite) and run the queries in `sql/audit\_detection\_queries.sql`.

**4. Run the hybrid rules + ML detection**

```cmd
python python\\detect\_anomalies.py
```

This produces `data/gl\_transactions\_scored.csv`, the precision/recall summary, and the top flagged transactions.

**5. Review the materiality calculator**
Open `excel/materiality\_calculator.xlsx` in Excel.

**6. Explore the dashboard**
Open `powerbi/Audit\_Anomaly\_Fraud\_Dashboard.pbix` in Power BI Desktop.
