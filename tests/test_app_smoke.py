from streamlit.testing.v1 import AppTest

app = AppTest.from_file("app.py", default_timeout=30).run()
assert not app.exception, "\n".join(str(error.value) for error in app.exception)
print("Streamlit app startup smoke test passed.")
