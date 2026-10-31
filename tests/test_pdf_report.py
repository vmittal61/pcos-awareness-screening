from datetime import date
from io import BytesIO
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pcos_report import IMPORTANT, build_pdf

buffer = BytesIO()
build_pdf(buffer, {
    "created": date(2026, 10, 31),
    "age": "24",
    "score": 57.4,
    "model_name": "RBF-SVM",
    "not_sure_count": 1,
    "symptoms": [
        ("Menstrual-cycle pattern", "Irregular"),
        ("Unexplained weight gain", "Yes"),
        ("Increased facial or body hair", "Not sure"),
        ("Darker skin around neck or folds", "No"),
        ("Scalp hair thinning or hair loss", "No"),
        ("Persistent acne", "Yes"),
    ],
    "clinical": [
        ("BMI", 23.4, "kg/m²"), ("Cycle length", None, "days"),
        ("FSH", None, "mIU/mL"), ("LH", None, "mIU/mL"),
        ("FSH/LH", None, ""), ("TSH", None, "mIU/L"),
        ("AMH", None, "ng/mL"), ("PRL", None, "ng/mL"),
        ("Vitamin D", None, "ng/mL"), ("Left follicle count", None, ""),
        ("Right follicle count", None, ""), ("Left follicle size", None, "mm"),
        ("Right follicle size", None, "mm"), ("Endometrial thickness", None, "mm"),
    ],
    "steps": [
        "Track cycle dates and note changes.",
        "Keep existing reports together.",
        "Discuss persistent symptoms with a qualified healthcare professional.",
    ],
    "important": IMPORTANT,
})

pdf = buffer.getvalue()
assert pdf.startswith(b"%PDF-"), "PDF signature missing"
assert len(pdf) > 3000, f"PDF unexpectedly small: {len(pdf)} bytes"
print(f"Updated PDF report generated successfully ({len(pdf)} bytes).")
