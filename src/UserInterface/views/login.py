"""Login view for AutoRBI application."""

import tkinter as tk
from tkinter import messagebox, ttk


class LoginView:
    """Handles the login interface."""
    
    def __init__(self, parent: tk.Tk, controller):
        self.parent = parent
        self.controller = controller
    
    def show(self) -> None:
        """Display the login interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Main container with padding
        main_frame = ttk.Frame(self.parent, padding=40)
        main_frame.pack(expand=True, fill="both")
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="AutoRBI",
            font=("Segoe UI", 32, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(
            main_frame,
            text="Welcome back. Please login to continue.",
            font=("Segoe UI", 11),
            foreground="gray"
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Login card
        login_card = ttk.LabelFrame(main_frame, text="Login", style="Card.TLabelframe")
        login_card.pack(fill="x", padx=100)
        
        # Username field
        username_frame = ttk.Frame(login_card)
        username_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(username_frame, text="Username", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        username_entry = ttk.Entry(username_frame, font=("Segoe UI", 10), width=30)
        username_entry.pack(fill="x")
        username_entry.focus()
        
        # Password field
        password_frame = ttk.Frame(login_card)
        password_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(password_frame, text="Password", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        password_entry = ttk.Entry(password_frame, font=("Segoe UI", 10), show="*", width=30)
        password_entry.pack(fill="x")
        
        # Login button
        def handle_login():
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if not username or not password:
                messagebox.showwarning("Login Error", "Please enter both username and password.")
                return
            # TODO: Integrate with backend authentication
            # if backend.authenticate(username, password):
            self.controller.show_main_menu()
            # else:
            #     messagebox.showerror("Login Failed", "Invalid username or password.")
        
        login_btn = ttk.Button(
            login_card,
            text="Login",
            style="Primary.TButton",
            command=handle_login
        )
        login_btn.pack(fill="x", pady=(0, 15))
        
        # Register button
        register_btn = ttk.Button(
            login_card,
            text="Don't have an account? Register",
            style="Secondary.TButton",
            command=self.controller.show_registration
        )
        register_btn.pack(fill="x")
        
        # Bind Enter key to login
        password_entry.bind("<Return>", lambda e: handle_login())

