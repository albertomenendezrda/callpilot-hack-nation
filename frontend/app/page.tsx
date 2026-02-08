'use client';

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Phone,
  Calendar,
  MapPin,
  Star,
  Zap,
  Clock,
  Bot,
  Target,
  Users,
  ArrowRight,
  CheckCircle2,
  Sparkles,
  PhoneCall,
  MessageSquare,
  TrendingUp
} from 'lucide-react';

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-white/80 backdrop-blur-md border-b border-black/10 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-2">
              <Phone className="h-8 w-8 text-black" />
              <span className="text-2xl font-bold text-black">CallPilot</span>
            </div>
            <div className="flex items-center space-x-6">
              <a href="#features" className="text-sm font-medium text-black/70 hover:text-black transition-colors">
                Features
              </a>
              <a href="#how-it-works" className="text-sm font-medium text-black/70 hover:text-black transition-colors">
                How It Works
              </a>
              <Link href="/dashboard">
                <span className="text-sm font-medium text-black/70 hover:text-black transition-colors cursor-pointer">
                  Dashboard
                </span>
              </Link>
              <Link href="/dashboard/chat">
                <Button size="sm" className="bg-black text-white hover:bg-black/90">
                  Try AI Chat
                </Button>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center">
            <div className="inline-flex items-center px-4 py-1.5 mb-8 border border-black rounded-full bg-white">
              <Sparkles className="h-4 w-4 mr-2 text-black" />
              <span className="text-sm font-medium text-black">Powered by ElevenLabs Voice AI</span>
            </div>
            <h1 className="text-5xl md:text-7xl lg:text-8xl font-bold tracking-tight mb-6 text-black">
              Never waste time
              <br />
              <span className="text-black/60">calling for appointments</span>
            </h1>
            <p className="text-xl md:text-2xl text-black/60 mb-12 max-w-3xl mx-auto leading-relaxed">
              CallPilot calls every provider for you, negotiates appointments in parallel,
              and books the earliest available slot that matches your calendar.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center mb-12">
              <Link href="/dashboard/chat">
                <Button size="lg" className="text-lg px-10 py-6 bg-black text-white hover:bg-black/90">
                  Try AI Chat
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              <Button size="lg" variant="outline" className="text-lg px-10 py-6 border-2 border-black text-black hover:bg-black/5">
                Watch Demo
              </Button>
            </div>
            <p className="text-sm text-black/50">
              Book your first 3 appointments free • No credit card required
            </p>
          </div>
        </div>

        {/* Decorative grid */}
        <div className="absolute top-0 left-0 -z-10 h-full w-full">
          <div className="absolute top-40 left-20 h-96 w-96 rounded-full bg-black/5 blur-3xl" />
          <div className="absolute bottom-40 right-20 h-96 w-96 rounded-full bg-black/5 blur-3xl" />
        </div>
      </section>

      {/* Problem Statement */}
      <section className="py-20 bg-black text-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl md:text-5xl font-bold mb-6">
            The last mile of the internet is still a phone call
          </h2>
          <p className="text-xl md:text-2xl text-white/70 leading-relaxed">
            Booking a single appointment wastes 20-30 minutes of your life.
            Finding the earliest slot across 15 providers? Impossible... until now.
          </p>
        </div>
      </section>

      {/* How It Works Section */}
      <section id="how-it-works" className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-black">
              How CallPilot Works
            </h2>
            <p className="text-xl text-black/60 max-w-2xl mx-auto">
              Three simple steps to never waste time booking appointments again
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-12">
            <div className="text-center">
              <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-black text-white text-3xl font-bold mb-8">
                1
              </div>
              <MessageSquare className="h-16 w-16 mx-auto mb-6 text-black" />
              <h3 className="text-2xl font-bold mb-4 text-black">Tell Us What You Need</h3>
              <p className="text-black/60 text-lg leading-relaxed">
                Type or speak: "Book me the earliest dentist appointment this week"
              </p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-black text-white text-3xl font-bold mb-8">
                2
              </div>
              <PhoneCall className="h-16 w-16 mx-auto mb-6 text-black" />
              <h3 className="text-2xl font-bold mb-4 text-black">We Call Everyone</h3>
              <p className="text-black/60 text-lg leading-relaxed">
                Our AI agents call up to 15 providers simultaneously, negotiating slots in natural conversation
              </p>
            </div>

            <div className="text-center">
              <div className="inline-flex items-center justify-center h-20 w-20 rounded-full bg-black text-white text-3xl font-bold mb-8">
                3
              </div>
              <CheckCircle2 className="h-16 w-16 mx-auto mb-6 text-black" />
              <h3 className="text-2xl font-bold mb-4 text-black">You Get the Best Option</h3>
              <p className="text-black/60 text-lg leading-relaxed">
                We rank by availability, ratings, and distance. You confirm, we book it.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-24 bg-black/5">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-black">
              The Phone Call, Automated
            </h2>
            <p className="text-xl text-black/60 max-w-2xl mx-auto">
              Powered by ElevenLabs Conversational AI and Agentic Functions
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
            <Card className="border-2 border-black/10 hover:border-black/30 transition-all hover:shadow-xl bg-white">
              <CardHeader>
                <Bot className="h-14 w-14 text-black mb-4" />
                <CardTitle className="text-xl">Voice AI Agents</CardTitle>
                <CardDescription className="text-base">
                  Natural conversation with receptionists. Handles interruptions, holds, and complex negotiations.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 border-black/10 hover:border-black/30 transition-all hover:shadow-xl bg-white">
              <CardHeader>
                <Zap className="h-14 w-14 text-black mb-4" />
                <CardTitle className="text-xl">Parallel Outreach</CardTitle>
                <CardDescription className="text-base">
                  Call up to 15 providers simultaneously. What takes you hours takes us seconds.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 border-black/10 hover:border-black/30 transition-all hover:shadow-xl bg-white">
              <CardHeader>
                <Calendar className="h-14 w-14 text-black mb-4" />
                <CardTitle className="text-xl">Calendar Integration</CardTitle>
                <CardDescription className="text-base">
                  Real-time calendar checking prevents double booking. Only books slots that work for you.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 border-black/10 hover:border-black/30 transition-all hover:shadow-xl bg-white">
              <CardHeader>
                <Target className="h-14 w-14 text-black mb-4" />
                <CardTitle className="text-xl">Smart Ranking</CardTitle>
                <CardDescription className="text-base">
                  Scores options by earliest availability, Google ratings, travel distance, and your preferences.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 border-black/10 hover:border-black/30 transition-all hover:shadow-xl bg-white">
              <CardHeader>
                <MapPin className="h-14 w-14 text-black mb-4" />
                <CardTitle className="text-xl">Location-Aware</CardTitle>
                <CardDescription className="text-base">
                  Considers travel distance and time via Google Maps. Never book across town when there's closer.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 border-black/10 hover:border-black/30 transition-all hover:shadow-xl bg-white">
              <CardHeader>
                <Star className="h-14 w-14 text-black mb-4" />
                <CardTitle className="text-xl">Quality First</CardTitle>
                <CardDescription className="text-base">
                  Integrates Google Places ratings and reviews. We only recommend providers you'll love.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section className="py-24 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-20">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-black">
              Works For Any Appointment
            </h2>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
            {[
              { icon: '🦷', title: 'Healthcare', desc: 'Dentists, doctors, specialists' },
              { icon: '✂️', title: 'Personal Care', desc: 'Salons, spas, barbers' },
              { icon: '🔧', title: 'Home Services', desc: 'Plumbers, electricians, HVAC' },
              { icon: '🚗', title: 'Auto Services', desc: 'Mechanics, detailing, inspections' }
            ].map((useCase, idx) => (
              <Card key={idx} className="border-2 border-black/10 hover:border-black/30 transition-all bg-white text-center">
                <CardHeader>
                  <div className="text-6xl mb-4">{useCase.icon}</div>
                  <CardTitle className="text-lg">{useCase.title}</CardTitle>
                  <CardDescription>{useCase.desc}</CardDescription>
                </CardHeader>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="py-24 bg-black text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-12 text-center">
            <div>
              <div className="text-5xl md:text-6xl font-bold mb-3">15×</div>
              <div className="text-xl text-white/70">Faster Than Manual Calling</div>
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-bold mb-3">20min</div>
              <div className="text-xl text-white/70">Average Time Saved Per Booking</div>
            </div>
            <div>
              <div className="text-5xl md:text-6xl font-bold mb-3">98%</div>
              <div className="text-xl text-white/70">Successful Booking Rate</div>
            </div>
          </div>
        </div>
      </section>

      {/* Technology Section */}
      <section className="py-24 bg-white">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl md:text-5xl font-bold mb-6 text-black">
              Built on Cutting-Edge Voice AI
            </h2>
            <p className="text-xl text-black/60 max-w-3xl mx-auto leading-relaxed">
              CallPilot leverages ElevenLabs Conversational AI and Agentic Functions to deliver
              human-like phone interactions with real-time decision making and tool orchestration.
            </p>
          </div>

          <div className="grid md:grid-cols-2 gap-8">
            <Card className="border-2 border-black/10 bg-white">
              <CardHeader>
                <CardTitle className="text-2xl mb-3">ElevenLabs Voice Engine</CardTitle>
                <CardDescription className="text-base leading-relaxed">
                  Natural, responsive voice interactions with &lt;1s latency. Handles interruptions,
                  clarifying questions, and complex multi-turn conversations.
                </CardDescription>
              </CardHeader>
            </Card>

            <Card className="border-2 border-black/10 bg-white">
              <CardHeader>
                <CardTitle className="text-2xl mb-3">Agentic Functions</CardTitle>
                <CardDescription className="text-base leading-relaxed">
                  Real-time tool calling for calendar checks, provider lookup, distance calculations,
                  and slot validation during live conversations.
                </CardDescription>
              </CardHeader>
            </Card>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-24 bg-black text-white">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            Stop wasting time on hold
          </h2>
          <p className="text-xl md:text-2xl text-white/70 mb-12 leading-relaxed">
            Let CallPilot handle the phone calls. You just show up.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-8">
            <Link href="/book">
              <Button size="lg" className="text-lg px-10 py-6 bg-white text-black hover:bg-white/90">
                Start Booking Free
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
            </Link>
            <Button size="lg" variant="outline" className="text-lg px-10 py-6 border-2 border-white text-white hover:bg-white/10">
              Schedule Demo
            </Button>
          </div>
          <p className="text-sm text-white/50">
            First 3 bookings free • No credit card required
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-black/10 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="flex items-center space-x-2 mb-4">
                <Phone className="h-6 w-6 text-black" />
                <span className="text-lg font-bold text-black">CallPilot</span>
              </div>
              <p className="text-sm text-black/60">
                Autonomous voice AI for appointment scheduling
              </p>
            </div>

            <div>
              <h3 className="font-semibold mb-4 text-black">Product</h3>
              <ul className="space-y-2 text-sm text-black/60">
                <li><a href="#features" className="hover:text-black transition-colors">Features</a></li>
                <li><a href="#how-it-works" className="hover:text-black transition-colors">How It Works</a></li>
                <li><a href="#" className="hover:text-black transition-colors">Pricing</a></li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4 text-black">Company</h3>
              <ul className="space-y-2 text-sm text-black/60">
                <li><a href="#" className="hover:text-black transition-colors">About</a></li>
                <li><a href="#" className="hover:text-black transition-colors">Blog</a></li>
                <li><a href="#" className="hover:text-black transition-colors">Contact</a></li>
              </ul>
            </div>

            <div>
              <h3 className="font-semibold mb-4 text-black">Legal</h3>
              <ul className="space-y-2 text-sm text-black/60">
                <li><a href="#" className="hover:text-black transition-colors">Privacy</a></li>
                <li><a href="#" className="hover:text-black transition-colors">Terms</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-black/10 mt-8 pt-8 text-center text-sm text-black/60">
            <p>&copy; 2026 CallPilot. All rights reserved. Powered by ElevenLabs.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
