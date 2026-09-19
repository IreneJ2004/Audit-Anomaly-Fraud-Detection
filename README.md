# Audit Anomaly & Fraud Detection System

## Project Overview

This project focuses on building an end-to-end audit analytics workflow for identifying potentially anomalous and high-risk General Ledger (GL) transactions.

The objective is to combine traditional audit-oriented detection rules with statistical and machine-learning techniques to create a practical transaction-level risk assessment process.

The analysis uses a synthetic FY 2024–25 Indian GL dataset containing 15,250 transactions. The dataset was designed to represent realistic corporate expense and accounting activity while embedding five known anomaly patterns for evaluation:

- Round-number transactions
- Transactions just below the approval threshold
- Weekend postings
- Duplicate invoice patterns
- Benford's Law deviations

The workflow combines:

**SQL → Audit Rules → Machine Learning → Hybrid Risk Scoring → Materiality Analysis → Power BI**

Rather than treating machine learning as a standalone fraud detector, the project uses it alongside rule-based audit tests. This provides both explainable audit indicators and a broader anomaly-detection layer.

The final output is a scored transaction dataset and an interactive Power BI dashboard that can be used to prioritize transactions for further investigation.

## Business Objective & Audit Context

The primary objective is to support the audit review process by identifying GL transactions that exhibit characteristics commonly associated with higher audit risk.

The analysis focuses on four practical questions:

1. Which transactions show unusual or potentially suspicious characteristics?
2. Which vendors, accounts, and periods contain a higher concentration of flagged activity?
3. Which transactions should be prioritized for further investigation?
4. How can rule-based audit procedures be complemented by machine-learning-based anomaly detection?

The project is designed as an analytical screening and prioritization system. A flagged transaction is not treated as confirmed fraud; it represents a transaction requiring further review based on the available indicators.

This distinction is important in an audit context, where analytical procedures can help identify areas requiring additional investigation but do not independently establish fraud.

## Dataset & Data Generation

The project uses a synthetic General Ledger dataset representing FY 2024–25 accounting activity.

### Dataset Summary

| Attribute | Details |
|---|---|
| Financial Year | FY 2024–25 |
| Total Transactions | 15,250 |
| Normal Transactions | 14,000 |
| Anomaly-labelled Transactions | 1,250 |
| Accounts | 10 |
| Vendors | 25 |
| Employees / Approvers | 60 |
| Approval Threshold | ₹5,00,000 |

The dataset was generated programmatically using Python to create a controlled environment for testing audit detection techniques.

The transaction population contains a mixture of baseline accounting activity and intentionally embedded anomaly patterns. Each injected anomaly is retained in a ground-truth `answer_key`, allowing the detection methods to be evaluated using precision and recall rather than relying only on visual inspection.

### Embedded Anomaly Patterns

| Anomaly Type | Purpose |
|---|---|
| Round-number transactions | Identify unusually rounded transaction amounts |
| Just-under-threshold transactions | Identify transactions clustered immediately below the approval threshold |
| Weekend postings | Identify transactions posted on Saturdays or Sundays |
| Duplicate invoice patterns | Identify repeated vendor and amount combinations within a short period |
| Benford's Law deviations | Identify unusual first-digit distributions |

The synthetic nature of the dataset means the project demonstrates the analytical methodology and implementation rather than making claims about real-world fraudulent entities or transactions.

## Technology Stack

- **Python** — Synthetic data generation, feature engineering, anomaly detection and evaluation
- **Pandas / NumPy** — Data preparation and numerical analysis
- **Scikit-learn** — Isolation Forest anomaly detection
- **SQLite** — Transaction storage and audit-oriented SQL analysis
- **SQL** — Rule-based audit tests and transaction investigation
- **Excel** — Materiality calculation and audit prioritization
- **Power BI** — Interactive audit dashboard and investigation queue

## Analytical Workflow

The project follows an end-to-end analytical workflow:

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

## Detection Methodology

The detection framework uses two complementary approaches:

1. **Rule-based audit detection**
2. **Machine-learning-based anomaly detection**

The outputs are then combined into a hybrid detection layer and converted into a transaction-level risk score.

### 1. Rule-Based Audit Detection

The following audit-oriented rules were implemented:

| Detection Rule | Description |
|---|---|
| Round Number | Flags high-value transactions with unusually rounded amounts |
| Just Under Threshold | Flags transactions between ₹4,85,000 and ₹4,99,999.99 |
| Weekend Posting | Flags transactions posted on Saturdays or Sundays |
| Duplicate Invoice | Identifies repeated vendor and amount combinations occurring within a short period |

These rules provide interpretable indicators that can be directly reviewed by an auditor.

### 2. Machine Learning Detection

An **Isolation Forest** model was used as an unsupervised anomaly-detection technique.

The model uses transaction-level features including:

- Transaction amount
- Vendor transaction frequency
- Account-level amount behaviour
- Day of week
- Month-end indicator
- Rule-based flags
- Leading-digit characteristics

The model identifies observations that differ from the broader transaction population without requiring the model itself to know which transactions are anomalous.

### 3. Hybrid Detection

The final detection layer combines the rule-based and machine-learning outputs:

```text
Rule Flags + ML Flag
       ↓
Hybrid Flag

### 4. Risk Scoring

Each transaction receives a risk score based on a combination of:

- Machine-learning anomaly score
- Number of rule-based indicators triggered

The two components are combined into a single transaction-level score:

**Risk Score = 50% ML Anomaly Score + 50% Rule-Based Score**

The rule-based component is calculated from the number of audit rules triggered, while the machine-learning component is normalized before being combined.

The resulting score is used to prioritize transactions for investigation.

A higher risk score indicates that a transaction has a greater concentration of anomaly indicators within this analytical framework. It does not represent a probability of fraud or establish that fraud occurred.

## SQL Audit Tests

SQL was used to perform targeted audit-oriented tests against the SQLite transaction database.

The implemented tests include:

1. **Benford's Law Analysis** — compares the observed first-digit distribution of transaction amounts with the expected Benford distribution.
2. **Duplicate Invoice Detection** — identifies repeated vendor and transaction-amount combinations occurring within a short time period.
3. **Approval Threshold Analysis** — identifies transactions recorded immediately below the ₹5,00,000 approval threshold.
4. **Weekend Posting Analysis** — identifies transactions posted on Saturdays and Sundays.
5. **Round-Number Analysis** — identifies high-value transactions with unusually rounded amounts.
6. **Monetary Unit Sampling (MUS)** — selects transactions using a monetary-unit-based sampling approach.
7. **Materiality-Based Analysis** — compares account-level transaction values against the defined materiality threshold.

These tests provide an audit-focused SQL layer before the machine-learning detection stage.

The SQL results are used as analytical indicators and investigation inputs rather than as evidence that a transaction is fraudulent.

## Python Anomaly Detection & Evaluation

The Python detection layer combines rule-based indicators with an unsupervised machine-learning model.

### Isolation Forest

An Isolation Forest model was trained using transaction-level behavioural features.

The model configuration used:

- **Number of estimators:** 300
- **Contamination:** 5%
- **Random state:** 42

The model generates an anomaly score for each transaction and identifies observations that appear unusual relative to the broader transaction population.

### Detection Performance

Because the synthetic dataset contains known anomaly labels, the detection results can be evaluated against the ground truth using precision and recall.

| Detection Approach | Transactions Flagged | Precision | Recall |
|---|---:|---:|---:|
| Rules Only | 767 | 83.7% | 51.4% |
| Isolation Forest Only | 763 | 62.6% | 38.2% |
| Hybrid (Rules + ML) | 969 | 70.6% | 54.7% |

The rule-based approach provides highly interpretable detection, while the machine-learning layer identifies additional behavioural patterns.

The hybrid approach combines both layers to provide broader transaction screening while retaining the underlying rule indicators for investigation.

Precision and recall are evaluated against the synthetic ground truth created during data generation. These metrics therefore demonstrate the performance of the implemented methodology on the controlled dataset and should not be interpreted as real-world fraud-detection accuracy.

## Materiality Analysis

Excel was used to add an audit materiality layer to the transaction analysis.

The materiality calculator uses the total GL transaction value for FY 2024–25 and applies defined percentage assumptions to establish different levels of audit significance.

### Materiality Framework

| Measure | Assumption / Result |
|---|---:|
| Total GL Transaction Value | ₹747,159,231.80 |
| Overall Materiality | 5% |
| Performance Materiality | 75% of Overall Materiality |
| Individually Significant Threshold | 50% of Overall Materiality |
| Approval Sub-Threshold | ₹4,85,000 |

Based on these assumptions:

- **Overall Materiality:** ₹37,357,961.59
- **Performance Materiality:** ₹28,018,471.19
- **Individually Significant Threshold:** ₹18,678,980.80

The materiality analysis is used as a prioritization layer alongside the anomaly-detection results.

Materiality does not determine whether an individual transaction is anomalous or fraudulent. Instead, it provides an additional financial-significance perspective for deciding which areas may warrant greater audit attention.

The workbook is formula-driven so that the materiality calculations update when the underlying assumptions or transaction values change.

## Power BI Dashboard

The final analysis is presented through an interactive Power BI dashboard designed to support audit review and investigation prioritization.

The dashboard includes:

- **Total Transactions** — overall transaction population
- **Hybrid Flagged Transactions** — transactions identified by the combined detection framework
- **Flagged Transaction Value** — total value of hybrid-flagged transactions
- **Anomalies by Detection Method** — comparison of rule-based and ML detection indicators
- **Flagged Transaction Value by Account** — identifies accounts containing higher-value flagged activity
- **Monthly Flagged Transaction Value** — shows flagged transaction value across the financial year
- **High-Risk Transactions — Investigation Queue** — displays transactions with a risk score of 60 or above for further review

The dashboard is structured around an audit-review workflow:

**Population Overview → Detection Patterns → Financial Exposure → Time Trends → Investigation Queue**

The investigation queue is intended to help an auditor or analyst prioritize transactions for further examination rather than automatically conclude that a transaction represents fraud.

## Key Results

The completed workflow produced the following analytical outputs:

- **15,250** synthetic GL transactions processed end-to-end.
- **969** transactions identified by the hybrid detection framework.
- **₹396.76 million** in transaction value associated with hybrid-flagged transactions.
- **7** transactions with risk scores of 60 or above displayed in the investigation queue.
- **40** transactions selected through the Monetary Unit Sampling analysis.
- SQL-based audit tests were performed for duplicate transactions, approval-threshold patterns, weekend postings, round-number transactions, Benford's Law, MUS, and materiality.
- The anomaly-detection framework was evaluated against known synthetic ground-truth labels using precision and recall.
- The final Power BI dashboard provides a consolidated view of transaction population, detection methods, financial exposure, monthly trends, and high-risk transactions.

These results demonstrate how multiple analytical techniques can be combined into a structured audit-screening workflow.

## Project Structure

```text
Project_1_Audit_Anomaly_Fraud/
│
├── README.md
│
├── data/
│   ├── gl_transactions.csv
│   ├── gl_transactions_scored.csv
│   └── audit.db
│
├── python/
│   ├── generate_data.py
│   ├── load_db.py
│   └── detect_anomalies.py
│
├── sql/
│   └── audit_detection_queries.sql
│
├── excel/
│   └── materiality_calculator.xlsx
│
├── powerbi/
│   └── Audit_Anomaly_Fraud_Dashboard.pbix
│
└── outputs/


## Limitations & Audit Considerations

This project is designed as an analytical screening and prioritization framework. Several limitations should be considered when interpreting the results.

- The dataset is **synthetic**, so the results demonstrate the methodology rather than representing findings from a real organization.
- The anomaly patterns were intentionally embedded during data generation, which allows controlled evaluation but does not reproduce the full complexity of real-world fraud.
- Rule-based tests can produce false positives because unusual transactions are not necessarily inappropriate transactions.
- Isolation Forest is an unsupervised anomaly-detection method and identifies statistical outliers rather than confirmed fraudulent activity.
- Benford's Law analysis should be interpreted carefully because first-digit distributions can vary depending on the nature and characteristics of the underlying population.
- Materiality thresholds used in the project are analytical assumptions for demonstrating the workflow and should not be interpreted as an actual audit firm's materiality determination.
- A flagged transaction requires further investigation and supporting evidence before any conclusion about error, control weakness, or fraud can be made.

The project therefore treats anomaly detection as a tool for **risk identification and investigation prioritization**, rather than as a replacement for professional audit judgement.

## How to Run

### 1. Generate the Synthetic Dataset

From the project root:

```cmd
python python\generate_data.py

python python\load_db.py

sql/audit_detection_queries.sql

python python\detect_anomalies.py

excel/materiality_calculator.xlsx

powerbi/Audit_Anomaly_Fraud_Dashboard.pbix





