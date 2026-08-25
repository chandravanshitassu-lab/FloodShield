"""
FloodShield - Model Service
===========================
Singleton service that loads the trained FloodShield risk classification model
from `ml/models/flood_risk_model.joblib` and performs inference on district feature inputs.
"""

import os
import logging
from typing import Dict, List, Any, Optional, Union
import pandas as pd
import joblib

logger = logging.getLogger("FloodShield.ModelService")


class FloodRiskModelService:
    """
    Service responsible for loading and querying the trained FloodShield
    scikit-learn risk classification pipeline.
    """
    _instance: Optional["FloodRiskModelService"] = None

    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path or self._resolve_model_path()
        self.pipeline = None
        self.feature_names: List[str] = []
        self.classes: List[str] = []
        self.numeric_features: List[str] = []
        self.categorical_features: List[str] = []
        self.metrics: Dict[str, Any] = {}
        self._load_model()

    @classmethod
    def get_instance(cls, model_path: Optional[str] = None) -> "FloodRiskModelService":
        """Singleton accessor for the model service."""
        if cls._instance is None:
            cls._instance = cls(model_path=model_path)
        return cls._instance

    def _resolve_model_path(self) -> str:
        """
        Dynamically discovers the flood_risk_model.joblib path
        relative to the repository root without hardcoded absolute paths.
        """
        # Directory of this file: backend/app/services/
        current_dir = os.path.dirname(os.path.abspath(__file__))
        # Project root: FloodShield/
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))

        candidate_paths = [
            os.path.join(project_root, "ml", "models", "flood_risk_model.joblib"),
            os.path.join(project_root, "backend", "ml", "models", "flood_risk_model.joblib"),
            os.path.abspath(os.path.join(current_dir, "..", "..", "..", "ml", "models", "flood_risk_model.joblib")),
        ]

        for path in candidate_paths:
            normalized = os.path.normpath(path)
            if os.path.isfile(normalized):
                return normalized

        raise FileNotFoundError(
            f"Trained model artifact 'flood_risk_model.joblib' not found. Checked: {candidate_paths}"
        )

    def _load_model(self) -> None:
        """Loads the serialized model bundle into memory."""
        if not os.path.isfile(self.model_path):
            raise FileNotFoundError(f"Model file not found at: {self.model_path}")

        logger.info(f"Loading FloodShield model bundle from: {self.model_path}")
        bundle = joblib.load(self.model_path)

        if isinstance(bundle, dict) and "pipeline" in bundle:
            self.pipeline = bundle["pipeline"]
            self.feature_names = bundle.get("feature_names", [])
            self.classes = bundle.get("classes", self.pipeline.classes_.tolist())
            self.numeric_features = bundle.get("numeric_features", [])
            self.categorical_features = bundle.get("categorical_features", [])
            self.metrics = bundle.get("metrics", {})
        else:
            # Standalone pipeline fallback
            self.pipeline = bundle
            self.classes = self.pipeline.classes_.tolist()

        logger.info(f"Model successfully loaded with {len(self.feature_names)} expected features and classes: {self.classes}")

    @property
    def is_loaded(self) -> bool:
        """Returns True if the model pipeline is loaded and ready for inference."""
        return self.pipeline is not None

    def predict(self, input_data: Union[Dict[str, Any], pd.DataFrame]) -> Dict[str, Any]:
        """
        Runs inference on the provided input dictionary or DataFrame.

        Parameters
        ----------
        input_data : dict or pd.DataFrame
            Dictionary containing district feature values. Missing optional
            features will be imputed automatically by the pipeline.

        Returns
        -------
        dict
            {
                "flood_risk_level": str,
                "probabilities": dict,
                "confidence": float
            }
        """
        if not self.is_loaded:
            raise RuntimeError("Model pipeline is not loaded.")

        # Convert input dictionary to DataFrame
        if isinstance(input_data, dict):
            # Extract only expected features or default missing ones to None/NaN
            row_dict = {}
            for col in self.feature_names:
                row_dict[col] = input_data.get(col, None)
            df_input = pd.DataFrame([row_dict])
        elif isinstance(input_data, pd.DataFrame):
            # Reindex / ensure expected columns are present
            df_input = input_data.copy()
            for col in self.feature_names:
                if col not in df_input.columns:
                    df_input[col] = None
            df_input = df_input[self.feature_names]
        else:
            raise ValueError(f"Unsupported input data type: {type(input_data)}")

        # Predict class and probabilities using the saved pipeline
        predicted_class = self.pipeline.predict(df_input)[0]
        probabilities_array = self.pipeline.predict_proba(df_input)[0]

        # Map classes to float probabilities
        probs_dict = {
            cls_name: round(float(prob), 4)
            for cls_name, prob in zip(self.classes, probabilities_array)
        }

        confidence = round(float(max(probabilities_array)), 4)

        return {
            "flood_risk_level": str(predicted_class),
            "probabilities": probs_dict,
            "confidence": confidence
        }
