
from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import re

app = Flask(__name__)

def detect_violations(file_stream):
    doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    text = ""
    page_count = doc.page_count
    issues = []

    # Combine all text
    for page in doc:
        text += page.get_text()

    # Check for missing signature
    if not re.search(r"signature|signed|notary", text, re.IGNORECASE):
        issues.append("❌ No signature or perjury clause detected (Fla. Stat. § 92.525).")

    # Check for perjury language
    if not re.search(r"penalty of perjury", text, re.IGNORECASE):
        issues.append("❌ Missing penalty of perjury clause — affidavit may be inadmissible.")

    # Discovery violation (user-confirmed flag via checkbox — simulated here)
    # In live mode, check if `from_discovery` field is sent
    issues.append("⚠️ Affidavit not listed in discovery response (Rule 1.380 Fla. R. Civ. P.).")

    # Check if wrong form used (detect 12.902(b) or (c))
    if "12.902(b)" in text:
        issues.append("📄 Detected Form 12.902(b) — may be incorrect if this is a support case.")
    if "12.902(c)" in text:
        issues.append("📄 Detected Form 12.902(c) — may be incorrect if this is a parenting case.")

    # Page skipping or suspiciously blank pages
    expected_pages = page_count
    if expected_pages < 2:
        issues.append("⚠️ Very short affidavit (1 page). Could be incomplete.")

    # Redaction/black box detection (beta using image analysis)
    redaction_found = False
    for page in doc:
        pix = page.get_pixmap()
        if pix.width == 0 or pix.height == 0:
            continue
        if pix.samples.count(0) > 1000:
            redaction_found = True
    if redaction_found:
        issues.append("⚠️ Potential redactions or black box overlays detected.")

    if not issues:
        issues.append("✅ No major issues found. Let me know if you need further review.")

    return issues

@app.route("/analyze", methods=["POST"])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    findings = detect_violations(file)
    return jsonify({"results": findings})

if __name__ == "__main__":
    app.run(debug=True)
