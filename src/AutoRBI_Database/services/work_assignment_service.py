"""
Work Assignment Service
Handles business logic for creating works and managing engineer assignments.
"""

from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime

from AutoRBI_Database.database.models import Work, AssignWork, User
from AutoRBI_Database.database.crud import (
    work_crud,
    assign_work_crud,
    user_crud
)
from AutoRBI_Database.exceptions import (
    ValidationError,
    DatabaseError,
)
from AutoRBI_Database.logging_config import get_logger

logger = get_logger(__name__)


class WorkAssignmentService:
    """Service class for work assignment operations."""

    @staticmethod
    def create_work_and_assign(
        db: Session,
        work_name: str,
        description: Optional[str] = None,
        assigned_user_ids: Optional[List[int]] = None
    ) -> Dict:
        """
        Create a new work and assign engineers to it.
        
        Args:
            db: Database session
            work_name: Name of the work (must be unique)
            description: Optional work description
            assigned_user_ids: List of user IDs to assign (must be engineers)
            
        Returns:
            Dictionary with work details and assignment information
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Validate work name
            if not work_name or not work_name.strip():
                raise ValidationError("Work name cannot be empty")
            
            work_name = work_name.strip()
            
            # Check if work name already exists
            existing_work = work_crud.get_work_by_name(db, work_name)
            if existing_work:
                raise ValidationError(f"Work with name '{work_name}' already exists")
            
            # Validate assigned users if provided
            if assigned_user_ids:
                for user_id in assigned_user_ids:
                    user = user_crud.get_user_by_id(db, user_id)
                    if not user:
                        raise ValidationError(f"User with ID {user_id} not found")
                    if user.role != "Engineer":
                        raise ValidationError(
                            f"User '{user.full_name}' is not an engineer and cannot be assigned to work"
                        )
                    if user.status != "Active":
                        raise ValidationError(
                            f"User '{user.full_name}' is inactive and cannot be assigned to work"
                        )
            
            # Create the work
            logger.info(f"Creating work: {work_name}")
            new_work = work_crud.create_work(
                db=db,
                work_name=work_name,
                description=description
            )
            
            # Assign engineers to the work
            assignments = []
            if assigned_user_ids:
                logger.info(f"Assigning {len(assigned_user_ids)} engineers to work {new_work.work_id}")
                for user_id in assigned_user_ids:
                    assignment = assign_work_crud.assign_user_to_work(
                        db=db,
                        user_id=user_id,
                        work_id=new_work.work_id
                    )
                    assignments.append(assignment)
            
            # Get assigned engineer details
            assigned_engineers = []
            for assignment in assignments:
                user = user_crud.get_user_by_id(db, assignment.user_id)
                if user:
                    assigned_engineers.append({
                        "user_id": user.user_id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "email": user.email,
                        "assigned_at": assignment.assigned_at
                    })
            
            logger.info(f"Successfully created work '{work_name}' with {len(assigned_engineers)} assignments")
            
            return {
                "work": {
                    "work_id": new_work.work_id,
                    "work_name": new_work.work_name,
                    "description": new_work.description,
                    "status": new_work.status,
                    "created_at": new_work.created_at,
                },
                "assigned_engineers": assigned_engineers,
                "assignment_count": len(assigned_engineers)
            }
            
        except ValidationError:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error creating work: {str(e)}")
            raise DatabaseError(f"Failed to create work: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating work: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")

    @staticmethod
    def get_all_engineers(db: Session) -> List[Dict]:
        """
        Get all active engineers for assignment selection.
        
        Args:
            db: Database session
            
        Returns:
            List of engineer details
        """
        try:
            # Get all users
            all_users = user_crud.get_all_users(db)
            
            # Filter for active engineers only
            engineers = [
                {
                    "user_id": user.user_id,
                    "username": user.username,
                    "full_name": user.full_name,
                    "email": user.email,
                    "created_at": user.created_at
                }
                for user in all_users
                if user.role == "Engineer" and user.status == "Active"
            ]
            
            # Sort by full name
            engineers.sort(key=lambda x: x["full_name"])
            
            logger.info(f"Retrieved {len(engineers)} active engineers")
            return engineers
            
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching engineers: {str(e)}")
            raise DatabaseError(f"Failed to fetch engineers: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching engineers: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")

    @staticmethod
    def get_work_with_assignments(db: Session, work_id: int) -> Optional[Dict]:
        """
        Get work details with all assigned engineers.
        
        Args:
            db: Database session
            work_id: ID of the work
            
        Returns:
            Dictionary with work and assignment details, or None if not found
        """
        try:
            # Get work details
            work = work_crud.get_work_by_id(db, work_id)
            if not work:
                return None
            
            # Get assignments
            assignments = assign_work_crud.get_engineers_for_work(db, work_id)
            
            # Get engineer details for each assignment
            assigned_engineers = []
            for assignment in assignments:
                user = user_crud.get_user_by_id(db, assignment.user_id)
                if user:
                    assigned_engineers.append({
                        "user_id": user.user_id,
                        "username": user.username,
                        "full_name": user.full_name,
                        "email": user.email,
                        "assigned_at": assignment.assigned_at
                    })
            
            return {
                "work": {
                    "work_id": work.work_id,
                    "work_name": work.work_name,
                    "description": work.description,
                    "status": work.status,
                    "created_at": work.created_at,
                    "excel_path": work.excel_path,
                    "ppt_path": work.ppt_path,
                },
                "assigned_engineers": assigned_engineers,
                "assignment_count": len(assigned_engineers)
            }
            
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching work: {str(e)}")
            raise DatabaseError(f"Failed to fetch work: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching work: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")

    @staticmethod
    def get_all_works_with_assignments(db: Session) -> List[Dict]:
        """
        Get all works with their assigned engineers.
        
        Args:
            db: Database session
            
        Returns:
            List of works with assignment details
        """
        try:
            all_works = work_crud.get_all_works(db)
            
            works_data = []
            for work in all_works:
                # Get assignments for this work
                assignments = assign_work_crud.get_engineers_for_work(db, work.work_id)
                
                # Get engineer details
                assigned_engineers = []
                for assignment in assignments:
                    user = user_crud.get_user_by_id(db, assignment.user_id)
                    if user:
                        assigned_engineers.append({
                            "user_id": user.user_id,
                            "username": user.username,
                            "full_name": user.full_name,
                            "email": user.email,
                            "assigned_at": assignment.assigned_at
                        })
                
                works_data.append({
                    "work": {
                        "work_id": work.work_id,
                        "work_name": work.work_name,
                        "description": work.description,
                        "status": work.status,
                        "created_at": work.created_at,
                        "excel_path": work.excel_path,
                        "ppt_path": work.ppt_path,
                    },
                    "assigned_engineers": assigned_engineers,
                    "assignment_count": len(assigned_engineers)
                })
            
            # Sort by creation date (newest first)
            works_data.sort(key=lambda x: x["work"]["created_at"], reverse=True)
            
            logger.info(f"Retrieved {len(works_data)} works with assignments")
            return works_data
            
        except SQLAlchemyError as e:
            logger.error(f"Database error fetching works: {str(e)}")
            raise DatabaseError(f"Failed to fetch works: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error fetching works: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")

    @staticmethod
    def update_work_assignments(
        db: Session,
        work_id: int,
        user_ids_to_add: Optional[List[int]] = None,
        user_ids_to_remove: Optional[List[int]] = None
    ) -> Dict:
        """
        Update work assignments by adding/removing engineers.
        
        Args:
            db: Database session
            work_id: ID of the work
            user_ids_to_add: List of user IDs to assign
            user_ids_to_remove: List of user IDs to unassign
            
        Returns:
            Updated assignment information
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Verify work exists
            work = work_crud.get_work_by_id(db, work_id)
            if not work:
                raise ValidationError(f"Work with ID {work_id} not found")
            
            # Remove assignments
            removed_count = 0
            if user_ids_to_remove:
                logger.info(f"Removing {len(user_ids_to_remove)} assignments from work {work_id}")
                for user_id in user_ids_to_remove:
                    result = assign_work_crud.unassign_user_from_work(db, user_id, work_id)
                    if result:
                        removed_count += 1
            
            # Add new assignments
            added_count = 0
            if user_ids_to_add:
                logger.info(f"Adding {len(user_ids_to_add)} assignments to work {work_id}")
                for user_id in user_ids_to_add:
                    # Validate user
                    user = user_crud.get_user_by_id(db, user_id)
                    if not user:
                        raise ValidationError(f"User with ID {user_id} not found")
                    if user.role != "Engineer":
                        raise ValidationError(
                            f"User '{user.full_name}' is not an engineer"
                        )
                    if user.status != "Active":
                        raise ValidationError(
                            f"User '{user.full_name}' is inactive"
                        )
                    
                    # Add assignment
                    assign_work_crud.assign_user_to_work(db, user_id, work_id)
                    added_count += 1
            
            # Get updated assignments
            updated_data = WorkAssignmentService.get_work_with_assignments(db, work_id)
            
            logger.info(
                f"Updated assignments for work {work_id}: "
                f"added {added_count}, removed {removed_count}"
            )
            
            return {
                **updated_data,
                "added_count": added_count,
                "removed_count": removed_count
            }
            
        except ValidationError:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating assignments: {str(e)}")
            raise DatabaseError(f"Failed to update assignments: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating assignments: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")

    @staticmethod
    def delete_work_and_assignments(db: Session, work_id: int) -> bool:
        """
        Delete a work and all its assignments.
        
        Args:
            db: Database session
            work_id: ID of the work to delete
            
        Returns:
            True if successful
            
        Raises:
            ValidationError: If work not found
            DatabaseError: If database operation fails
        """
        try:
            # Verify work exists
            work = work_crud.get_work_by_id(db, work_id)
            if not work:
                raise ValidationError(f"Work with ID {work_id} not found")
            
            logger.info(f"Deleting work {work_id} and its assignments")
            
            # Get all assignments
            assignments = assign_work_crud.get_engineers_for_work(db, work_id)
            
            # Delete all assignments first
            for assignment in assignments:
                assign_work_crud.unassign_user_from_work(
                    db, assignment.user_id, work_id
                )
            
            # Delete the work
            db.delete(work)
            db.commit()
            
            logger.info(
                f"Successfully deleted work {work_id} with "
                f"{len(assignments)} assignments"
            )
            return True
            
        except ValidationError:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error deleting work: {str(e)}")
            raise DatabaseError(f"Failed to delete work: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error deleting work: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")

    @staticmethod
    def update_work_info(
        db: Session,
        work_id: int,
        work_name: Optional[str] = None,
        description: Optional[str] = None,
        status: Optional[str] = None
    ) -> Dict:
        """
        Update work information (name, description, status).
        
        Args:
            db: Database session
            work_id: ID of the work
            work_name: New work name
            description: New description
            status: New status
            
        Returns:
            Updated work details
            
        Raises:
            ValidationError: If validation fails
            DatabaseError: If database operation fails
        """
        try:
            # Verify work exists
            work = work_crud.get_work_by_id(db, work_id)
            if not work:
                raise ValidationError(f"Work with ID {work_id} not found")
            
            updates = {}
            
            # Validate and prepare updates
            if work_name is not None:
                work_name = work_name.strip()
                if not work_name:
                    raise ValidationError("Work name cannot be empty")
                
                # Check for duplicate name (if different from current)
                if work_name != work.work_name:
                    existing = work_crud.get_work_by_name(db, work_name)
                    if existing:
                        raise ValidationError(
                            f"Work with name '{work_name}' already exists"
                        )
                updates["work_name"] = work_name
            
            if description is not None:
                updates["description"] = description
            
            # Update work info
            if updates:
                work_crud.update_work_info(db, work_id, updates)
            
            # Update status separately if provided
            if status is not None:
                work_crud.update_work_status(db, work_id, status)
            
            # Get updated work with assignments
            updated_data = WorkAssignmentService.get_work_with_assignments(db, work_id)
            
            logger.info(f"Successfully updated work {work_id}")
            return updated_data
            
        except ValidationError:
            db.rollback()
            raise
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error updating work: {str(e)}")
            raise DatabaseError(f"Failed to update work: {str(e)}")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating work: {str(e)}")
            raise DatabaseError(f"Unexpected error: {str(e)}")


# Convenience function for backward compatibility
def create_work_and_assign(
    db: Session,
    work_name: str,
    description: Optional[str] = None,
    assigned_user_ids: Optional[List[int]] = None
) -> Dict:
    """Convenience function - delegates to WorkAssignmentService."""
    return WorkAssignmentService.create_work_and_assign(
        db, work_name, description, assigned_user_ids
    )


def get_all_engineers(db: Session) -> List[Dict]:
    """Convenience function - delegates to WorkAssignmentService."""
    return WorkAssignmentService.get_all_engineers(db)


def get_work_with_assignments(db: Session, work_id: int) -> Optional[Dict]:
    """Convenience function - delegates to WorkAssignmentService."""
    return WorkAssignmentService.get_work_with_assignments(db, work_id)


def get_all_works_with_assignments(db: Session) -> List[Dict]:
    """Convenience function - delegates to WorkAssignmentService."""
    return WorkAssignmentService.get_all_works_with_assignments(db)


def update_work_assignments(
    db: Session,
    work_id: int,
    user_ids_to_add: Optional[List[int]] = None,
    user_ids_to_remove: Optional[List[int]] = None
) -> Dict:
    """Convenience function - delegates to WorkAssignmentService."""
    return WorkAssignmentService.update_work_assignments(
        db, work_id, user_ids_to_add, user_ids_to_remove
    )


def delete_work_and_assignments(db: Session, work_id: int) -> bool:
    """Convenience function - delegates to WorkAssignmentService."""
    return WorkAssignmentService.delete_work_and_assignments(db, work_id)


def update_work_info(
    db: Session,
    work_id: int,
    work_name: Optional[str] = None,
    description: Optional[str] = None,
    status: Optional[str] = None
) -> Dict:
    """Convenience function - delegates to WorkAssignmentService."""
    return WorkAssignmentService.update_work_info(
        db, work_id, work_name, description, status
    )