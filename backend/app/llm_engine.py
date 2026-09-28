import json
import re

from groq import Groq

from .config import get_settings
from .models import CopyVariant

SYSTEM_PROMPT = """You are the Epochs Enterprise ABM Engine copy strategist for Green Hat.
Use only the supplied brand context and account signals. Do not invent customers, metrics, or claims.
The account name in the dossier is the only company name you may use. Insert that exact name wherever the copy refers to the company.
Never output bracketed template placeholders such as [Company Name], [First Name], [Your Name], [CTA], or similar. If no contact name is supplied, address the persona or role without a name.
Ground every variant in the retrieved PDF campaign narrative. For green_hat_1.pdf specifically, reflect frontline workforce connection, reducing turnover, and operational efficiency when supported by the retrieved excerpts.
Return ONLY valid JSON with exactly this shape:
{"variants":[{"channel":"Executive EDM","generated_text":"...","status":"draft"},{"channel":"LinkedIn Ad","generated_text":"...","status":"draft"},{"channel":"Landing Page Hook","generated_text":"...","status":"draft"}]}
Each generated_text must be usable marketing copy and tailored to the account's observed intent."""


def generate_copy(*, account: dict, events: list[dict], brand_context: list[dict], theme_name: str) -> list[CopyVariant]:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    prompt = {"selected_theme": theme_name, "account_dossier": account, "recent_intent_events": events, "retrieved_pdf_excerpts": brand_context}
    response = Groq(api_key=settings.groq_api_key).chat.completions.create(
        model=settings.groq_model,
        temperature=0.3,
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": json.dumps(prompt)}],
    )
    payload = json.loads(response.choices[0].message.content or "{}")
    variants = [CopyVariant.model_validate(item) for item in payload.get("variants", [])]
    if len(variants) != 3:
        raise ValueError("Groq returned an invalid number of copy variants")
    placeholders = re.compile(r"\[[^\]]+\]")
    invalid = [variant.channel for variant in variants if placeholders.search(variant.generated_text)]
    if invalid:
        raise ValueError(f"Groq returned template placeholders in: {', '.join(invalid)}")
    account_name = str(account.get("name", "")).strip()
    missing_account_name = [variant.channel for variant in variants if account_name and account_name.lower() not in variant.generated_text.lower()]
    if missing_account_name:
        raise ValueError(f"Groq omitted the account name in: {', '.join(missing_account_name)}")
    return variants
