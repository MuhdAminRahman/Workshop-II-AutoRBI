"""Report Menu view for AutoRBI application."""

import tkinter as tk
from tkinter import ttk


class ReportMenuView:
    """Handles the Report Menu interface."""
    
    def __init__(self, parent: tk.Tk, controller):
        self.parent = parent
        self.controller = controller
    
    def show(self) -> None:
        """Display the Report Menu interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Header with back button
        header = ttk.Frame(self.parent, padding=20)
        header.pack(fill="x")
        
        back_btn = ttk.Button(
            header,
            text="← Back to Main Menu",
            style="Secondary.TButton",
            command=self.controller.show_main_menu
        )
        back_btn.pack(side="left")
        
        title_label = ttk.Label(
            header,
            text="AutoRBI",
            font=("Segoe UI", 24, "bold")
        )
        title_label.pack(side="right")
        
        # Main content area
        main_frame = ttk.Frame(self.parent, padding=60)
        main_frame.pack(expand=True, fill="both")
        
        page_title = ttk.Label(
            main_frame,
            text="Report Menu",
            font=("Segoe UI", 28, "bold")
        )
        page_title.pack(expand=True)
        
        # TODO: Add page-specific content here
        placeholder = ttk.Label(
            main_frame,
            font=("Segoe UI", 11),
            foreground="gray",
            justify="center"
        )
        placeholder.pack(pady=(20, 0))

