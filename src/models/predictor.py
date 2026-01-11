"""Prediction service for Airbnb Price Predictor."""
from pathlib import Path
from typing import Dict, Union, List
import pandas as pd
from joblib import load
from src.utils.logger import get_logger

logger = get_logger(__name__)


class PricePredictor:
    """Handles price predictions using trained model."""

    def __init__(self, model_path: str):
        """
        Initialize PricePredictor.

        Args:
            model_path: Path to the trained model file
        """
        self.model_path = Path(model_path)
        self.model = self._load_model()
        self.price_labels = ["0-50", "51-100", "101-150", "151-200", "201-500", "501-1000", "1000+"]

    def _load_model(self):
        """Load the trained model from disk."""
        if not self.model_path.exists():
            raise FileNotFoundError(f"Model file not found: {self.model_path}")

        logger.info(f"Loading model from {self.model_path}")
        model = load(self.model_path)
        logger.info("Model loaded successfully")
        return model

    def predict(self, X: pd.DataFrame) -> List[int]:
        """
        Make predictions on input features.

        Args:
            X: DataFrame with preprocessed features

        Returns:
            List of predicted price category indices
        """
        predictions = self.model.predict(X)
        logger.info(f"Made {len(predictions)} predictions")
        return predictions.tolist()

    def predict_proba(self, X: pd.DataFrame) -> List[List[float]]:
        """
        Predict probability distributions for each class.

        Args:
            X: DataFrame with preprocessed features

        Returns:
            List of probability distributions
        """
        if hasattr(self.model, 'predict_proba'):
            probabilities = self.model.predict_proba(X)
            return probabilities.tolist()
        else:
            raise AttributeError("Model does not support probability predictions")

    def predict_price_category(self, X: pd.DataFrame) -> List[str]:
        """
        Predict price categories as human-readable labels.

        Args:
            X: DataFrame with preprocessed features

        Returns:
            List of price category labels (e.g., "0-50", "51-100")
        """
        predictions = self.predict(X)
        categories = [self.price_labels[pred] for pred in predictions]
        return categories

    def predict_single(self, features: Dict) -> Dict:
        """
        Make a prediction for a single listing.

        Args:
            features: Dictionary with feature values

        Returns:
            Dictionary with prediction results
        """
        # Convert single instance to DataFrame
        X = pd.DataFrame([features])

        # Make prediction
        prediction_idx = self.predict(X)[0]
        category = self.price_labels[prediction_idx]

        result = {
            'predicted_category': category,
            'predicted_category_index': prediction_idx
        }

        # Add probability distribution if available
        try:
            probabilities = self.predict_proba(X)[0]
            result['probabilities'] = {
                label: float(prob)
                for label, prob in zip(self.price_labels, probabilities)
            }
        except AttributeError:
            pass

        logger.info(f"Predicted category: {category}")
        return result

    def get_model_info(self) -> Dict:
        """
        Get information about the loaded model.

        Returns:
            Dictionary with model metadata
        """
        info = {
            'model_path': str(self.model_path),
            'model_type': type(self.model).__name__,
            'price_categories': self.price_labels
        }

        # Add model-specific attributes if available
        if hasattr(self.model, 'n_estimators'):
            info['n_estimators'] = self.model.n_estimators
        if hasattr(self.model, 'max_depth'):
            info['max_depth'] = self.model.max_depth
        if hasattr(self.model, 'n_features_in_'):
            info['n_features'] = self.model.n_features_in_

        return info
