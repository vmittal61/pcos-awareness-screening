from pathlib import Path
from datetime import date
from io import BytesIO
import html
import json

import joblib
import numpy as np
import pandas as pd
import streamlit as st
from pcos_report import build_pdf, IMPORTANT

BASE = Path(__file__).resolve().parent
SYM_MODEL_PATH = BASE / "pcos_symptom_logistic_regression.joblib"
ENH_MODEL_PATH = BASE / "pcos_enhanced_rbf_svm.joblib"
METRICS_PATH = BASE / "model_comparison.json"

st.set_page_config(page_title="PCOS Awareness", page_icon="✿", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:ital,wght@0,500;0,600;0,700;1,500&display=swap');
:root {
  --ink:#243A35; --muted:#687A73; --teal:#197C69; --deep:#17483E;
  --mint:#EAF3ED; --paper:#FAF8F1; --line:#DFE5DA; --rust:#B65D43;
}
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background:var(--paper); color:var(--ink);}
.block-container {max-width:1120px; padding-top:1.25rem; padding-bottom:3rem;}
h1,h2,h3 {color:var(--ink)!important; letter-spacing:-.025em;}
h1 {font-family:'Playfair Display',serif!important; font-size:2.55rem!important; font-weight:600!important;}
h2 {font-family:'Playfair Display',serif!important; font-size:1.75rem!important;}
h3 {font-size:1.12rem!important; font-weight:700!important;}
p,label {color:var(--ink);}
[data-testid="stHeader"] {background:transparent;}
.hero {background:linear-gradient(120deg,#E8F1E9 0%,#F4F2E8 100%); border:1px solid #DCE6DA;
       border-radius:24px; padding:2.2rem 2rem; margin:.3rem 0 1.2rem;}
.eyebrow {text-transform:uppercase; letter-spacing:.18em; color:var(--teal); font-size:.7rem;
          font-weight:700; text-align:center; margin-bottom:.8rem;}
.hero h1 {text-align:center; margin:0 auto; max-width:800px; line-height:1.12!important;}
.hero p {text-align:center; max-width:760px; margin:.85rem auto 0; color:#5F7169; line-height:1.65;}
.kicker {text-transform:uppercase; letter-spacing:.15em; color:var(--teal); font-size:.7rem;
         font-weight:700; margin:1.5rem 0 .35rem;}
.section-intro {color:var(--muted); margin-top:-.35rem; line-height:1.55;}
.card {background:white; border:1px solid var(--line); border-radius:18px; padding:1.15rem 1.25rem;}
div[data-baseweb="select"]>div, div[data-baseweb="input"]>div {border-radius:10px!important;
  border-color:var(--line)!important; background:white!important;}
.stButton>button, .stDownloadButton>button {background:var(--teal)!important; color:white!important;
  border:0!important; border-radius:11px!important; font-weight:700!important; min-height:3rem;}
.stButton>button:hover, .stDownloadButton>button:hover {background:var(--deep)!important;}
[data-testid="stMetric"] {background:var(--mint); border:1px solid #D5E4D8; padding:1rem; border-radius:16px;}
[data-testid="stMetricValue"] {color:var(--deep); font-weight:700;}
div[data-testid="stAlert"] {border-radius:12px;}
hr {border-color:var(--line);}
.result-copy {background:white; border-left:4px solid #78A88E; border-radius:12px;
              padding:1rem 1.1rem; margin:.6rem 0 1rem; line-height:1.65;}
.download-panel {background:#17483E; border-radius:18px; padding:1.15rem 1.35rem; margin-top:1.2rem;}
.download-panel p {color:#E5EFE8; margin:0;}
.download-panel strong {color:white; font-size:1.08rem;}
.small-muted {font-size:.85rem; color:var(--muted);}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class="hero">
  <div class="eyebrow">PCOS awareness · Personal check-in</div>
  <h1>Understand the changes you’ve been noticing</h1>
  <p>Answer a few questions about your symptoms. If you already have blood-test or ultrasound results,
  you can add the values here for a more complete experimental estimate.</p>
</div>
""", unsafe_allow_html=True)

st.info(
    "This is an educational research prototype, not a diagnosis or medical triage tool. "
    "The model score is not your personal chance of having PCOS. A low score does not rule out PCOS "
    "or another condition."
)

if not all(path.exists() for path in [SYM_MODEL_PATH, ENH_MODEL_PATH, METRICS_PATH]):
    st.error(
        "The trained model files are missing. Keep these files in the same folder as app.py: "
        "pcos_symptom_logistic_regression.joblib, pcos_enhanced_rbf_svm.joblib and model_comparison.json."
    )
    st.stop()

sym_bundle = joblib.load(SYM_MODEL_PATH)
clinical_bundle = joblib.load(ENH_MODEL_PATH)
_ = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

SYMPTOM_FEATURES = sym_bundle["features"]
CLINICAL_FEATURES = [c for c in clinical_bundle["features"] if c not in SYMPTOM_FEATURES]

FEATURE_LABELS = {
    " Age (yrs)": "Age",
    "Cycle(R/I)": "Menstrual-cycle pattern",
    "Weight gain(Y/N)": "Unexplained weight gain",
    "hair growth(Y/N)": "Increased facial or body hair",
    "Skin darkening (Y/N)": "Darker skin around neck or folds",
    "Hair loss(Y/N)": "Scalp hair thinning or hair loss",
    "Pimples(Y/N)": "Persistent acne",
    "BMI": "BMI",
    "Cycle length(days)": "Cycle length",
    "FSH(mIU/mL)": "FSH",
    "LH(mIU/mL)": "LH",
    "FSH/LH": "FSH-to-LH ratio",
    "TSH (mIU/L)": "TSH",
    "AMH(ng/mL)": "AMH",
    "PRL(ng/mL)": "Prolactin",
    "Vit D3 (ng/mL)": "Vitamin D",
    "Follicle No. (L)": "Left ovarian follicle count",
    "Follicle No. (R)": "Right ovarian follicle count",
    "Avg. F size (L) (mm)": "Average left follicle size",
    "Avg. F size (R) (mm)": "Average right follicle size",
    "Endometrium (mm)": "Endometrial thickness",
}
UNITS = {
    "BMI": "kg/m²", "Cycle length(days)": "days", "FSH(mIU/mL)": "mIU/mL",
    "LH(mIU/mL)": "mIU/mL", "FSH/LH": "ratio", "TSH (mIU/L)": "mIU/L",
    "AMH(ng/mL)": "ng/mL", "PRL(ng/mL)": "ng/mL", "Vit D3 (ng/mL)": "ng/mL",
    "Follicle No. (L)": "count", "Follicle No. (R)": "count",
    "Avg. F size (L) (mm)": "mm", "Avg. F size (R) (mm)": "mm",
    "Endometrium (mm)": "mm",
}

QUESTIONS = [
    ("cycle", "How would you describe your menstrual cycles?", "cycle"),
    ("weight", "Have you noticed unexplained weight gain?", "binary"),
    ("hair", "Have you noticed increased facial or body hair?", "binary"),
    ("skin", "Have you noticed darker skin around your neck or skin folds?", "binary"),
    ("loss", "Have you noticed scalp hair thinning or hair loss?", "binary"),
    ("acne", "Have you experienced persistent acne?", "binary"),
]

def current_unknown_count(exclude_key=None):
    keys = [f"answer_{key}" for key, _, _ in QUESTIONS if key != exclude_key]
    return sum(st.session_state.get(key) == "Not sure" for key in keys)

st.markdown('<div class="kicker">Your symptoms</div>', unsafe_allow_html=True)
st.header("Symptoms you’re noticing")
st.markdown(
    '<p class="section-intro">Choose the answer that best reflects what you have noticed. '
    'All questions begin unanswered so you can select the response that fits.</p>',
    unsafe_allow_html=True
)

age = st.number_input(
    "Age (years)", min_value=12.0, max_value=80.0, value=None,
    step=0.5, format="%.1f", placeholder="Enter age", key="age_input"
)

answers = {}
left, right = st.columns(2)
for index, (key, label, kind) in enumerate(QUESTIONS):
    container = left if index < 3 else right
    with container:
        other_unknowns = current_unknown_count(exclude_key=key)
        choices = ["Choose an answer"]
        choices += ["Regular", "Irregular"] if kind == "cycle" else ["Yes", "No"]
        if other_unknowns == 0:
            choices.append("Not sure")
        state_key = f"answer_{key}"
        # If a previous selection becomes unavailable because another answer is Not sure,
        # reset it to unanswered rather than silently changing the response.
        if st.session_state.get(state_key) not in choices:
            st.session_state[state_key] = "Choose an answer"
        answers[key] = st.selectbox(label, choices, index=0, key=state_key)

unknown_count = sum(value == "Not sure" for value in answers.values())
if unknown_count == 1:
    st.info(
        "One answer is marked “Not sure”. To keep the estimate as consistent as possible, "
        "the remaining questions now require a Yes/No or Regular/Irregular response."
    )

st.markdown("---")
st.markdown('<div class="kicker">Existing clinical reports</div>', unsafe_allow_html=True)
st.header("Have blood-test or ultrasound results?")
st.markdown(
    '<p class="section-intro">Have blood-test or ultrasound results? Enter the values provided on your report. '
    'Leave fields blank if they are not included.</p>',
    unsafe_allow_html=True
)

clinical = {}
col_a, col_b = st.columns(2)
for index, feature in enumerate(CLINICAL_FEATURES):
    with (col_a if index % 2 == 0 else col_b):
        clinical[feature] = st.number_input(
            f"{FEATURE_LABELS.get(feature, feature)} · {UNITS.get(feature, 'value')}",
            value=None, min_value=0.0, max_value=100000.0, step=0.1,
            format="%.2f", placeholder="Optional", key=f"clinical_{feature}"
        )

consent = st.checkbox(
    "I understand this is an experimental educational estimate, not a diagnosis.",
    key="consent"
)
submitted = st.button("Review My Symptom Pattern", use_container_width=True)

def encode_yes(value):
    return np.nan if value == "Not sure" else (1.0 if value == "Yes" else 0.0)

def encode_cycle(value):
    return np.nan if value == "Not sure" else (2.0 if value == "Regular" else 4.0)

def safe_paragraph(text, style):
    return Paragraph(html.escape(str(text)), style)

if submitted:
    if not consent:
        st.error("Please confirm the educational-use notice before continuing.")
        st.stop()
    if age is None:
        st.error("Please enter your age.")
        st.stop()

    unanswered = [label for key, label, _ in QUESTIONS if answers[key] == "Choose an answer"]
    if unanswered:
        st.error("Please answer each symptom question before reviewing your pattern.")
        st.stop()
    if unknown_count > 1:
        st.error("Please select Not sure for no more than one symptom question.")
        st.stop()

    symptom_row = {
        " Age (yrs)": float(age),
        "Cycle(R/I)": encode_cycle(answers["cycle"]),
        "Weight gain(Y/N)": encode_yes(answers["weight"]),
        "hair growth(Y/N)": encode_yes(answers["hair"]),
        "Skin darkening (Y/N)": encode_yes(answers["skin"]),
        "Hair loss(Y/N)": encode_yes(answers["loss"]),
        "Pimples(Y/N)": encode_yes(answers["acne"]),
    }
    row = pd.DataFrame([symptom_row])
    provided_clinical = {feature: float(value) for feature, value in clinical.items() if value is not None}
    use_clinical_model = bool(provided_clinical)
    selected_bundle = clinical_bundle if use_clinical_model else sym_bundle
    model_name = "RBF Support Vector Machine (SVM)" if use_clinical_model else "Logistic Regression"
    model = selected_bundle["model"]
    features = selected_bundle["features"]

    for feature in CLINICAL_FEATURES:
        row[feature] = provided_clinical.get(feature, np.nan)

    uncertainty_note = ""
    if unknown_count == 1:
        unknown_key = next(key for key, value in answers.items() if value == "Not sure")
        unknown_feature = {
            "cycle": "Cycle(R/I)",
            "weight": "Weight gain(Y/N)",
            "hair": "hair growth(Y/N)",
            "skin": "Skin darkening (Y/N)",
            "loss": "Hair loss(Y/N)",
            "acne": "Pimples(Y/N)",
        }[unknown_key]
        possible_values = [2.0, 4.0] if unknown_key == "cycle" else [0.0, 1.0]
        possible_scores = []
        for possible_value in possible_values:
            candidate = row.copy()
            candidate.loc[0, unknown_feature] = possible_value
            possible_scores.append(float(model.predict_proba(candidate[features])[:, 1][0]))
        score = float(np.mean(possible_scores))
        uncertainty_note = (
            "One answer was marked Not sure. The model was evaluated under both possible "
            "responses and the two outputs were averaged. This is an experimental workaround, "
            "not a validated method for handling uncertain answers."
        )
    else:
        score = float(model.predict_proba(row[features])[:, 1][0])

    symptom_rows = [(label, answers[key]) for key, label, kind in QUESTIONS]
    positives = [key for key, _, _ in QUESTIONS if answers[key] in ("Yes", "Irregular")]
    irregular = answers["cycle"] == "Irregular"

    st.markdown("---")
    st.markdown('<div class="kicker">Your check-in</div>', unsafe_allow_html=True)
    st.header("What you’ve noticed")

    if irregular or any(answers[key] == "Yes" for key in ("hair", "skin")):
        intro = (
            "Some of the changes you selected — particularly cycle irregularity, increased facial "
            "or body hair, or darker skin around folds — are worth discussing with a healthcare "
            "professional. They can be associated with PCOS, but they can also have other causes."
        )
    elif positives:
        intro = (
            "You’ve noticed changes involving areas such as weight, skin or hair. These concerns "
            "are common and can have several explanations. Their presence alone does not establish PCOS."
        )
    else:
        intro = (
            "You have not marked the listed symptoms as present. That can be reassuring, but this "
            "short check-in cannot rule out PCOS or other conditions. If something continues to concern "
            "you, it is reasonable to get it assessed."
        )
    st.markdown(f'<div class="result-copy">{html.escape(intro)}</div>', unsafe_allow_html=True)

    st.subheader("Your experimental model score")
    st.metric("Uncalibrated model output · not a personal probability", f"{score*100:.1f}%")
    st.caption(f"Model used: {model_name}.")
    if use_clinical_model:
        st.caption(
            "Your entered clinical values were included. Any report fields left blank were handled "
            "by the model’s trained imputation pipeline; they were not treated as normal results."
        )
    else:
        st.caption("No clinical values were entered, so the symptom-only model was used.")
    if uncertainty_note:
        st.caption(uncertainty_note)

    st.subheader("What to do next")
    steps = []
    if irregular:
        steps.append(
            "Track the first day of each period and the time between cycles for the next few months. "
            "This gives a clearer picture of how regular your cycles are."
        )
    if answers["hair"] == "Yes" or answers["acne"] == "Yes" or answers["loss"] == "Yes":
        steps.append(
            "Note when the skin or hair changes began and whether they are becoming more noticeable. "
            "A short timeline or a few dated photos may help you describe the changes."
        )
    if answers["weight"] == "Yes":
        steps.append(
            "If your weight has changed unexpectedly, note when it happened and any other changes "
            "you noticed. Avoid crash diets or unprescribed weight-loss products."
        )
    if use_clinical_model:
        steps.append(
            "Keep your original blood-test or ultrasound reports. A healthcare professional can "
            "interpret the values using the report’s reference ranges and your medical history."
        )
    else:
        steps.append(
            "If you already have blood-test or ultrasound reports, keep them together. You do not "
            "need to arrange tests just to complete this check-in."
        )
    if irregular or any(answers[key] == "Yes" for key in ("hair", "skin", "loss", "acne", "weight")):
        steps.append(
            "Consider booking a routine appointment with a gynaecologist or another qualified "
            "healthcare professional, especially if the changes persist or affect your wellbeing."
        )
    else:
        steps.append(
            "If you remain concerned or notice new changes, arrange a routine appointment with a "
            "qualified healthcare professional to discuss whether an assessment is needed."
        )
    steps = steps[:4]
    for step in steps:
        st.markdown(f"- {step}")

    if provided_clinical:
        st.subheader("Values you entered")
        display_rows = [
            (FEATURE_LABELS.get(feature, feature),
             f"{value:g} {UNITS.get(feature, '')}".strip())
            for feature, value in provided_clinical.items()
        ]
        for label, value in display_rows:
            st.markdown(f"**{label}:** {value}")

    st.warning(
        "**Seek urgent medical care** for severe or sudden pelvic pain, fainting, very heavy bleeding, "
        "or if you feel acutely unwell."
    )

    clinical_values = [
        (
            FEATURE_LABELS.get(feature, feature),
            provided_clinical.get(feature),
            UNITS.get(feature, "")
        )
        for feature in CLINICAL_FEATURES
    ]

    pdf_buffer = BytesIO()
    build_pdf(
        pdf_buffer,
        {
            "created": date.today(),
            "age": f"{float(age):g}",
            "score": score * 100,
            "model_name": model_name,
            "not_sure_count": unknown_count,
            "symptoms": symptom_rows,
            "clinical": clinical_values,
            "steps": steps,
            "important": IMPORTANT,
        }
    )
    pdf = pdf_buffer.getvalue()
    st.markdown(
        '<div class="download-panel"><strong>Your summary is ready.</strong>'
        '<p>Download a copy of your answers, model output and next steps for your own reference.</p></div>',
        unsafe_allow_html=True
    )
    st.download_button(
        "Download Summary as PDF",
        data=pdf,
        file_name="pcos_awareness_summary.pdf",
        mime="application/pdf",
        use_container_width=True
    )