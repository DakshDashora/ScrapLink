# ScrapLink

ScrapLink is a business-to-business marketplace for industrial scrap. It connects organizations that sell scrap with buyers looking for recyclable materials, with listing discovery, location-aware browsing, and a separate data and machine-learning service for market-price estimates.

This repository contains the React web application, the FastAPI marketplace API, and the standalone ML data pipeline.

## Project overview

- **Marketplace API** — user registration and authentication, email/phone verification, organizations, scrap categories, and seller-managed listings.
- **Marketplace web app** — React interface for browsing, creating, and managing listings, with search/filter controls, image uploads, and map views.
- **ML pipeline service** — ingests market observations, builds leakage-aware features, tracks pipeline runs, and trains price-estimation models when sufficient eligible history is available.
- **Price-model storage** — immutable model versions are stored as private Cloudinary raw assets; the active version and checksums are recorded in the ML database.

Price outputs are estimates/reference prices, not guaranteed transaction prices. The current training pipeline will skip model promotion until it has at least 30 distinct ScrapMonster observation dates and 500 eligible rows. Therefore, a trained model may not yet be available.

## Technology

| Area | Main technologies |
| --- | --- |
| Frontend | React, Vite, Redux Toolkit, React Router, Axios, Leaflet |
| Marketplace API | Python 3.12+, FastAPI, SQLAlchemy, PostgreSQL, pgvector |
| ML service | FastAPI, pandas, NumPy, scikit-learn, joblib, Yahoo Finance data |
| Model artifacts and listing images | Cloudinary |

The ML service is separate from the marketplace API and has its own database/job credentials and Cloudinary settings.

## Repository layout

```text
.
├── Backend/
│   ├── app/                 # Marketplace API, models, routes, and utilities
│   ├── ml_pipeline/         # Standalone ingestion, feature, training, and prediction service
│   ├── .env.example         # ML-service environment-variable template
│   ├── pyproject.toml       # Python dependencies
│   └── seed_categories.py   # Seed marketplace categories
├── Frontend/
│   ├── src/                 # React application
│   └── package.json
├── .github/workflows/       # Scheduled ML pipeline jobs
├── weekly_reports/          # Generated progress reports
├── generate_report.py       # Git-history contribution-report generator
└── README.md
```

## Prerequisites

- Git
- Node.js and npm
- Python 3.12 or newer
- [`uv`](https://docs.astral.sh/uv/) for installing and running the Python backend
- PostgreSQL with pgvector for the marketplace API and ML pipeline database

## Configuration

### Marketplace API

The API reads its settings from `Backend/.env` when started from the `Backend` directory. Configure the required database, JWT, and email settings declared in `Backend/app/config.py`:

```dotenv
DATABASE_URL=
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DB=
JWT_SECRET_KEY=
EMAIL_HOST=
EMAIL_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
EMAIL_FROM=
```

`BREVO_API_KEY` and the main application's `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, and `CLOUDINARY_API_SECRET` are optional settings used for email delivery and listing image uploads. Keep real credentials in local or hosting-provider environment settings only.

### ML pipeline service

`Backend/.env.example` documents the ML service variables. Copy it to `Backend/.env` if needed, then configure:

```dotenv
ML_JOB_TOKEN=
ML_DATABASE_URL=
ML_CLOUDINARY_CLOUD_NAME=
ML_CLOUDINARY_API_KEY=
ML_CLOUDINARY_API_SECRET=
ML_CLOUDINARY_MODEL_FOLDER=scraplink/models
```

Use separate ML-specific Cloudinary variables: the ML service does not rely on the marketplace app's Cloudinary configuration. See [`Backend/ml_pipeline/README.md`](Backend/ml_pipeline/README.md) for model artifact storage details.

## Run locally

### Frontend

```powershell
cd Frontend
npm install
npm run dev
```

Vite prints the local URL when the development server starts.

### Marketplace API

From the repository root:

```powershell
cd Backend
uv sync
uv run uvicorn app.main:app --reload
```

The API serves interactive documentation at `http://localhost:8000/docs`. To seed the initial scrap categories, run this from `Backend`:

```powershell
uv run python seed_categories.py
```

### ML pipeline service

Configure `ML_DATABASE_URL`, `ML_JOB_TOKEN`, and the ML Cloudinary credentials, then run from `Backend`:

```powershell
uv run python -m ml_pipeline.api.service
```

The ML service listens on port `8010` by default. Its health endpoint is `GET /health`; prediction and job endpoints are documented at `http://localhost:8010/docs`. Protected endpoints require the `X-ML-Job-Token` header.

The data and model workflows can also be run from `Backend`:

```powershell
uv run python -m ml_pipeline.pipelines.run_pipeline
uv run python -m ml_pipeline.jobs.collect_daily
uv run python -m ml_pipeline.training.retrain_model
```

Training requires sufficient eligible historical data. If the configured history or row-count gates are not met, the training job reports that it skipped and does not promote a model.

## Frontend checks

Run from `Frontend`:

```powershell
npm run lint
npm run build
```

## Contributing

Create a feature branch, make focused changes, and open a pull request for review. Do not commit `.env` files, API secrets, model credentials, or other private configuration.
