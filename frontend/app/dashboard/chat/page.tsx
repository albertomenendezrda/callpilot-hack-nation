'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Mic, MicOff, Loader2, MessageSquare, Bot, AlertCircle } from 'lucide-react';
import { apiClient, BookingRequest } from '@/lib/api-client';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isFormatted?: boolean;
  formattedData?: { service?: string; location?: string; timeframe?: string; preferred_slots?: string };
}

type TaskStatus = 'gathering_info' | 'ready_to_call' | 'requires_user_attention';

interface BookingData {
  service_type?: string;
  location?: string;
  timeframe?: string;
  preferred_slots?: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

export default function ChatPage() {
  const router = useRouter();
  const [messages, setMessages] = useState<Message[]>([
    {
      role: 'assistant',
      content: "Hi! I'm CallPilot. Tell me what you need—for example, \"I need a dentist in Cambridge this week\"—and I'll gather the details and call providers for you.",
      timestamp: new Date()
    }
  ]);
  const [input, setInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [bookingData, setBookingData] = useState<BookingData>({});
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<TaskStatus>('gathering_info');
  const [isListening, setIsListening] = useState(false);
  const [creatingBooking, setCreatingBooking] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const recognitionRef = useRef<any>(null);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);
  useEffect(() => {
    return () => { recognitionRef.current?.stop(); };
  }, []);

  // Create task on mount
  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch(`${API_URL}/api/task`, { method: 'POST' });
        const data = await res.json();
        if (!cancelled && data.task_id) setTaskId(data.task_id);
      } catch (_) {}
    })();
    return () => { cancelled = true; };
  }, []);

  const addMessage = (role: 'user' | 'assistant', content: string, formattedData?: Message['formattedData']) => {
    setMessages(prev => [...prev, {
      role,
      content,
      timestamp: new Date(),
      ...(formattedData && { isFormatted: true, formattedData })
    }]);
  };

  const processUserInput = async (userMessage: string) => {
    if (!taskId) {
      addMessage('assistant', "Please wait a moment while I set things up, then try again.");
      return;
    }
    addMessage('user', userMessage);
    setInput('');
    setIsProcessing(true);

    try {
      const res = await fetch(`${API_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ task_id: taskId, message: userMessage })
      });
      const data = await res.json();
      if (!res.ok) {
        addMessage('assistant', data.error || 'Something went wrong.');
        setTaskStatus('requires_user_attention');
        return;
      }

      setBookingData(data.extracted_data || {});
      setTaskStatus(data.task_status || 'gathering_info');

      const ext = data.extracted_data || {};
      const formatted = (data.task_status === 'ready_to_call' && (ext.service_type || ext.location || ext.timeframe))
        ? { service: ext.service_type?.replace('_', ' '), location: ext.location, timeframe: ext.timeframe?.replace('_', ' '), preferred_slots: ext.preferred_slots }
        : undefined;
      addMessage('assistant', data.reply || 'Got it.', formatted);
    } catch (_) {
      addMessage('assistant', "I couldn’t reach the server. Please try again.");
      setTaskStatus('requires_user_attention');
    } finally {
      setIsProcessing(false);
    }
  };

  const confirmAndCallProviders = async () => {
    const { service_type, location, timeframe } = bookingData;
    if (!service_type || !location || !timeframe) return;
    setCreatingBooking(true);
    try {
      const request: BookingRequest = {
        service_type,
        timeframe,
        location,
        preferences: {
          availability_weight: 0.4,
          rating_weight: 0.3,
          distance_weight: 0.3,
          ...(bookingData.preferred_slots && { preferred_slots: bookingData.preferred_slots }),
        },
      };
      await apiClient.createBookingRequest(request);
      addMessage('assistant', "Booking created. I’m calling providers now. You can watch progress on the Tasks page.");
      setTaskStatus('gathering_info');
      setTimeout(() => router.push('/dashboard/tasks'), 1500);
    } catch (_) {
      addMessage('assistant', "Sorry, creating the booking failed. Please try again.");
    } finally {
      setCreatingBooking(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing && !creatingBooking) processUserInput(input);
  };

  const toggleVoice = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      addMessage('assistant', 'Voice input is not supported in this browser. Try Chrome, Edge, or Safari.');
      return;
    }
    if (!isListening) {
      const SpeechRecognition = (window as any).webkitSpeechRecognition || (window as any).SpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';
      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
        setTimeout(() => processUserInput(transcript), 100);
      };
      recognition.onerror = () => {
        setIsListening(false);
        addMessage('assistant', 'Voice input failed. Please try again or type.');
      };
      recognition.onend = () => setIsListening(false);
      recognitionRef.current = recognition;
      recognition.start();
    } else {
      recognitionRef.current?.stop();
      setIsListening(false);
    }
  };

  const canConfirm = taskStatus === 'ready_to_call' && bookingData.service_type && bookingData.location && bookingData.timeframe;

  return (
    <div className="min-h-full flex flex-col bg-white">
      {/* Header: same height as sidebar (h-16) */}
      <div className="flex-shrink-0 h-16 flex items-center border-b border-black/10 bg-white sticky top-0 z-10">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full flex items-center space-x-3">
          <MessageSquare className="h-6 w-6 text-black" />
          <h1 className="text-2xl font-bold text-black">AI Chat Assistant</h1>
          {taskStatus === 'requires_user_attention' && (
            <div className="flex items-center gap-2 rounded-lg bg-amber-50 border border-amber-200 px-3 py-1.5 text-sm text-amber-800">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>Need more info—keep chatting.</span>
            </div>
          )}
        </div>
      </div>

      <div className="flex-1 min-h-0 flex flex-col max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 w-full py-4">
        <div className="flex-1 min-h-0 overflow-y-auto mb-4 space-y-4">
          {messages.map((message, index) => (
            <div key={index} className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded-lg px-4 py-3 ${
                message.role === 'user' ? 'bg-black text-white' : 'bg-black/5 text-black border-2 border-black/10'
              }`}>
                {message.role === 'assistant' && (
                  <div className="flex items-center space-x-2 mb-2">
                    <Bot className="h-4 w-4" />
                    <span className="text-xs font-semibold">CallPilot AI</span>
                  </div>
                )}
                <p className="text-sm whitespace-pre-line">{message.content}</p>
                {message.isFormatted && message.formattedData && (
                  <div className="mt-3 p-3 bg-white rounded-lg border-2 border-black/10">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="text-lg">📋</span>
                      <span className="font-semibold text-sm">Booking Summary</span>
                    </div>
                    <div className="space-y-1 text-sm">
                      <div className="flex items-start">
                        <span className="font-medium min-w-[80px]">Service:</span>
                        <span className="capitalize">{message.formattedData.service}</span>
                      </div>
                      <div className="flex items-start">
                        <span className="font-medium min-w-[80px]">Location:</span>
                        <span>{message.formattedData.location}</span>
                      </div>
                        <div className="flex items-start">
                        <span className="font-medium min-w-[80px]">Timeframe:</span>
                        <span className="capitalize">{message.formattedData.timeframe}</span>
                      </div>
                      {message.formattedData.preferred_slots && (
                        <div className="flex items-start">
                          <span className="font-medium min-w-[80px]">Availability:</span>
                          <span>{message.formattedData.preferred_slots}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
                <p className="text-xs opacity-50 mt-1">{message.timestamp.toLocaleTimeString()}</p>
              </div>
            </div>
          ))}
          {isProcessing && (
            <div className="flex justify-start">
              <div className="bg-black/5 text-black border-2 border-black/10 rounded-lg px-4 py-3 flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Thinking...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {canConfirm && (
          <div className="mb-4">
            <Button
              onClick={confirmAndCallProviders}
              disabled={creatingBooking}
              className="w-full bg-black text-white hover:bg-black/90"
            >
              {creatingBooking ? <Loader2 className="h-4 w-4 animate-spin mx-auto" /> : 'Call providers to find options'}
            </Button>
          </div>
        )}

        <form onSubmit={handleSubmit} className="border-2 border-black/10 rounded-lg p-3 bg-white">
          <div className="flex items-center space-x-2">
            <Button type="button" variant="outline" size="icon" onClick={toggleVoice} className={`border-black/10 ${isListening ? 'bg-red-50 text-red-600' : ''}`}>
              {isListening ? <MicOff className="h-4 w-4" /> : <Mic className="h-4 w-4" />}
            </Button>
            <Input
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Type your message..."
              disabled={isProcessing || creatingBooking}
              className="flex-1 border-0 focus-visible:ring-0 focus-visible:ring-offset-0"
            />
            <Button type="submit" size="icon" disabled={!input.trim() || isProcessing || creatingBooking} className="bg-black text-white hover:bg-black/90">
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
        <p className="text-xs text-center text-black/40 mt-2">🎤 Click the microphone to speak</p>
      </div>
    </div>
  );
}
