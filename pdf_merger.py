import sys
from PyPDF2 import PdfMerger

def merge_pdfs(pdf_list, output_path):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output_path)
    merger.close()

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python pdf_merger.py output.pdf input1.pdf input2.pdf ...")
        sys.exit(1)
    output_file = sys.argv[1]
    input_files = sys.argv[2:]
    merge_pdfs(input_files, output_file)
    print(f"Merged PDF saved as {output_file}")
