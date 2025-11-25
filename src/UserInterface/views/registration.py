"""Registration view for AutoRBI application."""

import tkinter as tk
from tkinter import messagebox, ttk


class RegistrationView:
    """Handles the registration interface."""
    
    def __init__(self, parent: tk.Tk, controller):
        self.parent = parent
        self.controller = controller
    
    def show(self) -> None:
        """Display the registration interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        # Main container
        main_frame = ttk.Frame(self.parent, padding=40)
        main_frame.pack(expand=True, fill="both")
        
        # Title
        title_label = ttk.Label(
            main_frame,
            text="Create New Account",
            font=("Segoe UI", 28, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = ttk.Label(
            main_frame,
            text="Fill in your details to create an account.",
            font=("Segoe UI", 11),
            foreground="gray"
        )
        subtitle_label.pack(pady=(0, 40))
        
        # Registration card
        register_card = ttk.LabelFrame(main_frame, text="Registration", style="Card.TLabelframe")
        register_card.pack(fill="x", padx=100)
        
        # Full Name field
        fullname_frame = ttk.Frame(register_card)
        fullname_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(fullname_frame, text="Full Name", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        fullname_entry = ttk.Entry(fullname_frame, font=("Segoe UI", 10), width=30)
        fullname_entry.pack(fill="x")
        fullname_entry.focus()
        
        # Username field
        username_frame = ttk.Frame(register_card)
        username_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(username_frame, text="Username", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        username_entry = ttk.Entry(username_frame, font=("Segoe UI", 10), width=30)
        username_entry.pack(fill="x")
        
        # Password field
        password_frame = ttk.Frame(register_card)
        password_frame.pack(fill="x", pady=(0, 15))
        ttk.Label(password_frame, text="Password", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        password_entry = ttk.Entry(password_frame, font=("Segoe UI", 10), show="*", width=30)
        password_entry.pack(fill="x")
        
        # Confirm Password field
        confirm_frame = ttk.Frame(register_card)
        confirm_frame.pack(fill="x", pady=(0, 20))
        ttk.Label(confirm_frame, text="Confirm Password", font=("Segoe UI", 9)).pack(anchor="w", pady=(0, 5))
        confirm_entry = ttk.Entry(confirm_frame, font=("Segoe UI", 10), show="*", width=30)
        confirm_entry.pack(fill="x")
        
        # Register button
        def handle_register():
            fullname = fullname_entry.get().strip()
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            confirm = confirm_entry.get().strip()
            
            if not all([fullname, username, password, confirm]):
                messagebox.showwarning("Registration Error", "Please fill in all fields.")
                return
            
            if password != confirm:
                messagebox.showerror("Registration Error", "Passwords do not match.")
                return
            
            if len(password) < 6:
                messagebox.showwarning("Registration Error", "Password must be at least 6 characters long.")
                return
            
            # TODO: Integrate with backend registration
            # if backend.register(fullname, username, password):
            messagebox.showinfo("Success", "Registration successful! You can now login.")
            self.controller.show_login()
            # else:
            #     messagebox.showerror("Registration Failed", "Username already exists or registration failed.")
        
        register_btn = ttk.Button(
            register_card,
            text="Register",
            style="Primary.TButton",
            command=handle_register
        )
        register_btn.pack(fill="x", pady=(0, 15))
        
        # Back to login button
        back_btn = ttk.Button(
            register_card,
            text="Back to Login",
            style="Secondary.TButton",
            command=self.controller.show_login
        )
        back_btn.pack(fill="x")
        
        # Bind Enter key to register
        confirm_entry.bind("<Return>", lambda e: handle_register())

