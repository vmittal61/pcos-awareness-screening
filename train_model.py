
"""Compare Logistic Regression and RBF-SVM on identical stratified splits.
The dataset is tabular: CNN/InceptionResNet are not suitable unless image data is added.
"""
from pathlib import Path
import json, joblib
import numpy as np, pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score, confusion_matrix

BASE=Path(__file__).resolve().parent
df=pd.read_csv(BASE/"PCOS_cleaned.csv")
TARGET="PCOS (Y/N)"
SYM=[" Age (yrs)","Cycle(R/I)","Weight gain(Y/N)","hair growth(Y/N)","Skin darkening (Y/N)","Hair loss(Y/N)","Pimples(Y/N)"]
CLIN=["BMI","Cycle length(days)","FSH(mIU/mL)","LH(mIU/mL)","FSH/LH","TSH (mIU/L)","AMH(ng/mL)","PRL(ng/mL)","Vit D3 (ng/mL)","Follicle No. (L)","Follicle No. (R)","Avg. F size (L) (mm)","Avg. F size (R) (mm)","Endometrium (mm)"]
for c in SYM+CLIN+[TARGET]:
    if c not in df.columns: raise ValueError(f"Missing column: {c}")
y=pd.to_numeric(df[TARGET],errors="coerce"); ok=y.isin([0,1]); df=df.loc[ok].copy(); y=y.loc[ok].astype(int)
def clean(cols):
    X=df[cols].copy()
    for c in cols: X[c]=pd.to_numeric(X[c],errors="coerce")
    X.loc[~X["Cycle(R/I)"].isin([2,4]),"Cycle(R/I)"]=np.nan
    for c in SYM:
        if c.endswith("(Y/N)"): X.loc[~X[c].isin([0,1]),c]=np.nan
    return X
def metrics(y,p,t):
    pred=(p>=t).astype(int); tn,fp,fn,tp=confusion_matrix(y,pred,labels=[0,1]).ravel()
    return {"threshold":round(float(t),3),"accuracy":round(float(accuracy_score(y,pred)),3),
    "precision":round(float(precision_score(y,pred,zero_division=0)),3),
    "sensitivity":round(float(recall_score(y,pred,zero_division=0)),3),
    "specificity":round(float(tn/(tn+fp)),3),"f1":round(float(f1_score(y,pred,zero_division=0)),3),
    "roc_auc":round(float(roc_auc_score(y,p)),3),"false_negatives":int(fn),"false_positives":int(fp),
    "confusion_matrix_TN_FP_FN_TP":[int(tn),int(fp),int(fn),int(tp)]}
idx_train,idx_tmp,y_train,y_tmp=train_test_split(df.index,y,test_size=.4,random_state=42,stratify=y)
idx_val,idx_test,y_val,y_test=train_test_split(idx_tmp,y_tmp,test_size=.5,random_state=43,stratify=y_tmp)
out={"dataset_rows":len(df),"positive_rows":int(y.sum()),"negative_rows":int((y==0).sum()),
"split":"60% train / 20% validation / 20% untouched test; stratified; random_state 42/43",
"models":{},"notes":"CNN/InceptionResNet are not trained: inputs are tabular columns, not images. SVM and Logistic Regression are compared. Test set is not used for threshold selection."}
for name,cols in [("symptom",SYM),("enhanced",SYM+CLIN)]:
    X=clean(cols); Xt,Xv,Xte=X.loc[idx_train],X.loc[idx_val],X.loc[idx_test]
    out["models"][name]={}
    for alg,est in [("logistic_regression",LogisticRegression(max_iter=4000,class_weight="balanced")),
                    ("rbf_svm",SVC(C=1.0,kernel="rbf",gamma="scale",probability=True,class_weight="balanced",random_state=42))]:
        pipe=Pipeline([("imputer",SimpleImputer(strategy="median",add_indicator=True)),("scale",StandardScaler()),("model",est)])
        pipe.fit(Xt,y_train); pv=pipe.predict_proba(Xv)[:,1]
        thresholds=np.arange(.05,.81,.01)
        vals=[(t,recall_score(y_val,pv>=t,zero_division=0),precision_score(y_val,pv>=t,zero_division=0)) for t in thresholds]
        eligible=[v for v in vals if v[1]>=.90]
        threshold=max(eligible,key=lambda v:(v[2],v[0]))[0] if eligible else max(vals,key=lambda v:(v[1],v[2],v[0]))[0]
        ptest=pipe.predict_proba(Xte)[:,1]
        out["models"][name][alg]={"validation":metrics(y_val,pv,threshold),"test":metrics(y_test,ptest,threshold)}
        final=Pipeline([("imputer",SimpleImputer(strategy="median",add_indicator=True)),("scale",StandardScaler()),("model",est)])
        final.fit(pd.concat([Xt,Xv]),pd.concat([y_train,y_val]))
        joblib.dump({"model":final,"features":cols,"threshold":float(threshold),"model_name":alg},BASE/f"pcos_{name}_{alg}.joblib")
        if alg=="logistic_regression":
            joblib.dump({"model":final,"features":cols,"threshold":float(threshold),"model_name":alg},BASE/f"pcos_{name}_model.joblib")
out["feature_audit_warning"]="The target-label generation process is undocumented. Hormone and ultrasound variables may overlap with diagnostic criteria used to assign labels; enhanced performance may be inflated by label leakage."
out["clinical_warning"]="Research/portfolio prototype only. Neither pathway is clinically validated, externally validated, or calibrated for individual diagnosis."
(BASE/"model_comparison.json").write_text(json.dumps(out,indent=2),encoding="utf-8")
print(json.dumps(out,indent=2))
