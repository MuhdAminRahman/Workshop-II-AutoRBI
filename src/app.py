"""Main application class for AutoRBI."""

from tkinter import messagebox

import customtkinter as ctk

import styles
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

        # Initialize views
        self.login_view = LoginView(self, self)
        self.registration_view = RegistrationView(self, self)
        self.main_menu_view = MainMenuView(self, self)
        self.new_work_view = NewWorkView(self, self)
        self.report_menu_view = ReportMenuView(self, self)
        self.work_history_view = WorkHistoryView(self, self)
        self.analytics_view = AnalyticsView(self, self)
        self.settings_view = SettingsView(self, self)
        self.profile_view = ProfileView(self, self)

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
        self.new_work_view.show()

    def show_report_menu(self) -> None:
        """Display the Report Menu view."""
        self.report_menu_view.show()

    def show_work_history(self) -> None:
        """Display the Work History view."""
        self.work_history_view.show()

    def show_analytics(self) -> None:
        """Display the Analytics Dashboard view."""
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

