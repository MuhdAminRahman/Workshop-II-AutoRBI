"""
Tooltip Component
Provides hover tooltips for truncated text and other UI elements.
"""

import customtkinter as ctk
from typing import Optional


class Tooltip:
    """
    Creates a tooltip for a given widget.
    
    Usage:
        label = ctk.CTkLabel(parent, text="Short...")
        Tooltip(label, "This is the full text that was truncated")
    """
    
    def __init__(
        self, 
        widget: ctk.CTkBaseClass, 
        text: str,
        delay: int = 500,
        wrap_length: int = 300
    ):
        """
        Initialize tooltip.
        
        Args:
            widget: The widget to attach tooltip to
            text: Tooltip text to display
            delay: Delay in ms before showing tooltip
            wrap_length: Maximum width before text wraps
        """
        self.widget = widget
        self.text = text
        self.delay = delay
        self.wrap_length = wrap_length
        self.tooltip_window: Optional[ctk.CTkToplevel] = None
        self.scheduled_id: Optional[str] = None
        
        # Bind events
        self.widget.bind("<Enter>", self._on_enter)
        self.widget.bind("<Leave>", self._on_leave)
        self.widget.bind("<Button-1>", self._on_leave)
    
    def _on_enter(self, event=None):
        """Schedule tooltip display."""
        self._cancel_scheduled()
        self.scheduled_id = self.widget.after(self.delay, self._show_tooltip)
    
    def _on_leave(self, event=None):
        """Hide tooltip and cancel scheduled display."""
        self._cancel_scheduled()
        self._hide_tooltip()
    
    def _cancel_scheduled(self):
        """Cancel any scheduled tooltip display."""
        if self.scheduled_id:
            self.widget.after_cancel(self.scheduled_id)
            self.scheduled_id = None
    
    def _show_tooltip(self):
        """Display the tooltip."""
        if self.tooltip_window or not self.text:
            return
        
        try:
            # Check if widget still exists
            if not self.widget.winfo_exists():
                return
            
            # Get widget position
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
            
            # Create tooltip window
            self.tooltip_window = ctk.CTkToplevel(self.widget)
            self.tooltip_window.wm_overrideredirect(True)
            self.tooltip_window.wm_geometry(f"+{x}+{y}")
            
            # Tooltip frame
            frame = ctk.CTkFrame(
                self.tooltip_window,
                corner_radius=6,
                fg_color=("gray20", "gray80"),
                border_width=1,
                border_color=("gray40", "gray60"),
            )
            frame.pack(fill="both", expand=True)
            
            # Tooltip label
            label = ctk.CTkLabel(
                frame,
                text=self.text,
                font=("Segoe UI", 10),
                text_color=("white", "black"),
                wraplength=self.wrap_length,
                justify="left",
            )
            label.pack(padx=8, pady=6)
            
            # Keep tooltip on top
            self.tooltip_window.lift()
            
        except Exception:
            # Silently fail if tooltip can't be created
            self._hide_tooltip()
    
    def _hide_tooltip(self):
        """Hide and destroy the tooltip."""
        if self.tooltip_window:
            try:
                self.tooltip_window.destroy()
            except Exception:
                pass
            self.tooltip_window = None
    
    def update_text(self, new_text: str):
        """Update tooltip text."""
        self.text = new_text


class ConditionalTooltip(Tooltip):
    """
    Tooltip that only shows if text was truncated.
    
    Usage:
        ConditionalTooltip(label, full_text="Very long text...", display_text="Very...")
    """
    
    def __init__(
        self,
        widget: ctk.CTkBaseClass,
        full_text: str,
        display_text: str,
        **kwargs
    ):
        """
        Initialize conditional tooltip.
        
        Args:
            widget: The widget to attach tooltip to
            full_text: The complete text
            display_text: The truncated text being displayed
            **kwargs: Additional arguments passed to Tooltip
        """
        # Only create functional tooltip if text was actually truncated
        if full_text != display_text:
            super().__init__(widget, full_text, **kwargs)
        else:
            # Store references but don't bind events
            self.widget = widget
            self.text = ""
            self.tooltip_window = None
            self.scheduled_id = None