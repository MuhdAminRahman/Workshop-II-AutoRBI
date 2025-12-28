"""Report Menu view for AutoRBI application (CustomTkinter)."""

import os
import subprocess
import platform
from typing import List, Dict, Any, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox


class ReportMenuView:
    """Handles the Report Menu interface (view/export generated reports)."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.report_rows: List[Dict[str, Any]] = []
        self.table_body: Optional[ctk.CTkScrollableFrame] = None
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )

    def _load_reports_from_filesystem(self) -> List[Dict[str, Any]]:
        """Load reports by scanning output_files directory structure."""
        reports = []
        output_files_dir = os.path.join(self.project_root, "src", "output_files")
        
        if not os.path.isdir(output_files_dir):
            return reports
        
        try:
            # Iterate through all work directories
            for work_name in os.listdir(output_files_dir):
                work_path = os.path.join(output_files_dir, work_name)
                
                if not os.path.isdir(work_path):
                    continue
                
                # Look for Excel files in {work}/excel/updated/
                excel_path = self._find_latest_file(
                    os.path.join(work_path, "excel", "updated"),
                    ['.xlsx', '.xls']
                )
                
                # Look for PowerPoint files in {work}/powerpoint/
                ppt_path = self._find_latest_file(
                    os.path.join(work_path, "powerpoint"),
                    ['.pptx']
                )
                
                # Only add if at least one file exists
                if excel_path or ppt_path:
                    # Get file modification time for sorting
                    latest_time = None
                    if excel_path and os.path.exists(excel_path):
                        latest_time = os.path.getmtime(excel_path)
                    if ppt_path and os.path.exists(ppt_path):
                        ppt_time = os.path.getmtime(ppt_path)
                        if latest_time is None or ppt_time > latest_time:
                            latest_time = ppt_time
                    
                    from datetime import datetime
                    created_at = datetime.fromtimestamp(latest_time).strftime('%Y-%m-%d %H:%M')
                    
                    reports.append({
                        'work_name': work_name,
                        'name': f"Work: {work_name}",
                        'created_at': created_at,
                        'excel_path': excel_path,
                        'ppt_path': ppt_path,
                        'excel_exists': os.path.exists(excel_path) if excel_path else False,
                        'ppt_exists': os.path.exists(ppt_path) if ppt_path else False,
                    })
        
        except Exception as e:
            print(f"Error loading reports from filesystem: {e}")
        
        # Sort by created_at descending (newest first)
        reports.sort(key=lambda x: x['created_at'], reverse=True)
        
        return reports

    def _find_latest_file(self, directory: str, extensions: List[str]) -> Optional[str]:
        """Find the most recent file with given extensions in a directory."""
        if not os.path.isdir(directory):
            return None
        
        try:
            matching_files = []
            
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                
                if os.path.isfile(file_path):
                    # Check if file has one of the target extensions
                    if any(filename.lower().endswith(ext) for ext in extensions):
                        matching_files.append(file_path)
            
            if matching_files:
                # Return the most recently modified file
                matching_files.sort(
                    key=lambda f: os.path.getmtime(f),
                    reverse=True
                )
                return matching_files[0]
        
        except OSError:
            pass
        
        return None

    def _open_file(self, file_path: str) -> None:
        """Open a file with the default application."""
        if not os.path.exists(file_path):
            messagebox.showerror("File Not Found", f"File does not exist:\n{file_path}")
            return
        
        try:
            if platform.system() == 'Windows':
                os.startfile(file_path)
            elif platform.system() == 'Darwin':  # macOS
                subprocess.Popen(['open', file_path])
            else:  # Linux
                subprocess.Popen(['xdg-open', file_path])
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}")

    def _save_file_copy(self, source_path: str, file_type: str) -> None:
        """Save a copy of the file to a user-selected location."""
        if not os.path.exists(source_path):
            messagebox.showerror("File Not Found", f"File does not exist:\n{source_path}")
            return
        
        # Determine file type for dialog
        if file_type == "excel":
            filetypes = [("Excel files", "*.xlsx"), ("All files", "*.*")]
        elif file_type == "ppt":
            filetypes = [("PowerPoint files", "*.pptx"), ("All files", "*.*")]
        else:
            filetypes = [("All files", "*.*")]
        
        default_name = os.path.basename(source_path)
        save_path = filedialog.asksaveasfilename(
            defaultextension=os.path.splitext(default_name)[1],
            initialfile=default_name,
            filetypes=filetypes
        )
        
        if not save_path:
            return  # User cancelled
        
        try:
            import shutil
            shutil.copy2(source_path, save_path)
            messagebox.showinfo("Success", f"File saved to:\n{save_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}")

    def _export_excel(self, report: Dict[str, Any]) -> None:
        """Open Excel file."""
        if not report.get('excel_exists'):
            messagebox.showwarning("Not Available", "Excel report is not available for this work.")
            return
        
        excel_path = report.get('excel_path')
        if excel_path:
            self._open_file(excel_path)

    def _export_ppt(self, report: Dict[str, Any]) -> None:
        """Open PowerPoint file."""
        if not report.get('ppt_exists'):
            messagebox.showwarning("Not Available", "PowerPoint report is not available for this work.")
            return
        
        ppt_path = report.get('ppt_path')
        if ppt_path:
            self._open_file(ppt_path)

    def _download_excel(self, report: Dict[str, Any]) -> None:
        """Download Excel file (save as)."""
        if not report.get('excel_exists'):
            messagebox.showwarning("Not Available", "Excel report is not available for this work.")
            return
        
        excel_path = report.get('excel_path')
        if excel_path:
            self._save_file_copy(excel_path, "excel")

    def _download_ppt(self, report: Dict[str, Any]) -> None:
        """Download PowerPoint file (save as)."""
        if not report.get('ppt_exists'):
            messagebox.showwarning("Not Available", "PowerPoint report is not available for this work.")
            return
        
        ppt_path = report.get('ppt_path')
        if ppt_path:
            self._save_file_copy(ppt_path, "ppt")

    def _add_report_row(self, index: int, report: Dict[str, Any]) -> None:
        """Add a row to the report table."""
        if self.table_body is None:
            return

        name = report.get("name", f"Report {index}")
        created_at = report.get("created_at", "-")
        excel_exists = report.get('excel_exists', False)
        ppt_exists = report.get('ppt_exists', False)

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
        row_frame.grid_columnconfigure(1, weight=2)                # Work Name
        row_frame.grid_columnconfigure(2, weight=1)                # Date
        row_frame.grid_columnconfigure(3, weight=2)                # Actions

        # Column 0: No.
        no_label = ctk.CTkLabel(
            row_frame,
            text=str(index),
            font=("Segoe UI", 11),
            anchor="center",
        )
        no_label.grid(row=0, column=0, sticky="ew", padx=12, pady=12)

        # Column 1: Work Name
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

        # Column 3: Actions
        actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
        actions_frame.grid(row=0, column=3, sticky="e", padx=12, pady=8)

        # Excel button
        excel_state = "normal" if excel_exists else "disabled"
        excel_btn = ctk.CTkButton(
            actions_frame,
            text="Excel",
            width=70,
            height=28,
            font=("Segoe UI", 9),
            state=excel_state,
            command=lambda r=report: self._export_excel(r),
        )
        excel_btn.pack(side="left", padx=(0, 4))

        # PowerPoint button
        ppt_state = "normal" if ppt_exists else "disabled"
        ppt_btn = ctk.CTkButton(
            actions_frame,
            text="PowerPoint",
            width=90,
            height=28,
            font=("Segoe UI", 9),
            state=ppt_state,
            command=lambda r=report: self._export_ppt(r),
        )
        ppt_btn.pack(side="left", padx=(0, 4))

        # Download button (opens save dialog)
        download_btn = ctk.CTkButton(
            actions_frame,
            text="Download",
            width=80,
            height=28,
            font=("Segoe UI", 9),
            fg_color=("gray20", "gray30"),
            state="normal" if (excel_exists or ppt_exists) else "disabled",
            command=lambda r=report: self._show_download_menu(r),
        )
        download_btn.pack(side="left")

    def _show_download_menu(self, report: Dict[str, Any]) -> None:
        """Show menu for choosing which file to download."""
        excel_exists = report.get('excel_exists', False)
        ppt_exists = report.get('ppt_exists', False)
        
        if not (excel_exists or ppt_exists):
            messagebox.showwarning("No Files", "No files available for download.")
            return
        
        # If only one exists, download it directly
        if excel_exists and not ppt_exists:
            self._download_excel(report)
            return
        if ppt_exists and not excel_exists:
            self._download_ppt(report)
            return
        
        # Show menu if both exist
        menu = ctk.CTkFrame(self.parent, corner_radius=8)
        menu.place(relx=0.5, rely=0.5, anchor="center")
        
        label = ctk.CTkLabel(menu, text="Download:", font=("Segoe UI", 11, "bold"))
        label.pack(padx=12, pady=(8, 4))
        
        if excel_exists:
            excel_btn = ctk.CTkButton(
                menu,
                text="Excel File",
                width=150,
                command=lambda r=report: (menu.destroy(), self._download_excel(r))
            )
            excel_btn.pack(padx=12, pady=2)
        
        if ppt_exists:
            ppt_btn = ctk.CTkButton(
                menu,
                text="PowerPoint File",
                width=150,
                command=lambda r=report: (menu.destroy(), self._download_ppt(r))
            )
            ppt_btn.pack(padx=12, pady=2)
        
        cancel_btn = ctk.CTkButton(
            menu,
            text="Cancel",
            width=150,
            fg_color="transparent",
            hover_color=("gray85", "gray30"),
            command=menu.destroy
        )
        cancel_btn.pack(padx=12, pady=(2, 8))

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
            text="View and export completed work reports (Excel and PowerPoint).",
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
        header_row.grid_columnconfigure(0, weight=0, minsize=50)
        header_row.grid_columnconfigure(1, weight=2)
        header_row.grid_columnconfigure(2, weight=1)
        header_row.grid_columnconfigure(3, weight=2)

        headers = ["No.", "Work Name", "Date", "Actions"]
        for col, header_text in enumerate(headers):
            header_label = ctk.CTkLabel(
                header_row,
                text=header_text,
                font=("Segoe UI", 11, "bold"),
                anchor="w" if col < 3 else "e",
            )
            header_label.grid(row=0, column=col, sticky="ew", padx=12, pady=10)

        # Scrollable table body
        self.table_body = ctk.CTkScrollableFrame(table_container, fg_color="transparent")
        self.table_body.grid(row=1, column=0, sticky="nsew")
        self.table_body.grid_columnconfigure(0, weight=0, minsize=50)
        self.table_body.grid_columnconfigure(1, weight=2)
        self.table_body.grid_columnconfigure(2, weight=1)
        self.table_body.grid_columnconfigure(3, weight=2)

        # Load reports and populate table
        reports = self._load_reports_from_filesystem()
        
        if reports:
            for idx, report in enumerate(reports, start=1):
                self._add_report_row(idx, report)
        else:
            hint_label = ctk.CTkLabel(
                self.table_body,
                text="No reports available. Complete a 'New Work' to generate reports.",
                font=("Segoe UI", 11),
                text_color=("gray40", "gray75"),
                justify="left",
            )
            hint_label.grid(row=0, column=0, columnspan=4, sticky="w", pady=(8, 8))

        # Refresh button
        refresh_btn = ctk.CTkButton(
            main_frame,
            text="🔄 Refresh Reports",
            command=self.show,
            height=36,
            font=("Segoe UI", 11),
            width=150,
        )
        refresh_btn.grid(row=3, column=0, sticky="e", padx=24, pady=(0, 24))