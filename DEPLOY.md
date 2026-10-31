# Deploy the PCOS Awareness app

The repository is structured for Streamlit Community Cloud.

## App configuration
- GitHub repository: `vmittal61/pcos-awareness-screening`
- Branch: `main`
- Entrypoint: `app.py`
- Dependency file: `requirements.txt`
- Python: choose Python 3.11 in the Community Cloud deploy form.

The app expects these files in the repository root:
- `pcos_symptom_logistic_regression.joblib`
- `pcos_enhanced_rbf_svm.joblib`
- `model_comparison.json`

They are committed in this repository. The app also keeps analysis datasets and plots under `data/` and `plots/`.

## Deploy from GitHub
1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with GitHub.
2. Select **Create app**.
3. Choose **Yup, I have an app**.
4. Set repository to `vmittal61/pcos-awareness-screening`.
5. Set branch to `main`.
6. Set main file path to `app.py`.
7. Choose Python 3.11 and deploy.

If the repository is missing from the picker, open Streamlit Community Cloud settings → Linked accounts → Source control and authorize Streamlit to access your GitHub account/repository. The GitHub repository must be public or explicitly granted to the Streamlit GitHub connection.

## Local run
```bash
python -m pip install -r requirements.txt
streamlit run app.py
``

After deployment, commits pushed to `main` are the app's source of truth and trigger an update in Community Cloud.
