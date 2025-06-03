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

    prompt =  f"""
You are an intelligent and precise information extraction assistant. From the provided project document text, extract and return ONLY a JSON object with the following fields:

{{
  "filename": "{file_name}",
  "Project Title": "",
  "Student Name": "",
  "College Name": "",
  "Guide Name": "",
  "Domain": "",  // This field must be chosen strictly from the list below
  "Abstract": ""
}}

The "domain" field must contain exactly one of the following categories (whichever is most relevant to the text content):

["Research based or innovation", "Technology Demonstration", "Software Development", "Hardware Development", "Cyber security", "AI", "ML", "DEEP LEARNING", "IOT", "Neural Netwrok", "Block Chain", "Agriculture", "Disaster Management Support", "Forestry & Ecology", "Geosciences", "LULC", "Rural Development", "Soils", "Urban & Infrastructure", "Water Resources", "Earth and Climatic Studies"]

In case of ambiguity, choose the **most relevant** single domain based on the overall context.

Text:
```{full_text}```

IMPORTANT: 
- Return ONLY the JSON object.
- Do NOT include any additional text, code blocks, or explanations.
""".strip()

    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()

        if not response_text:
            raise ValueError("❌ Empty response from Gemini API.")

        cleaned_response = clean_json_response(response_text)

        if not cleaned_response:
            raise ValueError("❌ Cleaned response is empty. Possibly missing JSON or improperly formatted.")

        try:
            result = json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            print("⚠ JSON decode error. Raw response:")
            print(response_text)
            raise e

        # ✅ Save to parsed_data.json only
        if os.path.exists("parsed_data.json"):
            with open("parsed_data.json", "r", encoding="utf-8") as f:
                parsed_data = json.load(f)
        else:
            parsed_data = []

        parsed_data.append(result)
        with open("parsed_data.json", "w", encoding="utf-8") as f:
            json.dump(parsed_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Processed and added to parsed_data.json: {file_name}")

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
