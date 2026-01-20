# utils.py

import os
import pandas as pd

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
WORKBOOK_PATH = os.path.join(BASE_DIR, "SCLOG.xlsx")

# -------------------------
# LOAD EXCEL
# -------------------------
def load_df(sheet_name):
    if not os.path.exists(WORKBOOK_PATH):
        return pd.DataFrame()
    try:
        return pd.read_excel(WORKBOOK_PATH, sheet_name=sheet_name, engine="openpyxl")
    except:
        return pd.DataFrame()

# -------------------------
# PLO DETAILS
# -------------------------
def get_plo_details(plo, profile="sc"):
    from app import PROFILE_SHEET_MAP
    sheet = PROFILE_SHEET_MAP.get(profile, "Mapping")
    df = load_df(sheet)
    if df.empty:
        return None

    df.columns = [str(c).strip() for c in df.columns]
    col_plo = df.columns[0]
    mask = df[col_plo].astype(str).str.upper() == str(plo).upper()
    if not mask.any():
        return None

    row = df[mask].iloc[0]
    return {
        "SC_Code": row.get("SC Code", ""),
        "SC_Desc": row.get("SC Description", ""),
        "VBE": row.get("VBE", ""),
        "Domain": row.get("Domain", "")
    }

# -------------------------
# META (CRITERION + CONDITION)
# -------------------------
def get_meta_data(plo, bloom, profile="sc"):
    details = get_plo_details(plo, profile)
    if not details:
        return {}

    domain = details["Domain"].lower()
    criterion = ""
    condition = ""

    df = load_df("Criterion")
    if not df.empty:
        df.columns = [c.strip() for c in df.columns]
        mask = (
            df.iloc[:,0].str.lower() == domain
        ) & (
            df.iloc[:,1].str.lower() == bloom.lower()
        )
        if mask.any():
            row = df[mask].iloc[0]
            if len(row) > 2: criterion = str(row.iloc[2])
            if len(row) > 3: condition = str(row.iloc[3])

    defaults = {
        "cognitive": "interpreting tasks",
        "affective": "engaging with peers",
        "psychomotor": "performing skills"
    }

    connector = "by" if domain == "psychomotor" else "when"
    return {
        "criterion": criterion,
        "condition": f"{connector} {condition or defaults.get(domain,'')}"
    }

# -------------------------
# ASSESSMENT
# -------------------------
def get_assessment(plo, bloom, domain):
    b = bloom.lower()
    d = domain.lower()

    cognitive = {
        "remember": ["MCQ","Recall quiz"],
        "understand": ["Short answer","Concept explanation"],
        "apply": ["Case study","Problem-solving"],
        "analyze": ["Data analysis","Critique"],
        "analyse": ["Data analysis","Critique"],
        "evaluate": ["Evaluation report"],
        "create": ["Design project","Proposal"]
    }

    affective = {
        "receive": ["Reflection log"],
        "respond": ["Participation","Peer feedback"],
        "value": ["Value essay"],
        "organization": ["Group portfolio"],
        "characterization": ["Professional behaviour assessment"]
    }

    psychomotor = {
        "perception": ["Observation"],
        "set": ["Preparation checklist"],
        "guided response": ["Guided task"],
        "mechanism": ["Skills test"],
        "complex overt response": ["OSCE"],
        "adaptation": ["Adapted task"],
        "origination": ["Capstone practical"]
    }

    if d == "affective": return affective.get(b, [])
    if d == "psychomotor": return psychomotor.get(b, [])
    return cognitive.get(b, [])

# -------------------------
# EVIDENCE
# -------------------------
def get_evidence_for(assessment):
    a = assessment.lower()
    mapping = {
        "mcq": ["score report"],
        "quiz": ["quiz score"],
        "analysis": ["analysis sheet"],
        "critique": ["written critique"],
        "skills": ["skills checklist"],
        "osce": ["OSCE score sheet"],
        "reflection": ["reflection journal"]
    }
    for k,v in mapping.items():
        if k in a:
            return v
    return ["assessment evidence"]
