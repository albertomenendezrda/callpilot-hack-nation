# Voice Chat Integration Guide

## ✅ VOICE AI NOW LIVE!

The **Voice AI** interface (`/dashboard/voice`) is now fully implemented with ElevenLabs TTS for natural-sounding voices!

### Current Voice Setup

**ElevenLabs Voice Options** (change in `/dashboard/voice/page.tsx` and `/backend/app.py`):

- **Sarah** (Default): `EXAVITQu4vr4xnSDxMaL` - Warm, friendly female voice ✨
- **Rachel**: `21m00Tcm4TlvDq8ikWAM` - Professional, clear female voice
- **Adam**: `pNInz6obpgDQGcFmaJgB` - Confident, natural male voice
- **Antoni**: `ErXwobaYiN019PkySvjV` - Deep, calm male voice
- **Bella**: `EXAVITQu4vr4xnSDxMaL` - Soft, gentle female voice
- **Josh**: `TxGEqnHWrfWFTfGW9XjX` - Energetic, young male voice

To change the voice, update the `voice_id` parameter in:
- Frontend: `/dashboard/voice/page.tsx` line 81
- Backend: `/backend/app.py` in the `/api/tts` endpoint

## Current Implementation

The chat interface is now the primary booking method. Users can have a natural conversation with the AI to book appointments.

### ✅ What's Working

**Text-based Conversational AI**:
- Natural language understanding for booking requests
- Extracts: service type, location, timeframe
- Confirms details before creating booking
- Quick reply buttons for faster input
- Auto-redirects to progress page when booking starts

**Smart Detection**:
- Recognizes 9 service types (dentist, doctor, hair salon, etc.)
- Understands location queries
- Parses timeframe preferences (today, this week, etc.)

## 🎤 Enabling Voice Input with ElevenLabs

To add voice chat capabilities, you need to integrate ElevenLabs Conversational AI:

### Option 1: Browser Speech Recognition (Quick Start)

Add basic voice input using Web Speech API:

```typescript
// In chat/page.tsx

const recognition = new (window as any).webkitSpeechRecognition();
recognition.continuous = false;
recognition.interimResults = false;

const toggleVoice = () => {
  if (!isListening) {
    recognition.start();
    setIsListening(true);

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      setInput(transcript);
      setIsListening(false);
    };

    recognition.onerror = () => {
      setIsListening(false);
    };
  } else {
    recognition.stop();
    setIsListening(false);
  }
};
```

**Pros**: Simple, no backend needed
**Cons**: Basic quality, no AI voice response

### Option 2: ElevenLabs Conversational AI (Full Voice Chat)

For full duplex voice conversation:

#### 1. Backend WebSocket Endpoint

```python
# In backend/routes/voice_chat.py

from flask_socketio import SocketIO, emit
from elevenlabs import ElevenLabs
import asyncio

socketio = SocketIO(app, cors_allowed_origins="*")

@socketio.on('start_voice_chat')
def handle_voice_chat(data):
    """Handle voice chat session"""
    client = ElevenLabs(api_key=os.getenv('ELEVENLABS_API_KEY'))

    # Create conversational AI agent
    agent = client.conversational_ai.create_agent(
        name="CallPilot Booking Agent",
        prompt="""You are a helpful booking assistant for CallPilot.

        Your job:
        1. Ask what service they need (dentist, doctor, hair salon, etc.)
        2. Ask for their location
        3. Ask when they need the appointment
        4. Confirm details and initiate the search

        Be friendly, natural, and concise.""",
        voice_id="21m00Tcm4TlvDq8ikWAM",  # Rachel voice
        model="eleven_multilingual_v2"
    )

    # Start voice conversation
    conversation_id = client.conversational_ai.start_conversation(
        agent_id=agent.id,
        # WebSocket connection details
    )

    emit('voice_ready', {'conversation_id': conversation_id})

@socketio.on('audio_chunk')
def handle_audio(data):
    """Receive user audio and send to ElevenLabs"""
    # Forward audio to ElevenLabs
    # Receive AI response
    # Send back to frontend
    pass
```

#### 2. Frontend Voice Integration

```typescript
// In chat/page.tsx

import { io } from 'socket.io-client';

const [socket, setSocket] = useState<any>(null);
const [audioContext, setAudioContext] = useState<AudioContext | null>(null);

useEffect(() => {
  const newSocket = io('http://localhost:8080');
  setSocket(newSocket);

  newSocket.on('voice_ready', (data) => {
    console.log('Voice chat ready:', data.conversation_id);
  });

  newSocket.on('ai_response_audio', (audioData) => {
    // Play AI voice response
    playAudio(audioData);
  });

  return () => newSocket.close();
}, []);

const startVoiceChat = async () => {
  const context = new AudioContext();
  setAudioContext(context);

  const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  const source = context.createMediaStreamSource(stream);

  // Process and send audio chunks to backend
  const processor = context.createScriptProcessor(4096, 1, 1);
  processor.onaudioprocess = (e) => {
    const audioData = e.inputBuffer.getChannelData(0);
    socket.emit('audio_chunk', audioData);
  };

  source.connect(processor);
  processor.connect(context.destination);

  setIsListening(true);
};
```

### Option 3: ElevenLabs Text-to-Speech for Responses

Add voice responses to text chat (simpler than full voice):

```typescript
const speakResponse = async (text: string) => {
  const response = await fetch('http://localhost:8080/api/tts', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text,
      voice_id: '21m00Tcm4TlvDq8ikWAM'
    })
  });

  const audioBlob = await response.blob();
  const audioUrl = URL.createObjectURL(audioBlob);
  const audio = new Audio(audioUrl);
  audio.play();
};
```

Backend endpoint:
```python
from elevenlabs import generate

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    data = request.json
    text = data.get('text')
    voice_id = data.get('voice_id', '21m00Tcm4TlvDq8ikWAM')

    audio = generate(
        text=text,
        voice=voice_id,
        model="eleven_monolingual_v1"
    )

    return audio, 200, {'Content-Type': 'audio/mpeg'}
```

## 🔧 Implementation Checklist

- [x] Text-based conversational interface
- [x] Natural language understanding
- [x] Booking data extraction
- [x] Auto-redirect to progress
- [ ] Browser speech recognition (Option 1)
- [ ] ElevenLabs TTS for responses (Option 3)
- [ ] Full duplex voice chat (Option 2)
- [ ] WebSocket infrastructure
- [ ] Audio processing pipeline

## 📊 Recommended Approach

**For Demo/MVP**: Start with Option 1 (Browser Speech Recognition)
**For Production**: Implement Option 2 (Full ElevenLabs Conversational AI)

## 🎯 Current User Flow

1. User clicks "Try CallPilot" → Goes to `/dashboard/chat`
2. AI greets: "What type of appointment do you need?"
3. User types/speaks: "I need a dentist"
4. AI: "Where are you located?"
5. User: "Cambridge, MA"
6. AI: "When do you need this appointment?"
7. User: "This week"
8. AI confirms details and creates booking
9. Auto-redirects to `/booking/{id}/progress`
10. Shows live calling progress

## 💡 Tips

- Keep voice prompts short and clear
- Add visual feedback when listening
- Show transcript of what was heard
- Provide quick reply buttons as backup
- Handle errors gracefully (background noise, unclear speech)

## 🎤 Voice Commands to Support

- "I need a [service]"
- "Book me a [service] appointment"
- "Find me a [service] in [location]"
- "I'm looking for [service] [timeframe]"
- "Yes" / "No" / "Confirm" / "Cancel"
- "Change location/service/time"

## 📚 Resources

- [ElevenLabs Conversational AI](https://elevenlabs.io/docs/conversational-ai/overview)
- [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API)
- [Socket.IO Documentation](https://socket.io/docs/v4/)
- [ElevenLabs Text-to-Speech](https://elevenlabs.io/docs/api-reference/text-to-speech)
