"""Login view for AutoRBI application (CustomTkinter)."""

from tkinter import messagebox
import os
from typing import Optional

from PIL import Image
import customtkinter as ctk


class LoginView:
    """Handles the login interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self._logo_image: Optional[ctk.CTkImage] = self._load_logo()

    def _load_logo(self) -> Optional[ctk.CTkImage]:
        """Load the iPETRO logo from disk if available."""
        try:
            base_dir = os.path.dirname(__file__)
            logo_path = os.path.join(base_dir, "ipetro.png")
            image = Image.open(logo_path)
            # Adjust size to suit the header
            return ctk.CTkImage(image, size=(160, 34))
        except Exception:
            # Fail gracefully if the image cannot be loaded
            return None

    def show(self) -> None:
        """Display the login interface."""
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
            width=480,  # Square width
            height=480,  # Square height (same as width for perfect square)
            # Glass effect: light colors for light mode, darker semi-transparent for dark mode
            fg_color=("#F0F0F0", "#2B2B2B"),
            border_color=("#E0E0E0", "#404040"),
        )
        glass_card.grid(row=0, column=0, padx=80, pady=60, sticky="")
        # Prevent the card from resizing - maintain square shape
        glass_card.grid_propagate(False)
        glass_card.grid_rowconfigure(0, weight=1)
        glass_card.grid_columnconfigure(0, weight=1)

        # Content inside glass card
        content = ctk.CTkFrame(glass_card, fg_color="transparent")
        content.grid(row=0, column=0, sticky="nsew", padx=50, pady=50)

        # Logo centered
        if self._logo_image is not None:
            logo_label = ctk.CTkLabel(
                content,
                text="",
                image=self._logo_image,
            )
            logo_label.pack(pady=(0, 12))

        subtitle_label = ctk.CTkLabel(
            content,
            text="Welcome back. Please sign in to continue.",
            font=("Segoe UI", 13),
            text_color=("gray40", "gray75"),
        )
        subtitle_label.pack(pady=(0, 32))

        # Fields container
        fields = ctk.CTkFrame(content, fg_color="transparent")
        fields.pack(fill="both", expand=True)

        # Username
        username_label = ctk.CTkLabel(
            fields,
            text="Username",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        username_label.pack(anchor="w", pady=(0, 8))

        username_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Enter your username",
            font=("Segoe UI", 12),
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        username_entry.pack(fill="x", pady=(0, 20))
        username_entry.focus()

        # Password
        password_label = ctk.CTkLabel(
            fields,
            text="Password",
            font=("Segoe UI", 12, "bold"),
            text_color=("gray20", "gray90"),
        )
        password_label.pack(anchor="w", pady=(0, 8))

        password_entry = ctk.CTkEntry(
            fields,
            placeholder_text="Enter your password",
            font=("Segoe UI", 12),
            show="*",
            height=42,
            corner_radius=10,
            border_width=1,
            border_color=("#D0D0D0", "#505050"),
            fg_color=("#FFFFFF", "#3A3A3A"),
        )
        password_entry.pack(fill="x", pady=(0, 24))

        # Login behaviour
        def handle_login() -> None:
            username = username_entry.get().strip()
            password = password_entry.get().strip()
            if not username or not password:
                messagebox.showwarning(
                    "Login Error", "Please enter both username and password."
                )
                return
            # TODO: Backend - Authenticate user credentials against database
            # TODO: Backend - Validate username and password
            # TODO: Backend - Load user session and profile data
            # TODO: Backend - Get employee group/department for work assignment filtering
            # TODO: Backend - Return success/error status and employee group
            
            # Example backend integration:
            # auth_result = self.controller.authenticate_user(username, password)
            # if auth_result.get("success"):
            #     self.controller.current_user["group"] = auth_result.get("group")
            #     self.controller.available_works = auth_result.get("available_works", [])
            #     self.controller.show_main_menu()
            # else:
            #     messagebox.showerror("Login Failed", "Invalid username or password.")
            
            # For now, set default group (remove when backend is integrated)
            self.controller.current_user["group"] = "Engineering"
            self.controller.available_works = [
                {"id": "W001", "name": "Work 1 - GA Drawing Analysis"},
                {"id": "W002", "name": "Work 2 - Equipment Inspection"},
                {"id": "W003", "name": "Work 3 - Component Verification"},
            ]
            self.controller.current_work = self.controller.available_works[0] if self.controller.available_works else None
            self.controller.show_main_menu()

        # Primary button with glass effect
        login_btn = ctk.CTkButton(
            fields,
            text="Sign in",
            command=handle_login,
            height=46,
            font=("Segoe UI", 13, "bold"),
            corner_radius=12,
            border_width=1,
            border_color=("#6496FF", "#6496FF"),
        )
        login_btn.pack(fill="x", pady=(0, 12))

        # Secondary action
        register_btn = ctk.CTkButton(
            fields,
            text="Don't have an account? Create one",
            command=self.controller.show_registration,
            height=36,
            font=("Segoe UI", 11),
            fg_color="transparent",
            text_color=("gray40", "gray70"),
            hover_color=("#E8E8E8", "#404040"),
            border_width=0,
        )
        register_btn.pack(fill="x", pady=(0, 0))

        # Bind Enter key to login
        password_entry.bind("<Return>", lambda _event: handle_login())
