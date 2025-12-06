"""Loading states and progress indicators for AutoRBI application."""

from typing import Optional
import customtkinter as ctk


class LoadingOverlay:
    """Full-screen loading overlay with spinner."""

    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self.overlay: Optional[ctk.CTkFrame] = None
        self.progress_bar: Optional[ctk.CTkProgressBar] = None
        self.status_label: Optional[ctk.CTkLabel] = None

    def show(self, message: str = "Loading...", show_progress: bool = False) -> None:
        """Show loading overlay."""
        if self.overlay is not None:
            self.hide()

        self.overlay = ctk.CTkFrame(
            self.parent,
            corner_radius=0,
            fg_color=("#000000", "#000000"),  # Black overlay
        )
        self.overlay.place(relx=0, rely=0, relwidth=1, relheight=1)

        content = ctk.CTkFrame(self.overlay, fg_color="transparent")
        content.place(relx=0.5, rely=0.5, anchor="center")

        # Spinner (animated dots)
        spinner_frame = ctk.CTkFrame(content, fg_color="transparent")
        spinner_frame.pack(pady=(0, 20))

        spinner_label = ctk.CTkLabel(
            spinner_frame,
            text="⏳",
            font=("Segoe UI", 32),
        )
        spinner_label.pack()

        # Status message
        self.status_label = ctk.CTkLabel(
            content,
            text=message,
            font=("Segoe UI", 14),
            text_color=("gray20", "gray90"),
        )
        self.status_label.pack(pady=(0, 10))

        # Progress bar (optional)
        if show_progress:
            self.progress_bar = ctk.CTkProgressBar(
                content,
                width=300,
                height=8,
            )
            self.progress_bar.pack(pady=(0, 10))
            self.progress_bar.set(0)

    def update_progress(self, value: float, message: Optional[str] = None) -> None:
        """Update progress bar (0.0 to 1.0)."""
        if self.progress_bar:
            self.progress_bar.set(value)
        if message and self.status_label:
            self.status_label.configure(text=message)

    def hide(self) -> None:
        """Hide loading overlay."""
        if self.overlay and self.overlay.winfo_exists():
            self.overlay.destroy()
            self.overlay = None
            self.progress_bar = None
            self.status_label = None


class SkeletonLoader:
    """Skeleton screen loader for content placeholders."""

    @staticmethod
    def create_skeleton_card(parent: ctk.CTkFrame, width: int = 300, height: int = 100) -> ctk.CTkFrame:
        """Create a skeleton loading card."""
        skeleton = ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
            fg_color=("gray90", "gray20"),
            width=width,
            height=height,
        )
        
        # Animated shimmer effect (simulated with gradient-like appearance)
        shimmer = ctk.CTkFrame(
            skeleton,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            width=width - 20,
            height=20,
        )
        shimmer.place(relx=0.5, rely=0.3, anchor="center")
        
        shimmer2 = ctk.CTkFrame(
            skeleton,
            corner_radius=8,
            fg_color=("gray85", "gray25"),
            width=width - 40,
            height=16,
        )
        shimmer2.place(relx=0.5, rely=0.5, anchor="center")
        
        return skeleton

