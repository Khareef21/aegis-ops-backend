import os
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client
import anthropic

app = FastAPI(title="Aegis Ops API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

supabase = create_client(
    os.environ["SUPABASE_URL"],
    os.environ["SUPABASE_SERVICE_KEY"]
)
claude = anthropic.Anthropic(
    api_key=os.environ["ANTHROPIC_API_KEY"]
)

class EmailPayload(BaseModel):
    raw_email: str
    sender: str = "unknown@vendor.com"
    subject: str = "No subject"

@app.get("/")
async def root():
    return {"status": "Aegis Ops API is running"}

@app.post("/webhook/email")
async def process_email(payload: EmailPayload):
    message = claude.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": f"""You are a supply chain assistant.
Extract data from this vendor email and return ONLY
valid JSON with these exact keys:
- vendor_name (string)
- sku (string)
- delay_days (integer)
- quantity_affected (integer)
If any field is unclear, use null.
Return ONLY the JSON object. No explanation. No markdown.
Email:
{payload.raw_email}"""
        }]
    )
    raw = message.content[0].text.strip()
    try:
        extracted = json.loads(raw)
    except json.JSONDecodeError:
        supabase.table("triage_events").insert({
            "email_raw": payload.raw_email,
            "vendor_name": payload.sender,
            "status": "UNRESOLVED",
            "confidence_score": 0.0
        }).execute()
        return {"status": "UNRESOLVED", "reason": "parse failed"}

    sku        = extracted.get("sku")
    delay_days = extracted.get("delay_days") or 0
    current_stock  = 0
    daily_velocity = 1

    if sku:
        inv = supabase.table("inventory_cache")\
            .select("*").eq("sku", sku).execute()
        if inv.data:
            current_stock  = inv.data[0]["current_stock"]
            daily_velocity = inv.data[0]["daily_velocity"]

    stockout_in     = current_stock / max(daily_velocity, 0.1)
    revenue_at_risk = max(0, (delay_days - stockout_in) * daily_velocity * 90)

    if delay_days > stockout_in:
        status = "CRITICAL"
    elif delay_days > stockout_in * 0.75:
        status = "WARNING"
    else:
        status = "OK"

    draft_msg = claude.messages.create(
        model="claude-haiku-4-5",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"""Write a short, firm, professional B2B reply
to a vendor about a {delay_days}-day delay on SKU {sku}.
Revenue at risk: \${revenue_at_risk:.0f}.
2-3 sentences. No emojis. No fluff."""
        }]
    )
    draft_reply = draft_msg.content[0].text.strip()

    supabase.table("triage_events").insert({
        "email_raw":         payload.raw_email,
        "vendor_name":       extracted.get("vendor_name"),
        "sku":               sku,
        "delay_days":        delay_days,
        "quantity_affected": extracted.get("quantity_affected"),
        "current_stock":     current_stock,
        "daily_velocity":    daily_velocity,
        "revenue_at_risk":   round(revenue_at_risk, 2),
        "status":            status,
        "draft_reply":       draft_reply,
        "confidence_score":  0.92
    }).execute()

    return {
        "status":          status,
        "sku":             sku,
        "delay_days":      delay_days,
        "revenue_at_risk": round(revenue_at_risk, 2),
        "draft_reply":     draft_reply,
        "message":         "Triage event saved"
    }

@app.get("/triage")
async def get_triage():
    result = supabase.table("triage_events")\
        .select("*")\
        .order("revenue_at_risk", desc=True)\
        .execute()
    return result.data

@app.post("/triage/{event_id}/approve")
async def approve_triage(event_id: str):
    supabase.table("triage_events")\
        .update({"status": "RESOLVED"})\
        .eq("id", event_id)\
        .execute()
    return {"status": "RESOLVED", "id": event_id}
