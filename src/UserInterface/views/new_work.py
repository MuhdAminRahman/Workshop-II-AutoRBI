"""New Work view for AutoRBI application (CustomTkinter)."""

import os
from typing import List, Optional, Dict
from tkinter import filedialog
import shutil

import customtkinter as ctk


class NewWorkView:
    """Handles the New Work interface (file upload + extraction flow)."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.selected_files: List[str] = []
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.extraction_log_textbox: Optional[ctk.CTkTextbox] = None
        self.extracted_tabs: Optional[ctk.CTkTabview] = None
        # map file path -> list of textboxes (side-by-side columns)
        self.file_to_textboxes: Dict[str, List[ctk.CTkTextbox]] = {}
        self.selected_excel: Optional[str] = None
        self.current_page: int = 1  # Track page (1 = upload/extract, 2 = review/save)
        self.extraction_complete: bool = False
        self.next_button: Optional[ctk.CTkButton] = None
        # Store extracted equipment data
        self.extracted_equipment_data: Dict[str, List[Dict]] = {}  # {file_path: [equipment_rows]}

    # Public helpers the backend can call later
    def set_progress(self, value: float, text: Optional[str] = None) -> None:
        """Update the extraction progress bar (0.0–1.0)."""
        if self.progress_bar is not None:
            self.progress_bar.set(value)
        if text is not None and self.progress_label is not None:
            self.progress_label.configure(text=text)

    def append_extraction_log(self, message: str) -> None:
        """Append a message to the extraction log textbox."""
        if self.extraction_log_textbox is not None:
            self.extraction_log_textbox.configure(state="normal")
            self.extraction_log_textbox.insert("end", message + "\n")
            self.extraction_log_textbox.see("end")  # Auto-scroll to bottom
            self.extraction_log_textbox.configure(state="disabled")

    def set_extracted_text_for_file(self, file_path: str, content: str) -> None:
        """Populate the editable extracted data area for a specific file."""
        textboxes = self.file_to_textboxes.get(file_path)
        textbox = textboxes[0] if textboxes else None
        if textbox is None:
            # Fallback to match by filename only
            filename = os.path.basename(file_path)
            for path, tbs in self.file_to_textboxes.items():
                if os.path.basename(path) == filename and tbs:
                    textbox = tbs[0]
                    break
        if textbox is not None:
            textbox.configure(state="normal")
            textbox.delete("1.0", "end")
            textbox.insert("1.0", content)

    def set_extracted_equipment_data(self, file_path: str, equipment_list: List[Dict]) -> None:
        """
        Set extracted equipment data for a file.
        
        Args:
            file_path: Path to the extracted file
            equipment_list: List of dicts with equipment data
                Example: [
                    {
                        'equipment_no': 'V-001',
                        'pmt_no': 'PMT-001',
                        'description': 'Vessel 1',
                        'parts': 'Component A',
                        'phase': 'Gas',
                        'fluid': 'Nitrogen',
                        'type': 'Steel',
                        'spec': 'ASTM A516',
                        'grade': 'Grade 70',
                        'insulation': 'Yes',
                        'design_temp': '250',
                        'design_pressure': '10',
                        'operating_temp': '200',
                        'operating_pressure': '8'
                    },
                    ...
                ]
        """
        self.extracted_equipment_data[file_path] = equipment_list

    def set_extracted_text(self, content: str) -> None:
        """Populate all extracted data fields with the same content (simple case)."""
        for textboxes in self.file_to_textboxes.values():
            for textbox in textboxes:
                textbox.configure(state="normal")
                textbox.delete("1.0", "end")
                textbox.insert("1.0", content)

    def _select_files(self, mode: str) -> None:
        """Open file dialog to select one or multiple input files."""
        # Only allow image uploads (JPG, JPEG). PDF support removed per request.
        filetypes = [
            ("Images (JPG, JPEG)", "*.jpg *.jpeg"),
            ("JPG", "*.jpg"),
            ("JPEG", "*.jpeg"),
            ("All files", "*.*"),
        ]
        if mode == "single":
            path = filedialog.askopenfilename(filetypes=filetypes)
            self.selected_files = [path] if path else []
        else:
            paths = filedialog.askopenfilenames(filetypes=filetypes)
            self.selected_files = list(paths)

        # Update list display
        self._refresh_file_list()

    def _refresh_file_list(self) -> None:
        # Update compact file list (if created)
        if hasattr(self, "file_listbox"):
            self.file_listbox.configure(state="normal")
            self.file_listbox.delete("1.0", "end")
            if not self.selected_files:
                self.file_listbox.insert("1.0", "No files selected.")
            else:
                for idx, path in enumerate(self.selected_files, start=1):
                    self.file_listbox.insert("end", f"{idx}. {path}\n")
            self.file_listbox.configure(state="disabled")

    def _rebuild_extracted_data_page_2(self) -> None:
        """Rebuild extracted data display as a table for Page 2 with dynamic rows."""
        # Clear old sections and mapping
        for child in self.files_edit_container.winfo_children():
            child.destroy()
        self.file_to_textboxes.clear()

        if not self.selected_files:
            info_lbl = ctk.CTkLabel(
                self.files_edit_container,
                text="No input files processed. Go back to Step 1 to select files.",
                font=("Segoe UI", 11),
                text_color=("gray50", "gray75"),
                wraplength=600,
                justify="left",
            )
            info_lbl.grid(row=0, column=0, sticky="w", padx=4, pady=4)
        else:
            # Define masterfile columns exactly as in the Excel sheet
            columns = [
                ("NO.", 40),
                ("EQUIPMENT NO.", 100),
                ("PMT NO.", 90),
                ("EQUIPMENT DESCRIPTION", 150),
                ("PARTS", 100),
                ("PHASE", 70),
                ("FLUID", 80),
                ("TYPE", 80),
                ("SPEC.", 80),
                ("GRADE", 70),
                ("INSULATION\n(yes/No)", 80),
                ("DESIGN\nTEMP. (°C)", 90),
                ("DESIGN\nPRESSURE\n(Mpa)", 90),
                ("OPERATING\nTEMP. (°C)", 90),
                ("OPERATING\nPRESSURE\n(Mpa)", 90),
            ]

            for file_idx, path in enumerate(self.selected_files, start=1):
                filename = os.path.basename(path) or f"File {file_idx}"

                # File section header
                file_section = ctk.CTkFrame(self.files_edit_container, fg_color="transparent")
                file_section.grid(row=file_idx - 1, column=0, sticky="ew", padx=0, pady=(12, 8))
                file_section.grid_columnconfigure(0, weight=1)

                name_label = ctk.CTkLabel(
                    file_section,
                    text=f"📄 {filename}",
                    font=("Segoe UI", 12, "bold"),
                )
                name_label.pack(anchor="w", pady=(0, 8))

                # Create scrollable table frame with horizontal scrolling
                table_wrapper = ctk.CTkFrame(file_section, fg_color="transparent")
                table_wrapper.pack(fill="both", expand=True)
                table_wrapper.grid_columnconfigure(0, weight=1)

                # Horizontal scrollable frame for table
                table_frame = ctk.CTkScrollableFrame(
                    table_wrapper,
                    fg_color=("gray90", "gray15"),
                    corner_radius=8,
                    height=300,
                    orientation="horizontal",
                )
                table_frame.pack(fill="both", expand=True)

                # Table header with yellow background (matching masterfile)
                header_row = ctk.CTkFrame(table_frame, fg_color=("#FFFF00", "#555500"), corner_radius=0)
                header_row.pack(fill="x", padx=0, pady=0)

                for col_name, col_width in columns:
                    header_label = ctk.CTkLabel(
                        header_row,
                        text=col_name,
                        font=("Segoe UI", 8, "bold"),
                        text_color=("black", "yellow"),
                        fg_color=("#FFFF00", "#555500"),
                        width=col_width,
                        corner_radius=0,
                    )
                    header_label.pack(side="left", padx=1, pady=1)

                # Get equipment data for this file from extracted data
                equipment_rows = self.extracted_equipment_data.get(path, [])
                
                # If no extracted data, show placeholder rows
                if not equipment_rows:
                    equipment_rows = [
                        {
                            'equipment_no': '',
                            'pmt_no': '',
                            'description': '',
                            'parts': '',
                            'phase': '',
                            'fluid': '',
                            'type': '',
                            'spec': '',
                            'grade': '',
                            'insulation': '',
                            'design_temp': '',
                            'design_pressure': '',
                            'operating_temp': '',
                            'operating_pressure': ''
                        }
                    ]

                # Create row for each equipment
                for row_idx, equipment_data in enumerate(equipment_rows):
                    row_frame = ctk.CTkFrame(table_frame, fg_color="transparent")
                    row_frame.pack(fill="x", padx=0, pady=1)

                    row_entries = []

                    # Column values in order matching columns list
                    col_values = [
                        str(row_idx + 1),  # NO.
                        equipment_data.get('equipment_no', ''),
                        equipment_data.get('pmt_no', ''),
                        equipment_data.get('description', ''),
                        equipment_data.get('parts', ''),
                        equipment_data.get('phase', ''),
                        equipment_data.get('fluid', ''),
                        equipment_data.get('type', ''),
                        equipment_data.get('spec', ''),
                        equipment_data.get('grade', ''),
                        equipment_data.get('insulation', ''),
                        equipment_data.get('design_temp', ''),
                        equipment_data.get('design_pressure', ''),
                        equipment_data.get('operating_temp', ''),
                        equipment_data.get('operating_pressure', ''),
                    ]

                    for col_idx, (col_name, col_width) in enumerate(columns):
                        # Create editable entry field
                        entry = ctk.CTkEntry(
                            row_frame,
                            placeholder_text="",
                            font=("Segoe UI", 8),
                            width=col_width,
                            height=24,
                        )
                        entry.insert(0, col_values[col_idx])
                        entry.pack(side="left", padx=1, pady=1)
                        row_entries.append(entry)

                    # Store entries for this file path and row
                    if path not in self.file_to_textboxes:
                        self.file_to_textboxes[path] = []
                    self.file_to_textboxes[path].extend(row_entries)

    def _clear_files(self) -> None:
        self.selected_files = []
        self._refresh_file_list()

    def _start_extraction(self) -> None:
        """Entry point for starting extraction (to be wired to backend)."""
        # TODO: Backend - Call extraction service with self.selected_files
        # TODO: Backend - Call append_extraction_log() to send live status updates
        # TODO: Backend - Call set_extracted_equipment_data() to populate table on Page 2
        # TODO: Backend - Call set_progress() to update progress bar
        if not self.selected_files:
            from tkinter import messagebox
            messagebox.showwarning("No Files", "Please select files first.")
            return

        # Show loading overlay
        if hasattr(self.controller, 'show_loading'):
            self.controller.show_loading("Starting extraction...", show_progress=True)

        # Update progress bar
        self.set_progress(0.0, "Initializing extraction...")

        # TODO: Backend - Call extraction service and save results to Excel/database
        # Example (to be implemented in controller/backend):
        # self.controller.start_extraction(self.selected_files, self)
        
        # Simulate extraction progress (remove when backend is integrated)
        self._simulate_extraction()

    def _simulate_extraction(self) -> None:
        """Simulate extraction progress (for UI testing only)."""
        import threading
        import time

        def extraction_thread():
            total_files = len(self.selected_files)
            for idx, file_path in enumerate(self.selected_files):
                progress = (idx + 1) / total_files
                status = f"Processing {idx + 1}/{total_files}: {os.path.basename(file_path)}"
                
                self.parent.after(0, lambda p=progress, s=status: self.set_progress(p, s))
                self.parent.after(0, lambda f=file_path: self.append_extraction_log(f"▶ Processing: {os.path.basename(f)}"))
                
                if hasattr(self.controller, 'update_loading_progress'):
                    self.parent.after(0, lambda p=progress, s=status: self.controller.update_loading_progress(p, s))
                
                time.sleep(1)  # Simulate processing time
                self.parent.after(0, lambda f=file_path: self.append_extraction_log(f"✓ Completed: {os.path.basename(f)}"))

            # Complete extraction
            self.parent.after(0, lambda: self.set_progress(1.0, "Extraction complete!"))
            self.parent.after(0, lambda: self.append_extraction_log("✓ All files extracted successfully."))
            self.extraction_complete = True
            self.parent.after(0, lambda: self._show_next_button())
            
            if hasattr(self.controller, 'hide_loading'):
                self.parent.after(0, self.controller.hide_loading)
            if hasattr(self.controller, 'show_notification'):
                self.parent.after(0, lambda: self.controller.show_notification(
                    f"Successfully extracted data from {total_files} file(s)!",
                    "success",
                    5000
                ))

        thread = threading.Thread(target=extraction_thread, daemon=True)
        thread.start()

    def _show_next_button(self) -> None:
        """Show the Next button after extraction completes."""
        if self.next_button is not None:
            self.next_button.configure(state="normal")

    def _save_to_excel(self) -> None:
        """Confirm edits and trigger save to Excel/database (backend wiring required)."""
        # TODO: Backend - Retrieve edited data from self.file_to_textboxes
        # TODO: Backend - Validate edited data against masterfile schema
        # TODO: Backend - Update Excel file with edited equipment data
        # TODO: Backend - Save to database
        # TODO: Backend - Return status: success/error for notification
        # Collect edited text per file; backend can parse into structured fields.
        edited_data: Dict[str, List[str]] = {}
        for path, textboxes in self.file_to_textboxes.items():
            lines: List[str] = []
            for tb in textboxes:
                content = tb.get("1.0", "end").strip()
                if content:
                    lines.extend(content.splitlines())
            edited_data[path] = lines

        # Show loading
        if hasattr(self.controller, 'show_loading'):
            self.controller.show_loading("Saving to Excel and database...", show_progress=True)

        # TODO: Backend - Delegate to controller/backend for file validation and processing
        # self.controller.save_edited_data_to_excel(edited_data)
        
        # Simulate save (remove when backend is integrated)
        import threading
        import time

        def save_thread():
            time.sleep(1)  # Simulate save time
            self.parent.after(0, lambda: self.controller.hide_loading() if hasattr(self.controller, 'hide_loading') else None)
            self.parent.after(0, lambda: self.controller.show_notification(
                "Data saved successfully to Excel and database!",
                "success",
                5000
            ) if hasattr(self.controller, 'show_notification') else None)
            if self.progress_label is not None:
                self.parent.after(0, lambda: self.progress_label.configure(
                    text="✅ Data saved successfully to Excel and database."
                ))

        thread = threading.Thread(target=save_thread, daemon=True)
        thread.start()

    def show(self) -> None:
        """Display the New Work interface (Page 1: Upload & Extract)."""
        self.show_page_1()

    def show_page_1(self) -> None:
        """Page 1: File selection, extraction, and logs."""
        self.current_page = 1
        self.extraction_complete = False
        
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Outer frame with scrollable content inside
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

        # Scrollable main content area
        scroll_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        scroll_container.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame = scroll_container

        main_frame.grid_rowconfigure(5, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="New Work - Step 1: Upload & Extract",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Upload GA drawings and extract data.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=30, pady=(0, 18))

        # --- Top section: file selection & progress ---------------------------------
        top_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 12))
        top_section.grid_columnconfigure(0, weight=1)
        top_section.grid_columnconfigure(1, weight=0)

        # File mode (single / multiple)
        mode_label = ctk.CTkLabel(
            top_section,
            text="Select input mode:",
            font=("Segoe UI", 11, "bold"),
        )
        mode_label.grid(row=0, column=0, sticky="w")

        self.file_mode = ctk.StringVar(value="single")
        mode_switch = ctk.CTkSegmentedButton(
            top_section,
            values=["single", "multiple"],
            variable=self.file_mode,
        )
        mode_switch.grid(row=0, column=1, sticky="e")

        # File selection buttons
        file_buttons = ctk.CTkFrame(top_section, fg_color="transparent")
        file_buttons.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # Excel upload
        excel_btn = ctk.CTkButton(
            file_buttons,
            text="Upload Excel Sheet",
            command=self._upload_excel_sheet,
            height=32,
        )
        excel_btn.pack(side="left", padx=(0, 8))

        select_btn = ctk.CTkButton(
            file_buttons,
            text="Browse files (JPG, JPEG)",
            command=lambda: self._select_files(self.file_mode.get()),
            height=32,
        )
        select_btn.pack(side="left")

        clear_btn = ctk.CTkButton(
            file_buttons,
            text="Clear",
            command=self._clear_files,
            height=32,
            fg_color="transparent",
            text_color=("gray20", "gray90"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        clear_btn.pack(side="left", padx=(8, 0))

        # Progress bar
        progress_frame = ctk.CTkFrame(top_section, fg_color="transparent")
        progress_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        progress_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = ctk.CTkProgressBar(progress_frame, height=10)
        self.progress_bar.grid(row=0, column=0, sticky="ew")
        self.progress_bar.set(0.0)

        self.progress_label = ctk.CTkLabel(
            progress_frame,
            text="Ready to extract.",
            font=("Segoe UI", 10),
            text_color=("gray70", "gray80"),
        )
        self.progress_label.grid(row=1, column=0, sticky="w", pady=(4, 0))

        # Start extraction button (top-right)
        extract_btn = ctk.CTkButton(
            top_section,
            text="Start extraction",
            command=self._start_extraction,
            height=32,
            font=("Segoe UI", 11, "bold"),
        )
        extract_btn.grid(row=0, column=2, rowspan=3, sticky="e", padx=(16, 0))

        # --- Middle section: selected file list -------------------------------------
        file_list_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        file_list_section.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 4))
        file_list_section.grid_columnconfigure(0, weight=1)

        file_list_label = ctk.CTkLabel(
            file_list_section,
            text="Selected files:",
            font=("Segoe UI", 10, "bold"),
        )
        file_list_label.grid(row=0, column=0, sticky="w")

        self.file_listbox = ctk.CTkTextbox(
            file_list_section,
            height=60,
            font=("Segoe UI", 9),
        )
        self.file_listbox.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.file_listbox.configure(state="disabled")

        # --- Extraction log section ------------------------------------------------
        log_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        log_section.grid(row=4, column=0, sticky="nsew", padx=24, pady=(12, 12))
        log_section.grid_rowconfigure(1, weight=1)
        log_section.grid_columnconfigure(0, weight=1)

        log_label = ctk.CTkLabel(
            log_section,
            text="Extraction Log:",
            font=("Segoe UI", 11, "bold"),
        )
        log_label.grid(row=0, column=0, sticky="w", pady=(0, 4))

        self.extraction_log_textbox = ctk.CTkTextbox(
            log_section,
            height=150,
            font=("Segoe UI", 9),
            fg_color=("gray90", "gray15"),
            text_color=("gray20", "gray85"),
        )
        self.extraction_log_textbox.grid(row=1, column=0, sticky="nsew")
        self.extraction_log_textbox.configure(state="disabled")

        # --- Bottom section: Next button -------------------------------------------
        bottom_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_section.grid(row=5, column=0, sticky="ew", padx=24, pady=(12, 24))
        bottom_section.grid_columnconfigure(0, weight=1)

        self.next_button = ctk.CTkButton(
            bottom_section,
            text="Next: Review Extracted Data",
            command=self.show_page_2,
            height=36,
            font=("Segoe UI", 11, "bold"),
            state="disabled",  # Disabled until extraction completes
        )
        self.next_button.pack(side="right")

        # Initial state for file list
        self._refresh_file_list()

    def show_page_2(self) -> None:
        """Page 2: Review and edit extracted data, then save."""
        self.current_page = 2

        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Outer frame with scrollable content
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
            text="← Back to Step 1",
            command=self.show_page_1,
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

        # Scrollable main content area
        scroll_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        scroll_container.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame = scroll_container

        main_frame.grid_rowconfigure(2, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="New Work - Step 2: Review & Save",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Review extracted data, edit if needed, then save to Excel and database.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # --- Per-file editable extracted data ----------------------------------------
        data_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        data_section.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        data_section.grid_rowconfigure(2, weight=1)
        data_section.grid_columnconfigure(0, weight=1)

        data_label = ctk.CTkLabel(
            data_section,
            text="Extracted Data (Editable):",
            font=("Segoe UI", 12, "bold"),
        )
        data_label.grid(row=0, column=0, sticky="w", pady=(0, 8))

        helper_label = ctk.CTkLabel(
            data_section,
            text="Review and edit extracted values below. They will be saved to Excel and the database.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
        )
        helper_label.grid(row=1, column=0, sticky="w", pady=(0, 12))

        # Container that will hold per-file editable fields
        self.files_edit_container = ctk.CTkFrame(
            data_section,
            fg_color="transparent",
        )
        self.files_edit_container.grid(row=2, column=0, sticky="nsew", pady=(0, 12))
        self.files_edit_container.grid_columnconfigure(0, weight=1)
        self.files_edit_container.grid_rowconfigure(0, weight=1)

        # --- Action buttons at bottom -----------------------------------------------
        action_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_section.grid(row=3, column=0, sticky="ew", padx=24, pady=(12, 24))
        action_section.grid_columnconfigure(0, weight=1)

        save_btn = ctk.CTkButton(
            action_section,
            text="Save & Update Excel",
            command=self._save_to_excel,
            height=36,
            font=("Segoe UI", 11, "bold"),
            fg_color=("gray20", "gray30"),
        )
        save_btn.pack(side="right", padx=(8, 0))

        back_extract_btn = ctk.CTkButton(
            action_section,
            text="← Back to Extraction",
            command=self.show_page_1,
            height=36,
            font=("Segoe UI", 11),
        )
        back_extract_btn.pack(side="right")

        # Rebuild per-file editable sections with extracted data
        self._rebuild_extracted_data_page_2()

    def _upload_excel_sheet(self) -> None:
        """Open file dialog to choose an Excel file and copy into output folder."""
        # TODO: Backend - Validate Excel file format (check sheets, columns)
        # TODO: Backend - Verify Excel contains valid masterfile structure
        # TODO: Backend - Load and cache equipment data for later use
        filetypes = [
            ("Excel files", "*.xlsx *.xls"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Select Master Excel file", filetypes=filetypes)
        if not path:
            return

        # Copy selected file into output_files/default/excel (create if needed)
        try:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            dest_dir = os.path.join(project_root, "src", "output_files", "default", "excel")
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, os.path.basename(path))
            shutil.copy2(path, dest_path)
            self.selected_excel = dest_path
            if hasattr(self.controller, 'show_notification'):
                self.controller.show_notification("Master Excel uploaded successfully.", "success", 4000)
        except Exception as e:
            try:
                from tkinter import messagebox
                messagebox.showerror("Upload Failed", f"Failed to upload Excel file:\n{e}")
            except Exception:
                pass
