import os
import json
import math
import re
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from openai import OpenAI

# ----------------------------------------------------
# Environment & OpenAI setup
# ----------------------------------------------------
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY is not set. Add it to your .env file.")

client = OpenAI(api_key=OPENAI_API_KEY)

# Path to local knowledge file
KNOWLEDGE_FILE = os.path.join("knowledge", "billing_notes.txt")

# ----------------------------------------------------
# Mock bills table used in the demo
# ----------------------------------------------------
MOCK_BILLS = [
    {
        "patient": "Alex Rivera",
        "account_id": "ACC-1001",
        "service_date": "2024-10-29",
        "service_type": "CT Scan",
        "status": "New",
        "amount_due": 339.47,
    },
    {
        "patient": "Alex Rivera",
        "account_id": "ACC-1002",
        "service_date": "2024-09-29",
        "service_type": "Same Day Surgery",
        "status": "Final Notice",
        "amount_due": 786.91,
    },
    {
        "patient": "Alex Rivera",
        "account_id": "ACC-1003",
        "service_date": "2024-09-15",
        "service_type": "Family Medicine Clinic",
        "status": "Final Notice",
        "amount_due": 840.40,
    },
    {
        "patient": "Alex Rivera",
        "account_id": "ACC-1004",
        "service_date": "2024-10-23",
        "service_type": "Laboratory",
        "status": "New",
        "amount_due": 170.92,
    },
]


def build_mock_bills_summary() -> str:
    """Return natural-language summary of mock bills table for system prompt."""
    total = sum(b["amount_due"] for b in MOCK_BILLS)
    lines = [
        "In this demo portal you can see the following MOCK open balances ",
        "for patient Alex Rivera. All amounts and account IDs are synthetic ",
        "and for classroom use only:",
    ]
    for b in MOCK_BILLS:
        lines.append(
            f"- Account {b['account_id']} ({b['service_type']} on {b['service_date']}), "
            f"status {b['status']}, amount due ${b['amount_due']:.2f}."
        )
    lines.append(
        f"The total amount due across all of these mock balances is ${total:.2f}."
    )
    return "\n".join(lines)


# ----------------------------------------------------
# FastAPI app, templates, static
# ----------------------------------------------------
app = FastAPI(
    title="Billing Helper Demo",
    description="Prototype for billing/insurance education in a mock portal.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.isdir("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

# ----------------------------------------------------
# Knowledge base (simple RAG)
# ----------------------------------------------------
kb_chunks: List[str] = []
kb_embeddings: List[List[float]] = []


def embed_texts(texts: List[str]) -> List[List[float]]:
    """
    Safe embedding function to avoid 8k token overflow.
    Splits text into batches and trims long paragraphs automatically.
    """
    if not texts:
        return []

    all_embeddings = []
    BATCH_SIZE = 20

    for i in range(0, len(texts), BATCH_SIZE):
        batch = texts[i:i + BATCH_SIZE]
        try:
            resp = client.embeddings.create(model=EMBED_MODEL, input=batch)
            all_embeddings.extend([d.embedding for d in resp.data])
        except Exception as e:
            print(f"⚠️ Error embedding batch {i}: {e}")
            trimmed = [t[:4000] for t in batch]
            try:
                resp = client.embeddings.create(model=EMBED_MODEL, input=trimmed)
                all_embeddings.extend([d.embedding for d in resp.data])
            except Exception as e2:
                print(f"⚠️ Skipping batch {i} after second failure: {e2}")
    return all_embeddings


def cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def load_knowledge_base() -> None:
    global kb_chunks, kb_embeddings
    if not os.path.exists(KNOWLEDGE_FILE):
        print(f"⚠️ Knowledge file not found at {KNOWLEDGE_FILE}")
        kb_chunks = []
        kb_embeddings = []
        return

    with open(KNOWLEDGE_FILE, "r", encoding="utf-8") as f:
        text = f.read()

    raw_chunks = [p.strip()[:4000] for p in text.split("\n\n") if p.strip()]
    kb_chunks = raw_chunks
    kb_embeddings = embed_texts(kb_chunks)
    print(f"✅ Loaded {len(kb_chunks)} knowledge chunks for RAG.")


def retrieve_relevant_chunks(query: str, k: int = 4) -> str:
    if not kb_chunks or not kb_embeddings or not query.strip():
        return ""

    q_emb = embed_texts([query])[0]
    scored = [(cosine_similarity(q_emb, emb), chunk)
              for emb, chunk in zip(kb_embeddings, kb_chunks)]
    scored.sort(key=lambda x: x[0], reverse=True)
    top_chunks = [c for _, c in scored[:k]]
    return "\n\n".join(top_chunks)


@app.on_event("startup")
async def on_startup():
    load_knowledge_base()

# ----------------------------------------------------
# Chat logic
# ----------------------------------------------------
class ChatRequest(BaseModel):
    message: str
    language: Optional[str] = "auto"


class ChatResponse(BaseModel):
    reply: str


PHI_PATTERN = re.compile(
    r"(account\s*number|ssn|social\s*security|dob|date\s*of\s*birth|policy\s*number|member\s*id)",
    re.I,
)

ROUTER_SCHEMA = """
You are a strict JSON router. Return ONLY a JSON object with keys:
- intent: one of ["payment_help","portal_navigation","cost_estimate","sensitive_info","other"]
- needs_escalation: boolean
- brief_reason: short string
"""


def route_intent(user_message: str, language_label: str) -> Dict[str, Any]:
    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": ROUTER_SCHEMA},
                {
                    "role": "user",
                    "content": f"Language: {language_label}\nMessage: {user_message}",
                },
            ],
            temperature=0,
        )
        raw = completion.choices[0].message.content.strip()
        data = json.loads(raw)
        return data
    except Exception as e:
        print("⚠️ Router error:", e)
        return {"intent": "other", "needs_escalation": False, "brief_reason": "fallback"}


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request):
    return templates.TemplateResponse("salud_site.html", {"request": request})


@app.get("/portal", response_class=HTMLResponse)
async def manage_bills(request: Request):
    return templates.TemplateResponse("manage.html", {"request": request})


@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    message = (req.message or "").strip()
    if not message:
        return ChatResponse(reply="Please type a question about your bill or insurance.")

    lang_raw = (req.language or "auto").lower()
    language_label = "Spanish" if lang_raw == "es" else "English"

    # PHI protection
    if PHI_PATTERN.search(message):
        if lang_raw == "es":
            safe = ("Por tu seguridad, no compartas números de cuenta, SSN, fecha de nacimiento "
                    "u otros datos personales en este chat. Usa el portal oficial o llama a la oficina de cobros.")
        else:
            safe = ("For your safety, please don’t share account numbers, SSNs, dates of birth, "
                    "or policy/member IDs in this chat. Please use your official billing portal or call the billing office.")
        return ChatResponse(reply=safe)

    route = route_intent(message, language_label)
    if route.get("needs_escalation"):
        if lang_raw == "es":
            return ChatResponse(reply="Esta pregunta necesita ayuda humana. Usa el portal oficial o llama a la oficina de cobros.")
        else:
            return ChatResponse(reply="This looks like it needs a real person. Please contact the billing office.")

    kb_context = retrieve_relevant_chunks(message, k=4)
    mock_bills_text = build_mock_bills_summary()

    system_prompt = f"""
You are a patient-friendly billing and insurance assistant for a health system.

This is a MOCK demo portal for a billing assistant class project. You can "see" only the mock bills below:

{mock_bills_text}

Speak at a 4th–6th grade level. Be concise, kind, and clear.
Do NOT create new accounts or amounts beyond the mock data above.
If the user asks about "my bill", "my balance", or a specific account ID (like ACC-1002),
answer using ONLY that mock data.

If asked about real accounts, always remind them this is a demo and tell them to use the official portal.

Use the internal billing guide below if relevant:
{kb_context}
"""

    user_content = message if lang_raw == "auto" else (
        "Responde en español sencillo. " + message if lang_raw == "es" else "Answer in English. " + message
    )

    try:
        completion = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            temperature=0.4,
        )
        reply = completion.choices[0].message.content.strip()
    except Exception as e:
        print("⚠️ OpenAI error:", e)
        reply = "Sorry, I had trouble reaching the assistant service. Please try again."

    return ChatResponse(reply=reply)