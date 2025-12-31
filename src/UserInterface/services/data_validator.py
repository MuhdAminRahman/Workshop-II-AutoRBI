from dataclasses import dataclass
from typing import Dict, List, Tuple


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    empty_cells: List[Tuple[str, str, str]]  # (equipment_no, component, field)
    error_message: str
    
    @property
    def has_empty_cells(self) -> bool:
        return len(self.empty_cells) > 0


class DataValidator:
    """Validates extracted and edited data"""
    
    # Required fields that must be filled
    REQUIRED_FIELDS = [
        'equipment_no',
        'parts',
        'fluid',
        'material_type',
        'spec',
        'grade'
    ]
    
    def validate_equipment_map(
        self,
        equipment_map: Dict,
        file_to_textboxes: Dict
    ) -> ValidationResult:
        """
        Validate all equipment data for completeness.
        
        Returns:
            ValidationResult with empty cells and validation status
        """
        empty_cells = []
        
        # Validate from UI entries
        for file_path, entries in file_to_textboxes.items():
            if not entries:
                continue
            
            num_cols = 15  # From TableColumns.NUM_COLUMNS
            num_rows = len(entries) // num_cols
            
            for row_idx in range(num_rows):
                start_idx = row_idx * num_cols
                row_entries = entries[start_idx:start_idx + num_cols]
                
                if len(row_entries) < num_cols:
                    continue
                
                # Map indices to field names
                equipment_no = row_entries[1].get().strip()
                parts = row_entries[4].get().strip()
                
                # Check required fields
                field_checks = {
                    'equipment_no': row_entries[1].get().strip(),
                    'parts': row_entries[4].get().strip(),
                    'fluid': row_entries[6].get().strip(),
                    'material_type': row_entries[7].get().strip(),
                    'spec': row_entries[8].get().strip(),
                    'grade': row_entries[9].get().strip(),
                }
                
                for field_name, field_value in field_checks.items():
                    if not field_value:
                        empty_cells.append((equipment_no or f"Row {row_idx+1}", parts, field_name))
        
        # Build error message
        if empty_cells:
            error_msg = f"Found {len(empty_cells)} empty required field(s). Please fill all required fields."
        else:
            error_msg = ""
        
        return ValidationResult(
            is_valid=len(empty_cells) == 0,
            empty_cells=empty_cells,
            error_message=error_msg
        )
    
    def get_empty_cell_indices(
        self,
        file_to_textboxes: Dict,
        empty_cells: List[Tuple[str, str, str]]
    ) -> List[int]:
        """
        Get list of entry widget indices that are empty.
        Used for highlighting empty cells.
        """
        empty_indices = []
        
        # Create a set of (equipment_no, parts, field) for quick lookup
        empty_set = set(empty_cells)
        
        for file_path, entries in file_to_textboxes.items():
            if not entries:
                continue
            
            num_cols = 15
            num_rows = len(entries) // num_cols
            
            for row_idx in range(num_rows):
                start_idx = row_idx * num_cols
                row_entries = entries[start_idx:start_idx + num_cols]
                
                if len(row_entries) < num_cols:
                    continue
                
                equipment_no = row_entries[1].get().strip()
                parts = row_entries[4].get().strip()
                
                # Check each field
                field_map = {
                    1: 'equipment_no',
                    4: 'parts',
                    6: 'fluid',
                    7: 'material_type',
                    8: 'spec',
                    9: 'grade',
                }
                
                for col_idx, field_name in field_map.items():
                    if (equipment_no, parts, field_name) in empty_set:
                        empty_indices.append(start_idx + col_idx)
        
        return empty_indices