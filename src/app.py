"""Main application class for AutoRBI."""

from tkinter import messagebox
from typing import Dict, List

import customtkinter as ctk

import sys, os

# Absolute path to the folder where *this* file (app.py) lives
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# BASE_DIR == "C:\\Users\\user\\Desktop\\Workshop2\\AutoRBI\\src"

# Path to the AutoRBI_Database folder
DB_ROOT = os.path.join(BASE_DIR, "AutoRBI_Database")
# DB_ROOT == "C:\\Users\\user\\Desktop\\Workshop2\\AutoRBI\\src\\AutoRBI_Database"

# Add it to sys.path if it's not already there
if DB_ROOT not in sys.path:
    sys.path.append(DB_ROOT)


import styles

from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.services.work_service import get_assigned_works,get_work_details
from AutoRBI_Database.database.models.equipment import Equipment as DBEquipment
from AutoRBI_Database.database.models.correction_log import CorrectionLog

from UserInterface.views import (
    AnalyticsView,
    LoginView,
    MainMenuView,
    NewWorkView,
    RegistrationView,
    ReportMenuView,
    WorkHistoryView,
    SettingsView,
    ProfileView,
    UserManagementView,
)
from UserInterface.components import NotificationSystem, LoadingOverlay


from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.services.auth_service import (
    authenticate_user as auth_login,
    register_user as auth_register,
)

from AutoRBI_Database.exceptions import (
    InvalidPasswordError,
    InactiveAccountError,
    AccountAlreadyExistsError,
    ValidationError,
    DatabaseError,
)

from AutoRBI_Database.messages import AuthMessages, RegistrationMessages, ErrorTypes
from AutoRBI_Database.logging_config import get_logger
from AutoRBI_Database.services import admin_service
from AutoRBI_Database.services import profile_service

# Initialize logger
logger = get_logger(__name__)


class AutoRBIApp(ctk.CTk):
    """Main window coordinating all AutoRBI views (CustomTkinter)."""

    def __init__(self) -> None:
        super().__init__()

        # Global CustomTkinter look & feel
        styles.configure_styles()

        self.title("AutoRBI")
        self.geometry("1100x720")
        self.minsize(1000, 680)

        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x_pos = (self.winfo_screenwidth() // 2) - (width // 2)
        y_pos = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

        # Initialize notification system and loading overlay
        self.notification_system = NotificationSystem(self)
        self.loading_overlay = LoadingOverlay(self)

        # Current user info (TODO: Get from authentication)
        self.current_user = None
        self.available_works = None
        self.current_work = None
        # Initialize views
        self.login_view = LoginView(self, self)
        self.registration_view = RegistrationView(self, self)
        self.main_menu_view = MainMenuView(self, self)
        self.new_work_view = None
        self.report_menu_view = ReportMenuView(self, self)
        self.work_history_view = WorkHistoryView(self, self)
        self.analytics_view = None
        self.settings_view = SettingsView(self, self)
        self.profile_view = ProfileView(self, self)
        # Admin views
        self.user_management_view = UserManagementView(self, self)

        # Current user info (TODO: Get from authentication)
        self.current_user = {
            "username": "John Doe",
            "role": "Engineer",
            "email": "john.doe@ipetro.com",
            "group": None,  # Employee group/department set after login
        }
        
        # Current work context in New Work view
        self.current_work = None  # Currently selected work assignment
        self.available_works = []  # Works assigned to employee's group

        # Show login screen initially
        self.show_login()

    def authenticate_user(self, username: str, password: str) -> dict:
        """
        Authenticate user with proper resource cleanup and error handling.

        This method implements:
        - Resource Cleanup: Database session always closes (try-finally)
        - Graceful Degradation: Errors don't crash the app
        - Logging: Track authentication flow

        Args:
            username: Username to authenticate
            password: Plain text password

        Returns:
            Authentication result dictionary from auth_service
        """
        # LOGGING - Log authentication attempt at controller level
        logger.info(f"Controller: Authentication request for username: {username}")

        # RESOURCE CLEANUP - Create database session
        db = SessionLocal()

        try:
            # Call the authentication service
            result = auth_login(db, username, password)

            # If successful, set current user session
            if result["success"]:
                user = result["user"]

                try:
                    # Extract user information for session
                    self.current_user = {
                        "id": user.user_id,
                        "username": user.username,
                        "full_name": getattr(user, "full_name", None),
                        "role": getattr(user, "role", None),
                        "email": getattr(user, "email", None),
                        "created_at": getattr(user, "created_at", None),
                    }

                    # LOGGING - Log successful session creation
                    logger.info(
                        f"Controller: User session created for: {user.username}"
                    )

                except AttributeError as e:
                    # Handle case where user object is missing expected attributes
                    logger.error(
                        f"Controller: Error extracting user attributes: {e}",
                        exc_info=True,
                    )

                    # GRACEFUL DEGRADATION - Return error instead of crashing
                    return {
                        "success": False,
                        "message": "Error processing user data. Please try again.",
                        "user": None,
                        "error_type": "system",
                    }

            # LOGGING - Log result
            if result["success"]:
                logger.info(f"Controller: Authentication successful for: {username}")
            else:
                logger.info(f"Controller: Authentication failed for: {username}")

            return result

        except Exception as e:
            # Catch-all for any unexpected errors at controller level
            logger.error(
                f"Controller: Unexpected error during authentication: {e}",
                exc_info=True,
            )

            return {
                "success": False,
                "message": "An unexpected error occurred. Please try again.",
                "user": None,
                "error_type": "system",
            }

        finally:
            # ALWAYS close database session
            try:
                db.close()
                logger.debug("Controller: Database session closed")
            except Exception as e:
                # Even closing can fail - log but don't raise
                logger.error(
                    f"Controller: Error closing database session: {e}",
                    exc_info=True,
                )

    def register_user(self, full_name: str, username: str, password: str) -> dict:
        """
        Register new user with proper resource cleanup and error handling.

        This method implements:
        - Resource Cleanup: Database session always closes (try-finally)
        - Graceful Degradation: Errors don't crash the app
        - Logging: Track registration flow

        Args:
            full_name: User's full name
            username: Desired username
            password: Plain text password

        Returns:
            Registration result dictionary from auth_service
        """
        # LOGGING - Log registration attempt at controller level
        logger.info(f"Controller: Registration request for username: {username}")

        # RESOURCE CLEANUP - Create database session
        db = SessionLocal()

        try:
            # Call the registration service
            result = auth_register(db, full_name, username, password)

            # LOGGING - Log result
            if result["success"]:
                logger.info(f"Controller: Registration successful for: {username}")
            else:
                logger.info(
                    f"Controller: Registration failed for: {username} - "
                    f"{result.get('error_type', 'unknown')}"
                )

            # Note: We don't automatically log in the user after registration
            # They need to login separately for security
            return result

        except Exception as e:
            # Catch-all for any unexpected errors at controller level
            logger.error(
                f"Controller: Unexpected error during registration: {e}",
                exc_info=True,
            )

            return {
                "success": False,
                "message": (
                    "An unexpected error occurred during registration. "
                    "Please try again."
                ),
                "user": None,
                "error_type": "system",
            }

        finally:
            # ALWAYS close database session
            try:
                db.close()
                logger.debug("Controller: Database session closed")
            except Exception as e:
                logger.error(
                    f"Controller: Error closing database session: {e}",
                    exc_info=True,
                )

    # ========================================================================
    # ADMIN METHODS
    # ========================================================================

    def get_users_list(
        self,
        status_filter: str = None,
        role_filter: str = None,
        search_query: str = None,
        page: int = 1,
        per_page: int = 20,
    ) -> dict:
        """
        Get paginated list of users (admin only).

        Args:
            status_filter: "Active" or "Inactive" (None = all)
            role_filter: "Admin" or "Engineer" (None = all)
            search_query: Search term
            page: Page number
            per_page: Items per page

        Returns:
            Result dict with users list and pagination info
        """
        logger.info(f"Controller: Fetching users list (page {page})")

        db = SessionLocal()
        try:
            result = admin_service.get_users(
                db=db,
                current_user=self.current_user,
                status_filter=status_filter,
                role_filter=role_filter,
                search_query=search_query,
                page=page,
                per_page=per_page,
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error fetching users: {e}")
            return {
                "success": False,
                "message": "Unable to fetch users.",
                "error_type": "system",
            }
        finally:
            db.close()

    def toggle_user_status(self, user_id: int) -> dict:
        """
        Toggle user active/inactive status (admin only).

        Args:
            user_id: ID of user to toggle

        Returns:
            Result dict
        """
        logger.info(f"Controller: Toggling status for user ID {user_id}")

        db = SessionLocal()
        try:
            result = admin_service.toggle_user_status(
                db=db, current_user=self.current_user, target_user_id=user_id
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error toggling user status: {e}")
            return {
                "success": False,
                "message": "Operation failed.",
                "error_type": "system",
            }
        finally:
            db.close()

    def update_user(
        self,
        user_id: int,
        full_name: str = None,
        role: str = None,
        new_password: str = None,
    ) -> dict:
        """
        Update user details (admin only).

        Args:
            user_id: ID of user to update
            full_name: New full name (None = don't change)
            role: New role (None = don't change)
            new_password: New password (None = don't change)

        Returns:
            Result dict
        """
        logger.info(f"Controller: Updating user ID {user_id}")

        db = SessionLocal()
        try:
            result = admin_service.modify_user(
                db=db,
                current_user=self.current_user,
                target_user_id=user_id,
                full_name=full_name,
                role=role,
                new_password=new_password,
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error updating user: {e}")
            return {
                "success": False,
                "message": "Operation failed.",
                "error_type": "system",
            }
        finally:
            db.close()

    def create_new_user(
        self, username: str, full_name: str, password: str, role: str = "Engineer"
    ) -> dict:
        """
        Create new user (admin only).

        Args:
            username: New username
            full_name: Full name
            password: Password
            role: "Admin" or "Engineer"

        Returns:
            Result dict
        """
        logger.info(f"Controller: Creating new user '{username}'")

        db = SessionLocal()
        try:
            result = admin_service.add_user(
                db=db,
                current_user=self.current_user,
                username=username,
                full_name=full_name,
                password=password,
                role=role,
            )
            return result
        except Exception as e:
            logger.error(f"Controller: Error creating user: {e}")
            return {
                "success": False,
                "message": "Operation failed.",
                "error_type": "system",
            }
        finally:
            db.close()

    

    # ========================================================================
    # PROFILE METHODS
    # ========================================================================

    def update_profile(self, full_name: str = None, email: str = None) -> dict:
        """
        Update current user's profile information.

        Args:
            full_name: New full name (None = don't change)
            email: New email (None = don't change)

        Returns:
            Result dict with success status and updated user data
        """
        logger.info(
            f"Controller: Updating profile for user ID {self.current_user.get('id')}"
        )

        db = SessionLocal()
        try:
            result = profile_service.update_profile(
                db=db,
                user_id=self.current_user.get("id"),
                full_name=full_name,
                email=email,
            )

            # Update session data if successful
            if result.get("success") and result.get("user"):
                user_data = result["user"]
                self.current_user["full_name"] = user_data.get("full_name")
                self.current_user["email"] = user_data.get("email")
                logger.info("Controller: Session data updated with new profile info")

            return result

        except Exception as e:
            logger.error(f"Controller: Error updating profile: {e}")
            return {
                "success": False,
                "message": "Unable to update profile.",
                "error_type": "system",
            }
        finally:
            db.close()

    def change_password(self, current_password: str, new_password: str) -> dict:
        """
        Change current user's password.

        Args:
            current_password: Current password for verification
            new_password: New password to set

        Returns:
            Result dict with success status
        """
        logger.info(
            f"Controller: Changing password for user ID {self.current_user.get('id')}"
        )

        db = SessionLocal()
        try:
            result = profile_service.change_password(
                db=db,
                user_id=self.current_user.get("id"),
                current_password=current_password,
                new_password=new_password,
            )

            return result

        except Exception as e:
            logger.error(f"Controller: Error changing password: {e}")
            return {
                "success": False,
                "message": "Unable to change password.",
                "error_type": "system",
            }
        finally:
            db.close()

    def refresh_profile(self) -> dict:
        """
        Refresh current user's profile from database.

        Returns:
            Result dict with user data
        """
        logger.info(
            f"Controller: Refreshing profile for user ID {self.current_user.get('id')}"
        )

        db = SessionLocal()
        try:
            result = profile_service.get_profile(
                db=db, user_id=self.current_user.get("id")
            )

            # Update session data if successful
            if result.get("success") and result.get("user"):
                user_data = result["user"]
                self.current_user["full_name"] = user_data.get("full_name")
                self.current_user["email"] = user_data.get("email")
                self.current_user["role"] = user_data.get("role")
                self.current_user["created_at"] = user_data.get("created_at")

            return result

        except Exception as e:
            logger.error(f"Controller: Error refreshing profile: {e}")
            return {
                "success": False,
                "message": "Unable to load profile.",
                "error_type": "system",
            }
        finally:
            db.close()

    # ------------------------------------------------------------------ #
    # Navigation helpers
    # ------------------------------------------------------------------ #
    def show_login(self) -> None:
        """Display the login view."""
        self.login_view.show()

    def show_registration(self) -> None:
        """Display the registration view."""
        self.registration_view.show()

    def show_main_menu(self) -> None:
        """Display the main menu view."""
        self.main_menu_view.show()

    def show_new_work(self) -> None:
        """Display the New Work view."""
        self.available_works = self.getAssignedWorks()
        self.current_work = self.available_works[0] if self.available_works else None
        self.new_work_view = NewWorkView(self, self)
        self.new_work_view.show()

    def show_report_menu(self) -> None:
        """Display the Report Menu view."""
        self.report_menu_view.show()

    def show_work_history(self) -> None:
        """Display the Work History view."""
        self.work_history_view.show()

    def show_analytics(self) -> None:
        """Display the Analytics Dashboard view."""
        self.available_works = self.getAssignedWorks()
        self.current_work = self.available_works[0] if self.available_works else None
        self.analytics_view = AnalyticsView(self, self)
        self.analytics_view.show()

    def show_settings(self) -> None:
        """Display the Settings view."""
        self.settings_view.show()

    def show_profile(self) -> None:
        """Display the Profile view."""
        self.profile_view.show()

    def logout(self) -> None:
        """Prompt user for logout confirmation and return to login."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.notification_system.clear_all()
            self.show_login()

    def show_notification(
        self, message: str, notification_type: str = "info", duration: int = 5000
    ) -> None:
        """Show a notification."""
        self.notification_system.show_notification(message, notification_type, duration)

    def show_loading(
        self, message: str = "Loading...", show_progress: bool = False
    ) -> None:
        """Show loading overlay."""
        self.loading_overlay.show(message, show_progress)

    def hide_loading(self) -> None:
        """Hide loading overlay."""
        self.loading_overlay.hide()

    def update_loading_progress(self, value: float, message: str = None) -> None:
        """Update loading progress (0.0 to 1.0)."""
        self.loading_overlay.update_progress(value, message)
        
    def show_user_management(self) -> None:
        """Display the User Management view (admin only)."""
        # Check if user is admin
        if self.current_user.get("role") != "Admin":
            messagebox.showerror(
                "Access Denied", "Only administrators can access User Management."
            )
            return

        # Show the view
        self.user_management_view.show()

    # ------------------------------------------------------------------ #
    # New Work Methods
    # ------------------------------------------------------------------ #
    def getAssignedWorks(self)-> list[Dict[str,str]]:
        """Get list of works assigned to current user (stub)."""
        db = SessionLocal()
        try:
            user_id = self.current_user.get("id") 
            works = get_assigned_works(db, user_id)
            work_details = []
            work_list = []
            for work in works:
                work_details.append(get_work_details(db, work.work_id))
            for work in work_details:
                work_list.append({
                    "work_id": f"{work.work_id}",
                    "work_name": f"{work.work_name}"
                })
            return work_list
        finally:
            db.close()

    def getWorkDetails(self, work_id: int) -> Dict:
        """Get detailed information about a specific work (stub)."""
        db = SessionLocal()
        try:
            workdetails = get_work_details(db, work_id)
            if workdetails:
                details = {
                    "work_id": workdetails.work_id,
                    "work_name": workdetails.work_name,
                    "description": workdetails.description,
                    "status": workdetails.status,
                    "created_at": workdetails.created_at,
                    # Add more fields as needed
                }
                return details
            else:
                return {}
        finally:
            db.close()
    
        """
        Get work progress statistics.
        
        Returns:
            Dictionary with:
                - total_equipment: Total equipment count
                - extracted_equipment: Equipment with extraction complete
                - corrected_equipment: Equipment with corrections
                - completion_percentage: Overall completion %
        """
        db = SessionLocal()
        try:
            # Total equipment
            total = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id
            ).count()
            
            # Equipment with extraction date
            extracted = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.extracted_date.isnot(None)
            ).count()
            
            # Equipment with corrections
            corrected_equipment_ids = db.query(CorrectionLog.equipment_id).distinct().join(
                DBEquipment
            ).filter(
                DBEquipment.work_id == work_id
            ).all()
            corrected = len(corrected_equipment_ids)
            
            # Calculate completion percentage
            completion = (extracted / total * 100) if total > 0 else 0
            
            return {
                'total_equipment': total,
                'extracted_equipment': extracted,
                'corrected_equipment': corrected,
                'completion_percentage': round(completion, 1)
            }
            
        except Exception as e:
            print(f"Error getting work progress: {e}")
            return {
                'total_equipment': 0,
                'extracted_equipment': 0,
                'corrected_equipment': 0,
                'completion_percentage': 0.0
            }
        finally:
            db.close()