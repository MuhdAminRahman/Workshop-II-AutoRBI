"""Main entry point for AutoRBI application."""
import logging
from data_extractor import MasterfileExtractor
from excel_manager import ExcelManager
from app import AutoRBIApp
# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

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
        
        #for equipment_number, equipment in equipment_map.items():
        #    print(f"Key: {equipment_number} -> {equipment}")
        #    for component in equipment.components:
        #        print(f"  - {component}")

        print(f"✅ Loaded {len(equipment_map)} equipment items")
        
        # Step 2: Initialize the data extractor
        print("\n2. 🔧 Initializing data extractor...")
        extractor = MasterfileExtractor()
        
        # Step 3: Process equipment images and extract data
        print("\n3. 🖼️ Extracting data from equipment images...")
        updated_equipment_map = extractor.process_and_update_equipment(equipment_map)
        

        #for equipment_number, equipment in updated_equipment_map.items():
        #   print(f"Key: {equipment_number} -> {equipment}")
        #   for component in equipment.components:
        #       print(f"  - {component}")

        # Step 4: Save updated data back to Excel
        print("\n4. 💾 Saving updated data to Excel...")
        excel_manager.save_to_excel()
        
        print("\n🎯 Pipeline completed successfully!")
        
    except Exception as e:
        logging.error(f"❌ Error in main pipeline: {e}")
        raise
if __name__ == "__main__":
    main()

