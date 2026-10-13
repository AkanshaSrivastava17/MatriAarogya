"""
schedule.py — National Immunization Schedule (Universal Immunization Programme - India) for Pregnant Women.

Authoritative Source:
- Ministry of Health & Family Welfare (MoHFW), Government of India
- Maternal and Child Health Division, UIP Guidelines
- Target Antigens: Tetanus & adult Diphtheria (Td) toxoids
"""
from typing import Dict, Any, List

SCHEDULE_METADATA = {
    "source": "Ministry of Health and Family Welfare (MoHFW), Government of India",
    "program": "Universal Immunization Programme (UIP)",
    "guideline_title": "National Immunization Schedule for Pregnant Women (Replacement of TT with Td)",
    "country": "India",
    "version": "MoHFW-UIP-Td-v2.0"
}

# The National Immunization Schedule specifies:
# 1. Td-1: Early in pregnancy (as soon as pregnancy is registered/detected).
# 2. Td-2: 4 weeks after Td-1 (minimum 28 days interval).
# 3. Td-Booster: If the woman has received 2 Td/TT doses in a pregnancy within the last 3 years,
#    only ONE dose of Td-Booster is required during the current pregnancy.

VACCINE_DEFINITIONS = {
    "Td-1": {
        "full_name": "Tetanus and adult Diphtheria Toxoid Vaccine — Dose 1",
        "target_condition": "Maternal and Neonatal Tetanus (MNT) & Diphtheria",
        "recommended_timing": "Early in pregnancy / 1st Trimester (Weeks 1 to 16)",
        "minimum_interval_days": None,
        "dose_number": 1,
        "is_primary": True,
    },
    "Td-2": {
        "full_name": "Tetanus and adult Diphtheria Toxoid Vaccine — Dose 2",
        "target_condition": "Maternal and Neonatal Tetanus (MNT) & Diphtheria",
        "recommended_timing": "4 weeks (28 days) after Td-1",
        "minimum_interval_days": 28,
        "dose_number": 2,
        "is_primary": True,
    },
    "Td-Booster": {
        "full_name": "Tetanus and adult Diphtheria Toxoid Vaccine — Booster",
        "target_condition": "Maternal and Neonatal Tetanus (MNT) & Diphtheria",
        "recommended_timing": "If 2 doses received in prior pregnancy within last 3 years",
        "minimum_interval_days": None,
        "dose_number": 1,
        "is_primary": False,
    }
}
