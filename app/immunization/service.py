"""
service.py — Maternal Immunization Status Evaluation Service.

Calculates maternal vaccine status (Td-1, Td-2, Td-Booster) according to
the Universal Immunization Programme (UIP) India guidelines.
"""
from typing import List, Dict, Any, Optional
from datetime import date, datetime, timedelta

from .schedule import SCHEDULE_METADATA, VACCINE_DEFINITIONS
from .schemas import (
    CreateImmunizationRecordRequest,
    VaccineDoseStatus,
    PatientImmunizationStatusResponse,
)
from app.mental_health import store


def evaluate_patient_immunization_status(
    patient_id: int,
    records: Optional[List[Dict[str, Any]]] = None
) -> PatientImmunizationStatusResponse:
    patient = store.get_patient(patient_id)
    if not patient:
        raise ValueError(f"Patient ID {patient_id} not found")

    if records is None:
        records = store.get_immunization_records(patient_id)

    # Find patient's latest visit to get gestational age if available
    latest_visit = store.get_latest_visit(patient_id)
    gestational_age = latest_visit.get("gestational_age") if latest_visit else None
    pregnancy_status = patient.get("pregnancy_status", "pregnant")

    # Group records by vaccine
    rec_by_vaccine = {r["vaccine_name"]: r for r in records}
    dose_statuses: List[VaccineDoseStatus] = []
    actions: List[str] = []

    # Check for Td-Booster pathway first (if mother received Td in pregnancy within last 3 years)
    has_booster = "Td-Booster" in rec_by_vaccine
    booster_rec = rec_by_vaccine.get("Td-Booster")

    if has_booster and booster_rec.get("status") == "completed":
        dose_statuses.append(
            VaccineDoseStatus(
                vaccine_name="Td-Booster",
                dose_number=1,
                status="completed",
                administration_date=booster_rec.get("administration_date"),
                confirmation_source=booster_rec.get("confirmation_source"),
                card_verified=bool(booster_rec.get("card_verified")),
                status_label="Completed (Protected for Current Pregnancy)",
                action_required=None,
            )
        )
        dose_statuses.append(
            VaccineDoseStatus(
                vaccine_name="Td-1",
                dose_number=1,
                status="not_indicated",
                status_label="Not Indicated (Booster Route Active)",
                action_required=None,
            )
        )
        dose_statuses.append(
            VaccineDoseStatus(
                vaccine_name="Td-2",
                dose_number=2,
                status="not_indicated",
                status_label="Not Indicated (Booster Route Active)",
                action_required=None,
            )
        )
        overall_compliance = "fully_protected"
        actions.append("✓ Immunization Complete: Mother received Td-Booster. Fully protected for this pregnancy.")
    else:
        # Standard 2-dose Td pathway
        td1_rec = rec_by_vaccine.get("Td-1")
        td2_rec = rec_by_vaccine.get("Td-2")

        # ── Evaluate Td-1 ─────────────────────────────────────────────────────
        if td1_rec and td1_rec.get("status") == "completed":
            td1_status = "completed"
            td1_label = "Completed"
            td1_act = None
            if not td1_rec.get("card_verified"):
                td1_label += " (Verbal - Card Verification Pending)"
                actions.append("📋 Verify MCP Card: Td-1 was reported verbally. Check mother's MCP card or ANM register to confirm.")
        elif td1_rec and td1_rec.get("status") == "unknown":
            td1_status = "unknown"
            td1_label = "Documentation Unknown"
            td1_act = "Verify immunization status with ANM or facility register."
            actions.append("❓ Td-1 Unknown: Check with ANM if mother received Td-1 earlier.")
        else:
            # Not completed yet
            if gestational_age and gestational_age > 16:
                td1_status = "overdue"
                td1_label = f"Overdue (Gestational Week {gestational_age})"
                td1_act = "Urgent: Coordinate with ANM to administer Td-1 at next VHND."
                actions.append(f"⚠️ Td-1 Overdue: Mother is in week {gestational_age}. Coordinate with ANM to give Td-1 immediately.")
            else:
                td1_status = "due"
                td1_label = "Due Early in Pregnancy"
                td1_act = "Schedule Td-1 with ANM at upcoming Village Health and Nutrition Day (VHND)."
                actions.append("📅 Schedule Td-1: Arrange Td-1 vaccination at the nearest VHND or Anganwadi center.")

        dose_statuses.append(
            VaccineDoseStatus(
                vaccine_name="Td-1",
                dose_number=1,
                status=td1_status,
                administration_date=td1_rec.get("administration_date") if td1_rec else None,
                confirmation_source=td1_rec.get("confirmation_source") if td1_rec else None,
                card_verified=bool(td1_rec.get("card_verified")) if td1_rec else False,
                next_due_date=td1_rec.get("next_due_date") if td1_rec else None,
                status_label=td1_label,
                action_required=td1_act,
            )
        )

        # ── Evaluate Td-2 ─────────────────────────────────────────────────────
        if td2_rec and td2_rec.get("status") == "completed":
            td2_status = "completed"
            td2_label = "Completed"
            td2_act = None
            if not td2_rec.get("card_verified"):
                td2_label += " (Verbal - Verification Pending)"
                actions.append("📋 Verify MCP Card: Check card to confirm Td-2 dose date.")
        elif td1_status != "completed":
            td2_status = "not_indicated"
            td2_label = "Awaiting Td-1 Completion"
            td2_act = "Administer Td-1 first; Td-2 is due 4 weeks after Td-1."
        else:
            # Td-1 is completed. Check interval to determine if Td-2 is due or overdue
            td1_date = None
            if td1_rec and td1_rec.get("administration_date"):
                try:
                    td1_date = date.fromisoformat(td1_rec["administration_date"])
                except Exception:
                    pass

            if td1_date:
                days_since_td1 = (date.today() - td1_date).days
                if days_since_td1 < 28:
                    days_remaining = 28 - days_since_td1
                    td2_status = "due"
                    td2_label = f"Due in {days_remaining} days"
                    td2_act = f"Schedule Td-2 dose on {(td1_date + timedelta(days=28)).isoformat()}."
                    actions.append(f"📅 Plan Td-2: Dose will be due on {(td1_date + timedelta(days=28)).isoformat()} (4 weeks after Td-1).")
                elif days_since_td1 <= 56:
                    td2_status = "due"
                    td2_label = "Due Now (Eligible for Dose 2)"
                    td2_act = "Administer Td-2 dose at upcoming VHND."
                    actions.append("💉 Td-2 Due Now: 4 weeks have passed since Td-1. Mobilize mother for Td-2 at next VHND.")
                else:
                    td2_status = "overdue"
                    td2_label = f"Overdue ({days_since_td1} days since Td-1)"
                    td2_act = "Urgent: Arrange Td-2 dose with ANM to complete protection."
                    actions.append(f"⚠️ Td-2 Overdue: More than 8 weeks since Td-1. Coordinate immediate Td-2 vaccination with ANM.")
            else:
                td2_status = "due"
                td2_label = "Due 4 weeks after Td-1"
                td2_act = "Schedule Td-2 4 weeks following Td-1 date."

        dose_statuses.append(
            VaccineDoseStatus(
                vaccine_name="Td-2",
                dose_number=2,
                status=td2_status,
                administration_date=td2_rec.get("administration_date") if td2_rec else None,
                confirmation_source=td2_rec.get("confirmation_source") if td2_rec else None,
                card_verified=bool(td2_rec.get("card_verified")) if td2_rec else False,
                next_due_date=td2_rec.get("next_due_date") if td2_rec else None,
                status_label=td2_label,
                action_required=td2_act,
            )
        )

        # Determine overall compliance
        if td1_status == "completed" and td2_status == "completed":
            overall_compliance = "fully_protected"
            actions.append("✓ Immunization Complete: Both Td-1 and Td-2 documented. Mother is protected against tetanus.")
        elif any(s.status == "overdue" for s in dose_statuses):
            overall_compliance = "action_needed"
        elif any(s.status == "unknown" for s in dose_statuses):
            overall_compliance = "history_unknown"
        else:
            overall_compliance = "partially_protected"

    return PatientImmunizationStatusResponse(
        patient_id=patient_id,
        gestational_age_weeks=gestational_age,
        pregnancy_status=pregnancy_status,
        schedule_version=SCHEDULE_METADATA["version"],
        overall_compliance=overall_compliance,
        doses=dose_statuses,
        asha_action_checklist=actions,
        disclaimer=(
            "Note for ASHA Worker: Immunization tracking follows the National Immunization Schedule (MoHFW India). "
            "Vaccines must be administered by a qualified ANM or Medical Officer. ASHA workers mobilize mothers, "
            "verify MCP cards, and coordinate follow-up. Immunization tracking is a preventive care indicator."
        ),
    )
