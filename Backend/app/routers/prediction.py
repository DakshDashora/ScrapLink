from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field
import httpx
from app.config import settings
from app.security import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api", tags=["Price Prediction"])

class PredictionRequest(BaseModel):
    commodity: str = Field(..., min_length=1, max_length=128)
    scrap_type: str | None = None  # ✅ Added this based on Daksh's contract
    
    # Optional legacy hints
    lag_1: float | None = None
    lag_7: float | None = None
    lag_14: float | None = None
    lag_30: float | None = None
    rolling_mean_7: float | None = None
    rolling_mean_30: float | None = None
    rolling_std_7: float | None = None
    rolling_std_30: float | None = None
    pct_change_7: float | None = None
    pct_change_30: float | None = None


class PredictionResponse(BaseModel):
    status: str
    commodity: str
    scrap_type: str  # ✅ Added this based on Daksh's contract
    estimated_price_p10_inr_per_kg: float
    estimated_price_p50_inr_per_kg: float
    estimated_price_p90_inr_per_kg: float
    model_version: str
    prediction_date: str | None
    estimate_type: str
    is_guaranteed_transaction_price: bool
    recommended_price: float
    price_band: dict
    trend: str
    unit: str
    disclaimer: str


@router.post("/predict-price", response_model=PredictionResponse)
async def predict_price(
    request: PredictionRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Proxy to the standalone ML service.
    The ML_JOB_TOKEN stays server-side and is never exposed.
    """

    if not settings.ML_SERVICE_URL or not settings.ML_JOB_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Price prediction service is not configured",
        )

    ml_url = f"{settings.ML_SERVICE_URL.rstrip('/')}/predict-price"

    # exclude_none=True ensures we don't send nulls to Daksh's strict ML schema
    payload = request.model_dump(exclude_none=True)

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                ml_url,
                json=payload,
                headers={
                    "X-ML-Job-Token": settings.ML_JOB_TOKEN,
                    "Content-Type": "application/json",
                },
            )

        if response.status_code == 200:
            return response.json()

        if response.status_code == 401:
            print("❌ ML service rejected our token")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Price prediction service authentication failed",
            )

        if response.status_code == 422:
            # 422 means the material or scrap_type wasn't found by the ML model
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid material or missing history: {response.text}",
            )

        if response.status_code == 503:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Price prediction model is not yet available",
            )

        # Any other error
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Price prediction service error: {response.status_code}",
        )

    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Price prediction service timed out",
        )
    except httpx.RequestError as e:
        print(f"❌ ML service connection error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not reach price prediction service",
        )