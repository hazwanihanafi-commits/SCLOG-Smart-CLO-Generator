from flask import Blueprint, request, jsonify, send_file, current_app, send_from_directory
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime
import os
import json

def load_plo_mapping():
    path = os.path.join(current_app.root_path, "static", "data", "plo_mapping.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


from utils import (
    get_meta_data,
    get_assessment,
    get_evidence_for
)


# ======================================================
# Blueprint
# ======================================================
clo_only = Blueprint("clo_only", __name__)

@clo_only.route("/clo-only/plo-mapping")
def serve_plo_mapping():
    return send_from_directory(
        os.path.join(current_app.root_path, "static", "data"),
        "plo_mapping.json"
    )

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
    plo_map = load_plo_mapping()
    details = plo_map.get(plo)

    if not details:
        return jsonify("")

    domain = details["domain"].lower()
    return jsonify(
        BLOOM_DESCRIPTIONS.get(domain, {}).get(bloom.lower(), "")
    )

# ======================================================
# API — GENERATE CLO (FULL QUALITY)
# ======================================================
@clo_only.route("/clo-only/generate", methods=["POST"])
def clo_only_generate():
    data = request.form

    plo = data.get("plo", "")
    bloom = (data.get("bloom_key") or data.get("bloom", "")).strip().lower()
    verb = data.get("verb", "")
    content = data.get("content", "")
    level = data.get("level", "Degree")

    # -------------------------
    # REQUIRED FIELD CHECK
    # -------------------------
    if not all([plo, bloom, verb, content]):
        return jsonify({"error": "Missing required fields"}), 400

    # -------------------------
    # SINGLE SOURCE OF TRUTH — PLO
    # -------------------------
    plo_map = load_plo_mapping()
    details = plo_map.get(plo)

    if not details:
        return jsonify({"error": "Invalid PLO"}), 400

    domain = details["domain"].lower()
    sc_desc = details["sc_description"]
    vbe = details["vbe"]

    # -------------------------
    # BLOOM METADATA (SAFE FALLBACK)
    # -------------------------
    meta = get_meta_data(plo, bloom, "sc") or {}

# ✅ NORMALISE condition (NO "when", NO "guided by")
raw_condition = meta.get(
    "condition",
    f"applying {bloom} level cognitive processes"
)

condition = (
    raw_condition
    .replace("when ", "")
    .replace("guided by", "")
    .strip()
)


    # -------------------------
    # DEGREE × BLOOM ENFORCEMENT
    # -------------------------
    allowed = [b.lower() for b in DEGREE_BLOOM_LIMIT.get(domain, {}).get(level, [])]
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
    clo = (
        f"{verb.lower()} {content} using {sc_desc.lower()} "
        f"when {condition.replace('when ', '')} "
        f"guided by {vbe.lower()}."
    ).capitalize()

    variants = {
        "Standard": clo,
        "Short": f"{verb.capitalize()} {content}."
    }

    assessments = get_assessment(plo, bloom, domain)
    evidence = {a: get_evidence_for(a) for a in assessments}

    return jsonify({
        "clo": clo,
        "variants": variants,
        "meta": {
            "domain": domain,
            "bloom": bloom,
            "sc": sc_desc,
            "vbe": vbe,
            "condition": condition
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
