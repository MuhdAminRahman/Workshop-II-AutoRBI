"""Registration view for AutoRBI application (CustomTkinter)."""

from tkinter import messagebox

import customtkinter as ctk


class RegistrationView:
    """Handles the registration interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller

    def show(self) -> None:
        """Display the registration interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Background container with gradient-like effect
        bg_frame = ctk.CTkFrame(
            self.parent,
            corner_radius=0,
            fg_color=("gray95", "gray10"),
        )
        bg_frame.pack(expand=True, fill="both")

        # Center container for glass card
        center_container = ctk.CTkFrame(bg_frame, fg_color="transparent")
        center_container.pack(expand=True, fill="both")
        center_container.grid_rowconfigure(0, weight=1)
        center_container.grid_columnconfigure(0, weight=1)

        # Glass morphism card - SQUARE shape with blur effect
        glass_card = ctk.CTkFrame(
            center_container,
            corner_radius=20,
            border_width=2,
            width=520,  # Square width (slightly larger for registration form)
            height=520,  # Square height (same as width for perfect square)
            # Glass effect: light colors for light mode, darker semi-transparent for dark mode
            fg_color=("#F0F0F0", "#2B2B2B"),
            border_color=("#E0E0E0", "#404040"),
        )
        glass_card.grid(row=0, column=0, padx=50, pady=40, sticky="")
        # Prevent the card from resizing - maintain square shape
        glass_card.grid_propagate(False)
        glass_card.grid_rowconfigure(0, weight=1)
        glass_card.grid_columnconfigure(0, weight=1)

        # Scrollable content inside glass card
        content = ctk.CTkScrollableFrame(
            glass_card,
            fg_color="transparent",
            scrollbar_button_color=("gray70", "gray40"),
            scrollbar_button_hover_color=("gray60", "gray50"),
        )
        content.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)
        content.grid_columnconfigure(0, weight=1)

        # Title
        title_label = ctk.CTkLabel(
            content,
            text="Create New Account",
            font=("Segoe UI", 28, "bold"),
            text_color=("gray20", "gray95"),
        )
        title_label.grid(row=0, column=0, pady=(0, 8), sticky="ew")

        subtitle_label = ctk.CTkLabel(
            content,
            text="Fill in your details to create an account.",
            font=("Segoe UI", 12),
            text_color=("gray40", "gray75"),
        )
        subtitle_label.grid(row=1, column=0, pady=(0, 32), sticky="ew")

        fields = ctk.CTkFrame(content, fg_color="transparent")
        fields.grid(row=2, column=0, sticky="ew")
        fields.grid_columnconfigure(0, weight=1)

        # Full Name field
        fullname_label = ctk.CTkLabel(
            fields,
            text="Full Name",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        fullname_label.pack(anchor="w", pady=(0, 8))

        fullname_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Enter your full name",
            font=("Segoe UI", 12),
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        fullname_entry.pack(fill="x", pady=(0, 16))
        fullname_entry.focus()

        # Username field
        username_label = ctk.CTkLabel(
            fields,
            text="Username",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        username_label.pack(anchor="w", pady=(0, 8))

        username_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Choose a username",
            font=("Segoe UI", 12),
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        username_entry.pack(fill="x", pady=(0, 16))

        # Password field
        password_label = ctk.CTkLabel(
            fields,
            text="Password",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        password_label.pack(anchor="w", pady=(0, 8))

        password_entry = ctk.CTkEntry(
            fields,
            placeholder_text="At least 6 characters",
            font=("Segoe UI", 12),
            show="*",
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        password_entry.pack(fill="x", pady=(0, 16))

        # Confirm Password field
        confirm_label = ctk.CTkLabel(
            fields,
            text="Confirm Password",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        confirm_label.pack(anchor="w", pady=(0, 8))

        confirm_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Re-enter your password",
            font=("Segoe UI", 12),
            show="*",
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        confirm_entry.pack(fill="x", pady=(0, 24))

        # Register button
        def handle_register() -> None:
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
                messagebox.showwarning(
                    "Registration Error",
                    "Password must be at least 6 characters long.",
                )
                return

            # TODO: Backend - Integrate with backend registration and user creation
            # if backend.register(fullname, username, password):
            messagebox.showinfo(
                "Success", "Registration successful! You can now login."
            )
            self.controller.show_login()
            # else:
            #     messagebox.showerror("Registration Failed", "Username already exists or registration failed.")

        # Primary button with glass effect
        register_btn = ctk.CTkButton(
            fields,
            text="Create account",
            command=handle_register,
            height=46,
            font=("Segoe UI", 13, "bold"),
            corner_radius=12,
            border_width=1,
            border_color=("#6496FF", "#6496FF"),
        )
        register_btn.pack(fill="x", pady=(0, 12))

        # Back to login button
        back_btn = ctk.CTkButton(
            fields,
            text="Back to login",
            command=self.controller.show_login,
            height=36,
            font=("Segoe UI", 11),
            fg_color="transparent",
            text_color=("gray40", "gray70"),
            hover_color=("#E8E8E8", "#404040"),
            border_width=0,
        )
        back_btn.pack(fill="x", pady=(0, 0))

        # Bind Enter key to register
        confirm_entry.bind("<Return>", lambda _event: handle_register())
