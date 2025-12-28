"""Main application class for AutoRBI."""

from tkinter import messagebox
from typing import Dict, List

import customtkinter as ctk
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
)
from UserInterface.components import NotificationSystem, LoadingOverlay

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

        
        # Show login screen initially
        self.show_login()

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

    def show_notification(self, message: str, notification_type: str = "info", duration: int = 5000) -> None:
        """Show a notification."""
        self.notification_system.show_notification(message, notification_type, duration)

    def show_loading(self, message: str = "Loading...", show_progress: bool = False) -> None:
        """Show loading overlay."""
        self.loading_overlay.show(message, show_progress)

    def hide_loading(self) -> None:
        """Hide loading overlay."""
        self.loading_overlay.hide()

    def update_loading_progress(self, value: float, message: str = None) -> None:
        """Update loading progress (0.0 to 1.0)."""
        self.loading_overlay.update_progress(value, message)

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