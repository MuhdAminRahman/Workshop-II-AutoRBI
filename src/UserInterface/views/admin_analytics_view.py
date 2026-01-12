"""Admin Analytics Dashboard - User Performance & Team Metrics."""

from typing import Dict, List, Optional
import customtkinter as ctk


class AdminAnalyticsView:
    """
    Admin-only dashboard for user performance analytics.

    Features:
    - Individual user performance summaries
    - Team comparison and leaderboards
    - Productivity insights (hourly/daily patterns)
    - Time tracking per work
    """

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.current_period = "last_7_days"
        self.selected_user_id = None

    def show(self, selected_user_id: Optional[int] = None) -> None:
        """Display Admin Analytics Dashboard.

        Args:
            selected_user_id: If provided, show details for this specific user
        """
        # Store selected user ID
        if selected_user_id is not None:
            self.selected_user_id = selected_user_id

        # Clear parent
        for widget in self.parent.winfo_children():
            widget.destroy()

        # Root container
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)
        root_frame.grid_rowconfigure(2, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # HEADER
        self._build_header(root_frame)

        # PERIOD FILTER
        self._build_period_filter(root_frame)

        # MAIN CONTENT (Scrollable)
        self.content_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=0,
            border_width=0,
            fg_color="transparent",
        )
        self.content_container.grid(row=2, column=0, sticky="nsew")
        self.content_container.grid_columnconfigure(0, weight=1)

        # Load initial data - if selected_user_id provided, go directly to user details
        if self.selected_user_id is not None:
            self._show_user_details(self.selected_user_id)
            # Reset after showing
            self.selected_user_id = None
        else:
            self._load_team_analytics()

    def _build_header(self, parent):
        """Build header with title and back button."""
        header = ctk.CTkFrame(parent, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 24))
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back",
            command=self.controller.show_admin_menu,
            width=100,
            height=36,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray40", "gray80"),
            hover_color=("gray85", "gray30"),
            border_width=0,
        )
        back_btn.pack(side="left")

        title_label = ctk.CTkLabel(
            header,
            text="👥 User Performance Analytics",
            font=("Segoe UI", 26, "bold"),
        )
        title_label.pack(side="right")

    def _build_period_filter(self, parent):
        """Build period selection filter."""
        filter_frame = ctk.CTkFrame(parent, fg_color="transparent")
        filter_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        label = ctk.CTkLabel(
            filter_frame,
            text="Time Period:",
            font=("Segoe UI", 12, "bold"),
        )
        label.pack(side="left", padx=(0, 12))

        period_var = ctk.StringVar(value="Last 7 Days")
        period_dropdown = ctk.CTkComboBox(
            filter_frame,
            values=["Today", "Last 7 Days", "Last Month", "All Time"],
            variable=period_var,
            command=self._on_period_changed,
            width=180,
            height=36,
            font=("Segoe UI", 11),
        )
        period_dropdown.pack(side="left")

        refresh_btn = ctk.CTkButton(
            filter_frame,
            text="🔄 Refresh",
            command=self._refresh_all,
            width=120,
            height=36,
            font=("Segoe UI", 11),
            fg_color="#3498db",
            hover_color="#2980b9",
        )
        refresh_btn.pack(side="right")

    def _on_period_changed(self, choice: str):
        """Handle period filter change."""
        period_map = {
            "Today": "today",
            "Last 7 Days": "last_7_days",
            "Last Month": "last_month",
            "All Time": "all"
        }
        self.current_period = period_map.get(choice, "last_7_days")
        self._load_team_analytics()

    def _load_team_analytics(self):
        """Load and display team-wide analytics."""
        # Clear content
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Fetch team data
        result = self.controller.get_team_analytics(self.current_period)

        if not result.get("success"):
            self._show_error(result.get("message", "Failed to load analytics"))
            return

        team_data = result.get("data", [])
        summary = result.get("summary", {})

        # SECTION 1: Team Summary Card
        self._build_team_summary_card(self.content_container, summary)

        # SECTION 2: Team Performance Table
        self._build_team_performance_table(self.content_container, team_data)

    def _build_team_summary_card(self, parent, summary: Dict):
        """Build team summary statistics card."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=0,
            fg_color=("white", "gray17"),
        )
        card.pack(fill="x", pady=(0, 24))
        card.grid_columnconfigure((0, 1, 2, 3), weight=1)

        title = ctk.CTkLabel(
            card,
            text="📊 Team Overview",
            font=("Segoe UI", 14, "bold"),
        )
        title.grid(row=0, column=0, columnspan=4, sticky="w", padx=24, pady=(20, 16))

        # Metrics
        metrics = [
            ("Total Engineers", summary.get("total_engineers", 0), "#3498db"),
            ("Total Actions", summary.get("total_team_actions", 0), "#9b59b6"),
            ("Equipment Extracted", summary.get("total_equipment_extracted", 0), "#2ecc71"),
            ("Avg Time per Equipment", f"{summary.get('team_avg_time_per_equipment', 0)} min", "#f39c12"),
        ]

        for i, (label, value, color) in enumerate(metrics):
            metric_frame = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=10)
            metric_frame.grid(row=1, column=i, sticky="ew", padx=12, pady=(0, 20))

            value_label = ctk.CTkLabel(
                metric_frame,
                text=str(value),
                font=("Segoe UI", 24, "bold"),
                text_color=color,
            )
            value_label.pack(pady=(14, 4))

            label_widget = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=("Segoe UI", 10),
                text_color=("gray60", "gray80"),
            )
            label_widget.pack(pady=(0, 14))

    def _build_team_performance_table(self, parent, team_data: List[Dict]):
        """Build team performance comparison table."""
        section = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=0,
            fg_color=("white", "gray17"),
        )
        section.pack(fill="both", expand=True)

        title = ctk.CTkLabel(
            section,
            text="🏆 Team Performance Leaderboard",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(anchor="w", padx=24, pady=(20, 16))

        if not team_data:
            no_data = ctk.CTkLabel(
                section,
                text="No user activity data available for this period.",
                font=("Segoe UI", 12),
                text_color=("gray60", "gray80"),
            )
            no_data.pack(pady=40)
            return

        # Table container
        table_container = ctk.CTkFrame(section, fg_color="transparent")
        table_container.pack(fill="both", expand=True, padx=18, pady=(0, 20))

        # Header row
        header_row = ctk.CTkFrame(
            table_container,
            fg_color=("gray90", "gray25"),
            corner_radius=8,
        )
        header_row.pack(fill="x", pady=(0, 8))
        header_row.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        headers = ["Rank", "Engineer", "Total Actions", "Equipment", "Avg Time", "Details"]
        for i, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_row,
                text=header,
                font=("Segoe UI", 11, "bold"),
                text_color=("gray40", "gray80"),
            )
            label.grid(row=0, column=i, padx=12, pady=12)

        # Data rows (sorted by total actions descending)
        sorted_team_data = sorted(
            team_data,
            key=lambda x: x.get("total_actions", 0),
            reverse=True
        )

        for rank, user_data in enumerate(sorted_team_data, start=1):
            self._build_user_row(table_container, rank, user_data)

    def _build_user_row(self, parent, rank: int, user_data: Dict):
        """Build a single user performance row."""
        row_frame = ctk.CTkFrame(
            parent,
            fg_color=("white", "gray20"),
            corner_radius=8,
            border_width=1,
            border_color=("gray85", "gray30"),
        )
        row_frame.pack(fill="x", pady=(0, 6))
        row_frame.grid_columnconfigure((0, 1, 2, 3, 4, 5), weight=1)

        # Rank badge
        rank_color = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}.get(rank, ("gray60", "gray80"))
        rank_label = ctk.CTkLabel(
            row_frame,
            text=f"#{rank}",
            font=("Segoe UI", 12, "bold"),
            text_color=rank_color,
        )
        rank_label.grid(row=0, column=0, padx=12, pady=12)

        # Engineer name
        name_label = ctk.CTkLabel(
            row_frame,
            text=user_data.get("full_name", user_data.get("username", "-")),
            font=("Segoe UI", 11),
            anchor="w",
        )
        name_label.grid(row=0, column=1, sticky="w", padx=12, pady=12)

        # Total actions
        actions_label = ctk.CTkLabel(
            row_frame,
            text=str(user_data.get("total_actions", 0)),
            font=("Segoe UI", 11, "bold"),
            text_color="#3498db",
        )
        actions_label.grid(row=0, column=2, padx=12, pady=12)

        # Equipment extracted
        equipment_label = ctk.CTkLabel(
            row_frame,
            text=str(user_data.get("equipment_extracted", 0)),
            font=("Segoe UI", 11, "bold"),
            text_color="#2ecc71",
        )
        equipment_label.grid(row=0, column=3, padx=12, pady=12)

        # Average time per equipment
        avg_time = user_data.get("avg_time_per_equipment_minutes", 0)
        time_label = ctk.CTkLabel(
            row_frame,
            text=f"{avg_time:.1f} min" if avg_time > 0 else "-",
            font=("Segoe UI", 11),
            text_color="#f39c12",
        )
        time_label.grid(row=0, column=4, padx=12, pady=12)

        # Details button
        details_btn = ctk.CTkButton(
            row_frame,
            text="View Details",
            command=lambda: self._show_user_details(user_data.get("user_id")),
            width=100,
            height=28,
            font=("Segoe UI", 10),
            fg_color="#3498db",
            hover_color="#2980b9",
        )
        details_btn.grid(row=0, column=5, padx=12, pady=12)

    def _show_user_details(self, user_id: int):
        """Show detailed analytics for a specific user."""
        # Clear content
        for widget in self.content_container.winfo_children():
            widget.destroy()

        # Add back button
        back_frame = ctk.CTkFrame(self.content_container, fg_color="transparent")
        back_frame.pack(fill="x", pady=(0, 20))

        back_to_team_btn = ctk.CTkButton(
            back_frame,
            text="← Back to Team View",
            command=self._load_team_analytics,
            width=150,
            height=32,
            font=("Segoe UI", 10),
            fg_color="transparent",
            text_color=("gray40", "gray80"),
            hover_color=("gray85", "gray30"),
            border_width=1,
            border_color=("gray70", "gray50"),
        )
        back_to_team_btn.pack(side="left")

        # Fetch user performance data
        result = self.controller.get_user_performance_analytics(user_id, self.current_period)

        if not result.get("success"):
            self._show_error(result.get("message", "Failed to load user analytics"))
            return

        user_data = result.get("data", {})

        # User header
        user_header = ctk.CTkFrame(self.content_container, fg_color="transparent")
        user_header.pack(fill="x", pady=(0, 24))

        user_title = ctk.CTkLabel(
            user_header,
            text=f"👤 {user_data.get('full_name', 'User')}",
            font=("Segoe UI", 20, "bold"),
        )
        user_title.pack(anchor="w")

        user_subtitle = ctk.CTkLabel(
            user_header,
            text=f"{user_data.get('username', '')} • {user_data.get('role', '')}",
            font=("Segoe UI", 12),
            text_color=("gray60", "gray80"),
        )
        user_subtitle.pack(anchor="w", pady=(4, 0))

        # Performance metrics card
        self._build_user_performance_card(self.content_container, user_data)

        # Productivity insights
        self._load_productivity_insights(self.content_container, user_id)

    def _build_user_performance_card(self, parent, user_data: Dict):
        """Build user performance metrics card."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=0,
            fg_color=("white", "gray17"),
        )
        card.pack(fill="x", pady=(0, 24))
        card.grid_columnconfigure((0, 1, 2), weight=1)

        title = ctk.CTkLabel(
            card,
            text="📈 Performance Summary",
            font=("Segoe UI", 14, "bold"),
        )
        title.grid(row=0, column=0, columnspan=3, sticky="w", padx=24, pady=(20, 16))

        # Row 1 metrics
        # Format duration: show minutes if < 1 hour, otherwise show hours
        duration_hours = user_data.get('total_duration_hours', 0)
        duration_minutes = user_data.get('total_duration_minutes', 0)

        if duration_hours < 1 and duration_minutes > 0:
            duration_display = f"{duration_minutes:.0f} min"
        elif duration_hours >= 1:
            duration_display = f"{duration_hours:.1f} hrs"
        else:
            duration_display = "0 min"

        metrics_row1 = [
            ("Total Actions", user_data.get("total_actions", 0), "#3498db"),
            ("Equipment Extracted", user_data.get("equipment_extracted", 0), "#2ecc71"),
            ("Duration", duration_display, "#9b59b6"),
        ]

        for i, (label, value, color) in enumerate(metrics_row1):
            metric_frame = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=10)
            metric_frame.grid(row=1, column=i, sticky="ew", padx=12, pady=(0, 12))

            value_label = ctk.CTkLabel(
                metric_frame,
                text=str(value),
                font=("Segoe UI", 20, "bold"),
                text_color=color,
            )
            value_label.pack(pady=(12, 4))

            label_widget = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=("Segoe UI", 10),
                text_color=("gray60", "gray80"),
            )
            label_widget.pack(pady=(0, 12))

        # Row 2: Action breakdown
        action_breakdown = user_data.get("action_breakdown", {})

        breakdown_frame = ctk.CTkFrame(card, fg_color="transparent")
        breakdown_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=24, pady=(8, 20))

        breakdown_title = ctk.CTkLabel(
            breakdown_frame,
            text="Action Breakdown:",
            font=("Segoe UI", 11, "bold"),
            text_color=("gray60", "gray80"),
        )
        breakdown_title.pack(anchor="w", pady=(0, 8))

        for action_type, count in action_breakdown.items():
            action_row = ctk.CTkFrame(breakdown_frame, fg_color=("gray90", "gray20"), corner_radius=6)
            action_row.pack(fill="x", pady=2)

            action_label = ctk.CTkLabel(
                action_row,
                text=action_type.replace("_", " ").title(),
                font=("Segoe UI", 10),
            )
            action_label.pack(side="left", padx=12, pady=8)

            count_label = ctk.CTkLabel(
                action_row,
                text=str(count),
                font=("Segoe UI", 10, "bold"),
                text_color="#3498db",
            )
            count_label.pack(side="right", padx=12, pady=8)

    def _load_productivity_insights(self, parent, user_id: int):
        """Load and display productivity insights."""
        result = self.controller.get_productivity_analytics(user_id, self.current_period)

        if not result.get("success"):
            return

        insights_data = result.get("data", {})
        hourly_data = insights_data.get("hourly_productivity", [])
        daily_data = insights_data.get("daily_activity", [])
        peak_hours = insights_data.get("peak_hours", {})
        insights = insights_data.get("insights", {})

        # Productivity insights card
        card = ctk.CTkFrame(
            parent,
            corner_radius=14,
            border_width=0,
            fg_color=("white", "gray17"),
        )
        card.pack(fill="x", pady=(0, 24))

        title = ctk.CTkLabel(
            card,
            text="⏰ Productivity Insights",
            font=("Segoe UI", 14, "bold"),
        )
        title.pack(anchor="w", padx=24, pady=(20, 16))

        # Insights summary
        summary_frame = ctk.CTkFrame(card, fg_color="transparent")
        summary_frame.pack(fill="x", padx=24, pady=(0, 16))
        summary_frame.grid_columnconfigure((0, 1, 2), weight=1)

        insights_metrics = [
            ("Total Active Days", insights.get("total_days_active", 0)),
            ("Avg Actions/Day", insights.get("avg_actions_per_day", 0)),
            ("Most Active Day", insights.get("most_active_day", "-")),
        ]

        for i, (label, value) in enumerate(insights_metrics):
            metric_frame = ctk.CTkFrame(summary_frame, fg_color=("gray90", "gray20"), corner_radius=8)
            metric_frame.grid(row=0, column=i, sticky="ew", padx=6)

            value_label = ctk.CTkLabel(
                metric_frame,
                text=str(value),
                font=("Segoe UI", 16, "bold"),
                text_color="#3498db",
            )
            value_label.pack(pady=(10, 4))

            label_widget = ctk.CTkLabel(
                metric_frame,
                text=label,
                font=("Segoe UI", 9),
                text_color=("gray60", "gray80"),
            )
            label_widget.pack(pady=(0, 10))

        # Peak hours
        if peak_hours:
            peak_frame = ctk.CTkFrame(card, fg_color=("gray90", "gray20"), corner_radius=8)
            peak_frame.pack(fill="x", padx=24, pady=(0, 20))

            peak_title = ctk.CTkLabel(
                peak_frame,
                text=f"🔥 Most Productive Hour: {peak_hours.get('most_productive_hour', '-')}:00 ({peak_hours.get('most_productive_count', 0)} actions)",
                font=("Segoe UI", 11, "bold"),
                text_color="#f39c12",
            )
            peak_title.pack(pady=12)

    def _show_error(self, message: str):
        """Display error message."""
        error_label = ctk.CTkLabel(
            self.content_container,
            text=f"❌ {message}",
            font=("Segoe UI", 12),
            text_color="#e74c3c",
        )
        error_label.pack(pady=40)

    def _refresh_all(self):
        """Refresh all analytics data."""
        self._load_team_analytics()
