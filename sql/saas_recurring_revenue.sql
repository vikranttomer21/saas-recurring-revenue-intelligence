CREATE DATABASE saas_recurring_revenue;
USE saas_recurring_revenue;

DROP TABLE IF EXISTS saas_subscription_ledger;
CREATE TABLE saas_subscription_ledger (
    account_id       VARCHAR(20) NOT NULL,
    company_name     VARCHAR(100) NOT NULL,
    industry         VARCHAR(50) NOT NULL,
    region           VARCHAR(50) NOT NULL,
    cohort_month     DATE NOT NULL,
    billing_month    DATE NOT NULL,
    tenure_months    INT NOT NULL,
    billing_cadence  VARCHAR(20) NOT NULL,
    plan_tier        VARCHAR(20) NOT NULL,
    licensed_seats   INT NOT NULL,
    active_users     INT NOT NULL,
    utilization_rate DECIMAL(5, 1) NOT NULL,
    health_score     INT NOT NULL,
    mrr_amount       DECIMAL(10, 2) NOT NULL,
    delta_mrr        DECIMAL(10, 2) NOT NULL,
    event_type       VARCHAR(20) NOT NULL,
    INDEX idx_account (account_id),
    INDEX idx_billing_month (billing_month),
    INDEX idx_cohort_month (cohort_month)
);

USE saas_recurring_revenue;
SELECT COUNT(*) FROM saas_subscription_ledger;

SELECT 
    COUNT(*) AS total_months_modeled,
    ROUND(MIN(starting_mrr), 2) AS initial_starting_mrr,
    ROUND(MAX(ending_mrr), 2) AS peak_ending_mrr,
    ROUND(AVG(saas_quick_ratio), 2) AS avg_quick_ratio
FROM vw_mrr_revenue_bridge;

SELECT * 
FROM vw_cohort_nrr_matrix 
WHERE cohort_month = '2023-01-01' 
LIMIT 6;

USE saas_recurring_revenue;

CREATE OR REPLACE VIEW vw_cohort_nrr_matrix AS
WITH cohort_baselines AS (
    SELECT 
        cohort_month,
        COUNT(DISTINCT account_id) AS cohort_starting_accounts,
        SUM(mrr_amount) AS cohort_starting_mrr
    FROM saas_subscription_ledger
    WHERE tenure_months = 0
    GROUP BY cohort_month
),
tenure_aggregations AS (
    SELECT 
        cohort_month,
        tenure_months,
        COUNT(DISTINCT CASE WHEN mrr_amount > 0 THEN account_id END) AS retained_accounts,
        SUM(mrr_amount) AS retained_mrr
    FROM saas_subscription_ledger
    GROUP BY cohort_month, tenure_months
)
SELECT 
    t.cohort_month,
    t.tenure_months,
    b.cohort_starting_accounts,
    t.retained_accounts,
    ROUND(b.cohort_starting_mrr, 2) AS cohort_starting_mrr,
    ROUND(t.retained_mrr, 2) AS retained_mrr,
    ROUND((t.retained_accounts / b.cohort_starting_accounts) * 100, 2) AS logo_retention_rate_pct,
    ROUND((t.retained_mrr / b.cohort_starting_mrr) * 100, 2) AS nrr_pct
FROM tenure_aggregations t
JOIN cohort_baselines b 
    ON t.cohort_month = b.cohort_month
ORDER BY t.cohort_month, t.tenure_months;


USE saas_recurring_revenue;
SELECT * FROM vw_mrr_revenue_bridge;