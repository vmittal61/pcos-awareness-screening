from pathlib import Path

from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
app = AppTest.from_file(str(ROOT / "app.py"), default_timeout=30).run()
assert not app.exception, "\\n".join(str(error.value) for error in app.exception)
print("Streamlit app startup smoke test passed.")
