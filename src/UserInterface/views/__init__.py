"""Views package for AutoRBI interface."""

from .login import LoginView
from .registration import RegistrationView
from .main_menu import MainMenuView
from .new_work import NewWorkView
from .report_menu import ReportMenuView
from .work_history import WorkHistoryView
from .analytics import AnalyticsView

__all__ = [
    "LoginView",
    "RegistrationView",
    "MainMenuView",
    "NewWorkView",
    "ReportMenuView",
    "WorkHistoryView",
    "AnalyticsView",
]

