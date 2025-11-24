import os
import logging
import time
from typing import Dict, List
from dotenv import load_dotenv
from anthropic import Anthropic

from models import Equipment
from .extraction_rules import ExtractionRules
from .prompt_builder import PromptBuilder
from .response_parser import ResponseParser
from .data_updater import DataUpdater
from .utils import compress_image_for_api, find_equipment_images

logger = logging.getLogger(__name__)

class MasterfileExtractor:
    """Main class for extracting technical data from equipment images"""
    
    def __init__(self):
        load_dotenv()
        self.client = Anthropic()
        self.max_retries = 5
        self.base_delay = 1
        
        self.rules = ExtractionRules()
        self.prompt_builder = PromptBuilder()
        self.response_parser = ResponseParser(self.rules)
        self.data_updater = DataUpdater(self.rules)
    
    def extract_technical_data(self, image_path: str, equipment: Equipment) -> Dict[str, List[Dict[str, any]]]:
        """Extract technical data from image"""
        equipment_number = equipment.equipment_number
        
        for attempt in range(self.max_retries):
            try:
                if not os.path.exists(image_path):
                    logger.error(f"File not found: {image_path}")
                    return {}
                
                image_data = compress_image_for_api(image_path)
                prompt = self._build_prompt(equipment_number, equipment)
                
                message = self.client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=4000,
                    messages=[{
                        "role": "user",
                        "content": [
                            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_data}},
                            {"type": "text", "text": prompt}
                        ]
                    }]
                )
                
                return self.response_parser.parse_response(message.content[0].text, equipment.components, equipment_number)
                
            except Exception as e:
                if self._should_retry(e, attempt):
                    continue
                logger.error(f"Error extracting data from {image_path}: {str(e)}")
                return {}
        
        logger.error(f"❌ Failed to extract data from {image_path} after {self.max_retries} attempts")
        return {}
    
    def _build_prompt(self, equipment_number: str, equipment: Equipment) -> str:
        """Build the appropriate prompt for the equipment"""
        if equipment_number in self.rules.INSULATION_ONLY_EQUIPMENT:
            insulation_config = self.rules.INSULATION_CONFIGS[equipment_number]
            return self.prompt_builder.build_insulation_only_prompt(equipment_number, equipment, insulation_config)
        
        if equipment_number in self.rules.FIELD_INSTRUCTIONS:
            field_instructions = self.rules.FIELD_INSTRUCTIONS[equipment_number]
            insulation_config = self.rules.INSULATION_CONFIGS[equipment_number]
            skip_operation_pressure_temp = equipment_number in self.rules.SKIP_OPERATING_PRESSURE_TEMPERATURE
            
            return self.prompt_builder.build_full_extraction_prompt(
                equipment_number, equipment, field_instructions, insulation_config, skip_operation_pressure_temp
            )
        
        return f"Extract technical data for {equipment_number} - {equipment.equipment_description}"
    
    def _should_retry(self, error: Exception, attempt: int) -> bool:
        """Determine if a request should be retried"""
        error_msg = str(error)
        if '529' in error_msg or 'overloaded' in error_msg.lower():
            delay = self.base_delay * (2 ** attempt)
            logger.warning(f"⚠️ API overloaded (attempt {attempt + 1}/{self.max_retries}). Retrying in {delay} seconds...")
            time.sleep(delay)
            return True
        return False
    
    def process_equipment_images(self, equipment_map: Dict[str, Equipment]) -> Dict[str, Dict[str, any]]:
        """Process images for all equipment"""
        extracted_data = {}
        
        for equipment_number, equipment in equipment_map.items():
            extracted_data.update(self._process_single_equipment(equipment_number, equipment))
        
        return extracted_data
    
    def _process_single_equipment(self, equipment_number: str, equipment: Equipment) -> Dict[str, Dict[str, any]]:
        """Process a single equipment"""
        logger.info(f"🔍 Processing equipment: {equipment_number} - {equipment.pmt_number}")
        
        image_files = find_equipment_images(equipment.pmt_number)
        if not image_files:
            logger.warning(f"❌ No images found for {equipment.pmt_number}")
            return {}
        
        for image_file in image_files:
            logger.info(f"  📄 Analyzing {image_file.name}...")
            technical_data = self.extract_technical_data(str(image_file), equipment)
            
            if technical_data and technical_data.get('components_data'):
                logger.info(f"  ✅ Successfully extracted data from {image_file.name}")
                return {equipment_number: technical_data}
            else:
                logger.warning(f"  ⚠️ No data extracted from {image_file.name}")
        
        logger.error(f"  ❌ Failed to extract data for {equipment_number}")
        return {}
    
    def update_equipment_with_extracted_data(self, equipment_map: Dict[str, Equipment], extracted_data: Dict[str, Dict[str, any]]) -> None:
        """Update equipment with extracted data"""
        self.data_updater.update_equipment(equipment_map, extracted_data)
    
    def process_and_update_equipment(self, equipment_map: Dict[str, Equipment]) -> Dict[str, Equipment]:
        """Complete pipeline: extract data and update equipment"""
        logger.info("🚀 Starting equipment data extraction pipeline...")
        
        extracted_data = self.process_equipment_images(equipment_map)
        self.update_equipment_with_extracted_data(equipment_map, extracted_data)
        
        logger.info(f"✅ Completed processing {len(extracted_data)} equipment items")
        return equipment_map
    