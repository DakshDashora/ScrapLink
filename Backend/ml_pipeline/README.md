# ML pipeline model storage

The ML service stores immutable model artifacts as private Cloudinary raw
assets and keeps the active model version and asset checksums in Neon. It
downloads the active version into a temporary local cache for inference;
Render's local filesystem is not used as durable storage.

Configure these environment variables on the ML service:

- `ML_CLOUDINARY_CLOUD_NAME`
- `ML_CLOUDINARY_API_KEY`
- `ML_CLOUDINARY_API_SECRET`
- `ML_CLOUDINARY_MODEL_FOLDER` (optional; defaults to `scraplink/models`)

The Cloudinary API credentials are used only by `ml_pipeline`; this integration
does not use or change the main application's Cloudinary configuration. The
`ml_model_registry` table is created alongside the other ML pipeline tables.

A model is made active only after all required artifacts upload successfully.
Each version is immutable, and the previous registry entry remains available
for rollback. Do not delete an artifact version while its registry record may
still be used for rollback.
