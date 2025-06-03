import os
import sys
import json
import re

# Add the backend directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)

from projects.pdf_processor import process_new_pdf

def get_next_id():
    """Get next available project ID from existing data"""
    json_path = os.path.join(BASE_DIR, 'parsed_data.json')
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if not data:
                return 1
            return max(item.get('project_id', 0) for item in data) + 1
    except (FileNotFoundError, json.JSONDecodeError):
        return 1

def extract_number(filename):
    """Extract number from filename like 'project_report (1).pdf'"""
    match = re.search(r'\((\d+)\)', filename)
    return int(match.group(1)) if match else None

def process_all_pdfs():
    pdf_folder = os.path.join(BASE_DIR, 'pdf_folder')
    if not os.path.exists(pdf_folder):
        os.makedirs(pdf_folder)
        print(f"📁 Created PDF folder: {pdf_folder}")
        return

    # Initialize parsed_data.json if it doesn't exist
    json_path = os.path.join(BASE_DIR, 'parsed_data.json')
    if not os.path.exists(json_path):
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump([], f)

    # Get list of PDFs sorted by their numbers
    pdfs = [f for f in os.listdir(pdf_folder) if f.endswith('.pdf')]
    pdfs.sort(key=lambda f: extract_number(f) or 0)

    if not pdfs:
        print("❌ No PDF files found in pdf_folder")
        return

    print(f"📑 Found {len(pdfs)} PDF files to process")

    # Process each PDF
    for pdf_file in pdfs:
        pdf_path = os.path.join(pdf_folder, pdf_file)
        try:
            file_id = extract_number(pdf_file)
            project_id = file_id if file_id else get_next_id()

            print(f"\n⏳ Processing: {pdf_file} (ID: {project_id})")
            result = process_new_pdf(pdf_path, project_id=project_id)
            
            if result is None:
                print(f"❌ Skipped {pdf_file} due to empty or invalid Gemini response.")
            else:
                print(f"✅ Successfully processed: {pdf_file}")

        except Exception as e:
            print(f"❌ Error processing {pdf_file}: {e}")

if __name__ == "__main__":
    print("🚀 Starting batch PDF processing...")
    process_all_pdfs()
    print("\n✨ Batch processing complete!")
