"""Main menu view for AutoRBI application (CustomTkinter)."""

import os
from datetime import datetime
from typing import Optional

from PIL import Image
import customtkinter as ctk


class MainMenuView:
    """Handles the main menu interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self._logo_image: Optional[ctk.CTkImage] = self._load_logo()
        self._datetime_label: Optional[ctk.CTkLabel] = None
        self.profile_dropdown_open = False
        self.search_results_frame: Optional[ctk.CTkFrame] = None

    def _load_logo(self) -> Optional[ctk.CTkImage]:
        """Load the iPETRO logo from disk if available."""
        try:
            base_dir = os.path.dirname(__file__)
            logo_path = os.path.join(base_dir, "ipetro.png")
            image = Image.open(logo_path)
            return ctk.CTkImage(image, size=(150, 32))
        except Exception:
            return None

    def _update_datetime(self) -> None:
        """Update the datetime label every second."""
        if self._datetime_label is None:
            return
        now = datetime.now().strftime("%d %b %Y  •  %I:%M:%S %p")
        self._datetime_label.configure(text=now)
        # Schedule next update
        self.parent.after(1000, self._update_datetime)

    def show(self) -> None:
        """Display the main menu interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Root content frame
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with logo, search, datetime, profile, and logout
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        header.grid_columnconfigure(0, weight=0)  # logo
        header.grid_columnconfigure(1, weight=1)  # search
        header.grid_columnconfigure(2, weight=0)  # datetime
        header.grid_columnconfigure(3, weight=0)  # profile/logout

        # Left side: logo on top, small title below
        logo_block = ctk.CTkFrame(header, fg_color="transparent")
        logo_block.grid(row=0, column=0, sticky="w")

        if self._logo_image is not None:
            logo_label = ctk.CTkLabel(
                logo_block,
                text="",
                image=self._logo_image,
            )
            logo_label.pack(anchor="w")

        # Search bar (center)
        search_frame = ctk.CTkFrame(header, fg_color="transparent")
        search_frame.grid(row=0, column=1, sticky="ew", padx=20)

        search_entry = ctk.CTkEntry(
            search_frame,
            placeholder_text="🔍 Search work history, reports, equipment...",
            font=("Segoe UI", 11),
            height=36,
            corner_radius=18,
        )
        search_entry.pack(fill="x", expand=True)
        search_entry.bind("<KeyRelease>", lambda e: self._handle_search(search_entry.get()))

        # Search results dropdown (initially hidden)
        self.search_results_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("white", "gray20"),
        )

        # Center/right: larger date & time
        self._datetime_label = ctk.CTkLabel(
            header,
            text="",
            font=("Segoe UI", 14, "bold"),
            text_color=("gray85", "gray90"),
        )
        self._datetime_label.grid(row=0, column=2, sticky="e", padx=(0, 20))
        self._update_datetime()

        # User profile section (right side)
        profile_section = ctk.CTkFrame(header, fg_color="transparent")
        profile_section.grid(row=0, column=3, sticky="e")

        # Username label (optional - can be hidden)
        username_label = ctk.CTkLabel(
            profile_section,
            text="John Doe",  # TODO: Get from backend
            font=("Segoe UI", 11),
            text_color=("gray60", "gray80"),
        )
        username_label.pack(side="left", padx=(0, 10))

        # Circular profile avatar frame
        avatar_frame = ctk.CTkFrame(
            profile_section,
            width=44,
            height=44,
            corner_radius=22,  # Perfect circle (half of width/height)
            fg_color=("gray80", "gray30"),
            border_width=2,
            border_color=("gray70", "gray40"),
        )
        avatar_frame.pack(side="left", padx=(0, 8))
        
        def on_avatar_click(e):
            """Handle avatar click - stop event propagation."""
            e.widget.focus_set()
            self._toggle_profile_dropdown()
            return "break"  # Stop event propagation
        
        avatar_frame.bind("<Button-1>", on_avatar_click)
        
        # Avatar icon/label inside circle
        avatar_label = ctk.CTkLabel(
            avatar_frame,
            text="👤",
            font=("Segoe UI", 20),
            fg_color="transparent",
        )
        avatar_label.place(relx=0.5, rely=0.5, anchor="center")
        avatar_label.bind("<Button-1>", on_avatar_click)
        
        # Make the frame clickable with hover effect
        def on_enter(e):
            avatar_frame.configure(fg_color=("gray75", "gray35"), border_color=("gray65", "gray45"))
        
        def on_leave(e):
            avatar_frame.configure(fg_color=("gray80", "gray30"), border_color=("gray70", "gray40"))
        
        for widget in [avatar_frame, avatar_label]:
            widget.bind("<Enter>", on_enter)
            widget.bind("<Leave>", on_leave)

        # Profile dropdown menu (initially hidden)
        self.profile_dropdown = ctk.CTkFrame(
            root_frame,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("white", "gray20"),
            width=200,
        )
        # Initially hide the dropdown
        self.profile_dropdown.place_forget()

        # Logout button
        logout_btn = ctk.CTkButton(
            profile_section,
            text="Logout",
            command=self.controller.logout,
            width=100,
            height=36,
            font=("Segoe UI", 10, "bold"),
        )
        logout_btn.pack(side="left")

        # Store reference to profile section for click detection (after widgets are created)
        self.profile_section_ref = profile_section
        self.avatar_frame_ref = avatar_frame
        self.avatar_label_ref = avatar_label
        
        # Bind click outside to close dropdowns (use after a delay to allow dropdown to show)
        def delayed_click_handler(event):
            # Only check for outside clicks if dropdown is open
            if self.profile_dropdown_open:
                self.parent.after(100, lambda: self._handle_click_outside(event))
        root_frame.bind("<Button-1>", delayed_click_handler)

        # Main content area
        main_frame = ctk.CTkFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        main_frame.grid(row=1, column=0, sticky="nsew", pady=(10, 0))

        main_frame.grid_rowconfigure(1, weight=1)
        main_frame.grid_columnconfigure(0, weight=1)

        # Section title
        welcome_label = ctk.CTkLabel(
            main_frame,
            text="Main Menu",
            font=("Segoe UI", 24, "bold"),
        )
        welcome_label.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Choose what you want to work on.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=0, column=0, sticky="w", padx=24, pady=(44, 24))

        # Menu buttons container (grid of cards)
        buttons_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        buttons_frame.grid(row=1, column=0, sticky="nsew", padx=24, pady=(0, 24))

        for col in range(2):
            buttons_frame.grid_columnconfigure(col, weight=1, uniform="menu_col")
        for row in range(2):
            buttons_frame.grid_rowconfigure(row, weight=1)

        # Button configurations
        menu_buttons = [
            ("New Work", "Create and manage new work items.", self.controller.show_new_work),
            ("Report Menu", "Generate and review reports.", self.controller.show_report_menu),
            (
                "Work History Menu",
                "Browse historical work items and activities.",
                self.controller.show_work_history,
            ),
            ("Analytics Dashboard", "View performance and risk analytics.", self.controller.show_analytics),
        ]

        # Create "cards" with button and description
        for idx, (title, description, command) in enumerate(menu_buttons):
            row = idx // 2
            col = idx % 2

            card = ctk.CTkFrame(
                buttons_frame,
                corner_radius=16,
                border_width=1,
                border_color=("gray80", "gray30"),
            )
            card.grid(
                row=row,
                column=col,
                padx=10,
                pady=10,
                sticky="nsew",
            )

            card.grid_rowconfigure(1, weight=1)
            card.grid_columnconfigure(0, weight=1)

            title_lbl = ctk.CTkLabel(
                card,
                text=title,
                font=("Segoe UI", 15, "bold"),
                anchor="w",
            )
            title_lbl.grid(row=0, column=0, sticky="w", padx=18, pady=(14, 4))

            desc_lbl = ctk.CTkLabel(
                card,
                text=description,
                font=("Segoe UI", 11),
                text_color=("gray25", "gray80"),
                anchor="w",
                justify="left",
                wraplength=260,
            )
            desc_lbl.grid(row=1, column=0, sticky="nsew", padx=18, pady=(0, 10))

            action_btn = ctk.CTkButton(
                card,
                text="Open",
                command=command,
                height=32,
                font=("Segoe UI", 10, "bold"),
            )
            action_btn.grid(row=2, column=0, sticky="ew", padx=18, pady=(0, 16))

    def _toggle_profile_dropdown(self) -> None:
        """Toggle profile dropdown menu."""
        if self.profile_dropdown_open:
            self._hide_profile_dropdown()
        else:
            self._show_profile_dropdown()

    def _show_profile_dropdown(self) -> None:
        """Show profile dropdown menu."""
        self.profile_dropdown_open = True
        
        # Clear existing items
        for widget in self.profile_dropdown.winfo_children():
            widget.destroy()

        # Position dropdown below circular avatar
        # Calculate position: right side of window, below header
        window_width = self.parent.winfo_width() or 1100  # Default if not yet rendered
        dropdown_x = window_width - 220  # 200px from right + 20px padding
        self.profile_dropdown.place(x=dropdown_x, y=80, anchor="ne")
        
        # Ensure dropdown is visible and on top of all widgets
        self.profile_dropdown.lift()
        self.profile_dropdown.tkraise()
        self.profile_dropdown.update_idletasks()
        self.parent.update_idletasks()

        # Menu items
        menu_items = [
            ("👤 Profile", lambda: self._navigate_to_profile()),
            ("⚙️ Settings", lambda: self._navigate_to_settings()),
            ("❓ Help", lambda: self._show_help()),
            ("─" * 20, None),
        ]

        for item_text, command in menu_items:
            if item_text.startswith("─"):
                # Separator
                separator = ctk.CTkFrame(
                    self.profile_dropdown,
                    height=1,
                    fg_color=("gray80", "gray30"),
                )
                separator.pack(fill="x", padx=8, pady=4)
            else:
                item_btn = ctk.CTkButton(
                    self.profile_dropdown,
                    text=item_text,
                    command=command if command else None,
                    width=180,
                    height=36,
                    font=("Segoe UI", 11),
                    fg_color="transparent",
                    text_color=("gray20", "gray90"),
                    hover_color=("gray85", "gray30"),
                    anchor="w",
                )
                item_btn.pack(fill="x", padx=8, pady=2)

    def _hide_profile_dropdown(self) -> None:
        """Hide profile dropdown menu."""
        self.profile_dropdown_open = False
        if self.profile_dropdown.winfo_exists():
            self.profile_dropdown.place_forget()

    def _navigate_to_profile(self) -> None:
        """Navigate to profile page."""
        self._hide_profile_dropdown()
        if hasattr(self.controller, 'show_profile'):
            self.controller.show_profile()
        else:
            import tkinter.messagebox as mb
            mb.showinfo("Info", "Profile page will be available soon.")

    def _navigate_to_settings(self) -> None:
        """Navigate to settings page."""
        self._hide_profile_dropdown()
        if hasattr(self.controller, 'show_settings'):
            self.controller.show_settings()
        else:
            import tkinter.messagebox as mb
            mb.showinfo("Info", "Settings page will be available soon.")

    def _show_help(self) -> None:
        """Show help dialog."""
        self._hide_profile_dropdown()
        import tkinter.messagebox as mb
        mb.showinfo(
            "Help",
            "AutoRBI Help\n\n"
            "• New Work: Upload and process equipment drawings\n"
            "• Report Menu: View and export generated reports\n"
            "• Work History: Browse past work activities\n"
            "• Analytics: View performance metrics\n\n"
            "Keyboard Shortcuts:\n"
            "Ctrl+N - New Work\n"
            "Ctrl+R - Reports\n"
            "Ctrl+H - History\n"
            "Ctrl+A - Analytics"
        )

    def _handle_search(self, query: str) -> None:
        """Handle search input."""
        if not query or len(query) < 2:
            self._hide_search_results()
            return

        # Show search results
        self._show_search_results(query)

    def _show_search_results(self, query: str) -> None:
        """Show search results dropdown."""
        # Clear existing results
        for widget in self.search_results_frame.winfo_children():
            widget.destroy()

        # Position results below search bar
        self.search_results_frame.place(relx=0.5, y=100, anchor="n", relwidth=0.6)

        # Header
        header_label = ctk.CTkLabel(
            self.search_results_frame,
            text=f"Search results for '{query}'",
            font=("Segoe UI", 11, "bold"),
        )
        header_label.pack(pady=(12, 8), padx=12)

        # TODO: Get actual search results from backend
        # For now, show placeholder results
        results = [
            ("📄 Report: Equipment Analysis", "Report Menu"),
            ("📊 Work: V-001 Extraction", "Work History"),
            ("🔧 Equipment: E-1002", "Equipment Database"),
        ]

        for result_text, category in results[:5]:  # Limit to 5 results
            result_btn = ctk.CTkButton(
                self.search_results_frame,
                text=f"{result_text} ({category})",
                command=lambda c=category: self._navigate_from_search(c),
                width=300,
                height=32,
                font=("Segoe UI", 10),
                fg_color="transparent",
                text_color=("gray20", "gray90"),
                hover_color=("gray85", "gray30"),
                anchor="w",
            )
            result_btn.pack(fill="x", padx=12, pady=2)

        # No results message if empty
        if not results:
            no_results = ctk.CTkLabel(
                self.search_results_frame,
                text="No results found",
                font=("Segoe UI", 10),
                text_color=("gray50", "gray70"),
            )
            no_results.pack(pady=12)

    def _hide_search_results(self) -> None:
        """Hide search results dropdown."""
        if self.search_results_frame.winfo_exists():
            self.search_results_frame.place_forget()

    def _navigate_from_search(self, category: str) -> None:
        """Navigate to search result category."""
        self._hide_search_results()
        if category == "Report Menu":
            self.controller.show_report_menu()
        elif category == "Work History":
            self.controller.show_work_history()
        # Add more navigation as needed

    def _handle_click_outside(self, event) -> None:
        """Handle clicks outside dropdowns to close them."""
        if not self.profile_dropdown_open:
            return
        
        # Don't close if clicking on avatar or profile section
        try:
            widget = event.widget
            # Check if click is on avatar frame, avatar label, or profile section
            if (hasattr(self, 'avatar_frame_ref') and 
                (widget == self.avatar_frame_ref or 
                 str(widget).find('avatar') != -1 or
                 widget.master == self.avatar_frame_ref or
                 widget.master == self.profile_section_ref)):
                return
        except:
            pass
            
        # Check if click is outside profile dropdown
        if self.profile_dropdown.winfo_exists():
            try:
                # Get click coordinates
                x = event.x_root
                y = event.y_root
                
                # Get dropdown position and size (absolute coordinates)
                dropdown_x = self.profile_dropdown.winfo_rootx()
                dropdown_y = self.profile_dropdown.winfo_rooty()
                dropdown_w = self.profile_dropdown.winfo_width()
                dropdown_h = self.profile_dropdown.winfo_height()
                
                # Check if click is outside dropdown
                if not (dropdown_x <= x <= dropdown_x + dropdown_w and 
                       dropdown_y <= y <= dropdown_y + dropdown_h):
                    self._hide_profile_dropdown()
            except Exception:
                # If any error, just hide the dropdown
                try:
                    self._hide_profile_dropdown()
                except:
                    pass

        # Check if click is outside search results
        if self.search_results_frame and self.search_results_frame.winfo_exists():
            try:
                x, y = event.x_root, event.y_root
                results_x = self.search_results_frame.winfo_x()
                results_y = self.search_results_frame.winfo_y()
                results_w = self.search_results_frame.winfo_width()
                results_h = self.search_results_frame.winfo_height()
                
                if not (results_x <= x <= results_x + results_w and 
                       results_y <= y <= results_y + results_h):
                    self._hide_search_results()
            except:
                pass
