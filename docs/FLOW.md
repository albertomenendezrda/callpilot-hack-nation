# CallPilot flow — where it happens

## 1. Inbound: user chat → task → booking

| Step | Where it happens | File:line (approx) |
|------|------------------|--------------------|
| User opens Chat | Frontend creates a task on load | `frontend/app/dashboard/chat/page.tsx` — `useEffect` → `POST /api/task` |
| Create task | Backend creates task in DB | `backend/app.py` — `create_task()` ~425, `db.create_task()` in `database.py` |
| User sends a message | Frontend posts to chat API | `frontend/app/dashboard/chat/page.tsx` — `processUserInput()` → `POST /api/chat` |
| Chat API | Backend loads task, calls GenAI, updates task | `backend/app.py` — `chat()` ~437; `services/chat_service.py` — `chat()` (Gemini/OpenAI) |
| User confirms "Call providers" | Frontend creates booking with extracted data | `frontend/app/dashboard/chat/page.tsx` — `confirmAndCallProviders()` → `apiClient.createBookingRequest()` |
| Create booking | Backend stores booking, starts outbound calls in background | `backend/app.py` — `create_booking_request()` ~498; background thread calls `make_real_calls()` ~530 |

---

## 2. Outbound: booking → calling providers

**Primary integration is ElevenLabs.** When ElevenLabs is configured, we only call the ElevenLabs API; they place the call (they use Twilio on their side). Our Twilio client is used only as a fallback when ElevenLabs is not set (scripted TwiML, no AI).

| Step | Where it happens | File:line (approx) |
|------|------------------|--------------------|
| Start calls | Runs in background thread after booking is created | `backend/app.py` — `run_calls()` inside `create_booking_request()` ~524–534 |
| Get providers + make calls | Builds `booking_context`, loops over providers, calls Twilio or ElevenLabs | `backend/app.py` — `make_real_calls(service_type, location, timeframe)` ~144–266 |
| **ElevenLabs path** (if `ELEVENLABS_AGENT_ID` + `ELEVENLABS_AGENT_PHONE_NUMBER_ID` set) | Builds prompt + first message, calls ElevenLabs outbound API | `backend/services/elevenlabs_service.py` — `make_elevenlabs_outbound_call()` ~63–136; uses `agent_prompts.get_first_message()`, `get_agent_prompt()` |
| **Twilio fallback** (no ElevenLabs agent IDs) | Our app uses Twilio directly with scripted TwiML (no AI). Only used when ElevenLabs is not configured. | `backend/services/twilio_service.py` — `make_call()`; optional `twilio_voice_webhook()` in `app.py` |

---

## 3. Prompts and context (outbound calls)

| What | Where |
|------|--------|
| First message (“on behalf of Alberto Menendez”, “He’s looking for [timeframe]”) | `backend/agent_prompts.py` — `get_first_message()` |
| Full agent prompt (goal, steps, guardrails, stopping conditions) | `backend/agent_prompts.py` — `BASE_AGENT_PROMPT`, `get_agent_prompt()`, vertical prompts |
| Continuity block (“complete the booking on this call”) | `backend/services/elevenlabs_service.py` — `make_elevenlabs_outbound_call()` ~95–104 |
| `booking_context` (service_type, timeframe, location, client_name) | Built in `backend/app.py` — `make_real_calls()` ~176–181; passed into Twilio and ElevenLabs |

---

## 4. Quick reference

- **Inbound chat UI:** `frontend/app/dashboard/chat/page.tsx`
- **Chat API + task creation:** `backend/app.py` — routes `/api/task`, `/api/chat`
- **GenAI extraction (Gemini/OpenAI):** `backend/services/chat_service.py`
- **Booking creation + starting calls:** `backend/app.py` — `create_booking_request()`, `make_real_calls()`
- **Outbound calls (ElevenLabs):** `backend/services/elevenlabs_service.py` — `make_elevenlabs_outbound_call()`
- **Outbound calls (Twilio):** `backend/services/twilio_service.py` — `make_call()`; TwiML in `backend/app.py` — `_twilio_voice_twiml()`, `twilio_voice_webhook()`
- **Agent copy and first message:** `backend/agent_prompts.py`
