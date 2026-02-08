# ElevenLabs + Twilio: Fix “call hangs up immediately”

If the outbound call connects but **hangs up right after the other party answers**, the agent is usually misconfigured for Twilio. Apply these in the **ElevenLabs dashboard** for the agent you use with `ELEVENLABS_AGENT_ID`:

## 1. TTS output format (required for Twilio)

- Go to your **agent** → **Voice** (or equivalent) section.
- Set **TTS output format** to **μ-law 8000 Hz** (telephony format).  
- If you leave the default (e.g. PCM 24kHz), Twilio may get invalid audio and drop the call.

## 2. Input format (for caller audio)

- In the agent’s **Advanced** (or similar) section.
- Set **Input format** to **μ-law 8000 Hz** so the agent receives telephony audio correctly.

## 3. Overrides (so our app can inject the prompt)

- In the agent’s **Security** or **Configuration** section.
- Enable **“System prompt” override** (required). CallPilot sends the full prompt including the opening line; the agent must allow prompt overrides.
- “First message” override is optional; CallPilot does not send it (the opening line is included in the prompt instead).

## 4. First message on the agent

- Ensure the agent has some default first message configured (it will be overridden per call by CallPilot, but the field must exist).

After saving, try another outbound call. If it still drops, double-check that the **phone number** linked in ElevenLabs is the same one you’re using for `ELEVENLABS_AGENT_PHONE_NUMBER_ID` and that it’s correctly connected to Twilio in the ElevenLabs Phone Numbers tab.

---

## Post-call webhook (optional): mark tasks completed when calls end

When using ElevenLabs outbound calls, the app keeps the booking in "Processing" until each call is finished. To update results and mark the task "Completed" when a call actually ends:

1. **Expose your backend** so ElevenLabs can reach it (e.g. ngrok: `ngrok http 8080`, or your production URL).
2. In **ElevenLabs** → **Agents** → **Settings** (or workspace settings) → **Post-call webhooks**, add a webhook:
   - **URL:** `https://your-domain.com/api/webhooks/elevenlabs`
   - Enable **Transcription** (and optionally **Call initiation failure**).
   - If you use HMAC authentication, copy the **secret** and set it in your `.env` as `ELEVENLABS_WEBHOOK_SECRET`.
3. Ensure the backend has `ELEVENLABS_WEBHOOK_SECRET` set to the same value as in the dashboard (or leave unset to skip signature verification, e.g. for local testing with ngrok).

When a call ends, ElevenLabs sends a POST to that URL. The backend finds the booking by `conversation_id`, updates that provider's result to completed/failed, and if all calls are done, marks the booking as completed.
