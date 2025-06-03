import os
import re
import json
import time
import fitz  # PyMuPDF
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

# Load API key
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

def get_pdf_dataframe():
    pdf_folder = os.path.join(os.path.dirname(__file__), "pdf_folder")
    pdf_data = []

    for filename in sorted(os.listdir(pdf_folder)):
        match = re.match(r"project_report \((\d+)\)\.pdf", filename)
        if match:
            pdf_id = int(match.group(1))
            pdf_path = os.path.join(pdf_folder, filename)

            try:
                doc = fitz.open(pdf_path)
                full_text = " ".join(
                    page.get_text() for page in doc
                ).replace(",", "").replace("\n", " ").replace("\r", " ")
                doc.close()

                full_text = re.sub(r"\s+", " ", full_text).strip()
                full_text = " ".join(full_text.split()[:5000])

            except Exception as e:
                full_text = f"ERROR reading PDF: {e}"

            pdf_data.append({
                "ID": pdf_id,
                "File Name": filename,
                "Full Text": full_text
            })

    return pd.DataFrame(pdf_data).sort_values("ID")

# Load existing data
json_path = "parsed_data.json"
csv_path = "structured_project_data.csv"

if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        parsed_json_data = json.load(f)
else:
    parsed_json_data = []

if os.path.exists(csv_path):
    df_existing = pd.read_csv(csv_path)
else:
    df_existing = pd.DataFrame()

df_input = get_pdf_dataframe()
output_data = []

for _, row in df_input.iterrows():
    project_id = row["ID"]
    file_name = row["File Name"]
    full_text = row["Full Text"]

    if file_name in df_existing.get("file_name", []):
        continue  # Skip already processed files

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
            "project_id": project_id,
            "file_name": file_name,
            "project_title": result.get("Project Title", "N/A"),
            "student_name": result.get("Student Name", "N/A"),
            "college_name": result.get("College Name", "N/A"),
            "guide_name": result.get("Guide Name", "N/A"),
            "domain": result.get("Domain", "N/A"),
            "abstract": result.get("Abstract", "N/A")
        }

        parsed_json_data.append(entry)
        output_data.append(entry)

    except Exception as e:
        print(f"⚠️ Error processing {file_name}: {e}")

    time.sleep(5)

# Save to files
if output_data:
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(parsed_json_data, f, indent=2, ensure_ascii=False)

    df_combined = pd.concat([df_existing, pd.DataFrame(output_data)], ignore_index=True)
    df_combined.to_csv(csv_path, index=False)
    print("✅ Updated parsed_data.json and structured_project_data.csv")
else:
    print("✅ No new PDFs to process.")
