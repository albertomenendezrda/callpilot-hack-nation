# CallPilot - Architecture Documentation

## System Overview

CallPilot is a consumer-facing web application that uses AI voice agents to autonomously book appointments. The system follows a **product-first** architecture where users interact with a simple interface, while AI agents handle the complexity behind the scenes.

## Architecture Philosophy

### The Uber Model

CallPilot follows the Uber approach:
- **User doesn't hire drivers** → User doesn't manage agents
- **User requests a ride** → User requests an appointment
- **System handles dispatch** → System orchestrates AI agents

The key insight: **Users trust outcomes, not processes**

✅ "Booked at SmileCare Dental, Tuesday 10:30am"
❌ "Agent completed 3 tool calls and negotiated availability"

## High-Level Architecture

```
┌──────────────────────────────────────────────────────────┐
│                     USER INTERFACE                        │
│              (Next.js Web Application)                    │
│                                                           │
│  Landing Page → Booking Form → Results → Confirmation    │
└──────────────────────┬───────────────────────────────────┘
                       │
                       │ HTTPS/REST API
                       │
┌──────────────────────▼───────────────────────────────────┐
│              CALLPILOT ORCHESTRATOR                       │
│                  (Flask Backend)                          │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │          Request Processing Layer                │    │
│  │   - Parse user request                          │    │
│  │   - Validate inputs                             │    │
│  │   - Generate booking ID                          │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
│  ┌─────────────────────────────────────────────────┐    │
│  │            Engines & Services                    │    │
│  │                                                   │    │
│  │   ┌──────────────┐  ┌──────────────┐           │    │
│  │   │ Preference   │  │  Calendar    │           │    │
│  │   │   Engine     │  │   Engine     │           │    │
│  │   └──────────────┘  └──────────────┘           │    │
│  │                                                   │    │
│  │   ┌──────────────┐  ┌──────────────┐           │    │
│  │   │   Ranking    │  │    Swarm     │           │    │
│  │   │   Engine     │  │  Controller  │           │    │
│  │   └──────────────┘  └──────────────┘           │    │
│  └─────────────────────────────────────────────────┘    │
│                                                           │
└───────────────────┬───────────────────┬──────────────────┘
                    │                   │
        ┌───────────▼─────┐   ┌────────▼────────┐
        │  Firestore DB   │   │ Secret Manager  │
        │  (State Store)  │   │  (API Keys)     │
        └─────────────────┘   └─────────────────┘
                    │
        ┌───────────▼──────────────────┐
        │    External Integrations     │
        │                              │
        │  ┌────────────────────────┐ │
        │  │   ElevenLabs Voice AI  │ │  ← Voice Agent Creation
        │  └────────────────────────┘ │
        │                              │
        │  ┌────────────────────────┐ │
        │  │    Twilio Phone API    │ │  ← Outbound Calls
        │  └────────────────────────┘ │
        │                              │
        │  ┌────────────────────────┐ │
        │  │   Google Places API    │ │  ← Provider Search
        │  └────────────────────────┘ │
        │                              │
        │  ┌────────────────────────┐ │
        │  │   Google Maps API      │ │  ← Distance/Travel
        │  └────────────────────────┘ │
        │                              │
        │  ┌────────────────────────┐ │
        │  │  Google Calendar API   │ │  ← Availability Check
        │  └────────────────────────┘ │
        └──────────────────────────────┘
```

## Component Details

### Frontend (Next.js)

**Purpose**: User-facing interface for booking appointments

**Key Pages**:
- `/` - Landing page with product information
- `/book` - Booking form (service type, location, timeframe)
- `/booking/[id]` - Results page showing ranked options
- `/booking/[id]/success` - Confirmation page

**Technology Stack**:
- Next.js 15 (React 19)
- TypeScript
- TailwindCSS (Black & White theme)
- Radix UI components

**Design Principles**:
- Minimalist black and white aesthetic
- Mobile-first responsive design
- Focus on outcomes, not complexity
- Clear CTAs and conversion paths

### Backend (Flask API)

**Purpose**: Orchestrates the booking workflow and manages AI agents

**Core Endpoints**:

```
POST /api/booking/request
GET  /api/booking/{id}
POST /api/booking/{id}/confirm
GET  /health
```

**Services Architecture**:

#### 1. **Preference Engine**
- Manages user preferences for ranking
- Default weights: 40% availability, 30% rating, 30% distance
- Customizable per request

#### 2. **Calendar Engine**
- Integrates with Google Calendar API
- Checks availability in real-time
- Prevents double booking
- Adds confirmed appointments

#### 3. **Ranking Engine**
- Scores appointment options (0-100)
- Multi-factor scoring:
  - **Availability**: Earlier is better
  - **Rating**: Higher Google rating is better
  - **Distance**: Closer is better
  - **Travel Time**: Less time is better
- Returns sorted ranked list

#### 4. **Swarm Controller**
- Manages parallel AI agent execution
- Creates up to 15 simultaneous voice agents
- Collects and aggregates results
- Handles failures gracefully

### ElevenLabs Integration

**Voice Agent Lifecycle**:

1. **Agent Creation**
   ```python
   agent = elevenlabs.create_agent(
       voice_id="professional-voice",
       tools=[calendar_tool, provider_tool],
       system_prompt="You are booking an appointment..."
   )
   ```

2. **Tool Registration**
   - `check_calendar(datetime)` - Verify availability
   - `get_provider_info(name)` - Retrieve details
   - `calculate_distance(address)` - Get travel time
   - `confirm_slot(provider, datetime)` - Book appointment

3. **Call Execution**
   ```python
   call = elevenlabs.initiate_call(
       agent_id=agent.id,
       phone_number=provider.phone,
       context={"service": "dentist", "timeframe": "this week"}
   )
   ```

4. **Result Processing**
   - Extract availability data
   - Parse provider responses
   - Handle edge cases (closed, no availability, etc.)

### Swarm Mode (Parallel Calls)

**How It Works**:

```python
# Pseudo-code
async def swarm_call(providers):
    tasks = []
    for provider in providers:
        agent = create_agent(provider)
        task = asyncio.create_task(
            make_call(agent, provider.phone)
        )
        tasks.append(task)

    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if not isinstance(r, Exception)]
```

**Benefits**:
- 15 calls complete in ~60 seconds (vs 15-20 minutes manually)
- Fault tolerant (one failure doesn't block others)
- Scalable (can increase to 20-30 agents)

### Ranking Algorithm

**Scoring Formula**:

```
Score = (
    availability_weight * availability_score +
    rating_weight * rating_score +
    distance_weight * distance_score
)

Where:
- availability_score = 100 - (days_until_appointment * 10)
- rating_score = (google_rating / 5) * 100
- distance_score = max(0, 100 - (distance_miles * 5))
```

**Example**:

Provider A:
- Available: Tomorrow (+90 pts)
- Rating: 4.5/5 (+90 pts)
- Distance: 2 miles (+90 pts)
- **Score: 90**

Provider B:
- Available: Next week (+30 pts)
- Rating: 4.8/5 (+96 pts)
- Distance: 0.5 miles (+97.5 pts)
- **Score: 74.5**

→ Provider A wins (earliest availability)

## Data Flow

### Booking Request Flow

```
1. User submits form → POST /api/booking/request
2. Backend validates input
3. Google Places API → Find providers
4. Create booking record in Firestore
5. Swarm Controller → Spawn 15 ElevenLabs agents
6. Each agent → Call provider via Twilio
7. Agents → Use tools to check calendar, gather info
8. Results → Aggregated and stored
9. Ranking Engine → Score and sort results
10. Frontend polls → GET /api/booking/{id}
11. User sees ranked options
12. User confirms → POST /api/booking/{id}/confirm
13. Final call → Confirm appointment
14. Calendar Engine → Add to Google Calendar
15. Success page → Redirect
```

### State Management

**Firestore Schema**:

```javascript
bookings/{booking_id}: {
  user_id: string,
  service_type: string,
  location: string,
  timeframe: string,
  status: 'pending' | 'processing' | 'completed' | 'failed',
  preferences: {
    availability_weight: 0.4,
    rating_weight: 0.3,
    distance_weight: 0.3
  },
  results: [
    {
      provider_id: string,
      provider_name: string,
      phone: string,
      address: string,
      rating: number,
      distance: number,
      travel_time: number,
      availability_date: string,
      availability_time: string,
      score: number
    }
  ],
  confirmed_provider_id?: string,
  created_at: timestamp,
  updated_at: timestamp
}
```

## Security Architecture

### API Keys (Secret Manager)
- All credentials stored in Google Secret Manager
- Never committed to code
- Accessed via service account permissions
- Rotated regularly

### Authentication (Future)
- Firebase Auth for user accounts
- JWT tokens for API access
- OAuth 2.0 for Google Calendar
- Role-based access control

### CORS
- Whitelist frontend domains
- Block unauthorized origins
- HTTPS only in production

## Scalability Considerations

### Current Architecture
- Cloud Run (auto-scaling 0-10 instances)
- Firestore (managed NoSQL database)
- Stateless backend (horizontal scaling)

### Bottlenecks
1. **ElevenLabs API Rate Limits**
   - Solution: Queue system with backpressure
2. **Twilio Concurrent Call Limits**
   - Solution: Throttling + retry logic
3. **Firestore Write Throughput**
   - Solution: Batch writes, caching

### Future Enhancements
- Redis caching for provider data
- Pub/Sub for async processing
- Cloud Tasks for call scheduling
- CDN for frontend assets

## Deployment Architecture

### Production Environment

```
Users → Cloud CDN → Firebase Hosting (Frontend)
                         ↓ API Calls
Users → Load Balancer → Cloud Run (Backend)
                         ↓ Storage
                    Firestore Database
                         ↓ Secrets
                    Secret Manager
```

### CI/CD Pipeline
1. Git push to main
2. Cloud Build triggers
3. Run tests
4. Build Docker images
5. Deploy to Cloud Run
6. Run smoke tests
7. Rollback if failed

## Monitoring & Observability

### Metrics
- Booking success rate
- Average call duration
- API latency (p50, p95, p99)
- Error rates by endpoint

### Logging
- Structured JSON logs
- Cloud Logging aggregation
- Log-based metrics

### Alerting
- High error rate (>5%)
- Slow response time (>2s)
- Service downtime
- Budget thresholds

## Cost Structure

### Per Booking Estimate
- ElevenLabs API: ~$0.30-0.50 (15 calls)
- Twilio calls: ~$0.15-0.30 (15 calls)
- Google APIs: ~$0.05
- Cloud Run: ~$0.01
- **Total: ~$0.50-1.00 per booking**

### Optimization Strategies
- Cache provider data (reduce Places API calls)
- Intelligent provider selection (< 15 calls)
- Batch calendar operations
- Use Cloud Run min instances = 0

## Future Roadmap

### Phase 1 (MVP)
- [x] Landing page
- [x] Booking form
- [x] API structure
- [ ] ElevenLabs integration
- [ ] Single call functionality

### Phase 2 (Beta)
- [ ] Parallel calling (swarm mode)
- [ ] Google Calendar integration
- [ ] Ranking algorithm v1
- [ ] User accounts

### Phase 3 (Production)
- [ ] Rescheduling/cancellation agents
- [ ] Waitlist management
- [ ] Multi-language support
- [ ] Mobile apps (iOS/Android)

### Phase 4 (Scale)
- [ ] Enterprise features
- [ ] White-label solution
- [ ] API for third-party integrations
- [ ] Vertical-specific agents (CallPilot Health, etc.)

## Technology Decisions

### Why These Choices?

**Next.js**: Modern React framework with excellent DX and performance
**Flask**: Lightweight Python framework perfect for AI integrations
**GCP**: Comprehensive cloud platform with AI/ML services
**ElevenLabs**: Best-in-class voice AI with tool calling
**Twilio**: Industry standard for telephony
**Firestore**: Managed NoSQL with real-time capabilities
**TypeScript**: Type safety reduces bugs in production

## Success Metrics

### Key Performance Indicators
- **Booking Success Rate**: >95%
- **Average Booking Time**: <90 seconds
- **User Satisfaction**: >4.5/5 stars
- **Cost Per Booking**: <$1.00
- **API Uptime**: >99.9%

## References

- [ElevenLabs Conversational AI Docs](https://elevenlabs.io/docs)
- [Google Cloud Run Docs](https://cloud.google.com/run/docs)
- [Twilio Voice API](https://www.twilio.com/docs/voice)
- [Next.js Documentation](https://nextjs.org/docs)
