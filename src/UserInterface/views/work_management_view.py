"""
Work Management View
View for managing works and engineer assignments (Admin only).
"""

import customtkinter as ctk
from typing import Optional, List, Dict
from tkinter import messagebox
from datetime import datetime

from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.services.work_assignment_service import (
    get_all_works_with_assignments,
    get_work_with_assignments,
    update_work_assignments,
    delete_work_and_assignments,
    update_work_info,
    get_all_engineers,
)
from AutoRBI_Database.exceptions import ValidationError, DatabaseError
from AutoRBI_Database.logging_config import get_logger
from UserInterface.views.work_assignment_dialog import WorkAssignmentDialog

logger = get_logger(__name__)


class WorkManagementView:
    """View for managing works and assignments."""

    def __init__(self, parent: ctk.CTk, controller):
        """
        Initialize the work management view.

        Args:
            parent: Parent window
            controller: Application controller
        """
        self.parent = parent
        self.controller = controller
        self.works_data: List[Dict] = []
        self.selected_work: Optional[Dict] = None
        self.search_var = ctk.StringVar()
        self.filter_var = ctk.StringVar(value="All")

        # UI components
        self.works_container: Optional[ctk.CTkScrollableFrame] = None
        self.details_panel: Optional[ctk.CTkFrame] = None

    def show(self):
        """Display the work management view."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Root content frame
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(2, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header section
        self._build_header(root_frame)

        # Toolbar section
        self._build_toolbar(root_frame)

        # Content section (works list and details)
        content_frame = ctk.CTkFrame(root_frame, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)

        # Works list
        self._build_works_list(content_frame)

        # Details panel
        self._build_details_panel(content_frame)

        # Load works data
        self._load_works()

    def _build_header(self, parent):
        """Build the header section."""
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 12))
        header_frame.grid_columnconfigure(0, weight=1)

        # Left side: Title and back button
        left_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        left_frame.grid(row=0, column=0, sticky="w")

        back_btn = ctk.CTkButton(
            left_frame,
            text="← Back",
            command=self._on_back,
            width=80,
            height=32,
            font=("Segoe UI", 11),
            fg_color="transparent",
            hover_color=("gray85", "gray25"),
            border_width=1,
            border_color=("gray70", "gray40"),
        )
        back_btn.pack(side="left", padx=(0, 12))

        title_label = ctk.CTkLabel(
            left_frame, text="Work Management", font=("Segoe UI", 24, "bold")
        )
        title_label.pack(side="left")

        # Right side: Create button
        create_btn = ctk.CTkButton(
            header_frame,
            text="+ Create New Work",
            command=self._open_create_dialog,
            width=160,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954"),
        )
        create_btn.grid(row=0, column=1, sticky="e")

    def _build_toolbar(self, parent):
        """Build the toolbar with search and filter."""
        toolbar_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        toolbar_frame.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        toolbar_frame.grid_columnconfigure(0, weight=1)

        inner_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
        inner_frame.pack(fill="x", padx=16, pady=12)
        inner_frame.grid_columnconfigure(0, weight=1)

        # Search bar
        search_entry = ctk.CTkEntry(
            inner_frame,
            placeholder_text="🔍 Search works by name or description...",
            font=("Segoe UI", 11),
            height=36,
            textvariable=self.search_var,
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.search_var.trace_add("write", lambda *args: self._filter_works())

        # Status filter
        filter_menu = ctk.CTkOptionMenu(
            inner_frame,
            values=["All", "In Progress", "Completed"],
            variable=self.filter_var,
            command=lambda _: self._filter_works(),
            width=140,
            height=36,
            font=("Segoe UI", 11),
        )
        filter_menu.grid(row=0, column=1)

        # Refresh button
        refresh_btn = ctk.CTkButton(
            inner_frame,
            text="↻",
            command=self._load_works,
            width=40,
            height=36,
            font=("Segoe UI", 16),
            fg_color=("gray80", "gray30"),
            hover_color=("gray70", "gray35"),
        )
        refresh_btn.grid(row=0, column=2, padx=(12, 0))

    def _build_works_list(self, parent):
        """Build the works list section."""
        list_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Header
        list_header = ctk.CTkLabel(
            list_frame, text="Works List", font=("Segoe UI", 14, "bold"), anchor="w"
        )
        list_header.pack(fill="x", padx=16, pady=(16, 8))

        # Column headers
        headers_frame = ctk.CTkFrame(list_frame, fg_color="transparent", height=30)
        headers_frame.pack(fill="x", padx=16, pady=(0, 8))
        headers_frame.pack_propagate(False)

        headers = [
            ("Work Name", 0.35),
            ("Status", 0.15),
            ("Engineers", 0.20),
            ("Created", 0.20),
            ("Actions", 0.10),
        ]

        for header_text, width_ratio in headers:
            header_label = ctk.CTkLabel(
                headers_frame,
                text=header_text,
                font=("Segoe UI", 10, "bold"),
                text_color=("gray50", "gray70"),
                anchor="w",
            )
            x_pos = sum(
                h[1] for h in headers[: headers.index((header_text, width_ratio))]
            )
            header_label.place(relx=x_pos, rely=0.5, anchor="w", relwidth=width_ratio)

        # Scrollable works container
        self.works_container = ctk.CTkScrollableFrame(
            list_frame, fg_color=("white", "gray25")
        )
        self.works_container.pack(fill="both", expand=True, padx=16, pady=(0, 16))

    def _build_details_panel(self, parent):
        """Build the details panel section."""
        self.details_panel = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        self.details_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        # Initially show empty state
        self._show_empty_details()

    def _show_empty_details(self):
        """Show empty state in details panel."""
        for widget in self.details_panel.winfo_children():
            widget.destroy()

        empty_label = ctk.CTkLabel(
            self.details_panel,
            text="Select a work to view details",
            font=("Segoe UI", 12),
            text_color=("gray50", "gray70"),
        )
        empty_label.pack(expand=True)

    def _load_works(self):
        """Load all works from database."""
        try:
            with SessionLocal() as db:
                self.works_data = get_all_works_with_assignments(db)
                self._display_works()

                # Show notification
                if hasattr(self.controller, "notification_system"):
                    self.controller.notification_system.show_notification(
                        f"Loaded {len(self.works_data)} work(s)"
                    )

        except Exception as e:
            logger.error(f"Error loading works: {str(e)}")
            messagebox.showerror("Error", f"Failed to load works: {str(e)}")

    def _filter_works(self):
        """Filter works based on search and filter criteria."""
        # Safety check: ensure we have data and container
        if not self.works_container or not self.works_container.winfo_exists():
            return
        self._display_works()

    def _display_works(self):
        """Display works in the list."""
        # Safety check: ensure container exists
        if not self.works_container or not self.works_container.winfo_exists():
            return
            
        # Clear existing widgets
        for widget in self.works_container.winfo_children():
            widget.destroy()

        # Get filter criteria
        search_text = self.search_var.get().lower()
        status_filter = self.filter_var.get()

        # Filter works
        filtered_works = []
        for work_data in self.works_data:
            work = work_data["work"]

            # Apply status filter
            if status_filter != "All" and work["status"] != status_filter:
                continue

            # Apply search filter
            if search_text:
                work_name = work["work_name"].lower()
                description = (work["description"] or "").lower()
                if search_text not in work_name and search_text not in description:
                    continue

            filtered_works.append(work_data)

        # Display filtered works
        if not filtered_works:
            no_works_label = ctk.CTkLabel(
                self.works_container,
                text="No works found",
                font=("Segoe UI", 12),
                text_color=("gray50", "gray70"),
            )
            no_works_label.pack(pady=40)
            return

        for work_data in filtered_works:
            self._create_work_row(work_data)

    def _create_work_row(self, work_data: Dict):
        """Create a work row in the list."""
        work = work_data["work"]
        assigned_engineers = work_data["assigned_engineers"]

        # Row frame
        row_frame = ctk.CTkFrame(
            self.works_container, fg_color=("gray95", "gray30"), height=60
        )
        row_frame.pack(fill="x", pady=4, padx=4)
        row_frame.pack_propagate(False)

        # Make row clickable
        row_frame.bind("<Button-1>", lambda e: self._select_work(work_data))

        # Work name (truncate if too long)
        work_name = work["work_name"]
        if len(work_name) > 30:
            work_name = work_name[:27] + "..."

        name_label = ctk.CTkLabel(
            row_frame, text=work_name, font=("Segoe UI", 11, "bold"), anchor="w"
        )
        name_label.place(relx=0, rely=0.5, anchor="w", relwidth=0.35, x=12)
        name_label.bind("<Button-1>", lambda e: self._select_work(work_data))

        # Status badge
        status_color = "#2ecc71" if work["status"] == "Completed" else "#3498db"
        status_frame = ctk.CTkFrame(
            row_frame, 
            fg_color=status_color, 
            corner_radius=12,
            height=24  # ← MOVE height HERE
        )
        status_frame.place(relx=0.35, rely=0.5, anchor="w", relwidth=0.13)  # ← REMOVE height from here

        status_label = ctk.CTkLabel(
            status_frame,
            text=work["status"],
            font=("Segoe UI", 9, "bold"),
            text_color="white",
        )
        status_label.place(relx=0.5, rely=0.5, anchor="center")

        # Engineers count
        eng_count = len(assigned_engineers)
        eng_text = f"{eng_count} assigned"
        eng_label = ctk.CTkLabel(
            row_frame, text=eng_text, font=("Segoe UI", 10), anchor="w"
        )
        eng_label.place(relx=0.50, rely=0.5, anchor="w", relwidth=0.20)
        eng_label.bind("<Button-1>", lambda e: self._select_work(work_data))

        # Created date
        created_date = work["created_at"].strftime("%Y-%m-%d")
        date_label = ctk.CTkLabel(
            row_frame, text=created_date, font=("Segoe UI", 10), anchor="w"
        )
        date_label.place(relx=0.70, rely=0.5, anchor="w", relwidth=0.20)
        date_label.bind("<Button-1>", lambda e: self._select_work(work_data))

        # Actions button
        actions_btn = ctk.CTkButton(
            row_frame,
            text="•••",
            command=lambda: self._show_work_actions(work_data),
            width=30,
            height=30,
            font=("Segoe UI", 14, "bold"),
            fg_color="transparent",
            hover_color=("gray85", "gray35"),
        )
        actions_btn.place(relx=0.90, rely=0.5, anchor="w")

    def _select_work(self, work_data: Dict):
        """Select a work and show its details."""
        self.selected_work = work_data
        self._show_work_details(work_data)

    def _show_work_details(self, work_data: Dict):
        """Show work details in the details panel."""
        for widget in self.details_panel.winfo_children():
            widget.destroy()

        work = work_data["work"]
        assigned_engineers = work_data["assigned_engineers"]

        # Scrollable container
        details_container = ctk.CTkScrollableFrame(
            self.details_panel, fg_color="transparent"
        )
        details_container.pack(fill="both", expand=True, padx=16, pady=16)

        # Header
        header_label = ctk.CTkLabel(
            details_container,
            text="Work Details",
            font=("Segoe UI", 16, "bold"),
            anchor="w",
        )
        header_label.pack(fill="x", pady=(0, 16))

        # Work information
        info_frame = ctk.CTkFrame(details_container, fg_color=("white", "gray25"))
        info_frame.pack(fill="x", pady=(0, 12))

        # Work name
        self._add_detail_row(info_frame, "Work Name:", work["work_name"], 0)

        # Status
        status_text = work["status"]
        self._add_detail_row(info_frame, "Status:", status_text, 1)

        # Created date
        created_text = work["created_at"].strftime("%Y-%m-%d %H:%M")
        self._add_detail_row(info_frame, "Created:", created_text, 2)

        # Description
        if work["description"]:
            desc_label = ctk.CTkLabel(
                info_frame,
                text="Description:",
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                text_color=("gray50", "gray70"),
            )
            desc_label.pack(fill="x", padx=12, pady=(12, 4))

            desc_text = ctk.CTkTextbox(
                info_frame, height=80, font=("Segoe UI", 10), wrap="word"
            )
            desc_text.pack(fill="x", padx=12, pady=(0, 12))
            desc_text.insert("1.0", work["description"])
            desc_text.configure(state="disabled")

        # Assigned Engineers section
        engineers_label = ctk.CTkLabel(
            details_container,
            text=f"Assigned Engineers ({len(assigned_engineers)})",
            font=("Segoe UI", 14, "bold"),
            anchor="w",
        )
        engineers_label.pack(fill="x", pady=(8, 8))

        if assigned_engineers:
            engineers_frame = ctk.CTkFrame(
                details_container, fg_color=("white", "gray25")
            )
            engineers_frame.pack(fill="x")

            for engineer in assigned_engineers:
                eng_row = ctk.CTkFrame(engineers_frame, fg_color="transparent")
                eng_row.pack(fill="x", padx=12, pady=6)

                # Engineer icon and name
                icon_label = ctk.CTkLabel(eng_row, text="👤", font=("Segoe UI", 16))
                icon_label.pack(side="left", padx=(0, 8))

                info_container = ctk.CTkFrame(eng_row, fg_color="transparent")
                info_container.pack(side="left", fill="x", expand=True)

                name_label = ctk.CTkLabel(
                    info_container,
                    text=engineer["full_name"],
                    font=("Segoe UI", 11, "bold"),
                    anchor="w",
                )
                name_label.pack(anchor="w")

                details_text = (
                    f"{engineer['username']} • {engineer.get('email', 'N/A')}"
                )
                details_label = ctk.CTkLabel(
                    info_container,
                    text=details_text,
                    font=("Segoe UI", 9),
                    text_color=("gray50", "gray70"),
                    anchor="w",
                )
                details_label.pack(anchor="w")
        else:
            no_engineers_label = ctk.CTkLabel(
                details_container,
                text="No engineers assigned",
                font=("Segoe UI", 10),
                text_color=("gray50", "gray70"),
            )
            no_engineers_label.pack(pady=12)

        # Action buttons
        buttons_frame = ctk.CTkFrame(details_container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(16, 0))

        edit_assignments_btn = ctk.CTkButton(
            buttons_frame,
            text="Edit Assignments",
            command=lambda: self._edit_assignments(work_data),
            height=36,
            font=("Segoe UI", 11),
            fg_color=("#3498db", "#2980b9"),
            hover_color=("#2980b9", "#21618c"),
        )
        edit_assignments_btn.pack(fill="x", pady=(0, 8))

        edit_info_btn = ctk.CTkButton(
            buttons_frame,
            text="Edit Work Info",
            command=lambda: self._edit_work_info(work_data),
            height=36,
            font=("Segoe UI", 11),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray35"),
        )
        edit_info_btn.pack(fill="x", pady=(0, 8))

        delete_btn = ctk.CTkButton(
            buttons_frame,
            text="Delete Work",
            command=lambda: self._delete_work(work_data),
            height=36,
            font=("Segoe UI", 11),
            fg_color=("#e74c3c", "#c0392b"),
            hover_color=("#c0392b", "#a93226"),
        )
        delete_btn.pack(fill="x")

    def _add_detail_row(self, parent, label_text: str, value_text: str, row: int):
        """Add a detail row to the info frame."""
        row_frame = ctk.CTkFrame(parent, fg_color="transparent")
        row_frame.pack(fill="x", padx=12, pady=6)

        label = ctk.CTkLabel(
            row_frame,
            text=label_text,
            font=("Segoe UI", 10, "bold"),
            anchor="w",
            text_color=("gray50", "gray70"),
            width=100,
        )
        label.pack(side="left")

        value = ctk.CTkLabel(
            row_frame, text=value_text, font=("Segoe UI", 10), anchor="w"
        )
        value.pack(side="left", fill="x", expand=True)

    def _show_work_actions(self, work_data: Dict):
        """Show actions menu for a work."""
        # For now, just select the work
        self._select_work(work_data)

    def _open_create_dialog(self):
        """Open the create work dialog."""
        dialog = WorkAssignmentDialog(
            self.parent,
            on_success=lambda result: self._on_work_created(result),
            notification_system=getattr(self.controller, "notification_system", None),
        )

    def _on_work_created(self, result: Dict):
        """Handle successful work creation."""
        # Reload works list
        self._load_works()

    def _edit_assignments(self, work_data: Dict):
        """Edit work assignments."""
        # Create a dialog for editing assignments
        EditAssignmentsDialog(
            self.parent,
            work_data=work_data,
            on_success=lambda: self._on_assignments_updated(
                work_data["work"]["work_id"]
            ),
            notification_system=getattr(self.controller, "notification_system", None),
        )

    def _on_assignments_updated(self, work_id: int):
        """Handle successful assignment update."""
        # Reload works and refresh details
        self._load_works()

        # Find and reselect the updated work
        for work_data in self.works_data:
            if work_data["work"]["work_id"] == work_id:
                self._select_work(work_data)
                break

    def _edit_work_info(self, work_data: Dict):
        """Edit work information."""
        EditWorkInfoDialog(
            self.parent,
            work_data=work_data,
            on_success=lambda: self._on_work_updated(work_data["work"]["work_id"]),
            notification_system=getattr(self.controller, "notification_system", None),
        )

    def _on_work_updated(self, work_id: int):
        """Handle successful work update."""
        self._load_works()

        for work_data in self.works_data:
            if work_data["work"]["work_id"] == work_id:
                self._select_work(work_data)
                break

    def _delete_work(self, work_data: Dict):
        """Delete a work."""
        work = work_data["work"]

        # Confirm deletion
        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete work '{work['work_name']}'?\n\n"
            f"This will also remove all engineer assignments.\n"
            f"This action cannot be undone.",
            icon="warning",
        )

        if not result:
            return

        try:
            with SessionLocal() as db:
                delete_work_and_assignments(db, work["work_id"])

                messagebox.showinfo(
                    "Success", f"Work '{work['work_name']}' deleted successfully."
                )

                if hasattr(self.controller, "notification_system"):
                    self.controller.notification_system.show_success(
                        f"Work deleted: {work['work_name']}"
                    )

                # Reload works and clear details
                self._load_works()
                self._show_empty_details()

        except Exception as e:
            logger.error(f"Error deleting work: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete work: {str(e)}")

    def _on_back(self):
        """Handle back button click."""
        if hasattr(self.controller, "show_admin_menu"):
            self.controller.show_admin_menu()


class EditAssignmentsDialog(ctk.CTkToplevel):
    """Dialog for editing work assignments."""

    def __init__(
        self, parent, work_data: Dict, on_success=None, notification_system=None
    ):
        super().__init__(parent)

        self.work_data = work_data
        self.on_success = on_success
        self.notification_system = notification_system
        self.engineers: List[Dict] = []
        self.engineer_vars: Dict[int, ctk.BooleanVar] = {}

        # Dialog configuration
        self.title("Edit Work Assignments")
        self.geometry("500x600")
        self.resizable(False, False)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (250)
        y = (self.winfo_screenheight() // 2) - (300)
        self.geometry(f"500x600+{x}+{y}")

        # Build UI
        self._build_ui()
        self._load_engineers()

    def _build_ui(self):
        """Build dialog UI."""
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Header
        work_name = self.work_data["work"]["work_name"]
        header_label = ctk.CTkLabel(
            main_frame,
            text=f"Edit Assignments\n{work_name}",
            font=("Segoe UI", 16, "bold"),
        )
        header_label.pack(pady=(0, 16))

        # Engineers list
        engineers_label = ctk.CTkLabel(
            main_frame,
            text="Select Engineers:",
            font=("Segoe UI", 12, "bold"),
            anchor="w",
        )
        engineers_label.pack(fill="x", pady=(0, 8))

        self.engineers_frame = ctk.CTkScrollableFrame(
            main_frame, fg_color=("white", "gray25"), height=400
        )
        self.engineers_frame.pack(fill="both", expand=True, pady=(0, 16))

        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=120,
            height=36,
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray35"),
        )
        cancel_btn.pack(side="left", padx=(0, 8))

        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self._save_changes,
            width=140,
            height=36,
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954"),
        )
        self.save_btn.pack(side="right")

    def _load_engineers(self):
        """Load engineers and populate checkboxes."""
        try:
            with SessionLocal() as db:
                self.engineers = get_all_engineers(db)
                currently_assigned = {
                    eng["user_id"] for eng in self.work_data["assigned_engineers"]
                }

                for engineer in self.engineers:
                    eng_id = engineer["user_id"]

                    eng_frame = ctk.CTkFrame(
                        self.engineers_frame, fg_color="transparent"
                    )
                    eng_frame.pack(fill="x", pady=4, padx=8)

                    var = ctk.BooleanVar(value=(eng_id in currently_assigned))
                    self.engineer_vars[eng_id] = var

                    checkbox = ctk.CTkCheckBox(
                        eng_frame,
                        text=f"{engineer['full_name']} ({engineer['username']})",
                        variable=var,
                        font=("Segoe UI", 11),
                    )
                    checkbox.pack(anchor="w")

        except Exception as e:
            logger.error(f"Error loading engineers: {str(e)}")
            messagebox.showerror("Error", f"Failed to load engineers: {str(e)}")

    def _save_changes(self):
        """Save assignment changes."""
        work_id = self.work_data["work"]["work_id"]

        # Get current and new selections
        currently_assigned = {
            eng["user_id"] for eng in self.work_data["assigned_engineers"]
        }
        newly_selected = {
            user_id for user_id, var in self.engineer_vars.items() if var.get()
        }

        # Calculate changes
        to_add = list(newly_selected - currently_assigned)
        to_remove = list(currently_assigned - newly_selected)

        if not to_add and not to_remove:
            messagebox.showinfo("No Changes", "No changes to save.")
            return

        self.save_btn.configure(state="disabled", text="Saving...")
        self.update()

        try:
            with SessionLocal() as db:
                update_work_assignments(db, work_id, to_add, to_remove)

                messagebox.showinfo(
                    "Success",
                    f"Assignments updated!\nAdded: {len(to_add)}, Removed: {len(to_remove)}",
                )

                if self.on_success:
                    self.on_success()

                self.destroy()

        except Exception as e:
            logger.error(f"Error updating assignments: {str(e)}")
            messagebox.showerror("Error", f"Failed to update assignments: {str(e)}")
        finally:
            self.save_btn.configure(state="normal", text="Save Changes")


class EditWorkInfoDialog(ctk.CTkToplevel):
    """Dialog for editing work information."""

    def __init__(
        self, parent, work_data: Dict, on_success=None, notification_system=None
    ):
        super().__init__(parent)

        self.work_data = work_data
        self.on_success = on_success
        self.notification_system = notification_system

        # Dialog configuration
        self.title("Edit Work Information")
        self.geometry("550x500")
        self.minsize(500, 450)
        self.resizable(True, True)

        # Make modal
        self.transient(parent)
        self.grab_set()

        # Center dialog
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (275)
        y = (self.winfo_screenheight() // 2) - (250)
        self.geometry(f"550x500+{x}+{y}")

        # Build UI
        self._build_ui()

        # Keyboard bindings
        self.bind("<Return>", lambda e: self._save_changes())
        self.bind("<Escape>", lambda e: self.destroy())

        # Focus on work name entry
        self.name_entry.focus()

    def _build_ui(self):
        """Build dialog UI."""
        # Main container with padding
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=24, pady=20)

        work = self.work_data["work"]

        # Header
        header_label = ctk.CTkLabel(
            main_frame, text="Edit Work Information", font=("Segoe UI", 18, "bold")
        )
        header_label.pack(pady=(0, 20))

        # Work Information Section
        work_section = ctk.CTkFrame(main_frame, fg_color=("gray90", "gray20"))
        work_section.pack(fill="both", expand=True, pady=(0, 20))

        # Work Name
        work_name_label = ctk.CTkLabel(
            work_section, text="Work Name *", font=("Segoe UI", 12, "bold"), anchor="w"
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
            work_section, font=("Segoe UI", 11), height=100, wrap="word"
        )
        self.desc_text.pack(fill="x", padx=16, pady=(0, 12))
        self.desc_text.bind("<Return>", lambda e: None)  # Allow Enter in textbox
        if work["description"]:
            self.desc_text.insert("1.0", work["description"])

        # Status
        status_label = ctk.CTkLabel(
            work_section, text="Status", font=("Segoe UI", 12, "bold"), anchor="w"
        )
        status_label.pack(fill="x", padx=16, pady=(0, 4))

        self.status_var = ctk.StringVar(value=work["status"])
        status_menu = ctk.CTkOptionMenu(
            work_section,
            values=["In progress", "Completed"],
            variable=self.status_var,
            height=36,
            font=("Segoe UI", 11),
        )
        status_menu.pack(fill="x", padx=16, pady=(0, 16))

        # Action buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 0))

        cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self.destroy,
            width=140,
            height=40,
            font=("Segoe UI", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray35"),
        )
        cancel_btn.pack(side="left", pady=5)

        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self._save_changes,
            width=180,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954"),
        )
        self.save_btn.pack(side="right", pady=5)

    def _save_changes(self):
        """Save work information changes."""
        work_id = self.work_data["work"]["work_id"]
        new_name = self.name_entry.get().strip()
        new_desc = self.desc_text.get("1.0", "end-1c").strip()
        new_status = self.status_var.get()

        if not new_name:
            messagebox.showerror("Validation Error", "Work name cannot be empty.")
            return

        self.save_btn.configure(state="disabled", text="Saving...")
        self.update()

        try:
            with SessionLocal() as db:
                update_work_info(
                    db,
                    work_id,
                    work_name=new_name,
                    description=new_desc if new_desc else None,
                    status=new_status,
                )

                messagebox.showinfo("Success", "Work information updated successfully!")

                if self.on_success:
                    self.on_success()

                self.destroy()

        except ValidationError as e:
            messagebox.showerror("Validation Error", str(e))
        except Exception as e:
            logger.error(f"Error updating work: {str(e)}")
            messagebox.showerror("Error", f"Failed to update work: {str(e)}")
        finally:
            self.save_btn.configure(state="normal", text="Save Changes")