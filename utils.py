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
# utils.py
def get_assessment(plo, bloom, domain):
    b = bloom.lower().strip()
    d = domain.lower().strip()

    cognitive = {
        "Medical & Health": {
            "remember": ["MCQ", "Quiz", "Recall questions"],
            "understand": ["Short answer", "Concept explanation"],
            "apply": ["Case-based discussion", "Short case", "Screening task"],
            "analyze": ["Case analysis", "Journal critique"],
            "analyse": ["Case analysis", "Journal critique"],
            "evaluate": ["Long case", "Viva Voce", "Clinical decision justification"],
            "create": ["Clinical management plan", "Health intervention proposal"]
        },
        "Computer Science & IT": {
            "remember": ["MCQ", "Quiz"],
            "understand": ["Short answer", "Code explanation"],
            "apply": ["Programming assignment", "Coding exercise"],
            "analyze": ["Code analysis", "Debugging task"],
            "analyse": ["Code analysis", "Debugging task"],
            "evaluate": ["Code review", "System evaluation report"],
            "create": ["Software project", "Capstone project"]
        },
        "Engineering & Technology": {
            "remember": ["Test", "Quiz"],
            "understand": ["Technical explanation"],
            "apply": ["Problem-solving assignment", "Design exercise"],
            "analyze": ["System analysis", "Technical report"],
            "analyse": ["System analysis", "Technical report"],
            "evaluate": ["Design evaluation", "Oral presentation"],
            "create": ["Design project", "Capstone project"]
        },
        "Social Sciences": {
            "remember": ["Test", "Reading quiz"],
            "understand": ["Essay", "Discussion"],
            "apply": ["Case study", "Fieldwork report"],
            "analyze": ["Thematic analysis", "Policy analysis"],
            "analyse": ["Thematic analysis", "Policy analysis"],
            "evaluate": ["Critical review", "Oral presentation"],
            "create": ["Research project", "Policy proposal"]
        },
        "Education": {
            "remember": ["Test", "Quiz"],
            "understand": ["Essay", "Reflection"],
            "apply": ["Lesson plan", "Microteaching"],
            "analyze": ["Teaching reflection report"],
            "analyse": ["Teaching reflection report"],
            "evaluate": ["Teaching evaluation", "Portfolio review"],
            "create": ["Curriculum design project", "Action research"]
        },
        "Business & Management": {
            "remember": ["Test", "Quiz"],
            "understand": ["Essay", "Case discussion"],
            "apply": ["Business case study", "Problem-solving assignment"],
            "analyze": ["Financial analysis", "Market analysis"],
            "analyse": ["Financial analysis", "Market analysis"],
            "evaluate": ["Strategy evaluation", "Oral presentation"],
            "create": ["Business plan", "Consultancy project"]
        },
        "Arts & Humanities": {
            "remember": ["Quiz", "Visual identification"],
            "understand": ["Essay", "Artwork interpretation"],
            "apply": ["Studio exercise", "Creative task"],
            "analyze": ["Artwork analysis", "Critical review"],
            "analyse": ["Artwork analysis", "Critical review"],
            "evaluate": ["Portfolio critique", "Oral presentation"],
            "create": ["Creative project", "Final portfolio"]
        }
    }

    affective = {
        "receive": ["Reflection log", "Learning journal"],
        "respond": ["Participation", "Peer feedback", "Discussion activity"],
        "value": ["Values / ethics essay", "Reflective portfolio"],
        "organization": ["Group portfolio", "Team-based project"],
        "characterization": ["Professional behaviour assessment", "360° feedback"]
    }

    psychomotor = {
        "perception": ["Observation", "Recognition task"],
        "set": ["Preparation checklist", "Readiness assessment"],
        "guided response": ["Guided task", "Supervised practical"],
        "mechanism": ["Skills test", "Practical examination"],
        "complex overt response": ["OSCE", "Simulation assessment"],
        "adaptation": ["Adapted task", "Advanced practical"],
        "origination": ["Capstone practical", "Independent performance task"]
    }

    if d == "cognitive":
        return {field: items[b] for field, items in cognitive.items() if b in items}
    if d == "affective":
        return {"Affective domain": affective.get(b, [])}
    if d == "psychomotor":
        return {"Psychomotor domain": psychomotor.get(b, [])}

    return {}
    
    def get_evidence_for(assessment):
    a = assessment.lower().strip()

    mapping = {
        "mcq": ["Score report"],
        "quiz": ["Quiz score"],
        "test": ["Test score report"],
        "recall": ["Marked answer script"],

        "short answer": ["Marked answer script"],
        "essay": ["Written essay"],
        "concept": ["Written explanation"],

        "case": ["Case report / assessment form"],
        "analysis": ["Analysis worksheet"],
        "critique": ["Written critique"],

        "project": ["Project report"],
        "proposal": ["Proposal document"],

        "skills": ["Skills checklist"],
        "osce": ["OSCE score sheet"],
        "simulation": ["Simulation checklist"],

        "presentation": ["Presentation rubric"],
        "portfolio": ["Portfolio evidence"],
        "reflection": ["Reflection journal"]
    }

    evidence = []
    for k, v in mapping.items():
        if k in a:
            evidence.extend(v)

    return list(dict.fromkeys(evidence)) if evidence else ["Assessment evidence"]

