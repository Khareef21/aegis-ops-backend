# Aegis Ops — Autonomous Supply Chain Triage Agent

An AI-powered middleware that automatically reads vendor emails,
calculates stockout risk, and generates draft replies — 
so operations teams spend 10 seconds per alert instead of 3 hours.

## Live Demo
[aegis-ops-dashboard.vercel.app](https://aegis-ops-dashboard.vercel.app)

## What it does
1. Vendor sends a delay email
2. Gemini AI extracts: vendor, SKU, delay days, quantity affected
3. System checks real-time inventory from database
4. Calculates revenue at risk and stockout timeline
5. Classifies alert as CRITICAL / WARNING / OK
6. Generates a professional vendor reply draft
7. Saves everything to Supabase
8. Dashboard shows ops manager the card with Approve / Reject buttons

## Tech Stack
- **Backend:** Python, FastAPI, Uvicorn
- **AI:** Google Gemini 2.5 Flash (free tier)
- **Database:** Supabase (PostgreSQL)
- **Frontend:** Next.js, deployed on Vercel
- **Architecture:** Event-driven webhook pipeline

## API Endpoints
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Health check |
| POST | /webhook/email | Process a vendor email |
| GET | /triage | Get all triage events |
| POST | /triage/{id}/approve | Approve and resolve an event |

## Local Setup
```bash
git clone https://github.com/Khareef21/aegis-ops-backend.git
cd aegis-ops-backend
pip install -r requirements.txt
```

Add these environment variables:
```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
GEMINI_API_KEY=your_gemini_key
```

Run the server:
```bash
uvicorn main:app --host 0.0.0.0 --port 8001
```

## Test the webhook
```bash
curl -X POST http://localhost:8001/webhook/email \
  -H "Content-Type: application/json" \
  -d '{"raw_email": "Your order of SKU-TSHIRT-WHT-L 
       will be delayed by 8 days.", 
       "sender": "vendor@example.com"}'
```

## Sample Response
```json
{
  "status": "CRITICAL",
  "sku": "SKU-TSHIRT-WHT-L",
  "delay_days": 8,
  "revenue_at_risk": 2430.0,
  "draft_reply": "We acknowledge the 8-day delay...",
  "message": "Triage event saved to Supabase"
}
```

## Built by
Khareef Shaik — 3rd year B.Tech CSE (AIML)  
CMR Institute of Technology, Hyderabad  
GitHub: [@Khareef21](https://github.com/Khareef21)
