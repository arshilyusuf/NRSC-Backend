import os
import re
import json
import time
import fitz  # PyMuPDF
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
# api_key = os.environ.get("GEMINI_API_KEY")
api_key = 'AIzaSyBhEVVQZDc48fPKK9_jdJz1hYj0viH1oqg'

if not api_key:
    raise ValueError("⚠️ Missing GEMINI_API_KEY in .env file.")

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
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()

                # Clean and truncate text to 5000 words
                full_text = full_text.replace(",", "")
                full_text = full_text.replace("\n", " ").replace("\r", " ")
                full_text = re.sub(r"\s+", " ", full_text).strip()
                words = full_text.split()
                full_text = " ".join(words[:5000])

            except Exception as e:
                full_text = f"ERROR reading PDF: {e}"

            pdf_data.append({
                "ID": pdf_id,
                "File Name": filename,
                "Full Text": full_text
            })

    return pd.DataFrame(pdf_data).sort_values("ID")

# ✅ Load PDFs
df_input = get_pdf_dataframe()
output_data = []

# ✅ JSON save target
# ✅ JSON save target
json_path = "parsed_data.json"
if os.path.exists(json_path) and os.path.getsize(json_path) > 0:
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            parsed_json_data = json.load(f)
        except json.JSONDecodeError:
            print("JSONDecodeError: 'parsed_data.json' contains invalid JSON. Starting with an empty list.")
            parsed_json_data = []
else:
    parsed_json_data = []

for _, row in df_input.iterrows():
    project_id = row["ID"]
    file_name = row["File Name"]
    full_text = row["Full Text"]

    prompt = f"""
You are a helpful assistant. Extract and return only a JSON object with the following fields:
{{
  "filename": "{file_name}",
  "Project Title": "",
  "Student Name": "",
  "College Name": "",
  "Professor Name": "",
  "Technical Domain": "",
  "Application Domain": "",
  "Abstract": ""
}}

Text: ```{full_text}```

IMPORTANT: Return ONLY the JSON object with no other text, no code blocks, no explanations.

Allowed application domains = [
    "Agriculture", "Disaster Management Support", "Forestry & Ecology", "Geosciences", "LULC",
    "Rural Development", "Soils", "Urban & Infrastructure", "Water Resources",
    "Earth and Climatic Studies", "Miscelleaneous"
]

Allowed technical domains = [
    "Remote Sensing and GIS", "App Development", "Web Development", "AI/ML",
    "Image Processing/Computer Vision", "Data Science / Big Data Analytics",
    "Cloud Computing / High Performance Computing", "IoT", "Sensor Integration",
    "Drone Data Processing and Integration", "AR/VR", "Robotics",
    "Embedded Systems", "3D Printing / Fabrication Technology"
]
""".strip()

    try:
        response = model.generate_content(prompt)
        cleaned_response = clean_json_response(response.text)
        result = json.loads(cleaned_response)

        entry = {
            "project_id": project_id,
            "file_name": file_name,
            "project_title": result.get("Project Title", "N/A"),
            "student_name": result.get("Student Name", "N/A"),
            "college_name": result.get("College Name", "N/A"),
            "professor_name": result.get("Professor Name", "N/A"),
            "technical_domain": result.get("Technical Domain", "N/A"),
            "application_domain": result.get("Application Domain", "N/A"),
            "abstract": result.get("Abstract", "N/A"),
            "grade": "N/A"
        }

        # ✅ Add to both CSV and JSON
        output_data.append(entry)
        parsed_json_data.append(entry)

    except json.JSONDecodeError as je:
        print(f"⚠️ JSON Error for {file_name}: {str(je)}")
    except Exception as e:
        print(f"⚠️ Error for {file_name}: {str(e)}")

    time.sleep(5)

# ✅ Save to CSV
df_output = pd.DataFrame(output_data)
df_output.to_csv("structured_project_data.csv", index=False)
print("✅ Output saved to 'structured_project_data.csv'")

# ✅ Save to JSON
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(parsed_json_data, f, indent=2, ensure_ascii=False)
print("✅ Output saved to 'parsed_data.json'")
