import pandas as pd
from python_calamine import CalamineWorkbook
import json
from typing import Dict, List, Any

class ExcelEquipmentAnalyzer:
    """
    A class to analyze Excel files containing equipment data and export to JSON
    """
    
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.sheets_data = {}
        self.analysis_results = {}
    
    def read_excel_file(self) -> Dict[str, pd.DataFrame]:
        """
        Read Excel file using python_calamine
        """
        workbook = CalamineWorkbook.from_path(self.file_path)
        sheets_data = {}
        
        for sheet_name in workbook.sheet_names:
            sheet_data = workbook.get_sheet_by_name(sheet_name).to_python()
            
            if not sheet_data:
                sheets_data[sheet_name] = pd.DataFrame()
                continue
                
            # Convert to DataFrame first
            df = pd.DataFrame(sheet_data)
            
            # Find the header row
            header_row_idx = self._find_header_row(df)
            
            if header_row_idx is not None:
                # Create new DataFrame with proper headers
                new_columns = df.iloc[header_row_idx].fillna('').astype(str)
                new_df = df.iloc[header_row_idx + 1:].copy()
                new_df.columns = [f"col_{i}" if col == '' else str(col).strip() 
                                for i, col in enumerate(new_columns)]
                
                # Remove completely empty rows and columns
                new_df = new_df.dropna(how='all').dropna(axis=1, how='all')
                
                sheets_data[sheet_name] = new_df
            else:
                sheets_data[sheet_name] = pd.DataFrame()
        
        self.sheets_data = sheets_data
        return sheets_data
    
    def _find_header_row(self, df: pd.DataFrame, max_rows_to_check: int = 15) -> int:
        """
        Find the row that contains the actual column headers
        """
        for i in range(min(max_rows_to_check, len(df))):
            row = df.iloc[i].fillna('').astype(str)
            
            # Count non-empty cells in this row
            non_empty_count = sum(1 for cell in row if str(cell).strip() != '')
            
            # Check for header indicators
            header_indicators = ['NO', 'EQUIPMENT', 'DESCRIPTION', 'MATERIAL', 
                               'THICKNESS', 'CORROSION', 'RATE', 'LIFE', 'DATE', 'PMT']
            row_text = ' '.join(str(cell) for cell in row)
            
            # If row has reasonable number of non-empty cells and contains headers
            if non_empty_count >= 5 and any(indicator in row_text.upper() for indicator in header_indicators):
                return i
        
        return None
    
    def _convert_to_number_if_possible(self, value):
        """
        Convert value to number if possible, otherwise return as string
        """
        if value is None or value == '':
            return None
        
        try:
            # Try to convert to float first
            float_val = float(value)
            # If it's an integer, return as int, otherwise float
            return int(float_val) if float_val.is_integer() else float_val
        except (ValueError, TypeError):
            return str(value)
    
    def _group_masterfile_parts(self, masterfile_df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Group masterfile parts by equipment
        """
        equipment_groups = {}
        current_equipment = None
        current_equipment_info = {}
        
        for idx, row in masterfile_df.iterrows():
            equipment_number = row.get('EQUIPMENT NO.', '')
            pmt_number = row.get('PMT NO.', '')
            equipment_description = row.get('EQUIPMENT DESCRIPTION', '')
            
            # Check if this row has a new equipment number
            if (pd.notna(equipment_number) and 
                str(equipment_number).strip() != '' and
                'EQUIPMENT' not in str(equipment_number).upper()):
                
                # This is a new equipment
                current_equipment = str(equipment_number)
                current_equipment_info = {
                    "pmt_number": str(pmt_number),
                    "equipment_description": str(equipment_description)
                }
                
                # Initialize equipment group if not exists
                if current_equipment not in equipment_groups:
                    equipment_groups[current_equipment] = {
                        "equipment_info": {
                            "equipment_number": current_equipment,
                            "pmt_number": current_equipment_info["pmt_number"],
                            "equipment_description": current_equipment_info["equipment_description"],
                            "total_parts": 0
                        },
                        "parts": []
                    }
            
            # If we have a current equipment and this row has part data
            if (current_equipment and 
                pd.notna(row.get('PARTS', None)) and 
                str(row.get('PARTS', '')).strip() != '' and
                'PARTS' not in str(row.get('PARTS', '')).upper()):
                
                # Create part entry
                part_entry = {
                    "row_index": int(idx),
                    "part_name": str(row.get('PARTS', '')),
                    "phase": str(row.get('PHASE', '')),
                    "fluid": str(row.get('FLUID', '')),
                    "material_information": {
                        "type": str(row.get('MATERIAL INFORMATION', '')),
                        "specification": str(row.get('col_8', '')),  # This is the SPEC
                        "grade": self._convert_to_number_if_possible(row.get('col_9', ''))  # This is the GRADE
                    },
                    "insulation": str(row.get('INSULATION\n(yes/No)', '')),
                    "design_conditions": {
                        "temperature": self._convert_to_number_if_possible(row.get('DESIGN', '')),
                        "pressure": self._convert_to_number_if_possible(row.get('col_12', ''))
                    },
                    "operating_conditions": {
                        "temperature": self._convert_to_number_if_possible(row.get('OPERATING', '')),
                        "pressure": self._convert_to_number_if_possible(row.get('col_14', ''))
                    }
                }
                
                # Remove empty values from nested structures
                part_entry["material_information"] = {k: v for k, v in part_entry["material_information"].items() if v not in ['', None]}
                part_entry["design_conditions"] = {k: v for k, v in part_entry["design_conditions"].items() if v not in ['', None]}
                part_entry["operating_conditions"] = {k: v for k, v in part_entry["operating_conditions"].items() if v not in ['', None]}
                
                # Add part to current equipment
                equipment_groups[current_equipment]["parts"].append(part_entry)
        
        # Update total parts count for each equipment
        for equipment_number, equipment_data in equipment_groups.items():
            equipment_data["equipment_info"]["total_parts"] = len(equipment_data["parts"])
        
        return equipment_groups
    
    def _group_summary_parts(self, summary_df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Group summary parts by equipment with proper subheading structure
        """
        equipment_groups = {}
        current_equipment = None
        current_equipment_info = {}
        
        for idx, row in summary_df.iterrows():
            equipment_number = row.get('EQUIPMENT NO.', '')
            pmt_number = row.get('PMT NO.', '')
            equipment_description = row.get('EQUIPMENT DESCRIPTION', '')
            
            # Check if this row has a new equipment number
            if (pd.notna(equipment_number) and 
                str(equipment_number).strip() != '' and
                'EQUIPMENT' not in str(equipment_number).upper()):
                
                # This is a new equipment
                current_equipment = str(equipment_number)
                current_equipment_info = {
                    "pmt_number": str(pmt_number),
                    "equipment_description": str(equipment_description)
                }
                
                # Initialize equipment group if not exists
                if current_equipment not in equipment_groups:
                    equipment_groups[current_equipment] = {
                        "equipment_info": {
                            "equipment_number": current_equipment,
                            "pmt_number": current_equipment_info["pmt_number"],
                            "equipment_description": current_equipment_info["equipment_description"],
                            "total_parts": 0
                        },
                        "parts": []
                    }
            
            # If we have a current equipment and this row has part data
            if (current_equipment and 
                pd.notna(row.get('PARTS', None)) and 
                str(row.get('PARTS', '')).strip() != '' and
                'PARTS' not in str(row.get('PARTS', '')).upper()):
                
                # Create structured part entry for summary data
                part_entry = {
                    "row_index": int(idx),
                    "part_name": str(row.get('PARTS', '')),
                    "representing_fluid": str(row.get('REPRESENTING FLUID', '')),
                    "phase": str(row.get('PHASE', '')),
                    "material_information": {
                        "design_code": str(row.get('MATERIAL', '')),
                        "type": str(row.get('col_8', '')),
                        "specification": str(row.get('col_9', '')),
                        "grade": str(row.get('col_10', ''))
                    },
                    "lining": str(row.get('Lining', '')),
                    "design_conditions": {
                        "temperature": self._convert_to_number_if_possible(row.get('DESIGN', '')),
                        "pressure": self._convert_to_number_if_possible(row.get('col_13', ''))
                    },
                    "operating_conditions": {
                        "temperature": self._convert_to_number_if_possible(row.get('OPERATING', '')),
                        "pressure": self._convert_to_number_if_possible(row.get('col_15', ''))
                    },
                    "outer_diameter": self._convert_to_number_if_possible(row.get('OD', '')),
                    "thickness": {
                        "design": self._convert_to_number_if_possible(row.get('THICKNESS**(mm)', '')),
                        "nominal": self._convert_to_number_if_possible(row.get('col_18', '')),
                        "required": self._convert_to_number_if_possible(row.get('col_19', ''))
                    },
                    "uttm_record_thickness": {
                        "initial": {
                            "value": self._convert_to_number_if_possible(row.get('UTTM RECORD THICKNESS**(mm)', '')),
                            "date": str(row.get('col_21', ''))
                        },
                        "previous": {
                            "value": self._convert_to_number_if_possible(row.get('col_22', '')),
                            "date": str(row.get('col_23', ''))
                        },
                        "actual": {
                            "value": self._convert_to_number_if_possible(row.get('col_24', '')),
                            "date": str(row.get('col_25', ''))
                        }
                    },
                    "corrosion_rate": {
                        "st": self._convert_to_number_if_possible(row.get('CORROSION RATE', '')),
                        "lt": self._convert_to_number_if_possible(row.get('col_27', '')),
                        "selected": self._convert_to_number_if_possible(row.get('col_28', ''))
                    },
                    "corrosion_remark": str(row.get('REMARK FOR SELECTED CORROSION RATE***', '')),
                    "remaining_life": self._convert_to_number_if_possible(row.get('REMAINING LIFE (RL)', '')),
                    "service_start_date": str(row.get('SERVICE START DATE', '')),
                    "years_in_service": self._convert_to_number_if_possible(row.get('YEARS IN SERVICE', ''))
                }
                
                # Remove empty values from nested structures
                part_entry["material_information"] = {k: v for k, v in part_entry["material_information"].items() if v not in ['', None]}
                part_entry["design_conditions"] = {k: v for k, v in part_entry["design_conditions"].items() if v not in ['', None]}
                part_entry["operating_conditions"] = {k: v for k, v in part_entry["operating_conditions"].items() if v not in ['', None]}
                part_entry["thickness"] = {k: v for k, v in part_entry["thickness"].items() if v not in ['', None]}
                part_entry["uttm_record_thickness"] = {k: v for k, v in part_entry["uttm_record_thickness"].items() if v not in ['', None]}
                part_entry["corrosion_rate"] = {k: v for k, v in part_entry["corrosion_rate"].items() if v not in ['', None]}
                
                # Add part to current equipment
                equipment_groups[current_equipment]["parts"].append(part_entry)
        
        # Update total parts count for each equipment
        for equipment_number, equipment_data in equipment_groups.items():
            equipment_data["equipment_info"]["total_parts"] = len(equipment_data["parts"])
        
        return equipment_groups
    
    def _restructure_masterfile_data(self, masterfile_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Restructure masterfile data to group parts by equipment
        """
        equipment_groups = self._group_masterfile_parts(masterfile_df)
        
        # Convert to list format
        equipment_list = []
        for equipment_number, equipment_data in equipment_groups.items():
            equipment_entry = {
                **equipment_data["equipment_info"],
                "parts": equipment_data["parts"]
            }
            equipment_list.append(equipment_entry)
        
        return equipment_list
    
    def _restructure_summary_data(self, summary_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """
        Restructure summary data to group parts by equipment with proper subheadings
        """
        equipment_groups = self._group_summary_parts(summary_df)
        
        # Convert to list format
        equipment_list = []
        for equipment_number, equipment_data in equipment_groups.items():
            equipment_entry = {
                **equipment_data["equipment_info"],
                "parts": equipment_data["parts"]
            }
            equipment_list.append(equipment_entry)
        
        return equipment_list
    
    def analyze(self) -> Dict[str, Any]:
        """
        Main analysis method - reads and processes the Excel file
        """
        print(f"Analyzing Excel file: {self.file_path}")
        
        # Read the Excel file
        self.read_excel_file()
        
        # Extract equipment data
        equipment_data = self._extract_equipment_data()
        
        # Get sheet structure
        structure_data = self._get_sheet_structure()
        
        # Combine all data
        self.analysis_results = {
            "analysis_timestamp": pd.Timestamp.now().isoformat(),
            "file_name": self.file_path,
            "sheet_structure": structure_data,
            "equipment_data": equipment_data,
            "summary": {
                "total_sheets": len(structure_data),
                "sheets_with_data": [name for name, data in structure_data.items() if data["shape"]["rows"] > 0],
                "total_equipment_entries": equipment_data["metadata"]["total_equipment"]
            }
        }
        
        return self.analysis_results
    
    def _extract_equipment_data(self) -> Dict[str, Any]:
        """
        Extract meaningful equipment data from both sheets
        """
        results = {
            "summary": {
                "equipment_count": 0,
                "equipment_list": []
            },
            "masterfile": {
                "equipment_count": 0,
                "equipment_list": []
            },
            "metadata": {
                "total_equipment": 0,
                "sheets_processed": list(self.sheets_data.keys())
            }
        }
        
        # Process Summary Data sheet
        summary_df = self.sheets_data.get("(A) SUMMARY DATA")
        if summary_df is not None and not summary_df.empty:
            summary_equipment = self._restructure_summary_data(summary_df)
            results["summary"]["equipment_list"] = summary_equipment
            results["summary"]["equipment_count"] = len(summary_equipment)
        
        # Process Masterfile sheet
        masterfile_df = self.sheets_data.get("Masterfile")
        if masterfile_df is not None and not masterfile_df.empty:
            masterfile_equipment = self._restructure_masterfile_data(masterfile_df)
            results["masterfile"]["equipment_list"] = masterfile_equipment
            results["masterfile"]["equipment_count"] = len(masterfile_equipment)
        
        # Calculate totals
        results["metadata"]["total_equipment"] = (
            results["summary"]["equipment_count"] + 
            results["masterfile"]["equipment_count"]
        )
        
        return results
    
    def _get_sheet_structure(self) -> Dict[str, Any]:
        """
        Get JSON structure of all sheets
        """
        structure = {}
        
        for sheet_name, df in self.sheets_data.items():
            sheet_info = {
                "sheet_name": sheet_name,
                "shape": {
                    "rows": df.shape[0],
                    "columns": df.shape[1]
                },
                "columns": [],
                "sample_data": []
            }
            
            if not df.empty:
                # Column information
                for i, col in enumerate(df.columns):
                    non_empty_count = int(df[col].notna().sum())
                    sheet_info["columns"].append({
                        "index": i,
                        "name": str(col),
                        "non_empty_values": non_empty_count
                    })
            
            structure[sheet_name] = sheet_info
        
        return structure
    
    def save_to_json(self, output_file: str = "equipment_analysis.json") -> None:
        """
        Save analysis results to JSON file
        """
        if not self.analysis_results:
            self.analyze()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.analysis_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"Analysis results saved to: {output_file}")
    
    def get_equipment_list(self, sheet_type: str = "masterfile") -> List[Dict[str, Any]]:
        """
        Get equipment list from specified sheet type
        """
        if not self.analysis_results:
            self.analyze()
        
        return self.analysis_results["equipment_data"][sheet_type]["equipment_list"]
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get analysis summary
        """
        if not self.analysis_results:
            self.analyze()
        
        return self.analysis_results["summary"]