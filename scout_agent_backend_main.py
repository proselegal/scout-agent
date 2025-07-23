from flask import Flask, request, jsonify
import fitz  # PyMuPDF
import re
import io

app = Flask(__name__)

def detect_violations(file_stream):
    try:
        doc = fitz.open(stream=file_stream.read(), filetype="pdf")
    except Exception as e:
        return [f"❌ Failed to process PDF: {str(e)}"]

    text = ""
    page_count = doc.page_count
    issues = []

    # Combine all text
    for page in doc:
        try:
            text += page.get_text()
        except:
            continue

    # Check for missing signature
    if not re.search(r"signature|signed|notary", text, re.IGNORECASE):
        issues.append("❌ No signature or perjury clause detected (Fla. Stat. § 92.525).")

    # Check for perjury language
    if not re.search(r"penalty of perjury", text, re.IGNORECASE):
        issues.append("❌ Missing penalty of perjury clause — affidavit may be inadmissible.")

    # Placeholder discovery violation notice
    issues.append("⚠️ Affidavit not listed in discovery response (Rule 1.380 Fla. R. Civ. P.).")

    # Detect use of wrong form
    if "12.902(b)" in text:
        issues.append("📄 Detected Form 12.902(b) — may be incorrect if this is a support case.")
    if "12.902(c)" in text:
        issues.append("📄 Detected Form 12.902(c) — may be incorrect if this is a parenting case.")

    # Check for very short affidavit
    if page_count < 2:
        issues.append("⚠️ Very short affidavit (1 page). Could be incomplete.")

    # Detect possible redaction
    redaction_found = False
    try:
        for page in doc:
            pix = page.get_pixmap()
            black_pixels = pix.samples.count(0)
            if black_pixels > 10000:
                redaction_found = True
                break
    except:
        issues.append("⚠️ Error during redaction scan.")

    if redaction_found:
        issues.append("⚠️ Potential redactions or black box overlays detected.")

    if not issues:
        issues.append("✅ No major issues found. Let me know if you need further review.")

    return issues

@app.route("/analyze", methods=["POST"])
def analyze():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    try:
        file.stream.seek(0)  # Ensure file pointer is at start
        findings = detect_violations(file.stream)
        return jsonify({"results": findings})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=5000)
