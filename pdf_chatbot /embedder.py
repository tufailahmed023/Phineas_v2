import os 
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pdf_utils import get_pdf_text_emd


pdf_file_path = '/Users/tufailahmed/Desktop/PDFs'
print("Loading PDF and extracting text...")
get_pdf_text_emd(pdf_file_path)