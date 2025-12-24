from datetime import datetime
from sqlalchemy.orm import Session
from AutoRBI_Database.database.models import WorkHistory


# 1. Record a new history entry
def create_history(
    db: Session,
    work_id: int,
    user_id: int,
    action_type: str,
    description: str = None,
    equipment_id: int = None
):

    history = WorkHistory(
        work_id=work_id,
        user_id=user_id,
        equipment_id=equipment_id,
        action_type=action_type,
        description=description,
        timestamp=datetime.utcnow()
    )

    db.add(history)
    db.flush()   # Assign history_id without committing

    return history


# 2. Get all history for a work
def get_history_for_work(db: Session, work_id: int):
    return (
        db.query(WorkHistory)
        .filter(WorkHistory.work_id == work_id)
        .order_by(WorkHistory.timestamp.asc())
        .all()
    )


# 3. Get history for a specific equipment
def get_history_for_equipment(db: Session, equipment_id: int):
    return (
        db.query(WorkHistory)
        .filter(WorkHistory.equipment_id == equipment_id)
        .order_by(WorkHistory.timestamp.asc())
        .all()
    )


# 4. Get all actions performed by a specific user
def get_history_for_user(db: Session, user_id: int):
    return (
        db.query(WorkHistory)
        .filter(WorkHistory.user_id == user_id)
        .order_by(WorkHistory.timestamp.asc())
        .all()
    )
