import os 
import sys 
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from pdf_utils import get_pdf_text_emd
from vectordb import pdf_file_path


# print(os.path.basename(pdf_file_path).lower())
print("Loading PDF and extracting text...")
log_file="processed_pdfs.txt"
output_folder="extracted_texts"
pdf_file_path = pdf_file_path

get_pdf_text_emd(pdf_file_path)