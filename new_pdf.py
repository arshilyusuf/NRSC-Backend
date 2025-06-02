# new_pdf.py
import fitz  
import re
import os
import json
import pandas as pd
import google.generativeai as genai
from dotenv import load_dotenv
import time

load_dotenv()
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("⚠️ Missing GEMINI_API_KEY. Set it as an environment variable.")
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
        full_text = ""
        for page in doc:
            full_text += page.get_text()
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
technical domain and application domain should only have one entry only

application domains = [
  "Agriculture", "Disaster Management Support", "Forestry & Ecology", "Geosciences", "LULC",
  "Rural Development", "Soils", "Urban & Infrastructure", "Water Resources", 
  "Earth and Climatic Studies", "Miscelleaneous"
]

technical domains = [
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

        # ✅ Read structured_project_data.json
        with open("structured_project_data.json", "r", encoding="utf-8") as f:
            current_data = json.load(f)

        project_id = max(item["project_id"] for item in current_data) + 1

        entry = {
            "project_id": project_id,
            "file_name": result.get("filename", file_name),
            "project_title": result.get("Project Title", "N/A"),
            "student_name": result.get("Student Name", "N/A"),
            "college_name": result.get("College Name", "N/A"),
            "professor_name": result.get("Professor Name", "N/A"),
            "technical_domain": result.get("Technical Domain", "N/A"),
            "application_domain": result.get("Application Domain", "N/A"),
            "abstract": result.get("Abstract", "N/A")
        }

        # ✅ Save to structured_project_data.json
        current_data.append(entry)
        with open("structured_project_data.json", "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2, ensure_ascii=False)

        # ✅ Save to parsed_data.json
        if os.path.exists("parsed_data.json"):
            with open("parsed_data.json", "r", encoding="utf-8") as f:
                parsed_data = json.load(f)
        else:
            parsed_data = []

        parsed_data.append(result)
        with open("parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)

        # ✅ Append to CSV
        df = pd.DataFrame([entry])
        df.to_csv("structured_project_data.csv", mode='a', index=False, header=False)

        print(f"✅ Processed and added: {file_name}")

    except Exception as e:
        print(f"⚠️ Error processing {file_name}: {e}")

# CLI usage (optional)
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python new_pdf.py path/to/newfile.pdf")
    else:
        process_new_pdf(sys.argv[1])
        time.sleep(5)
