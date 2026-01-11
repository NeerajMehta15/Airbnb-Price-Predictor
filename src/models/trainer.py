"""Model training for Airbnb Price Predictor."""
from typing import Dict, Tuple
import pandas as pd
import numpy as np
from joblib import dump
from pathlib import Path

from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import (
    RandomForestClassifier,
    GradientBoostingClassifier,
    AdaBoostClassifier
)
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

from src.utils.logger import get_logger

logger = get_logger(__name__)


class ModelTrainer:
    """Handles model training and hyperparameter tuning."""

    def __init__(self, random_state: int = 21):
        """
        Initialize ModelTrainer.

        Args:
            random_state: Random state for reproducibility
        """
        self.random_state = random_state
        self.models = self._initialize_models()
        self.best_model = None
        self.best_model_name = None

    def _initialize_models(self) -> Dict:
        """Initialize classification models for comparison."""
        return {
            'Decision Tree': DecisionTreeClassifier(random_state=self.random_state),
            'Random Forest': RandomForestClassifier(random_state=self.random_state),
            'Gradient Boosting': GradientBoostingClassifier(random_state=self.random_state),
            'AdaBoost': AdaBoostClassifier(random_state=self.random_state),
            'XGBoost': XGBClassifier(
                random_state=self.random_state,
                use_label_encoder=False,
                eval_metric='logloss'
            )
        }

    def split_data(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2
    ) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
        """
        Split data into training and testing sets.

        Args:
            X: Features
            y: Target variable
            test_size: Proportion of data for testing

        Returns:
            Tuple of (X_train, X_test, y_train, y_test)
        """
        logger.info(f"Splitting data with test_size={test_size}")

        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=test_size,
            random_state=self.random_state
        )

        logger.info(f"Training set: {X_train.shape[0]} samples")
        logger.info(f"Testing set: {X_test.shape[0]} samples")

        return X_train, X_test, y_train, y_test

    def compare_models(
        self,
        X_train: pd.DataFrame,
        X_test: pd.DataFrame,
        y_train: pd.Series,
        y_test: pd.Series
    ) -> Dict[str, float]:
        """
        Train and compare multiple models.

        Args:
            X_train: Training features
            X_test: Testing features
            y_train: Training target
            y_test: Testing target

        Returns:
            Dictionary mapping model names to accuracy scores
        """
        logger.info("Comparing models...")
        results = {}

        for model_name, model in self.models.items():
            logger.info(f"Training {model_name}...")

            # Train model
            model.fit(X_train, y_train)

            # Make predictions
            y_pred = model.predict(X_test)

            # Calculate accuracy
            accuracy = accuracy_score(y_test, y_pred)
            results[model_name] = accuracy

            logger.info(f"{model_name} Accuracy: {accuracy:.4f}")

        # Identify best model
        self.best_model_name = max(results, key=results.get)
        self.best_model = self.models[self.best_model_name]

        logger.info(f"Best model: {self.best_model_name} with accuracy {results[self.best_model_name]:.4f}")

        return results

    def tune_hyperparameters(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        param_grid: Dict,
        cv: int = 5,
        scoring: str = 'accuracy',
        n_jobs: int = -1
    ) -> GridSearchCV:
        """
        Perform hyperparameter tuning using GridSearchCV.

        Args:
            X_train: Training features
            y_train: Training target
            param_grid: Dictionary of hyperparameters to search
            cv: Number of cross-validation folds
            scoring: Scoring metric
            n_jobs: Number of parallel jobs

        Returns:
            Fitted GridSearchCV object
        """
        logger.info("Starting hyperparameter tuning...")

        # Use Random Forest for tuning (best performing base model)
        model = RandomForestClassifier(random_state=self.random_state)

        grid_search = GridSearchCV(
            estimator=model,
            param_grid=param_grid,
            scoring=scoring,
            cv=cv,
            n_jobs=n_jobs,
            verbose=2
        )

        grid_search.fit(X_train, y_train)

        logger.info(f"Best parameters: {grid_search.best_params_}")
        logger.info(f"Best cross-validation score: {grid_search.best_score_:.4f}")

        self.best_model = grid_search.best_estimator_
        self.best_model_name = f"Tuned Random Forest"

        return grid_search

    def evaluate_model(
        self,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        model=None
    ) -> Dict:
        """
        Evaluate model performance on test set.

        Args:
            X_test: Testing features
            y_test: Testing target
            model: Model to evaluate (uses best_model if None)

        Returns:
            Dictionary with evaluation metrics
        """
        if model is None:
            model = self.best_model

        if model is None:
            raise ValueError("No model available for evaluation. Train a model first.")

        logger.info("Evaluating model...")

        y_pred = model.predict(X_test)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        conf_matrix = confusion_matrix(y_test, y_pred)
        class_report = classification_report(y_test, y_pred)

        logger.info(f"Test Accuracy: {accuracy:.4f}")
        logger.info(f"\nClassification Report:\n{class_report}")

        return {
            'accuracy': accuracy,
            'confusion_matrix': conf_matrix,
            'classification_report': class_report,
            'predictions': y_pred
        }

    def save_model(self, output_path: str, model=None):
        """
        Save trained model to disk.

        Args:
            output_path: Path to save the model
            model: Model to save (uses best_model if None)
        """
        if model is None:
            model = self.best_model

        if model is None:
            raise ValueError("No model available to save. Train a model first.")

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        dump(model, output_path)
        logger.info(f"Model saved to {output_path}")

    def train_pipeline(
        self,
        X: pd.DataFrame,
        y: pd.Series,
        test_size: float = 0.2,
        tune: bool = True,
        param_grid: Dict = None,
        save_path: str = None
    ) -> Dict:
        """
        Execute full training pipeline.

        Args:
            X: Features
            y: Target variable
            test_size: Proportion for test set
            tune: Whether to perform hyperparameter tuning
            param_grid: Hyperparameter grid for tuning
            save_path: Path to save the trained model

        Returns:
            Dictionary with training results
        """
        logger.info("Starting training pipeline...")

        # Split data
        X_train, X_test, y_train, y_test = self.split_data(X, y, test_size)

        # Compare models
        comparison_results = self.compare_models(X_train, X_test, y_train, y_test)

        results = {
            'model_comparison': comparison_results,
            'best_model_name': self.best_model_name
        }

        # Hyperparameter tuning
        if tune and param_grid:
            grid_search = self.tune_hyperparameters(
                X_train, y_train, param_grid
            )
            results['grid_search'] = grid_search
            results['best_params'] = grid_search.best_params_
            results['best_cv_score'] = grid_search.best_score_

        # Final evaluation
        evaluation = self.evaluate_model(X_test, y_test)
        results['evaluation'] = evaluation

        # Save model
        if save_path:
            self.save_model(save_path)
            results['model_path'] = save_path

        logger.info("Training pipeline completed successfully")
        return results
