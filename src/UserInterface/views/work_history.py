"""Work History view for AutoRBI application (CustomTkinter)."""

from typing import List, Dict, Any, Optional
import customtkinter as ctk


class WorkHistoryView:
    """Handles the Work History Menu interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.history_rows: List[Dict[str, Any]] = []
        self.table_body: Optional[ctk.CTkScrollableFrame] = None
        self.current_filter: str = "all"

    def load_history(self, history_items: List[Dict[str, Any]]) -> None:
        """Populate the work history table.
        
        Each item dict can contain keys like:
        {"id": str, "file_name": str, "created_at": str, "status": str, "files_count": int}
        """
        self.history_rows = history_items
        if self.table_body is not None:
            # Clear current rows
            for child in self.table_body.winfo_children():
                child.destroy()
            # Rebuild
            filtered = self._filter_items(history_items)
            if filtered:
                for idx, item in enumerate(filtered, start=1):
                    self._add_history_row(idx, item)
            else:
                # Show hint if no data
                hint_label = ctk.CTkLabel(
                    self.table_body,
                    text="No work history found for the selected filter.",
                    font=("Segoe UI", 11),
                    text_color=("gray40", "gray75"),
                    justify="left",
                )
                hint_label.grid(row=0, column=0, columnspan=6, sticky="w", pady=(8, 8))

    def _filter_items(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Filter items based on current filter selection."""
        if self.current_filter == "all":
            return items
        # TODO: Implement date-based filtering when backend provides date data
        return items

    def _apply_filter(self, period: str) -> None:
        """Apply time period filter (button-based, no input fields)."""
        self.current_filter = period
        if self.table_body is not None:
            for child in self.table_body.winfo_children():
                child.destroy()
            filtered = self._filter_items(self.history_rows)
            for idx, item in enumerate(filtered, start=1):
                self._add_history_row(idx, item)

    def _view_details(self, item: Dict[str, Any]) -> None:
        """Open details view for a work history item."""
        # TODO: delegate to controller/backend
        pass

    def _export_work(self, item: Dict[str, Any]) -> None:
        """Export work item to Excel/PDF."""
        # TODO: delegate to controller/backend
        pass

    def _delete_work(self, item: Dict[str, Any]) -> None:
        """Delete/archive a work history item."""
        # TODO: delegate to controller/backend
        pass

    def _add_history_row(self, index: int, item: Dict[str, Any]) -> None:
        """Add a row to the history table."""
        if self.table_body is None:
            return

        file_name = item.get("file_name", f"Work {index}")
        created_at = item.get("created_at", "-")
        status = item.get("status", "Completed")
        files_count = item.get("files_count", 0)

        # Table row frame
        row_frame = ctk.CTkFrame(
            self.table_body,
            corner_radius=4,
            border_width=1,
            border_color=("gray80", "gray30"),
            height=50,
        )
        row_frame.grid(row=index, column=0, columnspan=6, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(0, weight=0, minsize=50)   # No.
        row_frame.grid_columnconfigure(1, weight=2)                # File Name
        row_frame.grid_columnconfigure(2, weight=1)                # Date
        row_frame.grid_columnconfigure(3, weight=1)                # Status
        row_frame.grid_columnconfigure(4, weight=1)                # Files Count
        row_frame.grid_columnconfigure(5, weight=1)                # Actions

        # Column 0: No.
        no_label = ctk.CTkLabel(
            row_frame,
            text=str(index),
            font=("Segoe UI", 11),
            anchor="center",
        )
        no_label.grid(row=0, column=0, sticky="ew", padx=12, pady=12)

        # Column 1: File Name
        name_label = ctk.CTkLabel(
            row_frame,
            text=file_name,
            font=("Segoe UI", 11),
            anchor="w",
        )
        name_label.grid(row=0, column=1, sticky="ew", padx=12, pady=12)

        # Column 2: Date
        date_label = ctk.CTkLabel(
            row_frame,
            text=created_at,
            font=("Segoe UI", 10),
            text_color=("gray60", "gray80"),
            anchor="w",
        )
        date_label.grid(row=0, column=2, sticky="ew", padx=12, pady=12)

        # Column 3: Status badge
        status_colors = {
            "Completed": ("#2ecc71", "#27ae60"),
            "In Progress": ("#f39c12", "#e67e22"),
            "Failed": ("#e74c3c", "#c0392b"),
        }
        status_color = status_colors.get(status, ("gray70", "gray60"))
        status_badge = ctk.CTkLabel(
            row_frame,
            text=status,
            font=("Segoe UI", 9, "bold"),
            fg_color=status_color,
            corner_radius=4,
            width=90,
            height=24,
        )
        status_badge.grid(row=0, column=3, sticky="w", padx=12, pady=12)

        # Column 4: Files Count
        files_label = ctk.CTkLabel(
            row_frame,
            text=str(files_count),
            font=("Segoe UI", 10),
            anchor="center",
        )
        files_label.grid(row=0, column=4, sticky="ew", padx=12, pady=12)

        # Column 5: Actions
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=5, sticky="e", padx=12, pady=8)

        view_btn = ctk.CTkButton(
            actions_frame,
            text="View",
            width=60,
            height=28,
            font=("Segoe UI", 9),
            command=lambda i=item: self._view_details(i),
        )
        view_btn.pack(side="left", padx=(0, 4))

        export_btn = ctk.CTkButton(
            actions_frame,
            text="Export",
            width=60,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            command=lambda i=item: self._export_work(i),
        )
        export_btn.pack(side="left", padx=(0, 4))

        delete_btn = ctk.CTkButton(
            actions_frame,
            text="Delete",
            width=60,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            hover_color=("red", "darkred"),
            command=lambda i=item: self._delete_work(i),
        )
        delete_btn.pack(side="left")

    def show(self) -> None:
        """Display the Work History Menu interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with back button
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back to Main Menu",
            command=self.controller.show_main_menu,
            width=180,
            height=32,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        back_btn.grid(row=0, column=0, sticky="w")

        title_label = ctk.CTkLabel(
            header,
            text="AutoRBI",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.grid(row=0, column=1, sticky="e")

        # Main content area
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame.grid_rowconfigure(3, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="Work History",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Browse completed work sessions and manage your extraction history.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # Filter buttons (no input fields)
        filter_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        filter_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))

        filter_label = ctk.CTkLabel(
            filter_section,
            text="Time period:",
            font=("Segoe UI", 10, "bold"),
        )
        filter_label.pack(side="left", padx=(0, 8))

        filter_buttons = ["All", "Today", "Last 7 days", "Last month"]
        for period in filter_buttons:
            period_key = period.lower().replace(" ", "_")
            btn = ctk.CTkButton(
                filter_section,
                text=period,
                width=100,
                height=28,
                font=("Segoe UI", 9),
                fg_color=("gray20", "gray30") if self.current_filter != period_key else None,
                command=lambda p=period_key: self._apply_filter(p),
            )
            btn.pack(side="left", padx=(0, 6))

        # Table container
        table_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_container.grid(row=3, column=0, sticky="nsew", padx=24, pady=(0, 24))
        table_container.grid_rowconfigure(1, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

        # Table header
        header_row = ctk.CTkFrame(
            table_container,
            corner_radius=8,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("gray90", "gray20"),
        )
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        header_row.grid_columnconfigure(0, weight=0, minsize=50)   # No.
        header_row.grid_columnconfigure(1, weight=2)                # File Name
        header_row.grid_columnconfigure(2, weight=1)                # Date
        header_row.grid_columnconfigure(3, weight=1)                # Status
        header_row.grid_columnconfigure(4, weight=1)               # Files Count
        header_row.grid_columnconfigure(5, weight=1)               # Actions

        headers = ["No.", "File Name", "Date", "Status", "Files", "Actions"]
        for col, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_row,
                text=header_text,
                font=("Segoe UI", 11, "bold"),
                anchor="w" if col < 5 else "center",
            )
            header_label.grid(row=0, column=col, sticky="ew", padx=12, pady=10)

        # Scrollable history table body
        self.table_body = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.table_body.grid(row=1, column=0, sticky="nsew")
        self.table_body.grid_columnconfigure(0, weight=0, minsize=50)   # No.
        self.table_body.grid_columnconfigure(1, weight=2)                # File Name
        self.table_body.grid_columnconfigure(2, weight=1)                # Date
        self.table_body.grid_columnconfigure(3, weight=1)                # Status
        self.table_body.grid_columnconfigure(4, weight=1)                # Files Count
        self.table_body.grid_columnconfigure(5, weight=1)                # Actions

        # Initially show hint
        hint_label = ctk.CTkLabel(
            self.table_body,
            text="No work history loaded yet. Completed extractions will appear here.",
            font=("Segoe UI", 11),
            text_color=("gray40", "gray75"),
            justify="left",
        )
        hint_label.grid(row=0, column=0, columnspan=6, sticky="w", pady=(8, 8))
