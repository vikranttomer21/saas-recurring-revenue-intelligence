import pandas as pd
import numpy as np
from datetime import datetime, timedelta

np.random.seed(42)

# --- CONFIGURATION ---
NUM_ACCOUNTS = 1250
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2024, 12, 31)

COMPANY_PREFIXES = [
    'Apex', 'Vanguard', 'Starlight', 'Hyperion', 'Crestline', 'BlueShift', 
    'Cognitive', 'Omni', 'Sentry', 'Synthetix', 'Ironclad', 'Pulse', 
    'Acuity', 'Stratosphere', 'Zephyr', 'Veritas', 'Quantix', 'Helix', 
    'Novus', 'Solstice', 'Cipher', 'Kinetics', 'Beacon', 'Prism'
]
COMPANY_SUFFIXES = [
    'Technologies', 'Labs', 'Analytics', 'Systems', 'Networks', 'Solutions', 
    'Financial', 'Logistics', 'Health', 'Software', 'Commerce', 'Security'
]

TIER_BASE_SEAT_PRICE = {
    'Starter': 29,         # Per seat / mo
    'Professional': 69,    # Per seat / mo
    'Enterprise': 149      # Per seat / mo
}

INDUSTRIES = ['Fintech', 'Healthtech', 'B2B E-commerce', 'Cybersecurity', 'Edtech', 'Logistics SaaS']
INDUSTRY_WEIGHTS = [0.25, 0.20, 0.20, 0.15, 0.10, 0.10]

REGIONS = ['North America', 'EMEA', 'APAC', 'LATAM']
REGION_WEIGHTS = [0.45, 0.30, 0.18, 0.07]

BILLING_CADENCE = ['Monthly', 'Annual']
CADENCE_WEIGHTS = [0.65, 0.35]

records = []

# --- GENERATE DATASET ---
for i in range(1, NUM_ACCOUNTS + 1):
    comp_name = f"{np.random.choice(COMPANY_PREFIXES)} {np.random.choice(COMPANY_SUFFIXES)} {i}"
    account_id = f"ACC-{10000 + i}"
    industry = np.random.choice(INDUSTRIES, p=INDUSTRY_WEIGHTS)
    region = np.random.choice(REGIONS, p=REGION_WEIGHTS)
    billing_term = np.random.choice(BILLING_CADENCE, p=CADENCE_WEIGHTS)
    
    # Seasonality acquisition: skew toward Q1 (budget opens) and Q4 (budget burn)
    month_weights = [0.12, 0.10, 0.09, 0.07, 0.06, 0.05, 0.05, 0.06, 0.08, 0.10, 0.11, 0.11]
    acq_year = np.random.choice([2023, 2024], p=[0.55, 0.45])
    acq_month = np.random.choice(range(1, 13), p=month_weights)
    cohort_month = f"{acq_year}-{acq_month:02d}-01"
    
    # Initial Tier & Seat Allocation
    tier = np.random.choice(['Starter', 'Professional', 'Enterprise'], p=[0.50, 0.38, 0.12])
    if tier == 'Starter':
        licensed_seats = np.random.randint(5, 20)
    elif tier == 'Professional':
        licensed_seats = np.random.randint(15, 60)
    else:
        licensed_seats = np.random.randint(50, 250)
        
    current_date = datetime.strptime(cohort_month, '%Y-%m-%d')
    active = True
    tenure = 0
    prev_mrr = 0
    
    # Baseline health score for this account
    account_base_health = np.random.randint(55, 95)
    
    while current_date <= END_DATE and active:
        billing_month_str = current_date.strftime('%Y-%m-01')
        
        # Fluctuate monthly usage & health
        utilization_rate = np.clip(np.random.normal(0.82, 0.12), 0.20, 1.0)
        active_users = int(np.ceil(licensed_seats * utilization_rate))
        health_score = int(np.clip(account_base_health + np.random.randint(-8, 9), 10, 100))
        
        # Calculate Base MRR with annual discount factor if applicable
        discount = 0.15 if billing_term == 'Annual' else 0.0
        mrr = round(licensed_seats * TIER_BASE_SEAT_PRICE[tier] * (1 - discount), 2)
        
        if tenure == 0:
            event_type = 'New'
            delta_mrr = mrr
        else:
            # Churn and contraction dynamics based on Health Score & Utilization
            churn_risk_modifier = 0.0
            if health_score < 45 or utilization_rate < 0.40:
                churn_risk_modifier += 0.08
            if tenure > 6:
                churn_risk_modifier -= 0.015 # Sticky mature accounts
                
            churn_prob = max(0.008, 0.035 + churn_risk_modifier)
            expansion_prob = 0.07 if health_score > 75 else 0.02
            contraction_prob = 0.05 if health_score < 60 else 0.015
            
            roll = np.random.rand()
            
            if roll < churn_prob and (billing_term == 'Monthly' or tenure % 12 == 0):
                event_type = 'Churn'
                active = False
                delta_mrr = -prev_mrr
                mrr = 0
                licensed_seats = 0
                active_users = 0
            elif roll < churn_prob + expansion_prob:
                event_type = 'Expansion'
                added_seats = int(max(2, licensed_seats * np.random.choice([0.15, 0.30, 0.50])))
                # Possibility of tier upgrade
                if tier == 'Starter' and licensed_seats > 25:
                    tier = 'Professional'
                elif tier == 'Professional' and licensed_seats > 75:
                    tier = 'Enterprise'
                licensed_seats += added_seats
                mrr = round(licensed_seats * TIER_BASE_SEAT_PRICE[tier] * (1 - discount), 2)
                delta_mrr = round(mrr - prev_mrr, 2)
            elif roll < churn_prob + expansion_prob + contraction_prob:
                event_type = 'Contraction'
                removed_seats = int(max(1, licensed_seats * np.random.choice([0.10, 0.20])))
                licensed_seats = max(2, licensed_seats - removed_seats)
                mrr = round(licensed_seats * TIER_BASE_SEAT_PRICE[tier] * (1 - discount), 2)
                delta_mrr = round(mrr - prev_mrr, 2)
            else:
                event_type = 'Renewal'
                delta_mrr = 0.0
        
        records.append({
            'account_id': account_id,
            'company_name': comp_name,
            'industry': industry,
            'region': region,
            'cohort_month': cohort_month,
            'billing_month': billing_month_str,
            'tenure_months': tenure,
            'billing_cadence': billing_term,
            'plan_tier': tier,
            'licensed_seats': licensed_seats,
            'active_users': active_users,
            'utilization_rate': round(utilization_rate * 100, 1),
            'health_score': health_score,
            'mrr_amount': mrr,
            'delta_mrr': delta_mrr,
            'event_type': event_type
        })
        
        prev_mrr = mrr
        tenure += 1
        
        # Advance 1 calendar month
        if current_date.month == 12:
            current_date = datetime(current_date.year + 1, 1, 1)
        else:
            current_date = datetime(current_date.year, current_date.month + 1, 1)

# Export clean CSV
df = pd.DataFrame(records)
df.to_csv('saas_subscription_ledger.csv', index=False)
print(f"✓ Synthetic Enterprise Ledger Generated successfully!")
print(f"✓ Total Records: {len(df):,} billing cycles")
print(f"✓ Total Unique Accounts: {df['account_id'].nunique():,}")
print(f"✓ Total Columns: {len(df.columns)}")