# CallPilot Testing Guide

## Current Setup (Cost-Efficient Testing Mode)

To avoid burning through Google API budgets, CallPilot is configured to use **mock Cambridge, MA providers** while still making **real Twilio phone calls** to your test number.

## How It Works

### Provider Data
- **15 mock providers** per service category (dentist, doctor, hair salon, etc.)
- All located in **Cambridge, MA** with realistic addresses
- All use the **same phone number**: `+16173596803` (your cofounder's test number)
- Each has realistic ratings (4.0-5.0 stars)
- Mock distances: 0.3-2.8 miles (Cambridge is small!)

### Real Phone Calls
When you create a booking:
1. ✅ **Real Twilio calls** are made to `+16173596803`
2. ✅ Each provider gets a **custom TwiML message** mentioning their name
3. ✅ You get **real Twilio Call SIDs** for tracking
4. ✅ Your cofounder receives **actual phone calls** for each provider

### What's Simulated
- ❌ Provider search (using mock data instead of Google Places)
- ❌ Distance calculation (random distances between 0.3-2.8 mi)
- ❌ Availability results (70% chance of having appointments)

## Testing the System

### 1. Start the Backend
```bash
cd callpilot/backend
source venv/bin/activate
python app.py
```

You should see:
```
📊 Mode Configuration:
   🎯 REAL TWILIO CALLS enabled
   📍 Using mock Cambridge, MA providers (no Google API costs)
   📞 All calls route to: +16173596803

🔧 Configured APIs:
   - Twilio: ✅
   - ElevenLabs: ✅
```

### 2. Start the Frontend
```bash
cd callpilot/frontend
npm run dev
```

### 3. Create a Test Booking
1. Go to http://localhost:3000
2. Click "Get Started"
3. Fill in the form:
   - **Service Type**: Select any (e.g., "Dentist")
   - **Timeframe**: "this week"
   - **Location**: "Cambridge, MA" (or any location - it will still use Cambridge providers)
4. Submit

### 4. What Happens Next
- Backend finds 15 mock Cambridge providers
- Makes **real Twilio calls** to each one (all to +16173596803)
- Your cofounder receives **15 phone calls** in sequence
- Each call has a custom message mentioning the provider name
- Results appear on the UI ranked by score

### 5. Check the Dashboard
- Navigate to http://localhost:3000/dashboard
- See:
  - Total bookings created
  - Number of calls made
  - Connection status
  - Recent bookings with call information

## What Your Cofounder Will Hear

Each call will say something like:
> "Hello, this is Call Pilot. I'm an AI assistant calling on behalf of a customer to book a dentist appointment at [Provider Name]. Do you have any availability this week?"

Where `[Provider Name]` rotates through:
- Cambridge Dental Associates
- Harvard Square Dental
- Central Square Smiles
- Porter Dental Group
- Kendall Dentistry
- etc.

## Cost Breakdown

### Current Setup (Mock Providers + Real Calls)
- **Twilio**: ~$0.01-0.02 per call
- **15 calls per booking** = $0.15-0.30 per booking
- **Google APIs**: $0 (using mock data)
- **Total**: ~$0.15-0.30 per booking

### If Using Real Google APIs
- **Twilio**: $0.15-0.30 per booking
- **Google Places API**: ~$0.017 per search
- **Google Geocoding**: ~$0.005 per request
- **Google Distance Matrix**: ~$0.005-0.010 per element (15 providers = $0.075-0.15)
- **Total**: ~$0.25-0.50 per booking

**Savings**: ~50% by using mock providers!

## Available Mock Provider Categories

All categories have 15 realistic Cambridge, MA providers:
- `dentist`
- `doctor`
- `hair_salon`
- `barber`
- `auto_mechanic`
- `plumber`
- `electrician`
- `massage`
- `veterinarian`

## Sample Provider Addresses

All addresses are real Cambridge locations:
- 1 Massachusetts Ave, Cambridge, MA 02139 (Near MIT)
- 730 Massachusetts Ave, Cambridge, MA 02139 (Central Square)
- 50 JFK St, Cambridge, MA 02138 (Harvard Square)
- 625 Mt Auburn St, Cambridge, MA 02138 (Near Harvard)
- 907 Main St, Cambridge, MA 02139 (Kendall Square)
- And 10 more realistic locations...

## Switching Modes

### To Disable Real Calls (Full Demo Mode)
```bash
# In backend/.env
USE_REAL_CALLS=false
```
- No Twilio calls made
- No costs at all
- Fully simulated experience

### To Enable Real Google APIs (Future)
```bash
# In backend/.env
USE_REAL_CALLS=true
USE_MOCK_PROVIDERS=false  # (Would need to implement this)
```
- Real Google Places search
- Real distances
- Real Twilio calls
- Higher cost but production-ready

## Monitoring Calls

### Via Twilio Console
1. Go to https://console.twilio.com
2. Navigate to Phone Numbers → Logs
3. See all Call SIDs and statuses
4. Listen to recordings (if enabled)

### Via Dashboard
1. Go to http://localhost:3000/dashboard
2. See call statistics
3. View recent bookings with call SIDs

## Tips for Testing

1. **Test one category at a time** to limit calls to 15
2. **Your cofounder should be ready** - 15 calls happen quickly!
3. **Check the backend logs** for detailed Call SID information
4. **Use the Dashboard** to track all booking activity
5. **Monitor Twilio console** for call status and recordings

## Future Enhancements

When ready for production:
- [ ] Enable real Google Places API search
- [ ] Implement ElevenLabs Conversational AI WebSocket integration
- [ ] Parse call transcripts for actual availability
- [ ] Add Google Calendar integration
- [ ] Implement provider website scraping
- [ ] Add call recording analysis
- [ ] Implement callback functionality for confirmed appointments

## Troubleshooting

### No calls being made?
- Check `USE_REAL_CALLS=true` in `.env`
- Verify Twilio credentials in `.env`
- Check backend logs for errors

### Calls failing?
- Verify `TEST_CALL_NUMBER=+16173596803` in `.env`
- Check Twilio account balance
- Verify phone number format includes `+1`

### Not seeing providers?
- Any location will return Cambridge providers (by design)
- Check backend logs for provider generation
- All categories are supported

## Questions?

Check the main documentation:
- [README.md](../README.md) - Project overview
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [ELEVENLABS_INTEGRATION.md](ELEVENLABS_INTEGRATION.md) - Voice AI details
