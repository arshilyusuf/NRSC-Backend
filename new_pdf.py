import fitz
import re
import os
import json
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import time

# Load environment
load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("⚠️ Missing GEMINI_API_KEY.")
genai.configure(api_key=api_key)
model = genai.GenerativeModel("gemini-1.5-flash")

def clean_json_response(response_text):
    if "```json" in response_text:
        response_text = response_text.split("```json", 1)[1]
    if "```" in response_text:
        response_text = response_text.split("```", 1)[0]
    return response_text.strip()

def extract_text_from_pdf(pdf_path):
    try:
        doc = fitz.open(pdf_path)
        full_text = " ".join(page.get_text() for page in doc)
        doc.close()
        full_text = full_text.replace(",", "").replace("\n", " ").replace("\r", " ")
        full_text = re.sub(r"\s+", " ", full_text).strip()
        return " ".join(full_text.split()[:5000])
    except Exception as e:
        return f"ERROR reading PDF: {e}"

def process_new_pdf(pdf_path):
    file_name = os.path.basename(pdf_path)
    full_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
You are an intelligent and precise information extraction assistant. From the provided project document text, extract and return ONLY a JSON object with the following fields:

{{
  "filename": "{file_name}",
  "Project Title": "",
  "Student Name": "",
  "College Name": "",
  "Guide Name": "",
  "Domain": "",
  "Abstract": ""
}}

The "Domain" field must contain one of the following categories:

["Research based or innovation", "Technology Demonstration", "Software Development", "Hardware Development", "Cyber security", "AI", "ML", "DEEP LEARNING", "IOT", "Neural Netwrok", "Block Chain", "Agriculture", "Disaster Management Support", "Forestry & Ecology", "Geosciences", "LULC", "Rural Development", "Soils", "Urban & Infrastructure", "Water Resources", "Earth and Climatic Studies"]

Text:
```{full_text}```

IMPORTANT:
- Return ONLY the JSON object.
""".strip()

    try:
        response = model.generate_content(prompt)
        cleaned = clean_json_response(response.text)
        result = json.loads(cleaned)

        entry = {
            "project_id": -1,  # or assign dynamically
            "file_name": file_name,
            "project_title": result.get("Project Title", "N/A"),
            "student_name": result.get("Student Name", "N/A"),
            "college_name": result.get("College Name", "N/A"),
            "guide_name": result.get("Guide Name", "N/A"),
            "domain": result.get("Domain", "N/A"),
            "abstract": result.get("Abstract", "N/A")
        }

        # Update parsed_data.json
        if os.path.exists("parsed_data.json"):
            with open("parsed_data.json", "r", encoding="utf-8") as f:
                parsed = json.load(f)
        else:
            parsed = []

        parsed.append(entry)
        with open("parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)

        # Update structured_project_data.csv
        if os.path.exists("structured_project_data.csv"):
            df_csv = pd.read_csv("structured_project_data.csv")
        else:
            df_csv = pd.DataFrame()

        df_csv = pd.concat([df_csv, pd.DataFrame([entry])], ignore_index=True)
        df_csv.to_csv("structured_project_data.csv", index=False)

        print(f"✅ Processed and added: {file_name}")

    except Exception as e:
        print(f"⚠️ Error processing {file_name}: {e}")

# CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python new_pdf.py path/to/newfile.pdf")
    else:
        process_new_pdf(sys.argv[1])
        time.sleep(5)
