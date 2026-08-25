"""
FloodShield - Machine Learning Training Pipeline (MVP)
=====================================================
This script trains a supervised multi-class flood risk classification model
using the processed district-level dataset (`flood_risk_dataset.csv`).

ML Formulation & Data Leakage Note:
----------------------------------
1. Target Variable: `flood_risk_level` ('Low', 'Moderate', 'High', 'Very High').
2. Data Leakage Prevention:
   - `flood_risk_score` is strictly excluded from feature inputs because it was
     used to define the continuous ground-truth risk index during preprocessing.
   - `district_name` is an administrative identifier and is excluded to ensure
     the model learns generalizable geographical, hazard, and vulnerability patterns.
3. MVP Scope:
   - This model serves as an operational baseline risk classification engine.
   - It captures non-linear interactions across satellite inundation exposure,
     historical flood frequency/duration, casualty impacts, and seasonal precipitation.
   - It outputs calibrated risk tiers and class probabilities for backend API services.
"""

import os
import sys
import logging
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("FloodShield.TrainModel")


def resolve_project_paths() -> Tuple[str, str]:
    """
    Dynamically locates the processed dataset and target models directory
    regardless of whether the script is run from project root, backend, or ml.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))

    # Candidate dataset paths
    candidate_data_paths = [
        os.path.join(project_root, "ml", "datasets", "processed", "flood_risk_dataset.csv"),
        os.path.join(project_root, "backend", "ml", "datasets", "processed", "flood_risk_dataset.csv"),
        os.path.join(current_dir, "..", "datasets", "processed", "flood_risk_dataset.csv"),
    ]

    data_path = None
    for p in candidate_data_paths:
        norm_p = os.path.normpath(p)
        if os.path.isfile(norm_p):
            data_path = norm_p
            break

    if not data_path:
        raise FileNotFoundError(
            f"Processed dataset 'flood_risk_dataset.csv' not found in candidate locations: {candidate_data_paths}"
        )

    # Candidate models directory
    candidate_models_dirs = [
        os.path.join(project_root, "ml", "models"),
        os.path.join(project_root, "backend", "ml", "models"),
        os.path.join(current_dir, "..", "models"),
    ]

    models_dir = None
    for d in candidate_models_dirs:
        norm_d = os.path.normpath(d)
        if os.path.isdir(norm_d):
            models_dir = norm_d
            break

    if not models_dir:
        # Default to standard ml/models
        models_dir = os.path.normpath(os.path.join(project_root, "ml", "models"))
        os.makedirs(models_dir, exist_ok=True)

    return data_path, models_dir


def inspect_dataset(df: pd.DataFrame) -> Tuple[List[str], List[str], str]:
    """
    Inspects dataset columns and data types, partitions features into numeric
    and categorical sets, and prevents data leakage by excluding derived target scores.
    """
    logger.info(f"Inspecting dataset: {df.shape[0]} samples x {df.shape[1]} columns")

    target_column = "flood_risk_level"
    if target_column not in df.columns:
        raise ValueError(f"Target column '{target_column}' missing from dataset.")

    # Explicitly exclude identifier and direct formula components that cause leakage
    leakage_and_id_cols = {"flood_risk_score", "district_name", target_column}

    candidate_features = [c for c in df.columns if c not in leakage_and_id_cols]

    categorical_features = []
    numeric_features = []

    for col in candidate_features:
        if df[col].dtype == "object" or col == "state":
            categorical_features.append(col)
        else:
            numeric_features.append(col)

    logger.info(f"Feature Selection: {len(numeric_features)} numeric features, {len(categorical_features)} categorical features.")
    logger.info(f"Excluded for leakage/identity: {list(leakage_and_id_cols)}")
    return numeric_features, categorical_features, target_column


def build_pipeline(numeric_features: List[str], categorical_features: List[str]) -> Pipeline:
    """
    Constructs an end-to-end scikit-learn Pipeline with preprocessing transformations
    (imputation, scaling, one-hot encoding) bundled directly with the classifier.
    This guarantees identical transformations during backend inference.
    """
    # Numeric preprocessing: median imputation for missing rainfall/hazard values + standard scaling
    numeric_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler())
    ])

    # Categorical preprocessing: constant imputation + one-hot encoding with unknown handling
    categorical_transformer = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="Unknown")),
        ("onehot", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    preprocessor = ColumnTransformer(transformers=[
        ("num", numeric_transformer, numeric_features),
        ("cat", categorical_transformer, categorical_features)
    ])

    # Regularized Random Forest Classifier for robust non-linear risk tier modeling
    classifier = RandomForestClassifier(
        n_estimators=150,
        max_depth=8,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )

    full_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])

    return full_pipeline


def train_and_evaluate(
    data_path: Optional[str] = None,
    output_dir: Optional[str] = None
) -> Tuple[Pipeline, Dict[str, Any]]:
    """
    Loads data, trains the pipeline, evaluates test performance, and saves the joblib artifact.
    """
    if data_path is None or output_dir is None:
        default_data_path, default_models_dir = resolve_project_paths()
        data_path = data_path or default_data_path
        output_dir = output_dir or default_models_dir

    logger.info(f"Loading processed dataset from: {data_path}")
    df = pd.read_csv(data_path)

    # Inspect features
    numeric_features, categorical_features, target_column = inspect_dataset(df)
    feature_cols = numeric_features + categorical_features

    X = df[feature_cols].copy()
    y = df[target_column].copy()

    # Stratified Train/Test Split (80% Train, 20% Test)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    logger.info(f"Dataset split: {len(X_train)} training samples, {len(X_test)} testing samples.")

    # Build and fit pipeline
    pipeline = build_pipeline(numeric_features, categorical_features)
    logger.info("Training Random Forest model pipeline...")
    pipeline.fit(X_train, y_train)

    # Predictions & Evaluation
    y_pred = pipeline.predict(X_test)
    y_pred_proba = pipeline.predict_proba(X_test)

    acc = float(accuracy_score(y_test, y_pred))
    prec_macro = float(precision_score(y_test, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_test, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_test, y_pred, average="macro", zero_division=0))
    f1_weighted = float(f1_score(y_test, y_pred, average="weighted", zero_division=0))

    classes = pipeline.classes_.tolist()
    cm = confusion_matrix(y_test, y_pred, labels=classes)
    cm_df = pd.DataFrame(
        cm,
        index=[f"Actual {c}" for c in classes],
        columns=[f"Pred {c}" for c in classes]
    )

    clf_report = classification_report(y_test, y_pred, labels=classes, zero_division=0)

    # Feature Importances
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]

    cat_ohe = preprocessor.named_transformers_["cat"].named_steps["onehot"]
    cat_feature_names = cat_ohe.get_feature_names_out(categorical_features).tolist()
    all_transformed_features = numeric_features + cat_feature_names

    importances = classifier.feature_importances_
    feat_imp_series = pd.Series(importances, index=all_transformed_features).sort_values(ascending=False)

    # Build model artifact bundle
    artifact_bundle = {
        "pipeline": pipeline,
        "feature_names": feature_cols,
        "numeric_features": numeric_features,
        "categorical_features": categorical_features,
        "target_column": target_column,
        "classes": classes,
        "metrics": {
            "accuracy": acc,
            "precision_macro": prec_macro,
            "recall_macro": rec_macro,
            "f1_macro": f1_macro,
            "f1_weighted": f1_weighted,
        },
        "top_features": feat_imp_series.head(15).to_dict()
    }

    # Save artifact
    output_model_path = os.path.join(output_dir, "flood_risk_model.joblib")
    joblib.dump(artifact_bundle, output_model_path)
    logger.info(f"Saved trained model and preprocessing pipeline to: {output_model_path}")

    # Validation: Test loading and sample inference
    loaded_bundle = joblib.load(output_model_path)
    loaded_pipe = loaded_bundle["pipeline"]
    sample_pred = loaded_pipe.predict(X_test.head(2))
    sample_probs = loaded_pipe.predict_proba(X_test.head(2))
    logger.info(f"Inference smoke test passed. Sample predictions: {sample_pred.tolist()}")

    # Print Summary Report
    print("\n" + "=" * 75)
    print("FLOODSHIELD MODEL TRAINING & EVALUATION SUMMARY")
    print("=" * 75)
    print(f"Model Artifact Saved To: {output_model_path}")
    print(f"Total Features Used: {len(feature_cols)} (Numeric: {len(numeric_features)}, Categorical: {len(categorical_features)})")
    print(f"Train/Test Split: {len(X_train)} train / {len(X_test)} test (Stratified 80/20)")
    print(f"Target Classes: {classes}")
    print("\n--- Key Performance Metrics ---")
    print(f"Accuracy:        {acc:.4f} ({acc*100:.2f}%)")
    print(f"Macro Precision: {prec_macro:.4f}")
    print(f"Macro Recall:    {rec_macro:.4f}")
    print(f"Macro F1-Score:  {f1_macro:.4f}")
    print(f"Weighted F1:     {f1_weighted:.4f}")
    print("\n--- Detailed Classification Report ---")
    print(clf_report)
    print("--- Confusion Matrix ---")
    print(cm_df.to_string())
    print("\n--- Top 10 Most Influential Features ---")
    for rank, (feat, imp) in enumerate(feat_imp_series.head(10).items(), start=1):
        print(f"  {rank:2d}. {feat:35s}: {imp:.4f} ({imp*100:.2f}%)")
    print("=" * 75 + "\n")

    return pipeline, artifact_bundle


if __name__ == "__main__":
    custom_data = sys.argv[1] if len(sys.argv) > 1 else None
    custom_out = sys.argv[2] if len(sys.argv) > 2 else None
    train_and_evaluate(custom_data, custom_out)
