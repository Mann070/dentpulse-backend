from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database.connection import get_db
from app.models.chatbot_history import ChatbotHistory
from app.schemas.patient_schema import ChatbotMessageSchema
from app.routes.patient_auth import get_current_patient
from app.models.patient_account import PatientAccount

router = APIRouter(prefix="/chatbot", tags=["AI Health Chatbot"])

# ─── Dental / Implant Knowledge Base ──────────────────────────────────────────

CHATBOT_KB = [
    {
        "keywords": ["food", "eat", "diet", "drink", "avoid", "soft"],
        "response": (
            "🥗 **Post-Implant Diet Tips:**\n\n"
            "• Stick to soft foods for the first 2 weeks (yogurt, mashed potatoes, soups, smoothies)\n"
            "• Avoid hard, crunchy, or chewy foods (nuts, raw vegetables, tough meat)\n"
            "• No hot or spicy foods for 48 hours\n"
            "• Avoid straws — suction can disturb healing\n"
            "• Stay hydrated with cool water\n"
            "• No alcohol for at least 72 hours after surgery\n\n"
            "*Always follow your doctor's specific dietary instructions.*"
        ),
    },
    {
        "keywords": ["medicine", "medication", "painkiller", "pain", "ibuprofen", "antibiotic", "tablet", "pill", "drug"],
        "response": (
            "💊 **Medication Guidance:**\n\n"
            "• Take prescribed antibiotics for the full course — even if you feel better\n"
            "• For pain, paracetamol or ibuprofen is generally safe (as prescribed)\n"
            "• Do NOT take aspirin — it can increase bleeding risk\n"
            "• Take medications with food to avoid nausea\n"
            "• Never double-dose if you miss one\n\n"
            "⚠️ *Always take medications exactly as prescribed by your doctor. Contact your clinic for any concerns.*"
        ),
    },
    {
        "keywords": ["swell", "swelling", "bruise", "bruising", "puffiness"],
        "response": (
            "🧊 **Managing Swelling:**\n\n"
            "• Mild swelling is completely normal after implant surgery\n"
            "• Apply an ice pack (wrapped in cloth) for 15–20 mins every hour for the first 24 hours\n"
            "• Swelling typically peaks at 48–72 hours and subsides by Day 5–7\n"
            "• Keep your head elevated when sleeping (extra pillow)\n"
            "• Warm salt water rinses help after 48 hours\n\n"
            "*If swelling increases significantly after Day 3, contact your doctor immediately.*"
        ),
    },
    {
        "keywords": ["heal", "healing", "recover", "recovery", "long", "how long", "time", "duration", "weeks"],
        "response": (
            "⏱️ **Implant Healing Timeline:**\n\n"
            "• **0–2 weeks:** Initial healing — follow soft diet and medication plan\n"
            "• **2–4 weeks:** Tissue healing — mild discomfort may persist\n"
            "• **1–3 months:** Osseointegration (implant fusing with bone)\n"
            "• **3–6 months:** Full stabilization — regular check-ups needed\n"
            "• **6 months+:** Final restoration (crown placement)\n\n"
            "*Individual healing varies. Your doctor will track your progress at each follow-up.*"
        ),
    },
    {
        "keywords": ["care", "implant care", "clean", "brush", "hygiene", "oral", "rinse", "mouth"],
        "response": (
            "🦷 **Implant Care & Oral Hygiene:**\n\n"
            "• Gently brush teeth twice daily — avoid the implant site for first 48 hours\n"
            "• Use a soft-bristled toothbrush\n"
            "• Saltwater rinse (1/2 tsp salt in warm water) 3–4 times daily after 24 hours\n"
            "• Do NOT spit forcefully — use gentle rinses\n"
            "• Avoid touching the surgical site with your tongue or fingers\n"
            "• No smoking — it significantly delays healing\n"
            "• Use interdental brushes around the implant after full healing"
        ),
    },
    {
        "keywords": ["smoke", "smoking", "tobacco", "cigarette"],
        "response": (
            "🚭 **Smoking & Implant Healing:**\n\n"
            "Smoking is one of the biggest risk factors for implant failure.\n\n"
            "• Smoking reduces blood flow, slowing healing significantly\n"
            "• It increases infection and implant rejection risk\n"
            "• Strongly advised to quit at least 1 week before and 6–8 weeks after surgery\n"
            "• If you cannot quit, please inform your doctor for a customized plan\n\n"
            "*Studies show smokers have 3× higher implant failure rates. Your health is worth it!*"
        ),
    },
    {
        "keywords": ["bleed", "bleeding", "blood"],
        "response": (
            "🩸 **Managing Bleeding:**\n\n"
            "• Mild bleeding/oozing is normal for the first 24 hours\n"
            "• Bite gently on a gauze pad for 30–45 minutes\n"
            "• Avoid spitting or rinsing forcefully for 24 hours\n"
            "• No straws — suction worsens bleeding\n"
            "• Keep your head elevated\n\n"
            "⚠️ *If bleeding is heavy or doesn't stop after 1–2 hours, contact your doctor or go to emergency care immediately.*"
        ),
    },
    {
        "keywords": ["fever", "temperature", "infection", "pus", "discharge"],
        "response": (
            "🌡️ **Signs of Infection:**\n\n"
            "Contact your doctor immediately if you experience:\n\n"
            "• Fever above 38°C (100.4°F)\n"
            "• Increasing (not decreasing) pain after Day 3\n"
            "• Foul taste or smell from the surgical site\n"
            "• Visible pus or yellow/green discharge\n"
            "• Excessive swelling that keeps growing\n"
            "• Difficulty opening your mouth\n\n"
            "*Early treatment of infection is crucial for implant success. Do not wait.*"
        ),
    },
    {
        "keywords": ["exercise", "sport", "gym", "physical", "activity", "work"],
        "response": (
            "🏃 **Physical Activity After Implant Surgery:**\n\n"
            "• Rest completely for the first 24–48 hours\n"
            "• Avoid strenuous exercise for at least 5–7 days\n"
            "• No contact sports, swimming, or heavy lifting for 2 weeks\n"
            "• Light walking is encouraged after 48 hours to improve circulation\n"
            "• Avoid bending over (increases blood pressure in head)\n\n"
            "*Resume normal activities gradually — listen to your body and your doctor's guidance.*"
        ),
    },
    {
        "keywords": ["appointment", "visit", "check", "follow", "followup", "next", "schedule", "when"],
        "response": (
            "📅 **Your Follow-Up Schedule:**\n\n"
            "Typical implant follow-up schedule:\n\n"
            "• **24–48 hours:** Initial check (bleeding, swelling)\n"
            "• **1 week:** Suture removal and healing assessment\n"
            "• **1 month:** Osseointegration progress review\n"
            "• **3 months:** Stability check (ISQ measurement)\n"
            "• **6 months:** Final crown placement assessment\n\n"
            "*Use the Appointments tab to book your next visit with your doctor.*"
        ),
    },
    {
        "keywords": ["hello", "hi", "hey", "help", "start", "good morning", "good evening"],
        "response": (
            "👋 **Hello! I'm your DentPulse AI Health Assistant.**\n\n"
            "I can help you with:\n\n"
            "• 🥗 **Food Advice** — What to eat after surgery\n"
            "• 💊 **Medicines** — Medication guidance\n"
            "• 🦷 **Implant Care** — Oral hygiene tips\n"
            "• ⏱️ **Recovery Tips** — Healing timeline\n"
            "• 🌡️ **Symptoms** — Understanding post-op symptoms\n\n"
            "Just type your question and I'll guide you!"
        ),
    },
]


def get_chatbot_response(message: str) -> str:
    message_lower = message.lower().strip()

    for entry in CHATBOT_KB:
        if any(kw in message_lower for kw in entry["keywords"]):
            return entry["response"]

    # Default fallback for unrecognized queries
    return (
        "🤖 **DentPulse AI Assistant:**\n\n"
        "I understand you have a question about your dental health. "
        "For personalized medical advice, please consult your treating doctor directly.\n\n"
        "I can help you with:\n"
        "• 🥗 Food & Diet after implant surgery\n"
        "• 💊 Medication guidance\n"
        "• 🦷 Oral hygiene & implant care\n"
        "• ⏱️ Recovery timeline & healing tips\n"
        "• 🌡️ Recognizing infection symptoms\n\n"
        "Try asking: *'What can I eat after surgery?'* or *'How long does healing take?'*"
    )


@router.post("/message")
async def send_chatbot_message(
    payload: ChatbotMessageSchema,
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    response = get_chatbot_response(payload.message)

    # Persist conversation entry
    history_entry = ChatbotHistory(
        patient_account_id=current_patient.id,
        message=payload.message,
        response=response,
    )
    db.add(history_entry)
    await db.commit()
    await db.refresh(history_entry)

    return {
        "message": payload.message,
        "response": response,
        "timestamp": history_entry.created_at.isoformat() if history_entry.created_at else None,
    }


@router.get("/history")
async def get_chatbot_history(
    db: AsyncSession = Depends(get_db),
    current_patient: PatientAccount = Depends(get_current_patient),
):
    result = await db.execute(
        select(ChatbotHistory)
        .filter(ChatbotHistory.patient_account_id == current_patient.id)
        .order_by(ChatbotHistory.created_at.asc())
    )
    history = result.scalars().all()
    return [
        {
            "id": h.id,
            "message": h.message,
            "response": h.response,
            "created_at": h.created_at.isoformat() if h.created_at else None,
        }
        for h in history
    ]
