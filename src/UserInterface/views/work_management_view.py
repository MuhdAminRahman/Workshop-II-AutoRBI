"""
Work Management View
View for managing works and engineer assignments (Admin only).
Refactored version with proper architecture and bug fixes.
"""

import customtkinter as ctk
from typing import Optional, List, Dict
from tkinter import messagebox
from datetime import datetime

from AutoRBI_Database.logging_config import get_logger
from UserInterface.views.work_assignment_dialog import WorkAssignmentDialog
from UserInterface.views.edit_assignments_dialog import EditAssignmentsDialog
from UserInterface.views.edit_work_info_dialog import EditWorkInfoDialog
from UserInterface.views.constants import (
    WORK_TABLE_COLUMNS,
    WORK_STATUS_FILTER_MAP,
    WORK_ROW_HEIGHT,
    WORK_NAME_MAX_LENGTH,
    WORK_NAME_TRUNCATE_LENGTH,
    WORKS_PER_PAGE,
)
from UserInterface.components.tooltip import ConditionalTooltip

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
        self.filtered_works: List[Dict] = []
        self.selected_work: Optional[Dict] = None
        self.search_var = ctk.StringVar()
        self.filter_var = ctk.StringVar(value="All")
        
        # Pagination state
        self.current_page = 1
        self.total_pages = 1
        self.total_works = 0

        # UI component references
        self.works_container: Optional[ctk.CTkScrollableFrame] = None
        self.details_panel: Optional[ctk.CTkFrame] = None
        self.pagination_frame: Optional[ctk.CTkFrame] = None
        
        # State flags
        self._is_loading = False
        self._view_active = False
        self._search_timer = None
        self._work_id_to_reselect = None  # Store work ID to reselect after reload

    def _safe_show_notification(self, message: str, notification_type: str = "info") -> None:
        """
        Safely show notification with widget existence checks.
        
        Args:
            message: Notification message
            notification_type: Type of notification (info, success, error, warning)
        """
        if not self._view_active:
            return
            
        try:
            if not hasattr(self.controller, "notification_system"):
                return
            
            notif_system = self.controller.notification_system
            
            if not hasattr(notif_system, "notification_container"):
                notif_system.show_notification(message, notification_type)
                return
                
            if notif_system.notification_container and not notif_system.notification_container.winfo_exists():
                logger.debug("Notification container destroyed, skipping notification")
                return
            
            notif_system.show_notification(message, notification_type)
            
        except Exception as e:
            logger.debug(f"Could not show notification: {str(e)}")

    def show(self) -> None:
        """Display the work management view."""
        self._view_active = True
        
        # Clear existing widgets and references
        self._cleanup_widgets()
        
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Root content frame
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(2, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Build sections
        self._build_header(root_frame)
        self._build_toolbar(root_frame)
        
        # Content section (works list and details)
        content_frame = ctk.CTkFrame(root_frame, fg_color="transparent")
        content_frame.grid(row=2, column=0, sticky="nsew", pady=(12, 0))
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=1)

        self._build_works_list(content_frame)
        self._build_details_panel(content_frame)

        # Load works data
        self._load_works()

    def _cleanup_widgets(self) -> None:
        """Clean up widget references to prevent memory leaks."""
        self.works_container = None
        self.details_panel = None
        self.pagination_frame = None
        self.selected_work = None
        
        # Cancel any pending search timer
        if self._search_timer:
            try:
                self.parent.after_cancel(self._search_timer)
            except Exception:
                pass
            self._search_timer = None

    def _build_header(self, parent) -> None:
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

    def _build_toolbar(self, parent) -> None:
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
            placeholder_text="Search works by name or description...",
            font=("Segoe UI", 11),
            height=36,
            textvariable=self.search_var,
        )
        search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        self.search_var.trace_add("write", lambda *args: self._on_search_changed())

        # Status filter - using display values
        filter_menu = ctk.CTkOptionMenu(
            inner_frame,
            values=list(WORK_STATUS_FILTER_MAP.keys()),
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

    def _build_works_list(self, parent) -> None:
        """Build the works list section."""
        list_frame = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        list_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        list_frame.grid_rowconfigure(2, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)

        # Header
        list_header = ctk.CTkLabel(
            list_frame, text="Works List", font=("Segoe UI", 14, "bold"), anchor="w"
        )
        list_header.pack(fill="x", padx=16, pady=(16, 8))

        # Column headers
        headers_frame = ctk.CTkFrame(list_frame, fg_color="transparent", height=30)
        headers_frame.pack(fill="x", padx=16, pady=(0, 8))
        headers_frame.pack_propagate(False)

        x_position = 0
        for col_key, col_info in WORK_TABLE_COLUMNS.items():
            header_label = ctk.CTkLabel(
                headers_frame,
                text=col_info["header"],
                font=("Segoe UI", 10, "bold"),
                text_color=("gray50", "gray70"),
                anchor="w",
            )
            header_label.place(relx=x_position, rely=0.5, anchor="w", relwidth=col_info["width"])
            x_position += col_info["width"]

        # Scrollable works container
        self.works_container = ctk.CTkScrollableFrame(
            list_frame, fg_color=("white", "gray25")
        )
        self.works_container.pack(fill="both", expand=True, padx=16, pady=(0, 8))
        
        # Pagination frame
        self.pagination_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        self.pagination_frame.pack(fill="x", padx=16, pady=(0, 16))

    def _build_details_panel(self, parent) -> None:
        """Build the details panel section."""
        self.details_panel = ctk.CTkFrame(parent, fg_color=("gray90", "gray20"))
        self.details_panel.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        self._show_empty_details()

    def _show_empty_details(self) -> None:
        """Show empty state in details panel."""
        if not self.details_panel:
            return
            
        for widget in self.details_panel.winfo_children():
            widget.destroy()

        empty_label = ctk.CTkLabel(
            self.details_panel,
            text="Select a work to view details",
            font=("Segoe UI", 12),
            text_color=("gray50", "gray70"),
        )
        empty_label.pack(expand=True)

    def _load_works(self) -> None:
        """Load all works from database via controller."""
        if self._is_loading:
            return

        self._is_loading = True

        # Show loading state
        if hasattr(self.controller, 'loading_overlay'):
            self.controller.loading_overlay.show("Loading works...")

        try:
            # Get current search and filter values
            search_text = self.search_var.get().strip() or None
            status_filter_display = self.filter_var.get()
            status_filter_db = WORK_STATUS_FILTER_MAP.get(status_filter_display)

            # Use controller method with filters
            result = self.controller.get_all_works_with_assignments(
                page=self.current_page,
                per_page=WORKS_PER_PAGE,
                search_text=search_text,
                status_filter=status_filter_db
            )

            if result.get("success"):
                self.works_data = result.get("data", [])
                pagination = result.get("pagination", {})
                self.total_pages = pagination.get("total_pages", 1)
                self.total_works = pagination.get("total", 0)

                # No need to filter again - data is already filtered by controller
                self.filtered_works = self.works_data
                self._display_works()
                self._update_pagination()

                # Reselect work if needed (after update/assignment change)
                if self._work_id_to_reselect:
                    self._reselect_work_by_id(self._work_id_to_reselect)
                    self._work_id_to_reselect = None

                # Schedule notification
                if self._view_active:
                    self.parent.after(100, lambda:
                        self._safe_show_notification(f"Loaded {self.total_works} work(s)")
                    )
            else:
                self._safe_show_notification(
                    result.get("message", "Failed to load works"),
                    "error"
                )

        except Exception as e:
            logger.error(f"Error loading works: {str(e)}")
            messagebox.showerror("Error", f"Failed to load works: {str(e)}")
        finally:
            self._is_loading = False
            if hasattr(self.controller, 'loading_overlay'):
                self.controller.loading_overlay.hide()

    def _on_search_changed(self) -> None:
        """Handle search text changes with debouncing."""
        # Cancel previous timer
        if self._search_timer:
            try:
                self.parent.after_cancel(self._search_timer)
            except Exception:
                pass
        
        # Schedule new filter
        self._search_timer = self.parent.after(300, self._filter_works)

    def _filter_works(self) -> None:
        """
        Trigger work reload with current filters.
        Resets to page 1 and reloads data from controller with search/filter applied.
        """
        if not self.works_container or not self.works_container.winfo_exists():
            return

        # Reset to page 1 when search or filter changes
        self.current_page = 1

        # Reload works with current search/filter parameters
        self._load_works()

    def _display_works(self) -> None:
        """Display works in the list."""
        if not self.works_container or not self.works_container.winfo_exists():
            return
            
        # Clear existing widgets
        for widget in self.works_container.winfo_children():
            widget.destroy()

        if not self.filtered_works:
            self._show_empty_works_state()
            return

        for work_data in self.filtered_works:
            self._create_work_row(work_data)

    def _show_empty_works_state(self) -> None:
        """Show empty state when no works found."""
        empty_frame = ctk.CTkFrame(self.works_container, fg_color="transparent")
        empty_frame.pack(expand=True, fill="both", pady=40)
        
        no_works_label = ctk.CTkLabel(
            empty_frame,
            text="No works found",
            font=("Segoe UI", 14),
            text_color=("gray50", "gray70"),
        )
        no_works_label.pack(pady=(0, 12))
        
        # Add helpful action if no works at all
        if not self.works_data:
            create_hint = ctk.CTkLabel(
                empty_frame,
                text="Click '+ Create New Work' to get started",
                font=("Segoe UI", 11),
                text_color=("gray60", "gray60"),
            )
            create_hint.pack()

    def _create_work_row(self, work_data: Dict) -> None:
        """Create a work row in the list."""
        work = work_data["work"]
        assigned_engineers = work_data["assigned_engineers"]

        # Row frame
        row_frame = ctk.CTkFrame(
            self.works_container, 
            fg_color=("gray95", "gray30"), 
            height=WORK_ROW_HEIGHT
        )
        row_frame.pack(fill="x", pady=4, padx=4)
        row_frame.pack_propagate(False)

        # Make row clickable
        row_frame.bind("<Button-1>", lambda e, wd=work_data: self._select_work(wd))

        # Work name with truncation and tooltip
        full_work_name = work["work_name"]
        display_name = full_work_name
        if len(full_work_name) > WORK_NAME_MAX_LENGTH:
            display_name = full_work_name[:WORK_NAME_TRUNCATE_LENGTH] + "..."

        name_label = ctk.CTkLabel(
            row_frame, 
            text=display_name, 
            font=("Segoe UI", 11, "bold"), 
            anchor="w"
        )
        name_label.place(
            relx=0, 
            rely=0.5, 
            anchor="w", 
            relwidth=WORK_TABLE_COLUMNS["work_name"]["width"], 
            x=12
        )
        name_label.bind("<Button-1>", lambda e, wd=work_data: self._select_work(wd))
        
        # Add tooltip for truncated names
        ConditionalTooltip(name_label, full_work_name, display_name)

        # Status badge
        status_color = "#2ecc71" if work["status"] == "Completed" else "#3498db"
        status_frame = ctk.CTkFrame(
            row_frame, 
            fg_color=status_color, 
            corner_radius=12,
            height=24,
        )
        status_frame.place(
            relx=WORK_TABLE_COLUMNS["work_name"]["width"], 
            rely=0.5, 
            anchor="w", 
            relwidth=WORK_TABLE_COLUMNS["status"]["width"] - 0.02
        )

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
        eng_x = WORK_TABLE_COLUMNS["work_name"]["width"] + WORK_TABLE_COLUMNS["status"]["width"]
        eng_label = ctk.CTkLabel(
            row_frame, 
            text=eng_text, 
            font=("Segoe UI", 10), 
            anchor="w"
        )
        eng_label.place(
            relx=eng_x, 
            rely=0.5, 
            anchor="w", 
            relwidth=WORK_TABLE_COLUMNS["engineers"]["width"]
        )
        eng_label.bind("<Button-1>", lambda e, wd=work_data: self._select_work(wd))

        # Created date with null check
        created_at = work.get("created_at")
        if created_at and isinstance(created_at, datetime):
            created_date = created_at.strftime("%Y-%m-%d")
        else:
            created_date = "N/A"
            
        date_x = eng_x + WORK_TABLE_COLUMNS["engineers"]["width"]
        date_label = ctk.CTkLabel(
            row_frame, 
            text=created_date, 
            font=("Segoe UI", 10), 
            anchor="w"
        )
        date_label.place(
            relx=date_x, 
            rely=0.5, 
            anchor="w", 
            relwidth=WORK_TABLE_COLUMNS["created"]["width"]
        )
        date_label.bind("<Button-1>", lambda e, wd=work_data: self._select_work(wd))

        # Actions button
        actions_x = date_x + WORK_TABLE_COLUMNS["created"]["width"]
        actions_btn = ctk.CTkButton(
            row_frame,
            text="...",
            command=lambda wd=work_data: self._show_work_actions_menu(wd),
            width=30,
            height=30,
            font=("Segoe UI", 14, "bold"),
            fg_color="transparent",
            hover_color=("gray85", "gray35"),
        )
        actions_btn.place(relx=actions_x, rely=0.5, anchor="w")

    def _update_pagination(self) -> None:
        """Update pagination controls."""
        if not self.pagination_frame:
            return
            
        # Clear existing pagination
        for widget in self.pagination_frame.winfo_children():
            widget.destroy()
        
        if self.total_pages <= 1:
            return
        
        # Page info
        page_info = ctk.CTkLabel(
            self.pagination_frame,
            text=f"Page {self.current_page} of {self.total_pages}",
            font=("Segoe UI", 10),
        )
        page_info.pack(side="left")
        
        # Navigation buttons frame
        nav_frame = ctk.CTkFrame(self.pagination_frame, fg_color="transparent")
        nav_frame.pack(side="right")
        
        # Previous button
        prev_btn = ctk.CTkButton(
            nav_frame,
            text="< Prev",
            command=lambda: self._change_page(self.current_page - 1),
            width=70,
            height=28,
            font=("Segoe UI", 10),
            state="normal" if self.current_page > 1 else "disabled",
        )
        prev_btn.pack(side="left", padx=(0, 8))
        
        # Next button
        next_btn = ctk.CTkButton(
            nav_frame,
            text="Next >",
            command=lambda: self._change_page(self.current_page + 1),
            width=70,
            height=28,
            font=("Segoe UI", 10),
            state="normal" if self.current_page < self.total_pages else "disabled",
        )
        next_btn.pack(side="left")

    def _change_page(self, page: int) -> None:
        """Change to a different page."""
        if page < 1 or page > self.total_pages:
            return
        self.current_page = page
        self._load_works()

    def _select_work(self, work_data: Dict) -> None:
        """Select a work and show its details."""
        self.selected_work = work_data
        self._show_work_details(work_data)

    def _reselect_work_by_id(self, work_id: int) -> None:
        """Reselect a work by its ID after data reload."""
        for work_data in self.works_data:
            if work_data["work"]["work_id"] == work_id:
                self._select_work(work_data)
                return
        # If not found in current page, clear selection
        logger.debug(f"Work {work_id} not found in current page after reload")

    def _show_work_details(self, work_data: Dict) -> None:
        """Show work details in the details panel."""
        if not self.details_panel:
            return
            
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

        # Work information frame
        info_frame = ctk.CTkFrame(details_container, fg_color=("white", "gray25"))
        info_frame.pack(fill="x", pady=(0, 12))

        # Work name
        self._add_detail_row(info_frame, "Work Name:", work["work_name"])

        # Status
        self._add_detail_row(info_frame, "Status:", work["status"])

        # Created date with null check
        created_at = work.get("created_at")
        if created_at and isinstance(created_at, datetime):
            created_text = created_at.strftime("%Y-%m-%d %H:%M")
        else:
            created_text = "N/A"
        self._add_detail_row(info_frame, "Created:", created_text)

        # Description
        if work.get("description"):
            desc_label = ctk.CTkLabel(
                info_frame,
                text="Description:",
                font=("Segoe UI", 10, "bold"),
                anchor="w",
                text_color=("gray50", "gray70"),
            )
            desc_label.pack(fill="x", padx=12, pady=(12, 4))

            desc_text = ctk.CTkTextbox(
                info_frame, 
                height=80, 
                font=("Segoe UI", 10), 
                wrap="word"
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

                icon_label = ctk.CTkLabel(eng_row, text="@", font=("Segoe UI", 16))
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

                details_text = f"{engineer['username']} - {engineer.get('email', 'N/A')}"
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
        self._build_detail_action_buttons(details_container, work_data)

    def _add_detail_row(self, parent, label_text: str, value_text: str) -> None:
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
            row_frame, 
            text=value_text, 
            font=("Segoe UI", 10), 
            anchor="w"
        )
        value.pack(side="left", fill="x", expand=True)

    def _build_detail_action_buttons(self, parent, work_data: Dict) -> None:
        """Build action buttons for work details."""
        buttons_frame = ctk.CTkFrame(parent, fg_color="transparent")
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

    def _show_work_actions_menu(self, work_data: Dict) -> None:
        """Show context menu for work actions."""
        # For now, select the work to show details with action buttons
        self._select_work(work_data)

    def _open_create_dialog(self) -> None:
        """Open the create work dialog."""
        WorkAssignmentDialog(
            self.parent,
            on_success=lambda result: self._on_work_created(result),
            notification_system=getattr(self.controller, "notification_system", None),
        )

    def _on_work_created(self, result: Dict) -> None:
        """Handle successful work creation."""
        self._load_works()

    def _edit_assignments(self, work_data: Dict) -> None:
        """Edit work assignments."""
        EditAssignmentsDialog(
            self.parent,
            work_data=work_data,
            on_success=lambda: self._on_assignments_updated(work_data["work"]["work_id"]),
            notification_system=getattr(self.controller, "notification_system", None),
            controller=self.controller,
        )

    def _on_assignments_updated(self, work_id: int) -> None:
        """Handle successful assignment update."""
        # Store work_id to reselect after reload
        self._work_id_to_reselect = work_id
        self._load_works()

    def _edit_work_info(self, work_data: Dict) -> None:
        """Edit work information."""
        EditWorkInfoDialog(
            self.parent,
            work_data=work_data,
            on_success=lambda: self._on_work_updated(work_data["work"]["work_id"]),
            notification_system=getattr(self.controller, "notification_system", None),
            controller=self.controller,
        )

    def _on_work_updated(self, work_id: int) -> None:
        """Handle successful work update."""
        # Store work_id to reselect after reload
        self._work_id_to_reselect = work_id
        self._load_works()

    def _delete_work(self, work_data: Dict) -> None:
        """Delete a work with confirmation."""
        work = work_data["work"]

        result = messagebox.askyesno(
            "Confirm Delete",
            f"Are you sure you want to delete work '{work['work_name']}'?\n\n"
            f"This will permanently delete:\n"
            f"• All engineer assignments\n"
            f"• All equipment and component records\n"
            f"• All work history logs\n"
            f"• All correction logs\n"
            f"• Associated Excel and PowerPoint files\n\n"
            f"This action cannot be undone!",
            icon="warning",
        )

        if not result:
            return

        # Show loading
        if hasattr(self.controller, 'loading_overlay'):
            self.controller.loading_overlay.show("Deleting work...")

        try:
            # Use controller method
            delete_result = self.controller.delete_work(work["work_id"])
            
            if delete_result.get("success"):
                self._safe_show_notification(
                    f"Work deleted: {work['work_name']}", 
                    "success"
                )
                self._load_works()
                self._show_empty_details()
            else:
                self._safe_show_notification(
                    delete_result.get("message", "Failed to delete work"),
                    "error"
                )

        except Exception as e:
            logger.error(f"Error deleting work: {str(e)}")
            messagebox.showerror("Error", f"Failed to delete work: {str(e)}")
        finally:
            if hasattr(self.controller, 'loading_overlay'):
                self.controller.loading_overlay.hide()

    def _on_back(self) -> None:
        """Handle back button click."""
        self._view_active = False
        if hasattr(self.controller, "show_admin_menu"):
            self.controller.show_admin_menu()