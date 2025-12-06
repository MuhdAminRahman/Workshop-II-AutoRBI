"""Analytics Dashboard view for AutoRBI application (CustomTkinter)."""

from typing import Optional, Dict, Any
import customtkinter as ctk


class AnalyticsView:
    """Handles the Analytics Dashboard interface."""

    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.current_period: str = "all_time"
        self.kpi_cards: Dict[str, ctk.CTkFrame] = {}

    def update_metrics(self, metrics: Dict[str, Any]) -> None:
        """Update KPI cards with new metric values.
        
        metrics dict can contain keys like:
        {"total_works": int, "success_rate": float, "avg_time": float, "total_files": int}
        """
        if "total_works" in metrics and "total_works_card" in self.kpi_cards:
            card = self.kpi_cards["total_works_card"]
            for widget in card.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("font")[0] == "Segoe UI" and widget.cget("font")[1] == 20:
                    widget.configure(text=str(metrics["total_works"]))
        
        if "success_rate" in metrics and "success_rate_card" in self.kpi_cards:
            card = self.kpi_cards["success_rate_card"]
            for widget in card.winfo_children():
                if isinstance(widget, ctk.CTkLabel) and widget.cget("font")[0] == "Segoe UI" and widget.cget("font")[1] == 20:
                    widget.configure(text=f"{metrics['success_rate']:.1f}%")
        
        # TODO: Update other cards similarly

    def _change_period(self, period: str) -> None:
        """Change analytics time period (button-based, no input fields)."""
        self.current_period = period
        # TODO: Reload analytics data for selected period
        # self.controller.load_analytics(period)

    def _create_kpi_card(self, parent: ctk.CTkFrame, title: str, value: str, key: str, row: int, col: int) -> None:
        """Create a KPI metric card."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        card.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=("Segoe UI", 11),
            text_color=("gray50", "gray70"),
        )
        title_label.pack(pady=(12, 4))

        value_label = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 20, "bold"),
        )
        value_label.pack(pady=(0, 12))

        self.kpi_cards[key] = card

    def show(self) -> None:
        """Display the Analytics Dashboard interface."""
        # Clear existing widgets
        for widget in self.parent.winfo_children():
            widget.destroy()

        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)

        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)

        # Header with back button
        header = ctk.CTkFrame(root_frame, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        back_btn = ctk.CTkButton(
            header,
            text="← Back to Main Menu",
            command=self.controller.show_main_menu,
            width=180,
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
            text="AutoRBI",
            font=("Segoe UI", 24, "bold"),
        )
        title_label.grid(row=0, column=1, sticky="e")

        # Scrollable main content area
        scroll_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        scroll_container.grid(row=1, column=0, sticky="nsew", pady=(12, 0))

        main_frame = scroll_container
        main_frame.grid_columnconfigure(0, weight=1)

        page_title = ctk.CTkLabel(
            main_frame,
            text="Analytics Dashboard",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))

        subtitle_label = ctk.CTkLabel(
            main_frame,
            text="Monitor performance metrics and extraction statistics.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle_label.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))

        # Period selector buttons (no input fields)
        period_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        period_section.grid(row=2, column=0, sticky="ew", padx=24, pady=(0, 18))

        period_label = ctk.CTkLabel(
            period_section,
            text="Time period:",
            font=("Segoe UI", 10, "bold"),
        )
        period_label.pack(side="left", padx=(0, 8))

        period_buttons = [
            ("All time", "all_time"),
            ("Last month", "last_month"),
            ("Last week", "last_week"),
            ("Today", "today"),
        ]
        for label, period_key in period_buttons:
            btn = ctk.CTkButton(
                period_section,
                text=label,
                width=100,
                height=28,
                font=("Segoe UI", 9),
                fg_color=("gray20", "gray30") if self.current_period != period_key else None,
                command=lambda p=period_key: self._change_period(p),
            )
            btn.pack(side="left", padx=(0, 6))

        # KPI cards row
        kpi_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        kpi_section.grid(row=3, column=0, sticky="ew", padx=24, pady=(0, 18))
        kpi_section.grid_columnconfigure(0, weight=1)
        kpi_section.grid_columnconfigure(1, weight=1)
        kpi_section.grid_columnconfigure(2, weight=1)
        kpi_section.grid_columnconfigure(3, weight=1)

        self._create_kpi_card(kpi_section, "Total Works", "0", "total_works_card", 0, 0)
        self._create_kpi_card(kpi_section, "Success Rate", "0%", "success_rate_card", 0, 1)
        self._create_kpi_card(kpi_section, "Avg Time", "0s", "avg_time_card", 0, 2)
        self._create_kpi_card(kpi_section, "Total Files", "0", "total_files_card", 0, 3)

        # Charts section (2 columns)
        charts_section = ctk.CTkFrame(main_frame, fg_color="transparent")
        charts_section.grid(row=4, column=0, sticky="ew", padx=24, pady=(0, 18))
        charts_section.grid_columnconfigure(0, weight=1)
        charts_section.grid_columnconfigure(1, weight=1)

        # Chart 1: Works over time
        chart1_card = ctk.CTkFrame(
            charts_section,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        chart1_card.grid(row=0, column=0, padx=(0, 8), pady=8, sticky="nsew")
        chart1_card.grid_columnconfigure(0, weight=1)
        chart1_card.grid_rowconfigure(1, weight=1)

        chart1_title = ctk.CTkLabel(
            chart1_card,
            text="Works Over Time",
            font=("Segoe UI", 12, "bold"),
        )
        chart1_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        chart1_placeholder = ctk.CTkLabel(
            chart1_card,
            text="[Chart placeholder]\nTime series visualization\nwill be rendered here.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
            justify="center",
        )
        chart1_placeholder.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Chart 2: Status distribution
        chart2_card = ctk.CTkFrame(
            charts_section,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        chart2_card.grid(row=0, column=1, padx=(8, 0), pady=8, sticky="nsew")
        chart2_card.grid_columnconfigure(0, weight=1)
        chart2_card.grid_rowconfigure(1, weight=1)

        chart2_title = ctk.CTkLabel(
            chart2_card,
            text="Status Distribution",
            font=("Segoe UI", 12, "bold"),
        )
        chart2_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        chart2_placeholder = ctk.CTkLabel(
            chart2_card,
            text="[Chart placeholder]\nPie/bar chart showing\nstatus breakdown.",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
            justify="center",
        )
        chart2_placeholder.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

        # Summary statistics card
        summary_card = ctk.CTkFrame(
            main_frame,
            corner_radius=12,
            border_width=1,
            border_color=("gray80", "gray30"),
        )
        summary_card.grid(row=5, column=0, sticky="ew", padx=24, pady=(0, 24))

        summary_title = ctk.CTkLabel(
            summary_card,
            text="Recent Activity Summary",
            font=("Segoe UI", 12, "bold"),
        )
        summary_title.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))

        summary_content = ctk.CTkLabel(
            summary_card,
            text="• Most active day: N/A\n• Peak extraction time: N/A\n• Most processed file type: N/A",
            font=("Segoe UI", 10),
            text_color=("gray50", "gray70"),
            anchor="w",
            justify="left",
        )
        summary_content.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 16))
