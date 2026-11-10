import os
from pathlib import Path

def load_environment_variables():
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    with open(env_path, "r", encoding="utf-8") as file:
        for line in file:
            clean_line = line.strip()
            if not clean_line or clean_line.startswith("#"):
                continue
            if "=" in clean_line:
                key, value = clean_line.split("=", 1)
                clean_key = key.strip()
                clean_value = value.strip().strip("'\"")
                if clean_key not in os.environ:
                    os.environ[clean_key] = clean_value

load_environment_variables()

class ConfigurationSettings:
    app_name: str = "TokenBrief"
    database_connection_url: str = os.environ.get(
        "DATABASE_URL",
        "postgresql+asyncpg://postgres:postgres@localhost:5432/rag_db"
    )
    gemini_api_key: str = os.environ.get("GEMINI_API_KEY", "")
    gemini_model_name: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")
    google_cloud_project: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "projects/218902508443")
    google_cloud_project_number: str = os.environ.get("GOOGLE_CLOUD_PROJECT_NUMBER", "218902508443")
    security_secret_key: str = os.environ.get(
        "SECRET_KEY",
        "b71c265324df504938637c358042fa2277dca08dbca645001ff2a5f64d0846be"
    )
    security_algorithm_name: str = os.environ.get("ALGORITHM", "HS256")
    access_token_expire_minutes: int = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    refresh_token_expire_days: int = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    embedding_model_name: str = os.environ.get("EMBEDDING_MODEL_NAME", "all-MiniLM-L6-v2")
    document_upload_directory: str = os.environ.get("UPLOAD_DIR", "uploads")
    resend_api_key: str = os.environ.get("RESEND_API_KEY", "")
    resend_from_email: str = os.environ.get("RESEND_FROM_EMAIL", "TokenBrief Intelligence <onboarding@resend.dev>")
    gmail_sender_email: str = os.environ.get("GMAIL_SENDER_EMAIL", "connect.tushar0318@gmail.com")
    gmail_app_password: str = os.environ.get("GMAIL_APP_PASSWORD", "")
    otp_expiration_minutes: int = int(os.environ.get("OTP_EXPIRATION_MINUTES", "10"))
    semantic_cache_similarity_threshold: float = float(os.environ.get("SEMANTIC_CACHE_THRESHOLD", "0.92"))
    max_upload_size_mb: int = int(os.environ.get("MAX_UPLOAD_SIZE_MB", "15"))
    min_upload_size_bytes: int = int(os.environ.get("MIN_UPLOAD_SIZE_BYTES", "100"))
    allowed_extensions: tuple = (".pdf", ".txt", ".md")

    def get_max_upload_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def get_normalized_database_url(self) -> str:
        url = self.database_connection_url.strip()
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

settings = ConfigurationSettings()
