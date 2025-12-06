"""Report Menu view for AutoRBI application (CustomTkinter)."""

from typing import List, Dict, Any, Optional

import customtkinter as ctk


class ReportMenuView:
    """Handles the Report Menu interface (view/export generated reports)."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.report_rows: List[Dict[str, Any]] = []
        self.table_body: Optional[ctk.CTkScrollableFrame] = None

    # Public helper that backend can call to populate the table
    def load_reports(self, reports: List[Dict[str, Any]]) -> None:
        """Populate the report list.

        Each report dict can contain keys like:
        {"name": str, "created_at": str, "excel_path": str, "id": any}
        """
        self.report_rows = reports
        if self.table_body is not None:
            # Clear current rows
            for child in self.table_body.winfo_children():
                child.destroy()
            # Rebuild
            if reports:
                for idx, report in enumerate(self.report_rows, start=1):
                    self._add_report_row(idx, report)
            else:
                # Show hint if no data
                hint_label = ctk.CTkLabel(
                    self.table_body,
                    text="No reports found. After running 'New Work', Excel files will appear here.",
                    font=("Segoe UI", 11),
                    text_color=("gray40", "gray75"),
                    justify="left",
                )
                hint_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(8, 8))

    def _open_pdf_preview(self, report: Dict[str, Any]) -> None:
        """Open a popup for PDF preview with download option (backend wiring required)."""
        popup = ctk.CTkToplevel(self.parent)
        popup.title(f"PDF Preview - {report.get('name', '')}")
        popup.geometry("800x600")

        popup.grid_rowconfigure(1, weight=1)
        popup.grid_columnconfigure(0, weight=1)

        header = ctk.CTkLabel(
            popup,
            text=f"Preview: {report.get('name', 'Report')}",
            font=("Segoe UI", 16, "bold"),
        )
        header.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 4))

        preview_area = ctk.CTkLabel(
            popup,
            text="PDF preview will be rendered here by the backend (e.g., image pages or embedded viewer).",
            font=("Segoe UI", 11),
            justify="left",
            wraplength=740,
            text_color=("gray60", "gray80"),
        )
        preview_area.grid(row=1, column=0, sticky="nsew", padx=20, pady=(4, 12))

        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.grid(row=2, column=0, sticky="e", padx=20, pady=(0, 16))

        download_btn = ctk.CTkButton(
            btn_frame,
            text="Download PDF",
            command=lambda r=report: self._export_pdf(r),
        )
        download_btn.pack(side="left")

        close_btn = ctk.CTkButton(
            btn_frame,
            text="Close",
            command=popup.destroy,
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        close_btn.pack(side="left", padx=(8, 0))

    def _export_pdf(self, report: Dict[str, Any]) -> None:
        """Generate PDF for the given report (backend implementation needed)."""
        # TODO: delegate to controller/backend
        pass

    def _export_ppt(self, report: Dict[str, Any]) -> None:
        """Generate PowerPoint for the given report (backend implementation needed)."""
        # TODO: delegate to controller/backend
        pass

    def _export_excel(self, report: Dict[str, Any]) -> None:
        """Open/export the underlying Excel file (backend implementation needed)."""
        # TODO: delegate to controller/backend
        pass

    def _add_report_row(self, index: int, report: Dict[str, Any]) -> None:
        """Add a row to the report table."""
        if self.table_body is None:
            return

        name = report.get("name", f"Report {index}")
        created_at = report.get("created_at", "-")

        # Table row frame
        row_frame = ctk.CTkFrame(
            self.table_body,
            corner_radius=4,
            border_width=1,
            border_color=("gray80", "gray30"),
            height=50,
        )
        row_frame.grid(row=index, column=0, columnspan=4, sticky="ew", pady=2)
        row_frame.grid_columnconfigure(0, weight=0, minsize=50)   # No.
        row_frame.grid_columnconfigure(1, weight=2)                # File Name
        row_frame.grid_columnconfigure(2, weight=1)                # Date
        row_frame.grid_columnconfigure(3, weight=1)                # Actions

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
            text=name,
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

        # Column 3: Actions (PDF, Excel, PPT)
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=3, sticky="e", padx=12, pady=8)

        pdf_btn = ctk.CTkButton(
            actions_frame,
            text="PDF",
            width=60,
            height=28,
            font=("Segoe UI", 9),
            command=lambda r=report: self._open_pdf_preview(r),
        )
        pdf_btn.pack(side="left", padx=(0, 4))

        excel_btn = ctk.CTkButton(
            actions_frame,
            text="Excel",
            width=60,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            command=lambda r=report: self._export_excel(r),
        )
        excel_btn.pack(side="left", padx=(0, 4))

        ppt_btn = ctk.CTkButton(
            actions_frame,
            text="PPT",
            width=60,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            command=lambda r=report: self._export_ppt(r),
        )
        ppt_btn.pack(side="left")

    def show(self) -> None:
        """Display the Report Menu interface."""
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

        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="Report Menu",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="View generated Excel files, preview them and export as PDF or PowerPoint.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # Table container
        table_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        table_container.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
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
        header_row.grid_columnconfigure(3, weight=1)               # Actions

        headers = ["No.", "File Name", "Date", "Actions"]
        for col, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_row,
                text=header_text,
                font=("Segoe UI", 11, "bold"),
                anchor="w" if col < 3 else "center",
            )
            header_label.grid(row=0, column=col, sticky="ew", padx=12, pady=10)

        # Scrollable table body
        self.table_body = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.table_body.grid(row=1, column=0, sticky="nsew")
        self.table_body.grid_columnconfigure(0, weight=0, minsize=50)   # No.
        self.table_body.grid_columnconfigure(1, weight=2)                # File Name
        self.table_body.grid_columnconfigure(2, weight=1)                # Date
        self.table_body.grid_columnconfigure(3, weight=1)                # Actions

        # Initially show a hint until backend populates reports
        hint_label = ctk.CTkLabel(
            self.table_body,
            text="No reports loaded yet. After running 'New Work', Excel files will appear here.",
            font=("Segoe UI", 11),
            text_color=("gray40", "gray75"),
            justify="left",
        )
        hint_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(8, 8))
