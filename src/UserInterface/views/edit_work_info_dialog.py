"""
Edit Work Info Dialog
Dialog for editing work information (name, description, status).
"""

import customtkinter as ctk
from typing import Dict
from tkinter import messagebox

from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.services.work_assignment_service import update_work_info
from AutoRBI_Database.exceptions import ValidationError
from AutoRBI_Database.logging_config import get_logger
from UserInterface.views.base_dialog import BaseDialog
from UserInterface.views.constants import DIALOG_EDIT_WORK_INFO, WORK_STATUS

logger = get_logger(__name__)


class EditWorkInfoDialog(BaseDialog):
    """Dialog for editing work information."""

    def __init__(
        self,
        parent,
        work_data: Dict,
        on_success=None,
        notification_system=None,
        controller=None,
    ):
        """
        Initialize the edit work info dialog.

        Args:
            parent: Parent window
            work_data: Dictionary containing work info
            on_success: Callback function on successful save
            notification_system: Notification system reference
            controller: Application controller for DB operations
        """
        self.work_data = work_data
        self.controller = controller

        # These will be set in _build_content
        self.name_entry = None
        self.desc_text = None
        self.status_var = None

        super().__init__(
            parent=parent,
            title="Edit Work Information",
            width=DIALOG_EDIT_WORK_INFO["width"],
            height=DIALOG_EDIT_WORK_INFO["height"],
            on_success=on_success,
            notification_system=notification_system,
            resizable=True,
        )

        # Bind Enter key for save (but not in textbox)
        self.bind("<Return>", self._on_enter_key)

        # Focus on work name entry
        self.name_entry.focus()

    def _on_enter_key(self, event):
        """Handle Enter key - save unless in textbox."""
        # Check if the event widget is the textbox's internal widget
        if (
            hasattr(self.desc_text, "_textbox")
            and event.widget == self.desc_text._textbox
        ):
            return  # Allow Enter in textbox
        self._handle_save()

    def _build_content(self):
        """Build dialog content."""
        work = self.work_data["work"]

        # Header
        header_label = ctk.CTkLabel(
            self.content_frame,
            text="Edit Work Information",
            font=("Segoe UI", 18, "bold"),
        )
        header_label.pack(pady=(0, 20))

        # Work Information Section
        work_section = ctk.CTkFrame(self.content_frame, fg_color=("gray90", "gray20"))
        work_section.pack(fill="both", expand=False, pady=(0, 20))

        # Work Name
        work_name_label = ctk.CTkLabel(
            work_section,
            text="Work Name *",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        work_name_label.pack(fill="x", padx=16, pady=(16, 4))

        self.name_entry = ctk.CTkEntry(
            work_section,
            placeholder_text="Enter work name",
            font=("Segoe UI", 11),
            height=36,
        )
        self.name_entry.pack(fill="x", padx=16, pady=(0, 12))
        self.name_entry.insert(0, work["work_name"])

        # Description
        desc_label = ctk.CTkLabel(
            work_section,
            text="Description (Optional)",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        desc_label.pack(fill="x", padx=16, pady=(0, 4))

        self.desc_text = ctk.CTkTextbox(
            work_section,
            font=("Segoe UI", 11),
            height=100,
            wrap="word",
        )
        self.desc_text.pack(fill="x", padx=16, pady=(0, 12))
        if work.get("description"):
            self.desc_text.insert("1.0", work["description"])

        # Status
        status_label = ctk.CTkLabel(
            work_section,
            text="Status",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        status_label.pack(fill="x", padx=16, pady=(0, 4))

        self.status_var = ctk.StringVar(value=work["status"])
        status_menu = ctk.CTkOptionMenu(
            work_section,
            values=[WORK_STATUS["IN_PROGRESS"], WORK_STATUS["COMPLETED"]],
            variable=self.status_var,
            height=36,
            font=("Segoe UI", 11),
        )
        status_menu.pack(fill="x", padx=16, pady=(0, 16))

    def _validate(self) -> bool:
        """Validate form inputs."""
        new_name = self.name_entry.get().strip()

        if not new_name:
            self._show_validation_error("Work name cannot be empty.")
            self.name_entry.focus()
            return False

        if len(new_name) < 3:
            self._show_validation_error("Work name must be at least 3 characters.")
            self.name_entry.focus()
            return False

        return True

    def _on_save(self):
        """Save work information changes."""
        if not self._validate():
            self._on_save_complete(success=False)
            return

        work_id = self.work_data["work"]["work_id"]
        new_name = self.name_entry.get().strip()
        new_desc = self.desc_text.get("1.0", "end-1c").strip()
        new_status = self.status_var.get()

        try:
            # Use controller if available
            if self.controller and hasattr(self.controller, "update_work_info"):
                result = self.controller.update_work_info(
                    work_id,
                    work_name=new_name,
                    description=new_desc if new_desc else None,
                    status=new_status,
                )
                if not result.get("success"):
                    raise Exception(result.get("message", "Unknown error"))
            else:
                with SessionLocal() as db:
                    update_work_info(
                        db,
                        work_id,
                        work_name=new_name,
                        description=new_desc if new_desc else None,
                        status=new_status,
                    )

            self._show_success("Work information updated successfully!")
            self._on_save_complete(success=True)

        except ValidationError as e:
            self._show_validation_error(str(e))
            self._on_save_complete(success=False)
        except Exception as e:
            logger.error(f"Error updating work: {str(e)}")
            self._show_error(f"Failed to update work: {str(e)}")
            self._on_save_complete(success=False)
