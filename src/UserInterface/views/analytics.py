"""Analytics Dashboard - RBI Risk Assessment Focus."""

from typing import Optional, Dict, Any, List
import customtkinter as ctk
from AutoRBI_Database.database.session import SessionLocal
from AutoRBI_Database.database.models.equipment import Equipment as DBEquipment
from AutoRBI_Database.database.models.component import Component as DBComponent
from AutoRBI_Database.database.models.correction_log import CorrectionLog
from AutoRBI_Database.database.models.work_history import WorkHistory
from AutoRBI_Database.database.models.users import User
from AutoRBI_Database.database.models.work import Work
from sqlalchemy import func


class RBIAnalyticsEngine:
    """Backend: Calculate RBI-relevant metrics from database."""
    
    @staticmethod
    def get_work_health_score(db, work_id: int) -> Dict:
        """Health score for RBI data readiness."""
        total_eq = db.query(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).count()
        
        extracted_eq = db.query(DBEquipment).filter(
            DBEquipment.work_id == work_id,
            DBEquipment.extracted_date.isnot(None)
        ).count()
        
        extraction_rate = (extracted_eq / total_eq * 100) if total_eq > 0 else 0
        
        # Critical RBI fields
        critical_fields = ['fluid', 'material_spec', 'design_temp', 'design_pressure']
        
        all_components = db.query(DBComponent).join(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).all()
        
        if not all_components:
            return {
                'health_score': 0,
                'extraction_rate': 0,
                'completeness_rate': 0,
                'risk_level': 'UNKNOWN',
                'status_color': ('gray50', 'gray70'),
            }
        
        filled_critical = sum(
            1 for comp in all_components
            for field in critical_fields
            if getattr(comp, field)
        )
        
        total_critical = len(all_components) * len(critical_fields)
        completeness_rate = (filled_critical / total_critical * 100) if total_critical > 0 else 0
        
        # Get correction count
        correction_count = db.query(CorrectionLog).join(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).count()
        
        # Health score: 40% extraction + 40% completeness + 20% quality
        correction_penalty = min(20, correction_count * 2)
        health_score = (
            (extraction_rate * 0.4) +
            (completeness_rate * 0.4) +
            (20 - correction_penalty)
        )
        
        # Color & risk
        if health_score >= 85:
            risk = 'LOW - Ready'
            color = ('#2ecc71', '#27ae60')
        elif health_score >= 70:
            risk = 'MEDIUM - Review'
            color = ('#f39c12', '#e67e22')
        elif health_score >= 50:
            risk = 'HIGH - Gaps'
            color = ('#e74c3c', '#c0392b')
        else:
            risk = 'CRITICAL'
            color = ('#c0392b', '#8b0000')
        
        return {
            'health_score': round(health_score, 1),
            'extraction_rate': round(extraction_rate, 1),
            'completeness_rate': round(completeness_rate, 1),
            'risk_level': risk,
            'status_color': color,
            'total_equipment': total_eq,
            'extracted_equipment': extracted_eq,
        }
    
    @staticmethod
    def get_critical_gaps(db, work_id: int) -> List[Dict]:
        """Fields missing for RBI assessment."""
        critical_fields = {
            'fluid': 'Fluid Type',
            'material_spec': 'Material Spec',
            'design_temp': 'Design Temp',
            'design_pressure': 'Design Pressure',
        }
        
        gaps = []
        for field, label in critical_fields.items():
            missing = db.query(DBComponent).join(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                getattr(DBComponent, field) == None
            ).count()
            
            if missing > 0:
                gaps.append({
                    'field': label,
                    'missing_count': missing,
                    'severity': 'HIGH' if missing > 5 else 'MEDIUM'
                })
        
        return sorted(gaps, key=lambda x: x['missing_count'], reverse=True)
    
    @staticmethod
    def get_equipment_status(db, work_id: int) -> List[Dict]:
        """Equipment prioritized by completeness."""
        critical_fields = ['fluid', 'material_spec', 'design_temp', 'design_pressure']
        
        equipment_list = db.query(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).all()
        
        ranking = []
        for eq in equipment_list:
            components = db.query(DBComponent).filter(
                DBComponent.equipment_id == eq.equipment_id
            ).all()
            
            total_fields = len(components) * len(critical_fields)
            filled = sum(
                1 for c in components
                for f in critical_fields
                if getattr(c, f)
            )
            
            completeness = (filled / total_fields * 100) if total_fields > 0 else 0
            
            if completeness >= 90:
                status = '✓'
                color = '#2ecc71'
            elif completeness >= 70:
                status = '⚠'
                color = '#f39c12'
            else:
                status = '✗'
                color = '#e74c3c'
            
            ranking.append({
                'equipment_no': eq.equipment_no,
                'completeness': round(completeness, 1),
                'status': status,
                'color': color,
                'components': len(components),
            })
        
        return sorted(ranking, key=lambda x: x['completeness'])
    
    @staticmethod
    def get_team_stats(db, work_id: int) -> Dict:
        """Extraction and correction activity."""
        extract_count = db.query(WorkHistory).filter(
            WorkHistory.work_id == work_id,
            WorkHistory.action_type == 'extract'
        ).count()
        
        correct_count = db.query(WorkHistory).filter(
            WorkHistory.work_id == work_id,
            WorkHistory.action_type.in_(['correct', 'generate_excel'])
        ).count()
        
        total_corrections = db.query(CorrectionLog).join(DBEquipment).filter(
            DBEquipment.work_id == work_id
        ).count()
        
        return {
            'extraction_actions': extract_count,
            'correction_actions': correct_count,
            'total_corrections': total_corrections,
        }


class AnalyticsView:
    """RBI Analytics Dashboard - CTK UI."""
    
    def __init__(self, parent: ctk.CTk, controller):
        self.parent = parent
        self.controller = controller
        self.current_work_id = controller.current_work.get("work_id") if controller.current_work else None
    
    def _refresh_data(self):
        """Fetch latest analytics from database."""
        if not self.current_work_id:
            return None
        
        db = SessionLocal()
        try:
            engine = RBIAnalyticsEngine()
            return {
                'health': engine.get_work_health_score(db, self.current_work_id),
                'gaps': engine.get_critical_gaps(db, self.current_work_id),
                'equipment': engine.get_equipment_status(db, self.current_work_id),
                'team': engine.get_team_stats(db, self.current_work_id),
            }
        finally:
            db.close()
    
    def show(self) -> None:
        """Display Analytics Dashboard."""
        for widget in self.parent.winfo_children():
            widget.destroy()
        
        root_frame = ctk.CTkFrame(self.parent, corner_radius=0, fg_color="transparent")
        root_frame.pack(expand=True, fill="both", padx=32, pady=24)
        
        root_frame.grid_rowconfigure(1, weight=1)
        root_frame.grid_columnconfigure(0, weight=1)
        
        # HEADER
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
        
        # MAIN SCROLLABLE CONTENT
        scroll_container = ctk.CTkScrollableFrame(
            root_frame,
            corner_radius=18,
            border_width=1,
            border_color=("gray80", "gray25"),
        )
        scroll_container.grid(row=1, column=0, sticky="nsew", pady=(12, 0))
        
        main_frame = scroll_container
        main_frame.grid_columnconfigure(0, weight=1)
        
        # PAGE TITLE
        page_title = ctk.CTkLabel(
            main_frame,
            text="RBI Data Assessment",
            font=("Segoe UI", 26, "bold"),
        )
        page_title.grid(row=0, column=0, sticky="w", padx=24, pady=(18, 6))
        
        subtitle = ctk.CTkLabel(
            main_frame,
            text="Monitor data readiness for RBI risk assessment.",
            font=("Segoe UI", 11),
            text_color=("gray25", "gray80"),
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=24, pady=(0, 18))
        
        # Load data
        data = self._refresh_data()
        if not data:
            no_data = ctk.CTkLabel(
                main_frame,
                text="No work selected.",
                font=("Segoe UI", 12),
                text_color=("gray50", "gray70"),
            )
            no_data.grid(row=2, column=0, sticky="w", padx=24)
            return
        
        # SECTION 1: HEALTH STATUS
        self._build_health_card(main_frame, data['health'], row=2)
        
        # SECTION 2: CRITICAL GAPS
        self._build_gaps_section(main_frame, data['gaps'], row=3)
        
        # SECTION 3: EQUIPMENT PRIORITY
        self._build_equipment_section(main_frame, data['equipment'], row=4)
        
        # SECTION 4: TEAM ACTIVITY
        self._build_team_section(main_frame, data['team'], row=5)
        
        # REFRESH BUTTON
        refresh_btn = ctk.CTkButton(
            main_frame,
            text="🔄 Refresh Data",
            command=self.show,
            height=36,
            font=("Segoe UI", 11),
            width=150,
        )
        refresh_btn.grid(row=6, column=0, sticky="e", padx=24, pady=(24, 24))
    
    def _build_health_card(self, parent, health: Dict, row: int):
        """Big health status card."""
        card = ctk.CTkFrame(
            parent,
            corner_radius=12,
            border_width=2,
            border_color=health['status_color'],
            fg_color=("white", "gray20"),
        )
        card.grid(row=row, column=0, sticky="ew", padx=24, pady=(0, 18))
        card.grid_columnconfigure(0, weight=1)
        
        # Status indicator
        status_label = ctk.CTkLabel(
            card,
            text=health['risk_level'],
            font=("Segoe UI", 14, "bold"),
            text_color=health['status_color'],
        )
        status_label.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        
        # Score
        score_label = ctk.CTkLabel(
            card,
            text=f"Health Score: {health['health_score']}/100",
            font=("Segoe UI", 12),
        )
        score_label.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 12))
        
        # Metrics grid
        metrics_frame = ctk.CTkFrame(card, fg_color="transparent")
        metrics_frame.grid(row=2, column=0, sticky="ew", padx=16, pady=(0, 16))
        metrics_frame.grid_columnconfigure(0, weight=1)
        metrics_frame.grid_columnconfigure(1, weight=1)
        metrics_frame.grid_columnconfigure(2, weight=1)
        
        # Extraction metric
        extract_label = ctk.CTkLabel(
            metrics_frame,
            text="Extraction",
            font=("Segoe UI", 10, "bold"),
            text_color=("gray50", "gray70"),
        )
        extract_label.grid(row=0, column=0, sticky="w")
        
        extract_val = ctk.CTkLabel(
            metrics_frame,
            text=f"{health['extraction_rate']}%",
            font=("Segoe UI", 16, "bold"),
        )
        extract_val.grid(row=1, column=0, sticky="w")
        
        # Completeness metric
        complete_label = ctk.CTkLabel(
            metrics_frame,
            text="Critical Fields",
            font=("Segoe UI", 10, "bold"),
            text_color=("gray50", "gray70"),
        )
        complete_label.grid(row=0, column=1, sticky="w")
        
        complete_val = ctk.CTkLabel(
            metrics_frame,
            text=f"{health['completeness_rate']}%",
            font=("Segoe UI", 16, "bold"),
        )
        complete_val.grid(row=1, column=1, sticky="w")
        
        # Equipment metric
        eq_label = ctk.CTkLabel(
            metrics_frame,
            text="Equipment",
            font=("Segoe UI", 10, "bold"),
            text_color=("gray50", "gray70"),
        )
        eq_label.grid(row=0, column=2, sticky="w")
        
        eq_val = ctk.CTkLabel(
            metrics_frame,
            text=f"{health['extracted_equipment']}/{health['total_equipment']}",
            font=("Segoe UI", 16, "bold"),
        )
        eq_val.grid(row=1, column=2, sticky="w")
    
    def _build_gaps_section(self, parent, gaps: List[Dict], row: int):
        """Missing critical fields."""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.grid(row=row, column=0, sticky="ew", padx=24, pady=(0, 18))
        section.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            section,
            text="Critical Data Gaps",
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(anchor="w", pady=(0, 8))
        
        if not gaps:
            no_gaps = ctk.CTkLabel(
                section,
                text="✓ All critical fields present",
                font=("Segoe UI", 11),
                text_color=("gray50", "gray70"),
            )
            no_gaps.pack(anchor="w")
            return
        
        # Gap items
        for gap in gaps:
            gap_frame = ctk.CTkFrame(
                section,
                fg_color=("gray90", "gray15"),
                corner_radius=8,
            )
            gap_frame.pack(fill="x", pady=(0, 6))
            gap_frame.grid_columnconfigure(1, weight=1)
            
            field_label = ctk.CTkLabel(
                gap_frame,
                text=gap['field'],
                font=("Segoe UI", 11, "bold"),
            )
            field_label.grid(row=0, column=0, sticky="w", padx=12, pady=8)
            
            count_label = ctk.CTkLabel(
                gap_frame,
                text=f"{gap['missing_count']} missing",
                font=("Segoe UI", 10),
                text_color=("gray60", "gray80"),
            )
            count_label.grid(row=0, column=1, sticky="e", padx=12, pady=8)
    
    def _build_equipment_section(self, parent, equipment: List[Dict], row: int):
        """Equipment priority ranking."""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.grid(row=row, column=0, sticky="ew", padx=24, pady=(0, 18))
        section.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            section,
            text="Equipment Priority (Incomplete First)",
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(anchor="w", pady=(0, 8))
        
        if not equipment:
            no_eq = ctk.CTkLabel(
                section,
                text="No equipment data",
                font=("Segoe UI", 11),
                text_color=("gray50", "gray70"),
            )
            no_eq.pack(anchor="w")
            return
        
        # Equipment items (show top 5)
        for eq in equipment[:10]:
            eq_frame = ctk.CTkFrame(
                section,
                fg_color=("gray90", "gray15"),
                corner_radius=8,
            )
            eq_frame.pack(fill="x", pady=(0, 4))
            eq_frame.grid_columnconfigure(1, weight=1)
            
            status_color = eq['color']
            status_label = ctk.CTkLabel(
                eq_frame,
                text=eq['status'],
                font=("Segoe UI", 11, "bold"),
                text_color=status_color,
                width=30,
            )
            status_label.grid(row=0, column=0, padx=8, pady=4)
            
            eq_label = ctk.CTkLabel(
                eq_frame,
                text=f"{eq['equipment_no']} ({eq['components']} components)",
                font=("Segoe UI", 10),
            )
            eq_label.grid(row=0, column=1, sticky="w", padx=8, pady=4)
            
            complete_label = ctk.CTkLabel(
                eq_frame,
                text=f"{eq['completeness']}%",
                font=("Segoe UI", 10, "bold"),
            )
            complete_label.grid(row=0, column=2, sticky="e", padx=12, pady=4)
        
        if len(equipment) > 5:
            more_label = ctk.CTkLabel(
                section,
                text=f"... and {len(equipment) - 5} more",
                font=("Segoe UI", 9),
                text_color=("gray50", "gray70"),
            )
            more_label.pack(anchor="w", pady=(4, 0))
    
    def _build_team_section(self, parent, team: Dict, row: int):
        """Team activity."""
        section = ctk.CTkFrame(parent, fg_color="transparent")
        section.grid(row=row, column=0, sticky="ew", padx=24, pady=(0, 18))
        section.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            section,
            text="Work Activity",
            font=("Segoe UI", 12, "bold"),
        )
        title.pack(anchor="w", pady=(0, 8))
        
        # Activity grid
        activity_frame = ctk.CTkFrame(section, fg_color="transparent")
        activity_frame.pack(fill="x")
        activity_frame.grid_columnconfigure(0, weight=1)
        activity_frame.grid_columnconfigure(1, weight=1)
        activity_frame.grid_columnconfigure(2, weight=1)
        
        metrics = [
            ("Extractions", team['extraction_actions']),
            ("Corrections", team['correction_actions']),
            ("Total Fixes", team['total_corrections']),
        ]
        
        for col, (label, value) in enumerate(metrics):
            card = ctk.CTkFrame(
                activity_frame,
                fg_color=("gray90", "gray15"),
                corner_radius=8,
            )
            card.grid(row=0, column=col, padx=(0, 8), sticky="ew")
            
            label_widget = ctk.CTkLabel(
                card,
                text=label,
                font=("Segoe UI", 9),
                text_color=("gray50", "gray70"),
            )
            label_widget.pack(pady=(8, 2))
            
            value_widget = ctk.CTkLabel(
                card,
                text=str(value),
                font=("Segoe UI", 18, "bold"),
            )
            value_widget.pack(pady=(2, 8))