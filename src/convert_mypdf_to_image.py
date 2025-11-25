import os
from pdf2image import convert_from_path

def batch_pdf_to_images(input_folder, output_folder="converted_to_image", dpi=200):
    """
    Convert all PDF files to images with same filenames in converted_to_image folder
    """
    # Check if input folder exists
    if not os.path.exists(input_folder):
        print(f"Error: Input folder '{input_folder}' does not exist!")
        return
    
    # Create output folder
    os.makedirs(output_folder, exist_ok=True)
    
    # Get all PDF files
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    
    if not pdf_files:
        print(f"No PDF files found in '{input_folder}'")
        return
    
    print(f"Found {len(pdf_files)} PDF files to convert:")
    for pdf_file in pdf_files:
        print(f"  - {pdf_file}")
    
    total_pages = 0
    
    # Convert each PDF file
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_folder, pdf_file)
        base_name = os.path.splitext(pdf_file)[0]
        
        try:
            print(f"\nConverting: {pdf_file}")
            
            # Convert PDF to images
            images = convert_from_path(pdf_path, dpi=dpi)
            
            # Save each page with same base filename
            for i, image in enumerate(images):
                if len(images) == 1:
                    # Single page - use exact PDF name
                    output_path = os.path.join(output_folder, f"{base_name}.png")
                else:
                    # Multiple pages - add page number
                    output_path = os.path.join(output_folder, f"{base_name}_page_{i+1}.png")
                
                image.save(output_path, "PNG")
                print(f"  Saved: {os.path.basename(output_path)}")
            
            total_pages += len(images)
            print(f"✓ Completed: {pdf_file} → {len(images)} pages")
            
        except Exception as e:
            print(f"✗ Error converting {pdf_file}: {e}")
    
    print(f"\n🎉 Conversion complete!")
    print(f"📁 PDF files processed: {len(pdf_files)}")
    print(f"📄 Total pages converted: {total_pages}")
    print(f"💾 Images saved in: {output_folder}/")

# Example usage
if __name__ == "__main__":
    input_folder = "CaseStudy1Resources"
    batch_pdf_to_images(input_folder)