"""FastAPI application for Airbnb Price Predictor."""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict
import uvicorn

from src.models.predictor import PricePredictor
from src.data.preprocessor import DataPreprocessor
from src.utils.config import get_config
from src.utils.logger import setup_logger

# Load configuration
config = get_config()
logger = setup_logger(__name__, level=config.get('logging.level', 'INFO'))

# Initialize FastAPI app
app = FastAPI(
    title=config.get('api.title', 'Airbnb Price Predictor API'),
    version=config.get('api.version', '1.0.0'),
    description=config.get('api.description', 'ML API for Airbnb price prediction')
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize predictor and preprocessor
predictor = None
preprocessor = None


class ListingFeatures(BaseModel):
    """Input schema for prediction request."""
    neighbourhood_group_cleansed: str = Field(..., description="Neighborhood group")
    property_type: str = Field(..., description="Type of property")
    room_type: str = Field(..., description="Type of room (Entire home/apt, Private room, etc.)")
    accommodates: int = Field(..., description="Number of guests it accommodates", ge=1)
    bathrooms_text: str = Field(..., description="Bathroom description (e.g., '1 bath', '2.5 baths')")
    beds: str = Field(..., description="Number of beds")
    number_of_reviews: int = Field(..., description="Total number of reviews", ge=0)
    review_scores_rating: float = Field(..., description="Average review rating", ge=0, le=5)
    reviews_per_month: float = Field(..., description="Average reviews per month", ge=0)

    class Config:
        schema_extra = {
            "example": {
                "neighbourhood_group_cleansed": "Central Region",
                "property_type": "Entire rental unit",
                "room_type": "Entire home/apt",
                "accommodates": 4,
                "bathrooms_text": "2 baths",
                "beds": "2",
                "number_of_reviews": 25,
                "review_scores_rating": 4.5,
                "reviews_per_month": 2.0
            }
        }


class PredictionResponse(BaseModel):
    """Output schema for prediction response."""
    predicted_category: str
    predicted_category_index: int
    probabilities: Optional[Dict[str, float]] = None


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    model_loaded: bool
    model_info: Optional[Dict] = None


@app.on_event("startup")
async def startup_event():
    """Initialize model and preprocessor on startup."""
    global predictor, preprocessor

    try:
        logger.info("Loading model and initializing components...")

        # Load predictor
        model_path = config.get('model.model_path')
        predictor = PricePredictor(model_path)

        # Initialize preprocessor
        property_types = config.get('data.property_types')
        price_bins = config.get('price_bins')
        preprocessor = DataPreprocessor(property_types, price_bins)

        logger.info("API startup complete")
    except Exception as e:
        logger.error(f"Failed to initialize API: {e}")
        raise


@app.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint."""
    return {
        "message": "Airbnb Price Predictor API",
        "version": config.get('api.version', '1.0.0'),
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    model_loaded = predictor is not None

    response = {
        "status": "healthy" if model_loaded else "unhealthy",
        "model_loaded": model_loaded
    }

    if model_loaded:
        response["model_info"] = predictor.get_model_info()

    return response


@app.post("/predict", response_model=PredictionResponse)
async def predict(features: ListingFeatures):
    """
    Predict price category for an Airbnb listing.

    Args:
        features: Listing features

    Returns:
        Prediction response with category and probabilities
    """
    if predictor is None or preprocessor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Convert Pydantic model to dict
        features_dict = features.dict()

        # Preprocess features
        X = preprocessor.transform_for_prediction(features_dict)

        # Make prediction
        result = predictor.predict_single(X.iloc[0].to_dict())

        return result

    except Exception as e:
        logger.error(f"Prediction error: {e}")
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@app.get("/model/info", response_model=Dict)
async def model_info():
    """Get information about the loaded model."""
    if predictor is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return predictor.get_model_info()


def main():
    """Run the FastAPI application."""
    host = config.get('api.host', '0.0.0.0')
    port = config.get('api.port', 8000)

    logger.info(f"Starting API server on {host}:{port}")

    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )


if __name__ == "__main__":
    main()
