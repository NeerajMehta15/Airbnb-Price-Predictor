"""Data preprocessing and feature engineering for Airbnb Price Predictor."""
import re
import pandas as pd
import numpy as np
from typing import List, Tuple
from sklearn.preprocessing import LabelEncoder
from src.utils.logger import get_logger

logger = get_logger(__name__)


class DataPreprocessor:
    """Handles data preprocessing and feature engineering."""

    def __init__(self, property_types: List[str], price_bins: dict):
        """
        Initialize DataPreprocessor.

        Args:
            property_types: List of property types to extract as features
            price_bins: Dictionary with 'edges' and 'labels' for price binning
        """
        self.property_types = property_types
        self.price_bins = price_bins
        self.label_encoder = LabelEncoder()

    def preprocess(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply full preprocessing pipeline.

        Args:
            df: Raw DataFrame

        Returns:
            Preprocessed DataFrame ready for modeling
        """
        logger.info("Starting data preprocessing")

        df = df.copy()

        # 1. Handle missing beds values
        df = self._fill_missing_beds(df)

        # 2. Convert price to numeric
        df = self._process_price_column(df)

        # 3. Create price categories
        df = self._create_price_categories(df)

        # 4. Extract property type features
        df = self._extract_property_types(df)

        # 5. Extract bathroom features
        df = self._extract_bathroom_features(df)

        # 6. One-hot encode categorical features
        df = self._encode_categorical_features(df)

        # 7. Drop unnecessary columns
        df = self._drop_unnecessary_columns(df)

        # 8. Encode target variable
        df = self._encode_target(df)

        # 9. Convert to integer types
        df = df.astype(int)

        logger.info(f"Preprocessing complete. Final shape: {df.shape}")
        return df

    def _fill_missing_beds(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing beds values with accommodates value."""
        df = df.copy()
        df.loc[df['beds'] == '', 'beds'] = np.nan
        df['beds'] = df['beds'].fillna(df['accommodates'])
        logger.info("Filled missing beds values")
        return df

    def _process_price_column(self, df: pd.DataFrame) -> pd.DataFrame:
        """Convert price column to numeric."""
        df = df.copy()
        df['price'] = pd.to_numeric(
            df['price'].astype(str).str.replace('[^0-9.]', '', regex=True)
        )
        df['price'] = df['price'].astype(float)
        logger.info("Converted price to numeric")
        return df

    def _create_price_categories(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create price category bins."""
        df = df.copy()

        bin_edges = self.price_bins['edges']
        bin_labels = self.price_bins['labels']

        df['price_category'] = pd.cut(
            df['price'],
            bins=bin_edges,
            labels=bin_labels,
            right=False
        )

        category_counts = df['price_category'].value_counts().sort_index()
        logger.info(f"Created price categories: {category_counts.to_dict()}")

        return df

    def _extract_property_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract property type features as binary columns."""
        df = df.copy()

        for prop_type in self.property_types:
            df[prop_type] = df['property_type'].str.lower().str.contains(
                prop_type.lower()
            ).astype(int)

        # Create 'other' column for property types not in the list
        df['sum_of_columns'] = df[self.property_types].sum(axis=1)
        df['other'] = (df['sum_of_columns'] == 0).astype(int)

        logger.info(f"Extracted {len(self.property_types)} property type features")
        return df

    def _extract_bathroom_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract bathroom-related features from bathrooms_text."""
        df = df.copy()

        df['bathrooms_text'] = df['bathrooms_text'].astype(str)
        df['num_bathrooms'] = 0
        df['Shared_bath'] = 0
        df['Half_bath'] = 0

        for idx, row in df['bathrooms_text'].items():
            # Extract number of bathrooms
            match = re.search(r'(\d+(\.\d+)?)', row)
            if match:
                df.loc[idx, 'num_bathrooms'] = float(match.group(1))
            else:
                df.loc[idx, 'num_bathrooms'] = 1

            # Check if bathroom is shared
            df.loc[idx, 'Shared_bath'] = 0 if 'shared' in row.lower() else 1

            # Check if there's a half-bath
            df.loc[idx, 'Half_bath'] = 0 if 'half' in row.lower() else 1

        logger.info("Extracted bathroom features")
        return df

    def _encode_categorical_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """One-hot encode categorical features."""
        df = df.copy()

        df = pd.get_dummies(
            df,
            columns=['neighbourhood_group_cleansed', 'room_type'],
            drop_first=True
        )

        logger.info("Applied one-hot encoding to categorical features")
        return df

    def _drop_unnecessary_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Drop columns not needed for modeling."""
        df = df.copy()

        columns_to_drop = [
            'property_type',
            'bathrooms_text',
            'sum_of_columns',
            'other',
            'price_category'
        ]

        # Only drop columns that exist
        columns_to_drop = [col for col in columns_to_drop if col in df.columns]
        df = df.drop(columns=columns_to_drop)

        logger.info(f"Dropped {len(columns_to_drop)} unnecessary columns")
        return df

    def _encode_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """Encode target variable (price_category)."""
        df = df.copy()

        if 'price_category' in df.columns:
            df['price_category_encoded'] = self.label_encoder.fit_transform(df['price_category'])
            df = df.drop(columns=['price_category'])
            logger.info("Encoded target variable")

        return df

    def prepare_features_target(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Separate features and target variable.

        Args:
            df: Preprocessed DataFrame

        Returns:
            Tuple of (X, y) where X is features and y is target
        """
        X = df.drop(['price', 'price_category_encoded'], axis=1, errors='ignore')
        y = df['price_category_encoded'] if 'price_category_encoded' in df.columns else None

        logger.info(f"Prepared features: {X.shape}, target: {y.shape if y is not None else 'None'}")
        return X, y

    def transform_for_prediction(self, data: dict) -> pd.DataFrame:
        """
        Transform raw input data for prediction.

        Args:
            data: Dictionary with raw feature values

        Returns:
            DataFrame ready for model prediction
        """
        # Create DataFrame from input
        df = pd.DataFrame([data])

        # Apply same preprocessing steps (without target encoding)
        df = self._fill_missing_beds(df)
        df = self._extract_property_types(df)
        df = self._extract_bathroom_features(df)
        df = self._encode_categorical_features(df)
        df = self._drop_unnecessary_columns(df)

        return df
