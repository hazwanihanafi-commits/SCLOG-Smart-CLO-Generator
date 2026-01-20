# server.py
from flask import Blueprint, request, jsonify, send_file
from openpyxl import Workbook
from io import BytesIO
from datetime import datetime

clo_only = Blueprint("clo_only", __name__)

# ------------------------------
# DEGREE × DOMAIN × BLOOM LIMIT
# ------------------------------
DEGREE_BLOOM_LIMIT = {
    "cognitive": {
        "Diploma": ["remember", "understand", "apply"],
        "Bachelor": ["apply", "analyze", "analyse", "evaluate"],
        "Master": ["analyze", "analyse", "evaluate", "create"],
        "PhD": ["evaluate", "create"]
    },
    "affective": {
        "Diploma": ["receive", "respond"],
        "Bachelor": ["respond", "value"],
        "Master": ["value", "organization"],
        "PhD": ["organization", "characterization"]
    },
    "psychomotor": {
        "Diploma": ["perception", "set", "guided response"],
        "Bachelor": ["guided response", "mechanism"],
        "Master": ["complex overt response", "adaptation"],
        "PhD": ["adaptation", "origination"]
    }
}

# ⚠️ Import shared helper from app.py OR utils.py
from app import get_plo_details, load_df

# ------------------------------
# API: GET BLOOMS
# ------------------------------
@clo_only.route("/api/clo-only/blooms/<plo>")
def get_blooms(plo):
    degree  = request.args.get("degree", "Bachelor")
    profile = request.args.get("profile", "sc")

    details = get_plo_details(plo, profile)
    if not details:
        return jsonify([])

    domain = details["Domain"].lower()

    sheet_map = {
        "cognitive":"Bloom_Cognitive",
        "affective":"Bloom_Affective",
        "psychomotor":"Bloom_Psychomotor"
    }

    df = load_df(sheet_map[domain])
    allowed = DEGREE_BLOOM_LIMIT[domain][degree]

    blooms = df.iloc[:,0].dropna().astype(str).tolist()
    blooms = [b for b in blooms if b.lower() in allowed]

    return jsonify(blooms)

# ------------------------------
# API: GET VERBS
# ------------------------------
@clo_only.route("/api/clo-only/verbs/<plo>/<bloom>")
def get_verbs(plo, bloom):
    profile = request.args.get("profile","sc")
    details = get_plo_details(plo, profile)
    if not details:
        return jsonify([])

    domain = details["Domain"].lower()

    sheet_map = {
        "cognitive":"Bloom_Cognitive",
        "affective":"Bloom_Affective",
        "psychomotor":"Bloom_Psychomotor"
    }

    df = load_df(sheet_map[domain])
    row = df[df.iloc[:,0].str.lower() == bloom.lower()]
    if row.empty:
        return jsonify([])

    verbs = row.iloc[0,1]
    return jsonify([v.strip() for v in str(verbs).split(",")])

# ------------------------------
# GENERATE CLO (CLO-ONLY)
# ------------------------------
@clo_only.route("/clo-only/generate", methods=["POST"])
def generate_clo():
    data = request.form

    plo     = data.get("plo")
    bloom   = data.get("bloom")
    verb    = data.get("verb")
    content = data.get("content")
    degree  = data.get("degree","Bachelor")
    profile = data.get("profile","sc")

    details = get_plo_details(plo, profile)
    if not details:
        return jsonify({"error":"Invalid PLO"}), 400

    domain = details["Domain"].lower()
    allowed = DEGREE_BLOOM_LIMIT[domain][degree]

    if bloom.lower() not in allowed:
        return jsonify({
            "error": f"Bloom '{bloom}' not allowed for {degree} ({domain})"
        }), 400

    clo = f"{verb.lower()} {content}".capitalize()

    return jsonify({
        "clo": clo,
        "plo": plo,
        "bloom": bloom,
        "degree": degree,
        "domain": domain
    })

# ------------------------------
# DOWNLOAD (STATELESS)
# ------------------------------
@clo_only.route("/clo-only/download", methods=["POST"])
def download_clo():
    data = request.json
    wb = Workbook()
    ws = wb.active
    ws.append(["Field","Value"])

    for k,v in data.items():
        ws.append([k, v])

    out = BytesIO()
    wb.save(out)
    out.seek(0)

    return send_file(
        out,
        as_attachment=True,
        download_name=f"CLO_Only_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"
    )
