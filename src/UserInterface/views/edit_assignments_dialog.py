"""
Edit Assignments Dialog
Dialog for editing engineer assignments for a work.
"""

import customtkinter as ctk
from typing import Dict, List, Optional
from tkinter import messagebox

from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.services.work_assignment_service import (
    get_all_engineers,
    update_work_assignments,
)
from AutoRBI_Database.logging_config import get_logger
from UserInterface.views.base_dialog import BaseDialog
from UserInterface.views.constants import DIALOG_EDIT_ASSIGNMENTS

logger = get_logger(__name__)


class EditAssignmentsDialog(BaseDialog):
    """Dialog for editing work assignments."""
    
    def __init__(
        self,
        parent,
        work_data: Dict,
        on_success=None,
        notification_system=None,
        controller=None,
    ):
        """
        Initialize the edit assignments dialog.
        
        Args:
            parent: Parent window
            work_data: Dictionary containing work info and assigned engineers
            on_success: Callback function on successful save
            notification_system: Notification system reference
            controller: Application controller for DB operations
        """
        self.work_data = work_data
        self.controller = controller
        self.engineers: List[Dict] = []
        self.engineer_vars: Dict[int, ctk.BooleanVar] = {}
        
        super().__init__(
            parent=parent,
            title="Edit Work Assignments",
            width=DIALOG_EDIT_ASSIGNMENTS["width"],
            height=DIALOG_EDIT_ASSIGNMENTS["height"],
            on_success=on_success,
            notification_system=notification_system,
            resizable=False,
        )
        
        # Load engineers after UI is built
        self._load_engineers()
    
    def _build_content(self):
        """Build dialog content."""
        # Header
        work_name = self.work_data["work"]["work_name"]
        header_label = ctk.CTkLabel(
            self.content_frame,
            text=f"Edit Assignments\n{work_name}",
            font=("Segoe UI", 16, "bold"),
        )
        header_label.pack(pady=(0, 16))
        
        # Engineers list label
        engineers_label = ctk.CTkLabel(
            self.content_frame,
            text="Select Engineers:",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        engineers_label.pack(fill="x", pady=(0, 8))
        
        # Scrollable engineers list
        self.engineers_frame = ctk.CTkScrollableFrame(
            self.content_frame,
            fg_color=("white", "gray25"),
            height=350,
        )
        self.engineers_frame.pack(fill="both", expand=False, pady=(0, 16))
        
        # Selection counter
        self.selection_label = ctk.CTkLabel(
            self.content_frame,
            text="Selected: 0 engineer(s)",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
        )
        self.selection_label.pack()
    
    def _load_engineers(self):
        """Load engineers and populate checkboxes."""
        try:
            # Use controller if available, otherwise direct DB access
            if self.controller and hasattr(self.controller, 'get_all_engineers'):
                self.engineers = self.controller.get_all_engineers()
            else:
                with SessionLocal() as db:
                    self.engineers = get_all_engineers(db)
            
            currently_assigned = {
                eng["user_id"] for eng in self.work_data["assigned_engineers"]
            }
            
            if not self.engineers:
                no_eng_label = ctk.CTkLabel(
                    self.engineers_frame,
                    text="No active engineers found",
                    font=("Segoe UI", 11),
                    text_color=("gray50", "gray70"),
                )
                no_eng_label.pack(pady=40)
                return
            
            for engineer in self.engineers:
                eng_id = engineer["user_id"]
                
                eng_frame = ctk.CTkFrame(
                    self.engineers_frame, fg_color="transparent"
                )
                eng_frame.pack(fill="x", pady=4, padx=8)
                
                var = ctk.BooleanVar(value=(eng_id in currently_assigned))
                self.engineer_vars[eng_id] = var
                var.trace_add("write", lambda *args: self._update_selection_count())
                
                checkbox = ctk.CTkCheckBox(
                    eng_frame,
                    text=f"{engineer['full_name']} ({engineer['username']})",
                    variable=var,
                    font=("Segoe UI", 11),
                )
                checkbox.pack(anchor="w")
            
            self._update_selection_count()
                
        except Exception as e:
            logger.error(f"Error loading engineers: {str(e)}")
            self._show_error(f"Failed to load engineers: {str(e)}")
    
    def _update_selection_count(self):
        """Update the selection counter."""
        count = sum(1 for var in self.engineer_vars.values() if var.get())
        self.selection_label.configure(text=f"Selected: {count} engineer(s)")
    
    def _on_save(self):
        """Save assignment changes."""
        work_id = self.work_data["work"]["work_id"]
        
        # Calculate changes
        currently_assigned = {
            eng["user_id"] for eng in self.work_data["assigned_engineers"]
        }
        newly_selected = {
            user_id for user_id, var in self.engineer_vars.items() if var.get()
        }
        
        to_add = list(newly_selected - currently_assigned)
        to_remove = list(currently_assigned - newly_selected)
        
        if not to_add and not to_remove:
            messagebox.showinfo("No Changes", "No changes to save.")
            self._on_save_complete(success=False)
            return
        
        try:
            # Use controller if available
            if self.controller and hasattr(self.controller, 'update_work_assignments'):
                result = self.controller.update_work_assignments(work_id, to_add, to_remove)
                if not result.get("success"):
                    raise Exception(result.get("message", "Unknown error"))
            else:
                with SessionLocal() as db:
                    update_work_assignments(db, work_id, to_add, to_remove)
            
            self._show_success(
                f"Assignments updated!\nAdded: {len(to_add)}, Removed: {len(to_remove)}"
            )
            self._on_save_complete(success=True)
            
        except Exception as e:
            logger.error(f"Error updating assignments: {str(e)}")
            self._show_error(f"Failed to update assignments: {str(e)}")
            self._on_save_complete(success=False)