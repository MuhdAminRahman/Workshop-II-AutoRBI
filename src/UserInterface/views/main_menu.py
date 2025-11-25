"""Main menu view for AutoRBI application."""

import tkinter as tk
from tkinter import ttk


class MainMenuView:
    """Handles the main menu interface."""
    
    def __init__(self, parent: tk.Tk, controller):
        self.parent = parent
        self.controller = controller
    
    def show(self) -> None:
        """Display the main menu interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Header with logout
        header = ttk.Frame(self.parent, padding=20)
        header.pack(fill="x")
        
        title_label = ttk.Label(
            header,
            text="AutoRBI",
            font=("Segoe UI", 24, "bold")
        )
        title_label.pack(side="left")
        
        logout_btn = ttk.Button(
            header,
            text="Logout",
            style="Secondary.TButton",
            command=self.controller.logout
        )
        logout_btn.pack(side="right")
        
        # Main content area
        main_frame = ttk.Frame(self.parent, padding=60)
        main_frame.pack(expand=True, fill="both")
        
        welcome_label = ttk.Label(
            main_frame,
            text="Main Menu",
            font=("Segoe UI", 20, "bold")
        )
        welcome_label.pack(pady=(0, 50))
        
        # Menu buttons container
        buttons_frame = ttk.Frame(main_frame)
        buttons_frame.pack(expand=True)
        
        # Button configurations
        menu_buttons = [
            ("New Work", self.controller.show_new_work),
            ("Report Menu", self.controller.show_report_menu),
            ("Work History Menu", self.controller.show_work_history),
            ("Analytics Dashboard", self.controller.show_analytics),
        ]
        
        # Create buttons in a grid
        for idx, (text, command) in enumerate(menu_buttons):
            btn = ttk.Button(
                buttons_frame,
                text=text,
                style="Primary.TButton",
                command=command,
                width=25
            )
            row = idx // 2
            col = idx % 2
            btn.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
        
        buttons_frame.columnconfigure(0, weight=1)
        buttons_frame.columnconfigure(1, weight=1)
        buttons_frame.rowconfigure(0, weight=1)
        buttons_frame.rowconfigure(1, weight=1)

