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
# GET VERBS
# -------------------------
def get_verbs(plo, bloom, profile="sc"):
    details = get_plo_details(plo, profile)
    if not details:
        return []

    domain = details["Domain"].lower()
    b = bloom.lower()

    return BLOOM_VERBS.get(domain, {}).get(b, [])

# -------------------------
# VERBS (BLOOM × DOMAIN)
# -------------------------

BLOOM_VERBS = {

    # =====================
    # COGNITIVE DOMAIN
    # =====================
    "cognitive": {

        "remember": [
            "Recall", "Recognise", "Identify", "Define", "List",
            "Name", "State", "Label", "Outline"
        ],

        "understand": [
            "Explain", "Describe", "Summarise", "Interpret", "Clarify",
            "Classify", "Discuss", "Illustrate", "Paraphrase"
        ],

        "apply": [
            "Apply", "Use", "Demonstrate", "Implement", "Execute",
            "Carry out", "Solve", "Calculate", "Perform"
        ],

        "analyze": [
            "Analyse", "Differentiate", "Compare", "Contrast", "Examine",
            "Deconstruct", "Investigate", "Categorise", "Relate"
        ],

        "analyse": [  # alias support
            "Analyse", "Differentiate", "Compare", "Contrast", "Examine",
            "Deconstruct", "Investigate", "Categorise", "Relate"
        ],

        "evaluate": [
            "Evaluate", "Assess", "Critique", "Justify", "Appraise",
            "Judge", "Validate", "Review", "Defend", "Prioritise"
        ],

        "create": [
            "Design", "Develop", "Formulate", "Construct", "Propose",
            "Generate", "Produce", "Devise", "Synthesise", "Model"
        ]
    },

    # =====================
    # AFFECTIVE DOMAIN
    # =====================
    "affective": {

        "receiving": [
            "Acknowledge", "Recognise", "Attend", "Notice", "Accept"
        ],

        "responding": [
            "Respond", "Participate", "Contribute", "Engage",
            "Comply", "Discuss", "Follow"
        ],

        "valuing": [
            "Demonstrate", "Commit", "Support", "Appreciate",
            "Advocate", "Respect", "Value"
        ],

        "organization": [
            "Organise", "Integrate", "Prioritise", "Reconcile",
            "Structure", "Align"
        ],

        "characterization": [
            "Demonstrate", "Internalise", "Exemplify",
            "Advocate", "Uphold", "Consistently apply"
        ]
    },

    # =====================
    # PSYCHOMOTOR DOMAIN
    # =====================
    "psychomotor": {

        "perception": [
            "Detect", "Identify", "Recognise", "Distinguish", "Sense"
        ],

        "set": [
            "Prepare", "Initiate", "Position", "Ready", "Adjust"
        ],

        "guided response": [
            "Perform", "Execute", "Imitate", "Follow",
            "Practise", "Replicate"
        ],

        "mechanism": [
            "Operate", "Manipulate", "Calibrate", "Assemble",
            "Measure", "Control"
        ],

        "complex overt response": [
            "Perform", "Execute", "Operate", "Carry out",
            "Demonstrate proficiency"
        ],

        "adaptation": [
            "Adapt", "Modify", "Adjust", "Reconfigure", "Refine"
        ],

        "origination": [
            "Create", "Construct", "Innovate", "Design",
            "Develop new procedures"
        ]
    }
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
