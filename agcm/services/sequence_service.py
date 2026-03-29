"""Sequence generator matching Odoo ir.sequence conventions.

Odoo sequences from ir_sequence_data.xml:
  Project:          Proj00001
  DailyActivityLog: DL00001
  ManPower:         MP00001
  Accident:         ACC00001
  Weather:          Weather00001
  Notes:            Observations00001
  Inspection:       Inspection00001
  Visitor:          Visitor00001
  SafetyViolation:  SV00001
  Delay:            Delay00001
  Photo:            PH00001
"""

import re
from sqlalchemy.orm import Session


# Prefix → (model_class_tablename, padding)
SEQUENCE_CONFIG = {
    "agcm_projects":           ("Proj", 5),
    "agcm_daily_activity_logs": ("DL", 5),
    "agcm_manpower":           ("MP", 5),
    "agcm_accidents":          ("ACC", 5),
    "agcm_weather":            ("Weather", 5),
    "agcm_notes":              ("Observations", 5),
    "agcm_inspections":        ("Inspection", 5),
    "agcm_visitors":           ("Visitor", 5),
    "agcm_safety_violations":  ("SV", 5),
    "agcm_delays":             ("Delay", 5),
    "agcm_deficiencies":       ("DEF", 5),
    "agcm_photos":             ("PH", 5),
    "agcm_weather_forecasts":  ("WF", 5),
}


def next_sequence(db: Session, model_class, company_id: int) -> str:
    """Generate the next sequence_name for a model, matching Odoo's ir.sequence format.

    Example: Proj00001, DL00002, MP00003
    """
    tablename = model_class.__tablename__
    config = SEQUENCE_CONFIG.get(tablename)
    if not config:
        return None

    prefix, padding = config

    # Find the highest existing sequence number for this company
    last = (
        db.query(model_class.sequence_name)
        .filter(model_class.company_id == company_id)
        .filter(model_class.sequence_name.isnot(None))
        .order_by(model_class.id.desc())
        .first()
    )

    num = 1
    if last and last[0]:
        # Extract trailing digits from the sequence name
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1

    return f"{prefix}{num:0{padding}d}"
