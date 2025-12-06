"""New Work view for AutoRBI application (CustomTkinter)."""

import os
from typing import List, Optional, Dict
from tkinter import filedialog

import customtkinter as ctk


class NewWorkView:
    """Handles the New Work interface (file upload + extraction flow)."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.selected_files: List[str] = []
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.extracted_tabs: Optional[ctk.CTkTabview] = None
        # map file path -> list of textboxes (side-by-side columns)
        self.file_to_textboxes: Dict[str, List[ctk.CTkTextbox]] = {}

    # Public helpers the backend can call later
    def set_progress(self, value: float, text: Optional[str] = None) -> None:
        """Update the extraction progress bar (0.0–1.0)."""
        if self.progress_bar is not None:
            self.progress_bar.set(value)
        if text is not None and self.progress_label is not None:
            self.progress_label.configure(text=text)

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

    def set_extracted_text(self, content: str) -> None:
        """Populate all extracted data fields with the same content (simple case)."""
        for textboxes in self.file_to_textboxes.values():
            for textbox in textboxes:
                textbox.configure(state="normal")
                textbox.delete("1.0", "end")
                textbox.insert("1.0", content)

    def _select_files(self, mode: str) -> None:
        """Open file dialog to select one or multiple input files."""
        filetypes = [
            ("Supported files", "*.pdf *.jpg *.jpeg"),
            ("PDF", "*.pdf"),
            ("Images", "*.jpg *.jpeg"),
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

        # Rebuild per-file editable sections
        if not hasattr(self, "files_edit_container"):
            return

        # Clear old sections and mapping
        for child in self.files_edit_container.winfo_children():
            child.destroy()
        self.file_to_textboxes.clear()

        if not self.selected_files:
            info_lbl = ctk.CTkLabel(
                self.files_edit_container,
                text="No input files selected. Choose files above to start a new extraction.",
                font=("Segoe UI", 11),
                text_color=("gray50", "gray75"),
                wraplength=600,
                justify="left",
            )
            info_lbl.grid(row=0, column=0, sticky="w", padx=4, pady=4)
        else:
            for idx, path in enumerate(self.selected_files, start=1):
                filename = os.path.basename(path) or f"File {idx}"

                section = ctk.CTkFrame(self.files_edit_container, fg_color="transparent")
                section.grid(row=idx - 1, column=0, sticky="ew", padx=0, pady=(4, 8))
                section.grid_columnconfigure(0, weight=1)

                name_label = ctk.CTkLabel(
                    section,
                    text=filename,
                    font=("Segoe UI", 11, "bold"),
                )
                name_label.grid(row=0, column=0, sticky="w", pady=(0, 2))

                # Single editable field for this file
                textbox = ctk.CTkTextbox(
                    section,
                    font=("Segoe UI", 11),
                    wrap="none",
                    height=120,
                )
                textbox.grid(row=1, column=0, sticky="nsew")

                self.file_to_textboxes[path] = [textbox]

    def _clear_files(self) -> None:
        self.selected_files = []
        self._refresh_file_list()

    def _start_extraction(self) -> None:
        """Entry point for starting extraction (to be wired to backend)."""
        if not self.selected_files:
            from tkinter import messagebox
            messagebox.showwarning("No Files", "Please select files first.")
            return

        # Show loading overlay
        if hasattr(self.controller, 'show_loading'):
            self.controller.show_loading("Starting extraction...", show_progress=True)

        # Update progress bar
        self.set_progress(0.0, "Initializing extraction...")

        # TODO: Call backend extraction + Excel/DB update here.
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
                if hasattr(self.controller, 'update_loading_progress'):
                    self.parent.after(0, lambda p=progress, s=status: self.controller.update_loading_progress(p, s))
                
                time.sleep(1)  # Simulate processing time

            # Complete
            self.parent.after(0, lambda: self.set_progress(1.0, "Extraction complete!"))
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

    def _save_to_excel(self) -> None:
        """Confirm edits and trigger save to Excel/database (backend wiring required)."""
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

        # TODO: delegate to controller/backend, e.g.:
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
        """Display the New Work interface."""
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

        main_frame.grid_rowconfigure(4, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="New Work",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="1) Upload GA drawings  2) Extract & edit data  3) Save to Excel & database.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

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

        select_btn = ctk.CTkButton(
            file_buttons,
            text="Browse files (PDF, JPG, JPEG)",
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

        # --- Bottom section: per-file editable extracted data ----------------------
        bottom_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        bottom_section.grid(row=4, column=0, sticky="nsew", padx=24, pady=(4, 24))
        bottom_section.grid_rowconfigure(1, weight=1)
        bottom_section.grid_columnconfigure(0, weight=1)
        self.bottom_section = bottom_section

        data_label = ctk.CTkLabel(
            bottom_section,
            text="Extracted data (editable):",
            font=("Segoe UI", 11, "bold"),
        )
        data_label.grid(row=0, column=0, sticky="w")

        # Container that will hold per-file editable fields
        self.files_edit_container = ctk.CTkFrame(
            bottom_section,
            fg_color="transparent",
        )
        self.files_edit_container.grid(row=1, column=0, sticky="nsew", pady=(4, 0))
        self.files_edit_container.grid_columnconfigure(0, weight=1)

        helper_label = ctk.CTkLabel(
            bottom_section,
            text="After extraction, review and edit values here. They will be written to Excel and the database by the backend.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
            wraplength=600,
        )
        helper_label.grid(row=2, column=0, sticky="w", pady=(4, 0))

        # Save button at bottom-right
        save_btn = ctk.CTkButton(
            bottom_section,
            text="Save & update Excel",
            command=self._save_to_excel,
            height=32,
            font=("Segoe UI", 11, "bold"),
            fg_color=("gray20", "gray30"),
        )
        save_btn.grid(row=3, column=0, sticky="e", pady=(8, 0))

        # Initial state for file list & tabs
        self._refresh_file_list()
