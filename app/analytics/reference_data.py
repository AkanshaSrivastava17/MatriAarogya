"""
reference_data.py — Real-world population benchmarks and external reference datasets.

Authoritative Sources:
1. NFHS-5 (National Family Health Survey 2019-2021, Ministry of Health and Family Welfare, Government of India / IIPS Mumbai)
2. ICMR-NIN (2020) Recommended Dietary Allowances for Indians
3. WHO / IOM Gestational Weight Gain Reference Curves
"""
from typing import Dict, Any, List

REFERENCE_PROVENANCE = {
    "NFHS-5": {
        "title": "National Family Health Survey (NFHS-5) 2019-2021: India and State Factsheets",
        "agency": "Ministry of Health and Family Welfare, Government of India & IIPS Mumbai",
        "url": "http://rchiips.org/nfhs/factsheet_NFHS-5.shtml",
        "collection_period": "2019-2021",
        "population": "All-India representative household survey of women aged 15-49 years",
        "sample_size": "724,115 women surveyed nationally",
        "retrieval_date": "2026-09-30",
        "known_limitations": "Cross-sectional survey reflecting national and state averages; individual clinical outcomes vary by district."
    },
    "ICMR-NIN-2020": {
        "title": "Nutrient Requirements for Indians: Recommended Dietary Allowances (RDA) and Estimated Average Requirements (EAR)",
        "agency": "Indian Council of Medical Research & National Institute of Nutrition, Hyderabad",
        "publication_year": 2020,
        "population": "Adult Indian Pregnant & Lactating Women",
        "retrieval_date": "2026-09-30",
        "known_limitations": "Normative physiological recommendations for reference Indian adult female."
    }
}

# NFHS-5 National & State Maternal Health Key Indicators (Percentages)
NFHS5_MATERNAL_INDICATORS: Dict[str, Dict[str, float]] = {
    "All India": {
        "anc_4_plus_visits_pct": 58.1,
        "maternal_anemia_pct": 52.2,
        "td_coverage_pct": 82.5,
        "ifa_100_days_pct": 44.1,
        "institutional_delivery_pct": 88.6,
        "postnatal_check_48h_pct": 78.0
    },
    "Uttar Pradesh": {
        "anc_4_plus_visits_pct": 42.4,
        "maternal_anemia_pct": 45.9,
        "td_coverage_pct": 80.8,
        "ifa_100_days_pct": 22.3,
        "institutional_delivery_pct": 83.4,
        "postnatal_check_48h_pct": 74.5
    },
    "Bihar": {
        "anc_4_plus_visits_pct": 25.2,
        "maternal_anemia_pct": 63.1,
        "td_coverage_pct": 82.8,
        "ifa_100_days_pct": 18.2,
        "institutional_delivery_pct": 76.2,
        "postnatal_check_48h_pct": 65.8
    },
    "Madhya Pradesh": {
        "anc_4_plus_visits_pct": 52.9,
        "maternal_anemia_pct": 52.9,
        "td_coverage_pct": 85.0,
        "ifa_100_days_pct": 42.1,
        "institutional_delivery_pct": 90.7,
        "postnatal_check_48h_pct": 80.3
    },
    "Rajasthan": {
        "anc_4_plus_visits_pct": 55.4,
        "maternal_anemia_pct": 46.6,
        "td_coverage_pct": 84.7,
        "ifa_100_days_pct": 44.2,
        "institutional_delivery_pct": 94.9,
        "postnatal_check_48h_pct": 83.2
    },
    "Maharashtra": {
        "anc_4_plus_visits_pct": 70.0,
        "maternal_anemia_pct": 45.7,
        "td_coverage_pct": 88.5,
        "ifa_100_days_pct": 54.3,
        "institutional_delivery_pct": 94.7,
        "postnatal_check_48h_pct": 86.8
    },
    "West Bengal": {
        "anc_4_plus_visits_pct": 76.3,
        "maternal_anemia_pct": 62.3,
        "td_coverage_pct": 89.2,
        "ifa_100_days_pct": 58.7,
        "institutional_delivery_pct": 91.7,
        "postnatal_check_48h_pct": 85.9
    },
    "Kerala": {
        "anc_4_plus_visits_pct": 78.6,
        "maternal_anemia_pct": 31.4,
        "td_coverage_pct": 92.4,
        "ifa_100_days_pct": 74.0,
        "institutional_delivery_pct": 99.8,
        "postnatal_check_48h_pct": 93.1
    },
    "Tamil Nadu": {
        "anc_4_plus_visits_pct": 81.2,
        "maternal_anemia_pct": 48.3,
        "td_coverage_pct": 93.1,
        "ifa_100_days_pct": 65.5,
        "institutional_delivery_pct": 99.2,
        "postnatal_check_48h_pct": 92.4
    }
}


def get_real_world_benchmarks(state: str = "All India") -> Dict[str, Any]:
    indicators = NFHS5_MATERNAL_INDICATORS.get(state, NFHS5_MATERNAL_INDICATORS["All India"])
    return {
        "state": state,
        "indicators": indicators,
        "provenance": REFERENCE_PROVENANCE["NFHS-5"]
    }
