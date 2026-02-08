'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import {
  Mic,
  MicOff,
  Loader2,
  MessageSquare,
  Calendar,
  MapPin,
  Clock,
  CheckCircle2,
  Send
} from 'lucide-react';
import { apiClient, BookingRequest } from '@/lib/api-client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface BookingData {
  service_type?: string;
  location?: string;
  timeframe?: string;
}

export default function VoiceBookingPage() {
  const router = useRouter();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [bookingData, setBookingData] = useState<BookingData>({});
  const [currentStep, setCurrentStep] = useState<'service' | 'location' | 'timeframe' | 'confirm' | 'done'>('service');
  const [transcriptText, setTranscriptText] = useState('');
  const [textInput, setTextInput] = useState('');
  const recognitionRef = useRef<any>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const initializedRef = useRef(false);

  useEffect(() => {
    // Welcome message when component mounts (only once, even with React Strict Mode)
    if (!initializedRef.current) {
      initializedRef.current = true;
      const welcomeMessage = "Hi! I'm your AI assistant. I'll help you book an appointment. What type of service do you need?";
      addMessage('assistant', welcomeMessage);
      speak(welcomeMessage);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty dependency array ensures this runs only once

  useEffect(() => {
    // Cleanup
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
    };
  }, []);

  const addMessage = (role: 'user' | 'assistant', content: string) => {
    setMessages(prev => [...prev, { role, content, timestamp: new Date() }]);
  };

  const speak = async (text: string) => {
    try {
      // Stop any currently playing audio
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }

      setIsSpeaking(true);

      // Try ElevenLabs TTS first
      try {
        const response = await fetch('http://localhost:8080/api/tts', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            text,
            voice_id: 'EXAVITQu4vr4xnSDxMaL' // Sarah - warm, natural female voice
          }),
        });

        if (response.ok) {
          // ElevenLabs TTS succeeded
          const audioBlob = await response.blob();
          const audioUrl = URL.createObjectURL(audioBlob);
          const audio = new Audio(audioUrl);

          audio.onended = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
          };

          audio.onerror = () => {
            setIsSpeaking(false);
            URL.revokeObjectURL(audioUrl);
          };

          audioRef.current = audio;
          await audio.play();
          return; // Success, exit early
        }
      } catch (elevenLabsError) {
        console.log('ElevenLabs TTS not available, using browser TTS');
      }

      // Fallback to browser TTS with enhanced settings
      setIsSpeaking(true);

      // Load voices if not already loaded
      let voices = window.speechSynthesis.getVoices();

      const speakWithVoice = () => {
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.1; // Slightly faster for more natural flow
        utterance.pitch = 1.0;
        utterance.volume = 1.0;

        // Try to use the best quality voice available
        voices = window.speechSynthesis.getVoices();

        // Priority order: Premium voices > Enhanced voices > Default
        const preferredVoice = voices.find(v =>
          v.name.includes('Samantha') || // Mac - best quality
          v.name.includes('Karen') || // Mac - good quality
          v.name.includes('Ava') || // Mac - enhanced
          v.name.includes('Google UK English Female') || // Google - natural
          v.name.includes('Google US English') || // Google
          v.name.includes('Microsoft Aria') || // Windows 11 - new natural voice
          v.name.includes('Microsoft Zira') || // Windows
          (v.lang === 'en-US' && v.localService && v.voiceURI.includes('Premium'))
        );

        if (preferredVoice) {
          utterance.voice = preferredVoice;
          console.log('Using voice:', preferredVoice.name);
        }

        utterance.onend = () => setIsSpeaking(false);
        utterance.onerror = () => setIsSpeaking(false);

        window.speechSynthesis.speak(utterance);
      };

      // If voices aren't loaded yet, wait for them
      if (voices.length === 0) {
        window.speechSynthesis.onvoiceschanged = () => {
          speakWithVoice();
        };
      } else {
        speakWithVoice();
      }

    } catch (error) {
      console.error('Speech error:', error);
      setIsSpeaking(false);
    }
  };

  const processUserInput = async (userMessage: string) => {
    addMessage('user', userMessage);

    await new Promise(resolve => setTimeout(resolve, 500));

    let response = '';
    let nextStep = currentStep;
    const lowerMessage = userMessage.toLowerCase();

    switch (currentStep) {
      case 'service':
        const serviceKeywords: Record<string, string> = {
          'dentist': 'dentist',
          'dental': 'dentist',
          'teeth': 'dentist',
          'doctor': 'doctor',
          'physician': 'doctor',
          'medical': 'doctor',
          'hair': 'hair_salon',
          'salon': 'hair_salon',
          'haircut': 'hair_salon',
          'barber': 'barber',
          'mechanic': 'auto_mechanic',
          'car': 'auto_mechanic',
          'auto': 'auto_mechanic',
          'plumber': 'plumber',
          'plumbing': 'plumber',
          'electrician': 'electrician',
          'electric': 'electrician',
          'massage': 'massage',
          'spa': 'massage',
          'vet': 'veterinarian',
          'veterinarian': 'veterinarian',
          'pet': 'veterinarian',
          'restaurant': 'restaurant',
          'dining': 'restaurant',
          'dinner': 'restaurant',
          'lunch': 'restaurant',
          'eat': 'restaurant',
          'reservation': 'restaurant',
          'table': 'restaurant'
        };

        let detectedService = '';
        for (const [keyword, service] of Object.entries(serviceKeywords)) {
          if (lowerMessage.includes(keyword)) {
            detectedService = service;
            break;
          }
        }

        if (detectedService) {
          setBookingData(prev => ({ ...prev, service_type: detectedService }));
          response = `Great! I'll help you find a ${detectedService.replace('_', ' ')}. Where are you located?`;
          nextStep = 'location';
        } else {
          response = "I can help you book appointments for: restaurant, dentist, doctor, hair salon, massage, or veterinarian. Which service do you need?";
        }
        break;

      case 'location':
        setBookingData(prev => ({ ...prev, location: userMessage }));
        response = `Perfect! I'll search in ${userMessage}. When do you need this appointment?`;
        nextStep = 'timeframe';
        break;

      case 'timeframe':
        const timeframeKeywords: Record<string, string> = {
          'today': 'today',
          'tomorrow': 'tomorrow',
          'this week': 'this_week',
          'next week': 'next_week',
          'this month': 'this_month',
          'asap': 'today',
          'soon': 'this_week'
        };

        let detectedTimeframe = 'this_week';
        for (const [keyword, timeframe] of Object.entries(timeframeKeywords)) {
          if (lowerMessage.includes(keyword)) {
            detectedTimeframe = timeframe;
            break;
          }
        }

        setBookingData(prev => ({ ...prev, timeframe: detectedTimeframe }));
        response = `Got it! Let me confirm: You need a ${bookingData.service_type?.replace('_', ' ')} in ${bookingData.location}, ${detectedTimeframe.replace('_', ' ')}. I'll call 2 providers to find your best options. Should I proceed?`;
        nextStep = 'confirm';
        break;

      case 'confirm':
        if (lowerMessage.includes('yes') || lowerMessage.includes('sure') || lowerMessage.includes('go') || lowerMessage.includes('proceed')) {
          response = "Perfect! I'm starting the search now. My AI agents are calling providers to find you the earliest appointments. You'll see the live progress in a moment.";
          nextStep = 'done';

          setTimeout(async () => {
            try {
              const request: BookingRequest = {
                service_type: bookingData.service_type!,
                timeframe: bookingData.timeframe!,
                location: bookingData.location!,
                preferences: {
                  availability_weight: 0.4,
                  rating_weight: 0.3,
                  distance_weight: 0.3,
                },
              };

              const bookingResponse = await apiClient.createBookingRequest(request);

              setTimeout(() => {
                router.push('/dashboard/tasks');
              }, 1500);
            } catch (error) {
              const errorMsg = "Sorry, there was an error creating your booking. Please try again.";
              addMessage('assistant', errorMsg);
              speak(errorMsg);
              setCurrentStep('service');
            }
          }, 1000);
        } else {
          response = "No problem! What would you like to change?";
        }
        break;

      case 'done':
        response = "Your booking is being processed! Redirecting you now.";
        break;
    }

    if (response) {
      addMessage('assistant', response);
      speak(response);
    }

    setCurrentStep(nextStep);
  };

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      const errorMsg = 'Voice input is not supported in your browser. Please use Chrome, Edge, or Safari.';
      addMessage('assistant', errorMsg);
      speak(errorMsg);
      return;
    }

    // Stop any ongoing speech
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setIsSpeaking(false);

    const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      setTranscriptText('');
    };

    recognition.onresult = (event: any) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          finalTranscript += transcript;
        } else {
          interimTranscript += transcript;
        }
      }

      setTranscriptText(interimTranscript || finalTranscript);

      if (finalTranscript) {
        processUserInput(finalTranscript);
      }
    };

    recognition.onerror = (event: any) => {
      console.error('Speech recognition error:', event.error);
      setIsListening(false);
      setTranscriptText('');

      if (event.error !== 'no-speech' && event.error !== 'aborted') {
        const errorMsg = 'Voice input failed. Please try again.';
        addMessage('assistant', errorMsg);
        speak(errorMsg);
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setTranscriptText('');
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const stopListening = () => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
    setIsListening(false);
  };

  return (
    <div className="min-h-full flex flex-col bg-white">
      {/* Header: same height as sidebar (h-16) */}
      <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10 bg-white sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex items-center space-x-3">
          <MessageSquare className="h-6 w-6 text-black" />
          <h1 className="text-2xl font-bold text-black">Voice AI Assistant</h1>
        </div>
      </div>

      {/* Main Content - Split Screen: scrollable area */}
      <div className="flex-1 min-h-0 flex overflow-hidden">
        {/* Left Side - Animated Bubble */}
        <div className="flex-1 flex items-center justify-center p-8">
          <div className="relative">
            {/* Animated Bubble */}
            <div className={`relative transition-all duration-300 ${
              isListening ? 'scale-110' : isSpeaking ? 'scale-105' : 'scale-100'
            }`}>
              {/* Outer glow rings */}
              <div className={`absolute inset-0 rounded-full transition-opacity duration-500 ${
                isListening || isSpeaking ? 'opacity-100' : 'opacity-0'
              }`}>
                <div className="absolute inset-[-20px] rounded-full bg-gradient-to-r from-blue-500/20 to-purple-500/20 animate-pulse" />
                <div className="absolute inset-[-40px] rounded-full bg-gradient-to-r from-blue-500/10 to-purple-500/10 animate-pulse" style={{ animationDelay: '0.5s' }} />
              </div>

              {/* Main bubble */}
              <div className={`relative w-64 h-64 rounded-full bg-gradient-to-br from-blue-500 via-purple-500 to-pink-500 shadow-2xl ${
                isListening ? 'animate-pulse' : isSpeaking ? 'animate-bounce' : ''
              }`}>
                {/* Inner shimmer */}
                <div className="absolute inset-4 rounded-full bg-gradient-to-br from-white/20 to-transparent backdrop-blur-sm" />

                {/* Center icon */}
                <div className="absolute inset-0 flex items-center justify-center">
                  {isListening ? (
                    <Mic className="h-20 w-20 text-white animate-pulse" />
                  ) : isSpeaking ? (
                    <Loader2 className="h-20 w-20 text-white animate-spin" />
                  ) : (
                    <MessageSquare className="h-20 w-20 text-white" />
                  )}
                </div>

                {/* Sound waves effect */}
                {(isListening || isSpeaking) && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    {[...Array(3)].map((_, i) => (
                      <div
                        key={i}
                        className="absolute rounded-full border-2 border-white/30"
                        style={{
                          width: `${100 + i * 40}%`,
                          height: `${100 + i * 40}%`,
                          animation: `ping ${1 + i * 0.3}s cubic-bezier(0, 0, 0.2, 1) infinite`,
                        }}
                      />
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Status Text */}
            <div className="text-center mt-8">
              <p className="text-2xl font-semibold text-black mb-2">
                {isListening ? 'Listening...' : isSpeaking ? 'Speaking...' : 'Ready to help'}
              </p>
              {transcriptText && (
                <p className="text-lg text-blue-600 italic">"{transcriptText}"</p>
              )}
            </div>

            {/* Control Button */}
            <div className="flex justify-center mt-8">
              <Button
                size="lg"
                onClick={isListening ? stopListening : startListening}
                className={`w-32 h-32 rounded-full text-white font-semibold text-lg shadow-2xl transition-all duration-300 ${
                  isListening
                    ? 'bg-red-500 hover:bg-red-600 scale-110'
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700'
                }`}
              >
                {isListening ? (
                  <>
                    <MicOff className="h-8 w-8" />
                  </>
                ) : (
                  <>
                    <Mic className="h-8 w-8" />
                  </>
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Right Side - Conversation & Data */}
        <div className="w-[500px] border-l border-black/10 bg-white flex flex-col">
          {/* Booking Data Summary */}
          {(bookingData.service_type || bookingData.location || bookingData.timeframe) && (
            <div className="p-6 border-b border-black/10">
              <h3 className="text-lg font-semibold mb-4 flex items-center text-black">
                <Calendar className="h-5 w-5 mr-2" />
                Booking Details
              </h3>
              <div className="space-y-3">
                {bookingData.service_type && (
                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-black/50">Service</p>
                      <p className="text-sm capitalize text-black">{bookingData.service_type.replace('_', ' ')}</p>
                    </div>
                  </div>
                )}
                {bookingData.location && (
                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-black/50">Location</p>
                      <p className="text-sm text-black">{bookingData.location}</p>
                    </div>
                  </div>
                )}
                {bookingData.timeframe && (
                  <div className="flex items-start space-x-3">
                    <CheckCircle2 className="h-5 w-5 text-green-600 mt-0.5" />
                    <div>
                      <p className="text-xs text-black/50">Timeframe</p>
                      <p className="text-sm capitalize text-black">{bookingData.timeframe.replace('_', ' ')}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Conversation Transcript */}
          <div className="flex-1 overflow-y-auto p-6">
            <h3 className="text-lg font-semibold mb-4 flex items-center text-black">
              <MessageSquare className="h-5 w-5 mr-2" />
              Conversation
            </h3>
            <div className="space-y-4">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`${
                    message.role === 'user' ? 'text-right' : 'text-left'
                  }`}
                >
                  <div
                    className={`inline-block px-4 py-2 rounded-lg ${
                      message.role === 'user'
                        ? 'bg-black text-white'
                        : 'bg-black/5 text-black border border-black/10'
                    }`}
                  >
                    <p className="text-sm">{message.content}</p>
                    <p className="text-xs opacity-50 mt-1">
                      {message.timestamp.toLocaleTimeString()}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Input Bar */}
          <div className="p-4 border-t border-black/10">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                if (textInput.trim()) {
                  processUserInput(textInput);
                  setTextInput('');
                }
              }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={textInput}
                onChange={(e) => setTextInput(e.target.value)}
                placeholder="Or type your message..."
                className="flex-1 px-4 py-2 border border-black/10 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-black"
              />
              <Button
                type="submit"
                size="sm"
                disabled={!textInput.trim()}
                className="bg-black text-white hover:bg-black/90"
              >
                Send
              </Button>
            </form>
            <p className="text-xs text-center text-black/40 mt-2">
              {isListening ? '🎤 Speak now...' : '💡 Click the microphone or type'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
