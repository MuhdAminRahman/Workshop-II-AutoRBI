"""User Profile view for AutoRBI application."""

import customtkinter as ctk
from tkinter import messagebox


class ProfileView:
    """Handles the User Profile interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller

    def show(self) -> None:
        """Display the Profile interface."""
        # TODO: Backend - Load user profile data from database
        # TODO: Backend - Fetch user statistics (extractions, reports generated)
        # TODO: Backend - Load profile picture/avatar
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back",
            command=self.controller.show_main_menu,
            width=120,
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
            text="User Profile",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.grid(row=0, column=1, sticky="e")

        # Main content
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        scroll = ctk.CTkScrollableFrame(main_frame, fg_color="transparent")
        scroll.pack(expand=True, fill="both", padx=24, pady=24)

        # Avatar/Profile section
        profile_section = ctk.CTkFrame(scroll, fg_color="transparent")
        profile_section.pack(fill="x", pady=(0, 24))

        # Avatar placeholder
        avatar_frame = ctk.CTkFrame(
            profile_section,
            width=120,
            height=120,
            corner_radius=60,
            fg_color=("gray80", "gray30"),
        )
        avatar_frame.pack(pady=(0, 16))

        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text="👤",
            font=("Segoe UI", 48),
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")

        # User info
        username_label = ctk.CTkLabel(
            profile_section,
            text="John Doe",  # TODO: Backend - Get from backend
            font=("Segoe UI", 20, "bold"),
        )
        username_label.pack(pady=(0, 4))

        role_label = ctk.CTkLabel(
            profile_section,
            text="Engineer",  # TODO: Backend - Get from backend
            font=("Segoe UI", 12),
            text_color=("gray50", "gray70"),
        )
        role_label.pack()

        # Profile details
        details_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        details_frame.pack(fill="x", pady=(0, 24))

        section_title = ctk.CTkLabel(
            details_frame,
            text="Profile Information",
            font=("Segoe UI", 16, "bold"),
        )
        section_title.pack(anchor="w", pady=(0, 16))

        # Fields
        fields = [
            ("Full Name", "John Doe"),
            ("Email", "john.doe@ipetro.com"),
            ("Role", "Engineer"),
            ("Member Since", "Jan 2024"),
        ]

        for field_label, field_value in fields:
            field_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
            field_frame.pack(fill="x", pady=(0, 12))

            label = ctk.CTkLabel(
                field_frame,
                text=f"{field_label}:",
                font=("Segoe UI", 11, "bold"),
            )
            label.pack(side="left", padx=(0, 12))

            value = ctk.CTkLabel(
                field_frame,
                text=field_value,
                font=("Segoe UI", 11),
                text_color=("gray40", "gray80"),
            )
            value.pack(side="left")

        # Edit button
        edit_btn = ctk.CTkButton(
            scroll,
            text="Edit Profile",
            command=lambda: messagebox.showinfo("Info", "Profile editing will be available soon."),
            height=40,
            font=("Segoe UI", 12, "bold"),
        )
        edit_btn.pack(pady=(20, 0))

