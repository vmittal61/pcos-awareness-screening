from pathlib import Path
import json

import joblib
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SYM_PATH = ROOT / "pcos_symptom_logistic_regression.joblib"
CLIN_PATH = ROOT / "pcos_enhanced_rbf_svm.joblib"
METRICS_PATH = ROOT / "model_comparison.json"

for path in [SYM_PATH, CLIN_PATH, METRICS_PATH]:
    assert path.exists(), f"Missing deploy artifact: {path.name}"

symptom = joblib.load(SYM_PATH)
clinical = joblib.load(CLIN_PATH)
metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))

assert set(symptom) >= {"model", "features", "threshold"}
assert set(clinical) >= {"model", "features", "threshold"}
assert len(symptom["features"]) == 7
assert len(clinical["features"]) == 21

# Smoke-test both model paths using the feature order stored with each artifact.
symptom_row = pd.DataFrame([{
    feature: (
        25.0 if feature.strip() == "Age (yrs)" else
        2.0 if feature == "Cycle(R/I)" else
        0.0 if feature in {
            "Weight gain(Y/N)", "hair growth(Y/N)", "Skin darkening (Y/N)",
            "Hair loss(Y/N)", "Pimples(Y/N)"
        } else np.nan
    )
    for feature in symptom["features"]
}])
symptom_output = symptom["model"].predict_proba(symptom_row[symptom["features"]])[:, 1]
assert symptom_output.shape == (1,)
assert np.isfinite(symptom_output[0])

clinical_row = symptom_row.copy()
for feature in clinical["features"]:
    if feature not in clinical_row.columns:
        clinical_row[feature] = np.nan
clinical_output = clinical["model"].predict_proba(clinical_row[clinical["features"]])[:, 1]
assert clinical_output.shape == (1,)
assert np.isfinite(clinical_output[0])

assert metrics["dataset_rows"] == 541
print("Both model artefacts loaded and returned finite predictions.")
