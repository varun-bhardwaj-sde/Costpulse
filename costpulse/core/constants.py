"""Constants for CostPulse including DBU rates and thresholds."""

from typing import Dict

# DBU rates as of December 2024 (USD)
DBU_RATES: Dict[str, float] = {
    # Jobs Compute
    "STANDARD_JOBS_COMPUTE": 0.15,
    "PREMIUM_JOBS_COMPUTE": 0.30,
    "JOBS_COMPUTE": 0.15,
    "JOBS_COMPUTE_PHOTON": 0.30,
    # All-Purpose Compute
    "STANDARD_ALL_PURPOSE_COMPUTE": 0.40,
    "PREMIUM_ALL_PURPOSE_COMPUTE": 0.55,
    "ALL_PURPOSE_COMPUTE": 0.55,
    "ALL_PURPOSE_COMPUTE_PHOTON": 1.10,
    # SQL Compute
    "STANDARD_SQL_COMPUTE": 0.22,
    "PREMIUM_SQL_COMPUTE": 0.22,
    "SQL_COMPUTE": 0.22,
    "SQL_COMPUTE_SERVERLESS": 0.70,
    # Delta Live Tables
    "STANDARD_DLT_CORE_COMPUTE": 0.20,
    "PREMIUM_DLT_CORE_COMPUTE": 0.20,
    "STANDARD_DLT_PRO_COMPUTE": 0.25,
    "PREMIUM_DLT_PRO_COMPUTE": 0.25,
    "STANDARD_DLT_ADVANCED_COMPUTE": 0.36,
    "PREMIUM_DLT_ADVANCED_COMPUTE": 0.36,
    # Model Serving
    "MODEL_SERVING": 0.07,
    "FOUNDATION_MODEL_SERVING": 0.07,
    # Serverless
    "SERVERLESS_REAL_TIME_INFERENCE": 0.07,
    "SERVERLESS_SQL_COMPUTE": 0.70,
}

# Cloud provider VM costs (approximate hourly rates)
VM_COSTS: Dict[str, Dict[str, float]] = {
    "AWS": {
        "i3.xlarge": 0.312,
        "i3.2xlarge": 0.624,
        "i3.4xlarge": 1.248,
        "r5.xlarge": 0.252,
        "r5.2xlarge": 0.504,
        "m5.xlarge": 0.192,
        "m5.2xlarge": 0.384,
    },
    "AZURE": {
        "Standard_DS3_v2": 0.293,
        "Standard_DS4_v2": 0.585,
        "Standard_E4s_v3": 0.252,
        "Standard_E8s_v3": 0.504,
    },
    "GCP": {
        "n1-standard-4": 0.190,
        "n1-standard-8": 0.380,
        "n1-highmem-4": 0.237,
        "n1-highmem-8": 0.473,
    },
}

# Anomaly detection thresholds
ANOMALY_THRESHOLDS: Dict[str, float] = {
    "cost_spike_percent": 50.0,  # Alert if cost increases by 50%
    "idle_cluster_minutes": 30.0,  # Alert if cluster idle for 30+ mins
    "query_cost_threshold": 100.0,  # Alert if single query costs > $100
}
