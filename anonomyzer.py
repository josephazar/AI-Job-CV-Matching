from anonympy.pdf import pdfAnonymizer

# Define paths to the PDF, Tesseract, and Poppler
path_to_pdf = r"C:\Users\KarimAlameh\Downloads\CV\Karim Alameh CV.pdf"  # Update with correct path
pytesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
poppler_path = r"C:\Program Files\poppler-24.08.0\Library\bin"

# Create an instance of the pdfAnonymizer class
anonym = pdfAnonymizer(path_to_pdf=path_to_pdf,
                       pytesseract_path=pytesseract_path,
                       poppler_path=poppler_path)

# Call the anonymize function with desired parameters
anonym.anonymize(output_path=r'C:\path\to\output.pdf',  # Specify output path
                 remove_metadata=True,
                 fill='black',
                 outline='black')
