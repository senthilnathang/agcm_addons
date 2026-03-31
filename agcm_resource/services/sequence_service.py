"""Sequence generator for agcm_resource models.

Sequences:
  Worker:              WRK00001
  Equipment:           EQP00001
  Timesheet:           TS00001
"""

import re
from sqlalchemy.orm import Session


SEQUENCE_CONFIG = {
    "agcm_workers":     ("WRK", 5),
    "agcm_equipment":   ("EQP", 5),
    "agcm_timesheets":  ("TS", 5),
}


def next_sequence(db: Session, model_class, company_id: int) -> str:
    """Generate the next sequence_name for a model.

    Example: WRK00001, EQP00002, TS00003
    """
    tablename = model_class.__tablename__
    config = SEQUENCE_CONFIG.get(tablename)
    if not config:
        return None

    prefix, padding = config

    last = (
        db.query(model_class.sequence_name)
        .filter(model_class.company_id == company_id)
        .filter(model_class.sequence_name.isnot(None))
        .order_by(model_class.id.desc())
        .first()
    )

    num = 1
    if last and last[0]:
        match = re.search(r'(\d+)$', last[0])
        if match:
            num = int(match.group(1)) + 1

    return f"{prefix}{num:0{padding}d}"
