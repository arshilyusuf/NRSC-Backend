import os
import fitz
import re
import json
import google.generativeai as genai
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
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

def process_new_pdf(pdf_path, project_id=-1):
    file_name = os.path.basename(pdf_path)
    full_text = extract_text_from_pdf(pdf_path)

    prompt = f"""
You are an intelligent and precise information extraction assistant. Extract ONLY the following JSON format with EXACT field names:

{{
    "project_id": {project_id},
    "file_name": "{file_name}",
    "project_title": "",
    "students": [],
    "colleges": [],
    "guide_name": "",
    "domain": "",
    "abstract": ""
}}

The "domain" field must contain one of: ["Research based or innovation", "Technology Demonstration", "Software Development", "Hardware Development", "Cyber security", "AI", "ML", "DEEP LEARNING", "IOT", "Neural Netwrok", "Block Chain", "Agriculture", "Disaster Management Support", "Forestry & Ecology", "Geosciences", "LULC", "Rural Development", "Soils", "Urban & Infrastructure", "Water Resources", "Earth and Climatic Studies"]

Text:
```{full_text}```

IMPORTANT: Return ONLY the JSON object with exact field names shown above. The students and colleges entries should be arrays of respective names and college of the individual from the project report. If any field is not found, return "N/A" for that field. If a person "X" is from college "Y", then the index of "X" in students should match the index of "Y" in colleges. "NRSC" is not a college, so do not include it in the colleges array. If no students or colleges are found, return empty arrays for those fields. Also if more than one student belongs to the same college, they should be listed in the students array with their respective college in the colleges array at their respective same index.
""".strip()

    try:
        response = model.generate_content(prompt)
        cleaned = clean_json_response(response.text)
        if not cleaned.strip():
            print(f"⚠️ Empty response from Gemini API for {pdf_path}")
            return None

        try:
            result = json.loads(cleaned)
        except Exception as e:
            print(f"⚠️ Invalid JSON from Gemini API for {pdf_path}:\n{cleaned}")
            return None

        entry = {
            "project_id": project_id,
            "file_name": file_name,
            "project_title": result.get("project_title", "N/A"),
            "students": result.get("students", "N/A"),
            "colleges": result.get("colleges", "N/A"),
            "guide_name": result.get("guide_name", "N/A"),
            "domain": result.get("domain", "N/A"),
            "abstract": result.get("abstract", "N/A")
        }

        json_path = os.path.join(BASE_DIR, 'parsed_data.json')
        parsed = []
        if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
            with open(json_path, 'r', encoding='utf-8') as f:
                try:
                    parsed = json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️ Warning: {json_path} is empty or corrupted. Starting with empty data.")
                    parsed = []
        else:
            parsed = []

        parsed.append(entry)
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(parsed, f, indent=2, ensure_ascii=False)

        print(f"✅ Processed and added: {file_name}")
        return entry

    except Exception as e:
        print(f"⚠️ Error processing {file_name}: {e}")
        return None
