"""
Base Dialog Class
Provides common functionality for modal dialogs.
"""

import customtkinter as ctk
from typing import Optional, Callable
from tkinter import messagebox

from AutoRBI_Database.logging_config import get_logger

logger = get_logger(__name__)


class BaseDialog(ctk.CTkToplevel):
    """
    Base class for modal dialogs with common functionality.
    
    Subclasses should override:
        - _build_content(): Build the main dialog content
        - _on_save(): Handle save/submit action
    """
    
    def __init__(
        self,
        parent,
        title: str,
        width: int = 500,
        height: int = 400,
        on_success: Optional[Callable] = None,
        notification_system=None,
        resizable: bool = True,
    ):
        """
        Initialize base dialog.
        
        Args:
            parent: Parent window
            title: Dialog title
            width: Dialog width
            height: Dialog height
            on_success: Callback on successful action
            notification_system: Notification system reference
            resizable: Whether dialog can be resized
        """
        super().__init__(parent)
        
        self.on_success = on_success
        self.notification_system = notification_system
        self._is_saving = False
        
        # Dialog configuration
        self.title(title)
        self.geometry(f"{width}x{height}")
        self.minsize(width - 50, height - 50)
        self.resizable(resizable, resizable)
        
        # Make modal
        self.transient(parent)
        self.grab_set()
        
        # Center dialog
        self._center_dialog(width, height)
        
        # Build UI structure
        self._build_structure()
        
        # Keyboard bindings
        self.bind("<Escape>", lambda e: self._on_cancel())
        
        # Protocol for window close button
        self.protocol("WM_DELETE_WINDOW", self._on_cancel)
    
    def _center_dialog(self, width: int, height: int):
        """Center the dialog on screen."""
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f"{width}x{height}+{x}+{y}")
    
    def _build_structure(self):
        """Build the dialog structure."""
        # Main container
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=24, pady=20)

        # Content area (to be filled by subclass)
        # Note: Don't expand to ensure buttons stay visible at bottom
        self.content_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=False)

        # Build subclass content
        self._build_content()

        # Button frame (will always appear at bottom)
        self._build_buttons()
    
    def _build_content(self):
        """
        Build dialog content. Override in subclass.
        """
        raise NotImplementedError("Subclasses must implement _build_content()")
    
    def _build_buttons(self):
        """Build standard button row."""
        button_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(16, 0))
        
        # Cancel button
        self.cancel_btn = ctk.CTkButton(
            button_frame,
            text="Cancel",
            command=self._on_cancel,
            width=140,
            height=40,
            font=("Segoe UI", 12),
            fg_color=("gray70", "gray30"),
            hover_color=("gray60", "gray35"),
        )
        self.cancel_btn.pack(side="left", pady=5)
        
        # Save button
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Save Changes",
            command=self._handle_save,
            width=180,
            height=40,
            font=("Segoe UI", 12, "bold"),
            fg_color=("#2ecc71", "#27ae60"),
            hover_color=("#27ae60", "#229954"),
        )
        self.save_btn.pack(side="right", pady=5)
    
    def _handle_save(self):
        """Handle save button click with loading state."""
        if self._is_saving:
            return
        
        self._is_saving = True
        self._set_saving_state(True)
        
        try:
            self._on_save()
        except Exception as e:
            logger.error(f"Error in save operation: {str(e)}")
            self._show_error(f"An error occurred: {str(e)}")
            self._set_saving_state(False)
            self._is_saving = False
    
    def _on_save(self):
        """
        Handle save action. Override in subclass.
        Must call _on_save_complete() when done.
        """
        raise NotImplementedError("Subclasses must implement _on_save()")
    
    def _on_save_complete(self, success: bool = True):
        """Called when save operation completes."""
        self._is_saving = False

        if success:
            if self.on_success:
                self.on_success()
            self.destroy()
        else:
            # Only reset button state if save failed (dialog stays open)
            self._set_saving_state(False)
    
    def _set_saving_state(self, is_saving: bool):
        """Update UI to reflect saving state."""
        # Check if dialog still exists before updating buttons
        if not self.winfo_exists():
            return

        if is_saving:
            self.save_btn.configure(state="disabled", text="Saving...")
            self.cancel_btn.configure(state="disabled")
        else:
            self.save_btn.configure(state="normal", text="Save Changes")
            self.cancel_btn.configure(state="normal")
        self.update()
    
    def _on_cancel(self):
        """Handle cancel/close action."""
        if self._is_saving:
            return  # Don't allow cancel during save
        self.destroy()
    
    def _show_error(self, message: str):
        """Show error message."""
        messagebox.showerror("Error", message)
    
    def _show_success(self, message: str):
        """Show success message."""
        messagebox.showinfo("Success", message)
    
    def _show_validation_error(self, message: str):
        """Show validation error message."""
        messagebox.showerror("Validation Error", message)