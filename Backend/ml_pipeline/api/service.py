"""Standalone FastAPI service for cron-triggered ML pipeline jobs."""

from __future__ import annotations

from fastapi import Depends, FastAPI, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..core.database import get_db, init_database
from ..core.db_store import finish_run, persist_canonical_sources, persist_features, start_run
from ..etl.canonical import build_canonical_datasets
from ..etl.quality_reports import build_quality_reports
from ..etl.trainable import build_trainable_dataset
from ..jobs.collect_daily import run_collection
from ..pipelines.run_pipeline import run_full_ml_data_pipeline
from ..utils import ML_JOB_TOKEN

app = FastAPI(title="ScrapLink ML Pipeline Service", version="1.0.0")


def require_job_token(x_ml_job_token: str | None = Header(default=None)) -> None:
    if not ML_JOB_TOKEN or x_ml_job_token != ML_JOB_TOKEN:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid ML job token")


@app.on_event("startup")
def startup() -> None:
    init_database()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "ml_pipeline"}


@app.post("/jobs/daily-ingestion")
def daily_ingestion(db: Session = Depends(get_db), _: None = Depends(require_job_token)):
    run = start_run(db, "daily_ingestion")
    try:
        collection = run_collection()
        canonical = build_canonical_datasets()
        written = persist_canonical_sources(
            db, canonical["scrap"], canonical["mcx"], canonical["reference"]
        )
        details = {"collection": collection, "manifest": canonical["manifest"]}
        finish_run(db, run, "succeeded", details=details, rows_read=len(canonical["scrap"]), rows_written=written)
        return {"status": "succeeded", "run_id": run.id, "rows_written": written, "details": details}
    except Exception as exc:
        finish_run(db, run, "failed", error_message=str(exc))
        raise HTTPException(status_code=500, detail="Daily ingestion failed") from exc


@app.post("/jobs/feature-engineering")
def feature_engineering(db: Session = Depends(get_db), _: None = Depends(require_job_token)):
    run = start_run(db, "feature_engineering")
    try:
        result = build_trainable_dataset()
        written = persist_features(db, result["dataset"])
        finish_run(db, run, "succeeded", details=result["eligibility"], rows_read=len(result["dataset"]), rows_written=written)
        return {"status": "succeeded", "run_id": run.id, "rows_written": written, "eligibility": result["eligibility"]}
    except Exception as exc:
        finish_run(db, run, "failed", error_message=str(exc))
        raise HTTPException(status_code=500, detail="Feature engineering failed") from exc


@app.post("/jobs/weekly-analysis")
def weekly_analysis(_: None = Depends(require_job_token)):
    try:
        return {"status": "succeeded", "manifest": run_full_ml_data_pipeline()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Weekly analysis failed") from exc


@app.post("/jobs/train")
def train(_: None = Depends(require_job_token)):
    from .training.retrain_model import retrain
    try:
        return retrain()
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Training failed") from exc


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ml_pipeline.api.service:app", host="0.0.0.0", port=8010)
