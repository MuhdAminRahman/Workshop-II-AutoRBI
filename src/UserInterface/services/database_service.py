# File: UserInterface/services/database_service.py
"""
Database Service Layer for Equipment Management
Handles all database operations for new_work.py
"""
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

# Import database models
from AutoRBI_Database.database.models.equipment import Equipment as DBEquipment
from AutoRBI_Database.database.models.component import Component as DBComponent
from AutoRBI_Database.database.models.type_material import TypeMaterial
from AutoRBI_Database.database.models.work_history import WorkHistory
from AutoRBI_Database.database.models.correction_log import CorrectionLog
from AutoRBI_Database.services.work_service import get_assigned_works,get_work_details

# Import local models
from models.equipment import Equipment
from models.equipment_component import Component


class DatabaseService:
    """Service for equipment database operations"""
    
    @staticmethod
    def save_equipment_with_components(
        db: Session,
        work_id: int,
        user_id: int,
        equipment: Equipment,
        drawing_path: str
    ) -> Optional[DBEquipment]:
        """
        Save equipment and its components to database.
        Returns the created Equipment DB object or None on failure.
        """
        try:
            # Check if equipment already exists for this work
            existing = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.equipment_no == equipment.equipment_number
            ).first()
            
            if existing:
                # Update existing equipment
                db_equipment = existing
                db_equipment.user_id = user_id
                db_equipment.pmt_no = equipment.pmt_number or ""
                db_equipment.description = equipment.equipment_description or ""
                db_equipment.drawing_path = drawing_path
                db_equipment.extracted_date = datetime.utcnow()
            else:
                # Create new equipment
                db_equipment = DBEquipment(
                    work_id=work_id,
                    user_id=user_id,
                    equipment_no=equipment.equipment_number,
                    pmt_no=equipment.pmt_number or "",
                    description=equipment.equipment_description or "",
                    drawing_path=drawing_path,
                    extracted_date=datetime.utcnow()
                )
                db.add(db_equipment)
            
            # Flush to get equipment_id
            db.flush()
            
            # Save components
            for component in equipment.components:
                DatabaseService._save_component(db, db_equipment.equipment_id, component)
            
            db.commit()
            return db_equipment
            
        except IntegrityError as e:
            db.rollback()
            print(f"IntegrityError saving equipment {equipment.equipment_number}: {e}")
            return None
        except Exception as e:
            db.rollback()
            print(f"Error saving equipment {equipment.equipment_number}: {e}")
            return None
    
    @staticmethod
    def _save_component(db: Session, equipment_id: int, component: Component) -> Optional[DBComponent]:
        """Save a single component to database"""
        try:
            # Check if component exists
            existing = db.query(DBComponent).filter(
                DBComponent.equipment_id == equipment_id,
                DBComponent.part_name == component.component_name
            ).first()
            
            # Get existing data values
            existing_data = component.existing_data
            
            if existing:
                # Update existing component
                db_component = existing
            else:
                # Create new component
                db_component = DBComponent(
                    equipment_id=equipment_id,
                    part_name=component.component_name
                )
                db.add(db_component)
            
            # Update component fields
            db_component.phase = component.phase
            db_component.fluid = existing_data.get('fluid')
            all_material_specs = db.query(TypeMaterial).all()
            for mat in all_material_specs:
                if mat.material_spec == existing_data.get('spec'):
                    db_component.material_spec = mat.material_spec
                    break
            db_component.material_grade = str(existing_data.get('grade'))
            
            # Handle insulation (convert to enum-compatible value)
            insulation_value = existing_data.get('insulation', '').lower()
            if insulation_value in ['yes', 'no']:
                db_component.insulation = insulation_value
            
            # Store temperatures/pressures as strings (as per schema)
            db_component.design_temp = existing_data.get('design_temp')
            db_component.design_pressure = existing_data.get('design_pressure')
            db_component.operating_temp = str(existing_data.get('operating_temp'))
            db_component.operating_pressure = str(existing_data.get('operating_pressure'))
            
            return db_component
            
        except Exception as e:
            print(f"Error saving component {component.component_name}: {e}")
            return None
    
    @staticmethod
    def log_work_history(
        db: Session,
        work_id: int,
        user_id: int,
        action_type: str,
        equipment_id: Optional[int] = None,
        description: Optional[str] = None
    ) -> bool:
        """
        Log an action to work history.
        
        Action types:
        - upload_pdf: PDF uploaded
        - extract: Data extracted from PDF
        - correct: Data corrected by user
        - generate_excel: Excel file generated
        - generate_ppt: PowerPoint generated
        """
        try:
            history_entry = WorkHistory(
                work_id=work_id,
                user_id=user_id,
                equipment_id=equipment_id,
                action_type=action_type,
                description=description,
                timestamp=datetime.utcnow()
            )
            db.add(history_entry)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error logging work history: {e}")
            return False
    
    @staticmethod
    def log_correction(
        db: Session,
        equipment_id: int,
        user_id: int,
        fields_to_fill: int,
        fields_corrected: int
    ) -> bool:
        """Log data correction to correction_log table"""
        try:
            correction_entry = CorrectionLog(
                equipment_id=equipment_id,
                user_id=user_id,
                fields_to_fill=fields_to_fill,
                fields_corrected=fields_corrected,
                timestamp=datetime.utcnow()
            )
            db.add(correction_entry)
            db.commit()
            return True
            
        except Exception as e:
            db.rollback()
            print(f"Error logging correction: {e}")
            return False
    
    @staticmethod
    def get_equipment_by_work_and_number(
        db: Session,
        work_id: int,
        equipment_no: str
    ) -> Optional[DBEquipment]:
        """Get equipment by work ID and equipment number"""
        try:
            return db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.equipment_no == equipment_no
            ).first()
        except Exception as e:
            print(f"Error getting equipment: {e}")
            return None
    
    @staticmethod
    def count_correction_fields(
        original_component: Component,
        updated_data: Dict[str, str]
    ) -> Tuple[int, int]:
        """
        Count fields that needed filling and were corrected.
        
        Returns:
            (fields_to_fill, fields_corrected)
        """
        fields_to_check = [
            'fluid', 'type', 'spec', 'grade', 'insulation',
            'design_temp', 'design_pressure',
            'operating_temp', 'operating_pressure'
        ]
        
        fields_to_fill = 0
        fields_corrected = 0
        
        for field in fields_to_check:
            original_value = original_component.get_existing_data_value(field)
            updated_value = updated_data.get(field, '').strip()
            
            # Field needed filling if it was empty
            if not original_value:
                fields_to_fill += 1
                
                # Field was corrected if it now has a value
                if updated_value:
                    fields_corrected += 1
        
        return fields_to_fill, fields_corrected
    
    @staticmethod
    def batch_save_equipment(
        db: Session,
        work_id: int,
        user_id: int,
        equipment_map: Dict[str, Equipment],
        drawing_paths: Dict[str, str]
    ) -> Tuple[int, int]:
        """
        Batch save multiple equipment items.
        
        Returns:
            (success_count, failure_count)
        """
        success_count = 0
        failure_count = 0
        
        for eq_no, equipment in equipment_map.items():
            drawing_path = drawing_paths.get(eq_no, "")
            
            result = DatabaseService.save_equipment_with_components(
                db, work_id, user_id, equipment, drawing_path
            )
            
            if result:
                success_count += 1
            else:
                failure_count += 1
        
        return success_count, failure_count
    
    @staticmethod
    def update_equipment_data(db, equipment_id: int, equipment):
        """Update equipment data in database with corrected values"""
        # This is a simplified example - adjust based on your schema
        from AutoRBI_Database.database.models import Equipment as DBEquipment
        
        db_equipment = db.query(DBEquipment).filter(DBEquipment.equipment_id == equipment_id).first()
        if db_equipment:
            # Update fields based on your schema
            # You'll need to map the equipment object to your database model
            # Example:
            db_equipment.equipment_number = equipment.equipment_number
            db_equipment.pmt_number = equipment.pmt_number
            db_equipment.equipment_description = equipment.equipment_description
            
            # Update component data if your schema supports it
            # This part depends on your database structure
            
            db.commit()
            return True
        return False

    @staticmethod
    def get_equipment_id_by_equipment_number(
        db: Session,
        work_id: int,
        equipment_no: str
    ) -> Optional[int]:
        """Get equipment ID by work ID and equipment number"""
        try:
            equipment = db.query(DBEquipment).filter(
                DBEquipment.work_id == work_id,
                DBEquipment.equipment_no == equipment_no
            ).first()
            return equipment.equipment_id if equipment else None
        except Exception as e:
            print(f"Error getting equipment ID: {e}")
            return None
