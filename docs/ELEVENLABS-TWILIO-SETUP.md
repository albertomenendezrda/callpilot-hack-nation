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
