from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    supabase_url: str = Field(validation_alias="SUPABASE_URL")
    supabase_service_role_key: str = Field(validation_alias="SUPABASE_SERVICE_ROLE_KEY")
    supabase_publishable_key: str = Field(default="", validation_alias="SUPABASE_PUBLISHABLE_KEY")
    groq_api_key: str = Field(default="", validation_alias="GROQ_API_KEY")
    groq_model: str = Field(default="qwen/qwen3.8-27b", validation_alias="GROQ_MODEL")
    frontend_origin: str = Field(default="http://localhost:3000", validation_alias="FRONTEND_ORIGIN")
    ingestion_webhook_secret: str = Field(default="", validation_alias="INGESTION_WEBHOOK_SECRET")
    supabase_owner_user_id: str = Field(default="", validation_alias="SUPABASE_OWNER_USER_ID")
    local_demo_mode: bool = Field(default=False, validation_alias="LOCAL_DEMO_MODE")
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

@lru_cache
def get_settings() -> Settings: return Settings()
