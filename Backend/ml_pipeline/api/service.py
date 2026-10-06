"""Standalone FastAPI service for cron-triggered ML pipeline jobs."""

from __future__ import annotations

from time import perf_counter

from fastapi import Body, Depends, FastAPI, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db, init_database
from ..core.db_store import (
    finish_run,
    load_feature_dataframe,
    load_source_dataframes,
    persist_canonical_sources,
    persist_features,
    start_run,
)
from ..core.db_models import PipelineRun
from ..core.job_lock import job_lock
from ..core.logger import logger
from .schemas import (
    DailyIngestionResponse,
    FeatureEngineeringResponse,
    HealthResponse,
    JobStatusResponse,
    JobTriggerRequest,
    PredictionRequest,
    PredictionResponse,
    TrainingResponse,
    WeeklyAnalysisResponse,
)
from ..etl.canonical import build_canonical_datasets
from ..etl.quality_reports import build_quality_reports
from ..etl.trainable import build_trainable_dataset
from ..jobs.collect_daily import run_collection
from ..pipelines.run_pipeline import run_full_ml_data_pipeline
from ..utils import ML_JOB_TOKEN
from .predict_service import get_price_prediction

app = FastAPI(title="ScrapLink ML Pipeline Service", version="1.0.0")
logger.info("ML FastAPI application object created")


def require_job_token(x_ml_job_token: str | None = Header(default=None)) -> None:
    if not ML_JOB_TOKEN or x_ml_job_token != ML_JOB_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ML job token")


@app.on_event("startup")
def startup() -> None:
    started = perf_counter()
    logger.info("Application startup: beginning database initialization")
    init_database()
    logger.info("Application startup: database initialization finished")
    logger.info("Application startup complete in %.2f seconds", perf_counter() - started)


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(status="ok", service="ml_pipeline")


@app.post("/predict-price", response_model=PredictionResponse)
def predict_price(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    _: None = Depends(require_job_token),
) -> PredictionResponse:
    try:
        result = get_price_prediction(**request.model_dump(exclude_none=True), db=db)
        return PredictionResponse(**result)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except (FileNotFoundError, ValueError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.post("/jobs/daily-ingestion", response_model=DailyIngestionResponse)
def daily_ingestion(
    _request: JobTriggerRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_job_token),
) -> DailyIngestionResponse:
    try:
        lock = job_lock(db, "daily_ingestion")
        lock.__enter__()
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Daily ingestion is already running") from exc
    run = start_run(db, "daily_ingestion")
    try:
        collection = run_collection()
        canonical = build_canonical_datasets()
        persistence = persist_canonical_sources(
            db, canonical["scrap"], canonical["mcx"], canonical["reference"]
        )
        details = {"collection": collection, "manifest": canonical["manifest"]}
        finish_run(
            db,
            run,
            "succeeded",
            details=details,
            rows_read=len(canonical["scrap"]),
            rows_written=persistence["inserted"],
        )
        return DailyIngestionResponse(
            status="succeeded",
            run_id=run.id,
            persistence=persistence,
            details=details,
        )
    except Exception as exc:
        finish_run(db, run, "failed", error_message=str(exc))
        raise HTTPException(status_code=500, detail="Daily ingestion failed") from exc
    finally:
        lock.__exit__(None, None, None)


@app.post("/jobs/feature-engineering", response_model=FeatureEngineeringResponse)
def feature_engineering(
    _request: JobTriggerRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_job_token),
) -> FeatureEngineeringResponse:
    try:
        lock = job_lock(db, "feature_engineering")
        lock.__enter__()
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Feature engineering is already running") from exc
    run = start_run(db, "feature_engineering")
    try:
        persisted_sources = load_source_dataframes(db)
        result = build_trainable_dataset(
            scrap=persisted_sources["scrap"],
            mcx=persisted_sources["mcx"],
        )
        persistence = persist_features(db, result["dataset"])
        finish_run(
            db,
            run,
            "succeeded",
            details=result["eligibility"],
            rows_read=len(result["dataset"]),
            rows_written=persistence["inserted"],
        )
        return FeatureEngineeringResponse(
            status="succeeded",
            run_id=run.id,
            persistence=persistence,
            eligibility=result["eligibility"],
        )
    except Exception as exc:
        finish_run(db, run, "failed", error_message=str(exc))
        raise HTTPException(status_code=500, detail="Feature engineering failed") from exc
    finally:
        lock.__exit__(None, None, None)


@app.post("/jobs/weekly-analysis", response_model=WeeklyAnalysisResponse)
def weekly_analysis(
    _request: JobTriggerRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_job_token),
) -> WeeklyAnalysisResponse:
    try:
        lock = job_lock(db, "weekly_analysis")
        lock.__enter__()
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Weekly analysis is already running") from exc
    run = start_run(db, "weekly_analysis")
    try:
        sources = load_source_dataframes(db)
        result = build_trainable_dataset(sources["scrap"], sources["mcx"])
        persistence = persist_features(db, result["dataset"])
        finish_run(
            db, run, "succeeded", details=result["eligibility"],
            rows_read=len(result["dataset"]), rows_written=persistence["inserted"],
        )
        return WeeklyAnalysisResponse(
            status="succeeded",
            manifest={
                "run_id": run.id,
                "source_rows": {key: len(value) for key, value in sources.items()},
                "feature_persistence": persistence,
                "eligibility": result["eligibility"],
            },
        )
    except Exception as exc:
        finish_run(db, run, "failed", error_message=str(exc))
        raise HTTPException(status_code=500, detail="Weekly analysis failed") from exc
    finally:
        lock.__exit__(None, None, None)


@app.post("/jobs/train", response_model=TrainingResponse)
def train(
    _request: JobTriggerRequest | None = Body(default=None),
    db: Session = Depends(get_db),
    _: None = Depends(require_job_token),
) -> TrainingResponse:
    from ..training.retrain_model import retrain
    try:
        lock = job_lock(db, "train")
        lock.__enter__()
    except Exception as exc:
        raise HTTPException(status_code=409, detail="Training is already running") from exc
    run = start_run(db, "train")
    try:
        result = retrain(load_feature_dataframe(db), db=db)
        finish_run(db, run, "succeeded", details=result, rows_written=0)
        return TrainingResponse(**result)
    except Exception as exc:
        finish_run(db, run, "failed", error_message=str(exc))
        raise HTTPException(status_code=500, detail="Training failed") from exc
    finally:
        lock.__exit__(None, None, None)


@app.get("/jobs/{run_id}", response_model=JobStatusResponse)
def job_status(
    run_id: int,
    _: None = Depends(require_job_token),
    db: Session = Depends(get_db),
) -> JobStatusResponse:
    run = db.get(PipelineRun, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail="Pipeline run not found")
    return JobStatusResponse(
        run_id=run.id,
        job_type=run.job_type,
        status=run.status,
        rows_read=run.rows_read,
        rows_written=run.rows_written,
        details=run.details,
        error_message=run.error_message,
        started_at=run.started_at.isoformat(),
        completed_at=run.completed_at.isoformat() if run.completed_at else None,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ml_pipeline.api.service:app", host="0.0.0.0", port=8010)
