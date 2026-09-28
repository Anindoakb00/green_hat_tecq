"""Extract, chunk, embed, and persist campaign PDFs into Supabase brand knowledge.

Run from the backend directory with: python ingest_pdfs.py
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from dotenv import load_dotenv
from pypdf import PdfReader
import fitz
import pytesseract
from sentence_transformers import SentenceTransformer
from supabase import Client, create_client

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
CHUNK_SIZE = 600
CHUNK_OVERLAP = 50
WINDOWS_TESSERACT = Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into paragraph-aware chunks with a small character overlap."""
    normalized = re.sub(r"\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start + chunk_size // 2, end)
            if boundary > start:
                end = boundary
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        next_start = max(end - overlap, start + 1)
        start = next_start
    return chunks


def extract_pdf_text(path: Path) -> str:
    reader = PdfReader(str(path))
    text = "\n".join(page.extract_text() or "" for page in reader.pages)
    if text.strip():
        return text

    try:
        if WINDOWS_TESSERACT.exists():
            pytesseract.pytesseract.tesseract_cmd = str(WINDOWS_TESSERACT)
        with fitz.open(path) as document:
            pages = []
            for page_number, page in enumerate(document, start=1):
                print(f"  OCR page {page_number}/{document.page_count}...")
                pixmap = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                from PIL import Image
                import io
                image = Image.open(io.BytesIO(pixmap.tobytes("png")))
                pages.append(pytesseract.image_to_string(image))
            return "\n".join(pages)
    except pytesseract.TesseractNotFoundError as exc:
        raise RuntimeError("This PDF is image-based and Tesseract OCR is not installed. Install Tesseract, then retry.") from exc


def ingest_pdfs(owner_id: str | None = None) -> dict[str, int]:
    load_dotenv(BASE_DIR / ".env")
    supabase_url = os.getenv("SUPABASE_URL")
    service_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    owner_id = owner_id or os.getenv("SUPABASE_OWNER_USER_ID")
    if not supabase_url or not service_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in backend/.env")
    pdfs = sorted(DATA_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDF files found in {DATA_DIR}")
        return {}
    print(f"Loading embedding model for {len(pdfs)} PDF file(s)...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    client: Client = create_client(supabase_url, service_key)
    if not owner_id:
        owners = client.table("accounts").select("agency_user_id").execute().data or []
        owner_ids = sorted({row["agency_user_id"] for row in owners if row.get("agency_user_id")})
        if len(owner_ids) != 1:
            raise RuntimeError("Set SUPABASE_OWNER_USER_ID in backend/.env when zero or multiple agency users exist")
        owner_id = owner_ids[0]
        print(f"Using the only agency user found in accounts: {owner_id}")
    counts: dict[str, int] = {}
    for pdf_path in pdfs:
        print(f"Processing {pdf_path.name}...")
        try:
            chunks = chunk_text(extract_pdf_text(pdf_path))
            if not chunks:
                print(f"Skipped {pdf_path.name}: no extractable text (OCR is required for scanned PDFs)")
                continue
            client.table("brand_knowledge").delete().eq("agency_user_id", owner_id).eq("theme_name", pdf_path.name).execute()
            embeddings = model.encode(chunks, normalize_embeddings=True).tolist()
            rows = [
                {
                    "agency_user_id": owner_id,
                    "theme_name": pdf_path.name,
                    "content": chunk,
                    "embedding": embedding,
                }
                for chunk, embedding in zip(chunks, embeddings)
            ]
            client.table("brand_knowledge").insert(rows).execute()
            counts[pdf_path.name] = len(rows)
            print(f"Replaced with {len(rows)} chunks for {pdf_path.name}")
        except Exception as exc:
            print(f"Failed {pdf_path.name}: {exc}")
    if not counts:
        raise RuntimeError("No chunks were inserted. Check OCR installation and backend logs.")
    print("PDF ingestion complete.")
    return counts


def main() -> None:
    ingest_pdfs()


if __name__ == "__main__":
    main()
