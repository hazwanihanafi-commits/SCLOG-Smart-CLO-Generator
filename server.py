from flask import Blueprint, request, jsonify, send_file
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

from utils import (
    load_df,
    get_plo_details,
    get_meta_data,
    get_assessment,
    get_evidence_for
)

# ======================================================
# Blueprint
# ======================================================
clo_only = Blueprint("clo_only", __name__)

# ======================================================
# DEGREE × DOMAIN × BLOOM LIMIT
# ======================================================
DEGREE_BLOOM_LIMIT = {
    "cognitive": {
        "Diploma": ["remember", "understand", "apply"],
        "Degree": ["apply", "analyze", "analyse", "evaluate"],
        "Master": ["analyze", "analyse", "evaluate", "create"],
        "PhD": ["evaluate", "create"]
    },
    "affective": {
        "Diploma": ["receive", "respond"],
        "Degree": ["respond", "value"],
        "Master": ["value", "organization"],
        "PhD": ["organization", "characterization"]
    },
    "psychomotor": {
        "Diploma": ["perception", "set", "guided response"],
        "Degree": ["guided response", "mechanism"],
        "Master": ["complex overt response", "adaptation"],
        "PhD": ["adaptation", "origination"]
    }
}

# ======================================================
# BLOOM DESCRIPTIONS (UI EXPLANATION)
# ======================================================
BLOOM_DESCRIPTIONS = {
    "cognitive": {
        "remember": "Recall relevant knowledge from long-term memory.",
        "understand": "Construct meaning from instructional messages.",
        "apply": "Use procedures to perform tasks or solve problems.",
        "analyze": "Break material into parts and determine relationships.",
        "evaluate": "Make judgments based on criteria and standards.",
        "create": "Put elements together to form a novel structure."
    },
    "affective": {
        "receive": "Willingness to listen and be aware of values.",
        "respond": "Active participation through response or compliance.",
        "value": "Attach worth or value to behaviours or ideas.",
        "organization": "Integrate values into a coherent system.",
        "characterization": "Consistent value-driven behaviour."
    },
    "psychomotor": {
        "perception": "Use sensory cues to guide motor activity.",
        "set": "Readiness to act based on mental and physical disposition.",
        "guided response": "Early stage of skill acquisition with guidance.",
        "mechanism": "Intermediate stage of skill proficiency.",
        "complex overt response": "Skilled performance of complex movements.",
        "adaptation": "Modify movements to fit special situations.",
        "origination": "Create new movement patterns."
    }
}

# ======================================================
# API — BLOOM DESCRIPTION
# ======================================================
@clo_only.route("/api/clo-only/bloom-desc/<plo>/<bloom>")
def bloom_desc(plo, bloom):
    profile = request.args.get("profile", "sc")
    details = get_plo_details(plo, profile)
    if not details:
        return jsonify("")

    domain = details["Domain"].lower()
    return jsonify(
        BLOOM_DESCRIPTIONS.get(domain, {}).get(bloom.lower(), "")
    )

# ======================================================
# API — GENERATE CLO (FULL QUALITY)
# ======================================================
@clo_only.route("/clo-only/generate", methods=["POST"])
def clo_only_generate():
    data = request.form

    profile = data.get("profile", "sc")
    plo     = data.get("plo", "")
    bloom   = (
        data.get("bloom_key")
        or data.get("bloom", "")
    ).strip().lower()
    verb    = data.get("verb", "")
    content = data.get("content", "")
    level   = data.get("level", "Degree")

    # -------------------------
    # REQUIRED FIELD CHECK
    # -------------------------
    if not plo or not bloom or not verb or not content:
        return jsonify({"error": "Missing required fields"}), 400

    details = get_plo_details(plo, profile)
    if not details:
        return jsonify({"error": "Invalid PLO"}), 400

    meta = get_meta_data(plo, bloom, profile)

# 🔒 SAFETY GUARD — ADD THIS
if not meta or "condition" not in meta:
    return jsonify({
        "error": "Invalid Bloom–PLO metadata configuration"
    }), 400

domain  = details["Domain"].lower()
sc_desc = details["SC_Desc"]
vbe     = details["VBE"]



    # -------------------------
    # DEGREE × BLOOM ENFORCEMENT
    # -------------------------
    allowed = DEGREE_BLOOM_LIMIT.get(domain, {}).get(level, [])
    allowed = [a.strip().lower() for a in allowed]

    if bloom not in allowed:
        return jsonify({
            "error": f"Bloom '{bloom}' not allowed for {level} ({domain})",
            "allowed": allowed
        }), 400

    # -------------------------
    # CLEAN VERB DUPLICATION
    # -------------------------
    words = content.strip().split()
    if words and words[0].lower() == verb.lower():
        content = " ".join(words[1:])

    # -------------------------
    # CLO CONSTRUCTION
    # -------------------------
    connector = "when" if domain != "psychomotor" else "by"
    condition_clean = (
        meta["condition"]
        .replace("when ", "")
        .replace("by ", "")
    )

    clo = (
        f"{verb.lower()} {content} using {sc_desc.lower()} "
        f"{connector} {condition_clean} guided by {vbe.lower()}."
    ).capitalize()

    variants = {
        "Standard": clo,
        "Critical Thinking": clo.replace("using", "critically using"),
        "Short": f"{verb.capitalize()} {content}."
    }

    assessments = get_assessment(plo, bloom, domain)
    evidence = {a: get_evidence_for(a) for a in assessments}

    return jsonify({
        "clo": clo,
        "variants": variants,
        "meta": {
            "plo": plo,
            "domain": domain,
            "bloom": bloom,
            "sc": sc_desc,
            "vbe": vbe,
            "criterion": meta.get("criterion", ""),
            "condition": meta.get("condition", "")
        },
        "assessments": assessments,
        "evidence": evidence
    })

# ======================================================
# DOWNLOAD — CLO EXCEL
# ======================================================
@clo_only.route("/clo-only/download", methods=["POST"])
def download_clo():
    data = request.json
    if not data:
        return "No data", 400

    wb = Workbook()
    ws = wb.active
    ws.title = "CLO"

    ws.append(["Item", "Description"])

    ws.append(["CLO", data.get("clo", "")])
    ws.append(["Domain", data["meta"]["domain"]])
    ws.append(["Bloom", data["meta"]["bloom"]])
    ws.append(["Scientific Core (SC)", data["meta"]["sc"]])
    ws.append(["VBE", data["meta"]["vbe"]])
    ws.append(["Condition", data["meta"]["condition"]])

    ws.append([])
    ws.append(["Variants", ""])
    for k,v in data.get("variants", {}).items():
        ws.append([k, v])

    ws.append([])
    ws.append(["Assessments", ""])
    for a in data.get("assessments", []):
        ws.append([a, ", ".join(data["evidence"].get(a, []))])

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    return send_file(
        out,
        as_attachment=True,
        download_name=f"CLO_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# ======================================================
# DOWNLOAD — RUBRIC EXCEL
# ======================================================
@clo_only.route("/clo-only/download-rubric", methods=["POST"])
def download_rubric():
    data = request.json
    if not data:
        return "No data", 400

    wb = Workbook()
    ws = wb.active
    ws.title = "Rubric"

    ws.append(["Criteria", "Description"])
    ws.append(["CLO", data.get("clo", "")])
    ws.append(["Excellent", "Exceeds expected performance"])
    ws.append(["Good", "Meets expected performance"])
    ws.append(["Satisfactory", "Meets minimum requirement"])
    ws.append(["Poor", "Below acceptable level"])

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    return send_file(
        out,
        as_attachment=True,
        download_name=f"CLO_Rubric_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
