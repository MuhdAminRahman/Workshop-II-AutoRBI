"""Views package for AutoRBI interface."""

from .login import LoginView
from .registration import RegistrationView
from .main_menu import MainMenuView
from .new_work import NewWorkView
from .report_menu import ReportMenuView
from .work_history import WorkHistoryView
from .analytics import AnalyticsView
from .settings import SettingsView
from .profile import ProfileView
from .constants import Fonts, Colors, Sizes, Messages, TableColumns
from .constants import (
    WORK_TABLE_COLUMNS,
    WORK_STATUS,
    WORK_STATUS_FILTER_MAP,
    WORK_ROW_HEIGHT,
    WORK_NAME_MAX_LENGTH,
    WORK_NAME_TRUNCATE_LENGTH,
    DIALOG_EDIT_ASSIGNMENTS,
    DIALOG_EDIT_WORK_INFO,
    WORKS_PER_PAGE,
)
from .page_builders import Page1Builder, Page2Builder
from .ui_updater import UIUpdateManager
from .user_management import UserManagementView
from .admin_menu import AdminMenuView
from .work_management_view import WorkManagementView
from .work_assignment_dialog import WorkAssignmentDialog
from .base_dialog import BaseDialog
from .edit_assignments_dialog import EditAssignmentsDialog
from .edit_work_info_dialog import EditWorkInfoDialog


__all__ = [
    "LoginView",
    "RegistrationView",
    "MainMenuView",
    "NewWorkView",
    "ReportMenuView",
    "WorkHistoryView",
    "AnalyticsView",
    "SettingsView",
    "ProfileView",
    "Fonts",
    "Colors",
    "Sizes",
    "Messages",
    "TableColumns",
    "WORK_TABLE_COLUMNS",
    "WORK_STATUS",
    "WORK_STATUS_FILTER_MAP",
    "WORK_ROW_HEIGHT",
    "WORK_NAME_MAX_LENGTH",
    "WORK_NAME_TRUNCATE_LENGTH",
    "DIALOG_EDIT_ASSIGNMENTS",
    "DIALOG_EDIT_WORK_INFO",
    "WORKS_PER_PAGE",
    "Page1Builder",
    "Page2Builder",
    "UIUpdateManager",
    "UserManagementView",
    "AdminMenuView",
    "WorkManagementView",
    "WorkAssignmentDialog",
    "BaseDialog",
    "EditAssignmentsDialog",
    "EditWorkInfoDialog",
]