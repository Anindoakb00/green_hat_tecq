import hmac
import httpx
from datetime import datetime, timezone
from functools import lru_cache
from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import Client, create_client
from .config import get_settings
from .models import Account, BrandKnowledgeInput, CopyVariant, GenerateCopyRequest, GenerateCopyResponse, IngestResponse, IntentEvent, IntentWebhookPayload, VariantStatusUpdate
from .scoring import calculate_intent_score
from .llm_engine import generate_copy
settings = get_settings(); app = FastAPI(title="Epochs Enterprise ABM Engine", version="2.0.0")
app.add_middleware(CORSMiddleware, allow_origins=[settings.frontend_origin], allow_credentials=True, allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type", "X-Webhook-Secret"])
@lru_cache
def supabase() -> Client: return create_client(settings.supabase_url, settings.supabase_service_role_key)
@lru_cache
def embedding_model():
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer("all-MiniLM-L6-v2")
def user_id(authorization: str | None = Header(default=None)) -> str:
    if settings.local_demo_mode and settings.supabase_owner_user_id:
        return settings.supabase_owner_user_id
    if not authorization or not authorization.lower().startswith("bearer "): raise HTTPException(401, "Bearer token required")
    try:
        access_token = authorization[7:].strip()
        if not settings.supabase_publishable_key:
            raise ValueError("SUPABASE_PUBLISHABLE_KEY is missing")
        response = httpx.get(f"{settings.supabase_url}/auth/v1/user", headers={"apikey": settings.supabase_publishable_key, "Authorization": f"Bearer {access_token}"}, timeout=10)
        if response.status_code != 200:
            raise ValueError(f"Supabase Auth returned {response.status_code}: {response.text}")
        user = response.json()
        if not user.get("id"): raise ValueError("No user id returned")
        return str(user["id"])
    except Exception as exc: raise HTTPException(401, "Invalid access token") from exc
def webhook_auth(secret: str | None = Header(default=None, alias="X-Webhook-Secret")) -> None:
    if not settings.ingestion_webhook_secret or not secret or not hmac.compare_digest(secret, settings.ingestion_webhook_secret): raise HTTPException(401, "Invalid webhook secret")
@app.get("/api/health")
def health(): return {"status": "ok"}
@app.get("/api/accounts", response_model=list[Account])
def accounts(uid: str = Depends(user_id)):
    rows = supabase().table("accounts").select("id,name,industry,target_tier,current_score,created_at").eq("agency_user_id", uid).order("current_score", desc=True).execute().data or []
    return [Account.model_validate(row) for row in rows]
@app.get("/api/accounts/{account_id}/events")
def account_events(account_id: str, uid: str = Depends(user_id)):
    account = supabase().table("accounts").select("id").eq("id", account_id).eq("agency_user_id", uid).single().execute().data
    if not account: raise HTTPException(404, "Account not found")
    return supabase().table("intent_events").select("id,account_id,source,event_type,weight,timestamp").eq("account_id", account_id).order("timestamp", desc=True).limit(100).execute().data or []
@app.post("/api/accounts/{account_id}/events", response_model=IngestResponse, status_code=201)
def add_account_event(account_id: str, payload: IntentWebhookPayload, uid: str = Depends(user_id)):
    if payload.account_id != account_id: raise HTTPException(400, "Account id mismatch")
    account = supabase().table("accounts").select("id").eq("id", account_id).eq("agency_user_id", uid).single().execute().data
    if not account: raise HTTPException(404, "Account not found")
    stamp = payload.timestamp or datetime.now(timezone.utc)
    inserted = supabase().table("intent_events").insert({"account_id": account_id, "source": payload.source, "event_type": payload.event_type, "weight": payload.weight, "timestamp": stamp.isoformat()}).execute().data[0]
    rows = supabase().table("intent_events").select("account_id,source,event_type,weight,timestamp").eq("account_id", account_id).execute().data or []
    score = calculate_intent_score([IntentEvent.model_validate(row) for row in rows])
    supabase().table("accounts").update({"current_score": score}).eq("id", account_id).execute()
    return IngestResponse(event_id=inserted["id"], account_id=account_id, current_score=score)
@app.post("/api/knowledge", status_code=201)
def knowledge(payload: BrandKnowledgeInput, uid: str = Depends(user_id)):
    vector = embedding_model().encode(payload.content, normalize_embeddings=True).tolist()
    return supabase().table("brand_knowledge").insert({"agency_user_id": uid, "theme_name": payload.theme_name, "content": payload.content, "embedding": vector}).execute().data[0]
@app.post("/api/knowledge/ingest-pdfs", status_code=202)
def ingest_pdfs_endpoint(uid: str = Depends(user_id)):
    from ingest_pdfs import ingest_pdfs
    try:
        chunks = ingest_pdfs(uid)
    except Exception as exc:
        raise HTTPException(502, f"PDF ingestion failed: {exc}") from exc
    return {"status": "complete", "chunks_by_file": chunks, "chunks_inserted": sum(chunks.values())}

@app.post("/api/generate-copy", response_model=GenerateCopyResponse)
def generate(payload: GenerateCopyRequest, uid: str = Depends(user_id)):
    account = supabase().table("accounts").select("id,name,industry,target_tier,current_score").eq("id", payload.account_id).eq("agency_user_id", uid).single().execute().data
    if not account:
        raise HTTPException(404, "Account not found")
    events = supabase().table("intent_events").select("source,event_type,weight,timestamp").eq("account_id", payload.account_id).order("timestamp", desc=True).limit(25).execute().data or []
    embedding = embedding_model().encode(payload.theme_name, normalize_embeddings=True).tolist()
    rag = supabase().rpc("match_brand_knowledge_for_owner", {"query_embedding": embedding, "match_theme": payload.theme_name, "owner_id": uid, "match_count": 5}).execute().data or []
    try:
        variants = generate_copy(account=account, events=events, brand_context=rag, theme_name=payload.theme_name)
    except Exception as exc:
        raise HTTPException(502, f"Groq generation failed: {exc}") from exc
    rows = [{"account_id": payload.account_id, "channel": item.channel, "generated_text": item.generated_text, "status": "draft"} for item in variants]
    saved = supabase().table("copy_variants").insert(rows).execute().data or []
    for variant, row in zip(variants, saved):
        variant.id = row.get("id")
        variant.account_id = payload.account_id
    return GenerateCopyResponse(account_id=payload.account_id, variants=variants)
@app.patch("/api/copy-variants/{variant_id}")
def update_variant(variant_id: str, payload: VariantStatusUpdate, uid: str = Depends(user_id)):
    owned = supabase().table("copy_variants").select("id,account_id,accounts!inner(agency_user_id)").eq("id", variant_id).eq("accounts.agency_user_id", uid).single().execute().data
    if not owned: raise HTTPException(404, "Copy variant not found")
    result = supabase().table("copy_variants").update({"status": payload.status}).eq("id", variant_id).execute()
    return result.data[0]
@app.post("/api/webhooks/ingest", response_model=IngestResponse, status_code=202)
def ingest(payload: IntentWebhookPayload, _: None = Depends(webhook_auth)):
    stamp = payload.timestamp or datetime.now(timezone.utc); account = supabase().table("accounts").select("id").eq("id", payload.account_id).single().execute().data
    if not account: raise HTTPException(404, "Account not found")
    inserted = supabase().table("intent_events").insert({"account_id": payload.account_id, "source": payload.source, "event_type": payload.event_type, "weight": payload.weight, "timestamp": stamp.isoformat()}).execute().data[0]
    rows = supabase().table("intent_events").select("account_id,source,event_type,weight,timestamp").eq("account_id", payload.account_id).execute().data or []
    score = calculate_intent_score([IntentEvent.model_validate(row) for row in rows]); supabase().table("accounts").update({"current_score": score}).eq("id", payload.account_id).execute()
    return IngestResponse(event_id=inserted["id"], account_id=payload.account_id, current_score=score)
