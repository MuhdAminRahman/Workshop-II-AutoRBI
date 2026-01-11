"""Notification system for AutoRBI application."""

from typing import Optional, List, Dict, Any
from datetime import datetime
import customtkinter as ctk


class NotificationSystem:
    """Manages notifications and alerts in the application."""

    def __init__(self, parent: ctk.CTk):
        self.parent = parent
        self.notifications: List[Dict[str, Any]] = []
        self.notification_container: Optional[ctk.CTkFrame] = None
        self.max_notifications = 5

    def show_notification(
        self,
        message: str,
        notification_type: str = "info",
        duration: int = 5000,
        action_callback: Optional[callable] = None,
    ) -> None:
        """Show a notification toast.
        
        Args:
            message: Notification message
            notification_type: "success", "error", "warning", "info"
            duration: Display duration in milliseconds
            action_callback: Optional callback function
            
        TODO: Backend - Can send real-time notifications via callback
        TODO: Backend - Log notification events for analytics
        """
        try:
            # Check if parent window still exists
            if not self.parent.winfo_exists():
                return
                
            notification = {
                "id": len(self.notifications),
                "message": message,
                "type": notification_type,
                "timestamp": datetime.now(),
                "action": action_callback,
            }
            self.notifications.insert(0, notification)
            
            # Keep only recent notifications
            if len(self.notifications) > self.max_notifications:
                self.notifications = self.notifications[:self.max_notifications]
            
            self._display_notification(notification, duration)
            
        except Exception as e:
            # Don't crash the app if notification fails - it's non-critical
            print(f"Warning: Could not show notification: {e}")

    def _display_notification(self, notification: Dict[str, Any], duration: int) -> None:
        """Display a single notification toast."""
        try:
            # Check if parent still exists before creating widgets
            if not self.parent.winfo_exists():
                return
                
            # Create notification container if it doesn't exist
            if self.notification_container is None:
                self.notification_container = ctk.CTkFrame(
                    self.parent,
                    corner_radius=0,
                    fg_color="transparent",
                )
                self.notification_container.place(relx=1.0, rely=0.0, anchor="ne", x=-20, y=20)
                self.notification_container.grid_columnconfigure(0, weight=1)
            
            # Double-check container still exists after creation
            if not self.notification_container.winfo_exists():
                return

            # Color scheme based on type
            colors = {
                "success": ("#10B981", "#059669", "#D1FAE5"),
                "error": ("#EF4444", "#DC2626", "#FEE2E2"),
                "warning": ("#F59E0B", "#D97706", "#FEF3C7"),
                "info": ("#3B82F6", "#2563EB", "#DBEAFE"),
            }
            bg_color, border_color, icon_bg = colors.get(notification["type"], colors["info"])

            # Notification frame
            notif_frame = ctk.CTkFrame(
                self.notification_container,
                corner_radius=12,
                border_width=1,
                border_color=border_color,
                fg_color=bg_color,
                width=350,
            )
            notif_frame.grid(row=len(self.notification_container.winfo_children()), column=0, pady=(0, 10), sticky="ew")

            # Icon and message
            content_frame = ctk.CTkFrame(notif_frame, fg_color="transparent")
            content_frame.pack(fill="both", expand=True, padx=16, pady=12)

            # Icon
            icon_text = {
                "success": "✓",
                "error": "✕",
                "warning": "⚠",
                "info": "ℹ",
            }
            icon_label = ctk.CTkLabel(
                content_frame,
                text=icon_text.get(notification["type"], "ℹ"),
                font=("Segoe UI", 16, "bold"),
                text_color="white",
                width=28,
                height=28,
                fg_color=icon_bg,
                corner_radius=14,
            )
            icon_label.pack(side="left", padx=(0, 12))

            # Message
            message_label = ctk.CTkLabel(
                content_frame,
                text=notification["message"],
                font=("Segoe UI", 11),
                text_color="white",
                anchor="w",
                justify="left",
                wraplength=250,
            )
            message_label.pack(side="left", fill="x", expand=True)

            # Close button
            close_btn = ctk.CTkButton(
                content_frame,
                text="×",
                width=24,
                height=24,
                font=("Segoe UI", 16),
                fg_color="transparent",
                text_color="white",
                hover_color=("#FFFFFF", "#FFFFFF"),
                command=lambda: self._remove_notification(notif_frame),
            )
            close_btn.pack(side="right", padx=(8, 0))

            # Auto-remove after duration
            if duration > 0:
                self.parent.after(duration, lambda: self._remove_notification(notif_frame))
                
        except Exception as e:
            # Don't crash if notification display fails
            print(f"Warning: Could not display notification: {e}")

    def _remove_notification(self, frame: ctk.CTkFrame) -> None:
        """Remove a notification from display."""
        if frame.winfo_exists():
            frame.destroy()
        
        # Check if container has any remaining children; if not, destroy the container too
        if (self.notification_container is not None and 
            self.notification_container.winfo_exists() and 
            len(self.notification_container.winfo_children()) == 0):
            self.notification_container.destroy()
            self.notification_container = None

    def get_notifications(self) -> List[Dict[str, Any]]:
        """Get all current notifications."""
        return self.notifications.copy()

    def show_success(self, message: str, duration: int = 5000) -> None:
        """Show a success notification.
        
        Args:
            message: Success message to display
            duration: Display duration in milliseconds
        """
        self.show_notification(message, notification_type="success", duration=duration)
    
    def show_error(self, message: str, duration: int = 5000) -> None:
        """Show an error notification.
        
        Args:
            message: Error message to display
            duration: Display duration in milliseconds
        """
        self.show_notification(message, notification_type="error", duration=duration)
    
    def show_warning(self, message: str, duration: int = 5000) -> None:
        """Show a warning notification.
        
        Args:
            message: Warning message to display
            duration: Display duration in milliseconds
        """
        self.show_notification(message, notification_type="warning", duration=duration)
    
    def show_info(self, message: str, duration: int = 5000) -> None:
        """Show an info notification.
        
        Args:
            message: Info message to display
            duration: Display duration in milliseconds
        """
        self.show_notification(message, notification_type="info", duration=duration)

    def clear_all(self) -> None:
        """Clear all notifications."""
        try:
            self.notifications.clear()
            
            # Check if container exists before clearing
            if self.notification_container is None:
                return
                
            if not self.notification_container.winfo_exists():
                # Container already destroyed, just reset reference
                self.notification_container = None
                return
            
            # Safely destroy all children
            for widget in self.notification_container.winfo_children():
                if widget.winfo_exists():
                    widget.destroy()
                    
        except Exception as e:
            # Even if clearing fails, ensure notifications list is cleared
            print(f"Warning: Error clearing notifications: {e}")
            self.notifications.clear()