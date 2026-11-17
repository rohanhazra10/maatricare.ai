from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.models.user import User
from app.security.dependencies import require_roles
from app.services.risk_service import predict_risk, ModelRuntimeError


router = APIRouter(
    prefix="/risk",
    tags=["Risk Prediction"]
)


class RiskInput(BaseModel):
    age: float = Field(..., ge=10, le=60)
    sbp: float = Field(..., ge=40, le=300, description="Systolic BP")
    dbp: float = Field(..., ge=20, le=200, description="Diastolic BP")
    temp_f: float = Field(..., ge=80, le=110, description="Temperature in Fahrenheit")
    hr: float = Field(..., ge=25, le=250, description="Heart rate")
    bmi: float = Field(..., ge=10, le=80)


@router.post("/predict")
def predict(
    data: RiskInput,
    current_user: User = Depends(
        require_roles("ASHA", "ANM", "MEDICAL_OFFICER", "ADMIN")
    )
):
    if data.sbp <= data.dbp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SBP must be greater than DBP"
        )

    try:
        return predict_risk(
            data.age, data.sbp, data.dbp,
            data.temp_f, data.hr, data.bmi
        )
    except ModelRuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
