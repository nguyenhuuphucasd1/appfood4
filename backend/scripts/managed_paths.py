from __future__ import annotations

import os
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[2]
KAGGLE_CONFIG_DIR = PROJECT_DIR / ".kaggle"
CACHE_DIR = PROJECT_DIR / ".cache"
RAW_DATASETS_DIR = PROJECT_DIR / "datasets" / "raw"
PROCESSED_DATASETS_DIR = PROJECT_DIR / "datasets" / "processed"
ARTIFACTS_DIR = PROJECT_DIR / "artifacts" / "training"
CANDIDATE_MODELS_DIR = PROJECT_DIR / "backend" / "models" / "candidates"


def configure_storage_environment() -> None:
    """Force ML/download caches to the project drive before client imports."""
    values = {
        "KAGGLE_CONFIG_DIR": KAGGLE_CONFIG_DIR,
        "HF_HOME": CACHE_DIR / "huggingface",
        "TRANSFORMERS_CACHE": CACHE_DIR / "huggingface",
        "TORCH_HOME": CACHE_DIR / "torch",
        "PIP_CACHE_DIR": CACHE_DIR / "pip",
        "TEMP": CACHE_DIR / "tmp",
        "TMP": CACHE_DIR / "tmp",
    }
    for variable, path in values.items():
        path.mkdir(parents=True, exist_ok=True)
        os.environ[variable] = str(path)
    # Kaggle 1.8 resolves new API tokens from this variable. Passing the file
    # path keeps the secret out of process arguments and logs.
    os.environ["KAGGLE_API_TOKEN"] = str(KAGGLE_CONFIG_DIR / "access_token")
    for path in (RAW_DATASETS_DIR, PROCESSED_DATASETS_DIR, ARTIFACTS_DIR, CANDIDATE_MODELS_DIR):
        path.mkdir(parents=True, exist_ok=True)


def kaggle_token_path() -> Path:
    """Return the preferred Kaggle 1.8+ token path on the project drive."""
    return KAGGLE_CONFIG_DIR / "access_token"


def require_kaggle_token() -> Path:
    token = kaggle_token_path()
    legacy_token = KAGGLE_CONFIG_DIR / "kaggle.json"
    if token.is_file():
        return token
    if legacy_token.is_file():
        return legacy_token
    raise RuntimeError(
        "Khong tim thay Kaggle token. Dat token moi vao "
        f"{token}, hoac dat credential cu kaggle.json tai {legacy_token} "
        "(khong dat o o C va khong gui token qua chat)."
    )
