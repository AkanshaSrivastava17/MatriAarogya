"""
trimester.py

Standard obstetric convention (documented, not invented):
  1st trimester: weeks 1-13
  2nd trimester: weeks 14-27
  3rd trimester: weeks 28-40
  Postpartum: after delivery (gestational_age is not meaningful once a
  delivery_date is recorded; postpartum status is derived from delivery_date
  presence, not from gestational_age).
"""
from datetime import date
from typing import Optional


def trimester_from_gestational_age(gestational_age_weeks: Optional[int], delivery_date: Optional[date] = None) -> str:
    if delivery_date is not None:
        return "Postpartum"
    if gestational_age_weeks is None:
        raise ValueError("gestational_age_weeks is required when delivery_date is not set")
    if gestational_age_weeks < 1:
        raise ValueError(f"gestational_age_weeks must be >= 1, got {gestational_age_weeks}")
    if gestational_age_weeks <= 13:
        return "First trimester"
    if gestational_age_weeks <= 27:
        return "Second trimester"
    return "Third trimester"  # weeks 28+ until delivery is recorded
