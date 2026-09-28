from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field
TargetTier = Literal["1:1", "1:Few", "1:Many"]
class Account(BaseModel):
    id: str; name: str; industry: str; target_tier: TargetTier; current_score: float = Field(ge=0, le=100); created_at: datetime | None = None
class IntentEvent(BaseModel):
    account_id: str; source: str; event_type: str; weight: float = Field(ge=0); timestamp: datetime
class IntentWebhookPayload(BaseModel):
    account_id: str; source: str; event_type: str; weight: float = Field(ge=0); timestamp: datetime | None = None
class IngestResponse(BaseModel):
    event_id: str; account_id: str; current_score: float
class BrandKnowledgeInput(BaseModel):
    theme_name: str = Field(min_length=1); content: str = Field(min_length=1)

class GenerateCopyRequest(BaseModel):
    account_id: str
    theme_name: str = Field(min_length=1)

class CopyVariant(BaseModel):
    id: str | None = None
    account_id: str | None = None
    channel: Literal["Executive EDM", "LinkedIn Ad", "Landing Page Hook"]
    generated_text: str
    status: Literal["draft", "approved", "synced"] = "draft"

class GenerateCopyResponse(BaseModel):
    account_id: str
    variants: list[CopyVariant]

class VariantStatusUpdate(BaseModel):
    status: Literal["draft", "approved", "synced"]
