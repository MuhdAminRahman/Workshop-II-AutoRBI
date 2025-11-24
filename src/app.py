"""Main application class for AutoRBI."""

import tkinter as tk
from tkinter import messagebox

import styles
from UserInterface.views import (
    AnalyticsView,
    LoginView,
    MainMenuView,
    NewWorkView,
    RegistrationView,
    ReportMenuView,
    WorkHistoryView,
)


class AutoRBIApp(tk.Tk):
    """Main window coordinating all AutoRBI views."""

    def __init__(self) -> None:
        super().__init__()
        self.title("AutoRBI")
        self.geometry("1000x700")
        self.minsize(900, 650)

        # Center window on screen
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x_pos = (self.winfo_screenwidth() // 2) - (width // 2)
        y_pos = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x_pos}+{y_pos}")

        # Configure ttk styles
        styles.configure_styles(self)

        # Initialize views
        self.login_view = LoginView(self, self)
        self.registration_view = RegistrationView(self, self)
        self.main_menu_view = MainMenuView(self, self)
        self.new_work_view = NewWorkView(self, self)
        self.report_menu_view = ReportMenuView(self, self)
        self.work_history_view = WorkHistoryView(self, self)
        self.analytics_view = AnalyticsView(self, self)

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

    def logout(self) -> None:
        """Prompt user for logout confirmation and return to login."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.show_login()

