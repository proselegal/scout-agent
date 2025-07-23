
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import fitz  # PyMuPDF
import openai
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = os.getenv("OPENAI_API_KEY")

logic_table = [
  {
    "Trigger": "Unsigned or Incomplete Affidavit",
    "Detection Method": "Scan for missing signature or perjury clause",
    "Legal Context": "Fla. Stat. \u00a7 92.525 \u2013 Unsworn documents have no evidentiary weight",
    "Agent Response": "\u26a0\ufe0f Affidavit is unsigned or missing penalty clause",
    "Upsell Action": "\ud83d\udd13 Unlock 'Affidavit Challenge Toolkit' in Strike Pack"
  },
  {
    "Trigger": "Affidavit Not Disclosed in Discovery",
    "Detection Method": "Compare affidavit source to discovery disclosures",
    "Legal Context": "Fla. R. Civ. P. 1.380 \u2013 False discovery response",
    "Agent Response": "\u274c Affidavit was obtained outside discovery. Strike Pack applicable.",
    "Upsell Action": "\ud83d\udd13 Unlock 'Sanctions + Vacatur Toolkit' in Strike Pack"
  },
  {
    "Trigger": "User Confirms Material Misstatement",
    "Detection Method": "Prompt user to verify if income/assets/benefits were misrepresented",
    "Legal Context": "Extrinsic fraud doctrine \u2013 Rule 1.540(b)",
    "Agent Response": "\ud83d\udea8 Fraud confirmed. Eligible for vacatur and sanctions.",
    "Upsell Action": "\ud83d\udd13 Unlock Strike Pack \u2013 Motion to Vacate & Debt Reassignment"
  }
]

def detect_red_flags(text):
    flags = []
    for item in logic_table:
        trigger = item["Trigger"].lower()
        if trigger in text.lower():
            flags.append(trigger)
    return flags

@app.post("/analyze")
async def analyze_affidavit(file: UploadFile = File(...)):
    content = await file.read()
    with open("temp.pdf", "wb") as f:
        f.write(content)

    doc = fitz.open("temp.pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()

    doc.close()
    os.remove("temp.pdf")

    flags = detect_red_flags(full_text)

    return {
        "filename": file.filename,
        "flags": flags,
        "summary": "Flag detection complete",
        "next_step": "Unlock Strike Pack" if flags else "No urgent issues detected"
    }
