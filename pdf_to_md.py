import os
import pdfplumber

def pdf_to_markdown(input_folder, output_folder):
    # Create output folder if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Get all PDF files in the input folder
    pdf_files = [f for f in os.listdir(input_folder) if f.lower().endswith('.pdf')]
    
    # Process each PDF file
    for pdf_file in pdf_files:
        try:
            # Construct full paths
            pdf_path = os.path.join(input_folder, pdf_file)
            # Create markdown filename (replace .pdf with .md)
            md_filename = os.path.splitext(pdf_file)[0] + '.md'
            md_path = os.path.join(output_folder, md_filename)
            
            # Open and extract text from PDF
            with pdfplumber.open(pdf_path) as pdf:
                text = ''
                # Extract text from each page
                for page in pdf.pages:
                    text += page.extract_text() or ''  # Add empty string if no text extracted
                    text += '\n\n'  # Add spacing between pages
            
            # Write text to markdown file
            with open(md_path, 'w', encoding='utf-8') as md_file:
                md_file.write(text)
                
            print(f"Converted: {pdf_file} -> {md_filename}")
            
        except Exception as e:
            print(f"Error converting {pdf_file}: {str(e)}")

def main():
    # Set your input and output folders
    input_folder = r"C:\Users\felix\Scripts\PDF"  # Using raw string with r prefix
    output_folder = r"C:\Users\felix\Scripts\MD"  # Different output folder suggested
    
    print("Starting PDF to Markdown conversion...")
    pdf_to_markdown(input_folder, output_folder)
    print("Conversion complete!")

if __name__ == "__main__":
    main()