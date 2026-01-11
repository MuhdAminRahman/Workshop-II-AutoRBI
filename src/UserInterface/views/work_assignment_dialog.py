"""
Work Assignment Dialog
Modal dialog for creating new works and assigning engineers.
"""

import customtkinter as ctk
from typing import Optional, Callable, List, Dict
from tkinter import messagebox

from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.services.work_assignment_service import (
    get_all_engineers,
    create_work_and_assign,
)
from AutoRBI_Database.exceptions import ValidationError, DatabaseError
from AutoRBI_Database.logging_config import get_logger

logger = get_logger(__name__)


class WorkAssignmentDialog(ctk.CTkToplevel):
    """Dialog for creating work and assigning engineers."""

    def __init__(
        self, parent, on_success: Optional[Callable] = None, notification_system=None
    ):
        """
        Initialize the work assignment dialog.

        Args:
            parent: Parent window
            on_success: Callback function when work is created successfully
            notification_system: Notification system for displaying messages
        """
        super().__init__(parent)

        self.on_success = on_success
        self.notification_system = notification_system
        self.engineers: List[Dict] = []
        self.engineer_vars: Dict[int, ctk.BooleanVar] = {}
        self.search_var = ctk.StringVar()
        self.search_timer = None
        self.search_var.trace_add("write", self._on_search_changed)
        

        # Dialog configuration
        self.title("Create New Work Assignment")
        self.geometry("600x750")
        self.minsize(500, 600)
        self.resizable(True, True)
        
        
        # Make dialog modal
        self.transient(parent)
        self.grab_set()

        # Center the dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.winfo_screenheight() // 2) - (750 // 2)
        self.geometry(f"600x750+{x}+{y}")

        # Build UI
        self._build_ui()

        # Load engineers
        self._load_engineers()
        
        self.bind("<Return>", lambda e: self._on_create())
        self.bind("<Escape>", lambda e: self._on_cancel())
        
        # Focus on work name entry
        self.work_name_entry.focus()

    def _build_ui(self):
        """Build the dialog UI."""
        # Main container with padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Header
        header_label = ctk.CTkLabel(
            main_frame, text="Create New Work Assignment", font=("Segoe UI", 18, "bold")
        )
        header_label.pack(pady=(0, 20))

        # Work Information Section
        work_section = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"))
        work_section.pack(fill="x", pady=(0, 20))

        # Work Name
        work_name_label = ctk.CTkLabel(
            work_section, text="Work Name *", font=("Segoe UI", 12, "bold"), anchor="w"
        )
        work_name_label.pack(fill="x", padx=16, pady=(16, 4))

        self.work_name_entry = ctk.CTkEntry(
            work_section,
            placeholder_text="Enter work name (e.g., Equipment Inspection)",
            font=("Segoe UI", 11),
            height=36,
        )
        self.work_name_entry.pack(fill="x", padx=16, pady=(0, 12))

        # Description
        desc_label = ctk.CTkLabel(
            work_section,
            text="Description (Optional)",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        desc_label.pack(fill="x", padx=16, pady=(0, 4))

        self.description_text = ctk.CTkTextbox(
            work_section, font=("Segoe UI", 11), height=80, wrap="word"
        )
        self.description_text.pack(fill="x", padx=16, pady=(0, 16))

        self.description_text.bind("<Return>", lambda e: None)  # Allow Enter in textbox
        
        # Engineer Assignment Section
        engineer_section = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"))
        engineer_section.pack(fill="both", expand=True)

        # Section header
        engineer_header = ctk.CTkLabel(
            engineer_section,
            text="Assign Engineers",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        engineer_header.pack(fill="x", padx=16, pady=(16, 8))

        # Search bar
        search_frame = ctk.CTkFrame(engineer_section, fg_color="transparent")
        search_frame.pack(fill="x", padx=16, pady=(0, 8))

        self.search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search engineers by name or username...",
            font=("Segoe UI", 11),
            height=36,
            textvariable=self.search_var,
        )
        self.search_entry.pack(fill="x")

        # Engineers list (scrollable) 
        self.engineers_frame = ctk.CTkScrollableFrame(
            engineer_section,
            fg_color=("white", "gray25"),
        )
        self.engineers_frame.pack(fill="both", expand=True, padx=16, pady=(0, 12))

        # Selection counter
        self.selection_label = ctk.CTkLabel(
            engineer_section,
            text="Selected: 0 engineer(s)",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
        )
        self.selection_label.pack(padx=16, pady=(0, 16))

        # Action buttons - FIXED LAYOUT
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(16, 0))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=140,
            height=40,
            font=("Segoe UI", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray35"),
        )
        cancel_btn.pack(side="left", pady=5)

        self.create_btn = ctk.CTkButton(
            button_frame,
            text="Create & Assign",
            command=self._on_create,
            width=180,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954"),
        )
        self.create_btn.pack(side="right", pady=5)

    def _load_engineers(self):
        """Load all active engineers from database."""
        try:
            with SessionLocal() as db:
                self.engineers = get_all_engineers(db)
                self._populate_engineers_list()

                if not self.engineers:
                    no_engineers_label = ctk.CTkLabel(
                        self.engineers_frame,
                        text="No active engineers found",
                        font=("Segoe UI", 11),
                        text_color=("gray50", "gray70"),
                    )
                    no_engineers_label.pack(pady=40)

        except Exception as e:
            logger.error(f"Error loading engineers: {str(e)}")
            messagebox.showerror("Error", f"Failed to load engineers: {str(e)}")

    def _populate_engineers_list(self, filter_text: str = ""):
        """
        Populate the engineers list with checkboxes.

        Args:
            filter_text: Text to filter engineers by name or username
        """
        # Clear existing widgets
        for widget in self.engineers_frame.winfo_children():
            widget.destroy()

        # Don't clear engineer_vars - keep selections across searches

        # Filter engineers
        filter_lower = filter_text.lower()
        filtered_engineers = [
            eng
            for eng in self.engineers
            if (
                filter_lower in eng["full_name"].lower()
                or filter_lower in eng["username"].lower()
            )
        ]

        if not filtered_engineers:
            no_results_label = ctk.CTkLabel(
                self.engineers_frame,
                text="No engineers match your search",
                font=("Segoe UI", 11),
                text_color=("gray50", "gray70"),
            )
            no_results_label.pack(pady=40)
            return

        # Create checkbox for each engineer
        for engineer in filtered_engineers:
            engineer_id = engineer["user_id"]

            # Create frame for engineer row
            eng_frame = ctk.CTkFrame(
                self.engineers_frame, fg_color="transparent", height=40
            )
            eng_frame.pack(fill="x", pady=2, padx=4)

            # Checkbox variable - reuse existing or create new
            if engineer_id not in self.engineer_vars:
                var = ctk.BooleanVar(value=False)
                self.engineer_vars[engineer_id] = var
                var.trace_add("write", lambda *args: self._update_selection_count())
            else:
                var = self.engineer_vars[engineer_id]

            # Checkbox
            checkbox = ctk.CTkCheckBox(
                eng_frame,
                text="",
                variable=var,
                width=20,
                checkbox_width=20,
                checkbox_height=20,
            )
            checkbox.pack(side="left", padx=(4, 12))

            # Engineer info
            info_frame = ctk.CTkFrame(eng_frame, fg_color="transparent")
            info_frame.pack(side="left", fill="x", expand=True)

            name_label = ctk.CTkLabel(
                info_frame,
                text=engineer["full_name"],
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            )
            name_label.pack(anchor="w")

            details_text = f"{engineer['username']}"
            if engineer.get("email"):
                details_text += f" • {engineer['email']}"

            details_label = ctk.CTkLabel(
                info_frame,
                text=details_text,
                font=("Segoe UI", 9),
                text_color=("gray50", "gray70"),
                anchor="w",
            )
            details_label.pack(anchor="w")

    def _on_search_changed(self, *args):
        """Handle search text changes with debouncing."""
        if self.search_timer:
            self.after_cancel(self.search_timer)
        self.search_timer = self.after(300, self._perform_search)
    
    def _perform_search(self):
        """Perform the actual search after debounce delay."""
        search_text = self.search_var.get()
        # Populate list - selections are preserved automatically via engineer_vars
        self._populate_engineers_list(search_text)

    def _update_selection_count(self):
        """Update the selection counter label."""
        selected_count = sum(1 for var in self.engineer_vars.values() if var.get())
        self.selection_label.configure(text=f"Selected: {selected_count} engineer(s)")

    def _validate_inputs(self) -> bool:
        """
        Validate form inputs.

        Returns:
            True if valid, False otherwise
        """
        work_name = self.work_name_entry.get().strip()

        if not work_name:
            messagebox.showerror("Validation Error", "Please enter a work name.")
            self.work_name_entry.focus()
            return False

        if len(work_name) < 3:
            messagebox.showerror(
                "Validation Error", "Work name must be at least 3 characters long."
            )
            self.work_name_entry.focus()
            return False

        return True

    def _on_create(self):
        """Handle create button click."""
        # Validate inputs
        if not self._validate_inputs():
            return

        # Get form data
        work_name = self.work_name_entry.get().strip()
        description = self.description_text.get("1.0", "end-1c").strip()
        description = description if description else None

        # Get selected engineers
        selected_user_ids = [
            user_id for user_id, var in self.engineer_vars.items() if var.get()
        ]

        # Disable button during creation
        self.create_btn.configure(state="disabled", text="Creating...")
        self.update()

        try:
            with SessionLocal() as db:
                # Create work and assign engineers
                result = create_work_and_assign(
                    db=db,
                    work_name=work_name,
                    description=description,
                    assigned_user_ids=selected_user_ids if selected_user_ids else None,
                )

                # Show success message
                success_msg = f"Work '{work_name}' created successfully!"
                if result["assignment_count"] > 0:
                    success_msg += (
                        f"\n{result['assignment_count']} engineer(s) assigned."
                    )

                messagebox.showinfo("Success", success_msg)

                # Show notification if available
                if self.notification_system:
                    self.notification_system.show_success(f"Work created: {work_name}")

                # Call success callback
                if self.on_success:
                    self.on_success(result)

                # Close dialog
                self.destroy()

        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
            logger.warning(f"Validation error: {str(e)}")
        except DatabaseError as e:
            messagebox.showerror("Database Error", str(e))
            logger.error(f"Database error: {str(e)}")
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
            logger.error(f"Unexpected error creating work: {str(e)}")
        finally:
            # Re-enable button only if dialog still exists
            if self.winfo_exists():
                self.create_btn.configure(state="normal", text="Create & Assign")

    def _on_cancel(self):
        """Handle cancel button click."""
        self.destroy()
