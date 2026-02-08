"""
GenAI-powered chat for appointment booking.
Uses Gemini or OpenAI to extract service_type, location, timeframe from natural conversation.
Goal: fulfill the task without needing to ask back; else mark requires_user_attention.
"""
import os
import json
import re
from typing import Dict, List, Optional, Any

# Required fields for a booking task
REQUIRED_FIELDS = ["service_type", "location", "timeframe"]

# Valid service_type values (for normalization)
SERVICE_TYPES = [
    "dentist", "doctor", "hair_salon", "barber", "auto_mechanic", "plumber",
    "electrician", "massage", "veterinarian", "restaurant"
]

SYSTEM_PROMPT = """You are CallPilot's friendly AI assistant. Your job is to help the user book an appointment by learning what they need in a natural conversation.

You must extract and maintain:
- service_type: one of dentist, doctor, hair_salon, barber, auto_mechanic, plumber, electrician, massage, veterinarian, restaurant (normalize: "dental" -> dentist, "medical" -> doctor, "hair cut" -> hair_salon, "dinner" -> restaurant, etc.)
- location: city/area or full address (e.g. "Cambridge, MA", "Boston", "123 Main St Boston")
- timeframe: when they need it (e.g. "today", "tomorrow", "this week", "next week", "asap")

Rules:
1. Be conversational and warm. Don't ask robotic step-by-step questions; infer from context when possible.
2. If the user gives multiple pieces of info in one message (e.g. "I need a dentist in Boston this week"), extract all of them and confirm naturally.
3. Only ask for what's still missing. If you have everything, summarize and ask them to confirm so we can call providers.
4. If the user is vague or you're unsure after a few exchanges, ask one clear, friendly question to disambiguate.
5. If you cannot get service_type, location, or timeframe after reasonable back-and-forth, say you'll need a bit more info and output status "requires_user_attention" so a human can help.
6. When you have service_type, location, and timeframe, summarize and ask: "Should I call providers to find you the best options?" Then output status "ready_to_call".
7. Reply in 1-3 short sentences. Be helpful and human.

At the end of your reply, output a single line in this exact format (no other text on this line):
CALLPILOT_JSON: {"service_type": "...", "location": "...", "timeframe": "...", "status": "gathering_info"|"ready_to_call"|"requires_user_attention"}
Use status "gathering_info" while still missing any required field; "ready_to_call" when all three are present and you've asked to proceed; "requires_user_attention" when you can't get what's needed."""


def _parse_model_json(reply: str) -> Optional[Dict]:
    """Extract CALLPILOT_JSON line from model reply."""
    for line in reply.strip().split("\n"):
        line = line.strip()
        if line.startswith("CALLPILOT_JSON:"):
            try:
                json_str = line.replace("CALLPILOT_JSON:", "").strip()
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass
    return None


def _normalize_extracted(data: Dict) -> Dict:
    """Normalize and validate extracted data."""
    out = {}
    st = (data.get("service_type") or "").strip().lower().replace(" ", "_")
    if st:
        mapping = {"dental": "dentist", "teeth": "dentist", "medical": "doctor", "physician": "doctor", "hair": "hair_salon", "salon": "hair_salon", "dinner": "restaurant", "lunch": "restaurant", "reservation": "restaurant", "table": "restaurant"}
        out["service_type"] = mapping.get(st, st) if st in mapping else (st if st in SERVICE_TYPES else st)
    loc = (data.get("location") or "").strip()
    if loc:
        out["location"] = loc
    tf = (data.get("timeframe") or "").strip().lower()
    if tf:
        tf_map = {"today": "today", "tomorrow": "tomorrow", "asap": "today", "soon": "this week", "this week": "this week", "next week": "next week", "this month": "this month", "this_week": "this week", "next_week": "next week"}
        out["timeframe"] = tf_map.get(tf.replace(" ", "_"), tf_map.get(tf, tf))
    return out


def _build_conversation_blob(messages: List[Dict], extracted_so_far: Dict) -> str:
    """Single blob: system + current extracted + conversation for one-shot API call."""
    context = f"Current extracted: service_type={extracted_so_far.get('service_type') or '(not yet)'}, location={extracted_so_far.get('location') or '(not yet)'}, timeframe={extracted_so_far.get('timeframe') or '(not yet)'}."
    lines = [f"{SYSTEM_PROMPT}\n\n{context}\n\nConversation so far:"]
    for m in messages:
        prefix = "User" if m["role"] == "user" else "Assistant"
        lines.append(f"{prefix}: {m['content']}")
    lines.append("Assistant:")
    return "\n".join(lines)


def chat_with_gemini(messages: List[Dict], extracted_so_far: Dict) -> tuple[str, Dict, str]:
    """
    Use Gemini to get next reply and updated extraction.
    Returns (assistant_message_clean, extracted_data, status).
    """
    try:
        import google.generativeai as genai
    except ImportError:
        return "I'm having trouble with the AI service. Please try again.", extracted_so_far, "requires_user_attention"

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return "Gemini API key is not configured.", extracted_so_far, "requires_user_attention"

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
    prompt = _build_conversation_blob(messages, extracted_so_far)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.4,
                max_output_tokens=512,
            ),
        )
        reply = (response.text or "").strip()
    except Exception as e:
        return f"Something went wrong: {str(e)}", extracted_so_far, "requires_user_attention"

    parsed = _parse_model_json(reply)
    if parsed:
        status = parsed.get("status", "gathering_info")
        new_extracted = _normalize_extracted(parsed)
        for k, v in new_extracted.items():
            if v:
                extracted_so_far[k] = v
        if status == "ready_to_call" and not all(extracted_so_far.get(f) for f in REQUIRED_FIELDS):
            status = "gathering_info"
        clean_reply = re.sub(r"\n?CALLPILOT_JSON:.*$", "", reply, flags=re.MULTILINE | re.DOTALL).strip()
        return clean_reply or "Got it.", extracted_so_far, status

    return reply, extracted_so_far, "gathering_info"


def chat_with_openai(messages: List[Dict], extracted_so_far: Dict) -> tuple[str, Dict, str]:
    """
    Use OpenAI to get next reply and updated extraction.
    Returns (assistant_message_clean, extracted_data, status).
    """
    try:
        from openai import OpenAI
    except ImportError:
        return "OpenAI is not installed.", extracted_so_far, "requires_user_attention"

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "OpenAI API key is not configured.", extracted_so_far, "requires_user_attention"

    client = OpenAI(api_key=api_key)
    # Use same system prompt; conversation as user messages + one assistant turn
    openai_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    context = f"Current extracted: service_type={extracted_so_far.get('service_type') or '(not yet)'}, location={extracted_so_far.get('location') or '(not yet)'}, timeframe={extracted_so_far.get('timeframe') or '(not yet)'}."
    openai_messages.append({"role": "user", "content": context})
    for m in messages:
        openai_messages.append({"role": m["role"], "content": m["content"]})

    try:
        resp = client.chat.completions.create(
            model=os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini"),
            messages=openai_messages,
            temperature=0.4,
            max_tokens=512,
        )
        reply = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        err = str(e)
        if "429" in err or "quota" in err.lower() or "insufficient_quota" in err.lower():
            return (
                "OpenAI quota exceeded. Add GEMINI_API_KEY to your server .env to use Google Gemini instead, or check your OpenAI plan and billing.",
                extracted_so_far,
                "requires_user_attention",
            )
        return f"Something went wrong: {err}", extracted_so_far, "requires_user_attention"

    parsed = _parse_model_json(reply)
    if parsed:
        status = parsed.get("status", "gathering_info")
        new_extracted = _normalize_extracted(parsed)
        for k, v in new_extracted.items():
            if v:
                extracted_so_far[k] = v
        if status == "ready_to_call" and not all(extracted_so_far.get(f) for f in REQUIRED_FIELDS):
            status = "gathering_info"
        clean_reply = re.sub(r"\n?CALLPILOT_JSON:.*$", "", reply, flags=re.MULTILINE | re.DOTALL).strip()
        return clean_reply or "Got it.", extracted_so_far, status

    return reply, extracted_so_far, "gathering_info"


def chat(messages: List[Dict], extracted_so_far: Dict) -> tuple[str, Dict, str]:
    """Use configured provider. Prefer Gemini (avoids OpenAI quota issues); fallback to OpenAI."""
    if os.getenv("GEMINI_API_KEY"):
        return chat_with_gemini(messages, extracted_so_far)
    if os.getenv("OPENAI_API_KEY"):
        return chat_with_openai(messages, extracted_so_far)
    return "Please set GEMINI_API_KEY or OPENAI_API_KEY in the server environment.", extracted_so_far, "requires_user_attention"
