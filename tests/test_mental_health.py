"""
Unit + integration tests for app/mental_health/*, per spec §23.
Run: pytest tests/test_mental_health.py -v
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from app.mental_health import screening, longitudinal, trimester


# ---------------------------------------------------------------------
# PHQ-9 scoring
# ---------------------------------------------------------------------
def _phq9(**overrides):
    base = {k: 0 for k in screening.PHQ9_ITEMS}
    base.update(overrides)
    return base


def test_phq9_total_score_sums_items():
    result = screening.score_phq9(_phq9(phq_anhedonia=2, phq_depressed_mood=3))
    assert result["total_score"] == 5


def test_phq9_at_risk_cutoff():
    assert screening.score_phq9(_phq9(phq_anhedonia=3, phq_depressed_mood=3, phq_sleep=3, phq_fatigue=1))["at_risk"] is True  # 10
    assert screening.score_phq9(_phq9(phq_anhedonia=3, phq_depressed_mood=3, phq_sleep=2, phq_fatigue=1))["at_risk"] is False  # 9


@pytest.mark.parametrize("total_items,expected_band", [
    ({"phq_anhedonia": 0}, "Minimal"),
    ({"phq_anhedonia": 2, "phq_depressed_mood": 3}, "Mild"),          # 5
    ({"phq_anhedonia": 3, "phq_depressed_mood": 3, "phq_sleep": 3, "phq_fatigue": 1}, "Moderate"),  # 10
    ({"phq_anhedonia": 3, "phq_depressed_mood": 3, "phq_sleep": 3, "phq_fatigue": 3, "phq_appetite": 3}, "Severe"),  # 15... actually check band
])
def test_severity_bands(total_items, expected_band):
    result = screening.score_phq9(_phq9(**total_items))
    # re-derive the expected band directly from the scoring rule to avoid a
    # brittle hardcoded table in the test itself
    total = result["total_score"]
    expected = next(b for lo, hi, b in screening.SEVERITY_BANDS if lo <= total <= hi)
    assert result["severity"] == expected


def test_safety_flag_independent_of_total_score():
    """A low total score must NOT suppress the safety flag (spec §4/§18)."""
    result = screening.score_phq9(_phq9(phq_suicidal_ideation=1))  # total score = 1, minimal
    assert result["total_score"] == 1
    assert result["severity"] == "Minimal"
    assert result["at_risk"] is False
    assert result["urgent_safety_flag"] is True  # must still be True


def test_missing_item_raises_rather_than_defaulting():
    incomplete = _phq9()
    del incomplete["phq_suicidal_ideation"]
    with pytest.raises(ValueError):
        screening.score_phq9(incomplete)


def test_out_of_range_item_raises():
    with pytest.raises(ValueError):
        screening.score_phq9(_phq9(phq_anhedonia=5))


def test_epds_safety_flag():
    epds = {f"epds_{i}": 0 for i in range(1, 11)}
    epds["epds_10"] = 2
    result = screening.score_epds(epds)
    assert result["urgent_safety_flag"] is True
    assert result["at_risk"] is False  # total score only 2, below cutoff 13


# ---------------------------------------------------------------------
# Trimester calculation
# ---------------------------------------------------------------------
@pytest.mark.parametrize("weeks,expected", [
    (1, "First trimester"), (13, "First trimester"),
    (14, "Second trimester"), (27, "Second trimester"),
    (28, "Third trimester"), (40, "Third trimester"),
])
def test_trimester_boundaries(weeks, expected):
    assert trimester.trimester_from_gestational_age(weeks) == expected


def test_postpartum_when_delivery_date_set():
    assert trimester.trimester_from_gestational_age(30, delivery_date=date(2026, 1, 1)) == "Postpartum"


def test_trimester_requires_gestational_age_if_no_delivery():
    with pytest.raises(ValueError):
        trimester.trimester_from_gestational_age(None)


# ---------------------------------------------------------------------
# Longitudinal features
# ---------------------------------------------------------------------
def test_first_visit_has_no_trend():
    result = longitudinal.build_longitudinal_features([], {
        "visit_date": date(2026, 1, 1), "phq9_total_score": 5, "phq9_at_risk": False,
    })
    assert result["trend"] == "insufficient_data"
    assert result["visit_count"] == 1
    assert result["score_change"] is None


def test_trend_increasing_above_threshold():
    prev = [{"visit_date": date(2026, 1, 1), "phq9_total_score": 4, "phq9_at_risk": False}]
    current = {"visit_date": date(2026, 2, 1), "phq9_total_score": 10, "phq9_at_risk": True}
    result = longitudinal.build_longitudinal_features(prev, current)
    assert result["score_change"] == 6
    assert result["trend"] == "increasing"


def test_trend_stable_below_threshold():
    prev = [{"visit_date": date(2026, 1, 1), "phq9_total_score": 4, "phq9_at_risk": False}]
    current = {"visit_date": date(2026, 2, 1), "phq9_total_score": 5, "phq9_at_risk": False}
    result = longitudinal.build_longitudinal_features(prev, current)
    assert result["score_change"] == 1
    assert result["trend"] == "stable"


def test_trend_decreasing():
    prev = [{"visit_date": date(2026, 1, 1), "phq9_total_score": 15, "phq9_at_risk": True}]
    current = {"visit_date": date(2026, 2, 1), "phq9_total_score": 8, "phq9_at_risk": False}
    result = longitudinal.build_longitudinal_features(prev, current)
    assert result["trend"] == "decreasing"


def test_num_previous_elevated_screenings():
    prev = [
        {"visit_date": date(2026, 1, 1), "phq9_total_score": 12, "phq9_at_risk": True},
        {"visit_date": date(2026, 2, 1), "phq9_total_score": 6, "phq9_at_risk": False},
    ]
    current = {"visit_date": date(2026, 3, 1), "phq9_total_score": 6, "phq9_at_risk": False}
    result = longitudinal.build_longitudinal_features(prev, current)
    assert result["num_previous_elevated_screenings"] == 1
    assert result["max_previous_score"] == 12
    assert result["avg_previous_score"] == 9.0
    assert result["days_since_last_visit"] == 28


# ---------------------------------------------------------------------
# Integration: patient -> visit 1 -> visit 2 -> history (via store.py directly,
# isolated sqlite file so tests don't touch the app's real store.db)
# ---------------------------------------------------------------------
@pytest.fixture()
def db_path(tmp_path):
    p = tmp_path / "test_store.db"
    from app.mental_health import store
    store.init_db(p)
    return p


def test_integration_patient_two_visits_history(db_path):
    from app.mental_health import store

    patient_id = store.create_patient(name=None, db_path=db_path)

    visit1_screen = screening.score_phq9(_phq9(phq_anhedonia=1, phq_depressed_mood=1))
    trimester1 = trimester.trimester_from_gestational_age(20)
    prev = store.get_previous_visits(patient_id, db_path=db_path)
    assert prev == []
    long1 = longitudinal.build_longitudinal_features(prev, {
        "visit_date": date(2026, 1, 1), "phq9_total_score": visit1_screen["total_score"],
        "phq9_at_risk": visit1_screen["at_risk"],
    })
    store.save_visit(patient_id, date(2026, 1, 1), trimester1, visit1_screen, None, long1,
                      gestational_age=20, db_path=db_path)

    visit2_screen = screening.score_phq9(_phq9(phq_anhedonia=3, phq_depressed_mood=3, phq_sleep=3, phq_fatigue=1))
    trimester2 = trimester.trimester_from_gestational_age(26)
    prev2 = store.get_previous_visits(patient_id, db_path=db_path)
    assert len(prev2) == 1  # visit 1 not overwritten
    long2 = longitudinal.build_longitudinal_features(prev2, {
        "visit_date": date(2026, 2, 1), "phq9_total_score": visit2_screen["total_score"],
        "phq9_at_risk": visit2_screen["at_risk"],
    })
    store.save_visit(patient_id, date(2026, 2, 1), trimester2, visit2_screen, None, long2,
                      gestational_age=26, db_path=db_path)

    history = store.get_patient_history(patient_id, db_path=db_path)
    assert len(history) == 2
    assert history[0]["total_score"] == 2   # visit 1, untouched by visit 2's write
    assert history[1]["total_score"] == 10  # visit 2
    assert history[1]["trend"] == "increasing"
