import os
from typing import List, Optional, Set
from tkinter import messagebox
import customtkinter as ctk

from data_extractor import MasterfileExtractor
from data_extractor.utils import get_equipment_number_from_image_path
from excel_manager import ExcelManager
from convert_mypdf_to_image import PDFToImageConverter

# Import refactored components
from .constants import Messages
from .page_builders import Page1Builder, Page2Builder
from .ui_updater import UIUpdateManager
from UserInterface.managers.extraction_manager import ExtractionManager
from UserInterface.managers.state_manager import ViewState
from UserInterface.managers.powerpoint_export_manager import PowerPointExportManager
from UserInterface.services.file_service import FileService
from UserInterface.services.equipment_service import EquipmentService
from UserInterface.utils.threading_utils import SafeThreadExecutor, LoadingContext
from UserInterface.services.excel_validator import ExcelValidator, ExcelFileInfo, ExcelFileType
from UserInterface.services.data_validator import DataValidator, ValidationResult
from UserInterface.managers.ui_state_manager import UIStateController, UIState, UIStateConfig


class NewWorkView:
    """
    Main coordinator for New Work interface.
    
    This class is now much simpler - it delegates to specialized components:
    - FileService: File operations
    - EquipmentService: Business logic
    - ExtractionManager: Extraction coordination
    - Page1Builder/Page2Builder: UI construction
    - UIUpdateManager: Thread-safe UI updates
    - ViewState: State management
    """
    
    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self._initialized = False
        self.is_extracting = False
        
        # Initialize state
        self.state = ViewState()
        
        # Get project root
        self.project_root = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", "..")
        )
        # Initialize thread executor
        self.executor = SafeThreadExecutor(max_workers=3)
        
        # Initialize UI update manager
        self.ui_updater = UIUpdateManager(parent, batch_interval_ms=100)
        self._register_ui_handlers()
        self.ui_updater.start()
        
        #initialized validators and manager
        self.excel_validator = ExcelValidator(self.project_root)
        self.data_validator = DataValidator()
        self.ui_state_controller = UIStateController()

        # Current Excel file info
        self.excel_file_info: Optional[ExcelFileInfo] = None

        # Validation state
        self.validation_result: Optional[ValidationResult] = None
        self.highlighted_entries: Set[int] = set()

        # Initialize core components
        self._initialize_converters()
        
        # Initialize services
        self.file_service = FileService(
            self.pdf_converter,
            log_callback=self.log_callback
        )
        self.excel_manager: Optional[ExcelManager] = None
        self._initialize_managers()

        self.equipment_service = EquipmentService(
            self.excel_manager,
            self.extractor,
            log_callback=self.log_callback
        )
        
        self.extraction_manager = ExtractionManager(
            self.equipment_service,
            self.file_service,
            self.executor,
            self.ui_updater,
            self.log_callback
        )
        self.powerpoint_manager = PowerPointExportManager(
            project_root=self.project_root,
            state=self.state,
            controller=self.controller,
            executor=self.executor,
            log_callback=self.log_callback,
            parent_window=self.parent  # Pass parent window reference
        )

        
        # Initialize UI builders (but don't build yet)
        self.page1_builder = Page1Builder(parent, self)
        self.page2_builder = Page2Builder(parent, self)
        
        # Page frames (built lazily)
        self.page1_frame: Optional[ctk.CTkFrame] = None
        self.page2_frame: Optional[ctk.CTkFrame] = None
        
        # UI references (set by builders)
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.extraction_log_textbox: Optional[ctk.CTkTextbox] = None
        self.next_button: Optional[ctk.CTkButton] = None
        self.file_listbox: Optional[ctk.CTkTextbox] = None
        self.work_combobox: Optional[ctk.CTkComboBox] = None
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.progress_label: Optional[ctk.CTkLabel] = None
        self.extraction_log_textbox: Optional[ctk.CTkTextbox] = None
        self.next_button: Optional[ctk.CTkButton] = None
        self.file_listbox: Optional[ctk.CTkTextbox] = None
        self.work_combobox: Optional[ctk.CTkComboBox] = None
        self.file_mode: Optional[ctk.StringVar] = None
        self.files_edit_container: Optional[ctk.CTkFrame] = None
        self.excel_upload_button: Optional[ctk.CTkButton] = None
        self.file_browse_button: Optional[ctk.CTkButton] = None
        self.file_clear_button: Optional[ctk.CTkButton] = None
        self.start_extraction_button: Optional[ctk.CTkButton] = None
        self.save_excel_button: Optional[ctk.CTkButton] = None
        self.export_ppt_button: Optional[ctk.CTkButton] = None
        self.info_label: Optional[ctk.CTkLabel] = None
    
    # =========================================================================
    # INITIALIZATION
    # =========================================================================
    
    def _initialize_managers(self) -> None:
        """Initialize PDF converter, Excel manager, and extractor"""
        # Excel Manager
        excel_path = self._get_work_excel_path()
        if excel_path:
            self.excel_manager = ExcelManager(excel_path, log_callback=self.log_callback)
        
        # Extractor
        self.extractor = MasterfileExtractor(log_callback=self.log_callback)

    def _initialize_converters(self) -> None:
        # PDF Converter
        self.pdf_converter = PDFToImageConverter()
        work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        if work_id:
            self.state.converted_images_dir = os.path.join(
                self.project_root, "src", "output_files", work_id, "converted_images"
            )
            self.pdf_converter.output_folder = self.state.converted_images_dir

    def _register_ui_handlers(self) -> None:
        """Register handlers for UI updates from background threads"""
        self.ui_updater.register_handler('progress', self._handle_progress_update)
        self.ui_updater.register_handler('log', self._handle_log_update)
        self.ui_updater.register_handler('enable_next', self._handle_enable_next)
    
    # =========================================================================
    # UI UPDATE HANDLERS (Called on main thread)
    # =========================================================================
    
    def _handle_progress_update(self, data: dict) -> None:
        """Handle progress updates on main thread"""
        if self.progress_bar and self.progress_bar.winfo_exists():
            self.progress_bar.set(data.get('value', 0.0))
        
        if self.progress_label and self.progress_label.winfo_exists():
            text = data.get('text')
            if text:
                self.progress_label.configure(text=text)
    
    def _handle_log_update(self, message: str) -> None:
        """Handle log updates on main thread"""
        if (self.state.current_page == 1 and 
            self.state.page_1_active and
            self.extraction_log_textbox and 
            self.extraction_log_textbox.winfo_exists()):
            
            self.extraction_log_textbox.configure(state="normal")
            self.extraction_log_textbox.insert("end", message + "\n")
            self.extraction_log_textbox.see("end")
            self.extraction_log_textbox.configure(state="disabled")
    
    def _handle_enable_next(self, _) -> None:
        """Enable next button"""
        if self.next_button and self.next_button.winfo_exists():
            self.next_button.configure(state="normal")
    
    # =========================================================================
    # LOGGING (Thread-safe)
    # =========================================================================
    
    def log_callback(self, message: str) -> None:
        """Thread-safe logging callback"""
        self.ui_updater.queue_update('log', message)
    
    # =========================================================================
    # UI STATE MANAGEMENT
    # =========================================================================
    
    def update_ui_state(self) -> None:
        """Update UI elements based on current state"""
        # Check permissions
        has_permission = True
        
        # Get work and check Excel
        work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        if work_id and not self.excel_file_info:
            self.check_excel_file(work_id)
        
        # Validate data if on page 2
        data_validated = False
        if self.state.current_page == 2:
            # Use existing validation result if available
            if self.validation_result:
                data_validated = self.validation_result.is_valid
            else:
                # If no validation result yet, mark as not validated
                data_validated = False
        
        # Compute UI state
        ui_config = self.ui_state_controller.compute_ui_state(
            has_permission=has_permission,
            excel_file_info=self.excel_file_info or ExcelFileInfo(
                ExcelFileType.NOT_FOUND, None, False, set(), None
            ),
            has_files_selected=self.state.has_files,
            extraction_complete=self.state.extraction_complete,
            data_validated=data_validated,
            is_extracting=self.is_extracting
        )
        
        # Apply UI configuration
        self._apply_ui_config(ui_config)
    
    def _apply_ui_config(self, config: UIStateConfig) -> None:
        """Apply UI configuration to widgets"""
        # Page 1 controls
        if self.work_combobox:
            state = "readonly" if config.work_selector_enabled else "disabled"
            self.work_combobox.configure(state=state)
        
        if self.excel_upload_button:
            if config.excel_upload_visible:
                self.excel_upload_button.pack(side="left", padx=(0, 8))
            else:
                self.excel_upload_button.pack_forget()
        
        if self.file_browse_button:
            state = "normal" if config.file_browse_enabled else "disabled"
            self.file_browse_button.configure(state=state)
        
        if self.file_clear_button:
            state = "normal" if config.file_clear_enabled else "disabled"
            self.file_clear_button.configure(state=state)
        
        if self.start_extraction_button:
            state = "normal" if config.start_extraction_enabled else "disabled"
            self.start_extraction_button.configure(state=state)
        
        if self.next_button:
            state = "normal" if config.next_button_enabled else "disabled"
            self.next_button.configure(state=state)
        
        # Page 2 controls
        if self.save_excel_button:
            state = "normal" if config.save_excel_enabled else "disabled"
            self.save_excel_button.configure(state=state)
        
        if self.export_ppt_button:
            state = "normal" if config.export_powerpoint_enabled else "disabled"
            self.export_ppt_button.configure(state=state)
        
        # Info message
        if self.info_label and config.info_message:
            self.info_label.configure(text=config.info_message)
        
        # Blocking message
        if config.show_blocking_message:
            messagebox.showwarning("Access Denied", config.info_message)
    
    # =========================================================================
    # UI UPDATE HANDLERS & LOGGING
    # =========================================================================
    
    def _register_ui_handlers(self) -> None:
        """Register handlers for UI updates from background threads"""
        self.ui_updater.register_handler('progress', self._handle_progress_update)
        self.ui_updater.register_handler('log', self._handle_log_update)
        self.ui_updater.register_handler('enable_next', self._handle_enable_next)
    
    def _handle_progress_update(self, data: dict) -> None:
        """Handle progress updates on main thread"""
        if self.progress_bar and self.progress_bar.winfo_exists():
            self.progress_bar.set(data.get('value', 0.0))
        
        if self.progress_label and self.progress_label.winfo_exists():
            text = data.get('text')
            if text:
                self.progress_label.configure(text=text)
    
    def _handle_log_update(self, message: str) -> None:
        """Handle log updates on main thread"""
        if (self.state.current_page == 1 and 
            self.state.page_1_active and
            self.extraction_log_textbox and 
            self.extraction_log_textbox.winfo_exists()):
            
            self.extraction_log_textbox.configure(state="normal")
            self.extraction_log_textbox.insert("end", message + "\n")
            self.extraction_log_textbox.see("end")
            self.extraction_log_textbox.configure(state="disabled")
    
    def _handle_enable_next(self, _) -> None:
        """Enable next button"""
        if self.next_button and self.next_button.winfo_exists():
            self.next_button.configure(state="normal")
    
    def log_callback(self, message: str) -> None:
        """Thread-safe logging callback"""
        self.ui_updater.queue_update('log', message)

    # =========================================================================
    # PAGE NAVIGATION
    # =========================================================================
    def _clear_parent(self) -> None:
        for widget in self.parent.winfo_children():
            widget.destroy()

    def _show_no_work_assigned_screen(self) -> None:
        """Show screen when user has no work assigned"""
        self._clear_parent()
        
        frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        frame.pack(expand=True, fill="both", padx=50, pady=50)
        
        # Icon
        icon = ctk.CTkLabel(
            frame,
            text="🚫",
            font=("Segoe UI", 72)
        )
        icon.pack(pady=(50, 20))
        
        # Title
        title = ctk.CTkLabel(
            frame,
            text="No Work Assigned",
            font=("Segoe UI", 24, "bold")
        )
        title.pack(pady=10)
        
        # Message
        msg = ctk.CTkLabel(
            frame,
            text="You do not have any work assigned.\nPlease contact your administrator.",
            font=("Segoe UI", 14),
            justify="center"
        )
        msg.pack(pady=20)
        
        # Back button
        back_btn = ctk.CTkButton(
            frame,
            text="← Back to Main Menu",
            command=self.controller.show_main_menu,
            width=200,
            height=40,
            font=("Segoe UI", 12)
        )
        back_btn.pack(pady=30)

    def setInitialized(self, value: bool) -> None:
        self._initialized = value

    def show(self) -> None:
        """Entry point - show Page 1"""
        if not self._initialized:
            self._clear_parent()
            self.setInitialized(True)
        self.show_page_1()
    
    def show_page_1(self) -> None:
        """Show Page 1 - Upload & Extract"""
        self.state.current_page = 1
        self.state.page_1_active = True
        self.state.page_2_active = False
        
        # Build page if not built yet
        if self.page1_frame is None:
            self.page1_frame = self.page1_builder.build()
        
        # Hide page 2 if shown
        if self.page2_frame is not None:
            self.page2_frame.pack_forget()
        
        # Show page 1 (only if it exists)
        if self.page1_frame.winfo_exists():
            self.page1_frame.pack(expand=True, fill="both")
        else:
            # Recreate if destroyed
            self.page1_frame = self.page1_builder.build()
            self.page1_frame.pack(expand=True, fill="both")
        
        # Refresh and update UI state
        self.refresh_file_list()
        self.update_ui_state()
    
    def show_page_2(self) -> None:
        """Show Page 2 - Review & Save"""
        if not self.state.can_proceed_to_page_2:
            messagebox.showwarning(
                "Cannot Proceed",
                "Please complete extraction before proceeding to review."
            )
            return
        
        self.state.current_page = 2
        self.state.page_1_active = False
        self.state.page_2_active = True
        
        # Build page if not built yet
        if self.page2_frame is None:
            self.page2_frame = self.page2_builder.build()
        
        # Hide page 1
        if self.page1_frame is not None:
            self.page1_frame.pack_forget()
        
        # Show page 2
        self.page2_frame.pack(expand=True, fill="both")
        
        # Rebuild data tables and validate
        self.rebuild_data_tables()
        # Validate data FIRST
        self.validate_data()

        self.update_ui_state()
    
    # =========================================================================
    # FILE OPERATIONS (Delegates to FileService)
    # =========================================================================
    
    def select_files(self, mode: str = "single") -> None:
        """Select files with validation"""
        # Check if we can upload files
        if not self._can_upload_files():
            return
        
        selected = self.file_service.select_files(mode)
        
        if selected:
            # Convert PDFs to images
            converted = self.file_service.convert_pdfs_to_images(selected)
            
            # Validate each equipment before adding
            valid_equipment = []
            for eq_no in converted:
                can_upload, reason = self._can_upload_equipment(eq_no)
                
                if can_upload:
                    valid_equipment.append(eq_no)
                    self.log_callback(f"✅ {eq_no}: Ready to extract")
                else:
                    self.log_callback(f"⚠️ {eq_no}: {reason}")
                    messagebox.showwarning(
                        "Cannot Upload",
                        f"Equipment {eq_no}: {reason}"
                    )
            
            # Add valid equipment to state
            for eq_no in valid_equipment:
                self.state.add_file(eq_no)
            
            if valid_equipment:
                self.log_callback(f"📁 Added {len(valid_equipment)} file(s) for extraction")
            
            self.refresh_file_list()
            self.update_ui_state()
    
    def _can_upload_files(self) -> bool:
        """Check if files can be uploaded"""
        # Must have Excel file
        if not self.excel_file_info or self.excel_file_info.file_type == ExcelFileType.NOT_FOUND:
            messagebox.showwarning(
                "No Excel File",
                "Please upload the default Excel masterfile before selecting GA drawings."
            )
            return False
        
        # Cannot upload if extraction is complete (must start over)
        if self.state.extraction_complete:
            messagebox.showwarning(
                "Extraction Complete",
                "Extraction is already complete. Please proceed to review or start a new work."
            )
            return False
        
        return True

    def _can_upload_equipment(self, equipment_number: str) -> tuple[bool, str]:
        """Check if specific equipment can be uploaded"""
        if not self.excel_file_info:
            return False, "No Excel file loaded"
        
        # Check if work already done for this equipment
        can_upload, reason = self.excel_validator.can_upload_equipment(
            self.excel_file_info,
            equipment_number
        )
        
        return can_upload, reason

    def clear_files(self) -> None:
        """Clear selected files"""
        self.state.clear_files()
        self.refresh_file_list()
    
    def upload_excel_for_work(self) -> None:
        """Upload Excel file for current work"""
        work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        
        if not work_id:
            messagebox.showwarning("No Work", Messages.NO_WORK)
            return
        
        from tkinter import filedialog
        import shutil
        
        filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        path = filedialog.askopenfilename(
            title=f"Select Excel file for {work_id}",
            filetypes=filetypes
        )
        
        if not path:
            return
        
        try:
            dest_dir = os.path.join(self.project_root, "src", "output_files", work_id, "excel","default")
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, os.path.basename(path))
            shutil.copy2(path, dest_file)
            
            # Reinitialize Excel manager
            self.excel_manager = ExcelManager(dest_file, log_callback=self.log_callback)
            
            messagebox.showinfo("Success", f"Excel file uploaded successfully for {work_id}.")
            
            # Refresh page 1 to update button visibility
            if self.state.current_page == 1:
                self.page1_frame = None  # Force rebuild
                self.show_page_1()
        
        except Exception as e:
            messagebox.showerror("Upload Failed", f"Failed to upload Excel file:\n{e}")
    
    def refresh_file_list(self) -> None:
        """Refresh the file list display"""
        if not hasattr(self, 'file_listbox') or self.file_listbox is None:
            return
        
        self.file_listbox.configure(state="normal")
        self.file_listbox.delete("1.0", "end")
        
        # Show Excel status
        work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        if work_id:
            excel_path = self._get_work_excel_path()
            if excel_path:
                excel_filename = os.path.basename(excel_path)
                self.file_listbox.insert("end", f"[MASTERFILE] 📋 {excel_filename}\n")
            else:
                self.file_listbox.insert("end", "[MASTERFILE] ⚠️ No Excel uploaded\n")
        
        # Show GA files
        if self.state.selected_files:
            self.file_listbox.insert("end", "\n[GA DRAWINGS]\n")
            for idx, file_path in enumerate(self.state.selected_files, start=1):
                filename = os.path.basename(file_path)
                self.file_listbox.insert("end", f"  {idx}. 📄 {filename}\n")
        else:
            self.file_listbox.insert("end", "\n[GA DRAWINGS] No files selected\n")
        
        self.file_listbox.configure(state="disabled")
    
    # =========================================================================
    # EXTRACTION (Delegates to ExtractionManager)
    # =========================================================================
    
    def start_extraction(self) -> None:
        """Start extraction with validation"""
        # Validate prerequisites
        if not self.state.has_files:
            messagebox.showwarning("No Files", "Please select GA drawing files first.")
            return
        
        if not self.excel_manager:
            messagebox.showerror("No Excel", "Excel masterfile not loaded.")
            return
        
        if self.state.extraction_complete:
            messagebox.showwarning(
                "Already Complete",
                "Extraction is already complete. Please proceed to review."
            )
            return
        
        # Set extracting flag
        self.is_extracting = True
        self.update_ui_state()
        
        # Run extraction
        with LoadingContext(self.controller, "Starting extraction...", show_progress=True):
            self.executor.submit(self._run_extraction)
    
    def _run_extraction(self) -> None:
        """Run extraction in background thread"""
        try:
            # Run extraction
            updated_map = self.extraction_manager.run_extraction(
                self.state.selected_files,
                self.state.converted_images_dir
            )
            
            # Update state
            self.state.equipment_map = updated_map
            
            # Store per-file data
            for file_path in self.state.selected_files:
                if file_path in updated_map:
                    self.state.set_equipment_data(
                        file_path,
                        {file_path: updated_map[file_path]}
                    )
            
            # Mark complete
            self.state.extraction_complete = True
            self.is_extracting = False
            
            # Update UI state
            self.parent.after(0, self.update_ui_state)
            
            # Show notification
            if hasattr(self.controller, 'show_notification'):
                total = len(self.state.selected_files)
                self.parent.after(100, lambda: self.controller.show_notification(
                    f"Successfully extracted data from {total} file(s)!",
                    "success",
                    5000
                ))
        
        except Exception as e:
            self.is_extracting = False
            self.log_callback(f"❌ Extraction error: {e}")
            self.parent.after(0, self.update_ui_state)
            self.parent.after(0, lambda: messagebox.showerror(
                "Extraction Error",
                f"Error during extraction:\n{e}"
            ))
    
    # =========================================================================
    # PAGE 2 DATA VALIDATION
    # =========================================================================
    
    def validate_data(self) -> ValidationResult:
        """Validate all data on Page 2"""
        self.validation_result = self.data_validator.validate_equipment_map(
            self.state.equipment_map,
            self.state.file_to_textboxes
        )
        
        if self.validation_result.has_empty_cells:
            self.log_callback(
                f"⚠️ Found {len(self.validation_result.empty_cells)} empty required field(s)"
            )
            # Highlight empty cells
            self._highlight_empty_cells()
        else:
            self.log_callback("✅ All required fields are filled")
            # Clear any previous highlights
            self._clear_highlights()
        
        
        return self.validation_result
    
    def _highlight_empty_cells(self) -> None:
        """Highlight empty required cells in red"""
        if not self.validation_result or not self.validation_result.has_empty_cells:
            return
        
        empty_indices = self.data_validator.get_empty_cell_indices(
            self.state.file_to_textboxes,
            self.validation_result.empty_cells
        )
        
        # Highlight each empty entry
        for file_path, entries in self.state.file_to_textboxes.items():
            for idx, entry in enumerate(entries):
                if idx in empty_indices:
                    entry.configure(
                        fg_color=("#FFE6E6", "#4D0000"),  # Light red
                        border_color=("red", "darkred"),
                        border_width=2
                    )
                    self.highlighted_entries.add(id(entry))
                elif id(entry) in self.highlighted_entries:
                    # Clear previous highlight
                    entry.configure(
                        fg_color=("white", "gray20"),
                        border_color=("gray70", "gray30"),
                        border_width=1
                    )
                    self.highlighted_entries.discard(id(entry))
    
    def _clear_highlights(self) -> None:
        """Clear all cell highlights"""
        for file_path, entries in self.state.file_to_textboxes.items():
            for entry in entries:
                if id(entry) in self.highlighted_entries:
                    entry.configure(
                        fg_color=("white", "gray20"),
                        border_color=("gray70", "gray30"),
                        border_width=1
                    )
        
        self.highlighted_entries.clear()

    # =========================================================================
    # DATA MANAGEMENT
    # =========================================================================
    
    def rebuild_data_tables(self) -> None:
        """Rebuild data tables on Page 2"""
        if not hasattr(self, 'files_edit_container') or self.files_edit_container is None:
            return
        
        # Clear existing
        for child in self.files_edit_container.winfo_children():
            child.destroy()
        self.state.file_to_textboxes.clear()
        
        if not self.state.selected_files:
            info = ctk.CTkLabel(
                self.files_edit_container,
                text="No files processed.",
                font=("Segoe UI", 11),
            )
            info.pack(pady=20)
            return
        
        # Build table for each file
        from .constants import TableColumns
        
        for file_idx, file_path in enumerate(self.state.selected_files, start=1):
            self._build_file_table(file_path, file_idx, TableColumns.COLUMNS)
    
    def _build_file_table(self, file_path: str, file_idx: int, columns: List[tuple]) -> None:
        """Build editable table for a single file"""
        from .constants import Colors, Sizes, Fonts
        
        filename = os.path.basename(file_path)
        equipment_number = get_equipment_number_from_image_path(file_path)
        
        # File section
        file_section = ctk.CTkFrame(self.files_edit_container, fg_color=Colors.TRANSPARENT)
        file_section.pack(fill="x", padx=0, pady=(12, 8))
        
        # Header
        header_text = f"📄 {filename}"
        if equipment_number:
            header_text += f" (Equipment: {equipment_number})"
        
        header = ctk.CTkLabel(file_section, text=header_text, font=Fonts.SECTION_LABEL)
        header.pack(anchor="w", pady=(0, 8))
        
        # Get equipment data for this file
        equipment_data = self.state.get_equipment_for_file(file_path)
        
        if not equipment_data:
            no_data = ctk.CTkLabel(
                file_section,
                text=f"No equipment data found for {equipment_number or 'this file'}",
                font=Fonts.SUBTITLE,
                text_color=("gray50", "gray75"),
            )
            no_data.pack(pady=10)
            return
        
        # Create table
        table_frame = ctk.CTkScrollableFrame(
            file_section,
            fg_color=Colors.SECTION_BG,
            corner_radius=Sizes.CORNER_RADIUS_XS,
            height=300,
            orientation="horizontal",
        )
        table_frame.pack(fill="both", expand=True)
        
        # Build table header
        self._build_table_header(table_frame, columns)
        
        # Build table rows
        self._build_table_rows(table_frame, file_path, equipment_data, columns)
    
    def _build_table_header(self, parent: ctk.CTkFrame, columns: List[tuple]) -> None:
        """Build table header"""
        from .constants import Colors, Fonts
        
        header_row = ctk.CTkFrame(parent, fg_color=Colors.TABLE_HEADER_BG, corner_radius=0)
        header_row.pack(fill="x", padx=0, pady=0)
        
        for col_name, col_width in columns:
            label = ctk.CTkLabel(
                header_row,
                text=col_name,
                font=Fonts.TABLE_HEADER,
                text_color=Colors.TABLE_HEADER_TEXT,
                fg_color=Colors.TABLE_HEADER_BG,
                width=col_width,
                corner_radius=0,
            )
            label.pack(side="left", padx=1, pady=1)
    
    def _build_table_rows(
        self, 
        parent: ctk.CTkFrame,
        file_path: str,
        equipment_data: dict,
        columns: List[tuple]
    ) -> None:
        """Build table rows with data"""
        from .constants import Fonts
        
        row_entries = []
        row_counter = 0
        
        # Convert equipment data to rows
        for equipment in equipment_data.values():
            for component in equipment.components:
                # Create row frame
                row_frame = ctk.CTkFrame(parent, fg_color="transparent")
                row_frame.pack(fill="x", padx=0, pady=1)
                
                # Column values
                col_values = [
                    str(row_counter + 1),
                    equipment.equipment_number,
                    equipment.pmt_number,
                    equipment.equipment_description,
                    component.component_name,
                    component.phase,
                    component.get_existing_data_value('fluid') or '',
                    component.get_existing_data_value('material_type') or '',
                    component.get_existing_data_value('spec') or '',
                    component.get_existing_data_value('grade') or '',
                    component.get_existing_data_value('insulation') or '',
                    component.get_existing_data_value('design_temp') or '',
                    component.get_existing_data_value('design_pressure') or '',
                    component.get_existing_data_value('operating_temp') or '',
                    component.get_existing_data_value('operating_pressure') or '',
                ]
                
                # Create entry for each column
                for col_idx, (col_name, col_width) in enumerate(columns):
                    entry = ctk.CTkEntry(
                        row_frame,
                        font=Fonts.TINY,
                        width=col_width,
                        height=24,
                    )
                    entry.insert(0, col_values[col_idx])
                    entry.pack(side="left", padx=1, pady=1)
                    row_entries.append(entry)
                
                row_counter += 1
        
        # Store entries for this file
        self.state.file_to_textboxes[file_path] = row_entries
    
    # =========================================================================
    # EXCEL FILE MANAGEMENT
    # =========================================================================
    
    def check_excel_file(self, work_id: str) -> ExcelFileInfo:
        """Check Excel file status for a work"""
        self.excel_file_info = self.excel_validator.get_excel_file_info(work_id)
        
        # Log status
        if self.excel_file_info.file_type == ExcelFileType.NOT_FOUND:
            self.log_callback("📋 No Excel file found for this work")
        elif self.excel_file_info.file_type == ExcelFileType.DEFAULT:
            self.log_callback("📋 Default Excel file found (no work done yet)")
        elif self.excel_file_info.file_type == ExcelFileType.UPDATED:
            self.log_callback(
                f"📋 Updated Excel file found ({len(self.excel_file_info.equipment_with_work)} equipment with work)"
            )
        
        # Initialize Excel manager if file exists
        if self.excel_file_info.file_path:
            self.excel_manager = ExcelManager(
                self.excel_file_info.file_path,
                log_callback=self.log_callback
            )
            # Update equipment service
            self.equipment_service.excel_manager = self.excel_manager
        
        return self.excel_file_info
    
    def upload_default_excel(self, work_id: str) -> bool:
        """Upload default Excel file for a work"""
        from tkinter import filedialog
        import shutil
        
        filetypes = [("Excel files", "*.xlsx *.xls"), ("All files", "*.*")]
        path = filedialog.askopenfilename(
            title=f"Select Default Excel Masterfile for {work_id}",
            filetypes=filetypes
        )
        
        if not path:
            return False
        
        try:
            # Save to default location
            dest_dir = os.path.join(
                self.project_root, "src", "output_files", work_id, "excel", "default"
            )
            os.makedirs(dest_dir, exist_ok=True)
            dest_file = os.path.join(dest_dir, os.path.basename(path))
            shutil.copy2(path, dest_file)
            
            self.log_callback(f"✅ Default Excel uploaded: {os.path.basename(path)}")
            
            # Re-check Excel file status
            self.check_excel_file(work_id)
            
            # Refresh UI
            self.update_ui_state()
            
            messagebox.showinfo("Success", "Default Excel file uploaded successfully!")
            return True
        
        except Exception as e:
            self.log_callback(f"❌ Error uploading Excel: {e}")
            messagebox.showerror("Upload Failed", f"Failed to upload Excel file:\n{e}")
            return False

    # =========================================================================
    # SAVE TO EXCEL (Delegates to EquipmentService)
    # =========================================================================
    
    def save_to_excel(self) -> None:
        """Save with validation"""
        # Validate first
        validation = self.validate_data()
        
        if not validation.is_valid:
            messagebox.showerror(
                "Validation Failed",
                validation.error_message + "\n\nEmpty fields are highlighted in red."
            )
            return
        
         # Update UI state based on validation
        self.update_ui_state()
        # Proceed with save
        if not self.state.can_save:
            messagebox.showerror("No Data", Messages.NO_DATA)
            return
        
        with LoadingContext(self.controller, "Checking for changes...", show_progress=True) as loading:
            # Collect changes from UI
            updated_equipment = self._collect_changes_from_ui()
            
            if not updated_equipment:
                messagebox.showinfo("No Changes", "No changes were made to the equipment data.")
                return
            
            loading.update_progress(0.5, f"Saving {len(updated_equipment)} equipment items...")
            
            # Save in background
            self.executor.submit(self._run_save, updated_equipment)
    
    def _collect_changes_from_ui(self) -> dict:
        """Collect changes from UI and return only modified equipment"""
        # Implementation similar to original _update_equipment_map_from_ui
        # but optimized to only copy changed equipment
        
        changed_equipment = {}
        
        for file_path, entries in self.state.file_to_textboxes.items():
            if not entries:
                continue
            
            from .constants import TableColumns
            num_cols = TableColumns.NUM_COLUMNS
            num_rows = len(entries) // num_cols
            
            for row_idx in range(num_rows):
                start_idx = row_idx * num_cols
                row_entries = entries[start_idx:start_idx + num_cols]
                
                if len(row_entries) < num_cols:
                    continue
                
                equipment_no = row_entries[1].get().strip()
                parts = row_entries[4].get().strip()
                
                if equipment_no and equipment_no in self.state.equipment_map and parts:
                    # Check if this equipment has changes
                    has_changes = self._check_row_for_changes(
                        equipment_no, 
                        parts, 
                        row_entries
                    )
                    
                    if has_changes and equipment_no not in changed_equipment:
                        # Deep copy only when we know there are changes
                        changed_equipment[equipment_no] = self._deep_copy_equipment(
                            self.state.equipment_map[equipment_no]
                        )
                        
                        # Apply changes
                        self._apply_row_changes(
                            changed_equipment[equipment_no],
                            parts,
                            row_entries
                        )
        
        return changed_equipment
    
    def _check_row_for_changes(self, equipment_no: str, parts: str, row_entries: list) -> bool:
        """Check if a row has changes"""
        equipment = self.state.equipment_map.get(equipment_no)
        if not equipment:
            return False
        
        for component in equipment.components:
            if component.component_name == parts:
                # Check if any field changed
                ui_values = {
                    'fluid': row_entries[6].get().strip(),
                    'type': row_entries[7].get().strip(),
                    'spec': row_entries[8].get().strip(),
                    'grade': row_entries[9].get().strip(),
                    'insulation': row_entries[10].get().strip(),
                    'design_temp': row_entries[11].get().strip(),
                    'design_pressure': row_entries[12].get().strip(),
                    'operating_temp': row_entries[13].get().strip(),
                    'operating_pressure': row_entries[14].get().strip(),
                }
                
                for key, ui_value in ui_values.items():
                    if ui_value:
                        current_value = str(component.get_existing_data_value(key) or '')
                        if ui_value != current_value:
                            return True
        
        return False
    
    def _deep_copy_equipment(self, equipment):
        """Deep copy an equipment object"""
        from models import Equipment, Component
        
        new_equipment = Equipment(
            equipment_number=equipment.equipment_number,
            pmt_number=equipment.pmt_number,
            equipment_description=equipment.equipment_description,
            row_index=equipment.row_index
        )
        
        for component in equipment.components:
            new_component = Component(
                component_name=component.component_name,
                phase=component.phase,
                existing_data=component.existing_data.copy(),
                row_index=component.row_index
            )
            new_equipment.add_component(new_component)
        
        return new_equipment
    
    def _apply_row_changes(self, equipment, parts: str, row_entries: list) -> None:
        """Apply UI changes to equipment"""
        for component in equipment.components:
            if component.component_name == parts:
                updates = {
                    'fluid': row_entries[6].get().strip(),
                    'type': row_entries[7].get().strip(),
                    'spec': row_entries[8].get().strip(),
                    'grade': row_entries[9].get().strip(),
                    'insulation': row_entries[10].get().strip(),
                    'design_temp': row_entries[11].get().strip(),
                    'design_pressure': row_entries[12].get().strip(),
                    'operating_temp': row_entries[13].get().strip(),
                    'operating_pressure': row_entries[14].get().strip(),
                }
                
                # Apply non-empty updates
                for key, value in updates.items():
                    if value:
                        component.existing_data[key] = value
    
    def _run_save(self, updated_equipment: dict) -> None:
        """Run save in background thread"""
        try:
            work_id = self.controller.current_work.get("id") if self.controller.current_work else None

            success = self.equipment_service.save_equipment_data(updated_equipment, work_id)
            
            if success:
                # Update main equipment map
                for eq_no, equipment in updated_equipment.items():
                    self.state.equipment_map[eq_no] = equipment
                
                # Show success
                self.parent.after(0, lambda: messagebox.showinfo(
                    "Save Successful",
                    Messages.SAVE_SUCCESS.format(len(updated_equipment))
                ))
                
                if hasattr(self.controller, 'show_notification'):
                    self.parent.after(0, lambda: self.controller.show_notification(
                        Messages.SAVE_SUCCESS.format(len(updated_equipment)),
                        "success",
                        5000
                    ))
            else:
                self.parent.after(0, lambda: messagebox.showerror(
                    "Save Failed",
                    Messages.SAVE_FAILED
                ))
        
        except Exception as e:
            self.parent.after(0, lambda: messagebox.showerror(
                "Save Error",
                f"Error saving data: {str(e)}"
            ))
    
    # =========================================================================
    # POWERPOINT EXPORT
    # =========================================================================
    
    def export_to_powerpoint(self) -> None:
        """Export to PowerPoint with validation"""
        # Validate first
        validation = self.validate_data()
        
        if not validation.is_valid:
            messagebox.showerror(
                "Validation Failed",
                validation.error_message + "\n\nEmpty fields are highlighted in red." +
                "\n\nPlease fill all required fields before exporting."
            )
            return
        
        # Proceed with export
        self.powerpoint_manager.export_to_powerpoint()

    # =========================================================================
    # UTILITIES
    # =========================================================================
    
    def _get_work_excel_path(self) -> Optional[str]:
        """Get Excel path for current work"""
        work_id = self.controller.current_work.get("id") if self.controller.current_work else None
        if not work_id:
            return None
        
        return self.file_service.get_work_excel_path(work_id, self.project_root)
    
    def _on_work_selected(self, choice: str) -> None:
        """Handle work selection"""
        for work in self.controller.available_works:
            if work.get("name", work.get("id")) == choice:
                self.controller.current_work = work
                break
    
    # =========================================================================
    # CLEANUP
    # =========================================================================
    
    def cleanup(self) -> None:
        """Cleanup resources"""
        self.ui_updater.stop()
        self.executor.shutdown(wait=False)
