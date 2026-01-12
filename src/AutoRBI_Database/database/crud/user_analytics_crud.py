"""
User Analytics CRUD Operations
Provides database queries for user performance metrics and analytics.
"""

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, case, distinct
from typing import List, Dict, Optional, Tuple

from AutoRBI_Database.database.models.work_history import WorkHistory
from AutoRBI_Database.database.models.users import User
from AutoRBI_Database.database.models.work import Work
from AutoRBI_Database.database.models.equipment import Equipment
from AutoRBI_Database.database.models.assign_work import AssignWork


def get_user_activity_summary(
    db: Session,
    user_id: int,
    start_date: datetime = None,
    end_date: datetime = None
) -> Dict:
    """
    Get comprehensive statistics for a single user.

    Args:
        db: Database session
        user_id: User ID to analyze
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        Dictionary with user activity metrics
    """
    # Build base query with date filters
    query = db.query(WorkHistory).filter(WorkHistory.user_id == user_id)

    if start_date:
        query = query.filter(WorkHistory.timestamp >= start_date)
    if end_date:
        query = query.filter(WorkHistory.timestamp <= end_date)

    # Total actions
    total_actions = query.count()

    # Action breakdown by type
    action_breakdown = {}
    action_counts = (
        query.with_entities(
            WorkHistory.action_type,
            func.count(WorkHistory.history_id).label("count")
        )
        .group_by(WorkHistory.action_type)
        .all()
    )
    for action_type, count in action_counts:
        action_breakdown[action_type] = count

    # First and last action timestamps
    timestamps = (
        query.with_entities(
            func.min(WorkHistory.timestamp).label("first_action"),
            func.max(WorkHistory.timestamp).label("last_action")
        )
        .first()
    )

    first_action = timestamps.first_action
    last_action = timestamps.last_action

    # Calculate total work duration (time between first and last action)
    # Show in minutes if less than 1 hour to avoid showing 0.0
    total_duration_hours = 0
    total_duration_minutes = 0
    if first_action and last_action:
        duration = last_action - first_action
        total_duration_minutes = round(duration.total_seconds() / 60, 2)
        total_duration_hours = round(duration.total_seconds() / 3600, 2)

    # Count unique works the user has worked on
    total_works = (
        query.with_entities(func.count(func.distinct(WorkHistory.work_id)))
        .scalar()
    )

    # Count equipment processed (distinct equipment_id with action_type='extract_equipment')
    # Note: 'extract' is logged without equipment_id (overall extraction action)
    # 'extract_equipment' is logged PER equipment with equipment_id
    equipment_extracted = (
        query.filter(WorkHistory.action_type == "extract_equipment")
        .filter(WorkHistory.equipment_id.isnot(None))
        .with_entities(func.count(func.distinct(WorkHistory.equipment_id)))
        .scalar()
    )

    # Count corrections made
    corrections_made = query.filter(WorkHistory.action_type == "correct").count()

    # Calculate average time per equipment more accurately
    # Strategy: Calculate time between consecutive extract_equipment actions
    avg_time_per_equipment = 0
    if equipment_extracted > 0:
        # Get all extract_equipment timestamps ordered by time
        extract_timestamps = (
            query.filter(WorkHistory.action_type == "extract_equipment")
            .filter(WorkHistory.equipment_id.isnot(None))
            .with_entities(WorkHistory.timestamp)
            .order_by(WorkHistory.timestamp)
            .all()
        )

        if len(extract_timestamps) > 1:
            # Calculate average time between consecutive extractions
            total_intervals = 0
            for i in range(1, len(extract_timestamps)):
                interval = (extract_timestamps[i][0] - extract_timestamps[i-1][0]).total_seconds() / 60
                # Cap intervals at 60 minutes to exclude long breaks
                if interval <= 60:
                    total_intervals += interval

            if total_intervals > 0:
                avg_time_per_equipment = round(total_intervals / (len(extract_timestamps) - 1), 2)
        elif len(extract_timestamps) == 1 and total_duration_minutes > 0:
            # Only one equipment, use total duration (but cap at reasonable value)
            avg_time_per_equipment = min(total_duration_minutes, 60)

    return {
        "user_id": user_id,
        "total_actions": total_actions,
        "action_breakdown": action_breakdown,
        "first_action": first_action.isoformat() if first_action else None,
        "last_action": last_action.isoformat() if last_action else None,
        "total_duration_hours": total_duration_hours,
        "total_duration_minutes": total_duration_minutes,
        "total_works": total_works,
        "equipment_extracted": equipment_extracted,
        "corrections_made": corrections_made,
        "avg_time_per_equipment_minutes": avg_time_per_equipment,
    }


def get_team_performance_comparison(
    db: Session,
    start_date: datetime = None,
    end_date: datetime = None
) -> List[Dict]:
    """
    Compare performance metrics across all users.

    Args:
        db: Database session
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of dictionaries with per-user metrics
    """
    # Get all users with Engineer role
    engineers = db.query(User).filter(User.role == "Engineer").all()

    results = []
    for engineer in engineers:
        # Get summary for this engineer
        summary = get_user_activity_summary(db, engineer.user_id, start_date, end_date)

        # Count works assigned to this engineer
        works_assigned = (
            db.query(AssignWork)
            .filter(AssignWork.user_id == engineer.user_id)
            .count()
        )

        results.append({
            "user_id": engineer.user_id,
            "username": engineer.username,
            "full_name": engineer.full_name,
            "works_assigned": works_assigned,
            "total_actions": summary["total_actions"],
            "equipment_extracted": summary["equipment_extracted"],
            "corrections_made": summary["corrections_made"],
            "avg_time_per_equipment_minutes": summary["avg_time_per_equipment_minutes"],
            "total_duration_hours": summary["total_duration_hours"],
            "total_duration_minutes": summary.get("total_duration_minutes", 0),
        })

    # Sort by total actions (most active first)
    results.sort(key=lambda x: x["total_actions"], reverse=True)

    return results


def get_work_duration_by_user(
    db: Session,
    work_id: int
) -> List[Dict]:
    """
    Calculate how long each user spent on a specific work.

    Args:
        db: Database session
        work_id: ID of the work to analyze

    Returns:
        List of dictionaries with per-user work duration
    """
    # Get all users who worked on this work
    user_ids = (
        db.query(WorkHistory.user_id)
        .filter(WorkHistory.work_id == work_id)
        .distinct()
        .all()
    )

    results = []
    for (user_id,) in user_ids:
        # Get user info
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            continue

        # Get first and last action for this user on this work
        timestamps = (
            db.query(
                func.min(WorkHistory.timestamp).label("first_action"),
                func.max(WorkHistory.timestamp).label("last_action"),
                func.count(WorkHistory.history_id).label("action_count")
            )
            .filter(WorkHistory.work_id == work_id)
            .filter(WorkHistory.user_id == user_id)
            .first()
        )

        first_action = timestamps.first_action
        last_action = timestamps.last_action
        action_count = timestamps.action_count

        # Calculate duration
        duration_hours = 0
        if first_action and last_action:
            duration = last_action - first_action
            duration_hours = round(duration.total_seconds() / 3600, 2)

        results.append({
            "user_id": user_id,
            "username": user.username,
            "full_name": user.full_name,
            "first_action": first_action.isoformat() if first_action else None,
            "last_action": last_action.isoformat() if last_action else None,
            "duration_hours": duration_hours,
            "action_count": action_count,
        })

    # Sort by first action (who started first)
    results.sort(key=lambda x: x["first_action"] or "")

    return results


def get_hourly_productivity(
    db: Session,
    user_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> List[Dict]:
    """
    Group actions by hour of day to find peak productivity times.

    Args:
        db: Database session
        user_id: Optional user ID filter (None = all users)
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of dictionaries with hourly action counts
    """
    # Build query
    query = db.query(
        func.extract('hour', WorkHistory.timestamp).label("hour"),
        func.count(WorkHistory.history_id).label("action_count")
    )

    # Apply filters
    if user_id:
        query = query.filter(WorkHistory.user_id == user_id)
    if start_date:
        query = query.filter(WorkHistory.timestamp >= start_date)
    if end_date:
        query = query.filter(WorkHistory.timestamp <= end_date)

    # Group by hour
    results = query.group_by(func.extract('hour', WorkHistory.timestamp)).all()

    # Convert to list of dicts
    hourly_data = []
    for hour, count in results:
        hourly_data.append({
            "hour": int(hour),
            "action_count": count,
        })

    # Sort by hour
    hourly_data.sort(key=lambda x: x["hour"])

    return hourly_data


def get_daily_activity(
    db: Session,
    user_id: int = None,
    start_date: datetime = None,
    end_date: datetime = None
) -> List[Dict]:
    """
    Get daily activity counts for timeline visualization.

    Args:
        db: Database session
        user_id: Optional user ID filter
        start_date: Optional start date filter
        end_date: Optional end date filter

    Returns:
        List of dictionaries with daily action counts
    """
    # Build query
    query = db.query(
        func.date(WorkHistory.timestamp).label("date"),
        func.count(WorkHistory.history_id).label("action_count")
    )

    # Apply filters
    if user_id:
        query = query.filter(WorkHistory.user_id == user_id)
    if start_date:
        query = query.filter(WorkHistory.timestamp >= start_date)
    if end_date:
        query = query.filter(WorkHistory.timestamp <= end_date)

    # Group by date
    results = query.group_by(func.date(WorkHistory.timestamp)).all()

    # Convert to list of dicts
    daily_data = []
    for date, count in results:
        daily_data.append({
            "date": date.isoformat() if date else None,
            "action_count": count,
        })

    # Sort by date
    daily_data.sort(key=lambda x: x["date"] or "")

    return daily_data
