"""Data loading utilities for Airbnb Price Predictor."""
import pandas as pd
from pathlib import Path
from typing import List, Optional
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataLoader:
    """Handles loading of Airbnb listing data."""

    def __init__(self, data_path: str):
        """
        Initialize DataLoader.

        Args:
            data_path: Path to the CSV data file
        """
        self.data_path = Path(data_path)
        if not self.data_path.exists():
            raise FileNotFoundError(f"Data file not found: {self.data_path}")

    def load_data(self, feature_columns: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Load data from CSV file.

        Args:
            feature_columns: Optional list of columns to load

        Returns:
            pandas DataFrame with loaded data
        """
        logger.info(f"Loading data from {self.data_path}")

        if feature_columns:
            df = pd.read_csv(self.data_path, usecols=feature_columns)
        else:
            df = pd.read_csv(self.data_path)

        # Remove rows with missing price
        initial_shape = df.shape
        df = df[df['price'].notna()]
        logger.info(f"Loaded {df.shape[0]} rows (removed {initial_shape[0] - df.shape[0]} rows with missing price)")

        return df

    def load_training_data(self, feature_columns: List[str]) -> pd.DataFrame:
        """
        Load data specifically for model training.

        Args:
            feature_columns: List of feature columns to load

        Returns:
            DataFrame with selected features
        """
        df = self.load_data(feature_columns)

        # Filter out rows where review_scores_rating is NaN
        initial_shape = df.shape
        df = df[pd.notna(df['review_scores_rating'])].copy()
        logger.info(f"Filtered data: {df.shape[0]} rows (removed {initial_shape[0] - df.shape[0]} rows with missing ratings)")

        return df
