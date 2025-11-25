import logging
from typing import Dict
from models import Equipment

logger = logging.getLogger(__name__)

class DataUpdater:
    """Handles updating equipment with extracted data"""
    
    def __init__(self, extraction_rules):
        self.rules = extraction_rules
    
    def update_equipment(self, equipment_map: Dict[str, Equipment], extracted_data: Dict[str, Dict[str, any]]):
        """Update equipment with extracted data"""
        for equipment_number, data in extracted_data.items():
            equipment = equipment_map.get(equipment_number)
            if not equipment:
                logger.warning(f"Equipment {equipment_number} not found in map")
                continue
            
            components_data = data.get('components_data', [])
            for comp_data in components_data:
                self._update_component(equipment, comp_data, equipment_number)
    
    def _update_component(self, equipment: Equipment, comp_data: Dict, equipment_number: str):
        """Update a single component with extracted data"""
        component = equipment.get_component(comp_data['component_name'])
        if not component:
            logger.warning(f"Component {comp_data['component_name']} not found in equipment {equipment_number}")
            return
        
        updates = self._build_updates(comp_data, equipment_number)
        if updates:
            try:
                component.update_existing_data(updates)
                logger.info(f"✅ Updated {equipment_number} - {comp_data['component_name']}: {', '.join(updates.keys())}")
            except KeyError as e:
                logger.error(f"❌ Invalid data field {e} for {equipment_number} - {comp_data['component_name']}")
    
    def _build_updates(self, comp_data: Dict, equipment_number: str) -> Dict:
        """Build updates dictionary from extracted component data"""
        updates = {}
        
        skip_operating_pressure_temp = equipment_number in self.rules.SKIP_OPERATING_PRESSURE_TEMPERATURE
        insulation_only = equipment_number in self.rules.INSULATION_ONLY_EQUIPMENT
        
        if not insulation_only:
            if comp_data['fluid'] != 'NOT_FOUND' and comp_data['fluid'] != '':
                updates['fluid'] = comp_data['fluid']
            
            if comp_data['material_specification'] != 'NOT_FOUND' and comp_data['material_specification'] != '':
                updates['spec'] = comp_data['material_specification']
            if comp_data['material_grade'] != 'NOT_FOUND' and comp_data['material_grade'] != '':
                updates['grade'] = comp_data['material_grade']
        
        if comp_data['insulation'] != 'NOT_FOUND' and comp_data['insulation'] != '':
            updates['insulation'] = comp_data['insulation']
        
        if skip_operating_pressure_temp:
            pressure_temp_fields = {
                'design_temperature': 'design_temp',
                'design_pressure': 'design_pressure',
            }
        if not skip_operating_pressure_temp:
            pressure_temp_fields = {
                'design_temperature': 'design_temp',
                'design_pressure': 'design_pressure', 
                'operating_temperature': 'operating_temp',
                'operating_pressure': 'operating_pressure'
            }
            
            for source_field, target_field in pressure_temp_fields.items():
                if comp_data[source_field] != 'NOT_FOUND' and comp_data[source_field] != '':
                    updates[target_field] = self._convert_value(comp_data[source_field])
        
        return updates
    
    def _convert_value(self, value: str) -> any:
        """Convert string values to appropriate types"""
        if value == 'NOT_FOUND' or not value:
            return None
        
        if value.lower() in ['yes', 'no']:
            return value.lower()
        
        try:
            clean_value = ''.join(c for c in value if c.isdigit() or c in ['.', '-'])
            if clean_value and clean_value != '-':
                return float(clean_value)
        except:
            pass
        
        return value