"""Main entry point for AutoRBI application."""
import logging
from data_extractor import MasterfileExtractor
from excel_manager import ExcelManager
from app import AutoRBIApp

def setup_logging():
    """Configure logging with no duplicate handlers"""
    # Get root logger
    logger = logging.getLogger()
    
    # Only configure if not already configured
    if not logger.hasHandlers():
        # Set logging level
        logger.setLevel(logging.INFO)
        
        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)

def main() -> None:
    """Run the AutoRBI application."""
    app = AutoRBIApp()
    app.mainloop()
    #test_DataExtractor()


def test_DataExtractor():
    """Main function to run the equipment data extraction"""
    print("🚀 Starting Equipment Data Extraction Pipeline")
    print("=" * 50)
    
    try:
        # Step 1: Load equipment data from Excel
        print("\n1. 📊 Loading equipment data from Excel...")
        excel_manager = ExcelManager("CaseStudy1Resources\MasterFile _ IPETRO PLANT.xlsx")
        equipment_map = excel_manager.read_masterfile()
        
        print(f"✅ Loaded {len(equipment_map)} equipment items")
        
        # Step 2: Initialize the data extractor
        print("\n2. 🔧 Initializing data extractor...")
        extractor = MasterfileExtractor()
        
        # Step 3: Process equipment images and extract data
        print("\n3. 🖼️ Extracting data from equipment images...")
        updated_equipment_map = extractor.process_and_update_equipment(equipment_map)
        
        # Step 4: Save updated data back to Excel
        print("\n4. 💾 Saving updated data to Excel...")
        excel_manager.save_to_excel()
        
        print("\n🎯 Pipeline completed successfully!")
        
    except Exception as e:
        logging.error(f"❌ Error in main pipeline: {e}")
        raise

if __name__ == "__main__":
    main()